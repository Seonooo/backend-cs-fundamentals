"""Claude Code hook: append one JSON line per event to .claude/logs/access.jsonl.

Registered in .claude/settings.json for UserPromptSubmit, PostToolUse, PostToolUseFailure and PreCompact.
Read by tools/check_reads.py. Never blocks or fails the session: any error is swallowed.
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / ".claude" / "logs" / "access.jsonl"
# Paths inside the repo worth tracking when they appear in a shell command.
BASH_PATH_RE = re.compile(r"(?:^|[\s'\"=(/])((?:guides|docs|plan|tools|README\.md|CLAUDE\.md)[^\s'\"|;&)<>\\]*)")


def rel(path: str) -> str:
    if not path:
        return ""
    p = path.replace("\\", "/")
    root = str(ROOT).replace("\\", "/")
    for prefix in (root + "/", "/" + root[0].lower() + root[2:] + "/"):  # C:/x/... and Git Bash /c/x/...
        if p.lower().startswith(prefix.lower()):
            return p[len(prefix):]
    return p


def record(data: dict) -> dict | None:
    event = data.get("hook_event_name", "")
    base = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "event": event, "session": data.get("session_id", "")[:8]}
    if event == "UserPromptSubmit":
        return {**base, "prompt": (data.get("prompt") or "")[:80]}
    if event == "PreCompact":
        return {**base, "trigger": data.get("trigger", "")}
    if event not in ("PostToolUse", "PostToolUseFailure"):
        return None
    tool = data.get("tool_name", "")
    ti = data.get("tool_input") or {}
    if event == "PostToolUseFailure":
        if tool in ("Edit", "Write"):
            return None  # a failed edit changed nothing
        base["failed"] = True  # e.g. grep with no match still read the file
    if tool in ("Read", "Edit", "Write"):
        paths = [rel(ti.get("file_path", ""))]
        if tool in ("Edit", "Write"):
            text = ti.get("new_string") or ti.get("content") or ""
            base["svg"] = "<svg" in text
    elif tool in ("Grep", "Glob"):
        paths = [rel(ti.get("path", "")) or "."]
        base["pattern"] = (ti.get("pattern") or "")[:60]
    elif tool == "Bash":
        cmd = ti.get("command") or ""
        paths = sorted({m.rstrip(".,:") for m in BASH_PATH_RE.findall(cmd)})
        if not paths:
            return None
        base["cmd"] = cmd[:120]
    else:
        return None
    return {**base, "tool": tool, "paths": [p for p in paths if p]}


def main() -> None:
    try:
        data = json.loads(sys.stdin.buffer.read().decode("utf-8") or "{}")
        rec = record(data)
        if rec:
            LOG.parent.mkdir(parents=True, exist_ok=True)
            with LOG.open("a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:  # a logging hook must never disturb the session
        pass


if __name__ == "__main__":
    main()
