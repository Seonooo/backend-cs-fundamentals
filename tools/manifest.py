"""docs/articles.json — the single list of areas, articles and connection keywords."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
REDIRECT_RE = re.compile(r"^[a-z0-9-]+/\d{2}-[a-z0-9]+(?:-[a-z0-9]+)*\.html$")


@dataclass(frozen=True)
class Article:
    no: int
    area: str
    slug: str
    title: str
    summary: str

    @property
    def nn(self) -> str:
        return f"{self.no:02d}"

    @property
    def path(self) -> str:  # relative to docs/
        return f"{self.area}/{self.nn}-{self.slug}.html"


@dataclass(frozen=True)
class Redirect:
    """An old article address kept alive after a rename: build writes a small page that forwards to article `to`."""
    src: str  # relative to docs/, e.g. "distributed/27-redis-basics.html"
    to: int

    @property
    def area(self) -> str:
        return self.src.split("/", 1)[0]


class ManifestError(ValueError):
    pass


class Manifest:
    def __init__(self, root: Path):
        self.path = root / "docs" / "articles.json"
        data = json.loads(self.path.read_text(encoding="utf-8"))
        self.areas: dict[str, str] = {a["id"]: a["name"] for a in data["areas"]}  # insertion order = display order
        self.articles = sorted((Article(**a) for a in data["articles"]), key=lambda a: a.no)
        self.keywords = data["keywords"]
        self.redirects = [Redirect(r["from"], r["to"]) for r in data.get("redirects", [])]
        self.by_no = {a.no: a for a in self.articles}
        self._validate()

    def _validate(self):
        problems = []
        if len(self.by_no) != len(self.articles):
            problems.append("같은 no가 두 번 이상 있음")
        for a in self.articles:
            if a.area not in self.areas:
                problems.append(f"{a.nn}: area '{a.area}'가 areas에 없음")
            if not SLUG_RE.match(a.slug):
                problems.append(f"{a.nn}: slug '{a.slug}'는 소문자·숫자·하이픈만")
        for k in self.keywords:
            for item in k["flow"]:
                no = item[0] if isinstance(item, list) else item
                if no not in self.by_no:
                    problems.append(f"키워드 '{k['name']}'의 {no}편이 articles에 없음")
        paths = {a.path for a in self.articles}
        seen = set()
        for r in self.redirects:
            if not REDIRECT_RE.match(r.src) or r.area not in self.areas:
                problems.append(f"redirect '{r.src}'는 '영역/NN-slug.html' 형식이어야 함")
            if r.src in paths:
                problems.append(f"redirect '{r.src}'가 현재 편의 경로와 같음")
            if r.src in seen:
                problems.append(f"redirect '{r.src}'가 두 번 이상 있음")
            seen.add(r.src)
            if r.to not in self.by_no:
                problems.append(f"redirect '{r.src}'의 대상 {r.to}편이 articles에 없음")
        if problems:
            raise ManifestError("; ".join(problems))

    def in_area(self, area: str) -> list[Article]:
        return [a for a in self.articles if a.area == area]

    def neighbours(self, article: Article) -> tuple[Article | None, Article | None]:
        i = self.articles.index(article)
        return (self.articles[i - 1] if i > 0 else None,
                self.articles[i + 1] if i + 1 < len(self.articles) else None)


def href(from_area: str | None, to: Article) -> str:
    """Relative link from a page in `from_area` (None = docs/index.html) to an article."""
    if from_area is None:
        return to.path
    return to.path.split("/", 1)[1] if from_area == to.area else f"../{to.path}"
