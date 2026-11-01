# 2) 기술 명세와 증거 해석

기준: 2026-10-31, Asia/Seoul. 이번 문서화에서는 소스를 읽었으며 실행 코드를 변경하거나 기기 시험을 다시 수행하지 않았다.

## A. Windows 진단기

| 항목 | 현재 구현 |
|---|---|
| 언어 / 환경 | Python, Windows 전용 `ctypes.WinDLL`; 과거 실행 환경 Python 3.12 |
| 의존성 선언 | `pycaw>=2024.6.1`, `comtypes>=1.4.0`; 고정 버전 아님 |
| 직접 입력 | 메시지 전용 창의 `WM_INPUT`, `WM_INPUT_DEVICE_CHANGE` |
| 등록 Usage | `(0x01,0x06)`, `(0x0C,0x01)`, `(0xFF00,0x01)`, `(0xFF01,0x01)` |
| 오디오 관측 | `G435AudioMonitor.poll()`에서 이름에 G435가 포함된 엔드포인트 상태·음소거·볼륨 조회 |
| 주기 | 코드상 다음 조회 기준 0.1초, 루프 sleep 0.01초; 실제 처리시간을 포함한 고정 100ms 보장은 아님 |
| 출력 | 콘솔 및 `g435-signal-log.jsonl`에 추가 저장 |

실행: 프로젝트 루트에서 `python -m pip install -r .\requirements.txt`, `python .\g435_signal_probe.py`. Ctrl+C로 종료한다. 사용 범위는 Bluetooth이며 LIGHTSPEED 동글 시험을 요구하지 않는다.

주요 이벤트는 `started`, `keyboard`, `hid`, `device_change`, `audio_baseline`, `audio_state_change`, `audio_volume_change`, `audio_mute_change`, 오류, `stopped`다. `audio_state_change` 기록은 2026-10-15 시험 도중 추가했다.

### 해석 제한

- `candidate=true`는 이름에 `G435`, `LOGITECH`, `VID_046D`가 있다는 휴리스틱이다. G435 장치 식별의 증명이 아니다. 실제 로그의 Alt·Tab 입력도 이 조건에 걸렸다.
- 오디오 변화는 장치 이름·ID·`state`를 함께 확인한다. `NotPresent`/`Unplugged`의 변화는 연결된 G435 버튼의 성공 증거로 세지 않는다.
- `audio_volume_change`는 두 관측값의 차이다. 물리 버튼 누름, 누름 횟수, 동시 조합, 변경 주체를 직접 알려주지 않는다.
- 빠른 왕복 변화는 폴링 사이에 누락될 수 있다. 장치 내부 음량·동기화·최소/최대 음량의 영향은 재현 전에는 가설이다.
- 현재 구현은 Core Audio 변경 콜백을 등록하지 않는다. 콜백 도입은 후속 검토안이며, 도입해도 버튼 식별이 보장되지는 않는다.

## B. Android 진단 앱

| 항목 | 현재 파일의 설정 |
|---|---|
| 앱 ID / namespace | `com.g435.signalprobe` |
| 앱 버전 | versionCode 1, versionName 0.1 |
| SDK | min 26, compile 35, target 35 |
| Java 언어 수준 | 11 |
| Android Gradle Plugin | 8.7.3 |
| Gradle Wrapper | 9.3.0 |
| UI | 플랫폼 Activity와 Java 코드로 구성한 View |
| 세션 | 플랫폼 `android.media.session.MediaSession`, `VolumeProvider` |
| 기록 | `SignalLog`, 앱 내부 `files/g435-signal-log.jsonl`; 화면 최근 200줄 |

시험 기기는 Samsung SM-S916N, Android 16 / SDK 36이다(2026-10-31 ADB 확인). 앱 compile SDK와 기기 SDK를 혼동하지 않는다. 위 AGP/Gradle 조합으로 2026-10-31 Android Studio JBR을 `JAVA_HOME`으로 지정해 빌드·테스트에 성공했다.

빌드: `android-signal-probe`에서 `.\gradlew.bat assembleDebug`. 설치 대상은 `app/build/outputs/apk/debug/app-debug.apk`다. 과거 `app/build/intermediates/apk/debug/app-debug.apk`가 오래된 APK여서 접근성 서비스가 누락된 설치 문제가 있었다. 빌드 후 manifest와 설치된 패키지를 확인한다.

### 접근성 서비스와 재생/일시정지 제스처

`accessibility_service_config.xml`에 `android:canRequestFilterKeyEvents="true"`를 선언했다(2026-10-31). 이전에는 선언이 없어 키 필터 플래그가 무시됐다. [Android 공식 API](https://developer.android.com/reference/android/accessibilityservice/AccessibilityServiceInfo#FLAG_REQUEST_FILTER_KEY_EVENTS)

`G435AccessibilityService`:

- 모든 키 이벤트와 `android.media.VOLUME_CHANGED_ACTION`/`STREAM_MUTE_CHANGED_ACTION`을 `SignalLog`에 기록한다. 키는 소비하지 않고 `false`를 반환한다.
- STREAM_MUSIC 볼륨이 1.5초(`GESTURE_WINDOW_MS`) 안에 반대 방향으로 바뀌면 `AudioManager.dispatchMediaKeyEvent`로 `KEYCODE_MEDIA_PLAY_PAUSE`를 보낸다. G435 +/−는 키가 아니라 볼륨 변화로만 도착하기 때문이다.
- 재생 중(`isMusicActive`)에 제스처로 멈추면 무음 `AudioTrack`을 최대 10분 재생한다. A2DP 스트림이 쉬면 G435 +/−가 폰에 도착하지 않기 때문이다. 다음 제스처나 시간 초과에 멈춘다. 오디오 포커스는 요청하지 않는다.
- 단위 테스트: `app/src/test/.../GestureTest.java` (`gradlew testDebugUnitTest`).

`MainActivity`의 MediaSession·VolumeProvider는 진단용이다. 화면이 열려 있으면 볼륨을 가로채므로 제스처 사용 시 닫는다. 앱에는 알림 읽기용 NotificationListenerService나 TTS 구현이 없다.

## C. 판정 규칙

1. `문서 확인`: 설명서 또는 코드에 적힌 내용. 실기기 검증과 구분한다.
2. `직접 증거`: 현재 열어 확인한 로그·소스.
3. `과거 관측`: 이전 대화의 명령 출력·기기 시험. 원본이 없으면 재분석할 수 없다고 표시한다.
4. `제안/가설`: 아직 구현·검증하지 않은 매핑과 원인.

Android의 `deviceId`만으로 G435를 판정하지 않는다. 이름·descriptor 등 출처를 확인하고 `gpio-keys`처럼 본체 버튼인 관측을 구분한다. 앱 로그 부재는 원시 Bluetooth 패킷 부재의 증명이 아니다. HCI 패킷이 보이는 것과 일반 앱이 그 패킷을 구독할 수 있는 것도 별개다.

HCI/버그리포트에는 식별자와 페어링 정보 등이 포함될 수 있다. 문서에는 비식별 요약만 남긴다. 현재 없는 원본을 새로 만들어 과거 증거처럼 사용하지 않는다.

## D. 검증 경계

- 문서화 작업은 문서 링크·경로·로그 시각·소스 일치 여부를 확인한다.
- Windows 구현 변경은 구문 검사 후 연결 상태와 입력 출처를 기록한 실기기 시험으로 확인한다.
- Android 구현 변경은 빌드·APK metadata·설치 상태·대조 입력·G435 입력을 순서대로 검증한다.
- 장치 연결이나 볼륨·통화 경로를 바꾸는 시험은 사용자와 누름 순서를 맞춘다. 아무 입력도 받지 못한 실행을 성공적인 G435 시험으로 기록하지 않는다.

참고: [Windows 오디오 상태 알림](https://learn.microsoft.com/en-us/windows/win32/api/endpointvolume/nn-endpointvolume-iaudioendpointvolumecallback), [Bluetooth 오디오 액세서리 지침](https://learn.microsoft.com/en-us/windows-hardware/design/accessory-guidelines/bluetooth-accessory-guidelines/bluetooth-accessory-guidelines-classic-audio).
