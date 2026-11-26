"""Comprobación estática de AUTONOMIA-01 (DP-08): ningún workflow ni script aplica al clúster.

Recorre un árbol y devuelve las infracciones. Solo `scripts/humano/` puede nombrar esas
operaciones, y cada archivo de esa carpeta debe abrir con la marca del humano. Las verbos
prohibidos aparecen aquí solo como datos de una expresión regular, de modo que este archivo no se
dispara a sí mismo cuando la comprobación recorre el repositorio.
"""

import os
import re
from collections.abc import Iterator, Mapping
from pathlib import Path

MARK = "# Lo ejecuta el humano (AUTONOMIA-01)"
HUMANO = "scripts/humano"
FIXTURES = "deploy/tests/fixtures"
SKIP_DIRS = frozenset(
    {".git", ".venv", ".worktrees", "node_modules", "__pycache__"}
    | {".mypy_cache", ".ruff_cache", ".pytest_cache"}
)
SUFFIXES = frozenset({".sh", ".py", ".yml", ".yaml"})

_WORD = r"[^\s|;&]+"
_APPLY = r"apply|create|delete|patch|replace"
RULES: Mapping[str, re.Pattern[str]] = {
    "kubectl": re.compile(rf"(?<![\w.-])kubectl(?:\s+{_WORD})*?\s+(?:{_APPLY})\b", re.IGNORECASE),
    "helm": re.compile(rf"(?<![\w.-])helm(?:\s+{_WORD})*?\s+(?:install|upgrade)\b", re.IGNORECASE),
    "sbatch": re.compile(r"(?<![A-Za-z0-9_])sbatch(?![A-Za-z0-9_])", re.IGNORECASE),
    "kustomize-kubectl": re.compile(r"kustomize\b[^\n#]*\|\s*kubectl\b", re.IGNORECASE),
}

# Excepciones declaradas con su motivo. Cada una solo exime las reglas que nombra.
# - El guardián de los workflows y su prueba nombran los verbos prohibidos como datos para detectarlos.
# - Los scripts SLURM de la validación de ZINE los lanza solo el humano.
EXCEPTIONS: Mapping[str, frozenset[str]] = {
    "contracts/src/veridicus_contracts/checks/ci_workflows.py": frozenset({"kubectl", "helm"}),
    "contracts/tests/checks/test_ci_workflows.py": frozenset({"kubectl", "helm"}),
    "docs/validacion-zine/": frozenset({"sbatch"}),
}


def logical_lines(text: str) -> Iterator[tuple[int, str]]:
    """Líneas lógicas: une las que terminan en barra invertida con la siguiente."""
    buffer = ""
    start = 0
    for number, line in enumerate(text.splitlines(), start=1):
        if not buffer:
            start = number
        stripped = line.rstrip()
        if stripped.endswith("\\"):
            buffer += stripped[:-1] + " "
            continue
        yield start, buffer + line
        buffer = ""
    if buffer:
        yield start, buffer


def _exempt(rel: str, exceptions: Mapping[str, frozenset[str]]) -> frozenset[str]:
    for path, rules in exceptions.items():
        if rel == path or (path.endswith("/") and rel.startswith(path)):
            return rules
    return frozenset()


def files(root: Path) -> Iterator[tuple[str, Path]]:
    """Archivos a revisar, con su ruta relativa en formato POSIX."""
    for directory, names, entries in os.walk(root):
        names[:] = sorted(name for name in names if name not in SKIP_DIRS)
        for entry in sorted(entries):
            path = Path(directory, entry)
            rel = path.relative_to(root).as_posix()
            if rel.startswith(FIXTURES + "/"):
                continue
            if rel.startswith(".github/") or path.suffix in SUFFIXES or entry == "Makefile":
                yield rel, path


def mark_violations(rel: str, text: str) -> list[str]:
    """Todo archivo de `scripts/humano/` abre, tras el shebang, con la marca del humano."""
    lines = text.splitlines()
    first = 1 if lines and lines[0].startswith("#!") else 0
    if first < len(lines) and lines[first].startswith(MARK):
        return []
    return [f"{rel}:{first + 1}: falta la marca «{MARK}» tras el shebang"]


def scan(root: Path, exceptions: Mapping[str, frozenset[str]] = EXCEPTIONS) -> list[str]:
    """Infracciones de AUTONOMIA-01 bajo `root`; vacío si cumple."""
    found: list[str] = []
    for rel, path in files(root):
        text = path.read_text(encoding="utf-8", errors="replace")
        if rel.startswith(HUMANO + "/"):
            found.extend(mark_violations(rel, text))
            continue
        if rel.startswith(".github/") and HUMANO in text:
            found.append(f"{rel}: un workflow no puede mencionar {HUMANO}/")
        allowed = _exempt(rel, exceptions)
        for number, line in logical_lines(text):
            for name, pattern in RULES.items():
                if name not in allowed and pattern.search(line):
                    found.append(f"{rel}:{number}: {name} fuera de {HUMANO}/")
    return found
