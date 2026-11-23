"""Guardia del reporte de la CLI C19 v2 (BR10.1, BR10.2, NFR1.4; E28, E29; FD-U1-03, FD-U1-05).

Los controles negativos trabajan sobre copias en memoria o en `tmp_path`, nunca sobre el contrato
versionado. Cada constante, cada lista cerrada y cada patrón de la guardia tiene un control que
falla si se cambia.
"""

import copy
import json
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
    reporte["properties"]["extra"] = {composicion: ["a"] if composicion != "const" else "a"}
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
    """`model-call.v1` es de otro paso: sin marca, pero cerrada y con tope de 128 como mucho."""
    reporte, llamada, fixtures = _documentos()
    assert "x-veridicus-limit" not in llamada["$defs"]["token"]
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
    esperado = ["BR10.1 $.properties.kind: un valor de enum o const lleva espacios o pasa de 128 caracteres"]
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


def test_el_formato_date_time_cuenta_como_cadena_cerrada() -> None:
    reporte, llamada, fixtures = _documentos()
    assert reporte["properties"]["created_at"]["format"] == "date-time"
    reporte["properties"]["created_at"] = {"type": "string", "format": "uri"}
    assert _problemas(reporte, llamada, fixtures) == [
        "BR10.1 $.properties.created_at: cadena abierta (sin enum, const, formato ni patrón)"
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
    assert _problemas(reporte, llamada, fixtures) == []


# --- Enteros y números (NFR1.4) ---------------------------------------------------------------


_SIN_TOPE = "NFR1.4 {sitio}: {tipo} sin minimum o maximum acotados"


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
    assert _problemas(reporte, llamada, fixtures) == [
        _SIN_TOPE.format(sitio=sitio, tipo="entero")
    ]


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
    assert len(_problemas(reporte, llamada, fixtures)) == 2


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
        (
            "BR10.2 $.properties.runs.items.properties.calls.items: "
            "las llamadas no referencian model-call.v1"
        )
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
    assert _problemas(reporte, llamada, fixtures) == [f"E28/E29: falta el fixture negativo {nombre}"]


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


def test_comprobar_informa_de_los_archivos_ausentes_ilegibles_o_mal_formados(tmp_path: Path) -> None:
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
    (raiz / DIRECTORIO_DE_FIXTURES / "report.role-prueba-a.json").write_text("{: roto", encoding="utf-8")
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
