"""Guardia del reporte de la CLI C19 v2 (BR10.1, BR10.2, NFR1.4; E28, E29; FD-U1-03, FD-U1-05).

Los controles negativos trabajan sobre copias en memoria o en `tmp_path`, nunca sobre el contrato
versionado. Cada constante, cada lista cerrada y cada patrón de la guardia tiene un control que
falla si se cambia.
"""

import copy
import json
import re
import shutil
from pathlib import Path
from typing import Any

import pytest
from helpers import CONTRACTS_ROOT, errores_de, load_contract, validador_de

from veridicus_contracts.checks import report_closed as guardia
from veridicus_contracts.checks.report_closed import (
    C19,
    DIRECTORIO_DE_FIXTURES,
    FIXTURES_NEGATIVOS,
    LIMITE_DECLARADO_DEL_CANARY,
    MAXIMO_COSTO,
    MAXIMO_ENTERO,
    MODELO_DE_LLAMADA,
    PALABRA_DEL_CANARY,
    PAPELES,
    campos_que_admiten_una_palabra,
    comprobar,
    comprobar_documentos,
)

pytestmark = pytest.mark.c19


def _documentos() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Copia en memoria de C19, de `model-call.v1` y de los tres fixtures negativos."""
    reporte = copy.deepcopy(load_contract(C19))
    llamada = copy.deepcopy(load_contract(MODELO_DE_LLAMADA))
    fixtures = {
        nombre: copy.deepcopy(load_contract(f"{DIRECTORIO_DE_FIXTURES}/{nombre}"))
        for nombre in FIXTURES_NEGATIVOS
    }
    return reporte, llamada, fixtures


def _problemas(reporte: Any, llamada: Any, fixtures: Any) -> list[str]:
    return comprobar_documentos(reporte, llamada, fixtures)


# --- Constantes y listas cerradas -------------------------------------------------------------


def test_las_constantes_de_la_guardia_son_las_del_contrato() -> None:
    assert MAXIMO_ENTERO == 9007199254740991
    assert MAXIMO_COSTO == 1_000_000_000
    assert PAPELES == frozenset({"judge", "verifier", "verifier_permuted"})
    assert dict(FIXTURES_NEGATIVOS) == {
        "report.role-prueba-a.json": "BR10.2",
        "report.testimony-in-model.json": "BR10.1",
        "report.testimony-in-price-table.json": "BR10.1",
    }
    assert C19 == "cli/report.schema.v2.yaml"
    assert MODELO_DE_LLAMADA == "model_calls/model-call.v1.yaml"
    assert DIRECTORIO_DE_FIXTURES == "cli/fixtures"
    assert PALABRA_DEL_CANARY == "CANARIO-7f3a"
    assert "FD-U1-05" in LIMITE_DECLARADO_DEL_CANARY
    assert "U12" in LIMITE_DECLARADO_DEL_CANARY


def test_el_contrato_versionado_pasa_la_guardia() -> None:
    assert comprobar(CONTRACTS_ROOT) == []
    reporte, llamada, fixtures = _documentos()
    assert _problemas(reporte, llamada, fixtures) == []


def test_la_guardia_es_pura_y_no_modifica_sus_entradas() -> None:
    reporte, llamada, fixtures = _documentos()
    antes = copy.deepcopy((reporte, llamada, fixtures))
    _problemas(reporte, llamada, fixtures)
    assert (reporte, llamada, fixtures) == antes


# --- Cadenas (BR10.1, E29) ---------------------------------------------------------------------


def test_cada_cadena_del_reporte_lleva_su_tope_y_su_marca_de_limite() -> None:
    """Control positivo: todo patrón del reporte tiene maxLength 128 y la marca del límite."""
    reporte, _, _ = _documentos()
    patrones = [
        nodo
        for nodo in _nodos(reporte)
        if isinstance(nodo, dict) and isinstance(nodo.get("pattern"), str)
    ]
    assert len(patrones) >= 6
    for nodo in patrones:
        assert nodo["maxLength"] == 128
        assert nodo["x-veridicus-limit"] == "report_token_max_chars"


def _nodos(nodo: Any) -> list[Any]:
    salida = [nodo]
    hijos = nodo.values() if isinstance(nodo, dict) else nodo if isinstance(nodo, list) else []
    for hijo in hijos:
        salida.extend(_nodos(hijo))
    return salida


def test_una_cadena_sin_enum_const_ni_patron_queda_en_rojo() -> None:
    reporte, llamada, fixtures = _documentos()
    reporte["$defs"]["token"] = {"type": "string", "maxLength": 128}
    assert _problemas(reporte, llamada, fixtures) == [
        "BR10.1 $.$defs.token: cadena abierta (sin enum, const, formato ni patrón)"
    ]


def test_una_propiedad_sin_tipo_queda_en_rojo() -> None:
    reporte, llamada, fixtures = _documentos()
    reporte["properties"]["libre"] = {"description": "cualquier cosa"}
    assert _problemas(reporte, llamada, fixtures) == [
        "BR10.1 $.properties.libre: propiedad sin tipo, $ref, enum ni const"
    ]


@pytest.mark.parametrize("composicion", ["$ref", "enum", "const", "allOf", "anyOf", "oneOf"])
def test_una_propiedad_con_composicion_no_cuenta_como_sin_tipo(composicion: str) -> None:
    reporte, llamada, fixtures = _documentos()
    cerrada = [{"type": "string", "enum": ["a"]}]
    reporte["properties"]["extra"] = {
        composicion: cerrada if composicion in ("allOf", "anyOf", "oneOf") else ["a"]
    }
    problemas = [p for p in _problemas(reporte, llamada, fixtures) if "sin tipo" in p]
    assert problemas == []


def test_un_patron_que_admite_espacios_queda_en_rojo() -> None:
    reporte, llamada, fixtures = _documentos()
    for patron in ("^[A-Za-z0-9 ]{1,128}$", r"^\s*[a-z]{1,128}$", r"^[a-z\s]{1,128}$"):
        reporte["$defs"]["token"]["pattern"] = patron
        assert _problemas(reporte, llamada, fixtures) == [
            "BR10.1 $.$defs.token: el patrón admite espacios"
        ], patron


def test_un_patron_sin_anclas_queda_en_rojo() -> None:
    reporte, llamada, fixtures = _documentos()
    for patron in ("[a-z]{1,128}$", "^[a-z]{1,128}", "[a-z]{1,128}"):
        reporte["$defs"]["token"]["pattern"] = patron
        assert _problemas(reporte, llamada, fixtures) == [
            "BR10.1 $.$defs.token: el patrón no está anclado con ^ y $"
        ], patron


def test_una_cadena_sin_maxlength_o_con_uno_mayor_a_128_queda_en_rojo() -> None:
    reporte, llamada, fixtures = _documentos()
    del reporte["$defs"]["token"]["maxLength"]
    esperado = [
        "BR10.1 $.$defs.token: maxLength ausente o mayor que 128",
        "BR10.1 $.$defs.token: maxLength distinto de 128",
    ]
    assert _problemas(reporte, llamada, fixtures) == esperado[:1]
    reporte["$defs"]["token"]["maxLength"] = 129
    assert _problemas(reporte, llamada, fixtures) == esperado[:1]
    reporte["$defs"]["token"]["maxLength"] = 64
    assert _problemas(reporte, llamada, fixtures) == esperado[1:]
    reporte["$defs"]["token"]["maxLength"] = 128
    assert _problemas(reporte, llamada, fixtures) == []


def test_una_cadena_del_reporte_sin_la_marca_del_limite_queda_en_rojo() -> None:
    reporte, llamada, fixtures = _documentos()
    del reporte["$defs"]["token"]["x-veridicus-limit"]
    assert _problemas(reporte, llamada, fixtures) == [
        "BR10.1 $.$defs.token: falta x-veridicus-limit: report_token_max_chars"
    ]
    reporte["$defs"]["token"]["x-veridicus-limit"] = "otro_limite"
    assert _problemas(reporte, llamada, fixtures) == [
        "BR10.1 $.$defs.token: falta x-veridicus-limit: report_token_max_chars"
    ]


def test_una_cadena_de_model_call_no_exige_la_marca_pero_si_el_tope() -> None:
    """`model-call.v1` lleva la marca `report_token_max_chars` (E-15, P-T15b-2); el reporte no se la exige a esa cadena, pero sí cerrada y con tope de 128 como mucho."""
    reporte, llamada, fixtures = _documentos()
    assert llamada["$defs"]["token"]["x-veridicus-limit"] == "report_token_max_chars"
    llamada["$defs"]["token"]["maxLength"] = 200
    assert _problemas(reporte, llamada, fixtures) == [
        "BR10.1 model-call $.$defs.token: maxLength ausente o mayor que 128"
    ]
    llamada["$defs"]["token"]["maxLength"] = 128
    llamada["properties"]["role"]["pattern"] = "^[a-z ]{1,31}$"
    assert _problemas(reporte, llamada, fixtures) == [
        "BR10.1 model-call $.properties.role: el patrón admite espacios"
    ]


def test_un_valor_de_enum_o_const_con_espacios_o_demasiado_largo_queda_en_rojo() -> None:
    reporte, llamada, fixtures = _documentos()
    esperado = [
        "BR10.1 $.properties.kind: un valor de enum o const lleva espacios o pasa de 128 caracteres"
    ]
    reporte["properties"]["kind"] = {"enum": ["run", "una frase"]}
    assert _problemas(reporte, llamada, fixtures) == esperado
    reporte["properties"]["kind"] = {"enum": ["run", "x" * 129]}
    assert _problemas(reporte, llamada, fixtures) == esperado
    reporte["properties"]["kind"] = {"const": "una frase"}
    assert _problemas(reporte, llamada, fixtures) == esperado
    reporte["properties"]["kind"] = {"enum": ["run", "x" * 128]}
    assert _problemas(reporte, llamada, fixtures) == []
    reporte["properties"]["kind"] = {"enum": ["run", 7]}
    assert _problemas(reporte, llamada, fixtures) == []


def test_el_formato_date_time_solo_cierra_una_cadena_de_model_call() -> None:
    """`model-call.v1` (de T08) cierra `at` con el formato; el reporte exige patrón, tope y marca (F-04)."""
    reporte, llamada, fixtures = _documentos()
    assert llamada["properties"]["at"] == {
        "type": "string",
        "format": "date-time",
        "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$",
        "maxLength": 128,
        "x-veridicus-limit": "report_token_max_chars",
    }
    assert _problemas(reporte, llamada, fixtures) == []
    reporte["properties"]["created_at"] = {"type": "string", "format": "date-time"}
    assert _problemas(reporte, llamada, fixtures) == [
        "BR10.1 $.properties.created_at: cadena abierta (sin enum, const, formato ni patrón)"
    ]
    llamada["properties"]["at"] = {"type": "string", "format": "uri"}
    assert len(_problemas(*_documentos_con(llamada=llamada))) == 1


def _documentos_con(llamada: Any) -> tuple[Any, Any, Any]:
    reporte, _, fixtures = _documentos()
    return reporte, llamada, fixtures


def test_created_at_lleva_patron_rfc3339_tope_y_marca() -> None:
    reporte, llamada, fixtures = _documentos()
    campo = reporte["properties"]["created_at"]
    assert campo["maxLength"] == 128
    assert campo["x-veridicus-limit"] == "report_token_max_chars"
    del campo["maxLength"]
    del campo["x-veridicus-limit"]
    assert _problemas(reporte, llamada, fixtures) == [
        "BR10.1 $.properties.created_at: maxLength ausente o mayor que 128",
        "BR10.1 $.properties.created_at: falta x-veridicus-limit: report_token_max_chars",
    ]


def test_una_cadena_en_una_lista_de_tipos_se_comprueba() -> None:
    reporte, llamada, fixtures = _documentos()
    reporte["$defs"]["token"] = {"type": ["string", "null"], "maxLength": 128}
    assert _problemas(reporte, llamada, fixtures) == [
        "BR10.1 $.$defs.token: cadena abierta (sin enum, const, formato ni patrón)"
    ]
    reporte["$defs"]["token"] = {"type": ["null", 3], "maxLength": 128}
    assert _problemas(reporte, llamada, fixtures) == []


def test_un_objeto_abierto_queda_en_rojo() -> None:
    reporte, llamada, fixtures = _documentos()
    esperado = ["BR10.1 $: objeto sin additionalProperties cerrado"]
    reporte["additionalProperties"] = True
    assert _problemas(reporte, llamada, fixtures) == esperado
    del reporte["additionalProperties"]
    assert _problemas(reporte, llamada, fixtures) == esperado
    reporte["additionalProperties"] = {"type": "integer", "minimum": 0, "maximum": 5}
    assert _problemas(reporte, llamada, fixtures) == [SIN_NOMBRES.format(sitio="$")]
    reporte["propertyNames"] = {"enum": ["a"]}
    assert _problemas(reporte, llamada, fixtures) == []


# --- Enteros y números (NFR1.4) ---------------------------------------------------------------


_SIN_TOPE = "NFR1.4 {sitio}: {tipo} sin minimum o maximum acotados"
SIN_NOMBRES = "BR10.1 {sitio}: additionalProperties sin propertyNames cerrado (enum o const)"
ABIERTO = "BR10.1 {sitio}: esquema abierto (acepta cualquier valor)"
ESPACIOS = "BR10.1 $.$defs.token: el patrón admite espacios"
CONSTRUCCIONES = (
    "BR10.1 $.$defs.token: el patrón sale de la gramática cerrada (anclas, clases con rangos de "
    "A-Za-z0-9, \\., \\-, \\+, ( ) | ?, cuantificadores)"
)


def _entero(reporte: dict[str, Any]) -> dict[str, Any]:
    """El primer entero del reporte (siempre con tope en el contrato versionado)."""
    for nodo in _nodos(reporte):
        if isinstance(nodo, dict) and nodo.get("type") == "integer":
            return nodo
    raise AssertionError("el reporte no tiene enteros")


def _sitio_del_entero(reporte: dict[str, Any]) -> str:
    objetivo = _entero(reporte)
    return _buscar(reporte, objetivo, "$")


def _buscar(nodo: Any, objetivo: Any, ruta: str) -> str:
    if nodo is objetivo:
        return ruta
    if isinstance(nodo, dict):
        for clave, hijo in nodo.items():
            hallado = _buscar(hijo, objetivo, f"{ruta}.{clave}")
            if hallado:
                return hallado
    elif isinstance(nodo, list):
        for indice, hijo in enumerate(nodo):
            hallado = _buscar(hijo, objetivo, f"{ruta}[{indice}]")
            if hallado:
                return hallado
    return ""


@pytest.mark.parametrize(
    "cambio",
    [
        pytest.param(lambda n: n.pop("maximum"), id="sin-maximum"),
        pytest.param(lambda n: n.pop("minimum"), id="sin-minimum"),
        pytest.param(lambda n: n.update(maximum=MAXIMO_ENTERO + 1), id="maximum-2-53"),
        pytest.param(lambda n: n.update(minimum=-1), id="minimum-negativo"),
        pytest.param(lambda n: n.update(maximum="9"), id="maximum-texto"),
        pytest.param(lambda n: n.update(minimum=True), id="minimum-booleano"),
        pytest.param(lambda n: n.update(minimum=5, maximum=4), id="minimum-mayor-que-maximum"),
    ],
)
def test_un_entero_sin_tope_valido_queda_en_rojo(cambio: Any) -> None:
    reporte, llamada, fixtures = _documentos()
    sitio = _sitio_del_entero(reporte)
    cambio(_entero(reporte))
    assert _problemas(reporte, llamada, fixtures) == [_SIN_TOPE.format(sitio=sitio, tipo="entero")]


def test_un_entero_en_el_limite_exacto_pasa() -> None:
    reporte, llamada, fixtures = _documentos()
    _entero(reporte).update(minimum=0, maximum=MAXIMO_ENTERO)
    assert _problemas(reporte, llamada, fixtures) == []


def test_un_entero_de_model_call_se_comprueba_y_seed_admite_negativos() -> None:
    reporte, llamada, fixtures = _documentos()
    assert llamada["properties"]["seed"]["minimum"] == -MAXIMO_ENTERO
    assert _problemas(reporte, llamada, fixtures) == []
    llamada["properties"]["seed"]["minimum"] = -MAXIMO_ENTERO - 1
    assert _problemas(reporte, llamada, fixtures) == [
        _SIN_TOPE.format(sitio="model-call $.properties.seed", tipo="entero")
    ]
    llamada["properties"]["seed"]["minimum"] = -MAXIMO_ENTERO
    del llamada["properties"]["seed"]["maximum"]
    assert len(_problemas(reporte, llamada, fixtures)) == 1
    llamada["properties"]["seed"] = {"type": "integer", "minimum": 0, "maximum": 5}
    assert _problemas(reporte, llamada, fixtures) == []
    llamada["properties"]["input_tokens"] = {"type": "integer", "minimum": -1, "maximum": 5}
    assert _problemas(reporte, llamada, fixtures) == [
        _SIN_TOPE.format(sitio="model-call $.properties.input_tokens", tipo="entero")
    ]


def test_el_costo_estimado_llega_a_mil_millones_y_ningun_numero_pasa_de_ahi() -> None:
    reporte, llamada, fixtures = _documentos()
    costo = reporte["properties"]["totals"]["properties"]["estimated_cost"]
    assert costo["type"] == "number"
    assert costo["minimum"] == 0
    assert costo["maximum"] == MAXIMO_COSTO
    sitio = "$.properties.totals.properties.estimated_cost"
    for maximo in (MAXIMO_COSTO + 1, "x", None):
        costo["maximum"] = maximo
        if maximo is None:
            del costo["maximum"]
        assert _problemas(reporte, llamada, fixtures) == [
            _SIN_TOPE.format(sitio=sitio, tipo="número")
        ], maximo
    costo["maximum"] = MAXIMO_COSTO
    costo["minimum"] = -0.5
    assert _problemas(reporte, llamada, fixtures) == [_SIN_TOPE.format(sitio=sitio, tipo="número")]
    del costo["minimum"]
    assert len(_problemas(reporte, llamada, fixtures)) == 1


def test_las_metricas_son_numeros_entre_cero_y_uno_o_enteros_acotados() -> None:
    reporte, _, _ = _documentos()
    metricas = reporte["properties"]["metrics"]["properties"]
    assert set(metricas) == {
        "verified_quotes",
        "json_format_errors",
        "permutation_coverage",
        "anonymizer_leaks",
        "completed_runs",
        "precision",
        "recall",
        "reversed_order_consistency",
        "three_run_agreement",
        "type_agreement",
        "scenario_a_marker_hits",
        "scenario_a_difference",
    }


# --- Papel de las llamadas (BR10.2, E28) -------------------------------------------------------


def _llamadas(reporte: dict[str, Any]) -> dict[str, Any]:
    return dict(
        reporte["properties"]["runs"]["items"]["properties"]["calls"]["items"],
    )


def test_las_llamadas_referencian_model_call_y_restringen_el_papel() -> None:
    reporte, _, _ = _documentos()
    llamadas = _llamadas(reporte)
    assert {"$ref": "/veridicus/contracts/model_calls/model-call.v1"} in llamadas["allOf"]
    restriccion = next(b for b in llamadas["allOf"] if "properties" in b)
    assert set(restriccion["properties"]["role"]["enum"]) == PAPELES
    assert len(restriccion["properties"]["role"]["enum"]) == 3


def test_sin_el_allof_de_papeles_queda_en_rojo() -> None:
    reporte, llamada, fixtures = _documentos()
    destino = reporte["properties"]["runs"]["items"]["properties"]["calls"]
    esperado = [
        (
            "BR10.2 $.properties.runs.items.properties.calls.items: "
            "las llamadas no restringen el papel a judge, verifier y verifier_permuted"
        )
    ]
    referencia = {"$ref": "/veridicus/contracts/model_calls/model-call.v1"}
    destino["items"] = {"allOf": [referencia]}
    assert _problemas(reporte, llamada, fixtures) == esperado
    destino["items"] = referencia
    assert len(_problemas(reporte, llamada, fixtures)) == 2
    destino["items"] = {"allOf": "no es una lista"}
    problemas = _problemas(reporte, llamada, fixtures)
    assert len(problemas) == 3
    assert problemas[0].endswith("esquema abierto (acepta cualquier valor)")


@pytest.mark.parametrize(
    "papeles",
    [
        ["judge", "verifier"],
        ["judge", "verifier", "verifier_permuted", "prueba_a"],
        ["judge", "verifier", "prueba_a"],
        ["judge", "judge", "verifier"],
        "judge",
    ],
)
def test_un_conjunto_de_papeles_distinto_de_los_tres_queda_en_rojo(papeles: Any) -> None:
    reporte, llamada, fixtures = _documentos()
    restriccion = next(b for b in _llamadas_vivas(reporte)["allOf"] if "properties" in b)
    restriccion["properties"]["role"]["enum"] = papeles
    problemas = _problemas(reporte, llamada, fixtures)
    assert len(problemas) == 1
    assert problemas[0].startswith("BR10.2 ")


def _llamadas_vivas(reporte: dict[str, Any]) -> dict[str, Any]:
    return reporte["properties"]["runs"]["items"]["properties"]["calls"]["items"]  # type: ignore[no-any-return]


def test_sin_la_referencia_a_model_call_queda_en_rojo() -> None:
    reporte, llamada, fixtures = _documentos()
    llamadas = _llamadas_vivas(reporte)
    llamadas["allOf"] = [b for b in llamadas["allOf"] if "properties" in b]
    assert _problemas(reporte, llamada, fixtures) == [
        ABIERTO.format(sitio="$.properties.runs.items.properties.calls.items"),
        (
            "BR10.2 $.properties.runs.items.properties.calls.items: "
            "las llamadas no referencian model-call.v1"
        ),
    ]
    llamadas["allOf"] = [{"$ref": "otra-cosa"}, *llamadas["allOf"]]
    assert len(_problemas(reporte, llamada, fixtures)) == 1


def test_un_reporte_sin_llamadas_tampoco_pasa_en_vacio() -> None:
    reporte, llamada, fixtures = _documentos()
    del reporte["properties"]["runs"]
    problemas = _problemas(reporte, llamada, fixtures)
    assert problemas == ["BR10.2: el reporte no declara runs[].calls[]"]
    reporte["properties"]["runs"] = []
    assert _problemas(reporte, llamada, fixtures) == problemas


# --- Sección clarifications (solo enteros) ----------------------------------------------------


def test_clarifications_es_opcional_y_solo_lleva_enteros() -> None:
    reporte, llamada, fixtures = _documentos()
    assert "clarifications" in reporte["properties"]
    assert "clarifications" not in reporte["required"]
    clarifications = reporte["properties"]["clarifications"]
    clarifications["properties"]["nota"] = {"type": "boolean"}
    assert _problemas(reporte, llamada, fixtures) == [
        "BR10.1 $.properties.clarifications.properties.nota: clarifications solo admite enteros"
    ]
    clarifications["properties"]["nota"] = {"type": "string", "enum": ["a"]}
    assert len(_problemas(reporte, llamada, fixtures)) == 1
    clarifications["properties"]["nota"] = {"$ref": "#/$defs/token"}
    assert len(_problemas(reporte, llamada, fixtures)) == 1
    for referencia in ("#/$defs/no-existe", "#/otra/parte", "/externa"):
        clarifications["properties"]["nota"] = {"$ref": referencia}
        assert _problemas(reporte, llamada, fixtures) == [
            "BR10.1 $.properties.clarifications.properties.nota: clarifications solo admite enteros"
        ], referencia
    clarifications["properties"]["nota"] = {"$ref": "#/$defs/count"}
    assert _problemas(reporte, llamada, fixtures) == []
    del clarifications["properties"]["nota"]
    assert _problemas(reporte, llamada, fixtures) == []
    clarifications["properties"]["discarded"]["additionalProperties"] = {"type": "boolean"}
    assert _problemas(reporte, llamada, fixtures) == [
        (
            "BR10.1 $.properties.clarifications.properties.discarded.additionalProperties: "
            "clarifications solo admite enteros"
        )
    ]
    clarifications["properties"]["discarded"]["additionalProperties"] = {
        "type": "integer",
        "minimum": 0,
        "maximum": 9,
    }
    assert _problemas(reporte, llamada, fixtures) == []


def test_clarifications_debe_existir_ser_objeto_y_ser_opcional() -> None:
    reporte, llamada, fixtures = _documentos()
    original = reporte["properties"]["clarifications"]
    del reporte["properties"]["clarifications"]
    assert _problemas(reporte, llamada, fixtures) == [
        "BR10.1: el reporte no declara la sección clarifications"
    ]
    reporte["properties"]["clarifications"] = original
    reporte["required"].append("clarifications")
    assert _problemas(reporte, llamada, fixtures) == [
        "BR10.1 $.properties.clarifications: la sección clarifications debe ser opcional"
    ]
    reporte["required"].remove("clarifications")
    reporte["properties"]["clarifications"] = {"type": "integer", "minimum": 0, "maximum": 3}
    assert _problemas(reporte, llamada, fixtures) == [
        "BR10.1 $.properties.clarifications: la sección clarifications debe ser un objeto"
    ]


# --- Fixtures negativos -----------------------------------------------------------------------


@pytest.mark.parametrize("nombre", sorted(FIXTURES_NEGATIVOS))
def test_un_fixture_negativo_ausente_queda_en_rojo(nombre: str) -> None:
    reporte, llamada, fixtures = _documentos()
    del fixtures[nombre]
    assert _problemas(reporte, llamada, fixtures) == [
        f"E28/E29: falta el fixture negativo {nombre}"
    ]


@pytest.mark.parametrize("nombre", sorted(FIXTURES_NEGATIVOS))
def test_un_fixture_que_no_se_rechaza_por_su_regla_queda_en_rojo(nombre: str) -> None:
    reporte, llamada, fixtures = _documentos()
    regla = FIXTURES_NEGATIVOS[nombre]
    fixtures[nombre]["expectation"] = "accept"
    esperado = [f"E28/E29: {nombre} debe rechazarse con reject_reason {regla}"]
    assert _problemas(reporte, llamada, fixtures) == esperado
    fixtures[nombre]["expectation"] = "reject"
    fixtures[nombre]["reject_reason"] = "BR0.0"
    assert _problemas(reporte, llamada, fixtures) == esperado
    fixtures[nombre]["reject_reason"] = regla
    assert _problemas(reporte, llamada, fixtures) == []
    fixtures[nombre] = "texto suelto"
    assert _problemas(reporte, llamada, fixtures) == [
        f"E28/E29: el fixture {nombre} no es un fixture con payload"
    ]
    fixtures[nombre] = {"payload": "no es un objeto", "expectation": "reject"}
    assert _problemas(reporte, llamada, fixtures) == [
        f"E28/E29: el fixture {nombre} no es un fixture con payload"
    ]


# --- Entrada principal: archivos reales y defecto sembrado en tmp_path ------------------------


def _copiar_raiz(destino: Path) -> Path:
    for relativa in (C19, MODELO_DE_LLAMADA):
        (destino / relativa).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(CONTRACTS_ROOT / relativa, destino / relativa)
    carpeta = destino / DIRECTORIO_DE_FIXTURES
    carpeta.mkdir(parents=True, exist_ok=True)
    for nombre in FIXTURES_NEGATIVOS:
        shutil.copy(CONTRACTS_ROOT / DIRECTORIO_DE_FIXTURES / nombre, carpeta / nombre)
    return destino


def test_comprobar_sobre_una_copia_intacta_pasa(tmp_path: Path) -> None:
    assert comprobar(_copiar_raiz(tmp_path)) == []


def test_comprobar_ve_un_defecto_sembrado_en_el_archivo(tmp_path: Path) -> None:
    """No pasa en vacío: un patrón con espacios sembrado en la copia en disco se detecta."""
    raiz = _copiar_raiz(tmp_path)
    ruta = raiz / C19
    texto = ruta.read_text(encoding="utf-8")
    assert "report_token_max_chars" in texto
    sembrado = texto.replace("^[A-Za-z0-9._:/@+-]{1,128}$", "^[A-Za-z0-9 ._:/@+-]{1,128}$", 1)
    assert sembrado != texto
    ruta.write_text(sembrado, encoding="utf-8")
    assert comprobar(raiz) == ["BR10.1 $.$defs.token: el patrón admite espacios"]


def test_comprobar_ve_un_fixture_sembrado_en_el_archivo(tmp_path: Path) -> None:
    raiz = _copiar_raiz(tmp_path)
    ruta = raiz / DIRECTORIO_DE_FIXTURES / "report.role-prueba-a.json"
    fixture = json.loads(ruta.read_text(encoding="utf-8"))
    fixture["expectation"] = "accept"
    ruta.write_text(json.dumps(fixture), encoding="utf-8")
    assert comprobar(raiz) == [
        "E28/E29: report.role-prueba-a.json debe rechazarse con reject_reason BR10.2"
    ]


def test_comprobar_informa_de_los_archivos_ausentes_ilegibles_o_mal_formados(
    tmp_path: Path,
) -> None:
    assert comprobar(tmp_path)[0].startswith("C19 ilegible o ausente")
    raiz = _copiar_raiz(tmp_path / "a")
    (raiz / C19).write_text("[1, 2", encoding="utf-8")
    assert comprobar(raiz)[0].startswith("C19 ilegible o ausente")
    (raiz / C19).write_text("[]", encoding="utf-8")
    assert comprobar(raiz) == ["C19 no es un objeto JSON"]
    raiz = _copiar_raiz(tmp_path / "b")
    (raiz / MODELO_DE_LLAMADA).unlink()
    assert comprobar(raiz)[0].startswith("model-call.v1 ilegible o ausente")
    (raiz / MODELO_DE_LLAMADA).write_text("[]", encoding="utf-8")
    assert comprobar(raiz) == ["model-call.v1 no es un objeto JSON"]
    raiz = _copiar_raiz(tmp_path / "c")
    (raiz / DIRECTORIO_DE_FIXTURES / "report.role-prueba-a.json").write_text(
        "{: roto", encoding="utf-8"
    )
    assert comprobar(raiz) == [
        "E28/E29: el fixture report.role-prueba-a.json no es un fixture con payload"
    ]
    (raiz / DIRECTORIO_DE_FIXTURES / "report.testimony-in-model.json").unlink()
    assert len(comprobar(raiz)) == 2


def test_los_mensajes_no_llevan_valores_del_reporte(tmp_path: Path) -> None:
    """Solo nombres de campo y reglas: un testimonio sembrado en el fixture no sale en el mensaje."""
    raiz = _copiar_raiz(tmp_path)
    ruta = raiz / DIRECTORIO_DE_FIXTURES / "report.testimony-in-model.json"
    fixture = json.loads(ruta.read_text(encoding="utf-8"))
    fixture["expectation"] = "accept"
    fixture["payload"]["runs"][0]["calls"][0]["model"] = "Dormí en Villa Rocamora esa noche"
    ruta.write_text(json.dumps(fixture, ensure_ascii=False), encoding="utf-8")
    problemas = comprobar(raiz)
    assert problemas
    assert all("Rocamora" not in p and "Dormí" not in p for p in problemas)


# --- Límite declarado del canary de una palabra (FD-U1-05) ------------------------------------


def test_una_palabra_del_alfabeto_permitido_cumple_el_patron_y_pasa_el_esquema() -> None:
    """Límite declarado: lo cierra U12. Control positivo (pasa) y negativo (una frase no pasa)."""
    validador = validador_de(C19)
    fixture = load_contract(f"{DIRECTORIO_DE_FIXTURES}/report.valid.json")
    carga = copy.deepcopy(fixture["payload"])
    carga["runs"][0]["calls"][0]["model"] = PALABRA_DEL_CANARY
    assert errores_de(validador, carga) == []
    carga["runs"][0]["calls"][0]["model"] = f"{PALABRA_DEL_CANARY} y una frase"
    assert errores_de(validador, carga)


def test_los_campos_que_admiten_una_palabra_se_listan_por_sitio() -> None:
    reporte, llamada, _ = _documentos()
    sitios = campos_que_admiten_una_palabra(llamada, PALABRA_DEL_CANARY)
    assert "$.$defs.token" in sitios
    assert "$.properties.role" not in sitios  # el papel es minúscula sin guion: no la admite
    assert campos_que_admiten_una_palabra(reporte, PALABRA_DEL_CANARY) != []
    assert "$.$defs.sha256" not in campos_que_admiten_una_palabra(reporte, PALABRA_DEL_CANARY)
    assert "$.$defs.token" in campos_que_admiten_una_palabra(reporte, PALABRA_DEL_CANARY)
    # Una cadena con espacios nunca la admite, y un patrón inválido no rompe la guardia.
    ajeno = {"a": {"type": "string", "pattern": "^[a-z ]{1,5}$"}, "b": {"pattern": "[sin cerrar"}}
    assert campos_que_admiten_una_palabra(ajeno, "x y") == ["$.a"]
    assert campos_que_admiten_una_palabra(ajeno, "x") == ["$.a"]
    assert campos_que_admiten_una_palabra({"enum": ["a"]}, "a") == []


def test_el_modulo_no_importa_nada_de_red_ni_de_las_pruebas() -> None:
    fuente = Path(guardia.__file__).read_text(encoding="utf-8")
    assert "import socket" not in fuente
    assert "import helpers" not in fuente
    assert "from helpers" not in fuente


# --- Ronda 2, F-02: patrones por lo que aceptan ------------------------------------------------


@pytest.mark.parametrize(
    "patron",
    [
        "^.{1,128}$",
        "^[^<>]{1,128}$",
        "^[a-z\\x20]{1,128}$",
        "^[a-z\\W]{1,128}$",
        "^\\D{1,128}$",
        "^\\W{1,128}$",
        "^[a-z\\t]{1,128}$",
        "^[a-z\\n]{1,128}$",
        "^[a-z ]{1,128}$",
        "^[a-z\\u00a0]{1,128}$",
        "^[a-z]\\s{1,128}$",
        "^a b$",
        "^(a|\\t)$",
    ],
)
def test_un_patron_que_acepta_un_espacio_un_tabulador_o_un_nbsp_queda_en_rojo(patron: str) -> None:
    reporte, llamada, fixtures = _documentos()
    reporte["$defs"]["token"]["pattern"] = patron
    assert _problemas(reporte, llamada, fixtures) == [ESPACIOS], patron


@pytest.mark.parametrize(
    "patron",
    [
        "^\\S{1,128}$",
        "^\\x41{1,128}$",
        "^[a-z]\\u0041{1,128}$",
        "^\\p{L}{1,128}$",
        "^\\P{L}{1,128}$",
        "^[a-z!]{1,128}$",
        "^[a-z\\d]{1,128}$",
        "^[a-z{1,128}$",
        "^[]{1,128}$",
    ],
)
def test_un_patron_con_construcciones_abiertas_queda_en_rojo(patron: str) -> None:
    reporte, llamada, fixtures = _documentos()
    reporte["$defs"]["token"]["pattern"] = patron
    assert _problemas(reporte, llamada, fixtures) == [CONSTRUCCIONES], patron


def test_los_patrones_cerrados_del_contrato_no_se_marcan() -> None:
    """Control positivo: clases de la lista blanca, escape del punto, grupos y alternancia."""
    reporte, llamada, fixtures = _documentos()
    for patron in (
        "^[A-Za-z0-9._:/@+-]{1,128}$",
        "^[0-9]+\\.[0-9]+\\.[0-9]+$",
        "^[0-9]{4}-[0-9]{2}(\\.[0-9]{1,9})?(Z|[+-][0-9]{2}:[0-9]{2})$",
        "^[a-z0-9-]{1,23}__[a-z0-9-]{1,23}$",
    ):
        reporte["$defs"]["token"]["pattern"] = patron
        assert _problemas(reporte, llamada, fixtures) == [], patron


# --- Ronda 2, F-02: esquemas que aceptan cualquier valor ---------------------------------------


def _discards(reporte: dict[str, Any]) -> dict[str, Any]:
    return reporte["properties"]["runs"]["items"]["properties"]["discards"]  # type: ignore[no-any-return]


SITIO_DISCARDS = "$.properties.runs.items.properties.discards"


def test_una_propiedad_true_queda_en_rojo() -> None:
    reporte, llamada, fixtures = _documentos()
    reporte["properties"]["libre"] = True
    assert _problemas(reporte, llamada, fixtures) == [
        "BR10.1 $.properties.libre: propiedad sin tipo, $ref, enum ni const"
    ]


@pytest.mark.parametrize("palabra", ["anyOf", "oneOf"])
@pytest.mark.parametrize("abierto", [True, {}, {"description": "nada"}])
def test_una_rama_abierta_de_anyof_u_oneof_queda_en_rojo(palabra: str, abierto: Any) -> None:
    reporte, llamada, fixtures = _documentos()
    cerrado = {"type": "string", "enum": ["a"]}
    reporte["properties"]["libre"] = {palabra: [cerrado, abierto]}
    assert _problemas(reporte, llamada, fixtures) == [
        "BR10.1 $.properties.libre: propiedad sin tipo, $ref, enum ni const",
        ABIERTO.format(sitio=f"$.properties.libre.{palabra}[1]"),
    ]
    reporte["properties"]["libre"] = {palabra: [cerrado, {"const": 1}]}
    assert _problemas(reporte, llamada, fixtures) == []


@pytest.mark.parametrize("abierto", [True, {}])
def test_un_defs_abierto_queda_en_rojo_aunque_se_referencie(abierto: Any) -> None:
    reporte, llamada, fixtures = _documentos()
    reporte["$defs"]["vacio"] = abierto
    reporte["properties"]["libre"] = {"$ref": "#/$defs/vacio"}
    assert _problemas(reporte, llamada, fixtures) == [ABIERTO.format(sitio="$.$defs.vacio")]
    reporte["$defs"]["vacio"] = {"type": "boolean"}
    assert _problemas(reporte, llamada, fixtures) == []


@pytest.mark.parametrize("abierto", [True, {}])
def test_items_abierto_queda_en_rojo(abierto: Any) -> None:
    reporte, llamada, fixtures = _documentos()
    original = reporte["properties"]["distance_sensitivity"]["items"]
    reporte["properties"]["distance_sensitivity"]["items"] = abierto
    assert _problemas(reporte, llamada, fixtures) == [
        ABIERTO.format(sitio="$.properties.distance_sensitivity.items")
    ]
    reporte["properties"]["distance_sensitivity"]["items"] = original
    assert _problemas(reporte, llamada, fixtures) == []


def test_additionalproperties_abierto_queda_en_rojo() -> None:
    reporte, llamada, fixtures = _documentos()
    original = _discards(reporte)["additionalProperties"]
    _discards(reporte)["additionalProperties"] = {}
    assert _problemas(reporte, llamada, fixtures) == [
        ABIERTO.format(sitio=f"{SITIO_DISCARDS}.additionalProperties")
    ]
    _discards(reporte)["additionalProperties"] = original
    assert _problemas(reporte, llamada, fixtures) == []
    condicion = reporte["allOf"][0]["if"]
    condicion["additionalProperties"] = True
    assert _problemas(reporte, llamada, fixtures) == [
        ABIERTO.format(sitio="$.allOf[0].if.additionalProperties")
    ]
    condicion["additionalProperties"] = False
    assert _problemas(reporte, llamada, fixtures) == []


def test_pattern_properties_queda_en_rojo() -> None:
    reporte, llamada, fixtures = _documentos()
    _discards(reporte)["patternProperties"] = {".*": {}}
    assert _problemas(reporte, llamada, fixtures) == [
        f"BR10.1 {SITIO_DISCARDS}: patternProperties no se admite"
    ]


def test_additionalproperties_sin_propertynames_cerrado_queda_en_rojo() -> None:
    reporte, llamada, fixtures = _documentos()
    discards = _discards(reporte)
    nombres = discards["propertyNames"]
    esperado = [SIN_NOMBRES.format(sitio=SITIO_DISCARDS)]
    del discards["propertyNames"]
    assert _problemas(reporte, llamada, fixtures) == esperado
    for abierto in ({"minLength": 1}, {"enum": []}, {"enum": "a"}, {"$ref": "#/$defs/token"}, True):
        discards["propertyNames"] = abierto
        assert _problemas(reporte, llamada, fixtures) == esperado, abierto
    discards["propertyNames"] = {"const": "cita_no_verificada"}
    assert _problemas(reporte, llamada, fixtures) == []
    discards["propertyNames"] = nombres
    assert _problemas(reporte, llamada, fixtures) == []
    descartadas = reporte["properties"]["clarifications"]["properties"]["discarded"]
    del descartadas["propertyNames"]
    assert _problemas(reporte, llamada, fixtures) == [
        SIN_NOMBRES.format(sitio="$.properties.clarifications.properties.discarded")
    ]


# --- Ronda 2, F-03: mutantes que sobrevivían ---------------------------------------------------


def test_el_piso_negativo_es_solo_de_la_propiedad_seed() -> None:
    """m04: un sitio que solo contiene «seed» no hereda el piso negativo."""
    reporte, llamada, fixtures = _documentos()
    for nombre in ("seeded", "preseed", "seed_extra"):
        llamada["properties"][nombre] = {"type": "integer", "minimum": -1, "maximum": 5}
        assert _problemas(reporte, llamada, fixtures) == [
            _SIN_TOPE.format(sitio=f"model-call $.properties.{nombre}", tipo="entero")
        ], nombre
        del llamada["properties"][nombre]
    llamada["$defs"]["seed"] = {"type": "integer", "minimum": -1, "maximum": 5}
    assert len(_problemas(reporte, llamada, fixtures)) == 1
    del llamada["$defs"]["seed"]
    llamada["properties"]["seed"] = {"type": "number", "minimum": -1, "maximum": 5}
    assert _problemas(reporte, llamada, fixtures) == [
        _SIN_TOPE.format(sitio="model-call $.properties.seed", tipo="número")
    ]


def test_un_enum_con_dos_valores_malos_da_un_solo_mensaje() -> None:
    """m06: sin el `break` salían un mensaje por valor."""
    reporte, llamada, fixtures = _documentos()
    reporte["properties"]["kind"] = {"enum": ["una frase", "otra frase", "x" * 200]}
    assert _problemas(reporte, llamada, fixtures) == [
        "BR10.1 $.properties.kind: un valor de enum o const lleva espacios o pasa de 128 caracteres"
    ]


@pytest.mark.parametrize(("minimo", "maximo"), [(0.0, 5.5), (0, 5.5), (0.5, 5), (0.0, 5)])
def test_un_entero_con_limites_decimales_queda_en_rojo(minimo: float, maximo: float) -> None:
    """m19: un `integer` exige límites enteros; un `number` sí admite decimales."""
    reporte, llamada, fixtures = _documentos()
    reporte["$defs"]["count"] = {"type": "integer", "minimum": minimo, "maximum": maximo}
    assert _problemas(reporte, llamada, fixtures) == [
        _SIN_TOPE.format(sitio="$.$defs.count", tipo="entero")
    ]
    reporte["$defs"]["count"] = {"type": "number", "minimum": minimo, "maximum": maximo}
    assert [p for p in _problemas(reporte, llamada, fixtures) if p.startswith("NFR1.4")] == []


def test_un_maxlength_booleano_queda_en_rojo() -> None:
    """m20: `True` es un `int` de Python y cabría bajo el tope."""
    reporte, llamada, fixtures = _documentos()
    reporte["$defs"]["token"]["maxLength"] = True
    assert _problemas(reporte, llamada, fixtures) == [
        "BR10.1 $.$defs.token: maxLength ausente o mayor que 128"
    ]
    reporte["$defs"]["token"]["maxLength"] = 128.0
    assert _problemas(reporte, llamada, fixtures) == [
        "BR10.1 $.$defs.token: maxLength ausente o mayor que 128"
    ]


# --- Ronda 2, F-01, F-04, F-05: forma del reporte según las fuentes -----------------------------


def _carga(**cambios: Any) -> dict[str, Any]:
    fixture = load_contract(f"{DIRECTORIO_DE_FIXTURES}/report.valid.json")
    carga = copy.deepcopy(fixture["payload"])
    carga.update(cambios)
    if carga["kind"] == "evaluation":
        for campo, valor in EVALUACION.items():
            carga.setdefault(campo, copy.deepcopy(valor))
        dadas = carga.get("metrics", {})
        if any(nombre.startswith("scenario_a") for nombre in dadas):
            carga.setdefault("adversarial", True)
        metricas = copy.deepcopy(METRICAS_BASE)
        if carga.get("adversarial") is True:
            metricas.update(copy.deepcopy(METRICAS_DEL_ESCENARIO_A))
        metricas.update(dadas)
        carga["metrics"] = metricas
    return carga  # type: ignore[no-any-return]


OBLIGATORIAS = (
    "verified_quotes",
    "json_format_errors",
    "permutation_coverage",
    "anonymizer_leaks",
    "completed_runs",
    "precision",
    "recall",
    "reversed_order_consistency",
    "three_run_agreement",
    "type_agreement",
)
METRICAS_BASE: dict[str, Any] = {
    nombre: (
        {"aggregate": 0}
        if nombre == "three_run_agreement"
        else {"per_run": [0, 0, 0], "aggregate": 0}
    )
    for nombre in OBLIGATORIAS
}
METRICAS_DEL_ESCENARIO_A: dict[str, Any] = {
    "scenario_a_marker_hits": {"aggregate": 0},
    "scenario_a_difference": {"aggregate": 0},
}


SHA = "cd34" * 16
EVALUACION: dict[str, Any] = {
    "dataset_version": "1.0.0",
    "dataset_sha256": SHA,
    "profile_sha256": SHA,
    "thresholds_sha256": SHA,
    "role_families": {"judge": "anthropic", "verifier": "openai", "verifier_permuted": "openai"},
    "generator_family": "google",
}


def _rechazos(carga: dict[str, Any]) -> list[str]:
    return [e.json_path for e in errores_de(validador_de(C19), carga)]


def _metrica(valor: float, **resto: Any) -> dict[str, Any]:
    return {"per_run": [valor, valor, valor], "aggregate": valor, **resto}


def test_metrics_lleva_valor_por_corrida_agregado_umbral_y_passes() -> None:
    carga = _carga(
        kind="evaluation",
        metrics={
            "precision": {
                "per_run": [0.9, 0.8, 1.0],
                "aggregate": 0.9,
                "threshold": 0.8,
                "passes": True,
            },
            "three_run_agreement": {"aggregate": 0.7},
            "scenario_a_difference": {"aggregate": 0.1, "threshold": 0.3, "passes": True},
            "scenario_a_marker_hits": {"aggregate": 0, "threshold": 0, "passes": True},
            "anonymizer_leaks": {
                "per_run": [0, 0, 0],
                "aggregate": 0,
                "threshold": 0,
                "passes": True,
            },
        },
    )
    assert _rechazos(carga) == []


SIN_CORRIDAS = ("three_run_agreement", "scenario_a_difference", "scenario_a_marker_hits")
CON_CORRIDAS = (
    "verified_quotes",
    "json_format_errors",
    "permutation_coverage",
    "anonymizer_leaks",
    "completed_runs",
    "precision",
    "recall",
    "reversed_order_consistency",
    "type_agreement",
)


@pytest.mark.parametrize("metrica", CON_CORRIDAS)
def test_per_run_es_obligatorio_salvo_en_tres_metricas(metrica: str) -> None:
    """G-04: BR12.3, entities.md:391 y BR12.6 solo eximen a tres métricas."""
    assert _rechazos(_carga(kind="evaluation", metrics={metrica: {"aggregate": 0}})) != []
    bueno = {"per_run": [0, 0, 0], "aggregate": 0}
    assert _rechazos(_carga(kind="evaluation", metrics={metrica: bueno})) == []


@pytest.mark.parametrize("metrica", SIN_CORRIDAS)
def test_las_tres_metricas_sin_corridas_no_llevan_per_run(metrica: str) -> None:
    assert _rechazos(_carga(kind="evaluation", metrics={metrica: {"aggregate": 0}})) == []
    con = {"per_run": [0, 0, 0], "aggregate": 0}
    assert _rechazos(_carga(kind="evaluation", metrics={metrica: con})) != []
    reporte, _, _ = _documentos()
    sin = reporte["properties"]["metrics"]["properties"][metrica]["$ref"]
    assert sin.endswith("_without_runs")


def test_los_conjuntos_de_metricas_cubren_las_doce() -> None:
    reporte, _, _ = _documentos()
    assert set(SIN_CORRIDAS) | set(CON_CORRIDAS) == set(
        reporte["properties"]["metrics"]["properties"]
    )
    assert not set(SIN_CORRIDAS) & set(CON_CORRIDAS)


@pytest.mark.parametrize(
    ("metrica", "valor"),
    [
        ("precision", _metrica(0.9, per_run=[0.9, 0.8])),
        ("precision", _metrica(0.9, per_run=[0.9, 0.8, 1.0, 1.0])),
        ("precision", _metrica(0.9, per_run=[0.9, 0.8, 1.5])),
        ("precision", {"per_run": [0.9, 0.8, 1.0]}),
        ("precision", _metrica(500000000)),
        ("precision", _metrica(0.9, threshold=2)),
        ("precision", _metrica(0.9, value=1)),
        ("precision", _metrica(0.9, passes="si")),
        ("anonymizer_leaks", _metrica(0.5)),
        ("anonymizer_leaks", _metrica(0, per_run=[0, 0.5, 0])),
        ("scenario_a_marker_hits", _metrica(1.5)),
        ("scenario_a_difference", _metrica(1.5)),
        ("recall", _metrica(-0.1)),
    ],
)
def test_una_metrica_mal_formada_se_rechaza(metrica: str, valor: Any) -> None:
    assert _rechazos(_carga(kind="evaluation", metrics={metrica: valor})) != []


def test_metrics_solo_se_acepta_con_kind_evaluation() -> None:
    metricas = {"precision": _metrica(0.9)}
    assert _rechazos(_carga(kind="evaluation", metrics=metricas)) == []
    assert _rechazos(_carga(kind="run", metrics=metricas)) != []
    assert _rechazos(_carga(kind="run")) == []


def test_el_escenario_a_tiene_una_sola_ubicacion_y_un_indicador_booleano() -> None:
    reporte, _, _ = _documentos()
    assert reporte["properties"]["adversarial"]["type"] == "boolean"
    assert {"scenario_a_marker_hits", "scenario_a_difference"} <= set(
        reporte["properties"]["metrics"]["properties"]
    )
    assert _rechazos(_carga(adversarial={"scenario": "scenario_a", "marker_hits": 0})) != []
    assert _rechazos(_carga(kind="evaluation", adversarial=True)) == []
    assert _rechazos(_carga(kind="evaluation", adversarial=False)) == []
    assert _rechazos(_carga(kind="evaluation", adversarial="scenario_a")) != []


@pytest.mark.parametrize(
    "perfil", ["todo_local", "Todo-local", "todo local", "x" * 49, "", "ñandú"]
)
def test_profile_name_usa_el_patron_de_c18(perfil: str) -> None:
    assert _rechazos(_carga(profile_name=perfil)) != []
    assert _rechazos(_carga(profile_name="todo-local-2")) == []
    assert _rechazos(_carga(profile_name="x" * 48)) == []


@pytest.mark.parametrize(
    "fecha",
    ["ayer", "2026-11-23 15:00:00Z", "2026-11-23T15:00:00", "2026-11-23T15:00:00 Z", "2026-11-23"],
)
def test_created_at_rechaza_lo_que_no_es_rfc3339_aun_sin_validar_formatos(fecha: str) -> None:
    """Solo con el patrón del esquema: un validador sin formatos (ajv sin ajv-formats) no lo abre."""
    reporte, _, _ = _documentos()
    assert re.fullmatch(reporte["properties"]["created_at"]["pattern"], fecha) is None
    assert _rechazos(_carga(created_at=fecha)) != []


def test_created_at_acepta_el_formato_unico() -> None:
    assert _rechazos(_carga(created_at="2026-11-23T15:00:00Z")) == []


@pytest.mark.parametrize("fecha", ["2026-11-23T15:00:00.123Z", "2026-11-23T15:00:00-05:00"])
def test_created_at_rechaza_fracciones_y_desplazamientos(fecha: str) -> None:
    """E-22: un solo formato de fecha (BR8.1); el patron ya no admite fracciones ni desfases."""
    assert _rechazos(_carga(created_at=fecha)) != []


REGLAS = [
    "schema",
    "mentions_contradiction",
    "phrases",
    "cites_turn",
    "quote_text",
    "quote_overlap",
    "forbidden_vocabulary",
]


def test_clarifications_discarded_solo_admite_las_siete_reglas() -> None:
    reporte, _, _ = _documentos()
    nombres = reporte["properties"]["clarifications"]["properties"]["discarded"]["propertyNames"]
    assert nombres["enum"] == REGLAS
    completo = {"emitted": 3, "quote_matches": 0, "discarded": dict.fromkeys(REGLAS, 1)}
    assert _rechazos(_carga(clarifications=completo)) == []
    assert _rechazos(_carga(clarifications={"discarded": {"rocamora": 1}})) != []
    assert _rechazos(_carga(clarifications={"discarded": {"schema": 1.5}})) != []
    assert _rechazos(_carga(clarifications={"emitted": "tres"})) != []


TRAMOS = ["up_to_overlap", "overlap_to_window", "beyond_window"]


def test_distance_sensitivity_solo_admite_los_tres_tramos() -> None:
    reporte, _, _ = _documentos()
    tramo = reporte["properties"]["distance_sensitivity"]["items"]["properties"]["range"]
    assert tramo["enum"] == TRAMOS
    for nombre in TRAMOS:
        assert (
            _rechazos(_carga(distance_sensitivity=[{"range": nombre, "expected": 2, "found": 1}]))
            == []
        )
    assert (
        _rechazos(_carga(distance_sensitivity=[{"range": "rocamora", "expected": 2, "found": 1}]))
        != []
    )


@pytest.mark.parametrize(
    "conjunto",
    [
        "fecha",
        "fecha__",
        "__persona",
        "fecha_persona",
        "Fecha__persona",
        "a b__c",
        "x" * 24 + "__persona",
    ],
)
def test_synthetic_set_es_tipo_hecho_doble_guion_bajo_perfil_persona(conjunto: str) -> None:
    fila = {"fact_type": "fecha", "synthetic_set": conjunto, "expected": 1, "found": 1}
    assert _rechazos(_carga(bias_table=[fila])) != []
    bueno = {**fila, "synthetic_set": "x" * 23 + "__" + "y-1" * 7}
    assert _rechazos(_carga(bias_table=[bueno])) == []


# --- Ronda 3, G-01: gramática blanca de patrones ----------------------------------------------


def _con_patron(patron: str) -> list[str]:
    reporte, llamada, fixtures = _documentos()
    reporte["$defs"]["token"]["pattern"] = patron
    return _problemas(reporte, llamada, fixtures)


@pytest.mark.parametrize(
    ("patron", "espacio", "mensaje"),
    [
        ("^a\\040$", " ", CONSTRUCCIONES),
        ("^a\\N{SPACE}$", " ", CONSTRUCCIONES),
        ("^a\\U00000020$", " ", CONSTRUCCIONES),
        ("^a\\r$", "\r", ESPACIOS),
        ("^a\\v$", "\v", ESPACIOS),
        ("^a\\f$", "\f", ESPACIOS),
        ("^a $", " ", ESPACIOS),
        ("^a　$", "　", ESPACIOS),
    ],
)
def test_los_ocho_rodeos_de_un_espacio_quedan_en_rojo(
    patron: str, espacio: str, mensaje: str
) -> None:
    """G-01: cada uno acepta de verdad un texto con espacio en blanco y la guardia lo ve."""
    assert re.fullmatch(patron, "a" + espacio) is not None
    assert espacio.isspace()
    assert _con_patron(patron) == [mensaje], patron


def test_un_rango_de_clase_entre_simbolos_queda_en_rojo() -> None:
    """G-01 (AMARILLO): `[+-z]` acepta `<>;=?[\\]^_` además de las letras."""
    assert re.fullmatch("[+-z]", "<") is not None
    assert _con_patron("^[+-z]{1,5}$") == [CONSTRUCCIONES]


@pytest.mark.parametrize(
    "patron",
    [
        "^[a-Z]{1,3}$",
        "^[z-a]{1,3}$",
        "^[0-z]{1,3}$",
        "^[A-z]{1,3}$",
        "^[._-z]{1,3}$",
        "^[a-z-9]{1,3}$",
        "^[a-z\\d]{1,3}$",
        "^[a-z\\\\]{1,3}$",
        "^[a-z!]{1,3}$",
        "^[é]{1,3}$",
        "^é$",
        "^a\\/b$",
        "^a\\\\b$",
        "^a\\wb$",
        "^a,b$",
        "^a=b$",
        "^a!b$",
        "^a{,3}$",
        "^a{1,2,3}$",
        "^a{1,2$",
        "^a{x}$",
        "^a^b$",
        "^a$b$",
        "^[a-z$",
        "^[a-z\\$",
        "^a<b$",
    ],
)
def test_lo_que_sale_de_la_gramatica_blanca_queda_en_rojo(patron: str) -> None:
    assert _con_patron(patron) == [CONSTRUCCIONES], patron


@pytest.mark.parametrize(
    "patron",
    [
        "^[a-f]{1,3}$",
        "^[A-Z]{1,3}$",
        "^[0-9]{1,3}$",
        "^[a-z0-9-]{1,3}$",
        "^[-a-z]{1,3}$",
        "^[+-]{1,3}$",
        "^[\\.\\-\\+]{1,3}$",
        "^[A-Za-z0-9._:/@+-]{1,128}$",
        "^a\\.b\\-c\\+d$",
        "^a_b-c:d/e@f$",
        "^(a|b)?c*d+e{2}f{1,3}$",
        "^[a-z]{1,3}(\\.[0-9]{1,9})?$",
        "[a-z]{1,3}",
    ],
)
def test_lo_que_cabe_en_la_gramatica_blanca_pasa(patron: str) -> None:
    problemas = _con_patron(patron)
    assert [p for p in problemas if "gramática" in p or "espacios" in p] == [], patron


def test_las_sondas_son_todos_los_caracteres_de_espacio_en_blanco() -> None:
    sondas = set(guardia.SONDAS)
    assert sondas == {chr(i) for i in range(0x110000) if chr(i).isspace()}


def test_los_patrones_del_contrato_pasan_la_gramatica_nueva() -> None:
    """G-01: todos los patrones de C19 y de model-call.v1 siguen pasando."""
    reporte, llamada, _ = _documentos()
    patrones = [
        n["pattern"]
        for documento in (reporte, llamada)
        for n in _nodos(documento)
        if isinstance(n, dict) and isinstance(n.get("pattern"), str)
    ]
    assert len(patrones) >= 8
    for patron in patrones:
        reporte["$defs"]["token"]["pattern"] = patron
        assert _problemas(reporte, llamada, _documentos()[2]) == [], patron


# --- Ronda 3, G-02: arrays abiertos ------------------------------------------------------------

CERRADO = {"type": "string", "enum": ["a"]}
ARRAY_SIN_ITEMS = "BR10.1 $.properties.lista: array sin items cerrado"


@pytest.mark.parametrize(
    "lista",
    [
        {"type": "array"},
        {"type": ["array", "null"]},
        {"type": "array", "contains": CERRADO},
        {"type": "array", "prefixItems": [CERRADO]},
    ],
)
def test_un_array_sin_items_queda_en_rojo(lista: dict[str, Any]) -> None:
    reporte, llamada, fixtures = _documentos()
    reporte["properties"]["lista"] = lista
    assert _problemas(reporte, llamada, fixtures) == [ARRAY_SIN_ITEMS]
    reporte["properties"]["lista"] = {**lista, "items": CERRADO}
    assert _problemas(reporte, llamada, fixtures) == []


@pytest.mark.parametrize("palabra", ["contains", "additionalItems"])
@pytest.mark.parametrize("abierto", [True, {}])
def test_contains_y_additionalitems_abiertos_quedan_en_rojo(palabra: str, abierto: Any) -> None:
    reporte, llamada, fixtures = _documentos()
    reporte["properties"]["lista"] = {"type": "array", "items": CERRADO, palabra: abierto}
    assert _problemas(reporte, llamada, fixtures) == [
        ABIERTO.format(sitio=f"$.properties.lista.{palabra}")
    ]
    reporte["properties"]["lista"][palabra] = CERRADO
    assert _problemas(reporte, llamada, fixtures) == []


@pytest.mark.parametrize("abierto", [True, {}])
def test_prefixitems_abierto_queda_en_rojo(abierto: Any) -> None:
    reporte, llamada, fixtures = _documentos()
    reporte["properties"]["lista"] = {
        "type": "array",
        "items": CERRADO,
        "prefixItems": [CERRADO, abierto],
    }
    assert _problemas(reporte, llamada, fixtures) == [
        ABIERTO.format(sitio="$.properties.lista.prefixItems[1]")
    ]
    reporte["properties"]["lista"]["prefixItems"] = "no es una lista"
    assert _problemas(reporte, llamada, fixtures) == []


# --- Ronda 3, G-03: mutantes n03 y n19 ----------------------------------------------------------


def test_un_salto_de_linea_literal_en_el_patron_se_prueba_como_espacio() -> None:
    """n03: sin `re.DOTALL` el salto literal desaparece del tokenizador y cae en otro mensaje."""
    assert _con_patron("^[a-z]\n{1,3}$") == [ESPACIOS]
    assert _con_patron("^a\nb$") == [ESPACIOS]


@pytest.mark.parametrize("valor", ["a\tb", "a\nb", "a b", "a b", "a\rb"])
def test_un_valor_de_enum_con_cualquier_espacio_en_blanco_queda_en_rojo(valor: str) -> None:
    """n19: `" " in valor` no ve el tabulador."""
    reporte, llamada, fixtures = _documentos()
    reporte["properties"]["kind"] = {"enum": ["run", valor]}
    assert _problemas(reporte, llamada, fixtures) == [
        "BR10.1 $.properties.kind: un valor de enum o const lleva espacios o pasa de 128 caracteres"
    ]


# --- Ronda 3, G-05: campos de U11 ---------------------------------------------------------------

CAMPOS_DE_EVALUACION = (
    "dataset_version",
    "dataset_sha256",
    "profile_sha256",
    "thresholds_sha256",
    "role_families",
    "generator_family",
)
FAMILIAS = ["anthropic", "openai", "qwen", "google"]


@pytest.mark.parametrize("campo", CAMPOS_DE_EVALUACION)
def test_un_reporte_de_evaluacion_exige_los_campos_de_u11(campo: str) -> None:
    carga = _carga(kind="evaluation")
    assert _rechazos(carga) == []
    del carga[campo]
    assert _rechazos(carga) != []
    corrida = _carga(kind="run", **{campo: EVALUACION[campo]})
    assert _rechazos(corrida) == []


@pytest.mark.parametrize("campo", ["profile_sha256", "thresholds_sha256", "dataset_sha256"])
@pytest.mark.parametrize("huella", ["abc", "G" * 64, "a" * 63, "a" * 65, "A" * 64])
def test_las_huellas_nuevas_usan_el_patron_sha256(campo: str, huella: str) -> None:
    assert _rechazos(_carga(kind="evaluation", **{campo: huella})) != []


def test_la_familia_de_cada_papel_y_la_del_generador_son_cerradas() -> None:
    reporte, _, _ = _documentos()
    assert reporte["$defs"]["family"]["enum"] == FAMILIAS
    familias = reporte["properties"]["role_families"]
    assert set(familias["properties"]) == set(PAPELES)
    assert set(familias["required"]) == set(PAPELES)
    assert familias["additionalProperties"] is False
    completo = EVALUACION["role_families"]
    for familia in FAMILIAS:
        assert _rechazos(_carga(kind="evaluation", generator_family=familia)) == []
        assert (
            _rechazos(_carga(kind="evaluation", role_families={**completo, "judge": familia})) == []
        )
    assert _rechazos(_carga(kind="evaluation", generator_family="meta")) != []
    assert _rechazos(_carga(kind="evaluation", role_families={**completo, "judge": "meta"})) != []
    assert _rechazos(_carga(kind="evaluation", role_families={**completo, "extra": "openai"})) != []
    for papel in PAPELES:
        incompleto = {k: v for k, v in completo.items() if k != papel}
        assert _rechazos(_carga(kind="evaluation", role_families=incompleto)) != []


def test_las_familias_viven_en_la_raiz_y_no_en_model_call() -> None:
    _, llamada, _ = _documentos()
    assert "family" not in llamada["properties"]
    reporte, _, _ = _documentos()
    assert {"role_families", "generator_family"} <= set(reporte["properties"])


# --- Aviso de integración con T11 (BR3.2): enums de C6 en línea ---------------------------------


def test_los_enum_de_c6_estan_en_linea_y_sin_ref() -> None:
    reporte, _, _ = _documentos()
    corrida = reporte["properties"]["runs"]["items"]["properties"]
    assert "$ref" not in corrida["status"]
    assert corrida["status"]["enum"] == ["ok", "error"]
    assert "$ref" not in corrida["error_code"]
    assert "$ref" not in corrida["discards"]["propertyNames"]
    assert len(corrida["discards"]["propertyNames"]["enum"]) == 8
    ajuste = reporte["properties"]["bias_table"]["items"]["properties"]["fact_type"]
    assert "$ref" not in ajuste
    assert len(ajuste["enum"]) == 7


# --- Ronda 4, H-02: la alternancia solo va dentro de un grupo -----------------------------------


@pytest.mark.parametrize(
    ("patron", "frase"),
    [("^a|b$", "a x y"), ("^[a-z]{1,9}|x$", "abc con espacios"), ("^a|$", "cualquier frase")],
)
def test_una_alternancia_en_el_nivel_superior_queda_en_rojo(patron: str, frase: str) -> None:
    """H-02: `pattern` usa búsqueda, así que la alternancia superior burla el anclaje."""
    assert re.search(patron, frase) is not None
    assert _con_patron(patron) == [CONSTRUCCIONES], patron


@pytest.mark.parametrize("patron", ["^(a)|(b)$", "^(a)|b$", "^a|(b)$", "^(a|b)|c$"])
def test_una_alternancia_fuera_de_su_grupo_queda_en_rojo(patron: str) -> None:
    assert _con_patron(patron) == [CONSTRUCCIONES], patron


@pytest.mark.parametrize("patron", ["^(a|b)$", "^((a|b)|c)$", "^x(a|b)y(c|d)$", "^(a|b)?c$"])
def test_una_alternancia_dentro_de_un_grupo_pasa(patron: str) -> None:
    assert _con_patron(patron) == [], patron


# --- Ronda 4, H-05: mutantes p07 y p14 ------------------------------------------------------------


def test_un_cuantificador_de_cuatro_cifras_queda_en_rojo() -> None:
    """p07: `{1,1000}` no cabe; `{1,999}` sí."""
    assert _con_patron("^a{1,1000}$") == [CONSTRUCCIONES]
    assert _con_patron("^a{1000}$") == [CONSTRUCCIONES]
    assert _con_patron("^a{1,999}$") == []
    assert _con_patron("^a{999}$") == []


@pytest.mark.parametrize("patron", ["^^a$$", "^^a$", "^a$$", "^^$$"])
def test_un_ancla_repetida_queda_en_rojo(patron: str) -> None:
    """p14: quitar solo un `^` inicial y un `$` final, no todos."""
    assert _con_patron(patron) == [CONSTRUCCIONES], patron


# --- Ronda 4, AMARILLO: compilar y ReDoS ----------------------------------------------------------


@pytest.mark.parametrize(
    "patron", ["^(a$", "^a)$", "^*a$", "^a{2}{3}$", "^a**$", "^a+*$", "^(*a)$"]
)
def test_un_patron_que_no_compila_queda_en_rojo(patron: str) -> None:
    assert _con_patron(patron) == [CONSTRUCCIONES], patron
    with pytest.raises(re.error):
        re.compile(patron)


@pytest.mark.parametrize(
    "patron",
    ["^([a-z]+)+$", "^(a*)*$", "^((a+))+$", "^(a{1,3})*$", "^(a{1,2}){2}$", "^(x(a+)y)+$"],
)
def test_un_cuantificador_sobre_un_grupo_que_ya_cuantifica_queda_en_rojo(patron: str) -> None:
    assert _con_patron(patron) == [CONSTRUCCIONES], patron


@pytest.mark.parametrize(
    "patron",
    ["^(a+)?$", "^(a|b)+$", "^(a+)(b+)$", "^((a+)b)?$", "^(ab)*$", "^((a|b)c)+$", "^(a+|b)?$"],
)
def test_un_cuantificador_sobre_un_grupo_sin_cuantificadores_pasa(patron: str) -> None:
    assert _con_patron(patron) == [], patron


# --- Ronda 4, H-03: ramas que no cierran un nodo ----------------------------------------------------


@pytest.mark.parametrize(
    "libre",
    [
        {"allOf": [True]},
        {"allOf": [{}]},
        {"allOf": [{"minimum": 0}]},
        {"allOf": []},
        {"allOf": "no es una lista"},
        {"allOf": [{"allOf": [True]}]},
        {"allOf": [{"description": "nada"}, {"properties": {}}]},
        {"anyOf": []},
        {"oneOf": "no es una lista"},
    ],
)
def test_un_nodo_cuya_unica_restriccion_es_una_composicion_abierta_queda_en_rojo(
    libre: Any,
) -> None:
    reporte, llamada, fixtures = _documentos()
    reporte["properties"]["libre"] = libre
    assert _problemas(reporte, llamada, fixtures) == [
        "BR10.1 $.properties.libre: propiedad sin tipo, $ref, enum ni const"
    ]


@pytest.mark.parametrize(
    "libre",
    [
        {"allOf": [{"minimum": 0}, CERRADO]},
        {"allOf": [{"allOf": [{}, CERRADO]}]},
        {"allOf": [{"$ref": "#/$defs/count"}]},
        {"allOf": [{"const": 1}]},
        {"anyOf": [CERRADO, {"const": 1}]},
        {"oneOf": [{"$ref": "#/$defs/count"}, {"enum": [1]}]},
    ],
)
def test_una_composicion_que_cierra_el_nodo_pasa(libre: Any) -> None:
    reporte, llamada, fixtures = _documentos()
    reporte["properties"]["libre"] = libre
    assert _problemas(reporte, llamada, fixtures) == []


@pytest.mark.parametrize(
    "abierto", [{"allOf": [True]}, {"allOf": [{}]}, {"allOf": [{"minimum": 0}]}]
)
def test_items_con_una_composicion_abierta_queda_en_rojo(abierto: Any) -> None:
    reporte, llamada, fixtures = _documentos()
    reporte["properties"]["distance_sensitivity"]["items"] = abierto
    assert _problemas(reporte, llamada, fixtures) == [
        ABIERTO.format(sitio="$.properties.distance_sensitivity.items")
    ]


@pytest.mark.parametrize("palabra", ["unevaluatedItems", "unevaluatedProperties"])
@pytest.mark.parametrize("abierto", [True, {}])
def test_unevaluated_abierto_queda_en_rojo(palabra: str, abierto: Any) -> None:
    """H-03: `prefixItems` con `unevaluatedItems: true` deja pasar cualquier resto."""
    reporte, llamada, fixtures = _documentos()
    reporte["properties"]["lista"] = {"type": "array", "items": CERRADO, palabra: abierto}
    assert _problemas(reporte, llamada, fixtures) == [
        ABIERTO.format(sitio=f"$.properties.lista.{palabra}")
    ]
    reporte["properties"]["lista"][palabra] = CERRADO
    assert _problemas(reporte, llamada, fixtures) == []
    reporte["properties"]["lista"] = {
        "type": "array",
        "prefixItems": [CERRADO],
        "unevaluatedItems": True,
    }
    assert _problemas(reporte, llamada, fixtures) == [
        ARRAY_SIN_ITEMS,
        ABIERTO.format(sitio="$.properties.lista.unevaluatedItems"),
    ]


# --- Ronda 4, H-04: metrics obligatorio y cruce con adversarial ------------------------------------


def _evaluacion() -> dict[str, Any]:
    return _carga(kind="evaluation")


def test_el_reporte_de_evaluacion_base_se_acepta() -> None:
    assert _rechazos(_evaluacion()) == []
    assert set(_evaluacion()["metrics"]) == set(OBLIGATORIAS)


def test_una_evaluacion_sin_metrics_o_con_metrics_vacio_se_rechaza() -> None:
    sin = _evaluacion()
    del sin["metrics"]
    assert _rechazos(sin) != []
    vacio = _evaluacion()
    vacio["metrics"] = {}
    assert _rechazos(vacio) != []


@pytest.mark.parametrize("metrica", OBLIGATORIAS)
def test_cada_metrica_de_br12_3_es_obligatoria_en_una_evaluacion(metrica: str) -> None:
    carga = _evaluacion()
    del carga["metrics"][metrica]
    assert _rechazos(carga) != []


def test_las_metricas_obligatorias_son_las_de_br12_3() -> None:
    reporte, _, _ = _documentos()
    condicional = reporte["allOf"][1]
    assert condicional["if"]["properties"]["kind"]["const"] == "evaluation"
    assert "metrics" in condicional["then"]["required"]
    assert set(condicional["then"]["properties"]["metrics"]["required"]) == set(OBLIGATORIAS)


@pytest.mark.parametrize("adversarial", [None, False])
@pytest.mark.parametrize("metrica", ["scenario_a_marker_hits", "scenario_a_difference"])
def test_las_metricas_del_escenario_a_estan_prohibidas_sin_adversarial_verdadero(
    adversarial: bool | None, metrica: str
) -> None:
    carga = _evaluacion()
    if adversarial is not None:
        carga["adversarial"] = adversarial
    assert _rechazos(carga) == []
    carga["metrics"][metrica] = {"aggregate": 0}
    assert _rechazos(carga) != []


@pytest.mark.parametrize("metrica", ["scenario_a_marker_hits", "scenario_a_difference"])
def test_las_metricas_del_escenario_a_son_obligatorias_con_adversarial_verdadero(
    metrica: str,
) -> None:
    carga = _carga(kind="evaluation", adversarial=True)
    assert _rechazos(carga) == []
    assert {"scenario_a_marker_hits", "scenario_a_difference"} <= set(carga["metrics"])
    del carga["metrics"][metrica]
    assert _rechazos(carga) != []


def test_adversarial_verdadero_sin_ninguna_metrica_del_escenario_a_se_rechaza() -> None:
    carga = _evaluacion()
    carga["adversarial"] = True
    assert _rechazos(carga) != []


def test_adversarial_en_una_corrida_no_habilita_metrics() -> None:
    carga = _carga(kind="run", adversarial=True, metrics={"precision": _metrica(0.9)})
    assert _rechazos(carga) != []


# --- Ronda 5, F-02: `false` cuenta como esquema cerrado -----------------------------------------------


@pytest.mark.parametrize("palabra", ["allOf", "anyOf", "oneOf"])
def test_false_en_una_composicion_cierra_el_nodo(palabra: str) -> None:
    """Decisión: `false` no acepta ningún valor, así que no abre nada; fija a q21."""
    reporte, llamada, fixtures = _documentos()
    reporte["properties"]["libre"] = {palabra: [False]}
    assert _problemas(reporte, llamada, fixtures) == []
    reporte["properties"]["libre"] = {palabra: [CERRADO, False]}
    assert _problemas(reporte, llamada, fixtures) == []
    reporte["properties"]["libre"] = {palabra: [False, False]}
    assert _problemas(reporte, llamada, fixtures) == []


@pytest.mark.parametrize("palabra", ["anyOf", "oneOf"])
def test_false_junto_a_una_rama_abierta_no_cierra_anyof_ni_oneof(palabra: str) -> None:
    reporte, llamada, fixtures = _documentos()
    reporte["properties"]["libre"] = {palabra: [False, {}]}
    assert _problemas(reporte, llamada, fixtures) == [
        "BR10.1 $.properties.libre: propiedad sin tipo, $ref, enum ni const",
        ABIERTO.format(sitio=f"$.properties.libre.{palabra}[1]"),
    ]


def test_false_anidado_en_allof_cierra_y_true_no() -> None:
    reporte, llamada, fixtures = _documentos()
    reporte["properties"]["libre"] = {"allOf": [{"allOf": [False]}]}
    assert _problemas(reporte, llamada, fixtures) == []
    reporte["properties"]["libre"] = {"allOf": [{"allOf": [True]}]}
    assert _problemas(reporte, llamada, fixtures) == [
        "BR10.1 $.properties.libre: propiedad sin tipo, $ref, enum ni const"
    ]


# --- Ronda 5, F-04: solo `(?:`; las banderas en línea no son ECMA -------------------------------------


@pytest.mark.parametrize(
    "patron",
    ["^(?i:a)$", "^(?a:a)$", "^(?-i:a)$", "^(?=a)a$", "^(?!a)b$", "^(?P<n>a)$", "^(?#c)a$"],
)
def test_un_grupo_con_interrogacion_distinto_de_dos_puntos_queda_en_rojo(patron: str) -> None:
    re.compile(patron)  # compilan en Python, que es justo el peligro
    assert _con_patron(patron) == [CONSTRUCCIONES], patron


@pytest.mark.parametrize("patron", ["^(?:a|b)$", "^x(?:ab)+y$", "^(a)?$", "^(a(?:b|c))?$"])
def test_un_grupo_sin_captura_o_con_interrogacion_de_cuantificador_pasa(patron: str) -> None:
    assert _con_patron(patron) == [], patron


# --- Ronda 5, F-03: limitación declarada del ReDoS sin anidar ----------------------------------------


@pytest.mark.parametrize("patron", ["^(a|a)+$", "^[a-z]*[a-z]*[a-z]*$", "^(a|aa)+$"])
def test_el_redos_sin_cuantificadores_anidados_es_una_limitacion_declarada(patron: str) -> None:
    """La guardia no ve estos patrones y no se amplía la regla: solo entran por PR con revisión."""
    assert _con_patron(patron) == [], patron
    fuente = Path(guardia.__file__).read_text(encoding="utf-8")
    assert "Limitación declarada (ReDoS sin cuantificadores anidados)" in fuente
