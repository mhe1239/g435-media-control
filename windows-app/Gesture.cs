namespace G435MediaGesture;

/// <summary>Turns alternating G435 +/− volume steps into media actions; values tested with the Python listener.</summary>
static class Gesture
{
    // shortcut: fixed window copied from Android, tune it if the user reports missed or false gestures.
    public const double WindowS = 1.5;
    // When playback starts Windows re-syncs the volume as an up/down pair ~15 ms apart, which is no human press.
    public const double MinFlipS = 0.05;
    // A two-press flip waits this long for a third press before it counts as play/pause.
    public const int ThirdPressWaitMs = 1000;
    // Restoring right after the third press was undone by the G435 resending its own level ~13 ms later (2026-11-02).
    public const int RestoreDelayMs = 500;

    public static bool IsFlip(int lastDirection, double? lastChangeAt, int direction, double now) =>
        lastChangeAt is double at && direction == -lastDirection && now - at >= MinFlipS && now - at <= WindowS;

    public static MediaAction ActionFor(IReadOnlyList<int> run) =>
        run.Count == 2 ? MediaAction.PlayPause : run[0] > 0 ? MediaAction.Next : MediaAction.Previous;

    public static int SelfTest()
    {
        static void Check(bool ok, string what) { if (!ok) throw new Exception("self-test failed: " + what); }
        Check(IsFlip(1, 1.0, -1, 1.0 + WindowS), "flip at window edge");
        Check(IsFlip(-1, 1.0, 1, 1.5), "−+ flip");
        Check(!IsFlip(1, 1.0, -1, 1.01 + WindowS), "too slow");
        Check(!IsFlip(1, 1.0, 1, 1.5), "same direction");
        Check(!IsFlip(1, null, -1, 1.0), "no previous press");
        Check(!IsFlip(1, 1.0, -1, 1.014), "re-sync pair");
        Check(ActionFor([1, -1]) == MediaAction.PlayPause && ActionFor([-1, 1]) == MediaAction.PlayPause, "play/pause");
        Check(ActionFor([1, -1, 1]) == MediaAction.Next, "next");
        Check(ActionFor([-1, 1, -1]) == MediaAction.Previous, "previous");
        Check(InQuietHours(0, 360, 0) && InQuietHours(0, 360, 359) && !InQuietHours(0, 360, 360), "00:00–06:00");
        Check(InQuietHours(1380, 360, 1439) && InQuietHours(1380, 360, 10) && !InQuietHours(1380, 360, 720), "past midnight");
        Check(!InQuietHours(0, 0, 0), "start == end is off");
        return 0;
    }

    /// <summary>Whether minute-of-day now falls in [start, end), wrapping past midnight; start == end means never.</summary>
    public static bool InQuietHours(int start, int end, int now) =>
        start <= end ? now >= start && now < end : now >= start || now < end;
}

enum MediaAction { PlayPause, Next, Previous }
