package com.g435.signalprobe;

import android.app.Activity;
import android.content.ComponentName;
import android.content.Intent;
import android.os.Bundle;
import android.provider.Settings;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

/** Shows whether the gesture service is on and opens accessibility settings; the gestures need no screen. */
public final class MainActivity extends Activity {
    private TextView statusView;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        int padding = (int) (16 * getResources().getDisplayMetrics().density);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(padding, padding, padding, padding);

        TextView usage = new TextView(this);
        usage.setTextSize(16);
        usage.setText("G435 +/− 버튼 제스처 (Bluetooth)\n\n"
                + "+− 또는 −+ : 재생/일시정지\n"
                + "+−+ : 다음 곡\n"
                + "−+− : 이전 곡\n\n"
                + "접근성 서비스를 켜 두면 이 화면을 닫아도 동작합니다.");
        root.addView(usage);

        statusView = new TextView(this);
        statusView.setTextSize(16);
        statusView.setPadding(0, padding, 0, padding);
        root.addView(statusView);

        Button settings = new Button(this);
        settings.setText("접근성 설정 열기");
        settings.setOnClickListener(v -> startActivity(new Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)));
        root.addView(settings);

        setContentView(root);
    }

    @Override
    protected void onResume() {
        super.onResume();
        statusView.setText("접근성 서비스: " + (isServiceEnabled() ? "켜짐" : "꺼짐"));
    }

    private boolean isServiceEnabled() {
        String enabled = Settings.Secure.getString(getContentResolver(), Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES);
        String service = new ComponentName(this, G435AccessibilityService.class).flattenToString();
        return enabled != null && enabled.contains(service);
    }
}
