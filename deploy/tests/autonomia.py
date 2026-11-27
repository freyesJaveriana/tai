"""Comprobación estática de AUTONOMIA-01 (DP-08): ningún workflow ni script aplica al clúster.

Recorre un árbol y devuelve las infracciones. Solo `scripts/humano/` puede nombrar esas
operaciones, y cada archivo de esa carpeta debe abrir con la marca del humano. Los verbos prohibidos
aparecen aquí solo como datos de una expresión regular, de modo que este archivo no se dispara a sí
mismo cuando la comprobación recorre el repositorio.
"""

import os
import re
from collections.abc import Iterator, Mapping
from pathlib import Path

import yaml

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
_INSTALL = r"install|upgrade"
_SLURM = "sb" + "atch"  # el comando que envía trabajos a ZINE, armado para no nombrarlo aquí
# Los nombres de las herramientas también se arman con fragmentos: este archivo guarda sus verbos
# como datos y no debe dispararse a sí mismo.
_KUBECTL = "kube" + "ctl"
_HELM = "he" + "lm"
RULES: Mapping[str, re.Pattern[str]] = {
    # Tras el nombre se admiten comillas y el cierre de una sustitución: `(which <tool>) <verbo>`.
    "kubectl": re.compile(
        rf"(?<![\w.-]){_KUBECTL}[\"')]*(?:\s+{_WORD})*?\s+(?:{_APPLY})\b", re.IGNORECASE
    ),
    "helm": re.compile(
        rf"(?<![\w.-]){_HELM}[\"')]*(?:\s+{_WORD})*?\s+(?:{_INSTALL})\b", re.IGNORECASE
    ),
    "slurm": re.compile(rf"(?<![A-Za-z0-9_]){_SLURM}(?![A-Za-z0-9_])", re.IGNORECASE),
    "kustomize-kubectl": re.compile(r"kustomize\b[^\n#]*\|\s*kubectl\b", re.IGNORECASE),
}


def _list_forms(tool: str, verbs: str) -> tuple[re.Pattern[str], re.Pattern[str]]:
    """Las dos formas de una orden escrita como lista de argumentos, que las líneas no ven.

    - Lista entre corchetes (Python o YAML de flujo): `["<tool>", "-n", "x", "<verbo>", …]`, con o
      sin comillas, en una o en varias líneas. Los elementos no cruzan un corchete.
    - Bloque de YAML: `- <tool>` seguido de elementos `- …` consecutivos hasta `- <verbo>`.
    """
    quote = "[\"']?"
    element = rf"\s*{quote}[^,\[\]\"'\n]*{quote}\s*,"
    flow = re.compile(
        rf"(?<![\w.-]){quote}{tool}{quote}\s*,(?:{element})*?\s*{quote}(?:{verbs}){quote}\s*[,\])]",
        re.IGNORECASE,
    )
    block = re.compile(
        rf"^[ \t]*-[ \t]+{quote}(?:[^\n\"']*/)?{tool}{quote}[ \t]*\n"
        rf"(?:[ \t]*-[ \t]+[^\n]*\n)*?"
        rf"[ \t]*-[ \t]+{quote}(?:{verbs}){quote}[ \t]*(?:#[^\n]*)?$",
        re.IGNORECASE | re.MULTILINE,
    )
    return flow, block


# Reglas que miran el texto entero, con el mismo nombre que la regla de línea de su herramienta.
LIST_RULES: Mapping[str, tuple[re.Pattern[str], ...]] = {
    "kubectl": _list_forms(_KUBECTL, _APPLY),
    "helm": _list_forms(_HELM, _INSTALL),
}

# Excepciones declaradas con su motivo. Cada una solo exime las reglas que nombra y solo vale para la
# ruta exacta (o para la carpeta si termina en «/», que hoy ninguna usa).
# - Los guardianes y sus pruebas nombran los verbos prohibidos como datos para detectarlos: el de los
#   workflows (contracts), el de los scripts (scripts/check-no-cluster-apply.sh) y la prueba de la
#   plantilla del PR, que exige que esas palabras no aparezcan en ella.
# - Los dos archivos de la validación de ZINE que nombran el envío a SLURM como dato (la lista de
#   trabajos y la comprobación del reporte); los scripts de envío los lanza solo el humano.
EXCEPTIONS: Mapping[str, frozenset[str]] = {
    "contracts/src/veridicus_contracts/checks/ci_workflows.py": frozenset({"kubectl", "helm"}),
    "contracts/tests/checks/test_ci_workflows.py": frozenset({"kubectl", "helm"}),
    "contracts/tests/tools/test_pull_request_template.py": frozenset({"slurm"}),
    "docs/validacion-zine/comprobar_reporte.py": frozenset({"slurm"}),
    "docs/validacion-zine/comun.sh": frozenset({"slurm"}),
    "scripts/check-no-cluster-apply.sh": frozenset({"slurm"}),
}


CONTAINER_KEYS = ("containers", "initContainers", "ephemeralContainers")


def _argv(container: object) -> str:
    """`command` y `args` de un contenedor unidos en una sola línea; vacío si no son listas."""
    if not isinstance(container, dict):
        return ""
    parts: list[str] = []
    for key in ("command", "args"):
        value = container.get(key)
        if isinstance(value, list):
            parts.extend(str(item) for item in value)
    return " ".join(parts)


def _argvs(node: object) -> Iterator[str]:
    """Las órdenes de todo contenedor del documento, a cualquier profundidad."""
    if isinstance(node, dict):
        for key, value in node.items():
            if key in CONTAINER_KEYS and isinstance(value, list):
                for container in value:
                    line = _argv(container)
                    if line:
                        yield line
            else:
                yield from _argvs(value)
    elif isinstance(node, list):
        for item in node:
            yield from _argvs(item)


def _container_hits(text: str) -> list[tuple[str, int]]:
    """Reglas de línea aplicadas a `command` + `args` de cada contenedor de un YAML.

    Si el archivo no se puede leer como YAML devuelve vacío: la regla de texto sigue aplicándose.
    """
    try:
        documents = list(yaml.safe_load_all(text))
    except yaml.YAMLError:
        return []
    hits: list[tuple[str, int]] = []
    for document in documents:
        for line in _argvs(document):
            for name, pattern in RULES.items():
                if name in {"kubectl", "helm"} and pattern.search(line):
                    first = line.split()[0] if line.split() else ""
                    number = text[: text.find(first)].count("\n") + 1 if first in text else 1
                    hits.append((name, number))
    return hits


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
        hits: list[str] = []
        for number, line in logical_lines(text):
            for name, pattern in RULES.items():
                if name not in allowed and pattern.search(line):
                    hits.append(f"{rel}:{number}: {name} fuera de {HUMANO}/")
        if path.suffix in {".yml", ".yaml"}:
            for name, number in _container_hits(text):
                if name not in allowed:
                    hits.append(f"{rel}:{number}: {name} fuera de {HUMANO}/")
        for name, patterns in LIST_RULES.items():
            if name in allowed:
                continue
            for pattern in patterns:
                for match in pattern.finditer(text):
                    number = text.count("\n", 0, match.start()) + 1
                    hits.append(f"{rel}:{number}: {name} fuera de {HUMANO}/")
        found.extend(dict.fromkeys(hits))
    return found
