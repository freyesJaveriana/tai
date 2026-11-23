"""Guardia de la forma de los casos de escaneo y del aviso de testimonio (BR5.8, E40, BR3.6, PD-6).

U1 no ejecuta el escáner (es de U11): valida solo la forma de `integrity/scan-cases.v1.yaml`, que
haya un caso por término de C8 y por frase de la aclaración neutra (E40), los escenarios E10–E14,
E30 y la decisión D-2, y la forma y coherencia de `integrity/testimony-warning-cases.v1.yaml`
(NFR-U13-10, NFRD-U13-13). Módulo guardia con 100 % de ramas: cada constante y cada patrón tiene
un control negativo con una copia con un defecto sembrado, en memoria o en `tmp_path`.
"""

import copy
import json
import shutil
from pathlib import Path
from typing import Any

import pytest
from helpers import CONTRACTS_ROOT, load_contract

from veridicus_contracts.checks import scan_cases
from veridicus_contracts.checks.scan_cases import (
    comprobar,
    problemas_de_casos,
    problemas_de_testimonio,
)

CASOS = "integrity/scan-cases.v1.yaml"
TESTIMONIO = "integrity/testimony-warning-cases.v1.yaml"
LIMITES = "limits.v1.yaml"
TERMINOS = ("mentiroso", "mentirosa", "miente", "mintió", "falso", "falsa", "verdadero", "verdadera", "engaño")  # fmt: skip
FRASES = ("antes dijo", "dijo antes", "se contradice", "antes mencionó", "había dicho")
ORIGENES = ("E10", "E11", "E12", "E13", "E14", "E30", "D-2")
CANARIO = "canario-de-testimonio-sintetico"
ESPACIOS = [
    9, 10, 11, 12, 13, 28, 29, 30, 31, 32, 133, 160, 5760, 8192, 8193, 8194, 8195, 8196, 8197, 8198,
    8199, 8200, 8201, 8202, 8232, 8233, 8239, 8287, 12288,
]  # fmt: skip
REQUERIDOS = {
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


def copia(relativa: str) -> Any:
    return copy.deepcopy(load_contract(relativa))


def casos() -> dict[str, Any]:
    return copia(CASOS)  # type: ignore[no-any-return]


def validar(documento: Any) -> list[str]:
    return problemas_de_casos(documento, TERMINOS, FRASES)


def uno(documento: dict[str, Any], origen_o_id: str) -> dict[str, Any]:
    return next(c for c in documento["cases"] if origen_o_id in (c["id"], c["source"]))


# ---------------------------------------------------------------- constantes y datos versionados


def test_los_archivos_versionados_pasan() -> None:
    assert comprobar(CONTRACTS_ROOT) == []
    assert validar(casos()) == []


def test_las_constantes_son_las_aprobadas() -> None:
    assert scan_cases.CASOS_DE_ESCANEO == CASOS
    assert scan_cases.CASOS_DE_TESTIMONIO == TESTIMONIO
    assert scan_cases.LIMITES == LIMITES
    assert scan_cases.CAMPOS == ("hecho", "observaciones", "tema")
    assert scan_cases.REGLAS == ("vocabulary", "clarification")
    assert scan_cases.MOTIVOS == ("mentions_contradiction", "phrase", "cites_turn")
    assert scan_cases.ORIGENES_EXIGIDOS == ORIGENES
    assert scan_cases.REQUERIDOS_DE_TESTIMONIO == REQUERIDOS


def test_el_conjunto_versionado_cubre_cada_termino_y_cada_frase() -> None:
    documento = casos()
    assert documento["schema_version"] == "1.0.0"
    de_vocabulario = [c for c in documento["cases"] if c["rule"] == "vocabulary"]
    coincidencias = {t for c in de_vocabulario for t in c["expect"]["matches"]}
    assert coincidencias == set(TERMINOS)
    de_aclaracion = [c for c in documento["cases"] if c["rule"] == "clarification"]
    rechazadas = {f for c in de_aclaracion for f in c["expect"]["phrases"]}
    assert rechazadas == set(FRASES)
    assert {c["source"] for c in documento["cases"]} >= set(ORIGENES)
    assert all(c["synthetic"] is True for c in documento["cases"])
    ids = [c["id"] for c in documento["cases"]]
    assert len(ids) == len(set(ids))


def test_el_caso_e11_excluye_una_cita_y_el_de_d2_escanea_el_termino_solo() -> None:
    documento = casos()
    e11 = uno(documento, "E11")
    assert e11["expect"]["matches"] == []
    assert e11["expect"]["excluded"] != []
    d2 = uno(documento, "D-2")
    assert d2["expect"]["excluded"] == []
    assert d2["expect"]["matches"] != []
    e14 = uno(documento, "E14")
    assert e14["expect"]["matches"] == []


# ---------------------------------------------------------------- forma del documento


def test_documento_que_no_es_un_objeto_o_con_claves_distintas() -> None:
    assert validar([]) == ["BR5.8: scan-cases no es un objeto"]
    documento = casos()
    documento["extra"] = 1
    assert validar(documento) == ["BR5.8: scan-cases trae claves de primer nivel no aprobadas"]
    documento = casos()
    documento["schema_version"] = "2.0.0"
    assert validar(documento) == ["BR5.8: schema_version de scan-cases debe ser 1.0.0"]
    documento = casos()
    documento["cases"] = {"a": 1}
    assert validar(documento) == ["BR5.8: cases no es una lista"]


def test_un_caso_que_no_es_un_objeto() -> None:
    documento = casos()
    documento["cases"][0] = "texto"
    problemas = validar(documento)
    assert problemas[0] == "BR5.8: casos[0]: no es un objeto"


@pytest.mark.parametrize("clave", ["id", "source", "synthetic", "rule", "field", "text", "literal_sources", "expect"])
def test_un_caso_sin_una_de_sus_claves(clave: str) -> None:
    documento = casos()
    primero = documento["cases"][0]
    del primero[clave]
    assert validar(documento)[0] == "BR5.8: casos[0]: claves no aprobadas"


def test_un_caso_con_una_clave_de_mas() -> None:
    documento = casos()
    documento["cases"][0]["extra"] = 1
    assert validar(documento) == ["BR5.8: casos[0]: claves no aprobadas"]


@pytest.mark.parametrize("identificador", ["", "Mayuscula", "con espacio", "con_guion_bajo", "-inicio", "fin-", "a--b", 7])
def test_un_id_que_no_es_identificador(identificador: Any) -> None:
    documento = casos()
    documento["cases"][0]["id"] = identificador
    assert validar(documento) == ["BR5.8: casos[0]: id no es un identificador válido"]


def test_un_id_repetido() -> None:
    documento = casos()
    documento["cases"][1]["id"] = documento["cases"][0]["id"]
    assert validar(documento) == ["BR5.8: casos[1]: id repetido"]


@pytest.mark.parametrize("origen", ["", "e10", "E", "E1x", "BR5", "BR5.8.1", "D-3", "otro", 5])
def test_un_origen_que_no_es_valido(origen: Any) -> None:
    documento = casos()
    documento["cases"][0]["source"] = origen
    problemas = validar(documento)
    assert "BR5.8: casos[0]: source no es un origen válido" in problemas


@pytest.mark.parametrize("origen", ["E1", "E40", "BR5.8", "BR12.3", "D-2"])
def test_los_origenes_validos(origen: str) -> None:
    documento = casos()
    documento["cases"][-1]["source"] = origen
    assert all("source" not in p for p in validar(documento))


@pytest.mark.parametrize("valor", [False, "true", 1, None])
def test_un_caso_no_sintetico(valor: Any) -> None:
    documento = casos()
    documento["cases"][0]["synthetic"] = valor
    assert validar(documento) == ["BR5.8: casos[0]: synthetic debe ser true"]


@pytest.mark.parametrize("regla", ["", "Vocabulary", "otra", 3])
def test_una_regla_que_no_es_aprobada(regla: Any) -> None:
    documento = casos()
    documento["cases"][0]["rule"] = regla
    assert "BR5.8: casos[0]: rule no es una regla aprobada" in validar(documento)


@pytest.mark.parametrize("campo", ["", "Hecho", "cita_a", "texto", 3])
def test_un_campo_que_no_es_aprobado(campo: Any) -> None:
    documento = casos()
    documento["cases"][0]["field"] = campo
    assert validar(documento) == ["BR5.8: casos[0]: field no es un campo aprobado"]


@pytest.mark.parametrize("campo", ["hecho", "observaciones", "tema"])
def test_los_tres_campos_de_vocabulario_son_validos(campo: str) -> None:
    documento = casos()
    caso = uno(documento, "E10")
    caso["field"] = campo
    assert validar(documento) == []


@pytest.mark.parametrize("campo", ["hecho", "observaciones"])
def test_una_aclaracion_solo_va_en_tema(campo: str) -> None:
    documento = casos()
    caso = uno(documento, "E30")
    caso["field"] = campo
    assert validar(documento) == ["BR5.8: casos[{}]: field de una aclaración debe ser tema".format(documento["cases"].index(caso))]


@pytest.mark.parametrize("texto", ["", None, 5, ["a"]])
def test_un_texto_vacio_o_que_no_es_texto(texto: Any) -> None:
    documento = casos()
    documento["cases"][0]["text"] = texto
    problemas = validar(documento)
    assert problemas[0] == "BR5.8: casos[0]: text vacío o no es texto"


@pytest.mark.parametrize("fuentes", ["texto", [""], [3], None, ["ok", ""]])
def test_fuentes_literales_que_no_son_una_lista_de_textos(fuentes: Any) -> None:
    documento = casos()
    caso = uno(documento, "E11")
    caso["literal_sources"] = fuentes
    problemas = validar(documento)
    assert "casos[{}]: literal_sources no es una lista de textos no vacíos".format(
        documento["cases"].index(caso)
    ) in " ".join(problemas)


@pytest.mark.parametrize(
    "numero", ["123456", "1234567890", "12 34 56", "12.34.56", "1-2-3-4-5-6", "1234567890123456789012345"]
)
def test_una_secuencia_de_seis_o_mas_digitos_no_es_sintetica(numero: str) -> None:
    mensaje = "BR5.8: casos[0]: text o literal_sources traen una secuencia de seis o más dígitos"
    documento = casos()
    documento["cases"][0]["text"] = f"el caso {numero} del relato"
    assert validar(documento) == [mensaje]
    documento = casos()
    assert documento["cases"][0]["literal_sources"] == []
    documento["cases"][0]["literal_sources"] = [f"turno {numero}"]
    assert validar(documento) == [mensaje]


@pytest.mark.parametrize("numero", ["12345", "12 34", "1 2 3 4 5", "12, 34, 56"])
def test_menos_de_seis_digitos_pasan(numero: str) -> None:
    documento = casos()
    documento["cases"][0]["text"] = f"el caso {numero} del relato"
    assert validar(documento) == []


# ---------------------------------------------------------------- expectativas de vocabulario


def test_expect_que_no_es_un_objeto_o_con_claves_distintas() -> None:
    documento = casos()
    documento["cases"][0]["expect"] = ["miente"]
    assert validar(documento) == ["BR5.8: casos[0]: expect no es un objeto"]
    documento = casos()
    documento["cases"][0]["expect"]["extra"] = 1
    assert validar(documento) == ["BR5.8: casos[0]: expect: claves no aprobadas"]
    documento = casos()
    del documento["cases"][0]["expect"]["excluded"]
    assert validar(documento) == ["BR5.8: casos[0]: expect: claves no aprobadas"]


@pytest.mark.parametrize("matches", ["miente", [3], ["otro"], ["Miente"], None, ["miente", "miente"]])
def test_matches_que_no_son_terminos_de_c8_sin_repetir(matches: Any) -> None:
    documento = casos()
    documento["cases"][0]["expect"]["matches"] = matches
    problemas = validar(documento)
    assert "BR5.8: casos[0]: expect.matches no es una lista de términos de C8 sin repetir" in problemas


def test_una_coincidencia_con_la_forma_de_c8_pasa() -> None:
    """Los términos se escriben como están en C8, con su tilde («mintió»)."""
    documento = casos()
    documento["cases"][0]["expect"]["matches"] = ["mintió", "engaño"]
    assert validar(documento) == []


@pytest.mark.parametrize("excluidos", ["tramo", [""], [3], None, ["no está entre comillas"]])
def test_excluded_que_no_son_tramos_citados_en_el_texto(excluidos: Any) -> None:
    documento = casos()
    caso = uno(documento, "E11")
    caso["expect"]["excluded"] = excluidos
    posicion = documento["cases"].index(caso)
    assert f"BR5.8: casos[{posicion}]: expect.excluded no es una lista de tramos citados en text" in validar(documento)


def test_un_tramo_excluido_debe_estar_entre_comillas_angulares() -> None:
    documento = casos()
    caso = uno(documento, "E11")
    tramo = caso["expect"]["excluded"][0]
    assert f"«{tramo}»" in caso["text"]
    caso["text"] = caso["text"].replace("«", "").replace("»", "")
    posicion = documento["cases"].index(caso)
    assert validar(documento) == [
        f"BR5.8: casos[{posicion}]: expect.excluded no es una lista de tramos citados en text"
    ]


def test_un_tramo_excluido_debe_estar_en_una_fuente_literal() -> None:
    documento = casos()
    caso = uno(documento, "E11")
    caso["literal_sources"] = ["otro turno sin la cita"]
    posicion = documento["cases"].index(caso)
    assert validar(documento) == [
        f"BR5.8: casos[{posicion}]: expect.excluded trae un tramo que no está en ninguna fuente literal"
    ]
    caso["literal_sources"] = []
    assert validar(documento) == [
        f"BR5.8: casos[{posicion}]: expect.excluded trae un tramo que no está en ninguna fuente literal"
    ]


def test_los_espacios_distintos_no_impiden_que_la_cita_este_en_la_fuente() -> None:
    """Regla del piloto: solo se normalizan espacios al comparar con el turno."""
    documento = casos()
    caso = uno(documento, "E11")
    tramo = caso["expect"]["excluded"][0]
    caso["literal_sources"] = ["antes   " + tramo.replace(" ", "  \n ") + " después"]
    assert validar(documento) == []


@pytest.mark.parametrize("termino", TERMINOS)
def test_d2_un_tramo_que_es_solo_un_termino_no_se_excluye(termino: str) -> None:
    documento = casos()
    caso = uno(documento, "E11")
    caso["text"] = f"dijo «{termino.upper()}» ayer"
    caso["literal_sources"] = [f"{termino.upper()}"]
    caso["expect"]["excluded"] = [termino.upper()]
    posicion = documento["cases"].index(caso)
    assert validar(documento) == [
        f"BR5.8: casos[{posicion}]: expect.excluded trae un tramo que es solo un término (D-2)"
    ]


def test_d2_el_tramo_es_solo_un_termino_sin_distinguir_tildes_ni_espacios() -> None:
    documento = casos()
    caso = uno(documento, "E11")
    caso["text"] = "dijo « Mintio » ayer"
    caso["literal_sources"] = ["Mintio"]
    caso["expect"]["excluded"] = [" Mintio "]
    assert validar(documento)[-1].endswith("expect.excluded trae un tramo que es solo un término (D-2)")


def test_un_tramo_con_un_termino_y_mas_palabras_si_se_excluye() -> None:
    documento = casos()
    caso = uno(documento, "E11")
    caso["text"] = "dijo «que miente a veces» ayer"
    caso["literal_sources"] = ["que miente a veces"]
    caso["expect"]["excluded"] = ["que miente a veces"]
    assert validar(documento) == []


# ---------------------------------------------------------------- expectativas de aclaración


def test_aclaracion_con_expect_valido_pasa() -> None:
    documento = casos()
    valida = next(c for c in documento["cases"] if c["rule"] == "clarification" and c["expect"]["valid"])
    assert valida["expect"] == {"valid": True, "reasons": [], "phrases": []}
    e30 = uno(documento, "E30")
    assert e30["expect"]["valid"] is False
    assert set(e30["expect"]["reasons"]) == {"phrase", "cites_turn"}
    assert e30["expect"]["phrases"] == ["antes dijo"]


def _aclaracion(documento: dict[str, Any]) -> tuple[dict[str, Any], int]:
    caso = uno(documento, "E30")
    return caso, documento["cases"].index(caso)


@pytest.mark.parametrize("expect", [["valid"], "valid", None, 3])
def test_aclaracion_con_expect_que_no_es_un_objeto(expect: Any) -> None:
    documento = casos()
    caso, i = _aclaracion(documento)
    caso["expect"] = expect
    assert validar(documento) == [f"BR5.8: casos[{i}]: expect no es un objeto"]


def test_el_aviso_acepta_la_ventana_en_el_ultimo_lugar_del_turno_y_de_la_nota() -> None:
    """F-04: una ventana que termina justo al final de la nota y del turno cuenta."""
    documento = datos_de_testimonio()
    caso = documento["cases"][0]
    caso["note"] = "Anoche vi la luna subió despacio sobre el techo viejo"
    caso["turns"] = ["Dijo que vio la luna subió despacio sobre el techo viejo"]
    caso["testimony_warning"] = True
    assert validar_testimonio(documento) == []
    caso["turns"] = ["Dijo que vio luna subió despacio sobre el techo viejo"]
    assert validar_testimonio(documento) == [
        "BR3.6: casos[0]: el resultado esperado no concuerda con la regla de BR3.6"
    ]


def test_aclaracion_con_expect_de_vocabulario() -> None:
    documento = casos()
    caso, i = _aclaracion(documento)
    caso["expect"] = {"matches": [], "excluded": []}
    assert validar(documento) == [f"BR5.8: casos[{i}]: expect: claves no aprobadas"]


@pytest.mark.parametrize("valido", [1, 0, "true", None])
def test_valid_debe_ser_booleano(valido: Any) -> None:
    documento = casos()
    caso, i = _aclaracion(documento)
    caso["expect"]["valid"] = valido
    assert f"BR5.8: casos[{i}]: expect.valid debe ser booleano" in validar(documento)


@pytest.mark.parametrize("motivos", ["phrase", ["otro"], [3], ["phrase", "phrase"], None])
def test_motivos_que_no_son_aprobados_o_se_repiten(motivos: Any) -> None:
    documento = casos()
    caso, i = _aclaracion(documento)
    caso["expect"]["reasons"] = motivos
    assert f"BR5.8: casos[{i}]: expect.reasons no es una lista de motivos aprobados sin repetir" in validar(documento)


@pytest.mark.parametrize("frases", ["antes dijo", ["otra frase"], [3], ["antes dijo", "antes dijo"], None])
def test_frases_que_no_son_aprobadas_o_se_repiten(frases: Any) -> None:
    documento = casos()
    caso, i = _aclaracion(documento)
    caso["expect"]["phrases"] = frases
    assert f"BR5.8: casos[{i}]: expect.phrases no es una lista de frases aprobadas sin repetir" in validar(documento)


def test_una_aclaracion_valida_no_lleva_motivos_ni_frases() -> None:
    documento = casos()
    caso, i = _aclaracion(documento)
    caso["expect"]["valid"] = True
    assert validar(documento) == [f"BR5.8: casos[{i}]: una aclaración válida no lleva motivos ni frases"]
    caso["expect"] = {"valid": True, "reasons": ["cites_turn"], "phrases": []}
    assert validar(documento) == [f"BR5.8: casos[{i}]: una aclaración válida no lleva motivos ni frases"]
    caso["expect"] = {"valid": True, "reasons": [], "phrases": ["antes dijo"]}
    problemas = validar(documento)
    assert f"BR5.8: casos[{i}]: una aclaración válida no lleva motivos ni frases" in problemas


def test_una_aclaracion_invalida_lleva_un_motivo() -> None:
    documento = casos()
    caso, i = _aclaracion(documento)
    caso["expect"] = {"valid": False, "reasons": [], "phrases": []}
    assert validar(documento)[0] == f"BR5.8: casos[{i}]: una aclaración inválida lleva al menos un motivo"


def test_el_motivo_phrase_y_las_frases_van_juntos() -> None:
    documento = casos()
    caso, i = _aclaracion(documento)
    caso["expect"] = {"valid": False, "reasons": ["cites_turn"], "phrases": ["antes dijo"]}
    assert f"BR5.8: casos[{i}]: el motivo phrase exige frases y las frases el motivo phrase" in validar(documento)
    caso["expect"] = {"valid": False, "reasons": ["phrase"], "phrases": []}
    assert f"BR5.8: casos[{i}]: el motivo phrase exige frases y las frases el motivo phrase" in validar(documento)
    caso["expect"] = {"valid": False, "reasons": ["mentions_contradiction"], "phrases": []}
    assert validar(documento) == []


# ---------------------------------------------------------------- cobertura (E40)


@pytest.mark.parametrize("termino", TERMINOS)
def test_e40_un_termino_sin_caso_deja_la_suite_en_rojo(termino: str) -> None:
    documento = casos()
    documento["cases"] = [
        c for c in documento["cases"] if not (c["rule"] == "vocabulary" and termino in c["expect"]["matches"])
    ]
    problemas = validar(documento)
    assert f"BR5.8: ningún caso espera la coincidencia del término {termino}" in problemas
    assert len([p for p in problemas if "ningún caso espera" in p]) == 1


@pytest.mark.parametrize("frase", FRASES)
def test_una_frase_sin_caso_deja_la_suite_en_rojo(frase: str) -> None:
    documento = casos()
    documento["cases"] = [
        c for c in documento["cases"] if not (c["rule"] == "clarification" and frase in c["expect"]["phrases"])
    ]
    problemas = validar(documento)
    assert f"BR5.8: ningún caso rechaza la frase {frase}" in problemas
    assert len([p for p in problemas if "ningún caso rechaza" in p]) == 1


def test_un_caso_de_otra_regla_no_cubre_el_termino() -> None:
    """El caso que espera la coincidencia debe ser de la regla de vocabulario, no de aclaración."""
    documento = casos()
    documento["cases"] = [
        c for c in documento["cases"] if not (c["rule"] == "vocabulary" and "miente" in c["expect"]["matches"])
    ]
    clarificacion = uno(documento, "E30")
    clarificacion["expect"]["phrases"] = ["antes dijo"]
    assert "BR5.8: ningún caso espera la coincidencia del término miente" in validar(documento)


@pytest.mark.parametrize("origen", ORIGENES)
def test_un_escenario_sin_caso_deja_la_suite_en_rojo(origen: str) -> None:
    documento = casos()
    documento["cases"] = [c for c in documento["cases"] if c["source"] != origen]
    assert f"BR5.8: falta un caso de origen {origen}" in validar(documento)


def test_sin_casos_faltan_todos() -> None:
    documento = casos()
    documento["cases"] = []
    problemas = validar(documento)
    assert len(problemas) == len(TERMINOS) + len(FRASES) + len(ORIGENES)


# ---------------------------------------------------------------- aviso de testimonio


def datos_de_testimonio() -> dict[str, Any]:
    return copia(TESTIMONIO)  # type: ignore[no-any-return]


def validar_testimonio(documento: Any, palabras: int = 8) -> list[str]:
    return problemas_de_testimonio(documento, palabras)


def test_el_testimonio_versionado_pasa_y_trae_los_nueve_casos() -> None:
    documento = datos_de_testimonio()
    assert validar_testimonio(documento) == []
    assert documento["schema_version"] == "1.0.0"
    assert documento["synthetic"] is True
    assert documento["testimony_warning_words"] == 8
    assert documento["whitespace_code_points"] == [f"U+{c:04X}" for c in ESPACIOS]
    por_id = {c["id"]: c for c in documento["cases"]}
    assert set(por_id) >= set(REQUERIDOS) | {"casi-al-final-del-turno"}
    esperado = {
        "ocho-palabras": True,
        "siete-palabras": False,
        "dos-turnos": False,
        "al-final-del-turno": True,
        "casi-al-final-del-turno": False,
        "espacios-distintos": True,
        "u00a0": True,
        "u3000": True,
        "ufeff": False,
        "tabulador": True,
        "salto-de-linea": True,
    }
    for identificador, valor in esperado.items():
        assert por_id[identificador]["testimony_warning"] is valor, identificador


def test_la_lista_de_espacios_es_la_de_isspace() -> None:
    computada = [c for c in range(0x110000) if chr(c).isspace()]
    assert computada == ESPACIOS
    assert 0xFEFF not in ESPACIOS


def test_el_documento_de_testimonio_con_forma_incorrecta() -> None:
    assert validar_testimonio([]) == ["BR3.6: testimony-warning-cases no es un objeto"]
    documento = datos_de_testimonio()
    documento["extra"] = 1
    assert validar_testimonio(documento) == ["BR3.6: testimony-warning-cases trae claves de primer nivel no aprobadas"]
    documento = datos_de_testimonio()
    documento["schema_version"] = "1.1.0"
    assert validar_testimonio(documento) == ["BR3.6: schema_version de testimony-warning-cases debe ser 1.0.0"]
    for valor in (False, "true", 1):
        documento = datos_de_testimonio()
        documento["synthetic"] = valor
        assert validar_testimonio(documento) == ["BR3.6: synthetic debe ser true"]
    documento = datos_de_testimonio()
    documento["cases"] = "casos"
    assert validar_testimonio(documento) == ["BR3.6: cases no es una lista"]


@pytest.mark.parametrize("valor", [7, 9, "8", None, True])
def test_las_palabras_del_aviso_deben_ser_las_del_catalogo(valor: Any) -> None:
    documento = datos_de_testimonio()
    documento["testimony_warning_words"] = valor
    assert validar_testimonio(documento) == [
        "BR3.6: testimony_warning_words no es el del catálogo de límites (C25)"
    ]


def test_las_palabras_se_comparan_con_las_que_pasa_el_catalogo() -> None:
    documento = datos_de_testimonio()
    assert validar_testimonio(documento, 8) == []
    assert "testimony_warning_words" in validar_testimonio(documento, 9)[0]


def test_la_lista_de_espacios_debe_ser_la_de_isspace() -> None:
    mensaje = "BR3.6: whitespace_code_points no es la lista de str.isspace()"
    for cambio in (
        lambda lista: lista.remove("U+00A0"),
        lambda lista: lista.append("U+FEFF"),
        lambda lista: lista.reverse(),
        lambda lista: lista.__setitem__(0, "U+0009 "),
        lambda lista: lista.__setitem__(0, 9),
    ):
        documento = datos_de_testimonio()
        cambio(documento["whitespace_code_points"])
        assert validar_testimonio(documento) == [mensaje]
    documento = datos_de_testimonio()
    documento["whitespace_code_points"] = "U+0009"
    assert validar_testimonio(documento) == [mensaje]


def test_un_caso_de_testimonio_con_forma_incorrecta() -> None:
    documento = datos_de_testimonio()
    documento["cases"][0] = "texto"
    assert validar_testimonio(documento)[0] == "BR3.6: casos[0]: no es un objeto"
    for clave in ("id", "note", "turns", "testimony_warning"):
        documento = datos_de_testimonio()
        del documento["cases"][0][clave]
        assert validar_testimonio(documento)[0] == "BR3.6: casos[0]: claves no aprobadas", clave
    documento = datos_de_testimonio()
    documento["cases"][0]["extra"] = 1
    assert validar_testimonio(documento) == ["BR3.6: casos[0]: claves no aprobadas"]


@pytest.mark.parametrize("identificador", ["", "Mayuscula", "con_guion_bajo", 4])
def test_un_id_de_testimonio_que_no_es_identificador(identificador: Any) -> None:
    documento = datos_de_testimonio()
    documento["cases"][0]["id"] = identificador
    assert "BR3.6: casos[0]: id no es un identificador válido" in validar_testimonio(documento)


def test_un_id_de_testimonio_repetido() -> None:
    documento = datos_de_testimonio()
    documento["cases"][1]["id"] = documento["cases"][0]["id"]
    problemas = validar_testimonio(documento)
    assert "BR3.6: casos[1]: id repetido" in problemas


@pytest.mark.parametrize("nota", ["", None, 4, ["a"]])
def test_una_nota_vacia_o_que_no_es_texto(nota: Any) -> None:
    documento = datos_de_testimonio()
    documento["cases"][0]["note"] = nota
    assert validar_testimonio(documento)[0] == "BR3.6: casos[0]: note vacío o no es texto"


@pytest.mark.parametrize("turnos", [[], "texto", [""], [3], None])
def test_turnos_que_no_son_una_lista_de_textos(turnos: Any) -> None:
    documento = datos_de_testimonio()
    documento["cases"][0]["turns"] = turnos
    assert validar_testimonio(documento)[0] == "BR3.6: casos[0]: turns no es una lista no vacía de textos no vacíos"


@pytest.mark.parametrize("valor", [1, 0, "true", None])
def test_el_resultado_esperado_debe_ser_booleano(valor: Any) -> None:
    documento = datos_de_testimonio()
    documento["cases"][0]["testimony_warning"] = valor
    assert validar_testimonio(documento)[0] == "BR3.6: casos[0]: testimony_warning debe ser booleano"


def test_el_resultado_esperado_debe_concordar_con_la_regla() -> None:
    mensaje = "BR3.6: casos[{}]: el resultado esperado no concuerda con la regla de BR3.6"
    documento = datos_de_testimonio()
    for i, caso in enumerate(documento["cases"]):
        caso["testimony_warning"] = not caso["testimony_warning"]
        assert validar_testimonio(documento) == [mensaje.format(i)], caso["id"]
        caso["testimony_warning"] = not caso["testimony_warning"]


def test_la_regla_de_referencia_en_sus_bordes() -> None:
    documento = datos_de_testimonio()
    caso = documento["cases"][0]
    caso["note"] = "uno dos tres cuatro cinco seis siete ocho"
    caso["turns"] = ["otro uno dos tres cuatro cinco seis siete ocho y más"]
    caso["testimony_warning"] = True
    assert validar_testimonio(documento) == []
    caso["turns"] = ["uno dos tres cuatro cinco seis siete nueve"]
    caso["testimony_warning"] = False
    assert validar_testimonio(documento) == []
    caso["note"] = "uno dos tres cuatro cinco seis siete"
    caso["turns"] = ["uno dos tres cuatro cinco seis siete"]
    assert validar_testimonio(documento) == []
    caso["note"] = "x uno dos tres cuatro cinco seis siete ocho"
    caso["turns"] = ["nada", "uno dos tres cuatro cinco seis siete ocho"]
    caso["testimony_warning"] = True
    assert validar_testimonio(documento) == []
    caso["turns"] = ["uno dos tres cuatro", "cinco seis siete ocho"]
    caso["testimony_warning"] = False
    assert validar_testimonio(documento) == []
    # Con un umbral de 4 palabras, dos turnos de 4 palabras sí contienen la ventana de la nota.
    documento["testimony_warning_words"] = 4
    caso["turns"] = ["uno dos tres cuatro", "cinco seis siete ocho"]
    caso["testimony_warning"] = True
    problemas = validar_testimonio(documento, 4)
    assert "BR3.6: casos[0]: el resultado esperado no concuerda con la regla de BR3.6" not in problemas


@pytest.mark.parametrize("identificador", list(REQUERIDOS))
def test_un_caso_requerido_ausente(identificador: str) -> None:
    documento = datos_de_testimonio()
    documento["cases"] = [c for c in documento["cases"] if c["id"] != identificador]
    assert f"BR3.6: falta el caso {identificador}" in validar_testimonio(documento)


@pytest.mark.parametrize("identificador", [i for i, c in REQUERIDOS.items() if c is not None])
def test_un_caso_que_nombra_un_caracter_debe_traerlo(identificador: str) -> None:
    documento = datos_de_testimonio()
    caso = next(c for c in documento["cases"] if c["id"] == identificador)
    posicion = documento["cases"].index(caso)
    caracter = REQUERIDOS[identificador]
    assert caracter is not None
    caso["note"] = caso["note"].replace(caracter, " ")
    caso["testimony_warning"] = identificador != "ufeff"
    assert (
        f"BR3.6: casos[{posicion}]: la nota no contiene el carácter que su id nombra"
        in validar_testimonio(documento)
    )


def test_ufeff_no_separa_palabras_y_u00a0_si() -> None:
    documento = datos_de_testimonio()
    por_id = {c["id"]: c for c in documento["cases"]}
    assert "﻿" in por_id["ufeff"]["note"] and len(por_id["ufeff"]["note"].split()) < 8
    assert " " in por_id["u00a0"]["note"] and len(por_id["u00a0"]["note"].split()) >= 8


def test_los_datos_de_testimonio_no_traen_secuencias_largas_de_digitos() -> None:
    documento = datos_de_testimonio()
    documento["cases"][0]["note"] = "caso 1234567 de la nota"
    assert "BR3.6: casos[0]: note o turns traen una secuencia de seis o más dígitos" in validar_testimonio(documento)
    documento = datos_de_testimonio()
    documento["cases"][0]["turns"] = ["turno 12 34 56"]
    assert "BR3.6: casos[0]: note o turns traen una secuencia de seis o más dígitos" in validar_testimonio(documento)


# ---------------------------------------------------------------- comprobar sobre un árbol


def _arbol(destino: Path) -> Path:
    shutil.copytree(CONTRACTS_ROOT / "integrity", destino / "integrity", ignore=shutil.ignore_patterns("fixtures"))
    shutil.copy(CONTRACTS_ROOT / LIMITES, destino / LIMITES)
    return destino


def _escribir(raiz: Path, relativa: str, documento: Any) -> None:
    ruta = raiz / relativa
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(documento, ensure_ascii=False), encoding="utf-8")


def test_el_arbol_copiado_pasa(tmp_path: Path) -> None:
    assert comprobar(_arbol(tmp_path)) == []


def test_un_defecto_sembrado_en_los_casos_de_escaneo_se_ve(tmp_path: Path) -> None:
    raiz = _arbol(tmp_path)
    documento = casos()
    documento["cases"] = [c for c in documento["cases"] if "mentirosa" not in c["expect"].get("matches", [])]
    _escribir(raiz, CASOS, documento)
    assert comprobar(raiz) == ["BR5.8: ningún caso espera la coincidencia del término mentirosa"]


def test_un_defecto_sembrado_en_el_testimonio_se_ve(tmp_path: Path) -> None:
    raiz = _arbol(tmp_path)
    documento = datos_de_testimonio()
    documento["cases"] = [c for c in documento["cases"] if c["id"] != "u3000"]
    _escribir(raiz, TESTIMONIO, documento)
    assert comprobar(raiz) == ["BR3.6: falta el caso u3000"]


def test_las_palabras_salen_del_catalogo_de_limites(tmp_path: Path) -> None:
    raiz = _arbol(tmp_path)
    limites = copia(LIMITES)
    limites["limits"]["testimony_warning_words"]["value"] = 9
    _escribir(raiz, LIMITES, limites)
    problemas = comprobar(raiz)
    assert problemas[0] == "BR3.6: testimony_warning_words no es el del catálogo de límites (C25)"
    assert any("no concuerda con la regla de BR3.6" in p for p in problemas)


@pytest.mark.parametrize(
    "limites",
    [
        [],
        {},
        {"limits": []},
        {"limits": {}},
        {"limits": {"testimony_warning_words": 8}},
        {"limits": {"testimony_warning_words": {}}},
        {"limits": {"testimony_warning_words": {"value": "ocho"}}},
    ],
)
def test_un_catalogo_sin_el_limite_es_un_problema(tmp_path: Path, limites: Any) -> None:
    raiz = _arbol(tmp_path)
    _escribir(raiz, LIMITES, limites)
    problemas = comprobar(raiz)
    assert problemas[0] == "BR3.6: testimony_warning_words no es el del catálogo de límites (C25)"


@pytest.mark.parametrize("relativa", [CASOS, TESTIMONIO, LIMITES])
def test_un_archivo_ausente_o_ilegible_se_informa_sin_su_contenido(tmp_path: Path, relativa: str) -> None:
    raiz = _arbol(tmp_path)
    (raiz / relativa).unlink()
    assert f"{relativa}: ausente o ilegible" in comprobar(raiz)
    (raiz / relativa).write_text(f"{CANARIO}: [1", encoding="utf-8")
    problemas = comprobar(raiz)
    assert f"{relativa}: ausente o ilegible" in problemas
    assert CANARIO not in "".join(problemas)


def test_los_mensajes_no_llevan_texto_del_documento(tmp_path: Path) -> None:
    raiz = _arbol(tmp_path)
    documento = casos()
    primero = documento["cases"][0]
    primero["id"] = CANARIO.upper()
    primero["source"] = CANARIO
    primero["text"] = f"{CANARIO} 1234567890"
    primero["literal_sources"] = [CANARIO, ""]
    primero["expect"] = {"matches": [CANARIO], "excluded": [CANARIO]}
    documento["cases"][1]["field"] = CANARIO
    documento["cases"][2]["rule"] = CANARIO
    documento["cases"][3]["expect"] = {CANARIO: CANARIO}
    _escribir(raiz, CASOS, documento)
    pruebas = datos_de_testimonio()
    pruebas["cases"][0]["id"] = CANARIO.upper()
    pruebas["cases"][1]["note"] = f"{CANARIO} 1234567890"
    pruebas["cases"][2]["turns"] = [CANARIO, 3]
    _escribir(raiz, TESTIMONIO, pruebas)
    problemas = comprobar(raiz)
    assert len(problemas) >= 8
    assert CANARIO not in "".join(problemas)
    assert CANARIO.upper() not in "".join(problemas)
