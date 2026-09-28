"""The crumb must show the article's own number and its area name."""
from checks import Issue, Rule
from site_model import AREAS

RULE = Rule(
    id="crumb",
    severity="error",
    fix="div.crumb의 번호를 파일명 번호와, 영역명을 폴더의 영역명(tools/site_model.py AREAS)과 맞추세요",
)


def check(site):
    issues = []
    for page in site.articles:
        src = site.display(page.rel)
        line = page.line_of('class="crumb"')
        if not page.crumb:
            issues.append(Issue(src, line, "crumb 없음"))
            continue
        area = AREAS.get(page.area)
        if area is None:
            issues.append(Issue(src, line, f'영역 폴더 "{page.area}"가 tools/site_model.py AREAS에 없음'))
        elif area not in page.crumb:
            issues.append(Issue(src, line, f'crumb "{page.crumb}"에 영역명 "{area}" 없음'))
        if f"{page.nn:02d}" not in page.crumb:
            issues.append(Issue(src, line, f'crumb "{page.crumb}"에 번호 {page.nn:02d} 없음'))
    return issues
