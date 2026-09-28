"""Claude Code Stop hook: when site files changed, run `tools/check.py --changed` before Claude finishes.

- errors  → block the stop and hand the report back to Claude so it fixes them now
- only warnings or nothing changed → stay silent
- if this hook already blocked once in a row (stop_hook_active), only show a message, to avoid a loop
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")  # Windows defaults to cp949, which garbles Korean for Claude Code
    try:
        data = json.loads(sys.stdin.buffer.read().decode("utf-8") or "{}")
    except Exception:
        data = {}
    try:
        result = subprocess.run([sys.executable, str(ROOT / "tools" / "check.py"), "--changed"],
                                capture_output=True, text=True, encoding="utf-8", cwd=ROOT, timeout=60)
    except Exception:
        return  # the check itself could not run; never trap the session
    if result.returncode == 0:
        return
    report = (result.stdout or result.stderr).strip()
    if data.get("stop_hook_active"):
        print(json.dumps({"systemMessage": "check.py 오류가 아직 남아 있습니다:\n" + report}, ensure_ascii=False))
        return
    print(json.dumps({
        "decision": "block",
        "reason": "끝내기 전에 tools/check.py --changed 오류를 고치세요. 새 유형의 문제라면 guides/lessons.md 절차도 따르세요.\n" + report,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
