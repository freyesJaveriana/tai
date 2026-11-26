"""Reglas estáticas de los scripts de `scripts/humano/` (paso 7).

Los scripts del humano manejan claves reales, así que se leen como texto y nunca se ejecutan. Cada
regla es una expresión que se aplica a las líneas lógicas que no son comentarios y devuelve su
nombre si la ve. Las operaciones del clúster no se nombran aquí en claro: lo que se detecta es una
variable secreta puesta en una línea que la imprime o la pasa como argumento.
"""

import re
from collections.abc import Mapping

from autonomia import logical_lines, mark_violations

_KEY_VAR = r"\$\{?\w*(?:clave|token|auth|password|api_key)\w*"
_COMMAND_START = r"(?:^\s*|[;&|(]\s*)"

LINE_RULES: Mapping[str, re.Pattern[str]] = {
    "echo o printf de una variable secreta": re.compile(
        rf"\b(?:echo|printf)\b.*{_KEY_VAR}", re.IGNORECASE
    ),
    "from-literal": re.compile(r"--from-literal"),
    "clave en la línea de comandos (--docker-password o --password)": re.compile(
        r"--(?:docker-)?password"
    ),
    "variable secreta como argumento de kubectl": re.compile(
        rf"\bkubectl\b.*{_KEY_VAR}", re.IGNORECASE
    ),
    "source o punto sobre un archivo": re.compile(rf"{_COMMAND_START}(?:source|\.)\s+\S"),
    "eval": re.compile(rf"{_COMMAND_START}eval\s"),
    "set -x o allexport": re.compile(r"\bset\s+(?:-[a-z]*x[a-z]*|-a|-o\s+(?:xtrace|allexport))\b"),
}


def violations(rel: str, text: str) -> list[str]:
    """Infracciones de un script del humano; vacío si cumple todas las reglas."""
    found = mark_violations(rel, text)
    if not re.search(r"^set -euo pipefail\s*$", text, re.MULTILINE):
        found.append(f"{rel}: falta «set -euo pipefail»")
    if not re.search(r"^\s*trap\s+\S", text, re.MULTILINE):
        found.append(f"{rel}: falta el trap que borra lo temporal")
    for number, line in logical_lines(text):
        if line.lstrip().startswith("#"):
            continue
        for name, pattern in LINE_RULES.items():
            if pattern.search(line):
                found.append(f"{rel}:{number}: {name}")
    return found


PINNED = re.compile(r"curlimages/curl@sha256:(?:[0-9a-f]{64}|REEMPLAZAR_DIGEST_CURL)\b")
REAL_DIGEST = re.compile(r"curlimages/curl@sha256:[0-9a-f]{64}\b")
