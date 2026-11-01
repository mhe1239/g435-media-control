package com.g435.signalprobe;

import android.content.Context;

import java.io.File;
import java.io.FileOutputStream;
import java.nio.charset.StandardCharsets;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

final class SignalLog {
    private static final String FILE_NAME = "g435-signal-log.jsonl";

    private SignalLog() {
    }

    // Gesture and volume-step log for diagnosing missed gestures; read with adb run-as.
    static synchronized void append(Context context, String kind, String detail) {
        String timestamp = new SimpleDateFormat(
                "yyyy-MM-dd'T'HH:mm:ss.SSSXXX", Locale.getDefault()).format(new Date());
        String json = "{\"time\":\"" + escapeJson(timestamp)
                + "\",\"kind\":\"" + escapeJson(kind)
                + "\",\"detail\":\"" + escapeJson(detail) + "\"}\n";
        File file = new File(context.getFilesDir(), FILE_NAME);
        try (FileOutputStream output = new FileOutputStream(file, true)) {
            output.write(json.getBytes(StandardCharsets.UTF_8));
        } catch (Exception ignored) {
            // Logging must never break the gesture.
        }
    }

    private static String escapeJson(String value) {
        return value.replace("\\", "\\\\").replace("\"", "\\\"");
    }
}
