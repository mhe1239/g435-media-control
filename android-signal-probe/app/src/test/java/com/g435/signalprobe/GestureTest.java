package com.g435.signalprobe;

import static com.g435.signalprobe.G435AccessibilityService.GESTURE_WINDOW_MS;
import static com.g435.signalprobe.G435AccessibilityService.gestureKeyCode;
import static com.g435.signalprobe.G435AccessibilityService.isPlayPauseGesture;
import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

import android.view.KeyEvent;
import org.junit.Test;

public class GestureTest {
    @Test
    public void directionFlipWithinWindowIsPlayPause() {
        assertTrue(isPlayPauseGesture(1, 1000, -1, 1000 + GESTURE_WINDOW_MS));
        assertTrue(isPlayPauseGesture(-1, 1000, 1, 1500));
        assertFalse(isPlayPauseGesture(1, 1000, -1, 1001 + GESTURE_WINDOW_MS));
        assertFalse(isPlayPauseGesture(1, 1000, 1, 1500));
        assertFalse(isPlayPauseGesture(1, -1, -1, 1000));
    }

    @Test
    public void runLengthPicksMediaKey() {
        assertEquals(KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE, gestureKeyCode(2, 1));
        assertEquals(KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE, gestureKeyCode(2, -1));
        assertEquals(KeyEvent.KEYCODE_MEDIA_NEXT, gestureKeyCode(3, 1));
        assertEquals(KeyEvent.KEYCODE_MEDIA_PREVIOUS, gestureKeyCode(3, -1));
    }
}
