"""Show what Claude read and edited per request, and flag work done without the required guide.

  py tools/check_reads.py            # last 5 requests of the latest session
  py tools/check_reads.py --last 20
  py tools/check_reads.py --all      # every session in the log

Source: .claude/logs/access.jsonl, written by tools/hooks/log_access.py.
A guide counts as read only if it was read after the most recent compaction in that session,
because compaction may summarise its contents away.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "hooks"))
from guide_rules import required_guides  # noqa: E402  (same rules decide.py enforces)

LOG = Path(__file__).resolve().parents[1] / ".claude" / "logs" / "access.jsonl"


def load():
    if not LOG.exists():
        sys.exit(f"no log yet: {LOG} (hooks in .claude/settings.json must be active)")
    records = []
    for line in LOG.read_text(encoding="utf-8").splitlines():
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return records


def requests(records):
    """Split one session's records into requests, tracking guides read since the last compaction."""
    out, current, read_since_compact = [], None, set()
    for r in records:
        ev = r.get("event")
        if ev == "PreCompact":
            read_since_compact = set()
            if current:
                current["compacted"] = True
            continue
        if ev == "UserPromptSubmit":
            current = {"prompt": r.get("prompt", ""), "ts": r["ts"], "reads": [], "edits": [], "issues": [], "compacted": False}
            out.append(current)
            continue
        if current is None:  # activity before the first logged prompt
            current = {"prompt": "(세션 시작 전 기록)", "ts": r["ts"], "reads": [], "edits": [], "issues": [], "compacted": False}
            out.append(current)
        tool, paths = r.get("tool"), r.get("paths", [])
        if tool in ("Edit", "Write"):
            for p in paths:
                current["edits"].append({"tool": tool, "path": p})
                content = "<svg" if r.get("svg") else ""
                # is_new is unknown after the fact; decide.py checks new-article.md at edit time
                for sev, guide, label in required_guides(tool, p, content, is_new=False):
                    if guide not in read_since_compact:
                        current["issues"].append((sev, f"{label} ({p}) 전에 {guide}를 읽지 않음"))
        else:
            for p in paths:
                current["reads"].append(p)
                read_since_compact.add(p)
    return out


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--last", type=int, default=5, help="number of recent requests to show")
    ap.add_argument("--all", action="store_true", help="all sessions, all requests")
    args = ap.parse_args()

    records = load()
    sessions: dict[str, list] = {}
    for r in records:
        sessions.setdefault(r.get("session", "?"), []).append(r)
    chosen = sessions.items() if args.all else [list(sessions.items())[-1]]
    errors = warns = 0
    for sid, recs in chosen:
        reqs = requests(recs)
        shown = reqs if args.all else reqs[-args.last:]
        print(f"== session {sid}: {len(reqs)} requests (showing {len(shown)})")
        for q in shown:
            flag = " [압축됨]" if q["compacted"] else ""
            print(f"- {q['ts']} \"{q['prompt']}\"{flag}")
            guides = sorted({p for p in q["reads"] if p.startswith("guides/")})
            docs_read = len({p for p in q["reads"] if p.startswith("docs/")})
            edits = sorted({e["path"] for e in q["edits"]})
            print(f"    읽음: guides {guides or '없음'} · docs {docs_read}개")
            if edits:
                print(f"    수정: {', '.join(edits[:6])}{' …' if len(edits) > 6 else ''}")
            for sev, msg in dict.fromkeys(q["issues"]):
                print(f"    [{sev}] {msg}")
                errors += sev == "error"
                warns += sev == "warn"
    print(f"{errors} error(s), {warns} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
