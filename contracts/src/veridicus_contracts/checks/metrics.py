"""Métricas de `contracts/metrics/`: prefijo, unicidad, etiquetas cerradas y sin texto libre (§4.12).

Módulo guardia (100 % de ramas). Corre sobre todos los archivos de `metrics/`, que tienen la forma
de C15: `schema_version`, `endpoint` y `metrics[]` con `name`, `type`, `labels` y `description`.
Cada etiqueta es un objeto `{name, values}`; `session_id` es la excepción y declara el `pattern` de
un UUID. `error_code` toma un `code` del catálogo o el centinela `none` (E-20). Las funciones
reciben documentos ya cargados y devuelven la lista de problemas (vacía si todo está bien); nunca
escriben. Un mensaje nombra el archivo, el puntero y la regla, nunca el valor (NFR10, AUTONOMIA-04).
"""

from collections.abc import Collection, Mapping
from pathlib import Path
from typing import Any

from veridicus_contracts.loaders import load_file

PREFIJO = "veridicus_"
TIPOS = frozenset({"counter", "gauge", "histogram"})
ETIQUETAS = frozenset(
    {
        "state",
        "session_id",
        "mode",
        "outcome",
        "error_code",
        "provider",
        "role",
        "slot",
        "category",
        "origin",
    }
)
PATRON_UUID = "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
SIN_ERROR = "none"  # centinela único de `error_code` en una serie sin error (E-20)
CATALOGO_RELATIVO = "errors/error-codes.v2.yaml"
FORMA = "la forma no es la de C15 (schema_version, endpoint y metrics con elementos)"


def _etiqueta(donde: str, etiqueta: Any, codigos: Collection[str]) -> list[str]:
    if not isinstance(etiqueta, dict) or not isinstance(etiqueta.get("name"), str):
        return [f"{donde}: la etiqueta debe ser un objeto con name (§4.12)"]
    nombre = etiqueta["name"]
    if nombre not in ETIQUETAS:
        return [f"{donde}: la etiqueta no es de la lista cerrada (§4.12)"]
    if nombre == "session_id":
        if etiqueta.get("pattern") != PATRON_UUID or "values" in etiqueta:
            return [f"{donde}: session_id declara solo el patrón de un UUID (§4.12)"]
        return []
    if "pattern" in etiqueta:
        return [f"{donde}: la etiqueta admite texto libre; declare values (§4.12)"]
    valores = etiqueta.get("values")
    if not isinstance(valores, list) or not valores:
        return [f"{donde}: la etiqueta declara values sin elementos (§4.12)"]
    if not all(isinstance(v, str) and v for v in valores) or len(set(valores)) != len(valores):
        return [f"{donde}: los values deben ser textos no vacíos y distintos (§4.12)"]
    if nombre == "error_code" and not set(valores) <= {*codigos, SIN_ERROR}:
        return [f"{donde}: error_code con un valor fuera del catálogo y de none (E-20)"]
    return []


def _metrica(archivo: str, indice: int, metrica: Any, codigos: Collection[str]) -> list[str]:
    donde = f"{archivo}: /metrics/{indice}"
    if not isinstance(metrica, dict):
        return [f"{donde}: la métrica debe ser un objeto (C15)"]
    problemas: list[str] = []
    nombre = metrica.get("name")
    if not (isinstance(nombre, str) and nombre.startswith(PREFIJO)):
        problemas.append(f"{donde}/name: el nombre no empieza por {PREFIJO} (BR8.2)")
    if metrica.get("type") not in TIPOS:
        problemas.append(f"{donde}/type: el tipo no es counter, gauge ni histogram (C15)")
    descripcion = metrica.get("description")
    if not (isinstance(descripcion, str) and descripcion.strip()):
        problemas.append(f"{donde}/description: falta la descripción (C15)")
    etiquetas = metrica.get("labels")
    if not isinstance(etiquetas, list):
        problemas.append(f"{donde}/labels: las etiquetas deben ser una lista (C15)")
    else:
        for numero, etiqueta in enumerate(etiquetas):
            problemas.extend(_etiqueta(f"{donde}/labels/{numero}", etiqueta, codigos))
        nombres = [e["name"] for e in etiquetas if isinstance(e, dict) and "name" in e]
        if len(set(map(str, nombres))) != len(nombres):
            problemas.append(f"{donde}/labels: hay etiquetas repetidas (§4.12)")
    return problemas


def comprobar_documentos(documentos: Mapping[str, Any], codigos: Collection[str]) -> list[str]:
    """Todas las reglas de §4.12 sobre los documentos de `metrics/`, por nombre de archivo."""
    problemas: list[str] = []
    vistos: dict[str, str] = {}
    for archivo, documento in documentos.items():
        valido = (
            isinstance(documento, dict)
            and isinstance(documento.get("schema_version"), str)
            and isinstance(documento.get("endpoint"), str)
            and isinstance(documento.get("metrics"), list)
            and bool(documento["metrics"])
        )
        if not valido:
            problemas.append(f"{archivo}: /: {FORMA}")
            continue
        for indice, metrica in enumerate(documento["metrics"]):
            problemas.extend(_metrica(archivo, indice, metrica, codigos))
            nombre = metrica.get("name") if isinstance(metrica, dict) else None
            if not isinstance(nombre, str):
                continue
            puntero = f"/metrics/{indice}/name"
            if nombre in vistos:
                problemas.append(
                    f"{archivo}: {puntero}: el nombre ya está en {vistos[nombre]} (§4.12)"
                )
            else:
                vistos[nombre] = f"{archivo} {puntero}"
    return problemas


def comprobar(contracts_root: Path) -> list[str]:
    """Las reglas de §4.12 sobre todos los archivos de `metrics/` y el catálogo de errores."""
    archivos = sorted(
        ruta for ruta in (contracts_root / "metrics").iterdir() if ruta.name.endswith(".yaml")
    )
    if not archivos:
        return ["metrics/: no hay archivos de métricas que comprobar (§4.12)"]
    codigos = load_file(contracts_root / CATALOGO_RELATIVO)["codes"]
    documentos = {f"metrics/{ruta.name}": load_file(ruta) for ruta in archivos}
    return comprobar_documentos(documentos, codigos)
