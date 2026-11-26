"""El directorio de resultados y la regla del corpus (BR11.5, BR11.6).

Una transcripción con origen `corpus` solo se analiza si Git no puede rastrear el directorio de
salida: si algún ancestro tiene `.git`, `git check-ignore` debe cubrirlo; si no cubre o Git no está
disponible, no se analiza. Fuera de todo repositorio (por ejemplo, la carpeta del proyecto en ZINE) se
permite. Sin `--salida`, el directorio es `resultados-locales/<fecha>-analyze`, que `.gitignore` cubre.
"""

import os
import subprocess
from datetime import date
from pathlib import Path
from typing import Final

DEFAULT_ROOT: Final = "resultados-locales"
GIT_TIMEOUT_S: Final = 20
# Un archivo que aún no existe dentro del directorio: `check-ignore` mira la ruta y sus padres.
_PROBE: Final = "AVISO.txt"


def default_output_dir(today: date, subcommand: str = "analyze") -> Path:
    """`resultados-locales/<fecha>-<subcomando>`, relativo al directorio de trabajo."""
    return Path(DEFAULT_ROOT) / f"{today.isoformat()}-{subcommand}"


def _nearest_existing(path: Path) -> Path:
    current = path.absolute()
    while not current.exists():
        current = current.parent
    return current


def is_writable(directory: Path) -> bool:
    """El directorio existe y se puede escribir, o se puede crear bajo su ancestro existente."""
    ancestor = _nearest_existing(directory)
    return ancestor.is_dir() and os.access(ancestor, os.W_OK | os.X_OK)


def _inside_git_work_tree(directory: Path) -> bool:
    """Algún ancestro del directorio tiene `.git` (carpeta o archivo de un *worktree*)."""
    return any((ancestor / ".git").exists() for ancestor in (directory, *directory.parents))


def is_safe_for_corpus(directory: Path) -> bool:
    """BR11.5: fuera de todo repositorio, o dentro de uno que lo ignora. Git ausente o con error, no."""
    absolute = directory.absolute()
    if not _inside_git_work_tree(absolute):
        return True
    try:
        result = subprocess.run(  # noqa: S603 - ejecutable y argumentos fijos, sin entrada externa
            ["git", "check-ignore", "-q", str(absolute / _PROBE)],  # noqa: S607 - `git` del PATH
            cwd=_nearest_existing(absolute),
            capture_output=True,
            timeout=GIT_TIMEOUT_S,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0
