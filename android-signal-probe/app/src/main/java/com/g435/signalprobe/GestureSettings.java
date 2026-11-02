package com.g435.signalprobe;

import android.content.Context;
import android.content.SharedPreferences;

/** User options shared by the settings screen and the service; the same choices as the Windows app. */
final class GestureSettings {
    static final String ENABLED = "enabled";
    static final String SKIP = "skip";
    static final String SILENCE_FOREVER = "silence_forever";
    static final String KEEP_ALIVE = "keep_alive";
    /** Minutes after midnight; keep-alive is off in [start, end) so an unused headset can power off at night. */
    static final String QUIET_START = "quiet_start";
    static final String QUIET_END = "quiet_end";
    static final int DEFAULT_QUIET_START = 0;
    static final int DEFAULT_QUIET_END = 6 * 60;
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

    static int quietStart(Context context) {
        return prefs(context).getInt(QUIET_START, DEFAULT_QUIET_START);
    }

    static int quietEnd(Context context) {
        return prefs(context).getInt(QUIET_END, DEFAULT_QUIET_END);
    }
}
