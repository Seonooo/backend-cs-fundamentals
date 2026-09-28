"""Claude Code UserPromptSubmit hook: when the user points out a mistake, remind Claude of the lessons procedure.

Adds context only; never blocks the prompt. False positives are harmless (a one-line reminder).
"""
from __future__ import annotations

import json
import re
import sys

CORRECTION = re.compile(r"틀렸|틀린|잘못|다시\s*(생각|해|확인|점검|봐)|왜\s*이렇게|아닌\s*것\s*같|아니야|아니잖|오류가|깨졌|안\s*되(는데|잖)|이상해")
REMINDER = (
    "사용자가 문제를 지적한 것일 수 있습니다. 수정한 뒤 guides/lessons.md 절차(기록 → 장치화 → 재현 테스트)를 따르세요. "
    "이미 기록된 유형이 재발한 것이면 검사 규칙이나 hook으로 올려야 합니다."
)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")  # L-13
    try:
        data = json.loads(sys.stdin.buffer.read().decode("utf-8") or "{}")
        if CORRECTION.search(data.get("prompt") or ""):
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": REMINDER}},
                             ensure_ascii=False))
    except Exception:
        pass


if __name__ == "__main__":
    main()
