"""<title> and <h1> of every page must agree, and an article's <h1> must equal its title in docs/articles.json."""
from checks import Issue, Rule
from manifest import Manifest, ManifestError

RULE = Rule(
    id="titles",
    severity="error",
    fix="제목을 바꿀 때는 docs/articles.json의 title과 페이지의 <title>·<h1>을 함께 고치고 py tools/build.py",
)


def check(site):
    issues = []
    for page in site.pages.values():
        if page.title != page.h1:
            issues.append(Issue(site.display(page.rel), page.line_of("<title>"), f'<title> "{page.title}" ≠ <h1> "{page.h1}"'))
    try:
        manifest = Manifest(site.root)
    except (ManifestError, OSError, ValueError):
        return issues  # reported by the generated rule
    for a in manifest.articles:
        page = site.pages.get(a.path)
        if page and page.h1 != a.title:
            issues.append(Issue(site.display(a.path), page.line_of("<h1>"), f'<h1> "{page.h1}" ≠ articles.json title "{a.title}"',
                                ("docs/articles.json",)))
    return issues
