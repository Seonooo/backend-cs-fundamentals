# 페이지 골격과 컴포넌트

> **읽는 시점**: `docs/` 페이지의 HTML을 만들거나 고칠 때. 그림은 `guides/svg.md`, 문장은 `guides/writing.md`를 함께 봅니다.

## 골격
모든 편은 아래 순서를 따릅니다. `docs/os/07-thread-pool.html`을 참고하세요.

```html
<!DOCTYPE html>
<html lang="ko"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>편 제목</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/pretendard@1.3.9/dist/web/static/pretendard.min.css">
<link rel="stylesheet" href="../assets/style.css"></head><body><div class="wrap">
<div class="crumb"><a href="../index.html">백엔드 CS 기본기</a> · 영역명 · NN / 전체편수</div><h1>편 제목</h1>
<p class="lead">앞 편과의 연결 + 이 편에서 얻을 것 (핵심어는 <b>)</p>
<nav class="toc"><a href="#id">1. 절 제목</a> … <a href="#cases">N. 실무 예시</a><a href="#check">N+1. 설명해보기</a></nav>

<h2 id="…"><span class="n">1</span>개념 절 제목</h2>   ← 개념 절 2~5개 (그림·표 포함)
…
<h2 id="cases"><span class="n">N</span>실무 예시</h2>    ← .case 여러 개
<div class="skipbox"><b>지금은 넘어가도 되는 것</b> · …</div>
<h2 id="check"><span class="n">N+1</span>설명해보기</h2>
<p class="muted">답을 열기 전에 먼저 소리 내어 설명해 보세요.</p>
<details><summary>질문</summary><div class="a">답</div></details> …
<h3>다음으로 이어지는 개념</h3>
<div class="next"><div><b>→ NN 편 제목</b><span>한 줄 설명</span></div> …</div>
<nav class="pager"><a href="이전.html"><span>← 이전 NN</span>제목</a><a class="nx" href="다음.html"><span>다음 NN →</span>제목</a></nav>
</div></body></html>
```

- `<title>`, `<h1>`, `index.html` 목차, 앞뒤 편 pager, `README.md` 표의 제목은 모두 같아야 합니다.
- 절 제목은 결론형 문장으로 씁니다. 예: "인덱스가 없으면 전부 읽는다", "캐리어는 기다리는 동안 자리를 비켜 준다"
- 첫 편에는 이전 링크가 없고, **최신 편**에는 다음 링크가 없습니다.
- crumb의 `NN / 전체편수` 형식은 `plan/do/2026-09-29-open-ended-series.md`에서 바뀔 수 있습니다.
- 페이지 안에 `<style>`을 두지 않습니다. 스타일은 `docs/assets/style.css` 한 곳에서 관리합니다.

## 컴포넌트

| 요소 | 마크업 | 쓰임 |
|---|---|---|
| 핵심 박스 | `<div class="key"><b>핵심</b> — …</div>` | 절의 결론 한 줄 |
| 보조 문단 | `<p class="muted">` | 주의·각주·"설명해보기" 안내 |
| 사례 | `<div class="case"><span class="tag X">라벨</span><h3>…</h3>…</div>` | 실무 예시 한 건 |
| 사례 라벨 | `tag b` 실수 예시 · `tag g` 좋은 패턴 · `tag i` 설계 이유 / 장애 대응 / 운영 설정 / 매일 보는 곳 / 용어 정리 | 사례 종류 |
| 코드 | `<div class="code bad\|good\|plain"><div class="hd">✕ … / ✓ … / 제목</div><pre>…</pre></div>` | 틀린 코드, 고친 코드, 일반 코드 |
| 코드 주석 강조 | `<span class="c">` 회색 · `r` 빨강 · `g` 초록 · `s` 파랑 (pre 안에서) | 코드 안 설명 |
| 나란히 | `<div class="two">` | 코드 두 개를 좌우로 비교 |
| 비유 | `<div class="analogy">` | 개념을 일상 비유와 나란히 |
| 단계 목록 | `<ol class="steps">` | 순서가 있는 규칙·절차 |
| 인라인 코드 | `<code class="i">` | 본문 속 코드·설정명 |
| 표 강조 | `<td class="hl">` | 표에서 핵심 칸 |
| 넘어가도 되는 것 | `<div class="skipbox">` | 깊은 내용, 정확성 보강, 용어 이름만 남기기 |

## 스크립트로 못 하는 확인
자동 검사(`tools/`)를 통과해도 아래는 눈으로 확인합니다.
- **화면**: 헤드리스 Chrome으로 스크린샷을 찍어 봅니다. 라이트 테마는 `<html data-theme="light">`, 다크 테마는 시스템 설정을 따릅니다. 새 그림은 두 테마 모두 봅니다.
- **그림 설명 일치**: SVG `aria-label`과 캡션이 그림 내용과 맞는지 봅니다(`guides/svg.md`).
- **같은 편 안의 반복 표현**: 본문을 고치면 같은 편의 "설명해보기" 답변과 요약 문장에도 같은 표현이 남았는지 봅니다.
