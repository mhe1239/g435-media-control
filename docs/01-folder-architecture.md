# 1) 폴더 아키텍처

기준: 2026-10-31, Asia/Seoul. 이 프로젝트는 Windows와 Android에서 G435의 Bluetooth 버튼 신호를 확인하는 두 개의 진단 프로그램으로 구성된다. 웹 서비스나 서버는 없다.

## A. 현재 구조와 책임

```text
C:/g435-media-control/
├─ AGENTS.md                       # 공통 규약과 프로젝트 문서 읽기 순서
├─ CLAUDE.md                       # Claude에서 AGENTS.md로 연결하는 진입점
├─ README.md                       # 실행 방법과 시간순 보고서 색인
├─ g435_signal_probe.py            # Windows Raw Input / 오디오 상태 진단
├─ requirements.txt               # pycaw, comtypes
├─ g435-signal-log.jsonl           # 실제 Windows 테스트 로그; 로컬 증거
├─ android-signal-probe/
│  ├─ README.md
│  ├─ build.gradle                 # Android Gradle Plugin 설정
│  ├─ gradle/wrapper/              # Gradle Wrapper
│  ├─ app/build.gradle             # SDK, 앱 ID, Java 설정
│  └─ app/src/main/
│     ├─ AndroidManifest.xml
│     ├─ java/com/g435/signalprobe/
│     │  ├─ MainActivity.java       # 화면, MediaSession, VolumeProvider
│     │  ├─ G435AccessibilityService.java # 접근성 키 이벤트 진단
│     │  └─ SignalLog.java          # 앱 내부 JSONL 기록과 화면 전달
│     └─ res/                      # 문자열, 접근성 서비스 메타데이터
├─ .claude/
│  ├─ session-handoff.md           # Claude용 짧은 현재 상태와 다음 행동
│  └─ skills/session-handoff/SKILL.md # 기존 프로젝트 인계 스킬
├─ docs/
│  ├─ 01-folder-architecture.md
│  ├─ 02-specs.md
│  ├─ 03-product-plan.md
│  ├─ reports/                    # 과거 작업을 시간순으로 복원한 보고서
│  └─ todo/                       # 후속 작업과 00-todo-list.md 색인
├─ 기록용/                         # 기존 2026-09-16 TXT 인계 기록
├─ diagnostics/                    # 진단 자료 보관 위치; 현재 비어 있음
└─ ROD/                            # 현재 비어 있음; 용도 미확인
```

## B. 프로그램 경계

- Windows 진단기는 로컬 Win32 입력과 G435 이름의 오디오 엔드포인트를 읽어 루트 JSONL에 추가한다. 미디어 명령을 보내지 않는다.
- Android 앱은 Activity, MediaSession, VolumeProvider, 접근성 서비스 관측을 앱 내부 저장소의 JSONL로 기록한다. Windows 로그와 별도 파일이다.
- REA/ADB는 기기 확인·설치·자료 수집에 사용했던 외부 도구다. 앱의 런타임 의존성이 아니다.
- Android `build/`, `.gradle/`, `local.properties`, `.idea/`, Python `__pycache__/` 등은 소스 명세가 아닌 로컬 설정·생성물이다.

## C. 문서의 역할

- `01`, `02`, `03`: 현재 확인한 구조, 기술 명세, 요구사항과 상태.
- `reports/`: 작업 당시 관측과 그때의 판단을 보존한다. 후속 정정도 명시한다.
- `todo/00-todo-list.md`: 진행할 작업의 단일 색인. 완료하면 결과를 보고서에 남기고 해당 TODO와 색인 항목을 정리한다.
- `.claude/session-handoff.md`: 다음 세션의 짧은 진입점. 상세 명세를 중복 관리하지 않는다.
- 기존 `기록용/2026-09-16-g435-media-control-handoff.txt`는 당시 기록으로 보존한다. 그 안의 미시험·기기 접근 불가 상태를 현재 상태로 적용하지 않는다.

## D. 증거와 파일 존재

Windows JSONL은 2026-10-31에도 존재한다. 반면 2026-10-14에 수집했던 `diagnostics/hci/dumpstate-2026-10-14-23-50-39.zip` 및 추출 HCI 로그는 현재 경로에 없다. 삭제 원인이나 시각은 확인하지 않았다. Android 로그는 이번 문서화에서 기기로부터 다시 읽지 않았다.

현재 작업 폴더와 상위 경로는 Git 저장소로 인식되지 않는다. 브랜치·원격·커밋 이력을 만들거나 추정하지 않는다.

참고 구조: [Austin Docs Architecture 한국어 번들](https://github.com/EunHyeokJung/austin-docs-architecture/tree/main/ko).
