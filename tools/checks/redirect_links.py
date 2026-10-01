"""Links inside the site should point at the renamed article, not at a generated forwarding page (articles.json "redirects")."""
from checks import Issue, Rule

RULE = Rule(
    id="redirect-links",
    severity="warn",
    fix="옮긴 편의 옛 주소입니다. 링크를 새 편 주소로 바꾸세요 (옛 주소 안내 페이지는 외부 링크용)",
)
EXTERNAL = ("http://", "https://", "mailto:", "javascript:")


def check(site):
    issues = []
    for page in site.pages.values():
        if page.redirect:
            continue
        for a in page.anchors:
            if a.href.startswith(EXTERNAL):
                continue
            target, _ = site.resolve(page, a.href)
            if target in site.pages and site.pages[target].redirect:
                issues.append(Issue(site.display(page.rel), a.line, f'"{a.href}"는 옮긴 편의 옛 주소', (site.display(target),)))
    return issues
