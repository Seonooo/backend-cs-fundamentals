"""Previous/next links must point at the adjacent articles, with matching number and title."""
from checks import Issue, Rule
from site_model import norm

RULE = Rule(
    id="pager",
    severity="error",
    fix="nav.pager의 이전/다음 링크를 번호상 바로 앞뒤 편으로 맞추고, 라벨 번호와 제목을 대상 편 <h1>과 같게",
)


def check(site):
    issues = []
    arts = site.articles
    for i, page in enumerate(arts):
        src = site.display(page.rel)
        pager = [a for a in page.anchors if a.context == "pager"]
        expected = {"이전": arts[i - 1] if i > 0 else None, "다음": arts[i + 1] if i + 1 < len(arts) else None}
        for kind, target in expected.items():
            found = [a for a in pager if ("nx" in a.classes) == (kind == "다음")]
            if target is None:
                if found:
                    issues.append(Issue(src, found[0].line, f"{kind} 링크가 있지만 {kind} 편이 없음"))
                continue
            if not found:
                issues.append(Issue(src, page.line_of('class="pager"'), f"{kind} 링크 없음 (→ {target.nn:02d})", (site.display(target.rel),)))
                continue
            a = found[0]
            rel, _ = site.resolve(page, a.href)
            related = (site.display(target.rel),)
            if rel != target.rel:
                issues.append(Issue(src, a.line, f'{kind} 링크 "{a.href}" → 기대값 {target.rel}', related))
            if f"{target.nn:02d}" not in a.span_text:
                issues.append(Issue(src, a.line, f'{kind} 라벨 "{a.span_text}"에 {target.nn:02d} 없음', related))
            if norm(a.text) != target.h1:
                issues.append(Issue(src, a.line, f'{kind} 제목 "{a.text}" ≠ 대상 <h1> "{target.h1}"', related))
    return issues
