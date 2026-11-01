"""Windows port of the Android G435 play/pause gesture.

Windows sees only the G435 +/− as absolute volume changes on its Bluetooth
render endpoint (mute/power send nothing), so quick +/− direction flips become
media commands: +− or −+ toggles play/pause (as on Android), +−+ skips to the
next track and −+− to the previous one.

Run: python g435_media_gesture.py        (Ctrl+C to stop)
     python g435_media_gesture.py --self-test
"""

from __future__ import annotations

import sys

sys.coinit_flags = 0  # MTA, required by pycaw volume callbacks

import ctypes
import tempfile
import threading
import time
import wave
import winsound
from pathlib import Path

from g435_signal_probe import VK_MEDIA_NEXT_TRACK, VK_MEDIA_PLAY_PAUSE, VK_MEDIA_PREV_TRACK, emit

# shortcut: fixed window copied from Android, tune it if the user reports missed or false gestures.
GESTURE_WINDOW_S = 1.5
# When playback starts Windows re-syncs the volume as an up/down pair ~15 ms apart, which is no human press.
MIN_FLIP_S = 0.05  # fast human +/− flips were 0.15 s apart
# A two-press flip waits this long for a third press before it counts as play/pause.
# shortcut: fixed 1 s wait, shorten it if play/pause feels slow or lengthen it if +−+ is missed.
THIRD_PRESS_WAIT_S = 1.0
# shortcut: fixed delay before restoring the volume after a skip, tune it if the G435 still overrides the restore.
RESTORE_DELAY_S = 0.5
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
# Without the extended flag and scan code, Chrome's media session ignored the key (tested 2026-11-01).
# action: (SMTC session method, media key, scan code)
MEDIA_ACTIONS = {
    "play_pause": ("try_toggle_play_pause_async", VK_MEDIA_PLAY_PAUSE, 0x22),
    "next": ("try_skip_next_async", VK_MEDIA_NEXT_TRACK, 0x19),
    "previous": ("try_skip_previous_async", VK_MEDIA_PREV_TRACK, 0x10),
}
ERROR_ALREADY_EXISTS = 183


def is_play_pause_gesture(last_direction: int, last_change_at: float | None, direction: int, now: float) -> bool:
    return (last_change_at is not None and direction == -last_direction
            and MIN_FLIP_S <= now - last_change_at <= GESTURE_WINDOW_S)


def gesture_action(run: list[int]) -> str:
    """Map an alternating run of +1/−1 presses to its media action."""
    if len(run) == 2:
        return "play_pause"
    return "next" if run[0] > 0 else "previous"


def press_media_key(vk: int, scan: int) -> None:
    user32 = ctypes.windll.user32
    user32.keybd_event(vk, scan, KEYEVENTF_EXTENDEDKEY, 0)
    user32.keybd_event(vk, scan, KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP, 0)


def send_media_action(action: str) -> str:
    """Ask Windows' current media session to act; fall back to the media key when there is none."""
    import asyncio

    from winsdk.windows.media.control import GlobalSystemMediaTransportControlsSessionManager as Manager

    method, vk, scan = MEDIA_ACTIONS[action]

    # Targets the session Windows shows as current instead of relying on how apps route the media key.
    async def send() -> bool:
        current = (await Manager.request_async()).get_current_session()
        return current is not None and await getattr(current, method)()

    try:
        if asyncio.run(send()):
            return "session"
    except Exception as exc:
        emit({"kind": "media_sessions_error", "label": action, "message": repr(exc)})
    press_media_key(vk, scan)
    return "media_key"


def log_media_sessions(label: str) -> dict:
    """Record which media session Windows targets and each app's playback state."""
    import asyncio

    from winsdk.windows.media.control import GlobalSystemMediaTransportControlsSessionManager as Manager

    async def read() -> dict:
        manager = await Manager.request_async()
        current = manager.get_current_session()
        return {
            "current": current.source_app_user_model_id if current else None,
            "sessions": {s.source_app_user_model_id: s.get_playback_info().playback_status.name
                         for s in manager.get_sessions()},
        }

    try:
        state = asyncio.run(read())
    except Exception as exc:
        emit({"kind": "media_sessions_error", "label": label, "message": repr(exc)})
        return {}
    emit({"kind": "media_sessions", "label": label, **state})
    return state


# About 10 s after playback pauses, G435 +/− stop reaching Windows (tested 2026-11-01, as on Android),
# so a resume gesture is never seen. Looping silence to the default output keeps the Bluetooth stream up.
# shortcut: fixed 10 min limit after a gesture pause; make it a setting if the user wants longer.
SILENCE_KEEPER_S = 10 * 60
SILENCE_WAV = Path(tempfile.gettempdir()) / "g435-silence.wav"


class SilenceKeeper:
    def __init__(self) -> None:
        with wave.open(str(SILENCE_WAV), "wb") as wav:
            wav.setnchannels(2)
            wav.setsampwidth(2)
            wav.setframerate(44100)
            wav.writeframes(bytes(44100 * 4))
        self.timer: threading.Timer | None = None

    @property
    def active(self) -> bool:
        return self.timer is not None

    def start(self) -> None:
        winsound.PlaySound(str(SILENCE_WAV), winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP)
        self.timer = threading.Timer(SILENCE_KEEPER_S, self.stop)
        self.timer.start()
        emit({"kind": "silence_keeper", "action": "started"})

    def stop(self) -> None:
        if self.timer is None:
            return
        self.timer.cancel()
        self.timer = None
        winsound.PlaySound(None, 0)
        emit({"kind": "silence_keeper", "action": "stopped"})


def self_test() -> None:
    assert is_play_pause_gesture(1, 1.0, -1, 1.0 + GESTURE_WINDOW_S)
    assert is_play_pause_gesture(-1, 1.0, 1, 1.5)
    assert not is_play_pause_gesture(1, 1.0, -1, 1.01 + GESTURE_WINDOW_S)
    assert not is_play_pause_gesture(1, 1.0, 1, 1.5)
    assert not is_play_pause_gesture(1, None, -1, 1.0)
    assert not is_play_pause_gesture(1, 1.0, -1, 1.014)
    assert gesture_action([1, -1]) == gesture_action([-1, 1]) == "play_pause"
    assert gesture_action([1, -1, 1]) == "next"
    assert gesture_action([-1, 1, -1]) == "previous"
    print("self-test ok")


def main() -> None:
    from pycaw.callbacks import AudioEndpointVolumeCallback
    from pycaw.pycaw import AudioUtilities

    # A second listener would toggle again on the same gesture and cancel the first (seen 2026-11-01).
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateMutexW.restype = ctypes.c_void_p
    mutex = kernel32.CreateMutexW(None, False, "Local\\G435MediaGesture")
    if ctypes.get_last_error() == ERROR_ALREADY_EXISTS:
        sys.exit("g435_media_gesture is already running.")

    # shortcut: watches the default output only; pick the G435 endpoint by name if the user switches outputs.
    speakers = AudioUtilities.GetSpeakers()
    name = speakers.FriendlyName or ""
    if "G435" not in name.upper():
        sys.exit(f"Default output is not the G435: {name!r}")
    volume = speakers.EndpointVolume
    keeper = SilenceKeeper()

    class Gesture(AudioEndpointVolumeCallback):
        def __init__(self) -> None:
            super().__init__()
            self.level = volume.GetMasterVolumeLevelScalar()
            self.run: list[int] = []  # alternating presses so far, each +1 or −1
            self.last_change_at: float | None = None
            self.run_start_level = self.level
            # A skip leaves the volume one step off; restoring it fires one more change that is not a press.
            self.restoring: float | None = None
            self.pending: threading.Timer | None = None  # fires play/pause if no third press comes
            self.lock = threading.Lock()

        def on_notify(self, new_volume, new_mute, event_context, channels, channel_volumes):
            now = time.monotonic()
            direction = (new_volume > self.level) - (new_volume < self.level)
            # The context GUID may tell PC slider changes apart from the headset; logged to find out.
            emit({"kind": "gesture_volume", "previous": round(self.level, 5), "volume_scalar": round(new_volume, 5),
                  "context": str(event_context.contents)})
            previous, self.level = self.level, new_volume
            if direction == 0:
                return
            if self.restoring is not None and abs(new_volume - self.restoring) < 1e-4:
                self.restoring = None
                return
            with self.lock:
                if self.pending is not None:
                    self.pending.cancel()
                    self.pending = None
                if self.run and is_play_pause_gesture(self.run[-1], self.last_change_at, direction, now):
                    self.run.append(direction)
                else:
                    self.run = [direction]
                    self.run_start_level = previous
                self.last_change_at = now
                # Stopping the silence closes a stream, which fires this callback again; doing that
                # here deadlocked the listener (2026-11-01), so act outside the COM callback.
                if len(self.run) == 3:
                    action = gesture_action(self.run)
                    self.run = []
                    self.restoring = self.run_start_level
                    threading.Thread(target=self.act, args=(action,)).start()
                elif len(self.run) == 2:
                    self.pending = threading.Timer(THIRD_PRESS_WAIT_S, self.flush)
                    self.pending.start()

        def flush(self) -> None:
            with self.lock:
                # A third press may have arrived while this timer was already running.
                if self.pending is not threading.current_thread():
                    return
                self.pending = None
                action = gesture_action(self.run)
                self.run = []
            self.act(action)

        def act(self, action: str) -> None:
            emit({"kind": "gesture", "action": action, "via": send_media_action(action)})
            if action != "play_pause" and self.restoring is not None:
                # Restoring 1 ms after the third press was undone by the G435 resending its own level ~13 ms later (2026-11-02).
                time.sleep(RESTORE_DELAY_S)
                volume.SetMasterVolumeLevelScalar(self.restoring, None)
                emit({"kind": "gesture", "action": "volume_restored", "volume_scalar": round(self.restoring, 5)})
            # Decide from the state after the toggle: the state read before it lagged for Spotify.
            time.sleep(1)
            after = log_media_sessions("+1s")
            if after.get("sessions", {}).get(after.get("current")) == "PAUSED":
                if not keeper.active:
                    keeper.start()
            else:
                keeper.stop()

    # The first SMTC call took ~1 s and the user pressed again before the toggle landed; pay it up front.
    log_media_sessions("start")
    callback = Gesture()
    volume.RegisterControlChangeNotify(callback)
    emit({"kind": "gesture_started", "device": name, "volume_scalar": round(callback.level, 5)})
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        if callback.pending is not None:
            callback.pending.cancel()
        keeper.stop()
        volume.UnregisterControlChangeNotify(callback)


if __name__ == "__main__":
    self_test() if "--self-test" in sys.argv else main()
