"""Reglas estáticas de los workflows de deploy (pasos 8 y 9, DP-07, DP-08).

Los workflows se leen como texto y como YAML; nunca se ejecutan. Cada regla devuelve su motivo y
cada una tiene un control negativo en `deploy/tests/fixtures/workflows/`. Los nombres de las
herramientas del clúster se arman con fragmentos, igual que en `autonomia.py`, para que este archivo
no se dispare a sí mismo cuando la comprobación de AUTONOMIA-01 recorre el repositorio.
"""

import re
from typing import Any

import yaml

# Las dos únicas acciones que el repositorio permite, con el SHA que ya usan sus workflows.
ALLOWED_ACTIONS = {
    "actions/checkout": "3d3c42e5aac5ba805825da76410c181273ba90b1",
    "astral-sh/setup-uv": "37802adc94f370d6bfd71619e3f0bf239e1f3b78",
}

# Herramientas que la CI descarga con curl: asset y suma SHA-256 de la release (tabla de la tarea).
TOOLS: dict[str, tuple[str, str]] = {
    "kustomize": (
        "kustomize_v5.8.3_linux_amd64.tar.gz",
        "cb9e31198d3f63b44848bd0afc4c8efc56e6cfef9c93a4a39a211940e6decd61",
    ),
    "kubeconform": (
        "kubeconform-linux-amd64.tar.gz",
        "9bc2bffbf71f261128533edaf912153948b7ff238f9a531ae6d34466ec287883",
    ),
    "kyverno": (
        "kyverno-cli_v1.20.0_linux_x86_64.tar.gz",
        "06b8f3ca7b5626473be8fb4d343ad54ab84e317142766f72420e7d44b80942e2",
    ),
    "hadolint": (
        "hadolint-linux-x86_64",
        "c7187db94eeeeca956519a6af171adc31453941a1e777961f6e680f697c8c507",
    ),
    "shellcheck": (
        "shellcheck-v0.11.0.linux.x86_64.tar.xz",
        "8c3be12b05d5c177a04c29e3c78ce89ac86f1595681cab149b65b97c4e227198",
    ),
    "trivy": (
        "trivy_0.76.2_Linux-64bit.tar.gz",
        "bc0fc726e017b8927a62b2d3531d7a84ee01769daf5c99ed866dced54089fdbf",
    ),
}
TOOL_SUMS = frozenset(sha for _, sha in TOOLS.values())

_K = "kube" + "ctl"
_KUBECONFIG = re.compile(r"kube_?config", re.IGNORECASE)
_CLUSTER_CLI = re.compile(rf"(?<![\w-]){_K}(?![\w-])", re.IGNORECASE)
# `latest` como etiqueta de imagen: tras dos puntos, o en cualquier línea de docker que lo nombre.
_LATEST_TAG = re.compile(r":latest\b", re.IGNORECASE)
_DOCKER_LATEST = re.compile(r"\bdocker\b[^\n]*\blatest\b", re.IGNORECASE)
_SHA40 = re.compile(r"[0-9a-f]{40}")
_SUM = re.compile(r"\b[0-9a-f]{64}\b")
_FETCH = re.compile(r"(?<![\w./-])(?:curl|wget)\s")
_VERIFY = re.compile(r"sha256sum\s+(?:--check|-c)\b")
# Lo que ejecuta o desempaqueta lo descargado, al inicio de un comando.
_USE = re.compile(
    r"(?:^|\n|;|&&|\|\|?)\s*(?:sudo\s+)?(?:tar|unzip|chmod|install|bash|sh|python3?|\./\S+)(?:\s|$)"
)
_PULL_REQUEST_TRIGGERS = ("pull_request", "pull_request_target")
_MAIN_ONLY = ("github.event_name == 'push'", "github.ref == 'refs/heads/main'")


def _triggers(document: dict[Any, Any]) -> list[str]:
    """Los eventos del workflow. PyYAML lee la clave `on` como el booleano `True`."""
    raw = document.get("on", document.get(True))
    if isinstance(raw, str):
        return [raw]
    if isinstance(raw, list):
        return [str(item) for item in raw]
    if isinstance(raw, dict):
        return [str(item) for item in raw]
    return []


def _steps(document: dict[Any, Any]) -> list[tuple[str, dict[str, Any]]]:
    found: list[tuple[str, dict[str, Any]]] = []
    for job_name, job in (document.get("jobs") or {}).items():
        for index, step in enumerate((job or {}).get("steps") or []):
            if isinstance(step, dict):
                found.append((f"{job_name}[{index}]", step))
    return found


def _packages_write(permissions: object) -> bool:
    return isinstance(permissions, dict) and permissions.get("packages") == "write"


def _permission_violations(rel: str, document: dict[Any, Any]) -> list[str]:
    found: list[str] = []
    root = document.get("permissions")
    if not (isinstance(root, dict) and root.get("contents") == "read"):
        found.append(f"{rel}: falta «permissions: contents: read» en el nivel del workflow")
    elif "write" in root.values():
        found.append(f"{rel}: el nivel del workflow declara una escritura; solo un job puede")
    in_pull_request = any(item in _PULL_REQUEST_TRIGGERS for item in _triggers(document))
    writers = 0
    for name, job in (document.get("jobs") or {}).items():
        permissions = (job or {}).get("permissions")
        if permissions == "write-all" or (
            isinstance(permissions, dict) and permissions.get("contents") == "write"
        ):
            found.append(f"{rel}: el job {name} escribe el contenido del repositorio")
        if not _packages_write(permissions):
            continue
        writers += 1
        condition = str((job or {}).get("if") or "")
        if in_pull_request and not all(part in condition for part in _MAIN_ONLY):
            found.append(
                f"{rel}: el job {name} tiene packages: write y puede correr en un pull_request"
            )
    if writers > 1:
        found.append(f"{rel}: packages: write en {writers} jobs; solo el que publica puede")
    return found


def _action_violations(rel: str, document: dict[Any, Any]) -> list[str]:
    found: list[str] = []
    for where, step in _steps(document):
        used = step.get("uses")
        if used is None:
            continue
        name, _, ref = str(used).partition("@")
        if not _SHA40.fullmatch(ref):
            found.append(f"{rel}: {where} usa {used}, que no está fijada por un SHA de 40 hex")
        elif name not in ALLOWED_ACTIONS:
            found.append(f"{rel}: {where} usa {name}, que no es una de las dos acciones permitidas")
        elif ALLOWED_ACTIONS[name] != ref:
            found.append(f"{rel}: {where} usa {name} con un SHA distinto del del repositorio")
    return found


def _code(run: str) -> str:
    """El script sin comentarios y con las continuaciones de línea unidas."""
    lines = [line for line in run.splitlines() if not line.lstrip().startswith("#")]
    return re.sub(r"\\\n", " ", "\n".join(lines))


def _download_violations(rel: str, document: dict[Any, Any]) -> list[str]:
    found: list[str] = []
    for where, step in _steps(document):
        code = _code(str(step.get("run") or ""))
        fetches = [match.start() for match in _FETCH.finditer(code)]
        if not fetches:
            continue
        sums = set(_SUM.findall(code + " " + str(step.get("env") or "")))
        if not sums:
            found.append(f"{rel}: {where} descarga con curl y no lleva ninguna suma SHA-256")
        for unknown in sorted(sums - TOOL_SUMS):
            found.append(f"{rel}: {where} usa la suma {unknown[:12]}…, que no es la de la tabla")
        bounds = [*fetches, len(code)]
        for number, start in enumerate(fetches):
            segment = code[start : bounds[number + 1]]
            first_line = segment.split("\n", 1)[0]
            if "|" in first_line:
                found.append(f"{rel}: {where} canaliza la descarga a otro comando")
            verify = _VERIFY.search(segment)
            if verify is None:
                found.append(f"{rel}: {where} no verifica la descarga con sha256sum -c")
            elif _USE.search(segment[: verify.start()]):
                found.append(f"{rel}: {where} usa lo descargado antes de verificarlo")
    return found


def violations(rel: str, text: str) -> list[str]:
    """Infracciones de un workflow; vacío si cumple todas las reglas."""
    found: list[str] = []
    for number, line in enumerate(text.splitlines(), start=1):
        if _KUBECONFIG.search(line):
            found.append(f"{rel}:{number}: nombra un kubeconfig")
        if _CLUSTER_CLI.search(line):
            found.append(f"{rel}:{number}: nombra la herramienta del clúster")
        if _LATEST_TAG.search(line) or _DOCKER_LATEST.search(line):
            found.append(f"{rel}:{number}: etiqueta de imagen latest")
    document = yaml.safe_load(text)
    if not isinstance(document, dict):
        return [*found, f"{rel}: no es un workflow"]
    found.extend(_permission_violations(rel, document))
    found.extend(_action_violations(rel, document))
    found.extend(_download_violations(rel, document))
    return found
