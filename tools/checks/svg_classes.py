"""t-s (small grey text) must not be combined with a colour text class: CSS order decides the colour."""
from checks import Issue, Rule

RULE = Rule(
    id="svg-classes",
    severity="error",
    origin="L-04",
    fix="색 글자는 sh-t·ok-t·bug-t만 단독으로 쓰세요 (t-b와는 함께 써도 됨, guides/svg.md)",
)
COLOURS = {"sh-t", "ok-t", "bug-t"}


def check(site):
    issues = []
    for page in site.pages.values():
        for line, tag, classes in page.class_elems:
            if "t-s" in classes and classes & COLOURS:
                issues.append(Issue(site.display(page.rel), line, f'<{tag} class="{" ".join(sorted(classes))}">'))
    return issues
