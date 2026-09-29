"""'다음으로 이어지는 개념' items written as '→ NN 제목' must name a real article with a matching title.

The title may be shortened (a prefix of the real title) and may end with " (복습)"; a wrong number is what this catches.
"""
import re

from checks import Issue, Rule
from manifest import Manifest, ManifestError

RULE = Rule(
    id="next-links",
    severity="error",
    fix='"→ NN 제목"의 번호가 맞는지 확인하세요. 제목은 실제 제목이거나 그 앞부분이어야 함 (끝에 " (복습)" 허용)',
)
ITEM = re.compile(r"<b>→ (\d{2}) ([^<]*)</b>")


def check(site):
    try:
        manifest = Manifest(site.root)
    except (ManifestError, OSError, ValueError):
        return []  # reported by the generated rule
    issues = []
    for page in site.pages.values():
        for m in ITEM.finditer(page.raw):
            no, text = int(m.group(1)), m.group(2).removesuffix(" (복습)")
            line = page.raw.count("\n", 0, m.start()) + 1
            target = manifest.by_no.get(no)
            if target is None:
                issues.append(Issue(site.display(page.rel), line, f"→ {m.group(1)}: 없는 편"))
            elif not target.title.startswith(text):
                issues.append(Issue(site.display(page.rel), line, f'→ {m.group(1)} "{text}" ≠ {target.nn}편 제목 "{target.title}"',
                                    ("docs/articles.json",)))
    return issues
