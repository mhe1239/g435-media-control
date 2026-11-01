package com.g435.signalprobe;

import android.accessibilityservice.AccessibilityService;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.media.AudioAttributes;
import android.media.AudioFormat;
import android.media.AudioManager;
import android.media.AudioTrack;
import android.os.Build;
import android.os.Handler;
import android.os.Looper;
import android.os.SystemClock;
import android.view.KeyEvent;
import android.view.accessibility.AccessibilityEvent;

public final class G435AccessibilityService extends AccessibilityService {
    // Hidden AudioManager broadcasts; Bluetooth absolute-volume changes arrive only this way.
    private static final String VOLUME_CHANGED_ACTION = "android.media.VOLUME_CHANGED_ACTION";

    // The G435 mute button sends nothing to the phone, so a quick +/− direction flip is the
    // play/pause gesture. Either order works: at the G435 maximum + sends nothing, at 0 − sends nothing.
    // shortcut: fixed window, tune it if the user reports missed or false gestures.
    static final long GESTURE_WINDOW_MS = 1500;
    // +−+ is next track and −+− previous, so a two-press flip waits this long for a third press
    // before it counts as play/pause (same as the Windows listener).
    // shortcut: fixed 1 s wait, shorten it if play/pause feels slow or lengthen it if +−+ is missed.
    static final long THIRD_PRESS_WAIT_MS = 1000;

    private final BroadcastReceiver volumeReceiver = new BroadcastReceiver() {
        @Override
        public void onReceive(Context context, Intent intent) {
            int stream = intent.getIntExtra("android.media.EXTRA_VOLUME_STREAM_TYPE", -1);
            int prev = intent.getIntExtra("android.media.EXTRA_PREV_VOLUME_STREAM_VALUE", -1);
            int value = intent.getIntExtra("android.media.EXTRA_VOLUME_STREAM_VALUE", -1);
            if (stream == AudioManager.STREAM_MUSIC) {
                SignalLog.append(context, "volume_change", "prev=" + prev + ", value=" + value);
                onMusicVolumeChanged(prev, value, SystemClock.uptimeMillis());
            }
        }
    };
    private boolean receiverRegistered;
    // Alternating presses so far; the receiver and the timeout both run on the main thread.
    private int runLength;
    private int firstDirection;
    private int lastDirection;
    private long lastChangeAt = -1;
    private int runStartVolume;
    // A skip leaves the volume one step off; restoring it fires one more change that is not a press.
    private int restoringVolume = -1;
    private final Runnable playPauseTimeout = () -> {
        runLength = 0;
        playPause();
    };

    private void onMusicVolumeChanged(int prev, int value, long now) {
        int direction = Integer.signum(value - prev);
        if (direction == 0) {
            return;
        }
        if (value == restoringVolume) {
            restoringVolume = -1;
            return;
        }
        handler.removeCallbacks(playPauseTimeout);
        if (runLength > 0 && isPlayPauseGesture(lastDirection, lastChangeAt, direction, now)) {
            runLength++;
        } else {
            runLength = 1;
            firstDirection = direction;
            runStartVolume = prev;
        }
        lastDirection = direction;
        lastChangeAt = now;
        if (runLength == 3) {
            sendMediaKey(gestureKeyCode(runLength, firstDirection));
            runLength = 0;
            restoringVolume = runStartVolume;
            getSystemService(AudioManager.class).setStreamVolume(AudioManager.STREAM_MUSIC, runStartVolume, 0);
            SignalLog.append(this, "gesture", "volume restored to " + runStartVolume);
        } else if (runLength == 2) {
            handler.postDelayed(playPauseTimeout, THIRD_PRESS_WAIT_MS);
        }
    }

    private void playPause() {
        boolean pausing = silenceKeeper == null && getSystemService(AudioManager.class).isMusicActive();
        sendMediaKey(KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE);
        if (silenceKeeper != null) {
            stopSilenceKeeper();
        } else if (pausing) {
            startSilenceKeeper();
        }
    }

    private void sendMediaKey(int keyCode) {
        AudioManager audio = getSystemService(AudioManager.class);
        // Real event times: players detect double/triple clicks from them, and 0 for
        // every press can be read as a multi-click instead of play/pause.
        long now = SystemClock.uptimeMillis();
        audio.dispatchMediaKeyEvent(new KeyEvent(now, now, KeyEvent.ACTION_DOWN, keyCode, 0));
        audio.dispatchMediaKeyEvent(new KeyEvent(now, now, KeyEvent.ACTION_UP, keyCode, 0));
        SignalLog.append(this, "gesture", "direction_flip -> " + KeyEvent.keyCodeToString(keyCode));
    }

    static boolean isPlayPauseGesture(int lastDirection, long lastChangeAt, int direction, long now) {
        return lastChangeAt >= 0 && direction == -lastDirection && now - lastChangeAt <= GESTURE_WINDOW_MS;
    }

    /** Media key for an alternating run of presses that began with firstDirection (+1 or −1). */
    static int gestureKeyCode(int runLength, int firstDirection) {
        if (runLength == 2) {
            return KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE;
        }
        return firstDirection > 0 ? KeyEvent.KEYCODE_MEDIA_NEXT : KeyEvent.KEYCODE_MEDIA_PREVIOUS;
    }

    // About 3 s after playback pauses, Android suspends the A2DP stream and G435 +/− stop
    // reaching the phone, so a resume gesture is never seen. Playing silence keeps the stream up.
    // shortcut: fixed 10 min limit after a gesture pause; make it a setting if the user wants longer.
    private static final long SILENCE_KEEPER_MS = 10 * 60 * 1000;
    private static final int SILENCE_RATE = 44100;
    private final Handler handler = new Handler(Looper.getMainLooper());
    private final Runnable silenceTimeout = this::stopSilenceKeeper;
    private AudioTrack silenceKeeper;

    private void startSilenceKeeper() {
        // One second of 16-bit stereo zeros, looped. No audio focus request, so the paused player keeps its session.
        byte[] silence = new byte[SILENCE_RATE * 4];
        silenceKeeper = new AudioTrack.Builder()
                .setAudioAttributes(new AudioAttributes.Builder()
                        .setUsage(AudioAttributes.USAGE_MEDIA)
                        .setContentType(AudioAttributes.CONTENT_TYPE_MUSIC)
                        .build())
                .setAudioFormat(new AudioFormat.Builder()
                        .setEncoding(AudioFormat.ENCODING_PCM_16BIT)
                        .setSampleRate(SILENCE_RATE)
                        .setChannelMask(AudioFormat.CHANNEL_OUT_STEREO)
                        .build())
                .setTransferMode(AudioTrack.MODE_STATIC)
                .setBufferSizeInBytes(silence.length)
                .build();
        silenceKeeper.write(silence, 0, silence.length);
        silenceKeeper.setLoopPoints(0, SILENCE_RATE, -1);
        silenceKeeper.play();
        handler.postDelayed(silenceTimeout, SILENCE_KEEPER_MS);
        SignalLog.append(this, "silence_keeper", "started");
    }

    private void stopSilenceKeeper() {
        handler.removeCallbacks(silenceTimeout);
        if (silenceKeeper == null) {
            return;
        }
        silenceKeeper.stop();
        silenceKeeper.release();
        silenceKeeper = null;
        SignalLog.append(this, "silence_keeper", "stopped");
    }

    @Override
    protected void onServiceConnected() {
        IntentFilter filter = new IntentFilter(VOLUME_CHANGED_ACTION);
        if (Build.VERSION.SDK_INT >= 33) {
            registerReceiver(volumeReceiver, filter, Context.RECEIVER_NOT_EXPORTED);
        } else {
            registerReceiver(volumeReceiver, filter);
        }
        receiverRegistered = true;
        SignalLog.append(this, "accessibility_status", "service_connected");
    }

    @Override
    public void onDestroy() {
        stopSilenceKeeper();
        if (receiverRegistered) {
            unregisterReceiver(volumeReceiver);
        }
        super.onDestroy();
    }

    @Override
    public void onAccessibilityEvent(AccessibilityEvent event) {
        // Not read: the events only keep Samsung's Freecess from freezing the volume receiver (see the service config).
    }

    @Override
    public void onInterrupt() {
        SignalLog.append(this, "accessibility_status", "service_interrupted");
    }
}
