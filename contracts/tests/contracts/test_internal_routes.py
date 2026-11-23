"""C21 (respuestas), ruta interna de voz y C16: forma, estados y cierre de los cuerpos (T13).

- C21: los estados de la revisión 4; `anonymizer.incident` no es respuesta de ninguna ruta
  (P-T07-1, CD-11). La comparación de los `code` con el catálogo es de T15 (K-19, PD-8).
- Ruta interna de voz: `bearerAuth`, cuerpo estricto, `401`, `422` con `rule_id` cerrado, `503` y
  `audio/wav` con tope (NFRD-U1-08).
- C16: `/healthz` y `/readyz` públicas, con cuerpos cerrados y sin datos sensibles.
"""

from typing import Any

import pytest
from helpers import errores_de, load_contract, recorrer, validador_de

C21 = "api/anonymizer-proxy.v1.yaml"
VOZ = "api/speech-internal.v1.yaml"
SALUD = "health/health.v2.yaml"
CATALOGO = "errors/error-codes.v2.yaml"
ESTADOS_C21 = {"200", "409", "413", "422", "451", "502", "503", "504"}


@pytest.mark.c21
def test_c21_declara_los_estados_de_la_revision_4() -> None:
    respuestas = load_contract(C21)["paths"]["/v1/generate"]["post"]["responses"]
    assert set(respuestas) == ESTADOS_C21


@pytest.mark.c21
def test_c21_no_nombra_anonymizer_incident_en_ninguna_respuesta() -> None:
    """P-T07-1: `anonymizer.incident` es `http: false` y no es respuesta de ninguna ruta."""
    documento = load_contract(C21)
    catalogo = load_contract(CATALOGO)["codes"]
    assert "status" not in catalogo["anonymizer.incident"]
    assert catalogo["anonymizer.incident"]["http"] is False
    assert "anonymizer.incident" not in str(documento)
    assert "incidente_anonimizacion" not in str(documento)


@pytest.mark.c21
def test_c21_la_respuesta_200_lleva_el_registro_de_la_llamada_por_referencia() -> None:
    operacion = load_contract(C21)["paths"]["/v1/generate"]["post"]
    esquema = operacion["responses"]["200"]["content"]["application/json"]["schema"]
    assert esquema["required"] == ["content", "altered_markers", "call"]
    assert esquema["properties"]["call"] == {"$ref": "/veridicus/contracts/model_calls/model-call.v1"}
    assert load_contract(C21)["servers"] == [{"url": "http://veridicus-anonymizer-proxy:8080"}]
    assert not [c for _, c, _ in recorrer(load_contract(C21)) if c in {"destination", "api_key_ref"}]


def _cuerpo_de_voz() -> dict[str, Any]:
    return {
        "observation_id": "c4e8b1f7-2d9a-4a6c-8b3e-d5f0a9c2e1b4",
        "tema": "la noche en la finca",
        "template_version": "1.0.0",
    }


@pytest.mark.speech
def test_voz_interna_declara_bearer_auth_y_los_cuatro_estados() -> None:
    documento = load_contract(VOZ)
    assert list(documento["paths"]) == ["/internal/v1/speech"]
    operacion = documento["paths"]["/internal/v1/speech"]["post"]
    assert operacion["security"] == [{"bearerAuth": []}]
    assert documento["components"]["securitySchemes"] == {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "description": "Token compartido `VERIDICUS_SPEECH_TOKEN`, en un Secret que crea el humano",
        }
    }
    assert set(operacion["responses"]) == {"200", "401", "422", "503"}
    assert documento["servers"] == [{"url": "http://veridicus-audio-worker:8080"}]
    assert "sessionCookie" not in str(documento)


@pytest.mark.speech
def test_voz_interna_responde_audio_wav_con_tope_de_bytes() -> None:
    operacion = load_contract(VOZ)["paths"]["/internal/v1/speech"]["post"]
    contenido = operacion["responses"]["200"]["content"]
    assert list(contenido) == ["audio/wav"]
    assert contenido["audio/wav"]["x-veridicus-max-bytes"] == "speech_audio_max_bytes"
    marcas = [v for _, c, v in recorrer(operacion) if c == "x-veridicus-max-bytes"]
    assert marcas == ["speech_audio_max_bytes"]


@pytest.mark.speech
def test_voz_interna_422_lleva_un_rule_id_de_lista_cerrada() -> None:
    operacion = load_contract(VOZ)["paths"]["/internal/v1/speech"]["post"]
    esquema = operacion["responses"]["422"]["content"]["application/problem+json"]["schema"]
    assert esquema["additionalProperties"] is False
    assert esquema["required"] == ["rule_id"]
    assert esquema["properties"]["rule_id"] == {
        "enum": ["template_version", "dt23", "vocabulary", "length"]
    }
    validador = validador_de(
        VOZ,
        "#/paths/~1internal~1v1~1speech/post/responses/422/content/application~1problem+json/schema",
    )
    for regla in ("template_version", "dt23", "vocabulary", "length"):
        assert errores_de(validador, {"rule_id": regla}) == []
    assert errores_de(validador, {"rule_id": "otra"})
    assert errores_de(validador, {})
    assert errores_de(validador, {"rule_id": "dt23", "texto": "x"})


@pytest.mark.speech
def test_voz_interna_422_admite_problem_details_de_rfc_9457_y_sigue_cerrado() -> None:
    validador = validador_de(
        VOZ,
        "#/paths/~1internal~1v1~1speech/post/responses/422/content/application~1problem+json/schema",
    )
    problema = {
        "type": "about:blank",
        "title": "Texto rechazado",
        "status": 422,
        # `validation.invalid_request` es 422 en el catálogo; el code propio de esta ruta es K-18.
        "code": "validation.invalid_request",
        "detail": "La frase propuesta no cumple la regla de longitud.",
        "instance": "/internal/v1/speech",
        "rule_id": "length",
    }
    assert errores_de(validador, problema) == []
    assert errores_de(validador, {"rule_id": "length"}) == []
    for campo, valor in (
        ("status", 409),
        ("status", "422"),
        ("code", "Texto rechazado"),
        ("type", 5),
        ("title", 5),
        ("detail", 5),
        ("instance", 5),
        ("extra", "x"),
    ):
        assert errores_de(validador, {**problema, campo: valor}), campo
    sin_regla = {k: v for k, v in problema.items() if k != "rule_id"}
    assert errores_de(validador, sin_regla)


def _validador_de_voz() -> Any:
    return validador_de(
        VOZ, "#/paths/~1internal~1v1~1speech/post/requestBody/content/application~1json/schema"
    )


@pytest.mark.speech
def test_voz_interna_cuerpo_estricto_acepta_el_valido() -> None:
    assert errores_de(_validador_de_voz(), _cuerpo_de_voz()) == []


@pytest.mark.speech
@pytest.mark.parametrize(
    "cambio",
    [
        {"extra": "x"},
        {"observation_id": "no-es-uuid"},
        {"tema": ""},
        {"tema": 5},
        {"template_version": "1.0"},
        {"template_version": "v1.0.0"},
    ],
    ids=["campo-extra", "uuid", "tema-vacio", "tema-no-texto", "version-corta", "version-con-v"],
)
def test_voz_interna_cuerpo_estricto_rechaza_cada_defecto(cambio: dict[str, Any]) -> None:
    assert errores_de(_validador_de_voz(), {**_cuerpo_de_voz(), **cambio})


@pytest.mark.speech
@pytest.mark.parametrize("campo", ["observation_id", "tema", "template_version"])
def test_voz_interna_cuerpo_exige_cada_campo(campo: str) -> None:
    cuerpo = _cuerpo_de_voz()
    del cuerpo[campo]
    assert errores_de(_validador_de_voz(), cuerpo)


@pytest.mark.c16
def test_salud_declara_las_dos_rutas_publicas_con_sus_estados() -> None:
    documento = load_contract(SALUD)
    assert list(documento["paths"]) == ["/healthz", "/readyz"]
    assert documento["info"]["version"] == "2.0.0"
    assert documento["servers"] == [{"url": "/"}]
    for ruta in ("/healthz", "/readyz"):
        assert documento["paths"][ruta]["get"]["security"] == []
    assert set(documento["paths"]["/healthz"]["get"]["responses"]) == {"200"}
    assert set(documento["paths"]["/readyz"]["get"]["responses"]) == {"200", "503"}
    assert "securitySchemes" not in documento.get("components", {})


def _salud(ruta: str, estado: str) -> Any:
    escapada = ruta.replace("/", "~1")
    return validador_de(
        SALUD,
        f"#/paths/{escapada}/get/responses/{estado}/content/application~1json/schema",
    )


@pytest.mark.c16
def test_salud_acepta_las_respuestas_documentadas() -> None:
    assert errores_de(_salud("/healthz", "200"), {"status": "ok"}) == []
    listo = {"status": "ready", "checks": [{"name": "access_log", "ok": True, "info": "not_configured"}]}
    assert errores_de(_salud("/readyz", "200"), listo) == []
    assert errores_de(_salud("/readyz", "200"), {"status": "ready", "checks": []}) == []
    no_listo = {"status": "not_ready", "checks": [{"name": "redis", "ok": False}]}
    assert errores_de(_salud("/readyz", "503"), no_listo) == []


@pytest.mark.c16
@pytest.mark.parametrize(
    ("ruta", "estado", "instancia"),
    [
        ("/healthz", "200", {"status": "listo"}),
        ("/healthz", "200", {"status": "ok", "extra": 1}),
        ("/healthz", "200", {}),
        ("/readyz", "200", {"status": "not_ready", "checks": []}),
        ("/readyz", "200", {"status": "ready"}),
        ("/readyz", "200", {"status": "ready", "checks": [{"name": "redis"}]}),
        ("/readyz", "200", {"status": "ready", "checks": [{"name": "Redis", "ok": True}]}),
        ("/readyz", "200", {"status": "ready", "checks": [{"name": "db", "ok": True, "info": "con espacio"}]}),
        ("/readyz", "200", {"status": "ready", "checks": [{"name": "db", "ok": True, "detalle": "x"}]}),
        ("/readyz", "200", {"status": "ready", "checks": [{"name": "db", "ok": "si"}]}),
        ("/readyz", "503", {"status": "ready", "checks": []}),
        ("/readyz", "503", {"status": "not_ready", "checks": [{"name": "x" * 65, "ok": False}]}),
    ],
    ids=[
        "estado-libre",
        "campo-extra",
        "vacio",
        "estado-cruzado-200",
        "sin-checks",
        "sin-ok",
        "nombre-con-mayuscula",
        "info-con-texto-libre",
        "campo-extra-en-check",
        "ok-no-booleano",
        "estado-cruzado-503",
        "nombre-largo",
    ],
)
def test_salud_rechaza_cuerpos_con_texto_libre_o_fuera_de_forma(
    ruta: str, estado: str, instancia: dict[str, Any]
) -> None:
    assert errores_de(_salud(ruta, estado), instancia)
