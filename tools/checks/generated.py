"""Generated parts (index list and map, README tables, crumbs, pagers) must match docs/articles.json."""
from build import BuildError, render
from checks import Issue, Rule
from manifest import ManifestError

RULE = Rule(
    id="generated",
    severity="error",
    fix="docs/articles.json을 기준으로 py tools/build.py를 실행하세요 (생성 구간은 손으로 고치지 않음)",
)


def check(site):
    try:
        results = render(site.root)
    except (BuildError, ManifestError) as e:
        return [Issue("docs/articles.json", 1, str(e))]
    issues = []
    for path, (cur, new) in results.items():
        if cur != new:
            rel = path.relative_to(site.root).as_posix()
            issues.append(Issue(rel, 1, "생성 구간이 articles.json과 다름", ("docs/articles.json",)))
    return issues
