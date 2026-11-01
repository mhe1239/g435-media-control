"""Log Windows input signals that may be produced by a Logitech G435.

This is intentionally a diagnostic tool.  It does not remap buttons or send
media commands yet.  Run it while the headset is connected, press each
physical button, and inspect the events printed to the console and written to
g435-signal-log.jsonl.
"""

from __future__ import annotations

import ctypes
import json
import time
import warnings
from ctypes import wintypes
from datetime import datetime, timezone
from pathlib import Path

try:
    from pycaw.pycaw import AudioUtilities
except ImportError:
    AudioUtilities = None


user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

LRESULT = ctypes.c_ssize_t
WNDPROC = ctypes.WINFUNCTYPE(
    LRESULT,
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM,
)

WM_INPUT = 0x00FF
WM_INPUT_DEVICE_CHANGE = 0x00FE
WM_DESTROY = 0x0002
RID_INPUT = 0x10000003
RIDEV_INPUTSINK = 0x00000100
RIDEV_DEVNOTIFY = 0x00002000
RIDI_DEVICENAME = 0x20000007

RIM_TYPEMOUSE = 0
RIM_TYPEKEYBOARD = 1
RIM_TYPEHID = 2

VK_POWER = 0x5E
VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_STOP = 0xB2
VK_MEDIA_PLAY_PAUSE = 0xB3
VK_LAUNCH_MAIL = 0xB4
VK_LAUNCH_MEDIA_SELECT = 0xB5
VK_LAUNCH_APP1 = 0xB6
VK_LAUNCH_APP2 = 0xB7

VK_NAMES = {
    VK_POWER: "POWER",
    VK_VOLUME_MUTE: "VOLUME_MUTE",
    VK_VOLUME_DOWN: "VOLUME_DOWN",
    VK_VOLUME_UP: "VOLUME_UP",
    VK_MEDIA_NEXT_TRACK: "MEDIA_NEXT_TRACK",
    VK_MEDIA_PREV_TRACK: "MEDIA_PREV_TRACK",
    VK_MEDIA_STOP: "MEDIA_STOP",
    VK_MEDIA_PLAY_PAUSE: "MEDIA_PLAY_PAUSE",
    VK_LAUNCH_MAIL: "LAUNCH_MAIL",
    VK_LAUNCH_MEDIA_SELECT: "LAUNCH_MEDIA_SELECT",
    VK_LAUNCH_APP1: "LAUNCH_APP1",
    VK_LAUNCH_APP2: "LAUNCH_APP2",
}

MEDIA_KEYS = set(VK_NAMES)

# Explicit signatures are important on 64-bit Windows; without them a
# WM_INPUT lParam can be truncated when passed to DefWindowProcW.
user32.DefWindowProcW.argtypes = [
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM,
]
user32.DefWindowProcW.restype = LRESULT


class RAWINPUTDEVICE(ctypes.Structure):
    _fields_ = [
        ("usUsagePage", wintypes.USHORT),
        ("usUsage", wintypes.USHORT),
        ("dwFlags", wintypes.DWORD),
        ("hwndTarget", wintypes.HWND),
    ]


class RAWINPUTHEADER(ctypes.Structure):
    _fields_ = [
        ("dwType", wintypes.DWORD),
        ("dwSize", wintypes.DWORD),
        ("hDevice", wintypes.HANDLE),
        ("wParam", wintypes.WPARAM),
    ]


class RAWKEYBOARD(ctypes.Structure):
    _fields_ = [
        ("MakeCode", wintypes.USHORT),
        ("Flags", wintypes.USHORT),
        ("Reserved", wintypes.USHORT),
        ("VKey", wintypes.USHORT),
        ("Message", wintypes.UINT),
        ("ExtraInformation", wintypes.ULONG),
    ]


LOG_PATH = Path(__file__).with_name("g435-signal-log.jsonl")


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="milliseconds")


def device_name(device_handle) -> str:
    if not device_handle:
        return "(system)"

    size = wintypes.UINT(0)
    result = user32.GetRawInputDeviceInfoW(
        device_handle,
        RIDI_DEVICENAME,
        None,
        ctypes.byref(size),
    )
    if result == -1 or size.value == 0:
        return f"(device 0x{int(device_handle):X})"

    buffer = ctypes.create_unicode_buffer(size.value + 1)
    result = user32.GetRawInputDeviceInfoW(
        device_handle,
        RIDI_DEVICENAME,
        buffer,
        ctypes.byref(size),
    )
    if result == -1:
        return f"(device 0x{int(device_handle):X})"
    return buffer.value


def is_g435_candidate(name: str) -> bool:
    upper = name.upper()
    return any(marker in upper for marker in ("G435", "LOGITECH", "VID_046D"))


def emit(event: dict) -> None:
    event = {"time": now_iso(), **event}
    with LOG_PATH.open("a", encoding="utf-8") as log:
        log.write(json.dumps(event, ensure_ascii=False) + "\n")

    print(json.dumps(event, ensure_ascii=False), flush=True)


def parse_raw_input(raw_handle: int) -> None:
    size = wintypes.UINT(0)
    header_size = ctypes.sizeof(RAWINPUTHEADER)
    result = user32.GetRawInputData(
        ctypes.c_void_p(raw_handle),
        RID_INPUT,
        None,
        ctypes.byref(size),
        header_size,
    )
    if result == -1 or size.value < header_size:
        return

    buffer = ctypes.create_string_buffer(size.value)
    result = user32.GetRawInputData(
        ctypes.c_void_p(raw_handle),
        RID_INPUT,
        buffer,
        ctypes.byref(size),
        header_size,
    )
    if result == -1:
        return

    header = RAWINPUTHEADER.from_buffer_copy(buffer)
    name = device_name(header.hDevice)
    candidate = is_g435_candidate(name)

    if header.dwType == RIM_TYPEKEYBOARD:
        keyboard_offset = ctypes.sizeof(RAWINPUTHEADER)
        keyboard = RAWKEYBOARD.from_buffer_copy(buffer, keyboard_offset)
        key_name = VK_NAMES.get(keyboard.VKey)

        # Ordinary keyboard traffic is ignored.  Media/power keys and events
        # from a likely Logitech/G435 device are retained.
        if not candidate and not key_name:
            return

        emit(
            {
                "kind": "keyboard",
                "device": name,
                "candidate": candidate,
                "virtual_key": f"0x{keyboard.VKey:02X}",
                "key_name": key_name or "UNKNOWN",
                "make_code": f"0x{keyboard.MakeCode:02X}",
                "flags": f"0x{keyboard.Flags:04X}",
                "message": f"0x{keyboard.Message:04X}",
            }
        )
        return

    if header.dwType == RIM_TYPEHID:
        # RAWINPUT's HID payload begins after the header.  Keep the bytes in
        # the log so vendor-specific G435 reports can be decoded later.
        payload = bytes(buffer[header_size:])
        if candidate or payload:
            emit(
                {
                    "kind": "hid",
                    "device": name,
                    "candidate": candidate,
                    "bytes": payload.hex(" "),
                    "length": len(payload),
                }
            )


def register_raw_input(hwnd) -> None:
    # Standard keyboard consumer controls cover media/power keys.  The vendor
    # page registrations are included because some wireless receivers expose
    # button reports outside the standard consumer page.
    devices = (RAWINPUTDEVICE * 4)(
        RAWINPUTDEVICE(0x01, 0x06, RIDEV_INPUTSINK | RIDEV_DEVNOTIFY, hwnd),
        RAWINPUTDEVICE(0x0C, 0x01, RIDEV_INPUTSINK | RIDEV_DEVNOTIFY, hwnd),
        RAWINPUTDEVICE(0xFF00, 0x01, RIDEV_INPUTSINK | RIDEV_DEVNOTIFY, hwnd),
        RAWINPUTDEVICE(0xFF01, 0x01, RIDEV_INPUTSINK | RIDEV_DEVNOTIFY, hwnd),
    )

    if not user32.RegisterRawInputDevices(
        devices,
        len(devices),
        ctypes.sizeof(RAWINPUTDEVICE),
    ):
        raise ctypes.WinError(ctypes.get_last_error())


class G435AudioMonitor:
    """Poll G435 render/capture endpoint state exposed by Windows Bluetooth."""

    def __init__(self) -> None:
        self.previous: dict[str, dict] = {}
        self.reported_dependency = False

    def poll(self) -> None:
        if AudioUtilities is None:
            if not self.reported_dependency:
                emit(
                    {
                        "kind": "dependency_error",
                        "message": "Install dependencies with: python -m pip install -r requirements.txt",
                    }
                )
                self.reported_dependency = True
            return

        # pycaw can emit harmless COM warnings for unrelated inactive audio
        # endpoints.  They would obscure the G435 events we are looking for.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                devices = AudioUtilities.GetAllDevices()
            except Exception as exc:
                emit({"kind": "audio_error", "message": repr(exc)})
                return

        current_ids = set()
        for device in devices:
            name = device.FriendlyName or ""
            if "G435" not in name.upper():
                continue

            device_id = str(getattr(device, "id", name))
            current_ids.add(device_id)
            try:
                endpoint = device.EndpointVolume
                state = {
                    "device": name,
                    "device_id": device_id,
                    "state": str(getattr(device, "state", "unknown")),
                    "mute": bool(endpoint.GetMute()),
                    "volume_scalar": round(
                        float(endpoint.GetMasterVolumeLevelScalar()), 5
                    ),
                }
            except Exception as exc:
                emit(
                    {
                        "kind": "audio_error",
                        "device": name,
                        "device_id": device_id,
                        "message": repr(exc),
                    }
                )
                continue

            old = self.previous.get(device_id)
            self.previous[device_id] = state
            if old is None:
                emit({"kind": "audio_baseline", **state})
                continue

            if old["state"] != state["state"]:
                emit(
                    {
                        "kind": "audio_state_change",
                        "previous": old["state"],
                        **state,
                    }
                )

            if old["mute"] != state["mute"]:
                emit(
                    {
                        "kind": "audio_mute_change",
                        "previous": old["mute"],
                        **state,
                    }
                )

            if old["volume_scalar"] != state["volume_scalar"]:
                emit(
                    {
                        "kind": "audio_volume_change",
                        "previous": old["volume_scalar"],
                        **state,
                    }
                )

        # Keep the monitor ready for reconnects without producing a noisy
        # event for every normal polling cycle.
        for device_id in set(self.previous) - current_ids:
            del self.previous[device_id]


def main() -> None:
    class WNDCLASS(ctypes.Structure):
        _fields_ = [
            ("style", wintypes.UINT),
            ("lpfnWndProc", WNDPROC),
            ("cbClsExtra", ctypes.c_int),
            ("cbWndExtra", ctypes.c_int),
            ("hInstance", wintypes.HINSTANCE),
            ("hIcon", wintypes.HANDLE),
            ("hCursor", wintypes.HANDLE),
            ("hbrBackground", wintypes.HANDLE),
            ("lpszMenuName", wintypes.LPCWSTR),
            ("lpszClassName", wintypes.LPCWSTR),
        ]

    class_name = "G435SignalProbeWindow"
    hinstance = kernel32.GetModuleHandleW(None)

    @WNDPROC
    def wnd_proc(hwnd, message, wparam, lparam):
        try:
            if message == WM_INPUT:
                parse_raw_input(lparam)
                return 0
            if message == WM_INPUT_DEVICE_CHANGE:
                emit({"kind": "device_change", "wparam": int(wparam)})
                return 0
            if message == WM_DESTROY:
                user32.PostQuitMessage(0)
                return 0
        except Exception as exc:  # Keep the probe alive if one packet is odd.
            emit({"kind": "error", "message": repr(exc)})
        return user32.DefWindowProcW(hwnd, message, wparam, lparam)

    wnd_class = WNDCLASS(
        0,
        wnd_proc,
        0,
        0,
        hinstance,
        None,
        None,
        None,
        None,
        class_name,
    )
    atom = user32.RegisterClassW(ctypes.byref(wnd_class))
    if not atom:
        raise ctypes.WinError(ctypes.get_last_error())

    HWND_MESSAGE = wintypes.HWND(-3)
    hwnd = user32.CreateWindowExW(
        0,
        class_name,
        "G435 Signal Probe",
        0,
        0,
        0,
        0,
        0,
        HWND_MESSAGE,
        None,
        hinstance,
        None,
    )
    if not hwnd:
        raise ctypes.WinError(ctypes.get_last_error())

    register_raw_input(hwnd)
    audio_monitor = G435AudioMonitor()
    emit(
        {
            "kind": "started",
            "message": "Press each G435 button once. Stop with Ctrl+C.",
            "log_file": str(LOG_PATH),
            "audio_monitor": AudioUtilities is not None,
        }
    )

    msg = wintypes.MSG()
    next_audio_poll = 0.0
    try:
        while True:
            # PeekMessage keeps Ctrl+C responsive while still draining the
            # message-only window used by Raw Input.
            while user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1):
                if msg.message == 0x0012:  # WM_QUIT
                    return
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
            now = time.monotonic()
            if now >= next_audio_poll:
                audio_monitor.poll()
                next_audio_poll = now + 0.1
            time.sleep(0.01)
    except KeyboardInterrupt:
        emit({"kind": "stopped", "message": "Stopped by user."})
    finally:
        user32.DestroyWindow(hwnd)
        user32.UnregisterClassW(class_name, hinstance)


if __name__ == "__main__":
    if __import__("sys").platform != "win32":
        raise SystemExit("This diagnostic tool must run on Windows.")
    main()
