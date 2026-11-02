package com.g435.signalprobe;

import android.app.Activity;
import android.content.ComponentName;
import android.content.Intent;
import android.content.SharedPreferences;
import android.media.AudioDeviceInfo;
import android.media.AudioManager;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.RadioButton;
import android.view.WindowInsets;
import android.widget.RadioGroup;
import android.widget.ScrollView;
import android.widget.Switch;
import android.widget.TextView;

/** Settings and status; the gestures run in the accessibility service and need no screen. */
public final class MainActivity extends Activity {
    private TextView serviceStatus;
    private TextView headsetStatus;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        // "system" keeps the manifest's AppTheme, which values-night switches with the phone's dark mode.
        String theme = GestureSettings.theme(this);
        if ("light".equals(theme)) {
            setTheme(android.R.style.Theme_Material_Light_NoActionBar);
        } else if ("dark".equals(theme)) {
            setTheme(android.R.style.Theme_Material_NoActionBar);
        }
        super.onCreate(savedInstanceState);
        int padding = (int) (16 * getResources().getDisplayMetrics().density);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(padding, padding, padding, padding);

        serviceStatus = new TextView(this);
        serviceStatus.setTextSize(16);
        root.addView(serviceStatus);
        headsetStatus = new TextView(this);
        headsetStatus.setTextSize(16);
        headsetStatus.setPadding(0, 0, 0, padding);
        root.addView(headsetStatus);

        SharedPreferences prefs = GestureSettings.prefs(this);
        Switch enabled = addSwitch(root, prefs, GestureSettings.ENABLED, GestureSettings.enabled(this),
                "제스처 사용", null);
        Switch skip = addSwitch(root, prefs, GestureSettings.SKIP, GestureSettings.skip(this),
                "곡 넘기기 사용 (+−+ 다음 곡, −+− 이전 곡)",
                "끄면 +− / −+ 재생/일시정지가 1초 기다리지 않고 바로 실행됩니다.");
        Switch forever = addSwitch(root, prefs, GestureSettings.SILENCE_FOREVER, GestureSettings.silenceForever(this),
                "일시정지 중 무음을 계속 유지 (끄면 10분)",
                "무음이 꺼지면 몇 초 뒤부터 G435 버튼으로 재개할 수 없습니다.");
        skip.setEnabled(enabled.isChecked());
        forever.setEnabled(enabled.isChecked());
        enabled.setOnCheckedChangeListener((view, checked) -> {
            prefs.edit().putBoolean(GestureSettings.ENABLED, checked).apply();
            skip.setEnabled(checked);
            forever.setEnabled(checked);
        });

        TextView themeLabel = new TextView(this);
        themeLabel.setText("화면 테마");
        themeLabel.setPadding(0, padding, 0, 0);
        root.addView(themeLabel);
        String[] themes = {"system", "light", "dark"};
        String[] themeNames = {"시스템 설정 따름", "라이트", "다크"};
        RadioGroup themeGroup = new RadioGroup(this);
        for (int i = 0; i < themes.length; i++) {
            RadioButton option = new RadioButton(this);
            option.setId(i + 1);
            option.setText(themeNames[i]);
            option.setChecked(themes[i].equals(theme));
            themeGroup.addView(option);
        }
        themeGroup.setOnCheckedChangeListener((group, id) -> {
            prefs.edit().putString(GestureSettings.THEME, themes[id - 1]).apply();
            recreate();
        });
        root.addView(themeGroup);

        TextView usage = new TextView(this);
        usage.setText("+− 또는 −+ : 재생/일시정지\n+−+ : 다음 곡\n−+− : 이전 곡\n곡을 넘기면 볼륨은 원래대로 돌아갑니다.");
        usage.setPadding(0, padding, 0, padding);
        root.addView(usage);

        Button settings = new Button(this);
        settings.setText("접근성 설정 열기");
        settings.setOnClickListener(v -> startActivity(new Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)));
        root.addView(settings);

        // targetSdk 35 draws edge to edge, so without this the status bar covered the first line.
        root.setOnApplyWindowInsetsListener((view, insets) -> {
            int top;
            int bottom;
            if (Build.VERSION.SDK_INT >= 30) {
                android.graphics.Insets bars = insets.getInsets(WindowInsets.Type.systemBars());
                top = bars.top;
                bottom = bars.bottom;
            } else {
                top = insets.getSystemWindowInsetTop();
                bottom = insets.getSystemWindowInsetBottom();
            }
            view.setPadding(padding, padding + top, padding, padding + bottom);
            return insets;
        });
        ScrollView scroll = new ScrollView(this);
        scroll.addView(root);
        setContentView(scroll);
    }

    private Switch addSwitch(LinearLayout root, SharedPreferences prefs, String key, boolean checked,
                             String label, String note) {
        Switch view = new Switch(this);
        view.setText(label);
        view.setChecked(checked);
        view.setOnCheckedChangeListener((v, on) -> prefs.edit().putBoolean(key, on).apply());
        root.addView(view);
        if (note != null) {
            TextView noteView = new TextView(this);
            noteView.setText(note);
            noteView.setAlpha(0.7f);
            noteView.setPadding(0, 0, 0, (int) (12 * getResources().getDisplayMetrics().density));
            root.addView(noteView);
        }
        return view;
    }

    @Override
    protected void onResume() {
        super.onResume();
        serviceStatus.setText("접근성 서비스: " + (isServiceEnabled() ? "켜짐" : "꺼짐 — 아래 버튼으로 켜 주세요"));
        headsetStatus.setText("G435: " + (isG435Connected() ? "연결됨" : "연결 안 됨"));
    }

    private boolean isServiceEnabled() {
        String enabled = Settings.Secure.getString(getContentResolver(), Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES);
        String service = new ComponentName(this, G435AccessibilityService.class).flattenToString();
        return enabled != null && enabled.contains(service);
    }

    private boolean isG435Connected() {
        for (AudioDeviceInfo device : getSystemService(AudioManager.class).getDevices(AudioManager.GET_DEVICES_OUTPUTS)) {
            if (device.getType() == AudioDeviceInfo.TYPE_BLUETOOTH_A2DP
                    && G435AccessibilityService.isG435Name(device.getProductName())) {
                return true;
            }
        }
        return false;
    }
}
