package com.g435.signalprobe;

import android.content.Context;
import android.content.SharedPreferences;

/** User options shared by the settings screen and the service; the same choices as the Windows app. */
final class GestureSettings {
    static final String ENABLED = "enabled";
    static final String SKIP = "skip";
    static final String SILENCE_FOREVER = "silence_forever";
    static final String KEEP_ALIVE = "keep_alive";
    /** "system", "light" or "dark". */
    static final String THEME = "theme";

    private GestureSettings() {
    }

    static SharedPreferences prefs(Context context) {
        return context.getSharedPreferences("settings", Context.MODE_PRIVATE);
    }

    static boolean enabled(Context context) {
        return prefs(context).getBoolean(ENABLED, true);
    }

    static boolean skip(Context context) {
        return prefs(context).getBoolean(SKIP, true);
    }

    static String theme(Context context) {
        return prefs(context).getString(THEME, "system");
    }

    static boolean silenceForever(Context context) {
        return prefs(context).getBoolean(SILENCE_FOREVER, false);
    }

    static boolean keepAlive(Context context) {
        return prefs(context).getBoolean(KEEP_ALIVE, false);
    }
}
