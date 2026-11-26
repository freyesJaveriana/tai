"""Escritura atómica de archivos de salida (BR11.4).

Se escribe en un archivo temporal del mismo directorio, se sincroniza y se renombra; después se
sincroniza el directorio. Si algo falla se borra el temporal y se lanza `AtomicWriteError` (la CLI
termina con 5): nunca queda un archivo final a medias ni un temporal.
"""

import contextlib
import os
import tempfile
from pathlib import Path


class AtomicWriteError(OSError):
    """La escritura falló; el archivo final no existe o conserva su contenido anterior."""


def _sync_directory(directory: Path) -> None:
    """Sincroniza el directorio para que el renombrado sobreviva a un corte."""
    descriptor = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def write_atomic(path: Path, data: bytes) -> None:
    """Escribe `data` en `path` de forma atómica (BR11.4)."""
    temporary: Path | None = None
    try:
        descriptor, name = tempfile.mkstemp(dir=path.parent, prefix=".", suffix=".tmp")
        temporary = Path(name)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        temporary = None
        _sync_directory(path.parent)
    except OSError as error:
        raise AtomicWriteError(f"no se pudo escribir {path.name}") from error
    finally:
        if temporary is not None:
            with contextlib.suppress(OSError):
                temporary.unlink()
