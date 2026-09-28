"""Run every rule in tools/checks/ against the site.

  python tools/check.py            # whole site
  python tools/check.py --changed  # only issues touching files changed in git (incl. untracked)
  python tools/check.py --rule pager --rule links

Prints "OK (...)" when nothing is wrong. Exit code 1 when any error-level issue is found.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from checks import load_rules  # noqa: E402
from site_model import Site  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
MAX_LINES_PER_RULE = 8


def changed_files(root: Path) -> set[str]:
    out = subprocess.run(["git", "-C", str(root), "status", "--porcelain", "-uall"],
                         capture_output=True, text=True, encoding="utf-8", check=True).stdout
    files = set()
    for line in out.splitlines():
        path = line[3:].split(" -> ")[-1].strip().strip('"')
        files.add(path)
    return files


def run(root: Path = ROOT, only_rules: list[str] | None = None, changed: set[str] | None = None):
    site = Site(root)
    results = []
    for rule, check in load_rules():
        if only_rules and rule.id not in only_rules:
            continue
        for issue in check(site):
            if changed is not None and issue.file not in changed and not changed.intersection(issue.related):
                continue
            results.append((rule, issue))
    return site, results


def report(site, results, scope: str) -> int:
    if not results:
        print(f"OK ({scope})")
        return 0
    order = {"error": 0, "warn": 1}
    results.sort(key=lambda r: (order[r[0].severity], r[0].id, r[1].file, r[1].line))
    shown: dict[str, int] = {}
    for rule, issue in results:
        shown[rule.id] = shown.get(rule.id, 0) + 1
        if shown[rule.id] <= MAX_LINES_PER_RULE:
            origin = f" ({rule.origin})" if rule.origin else ""
            print(f"{issue.file}:{issue.line} [{rule.severity} {rule.id}] {issue.msg}")
            if shown[rule.id] == 1:
                print(f"    → {rule.fix}{origin}")
    for rule_id, count in shown.items():
        if count > MAX_LINES_PER_RULE:
            print(f"    … [{rule_id}] {count - MAX_LINES_PER_RULE} more")
    errors = sum(1 for r, _ in results if r.severity == "error")
    warns = len(results) - errors
    print(f"{errors} error(s), {warns} warning(s) ({scope})")
    return 1 if errors else 0


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--changed", action="store_true", help="report only issues touching git-changed files")
    ap.add_argument("--rule", action="append", help="run only this rule id (repeatable)")
    ap.add_argument("--root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    args = ap.parse_args()
    changed = None
    if args.changed:
        changed = {f for f in changed_files(args.root) if f.startswith("docs/") or f == "README.md"}
        if not changed:
            print("OK (no changed site files)")
            return 0
    site, results = run(args.root, args.rule, changed)
    scope = f"{len(changed)} changed files" if changed is not None else f"{len(site.pages)} pages"
    return report(site, results, scope)


if __name__ == "__main__":
    sys.exit(main())
