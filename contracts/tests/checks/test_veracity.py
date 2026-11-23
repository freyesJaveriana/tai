"""Guardia de veracidad (BR3.2, BR3.3, BR5.1, BR5.6, BR5.7, BR6.1–BR6.3; security-design §4.8).

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

TERMINOS_APROBADOS = [
    "mentiroso", "mentirosa", "miente", "mintió", "falso", "falsa", "verdadero", "verdadera", "engaño",
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


@pytest.mark.parametrize("nombre", ["falsete", "mienten", "verdaderamente", "tipo", "cita_a"])
def test_palabra_completa_no_subcadena(nombre: str) -> None:
    """E14: «falsete» y «mienten» no coinciden (la lista se queda en 9 términos)."""
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
    c8["terms"].append("mienten")
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
    for texto in ("Texto distinto", FRASE_BASE[:-1], FRASE_BASE.replace("No son prueba", "Son prueba"), 5):
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
    assert problemas_de_aclaracion(documento) == [
        "BR5.6: reject_if trae claves no aprobadas"
    ]
    documento = _aclaracion()
    documento["reject_if"] = ["mentions_contradiction"]
    assert problemas_de_aclaracion(documento) == ["BR5.6: reject_if no es un objeto"]


# ---------------------------------------------------------------- nombres (BR3.3)


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
    documento = {"properties": {"falsete": {}, "mienten": {}, "tipo": {"enum": ["fecha", "otro"]}}}
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
    assert "estado" not in enums
    assert set(enums) == {"tipo", "codigo", "motivo", "papel"}


C6 = {
    "tipo": frozenset({"a", "b", "c"}),
    "papel": frozenset({"x", "y"}),
}


def test_un_enum_igual_o_sin_parentesco_pasa() -> None:
    documento = {"properties": {"t": {"enum": ["c", "b", "a"]}, "u": {"enum": ["a", "z"]}}}
    assert problemas_de_enums("x.yaml", documento, C6, exige_tipo=True) == []


def test_un_enum_que_comparte_dos_valores_y_difiere_da_br32() -> None:
    for valores in (["a", "b"], ["a", "b", "c", "d"], ["a", "b", "z"]):
        documento = {"properties": {"t": {"enum": valores}}}
        assert problemas_de_enums("x.yaml", documento, C6, exige_tipo=False) == [
            "BR3.2: x.yaml: un enum difiere del de C6 (tipo)"
        ], valores


def test_un_enum_que_comparte_un_solo_valor_no_se_compara() -> None:
    documento = {"properties": {"t": {"enum": ["a", "z"]}, "p": {"enum": ["x"]}}}
    assert problemas_de_enums("x.yaml", documento, C6, exige_tipo=False) == []


def test_un_enum_cuenta_aunque_traiga_valores_que_no_son_cadenas() -> None:
    documento = {"properties": {"t": {"enum": ["a", "b", 3]}}}
    assert problemas_de_enums("x.yaml", documento, C6, exige_tipo=False) == []
    documento = {"enum": ["a", "b", "z", "w"], "propiedad": {"enum": "a"}}
    assert problemas_de_enums("x.yaml", documento, C6, exige_tipo=False) == [
        "BR3.2: x.yaml: un enum difiere del de C6 (tipo)"
    ]


def test_exige_tipo_pide_el_enum_de_tipo_de_c6() -> None:
    assert problemas_de_enums("x.yaml", {"properties": {}}, C6, exige_tipo=True) == [
        "BR3.2: x.yaml: no declara el enum de tipo de C6"
    ]
    documento = {"properties": {"t": {"enum": ["a", "b"]}}}
    assert problemas_de_enums("x.yaml", documento, C6, exige_tipo=True) == [
        "BR3.2: x.yaml: un enum difiere del de C6 (tipo)",
        "BR3.2: x.yaml: no declara el enum de tipo de C6",
    ]
    assert problemas_de_enums("x.yaml", {"properties": {}}, C6, exige_tipo=False) == []


def test_c7_versionado_declara_el_enum_de_tipo() -> None:
    c6 = enums_de_c6(load_contract(SALIDA))
    assert problemas_de_enums(C7, load_contract(C7), c6, exige_tipo=True) == []


# ---------------------------------------------------------------- comprobar sobre un árbol


def _arbol(destino: Path) -> Path:
    """Copia los directorios de datos (sin fixtures) a `destino` y devuelve la raíz."""
    for directorio in DIRECTORIOS:
        shutil.copytree(
            CONTRACTS_ROOT / directorio, destino / directorio, ignore=shutil.ignore_patterns("fixtures")
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
    _escribir(raiz, "integrity/fixtures/review-suggestion/malo.json", {"properties": {"is_lying": {}}})
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


def test_un_enum_de_c6_alterado_en_cualquier_contrato_se_ve(tmp_path: Path) -> None:
    raiz = _arbol(tmp_path)
    _escribir(raiz, "queues/otro.json", {"properties": {"t": {"enum": ["fecha", "numero", "lugar"]}}})
    assert comprobar(raiz) == ["BR3.2: queues/otro.json: un enum difiere del de C6 (tipo)"]


def test_c7_con_el_enum_de_tipo_recortado_se_ve(tmp_path: Path) -> None:
    raiz = _arbol(tmp_path)
    c7 = copia(C7)
    c7["properties"]["tipo"] = {"enum": ["fecha", "numero", "lugar", "persona"]}
    _escribir(raiz, C7, c7)
    assert comprobar(raiz) == [
        "BR3.2: integrity/review-suggestion.v2.json: un enum difiere del de C6 (tipo)",
        "BR3.2: integrity/review-suggestion.v2.json: no declara el enum de tipo de C6",
    ]


def test_c7_sin_enum_de_tipo_se_ve(tmp_path: Path) -> None:
    raiz = _arbol(tmp_path)
    c7 = copia(C7)
    del c7["properties"]["tipo"]
    _escribir(raiz, C7, c7)
    assert comprobar(raiz) == [
        "BR3.2: integrity/review-suggestion.v2.json: no declara el enum de tipo de C6"
    ]


def test_el_reporte_y_la_consola_tambien_exigen_el_enum_de_tipo_cuando_existen(tmp_path: Path) -> None:
    raiz = _arbol(tmp_path)
    _escribir(raiz, "cli/report.schema.v2.yaml", {"properties": {"x": {"type": "string"}}})
    _escribir(raiz, "api/console.v2.yaml", {"properties": {"x": {"type": "string"}}})
    assert comprobar(raiz) == [
        "BR3.2: api/console.v2.yaml: no declara el enum de tipo de C6",
        "BR3.2: cli/report.schema.v2.yaml: no declara el enum de tipo de C6",
    ]
    _escribir(raiz, "cli/report.schema.v2.yaml", {"properties": {"x": {"enum": sorted(TIPOS)}}})
    assert comprobar(raiz) == ["BR3.2: api/console.v2.yaml: no declara el enum de tipo de C6"]


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
    c8["terms"].append("mienten")
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
