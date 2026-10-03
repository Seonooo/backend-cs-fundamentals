"""Check SVG figure labels with the real font, using headless Chrome (idea from Pretext: verify label overflow in development).

  py tools/check_figures.py            # all pages
  py tools/check_figures.py --changed  # only git-changed pages (if assets/style.css changed: all pages)
  py tools/check_figures.py docs/distributed/27-why-redis.html   # given files

For every <text> in every figure, after web fonts are loaded:
  out    the text goes outside the viewBox
  box    the text's center is inside a <rect> but the text is wider/taller than that rect (smallest enclosing rect)
  overlap two texts in the same figure overlap
Prints "OK (...)" or one line per problem. Exit code 1 on problems.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check import ROOT, changed_files  # noqa: E402
from check_mobile import find_chrome  # noqa: E402

TOLERANCE = 1.0  # SVG user units
OVERLAP_MIN = 3.0  # both sides of the intersection must exceed this many units

PROBE_JS = r"""
(async (pages, tol, ovMin) => {
  const out = [];
  let figs = 0, nTexts = 0;
  const load = url => new Promise(res => {
    const fr = document.createElement("iframe");
    fr.style.width = "900px"; fr.style.height = "800px";
    fr.onload = () => res(fr);
    fr.src = url; document.body.appendChild(fr);
  });
  const inDefs = el => !!el.closest("defs");
  for (const [name, url] of pages) {
    const fr = await load(url);
    try {
      const d = fr.contentDocument;
      await d.fonts.ready;
      await new Promise(r => setTimeout(r, 200));
      if (!d.fonts.check('13px Pretendard')) out.push({name, fig: 0, kind: "font", text: "Pretendard not loaded: widths measured with a fallback font", amount: 0});
      [...d.querySelectorAll("figure svg")].forEach((svg, fi) => {
        const vb = svg.viewBox.baseVal;
        const texts = [...svg.querySelectorAll("text")].filter(t => !inDefs(t) && t.textContent.trim());
        const rects = [...svg.querySelectorAll("rect")].filter(r => !inDefs(r))
          .map(r => { const b = r.getBBox(); return {x: b.x, y: b.y, w: b.width, h: b.height}; })
          .filter(r => r.w > 0 && r.h > 0);
        const boxes = texts.map(t => { const b = t.getBBox(); return {t: t.textContent.trim().slice(0, 40), x: b.x, y: b.y, w: b.width, h: b.height}; });
        const fig = fi + 1;
        figs++; nTexts += boxes.length;
        for (const b of boxes) {
          const over = Math.max(vb.x - b.x, b.x + b.w - (vb.x + vb.width), vb.y - b.y, b.y + b.h - (vb.y + vb.height));
          if (over > tol) out.push({name, fig, kind: "out", text: b.t, amount: +over.toFixed(1)});
          const cx = b.x + b.w / 2, cy = b.y + b.h / 2;
          const enclosing = rects.filter(r => cx >= r.x && cx <= r.x + r.w && cy >= r.y && cy <= r.y + r.h)
            .sort((a, c) => a.w * a.h - c.w * c.h)[0];
          if (enclosing) {
            const o = Math.max(enclosing.x - b.x, b.x + b.w - (enclosing.x + enclosing.w));
            if (o > tol) out.push({name, fig, kind: "box", text: b.t, amount: +o.toFixed(1)});
          }
        }
        for (let i = 0; i < boxes.length; i++) for (let j = i + 1; j < boxes.length; j++) {
          const a = boxes[i], c = boxes[j];
          const ix = Math.min(a.x + a.w, c.x + c.w) - Math.max(a.x, c.x);
          const iy = Math.min(a.y + a.h, c.y + c.h) - Math.max(a.y, c.y);
          if (ix > ovMin && iy > ovMin) out.push({name, fig, kind: "overlap", text: a.t + "  ×  " + c.t, amount: +Math.min(ix, iy).toFixed(1)});
        }
      });
    } catch (e) { out.push({name, fig: 0, kind: "error", text: String(e), amount: 0}); }
    fr.remove();
  }
  document.getElementById("OUT").textContent = JSON.stringify({problems: out, figs, texts: nTexts});
})(PAGES, TOL, OVMIN);
"""

LABEL = {"out": "그림 밖으로 나감", "box": "상자보다 넓음", "overlap": "글자끼리 겹침", "font": "글꼴 미로드(네트워크 확인)", "error": "검사 오류"}


def _display(p: Path) -> str:
    try:
        return p.resolve().relative_to(ROOT).as_posix()
    except ValueError:  # copies made by tools/test_figures.py
        return p.as_posix()


def probe(pages: list[Path]) -> dict | None:
    entries = [[_display(p), p.resolve().as_uri()] for p in pages]
    script = (PROBE_JS.replace("PAGES", json.dumps(entries))
              .replace("OVMIN", json.dumps(OVERLAP_MIN)).replace("TOL", json.dumps(TOLERANCE)))
    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / "probe.html"
        page.write_text(f'<!doctype html><meta charset="utf-8"><pre id="OUT">pending</pre><script>{script}</script>', encoding="utf-8")
        cmd = [find_chrome(), "--headless=new", "--disable-gpu", "--allow-file-access-from-files",
               f"--user-data-dir={Path(tmp) / 'profile'}", "--virtual-time-budget=180000", "--dump-dom", page.as_uri()]
        dom = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=600).stdout
    m = re.search(r'<pre id="OUT">(.*?)</pre>', dom, re.S)
    if not m or m.group(1).strip() == "pending":
        return None
    return json.loads(html.unescape(m.group(1)))


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--changed", action="store_true")
    ap.add_argument("files", nargs="*", type=Path)
    args = ap.parse_args()

    docs = ROOT / "docs"
    if args.files:
        pages = [f.resolve() for f in args.files]
    else:
        pages = sorted(p for p in docs.rglob("*.html") if "<figure>" in p.read_text(encoding="utf-8"))
        if args.changed:
            changed = changed_files(ROOT)
            if "docs/assets/style.css" not in changed:
                pages = [p for p in pages if p.relative_to(ROOT).as_posix() in changed]
    if not pages:
        print("OK (no pages with figures to check)")
        return 0
    res = probe(pages)
    if res is None:
        print("ERROR: headless Chrome did not finish the probe")
        return 2
    results = res["problems"]
    if res["texts"] == 0:
        print("ERROR: no figure labels were measured (did the pages load?)")
        return 2
    scope = f"{len(pages)} pages, {res['figs']} figures, {res['texts']} labels"
    if not results:
        print(f"OK ({scope})")
        return 0
    for r in results:
        print(f"{r['name']} 그림{r['fig']} [{r['kind']}] {LABEL[r['kind']]} {r['amount']} — {r['text']}")
    print("    → 글자를 줄이거나 상자·간격을 넓히세요. 의도한 배치면 좌표를 조정해 경계에서 1 이상 떨어뜨립니다 (guides/svg.md)")
    print(f"{len(results)} problem(s) ({scope})")
    return 1


if __name__ == "__main__":
    sys.exit(main())
