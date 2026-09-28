"""Check registry. Each module in this package defines RULE and check(site) -> list[Issue].

To add a rule after a problem happens (see guides/lessons.md):
  1. create tools/checks/<name>.py with RULE (id, severity, origin, fix) and check()
  2. add a mutation to tools/test_checks.py that reproduces the problem
"""
from __future__ import annotations

import importlib
import pkgutil
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Rule:
    id: str
    severity: str  # "error" | "warn"
    fix: str
    origin: str = ""  # lessons entry, e.g. "L-02"


@dataclass
class Issue:
    file: str  # repo-relative path
    line: int
    msg: str
    related: tuple[str, ...] = field(default_factory=tuple)  # other repo-relative files this issue depends on


def load_rules():
    rules = []
    for info in sorted(pkgutil.iter_modules(__path__), key=lambda m: m.name):
        module = importlib.import_module(f"{__name__}.{info.name}")
        if hasattr(module, "RULE") and hasattr(module, "check"):
            rules.append((module.RULE, module.check))
    return rules
