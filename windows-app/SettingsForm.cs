namespace G435MediaGesture;

/// <summary>The one settings window; closing it only hides it, the app keeps running in the tray.</summary>
sealed class SettingsForm : Form
{
    readonly Label status = new() { AutoSize = true };

    public SettingsForm(Settings settings, Action changed, Action themeChanged)
    {
        Text = "G435 미디어 제스처";
        FormBorderStyle = FormBorderStyle.FixedDialog;
        MaximizeBox = false;
        AutoSize = true;
        AutoSizeMode = AutoSizeMode.GrowAndShrink;
        StartPosition = FormStartPosition.CenterScreen;
        Icon = new Icon(typeof(SettingsForm).Assembly.GetManifestResourceStream("g435.ico")!);

        var enabled = new CheckBox { Text = "제스처 사용", Checked = settings.Enabled, AutoSize = true };
        var skip = new CheckBox { Text = "곡 넘기기 사용 (+−+ 다음 곡, −+− 이전 곡)", Checked = settings.SkipEnabled, AutoSize = true };
        var skipNote = new Label { Text = "끄면 +− / −+ 재생/일시정지가 1초 기다리지 않고 바로 실행됩니다.", AutoSize = true, ForeColor = SystemColors.GrayText };
        var forever = new CheckBox { Text = "일시정지 중 무음을 계속 유지 (끄면 10분)", Checked = settings.SilenceForever, AutoSize = true };
        var foreverNote = new Label { Text = "무음이 꺼지면 약 10초 뒤부터 G435 버튼으로 재개할 수 없습니다.", AutoSize = true, ForeColor = SystemColors.GrayText };
        var keepAlive = new CheckBox { Text = "G435 자동 꺼짐 방지 (20분마다 무음 10초)", Checked = settings.KeepAlive, AutoSize = true };
        var keepAliveNote = new Label { Text = "G435는 30분 동안 쓰지 않으면 꺼집니다.", AutoSize = true, ForeColor = SystemColors.GrayText };
        var theme = new ComboBox { DropDownStyle = ComboBoxStyle.DropDownList, Width = 200 };
        SystemColorMode[] modes = [SystemColorMode.System, SystemColorMode.Classic, SystemColorMode.Dark];
        theme.Items.AddRange(["시스템 설정 따름", "라이트", "다크"]);
        theme.SelectedIndex = Array.IndexOf(modes, settings.Theme) is int i and >= 0 ? i : 0;
        theme.SelectedIndexChanged += (_, _) =>
        {
            settings.Theme = modes[theme.SelectedIndex];
            settings.Save();
            themeChanged();
        };
        var themeLabel = new Label { Text = "화면 테마", AutoSize = true };
        var startup = new CheckBox { Text = "Windows 시작 시 실행", Checked = Settings.StartWithWindows, AutoSize = true };

        void Apply()
        {
            settings.Enabled = enabled.Checked;
            settings.SkipEnabled = skip.Checked;
            settings.SilenceForever = forever.Checked;
            settings.KeepAlive = keepAlive.Checked;
            skip.Enabled = forever.Enabled = keepAlive.Enabled = enabled.Checked;
            settings.Save();
            changed();
        }
        enabled.CheckedChanged += (_, _) => Apply();
        skip.CheckedChanged += (_, _) => Apply();
        forever.CheckedChanged += (_, _) => Apply();
        keepAlive.CheckedChanged += (_, _) => Apply();
        startup.CheckedChanged += (_, _) => Settings.StartWithWindows = startup.Checked;
        skip.Enabled = forever.Enabled = keepAlive.Enabled = enabled.Checked;

        var layout = new FlowLayoutPanel
        {
            FlowDirection = FlowDirection.TopDown,
            AutoSize = true,
            AutoSizeMode = AutoSizeMode.GrowAndShrink,
            Padding = new Padding(16),
            WrapContents = false,
        };
        layout.Controls.AddRange([status, enabled, skip, skipNote, forever, foreverNote, keepAlive, keepAliveNote, startup, themeLabel, theme]);
        foreach (Control c in layout.Controls)
            c.Margin = new Padding(0, 0, 0, c is Label && c != status && c != themeLabel ? 12 : 6);
        status.Margin = new Padding(0, 0, 0, 12);
        Controls.Add(layout);
        SetDevice(null);
    }

    public void SetDevice(string? name) =>
        status.Text = name == null ? "G435: 연결 안 됨 (기본 출력이 아님)" : $"G435: 연결됨 — {name}";

    protected override void OnFormClosing(FormClosingEventArgs e)
    {
        if (e.CloseReason == CloseReason.UserClosing)
        {
            e.Cancel = true;
            Hide();
        }
        base.OnFormClosing(e);
    }
}
