"""Claude Code PreToolUse hook: the single place that decides allow / warn / deny for tool calls.

Rules (each returns None to pass, or ("warn" | "deny", reason)):
  - guide_required: an Edit/Write on a docs page is denied until the required guide was read with the Read tool
    (or a shell command) in this session after the last compaction. Fails open when the access log is unavailable.
  - heredoc_backslash (L-15): warn when a Bash heredoc contains backslashes, which the Bash tool may collapse.

To delegate decisions to an external harness (e.g. Jev), replace decide() only — the wiring in .claude/settings.json stays.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from guide_rules import reads_since_compaction, required_guides  # noqa: E402
from log_access import ROOT, rel  # noqa: E402

LOG = Path(os.environ.get("CLAUDE_ACCESS_LOG", ROOT / ".claude" / "logs" / "access.jsonl"))


def guide_required(tool, ti, session):
    if tool not in ("Edit", "Write"):
        return None
    path = rel(ti.get("file_path", ""))
    content = ti.get("new_string") or ti.get("content") or ""
    is_new = tool == "Write" and not (ROOT / path).exists()
    needed = [(g, why) for level, g, why in required_guides(tool, path, content, is_new) if level == "error"]
    if not needed:
        return None
    read = reads_since_compaction(LOG, session)
    if read is None:
        return None  # no access log → cannot tell → do not block
    missing = [(g, why) for g, why in needed if g not in read]
    if not missing:
        return None
    todo = ", ".join(f"{g} ({why})" for g, why in missing)
    return ("deny", f"{path} 수정 전에 먼저 Read 도구로 읽으세요: {todo}. 읽은 뒤 같은 수정을 다시 시도하세요. "
                    "(대화 압축 이후에는 다시 읽어야 합니다. 규칙: tools/hooks/guide_rules.py)")


HEREDOC_RE = re.compile(r"<<-?\s*(['\"]?)(\w+)\1[^\n]*\n(.*?)\n\2\s*$", re.S | re.M)


def heredoc_backslash(tool, ti, session):
    cmd = ti.get("command", "") if tool == "Bash" else ""
    if any("\\" in m.group(3) for m in HEREDOC_RE.finditer(cmd)):  # only the heredoc body, not later arguments
        return ("warn", "heredoc 안의 백슬래시는 Bash 도구를 거치며 줄어들 수 있습니다(L-15). "
                        "결과가 이상하면 Write로 파일을 만들어 실행하세요.")
    return None


RULES = [guide_required, heredoc_backslash]


def decide(tool: str, tool_input: dict, session: str):
    for rule in RULES:
        verdict = rule(tool, tool_input, session)
        if verdict:
            return verdict
    return None


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")  # L-13
    try:
        data = json.loads(sys.stdin.buffer.read().decode("utf-8") or "{}")
        verdict = decide(data.get("tool_name", ""), data.get("tool_input") or {}, data.get("session_id", ""))
    except Exception:
        return  # never block because the decider itself failed
    if not verdict:
        return
    level, reason = verdict
    if level == "deny":
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                                 "permissionDecisionReason": reason}}, ensure_ascii=False))
    else:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": reason}},
                         ensure_ascii=False))


if __name__ == "__main__":
    main()
