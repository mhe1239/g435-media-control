using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Text.Json;
using NAudio.CoreAudioApi;
using NAudio.Wave;
using Windows.Media.Control;

namespace G435MediaGesture;

/// <summary>
/// Watches for the G435 as the default output, reads its +/− volume steps and sends media actions.
/// All Core Audio objects are created and used on thread-pool (MTA) threads, never the UI thread.
/// </summary>
sealed class GestureEngine : IDisposable
{
    // shortcut: polls the default output every 2 s instead of listening for endpoint events; fine for a connect check.
    const int WatchIntervalMs = 2000;
    const int SilenceKeeperMs = 10 * 60 * 1000;

    readonly Settings settings;
    readonly object gate = new();
    readonly Stopwatch clock = Stopwatch.StartNew();
    readonly System.Threading.Timer watchTimer;
    MMDeviceEnumerator? enumerator;
    MMDevice? device;
    AudioEndpointVolume? volume;
    GlobalSystemMediaTransportControlsSessionManager? sessions;
    bool disposed;

    // Gesture state, guarded by gate.
    float level;
    readonly List<int> run = [];
    double? lastChangeAt;
    float runStartLevel;
    float? restoring; // a skip leaves the volume one step off; restoring it fires one change that is not a press
    int generation;   // bumped on every press so a stale play/pause timer can tell it lost the race

    // Silence keeper, guarded by silenceGate. Never held together with gate: closing the stream fires the
    // volume callback, which waits on gate, so stopping under gate could deadlock as the Python one did.
    readonly object silenceGate = new();
    WasapiOut? silence;
    System.Threading.Timer? silenceTimer;

    public event Action<string?>? DeviceChanged; // G435 endpoint name, or null when it is not the default output

    public GestureEngine(Settings settings)
    {
        this.settings = settings;
        watchTimer = new System.Threading.Timer(_ => Watch(), null, Timeout.Infinite, Timeout.Infinite);
    }

    public void Start() => watchTimer.Change(0, Timeout.Infinite);

    /// <summary>Call after a settings change.</summary>
    public void SettingsChanged()
    {
        if (settings.Enabled)
            return;
        lock (gate)
        {
            run.Clear();
            generation++;
        }
        StopSilence();
    }

    void Watch()
    {
        try
        {
            enumerator ??= new MMDeviceEnumerator();
            MMDevice? current = enumerator.HasDefaultAudioEndpoint(DataFlow.Render, Role.Multimedia)
                ? enumerator.GetDefaultAudioEndpoint(DataFlow.Render, Role.Multimedia)
                : null;
            // A Bluetooth headset only appears as an output while it is connected, so this is the connection check.
            // shortcut: watches the default output only, like the tested Python listener; pick the G435 endpoint
            // by name if the user keeps another device as default.
            bool isG435 = current?.FriendlyName.Contains("G435", StringComparison.OrdinalIgnoreCase) == true;
            if (isG435 && current!.ID != device?.ID)
                Attach(current);
            else if (!isG435 && device != null)
                Detach();
        }
        catch (Exception e)
        {
            Log("watch_error", new { message = e.Message });
        }
        finally
        {
            lock (gate)
                if (!disposed)
                    watchTimer.Change(WatchIntervalMs, Timeout.Infinite);
        }
    }

    void Attach(MMDevice newDevice)
    {
        Detach();
        lock (gate)
        {
            device = newDevice;
            volume = newDevice.AudioEndpointVolume;
            level = volume.MasterVolumeLevelScalar;
            run.Clear();
            restoring = null;
            volume.OnVolumeNotification += OnVolume;
        }
        // The first media-session call took ~1 s and a press landed before the toggle; pay it up front.
        try { sessions = GlobalSystemMediaTransportControlsSessionManager.RequestAsync().AsTask().GetAwaiter().GetResult(); }
        catch (Exception e) { Log("media_sessions_error", new { message = e.Message }); }
        Log("attached", new { name = newDevice.FriendlyName, level });
        DeviceChanged?.Invoke(newDevice.FriendlyName);
    }

    void Detach()
    {
        lock (gate)
        {
            if (device == null)
                return;
            if (volume != null)
                volume.OnVolumeNotification -= OnVolume;
            volume = null;
            generation++;
        }
        StopSilence();
        lock (gate)
        {
            device?.Dispose();
            device = null;
        }
        Log("detached", null);
        DeviceChanged?.Invoke(null);
    }

    void OnVolume(AudioVolumeNotificationData data)
    {
        double now = clock.Elapsed.TotalSeconds;
        float value = data.MasterVolume;
        lock (gate)
        {
            float previous = level;
            level = value;
            int direction = Math.Sign(value - previous);
            Log("volume", new { previous, value, context = data.EventContext });
            if (direction == 0)
                return;
            if (restoring is float target && Math.Abs(value - target) < 1e-4)
            {
                restoring = null;
                return;
            }
            if (!settings.Enabled)
                return;

            int gen = ++generation; // also invalidates a pending play/pause timer
            if (run.Count > 0 && Gesture.IsFlip(run[^1], lastChangeAt, direction, now))
                run.Add(direction);
            else
            {
                run.Clear();
                run.Add(direction);
                runStartLevel = previous;
            }
            lastChangeAt = now;

            // Stopping the silence closes a stream, which fires this callback again; doing that inside the
            // callback deadlocked the Python listener (2026-11-01), so every action runs on another thread.
            if (run.Count == 3 || (run.Count == 2 && !settings.SkipEnabled))
            {
                MediaAction action = Gesture.ActionFor(run);
                float? restoreTo = action == MediaAction.PlayPause ? null : runStartLevel;
                restoring = restoreTo;
                run.Clear();
                Task.Run(() => Act(action, restoreTo));
            }
            else if (run.Count == 2)
            {
                Task.Delay(Gesture.ThirdPressWaitMs).ContinueWith(_ =>
                {
                    lock (gate)
                    {
                        if (gen != generation || run.Count != 2)
                            return;
                        run.Clear();
                    }
                    Act(MediaAction.PlayPause, null);
                });
            }
        }
    }

    void Act(MediaAction action, float? restoreTo)
    {
        Log("gesture", new { action = action.ToString(), via = Send(action) });
        if (restoreTo is float target)
        {
            Thread.Sleep(Gesture.RestoreDelayMs);
            AudioEndpointVolume? targetVolume;
            lock (gate)
                targetVolume = volume;
            // Set outside gate: the change fires OnVolume, which takes gate.
            if (targetVolume != null)
                targetVolume.MasterVolumeLevelScalar = target;
            Log("volume_restored", new { value = target });
        }
        // Decide from the state after the action: the state read before it lagged for Spotify.
        Thread.Sleep(1000 - (restoreTo is null ? 0 : Gesture.RestoreDelayMs));
        string? status = PlaybackStatus();
        Log("media_state", new { status });
        if (status == "Paused")
            StartSilence();
        else
            StopSilence();
    }

    string Send(MediaAction action)
    {
        try
        {
            var current = sessions?.GetCurrentSession();
            if (current != null)
            {
                var call = action switch
                {
                    MediaAction.Next => current.TrySkipNextAsync(),
                    MediaAction.Previous => current.TrySkipPreviousAsync(),
                    _ => current.TryTogglePlayPauseAsync(),
                };
                if (call.AsTask().GetAwaiter().GetResult())
                    return "session";
            }
        }
        catch (Exception e)
        {
            Log("media_sessions_error", new { message = e.Message });
        }
        // Without the extended flag and scan code, Chrome's media session ignored the key (tested 2026-11-01).
        (byte vk, byte scan) = action switch
        {
            MediaAction.Next => ((byte)0xB0, (byte)0x19),
            MediaAction.Previous => ((byte)0xB1, (byte)0x10),
            _ => ((byte)0xB3, (byte)0x22),
        };
        keybd_event(vk, scan, KEYEVENTF_EXTENDEDKEY, 0);
        keybd_event(vk, scan, KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP, 0);
        return "media_key";
    }

    string? PlaybackStatus()
    {
        try { return sessions?.GetCurrentSession()?.GetPlaybackInfo().PlaybackStatus.ToString(); }
        catch { return null; }
    }

    // About 10 s after playback pauses, G435 +/− stop reaching Windows (tested 2026-11-01), so a resume
    // gesture is never seen. Playing silence to the G435 keeps the Bluetooth stream up.
    void StartSilence()
    {
        MMDevice? target;
        lock (gate)
            target = device;
        lock (silenceGate)
        {
            if (silence != null || target == null)
                return;
            silence = new WasapiOut(target, AudioClientShareMode.Shared, false, 200);
            silence.Init(new SilenceProvider(target.AudioClient.MixFormat));
            silence.Play();
            if (!settings.SilenceForever)
                silenceTimer = new System.Threading.Timer(_ => StopSilence(), null, SilenceKeeperMs, Timeout.Infinite);
        }
        Log("silence_keeper", new { action = "started", forever = settings.SilenceForever });
    }

    void StopSilence()
    {
        lock (silenceGate)
        {
            silenceTimer?.Dispose();
            silenceTimer = null;
            if (silence == null)
                return;
            silence.Stop();
            silence.Dispose();
            silence = null;
        }
        Log("silence_keeper", new { action = "stopped" });
    }

    public void Dispose()
    {
        lock (gate)
        {
            disposed = true;
            watchTimer.Dispose();
        }
        Detach();
        enumerator?.Dispose();
    }

    // Volume steps and gesture results only, for diagnosing missed gestures.
    // shortcut: the log is never rotated; add a size cap if it grows past a few MB.
    static readonly string LogPath = Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "G435MediaGesture", "log.jsonl");
    static readonly object LogGate = new();

    static void Log(string kind, object? fields)
    {
        string line = JsonSerializer.Serialize(new { time = DateTimeOffset.Now.ToString("O"), kind, fields });
        lock (LogGate)
        {
            try
            {
                Directory.CreateDirectory(Path.GetDirectoryName(LogPath)!);
                File.AppendAllText(LogPath, line + "\n");
            }
            catch
            {
                // Logging must never break the gesture.
            }
        }
    }

    const uint KEYEVENTF_EXTENDEDKEY = 0x0001;
    const uint KEYEVENTF_KEYUP = 0x0002;

    [DllImport("user32.dll")]
    static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, nuint dwExtraInfo);
}
