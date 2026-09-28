"""Every relative href, #anchor and SVG url(#id) must point at something that exists."""
from checks import Issue, Rule

RULE = Rule(
    id="links",
    severity="error",
    fix="링크 대상 파일·id를 확인하세요. 파일을 옮겼다면 상대 경로(../)도 확인",
)
EXTERNAL = ("http://", "https://", "mailto:", "javascript:")


def check(site):
    issues = []
    for page in site.pages.values():
        src = site.display(page.rel)
        for a in page.anchors:
            if a.href.startswith(EXTERNAL):
                continue
            target, frag = site.resolve(page, a.href)
            if target is None or target not in site.pages and not (site.docs / target).exists():
                issues.append(Issue(src, a.line, f'"{a.href}" 파일이 없음'))
                continue
            if frag and target in site.pages and frag not in site.pages[target].ids:
                issues.append(Issue(src, a.line, f'"{a.href}"의 #{frag} 가 대상에 없음', (site.display(target),)))
        for line, ref in page.svg_refs:
            if ref not in page.ids:
                issues.append(Issue(src, line, f"url(#{ref}) 대상 id가 없음"))
        for rel in _stylesheets(page):
            if not (page.path.parent / rel).resolve().exists():
                issues.append(Issue(src, page.line_of(rel), f'스타일시트 "{rel}" 파일이 없음'))
    for n, line in enumerate(site.readme.splitlines(), 1):
        for url in _urls(line):
            rel = site.rel_of_url(url)
            if rel is not None and rel not in site.pages:
                issues.append(Issue("README.md", n, f'"{url}" 에 해당하는 docs 파일이 없음'))
    return issues


def _stylesheets(page):
    import re
    return [h for h in re.findall(r'<link rel="stylesheet" href="([^"]+)"', page.raw) if not h.startswith(EXTERNAL)]


def _urls(line):
    import re
    return re.findall(r"https://seonooo\.github\.io/backend-cs-fundamentals/[^\s)>\]*`]*", line)
