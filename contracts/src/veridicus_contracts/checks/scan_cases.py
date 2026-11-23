"""Módulo guardia de la forma de los casos de escaneo y del aviso de testimonio (BR5.8, E40; BR3.6).

Módulo guardia (100 % de ramas). U1 no ejecuta el escáner (es de U11, PD-6): comprueba solo la
**forma** de `integrity/scan-cases.v1.yaml`, que haya un caso que espere la coincidencia de cada
término de C8 y otro que rechace cada frase de la aclaración neutra (E40), los escenarios E10–E14 y
E30 y la decisión D-2; y la forma y la coherencia de `integrity/testimony-warning-cases.v1.yaml`
(NFR-U13-10, NFRD-U13-13) con una regla de referencia mínima, para que los ejemplos no se
contradigan. Nunca escribe. Ningún mensaje lleva texto del documento revisado: solo reglas,
posiciones de caso, nombres de campo y los términos y frases aprobados.
"""

import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any, TypeGuard

from veridicus_contracts.checks.veracity import FRASES_DE_ACLARACION, TERMINOS, normalizar
from veridicus_contracts.loaders import LoadError, load_file

CASOS_DE_ESCANEO = "integrity/scan-cases.v1.yaml"
CASOS_DE_TESTIMONIO = "integrity/testimony-warning-cases.v1.yaml"
LIMITES = "limits.v1.yaml"

CAMPOS = ("hecho", "observaciones", "tema")
REGLAS = ("vocabulary", "clarification")
MOTIVOS = ("mentions_contradiction", "phrase", "cites_turn")
# Escenarios de functional-spec y la decisión D-2 que deben tener al menos un caso.
ORIGENES_EXIGIDOS = ("E10", "E11", "E12", "E13", "E14", "E30", "D-2")

CLAVES_DE_CASO = frozenset(
    {"id", "source", "synthetic", "rule", "field", "text", "literal_sources", "expect"}
)
CLAVES_DE_VOCABULARIO = frozenset({"matches", "excluded"})
CLAVES_DE_ACLARACION = frozenset({"valid", "reasons", "phrases"})
IDENTIFICADOR = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")
ORIGEN = re.compile(r"E[0-9]+|BR[0-9]+\.[0-9]+|D-2")
SEPARADOR_DE_DIGITOS = re.compile(r"(?<=[0-9])[ .\-](?=[0-9])")
DIGITOS_LARGOS = re.compile(r"[0-9]{6,}")

CLAVES_DE_TESTIMONIO = frozenset(
    {"schema_version", "synthetic", "testimony_warning_words", "whitespace_code_points", "cases"}
)
CLAVES_DE_CASO_DE_TESTIMONIO = frozenset({"id", "note", "turns", "testimony_warning"})
# Casos que el aviso de testimonio exige y el carácter que su id nombra (None: no nombra ninguno).
REQUERIDOS_DE_TESTIMONIO: dict[str, str | None] = {
    "ocho-palabras": None,
    "siete-palabras": None,
    "dos-turnos": None,
    "al-final-del-turno": None,
    "espacios-distintos": None,
    "u00a0": " ",
    "u3000": "　",
    "ufeff": "﻿",
    "tabulador": "\t",
    "salto-de-linea": "\n",
}
ESPACIOS = tuple(f"U+{c:04X}" for c in range(0x110000) if chr(c).isspace())

_FALLO = object()


def _es_texto(valor: Any) -> TypeGuard[str]:
    return isinstance(valor, str) and valor != ""


def _lista_de_textos(valor: Any) -> TypeGuard[list[str]]:
    return isinstance(valor, list) and all(_es_texto(v) for v in valor)


def _sin_repetir(valor: Any, permitidos: tuple[str, ...]) -> bool:
    return (
        isinstance(valor, list)
        and all(isinstance(v, str) and v in permitidos for v in valor)
        and len(valor) == len(set(valor))
    )


def _digitos_largos(*textos: Any) -> bool:
    return any(
        DIGITOS_LARGOS.search(SEPARADOR_DE_DIGITOS.sub("", t)) for t in textos if isinstance(t, str)
    )


def _en_una_fuente(tramo: str, fuentes: list[str]) -> bool:
    """Regla del piloto: al comparar con el turno solo se normalizan los espacios."""
    buscado = " ".join(tramo.split())
    return any(buscado in " ".join(fuente.split()) for fuente in fuentes)


# ---------------------------------------------------------------------------- casos de escaneo


def problemas_de_casos(
    documento: Any, terminos: tuple[str, ...] = TERMINOS, frases: tuple[str, ...] = FRASES_DE_ACLARACION
) -> list[str]:
    """BR5.8: forma de cada caso, un caso por término y por frase (E40) y los escenarios exigidos."""
    if not isinstance(documento, Mapping):
        return ["BR5.8: scan-cases no es un objeto"]
    problemas: list[str] = []
    if set(documento) != {"schema_version", "cases"}:
        problemas.append("BR5.8: scan-cases trae claves de primer nivel no aprobadas")
    if documento.get("schema_version") != "1.0.0":
        problemas.append("BR5.8: schema_version de scan-cases debe ser 1.0.0")
    lista = documento.get("cases")
    if not isinstance(lista, list):
        return [*problemas, "BR5.8: cases no es una lista"]
    vistos: set[Any] = set()
    for posicion, caso in enumerate(lista):
        problemas += _problemas_de_un_caso(posicion, caso, vistos, terminos, frases)
    validos = [c for c in lista if isinstance(c, Mapping)]
    problemas += _problemas_de_cobertura(validos, terminos, frases)
    return problemas


def _problemas_de_un_caso(
    posicion: int, caso: Any, vistos: set[Any], terminos: tuple[str, ...], frases: tuple[str, ...]
) -> list[str]:
    prefijo = f"BR5.8: casos[{posicion}]: "
    if not isinstance(caso, Mapping):
        return [f"{prefijo}no es un objeto"]
    problemas: list[str] = []
    if set(caso) != CLAVES_DE_CASO:
        problemas.append(f"{prefijo}claves no aprobadas")
    identificador = caso.get("id")
    if not (isinstance(identificador, str) and IDENTIFICADOR.fullmatch(identificador)):
        problemas.append(f"{prefijo}id no es un identificador válido")
    elif identificador in vistos:
        problemas.append(f"{prefijo}id repetido")
    else:
        vistos.add(identificador)
    origen = caso.get("source")
    if not (isinstance(origen, str) and ORIGEN.fullmatch(origen)):
        problemas.append(f"{prefijo}source no es un origen válido")
    if caso.get("synthetic") is not True:
        problemas.append(f"{prefijo}synthetic debe ser true")
    regla = caso.get("rule")
    if regla not in REGLAS:
        problemas.append(f"{prefijo}rule no es una regla aprobada")
    campo = caso.get("field")
    if campo not in CAMPOS:
        problemas.append(f"{prefijo}field no es un campo aprobado")
    elif regla == "clarification" and campo != "tema":
        problemas.append(f"{prefijo}field de una aclaración debe ser tema")
    texto = caso.get("text")
    if not _es_texto(texto):
        problemas.append(f"{prefijo}text vacío o no es texto")
    fuentes = caso.get("literal_sources")
    if not _lista_de_textos(fuentes):
        problemas.append(f"{prefijo}literal_sources no es una lista de textos no vacíos")
    if _digitos_largos(texto, *(fuentes if isinstance(fuentes, list) else [])):
        problemas.append(f"{prefijo}text o literal_sources traen una secuencia de seis o más dígitos")
    problemas += _problemas_de_expect(prefijo, caso, terminos, frases)
    return problemas


def _problemas_de_expect(
    prefijo: str, caso: Mapping[str, Any], terminos: tuple[str, ...], frases: tuple[str, ...]
) -> list[str]:
    esperado = caso.get("expect")
    if not isinstance(esperado, Mapping):
        return [f"{prefijo}expect no es un objeto"]
    regla = caso.get("rule")
    claves = CLAVES_DE_ACLARACION if regla == "clarification" else CLAVES_DE_VOCABULARIO
    if set(esperado) != claves:
        return [f"{prefijo}expect: claves no aprobadas"]
    if regla == "clarification":
        return _problemas_de_aclaracion(prefijo, esperado, frases)
    return _problemas_de_vocabulario(prefijo, caso, esperado, terminos)


def _problemas_de_vocabulario(
    prefijo: str, caso: Mapping[str, Any], esperado: Mapping[str, Any], terminos: tuple[str, ...]
) -> list[str]:
    problemas: list[str] = []
    if not _sin_repetir(esperado["matches"], terminos):
        problemas.append(f"{prefijo}expect.matches no es una lista de términos de C8 sin repetir")
    excluidos = esperado["excluded"]
    texto = caso.get("text")
    fuentes = caso.get("literal_sources")
    if not _lista_de_textos(excluidos) or not all(
        isinstance(texto, str) and f"«{tramo}»" in texto for tramo in excluidos
    ):
        problemas.append(f"{prefijo}expect.excluded no es una lista de tramos citados en text")
        return problemas
    textos = fuentes if _lista_de_textos(fuentes) else []
    if not all(_en_una_fuente(t, textos) for t in excluidos):
        problemas.append(f"{prefijo}expect.excluded trae un tramo que no está en ninguna fuente literal")
    solos = {normalizar(t) for t in terminos}
    if any(normalizar(" ".join(t.split())) in solos for t in excluidos):
        problemas.append(f"{prefijo}expect.excluded trae un tramo que es solo un término (D-2)")
    return problemas


def _problemas_de_aclaracion(
    prefijo: str, esperado: Mapping[str, Any], frases: tuple[str, ...]
) -> list[str]:
    problemas: list[str] = []
    valida = esperado["valid"]
    motivos = esperado["reasons"]
    dichas = esperado["phrases"]
    if not isinstance(valida, bool):
        problemas.append(f"{prefijo}expect.valid debe ser booleano")
    buenos_motivos = _sin_repetir(motivos, MOTIVOS)
    if not buenos_motivos:
        problemas.append(f"{prefijo}expect.reasons no es una lista de motivos aprobados sin repetir")
    buenas_frases = _sin_repetir(dichas, frases)
    if not buenas_frases:
        problemas.append(f"{prefijo}expect.phrases no es una lista de frases aprobadas sin repetir")
    if not (buenos_motivos and buenas_frases and isinstance(valida, bool)):
        return problemas
    if valida and (motivos or dichas):
        problemas.append(f"{prefijo}una aclaración válida no lleva motivos ni frases")
    if not valida and not motivos:
        problemas.append(f"{prefijo}una aclaración inválida lleva al menos un motivo")
    if ("phrase" in motivos) != bool(dichas):
        problemas.append(f"{prefijo}el motivo phrase exige frases y las frases el motivo phrase")
    return problemas


def _problemas_de_cobertura(
    casos: list[Mapping[str, Any]], terminos: tuple[str, ...], frases: tuple[str, ...]
) -> list[str]:
    """E40: un caso por término y por frase; y los escenarios exigidos."""
    problemas: list[str] = []
    coincidencias = {
        t
        for c in casos
        if c.get("rule") == "vocabulary" and isinstance(c.get("expect"), Mapping)
        for t in _lista(c["expect"].get("matches"))
    }
    problemas += [
        f"BR5.8: ningún caso espera la coincidencia del término {t}"
        for t in terminos
        if t not in coincidencias
    ]
    rechazadas = {
        f
        for c in casos
        if c.get("rule") == "clarification" and isinstance(c.get("expect"), Mapping)
        for f in _lista(c["expect"].get("phrases"))
    }
    problemas += [f"BR5.8: ningún caso rechaza la frase {f}" for f in frases if f not in rechazadas]
    origenes = {c.get("source") for c in casos}
    problemas += [f"BR5.8: falta un caso de origen {o}" for o in ORIGENES_EXIGIDOS if o not in origenes]
    return problemas


def _lista(valor: Any) -> list[Any]:
    return valor if isinstance(valor, list) else []


# ---------------------------------------------------------------------------- aviso de testimonio


def _advierte(nota: str, turnos: list[str], palabras: int) -> bool:
    """Regla de referencia de BR3.6: `palabras` o más palabras idénticas y seguidas en un turno."""
    de_la_nota = nota.split()
    for turno in turnos:
        de_el_turno = turno.split()
        for i in range(len(de_la_nota) - palabras + 1):
            ventana = de_la_nota[i : i + palabras]
            if any(
                de_el_turno[j : j + palabras] == ventana
                for j in range(len(de_el_turno) - palabras + 1)
            ):
                return True
    return False


def problemas_de_testimonio(documento: Any, palabras: Any) -> list[str]:
    """BR3.6: forma del archivo compartido, sus espacios, sus casos requeridos y su coherencia.

    `palabras` es `testimony_warning_words` del catálogo C25.
    """
    if not isinstance(documento, Mapping):
        return ["BR3.6: testimony-warning-cases no es un objeto"]
    problemas: list[str] = []
    if set(documento) != CLAVES_DE_TESTIMONIO:
        problemas.append("BR3.6: testimony-warning-cases trae claves de primer nivel no aprobadas")
    if documento.get("schema_version") != "1.0.0":
        problemas.append("BR3.6: schema_version de testimony-warning-cases debe ser 1.0.0")
    if documento.get("synthetic") is not True:
        problemas.append("BR3.6: synthetic debe ser true")
    declaradas = documento.get("testimony_warning_words")
    if isinstance(declaradas, bool) or declaradas != palabras or not isinstance(palabras, int):
        problemas.append("BR3.6: testimony_warning_words no es el del catálogo de límites (C25)")
    if documento.get("whitespace_code_points") != list(ESPACIOS):
        problemas.append("BR3.6: whitespace_code_points no es la lista de str.isspace()")
    lista = documento.get("cases")
    if not isinstance(lista, list):
        return [*problemas, "BR3.6: cases no es una lista"]
    vistos: dict[str, int] = {}
    for posicion, caso in enumerate(lista):
        problemas += _problemas_de_un_caso_de_testimonio(posicion, caso, vistos, palabras)
    problemas += [
        f"BR3.6: falta el caso {identificador}"
        for identificador in REQUERIDOS_DE_TESTIMONIO
        if identificador not in vistos
    ]
    for identificador, caracter in REQUERIDOS_DE_TESTIMONIO.items():
        if caracter is not None and identificador in vistos:
            nota = lista[vistos[identificador]].get("note")
            if not (isinstance(nota, str) and caracter in nota):
                problemas.append(
                    f"BR3.6: casos[{vistos[identificador]}]: la nota no contiene el carácter que su id nombra"
                )
    return problemas


def _problemas_de_un_caso_de_testimonio(
    posicion: int, caso: Any, vistos: dict[str, int], palabras: Any
) -> list[str]:
    prefijo = f"BR3.6: casos[{posicion}]: "
    if not isinstance(caso, Mapping):
        return [f"{prefijo}no es un objeto"]
    problemas: list[str] = []
    if set(caso) != CLAVES_DE_CASO_DE_TESTIMONIO:
        problemas.append(f"{prefijo}claves no aprobadas")
    identificador = caso.get("id")
    if not (isinstance(identificador, str) and IDENTIFICADOR.fullmatch(identificador)):
        problemas.append(f"{prefijo}id no es un identificador válido")
    elif identificador in vistos:
        problemas.append(f"{prefijo}id repetido")
    else:
        vistos[identificador] = posicion
    nota = caso.get("note")
    turnos = caso.get("turns")
    esperado = caso.get("testimony_warning")
    if not _es_texto(nota):
        problemas.append(f"{prefijo}note vacío o no es texto")
    if not (_lista_de_textos(turnos) and turnos):
        problemas.append(f"{prefijo}turns no es una lista no vacía de textos no vacíos")
    if not isinstance(esperado, bool):
        problemas.append(f"{prefijo}testimony_warning debe ser booleano")
    if _digitos_largos(nota, *(turnos if isinstance(turnos, list) else [])):
        problemas.append(f"{prefijo}note o turns traen una secuencia de seis o más dígitos")
    if (
        _es_texto(nota)
        and _lista_de_textos(turnos)
        and turnos
        and isinstance(esperado, bool)
        and isinstance(palabras, int)
        and _advierte(nota, turnos, palabras) is not esperado
    ):
        problemas.append(f"{prefijo}el resultado esperado no concuerda con la regla de BR3.6")
    return problemas


# ---------------------------------------------------------------------------- recorrido


def _leer(ruta: Path) -> Any:
    try:
        return load_file(ruta)
    except (LoadError, OSError):
        return _FALLO


def _palabras_del_catalogo(limites: Any) -> Any:
    """`limits.testimony_warning_words.value` del catálogo C25, o None si no está."""
    secciones = limites.get("limits") if isinstance(limites, Mapping) else None
    limite = secciones.get("testimony_warning_words") if isinstance(secciones, Mapping) else None
    return limite.get("value") if isinstance(limite, Mapping) else None


def comprobar(raiz: Path) -> list[str]:
    """Lee los casos y el catálogo bajo `raiz` (la carpeta `contracts/`) y devuelve los problemas."""
    problemas: list[str] = []
    casos = _leer(raiz / CASOS_DE_ESCANEO)
    testimonio = _leer(raiz / CASOS_DE_TESTIMONIO)
    limites = _leer(raiz / LIMITES)
    for relativa, documento in (
        (CASOS_DE_ESCANEO, casos),
        (CASOS_DE_TESTIMONIO, testimonio),
        (LIMITES, limites),
    ):
        if documento is _FALLO:
            problemas.append(f"{relativa}: ausente o ilegible")
    if casos is not _FALLO:
        problemas += problemas_de_casos(casos)
    if testimonio is not _FALLO:
        problemas += problemas_de_testimonio(testimonio, _palabras_del_catalogo(limites))
    return problemas
