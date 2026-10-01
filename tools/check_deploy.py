"""After a push: wait for the GitHub Pages build of HEAD, then check that every page is served.

  py tools/check_deploy.py                                  # wait for HEAD build, check all pages return 200
  py tools/check_deploy.py --expect "network/12-http.html::HOL(Head-of-Line)"   # also check wording (repeatable)
  py tools/check_deploy.py --no-wait                        # only check pages

Old article addresses in docs/articles.json "redirects" must also forward to their new article.

If no build for HEAD appears (e.g. after changing the Pages source path), a rebuild is requested once (L-07).
Pages are fetched with a cache-busting query; browsers may still show the old page for 10 minutes (L-08).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check import ROOT  # noqa: E402
from manifest import Manifest, href  # noqa: E402


def sh(*cmd: str) -> str:
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", check=True, cwd=ROOT).stdout.strip()


def gh_api(path: str, method: str = "GET") -> dict | list:
    return json.loads(sh("gh", "api", "-X", method, path) or "{}")


def repo_slug() -> str:
    url = sh("git", "remote", "get-url", "origin")
    return url.rstrip("/").removesuffix(".git").split("github.com")[-1].lstrip(":/")


def wait_for_build(repo: str, head: str, timeout: int) -> bool:
    start, requested = time.time(), False
    while time.time() - start < timeout:
        latest = gh_api(f"repos/{repo}/pages/builds/latest")
        commit, status = latest.get("commit", ""), latest.get("status", "")
        if commit.startswith(head) and status == "built":
            return True
        if status == "errored" and commit.startswith(head):
            print(f"ERROR: Pages build for {head[:7]} errored")
            return False
        if not requested and time.time() - start > 60 and not commit.startswith(head) and status == "built":
            print(f"no build for {head[:7]} after 60s → requesting a rebuild (L-07)")
            gh_api(f"repos/{repo}/pages/builds", "POST")
            requested = True
        time.sleep(10)
    print(f"ERROR: Pages build for {head[:7]} not finished within {timeout}s")
    return False


def fetch(url: str) -> tuple[int, str]:
    req = urllib.request.Request(f"{url}?t={int(time.time())}", headers={"Cache-Control": "no-cache"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, ""


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--no-wait", action="store_true", help="do not wait for the Pages build")
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--expect", action="append", default=[], help='"docs-relative/path.html::text" to find on the live page')
    args = ap.parse_args()

    repo = repo_slug()
    head = sh("git", "rev-parse", "HEAD")
    if sh("git", "rev-parse", "@{u}") != head:
        print(f"WARN: HEAD {head[:7]} is not pushed; checking whatever is deployed")
    elif not args.no_wait and not wait_for_build(repo, head, args.timeout):
        return 1

    base = gh_api(f"repos/{repo}/pages")["html_url"].rstrip("/") + "/"
    docs = ROOT / "docs"
    pages = sorted(p.relative_to(docs).as_posix() for p in docs.rglob("*.html"))
    expects: dict[str, list[str]] = {}
    for e in args.expect:
        path, _, text = e.partition("::")
        expects.setdefault(path, []).append(text)
    manifest = Manifest(ROOT)
    for r in manifest.redirects:  # old addresses must forward to the renamed article
        expects.setdefault(r.src, []).append(f"url={href(r.area, manifest.by_no[r.to])}")
    problems = []
    for rel in sorted(set(pages) | expects.keys()):
        url = base + ("" if rel == "index.html" else rel)
        status, body = fetch(url)
        if status != 200:
            problems.append(f"{url} → HTTP {status}")
            continue
        for text in expects.get(rel, []):
            if text not in body:
                problems.append(f'{url} → "{text}" 없음')
    scope = f"{head[:7]}, {len(pages)} pages, {len(args.expect)} expectations"
    if problems:
        print("\n".join(problems))
        print(f"{len(problems)} problem(s) ({scope})")
        return 1
    print(f"OK ({scope})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
