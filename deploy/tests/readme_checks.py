"""Reglas de la guía de la demo (`deploy/demo-analyzer/README.md`, U02-T04, paso 10).

La guía se lee como texto y nunca se ejecuta nada de lo que cita. Cada regla devuelve un mensaje
fijo que no repite el texto hallado, para que un secreto pegado no llegue a la salida de la prueba.
"""

import re
from pathlib import Path

REQUIRED_SCRIPTS = (
    "crear-secret-anthropic.sh",
    "crear-pull-secret-ghcr.sh",
    "demo-analyzer.sh",
)

# Una palabra clave por sección obligatoria, buscada sin distinguir mayúsculas en los encabezados.
REQUIRED_SECTIONS = (
    "requisitos",
    "orden de los scripts",
    "logs",
    "networkpolicy",
    "reversión",
    "frontera de datos",
    "plan a y plan b",
)

_PATH = re.compile(r"(?:scripts/humano|deploy)/[\w./\-]*[\w/]")
_BARE_SCRIPT = re.compile(r"(?<![\w/.\-])([\w\-]+\.sh)\b")
_HEADING = re.compile(r"^#{1,6}\s+(.*)$", re.MULTILINE)
_SECRET_SHAPES = (
    re.compile(r"sk-ant-"),
    re.compile(r"\bsk-[A-Za-z0-9_\-]{20,}"),
    re.compile(r"\bghp_[A-Za-z0-9]{10,}"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{10,}"),
)
_KUBECONFIG = re.compile(r"kubeconfig", re.IGNORECASE)
_LATEST = re.compile(r"\blatest\b", re.IGNORECASE)


def violations(text: str, root: Path) -> list[str]:
    """Reglas incumplidas por `text`; las rutas se comprueban bajo `root` (raíz del repositorio)."""
    found: list[str] = []
    humano = root / "scripts" / "humano"

    if any(not (root / match.group(0)).exists() for match in _PATH.finditer(text)):
        found.append("cita una ruta del repositorio que no existe")

    if any(not (humano / name).is_file() for name in _BARE_SCRIPT.findall(text)):
        found.append("nombra un script que no está en scripts/humano")

    if any(name not in text for name in REQUIRED_SCRIPTS):
        found.append("falta alguno de los tres scripts del humano")

    headings = [match.group(1).lower() for match in _HEADING.finditer(text)]
    for keyword in REQUIRED_SECTIONS:
        if not any(keyword in heading for heading in headings):
            found.append(f"falta la sección «{keyword}»")

    if any(pattern.search(text) for pattern in _SECRET_SHAPES):
        found.append("lleva algo con forma de clave o token")
    if _KUBECONFIG.search(text):
        found.append("menciona un kubeconfig")
    if _LATEST.search(text):
        found.append("usa latest como etiqueta de imagen")

    starts = [line for line in text.splitlines() if "minikube start" in line]
    if not starts or any("--cni=calico" not in line for line in starts):
        found.append("el comando minikube start no lleva --cni=calico")

    return found
