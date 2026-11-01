# 작업 기록 - Claude 인계를 위한 문서 정리

- 기록 일시: 2026-10-31 13:47 기준 문서화, Asia/Seoul
- 실제 작업 시각: 2026-10-31, 사용자 요청에 따른 현재 문서화 작업
- 작성자/에이전트: Codex
- 작업 유형: 문서화 / 과거 이력 복원 / 소스 대조

## 요약

Claude가 대화 없이 이어서 작업할 수 있도록 Austin Docs Architecture의 한국어 문서 구조를 적용했다. 과거 시각이 없는 대화에는 임의의 작업 시각을 붙이지 않았다.

모든 `261031-1347-*` 보고서 파일명은 이번 문서화 시작 기준으로 작성한 기록이다. 실제 과거 작업 시각은 각 보고서 본문을 따른다.

## 변경 범위와 주요 파일

- `docs/01-folder-architecture.md`, `02-specs.md`, `03-product-plan.md`에 현재 소스·범위·관측 한계를 정리했다.
- `docs/reports/`에 요구사항, Windows 초기 관측, Android 입력, 접근성·REA, HCI, Windows 재시험을 나눴다.
- `docs/todo/00-todo-list.md`와 개별 TODO, `.claude/session-handoff.md`에 다음 시작점을 정리했다.
- 루트 `CLAUDE.md`를 AGENTS의 지정 템플릿 그대로 생성하고 재확인한 뒤, AGENTS의 일회성 생성 설정을 제거했다. 기존 공통 규칙은 보존하고 프로젝트 읽기 순서를 추가했다.
- 루트·Android README를 실제 진단 범위와 미해결 사항에 맞게 보완했다. 실행 소스·기존 로그·기존 TXT는 변경하지 않았다.

## 소스 대조에서 발견한 사항

- Android 접근성 XML에 `canRequestFilterKeyEvents`가 없다. 과거 enabled/bound 관측만으로 전역 키 필터링 검증을 완료 처리하지 않도록 정정했다.
- Windows `candidate` 필터는 G435 전용이 아니다. Alt·Tab을 G435 신호로 세지 않도록 명세에 기록했다.
- HCI 원본은 현재 없다. 대화상의 수집 성공과 현재 재분석 가능 여부를 구분했다.
- 현재 AGP/Gradle 설정은 읽었지만 빌드를 다시 수행하지 않았다.

## 관측과 검증

- Markdown 21개 파일을 대상으로 로컬 링크 60개와 해당 heading anchor를 검사했고 통과했다. `CLAUDE.md`의 조건부 상위 `../AGENTS.md` 참조는 파일 부재를 명시해 별도로 처리했다.
- `CLAUDE.md`가 AGENTS에서 지정했던 템플릿과 일치함을 저장 후 재확인했다.
- Windows JSONL 73개 행을 파싱하고 문서에 옮긴 활성 엔드포인트 볼륨 변화 두 건의 시각·값을 대조했다.
- Windows 소스·원본 로그, Android manifest·접근성 XML의 SHA-256이 편집 전과 동일함을 확인했다.
- 새 문서와 보완한 진입 문서의 내용·연결을 검토했다. Git 저장소가 아니므로 Git diff 대신 이번 편집 범위와 원본 증거를 대조했다.
- 실제 기기의 연결 상태·입력 및 Android 빌드는 이번에 재검증하지 않았다.

## 리스크/이슈

Git 명령 결과 현재 폴더는 저장소가 아니었다. 브랜치·원격·최근 커밋·Git diff를 확인할 수 없었고 커밋/푸시는 하지 않았다. 상위 `C:/AGENTS.md`, `C:/CLAUDE.md`는 없었으며 생성하지 않았다.

## 다음 작업과 참고

- [.claude/session-handoff.md](../../.claude/session-handoff.md)에서 이어간다.
- 첫 기술 작업은 [볼륨 누락 현상 구분](../todo/windows-volume-reliability.md)이다.
- 구조 출처: [Austin Docs Architecture](https://github.com/EunHyeokJung/austin-docs-architecture).
