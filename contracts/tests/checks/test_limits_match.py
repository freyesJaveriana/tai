"""Guardia de marcas y catálogo C25 en los dos sentidos (§4.4; NFR10.7, NFR10.14; R-05 de la revisión 1).

Los controles negativos trabajan sobre copias en memoria del catálogo y de los contratos reales y
comparan con el resultado sobre los originales: la guardia solo debe añadir el hallazgo que provoca
la prueba.
"""

import copy
import shutil
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from helpers import CONTRACTS_ROOT, importar_o_fallar, load_contract

pytestmark = pytest.mark.c1

CONSOLA = "api/console.v2.yaml"


@pytest.fixture
def guardia() -> ModuleType:
    return importar_o_fallar("veridicus_contracts.checks.limits_match", "T15, paso 16")


def _estado(guardia: ModuleType) -> tuple[dict[str, Any], dict[str, Any]]:
    # `load_contract` ya entrega una copia nueva en cada llamada (loaders._copia): no se copia dos veces.
    catalogo = load_contract("limits.v1.yaml")["limits"]
    documentos = {r: load_contract(r) for r in guardia.ARCHIVOS}
    return catalogo, documentos


def _nuevos(
    guardia: ModuleType, cambiar: Callable[[dict[str, Any], dict[str, Any]], None]
) -> list[str]:
    original = guardia.comprobar_documentos(*_estado(guardia))
    catalogo, documentos = _estado(guardia)
    cambiar(catalogo, documentos)
    return sorted(
        p for p in guardia.comprobar_documentos(catalogo, documentos) if p not in original
    )


def _propiedades_de_crear_usuario(documentos: dict[str, Any]) -> dict[str, Any]:
    cuerpo = documentos[CONSOLA]["paths"]["/users"]["post"]["requestBody"]
    propiedades: dict[str, Any] = cuerpo["content"]["application/json"]["schema"]["properties"]
    return propiedades


def test_los_contratos_versionados_coinciden_con_el_catalogo(guardia: ModuleType) -> None:
    assert guardia.comprobar(CONTRACTS_ROOT) == []


def test_el_valor_del_contrato_debe_ser_el_del_catalogo(guardia: ModuleType) -> None:
    def cambiar(catalogo: dict[str, Any], documentos: dict[str, Any]) -> None:
        _propiedades_de_crear_usuario(documentos)["username"]["maxLength"] = 33
        documentos["queues/speech.v2.yaml"]["components"]["messages"]["AudioToTranscribe"][
            "payload"
        ]["properties"]["audio_base64"]["maxLength"] = 1

    assert _nuevos(guardia, cambiar) == [
        (
            "api/console.v2.yaml: /paths/~1users/post/requestBody/content/application~1json/schema/"
            "properties/username: valor distinto del catálogo C25 (username_max_chars, §4.4 b)"
        ),
        (
            "queues/speech.v2.yaml: /components/messages/AudioToTranscribe/payload/properties/"
            "audio_base64: valor distinto del catálogo C25 (audio_base64_max_chars, §4.4 b)"
        ),
    ]


def test_la_unidad_debe_ser_coherente_con_la_palabra_clave(guardia: ModuleType) -> None:
    def cambiar(catalogo: dict[str, Any], documentos: dict[str, Any]) -> None:
        catalogo["turn_max_chars"]["unit"] = "bytes"
        catalogo["import_body_max_bytes"]["unit"] = "chars"
        catalogo["web_session_idle_s"]["unit"] = "ms"
        propiedad = _propiedades_de_crear_usuario(documentos)["password"]
        del propiedad["maxLength"]
        propiedad["maxItems"] = 128
        catalogo["password_max_chars"]["unit"] = "chars"

    assert _nuevos(guardia, cambiar) == [
        (
            "api/console.v2.yaml: /components/securitySchemes/sessionCookie/x-veridicus-cookie: la "
            "unidad de web_session_idle_s debe ser s con x-veridicus-cookie (§4.4 c)"
        ),
        (
            "api/console.v2.yaml: /paths/~1sessions~1import/post/requestBody: la unidad de "
            "import_body_max_bytes debe ser bytes con x-veridicus-max-bytes (§4.4 c)"
        ),
        (
            "api/console.v2.yaml: /paths/~1sessions~1{session_id}~1turns/post/requestBody/content/"
            "application~1json/schema/properties/texto: la unidad de turn_max_chars debe ser chars "
            "con maxLength (§4.4 c)"
        ),
        (
            "api/console.v2.yaml: /paths/~1users/post/requestBody/content/application~1json/schema/"
            "properties/password: la unidad de password_max_chars debe ser turns o runs con maxItems "
            "(§4.4 c)"
        ),
        # T15c (E-16) marcó `turnos[].texto` de `RunRequested.entrada` con turn_max_chars.
        (
            "queues/runs.v2.yaml: /components/messages/RunRequested/payload/properties/entrada/allOf/1/"
            "properties/transcripcion/properties/turnos/items/properties/texto: la unidad de "
            "turn_max_chars debe ser chars con maxLength (§4.4 c)"
        ),
        # T15b (E-15) marcó `TranscriptResult.text` con turn_max_chars.
        (
            "queues/speech.v2.yaml: /components/messages/TranscriptResult/payload/properties/text: la "
            "unidad de turn_max_chars debe ser chars con maxLength (§4.4 c)"
        ),
    ]


def test_maxitems_acepta_la_unidad_turns_y_la_unidad_runs_y_ninguna_otra(
    guardia: ModuleType,
) -> None:
    def cambiar(catalogo: dict[str, Any], documentos: dict[str, Any]) -> None:
        propiedades = _propiedades_de_crear_usuario(documentos)
        propiedades["turnos"] = {
            "type": "array",
            "maxItems": 2000,
            "x-veridicus-limit": "transcript_max_turns",
        }
        propiedades["corridas"] = {
            "type": "array",
            "maxItems": 3,
            "x-veridicus-limit": "report_per_run_items",
        }
        catalogo["transcript_max_turns"]["used_in"] = ["C1"]
        catalogo["report_per_run_items"]["used_in"] = ["C1", "C19"]

    assert _nuevos(guardia, cambiar) == []

    def con_otra_unidad(catalogo: dict[str, Any], documentos: dict[str, Any]) -> None:
        cambiar(catalogo, documentos)
        catalogo["report_per_run_items"]["unit"] = "suggestions"

    assert _nuevos(guardia, con_otra_unidad) == [
        (
            "api/console.v2.yaml: /paths/~1users/post/requestBody/content/application~1json/schema/"
            "properties/corridas: la unidad de report_per_run_items debe ser turns o runs con maxItems "
            "(§4.4 c)"
        ),
        (
            "cli/report.schema.v2.yaml: /$defs/metric_count/properties/per_run: la unidad de "
            "report_per_run_items debe ser turns o runs con maxItems (§4.4 c)"
        ),
        (
            "cli/report.schema.v2.yaml: /$defs/metric_ratio/properties/per_run: la unidad de "
            "report_per_run_items debe ser turns o runs con maxItems (§4.4 c)"
        ),
    ]


# ---- F-04: un texto sin tope se encuentra en toda forma de subesquema ----------------------------

BASE = "/paths/~1users/post/requestBody/content/application~1json/schema/properties/nota"
TEXTO = "campo de texto sin x-veridicus-limit (§4.4 a)"
FORMAS_DE_TEXTO: dict[str, tuple[Callable[[], dict[str, Any]], list[str]]] = {
    "oneOf": (lambda: {"oneOf": [{"type": "string"}]}, ["/oneOf/0"]),
    "anyOf": (lambda: {"anyOf": [{"type": "string"}, {"type": "integer"}]}, ["/anyOf/0"]),
    "allOf": (lambda: {"allOf": [{"type": "string"}]}, ["/allOf/0"]),
    "if_then_else": (
        lambda: {
            "if": {"type": "string"},
            "then": {"type": "string"},
            "else": {"type": "string"},
        },
        ["/else", "/if", "/then"],
    ),
    "patternProperties": (
        lambda: {"type": "object", "patternProperties": {"^a": {"type": "string"}}},
        ["/patternProperties/^a"],
    ),
    "additionalProperties": (
        lambda: {"type": "object", "additionalProperties": {"type": "string"}},
        ["/additionalProperties"],
    ),
    "prefixItems": (
        lambda: {"type": "array", "prefixItems": [{"type": "string"}]},
        ["/prefixItems/0"],
    ),
    "type_en_lista": (lambda: {"type": ["string", "null"]}, [""]),
}


@pytest.mark.parametrize("forma", sorted(FORMAS_DE_TEXTO))
def test_un_texto_sin_tope_dentro_de_una_forma_de_subesquema_es_rojo(
    guardia: ModuleType, forma: str
) -> None:
    construir, sitios = FORMAS_DE_TEXTO[forma]

    def cambiar(catalogo: dict[str, Any], documentos: dict[str, Any]) -> None:
        _propiedades_de_crear_usuario(documentos)["nota"] = construir()

    esperados = [f"{CONSOLA}: {BASE}{sitio}: {TEXTO}" for sitio in sitios]
    assert _nuevos(guardia, cambiar) == esperados


def test_un_def_solo_cuenta_si_alguien_lo_referencia(guardia: ModuleType) -> None:
    def cambiar(catalogo: dict[str, Any], documentos: dict[str, Any]) -> None:
        propiedades = _propiedades_de_crear_usuario(documentos)
        propiedades["con_defs"] = {"type": "object", "$defs": {"suelto": {"type": "string"}}}
        propiedades["via_ref"] = {"$ref": "#/components/schemas/Suelto"}
        documentos[CONSOLA]["components"]["schemas"]["Suelto"] = {"type": "string"}

    assert _nuevos(guardia, cambiar) == [
        f"{CONSOLA}: {BASE[: -len('nota')]}via_ref: {TEXTO}",
    ]


def test_un_texto_acotado_dentro_de_una_forma_de_subesquema_no_es_rojo(
    guardia: ModuleType,
) -> None:
    marcado = {
        "type": ["string", "null"],
        "maxLength": 32,
        "x-veridicus-limit": "username_max_chars",
    }

    def cambiar(catalogo: dict[str, Any], documentos: dict[str, Any]) -> None:
        propiedades = _propiedades_de_crear_usuario(documentos)
        propiedades["nota"] = {"oneOf": [copy.deepcopy(marcado), {"type": "null"}]}
        propiedades["otra"] = {"type": ["integer", "null"]}
        propiedades["fija"] = {"anyOf": [{"type": "string", "enum": ["a"]}]}

    assert _nuevos(guardia, cambiar) == []


def test_limite_huerfano_en_los_dos_sentidos(guardia: ModuleType) -> None:
    def cambiar(catalogo: dict[str, Any], documentos: dict[str, Any]) -> None:
        catalogo["retention_max_days"]["used_in"] = ["C1"]
        catalogo["cursor_max_chars"]["used_in"] = []
        catalogo["poll_interval_s"]["used_in"] = ["C3"]
        _propiedades_de_crear_usuario(documentos)["username"]["x-veridicus-limit"] = "no_existe"

    assert _nuevos(guardia, cambiar) == [
        (
            "api/console.v2.yaml: /components/schemas/Cursor: la marca cursor_max_chars no está en "
            "used_in de C25 para C1 (§4.4, comprobación inversa)"
        ),
        (
            "api/console.v2.yaml: /paths/~1users/post/requestBody/content/application~1json/schema/"
            "properties/username: la marca no_existe no es una cifra de C25 (§4.4)"
        ),
        "poll_interval_s: used_in nombra C3, que la guardia no recorre (§4.4)",
        "retention_max_days: used_in nombra C1 y C1 no la marca (§4.4, comprobación inversa)",
    ]


def test_todo_campo_de_texto_de_un_cuerpo_o_un_mensaje_lleva_su_marca(guardia: ModuleType) -> None:
    def cambiar(catalogo: dict[str, Any], documentos: dict[str, Any]) -> None:
        _propiedades_de_crear_usuario(documentos)["nota"] = {"type": "string"}
        _propiedades_de_crear_usuario(documentos)["etiquetas"] = {
            "type": "array",
            "items": {"type": "string"},
        }
        _propiedades_de_crear_usuario(documentos)["fecha"] = {"type": "string", "format": "date"}
        _sin_tope_de_runs(catalogo, documentos)  # P-T15-8: el tope del payload acotaría el texto
        runs = documentos["queues/runs.v2.yaml"]["components"]["messages"]["RunRequested"]
        runs["payload"]["properties"]["comentario"] = {"type": "string"}
        runs["payload"]["properties"]["vuelta"] = {
            "$ref": "#/components/messages/RunRequested/payload"
        }
        runs["payload"]["properties"]["lista"] = "no es un esquema"

    nuevos = _nuevos(guardia, cambiar)
    assert nuevos == [
        (
            "api/console.v2.yaml: /paths/~1users/post/requestBody/content/application~1json/schema/"
            "properties/etiquetas/items: campo de texto sin x-veridicus-limit (§4.4 a)"
        ),
        (
            "api/console.v2.yaml: /paths/~1users/post/requestBody/content/application~1json/schema/"
            "properties/nota: campo de texto sin x-veridicus-limit (§4.4 a)"
        ),
        (
            "queues/runs.v2.yaml: /components/messages/RunRequested/payload/properties/comentario: "
            "campo de texto sin x-veridicus-limit (§4.4 a)"
        ),
    ]


def test_un_cuerpo_con_tope_de_bytes_acota_sus_textos(guardia: ModuleType) -> None:
    documentos = _estado(guardia)[1]
    transcripcion = documentos[CONSOLA]["paths"]["/sessions/{session_id}/transcript"]["post"]
    cuerpo = transcripcion["requestBody"]
    assert "x-veridicus-max-bytes" in cuerpo
    assert cuerpo["content"]["application/json"]["schema"]["properties"]["text"] == {
        "type": "string",
        "minLength": 1,
    }

    def quitar_tope(catalogo: dict[str, Any], docs: dict[str, Any]) -> None:
        pegado = docs[CONSOLA]["paths"]["/sessions/{session_id}/transcript"]["post"]
        del pegado["requestBody"]["x-veridicus-max-bytes"]

    assert _nuevos(guardia, quitar_tope) == [
        (
            "api/console.v2.yaml: /paths/~1sessions~1{session_id}~1transcript/post/requestBody/content/"
            "application~1json/schema/properties/text: campo de texto sin x-veridicus-limit (§4.4 a)"
        ),
        "transcript_body_max_bytes: used_in nombra C1 y C1 no la marca (§4.4, comprobación inversa)",
    ]


def test_todo_maxlength_y_maxitems_llevan_marca_y_toda_marca_su_palabra_clave(
    guardia: ModuleType,
) -> None:
    def cambiar(catalogo: dict[str, Any], documentos: dict[str, Any]) -> None:
        llamada = documentos["model_calls/model-call.v1.yaml"]
        llamada["properties"]["role"]["x-veridicus-limit"] = "report_token_max_chars"
        propiedad = _propiedades_de_crear_usuario(documentos)
        propiedad["lista"] = {"type": "array", "maxItems": 3}
        propiedad["sin_palabra"] = {"type": "string", "x-veridicus-limit": "username_max_chars"}

    nuevos = _nuevos(guardia, cambiar)
    assert nuevos == [
        (
            "api/console.v2.yaml: /paths/~1users/post/requestBody/content/application~1json/schema/"
            "properties/lista: maxItems sin x-veridicus-limit (§4.4)"
        ),
        (
            "api/console.v2.yaml: /paths/~1users/post/requestBody/content/application~1json/schema/"
            "properties/sin_palabra: la marca username_max_chars no acompaña a maxLength ni a maxItems "
            "(§4.4)"
        ),
        # T15b (E-11) marcó `role`: al cambiarle la marca, la de C25 queda sin su uso.
        "model_call_role_max_chars: used_in nombra C19 y C19 no la marca (§4.4, comprobación inversa)",
        (
            "model_calls/model-call.v1.yaml: /properties/role: valor distinto del catálogo C25 "
            "(report_token_max_chars, §4.4 b)"
        ),
    ]


def test_la_ruta_de_voz_no_exige_marca_en_tema_ni_used_in(guardia: ModuleType) -> None:
    # K-15: §4.4 (a) no incluye la ruta interna de voz, así que `tema` no necesita marca.
    voz = load_contract("api/speech-internal.v1.yaml")
    tema = voz["paths"]["/internal/v1/speech"]["post"]["requestBody"]["content"][
        "application/json"
    ]["schema"]["properties"]["tema"]
    assert tema == {"type": "string", "minLength": 1}
    assert not any("speech-internal" in p for p in guardia.comprobar_documentos(*_estado(guardia)))

    # La ruta no tiene un C<n>: su marca no se contrasta con used_in, pero sí con el valor y la unidad.
    def cambiar(catalogo: dict[str, Any], documentos: dict[str, Any]) -> None:
        catalogo["speech_audio_max_bytes"]["unit"] = "chars"

    assert _nuevos(guardia, cambiar) == [
        (
            "api/speech-internal.v1.yaml: /paths/~1internal~1v1~1speech/post/responses/200/content/"
            "audio~1wav: la unidad de speech_audio_max_bytes debe ser bytes con x-veridicus-max-bytes "
            "(§4.4 c)"
        )
    ]


def test_una_cookie_sin_una_de_sus_dos_cifras_deja_huerfana_la_entrada(
    guardia: ModuleType,
) -> None:
    def cambiar(catalogo: dict[str, Any], documentos: dict[str, Any]) -> None:
        esquema = documentos[CONSOLA]["components"]["securitySchemes"]["sessionCookie"]
        del esquema["x-veridicus-cookie"]["idle_limit"]

    assert _nuevos(guardia, cambiar) == [
        "web_session_idle_s: used_in nombra C1 y C1 no la marca (§4.4, comprobación inversa)"
    ]


# ---- P-T15-6: la regla (a) sigue los `$ref` externos por `$id` ------------------------------------

RUNS = "queues/runs.v2.yaml"
C6 = "analyzer/v1/entrada.schema.json"
ENTRADA = "/components/messages/RunRequested/payload/properties/entrada"
TEXTO_DE_TURNO = (
    f"{ENTRADA}/allOf/0/properties/transcripcion/properties/turnos/items/properties/texto"
)
EXTERNO = "veridicus/contracts/externo/x.v1"


def _con_c6(
    cambiar: Callable[[dict[str, Any], dict[str, Any]], None],
) -> Callable[[dict[str, Any], dict[str, Any]], None]:
    """Añade C6 a los documentos antes de aplicar el cambio (la guardia lo busca por `$id`)."""

    def con_c6(catalogo: dict[str, Any], documentos: dict[str, Any]) -> None:
        documentos.setdefault(C6, copy.deepcopy(load_contract(C6)))
        cambiar(catalogo, documentos)

    return con_c6


def _nuevos_con_c6(
    guardia: ModuleType, cambiar: Callable[[dict[str, Any], dict[str, Any]], None]
) -> list[str]:
    """Como `_nuevos`, pero el original y el cambiado llevan C6."""
    catalogo, documentos = _estado(guardia)
    _con_c6(lambda c, d: None)(catalogo, documentos)
    original = guardia.comprobar_documentos(catalogo, documentos)
    catalogo, documentos = _estado(guardia)
    _con_c6(cambiar)(catalogo, documentos)
    return sorted(
        p for p in guardia.comprobar_documentos(catalogo, documentos) if p not in original
    )


def _externo() -> dict[str, Any]:
    return {
        "$id": EXTERNO,
        "type": "object",
        "additionalProperties": False,
        "properties": {"a": {"$ref": "#/$defs/texto"}},
        "$defs": {"texto": {"type": "string"}},
    }


def _payload_de_runs(documentos: dict[str, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = documentos[RUNS]["components"]["messages"]["RunRequested"]["payload"]
    return payload


def _sin_tope_de_runs(catalogo: dict[str, Any], documentos: dict[str, Any]) -> None:
    """Quita el tope del `payload` de `RunRequested` y su `used_in`: una copia sin tope (P-T15-8)."""
    del _payload_de_runs(documentos)["x-veridicus-max-bytes"]
    catalogo["run_message_max_bytes"]["used_in"] = []


def test_c2_con_la_rama_de_refinamiento_da_por_bueno_el_texto_de_turno_de_c6(
    guardia: ModuleType,
) -> None:
    catalogo, documentos = _estado(guardia)
    _con_c6(lambda c, d: None)(catalogo, documentos)
    assert [p for p in guardia.comprobar_documentos(catalogo, documentos) if "/turnos/" in p] == []


def test_c2_sin_la_rama_de_refinamiento_el_texto_de_turno_de_c6_es_rojo(
    guardia: ModuleType,
) -> None:
    def cambiar(catalogo: dict[str, Any], documentos: dict[str, Any]) -> None:
        entrada = _payload_de_runs(documentos)["properties"]["entrada"]
        entrada["allOf"] = entrada["allOf"][:1]

    assert _nuevos_con_c6(guardia, cambiar) == [
        f"{RUNS}: {TEXTO_DE_TURNO}: campo de texto sin x-veridicus-limit (§4.4 a)",
        "turn_max_chars: used_in nombra C2 y C2 no la marca (§4.4, comprobación inversa)",
    ]


def test_un_ref_externo_se_sigue_con_las_referencias_locales_de_su_propio_documento(
    guardia: ModuleType,
) -> None:
    def cambiar(catalogo: dict[str, Any], documentos: dict[str, Any]) -> None:
        _sin_tope_de_runs(catalogo, documentos)  # P-T15-8
        documentos["externo.schema.json"] = _externo()
        _payload_de_runs(documentos)["properties"]["ext"] = {"$ref": f"/{EXTERNO}"}

    assert _nuevos(guardia, cambiar) == [
        (
            f"{RUNS}: /components/messages/RunRequested/payload/properties/ext/properties/a: "
            "campo de texto sin x-veridicus-limit (§4.4 a)"
        )
    ]


def test_un_ref_externo_que_no_se_resuelve_no_aporta_textos(guardia: ModuleType) -> None:
    def cambiar(catalogo: dict[str, Any], documentos: dict[str, Any]) -> None:
        documentos["externo.schema.json"] = _externo()
        _payload_de_runs(documentos)["properties"]["ext"] = {"$ref": "/veridicus/contracts/otro"}

    assert _nuevos(guardia, cambiar) == []


def test_la_marca_de_una_rama_hermana_en_la_misma_posicion_acota_el_texto_externo(
    guardia: ModuleType,
) -> None:
    marca = {"maxLength": 32, "x-veridicus-limit": "username_max_chars"}

    def cambiar(catalogo: dict[str, Any], documentos: dict[str, Any]) -> None:
        documentos["externo.schema.json"] = _externo()
        catalogo["username_max_chars"]["used_in"] = ["C1", "C2"]
        _payload_de_runs(documentos)["properties"]["ext"] = {
            "allOf": [{"$ref": f"/{EXTERNO}"}, {"properties": {"a": marca}}]
        }

    assert _nuevos(guardia, cambiar) == []

    def en_otra_posicion(catalogo: dict[str, Any], documentos: dict[str, Any]) -> None:
        cambiar(catalogo, documentos)
        _sin_tope_de_runs(catalogo, documentos)  # P-T15-8
        _payload_de_runs(documentos)["properties"]["ext"]["allOf"][1] = {
            "properties": {"b": {"properties": {"a": marca}}}
        }

    assert _nuevos(guardia, en_otra_posicion) == [
        (
            f"{RUNS}: /components/messages/RunRequested/payload/properties/ext/allOf/0/properties/a: "
            "campo de texto sin x-veridicus-limit (§4.4 a)"
        )
    ]


def test_el_tope_de_bytes_de_run_requested_se_comprueba_en_valor_y_en_la_inversa(
    guardia: ModuleType,
) -> None:
    payload = "/components/messages/RunRequested/payload"

    def con_otra_unidad(catalogo: dict[str, Any], documentos: dict[str, Any]) -> None:
        catalogo["run_message_max_bytes"]["unit"] = "chars"

    assert _nuevos(guardia, con_otra_unidad) == [
        (
            f"{RUNS}: {payload}: la unidad de run_message_max_bytes debe ser bytes con "
            "x-veridicus-max-bytes (§4.4 c)"
        )
    ]

    def sin_used_in(catalogo: dict[str, Any], documentos: dict[str, Any]) -> None:
        catalogo["run_message_max_bytes"]["used_in"] = []

    assert _nuevos(guardia, sin_used_in) == [
        (
            f"{RUNS}: {payload}: la marca run_message_max_bytes no está en used_in de C25 para C2 "
            "(§4.4, comprobación inversa)"
        )
    ]

    def sin_marca(catalogo: dict[str, Any], documentos: dict[str, Any]) -> None:
        del _payload_de_runs(documentos)["x-veridicus-max-bytes"]

    assert _nuevos(guardia, sin_marca) == [
        "run_message_max_bytes: used_in nombra C2 y C2 no la marca (§4.4, comprobación inversa)"
    ]


# ---- E-18: el tope de bytes del `payload` acota los textos del mensaje, como el del `requestBody` ----

CINCO_DE_C6 = (
    "transcripcion/properties/entrevista",
    "transcripcion/properties/consentimiento/properties/version_texto",
    "transcripcion/properties/consentimiento/properties/constancia",
    "transcripcion/properties/consentimiento/properties/constancia_mandato",
)


def _cinco_textos_de_c6() -> list[str]:
    en_transcripcion = [
        f"{RUNS}: {ENTRADA}/allOf/0/properties/{sitio}: {TEXTO}" for sitio in CINCO_DE_C6
    ]
    return [*en_transcripcion, f"{RUNS}: {ENTRADA}/allOf/0/properties/perfil: {TEXTO}"]


def test_c2_con_el_tope_del_payload_los_cinco_textos_de_c6_no_son_rojo(guardia: ModuleType) -> None:
    catalogo, documentos = _estado(guardia)
    _con_c6(lambda c, d: None)(catalogo, documentos)
    assert "x-veridicus-max-bytes" in _payload_de_runs(documentos)
    problemas = guardia.comprobar_documentos(catalogo, documentos)
    assert [p for p in problemas if "/allOf/0/" in p] == []


def test_c2_sin_el_tope_del_payload_los_cinco_textos_de_c6_son_rojo(guardia: ModuleType) -> None:
    def cambiar(catalogo: dict[str, Any], documentos: dict[str, Any]) -> None:
        del _payload_de_runs(documentos)["x-veridicus-max-bytes"]

    esperados = [
        *_cinco_textos_de_c6(),
        "run_message_max_bytes: used_in nombra C2 y C2 no la marca (§4.4, comprobación inversa)",
    ]
    assert _nuevos_con_c6(guardia, cambiar) == sorted(esperados)


def test_la_lista_de_marca_propia_obligatoria_es_exactamente_turnos_texto_de_run_requested(
    guardia: ModuleType,
) -> None:
    # P-T15-8: añadir otra entrada requiere una precisión del humano.
    lista = getattr(guardia, "MARCA_PROPIA_OBLIGATORIA", {})
    assert set(lista) == {(RUNS, "RunRequested", "entrada.transcripcion.turnos[].texto")}
    assert all(len(motivo.split()) >= 5 for motivo in lista.values())


def test_c5_un_texto_sin_marca_solo_se_acota_con_el_tope_de_bytes_del_payload(
    guardia: ModuleType,
) -> None:
    nota = "/components/messages/TranscriptResult/payload/properties/nota"

    def sin_tope(catalogo: dict[str, Any], documentos: dict[str, Any]) -> None:
        mensaje = documentos["queues/speech.v2.yaml"]["components"]["messages"]["TranscriptResult"]
        mensaje["payload"]["properties"]["nota"] = {"type": "string"}

    assert _nuevos(guardia, sin_tope) == [f"queues/speech.v2.yaml: {nota}: {TEXTO}"]

    def con_tope(catalogo: dict[str, Any], documentos: dict[str, Any]) -> None:
        sin_tope(catalogo, documentos)
        mensaje = documentos["queues/speech.v2.yaml"]["components"]["messages"]["TranscriptResult"]
        mensaje["payload"]["x-veridicus-max-bytes"] = "run_message_max_bytes"
        catalogo["run_message_max_bytes"]["used_in"] = ["C2", "C5"]

    assert _nuevos(guardia, con_tope) == []


# ---- Ronda 4, F-01: solo cuentan las marcas del propio nodo o de ramas de `allOf` ------------------


@pytest.mark.parametrize("clave", ["oneOf", "anyOf", "if", "then", "else", "not"])
def test_una_marca_que_solo_esta_en_una_rama_que_no_es_de_allof_no_acota_el_texto(
    guardia: ModuleType, clave: str
) -> None:
    def cambiar(catalogo: dict[str, Any], documentos: dict[str, Any]) -> None:
        entrada = _payload_de_runs(documentos)["properties"]["entrada"]
        rama = entrada["allOf"][1]
        alternativa = [rama, {}] if clave in ("oneOf", "anyOf") else rama
        entrada["allOf"][1] = {clave: alternativa}

    # La marca sigue existiendo (no hay hallazgo de la inversa), pero no acota la instancia.
    assert _nuevos_con_c6(guardia, cambiar) == [
        f"{RUNS}: {TEXTO_DE_TURNO}: campo de texto sin x-veridicus-limit (§4.4 a)"
    ]


def test_un_esquema_compartido_se_revisa_en_cada_ruta_de_la_instancia(guardia: ModuleType) -> None:
    marca = {"maxLength": 32, "x-veridicus-limit": "username_max_chars"}
    mensaje = "/components/messages/TranscriptResult/payload/properties"

    def cambiar(catalogo: dict[str, Any], documentos: dict[str, Any]) -> None:
        voz = documentos["queues/speech.v2.yaml"]
        voz["components"].setdefault("schemas", {})["T"] = {"type": "string"}
        propiedades = voz["components"]["messages"]["TranscriptResult"]["payload"]["properties"]
        propiedades["p1"] = {"allOf": [{"$ref": "#/components/schemas/T"}, marca]}
        propiedades["p2"] = {"$ref": "#/components/schemas/T"}
        catalogo["username_max_chars"]["used_in"] = ["C1", "C5"]

    assert _nuevos(guardia, cambiar) == [f"queues/speech.v2.yaml: {mensaje}/p2: {TEXTO}"]


# ---- Ronda 4, F-02: el tope de bytes también se lee en el tipo de contenido -----------------------


def _mover_el_tope_al_tipo_de_contenido(
    documento: dict[str, Any], ruta: str, metodo: str, medio: str
) -> None:
    cuerpo = documento["paths"][ruta][metodo]["requestBody"]
    cuerpo["content"][medio]["x-veridicus-max-bytes"] = cuerpo.pop("x-veridicus-max-bytes")


def test_el_tope_de_bytes_en_el_tipo_de_contenido_acota_los_textos_de_c1(
    guardia: ModuleType,
) -> None:
    ruta = "/sessions/{session_id}/transcript"

    def en_el_tipo(catalogo: dict[str, Any], documentos: dict[str, Any]) -> None:
        _mover_el_tope_al_tipo_de_contenido(documentos[CONSOLA], ruta, "post", "application/json")

    assert _nuevos(guardia, en_el_tipo) == []

    def en_ningun_sitio(catalogo: dict[str, Any], documentos: dict[str, Any]) -> None:
        del documentos[CONSOLA]["paths"][ruta]["post"]["requestBody"]["x-veridicus-max-bytes"]

    assert _nuevos(guardia, en_ningun_sitio) == [
        (
            f"{CONSOLA}: /paths/~1sessions~1{{session_id}}~1transcript/post/requestBody/content/"
            f"application~1json/schema/properties/text: {TEXTO}"
        ),
        "transcript_body_max_bytes: used_in nombra C1 y C1 no la marca (§4.4, comprobación inversa)",
    ]


def test_el_tope_de_bytes_en_el_tipo_de_contenido_acota_los_textos_de_c21(
    guardia: ModuleType,
) -> None:
    c21 = "api/anonymizer-proxy.v1.yaml"

    def en_el_tipo(catalogo: dict[str, Any], documentos: dict[str, Any]) -> None:
        _mover_el_tope_al_tipo_de_contenido(
            documentos[c21], "/v1/generate", "post", "application/json"
        )

    assert _nuevos(guardia, en_el_tipo) == []

    def en_ningun_sitio(catalogo: dict[str, Any], documentos: dict[str, Any]) -> None:
        cuerpo = documentos[c21]["paths"]["/v1/generate"]["post"]["requestBody"]
        del cuerpo["x-veridicus-max-bytes"]

    contenido = "properties/messages/items/properties/content"
    assert _nuevos(guardia, en_ningun_sitio) == [
        "anonymizer_request_max_bytes: used_in nombra C21 y C21 no la marca (§4.4, comprobación inversa)",
        (
            f"{c21}: /paths/~1v1~1generate/post/requestBody/content/application~1json/schema/"
            f"{contenido}: {TEXTO}"
        ),
    ]


# ---- Ronda 5, F-01: cada segmento de la ruta lleva su clase ---------------------------------------

MARCA_DE_USUARIO = {"maxLength": 32, "x-veridicus-limit": "username_max_chars"}
PAYLOAD_DE_VOZ = "/components/messages/TranscriptResult/payload/properties"


def _propiedades_de_voz(documentos: dict[str, Any]) -> dict[str, Any]:
    mensaje = documentos["queues/speech.v2.yaml"]["components"]["messages"]["TranscriptResult"]
    propiedades: dict[str, Any] = mensaje["payload"]["properties"]
    return propiedades


def test_una_marca_bajo_una_propiedad_llamada_items_no_acota_los_elementos_del_arreglo(
    guardia: ModuleType,
) -> None:
    def cambiar(catalogo: dict[str, Any], documentos: dict[str, Any]) -> None:
        catalogo["username_max_chars"]["used_in"] = ["C1", "C5"]
        _propiedades_de_voz(documentos)["l"] = {
            "type": "array",
            "items": {"type": "string"},
            "allOf": [{"properties": {"items": MARCA_DE_USUARIO}}],
        }

    assert _nuevos(guardia, cambiar) == [
        f"queues/speech.v2.yaml: {PAYLOAD_DE_VOZ}/l/items: {TEXTO}"
    ]


def test_una_marca_bajo_una_propiedad_llamada_additionalproperties_no_acota_los_valores(
    guardia: ModuleType,
) -> None:
    def cambiar(catalogo: dict[str, Any], documentos: dict[str, Any]) -> None:
        catalogo["username_max_chars"]["used_in"] = ["C1", "C5"]
        _propiedades_de_voz(documentos)["m"] = {
            "type": "object",
            "additionalProperties": {"type": "string"},
            "allOf": [{"properties": {"additionalProperties": MARCA_DE_USUARIO}}],
        }

    assert _nuevos(guardia, cambiar) == [
        f"queues/speech.v2.yaml: {PAYLOAD_DE_VOZ}/m/additionalProperties: {TEXTO}"
    ]


def test_la_rama_de_c2_con_turnos_properties_items_no_acota_turnos_texto(
    guardia: ModuleType,
) -> None:
    def cambiar(catalogo: dict[str, Any], documentos: dict[str, Any]) -> None:
        entrada = _payload_de_runs(documentos)["properties"]["entrada"]
        turnos = entrada["allOf"][1]["properties"]["transcripcion"]["properties"]["turnos"]
        turnos["properties"] = {"items": turnos.pop("items")}

    assert _nuevos_con_c6(guardia, cambiar) == [
        f"{RUNS}: {TEXTO_DE_TURNO}: campo de texto sin x-veridicus-limit (§4.4 a)"
    ]


def test_la_lista_de_marca_propia_distingue_una_propiedad_items_de_la_palabra_clave(
    guardia: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    voz = "queues/speech.v2.yaml"
    monkeypatch.setattr(
        guardia,
        "MARCA_PROPIA_OBLIGATORIA",
        {(voz, "TranscriptResult", "l[]"): "los elementos de l llevan su propio tope"},
    )

    def con_tope(catalogo: dict[str, Any], documentos: dict[str, Any]) -> None:
        mensaje = documentos[voz]["components"]["messages"]["TranscriptResult"]
        mensaje["payload"]["x-veridicus-max-bytes"] = "run_message_max_bytes"
        catalogo["run_message_max_bytes"]["used_in"] = ["C2", "C5"]

    def arreglo(catalogo: dict[str, Any], documentos: dict[str, Any]) -> None:
        con_tope(catalogo, documentos)
        _propiedades_de_voz(documentos)["l"] = {"type": "array", "items": {"type": "string"}}

    assert _nuevos(guardia, arreglo) == [f"{voz}: {PAYLOAD_DE_VOZ}/l/items: {TEXTO}"]

    def objeto_con_propiedad_items(catalogo: dict[str, Any], documentos: dict[str, Any]) -> None:
        con_tope(catalogo, documentos)
        _propiedades_de_voz(documentos)["l"] = {
            "type": "object",
            "properties": {"items": {"type": "string"}},
        }

    assert _nuevos(guardia, objeto_con_propiedad_items) == []


# ---- Ronda 5, F-02: el costo de `_nodos` tiene un tope explícito ----------------------------------


def test_un_grafo_de_ref_compartidos_se_acota_con_un_problema_explicito_y_un_numero_de_nodos(
    guardia: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    tope = getattr(guardia, "TOPE_DE_NODOS", 20000)
    # `hijas` se llama una vez por cada nodo que `_nodos` expande: es una medida del trabajo que
    # no depende del reloj (el grafo de 18 niveles de la ronda 4 tiene 524 287 nodos).
    expandidos: list[int] = []
    original = guardia.hijas

    def contando(*argumentos: Any, **claves: Any) -> Any:
        expandidos.append(1)
        return original(*argumentos, **claves)

    monkeypatch.setattr(guardia, "hijas", contando)

    def cambiar(catalogo: dict[str, Any], documentos: dict[str, Any]) -> None:
        esquemas = documentos["queues/speech.v2.yaml"]["components"].setdefault("schemas", {})
        for nivel in range(18):
            siguiente = f"#/components/schemas/N{nivel + 1}"
            esquemas[f"N{nivel}"] = {
                "type": "object",
                "properties": {"a": {"$ref": siguiente}, "b": {"$ref": siguiente}},
            }
        esquemas["N18"] = {"type": "integer"}
        _propiedades_de_voz(documentos)["grafo"] = {"$ref": "#/components/schemas/N0"}

    nuevos = _nuevos(guardia, cambiar)
    assert nuevos == [
        (
            "queues/speech.v2.yaml: /components/messages/TranscriptResult/payload: la guardia superó "
            f"el tope de {tope} nodos de esquema y no revisa el resto (§4.4 a)"
        )
    ]
    # Con el tope, el trabajo total (los contratos reales y el grafo) no pasa del doble del tope.
    assert len(expandidos) <= 2 * tope


def test_con_un_texto_antes_del_tope_el_texto_se_informa_y_tambien_el_tope(
    guardia: ModuleType,
) -> None:
    tope = getattr(guardia, "TOPE_DE_NODOS", 20000)

    def cambiar(catalogo: dict[str, Any], documentos: dict[str, Any]) -> None:
        esquemas = documentos["queues/speech.v2.yaml"]["components"].setdefault("schemas", {})
        for nivel in range(18):
            siguiente = f"#/components/schemas/N{nivel + 1}"
            esquemas[f"N{nivel}"] = {
                "type": "object",
                "properties": {"a": {"$ref": siguiente}, "b": {"$ref": siguiente}},
            }
        esquemas["N18"] = {"type": "integer"}
        propiedades = _propiedades_de_voz(documentos)
        propiedades["antes"] = {"type": "string"}
        propiedades["grafo"] = {"$ref": "#/components/schemas/N0"}

    nuevos = _nuevos(guardia, cambiar)
    assert f"queues/speech.v2.yaml: {PAYLOAD_DE_VOZ}/antes: {TEXTO}" in nuevos
    assert any(f"el tope de {tope} nodos" in problema for problema in nuevos)


def test_comprobar_con_contratos_ausentes_o_ilegibles(guardia: ModuleType, tmp_path: Path) -> None:
    ausentes = guardia.comprobar(tmp_path)
    assert sorted(ausentes) == sorted(
        f"{r}: contrato ausente (§4.4)" for r in ("limits.v1.yaml", *guardia.ARCHIVOS)
    )
    # Con los contratos de marcas completos, falta solo lo que sus `$ref` por `$id` necesitan.
    for relativa in ("limits.v1.yaml", *guardia.ARCHIVOS):
        destino = tmp_path / relativa
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(CONTRACTS_ROOT / relativa, destino)
    estrictos = importar_o_fallar("veridicus_contracts.checks.strict_bodies", "T15, paso 16")
    sin_esquemas = [r for r in estrictos.ESQUEMAS_ESTRICTOS if r not in guardia.ARCHIVOS]
    assert sin_esquemas
    assert sorted(guardia.comprobar(tmp_path)) == sorted(
        f"{r}: contrato ausente (§4.4)" for r in sin_esquemas
    )
    (tmp_path / "limits.v1.yaml").write_text("a: 1\na: 2\n", encoding="utf-8")
    assert guardia.comprobar(tmp_path)[0] == (
        "limits.v1.yaml: contrato ilegible, no se pudo interpretar (§4.4)"
    )
