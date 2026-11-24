"""Guardia de marcas y catálogo C25 en los dos sentidos (§4.4; NFR10.7, NFR10.14; R-05 de la revisión 1).

Los controles negativos trabajan sobre copias en memoria del catálogo y de los contratos reales y
comparan con el resultado sobre los originales: la guardia solo debe añadir el hallazgo que provoca
la prueba.
"""

import copy
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
    catalogo = copy.deepcopy(load_contract("limits.v1.yaml"))["limits"]
    documentos = {r: copy.deepcopy(load_contract(r)) for r in guardia.ARCHIVOS}
    return catalogo, documentos


def _nuevos(
    guardia: ModuleType, cambiar: Callable[[dict[str, Any], dict[str, Any]], None]
) -> list[str]:
    original = guardia.comprobar_documentos(*_estado(guardia))
    catalogo, documentos = _estado(guardia)
    cambiar(catalogo, documentos)
    return sorted(p for p in guardia.comprobar_documentos(catalogo, documentos) if p not in original)


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
        ("api/console.v2.yaml: /paths/~1users/post/requestBody/content/application~1json/schema/"
        "properties/username: valor distinto del catálogo C25 (username_max_chars, §4.4 b)"),
        ("queues/speech.v2.yaml: /components/messages/AudioToTranscribe/payload/properties/"
        "audio_base64: valor distinto del catálogo C25 (audio_base64_max_chars, §4.4 b)"),
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
        ("api/console.v2.yaml: /components/securitySchemes/sessionCookie/x-veridicus-cookie: la "
        "unidad de web_session_idle_s debe ser s con x-veridicus-cookie (§4.4 c)"),
        ("api/console.v2.yaml: /paths/~1sessions~1import/post/requestBody: la unidad de "
        "import_body_max_bytes debe ser bytes con x-veridicus-max-bytes (§4.4 c)"),
        ("api/console.v2.yaml: /paths/~1sessions~1{session_id}~1turns/post/requestBody/content/"
        "application~1json/schema/properties/texto: la unidad de turn_max_chars debe ser chars "
        "con maxLength (§4.4 c)"),
        ("api/console.v2.yaml: /paths/~1users/post/requestBody/content/application~1json/schema/"
        "properties/password: la unidad de password_max_chars debe ser turns con maxItems (§4.4 c)"),
    ]


def test_limite_huerfano_en_los_dos_sentidos(guardia: ModuleType) -> None:
    def cambiar(catalogo: dict[str, Any], documentos: dict[str, Any]) -> None:
        catalogo["retention_max_days"]["used_in"] = ["C1"]
        catalogo["cursor_max_chars"]["used_in"] = []
        catalogo["poll_interval_s"]["used_in"] = ["C3"]
        _propiedades_de_crear_usuario(documentos)["username"]["x-veridicus-limit"] = "no_existe"

    assert _nuevos(guardia, cambiar) == [
        ("api/console.v2.yaml: /components/schemas/Cursor: la marca cursor_max_chars no está en "
        "used_in de C25 para C1 (§4.4, comprobación inversa)"),
        ("api/console.v2.yaml: /paths/~1users/post/requestBody/content/application~1json/schema/"
        "properties/username: la marca no_existe no es una cifra de C25 (§4.4)"),
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
        runs = documentos["queues/runs.v2.yaml"]["components"]["messages"]["RunRequested"]
        runs["payload"]["properties"]["comentario"] = {"type": "string"}
        runs["payload"]["properties"]["vuelta"] = {"$ref": "#/components/messages/RunRequested/payload"}
        runs["payload"]["properties"]["lista"] = "no es un esquema"

    nuevos = _nuevos(guardia, cambiar)
    assert nuevos == [
        ("api/console.v2.yaml: /paths/~1users/post/requestBody/content/application~1json/schema/"
        "properties/etiquetas/items: campo de texto sin x-veridicus-limit (§4.4 a)"),
        ("api/console.v2.yaml: /paths/~1users/post/requestBody/content/application~1json/schema/"
        "properties/nota: campo de texto sin x-veridicus-limit (§4.4 a)"),
        ("queues/runs.v2.yaml: /components/messages/RunRequested/payload/properties/comentario: "
        "campo de texto sin x-veridicus-limit (§4.4 a)"),
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
        ("api/console.v2.yaml: /paths/~1sessions~1{session_id}~1transcript/post/requestBody/content/"
        "application~1json/schema/properties/text: campo de texto sin x-veridicus-limit (§4.4 a)"),
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
        ("api/console.v2.yaml: /paths/~1users/post/requestBody/content/application~1json/schema/"
        "properties/lista: maxItems sin x-veridicus-limit (§4.4)"),
        ("api/console.v2.yaml: /paths/~1users/post/requestBody/content/application~1json/schema/"
        "properties/sin_palabra: la marca username_max_chars no acompaña a maxLength ni a maxItems "
        "(§4.4)"),
        ("model_calls/model-call.v1.yaml: /properties/role: valor distinto del catálogo C25 "
        "(report_token_max_chars, §4.4 b)"),
    ]


def test_la_ruta_de_voz_no_exige_marca_en_tema_ni_used_in(guardia: ModuleType) -> None:
    # K-15: §4.4 (a) no incluye la ruta interna de voz, así que `tema` no necesita marca.
    voz = load_contract("api/speech-internal.v1.yaml")
    tema = voz["paths"]["/internal/v1/speech"]["post"]["requestBody"]["content"][
        "application/json"
    ]["schema"]["properties"]["tema"]
    assert tema == {"type": "string", "minLength": 1}
    assert not any(
        "speech-internal" in p for p in guardia.comprobar_documentos(*_estado(guardia))
    )

    # La ruta no tiene un C<n>: su marca no se contrasta con used_in, pero sí con el valor y la unidad.
    def cambiar(catalogo: dict[str, Any], documentos: dict[str, Any]) -> None:
        catalogo["speech_audio_max_bytes"]["unit"] = "chars"

    assert _nuevos(guardia, cambiar) == [
        ("api/speech-internal.v1.yaml: /paths/~1internal~1v1~1speech/post/responses/200/content/"
        "audio~1wav: la unidad de speech_audio_max_bytes debe ser bytes con x-veridicus-max-bytes "
        "(§4.4 c)")
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


def test_comprobar_con_contratos_ausentes_o_ilegibles(guardia: ModuleType, tmp_path: Path) -> None:
    ausentes = guardia.comprobar(tmp_path)
    assert sorted(ausentes) == sorted(
        f"{r}: contrato ausente (§4.4)" for r in ("limits.v1.yaml", *guardia.ARCHIVOS)
    )
    (tmp_path / "limits.v1.yaml").write_text("a: 1\na: 2\n", encoding="utf-8")
    assert guardia.comprobar(tmp_path)[0] == (
        "limits.v1.yaml: contrato ilegible, no se pudo interpretar (§4.4)"
    )
