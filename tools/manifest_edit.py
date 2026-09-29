"""Small helper to edit docs/articles.json from scripts while keeping the one-item-per-line format.

  from manifest_edit import load, save
  data = load(); data["articles"].append({...}); save(data)
"""
from __future__ import annotations

import json
from pathlib import Path

PATH = Path(__file__).resolve().parent.parent / "docs" / "articles.json"
ORDER = ("areas", "articles", "keywords")


def load(path: Path = PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dumps(data: dict) -> str:
    def block(name):
        items = ",\n".join("    " + json.dumps(i, ensure_ascii=False) for i in data[name])
        return f'  "{name}": [\n{items}\n  ]'
    return "{\n" + ",\n".join(block(k) for k in ORDER) + "\n}\n"


def save(data: dict, path: Path = PATH) -> None:
    text = dumps(data)
    assert json.loads(text) == data
    path.write_text(text, encoding="utf-8")
