"""Contratos de Veridicus (D1, D15).

En el árbol de desarrollo (instalación editable de `uv sync`) los módulos de
`python/` y los directorios de datos de `contracts/` quedan visibles como
`veridicus_contracts.<nombre>`, igual que en la rueda, que los reubica con
`sources` en pyproject.toml. En la rueda instalada no se hace nada.
"""

from importlib.resources.abc import TraversableResources
from importlib.resources.readers import MultiplexedPath
from pathlib import Path
from typing import Any


class _LectorDeDesarrollo(TraversableResources):
    """Lector de recursos que une src/veridicus_contracts/ y la raíz de contracts/."""

    def __init__(self, directorios: list[Path]) -> None:
        self._directorios = directorios

    def files(self) -> MultiplexedPath:
        return MultiplexedPath(*self._directorios)


class _CargadorDeDesarrollo:
    """Delega en el cargador original y solo cambia el lector de recursos."""

    def __init__(self, original: Any, directorios: list[Path]) -> None:
        self._original = original
        self._directorios = directorios

    def __getattr__(self, nombre: str) -> Any:
        return getattr(self._original, nombre)

    def get_resource_reader(self, nombre: str) -> _LectorDeDesarrollo:
        return _LectorDeDesarrollo(self._directorios)


def _exponer_arbol_de_desarrollo() -> None:
    paquete = Path(__file__).resolve().parent
    raiz = paquete.parents[1]
    if not ((raiz / "python").is_dir() and (raiz / "pyproject.toml").is_file()):
        return  # rueda instalada: ya viene reubicada
    __path__.append(str(raiz / "python"))
    spec = __spec__
    if spec is not None and spec.loader is not None:
        spec.loader = _CargadorDeDesarrollo(spec.loader, [paquete, raiz])  # type: ignore[assignment]  # motivo: el cargador delega en el original


_exponer_arbol_de_desarrollo()
