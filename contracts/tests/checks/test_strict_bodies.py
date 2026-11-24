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
    # Con `Consent` abierto, sus condiciones `if` ya no refinan a un objeto cerrado (P-T15-2).
    assert sorted(_nuevos(guardia.comprobar_c1, original, cambiado)) == [
        ("api/console.v2.yaml: POST /sessions /requestBody/application/json/properties/"
        "consentimiento/allOf/0/if: objeto sin additionalProperties: false (§4.3)"),
        ("api/console.v2.yaml: POST /sessions /requestBody/application/json/properties/"
        "consentimiento/allOf/1/if: objeto sin additionalProperties: false (§4.3)"),
        ("api/console.v2.yaml: POST /sessions /requestBody/application/json/properties/"
        "consentimiento: objeto sin additionalProperties: false (§4.3)"),
        ("api/console.v2.yaml: POST /users /requestBody/application/json: objeto sin "
        "additionalProperties: false (§4.3)"),
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
    esquema["allOf"] = [
        {"type": "object", "additionalProperties": False},
        {"type": "object", "properties": {}},
        {"properties": {}},  # solo refina al objeto padre: no declara uno nuevo
    ]
    esquema["properties"]["mapa"] = {  # claves cerradas por un enum
        "type": "object",
        "propertyNames": {"enum": ["a"]},
        "additionalProperties": {"type": "integer"},
    }
    esquema["properties"]["tupla"] = {"type": "array", "prefixItems": [{"properties": {}}]}
    esquema["properties"]["sin_objeto"] = "no es un esquema"
    nuevos = _nuevos(guardia.comprobar_c1, original, cambiado)
    assert sorted(nuevos) == [
        ("api/console.v2.yaml: POST /users /requestBody/application/json/allOf/1: objeto sin "
        "additionalProperties: false (§4.3)"),
        ("api/console.v2.yaml: POST /users /requestBody/application/json/properties/lista/items: "
        "objeto sin additionalProperties: false (§4.3)"),
        ("api/console.v2.yaml: POST /users /requestBody/application/json/properties/tupla/"
        "prefixItems/0: objeto sin additionalProperties: false (§4.3)"),
    ]


def test_multipart_con_parte_de_texto_sin_acotar_y_sin_tope_de_bytes(guardia: ModuleType) -> None:
    original = _copia("api/console.v2.yaml")
    cambiado = copy.deepcopy(original)
    cuerpo = cambiado["paths"]["/sessions/import"]["post"]["requestBody"]
    esquema = cuerpo["content"]["multipart/form-data"]["schema"]
    esquema["properties"]["profile_name"] = {"type": "string"}
    del cuerpo["x-veridicus-max-bytes"]
    esquema["additionalProperties"] = True
    assert _nuevos(guardia.comprobar_c1, original, cambiado) == [
        ("api/console.v2.yaml: POST /sessions/import /requestBody/multipart/form-data: objeto sin "
        "additionalProperties: false (§4.3)"),
        ("api/console.v2.yaml: POST /sessions/import /requestBody/multipart/form-data: sin "
        "x-veridicus-max-bytes (§4.3)"),
        ("api/console.v2.yaml: POST /sessions/import "
        "/requestBody/multipart/form-data/properties/profile_name: parte de texto sin acotar (§4.3)"),
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
    externos = guardia.ids_de(_copia(r) for r in guardia.ESQUEMAS_ESTRICTOS)
    for relativa in guardia.ESQUEMAS_ESTRICTOS:
        documento = _copia(relativa)
        assert guardia.comprobar_esquema(relativa, documento, externos) == [], relativa
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
        ("integrity/review-suggestion.v2.json: /$defs/otro: objeto sin additionalProperties: false "
        "(§4.3)"),
        "integrity/review-suggestion.v2.json: /: objeto sin additionalProperties: false (§4.3)",
        # Con la raíz abierta, sus condiciones `if` ya no refinan a un objeto cerrado (P-T15-2).
        ("integrity/review-suggestion.v2.json: /allOf/0/if: objeto sin additionalProperties: "
        "false (§4.3)"),
        ("integrity/review-suggestion.v2.json: /allOf/1/if: objeto sin additionalProperties: "
        "false (§4.3)"),
        ("integrity/review-suggestion.v2.json: /allOf/2/if: objeto sin additionalProperties: "
        "false (§4.3)"),
        ("integrity/review-suggestion.v2.json: /properties/anidado: objeto sin "
        "additionalProperties: false (§4.3)"),
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
        ("v: POST /internal/v1/speech /requestBody/application/json: objeto sin "
        "additionalProperties: false (§4.3)"),
        ("v: POST /internal/v1/speech /responses/422/application/problem+json: objeto sin "
        "additionalProperties: false (§4.3)"),
    ]
    c21 = _copia("api/anonymizer-proxy.v1.yaml")
    sin_cierre = copy.deepcopy(c21)
    esquema = sin_cierre["paths"]["/v1/generate"]["post"]["requestBody"]["content"]
    esquema["application/json"]["schema"]["properties"]["messages"]["items"][
        "additionalProperties"
    ] = True
    assert _nuevos(lambda d: guardia.comprobar_openapi_interno("c21", d), c21, sin_cierre) == [
        ("c21: POST /v1/generate /requestBody/application/json/properties/messages/items: objeto "
        "sin additionalProperties: false (§4.3)")
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


# ---- F-04: las guardias bajan por toda forma de subesquema --------------------------------------

FALTA = "objeto sin additionalProperties: false (§4.3)"
CERRADO = {"type": "object", "additionalProperties": False}
CUERPO_USERS = "api/console.v2.yaml: POST /users /requestBody/application/json/properties/x1"


def _libre() -> dict[str, Any]:
    """Un objeto sin tipo ni cierre; cada llamada trae uno distinto (la guardia no repite esquemas)."""
    return {"properties": {"libre": {"type": "string"}}}


FORMAS = {
    "oneOf": ({"oneOf": [_libre()]}, ["/oneOf/0"]),
    "anyOf": ({"anyOf": [_libre()]}, ["/anyOf/0"]),
    "allOf": ({"allOf": [_libre()]}, ["/allOf/0"]),
    "if_then_else": (
        {"if": _libre(), "then": _libre(), "else": _libre()},
        ["/else", "/if", "/then"],
    ),
    "patternProperties": (
        {**CERRADO, "patternProperties": {"^a": {"type": "object", "properties": {}}}},
        ["/patternProperties/^a"],
    ),
    "additionalProperties_como_esquema": (
        {
            "type": "object",
            "propertyNames": {"enum": ["a"]},
            "additionalProperties": {"type": "object", "properties": {}},
        },
        ["/additionalProperties"],
    ),
    "type_en_lista": ({"type": ["object", "null"], "properties": {}}, [""]),
    "type_en_lista_sin_properties": ({"type": ["null", "object"]}, [""]),
}


@pytest.mark.parametrize("forma", sorted(FORMAS))
def test_un_objeto_abierto_dentro_de_una_forma_de_subesquema_es_rojo(
    guardia: ModuleType, forma: str
) -> None:
    esquema, sitios = FORMAS[forma]
    original = _copia("api/console.v2.yaml")
    cambiado = copy.deepcopy(original)
    _cuerpo_json(cambiado, "/users", "post")["properties"]["x1"] = copy.deepcopy(esquema)
    esperados = [f"{CUERPO_USERS}{sitio}: {FALTA}" for sitio in sitios]
    assert sorted(_nuevos(guardia.comprobar_c1, original, cambiado)) == esperados


def _abiertos(guardia: ModuleType, esquema: Any) -> list[str]:
    return sorted(guardia.comprobar_esquema("x", esquema))


def _aviso(puntero: str) -> str:
    return f"x: {puntero or '/'}: {FALTA}"


# ---- P-T15-1: un mapa con propertyNames.enum cuenta como cerrado solo con valores estrictos ----


def test_propertynames_enum_cierra_el_mapa_solo_si_los_valores_son_un_esquema_estricto(
    guardia: ModuleType,
) -> None:
    valores = {"type": "integer"}
    mapa = {"type": "object", "propertyNames": {"enum": ["a", "b"]}, "additionalProperties": valores}
    assert _abiertos(guardia, mapa) == []
    sin_valores = {"type": "object", "propertyNames": {"enum": ["a"]}}
    assert _abiertos(guardia, sin_valores) == [_aviso("")]
    for abiertos in (True, {}):
        libre = {**sin_valores, "additionalProperties": abiertos}
        assert _abiertos(guardia, libre) == [_aviso("")], abiertos
    sin_enum = {"type": "object", "propertyNames": {"pattern": "^a"}, "additionalProperties": valores}
    assert _abiertos(guardia, sin_enum) == [_aviso("")]
    de_objetos = {**mapa, "additionalProperties": {"type": "object", "properties": {"z": {}}}}
    assert _abiertos(guardia, de_objetos) == [_aviso("/additionalProperties")]


# ---- P-T15-2: una rama de allOf refina solo con el padre cerrado y sus propiedades declaradas ---


def _padre(**resto: Any) -> dict[str, Any]:
    declaradas = {"a": {"type": "string"}, "b": {"type": "string"}}
    return {**CERRADO, "properties": declaradas, **resto}


def test_una_rama_de_allof_con_solo_properties_refina_si_el_padre_esta_cerrado(
    guardia: ModuleType,
) -> None:
    assert _abiertos(guardia, _padre(allOf=[{"properties": {"a": {"enum": ["x"]}}}])) == []
    assert _abiertos(guardia, _padre(allOf=[{"properties": {}}, {"required": ["a"]}])) == []
    # Control negativo 1: una propiedad que el padre no declara.
    sin_declarar = _padre(allOf=[{"properties": {"c": {"enum": ["x"]}}}])
    assert _abiertos(guardia, sin_declarar) == [_aviso("/allOf/0")]
    # Control negativo 2: el padre no está cerrado (tampoco la rama se libra).
    abierto = {"type": "object", "properties": {"a": {}}, "allOf": [{"properties": {"a": {}}}]}
    assert _abiertos(guardia, abierto) == [_aviso(""), _aviso("/allOf/0")]
    # Control negativo 3: una rama que declara `type: object` es un objeto, no un refinamiento.
    con_tipo = _padre(allOf=[{"type": "object", "properties": {"a": {}}}])
    assert _abiertos(guardia, con_tipo) == [_aviso("/allOf/0")]
    # La rama que se cierra a sí misma no necesita el padre.
    propia = {"type": "object", "additionalProperties": False, "properties": {"c": {}}}
    assert _abiertos(guardia, _padre(allOf=[propia])) == []


def test_if_then_else_refinan_con_las_mismas_condiciones_que_allof(guardia: ModuleType) -> None:
    bien = _padre(
        **{"if": {"properties": {"a": {"const": "x"}}}, "then": {"properties": {"b": {}}}},
        **{"else": {"properties": {"b": {"enum": ["y"]}}}},
    )
    assert _abiertos(guardia, bien) == []
    mal = _padre(
        **{"if": {"properties": {"z": {}}}, "then": {"properties": {"y": {}}}},
        **{"else": {"properties": {"x": {}}}},
    )
    assert _abiertos(guardia, mal) == [_aviso("/else"), _aviso("/if"), _aviso("/then")]


# ---- P-T15-5: la rama de un allOf también la admite una rama hermana cerrada --------------------

HERMANA = "veridicus/contracts/otro/hermana.v1"


def _hermana(**cambios: Any) -> dict[str, Any]:
    cerrada = {**CERRADO, "$id": HERMANA, "properties": {"role": {"type": "string"}}}
    return {**cerrada, **cambios}


def _con_hermana(hermana: Any, rama: dict[str, Any] | None = None) -> dict[str, Any]:
    """Un anfitrión sin cierre ni propiedades y su allOf: la hermana y la rama de refinamiento."""
    return {"allOf": [hermana, rama or {"properties": {"role": {"enum": ["judge"]}}}]}


def test_una_rama_se_refina_con_una_hermana_cerrada_por_ref_externa_o_local(
    guardia: ModuleType,
) -> None:
    externos = guardia.ids_de([{"sin": "id"}, "no es un esquema", _hermana()])
    assert list(externos) == [HERMANA]
    por_id = _con_hermana({"$ref": f"/{HERMANA}"})
    assert guardia.comprobar_esquema("x", por_id, externos) == []
    local = {**_con_hermana({"$ref": "#/$defs/h"}), "$defs": {"h": _hermana()}}
    assert guardia.comprobar_esquema("x", local, {}) == []
    directa = _con_hermana(_hermana())
    assert guardia.comprobar_esquema("x", directa, {}) == []


def test_una_hermana_abierta_o_que_no_declara_la_propiedad_deja_la_rama_en_rojo(
    guardia: ModuleType,
) -> None:
    externos = guardia.ids_de([_hermana()])
    # Control negativo 1: la hermana no está cerrada.
    abierta = _hermana()
    del abierta["additionalProperties"]
    assert _abiertos(guardia, _con_hermana(abierta)) == [_aviso("/allOf/0"), _aviso("/allOf/1")]
    # Control negativo 2: la hermana está cerrada pero no declara la propiedad de la rama.
    sin_declarar = _hermana(properties={"otra": {"type": "string"}})
    assert _abiertos(guardia, _con_hermana(sin_declarar)) == [_aviso("/allOf/1")]
    # Una referencia que no se puede resolver no prueba nada.
    sin_resolver = _con_hermana({"$ref": "/veridicus/contracts/otro/desconocida"})
    assert guardia.comprobar_esquema("x", sin_resolver, externos) == [_aviso("/allOf/1")]
    # `if`, `then` y `else` no son hermanas de un allOf: la regla es solo para allOf.
    condicion = {
        "allOf": [_hermana()],
        "then": {"properties": {"role": {"enum": ["judge"]}}},
    }
    assert _abiertos(guardia, condicion) == [_aviso("/then")]


def test_las_condiciones_anidadas_en_una_rama_se_aplican_al_mismo_objeto_anfitrion(
    guardia: ModuleType,
) -> None:
    anidada = {"if": {"properties": {"a": {"const": "x"}}}, "then": {"properties": {"b": {}}}}
    assert _abiertos(guardia, _padre(allOf=[anidada])) == []
    sin_declarar = {"if": {"properties": {"a": {}}}, "then": {"properties": {"z": {}}}}
    assert _abiertos(guardia, _padre(allOf=[sin_declarar])) == [_aviso("/allOf/0/then")]
    # Una rama de oneOf es un objeto nuevo: sus propias condiciones se miden contra ella.
    rama = {**CERRADO, "properties": {"c": {}}, "if": {"properties": {"c": {}}}}
    assert _abiertos(guardia, _padre(oneOf=[rama])) == []
    ajena = {**CERRADO, "properties": {"c": {}}, "if": {"properties": {"a": {}}}}
    assert _abiertos(guardia, _padre(oneOf=[ajena])) == [_aviso("/oneOf/0/if")]


def test_en_oneof_y_anyof_cada_rama_es_un_objeto_que_debe_cerrarse(guardia: ModuleType) -> None:
    for clave in ("oneOf", "anyOf"):
        solo_properties = _padre(**{clave: [{"properties": {"a": {}}}]})
        assert _abiertos(guardia, solo_properties) == [_aviso(f"/{clave}/0")], clave
        cerrada = _padre(**{clave: [{**CERRADO, "properties": {"a": {}}}]})
        assert _abiertos(guardia, cerrada) == [], clave


# ---- E-13: los dos objetos abiertos de C21, por una lista explícita con su motivo ----------------

C21 = "api/anonymizer-proxy.v1.yaml"
GENERAR = "POST /v1/generate"
ADMITIDOS = {
    (C21, f"{GENERAR} /requestBody/application/json/properties/schema"),
    (C21, f"{GENERAR} /responses/200/application/json/properties/content"),
}


def test_la_lista_de_abiertos_admitidos_es_exactamente_schema_y_content_de_c21(
    guardia: ModuleType,
) -> None:
    assert set(guardia.ABIERTOS_ADMITIDOS) == ADMITIDOS
    assert all(len(motivo.split()) >= 5 for motivo in guardia.ABIERTOS_ADMITIDOS.values())


def test_sin_la_lista_c21_tiene_esos_dos_objetos_abiertos_y_con_ella_ninguno(
    guardia: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    c21 = _copia(C21)
    assert guardia.comprobar_openapi_interno(C21, c21) == []
    monkeypatch.setattr(guardia, "ABIERTOS_ADMITIDOS", {})
    sin_lista = guardia.comprobar_openapi_interno(C21, c21)
    assert sorted(sin_lista) == sorted(
        f"{C21}: {sitio}: objeto sin additionalProperties: false (§4.3)" for _, sitio in ADMITIDOS
    )


def test_ningun_otro_objeto_de_los_contratos_estrictos_queda_abierto(
    guardia: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(guardia, "ABIERTOS_ADMITIDOS", {})
    abiertos: list[str] = []
    externos = guardia.ids_de(_copia(r) for r in guardia.ESQUEMAS_ESTRICTOS)
    for relativa in guardia.ESQUEMAS_ESTRICTOS:
        abiertos.extend(guardia.comprobar_esquema(relativa, _copia(relativa), externos))
    for relativa in guardia.OPENAPI_INTERNOS:
        abiertos.extend(guardia.comprobar_openapi_interno(relativa, _copia(relativa)))
    abiertos.extend(guardia.comprobar_c1(_copia("api/console.v2.yaml")))
    assert len(abiertos) == 2
    assert all(abierto.startswith(f"{C21}: {GENERAR} ") for abierto in abiertos)


def test_lo_admitido_no_admite_otro_objeto_ni_otro_archivo(guardia: ModuleType) -> None:
    c21 = _copia(C21)
    cambiado = copy.deepcopy(c21)
    cuerpo = cambiado["paths"]["/v1/generate"]["post"]["requestBody"]["content"]["application/json"]
    cuerpo["schema"]["properties"]["schema"]["properties"] = {"hijo": {"type": "object"}}
    cuerpo["schema"]["properties"]["otro"] = {"type": "object"}
    respuesta = cambiado["paths"]["/v1/generate"]["post"]["responses"]["200"]["content"]
    respuesta["application/json"]["schema"]["properties"]["extra"] = {"type": "object"}
    esperados = [
        f"{C21}: {GENERAR} /requestBody/application/json/properties/otro: {FALTA}",
        f"{C21}: {GENERAR} /requestBody/application/json/properties/schema/properties/hijo: {FALTA}",
        f"{C21}: {GENERAR} /responses/200/application/json/properties/extra: {FALTA}",
    ]
    assert sorted(_nuevos(lambda d: guardia.comprobar_openapi_interno(C21, d), c21, cambiado)) == (
        sorted(esperados)
    )
    # La lista es por archivo: el mismo sitio en otro contrato no se admite.
    assert len(guardia.comprobar_openapi_interno("otro.yaml", c21)) == 2


# ---- P-T15-6: P-T15-5 en cada nivel anidado de la rama de refinamiento de C2 --------------------

RUNS = "queues/runs.v2.yaml"
C6 = "veridicus/contracts/analyzer/v1/entrada"
TRANSCRIPCION = "/allOf/1/properties/transcripcion"
ITEMS = f"{TRANSCRIPCION}/properties/turnos/items"


def _entrada_de_c2(runs: Any) -> dict[str, Any]:
    """El esquema de `entrada` de `RunRequested`: `allOf` con el `$ref` de C6 y la rama de T15c."""
    propiedades: dict[str, Any] = runs["components"]["messages"]["RunRequested"]["payload"][
        "properties"
    ]
    entrada: dict[str, Any] = propiedades["entrada"]
    return entrada


def _externos(guardia: ModuleType) -> dict[str, Any]:
    """Los esquemas estrictos por `$id`, copias en memoria que cada prueba puede cambiar."""
    return dict(guardia.ids_de(_copia(r) for r in guardia.ESQUEMAS_ESTRICTOS))


def _rama_c2(entrada: dict[str, Any]) -> dict[str, Any]:
    rama: dict[str, Any] = entrada["allOf"][1]
    return rama


def _aviso_c2(puntero: str) -> str:
    return f"{RUNS}: {puntero}: {FALTA}"


def test_la_rama_anidada_de_c2_se_admite_en_cada_nivel_con_su_contraparte_de_c6(
    guardia: ModuleType,
) -> None:
    entrada = _entrada_de_c2(_copia(RUNS))
    assert "$ref" in entrada["allOf"][0]
    assert guardia.comprobar_esquema(RUNS, entrada, _externos(guardia)) == []


def test_una_propiedad_de_la_rama_que_c6_no_tiene_en_ese_nivel_es_rojo(guardia: ModuleType) -> None:
    sin_c6 = {"transcripcion": TRANSCRIPCION, "items": ITEMS}
    for nivel, esperado in sin_c6.items():
        entrada = _entrada_de_c2(_copia(RUNS))
        rama = _rama_c2(entrada)["properties"]["transcripcion"]
        if nivel == "items":
            rama = rama["properties"]["turnos"]["items"]
        rama["properties"]["inventada"] = {"maxLength": 1}
        assert guardia.comprobar_esquema(RUNS, entrada, _externos(guardia)) == [
            _aviso_c2(esperado)
        ], nivel


def test_un_nivel_abierto_de_c6_deja_la_rama_de_ese_nivel_en_rojo(guardia: ModuleType) -> None:
    for nivel, esperado in {"transcripcion": TRANSCRIPCION, "items": ITEMS}.items():
        externos = _externos(guardia)
        c6 = externos[C6]
        abierto = c6["properties"]["transcripcion"]
        if nivel == "items":
            abierto = abierto["properties"]["turnos"]["items"]
        del abierto["additionalProperties"]
        entrada = _entrada_de_c2(_copia(RUNS))
        assert guardia.comprobar_esquema(RUNS, entrada, externos) == [_aviso_c2(esperado)], nivel


def test_la_contraparte_anidada_se_resuelve_con_las_referencias_locales_de_su_documento(
    guardia: ModuleType,
) -> None:
    externos = _externos(guardia)
    c6 = externos[C6]
    c6["$defs"] = {"transcripcion": c6["properties"]["transcripcion"]}
    c6["properties"]["transcripcion"] = {"$ref": "#/$defs/transcripcion"}
    entrada = _entrada_de_c2(_copia(RUNS))
    assert guardia.comprobar_esquema(RUNS, entrada, externos) == []


def test_una_condicion_dentro_de_la_rama_anidada_no_hereda_la_contraparte(
    guardia: ModuleType,
) -> None:
    entrada = _entrada_de_c2(_copia(RUNS))
    nivel = _rama_c2(entrada)["properties"]["transcripcion"]
    nivel["allOf"] = [{"properties": {"turnos": {}}}]
    assert guardia.comprobar_esquema(RUNS, entrada, _externos(guardia)) == [
        _aviso_c2(f"{TRANSCRIPCION}/allOf/0")
    ]


# ---- P-T15-7: los valores de un mapa con propertyNames.enum llevan `type` o `$ref` ----------------


def test_los_valores_de_un_mapa_cerrado_por_enum_exigen_type_o_ref(guardia: ModuleType) -> None:
    claves = {"propertyNames": {"enum": ["a"]}}
    for valores in ({"description": "libre"}, {"minLength": 0}):
        mapa = {"type": "object", **claves, "additionalProperties": valores}
        assert _abiertos(guardia, mapa) == [_aviso("")], valores
    con_type = {"type": "object", **claves, "additionalProperties": {"type": ["string", "null"]}}
    assert _abiertos(guardia, con_type) == []
    con_ref = {
        "type": "object",
        **claves,
        "additionalProperties": {"$ref": "#/$defs/valor"},
        "$defs": {"valor": {"type": "integer"}},
    }
    assert _abiertos(guardia, con_ref) == []
