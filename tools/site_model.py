"""Shared model of the site: page discovery and HTML parsing used by all checks."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path

# Area folder -> name shown in the crumb. Add new areas here.
AREAS = {
    "os": "운영체제",
    "network": "네트워크",
    "database": "데이터베이스",
    "common": "공통 원리",
}
SITE_URL = "https://seonooo.github.io/backend-cs-fundamentals/"
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
ARTICLE_RE = re.compile(r"^(\d{2})-[a-z0-9-]+\.html$")


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


@dataclass
class Anchor:
    line: int
    href: str
    classes: set[str]
    context: str | None  # "pager", "idx", "crumb" or None
    text: str = ""
    span_text: str = ""  # text inside <span> (pager label)
    b_text: str = ""  # text inside <b> (index number)


@dataclass
class Page:
    path: Path  # absolute
    rel: str  # posix path relative to docs/, e.g. "os/01-process-thread.html"
    raw: str
    nn: int | None = None
    area: str | None = None
    title: str = ""
    h1: str = ""
    crumb: str = ""
    ids: set[str] = field(default_factory=set)
    anchors: list[Anchor] = field(default_factory=list)
    svg_refs: list[tuple[int, str]] = field(default_factory=list)
    class_elems: list[tuple[int, str, set[str]]] = field(default_factory=list)
    tag_issues: list[tuple[int, str]] = field(default_factory=list)

    def line_of(self, needle: str) -> int:
        idx = self.raw.find(needle)
        return self.raw.count("\n", 0, idx) + 1 if idx >= 0 else 1


class _Parser(HTMLParser):
    def __init__(self, page: Page):
        super().__init__(convert_charrefs=True)
        self.p = page
        self.stack: list[tuple[str, int]] = []
        self.captures: list[tuple[str, int]] = []  # (kind, stack depth at start)
        self.context: list[tuple[str, int]] = []  # ("pager"|"idx"|"crumb", depth)
        self.anchor: Anchor | None = None
        self.anchor_depth = 0
        self.inline: list[tuple[str, int]] = []  # span/b inside current anchor

    # --- helpers
    def _line(self) -> int:
        return self.getpos()[0]

    def _attrs(self, attrs):
        d = {k: (v or "") for k, v in attrs}
        return d, set(d.get("class", "").split())

    def _open(self, tag, attrs, self_closing):
        d, classes = self._attrs(attrs)
        line = self._line()
        if "id" in d:
            self.p.ids.add(d["id"])
        if classes:
            self.p.class_elems.append((line, tag, classes))
        for attr in ("marker-end", "marker-start", "marker-mid", "fill", "stroke", "clip-path", "mask", "filter"):
            for ref in re.findall(r"url\(#([^)]+)\)", d.get(attr, "")):
                self.p.svg_refs.append((line, ref))
        for ref in re.findall(r"url\(#([^)]+)\)", d.get("style", "")):
            self.p.svg_refs.append((line, ref))
        depth = len(self.stack)
        if tag == "a" and "href" in d:
            ctx = self.context[-1][0] if self.context else None
            self.anchor = Anchor(line, d["href"], classes, ctx)
            self.anchor_depth = depth
        elif self.anchor and tag in ("span", "b"):
            self.inline.append((tag, depth))
        if self_closing or tag in VOID_TAGS:
            return
        if tag == "title":
            self.captures.append(("title", depth))
        elif tag == "h1":
            self.captures.append(("h1", depth))
        elif tag == "div" and "crumb" in classes:
            self.captures.append(("crumb", depth))
            self.context.append(("crumb", depth))
        elif tag == "nav" and "pager" in classes:
            self.context.append(("pager", depth))
        elif tag == "div" and "idx" in classes:
            self.context.append(("idx", depth))
        self.stack.append((tag, line))

    # --- HTMLParser hooks
    def handle_starttag(self, tag, attrs):
        self._open(tag, attrs, False)

    def handle_startendtag(self, tag, attrs):
        self._open(tag, attrs, True)

    def handle_endtag(self, tag):
        if tag in VOID_TAGS:
            return
        line = self._line()
        if not any(t == tag for t, _ in self.stack):
            self.p.tag_issues.append((line, f"</{tag}> has no matching open tag"))
            return
        while self.stack:
            t, open_line = self.stack.pop()
            if t == tag:
                break
            self.p.tag_issues.append((open_line, f"<{t}> is not closed before </{tag}> (line {line})"))
        depth = len(self.stack)
        while self.captures and self.captures[-1][1] >= depth:
            self.captures.pop()
        while self.context and self.context[-1][1] >= depth:
            self.context.pop()
        while self.inline and self.inline[-1][1] >= depth:
            self.inline.pop()
        if self.anchor and tag == "a" and depth <= self.anchor_depth:
            self.anchor.text = norm(self.anchor.text)
            self.anchor.span_text = norm(self.anchor.span_text)
            self.anchor.b_text = norm(self.anchor.b_text)
            self.p.anchors.append(self.anchor)
            self.anchor = None
            self.inline.clear()

    def handle_data(self, data):
        for kind, _ in self.captures:
            setattr(self.p, kind, getattr(self.p, kind) + data)
        if self.anchor:
            if self.inline and self.inline[-1][0] == "span":
                self.anchor.span_text += data
            elif self.inline and self.inline[-1][0] == "b":
                self.anchor.b_text += data
            else:
                self.anchor.text += data

    def close(self):
        super().close()
        for t, line in self.stack:
            self.p.tag_issues.append((line, f"<{t}> is never closed"))


def parse_page(path: Path, docs: Path) -> Page:
    raw = path.read_text(encoding="utf-8")
    rel = path.relative_to(docs).as_posix()
    page = Page(path=path, rel=rel, raw=raw)
    m = ARTICLE_RE.match(path.name)
    if m and path.parent != docs:
        page.nn = int(m.group(1))
        page.area = path.parent.name
    parser = _Parser(page)
    parser.feed(raw)
    parser.close()
    page.title, page.h1, page.crumb = norm(page.title), norm(page.h1), norm(page.crumb)
    return page


class Site:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.docs = self.root / "docs"
        self.readme_path = self.root / "README.md"
        self.readme = self.readme_path.read_text(encoding="utf-8") if self.readme_path.exists() else ""
        self.pages: dict[str, Page] = {}
        for path in sorted(self.docs.rglob("*.html")):
            page = parse_page(path, self.docs)
            self.pages[page.rel] = page
        self.index = self.pages.get("index.html")
        self.articles = sorted((p for p in self.pages.values() if p.nn is not None), key=lambda p: p.nn)

    def resolve(self, page: Page, href: str) -> tuple[str | None, str | None]:
        """Return (target rel path or None if outside docs, fragment)."""
        path, _, frag = href.partition("#")
        if not path:
            return page.rel, frag or None
        target = (page.path.parent / path).resolve()
        try:
            return target.relative_to(self.docs).as_posix(), frag or None
        except ValueError:
            return None, frag or None

    def rel_of_url(self, url: str) -> str | None:
        """Map a published site URL to a docs-relative path."""
        if not url.startswith(SITE_URL):
            return None
        rest = url[len(SITE_URL):].split("#")[0]
        return rest or "index.html"

    def display(self, rel: str) -> str:
        """Repo-relative path for messages."""
        return rel if rel == "README.md" else f"docs/{rel}"
