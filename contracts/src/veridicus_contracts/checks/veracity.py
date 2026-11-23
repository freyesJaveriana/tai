"""Módulo guardia de veracidad (AUTONOMIA-03; BR3.2, BR3.3, BR5.1, BR5.6, BR5.7, BR6.1–BR6.3; §4.8).

Módulo guardia (100 % de ramas). Comprueba, sin escribir nunca:

- el vocabulario prohibido C8 (los 9 términos, las 5 categorías, la forma de coincidencia y de
  exclusión, BR5.1), el aviso de VE-01 (BR5.7), la regla de las aclaraciones neutras (BR5.6) y el
  catálogo de nueve rótulos (BR6.1–BR6.3);
- que ningún nombre de propiedad, de parámetro ni valor de enum de ningún contrato sea una
  categoría prohibida ni tenga un segmento igual a un término de C8 (BR3.3), y que todo enum que
  copia uno de C6 sea igual a él (BR3.2).

La comparación es por igualdad de palabras, sin mayúsculas ni tildes: no es el escáner de texto
libre, que es de U11 (PD-6, P10 = A). Ningún mensaje lleva texto del documento revisado: solo
reglas, rutas de contratos, nombres de campo y cuentas.
"""

import re
import unicodedata
from collections import Counter
from collections.abc import Iterator, Mapping
from collections.abc import Set as AbstractSet
from pathlib import Path
from typing import Any

from veridicus_contracts.loaders import LoadError, load_file

C8 = "integrity/forbidden-vocabulary.v2.yaml"
RUTA_DE_ROTULOS = "ui/result-labels.v2.yaml"
AVISO = "integrity/notice.v1.yaml"
ACLARACION = "integrity/neutral-clarification.v1.yaml"
SALIDA_C6 = "analyzer/v1/salida.schema.json"
C7 = "integrity/review-suggestion.v2.json"
C19 = "cli/report.schema.v2.yaml"
C1 = "api/console.v2.yaml"

# Archivos que la guardia necesita: sin ellos informa y no sigue con lo que de ellos depende.
ARCHIVOS_CLAVE = (C8, RUTA_DE_ROTULOS, AVISO, ACLARACION, SALIDA_C6, C7)
# Contratos que copian el tipo de C6 y deben declararlo (BR3.2); C19 y C1 solo si ya existen.
EXIGEN_TIPO = (C7, C19, C1)

# Directorios de datos de contracts/ que se recorren (los mismos del mapa de la rueda, sin vendor/).
DIRECTORIOS_DE_DATOS = (
    "analyzer", "api", "cli", "errors", "format", "health", "integrity", "metrics", "model_calls",
    "profiles", "queues", "transcript", "ui",
)  # fmt: skip
SUFIJOS = frozenset({".yaml", ".yml", ".json"})
CARPETA_EXCLUIDA = "fixtures"

TERMINOS = (
    "mentiroso", "mentirosa", "miente", "mintió", "falso", "falsa", "verdadero", "verdadera", "engaño",
)  # fmt: skip
CATEGORIAS = ("veracity_score", "is_lying", "truthfulness", "veracidad", "credibilidad")
ESCANEADOS = (
    "salida.hallazgos[].hecho",
    "salida.hallazgos[].observaciones",
    "salida.observaciones_conductor[].tema",
    "reporte consolidado",
    "catálogo de mensajes de la consola",
)
COINCIDENCIA: dict[str, bool | tuple[str, ...]] = {
    "whole_word": True,
    "case_insensitive": True,
    "accent_insensitive": True,
    "excluded_spans": ("cita_literal", "analyst_text", "notice_text"),
    "quote_delimiters": ("«", "»"),
    "quote_fields": ("hecho", "observaciones", "tema"),
    "scan_bare_term_spans": True,
    "excluded_whole_texts": (
        "salida.hallazgos[].cita_a.texto",
        "salida.hallazgos[].cita_b.texto",
        "sugerencia.note",
        "sugerencia.reformulation",
        "aviso.text",
    ),
}
CLAVES_DE_C8 = frozenset(
    {"schema_version", "match", "terms", "categories_forbidden_in_schemas", "scanned"}
)

ROTULOS = {
    "suggestion": "Sugerencia de revisión",
    "finding": "Contradicción en el relato",
    "type_fecha": "Fecha",
    "type_numero": "Número",
    "type_lugar": "Lugar",
    "type_persona": "Persona",
    "type_negacion": "Negación",
    "type_secuencia": "Secuencia",
    "type_otro": "Otro",
}
PREFIJO_DE_TIPO = "type_"
TIPOS_APROBADOS = frozenset(
    clave.removeprefix(PREFIJO_DE_TIPO) for clave in ROTULOS if clave.startswith(PREFIJO_DE_TIPO)
)

FRASE_BASE = (
    "Los hallazgos son sugerencias de revisión sobre la coherencia interna del relato. "
    "No son prueba, no indican falsedad y no deben usarse para decidir sobre la persona"
)
CLAVES_DE_AVISO = frozenset({"schema_version", "version", "text"})
VERSION = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+")

FRASES_DE_ACLARACION = ("antes dijo", "dijo antes", "se contradice", "antes mencionó", "había dicho")
CLAVES_DE_RECHAZO = frozenset({"mentions_contradiction", "phrases", "cites_turn"})
BANDERAS_DE_RECHAZO = ("mentions_contradiction", "cites_turn")

SEPARADOR_DE_SEGMENTOS = re.compile(r"[_\-\s]")
PALABRAS = re.compile(r"[^\W\d_]+")

_FALLO = object()


def normalizar(texto: str) -> str:
    """Minúsculas y sin tildes, para comparar sin distinguir mayúsculas ni tildes."""
    descompuesto = unicodedata.normalize("NFKD", texto.lower())
    return "".join(c for c in descompuesto if not unicodedata.combining(c))


TERMINOS_NORMALIZADOS = frozenset(normalizar(t) for t in TERMINOS)
CATEGORIAS_NORMALIZADAS = frozenset(normalizar(c) for c in CATEGORIAS)


def _lista_de_cadenas(valor: Any) -> bool:
    return isinstance(valor, list) and all(isinstance(v, str) for v in valor)


def _cuentas(esperado: tuple[str, ...], valor: list[str]) -> tuple[int, int]:
    """(faltan, sobran) de una lista frente a la aprobada, contando repeticiones."""
    faltan = sum((Counter(esperado) - Counter(valor)).values())
    sobran = sum((Counter(valor) - Counter(esperado)).values())
    return faltan, sobran


def _igual(valor: Any, esperado: bool | tuple[str, ...]) -> bool:
    if isinstance(esperado, bool):
        return valor is esperado
    return isinstance(valor, list) and valor == list(esperado)


# ---------------------------------------------------------------------------- C8 (BR5.1)


def problemas_de_vocabulario(c8: Any) -> list[str]:
    """BR5.1 y la forma de C8: términos, categorías, coincidencia, exclusiones y alcance."""
    if not isinstance(c8, Mapping):
        return ["C8: no es un objeto"]
    problemas: list[str] = []
    if set(c8) != CLAVES_DE_C8:
        problemas.append("C8: las claves de primer nivel no son las aprobadas")
    if c8.get("schema_version") != "2.0.0":
        problemas.append("C8: schema_version debe ser 2.0.0")
    problemas += _problemas_de_coincidencia(c8.get("match"))
    problemas += _problemas_de_lista(c8.get("terms"), TERMINOS, "terms", "la lista de términos")
    problemas += _problemas_de_lista(
        c8.get("categories_forbidden_in_schemas"),
        CATEGORIAS,
        "categories_forbidden_in_schemas",
        "categories_forbidden_in_schemas",
    )
    if c8.get("scanned") != list(ESCANEADOS):
        problemas.append("C8: scanned no es el aprobado")
    return problemas


def _problemas_de_coincidencia(match: Any) -> list[str]:
    if not isinstance(match, Mapping):
        return ["C8: match no es un objeto"]
    problemas = [
        f"C8: match.{clave} no es el aprobado"
        for clave, esperado in COINCIDENCIA.items()
        if not _igual(match.get(clave), esperado)
    ]
    if set(match) - set(COINCIDENCIA):
        problemas.append("C8: match trae claves no aprobadas")
    return problemas


def _problemas_de_lista(
    valor: Any, aprobada: tuple[str, ...], clave: str, nombre: str
) -> list[str]:
    if not _lista_de_cadenas(valor):
        return [f"BR5.1: {clave} no es una lista de cadenas"]
    faltan, sobran = _cuentas(aprobada, valor)
    if faltan or sobran:
        return [f"BR5.1: {nombre} no es la aprobada (faltan {faltan}, sobran {sobran})"]
    return []


# ---------------------------------------------------------------------------- rótulos (BR6.1–BR6.3)


def problemas_de_rotulos(documento: Any, tipos: AbstractSet[str]) -> list[str]:
    """BR6.1: exactamente los nueve rótulos; BR6.2: uno por tipo de C6; BR6.3: sin términos."""
    if not isinstance(documento, Mapping) or not isinstance(documento.get("labels"), Mapping):
        return ["ui: result-labels no es un objeto con labels"]
    problemas: list[str] = []
    if documento.get("schema_version") != "2.0.0":
        problemas.append("ui: schema_version de result-labels debe ser 2.0.0")
    if set(documento) != {"schema_version", "labels"}:
        problemas.append("ui: result-labels trae claves de primer nivel no aprobadas")
    etiquetas = documento["labels"]
    faltan = [k for k in ROTULOS if k not in etiquetas]
    sobran = [k for k in etiquetas if k not in ROTULOS]
    distintos = [k for k in ROTULOS if k in etiquetas and etiquetas[k] != ROTULOS[k]]
    if faltan or sobran or distintos:
        problemas.append(
            "BR6.1: el catálogo debe tener exactamente los nueve rótulos aprobados "
            f"(faltan {len(faltan)}, sobran {len(sobran)}, distintos {len(distintos)})"
        )
    de_tipo = {k for k in etiquetas if k.startswith(PREFIJO_DE_TIPO)}
    if de_tipo != {f"{PREFIJO_DE_TIPO}{t}" for t in tipos}:
        problemas.append("BR6.2: las filas type_* no corresponden a los tipos de C6")
    for clave, texto in etiquetas.items():
        if isinstance(texto, str) and TERMINOS_NORMALIZADOS & set(PALABRAS.findall(normalizar(texto))):
            problemas.append(f"BR6.3: un rótulo contiene un término prohibido (clave {clave})")
    return problemas


# ---------------------------------------------------------------------------- aviso (BR5.7)


def problemas_de_aviso(documento: Any) -> list[str]:
    """BR5.7: el aviso tiene versión semántica y su texto contiene la frase base de VE-01."""
    if not isinstance(documento, Mapping):
        return ["BR5.7: notice no es un objeto"]
    problemas: list[str] = []
    if documento.get("schema_version") != "1.0.0":
        problemas.append("BR5.7: schema_version del aviso debe ser 1.0.0")
    if set(documento) != CLAVES_DE_AVISO:
        problemas.append("BR5.7: el aviso trae claves no aprobadas")
    version = documento.get("version")
    if not (isinstance(version, str) and VERSION.fullmatch(version)):
        problemas.append("BR5.7: la versión del aviso no es semántica (X.Y.Z)")
    texto = documento.get("text")
    if not (isinstance(texto, str) and FRASE_BASE in " ".join(texto.split())):
        problemas.append("BR5.7: el texto del aviso no contiene la frase base de VE-01")
    return problemas


# ---------------------------------------------------------------------------- aclaración (BR5.6)


def problemas_de_aclaracion(documento: Any) -> list[str]:
    """BR5.6: forma de la regla de las aclaraciones neutras y sus cinco frases."""
    if not isinstance(documento, Mapping):
        return ["BR5.6: neutral-clarification no es un objeto"]
    problemas: list[str] = []
    if documento.get("schema_version") != "1.1.0":
        problemas.append("BR5.6: schema_version de neutral-clarification debe ser 1.1.0")
    if set(documento) != {"schema_version", "reject_if"}:
        problemas.append("BR5.6: neutral-clarification trae claves de primer nivel no aprobadas")
    rechazo = documento.get("reject_if")
    if not isinstance(rechazo, Mapping):
        return [*problemas, "BR5.6: reject_if no es un objeto"]
    if set(rechazo) != CLAVES_DE_RECHAZO:
        problemas.append("BR5.6: reject_if trae claves no aprobadas")
    problemas += [
        f"BR5.6: reject_if.{clave} debe ser verdadero"
        for clave in BANDERAS_DE_RECHAZO
        if rechazo.get(clave) is not True
    ]
    if rechazo.get("phrases") != list(FRASES_DE_ACLARACION):
        problemas.append("BR5.6: las frases de neutral-clarification no son las aprobadas")
    return problemas


# ---------------------------------------------------------------------------- nombres (BR3.3)


def _recorrer(nodo: Any, clave: str | None = None) -> Iterator[tuple[str | None, Any]]:
    """Recorre un documento en profundidad: (clave del padre, valor). Los elementos de una lista
    conservan la clave de la lista (p. ej. `enum`)."""
    yield clave, nodo
    if isinstance(nodo, dict):
        for hija, valor in nodo.items():
            yield from _recorrer(valor, hija)
    elif isinstance(nodo, list):
        for valor in nodo:
            yield from _recorrer(valor, clave)


def nombres_de_un_documento(documento: Any) -> list[str]:
    """Nombres de propiedad, de parámetro y valores de enum de cadena de un contrato."""
    nombres: list[str] = []
    for clave, valor in _recorrer(documento):
        if clave == "properties" and isinstance(valor, dict):
            nombres += list(valor)
        elif clave == "parameters" and isinstance(valor, list):
            nombres += [p["name"] for p in valor if isinstance(p, dict) and "name" in p]
        elif clave == "enum" and isinstance(valor, str):
            nombres.append(valor)
    return nombres


def con_veracidad(nombre: str) -> bool:
    """Igualdad de palabras: el nombre es una categoría prohibida o un segmento es un término de C8."""
    normal = normalizar(nombre)
    if normal in CATEGORIAS_NORMALIZADAS:
        return True
    return any(segmento in TERMINOS_NORMALIZADOS for segmento in SEPARADOR_DE_SEGMENTOS.split(normal))


def problemas_de_nombres(ruta: str, documento: Any) -> list[str]:
    """BR3.3: los nombres de un contrato que declaran veracidad."""
    culpables = list(dict.fromkeys(n for n in nombres_de_un_documento(documento) if con_veracidad(n)))
    if culpables:
        return [f"BR3.3: {ruta}: nombres con vocabulario de veracidad: {culpables}"]
    return []


# ---------------------------------------------------------------------------- enum de C6 (BR3.2)


def enums_de_c6(salida: Any) -> dict[str, frozenset[str]]:
    """Los enum de C6 que otros contratos copian: tipo, código de error, motivo y papel."""
    definiciones = salida["$defs"]
    registro = definiciones["registro"]["properties"]
    return {
        "tipo": frozenset(definiciones["hallazgo"]["properties"]["tipo"]["enum"]),
        "codigo": frozenset(salida["properties"]["error"]["properties"]["codigo"]["enum"]),
        "motivo": frozenset(registro["descartes"]["items"]["properties"]["motivo"]["enum"]),
        "papel": frozenset(registro["llamadas"]["items"]["properties"]["papel"]["enum"]),
    }


def _enums_de_cadenas(documento: Any) -> list[frozenset[str]]:
    return [
        frozenset(valor)
        for clave, valor in _recorrer(documento)
        if clave == "enum" and _lista_de_cadenas(valor)
    ]


def problemas_de_enums(
    ruta: str, documento: Any, c6: Mapping[str, frozenset[str]], *, exige_tipo: bool
) -> list[str]:
    """BR3.2: todo enum que comparte dos o más valores con uno de C6 es igual a él."""
    enums = _enums_de_cadenas(documento)
    problemas = [
        f"BR3.2: {ruta}: un enum difiere del de C6 ({nombre})"
        for enum in enums
        for nombre, valores in c6.items()
        if len(enum & valores) >= 2 and enum != valores
    ]
    if exige_tipo and c6["tipo"] not in enums:
        problemas.append(f"BR3.2: {ruta}: no declara el enum de tipo de C6")
    return problemas


# ---------------------------------------------------------------------------- recorrido


def _leer(ruta: Path) -> Any:
    try:
        return load_file(ruta)
    except (LoadError, OSError):
        return _FALLO


def _contratos(raiz: Path) -> list[str]:
    """Rutas relativas (con `/`) de todos los YAML y JSON de datos de `raiz`, sin fixtures."""
    candidatos = [p for p in raiz.glob("*") if p.is_file()]
    for directorio in DIRECTORIOS_DE_DATOS:
        candidatos += [p for p in (raiz / directorio).rglob("*") if p.is_file()]
    relativas = (p.relative_to(raiz) for p in candidatos if p.suffix in SUFIJOS)
    return sorted(r.as_posix() for r in relativas if CARPETA_EXCLUIDA not in r.parts)


def comprobar(raiz: Path) -> list[str]:
    """Lee los contratos bajo `raiz` (la carpeta `contracts/`) y devuelve los problemas; vacío si todo está."""
    problemas: list[str] = []
    leidos: dict[str, Any] = {}
    for relativa in ARCHIVOS_CLAVE:
        documento = _leer(raiz / relativa)
        if documento is _FALLO:
            problemas.append(f"{relativa}: ausente o ilegible")
        else:
            leidos[relativa] = documento
    c6: dict[str, frozenset[str]] | None = None
    if SALIDA_C6 in leidos:
        try:
            c6 = enums_de_c6(leidos[SALIDA_C6])
        except (KeyError, TypeError):
            problemas.append(f"{SALIDA_C6}: no declara los enum de C6")
    tipos = c6["tipo"] if c6 else TIPOS_APROBADOS
    if C8 in leidos:
        problemas += problemas_de_vocabulario(leidos[C8])
    if RUTA_DE_ROTULOS in leidos:
        problemas += problemas_de_rotulos(leidos[RUTA_DE_ROTULOS], tipos)
    if AVISO in leidos:
        problemas += problemas_de_aviso(leidos[AVISO])
    if ACLARACION in leidos:
        problemas += problemas_de_aclaracion(leidos[ACLARACION])
    for relativa in _contratos(raiz):
        if relativa in leidos:
            documento = leidos[relativa]
        elif relativa in ARCHIVOS_CLAVE:
            continue  # ya se informó que falta o no se lee
        else:
            documento = _leer(raiz / relativa)
        if documento is _FALLO:
            problemas.append(f"{relativa}: ilegible")
            continue
        problemas += problemas_de_nombres(relativa, documento)
        if c6 is not None:
            problemas += problemas_de_enums(relativa, documento, c6, exige_tipo=relativa in EXIGEN_TIPO)
    return problemas
