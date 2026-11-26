"""La excepción de gitleaks para el canary sintético de las pruebas de fuga (U10-T06).

La excepción es exacta: cubre solo el canary de `tests/support.py` y ninguna otra clave.
Todo es sintético.
"""

import re
import tomllib
from pathlib import Path
from typing import Any

from tests.support import KEY_CANARY

ROOT = Path(__file__).resolve().parents[4]
MARKER = "canary sintético"


def _entry() -> dict[str, Any]:
    config = tomllib.loads((ROOT / ".gitleaks.toml").read_text(encoding="utf-8"))
    matches = [a for a in config["allowlists"] if MARKER in a.get("description", "").lower()]
    assert len(matches) == 1, "debe haber una única excepción del canary sintético"
    return dict(matches[0])


def _pattern() -> re.Pattern[str]:
    regexes = _entry()["regexes"]
    assert len(regexes) == 1
    return re.compile(regexes[0])


def test_pattern_matches_the_canary() -> None:
    assert _pattern().search(f'KEY_CANARY = "{KEY_CANARY}"') is not None


def test_pattern_rejects_other_keys() -> None:
    pattern = _pattern()
    other_keys = [
        "sk-ant-api03-" + "aB3dE5gH7jK9mN1pQ3sT5vW7yZ9bC1eF3hJ5kL7n",
        "sk-sintetico-canario-7f3a91c2d4e6",
        "x" + KEY_CANARY + "x",
    ]
    for key in other_keys:
        assert pattern.search(key) is None, key


def test_entry_carries_a_review_date() -> None:
    assert re.search(r"Revisar: \d{4}-\d{2}-\d{2}", _entry()["description"])
