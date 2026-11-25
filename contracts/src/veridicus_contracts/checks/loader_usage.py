"""Carga segura de YAML y suite sin subprocesos (security-design §4.1 y §4.2, NFR10.4, NFR10.5).

Módulo guardia (100 % de ramas). Recorre los `.py` de `src/` y `tests/` con `ast` y falla ante:

- `import yaml` (PyYAML);
- una llamada `YAML(...)` fuera de `loaders.py`, o con un `typ` distinto de `"safe"`;
- `load_all` o `Loader=`;
- `subprocess`, `multiprocessing` u `os.system`, salvo en la lista cerrada `EXCEPCIONES`.

`EXCEPCIONES` es cerrada (E-19): cada entrada nombra la ruta, el módulo que admite y su motivo, una prueba
fija la lista exacta y añadir una entrada exige una precisión aprobada. La excepción no exime ninguna otra
regla ni otro módulo prohibido del mismo archivo. Se publica como `scan(paths)` para que U11 la reutilice.

Los mensajes nombran el archivo, la línea y la regla, nunca el código.
"""

import ast
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import NamedTuple

LOADERS = "src/veridicus_contracts/loaders.py"
MODULOS_PROHIBIDOS = ("subprocess", "multiprocessing")


class Excepcion(NamedTuple):
    """Un archivo al que se admite un módulo prohibido, con su motivo."""

    ruta: str
    modulos: frozenset[str]
    motivo: str


EXCEPCIONES = (
    Excepcion(
        "src/veridicus_contracts/tools/check_package.py",
        frozenset({"subprocess"}),
        "§4.2: el paso del paquete en entorno limpio corre `uv build` y la instalación en su propio paso",
    ),
    Excepcion(
        "tests/test_package_map.py",
        frozenset({"subprocess"}),
        "E-19: `uv build` y `mypy --strict` sobre una copia, con argumentos fijos y sin entrada externa",
    ),
)


def _relativa(archivo: Path, raiz: Path | None) -> str | None:
    """La ruta de `archivo` relativa a `raiz` (la carpeta `contracts/`), o `None` si no cuelga de ella."""
    if raiz is None:
        return None
    try:
        return archivo.resolve().relative_to(raiz.resolve()).as_posix()
    except ValueError:
        return None


def archivos(paths: Iterable[Path | str]) -> list[Path]:
    """Los `.py` que cubre `paths`: cada archivo dado y cada `.py` bajo cada directorio, ordenados."""
    encontrados: set[Path] = set()
    for ruta in map(Path, paths):
        candidatos = ruta.rglob("*.py") if ruta.is_dir() else [ruta]
        encontrados.update(c for c in candidatos if c.suffix == ".py")
    return sorted(encontrados)


def _modulo_prohibido(nombre: str) -> str | None:
    raiz = nombre.split(".")[0]
    return raiz if raiz in MODULOS_PROHIBIDOS else None


def _hallazgos(arbol: ast.AST) -> Iterator[tuple[int, str, str | None]]:
    """(línea, texto, módulo prohibido si aplica) de cada defecto del árbol."""
    for nodo in ast.walk(arbol):
        linea = getattr(nodo, "lineno", 0)
        if isinstance(nodo, ast.Import):
            for alias in nodo.names:
                yield from _de_importacion(linea, alias.name, None)
        elif isinstance(nodo, ast.ImportFrom):
            yield from _de_importacion(linea, nodo.module or "", [a.name for a in nodo.names])
        elif isinstance(nodo, ast.Call):
            yield from _de_llamada(linea, nodo)
        elif isinstance(nodo, ast.Attribute):
            yield from _de_atributo(linea, nodo)


def _de_importacion(
    linea: int, modulo: str, nombres: list[str] | None
) -> Iterator[tuple[int, str, str | None]]:
    raiz = modulo.split(".")[0]
    if raiz == "yaml":
        yield (
            linea,
            "PyYAML no se usa: el único lector es ruamel.yaml en loaders.py (NFR10.4)",
            None,
        )
    if (prohibido := _modulo_prohibido(modulo)) is not None:
        yield linea, f"{prohibido} no se usa en el paquete ni en las pruebas (NFR10.5)", prohibido
    if modulo == "os" and "system" in (nombres or []):
        yield linea, "os.system no se usa en el paquete ni en las pruebas (NFR10.5)", "os.system"
    if "load_all" in (nombres or []):
        yield linea, "load_all no se usa: un solo documento por archivo (NFR10.4)", None


def _de_llamada(linea: int, llamada: ast.Call) -> Iterator[tuple[int, str, str | None]]:
    funcion = llamada.func
    nombre = funcion.id if isinstance(funcion, ast.Name) else getattr(funcion, "attr", "")
    if nombre == "YAML":
        yield linea, "YAML(...) fuera de loaders.py (NFR10.4)", "YAML"
        tipo = next((k.value for k in llamada.keywords if k.arg == "typ"), None)
        if not (isinstance(tipo, ast.Constant) and tipo.value == "safe"):
            yield linea, 'typ distinto de "safe" en YAML(...) (NFR10.4)', None
    if any(k.arg == "Loader" for k in llamada.keywords):
        yield linea, "Loader= no se usa (NFR10.4)", None


def _de_atributo(linea: int, atributo: ast.Attribute) -> Iterator[tuple[int, str, str | None]]:
    if atributo.attr == "load_all":
        yield linea, "load_all no se usa: un solo documento por archivo (NFR10.4)", None
    if (
        atributo.attr == "system"
        and isinstance(atributo.value, ast.Name)
        and atributo.value.id == "os"
    ):
        yield linea, "os.system no se usa en el paquete ni en las pruebas (NFR10.5)", "os.system"


def _admitido(relativa: str | None, modulo: str | None) -> bool:
    if modulo is None:
        return False
    if modulo == "YAML":
        return relativa == LOADERS
    return any(relativa == e.ruta and modulo in e.modulos for e in EXCEPCIONES)


def _problemas_de(archivo: Path, raiz: Path | None) -> list[str]:
    try:
        arbol = ast.parse(archivo.read_text(encoding="utf-8"))
    except (OSError, SyntaxError, UnicodeDecodeError, ValueError):
        return [f"{archivo.as_posix()}:1: no se pudo interpretar el archivo (NFR10.4)"]
    relativa = _relativa(archivo, raiz)
    return [
        f"{archivo.as_posix()}:{linea}: {texto}"
        for linea, texto, modulo in sorted(set(_hallazgos(arbol)), key=lambda h: (h[0], h[1]))
        if not _admitido(relativa, modulo)
    ]


def scan(paths: Iterable[Path | str], raiz: Path | None = None) -> list[str]:
    """Los problemas de carga insegura y de subprocesos en los `.py` que cubre `paths`.

    `raiz` es la carpeta `contracts/`: las excepciones de `EXCEPCIONES` y la de `loaders.py` se comparan
    por la ruta completa relativa a ella (E-19). Sin `raiz` no se exime nada, así que quien reutilice
    `scan` desde otro servicio no hereda las excepciones de `contracts/`.
    """
    problemas: list[str] = []
    for archivo in archivos(paths):
        problemas.extend(_problemas_de(archivo, raiz))
    return problemas


def comprobar(raiz: Path) -> list[str]:
    """Escanea `src/` y `tests/` bajo `raiz` (la carpeta `contracts/`)."""
    return scan([raiz / "src", raiz / "tests"], raiz=raiz)
