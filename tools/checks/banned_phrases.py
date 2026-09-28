"""The series is open-ended: no wording may assume a final article or a fixed total."""
import re

from checks import Issue, Rule

RULE = Rule(
    id="banned-phrases",
    severity="error",  # raised from warn once the site was cleaned up (plan 2026-09-29-open-ended-series)
    origin="L-02",
    fix="끝이나 전체 편수를 전제하는 표현을 빼세요 (guides/writing.md, guides/new-article.md)",
)
PATTERNS = [
    (re.compile(r"마지막 편"), '"마지막 편"'),
    (re.compile(r"마지막 \d+편"), '"마지막 N편"'),
    (re.compile(r"\d+편을 지나오며"), '"N편을 지나오며"'),
    (re.compile(r"\d+편 마지막의"), '"N편 마지막의"'),  # "07편 마지막 예시"처럼 편 안의 위치를 뜻하는 표현은 제외
    (re.compile(r"마지막 풀"), '"마지막 풀"'),
    (re.compile(r"\b\d{2} / \d{2,}\b"), '전체 편수 표기 "NN / 전체"'),
]


def check(site):
    issues = []
    sources = [(site.display(p.rel), p.raw) for p in site.pages.values()] + [("README.md", site.readme)]
    for name, text in sources:
        for n, line in enumerate(text.splitlines(), 1):
            for pattern, label in PATTERNS:
                if pattern.search(line):
                    issues.append(Issue(name, n, f"{label} 표현"))
    return issues
