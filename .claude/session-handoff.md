# Session handoff

- Updated: 2026-11-02 13:45 (Asia/Seoul)
- Objective: Bluetooth G435 버튼으로 갤럭시 재생/일시정지를 제어하고(1순위), 이후 다음/이전 곡·알림 읽기를 검토한다.
- Status: in progress

## Current state

- tested (SM-S916N / Android 16, Bluetooth, Samsung Music): G435 +/−를 1.5초 안에 반대로 누르면(+→− 또는 −→+) 재생/일시정지된다. 2026-10-31 23:39–23:40 정지·재개 4회 왕복 모두 성공.
- tested (23:51–23:57): AudioSeeker 12회(1회 −가 늦게 도착해 미인식), Chrome 6회, Brave 4회 모두 해당 앱으로 전달·성공. YouTube는 사용자가 쓰지 않아 제외.
- 일시정지 중에는 무음 `AudioTrack`을 최대 10분 재생해야 재개 제스처가 폰에 도착한다. A2DP가 쉬면 G435 +/−가 폰에 도착하지 않기 때문이다.
- G435 음소거·전원 버튼(짧게)은 재생 중에도 폰에 아무 패킷도 보내지 않는다(2026-11-01 HCI snoop으로 확인, [보고서](../docs/reports/261101-1605-10-android-power-mic-hci.md)). 폰이 받는 입력은 +/− 절대 볼륨뿐이다. G435 최대는 폰 볼륨 11/15, Windows 69%다.
- tested (Windows 11, Bluetooth, 2026-11-01): `g435_media_gesture.py`로 같은 +/− 방향 전환 제스처가 작동한다. 현재 SMTC 세션 토글 방식으로 Spotify(23:16–23:17) 11회, Chrome(23:23–23:33, −→+ 포함) 성공, 14–26초 정지 후 재개 확인. 첫 SMTC 호출이 약 1초 걸려 시작 시 미리 호출한다(23:31 G435로 확인, 첫 제스처 9ms). 정지 후 약 10초가 지나면 G435 신호가 PC에 오지 않아, 토글 1초 뒤 `PAUSED`이면 `winsound`로 무음을 최대 10분 재생한다. 세션이 없을 때 쓰는 미디어 키는 확장 키 플래그가 있어야 하고, 0.05초보다 빠른 방향 전환(재생 시작 때의 볼륨 재동기화)은 무시한다. 리스너를 두 개 띄우면 토글이 상쇄되므로 뮤텍스로 중복 실행을 막는다. 제스처 처리는 COM 콜백 밖의 스레드에서 한다(콜백 안에서 하면 교착 상태). [보고서](../docs/reports/261101-2312-11-windows-play-pause-gesture.md)
- tested (Windows, 2026-11-01 23:41–23:42): `+−+` 다음 곡, `−+−` 이전 곡이 Spotify와 YouTube 재생목록(23:43)에서 작동한다. Chrome·Spotify를 같이 열면 YouTube 영상 전환 순간 현재 세션이 Spotify로 바뀌어 제스처가 Spotify로 갈 수 있다. 두 번 누름은 세 번째 누름을 1초 기다린 뒤 재생/일시정지한다. YouTube 단일 영상은 Chrome 세션이 다음/이전을 꺼둬서 넘어가지 않는다.
- tested (Android, 2026-11-01 23:55–23:56): 같은 `+−+`/`−+−`를 폰에도 넣었고 Chrome YouTube 재생목록(일시정지·재개 뒤 포함), AudioSeeker(일시정지 중 넘김 포함), Samsung Music(11-02 00:01)에서 넘어갔다. 넘김 뒤 볼륨을 시작 값으로 되돌린다(Android 00:05 확인, Windows 00:10–00:12 확인. Windows는 즉시 복원하면 G435가 자기 볼륨을 다시 보내 덮어써서 0.5초 뒤 복원). 그 전 23:50–23:52에는 Chrome 세션이 넘김 지원(`actions=334`)을 꺼둬 실패했다. 원인 미확인. 확인: `adb shell dumpsys media_session`의 Chrome `actions`(382면 넘김 포함).
- 2026-11-02 00:17 Android 앱을 정리했다: 진단 화면(MediaSession)과 키 기록을 지우고 사용법·접근성 상태·설정 버튼 화면만 남겼다. 이름은 "G435 미디어 제스처", 패키지는 그대로 `com.g435.signalprobe`. 볼륨·제스처 로그(`files/g435-signal-log.jsonl`)는 유지한다. 이제 화면을 열어도 볼륨을 가로채지 않는다. 접근성 이벤트 종류는 `typeAllMask`로 둬야 한다: `typeAnnouncement`로 줄였더니 삼성 Freecess가 앱을 얼려 볼륨 신호를 놓쳤다(00:19). 되돌린 뒤 00:22 재생/일시정지·다음·이전·볼륨 복원 확인.
- tested (2026-11-02 13:24–13:41): Windows C# 트레이 앱 `windows-app/`(.NET 10, WinForms, NAudio.Wasapi)과 Android 앱에 같은 설정(제스처 사용, 곡 넘기기 사용, 무음 계속 유지, 테마 시스템/라이트/다크)을 넣고 사용자가 모두 확인했다. G435 연결 시에만 동작(Windows: 기본 출력 이름 2초 폴링, Android: A2DP 이름). Android도 복원을 0.5초 늦춰야 G435와 볼륨이 맞는다. targetSdk 35라 화면에 시스템 바 여백을 준다. [보고서](../docs/reports/261102-1345-12-apps-settings-csharp.md)
- tested (Android, 2026-11-02 18:20–19:12): 마지막 소리(일시정지 무음 유지 종료 18:20:51) 뒤 51분 동안 18:42, 19:02 무음 10초만 재생됐고 G435는 계속 연결돼 있었다. 알람은 20분 간격으로 정확히 울렸고, 재생 중이던 17:42·18:02는 건너뛰었다. Windows는 미확인.
- 2026-11-02: 두 앱에 "G435 자동 꺼짐 방지" 설정(기본 끔)을 넣었다. G435는 30분 동안 쓰지 않으면 꺼진다. 20분마다 G435가 연결돼 있고 재생 중이 아니면 무음을 10초 재생한다. Android는 잠든 폰에서도 깨도록 `AlarmManager` 정확한 알람(`USE_EXACT_ALARM`)을 쓴다. G435가 디지털 무음을 사용으로 치는지는 아직 모른다.

## Decisions and constraints

- Bluetooth만 사용한다. LIGHTSPEED 동글은 쓰지 않는다.
- 사용자는 “+ 다음 음소거”를 원했지만 음소거 신호가 없어 +/− 방향 전환으로 대체했다.
- 접근성 서비스 활성화는 보안 설정이라 사용자가 폰에서 직접 켠다(ADB로 켜지 않는다).
- 폰의 다른 접근성 서비스(`com.alarmfilter.app`)와 `com.creator.audioseeker` 세션은 건드리지 않는다.

## Files and evidence

- 보고서: [Android 제스처](../docs/reports/261031-2341-09-android-play-pause-gesture.md), [Windows 볼륨](../docs/reports/261031-2004-08-windows-volume-max.md).
- 코드: `android-signal-probe/app/src/main/java/com/g435/signalprobe/G435AccessibilityService.java`, 테스트 `app/src/test/.../GestureTest.java`.
- 빌드: `JAVA_HOME="/c/Program Files/Android/Android Studio/jbr"`, `./gradlew testDebugUnitTest assembleDebug`. ADB: `%LOCALAPPDATA%/Android/Sdk/platform-tools/adb.exe`. 앱 로그: `adb shell run-as com.g435.signalprobe cat files/g435-signal-log.jsonl`.
- Git 저장소: `origin` = https://github.com/mhe1239/g435-media-control (공개), 기본 브랜치 `main`. 원시 로그(`*.jsonl`), 빌드 출력, `local.properties`는 `.gitignore`로 제외한다.

## Remaining TODO

- [Android 후속 확인](../docs/todo/android-input-validation.md): 실사용 오인식, 무음 유지의 배터리·잡음.
- [Windows 볼륨 남은 확인](../docs/todo/windows-volume-reliability.md): Hands-Free 전환 재발 시 기록.
- [앱별 알림 읽기](../docs/todo/notification-readout.md).

- Windows: 실사용 확인, 시작 프로그램 등록은 사용자가 원할 때만.

## Next action

며칠 실사용하며 오인식, Chrome 넘김 지원이 꺼지는 조건, Windows 세션 전환 문제를 지켜본다. 사용자가 개발자 옵션의 HCI snoop을 껐는지 확인한다.

## Blockers or open questions

- 무음 유지 10분 제한과 화면에서 멈춘 경우의 재개 지원 여부는 사용자 결정이 필요하다.
