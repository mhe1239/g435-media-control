# 작업 기록 - Android G435 재생/일시정지 제스처

- 기록 일시: 2026-10-31 23:41 (Asia/Seoul)
- 실제 작업 시각: 2026-10-31 22:48–23:57 (빌드·앱 로그·logcat 기준)
- 작성자/에이전트: Claude
- 작업 유형: 구현 / 진단

## 요약

1순위 목표인 “G435 버튼으로 갤럭시 재생/일시정지”를 Bluetooth에서 구현하고 실기기에서 확인했다. G435 +/−를 1.5초 안에 반대 방향으로 누르면(+→− 또는 −→+) 접근성 서비스가 `KEYCODE_MEDIA_PLAY_PAUSE`를 현재 미디어 세션에 보낸다. 2026-10-31 23:39–23:40 시험에서 10초 이상 멈춘 뒤 다시 재생을 포함해 4회 왕복이 모두 성공했다(사용자 확인 + 앱 로그).

## 변경 범위와 주요 파일

- [accessibility_service_config.xml](../../android-signal-probe/app/src/main/res/xml/accessibility_service_config.xml): `android:canRequestFilterKeyEvents="true"` 추가.
- [G435AccessibilityService.java](../../android-signal-probe/app/src/main/java/com/g435/signalprobe/G435AccessibilityService.java): 모든 키 기록, `VOLUME_CHANGED_ACTION`/`STREAM_MUTE_CHANGED_ACTION` 기록, 방향 전환 제스처, 일시정지 중 무음 유지(`AudioTrack`, 최대 10분).
- [GestureTest.java](../../android-signal-probe/app/src/test/java/com/g435/signalprobe/GestureTest.java)와 `app/build.gradle`의 `testImplementation "junit:junit:4.13.2"`.
- 빌드: `assembleDebug`, `testDebugUnitTest` 통과(1 test, 0 failure). 설치: `app/build/outputs/apk/debug/app-debug.apk`.

## 관측과 검증

기기: Samsung SM-S916N, Android 16 / SDK 36. 연결: Bluetooth(A2DP·AVRCP 절대 볼륨). 재생 앱: Samsung Music.

| 관측 | 결과 |
|---|---|
| 접근성 키 필터 | tested: 선언 추가 후 `requestFilterKeyEvents=true`, 폰 본체 볼륨 키(`gpio-keys`, `pmic_resin`) 수신 |
| G435 +/− | tested: 키 이벤트 없음. STREAM_MUSIC 볼륨 변화(`VOLUME_CHANGED_ACTION`)로만 도착 |
| G435 음소거 | tested: 키·볼륨·음소거·AVRCP 로그 모두 흔적 없음 → 제스처에 사용 불가 |
| G435 최대 | tested: 폰 미디어 볼륨 11/15에서 멈춤(“따닥”). 그 상태의 +는 신호 없음 → 최대에서는 −→+ |
| 진단 앱 화면을 연 상태 | 앱의 MediaSession·VolumeProvider가 볼륨을 가로채 G435 변화가 기록되지 않음. 앱을 닫고 시험 |
| 일시정지 후 약 3초 | tested: A2DP 스트림이 쉬면 G435 +/−가 폰 볼륨을 바꾸지 않음(23:13:53–23:14:13 기록 0건). 재생 제스처를 볼 수 없던 원인 |
| 무음 유지 후 | tested: 23:39:20–23:40:23 제스처 9회, 일시정지 후 10–15초 뒤 재생 4회 모두 성공 |

- logcat에서 `MediaSessionService`가 `tempAllowlistTargetPkgIfPossible ... [WIU] [FGS]`로 Samsung Music에 키를 전달했고, Samsung Music `PlaybackSessionCallback onPause`가 호출됐다.
- 이벤트 시각 0으로 보내던 키는 실제 시각으로 바꿨다. 재생 실패의 원인은 아니었다(위 A2DP 원인으로 확인).

### 다른 재생 앱 (2026-10-31 23:51–23:57)

logcat `tempAllowlistTargetPkgIfPossible ... targetPackage`로 키가 간 앱을 확인했다. 모두 일시정지 10초 이상 뒤 재생을 포함한다.

| 앱 | 제스처 | 결과 |
|---|---|---|
| AudioSeeker (`com.creator.audioseeker`) | 12회 23:51:23–23:53:40 | tested: 12회 모두 AudioSeeker로 전달, 사용자 확인 성공. 23:52:57 + 뒤 −가 12초 뒤 도착해 1회 미인식 |
| Chrome | 6회 23:55:34–23:56:26 | tested: 모두 Chrome으로 전달, 성공. 직전 23:54의 2회는 그때 재생 중이던 Samsung Music으로 감 |
| Brave | 4회 23:57:23–23:57:47 | tested: 모두 Brave로 전달, 성공 |

- 미인식 1회는 −가 폰에 늦게 도착(또는 누락)한 것으로, 다시 누르면 바로 작동했다. 원인은 구분하지 못했다.
- 23:53:16 일시정지 직후 +/−가 다시 들어와 23:53:18 재생됐다. 의도치 않은 연속 조작일 수 있다.

### 추가: 다음/이전 곡 (2026-11-01)

Windows와 같은 조합을 넣었다. `+−+`는 `KEYCODE_MEDIA_NEXT`, `−+−`는 `KEYCODE_MEDIA_PREVIOUS`다. 두 번 누름은 세 번째 누름을 1초 기다린 뒤 재생/일시정지한다. 판정은 `GestureTest`로 확인했다.

| 시각 | 관측 | 판단 |
|---|---|---|
| 23:50:26–23:52:40 | Chrome YouTube 재생목록. 다음 8회·이전 9회 모두 인식·전달했지만 사용자는 일시정지 뒤 넘김이 안 됐다고 보고 | 당시 Chrome 세션 `actions=334`로 SKIP_TO_NEXT/PREVIOUS가 빠져 있었다. 페이지가 왜 껐는지는 unverified |
| 23:55:47–23:56:03 | 같은 재생목록에서 다음 → 일시정지 → 재개 → 다음 | tested: 사용자 확인 두 번 모두 넘어감. 세션 `actions=382`(넘김 포함)가 일시정지 전후 유지됐다 |
| 11-01 23:58:30–23:59:50 | AudioSeeker에서 다음 5회·이전 2회·재생/일시정지 3회. 일시정지 중 넘김 2회 포함 | tested: 사용자 확인 |
| 11-02 00:01:40–00:01:48 | Samsung Music에서 재생/일시정지 2회, 다음·이전 각 1회 | tested: 사용자 확인 |
| 11-02 00:05:12–00:05:29 | 넘김 뒤 볼륨 복원 추가. Samsung Music에서 넘김 7회 모두 시작 볼륨(6)으로 돌아왔고, 복원으로 생긴 볼륨 변화는 제스처로 세지 않았다 | tested: 사용자 확인 |

## 리스크/이슈

- 일시정지 중 무음 스트림 때문에 폰·헤드셋 배터리를 더 쓴다. 측정하지 않았다. 사용자는 이 동안의 잡음 여부를 따로 보고하지 않았다.
- 화면이나 다른 경로로 멈춘 경우 무음 유지가 켜지지 않아, 약 3초 뒤에는 제스처로 재생할 수 없다.
- 일반 볼륨 조작에서 1.5초 안에 방향을 바꾸면 의도치 않게 재생/일시정지된다(세 번이면 곡 넘김).
- 재생/일시정지는 다음/이전 곡 조합 때문에 약 1초 늦게 실행된다. 넘김은 앱·페이지가 지원할 때만 된다.
- 재생/일시정지는 Android의 미디어 버튼 세션(마지막으로 재생한 앱)으로 간다. Samsung Music·AudioSeeker·Chrome·Brave는 확인했고, YouTube는 사용자가 쓰지 않아 미시험이다.
- 2026-11-02 진단 화면(MediaSession)과 키 기록을 지웠다. 화면은 사용법과 접근성 상태만 보여 주며 볼륨을 가로채지 않는다. 앱 이름은 "G435 미디어 제스처"로 바꿨고 패키지(`com.g435.signalprobe`)는 접근성 설정을 유지하려고 그대로 뒀다.
- 정리하며 접근성 이벤트를 `typeAnnouncement`만 받게 줄였더니 00:19:18 삼성 Freecess가 앱을 얼려 이후 볼륨 신호를 받지 못했다. `typeAllMask`로 되돌린 뒤 얼리기가 건너뛰어졌고(`skipping freeze`), 00:22 재생/일시정지·다음·이전·볼륨 복원이 동작했다(tested, 사용자 확인).

## 다음 작업과 참고

- [Android TODO](../todo/android-input-validation.md): 다른 재생 앱, 배터리, 오인식 빈도 확인.
- 이전 Windows 결과: [Windows 볼륨 보고서](261031-2004-08-windows-volume-max.md).
