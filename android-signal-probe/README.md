# G435 Android Signal Probe

갤럭시와 Bluetooth로 연결한 G435의 버튼 신호를 플랫폼 `MediaSession`, `VolumeProvider`, Activity 및 접근성 서비스에서 확인하는 진단 앱입니다.

## 현재 진단의 제한

2026-10-31 소스 대조에서 접근성 XML의 `android:canRequestFilterKeyEvents` 선언 누락을 확인했습니다. 서비스가 켜져 있다는 사실만으로 전역 키 수신이 정상이라고 판단하지 않습니다. 이번 문서화에서는 코드를 수정하지 않았으며 [재검증 TODO](../docs/todo/android-input-validation.md)에 다음 단계를 남겼습니다. 기존의 입력 미관측을 하드웨어상 불가능으로 일반화하지 않습니다.

과거에 접근성 서비스가 없는 오래된 APK를 설치한 문제가 있었습니다. 빌드 후 설치할 파일은 `app/build/outputs/apk/debug/app-debug.apk`이며, `intermediates/apk`의 파일을 사용하지 않습니다. 오늘 빌드·기기 시험을 다시 수행한 것은 아닙니다.

## 사용 방법

1. Android Studio에서 `android-signal-probe` 폴더를 엽니다.
2. 갤럭시에서 개발자 옵션과 USB 디버깅을 켜고 앱을 설치합니다.
3. G435를 갤럭시에 Bluetooth로 연결합니다. LIGHTSPEED 수신기는 이 단계의 대상이 아닙니다.
4. 앱을 열어 `감지 중` 상태를 확인합니다.
   접근성 진단은 `접근성 설정 열기`에서 `G435 버튼 신호 확인`을 사용자가 켜야 합니다. capability 선언 검증도 별도로 필요합니다.
5. G435의 전원, 음소거, 볼륨 업, 볼륨 다운 버튼을 짧게 한 번씩 누릅니다.
6. 먼저 휴대폰 본체의 볼륨 업/다운 버튼을 눌러 `volume_provider` 기록이 나오는지 확인합니다.
7. 이어서 G435의 버튼을 누르고 `MEDIA_PLAY_PAUSE`, `MEDIA_NEXT`, `MEDIA_PREVIOUS`, `HEADSETHOOK`, `VOLUME_*` 또는 `volume_provider` 이벤트가 화면에 기록되는지 확인합니다. 각 입력 이벤트에는 장치 이름, descriptor, vendor/product ID가 함께 표시됩니다.
8. 기록은 앱 내부 저장소의 `g435-signal-log.jsonl`에 저장되고, `로그 복사` 버튼으로 현재 화면 기록을 복사할 수 있습니다.

## 해석 시 주의

- 접근성 서비스가 켜져 있으면 G435 +/−를 1.5초 안에 반대로 누를 때 재생/일시정지합니다. 앱 화면은 닫아 둡니다.
- 앱이 감지 중일 때는 이 앱의 `MediaSession`이 활성 상태이므로 다른 음악 앱 대신 진단 앱이 미디어 버튼을 받을 수 있습니다. 일반 사용 전에는 `감지 중지`를 누르거나 앱을 종료합니다.
- Android가 미디어 버튼을 활성 MediaSession으로 바로 전달하면 `media_button` 또는 `callback` 기록이 남습니다.
- 앱은 진단 중 음량 버튼을 `VolumeProvider`로 받아 `volume_provider`로 기록하도록 설정합니다. 휴대폰 본체 음량 버튼도 기록되지 않으면 앱 세션이 활성화되지 않은 상태일 수 있습니다.
- 전원 버튼은 Android 또는 Bluetooth 스택이 시스템에서 처리해 일반 앱에 전달하지 않을 수 있습니다.
- `전원+음소거` 짧은 동시 누름을 시험할 때는 먼저 각 버튼의 단독 이벤트를 확인한 뒤, 두 버튼을 약 0.2~0.5초 함께 눌러 기록을 비교합니다.
- `전원+음소거` 3초 이상은 G435 설명서상 Bluetooth 페어링이므로 진단 중에도 길게 누르지 않습니다.

이 앱은 미디어·입력 진단용이며 알림 읽기나 연락처 조회를 구현하지 않습니다. 접근성 서비스는 전달된 키의 코드와 장치 정보를 기록하고 UI 이벤트 내용은 사용하지 않습니다. 알림 읽기 요구사항과 현재 진단 코드는 별개입니다.
