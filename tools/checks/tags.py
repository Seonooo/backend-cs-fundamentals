"""Every opened HTML element must be closed in order."""
from checks import Issue, Rule

RULE = Rule(
    id="tags",
    severity="error",
    origin="L-05",
    fix="여는 태그와 닫는 태그의 짝을 맞추세요 (문자열 치환으로 태그 일부만 바뀌지 않았는지 확인)",
)


def check(site):
    return [Issue(site.display(p.rel), line, msg) for p in site.pages.values() for line, msg in p.tag_issues]
