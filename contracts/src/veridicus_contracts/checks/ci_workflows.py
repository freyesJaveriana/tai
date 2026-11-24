"""La CI no aplica cambios ni tiene credenciales del clúster (security-design §4.11, AUTONOMIA-01).

Módulo guardia (100 % de ramas). Falla si un *workflow* de `.github/workflows/` contiene `--write` (la CI
nunca regenera la huella de seguridad), `kubectl apply`, `helm install`, `helm upgrade` o credenciales del
clúster (`kubeconfig`, `KUBECONFIG`). Mira cada línea, también los comentarios: lo que un *workflow* nombra,
un cambio posterior lo puede activar. Los mensajes nombran el archivo, la línea y el término prohibido.
"""

import re
from collections.abc import Iterable
from pathlib import Path

REGLA = "(AUTONOMIA-01, §4.11)"
PROHIBIDOS = (
    ("--write", re.compile(r"--write\b")),
    ("kubectl apply", re.compile(r"kubectl\s+apply\b", re.IGNORECASE)),
    ("helm install", re.compile(r"helm\s+install\b", re.IGNORECASE)),
    ("helm upgrade", re.compile(r"helm\s+upgrade\b", re.IGNORECASE)),
    ("kubeconfig", re.compile(r"kubeconfig", re.IGNORECASE)),
)


def workflows(raiz: Path) -> list[Path]:
    """Los `.yml` y `.yaml` de `.github/workflows/` bajo `raiz`, ordenados."""
    carpeta = raiz / ".github" / "workflows"
    return sorted(carpeta.glob("*.yml")) + sorted(carpeta.glob("*.yaml"))


def scan(paths: Iterable[Path]) -> list[str]:
    """Los comandos prohibidos de cada workflow dado, por archivo y por línea."""
    problemas: list[str] = []
    for ruta in sorted(paths):
        lineas = ruta.read_text(encoding="utf-8", errors="replace").splitlines()
        for numero, linea in enumerate(lineas, start=1):
            problemas.extend(
                f"{ruta.as_posix()}:{numero}: {termino} no se permite en un workflow {REGLA}"
                for termino, patron in PROHIBIDOS
                if patron.search(linea)
            )
    return problemas


def comprobar(raiz: Path) -> list[str]:
    """Escanea los workflows del repositorio cuya raíz es `raiz`."""
    return scan(workflows(raiz))
