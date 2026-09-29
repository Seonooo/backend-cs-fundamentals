"""Regenerate the parts of the site that follow from docs/articles.json.

  py tools/build.py          # write changed files
  py tools/build.py --check  # only report which files are out of date (exit 1)

Generated:
  docs/index.html   <!-- gen:index-toc --> article list, <!-- gen:index-map --> keyword map table
  README.md         <!-- gen:readme-toc --> tables per area, <!-- gen:readme-map --> keyword table
  every article     <div class="crumb"> and <nav class="pager"> (replaced as whole elements)
Everything else is written by hand. Files whose content would not change are not touched.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from manifest import Manifest, href  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
from site_model import SITE_URL  # noqa: E402
NOTE = "자동 생성 — docs/articles.json을 고치고 py tools/build.py"


class BuildError(ValueError):
    pass


# ---------- renderers
def crumb(m: Manifest, a) -> str:
    return f'<div class="crumb"><a href="../index.html">백엔드 CS 기본기</a> · {m.areas[a.area]} · {a.nn}편</div>'


def pager(m: Manifest, a) -> str:
    prev, nxt = m.neighbours(a)
    parts = []
    if prev:
        parts.append(f'<a href="{href(a.area, prev)}"><span>← 이전 {prev.nn}</span>{prev.title}</a>')
    if nxt:
        parts.append(f'<a class="nx" href="{href(a.area, nxt)}"><span>다음 {nxt.nn} →</span>{nxt.title}</a>')
    return f'<nav class="pager">{"".join(parts)}</nav>'


def index_toc(m: Manifest) -> str:
    out = []
    for area, name in m.areas.items():
        links = "".join(f'<a href="{href(None, a)}"><b>{a.nn}</b>{a.title}</a>' for a in m.in_area(area))
        out.append(f'<div class="idx-area">{name}</div><div class="idx">{links}</div>')
    return "".join(out)


def flow_html(m: Manifest, flow) -> str:
    items = []
    for item in flow:
        no, hint = (item[0], item[1]) if isinstance(item, list) else (item, None)
        a = m.by_no[no]
        items.append(f'<a href="{href(None, a)}">{a.nn}</a>' + (f"({hint})" if hint else ""))
    return " → ".join(items)


def flow_text(m: Manifest, flow) -> str:
    return " → ".join(f"{i[0]:02d}({i[1]})" if isinstance(i, list) else f"{i:02d}" for i in flow)


def index_map(m: Manifest) -> str:
    rows = [f"  <tr><td><b>{k['name']}</b></td><td>{k['question']}</td><td>{flow_html(m, k['flow'])}</td></tr>" for k in m.keywords]
    return "\n".join(["<table>", "  <tr><th>연결 키워드</th><th>반복되는 질문</th><th>등장한 편</th></tr>", *rows, "</table>"])


def readme_toc(m: Manifest) -> str:
    blocks = []
    for area, name in m.areas.items():
        rows = [f"| {a.nn} | [{a.title}]({SITE_URL}{a.path}) | {a.summary} |" for a in m.in_area(area)]
        blocks.append("\n".join([f"### {name}", "", "| # | 편 | 한 줄 요약 |", "|---|---|---|", *rows]))
    return "\n\n".join(blocks)


def readme_map(m: Manifest) -> str:
    rows = [f"| {k['name']} | {k['question']} | {flow_text(m, k['flow'])} |" for k in m.keywords]
    return "\n".join(["| 연결 키워드 | 반복되는 질문 | 등장한 편 |", "|---|---|---|", *rows])


# ---------- replacement helpers
def replace_region(text: str, name: str, content: str, where: str) -> str:
    pattern = re.compile(rf"(<!-- gen:{re.escape(name)}\b[^>]*-->\n)(.*?)(\n<!-- /gen:{re.escape(name)} -->)", re.S)
    found = pattern.findall(text)
    if len(found) != 1:
        raise BuildError(f"{where}: 생성 구간 gen:{name}이 {len(found)}개 (정확히 1개여야 함)")
    return pattern.sub(lambda mt: mt.group(1) + content + mt.group(3), text)


def replace_element(text: str, pattern: str, content: str, where: str) -> str:
    rx = re.compile(pattern, re.S)
    n = len(rx.findall(text))
    if n != 1:
        raise BuildError(f"{where}: 교체할 요소가 {n}개 (정확히 1개여야 함): {pattern}")
    return rx.sub(lambda _: content, text)


# ---------- build
def render(root: Path = ROOT) -> dict[Path, tuple[str, str]]:
    """Return {path: (current_text, generated_text)} for every generated file."""
    m = Manifest(root)
    docs = root / "docs"
    out: dict[Path, tuple[str, str]] = {}

    idx = docs / "index.html"
    cur = idx.read_text(encoding="utf-8")
    new = replace_region(cur, "index-toc", index_toc(m), "docs/index.html")
    out[idx] = (cur, replace_region(new, "index-map", index_map(m), "docs/index.html"))

    readme = root / "README.md"
    cur = readme.read_text(encoding="utf-8")
    new = replace_region(cur, "readme-toc", readme_toc(m), "README.md")
    out[readme] = (cur, replace_region(new, "readme-map", readme_map(m), "README.md"))

    for a in m.articles:
        page = docs / a.path
        if not page.exists():
            raise BuildError(f"docs/{a.path}: articles.json에 있지만 파일이 없음")
        cur = page.read_text(encoding="utf-8")
        new = replace_element(cur, r'<div class="crumb">.*?</div>', crumb(m, a), f"docs/{a.path}")
        out[page] = (cur, replace_element(new, r'<nav class="pager">.*?</nav>', pager(m, a), f"docs/{a.path}"))

    listed = {docs / a.path for a in m.articles}
    for page in docs.glob("*/*.html"):
        if re.match(r"\d{2}-", page.name) and page not in listed:
            raise BuildError(f"docs/{page.relative_to(docs).as_posix()}: 파일은 있지만 articles.json에 없음")
    return out


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="report out-of-date files without writing")
    args = ap.parse_args()
    try:
        results = render()
    except (BuildError, ValueError) as e:
        print(f"ERROR {e}")
        return 1
    stale = [p for p, (cur, new) in results.items() if cur != new]
    for p in stale:
        rel = p.relative_to(ROOT).as_posix()
        if args.check:
            print(f"out of date: {rel}")
        else:
            p.write_text(results[p][1], encoding="utf-8")
            print(f"updated: {rel}")
    if not stale:
        print(f"OK ({len(results)} files up to date)")
    return 1 if (args.check and stale) else 0


if __name__ == "__main__":
    sys.exit(main())
