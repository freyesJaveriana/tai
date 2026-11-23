"""Módulo guardia del catálogo C25: forma, tipos, derivadas y relaciones (§4.4; E33, E37).

Módulo guardia (100 % de ramas). Comprueba `limits.v1.yaml` sin importar el catálogo
empaquetado: recibe el documento ya cargado (`comprobar_catalogo`) o una ruta (`comprobar`) y
devuelve la lista de problemas (vacía si todo está bien); nunca escribe. Las comprobaciones
van por etapas: si la forma falla, no se miran los tipos, y así hasta las relaciones.
"""

import math
import re
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from veridicus_contracts.limits import UNIDADES_DECIMALES, relaciones_rotas
from veridicus_contracts.loaders import load_file

UNIDADES = frozenset(
    {
        "chars",
        "turns",
        "bytes",
        "s",
        "ms",
        "deliveries",
        "suggestions",
        "words",
        "ratio",
        "days",
        "levels",
    }
)
SECCIONES = frozenset({"schema_version", "limits", "relations"})
CLAVES = frozenset({"value", "unit", "owner", "used_in"})
CLAVES_OPCIONALES = frozenset({"derived_from"})
OPERADORES = frozenset({"<", "<="})
VERSION = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+")
NOMBRE = re.compile(r"[a-z][a-z0-9_]*")
DUENO = re.compile(r"U[0-9]+")
USO = re.compile(r"C[0-9]+")

# Cifras que otras unidades piden y que no pueden faltar (NFRD-U6-01, NFRD-U7-04, NFRD-U9-03,
# NFRD-U12-02), más el origen de las derivadas.
OBLIGATORIAS = (
    "transcript_body_max_bytes",
    "import_body_max_bytes",
    "import_file_max_bytes",
    "cursor_max_chars",
    "voice_body_max_bytes",
    "research_report_read_timeout_s",
    "audio_max_bytes",
    "audio_base64_max_chars",
)

# nombre derivado -> (origen, fórmula del valor a partir del origen); §4.4 y NFRD-U6-01, -U9-03.
DERIVADAS: dict[str, tuple[str, Callable[[int], int]]] = {
    "audio_base64_max_chars": ("audio_max_bytes", lambda origen: 4 * -(-origen // 3)),
    "transcript_body_max_bytes": ("transcript_max_chars", lambda origen: 4 * origen + 4096),
    "import_body_max_bytes": ("import_file_max_bytes", lambda origen: origen + 16384),
    "voice_body_max_bytes": ("audio_max_bytes", lambda origen: origen + 16384),
}

# Relaciones que el catálogo debe declarar (§5, NFR-U6-01, NFRD-U6-01).
RELACIONES_OBLIGATORIAS = (
    ("fragment_overlap_turns", "<", "fragment_window_turns"),
    ("retention_min_days", "<=", "retention_max_days"),
    ("heartbeat_write_min_s", "<", "heartbeat_timeout_s"),
    ("poll_interval_active_s", "<=", "poll_interval_s"),
    ("voice_deadline_base_s", "<=", "voice_deadline_max_s"),
    ("run_deadline_incremental_s", "<=", "run_deadline_final_s"),
    ("import_file_max_bytes", "<=", "run_message_max_bytes"),
    ("import_file_max_bytes", "<", "import_body_max_bytes"),
)


def _es_texto(valor: Any, patron: re.Pattern[str]) -> bool:
    return isinstance(valor, str) and patron.fullmatch(valor) is not None


def _forma_entrada(nombre: str, entrada: Any, nombres: Mapping[str, Any]) -> list[str]:
    if not isinstance(entrada, dict):
        return [f"{nombre}: la entrada debe ser un objeto"]
    problemas: list[str] = []
    claves = set(entrada)
    if not CLAVES <= claves or not claves <= CLAVES | CLAVES_OPCIONALES:
        faltan = sorted(CLAVES - claves)
        sobran = sorted(claves - CLAVES - CLAVES_OPCIONALES)
        problemas.append(f"{nombre}: claves inválidas (faltan {faltan}, sobran {sobran})")
    if not NOMBRE.fullmatch(nombre):
        problemas.append(f"{nombre}: nombre inválido (minúsculas, dígitos y guion bajo)")
    if "value" in entrada and entrada["value"] is None:
        problemas.append(f"{nombre}: value no puede ser nulo")
    if "unit" in entrada and not (isinstance(entrada["unit"], str) and entrada["unit"] in UNIDADES):
        problemas.append(f"{nombre}: unit {entrada['unit']!r} fuera de la lista cerrada")
    if "owner" in entrada and not _es_texto(entrada["owner"], DUENO):
        problemas.append(f"{nombre}: owner {entrada['owner']!r} debe ser una unidad (U<n>)")
    if "used_in" in entrada and not (
        isinstance(entrada["used_in"], list) and all(_es_texto(u, USO) for u in entrada["used_in"])
    ):
        problemas.append(f"{nombre}: used_in debe ser una lista de contratos (C<n>)")
    if "derived_from" in entrada and (
        not isinstance(entrada["derived_from"], str)
        or entrada["derived_from"] == nombre
        or entrada["derived_from"] not in nombres
    ):
        problemas.append(f"{nombre}: derived_from debe nombrar otra entrada del catálogo")
    return problemas


def _forma_relacion(relacion: Any, nombres: Mapping[str, Any]) -> list[str]:
    valida = (
        isinstance(relacion, list)
        and len(relacion) == 3
        and all(isinstance(parte, str) for parte in relacion)
        and relacion[0] in nombres
        and relacion[1] in OPERADORES
        and relacion[2] in nombres
    )
    return [] if valida else [f"relations: {relacion!r} debe ser [nombre, '<' o '<=', nombre]"]


def comprobar_forma(documento: Any) -> list[str]:
    """Secciones, claves de cada entrada, unidades, dueños, usos y forma de las relaciones."""
    if not isinstance(documento, dict):
        return ["el catálogo debe ser un objeto"]
    problemas: list[str] = []
    if set(documento) != SECCIONES:
        problemas.append(
            f"secciones {sorted(documento)}: deben ser exactamente {sorted(SECCIONES)}"
        )
    if not _es_texto(documento.get("schema_version"), VERSION):
        problemas.append("schema_version debe ser un texto con forma de versión (n.n.n)")
    limites = documento.get("limits")
    relaciones = documento.get("relations")
    if not isinstance(limites, dict) or not limites:
        problemas.append("limits debe ser un objeto con al menos una entrada")
        limites = {}
    if not isinstance(relaciones, list):
        problemas.append("relations debe ser una lista")
        relaciones = []
    for nombre, entrada in limites.items():
        problemas.extend(_forma_entrada(nombre, entrada, limites))
    for relacion in relaciones:
        problemas.extend(_forma_relacion(relacion, limites))
    problemas.extend(
        f"{nombre}: cifra obligatoria ausente" for nombre in OBLIGATORIAS if nombre not in limites
    )
    return problemas


def _valor_valido(unidad: str, valor: Any) -> bool:
    if isinstance(valor, bool) or not isinstance(valor, int | float) or not math.isfinite(valor):
        return False
    if unidad == "ratio":
        return 0 < valor <= 1
    if unidad in UNIDADES_DECIMALES:
        return valor > 0
    return isinstance(valor, int) and valor >= 1


def comprobar_tipos(limites: Mapping[str, Mapping[str, Any]]) -> list[str]:
    """Todo valor es entero ≥ 1, salvo `ratio` (decimal en (0, 1]) y `s` (decimal > 0)."""
    return [
        f"{nombre}: valor {entrada['value']!r} inválido para la unidad {entrada['unit']}"
        for nombre, entrada in limites.items()
        if not _valor_valido(entrada["unit"], entrada["value"])
    ]


def comprobar_derivadas(limites: Mapping[str, Mapping[str, Any]]) -> list[str]:
    """Cada derivada declara su origen y vale lo que dice su fórmula (p. ej. 4 × ⌈audio / 3⌉)."""
    problemas = [
        f"{nombre}: derived_from sin fórmula conocida en la guardia"
        for nombre, entrada in limites.items()
        if "derived_from" in entrada and nombre not in DERIVADAS
    ]
    for nombre, (origen, formula) in DERIVADAS.items():
        entrada = limites[nombre]
        if entrada.get("derived_from") != origen:
            problemas.append(f"{nombre}: derived_from debe ser {origen}")
        elif entrada["value"] != formula(limites[origen]["value"]):
            problemas.append(
                f"{nombre}: vale {entrada['value']} y su fórmula sobre {origen} da "
                f"{formula(limites[origen]['value'])}"
            )
    return problemas


def comprobar_relaciones(documento: Mapping[str, Any]) -> list[str]:
    """Las relaciones obligatorias están declaradas y todas se cumplen con las cifras del catálogo."""
    declaradas = {tuple(relacion) for relacion in documento["relations"]}
    problemas = [
        f"relación obligatoria sin declarar: {a} {operador} {b}"
        for a, operador, b in RELACIONES_OBLIGATORIAS
        if (a, operador, b) not in declaradas
    ]
    valores = {nombre: entrada["value"] for nombre, entrada in documento["limits"].items()}
    problemas.extend(relaciones_rotas(valores, documento["relations"]))
    return problemas


def comprobar_catalogo(documento: Any) -> list[str]:
    """Forma, tipos, derivadas y relaciones de un catálogo ya cargado; vacía si todo está bien."""
    problemas = comprobar_forma(documento)
    if problemas:
        return problemas
    problemas = comprobar_tipos(documento["limits"])
    if problemas:
        return problemas
    return [*comprobar_derivadas(documento["limits"]), *comprobar_relaciones(documento)]


def comprobar(ruta: Path) -> list[str]:
    """Lee el catálogo en `ruta` y lo comprueba."""
    return comprobar_catalogo(load_file(ruta))
