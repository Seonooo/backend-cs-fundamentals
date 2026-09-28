"""The keyword map on the site and in README.md must be identical (including hints in parentheses)."""
import re

from checks import Issue, Rule
from site_model import norm

RULE = Rule(
    id="keyword-map",
    severity="error",
    origin="L-10",
    fix="사이트의 연결 키워드 지도와 README.md '관통하는 연결 키워드' 표를 똑같이 (괄호 힌트 포함)",
)
MAP_TITLE = "연결 키워드 지도"
README_SECTION = "## 관통하는 연결 키워드"


def site_map(site):
    for page in site.pages.values():
        m = next((h for h in re.finditer(r"<h2[^>]*>(.*?)</h2>", page.raw, re.S) if MAP_TITLE in h.group(1)), None)
        if not m:
            continue
        end = page.raw.find("<h2", m.end())
        section = page.raw[m.end(): end if end > 0 else None]
        rows = {}
        for tr in re.findall(r"<tr>(.*?)</tr>", section, re.S):
            cells = [norm(re.sub(r"<[^>]+>", "", c)) for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
            if len(cells) == 3:
                rows[cells[0]] = (cells[1], cells[2])
        return page, rows
    return None, {}


def readme_map(site):
    text = site.readme
    start = text.find(README_SECTION)
    if start < 0:
        return {}, 1
    end = text.find("\n## ", start + 1)
    rows = {}
    for line in text[start: end if end > 0 else None].splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 3 and cells[0] not in ("연결 키워드", "---") and not set(cells[0]) <= {"-"}:
            rows[cells[0]] = (cells[1], cells[2])
    return rows, text.count("\n", 0, start) + 1


def check(site):
    page, on_site = site_map(site)
    if page is None:
        return [Issue("docs/index.html", 1, f'"{MAP_TITLE}" 절을 가진 페이지가 없음')]
    in_readme, line = readme_map(site)
    related = (site.display(page.rel),)
    issues = []
    for key in on_site.keys() | in_readme.keys():
        if key not in in_readme:
            issues.append(Issue("README.md", line, f'키워드 "{key}"가 README에 없음', related))
        elif key not in on_site:
            issues.append(Issue("README.md", line, f'키워드 "{key}"가 사이트 지도에 없음', related))
        elif on_site[key] != in_readme[key]:
            issues.append(Issue("README.md", line, f'"{key}" 불일치: 사이트 {on_site[key]} / README {in_readme[key]}', related))
    return issues
