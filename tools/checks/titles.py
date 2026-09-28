"""<title>, <h1>, the index list and the README table must all use the same title."""
import re

from checks import Issue, Rule

RULE = Rule(
    id="titles",
    severity="error",
    fix="제목을 한 곳에서 바꿨다면 <title>, <h1>, docs/index.html 목차, README.md 목차 표를 모두 같게",
)
README_ROW = re.compile(r"^\| (\d{2}) \| \[([^\]]+)\]\(([^)]+)\) \|")


def check(site):
    issues = []
    for page in site.pages.values():
        if page.title != page.h1:
            issues.append(Issue(site.display(page.rel), page.line_of("<title>"), f'<title> "{page.title}" ≠ <h1> "{page.h1}"'))

    by_rel = {p.rel: p for p in site.articles}
    if site.index:
        seen = set()
        for a in (a for a in site.index.anchors if a.context == "idx"):
            rel, _ = site.resolve(site.index, a.href)
            target = by_rel.get(rel)
            if target is None:
                continue  # broken link is reported by the links rule
            seen.add(rel)
            related = (site.display(rel),)
            if a.b_text != f"{target.nn:02d}":
                issues.append(Issue("docs/index.html", a.line, f'목차 번호 "{a.b_text}" → {rel}은 {target.nn:02d}', related))
            if a.text != target.h1:
                issues.append(Issue("docs/index.html", a.line, f'목차 제목 "{a.text}" ≠ <h1> "{target.h1}"', related))
        for rel in by_rel.keys() - seen:
            issues.append(Issue("docs/index.html", 1, f"목차에 {rel} 없음", (site.display(rel),)))

    if site.readme:
        seen = set()
        for n, line in enumerate(site.readme.splitlines(), 1):
            m = README_ROW.match(line)
            if not m:
                continue
            nn, title, url = m.groups()
            rel = site.rel_of_url(url)
            target = by_rel.get(rel)
            if target is None:
                continue  # reported by the links rule
            seen.add(rel)
            related = (site.display(rel),)
            if nn != f"{target.nn:02d}":
                issues.append(Issue("README.md", n, f"목차 번호 {nn} → {rel}은 {target.nn:02d}", related))
            if title != target.h1:
                issues.append(Issue("README.md", n, f'목차 제목 "{title}" ≠ <h1> "{target.h1}"', related))
        for rel in by_rel.keys() - seen:
            issues.append(Issue("README.md", 1, f"목차 표에 {rel} 없음", (site.display(rel),)))
    return issues
