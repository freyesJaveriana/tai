"""Fechas de los contratos propios: el patrón único `AAAA-MM-DDTHH:MM:SSZ` y E16 (§4.12, BR8.1).

Módulo guardia (100 % de ramas). Todo `format: date-time` de un contrato propio lleva el `pattern`
de `format/datetime.v1.yaml`, y ese patrón rechaza las fracciones y los desfases (E16); además,
`fecha_valida` rechaza una fecha con la forma pero imposible (30 de febrero, hora 25). La copia de C6
(`analyzer/v1/`) no se toca y queda fuera (BR1.8). Las funciones reciben documentos ya cargados o una
ruta y devuelven la lista de problemas (vacía si todo está bien); nunca escriben.
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Any

from veridicus_contracts.checks._contratos import contratos_propios
from veridicus_contracts.loaders import load_file

FORMATO_RELATIVO = "format/datetime.v1.yaml"
FORMA_UNICA = "%Y-%m-%dT%H:%M:%SZ"
VALIDA = "2026-10-02T21:40:00Z"
E16 = ("2026-10-02T21:40:00.123Z", "2026-10-02T16:40:00-05:00")  # fracción y desfase


def fecha_valida(valor: str, patron: str) -> bool:
    """Tiene la forma del patrón y es una fecha real (E16, BR8.1)."""
    if re.fullmatch(patron, valor) is None:
        return False
    try:
        datetime.strptime(valor, FORMA_UNICA)  # solo valida la fecha; no se usa el resultado
    except ValueError:
        return False
    return True


def comprobar_formato(documento: Any) -> list[str]:
    """El propio `format/datetime.v1.yaml`: el patrón acepta la forma única y rechaza E16."""
    ruta = FORMATO_RELATIVO
    if (
        not isinstance(documento, dict)
        or documento.get("type") != "string"
        or documento.get("format") != "date-time"
    ):
        return [f"{ruta}: /: debe ser type string y format date-time (BR8.1)"]
    patron = documento.get("pattern")
    if not isinstance(patron, str):
        return [f"{ruta}: /pattern: falta el patrón (BR8.1)"]
    try:
        re.compile(patron)
    except re.error:
        return [f"{ruta}: /pattern: no es una expresión regular (BR8.1)"]
    if not fecha_valida(VALIDA, patron):
        return [
            f"{ruta}: /pattern: el patrón no acepta la forma única AAAA-MM-DDTHH:MM:SSZ (BR8.1)"
        ]
    if any(re.fullmatch(patron, texto) for texto in E16):
        return [f"{ruta}: /pattern: el patrón admite una forma que E16 rechaza (BR8.1)"]
    return []


def _escapar(clave: object) -> str:
    return str(clave).replace("~", "~0").replace("/", "~1")


def _recorrer(nodo: Any, puntero: str, archivo: str, patron: str, problemas: list[str]) -> None:
    if isinstance(nodo, dict):
        if nodo.get("format") == "date-time" and nodo.get("pattern") != patron:
            problemas.append(
                f"{archivo}: {puntero or '/'}: date-time sin el pattern de {FORMATO_RELATIVO} "
                "(BR8.1, E16)"
            )
        for clave, valor in nodo.items():
            _recorrer(valor, f"{puntero}/{_escapar(clave)}", archivo, patron, problemas)
    elif isinstance(nodo, list):
        for indice, valor in enumerate(nodo):
            _recorrer(valor, f"{puntero}/{indice}", archivo, patron, problemas)


def comprobar_documento(archivo: str, documento: Any, patron: str) -> list[str]:
    """Todo `format: date-time` del documento lleva exactamente `patron`."""
    problemas: list[str] = []
    _recorrer(documento, "", archivo, patron, problemas)
    return problemas


def comprobar(contracts_root: Path) -> list[str]:
    """El formato único y todos los contratos propios; un formato ausente o roto es un problema."""
    ruta = contracts_root / FORMATO_RELATIVO
    if not ruta.is_file():
        return [f"{FORMATO_RELATIVO}: contrato ausente (BR8.1)"]
    formato = load_file(ruta)
    problemas = comprobar_formato(formato)
    if problemas:
        return problemas
    for relativa, archivo in contratos_propios(contracts_root):
        problemas.extend(comprobar_documento(relativa, load_file(archivo), formato["pattern"]))
    return problemas
