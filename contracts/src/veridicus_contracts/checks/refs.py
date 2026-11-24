"""Referencias cerradas entre esquemas (security-design §4.2, NFR10.5, BR12.3, E36).

Módulo guardia (100 % de ramas). Todo `$ref` entre archivos usa el `$id` del esquema de destino como ruta
absoluta que empieza por `/veridicus/contracts/`, que el registro resuelve sin red. Falla ante:

- un esquema `http:`, `https:` o `file:`;
- una ruta relativa o fuera de `/veridicus/contracts/`, como
  `contracts/analyzer/v1/salida.schema.json#/$defs/cita` (E36).

Las referencias locales (`#/...`) son válidas. Los mensajes nombran el archivo, el puntero y la regla,
nunca el valor de la referencia.
"""

from pathlib import Path
from typing import Any

from veridicus_contracts.checks._recorrido import documentos, nodos

PREFIJO = "/veridicus/contracts/"
ESQUEMAS_DE_RED = ("http:", "https:", "file:")
REGLA = "(NFR10.5, E36)"


def comprobar_documento(documento: Any, nombre: str) -> list[str]:
    """Los problemas de un contrato ya cargado, con `nombre` como archivo."""
    problemas: list[str] = []
    for puntero, nodo in nodos(documento):
        referencia = nodo.get("$ref")
        if not isinstance(referencia, str) or referencia.startswith(("#", PREFIJO)):
            continue
        if referencia.lower().startswith(ESQUEMAS_DE_RED):
            texto = "$ref con esquema http, https o file"
        else:
            texto = f"$ref relativo o fuera de {PREFIJO}"
        problemas.append(f"{nombre}#{puntero}: {texto} {REGLA}")
    return problemas


def comprobar(raiz: Path) -> list[str]:
    """Recorre los contratos de `raiz` (sin `vendor/`, `fixtures/` ni `tests/`) y los comprueba."""
    problemas: list[str] = []
    for relativa, documento, legible in documentos(raiz):
        if legible:
            problemas.extend(comprobar_documento(documento, relativa))
        else:
            problemas.append(f"{relativa}: contrato ilegible (NFR10.5)")
    return problemas
