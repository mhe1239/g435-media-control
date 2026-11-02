namespace G435MediaGesture;

static class Program
{
    [STAThread]
    static int Main(string[] args)
    {
        if (args.Contains("--self-test"))
            return Gesture.SelfTest();

        // Same name as the Python listener's mutex: two listeners would each toggle on one gesture and cancel out.
        using var mutex = new Mutex(false, @"Local\G435MediaGesture", out bool created);
        if (!created)
        {
            MessageBox.Show("G435 미디어 제스처가 이미 실행 중입니다.", "G435 미디어 제스처");
            return 1;
        }

        ApplicationConfiguration.Initialize();
        var settings = Settings.Load();
        Application.SetColorMode(settings.Theme);
        using var engine = new GestureEngine(settings);
        string? deviceName = null;
        SettingsForm form = null!;
        SynchronizationContext ui = null!;

        // The color mode applies to forms created after it is set, so a theme change rebuilds the window.
        SettingsForm CreateForm() => new SettingsForm(settings, engine.SettingsChanged, () => ui.Post(_ =>
        {
            Application.SetColorMode(settings.Theme);
            var old = form;
            form = CreateForm();
            form.StartPosition = FormStartPosition.Manual;
            form.Location = old.Location;
            form.SetDevice(deviceName);
            old.Dispose();
            ShowSettings();
        }, null));
        // Creating the form installs the WinForms synchronization context used to marshal device updates.
        form = CreateForm();
        ui = SynchronizationContext.Current!;
        using var tray = new NotifyIcon { Icon = SystemIcons.Application, Text = "G435 미디어 제스처", Visible = true };

        void ShowSettings()
        {
            form.Show();
            form.Activate();
        }
        tray.DoubleClick += (_, _) => ShowSettings();
        tray.ContextMenuStrip = new ContextMenuStrip();
        tray.ContextMenuStrip.Items.Add("설정", null, (_, _) => ShowSettings());
        tray.ContextMenuStrip.Items.Add("종료", null, (_, _) => Application.Exit());

        engine.DeviceChanged += name => ui.Post(_ =>
        {
            deviceName = name;
            form.SetDevice(name);
            tray.Text = name == null ? "G435 미디어 제스처 — 연결 안 됨" : "G435 미디어 제스처 — 연결됨";
        }, null);
        engine.Start();

        // Started by Windows at sign-in it stays in the tray; started by hand it shows the settings.
        if (!args.Contains("--background"))
            ShowSettings();
        Application.Run();
        tray.Visible = false;
        form.Dispose();
        return 0;
    }
}
