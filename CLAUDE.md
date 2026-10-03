# CLAUDE.md — 백엔드 CS 기본기

Java/Spring 백엔드 개발자를 위한 CS 학습 사이트. 정적 HTML, GitHub Pages 배포.
- 사이트: https://seonooo.github.io/backend-cs-fundamentals/
- 저장소: https://github.com/Seonooo/backend-cs-fundamentals

## 구조
```
docs/       ← Pages 배포 폴더 (main /docs). index.html 목차, assets/style.css 공통 스타일,
              os/ network/ database/ common/ 영역별 NN-slug.html
docs/articles.json ← 편 목록·영역·연결 키워드 (목차·README·crumb·pager의 원본)
guides/     ← 작업별 상세 규칙 (아래 "상황별 안내"에서 필요한 것만 읽음)
tools/      ← 검증 스크립트
plan/do/    ← 진행 중인 계획 · plan/done/ 완료한 계획 (git 제외)
README.md   ← GitHub 소개 (목차 표 + 연결 키워드 지도)
```

## 기준 환경
| 영역 | 기준 |
|---|---|
| 언어·런타임 | Java 21. JDK 24+ 차이는 조건으로 표시 |
| 프레임워크 | Spring Boot 3, Hibernate(JPA), HikariCP, 내장 Tomcat |
| DB | MySQL 8 InnoDB (PostgreSQL과 다르면 비교) |
| HTTP / TLS | HTTP/1.1·2 기본, HTTP/3은 조건 표시 / TLS 1.3 |
| 인프라 예시 | AWS (ALB/NLB, vCPU) |
| Redis | Redis 7 이상·Valkey 공통 동작. 예시는 단일 인스턴스, 구성별 차이는 29편 참조로 표시. Spring Data Redis + Lettuce (분산 락은 Redisson 비교). 인프라 예시 ElastiCache(Valkey) |
| Kafka | 미정 — 첫 편 작성 전에 정해 이 표에 추가 |

바꿀 때는 `docs/index.html`, `README.md`의 기준 환경 문장도 함께 고칩니다.

## 작업 흐름
- 작업을 시작하면 먼저 `plan/do/`를 확인합니다. 새 작업은 `guides/plan.md` 형식으로 `plan/do/`에 계획을 만들고, 그 계획을 기준으로 진행합니다.
- 편 수는 계속 늘어납니다. 끝이나 전체 편수를 전제하는 표현은 쓰지 않습니다.
- 문제가 생기면(검사 실패, 사용자 지적) `guides/lessons.md` 절차로 기록하고, 가능하면 검사 규칙이나 hook으로 장치화합니다.

## 상황별 안내 (guide는 Read 도구로 읽을 것)
| 이런 작업이면 | 먼저 읽기 |
|---|---|
| 새 편·새 영역 추가 | `guides/new-article.md`, `page-format.md`, `writing.md` |
| 편 목록·제목·요약·연결 키워드 변경 | `docs/articles.json` 수정 후 `py tools/build.py` (생성 구간은 손으로 고치지 않음) |
| 페이지 HTML 수정 | `guides/page-format.md` |
| 본문 문장 쓰기·수정 | `guides/writing.md` |
| 그림 그리기·수정 | `guides/svg.md` |
| 계획 만들기·완료 | `guides/plan.md` |
| 문제 발생·재발 방지 | `guides/lessons.md` |
| 수정 후 검사 | `py tools/check.py --changed`, `py tools/check_mobile.py --changed`, 그림이 있으면 `py tools/check_figures.py --changed` |
| push 후 확인 | `py tools/check_deploy.py` |
| 검사 규칙·hook 추가·수정 | `tools/checks/`·`tools/hooks/`, 재현 케이스는 `tools/test_checks.py`·`tools/test_hooks.py` |

검사 명령은 Windows 기준 `py`입니다. Git Bash의 `python`은 스토어 가짜 실행 파일로 연결될 수 있습니다. 다른 환경에서는 `python3`을 씁니다.

## 배포·커밋
- push 후 1~2분 뒤 반영됩니다. Pages 설정을 바꾸면 빌드를 직접 요청해야 합니다. 브라우저는 10분 캐시합니다.
- 커밋·push는 사용자가 요청할 때 합니다. 메시지는 영어로, 첫 줄에 무엇을 왜 바꿨는지 씁니다.
- 파일 편집은 정확한 문자열 치환으로 하고, 대상이 파일에 정확히 1번 있는지 확인합니다.
