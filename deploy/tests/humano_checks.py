"""Reglas estáticas de los scripts de `scripts/humano/` (paso 7).

Los scripts del humano manejan claves reales, así que se leen como texto y nunca se ejecutan. Cada
regla es una expresión que se aplica a las líneas lógicas que no son comentarios y devuelve su
nombre si la ve. Las operaciones del clúster no se nombran aquí en claro: lo que se detecta es una
variable secreta puesta en una línea que la imprime o la pasa como argumento.
"""

import re
from collections.abc import Mapping
from pathlib import Path

from autonomia import logical_lines, mark_violations

_KEY_NAMES = r"clave|token|auth|password|passwd|api_?key|key|secreto|secret|credencial|credential"
_KEY_VAR = rf"\$\{{?\w*(?:{_KEY_NAMES})\w*"
_COMMAND_START = r"(?:^\s*|[;&|({]\s*|\b(?:then|do|else)\s+)"
_KUBECTL = "kube" + "ctl"  # armado con fragmentos, igual que en autonomia.py
_APPLY = "ap" + "ply"
# `export` de una sustitución de comando que lee un archivo: un `source` disfrazado que además
# pone los valores en la línea de comandos (se verían en `ps`).
_EXPORT_FILE = r"(?:\$\(|\x60)[^\n]*(?:\b(?:grep|cat|sed|awk|cut|xargs|tr|head)\b|<)"

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
    "export con sustitución de un archivo": re.compile(
        rf"{_COMMAND_START}export\s[^\n]*{_EXPORT_FILE}"
    ),
}

# Nombres con los que las pruebas buscan cada regla (el texto de la clave es el que se imprime).
SHEBANG_X = re.compile(r"^#!.*\s-[A-Za-z]*[xa]\b")


# Un Secret aplicado del lado del cliente deja su valor en la anotación last-applied-configuration.
APPLY_RULE = "apply sin --server-side (el Secret quedaría en last-applied-configuration)"
_APPLY_LINE = re.compile(
    rf"\b{_KUBECTL}\b(?!.*(?:--server-side|\s-k[\s=]|--kustomize)).*\b{_APPLY}\b"
)
_KUSTOMIZE_ARG = re.compile(r"""(?:\s-k|\s--kustomize)(?:=|\s+)("[^"]*"|'[^']*'|\S+)""")
_APPLY_WORD = re.compile(rf"\b{_KUBECTL}\b.*\b{_APPLY}\b")


def strip_comment(line: str) -> str:
    """La línea sin su comentario final: un `#` al inicio o tras un espacio, fuera de comillas."""
    quote = ""
    for index, char in enumerate(line):
        if quote:
            quote = "" if char == quote else quote
        elif char in "\"'":
            quote = char
        elif char == "#" and (index == 0 or line[index - 1].isspace()):
            return line[:index]
    return line


def _kustomization_problem(line: str, root: Path | None) -> str | None:
    """Si `apply -k` apunta a una kustomization con `secretGenerator`, el motivo; si no, None.

    Solo se resuelven rutas estáticas del repositorio (relativas a la raíz, o con `$raiz` o
    `${raiz}` al inicio). Si no se puede resolver estáticamente (otra variable, una sustitución
    de comando o una carpeta que no existe), la regla no decide y deja pasar: no se puede resolver.
    """
    match = _KUSTOMIZE_ARG.search(line)
    if root is None or match is None:
        return None
    arg = match.group(1).strip("\"'")
    arg = re.sub(r"^\$\{?raiz\}?/", "", arg)
    if "$" in arg or "\x60" in arg:
        return None
    file = root / arg / "kustomization.yaml"
    if not file.is_file():
        return None
    if re.search(r"^secretGenerator\s*:", file.read_text(encoding="utf-8"), re.MULTILINE):
        return (
            f"apply -k sobre {arg}, que tiene secretGenerator (el valor quedaría en el manifiesto)"
        )
    return None


def violations(rel: str, text: str, root: Path | None = None) -> list[str]:
    """Infracciones de un script del humano; vacío si cumple todas las reglas."""
    found = mark_violations(rel, text)
    first = text.splitlines()[0] if text.strip() else ""
    if SHEBANG_X.search(first):
        found.append(f"{rel}:1: set -x o allexport en el shebang")
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
        code = strip_comment(line)
        if _APPLY_LINE.search(code):
            found.append(f"{rel}:{number}: {APPLY_RULE}")
        elif _APPLY_WORD.search(code):
            problem = _kustomization_problem(code, root)
            if problem:
                found.append(f"{rel}:{number}: {problem}")
    return found


PINNED = re.compile(
    r"curlimages/curl(?::[\w.-]+)?@sha256:(?:[0-9a-f]{64}|REEMPLAZAR_DIGEST_CURL)\b"
)
REAL_DIGEST = re.compile(r"curlimages/curl(?::[\w.-]+)?@sha256:[0-9a-f]{64}\b")
