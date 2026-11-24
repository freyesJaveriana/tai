"""Recorrido de los contratos propios de `contracts/` para las guardias de fecha y de nombres.

Salta lo que no es un contrato propio: la copia de C6 (`analyzer/`, que no se toca, BR1.8), los
meta-esquemas de `vendor/`, los *fixtures*, las pruebas, el código y los directorios ocultos. Solo
lee; el orden es el alfabético de cada directorio, para que la salida sea reproducible.
"""

from collections.abc import Iterator
from pathlib import Path

EXCLUIDOS = frozenset(
    {"analyzer", "vendor", "fixtures", "tests", "ts", "src", "build", "dist", "node_modules"}
)
SUFIJOS = (".yaml", ".yml", ".json")


def _recorrer(carpeta: Path, prefijo: str) -> Iterator[tuple[str, Path]]:
    for entrada in sorted(carpeta.iterdir(), key=lambda e: e.name):
        if entrada.name.startswith((".", "_")):
            continue
        if entrada.is_dir():
            if entrada.name not in EXCLUIDOS:
                yield from _recorrer(entrada, f"{prefijo}{entrada.name}/")
        elif entrada.name.endswith(SUFIJOS):
            yield f"{prefijo}{entrada.name}", entrada


def contratos_propios(raiz: Path) -> Iterator[tuple[str, Path]]:
    """Pares (ruta relativa con `/`, ruta) de cada YAML o JSON propio bajo `raiz`."""
    return _recorrer(raiz, "")
