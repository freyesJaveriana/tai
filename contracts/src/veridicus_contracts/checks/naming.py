"""Nombres de los contratos propios: ASCII `snake_case` y `code` en `dominio.motivo` (§4.12, CD-05).

Módulo guardia (100 % de ramas). Comprueba los nombres de propiedades (las claves bajo
`properties`), de parámetros de ruta y de consulta y de métricas, y la forma de todo `code`: las
claves del catálogo de errores, el `enum` de `ErrorCode` y el `const` o `enum` de una propiedad
`code`. Los nombres de cabeceras y de cookies son los del protocolo y no se comprueban. La copia de
C6 (`analyzer/`) queda fuera: la regla 8 de contract-summary conserva sus nombres (BR1.8). Las
funciones reciben documentos ya cargados o una ruta y devuelven la lista de problemas (vacía si todo
está bien); nunca escriben. Un mensaje nombra el archivo, el puntero y la regla, nunca el valor de
un `code`.
"""

import re
from pathlib import Path
from typing import Any

from veridicus_contracts.checks._contratos import contratos_propios
from veridicus_contracts.loaders import load_file

__all__ = [
    "NOMBRE",
    "comprobar",
    "comprobar_catalogo",
    "comprobar_documento",
    "comprobar_metricas",
    "contratos_propios",
]

NOMBRE = re.compile(r"[a-z][a-z0-9_]*")
CODE = re.compile(r"[a-z][a-z_]*\.[a-z][a-z_]*")
PARAMETROS = frozenset({"query", "path"})
CLAVES_DE_CODE = frozenset({"code", "ErrorCode"})
CATALOGO_RELATIVO = "errors/error-codes.v2.yaml"
NO_SNAKE = "el nombre no es ASCII snake_case (CD-05)"
NO_CODE = "el code no tiene la forma dominio.motivo (CD-05)"


def _escapar(clave: object) -> str:
    return str(clave).replace("~", "~0").replace("/", "~1")


def _es_nombre(valor: object) -> bool:
    return isinstance(valor, str) and NOMBRE.fullmatch(valor) is not None


def _es_code(valor: object) -> bool:
    return isinstance(valor, str) and CODE.fullmatch(valor) is not None


def _recorrer(
    nodo: Any, puntero: str, clave: str | None, archivo: str, problemas: list[str]
) -> None:
    if isinstance(nodo, dict):
        if clave == "properties":
            problemas.extend(
                f"{archivo}: {puntero}/{_escapar(nombre)}: {NO_SNAKE}"
                for nombre in nodo
                if not _es_nombre(nombre)
            )
        if clave in CLAVES_DE_CODE:
            for palabra in ("const", "enum"):
                if palabra not in nodo:
                    continue
                valor = nodo[palabra]
                candidatos = valor if isinstance(valor, list) else [valor]
                for indice, candidato in enumerate(candidatos):
                    if not _es_code(candidato):
                        sufijo = f"/{indice}" if isinstance(valor, list) else ""
                        problemas.append(f"{archivo}: {puntero}/{palabra}{sufijo}: {NO_CODE}")
        for hija, valor in nodo.items():
            _recorrer(valor, f"{puntero}/{_escapar(hija)}", hija, archivo, problemas)
    elif isinstance(nodo, list):
        if clave == "parameters":
            problemas.extend(
                f"{archivo}: {puntero}/{indice}/name: {NO_SNAKE}"
                for indice, parametro in enumerate(nodo)
                if isinstance(parametro, dict)
                and parametro.get("in") in PARAMETROS
                and not _es_nombre(parametro.get("name"))
            )
        for indice, valor in enumerate(nodo):
            _recorrer(valor, f"{puntero}/{indice}", clave, archivo, problemas)


def comprobar_documento(archivo: str, documento: Any) -> list[str]:
    """Propiedades, parámetros de ruta y consulta y `code` de un documento."""
    problemas: list[str] = []
    _recorrer(documento, "", None, archivo, problemas)
    return problemas


def comprobar_catalogo(archivo: str, documento: Any) -> list[str]:
    """Cada clave de `codes` del catálogo de errores tiene la forma `dominio.motivo`."""
    codes = documento.get("codes") if isinstance(documento, dict) else None
    if not isinstance(codes, dict):
        return [f"{archivo}: /codes: debe ser un mapa de codes (CD-05)"]
    return [f"{archivo}: /codes/{_escapar(code)}: {NO_CODE}" for code in codes if not _es_code(code)]


def comprobar_metricas(archivo: str, documento: Any) -> list[str]:
    """El nombre de cada métrica de un archivo de `metrics/` es ASCII `snake_case`."""
    metricas = documento.get("metrics") if isinstance(documento, dict) else None
    if not isinstance(metricas, list):
        return []
    return [
        f"{archivo}: /metrics/{indice}/name: {NO_SNAKE}"
        for indice, metrica in enumerate(metricas)
        if isinstance(metrica, dict) and not _es_nombre(metrica.get("name"))
    ]


def comprobar(contracts_root: Path) -> list[str]:
    """Todas las reglas de nombres sobre los contratos propios de `contracts/`."""
    problemas: list[str] = []
    for relativa, archivo in contratos_propios(contracts_root):
        documento = load_file(archivo)
        problemas.extend(comprobar_documento(relativa, documento))
        if relativa == CATALOGO_RELATIVO:
            problemas.extend(comprobar_catalogo(relativa, documento))
        elif relativa.startswith("metrics/"):
            problemas.extend(comprobar_metricas(relativa, documento))
    return problemas
