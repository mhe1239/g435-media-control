using System.Text.Json;
using Microsoft.Win32;

namespace G435MediaGesture;

sealed class Settings
{
    public bool Enabled { get; set; } = true;
    public bool SkipEnabled { get; set; } = true;
    public bool SilenceForever { get; set; }
    public bool KeepAlive { get; set; }
    // Minutes after midnight; keep-alive is off in [start, end) so an unused headset can power off at night.
    public int QuietStartMinutes { get; set; }
    public int QuietEndMinutes { get; set; } = 6 * 60;
    // Classic is the light theme.
    public SystemColorMode Theme { get; set; } = SystemColorMode.System;

    static readonly string Dir = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "G435MediaGesture");
    static readonly string FilePath = Path.Combine(Dir, "settings.json");

    public static Settings Load()
    {
        try
        {
            return JsonSerializer.Deserialize<Settings>(File.ReadAllText(FilePath)) ?? new Settings();
        }
        catch
        {
            return new Settings();
        }
    }

    public void Save()
    {
        Directory.CreateDirectory(Dir);
        File.WriteAllText(FilePath, JsonSerializer.Serialize(this));
    }

    const string RunKey = @"Software\Microsoft\Windows\CurrentVersion\Run";
    const string RunName = "G435MediaGesture";

    // Kept in the registry, not the JSON, so it always matches what Windows will actually start.
    public static bool StartWithWindows
    {
        get
        {
            using var key = Registry.CurrentUser.OpenSubKey(RunKey);
            return key?.GetValue(RunName) is string;
        }
        set
        {
            using var key = Registry.CurrentUser.CreateSubKey(RunKey);
            if (value)
                key.SetValue(RunName, $"\"{Environment.ProcessPath}\" --background");
            else
                key.DeleteValue(RunName, false);
        }
    }
}
