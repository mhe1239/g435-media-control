# 작업 기록 - Windows C# 앱과 두 앱의 설정

- 기록 일시: 2026-11-02 13:45 (Asia/Seoul)
- 실제 작업 시각: 2026-11-02 00:30–13:41 (앱 로그와 화면 캡처 기준)
- 작성자/에이전트: Claude
- 작업 유형: 구현

## 요약

Windows의 Python 리스너를 C# 트레이 앱으로 옮기고, Windows와 Android 앱에 같은 설정을 넣었다. 설정은 제스처 사용, 곡 넘기기 사용, 일시정지 중 무음 계속 유지, 화면 테마(시스템/라이트/다크)다. 두 앱 모두 G435가 연결돼 있을 때만 동작한다. 사용자가 두 앱의 모든 항목을 실기기에서 확인했다(tested).

## 변경 범위와 주요 파일

- 추가: [windows-app/](../../windows-app). .NET 10, WinForms, NAudio.Wasapi. `--self-test`로 제스처 판정을 확인한다.
  - `GestureEngine.cs`: 기본 출력 2초 폴링으로 G435 감지, 제스처, 미디어 세션, 무음 유지(WASAPI), 볼륨 복원.
  - `SettingsForm.cs`, `Settings.cs`: 설정 창과 `%APPDATA%\G435MediaGesture\settings.json`, Windows 시작 시 실행(HKCU Run).
- 수정: Android `G435AccessibilityService.java`(설정 반영, G435 A2DP 확인, 복원 0.5초 지연), `MainActivity.java`(설정 화면, 테마, 상태 표시줄 여백), `GestureSettings.java`(추가), `values/themes.xml`, `values-night/themes.xml`.
- `g435_media_gesture.py`는 남겨 두었다. 같은 이름의 뮤텍스를 써서 C# 앱과 동시에 실행되지 않는다.

## 관측과 검증

| 시각 | 관측 | 판단 |
|---|---|---|
| 13:26:41–13:27:24 | Android에서 곡 넘김 직후 `−+−`가 일시정지로 바뀜 5회. 첫 `−`가 `7→7`로 도착했다 | 원인: 폰만 시작 볼륨으로 돌아가고 G435는 한 단계 위에 남았다(13:27:21 `7→9`). 복원을 0.5초 늦췄다 |
| 13:30:39–13:30:54 | 곡 넘김 직후 `−+−`, `+−` 정상 | tested: 사용자 확인 |
| 13:24–13:28 | Android 곡 넘기기 끔 → `+−` 즉시 재생/일시정지(13:28:05), 제스처 끔 → 무반응(13:28:18 이후), 폰 볼륨 키 무시 | tested: 사용자 확인 |
| 13:31–13:40 | Windows C# 앱: 연결 감지, 세 제스처, 볼륨 복원, 20초 넘게 정지 후 재개, 곡 넘기기 끔, 제스처 끔, 다크 모드 | tested: 사용자 확인 |
| 13:41 | 두 앱의 테마 선택. Android 화면이 상태 표시줄 아래에서 시작 | tested: 사용자 확인, Android 화면 캡처 |

## 리스크/이슈

- 곡 넘김 뒤 0.5초 안에 볼륨을 다시 누르면 그 조절은 시작 볼륨으로 덮어써진다(Android 13:30:26 관측).
- Windows는 G435가 **기본 출력**일 때만 동작한다. Android는 Bluetooth 이름에 "G435"가 있어야 한다.
- Windows 무음 유지를 winsound에서 WASAPI로 바꿨다. 20초 정지 후 재개는 확인했지만 10분 한계나 계속 유지는 길게 시험하지 않았다.
- Windows 앱 로그(`%LOCALAPPDATA%\G435MediaGesture\log.jsonl`)는 순환하지 않는다.
- 서명하지 않은 실행 파일이다. 배포용 단일 파일(.exe) 게시는 하지 않았다.

## 다음 작업과 참고

- 며칠 실사용: 오인식, 밤새 둔 뒤 Android 동작, Windows 시작 시 실행.
- 이전 보고서: [Windows 제스처](261101-2312-11-windows-play-pause-gesture.md), [Android 제스처](261031-2341-09-android-play-pause-gesture.md).
