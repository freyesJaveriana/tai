"""Guardia de estrictez de cuerpos, mensajes y archivos (§4.3; NFR10.1, NFR10.2, NFR10.7).

Los controles negativos trabajan sobre copias en memoria de los contratos reales y comparan con el
resultado sobre el original: la guardia solo debe añadir el hallazgo que provoca la prueba.
"""

import copy
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from helpers import CONTRACTS_ROOT, importar_o_fallar, load_contract

pytestmark = pytest.mark.c1


@pytest.fixture
def guardia() -> ModuleType:
    return importar_o_fallar("veridicus_contracts.checks.strict_bodies", "T15, paso 16")


def _copia(relativa: str) -> Any:
    return copy.deepcopy(load_contract(relativa))


def _nuevos(comprobar: Callable[[Any], list[str]], original: Any, cambiado: Any) -> list[str]:
    antes = set(comprobar(original))
    return [p for p in comprobar(cambiado) if p not in antes]


def _cuerpo_json(documento: dict[str, Any], ruta: str, metodo: str) -> dict[str, Any]:
    cuerpo: dict[str, Any] = documento["paths"][ruta][metodo]["requestBody"]["content"]
    return cuerpo["application/json"]["schema"]


def test_los_cuerpos_de_c1_versionados_son_estrictos(guardia: ModuleType) -> None:
    assert guardia.comprobar_c1(_copia("api/console.v2.yaml")) == []


def test_cuerpo_json_sin_estrictez_en_la_raiz_o_anidado(guardia: ModuleType) -> None:
    original = _copia("api/console.v2.yaml")
    cambiado = copy.deepcopy(original)
    del _cuerpo_json(cambiado, "/users", "post")["additionalProperties"]
    cambiado["components"]["schemas"]["Consent"]["additionalProperties"] = True
    assert sorted(_nuevos(guardia.comprobar_c1, original, cambiado)) == [
        "api/console.v2.yaml: POST /sessions /requestBody/application/json/properties/"
        "consentimiento: objeto sin additionalProperties: false (§4.3)",
        "api/console.v2.yaml: POST /users /requestBody/application/json: objeto sin "
        "additionalProperties: false (§4.3)",
    ]


def test_estrictez_dentro_de_arreglos_composiciones_y_referencias_externas(
    guardia: ModuleType,
) -> None:
    original = _copia("api/console.v2.yaml")
    cambiado = copy.deepcopy(original)
    esquema = _cuerpo_json(cambiado, "/users", "post")
    esquema["properties"]["lista"] = {"type": "array", "items": {"properties": {"a": {}}}}
    esquema["properties"]["vuelta"] = esquema
    esquema["properties"]["externo"] = {"$ref": "/veridicus/contracts/otro"}
    esquema["allOf"] = [{"type": "object", "additionalProperties": False}, {"properties": {}}]
    esquema["properties"]["sin_objeto"] = "no es un esquema"
    nuevos = _nuevos(guardia.comprobar_c1, original, cambiado)
    assert sorted(nuevos) == [
        "api/console.v2.yaml: POST /users /requestBody/application/json/allOf/1: objeto sin "
        "additionalProperties: false (§4.3)",
        "api/console.v2.yaml: POST /users /requestBody/application/json/properties/lista/items: "
        "objeto sin additionalProperties: false (§4.3)",
    ]


def test_multipart_con_parte_de_texto_sin_acotar_y_sin_tope_de_bytes(guardia: ModuleType) -> None:
    original = _copia("api/console.v2.yaml")
    cambiado = copy.deepcopy(original)
    cuerpo = cambiado["paths"]["/sessions/import"]["post"]["requestBody"]
    esquema = cuerpo["content"]["multipart/form-data"]["schema"]
    esquema["properties"]["profile_name"] = {"type": "string"}
    del cuerpo["x-veridicus-max-bytes"]
    esquema["additionalProperties"] = True
    assert sorted(_nuevos(guardia.comprobar_c1, original, cambiado)) == [
        "api/console.v2.yaml: POST /sessions/import /requestBody/multipart/form-data: objeto sin "
        "additionalProperties: false (§4.3)",
        "api/console.v2.yaml: POST /sessions/import /requestBody/multipart/form-data: sin "
        "x-veridicus-max-bytes (§4.3)",
        "api/console.v2.yaml: POST /sessions/import "
        "/requestBody/multipart/form-data/properties/profile_name: parte de texto sin acotar (§4.3)",
    ]
    acotada = copy.deepcopy(original)
    partes = acotada["paths"]["/sessions/import"]["post"]["requestBody"]["content"]
    partes["multipart/form-data"]["schema"]["properties"]["profile_name"] = {
        "type": "string",
        "maxLength": 5,
        "x-veridicus-limit": "username_max_chars",
    }
    assert _nuevos(guardia.comprobar_c1, original, acotada) == []


def test_esquemas_estrictos_de_c6_c7_c18_y_c19(guardia: ModuleType) -> None:
    for relativa in guardia.ESQUEMAS_ESTRICTOS:
        documento = _copia(relativa)
        assert guardia.comprobar_esquema(relativa, documento) == [], relativa
    original = _copia("integrity/review-suggestion.v2.json")
    cambiado = copy.deepcopy(original)
    cambiado["additionalProperties"] = True
    cambiado["properties"]["anidado"] = {"type": "object", "properties": {"a": {"type": "string"}}}
    cambiado["$defs"] = {"otro": {"type": "object", "additionalProperties": {"type": "string"}}}
    nuevos = _nuevos(
        lambda d: guardia.comprobar_esquema("integrity/review-suggestion.v2.json", d),
        original,
        cambiado,
    )
    assert sorted(nuevos) == [
        "integrity/review-suggestion.v2.json: /$defs/otro: objeto sin additionalProperties: false "
        "(§4.3)",
        "integrity/review-suggestion.v2.json: /: objeto sin additionalProperties: false (§4.3)",
        "integrity/review-suggestion.v2.json: /properties/anidado: objeto sin "
        "additionalProperties: false (§4.3)",
    ]
    unevaluated = copy.deepcopy(original)
    del unevaluated["additionalProperties"]
    unevaluated["unevaluatedProperties"] = False
    assert _nuevos(lambda d: guardia.comprobar_esquema("x", d), original, unevaluated) == []


def test_openapi_internos_c21_y_la_ruta_de_voz(guardia: ModuleType) -> None:
    for relativa in ("api/anonymizer-proxy.v1.yaml", "api/speech-internal.v1.yaml"):
        assert guardia.comprobar_openapi_interno(relativa, _copia(relativa)) == [], relativa
    voz = _copia("api/speech-internal.v1.yaml")
    cambiado = copy.deepcopy(voz)
    operacion = cambiado["paths"]["/internal/v1/speech"]["post"]
    del operacion["requestBody"]["content"]["application/json"]["schema"]["additionalProperties"]
    problema = operacion["responses"]["422"]["content"]["application/problem+json"]["schema"]
    problema["additionalProperties"] = True
    nuevos = _nuevos(lambda d: guardia.comprobar_openapi_interno("v", d), voz, cambiado)
    assert sorted(nuevos) == [
        "v: POST /internal/v1/speech /requestBody/application/json: objeto sin "
        "additionalProperties: false (§4.3)",
        "v: POST /internal/v1/speech /responses/422/application/problem+json: objeto sin "
        "additionalProperties: false (§4.3)",
    ]
    c21 = _copia("api/anonymizer-proxy.v1.yaml")
    sin_cierre = copy.deepcopy(c21)
    esquema = sin_cierre["paths"]["/v1/generate"]["post"]["requestBody"]["content"]
    esquema["application/json"]["schema"]["properties"]["messages"]["items"][
        "additionalProperties"
    ] = True
    assert _nuevos(lambda d: guardia.comprobar_openapi_interno("c21", d), c21, sin_cierre) == [
        "c21: POST /v1/generate /requestBody/application/json/properties/messages/items: objeto "
        "sin additionalProperties: false (§4.3)"
    ]


def test_mensajes_fallidos_sin_campos_de_texto(guardia: ModuleType) -> None:
    for relativa, mensaje in guardia.FALLIDOS.items():
        assert guardia.comprobar_fallidos(relativa, _copia(relativa), mensaje) == [], relativa
    relativa, mensaje = "queues/runs.v2.yaml", "RunFailed"
    original = _copia(relativa)
    cambiado = copy.deepcopy(original)
    carga = cambiado["components"]["messages"][mensaje]["payload"]
    carga["additionalProperties"] = True
    carga["properties"]["text"] = {"type": "string"}
    carga["properties"]["note"] = {"type": "string", "pattern": "^[a-z]+$"}
    carga["properties"]["numero"] = {"type": "integer"}

    def comprobar(documento: Any) -> list[str]:
        return list(guardia.comprobar_fallidos(relativa, documento, mensaje))

    assert sorted(_nuevos(comprobar, original, cambiado)) == [
        "queues/runs.v2.yaml: RunFailed: objeto sin additionalProperties: false (NFRD-U1-07)",
        "queues/runs.v2.yaml: RunFailed: text es un campo de texto libre (NFRD-U1-07)",
    ]
    ausente = copy.deepcopy(original)
    del ausente["components"]["messages"][mensaje]
    assert guardia.comprobar_fallidos(relativa, ausente, mensaje) == [
        "queues/runs.v2.yaml: RunFailed: mensaje ausente (NFRD-U1-07)"
    ]


def test_comprobar_recorre_todos_los_contratos_y_avisa_si_falta_alguno(
    guardia: ModuleType, tmp_path: Path
) -> None:
    ausentes = guardia.comprobar(tmp_path)
    todos = [
        *guardia.ESQUEMAS_ESTRICTOS,
        *guardia.OPENAPI_INTERNOS,
        "api/console.v2.yaml",
        *guardia.FALLIDOS,
    ]
    assert sorted(ausentes) == sorted(f"{r}: contrato ausente (§4.3)" for r in todos)
    assert guardia.comprobar(CONTRACTS_ROOT) == []
