"""Check that no page scrolls horizontally on phone widths (320px, 375px), using headless Chrome.

  py tools/check_mobile.py            # all pages
  py tools/check_mobile.py --changed  # only git-changed pages (if assets/style.css changed: all pages)

Prints "OK (...)" or each overflowing page with the element that causes it. Exit code 1 on overflow.
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check import ROOT, changed_files  # noqa: E402

WIDTHS = (320, 375)
CHROME_CANDIDATES = [
    os.environ.get("CHROME", ""),
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "google-chrome", "chromium", "chromium-browser", "chrome", "msedge",
]

# Loads each page in an iframe of the given width. When a page overflows, hides elements one by one
# (top-level children of .wrap, then leaves inside the culprit) to find what causes the overflow.
PROBE_JS = r"""
(async (pages, widths) => {
  const out = [];
  const load = (url, w) => new Promise(res => {
    const fr = document.createElement("iframe");
    fr.style.width = w + "px"; fr.style.height = "800px";
    fr.onload = () => setTimeout(() => res(fr), 300);
    fr.src = url; document.body.appendChild(fr);
  });
  for (const w of widths) for (const [name, url] of pages) {
    const fr = await load(url, w);
    try {
      const d = fr.contentDocument, de = d.documentElement;
      const ov = () => de.scrollWidth - de.clientWidth;
      const total = ov();
      if (total > 0) {
        let culprit = "";
        const root = d.querySelector(".wrap") || d.body;
        for (const k of root.children) {
          const old = k.style.display; k.style.display = "none"; const o = ov(); k.style.display = old;
          if (o < total) {
            culprit = k.tagName.toLowerCase();
            for (const c of k.querySelectorAll("*")) {
              if (c.children.length) continue;
              const od = c.style.display; c.style.display = "none"; const o2 = ov(); c.style.display = od;
              if (o2 < total) { culprit += " > " + c.tagName.toLowerCase() + ' "' + c.textContent.trim().slice(0, 50) + '"'; break; }
            }
            break;
          }
        }
        out.push({w, name, overflow: total, culprit});
      }
    } catch (e) { out.push({w, name, error: String(e)}); }
    fr.remove();
  }
  document.getElementById("OUT").textContent = JSON.stringify(out);
})(PAGES, WIDTHS);
"""


def find_chrome() -> str:
    for c in CHROME_CANDIDATES:
        if not c:
            continue
        if Path(c).exists():
            return c
        found = shutil.which(c)
        if found:
            return found
    sys.exit("Chrome/Edge not found. Set the CHROME environment variable to the browser executable.")


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--changed", action="store_true")
    args = ap.parse_args()

    docs = ROOT / "docs"
    pages = sorted(p.relative_to(docs).as_posix() for p in docs.rglob("*.html"))
    if args.changed:
        changed = changed_files(ROOT)
        if "docs/assets/style.css" not in changed:
            pages = [p for p in pages if f"docs/{p}" in changed]
        if not pages:
            print("OK (no changed pages)")
            return 0

    entries = [[p, (docs / p).resolve().as_uri()] for p in pages]
    script = PROBE_JS.replace("PAGES", json.dumps(entries)).replace("WIDTHS", json.dumps(list(WIDTHS)))
    with tempfile.TemporaryDirectory() as tmp:
        probe = Path(tmp) / "probe.html"
        probe.write_text(f'<!doctype html><meta charset="utf-8"><pre id="OUT">pending</pre><script>{script}</script>', encoding="utf-8")
        cmd = [find_chrome(), "--headless=new", "--disable-gpu", "--allow-file-access-from-files",
               f"--user-data-dir={Path(tmp) / 'profile'}", "--virtual-time-budget=120000", "--dump-dom", probe.as_uri()]
        dom = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=300).stdout
    m = re.search(r'<pre id="OUT">(.*?)</pre>', dom, re.S)
    if not m or m.group(1).strip() == "pending":
        print("ERROR: headless Chrome did not finish the probe")
        return 2
    results = json.loads(html.unescape(m.group(1)))
    scope = f"{len(pages)} pages × {'/'.join(map(str, WIDTHS))}px"
    if not results:
        print(f"OK ({scope})")
        return 0
    for r in results:
        if "error" in r:
            print(f"docs/{r['name']} @{r['w']}px ERROR {r['error']}")
        else:
            print(f"docs/{r['name']} @{r['w']}px overflow {r['overflow']}px ← {r['culprit'] or '(원인 요소를 특정하지 못함)'}")
    print("    → 긴 영문 식별자·코드는 줄바꿈 가능 여부를, 표·그림은 가로 스크롤 상자 안에 있는지 확인하세요 (L-03)")
    print(f"{len(results)} overflow(s) ({scope})")
    return 1


if __name__ == "__main__":
    sys.exit(main())
