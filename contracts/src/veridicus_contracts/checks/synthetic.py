"""Datos sintéticos y controles negativos (security-design §4.10, NFR12.1, BR1.6; cierra K-04).

Módulo guardia (100 % de ramas). Se publica como `scan(paths)` para que U10, U11 y las demás unidades lo
corran sobre sus `tests/`. Exige:

- cada *fixture* declara `synthetic: true`, `expectation` (`accept` o `reject`), `reject_reason` si es
  `reject` y `mentions`;
- cada mención está en `fixtures/synthetic-names.yaml` y aparece en el texto del fixture;
- ningún campo de texto ni `example` contiene secuencias de 6 a 10 dígitos ni de 23 dígitos, con o sin
  separadores. Se eximen, por su forma completa, los uuid y las huellas de 64 caracteres hexadecimales
  (K-04) y las fechas ISO 8601 que existen, con una fracción de hasta 6 dígitos, incluido el año-mes de
  `price_table_version` (P-T18-5 corregida por P-T18-11).

El alcance de los campos de texto es todo el *fixture*, y en los demás documentos los valores bajo
`example`, `examples`, `literal_sources`, `text`, `note` y `turns` (las `literal_sources` de
`integrity/scan-cases.v1.yaml` y los casos de `integrity/testimony-warning-cases.v1.yaml`). Los mensajes
nombran el archivo y el puntero, nunca el valor.
"""

import json
import os
import re
from collections.abc import Iterable, Iterator
from datetime import date, datetime
from pathlib import Path
from typing import Any

from veridicus_contracts.checks._recorrido import escapar
from veridicus_contracts.loaders import LoadError, load_file

REGLA = "(NFR12.1)"
CATALOGO_POR_OMISION = Path(__file__).resolve().parents[3] / "fixtures" / "synthetic-names.yaml"
SUFIJOS = (".yaml", ".yml", ".json")
DIRECTORIOS_SALTADOS = frozenset(
    {"vendor", "node_modules", ".venv", "ts", "build", "__pycache__", ".mypy_cache", ".ruff_cache"}
    | {".pytest_cache", ".hypothesis"}
)
CAMPOS_DE_FIXTURE = ("fixture_id", "contract", "synthetic", "expectation", "mentions", "payload")
CLAVES_DE_TEXTO = frozenset({"example", "examples", "literal_sources", "text", "note", "turns"})

_SECUENCIA = re.compile(r"[0-9](?:[ .\-/]?[0-9])*")
_EXENTOS = (
    re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.IGNORECASE),
    re.compile(r"[a-f0-9]{64}"),
)
# Una fecha ISO 8601: año-mes, fecha o fecha con hora, con una fracción de hasta 6 dígitos. La forma sola no
# basta: `_es_fecha` exige que la fecha y la hora existan (F-03).
_FECHA = re.compile(
    r"(?P<anio>[0-9]{4})-(?P<mes>[0-9]{2})(?:-(?P<dia>[0-9]{2})"
    r"(?P<hora>[Tt ][0-9]{2}:[0-9]{2}(?::[0-9]{2}(?:\.[0-9]{1,6})?)?(?:[Zz]|[+-][0-9]{2}:[0-9]{2})?)?)?"
)


def archivos(paths: Iterable[Path | str]) -> list[Path]:
    """Los `.yaml`, `.yml` y `.json` que cubre `paths`, sin los directorios ajenos, ordenados."""
    encontrados: set[Path] = set()
    for ruta in map(Path, paths):
        if ruta.is_dir():
            for carpeta, subcarpetas, nombres in os.walk(ruta):
                subcarpetas[:] = [d for d in subcarpetas if d not in DIRECTORIOS_SALTADOS]
                encontrados.update(Path(carpeta) / n for n in nombres if n.endswith(SUFIJOS))
        elif ruta.name.endswith(SUFIJOS):
            encontrados.add(ruta)
    return sorted(encontrados)


def _catalogo(ruta: Path) -> tuple[frozenset[str], list[str]]:
    try:
        datos = load_file(ruta)
        return frozenset(datos["personas"]) | frozenset(datos["lugares"]), []
    except (LoadError, OSError, KeyError, TypeError):
        return frozenset(), [f"{ruta.as_posix()}: catálogo de nombres sintéticos ilegible {REGLA}"]


def _formato(archivo: str, fixture: dict[str, Any], nombres: frozenset[str]) -> list[str]:
    """Los problemas del formato de fixture de §4.10."""
    faltan = [campo for campo in CAMPOS_DE_FIXTURE if campo not in fixture]
    if faltan:
        return [f"{archivo}: faltan campos de fixture: {', '.join(faltan)} {REGLA}"]
    problemas: list[str] = []
    if fixture["synthetic"] is not True:
        problemas.append(f"{archivo}#/synthetic: synthetic debe ser true {REGLA}")
    esperado = fixture["expectation"]
    razon = fixture.get("reject_reason")
    if esperado not in ("accept", "reject"):
        problemas.append(f"{archivo}#/expectation: expectation debe ser accept o reject {REGLA}")
    elif esperado == "reject" and not (isinstance(razon, str) and razon):
        problemas.append(f"{archivo}#/reject_reason: reject exige reject_reason {REGLA}")
    elif esperado == "accept" and razon is not None:
        problemas.append(f"{archivo}#/reject_reason: accept no lleva reject_reason {REGLA}")
    menciones = fixture["mentions"]
    if not isinstance(menciones, list):
        return [*problemas, f"{archivo}#/mentions: mentions debe ser una lista {REGLA}"]
    texto = json.dumps(fixture["payload"], ensure_ascii=False)
    for indice, mencion in enumerate(menciones):
        if not (isinstance(mencion, str) and mencion in nombres):
            problemas.append(
                f"{archivo}#/mentions/{indice}: mención que no está en el catálogo {REGLA}"
            )
        elif mencion not in texto:
            problemas.append(
                f"{archivo}#/mentions/{indice}: mención que no aparece en el texto {REGLA}"
            )
    return problemas


def _textos(valor: Any, puntero: str, dentro: bool) -> Iterator[tuple[str, str]]:
    """Los campos de texto del alcance: (puntero, texto)."""
    if isinstance(valor, str):
        if dentro:
            yield puntero, valor
    elif isinstance(valor, dict):
        for clave, hijo in valor.items():
            yield from _textos(
                hijo, f"{puntero}/{escapar(clave)}", dentro or clave in CLAVES_DE_TEXTO
            )
    elif isinstance(valor, list):
        for indice, hijo in enumerate(valor):
            yield from _textos(hijo, f"{puntero}/{indice}", dentro)


def _es_fecha(texto: str) -> bool:
    """Una fecha ISO 8601 que existe: año-mes, fecha, o fecha con hora y fracción de hasta 6 dígitos."""
    forma = _FECHA.fullmatch(texto)
    if forma is None:
        return False
    try:
        if forma["dia"] is None:
            date(int(forma["anio"]), int(forma["mes"]), 1)
        elif forma["hora"] is None:
            date.fromisoformat(texto)
        else:
            datetime.fromisoformat(texto.upper())
    except ValueError:
        return False
    return True


def _sospechoso(texto: str) -> bool:
    if _es_fecha(texto) or any(forma.fullmatch(texto) for forma in _EXENTOS):
        return False
    for secuencia in _SECUENCIA.finditer(texto):
        digitos = sum(c.isdigit() for c in secuencia.group())
        if 6 <= digitos <= 10 or digitos == 23:
            return True
    return False


def _es_fixture(documento: Any) -> bool:
    return isinstance(documento, dict) and bool(
        {"fixture_id", "expectation", "payload"} & documento.keys()
    )


def _problemas_de(ruta: Path, nombres: frozenset[str]) -> list[str]:
    archivo = ruta.as_posix()
    try:
        documento = load_file(ruta)
    except LoadError:
        return [f"{archivo}: archivo ilegible {REGLA}"]
    es_fixture = _es_fixture(documento)
    problemas = _formato(archivo, documento, nombres) if es_fixture else []
    problemas.extend(
        f"{archivo}#{puntero}: secuencia numérica que parece un identificador real {REGLA}"
        for puntero, texto in _textos(documento, "", es_fixture)
        if _sospechoso(texto)
    )
    return problemas


def scan(paths: Iterable[Path | str], catalogo: Path | None = None) -> list[str]:
    """Los problemas de datos no sintéticos en los archivos que cubre `paths`."""
    nombres, problemas = _catalogo(catalogo or CATALOGO_POR_OMISION)
    for ruta in archivos(paths):
        problemas.extend(_problemas_de(ruta, nombres))
    return problemas
