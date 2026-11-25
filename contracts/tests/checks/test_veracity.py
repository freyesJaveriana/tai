"""Guardia de veracidad (BR3.2, BR3.3, BR5.1, BR5.6, BR5.7, BR6.1\u2013BR6.3; security-design §4.8).

Módulo guardia con 100 % de ramas. Cada constante, cada lista cerrada y cada patrón de
`checks/veracity.py` tiene aquí un control positivo (el contrato versionado pasa) y uno negativo
(una copia con un defecto sembrado, en memoria o en `tmp_path`, da exactamente el problema que le
toca). Ningún control toca el contrato versionado. Los mensajes llevan reglas y nombres de campo,
nunca texto del documento revisado: una prueba lo comprueba con una cadena canario.
"""

import copy
import json
import shutil
from pathlib import Path
from typing import Any

import pytest
from helpers import CONTRACTS_ROOT, load_contract

from veridicus_contracts.checks import veracity
from veridicus_contracts.checks.veracity import (
    comprobar,
    con_veracidad,
    enums_de_c6,
    nombres_de_un_documento,
    normalizar,
    problemas_de_aclaracion,
    problemas_de_aviso,
    problemas_de_enums,
    problemas_de_nombres,
    problemas_de_rotulos,
    problemas_de_vocabulario,
)

C8 = "integrity/forbidden-vocabulary.v2.yaml"
ROTULOS = "ui/result-labels.v2.yaml"
AVISO = "integrity/notice.v1.yaml"
ACLARACION = "integrity/neutral-clarification.v1.yaml"
SALIDA = "analyzer/v1/salida.schema.json"
C7 = "integrity/review-suggestion.v2.json"

# E-7: los 9 términos de la primera versión más los de VE-02 con sus flexiones regulares.
# E-8: más las formas verbales comunes de «mentir», «inculpar» y «engañar» (presente, pretérito,
# imperfecto en tercera persona e infinitivo). Las formas de «probar» quedan fuera.
TERMINOS_E8 = [
    "miento", "mientes", "mienten", "mentimos", "mentís", "mentí", "mentiste", "mentisteis", "mintieron",
    "mentir", "mentía", "mentían",
    "inculpas", "inculpamos", "inculpáis", "inculpan", "inculpé", "inculpaste", "inculpasteis", "inculpó",
    "inculparon", "inculpar",
    "engañas", "engaña", "engañamos", "engañáis", "engañan", "engañé", "engañaste", "engañasteis",
    "engañó", "engañaron", "engañar",
]  # fmt: skip
TERMINOS_APROBADOS = [
    "mentiroso", "mentirosa", "miente", "mintió", "falso", "falsa", "verdadero", "verdadera", "engaño",
    "prueba", "pruebas", "probatorio", "probatoria", "probatorios", "probatorias", "pliego", "pliegos",
    "inculpa", "engaños", "falsos", "falsas",
    *TERMINOS_E8,
]  # fmt: skip
CATEGORIAS_APROBADAS = ["veracity_score", "is_lying", "truthfulness", "veracidad", "credibilidad"]
ROTULOS_APROBADOS = {
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
TIPOS = frozenset({"fecha", "numero", "lugar", "persona", "negacion", "secuencia", "otro"})
FRASE_BASE = (
    "Los hallazgos son sugerencias de revisión sobre la coherencia interna del relato. "
    "No son prueba, no indican falsedad y no deben usarse para decidir sobre la persona"
)
FRASES_APROBADAS = ["antes dijo", "dijo antes", "se contradice", "antes mencionó", "había dicho"]
DIRECTORIOS = (
    "analyzer", "api", "cli", "errors", "format", "health", "integrity", "metrics", "model_calls",
    "profiles", "queues", "transcript", "ui",
)  # fmt: skip
CANARIO = "canario-de-testimonio-sintetico"


def copia(relativa: str) -> Any:
    return copy.deepcopy(load_contract(relativa))


def br61(faltan: int, sobran: int, distintos: int) -> str:
    """Mensaje de BR6.1 con sus cuentas."""
    return (
        "BR6.1: el catálogo debe tener exactamente los nueve rótulos aprobados "
        f"(faltan {faltan}, sobran {sobran}, distintos {distintos})"
    )


# ---------------------------------------------------------------- constantes y datos versionados


def test_los_contratos_versionados_pasan_la_guardia() -> None:
    assert comprobar(CONTRACTS_ROOT) == []


def test_las_constantes_son_las_aprobadas() -> None:
    assert veracity.TERMINOS == tuple(TERMINOS_APROBADOS)
    assert veracity.CATEGORIAS == tuple(CATEGORIAS_APROBADAS)
    assert veracity.ROTULOS == ROTULOS_APROBADOS
    assert veracity.FRASE_BASE == FRASE_BASE
    assert veracity.FRASES_DE_ACLARACION == tuple(FRASES_APROBADAS)
    assert veracity.DIRECTORIOS_DE_DATOS == DIRECTORIOS
    assert veracity.C8 == C8
    assert veracity.RUTA_DE_ROTULOS == ROTULOS
    assert veracity.AVISO == AVISO
    assert veracity.ACLARACION == ACLARACION
    assert veracity.SALIDA_C6 == SALIDA
    assert veracity.C7 == C7


def test_c8_versionado_tiene_los_nueve_terminos_y_las_cinco_categorias() -> None:
    c8 = load_contract(C8)
    assert c8["terms"] == TERMINOS_APROBADOS
    assert c8["categories_forbidden_in_schemas"] == CATEGORIAS_APROBADAS
    assert c8["schema_version"] == "2.0.0"


def test_c8_versionado_fija_la_coincidencia_y_las_exclusiones() -> None:
    match = load_contract(C8)["match"]
    assert match["whole_word"] is True
    assert match["case_insensitive"] is True
    assert match["accent_insensitive"] is True
    assert match["scan_bare_term_spans"] is True
    assert match["quote_delimiters"] == ["«", "»"]
    assert match["quote_fields"] == ["hecho", "observaciones", "tema"]
    assert match["excluded_spans"] == ["cita_literal", "analyst_text", "notice_text"]
    assert match["excluded_whole_texts"] == [
        "salida.hallazgos[].cita_a.texto",
        "salida.hallazgos[].cita_b.texto",
        "sugerencia.note",
        "sugerencia.reformulation",
        "aviso.text",
    ]
    assert load_contract(C8)["scanned"] == [
        "salida.hallazgos[].hecho",
        "salida.hallazgos[].observaciones",
        "salida.observaciones_conductor[].tema",
        "reporte consolidado",
        "catálogo de mensajes de la consola",
    ]


def test_los_rotulos_versionados_son_los_nueve_aprobados() -> None:
    documento = load_contract(ROTULOS)
    assert documento["schema_version"] == "2.0.0"
    assert documento["labels"] == ROTULOS_APROBADOS


def test_a1_el_aviso_dice_prueba_y_c8_lo_excluye_entero() -> None:
    """A-1: «prueba» está en el aviso de VE-01; solo el aviso y los textos del analista se excluyen."""
    aviso = load_contract(AVISO)
    palabras = {
        normalizar(p) for p in "".join(c if c.isalpha() else " " for c in aviso["text"]).split()
    }
    assert {"prueba"} == palabras & {normalizar(t) for t in veracity.TERMINOS}
    match = load_contract(C8)["match"]
    assert "aviso.text" in match["excluded_whole_texts"]
    assert "notice_text" in match["excluded_spans"]
    assert "prueba" in veracity.TERMINOS


@pytest.mark.parametrize(
    "nombre", ["prueba", "Pruebas", "esProbatorio", "pliego_de_cargos", "inculpa", "falsos"]
)
def test_los_terminos_de_ve02_fuera_del_aviso_se_marcan_en_los_nombres(nombre: str) -> None:
    assert con_veracidad(nombre)


@pytest.mark.parametrize(
    "nombre",
    ["probar", "pruebe", "probó", "comprueba", "reprueba", "pliegue", "pruebaz", "mintiendo", "inculpando",
     "engañando", "mentira", "mentiras", "incluir"],
)  # fmt: skip
def test_e14_las_formas_que_no_estan_en_la_lista_son_una_limitacion_declarada(nombre: str) -> None:
    """E14: las formas de «probar» (E-8, por falsos positivos), los gerundios y los derivados no entran."""
    assert not con_veracidad(nombre)


@pytest.mark.parametrize("termino", TERMINOS_E8)
def test_e8_las_formas_verbales_se_detectan_en_nombres(termino: str) -> None:
    assert con_veracidad(termino)
    assert con_veracidad(f"es_{termino}")
    assert con_veracidad(termino.upper())


def test_el_aviso_versionado_trae_version_y_frase_base() -> None:
    documento = load_contract(AVISO)
    assert documento["schema_version"] == "1.0.0"
    assert documento["version"] == "1.0.0"
    assert FRASE_BASE in " ".join(documento["text"].split())


def test_la_aclaracion_versionada_trae_las_cinco_frases() -> None:
    documento = load_contract(ACLARACION)
    assert documento["schema_version"] == "1.1.0"
    assert documento["reject_if"]["mentions_contradiction"] is True
    assert documento["reject_if"]["cites_turn"] is True
    assert documento["reject_if"]["phrases"] == FRASES_APROBADAS


# ---------------------------------------------------------------- normalizar y comparación


def test_normalizar_quita_mayusculas_y_tildes() -> None:
    assert normalizar("MINTIÓ") == "mintio"
    assert normalizar("Engaño") == "engano"
    assert normalizar("verdadera") == "verdadera"


@pytest.mark.parametrize("termino", TERMINOS_APROBADOS)
def test_un_nombre_igual_a_un_termino_o_con_un_segmento_igual_es_veracidad(termino: str) -> None:
    assert con_veracidad(termino)
    assert con_veracidad(termino.upper())
    assert con_veracidad(f"valor_{termino}")
    assert con_veracidad(f"{termino}-final")
    assert con_veracidad(f"un {termino}")


@pytest.mark.parametrize("categoria", CATEGORIAS_APROBADAS)
def test_un_nombre_igual_a_una_categoria_prohibida_es_veracidad(categoria: str) -> None:
    assert con_veracidad(categoria)
    assert con_veracidad(categoria.upper())


@pytest.mark.parametrize("nombre", ["falsete", "mintiendo", "verdaderamente", "tipo", "cita_a"])
def test_palabra_completa_no_subcadena(nombre: str) -> None:
    """E14: «falsete» (subcadena) y «mintiendo» (gerundio, no cubierto) no coinciden."""
    assert not con_veracidad(nombre)


@pytest.mark.parametrize("nombre", ["veracity", "score", "credibilidad_extra", "is", "lying"])
def test_un_segmento_de_categoria_no_basta(nombre: str) -> None:
    """La categoría se compara completa; solo los términos de C8 se comparan por segmento."""
    assert not con_veracidad(nombre)


# ---------------------------------------------------------------- C8


def _vocabulario() -> dict[str, Any]:
    return copia(C8)  # type: ignore[no-any-return]


def test_c8_versionado_pasa() -> None:
    assert problemas_de_vocabulario(_vocabulario()) == []


@pytest.mark.parametrize("termino", TERMINOS_APROBADOS)
def test_c8_sin_un_termino_da_br51(termino: str) -> None:
    c8 = _vocabulario()
    c8["terms"].remove(termino)
    assert problemas_de_vocabulario(c8) == [
        "BR5.1: la lista de términos no es la aprobada (faltan 1, sobran 0)"
    ]


def test_c8_con_un_termino_nuevo_o_repetido_da_br51() -> None:
    c8 = _vocabulario()
    c8["terms"].append("mintiendo")
    assert problemas_de_vocabulario(c8) == [
        "BR5.1: la lista de términos no es la aprobada (faltan 0, sobran 1)"
    ]
    c8 = _vocabulario()
    c8["terms"].append("miente")
    assert problemas_de_vocabulario(c8) == [
        "BR5.1: la lista de términos no es la aprobada (faltan 0, sobran 1)"
    ]


def test_c8_con_un_termino_cambiado_cuenta_falta_y_sobra() -> None:
    c8 = _vocabulario()
    c8["terms"][0] = "mentira"
    assert problemas_de_vocabulario(c8) == [
        "BR5.1: la lista de términos no es la aprobada (faltan 1, sobran 1)"
    ]


def test_c8_con_terms_que_no_es_lista_de_cadenas() -> None:
    mensaje = "BR5.1: terms no es una lista de cadenas"
    for valor in ("mentiroso", ["mentiroso", 3], None, {"a": "b"}):
        c8 = _vocabulario()
        c8["terms"] = valor
        assert problemas_de_vocabulario(c8) == [mensaje], valor


@pytest.mark.parametrize("categoria", CATEGORIAS_APROBADAS)
def test_c8_sin_una_categoria_da_br51(categoria: str) -> None:
    c8 = _vocabulario()
    c8["categories_forbidden_in_schemas"].remove(categoria)
    assert problemas_de_vocabulario(c8) == [
        "BR5.1: categories_forbidden_in_schemas no es la aprobada (faltan 1, sobran 0)"
    ]


def test_c8_con_una_categoria_de_mas_o_que_no_es_lista() -> None:
    c8 = _vocabulario()
    c8["categories_forbidden_in_schemas"].append("score")
    assert problemas_de_vocabulario(c8) == [
        "BR5.1: categories_forbidden_in_schemas no es la aprobada (faltan 0, sobran 1)"
    ]
    c8 = _vocabulario()
    c8["categories_forbidden_in_schemas"] = "veracidad"
    assert problemas_de_vocabulario(c8) == [
        "BR5.1: categories_forbidden_in_schemas no es una lista de cadenas"
    ]


@pytest.mark.parametrize(
    "clave", ["whole_word", "case_insensitive", "accent_insensitive", "scan_bare_term_spans"]
)
def test_c8_con_una_bandera_de_coincidencia_distinta(clave: str) -> None:
    for valor in (False, 1, "true", None):
        c8 = _vocabulario()
        c8["match"][clave] = valor
        assert problemas_de_vocabulario(c8) == [f"C8: match.{clave} no es el aprobado"], valor


@pytest.mark.parametrize(
    ("clave", "valor"),
    [
        ("quote_delimiters", ["«"]),
        ("quote_delimiters", ["»", "«"]),
        ("quote_delimiters", ['"', '"']),
        ("quote_fields", ["hecho", "observaciones"]),
        ("quote_fields", ["hecho", "observaciones", "tema", "cita_a"]),
        ("excluded_spans", ["cita_literal", "analyst_text"]),
        ("excluded_spans", ["cita_literal", "analyst_text", "notice_text", "reporte"]),
        ("excluded_whole_texts", []),
        ("excluded_whole_texts", "aviso.text"),
    ],
)
def test_c8_con_una_lista_de_coincidencia_distinta(clave: str, valor: Any) -> None:
    c8 = _vocabulario()
    c8["match"][clave] = valor
    assert problemas_de_vocabulario(c8) == [f"C8: match.{clave} no es el aprobado"]


def test_c8_con_match_ausente_o_con_claves_de_mas() -> None:
    c8 = _vocabulario()
    c8["match"]["whole_word_extra"] = True
    assert problemas_de_vocabulario(c8) == ["C8: match trae claves no aprobadas"]
    c8 = _vocabulario()
    del c8["match"]["quote_fields"]
    assert problemas_de_vocabulario(c8) == ["C8: match.quote_fields no es el aprobado"]
    c8 = _vocabulario()
    c8["match"] = ["whole_word"]
    assert problemas_de_vocabulario(c8) == ["C8: match no es un objeto"]


def test_c8_con_scanned_o_version_o_claves_distintas() -> None:
    c8 = _vocabulario()
    c8["scanned"].pop()
    assert problemas_de_vocabulario(c8) == ["C8: scanned no es el aprobado"]
    c8 = _vocabulario()
    c8["schema_version"] = "1.0.0"
    assert problemas_de_vocabulario(c8) == ["C8: schema_version debe ser 2.0.0"]
    c8 = _vocabulario()
    c8["extra"] = 1
    assert problemas_de_vocabulario(c8) == ["C8: las claves de primer nivel no son las aprobadas"]
    c8 = _vocabulario()
    del c8["scanned"]
    assert problemas_de_vocabulario(c8) == [
        "C8: las claves de primer nivel no son las aprobadas",
        "C8: scanned no es el aprobado",
    ]


def test_c8_que_no_es_un_objeto() -> None:
    assert problemas_de_vocabulario(["mentiroso"]) == ["C8: no es un objeto"]


# ---------------------------------------------------------------- rótulos


def _rotulos() -> dict[str, Any]:
    return copia(ROTULOS)  # type: ignore[no-any-return]


def test_rotulos_versionados_pasan() -> None:
    assert problemas_de_rotulos(_rotulos(), TIPOS) == []


def test_e17_un_decimo_rotulo_se_detecta() -> None:
    documento = _rotulos()
    documento["labels"]["decimo"] = "Décimo rótulo"
    assert problemas_de_rotulos(documento, TIPOS) == [br61(0, 1, 0)]


@pytest.mark.parametrize("clave", list(ROTULOS_APROBADOS))
def test_rotulos_sin_uno_de_los_nueve(clave: str) -> None:
    documento = _rotulos()
    del documento["labels"][clave]
    problemas = problemas_de_rotulos(documento, TIPOS)
    esperado = [br61(1, 0, 0)]
    if clave.startswith("type_"):
        esperado.append("BR6.2: las filas type_* no corresponden a los tipos de C6")
    assert problemas == esperado


@pytest.mark.parametrize("clave", list(ROTULOS_APROBADOS))
def test_rotulos_con_un_texto_cambiado(clave: str) -> None:
    for texto in ("Otra cosa", ROTULOS_APROBADOS[clave].lower(), 7):
        documento = _rotulos()
        documento["labels"][clave] = texto
        assert problemas_de_rotulos(documento, TIPOS) == [br61(0, 0, 1)], (clave, texto)


def test_rotulos_con_dos_textos_intercambiados_no_pasan() -> None:
    documento = _rotulos()
    labels = documento["labels"]
    labels["type_fecha"], labels["type_lugar"] = labels["type_lugar"], labels["type_fecha"]
    assert problemas_de_rotulos(documento, TIPOS) == [br61(0, 0, 2)]


def test_rotulos_con_una_fila_type_que_no_es_de_c6() -> None:
    documento = _rotulos()
    documento["labels"]["type_otro"] = "Otro"
    problemas = problemas_de_rotulos(documento, TIPOS - {"otro"})
    assert problemas == ["BR6.2: las filas type_* no corresponden a los tipos de C6"]
    problemas = problemas_de_rotulos(documento, TIPOS | {"fuente"})
    assert problemas == ["BR6.2: las filas type_* no corresponden a los tipos de C6"]


def test_un_rotulo_con_un_termino_prohibido_da_br63() -> None:
    documento = _rotulos()
    documento["labels"]["type_otro"] = "Es FALSO"
    assert problemas_de_rotulos(documento, TIPOS) == [
        br61(0, 0, 1),
        "BR6.3: un rótulo contiene un término prohibido (clave type_otro)",
    ]
    documento["labels"]["type_otro"] = "Engaño"
    assert problemas_de_rotulos(documento, TIPOS)[-1] == (
        "BR6.3: un rótulo contiene un término prohibido (clave type_otro)"
    )
    documento["labels"]["type_otro"] = "Falsete"
    assert all(not p.startswith("BR6.3") for p in problemas_de_rotulos(documento, TIPOS))


def test_rotulos_con_forma_incorrecta() -> None:
    assert problemas_de_rotulos([], TIPOS) == ["ui: result-labels no es un objeto con labels"]
    assert problemas_de_rotulos({"labels": []}, TIPOS) == [
        "ui: result-labels no es un objeto con labels"
    ]
    assert problemas_de_rotulos({"schema_version": "2.0.0"}, TIPOS) == [
        "ui: result-labels no es un objeto con labels"
    ]
    documento = _rotulos()
    documento["schema_version"] = "1.0.0"
    assert problemas_de_rotulos(documento, TIPOS) == [
        "ui: schema_version de result-labels debe ser 2.0.0"
    ]
    documento = _rotulos()
    documento["extra"] = {}
    assert problemas_de_rotulos(documento, TIPOS) == [
        "ui: result-labels trae claves de primer nivel no aprobadas"
    ]


# ---------------------------------------------------------------- aviso


def _aviso() -> dict[str, Any]:
    return copia(AVISO)  # type: ignore[no-any-return]


def test_aviso_versionado_pasa() -> None:
    assert problemas_de_aviso(_aviso()) == []


@pytest.mark.parametrize("version", ["1.0", "1.0.0.0", "v1.0.0", "1.a.0", "", "1.0.0 ", 1])
def test_aviso_con_version_que_no_es_semantica(version: Any) -> None:
    documento = _aviso()
    documento["version"] = version
    assert problemas_de_aviso(documento) == ["BR5.7: la versión del aviso no es semántica (X.Y.Z)"]


@pytest.mark.parametrize("version", ["0.0.1", "1.10.200", "12.0.0"])
def test_aviso_acepta_cualquier_version_semantica(version: str) -> None:
    documento = _aviso()
    documento["version"] = version
    assert problemas_de_aviso(documento) == []


def test_aviso_sin_la_frase_base() -> None:
    mensaje = "BR5.7: el texto del aviso no contiene la frase base de VE-01"
    for texto in (
        "Texto distinto",
        FRASE_BASE[:-1],
        FRASE_BASE.replace("No son prueba", "Son prueba"),
        5,
    ):
        documento = _aviso()
        documento["text"] = texto
        assert problemas_de_aviso(documento) == [mensaje], texto


def test_aviso_mas_estricto_conserva_el_anterior_completo() -> None:
    documento = _aviso()
    documento["text"] = f"Antes. {FRASE_BASE}.  Después\ncon más."
    assert problemas_de_aviso(documento) == []
    documento["text"] = FRASE_BASE.replace("relato. No", "relato.\n  No")
    assert problemas_de_aviso(documento) == []


def test_aviso_con_forma_incorrecta() -> None:
    assert problemas_de_aviso("texto") == ["BR5.7: notice no es un objeto"]
    documento = _aviso()
    documento["schema_version"] = "2.0.0"
    assert problemas_de_aviso(documento) == ["BR5.7: schema_version del aviso debe ser 1.0.0"]
    documento = _aviso()
    documento["extra"] = 1
    assert problemas_de_aviso(documento) == ["BR5.7: el aviso trae claves no aprobadas"]
    documento = _aviso()
    del documento["version"]
    assert problemas_de_aviso(documento) == [
        "BR5.7: el aviso trae claves no aprobadas",
        "BR5.7: la versión del aviso no es semántica (X.Y.Z)",
    ]


# ---------------------------------------------------------------- aclaración neutra


def _aclaracion() -> dict[str, Any]:
    return copia(ACLARACION)  # type: ignore[no-any-return]


def test_aclaracion_versionada_pasa() -> None:
    assert problemas_de_aclaracion(_aclaracion()) == []


def test_aclaracion_con_frases_distintas() -> None:
    mensaje = "BR5.6: las frases de neutral-clarification no son las aprobadas"
    documento = _aclaracion()
    documento["reject_if"]["phrases"].pop()
    assert problemas_de_aclaracion(documento) == [mensaje]
    documento = _aclaracion()
    documento["reject_if"]["phrases"].append("más")
    assert problemas_de_aclaracion(documento) == [mensaje]
    documento = _aclaracion()
    documento["reject_if"]["phrases"][0] = "otra"
    assert problemas_de_aclaracion(documento) == [mensaje]
    documento = _aclaracion()
    documento["reject_if"]["phrases"] = "antes dijo"
    assert problemas_de_aclaracion(documento) == [mensaje]


@pytest.mark.parametrize("clave", ["mentions_contradiction", "cites_turn"])
def test_aclaracion_con_una_bandera_apagada(clave: str) -> None:
    for valor in (False, 1, None):
        documento = _aclaracion()
        documento["reject_if"][clave] = valor
        assert problemas_de_aclaracion(documento) == [
            f"BR5.6: reject_if.{clave} debe ser verdadero"
        ], valor


def test_aclaracion_con_forma_incorrecta() -> None:
    assert problemas_de_aclaracion([]) == ["BR5.6: neutral-clarification no es un objeto"]
    documento = _aclaracion()
    documento["schema_version"] = "1.0.0"
    assert problemas_de_aclaracion(documento) == [
        "BR5.6: schema_version de neutral-clarification debe ser 1.1.0"
    ]
    documento = _aclaracion()
    documento["extra"] = 1
    assert problemas_de_aclaracion(documento) == [
        "BR5.6: neutral-clarification trae claves de primer nivel no aprobadas"
    ]
    documento = _aclaracion()
    documento["reject_if"]["extra"] = True
    assert problemas_de_aclaracion(documento) == ["BR5.6: reject_if trae claves no aprobadas"]
    documento = _aclaracion()
    documento["reject_if"] = ["mentions_contradiction"]
    assert problemas_de_aclaracion(documento) == ["BR5.6: reject_if no es un objeto"]


# ---------------------------------------------------------------- nombres (BR3.3)


@pytest.mark.parametrize(
    "nombre",
    ["isLying", "veracityScore", "esFalso", "esVerdadero", "MintioEnLaHora", "falsoPositivo",
     "ESFalso", "EngañoFinal", "es_Falso", "truthfulness", "Credibilidad", "isTruthfulness_x_Miente"],
)  # fmt: skip
def test_camel_y_pascal_case_se_parten_en_las_fronteras(nombre: str) -> None:
    """F-01: BR3.3 parte también en las fronteras de minúscula a mayúscula."""
    assert con_veracidad(nombre)
    assert problemas_de_nombres("x.yaml", {"properties": {nombre: {}}}) == [
        f"BR3.3: x.yaml: nombres con vocabulario de veracidad: ['{nombre}']"
    ]


@pytest.mark.parametrize(
    "nombre",
    ["es_falso2", "falso2", "es2falso", "FALSO2", "es.falso", "falso2x", "Falso9Positivo", "v1.falso",
     "esＦａｌｓｏ", "ＦＡＬＳＯ2", "es_ｆａｌｓｏ", "is_lying2", "veracity2Score"],
)  # fmt: skip
def test_digitos_y_puntos_tambien_son_fronteras_y_el_ancho_completo_se_normaliza(
    nombre: str,
) -> None:
    """R2-01: letra y dígito (en los dos sentidos), el punto y NFKC antes de comparar."""
    assert con_veracidad(nombre)


def _textos(nodo: Any) -> list[str]:
    """Todas las cadenas de valor (no las claves) de un documento."""
    if isinstance(nodo, str):
        return [nodo]
    if isinstance(nodo, dict):
        return [t for valor in nodo.values() for t in _textos(valor)]
    if isinstance(nodo, list):
        return [t for valor in nodo for t in _textos(valor)]
    return []


# Archivos que traen los términos a propósito: la lista, sus casos y el texto del aviso (excluido, A-1).
CON_TERMINOS_A_PROPOSITO = {C8, "integrity/scan-cases.v1.yaml", AVISO}


def test_e8_ningun_termino_coincide_con_un_texto_fijo_de_los_contratos() -> None:
    """Un término de C8 solo aparece, como palabra completa, donde se declara o se ejercita."""
    terminos = {normalizar(t) for t in veracity.TERMINOS}
    coincidencias = []
    for relativa in veracity._contratos(CONTRACTS_ROOT):
        if relativa in CON_TERMINOS_A_PROPOSITO:
            continue
        for texto in _textos(load_contract(relativa)):
            palabras = set(veracity.PALABRAS.findall(normalizar(texto)))
            coincidencias += [(relativa, p) for p in sorted(palabras & terminos)]
    assert coincidencias == []


def test_el_recorrido_de_textos_fijos_ve_un_termino_sembrado() -> None:
    assert _textos({"a": ["x", {"b": "Un texto con MIENTEN dentro", "c": 3}], "d": None}) == [
        "x",
        "Un texto con MIENTEN dentro",
    ]
    palabras = set(veracity.PALABRAS.findall(normalizar("Un texto con MIENTEN dentro")))
    assert palabras & {normalizar(t) for t in veracity.TERMINOS} == {"mienten"}


def test_nfkc_no_rompe_las_tildes_descompuestas_ni_los_nombres_limpios() -> None:
    """NFKC compone «ñ» antes de comparar: la forma descompuesta y la compuesta dan lo mismo."""
    assert con_veracidad("EngañoFinal")
    assert con_veracidad("Engaño")
    assert con_veracidad("mintió")  # «mintió» descompuesto
    assert not con_veracidad("séptimo")
    assert not con_veracidad("ñandú")
    assert not con_veracidad("ﬁnal")  # la ligadura «ﬁ» se descompone en «fi»


@pytest.mark.parametrize(
    "nombre", ["falsete2", "v2", "tipo2", "x1y", "es.falsete", "ｔｉｐｏ", "mintiendo2", "2025"]
)
def test_digitos_y_puntos_no_marcan_lo_limpio(nombre: str) -> None:
    assert not con_veracidad(nombre)


@pytest.mark.parametrize("nombre", ["HTTPFALSO", "EsEngaÑo", "ESFALSO", "fAlso"])
def test_limitacion_declarada_mayusculas_a_mitad_de_palabra_no_se_parten(nombre: str) -> None:
    """Limitación declarada (R2-01): una mayúscula seguida de otra mayúscula, o a mitad de una
    palabra, no es frontera; el nombre queda como una sola palabra y no coincide con un término."""
    assert not con_veracidad(nombre)


@pytest.mark.parametrize(
    "nombre",
    [
        "filter[falso]", "falso[]", "es/falso", "es:falso", "es+falso", "es(falso)", "es@falso",
        "es,falso", "es;falso", "es|falso", "es\\falso", "es#falso", "es=falso", "es?falso", "es*falso",
        "es\u200bfalso",  # espacio de ancho cero
        "es\u00adfalso",  # guion blando
        "es\u00b7falso",  # punto medio
        "es\u2011falso",  # guion sin salto
        "es\u2010falso", "es\u2013falso", "es\u2014falso", "es\u2212falso",  # otros guiones y el menos
        "es\u00a0falso", "es\u3000falso", "es\ufefffalso",
        "deep[Object][falso]", "a.b[0].es_falso",
    ],
)  # fmt: skip
def test_r3_01_todo_lo_que_no_es_letra_ni_digito_es_frontera(nombre: str) -> None:
    assert con_veracidad(nombre)


@pytest.mark.parametrize(
    "nombre",
    [
        "filter[falsete]",
        "es/falsete",
        "es\u200bfalsete",
        "es\u00b7tipo",
        "es(tipo)",
        "a/b",
        "[]",
        "\u200b",
        "",
    ],
)
def test_r3_01_los_signos_no_marcan_lo_limpio(nombre: str) -> None:
    assert not con_veracidad(nombre)


@pytest.mark.parametrize(
    "nombre",
    [
        "f\u0430lso",  # «\u0430» cirílica en lugar de la «a» latina (homoglifo)
        "\u0101Falso",  # «\u0101» (fuera de Latin-1) pegada a una mayúscula: no es frontera
        "falso\u0662",  # dígito arábigo-índico: ni dígito ASCII ni frontera de letra a dígito
        "\u216bfalso",  # «\u216b»: NFKC lo pasa a «XII» y el nombre sigue siendo una sola palabra
    ],
)
def test_r3_04_limitaciones_declaradas_de_alfabeto_y_numeros(nombre: str) -> None:
    """Limitaciones declaradas (R3-04): homoglifos, letras fuera de Latin-1 antes de una mayúscula,
    dígitos que no son ASCII y números romanos. Ninguna cambia la regla."""
    assert not con_veracidad(nombre)


@pytest.mark.parametrize("nombre", ["menti_x", "x.engane", "es_inculpo", "mentia", "mentian"])
def test_r3_02_limitacion_declarada_la_comparacion_sin_tildes_coincide_con_segmentos(
    nombre: str,
) -> None:
    """Limitación declarada (R3-02): sin tildes, «menti» (de «mentí»), «engane» (de «engañé») e
    «inculpo» (de «inculpó») coinciden aunque no sean un uso prohibido."""
    assert con_veracidad(nombre)


@pytest.mark.parametrize(
    "nombre",
    [
        "Falsete",
        "esFalsete",
        "tipoDeCita",
        "credibilidadExtra",
        "isTruth",
        "mienteentodo",
        "Mintiendo",
    ],
)
def test_camel_case_limpio_no_se_marca(nombre: str) -> None:
    assert not con_veracidad(nombre)


def test_parameters_como_mapa_de_components_se_recoge() -> None:
    """F-02: `components.parameters` es un mapa nombre -> parámetro, no una lista."""
    documento = {
        "components": {
            "parameters": {"P": {"name": "es_falso", "in": "query"}, "Q": {"in": "query"}}
        }
    }
    assert nombres_de_un_documento(documento) == ["es_falso"]
    assert problemas_de_nombres("api/x.yaml", documento) == [
        "BR3.3: api/x.yaml: nombres con vocabulario de veracidad: ['es_falso']"
    ]
    documento = {"components": {"parameters": {"P": {"name": 7}, "Q": "texto"}}}
    assert nombres_de_un_documento(documento) == []


def test_los_nombres_de_defs_y_de_components_schemas_se_comparan() -> None:
    assert problemas_de_nombres("x.yaml", {"$defs": {"EsFalso": {}}}) == [
        "BR3.3: x.yaml: nombres con vocabulario de veracidad: ['EsFalso']"
    ]
    assert problemas_de_nombres("x.yaml", {"components": {"schemas": {"is_lying": {}}}}) == [
        "BR3.3: x.yaml: nombres con vocabulario de veracidad: ['is_lying']"
    ]
    assert (
        problemas_de_nombres(
            "x.yaml", {"$defs": {"hallazgo": {}}, "components": {"schemas": {"Run": {}}}}
        )
        == []
    )
    assert nombres_de_un_documento({"$defs": ["EsFalso"], "otro": {"schemas": 3}}) == []


def test_nombres_de_un_documento_recoge_propiedades_parametros_y_enum() -> None:
    documento = {
        "properties": {"a": {"properties": {"b": {}}}, "c": {"enum": ["x", "y"]}},
        "paths": {"/r": {"get": {"parameters": [{"name": "p"}, {"in": "query"}, "texto"]}}},
        "enum": "suelto",
        "ruido": {"properties": ["no es un mapa"], "parameters": {"name": "ignorado"}},
    }
    assert sorted(nombres_de_un_documento(documento)) == ["a", "b", "c", "p", "suelto", "x", "y"]


@pytest.mark.parametrize(
    "documento",
    [
        {"properties": {"is_lying": {}}},
        {"properties": {"valor_falso": {}}},
        {"properties": {"x": {"properties": {"Engaño": {}}}}},
        {"properties": {"x": {"enum": ["ok", "mentiroso"]}}},
        {"paths": {"/r": {"get": {"parameters": [{"name": "verdadera"}]}}}},
        {"properties": {"VERACIDAD": {}}},
    ],
)
def test_un_nombre_de_veracidad_se_detecta(documento: Any) -> None:
    problemas = problemas_de_nombres("x.yaml", documento)
    assert len(problemas) == 1
    assert problemas[0].startswith("BR3.3: x.yaml: nombres con vocabulario de veracidad: [")


def test_los_nombres_limpios_pasan() -> None:
    documento = {
        "properties": {"falsete": {}, "mintiendo": {}, "tipo": {"enum": ["fecha", "otro"]}}
    }
    assert problemas_de_nombres("x.yaml", documento) == []
    assert problemas_de_nombres("x.yaml", {}) == []


def test_el_mensaje_de_nombres_nombra_el_campo_y_la_ruta() -> None:
    documento = {"properties": {"ok": {}, "is_lying": {}, "is_truthfulness": {}}}
    assert problemas_de_nombres("api/x.yaml", documento) == [
        "BR3.3: api/x.yaml: nombres con vocabulario de veracidad: ['is_lying']"
    ]


# ---------------------------------------------------------------- enum de C6 (BR3.2)


def test_enums_de_c6_son_los_aprobados() -> None:
    enums = enums_de_c6(load_contract(SALIDA))
    assert enums["tipo"] == TIPOS
    assert enums["codigo"] == {
        "salida_invalida", "bloqueo_contenido", "tiempo_agotado", "proveedor",
        "anonimizador_no_disponible", "incidente_anonimizacion",
    }  # fmt: skip
    assert enums["motivo"] == {
        "cita_no_verificada", "cita_en_otro_turno", "marca_alterada", "campo_faltante",
        "rechazado_verificador", "rechazado_permutacion", "fuera_de_tramo", "vocabulario_prohibido",
    }  # fmt: skip
    assert enums["papel"] == {"juez", "verificador", "verificador_permutado"}
    assert enums["estado"] == {"ok", "error"}
    assert set(enums) == {"tipo", "codigo", "motivo", "papel", "estado"}


def test_las_rutas_declaradas_son_las_de_contract_summary() -> None:
    assert veracity.RUTAS_DE_ENUM == {
        C7: (("tipo", "tipo", False),),
        "cli/report.schema.v2.yaml": (
            ("status", "estado", False),
            ("error_code", "codigo", False),
            ("discards", "motivo", True),
            ("fact_type", "tipo", False),
        ),
        "api/console.v2.yaml": (("papel", "papel", False),),
    }


def test_c7_versionado_declara_el_enum_de_tipo() -> None:
    c6 = enums_de_c6(load_contract(SALIDA))
    assert problemas_de_enums(C7, load_contract(C7), c6) == []


def test_un_documento_sin_rutas_declaradas_no_se_compara() -> None:
    c6 = enums_de_c6(load_contract(SALIDA))
    documento = {"properties": {"tipo": {"enum": ["fecha"]}, "papel": {"enum": ["x"]}}}
    assert problemas_de_enums("queues/otro.json", documento, c6) == []


def test_un_enum_de_valores_que_no_son_cadenas_no_cuenta_como_declarado() -> None:
    c6 = enums_de_c6(load_contract(SALIDA))
    documento = {"properties": {"tipo": {"enum": ["fecha", 3]}}}
    assert problemas_de_enums(C7, documento, c6) == [
        f"BR3.2: {C7}: no declara el enum de tipo de C6"
    ]
    documento = {"properties": {"tipo": "texto"}}
    assert problemas_de_enums(C7, documento, c6) == [
        f"BR3.2: {C7}: no declara el enum de tipo de C6"
    ]
    documento = {"properties": ["tipo"]}
    assert problemas_de_enums(C7, documento, c6) == [
        f"BR3.2: {C7}: no declara el enum de tipo de C6"
    ]


PREFIJO_C6 = "/veridicus/contracts/analyzer/v1/salida#"
RUTAS_EN_C6 = {
    "estado": "/properties/estado",
    "tipo": "/$defs/hallazgo/properties/tipo",
    "codigo": "/properties/error/properties/codigo",
    "motivo": "/$defs/registro/properties/descartes/items/properties/motivo",
    "papel": "/$defs/registro/properties/llamadas/items/properties/papel",
}


def _apuntado(documento: Any, puntero: str) -> Any:
    nodo = documento
    for parte in puntero.removeprefix("/").split("/"):
        nodo = nodo[parte]
    return nodo


def test_las_rutas_de_c6_apuntan_a_los_enum_de_c6() -> None:
    """R2-04: cada ruta canónica resuelve de verdad en la copia de C6 al enum que se compara."""
    assert veracity.PREFIJO_DE_C6 == PREFIJO_C6
    assert veracity.RUTAS_EN_C6 == RUTAS_EN_C6
    salida = load_contract(SALIDA)
    c6 = enums_de_c6(salida)
    for nombre, ruta in RUTAS_EN_C6.items():
        assert frozenset(_apuntado(salida, ruta)["enum"]) == c6[nombre], nombre


def _ref(nombre: str) -> dict[str, str]:
    return {"$ref": PREFIJO_C6 + RUTAS_EN_C6[nombre]}


def test_un_ref_exacto_a_la_ruta_de_c6_cuenta_como_copia_correcta() -> None:
    c6 = enums_de_c6(load_contract(SALIDA))
    documento = {"properties": {"tipo": _ref("tipo")}}
    assert problemas_de_enums(C7, documento, c6) == []


def test_un_ref_a_otra_ruta_es_una_copia_desviada() -> None:
    c6 = enums_de_c6(load_contract(SALIDA))
    mensaje = [f"BR3.2: {C7}: el enum de tipo difiere del de C6 (tipo)"]
    for ref in (
        {"$ref": PREFIJO_C6 + RUTAS_EN_C6["estado"]},
        {"$ref": PREFIJO_C6 + "/$defs/hallazgo"},
        {"$ref": PREFIJO_C6 + RUTAS_EN_C6["tipo"] + "/enum"},
        {"$ref": "#/$defs/tipo"},
        {"$ref": "/veridicus/contracts/analyzer/v1/entrada#/$defs/hallazgo/properties/tipo"},
        {"$ref": RUTAS_EN_C6["tipo"]},
    ):
        documento = {"properties": {"tipo": ref}}
        assert problemas_de_enums(C7, documento, c6) == mensaje, ref


def test_un_ref_que_no_es_texto_no_cuenta_como_declarado() -> None:
    c6 = enums_de_c6(load_contract(SALIDA))
    documento = {"properties": {"tipo": {"$ref": 3}}}
    assert problemas_de_enums(C7, documento, c6) == [
        f"BR3.2: {C7}: no declara el enum de tipo de C6"
    ]


def test_c19_y_c1_con_ref_a_las_rutas_de_c6_pasan(tmp_path: Path) -> None:
    c19 = {
        "properties": {
            "runs": {
                "items": {
                    "properties": {
                        "status": _ref("estado"),
                        "error_code": _ref("codigo"),
                        "discards": {"propertyNames": _ref("motivo")},
                    }
                }
            },
            "bias_table": {"items": {"properties": {"fact_type": _ref("tipo")}}},
        }
    }
    c1 = {"components": {"schemas": {"ModelCall": {"properties": {"papel": _ref("papel")}}}}}
    raiz = _arbol(tmp_path)
    _con_c19_y_c1(raiz, c19, c1)
    assert comprobar(raiz) == []
    c1["components"]["schemas"]["ModelCall"]["properties"]["papel"] = _ref("tipo")
    _escribir(raiz, C1, c1)
    assert comprobar(raiz) == [f"BR3.2: {C1}: el enum de papel difiere del de C6 (papel)"]


def test_cada_copia_del_campo_se_compara_y_basta_una_declarada() -> None:
    c6 = enums_de_c6(load_contract(SALIDA))
    buena = {"enum": sorted(TIPOS)}
    mala = {"enum": ["fecha", "fuente"]}
    documento = {"a": {"properties": {"tipo": buena}}, "b": {"properties": {"tipo": mala}}}
    assert problemas_de_enums(C7, documento, c6) == [
        f"BR3.2: {C7}: el enum de tipo difiere del de C6 (tipo)"
    ]
    documento = {
        "a": {"properties": {"tipo": buena}},
        "b": {"properties": {"tipo": {"type": "string"}}},
    }
    assert problemas_de_enums(C7, documento, c6) == []


# ---------------------------------------------------------------- comprobar sobre un árbol


def _arbol(destino: Path) -> Path:
    """Copia los directorios de datos (sin fixtures) a `destino` y devuelve la raíz."""
    for directorio in DIRECTORIOS:
        shutil.copytree(
            CONTRACTS_ROOT / directorio,
            destino / directorio,
            ignore=shutil.ignore_patterns("fixtures"),
        )
    shutil.copy(CONTRACTS_ROOT / "limits.v1.yaml", destino / "limits.v1.yaml")
    return destino


def _escribir(raiz: Path, relativa: str, documento: Any) -> None:
    ruta = raiz / relativa
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(documento, ensure_ascii=False), encoding="utf-8")


def test_el_arbol_copiado_pasa(tmp_path: Path) -> None:
    assert comprobar(_arbol(tmp_path)) == []


def test_un_defecto_sembrado_en_cualquier_contrato_se_ve(tmp_path: Path) -> None:
    raiz = _arbol(tmp_path)
    _escribir(raiz, "api/nuevo.v1.json", {"properties": {"is_lying": {"type": "boolean"}}})
    assert comprobar(raiz) == [
        "BR3.3: api/nuevo.v1.json: nombres con vocabulario de veracidad: ['is_lying']"
    ]


def test_un_defecto_en_la_raiz_de_contracts_tambien_se_ve(tmp_path: Path) -> None:
    raiz = _arbol(tmp_path)
    _escribir(raiz, "suelto.v1.json", {"properties": {"puntaje_falso": {}}})
    assert comprobar(raiz) == [
        "BR3.3: suelto.v1.json: nombres con vocabulario de veracidad: ['puntaje_falso']"
    ]


def test_un_defecto_en_un_subdirectorio_se_ve(tmp_path: Path) -> None:
    raiz = _arbol(tmp_path)
    _escribir(raiz, "analyzer/v2/nuevo.json", {"properties": {"verdadero": {}}})
    assert comprobar(raiz) == [
        "BR3.3: analyzer/v2/nuevo.json: nombres con vocabulario de veracidad: ['verdadero']"
    ]


def test_los_fixtures_y_vendor_no_se_recorren(tmp_path: Path) -> None:
    raiz = _arbol(tmp_path)
    _escribir(raiz, "api/fixtures/malo.json", {"properties": {"is_lying": {}}})
    _escribir(
        raiz, "integrity/fixtures/review-suggestion/malo.json", {"properties": {"is_lying": {}}}
    )
    _escribir(raiz, "vendor/malo.json", {"properties": {"is_lying": {}}})
    _escribir(raiz, "tests/malo.json", {"properties": {"is_lying": {}}})
    assert comprobar(raiz) == []


def test_los_archivos_que_no_son_yaml_ni_json_no_se_leen(tmp_path: Path) -> None:
    raiz = _arbol(tmp_path)
    (raiz / "api" / "nota.txt").write_text("{ roto", encoding="utf-8")
    (raiz / "api" / "nota.md").write_text("properties is_lying", encoding="utf-8")
    assert comprobar(raiz) == []


def test_un_yaml_o_json_ilegible_se_informa_sin_su_contenido(tmp_path: Path) -> None:
    raiz = _arbol(tmp_path)
    (raiz / "api" / "roto.yaml").write_text(f"{CANARIO}: [1, 2", encoding="utf-8")
    (raiz / "api" / "roto.json").write_text(f'{{"{CANARIO}": ', encoding="utf-8")
    problemas = comprobar(raiz)
    assert problemas == ["api/roto.json: ilegible", "api/roto.yaml: ilegible"]
    assert CANARIO not in "".join(problemas)


CODIGOS_DE_C6 = [
    "salida_invalida", "bloqueo_contenido", "tiempo_agotado", "proveedor",
    "anonimizador_no_disponible", "incidente_anonimizacion",
]  # fmt: skip
MOTIVOS_DE_C6 = [
    "cita_no_verificada", "cita_en_otro_turno", "marca_alterada", "campo_faltante",
    "rechazado_verificador", "rechazado_permutacion", "fuera_de_tramo", "vocabulario_prohibido",
]  # fmt: skip
ENUMS_DE_C6 = {
    "status": ["ok", "error"],
    "error_code": CODIGOS_DE_C6,
    "discards": MOTIVOS_DE_C6,
    "fact_type": sorted(TIPOS),
    "papel": ["juez", "verificador", "verificador_permutado"],
}
NOMBRE_EN_C6 = {
    "status": "estado",
    "error_code": "codigo",
    "discards": "motivo",
    "fact_type": "tipo",
    "papel": "papel",
}
C19 = "cli/report.schema.v2.yaml"
C1 = "api/console.v2.yaml"


def _c19(**cambios: Any) -> dict[str, Any]:
    """Un reporte mínimo con las cuatro rutas de enum de C6 que declara contract-summary (C19)."""
    enums = {**ENUMS_DE_C6, **cambios}
    corrida = {
        "status": {"enum": enums["status"]},
        "error_code": {"enum": enums["error_code"]},
        "discards": {"propertyNames": {"enum": enums["discards"]}},
    }
    return {
        "properties": {
            "runs": {"items": {"properties": corrida}},
            "bias_table": {"items": {"properties": {"fact_type": {"enum": enums["fact_type"]}}}},
        }
    }


def _c1(papel: Any) -> dict[str, Any]:
    """Una consola mínima: ModelCall.papel copia el enum de C6; `estado` (visible/plegado) es ajeno."""
    return {
        "components": {
            "schemas": {
                "ModelCall": {"properties": {"papel": {"enum": papel}}},
                "Turn": {"properties": {"estado": {"enum": ["visible", "plegado"]}}},
            }
        }
    }


def _con_c19_y_c1(raiz: Path, c19: Any, c1: Any) -> None:
    _escribir(raiz, C19, c19)
    _escribir(raiz, C1, c1)


def test_las_rutas_declaradas_de_c19_y_c1_pasan(tmp_path: Path) -> None:
    raiz = _arbol(tmp_path)
    _con_c19_y_c1(raiz, _c19(), _c1(ENUMS_DE_C6["papel"]))
    assert comprobar(raiz) == []


@pytest.mark.parametrize("campo", ["status", "error_code", "discards", "fact_type"])
def test_una_copia_desviada_de_un_valor_en_c19_se_ve(tmp_path: Path, campo: str) -> None:
    """Una copia que conserva solo un valor de C6 también es una copia desviada (F-03)."""
    valores = ENUMS_DE_C6[campo]
    desviadas = (
        [valores[0], "otro_valor"],
        valores[:-1],
        [*valores, "otro_valor"],
        [*valores[:-1], "otro_valor"],
        [],
    )
    esperado = f"BR3.2: {C19}: el enum de {campo} difiere del de C6 ({NOMBRE_EN_C6[campo]})"
    for posicion, desviada in enumerate(desviadas):
        raiz = tmp_path / f"copia-{posicion}"
        raiz.mkdir()
        _arbol(raiz)
        _con_c19_y_c1(raiz, _c19(**{campo: desviada}), _c1(ENUMS_DE_C6["papel"]))
        assert comprobar(raiz) == [esperado], desviada


def test_una_copia_desviada_de_papel_en_c1_se_ve(tmp_path: Path) -> None:
    raiz = _arbol(tmp_path)
    _con_c19_y_c1(raiz, _c19(), _c1(["juez", "otro_papel"]))
    assert comprobar(raiz) == [f"BR3.2: {C1}: el enum de papel difiere del de C6 (papel)"]


def test_el_enum_estado_de_c6_se_compara_en_c19(tmp_path: Path) -> None:
    raiz = _arbol(tmp_path)
    _con_c19_y_c1(raiz, _c19(status=["ok", "advertencia"]), _c1(ENUMS_DE_C6["papel"]))
    assert comprobar(raiz) == [f"BR3.2: {C19}: el enum de status difiere del de C6 (estado)"]


@pytest.mark.parametrize("campo", ["status", "error_code", "discards", "fact_type"])
def test_una_ruta_declarada_de_c19_que_falta_se_ve(tmp_path: Path, campo: str) -> None:
    c19 = _c19()
    if campo == "fact_type":
        del c19["properties"]["bias_table"]
    else:
        del c19["properties"]["runs"]["items"]["properties"][campo]
    raiz = _arbol(tmp_path)
    _con_c19_y_c1(raiz, c19, _c1(ENUMS_DE_C6["papel"]))
    assert comprobar(raiz) == [f"BR3.2: {C19}: no declara el enum de {campo} de C6"]


def test_una_ruta_declarada_que_no_trae_el_enum_en_linea_se_ve(tmp_path: Path) -> None:
    c19 = _c19()
    c19["properties"]["runs"]["items"]["properties"]["discards"] = {
        "propertyNames": {"type": "string"}
    }
    c19["properties"]["runs"]["items"]["properties"]["status"] = {"enum": 3}
    raiz = _arbol(tmp_path)
    _con_c19_y_c1(raiz, c19, _c1(ENUMS_DE_C6["papel"]))
    assert comprobar(raiz) == [
        f"BR3.2: {C19}: no declara el enum de status de C6",
        f"BR3.2: {C19}: no declara el enum de discards de C6",
    ]


def test_c1_sin_el_enum_de_papel_se_ve(tmp_path: Path) -> None:
    raiz = _arbol(tmp_path)
    _con_c19_y_c1(raiz, _c19(), {"components": {"schemas": {}}})
    assert comprobar(raiz) == [f"BR3.2: {C1}: no declara el enum de papel de C6"]


def test_c7_con_el_enum_de_tipo_desviado_se_ve(tmp_path: Path) -> None:
    for valores in (
        ["fecha", "fuente"],
        ["fecha", "numero", "lugar", "persona"],
        [*sorted(TIPOS), "fuente"],
    ):
        raiz = tmp_path / str(len(valores))
        raiz.mkdir()
        _arbol(raiz)
        c7 = copia(C7)
        c7["properties"]["tipo"] = {"enum": valores}
        _escribir(raiz, C7, c7)
        assert comprobar(raiz) == [
            "BR3.2: integrity/review-suggestion.v2.json: el enum de tipo difiere del de C6 (tipo)"
        ], valores


def test_c7_sin_enum_de_tipo_se_ve(tmp_path: Path) -> None:
    raiz = _arbol(tmp_path)
    c7 = copia(C7)
    del c7["properties"]["tipo"]
    _escribir(raiz, C7, c7)
    assert comprobar(raiz) == [
        "BR3.2: integrity/review-suggestion.v2.json: no declara el enum de tipo de C6"
    ]


def test_un_enum_ajeno_que_se_parece_a_uno_de_c6_no_se_compara(tmp_path: Path) -> None:
    """La comparación va por la ruta declarada, no por parecido: un enum libre no es una copia."""
    raiz = _arbol(tmp_path)
    _escribir(
        raiz, "queues/otro.json", {"properties": {"t": {"enum": ["fecha", "numero", "lugar"]}}}
    )
    assert comprobar(raiz) == []


def test_un_defecto_sembrado_en_un_yml_se_ve(tmp_path: Path) -> None:
    raiz = _arbol(tmp_path)
    _escribir(raiz, "api/nuevo.v1.yml", {"properties": {"is_lying": {"type": "boolean"}}})
    assert comprobar(raiz) == [
        "BR3.3: api/nuevo.v1.yml: nombres con vocabulario de veracidad: ['is_lying']"
    ]


def test_los_directorios_de_datos_son_los_del_arbol() -> None:
    """Un directorio de datos nuevo sin listar en `DIRECTORIOS_DE_DATOS` deja la suite en rojo."""
    no_datos = {"src", "tests", "ts", "fixtures", "build", "dist", "vendor"}
    en_el_arbol = {
        d.name
        for d in CONTRACTS_ROOT.iterdir()
        if d.is_dir() and not d.name.startswith((".", "_")) and d.name not in no_datos
    }
    assert en_el_arbol == set(veracity.DIRECTORIOS_DE_DATOS)


@pytest.mark.parametrize(
    "relativa",
    [
        C8,
        ROTULOS,
        AVISO,
        ACLARACION,
        SALIDA,
        C7,
    ],
)
def test_un_archivo_clave_ausente_o_ilegible_se_informa(tmp_path: Path, relativa: str) -> None:
    raiz = _arbol(tmp_path)
    (raiz / relativa).unlink()
    assert comprobar(raiz) == [f"{relativa}: ausente o ilegible"]
    (raiz / relativa).write_text(f"{CANARIO}: [1", encoding="utf-8")
    problemas = comprobar(raiz)
    assert f"{relativa}: ausente o ilegible" in problemas
    assert CANARIO not in "".join(problemas)


@pytest.mark.parametrize("salida", [{}, [], {"$defs": {}}, {"$defs": {"registro": 3}}])
def test_una_salida_de_c6_sin_sus_enum_se_informa(tmp_path: Path, salida: Any) -> None:
    raiz = _arbol(tmp_path)
    _escribir(raiz, SALIDA, salida)
    assert comprobar(raiz) == [f"{SALIDA}: no declara los enum de C6"]


def test_comprobar_propaga_los_defectos_de_cada_archivo_clave(tmp_path: Path) -> None:
    raiz = _arbol(tmp_path)
    c8 = copia(C8)
    c8["terms"].append("mintiendo")
    _escribir(raiz, C8, c8)
    rotulos = copia(ROTULOS)
    rotulos["labels"]["decimo"] = "Décimo"
    _escribir(raiz, ROTULOS, rotulos)
    aviso = copia(AVISO)
    aviso["version"] = "x"
    _escribir(raiz, AVISO, aviso)
    aclaracion = copia(ACLARACION)
    aclaracion["reject_if"]["phrases"] = []
    _escribir(raiz, ACLARACION, aclaracion)
    problemas = comprobar(raiz)
    assert [p.split(":")[0] for p in problemas] == ["BR5.1", "BR6.1", "BR5.7", "BR5.6"]


def test_el_tipo_de_los_rotulos_sale_de_c6_y_no_de_una_lista_fija(tmp_path: Path) -> None:
    raiz = _arbol(tmp_path)
    salida = copia(SALIDA)
    salida["$defs"]["hallazgo"]["properties"]["tipo"]["enum"].append("fuente")
    _escribir(raiz, SALIDA, salida)
    problemas = comprobar(raiz)
    assert "BR6.2: las filas type_* no corresponden a los tipos de C6" in problemas


def test_los_mensajes_no_llevan_texto_del_documento(tmp_path: Path) -> None:
    raiz = _arbol(tmp_path)
    c8 = copia(C8)
    c8["terms"].append(CANARIO)
    c8["match"][CANARIO] = CANARIO
    _escribir(raiz, C8, c8)
    rotulos = copia(ROTULOS)
    rotulos["labels"]["type_otro"] = CANARIO
    rotulos["labels"][CANARIO] = CANARIO
    _escribir(raiz, ROTULOS, rotulos)
    aviso = copia(AVISO)
    aviso["text"] = CANARIO
    aviso["version"] = CANARIO
    _escribir(raiz, AVISO, aviso)
    aclaracion = copia(ACLARACION)
    aclaracion["reject_if"]["phrases"] = [CANARIO]
    _escribir(raiz, ACLARACION, aclaracion)
    problemas = comprobar(raiz)
    assert len(problemas) >= 5
    assert CANARIO not in "".join(problemas)
