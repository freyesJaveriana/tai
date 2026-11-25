"""Recorrido común de los contratos de `contracts/` para las guardias `refs` y `redos` (paso 19).

Reglas que sirve: BR12.3 y NFR10.5 (referencias cerradas) y NFR10.6 (patrones sin retroceso).

Lee cada `.yaml`, `.yml` o `.json` bajo una raíz con el cargador seguro del paquete y salta los directorios
que no son contratos del paquete: `vendor/` (esquemas de terceros), `fixtures/` y `tests/` (casos, con
rutas y patrones sembrados a propósito), la mitad TypeScript y los entornos.
"""

import os
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from veridicus_contracts.loaders import LoadError, load_file

SUFIJOS = (".yaml", ".yml", ".json")
DIRECTORIOS_SALTADOS = frozenset(
    {"vendor", "fixtures", "tests", "ts", "node_modules", ".venv", "build", "__pycache__"}
    | {".mypy_cache", ".ruff_cache", ".pytest_cache", ".hypothesis"}
)


def _archivos(raiz: Path, saltados: frozenset[str]) -> Iterator[Path]:
    for carpeta, subcarpetas, nombres in os.walk(raiz):
        subcarpetas[:] = sorted(d for d in subcarpetas if d not in saltados)
        for nombre in sorted(nombres):
            if nombre.endswith(SUFIJOS):
                yield Path(carpeta) / nombre


def documentos(
    raiz: Path, saltados: frozenset[str] = DIRECTORIOS_SALTADOS
) -> Iterator[tuple[str, Any, bool]]:
    """Cada contrato bajo `raiz`: su ruta relativa, su contenido y si se pudo leer (en orden)."""
    for ruta in sorted(_archivos(raiz, saltados)):
        relativa = ruta.relative_to(raiz).as_posix()
        try:
            yield relativa, load_file(ruta), True
        except LoadError:
            yield relativa, None, False


def escapar(clave: str) -> str:
    """Una clave como segmento de un puntero JSON (RFC 6901)."""
    return clave.replace("~", "~0").replace("/", "~1")


def nodos(valor: Any, puntero: str = "") -> Iterator[tuple[str, dict[str, Any]]]:
    """Cada objeto del documento, con su puntero JSON, en orden de aparición."""
    if isinstance(valor, dict):
        yield puntero, valor
        for clave, hijo in valor.items():
            yield from nodos(hijo, f"{puntero}/{escapar(clave)}")
    elif isinstance(valor, list):
        for indice, hijo in enumerate(valor):
            yield from nodos(hijo, f"{puntero}/{indice}")
