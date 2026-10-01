# 새 편·새 영역 추가

> **읽는 시점**: Redis, Kafka, 분산 락처럼 새 편이나 새 영역을 추가할 때. `guides/page-format.md`, `guides/writing.md`도 함께 봅니다.

## 기본 원칙: 편 수는 계속 늘어난다
- 이 시리즈에는 **마지막 편이 없습니다.** 새 편은 기존 번호 뒤에 이어 붙입니다(27, 28, …).
- 이미 공개된 편의 번호와 파일명은 바꾸지 않습니다. 번호를 다시 매기면 외부에 공유된 링크가 깨집니다. 주제가 바뀌어 파일명을 꼭 바꿔야 하면 아래 "공개된 편의 파일명 바꾸기"를 따릅니다.
- 어떤 편에도 "마지막 편입니다", "N편을 지나오며" 같이 **끝이나 전체 편수를 전제하는 표현**을 쓰지 않습니다.
- 새 주제는 기존 영역 폴더에 넣거나, 주제가 묶이면 새 영역 폴더를 만듭니다(예: `docs/distributed/`). 번호는 폴더와 상관없이 전체에서 이어집니다.

## 추가 절차
1. **기준 환경 확정**
   - 루트 `CLAUDE.md` 기준 환경 표의 "미정" 칸(Redis, Kafka 등)을 사용자와 정해 채웁니다.
   - `docs/index.html`과 `README.md`의 기준 환경 문장도 필요하면 고칩니다.
2. **`docs/articles.json`에 한 줄 추가**
   - `articles`에 `{"no", "area", "slug", "title", "summary"}`를 추가합니다. `summary`는 README 목차의 한 줄 요약입니다.
   - 새 영역이면 `areas`에도 `{"id", "name"}` 한 줄을 추가합니다. `name`이 crumb·목차·README의 영역명이 됩니다.
   - 새 편이 반복하는 원리가 있으면 `keywords`의 `flow`에 번호를 추가하고, 새 원리라면 키워드를 새로 만듭니다(힌트는 `[27, "설명"]`).
3. **파일 생성**: `docs/<area>/<NN>-<slug>.html`. `guides/page-format.md` 골격과 `guides/svg.md` 규칙을 따릅니다. crumb와 pager는 다음 단계에서 채워지므로 골격대로만 두면 됩니다.
4. **`py tools/build.py`**
   - 목차 편 목록·연결 키워드 지도, README 목차·키워드 표, 모든 편의 crumb·pager(직전 편의 "다음" 링크 포함)가 자동으로 맞춰집니다.
   - 손으로 할 것은 관련 편의 "다음으로 이어지는 개념"과 본문의 "(NN편)" 참조뿐입니다.
5. **검증**: `py tools/check.py`, `py tools/check_mobile.py --changed`

> 생성 구간(`<!-- gen:… -->` 표시 주석 안, 각 편의 crumb·pager)은 손으로 고치지 않습니다. 다음 `build.py` 실행 때 덮어써지고, 그 전에는 검사(`generated`)가 오류로 알려 줍니다. 제목을 바꿀 때도 `articles.json`의 `title`과 페이지의 `<title>`·`<h1>`을 함께 고친 뒤 `build.py`를 실행합니다.

## 공개된 편의 파일명 바꾸기
주제가 바뀌어 slug를 바꿔야 할 때(예: 2026-09-29 Redis 편 재구성)는 옛 주소를 살려 둡니다. GitHub Pages는 서버 리다이렉트를 못 하므로 build가 옛 주소에 **안내 페이지**(자동 이동 + canonical + 새 편 링크)를 만듭니다.
1. `docs/articles.json`에서 해당 편의 `slug`를 바꾸고, `redirects`에 `{"from": "영역/NN-옛slug.html", "to": 편번호}`를 추가합니다. 옛 주소 여러 개가 한 편을 가리켜도 됩니다.
2. 새 파일을 만들거나 옛 파일을 새 이름으로 옮긴 뒤 `py tools/build.py` — 옛 주소 파일은 안내 페이지로 덮어써집니다(손으로 고치지 않음).
3. 사이트 안의 링크는 새 주소로 바꿉니다. 옛 주소를 가리키면 `redirect-links` 검사가 경고합니다.
4. push 후 `py tools/check_deploy.py`가 옛 주소가 새 편으로 넘어가는지도 확인합니다.
- 공개 전 편(아직 push 안 한 편)은 안내 페이지 없이 이름만 바꿉니다.
