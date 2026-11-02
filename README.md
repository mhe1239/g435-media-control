# G435 Windows 신호 감지기

이 단계의 목적은 G435의 네 가지 물리 버튼이 Windows에 어떤 신호로 전달되는지 확인하는 것입니다.

- 전원
- 음량+
- 음량-
- 마이크 음소거

현재 프로그램은 버튼을 재매핑하거나 일시정지 명령을 보내지 않습니다. Raw Input에서 받은 키/HID 신호와 Windows에 노출된 G435 오디오 장치의 음소거·볼륨 상태 변화를 화면과 `g435-signal-log.jsonl`에 기록합니다.

## Claude에서 이어가기

`CLAUDE.md` → `AGENTS.md` → `docs/01`, `docs/02`, `docs/03` → [TODO 색인](docs/todo/00-todo-list.md) 순서로 읽습니다. 짧은 인계는 [.claude/session-handoff.md](.claude/session-handoff.md)에 있습니다.

현재 범위는 **Bluetooth 연결만**입니다. Windows에서 G435 +/−는 볼륨 0%–69% 안에서만 변하며, 무반응은 그 끝에 닿은 경우였습니다. 갤럭시에서는 +/− 방향 전환 제스처로 재생/일시정지를 구현해 확인했습니다(2026-10-31). 다음/이전 곡과 알림 읽기는 아직 구현되지 않았습니다.

## 시간순 작업 이력

다음 보고서는 2026-10-31에 대화와 남아 있는 파일을 대조해 복원했습니다. 파일명의 `261031-1347`은 문서화 시작 기준이며, 아래 날짜·시각이 실제 과거 관측 구간입니다. 시각 미상 작업은 임의로 추정하지 않았습니다. 시간대는 Asia/Seoul입니다.

| 작업 시점 | 내용 |
|---|---|
| 2026-09-16 23:26 인계 이전 | [설명서·미디어 조작 설계·알림 요구사항](docs/reports/261031-1347-01-history-20260916-requirements.md) |
| 2026-09-17 17:53–17:54 | [초기 Windows 진단 기록](docs/reports/261031-1347-02-history-20260917-windows.md) |
| 2026-09-19 17:21–17:22 사용자 로그 | [Android 전환과 입력 출처 확인](docs/reports/261031-1347-03-history-20260919-android.md) |
| 개별 준비 시각 미상 / 2026-10-14 23시대 진단 | [REA·ADB 연결, 접근성 서비스와 APK 설치 문제](docs/reports/261031-1347-04-history-20261014-accessibility.md) |
| 2026-10-14 23:50 이후 | [HCI 수집·분석과 결론의 한계](docs/reports/261031-1347-05-history-20261014-hci.md) |
| 2026-10-15 00:00–00:07 이후 | [PC 재시험·볼륨 변화·간헐적 무반응 보고](docs/reports/261031-1347-06-history-20261015-windows.md) |
| 2026-10-31 | [Claude 인계 문서화와 현재 소스 대조](docs/reports/261031-1347-07-claude-docs-handoff.md) |
| 2026-10-31 19:57–20:07 | [Windows 볼륨 무반응 재현: G435 조절 범위 0–69%](docs/reports/261031-2004-08-windows-volume-max.md) |
| 2026-10-31 22:48–23:40 | [Android G435 재생/일시정지 제스처](docs/reports/261031-2341-09-android-play-pause-gesture.md) |
| 2026-11-01 14:53–16:01 | [Android 전원·마이크 버튼 신호 없음(HCI snoop)](docs/reports/261101-1605-10-android-power-mic-hci.md) |
| 2026-11-01 22:43–23:11 | [Windows G435 재생/일시정지 제스처](docs/reports/261101-2312-11-windows-play-pause-gesture.md) |
| 2026-11-02 00:30–13:41 | [Windows C# 앱과 두 앱의 설정](docs/reports/261102-1345-12-apps-settings-csharp.md) |

현재 명세는 [기술 문서](docs/02-specs.md), 최신 판단은 [제품 상태](docs/03-product-plan.md)를 따릅니다. 기존 `기록용/` TXT는 당시 기록으로 보존합니다. 문서 구조는 [Austin Docs Architecture](https://github.com/EunHyeokJung/austin-docs-architecture)를 참고했습니다.

## 사용법 (G435 미디어 제스처)

| 누름 | 동작 |
|---|---|
| `+−` 또는 `−+` | 재생/일시정지 |
| `+−+` | 다음 곡 (볼륨은 원래대로) |
| `−+−` | 이전 곡 (볼륨은 원래대로) |

두 앱 모두 설정이 같습니다: 제스처 사용, 곡 넘기기 사용(끄면 재생/일시정지가 1초 기다리지 않음), 일시정지 중 무음 계속 유지(끄면 10분), G435 자동 꺼짐 방지(20분마다 아무것도 재생하지 않으면 무음 10초, Android에서 51분 유지 확인). G435가 연결돼 있을 때만 동작하고, 화면은 시스템의 라이트/다크 모드를 따릅니다.

- **Windows**: [`windows-app/`](windows-app) C# 트레이 앱. G435가 기본 출력이 되면 동작합니다. 설치: `powershell -ExecutionPolicy Bypass -File windows-app\install.ps1` (.NET 10 SDK). `%LOCALAPPDATA%\Programs\G435MediaGesture`에 게시하고 시작 메뉴 바로가기를 만들어 Windows 검색에 나옵니다. 코드를 고친 뒤 다시 실행하면 갱신됩니다. 설정 창에서 Windows 시작 시 실행을 켤 수 있습니다. 로그: `%LOCALAPPDATA%\G435MediaGesture\log.jsonl`.
- **Android**: [`android-signal-probe/`](android-signal-probe) 앱 "G435 미디어 제스처". 설치 후 앱의 버튼으로 접근성 설정을 열어 서비스를 직접 켭니다.

## 진단 도구 실행

G435를 PC에 Bluetooth로 연결한 뒤 PowerShell에서 실행합니다. 이번 프로젝트의 시험에는 LIGHTSPEED USB 동글을 사용하지 않습니다.

```powershell
python -m pip install -r .\requirements.txt
python .\g435_signal_probe.py
```

그 상태에서 네 버튼을 각각 한 번씩 눌러봅니다. 종료는 `Ctrl+C`입니다.

`g435_media_gesture.py`는 C# 앱 이전의 Python 제스처 리스너입니다(설정 없음). 두 프로그램은 같은 이름의 뮤텍스를 써서 동시에 실행되지 않습니다. 자세한 내용은 [보고서](docs/reports/261101-2312-11-windows-play-pause-gesture.md)를 참고합니다.

```powershell
python .\g435_media_gesture.py
```

## 결과 해석

- `keyboard` 이벤트가 나오면 Windows가 해당 입력을 키/미디어 키로 노출한 것입니다.
- `hid` 이벤트가 나오면 원시 HID 리포트가 들어온 것이며, 이후 G435 리포트 형식을 분석할 수 있습니다.
- `candidate=true`는 Logitech 장치를 넓게 포함하는 후보 표시이며 G435 식별의 증거가 아닙니다.
- `audio_mute_change`와 `audio_volume_change`는 엔드포인트 상태 변화입니다. 버튼, 마우스, 다른 앱 중 어떤 경로로 발생했는지는 별도로 확인해야 합니다.
- `audio_state_change`는 연결 상태 변화입니다. 버튼 시험 결과는 `Active`인 장치를 기준으로 해석합니다.
- 전원 버튼은 배터리 확인만 수행할 때 Windows 입력을 만들지 않을 수 있습니다. 이 경우 `전원+음소거` 조합을 PC에서 직접 구분할 수 있는지 별도로 판단해야 합니다.

G435 설명서상 전원+음소거 3초 이상은 Bluetooth 페어링입니다. 버튼 진단에서는 짧은 누름만 사용해 연결이 끊기는 상황과 혼동하지 않습니다.

## Android 신호 진단

갤럭시에서 G435를 Bluetooth로 연결한 뒤 Android의 표준 미디어 버튼 전달 여부를 확인하려면 `android-signal-probe`를 Android Studio에서 엽니다.

```text
android-signal-probe/
```

진단 화면(`MediaSession` 키 기록)은 2026-11-02에 지웠습니다. 지금 앱은 제스처 앱이며, 볼륨 단계와 제스처 결과만 앱 내부 JSONL 로그에 남깁니다.

접근성 서비스(“G435 미디어 제스처”)를 켜면 **G435 +/−를 1.5초 안에 반대로 누를 때(+→− 또는 −→+) 재생/일시정지**하고, **+−+는 다음 곡, −+−는 이전 곡**입니다. 곡을 넘기면 볼륨은 원래 값으로 돌아갑니다. G435 최대 음량에서는 −→+로 누릅니다. 자세한 내용은 [보고서](docs/reports/261031-2341-09-android-play-pause-gesture.md)를 참고합니다.

현재 Android 테스트의 우선순위는 다음과 같습니다.

1. G435를 갤럭시에 Bluetooth로 연결합니다.
2. 앱에서 감지를 시작하고 네 물리 버튼을 각각 짧게 누릅니다.
3. 각 버튼의 단독 이벤트를 확인한 뒤 전원+음소거, 전원+볼륨 업, 전원+볼륨 다운의 짧은 동시 누름을 확인합니다.
4. `전원+음소거` 3초 이상은 Bluetooth 페어링 기능이므로 테스트하지 않습니다.

자세한 실행 순서는 [Android 신호 진단기 README](./android-signal-probe/README.md)를 참고합니다.
