"""C1, la API de la consola (`api/console.v2.yaml`): forma, estados y marcas (T14, paso 16).

Se transcribe de contract-summary §C1 con las precisiones aprobadas (PD-1, PD-2) y las decisiones
C-3 y D-1. Aquí solo se comprueba la forma del contrato; las guardias de C1 (`auth_surface`,
`strict_bodies`, `config_write`, `limits_match` y la parte de C1 de `error_codes`) son de T15.

Rojo hasta T14 (`api/console.v2.yaml`).
"""

import copy
import re
from collections.abc import Iterator
from typing import Any, ClassVar

import pytest
from helpers import (
    cargar_fixture,
    errores_de,
    load_contract,
    recorrer,
    registro_de_contratos,
    validador_de,
)
from jsonschema.exceptions import ValidationError
from openapi_spec_validator.exceptions import OpenAPISpecValidatorError
from openapi_spec_validator.validation import OpenAPIV31SpecValidator

from veridicus_contracts.registry import BASE_URI

pytestmark = pytest.mark.c1

C1 = "api/console.v2.yaml"
CATALOGO = "errors/error-codes.v2.yaml"
LIMITES = "limits.v1.yaml"
SALIDA_C6 = "analyzer/v1/salida.schema.json"
SUGERENCIA_VALIDA = "integrity/fixtures/review-suggestion/valid.pending.yaml"

METODOS = ("get", "put", "post", "delete", "options", "head", "patch", "trace")
PATRON_DE_FECHA = "^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"
PROBLEM = "#/components/responses/Problem"
ROLES = {"analista", "admin", "investigador"}
SIN_ROLES = {("post", "/auth/login"), ("post", "/auth/logout"), ("get", "/auth/me")}
PUBLICAS = {("post", "/auth/login"), ("get", "/notice")}
EXTENSIONES = {
    "x-veridicus-roles",
    "x-veridicus-owner-only",
    "x-veridicus-owner-only-for-role",
    "x-veridicus-access-log",
    "x-veridicus-demo",
    "x-veridicus-priority",
    "x-veridicus-limit",
    "x-veridicus-max-bytes",
    "x-veridicus-cookie",
}
# Las seis operaciones que encolan trabajo de IA (NFR3.1, C-3): operationId -> (método, ruta).
ENCOLAN = {
    "create_turn": ("post", "/sessions/{session_id}/turns"),
    "paste_transcript": ("post", "/sessions/{session_id}/transcript"),
    "retry_run": ("post", "/sessions/{session_id}/runs/{run_id}/retry"),
    "launch_final_run": ("post", "/sessions/{session_id}/final-runs"),
    "set_analysis_paused": ("patch", "/sessions/{session_id}/analysis"),
    "create_voice_turn": ("post", "/sessions/{session_id}/voice-turns"),
}
RUTAS_DE_C1 = {
    "/auth/login": {"post"},
    "/auth/logout": {"post"},
    "/auth/me": {"get"},
    "/users": {"get", "post"},
    "/users/{user_id}": {"patch"},
    "/notice": {"get"},
    "/profiles": {"get"},
    "/sessions": {"get", "post"},
    "/sessions/import": {"post"},
    "/sessions/{session_id}": {"get"},
    "/sessions/{session_id}/heartbeat": {"post"},
    "/sessions/{session_id}/turns": {"post"},
    "/sessions/{session_id}/transcript": {"post"},
    "/sessions/{session_id}/final-runs": {"post"},
    "/sessions/{session_id}/runs/{run_id}/retry": {"post"},
    "/sessions/{session_id}/runs/{run_id}/model-calls": {"get"},
    "/sessions/{session_id}/analysis": {"patch"},
    "/sessions/{session_id}/terminate": {"post"},
    "/sessions/{session_id}/consent-withdrawal": {"post"},
    "/sessions/{session_id}/resume": {"post"},
    "/sessions/{session_id}/finalize": {"post"},
    "/suggestions/{suggestion_id}/observation-views": {"post"},
    "/suggestions/{suggestion_id}/decisions": {"post"},
    "/sessions/{session_id}/reports": {"get", "post"},
    "/sessions/{session_id}/correction-rounds": {"post"},
    "/sessions/{session_id}/correction-rounds/current/discard": {"post"},
    "/reports/{report_version_id}/download": {"get"},
    "/reports/{report_version_id}/exports": {"post"},
    "/conductor-observations/{observation_id}/decision": {"post"},
    "/conductor-observations/{observation_id}/audio": {"get"},
    "/sessions/{session_id}/voice-turns": {"post"},
    "/research-reports": {"get", "post"},
    "/research-reports/{research_report_id}": {"get"},
    "/research-reports/compare": {"get"},
    "/sessions/{session_id}/retention": {"patch"},
    "/acknowledgements": {"post"},
    "/problem-reports": {"post"},
}
SHOULD = {
    ("post", "/conductor-observations/{observation_id}/decision"),
    ("get", "/conductor-observations/{observation_id}/audio"),
    ("post", "/sessions/{session_id}/voice-turns"),
    ("get", "/research-reports/compare"),
}
DEMO = {
    ("patch", "/sessions/{session_id}/retention"),
    ("post", "/acknowledgements"),
    ("post", "/problem-reports"),
}


def c1() -> dict[str, Any]:
    documento = load_contract(C1)
    assert isinstance(documento, dict)
    return documento


def operaciones(documento: dict[str, Any]) -> Iterator[tuple[str, str, dict[str, Any]]]:
    """(método, ruta, operación) de cada operación del documento."""
    for ruta, item in documento["paths"].items():
        for metodo in METODOS:
            if metodo in item:
                yield metodo, ruta, item[metodo]


def operacion(metodo: str, ruta: str) -> dict[str, Any]:
    resultado = c1()["paths"][ruta][metodo]
    assert isinstance(resultado, dict)
    return resultado


def estados(metodo: str, ruta: str) -> set[str]:
    return set(operacion(metodo, ruta)["responses"])


def es_problema(respuesta: dict[str, Any]) -> bool:
    """La respuesta de error es el componente `Problem` o su equivalente en línea con cabeceras."""
    if respuesta.get("$ref") == PROBLEM:
        return True
    contenido = respuesta.get("content", {}).get("application/problem+json", {})
    return bool(contenido.get("schema") == {"$ref": "#/components/schemas/Problem"})


def contenidos(documento: Any) -> Iterator[tuple[str, dict[str, Any]]]:
    """(tipo de medio, objeto de contenido) de cada `content` de petición o respuesta."""
    for _, clave, valor in recorrer(documento):
        if clave == "content" and isinstance(valor, dict):
            yield from valor.items()


def catalogo_de_limites() -> dict[str, Any]:
    limites = load_contract(LIMITES)["limits"]
    assert isinstance(limites, dict)
    return limites


def esquemas_con(documento: Any, clave: str) -> Iterator[tuple[str, dict[str, Any]]]:
    for ruta, _, valor in recorrer(documento):
        if isinstance(valor, dict) and clave in valor:
            yield ruta, valor


# --- validez, versión y servidores ---------------------------------------------------------------


def _contenido_por_id(uri: str) -> Any:
    """Contenido del contrato que declara ese $id canónico (FD-U1-11), sin red."""
    return registro_de_contratos()[BASE_URI + uri.lstrip("/")].contents


class ValidadorConReferencias(OpenAPIV31SpecValidator):  # type: ignore[misc]
    """OpenAPI 3.1 que resuelve las referencias por $id canónico con el registro del paquete."""

    resolver_handlers: ClassVar[Any] = {"": _contenido_por_id}


def validar_openapi(documento: Any) -> None:
    """Valida con openapi-spec-validator (D3); las referencias por $id salen del registro, no de la red."""
    try:
        ValidadorConReferencias(documento).validate()
    except (ValidationError, OpenAPISpecValidatorError) as error:
        pytest.fail(f"OpenAPI 3.1 no válido: {error}")


def test_c1_es_un_openapi_3_1_valido() -> None:
    validar_openapi(c1())


def test_el_validador_de_openapi_rechaza_una_respuesta_con_un_campo_ajeno() -> None:
    """Control negativo: la comprobación de validez no pasa en vacío."""
    roto = copy.deepcopy(c1())
    roto["paths"]["/profiles"]["get"]["responses"]["200"]["ajeno"] = 1
    with pytest.raises(pytest.fail.Exception):
        validar_openapi(roto)


def test_c1_declara_version_servidor_interno_y_cookie_por_omision() -> None:
    documento = c1()
    assert documento["openapi"] == "3.1.0"
    assert documento["info"]["version"] == "2.0.0"
    assert documento["servers"] == [{"url": "/api/v1"}]
    assert documento["security"] == [{"sessionCookie": []}]


def test_c1_declara_exactamente_las_rutas_y_metodos_de_contract_summary() -> None:
    declaradas = {ruta: {m for m in METODOS if m in item} for ruta, item in c1()["paths"].items()}
    assert declaradas == RUTAS_DE_C1


def test_sin_put_ni_delete_y_patch_solo_en_tres_rutas() -> None:
    usados = {(m, r) for m, r, _ in operaciones(c1()) if m in {"put", "delete", "patch"}}
    assert usados == {
        ("patch", "/users/{user_id}"),
        ("patch", "/sessions/{session_id}/analysis"),
        ("patch", "/sessions/{session_id}/retention"),
    }


def test_cada_operacion_tiene_un_operation_id_unico() -> None:
    ids = [op.get("operationId") for _, _, op in operaciones(c1())]
    assert all(isinstance(i, str) and re.fullmatch(r"[a-z][a-z0-9_]*", i) for i in ids)
    assert len(ids) == len(set(ids))
    assert set(ENCOLAN) <= set(ids)


# --- ErrorCode, Problem y anti-CSRF --------------------------------------------------------------


def test_error_code_es_igual_a_los_code_http_del_catalogo() -> None:
    catalogo = load_contract(CATALOGO)["codes"]
    esperados = {codigo for codigo, fila in catalogo.items() if fila["http"] is True}
    enum = c1()["components"]["schemas"]["ErrorCode"]["enum"]
    assert len(enum) == len(set(enum)), "ErrorCode repite un valor"
    assert set(enum) == esperados
    for fuera in ("anonymizer.incident", "config.invalid_profile", "run.publish_failed"):
        assert fuera not in enum


def test_problem_es_problem_details_con_code_de_error_code() -> None:
    componentes = c1()["components"]
    problema = componentes["schemas"]["Problem"]
    assert problema["required"] == ["type", "title", "status", "code", "detail"]
    assert problema["properties"]["code"] == {"$ref": "#/components/schemas/ErrorCode"}
    respuesta = componentes["responses"]["Problem"]
    assert list(respuesta["content"]) == ["application/problem+json"]
    assert respuesta["content"]["application/problem+json"]["schema"] == {
        "$ref": "#/components/schemas/Problem"
    }


def test_csrf_token_es_una_cabecera_obligatoria_de_al_menos_32_caracteres() -> None:
    parametro = c1()["components"]["parameters"]["CsrfToken"]
    assert parametro["name"] == "X-CSRF-Token"
    assert parametro["in"] == "header"
    assert parametro["required"] is True
    assert parametro["schema"]["type"] == "string"
    assert parametro["schema"]["minLength"] == 32


def test_toda_escritura_lleva_el_token_anti_csrf_salvo_el_inicio_de_sesion() -> None:
    sin_token = []
    for metodo, ruta, op in operaciones(c1()):
        lleva = {"$ref": "#/components/parameters/CsrfToken"} in op.get("parameters", [])
        if metodo in {"post", "patch"} and (metodo, ruta) != ("post", "/auth/login"):
            if not lleva:
                sin_token.append(f"{metodo} {ruta}")
        else:
            assert not lleva, f"{metodo} {ruta} no es una escritura y pide el token"
    assert sin_token == []


# --- autenticación, roles y lista pública --------------------------------------------------------


def test_la_lista_publica_es_login_y_notice_y_cada_una_dice_su_motivo() -> None:
    publicas = {(m, r) for m, r, op in operaciones(c1()) if op.get("security") == []}
    assert publicas == PUBLICAS
    for metodo, ruta, op in operaciones(c1()):
        if (metodo, ruta) not in PUBLICAS:
            assert "security" not in op, f"{metodo} {ruta} cambia la seguridad por omisión"
    aviso = operacion("get", "/notice")
    assert "D-1" in aviso["description"]
    assert "x-veridicus-roles" not in aviso
    assert set(aviso["responses"]) == {"200"}


def test_toda_operacion_declara_roles_salvo_login_logout_me_y_la_lista_publica() -> None:
    sin_roles = set()
    for metodo, ruta, op in operaciones(c1()):
        roles = op.get("x-veridicus-roles")
        if roles is None:
            sin_roles.add((metodo, ruta))
            continue
        assert isinstance(roles, list) and roles, f"{metodo} {ruta}: roles vacíos"
        assert set(roles) <= ROLES, f"{metodo} {ruta}: rol desconocido"
    assert sin_roles == SIN_ROLES | PUBLICAS


def test_el_enum_de_rol_es_el_de_las_tres_funciones() -> None:
    assert set(c1()["components"]["schemas"]["Role"]["enum"]) == ROLES


def test_las_extensiones_de_operacion_tienen_su_valor_y_su_sitio() -> None:
    for metodo, ruta, op in operaciones(c1()):
        etiqueta = f"{metodo} {ruta}"
        if "x-veridicus-owner-only" in op:
            assert op["x-veridicus-owner-only"] is True, etiqueta
            assert "x-veridicus-roles" in op, etiqueta
        if "x-veridicus-owner-only-for-role" in op:
            assert op["x-veridicus-owner-only-for-role"] in op["x-veridicus-roles"], etiqueta
        if "x-veridicus-access-log" in op:
            assert op["x-veridicus-access-log"] in {"session", "suggestion", "report_version"}
        if "x-veridicus-demo" in op:
            assert op["x-veridicus-demo"] is True, etiqueta
        if "x-veridicus-priority" in op:
            assert op["x-veridicus-priority"] == "SHOULD", etiqueta
    registro = {
        ("get", "/sessions/{session_id}"): "session",
        ("post", "/suggestions/{suggestion_id}/observation-views"): "suggestion",
        ("get", "/reports/{report_version_id}/download"): "report_version",
    }
    marcadas = {
        (m, r): op["x-veridicus-access-log"]
        for m, r, op in operaciones(c1())
        if "x-veridicus-access-log" in op
    }
    assert marcadas == registro
    con_prioridad = {(m, r) for m, r, op in operaciones(c1()) if "x-veridicus-priority" in op}
    assert con_prioridad == SHOULD
    con_demo = {(m, r) for m, r, op in operaciones(c1()) if "x-veridicus-demo" in op}
    assert con_demo == DEMO


def test_401_y_403_son_problem_segun_nfrd_u1_12() -> None:
    for metodo, ruta, op in operaciones(c1()):
        etiqueta = f"{metodo} {ruta}"
        respuestas = op["responses"]
        if op.get("security") == []:
            continue
        assert respuestas.get("401", {}).get("$ref") == PROBLEM, etiqueta
        if "x-veridicus-roles" in op:
            assert respuestas.get("403", {}).get("$ref") == PROBLEM, etiqueta
        else:
            assert "403" not in respuestas, f"{etiqueta}: logout y me declaran 401 y no 403"


def test_toda_respuesta_4xx_y_5xx_es_problem_details() -> None:
    for metodo, ruta, op in operaciones(c1()):
        for estado, respuesta in op["responses"].items():
            if estado.startswith(("4", "5")):
                assert es_problema(respuesta), f"{metodo} {ruta} {estado}"


def test_session_cookie_declara_sus_atributos_y_los_dos_limites() -> None:
    cookie = c1()["components"]["securitySchemes"]["sessionCookie"]
    assert (cookie["type"], cookie["in"], cookie["name"]) == (
        "apiKey",
        "cookie",
        "veridicus_session",
    )
    assert cookie["x-veridicus-cookie"] == {
        "http_only": True,
        "secure": True,
        "same_site": "Strict",
        "path": "/",
        "max_age_limit": "web_session_max_s",
        "idle_limit": "web_session_idle_s",
    }
    catalogo = catalogo_de_limites()
    assert catalogo["web_session_max_s"]["unit"] == "s"
    assert catalogo["web_session_idle_s"]["unit"] == "s"


# --- extensiones cerradas y cifras de C25 --------------------------------------------------------


def test_solo_hay_extensiones_x_veridicus_de_la_lista_cerrada() -> None:
    usadas = {clave for _, clave, _ in recorrer(c1()) if clave and clave.startswith("x-")}
    assert usadas <= EXTENSIONES, sorted(usadas - EXTENSIONES)
    assert usadas == EXTENSIONES, "falta una extensión que el contrato debía usar"


def test_x_veridicus_limit_va_en_un_esquema_y_x_veridicus_max_bytes_en_un_cuerpo_o_respuesta() -> (
    None
):
    documento = c1()
    for metodo, ruta, op in operaciones(documento):
        cuerpo = op.get("requestBody", {})
        assert "x-veridicus-limit" not in cuerpo, f"{metodo} {ruta}"
        for tipo, contenido in contenidos(op):
            assert "x-veridicus-limit" not in contenido, f"{metodo} {ruta} {tipo}"
        assert "x-veridicus-max-bytes" not in op, (
            f"{metodo} {ruta}: va en el cuerpo, no en la operación"
        )
    for _, esquema in esquemas_con(documento["components"]["schemas"], "x-veridicus-max-bytes"):
        pytest.fail(f"x-veridicus-max-bytes en un esquema: {sorted(esquema)}")


def test_cada_marca_nombra_una_cifra_del_catalogo_con_su_unidad() -> None:
    catalogo = catalogo_de_limites()
    marcas = 0
    for _, esquema in esquemas_con(c1(), "x-veridicus-limit"):
        nombre = esquema["x-veridicus-limit"]
        assert nombre in catalogo, nombre
        assert catalogo[nombre]["unit"] in {"chars", "turns"}, nombre
        marcas += 1
    for _, objeto in esquemas_con(c1(), "x-veridicus-max-bytes"):
        nombre = objeto["x-veridicus-max-bytes"]
        assert nombre in catalogo, nombre
        assert catalogo[nombre]["unit"] == "bytes", nombre
        marcas += 1
    assert marcas >= 15


def test_cada_tope_de_texto_o_de_lista_lleva_la_cifra_del_catalogo() -> None:
    catalogo = catalogo_de_limites()
    topes = 0
    for ruta, _, valor in recorrer(c1()):
        if not isinstance(valor, dict):
            continue
        for clave, unidad in (("maxLength", "chars"), ("maxItems", "turns")):
            if clave not in valor:
                continue
            topes += 1
            nombre = valor.get("x-veridicus-limit")
            assert nombre in catalogo, f"{ruta}: {clave} sin x-veridicus-limit"
            assert catalogo[nombre]["unit"] == unidad, ruta
            assert valor[clave] == catalogo[nombre]["value"], f"{ruta}: {clave} difiere de {nombre}"
    assert topes >= 7


def test_las_cifras_que_usa_c1_son_las_de_los_nfr_de_cada_unidad() -> None:
    usadas = {v["x-veridicus-limit"] for _, v in esquemas_con(c1(), "x-veridicus-limit")} | {
        v["x-veridicus-max-bytes"] for _, v in esquemas_con(c1(), "x-veridicus-max-bytes")
    }
    assert {
        "username_max_chars",
        "password_max_chars",
        "turn_max_chars",
        "cursor_max_chars",
        "review_text_max_chars",
        "review_body_max_bytes",
        "import_body_max_bytes",
        "transcript_body_max_bytes",
        "voice_body_max_bytes",
        "research_report_max_bytes",
        "ethics_body_max_bytes",
        "problem_report_note_max_chars",
    } <= usadas


def test_todo_cuerpo_con_tope_de_bytes_o_de_texto_declara_413_limits_exceeded() -> None:
    for metodo, ruta, op in operaciones(c1()):
        con_tope = any(
            "x-veridicus-max-bytes" in contenido or "x-veridicus-limit" in str(contenido)
            for _, contenido in contenidos(op.get("requestBody", {}))
        ) or "x-veridicus-max-bytes" in op.get("requestBody", {})
        if con_tope:
            assert "413" in op["responses"], f"{metodo} {ruta}"
            assert es_problema(op["responses"]["413"]), f"{metodo} {ruta}"


def test_todo_multipart_declara_413_y_415_y_su_tope_de_bytes() -> None:
    multipart = []
    for metodo, ruta, op in operaciones(c1()):
        cuerpo = op.get("requestBody", {})
        if "multipart/form-data" in cuerpo.get("content", {}):
            multipart.append((metodo, ruta))
            assert {"413", "415"} <= set(op["responses"]), f"{metodo} {ruta}"
            assert es_problema(op["responses"]["413"]) and es_problema(op["responses"]["415"])
            assert "x-veridicus-max-bytes" in cuerpo, f"{metodo} {ruta}"
            esquema = cuerpo["content"]["multipart/form-data"]["schema"]
            assert esquema["additionalProperties"] is False, f"{metodo} {ruta}"
    assert set(multipart) == {
        ("post", "/sessions/import"),
        ("post", "/sessions/{session_id}/voice-turns"),
        ("post", "/research-reports"),
    }


# --- precisiones de PD-2 -------------------------------------------------------------------------


def test_nfrd_u3_10_el_503_del_login_documenta_retry_after() -> None:
    for estado in ("503", "429"):
        respuesta = operacion("post", "/auth/login")["responses"][estado]
        assert respuesta["headers"]["Retry-After"]["schema"]["type"] == "integer", estado
        assert es_problema(respuesta), estado
    assert (
        "auth.too_many_attempts"
        in operacion("post", "/auth/login")["responses"]["429"]["description"]
    )
    assert "route.not_found" in c1()["components"]["schemas"]["ErrorCode"]["enum"]


def test_nfrd_u7_04_consolidar_lleva_expected_cursor_y_409_view_outdated() -> None:
    op = operacion("post", "/sessions/{session_id}/reports")
    cuerpo = op["requestBody"]
    assert cuerpo["required"] is True
    esquema = cuerpo["content"]["application/json"]["schema"]
    assert esquema["required"] == ["expected_cursor"]
    assert esquema["additionalProperties"] is False
    assert esquema["properties"] == {"expected_cursor": {"$ref": "#/components/schemas/Cursor"}}
    assert {"201", "403", "409", "413", "422", "503"} <= set(op["responses"])
    assert "report.view_outdated" in op["description"]
    assert "El resumen cambió desde que abriste el diálogo" in op["description"]
    cursor = c1()["components"]["schemas"]["Cursor"]
    assert cursor["maxLength"] == 128
    assert cursor["x-veridicus-limit"] == "cursor_max_chars"
    assert c1()["components"]["parameters"]["Since"]["schema"] == {
        "$ref": "#/components/schemas/Cursor"
    }


def test_nfrd_u8_05_la_decision_de_la_aclaracion_tiene_tope_y_413() -> None:
    op = operacion("post", "/conductor-observations/{observation_id}/decision")
    assert op["requestBody"]["x-veridicus-max-bytes"] == "review_body_max_bytes"
    assert es_problema(op["responses"]["413"])
    assert {"200", "403", "404", "409", "413"} <= set(op["responses"])


def test_nfr_u5_05_la_decision_sobre_una_sugerencia_documenta_sus_respuestas() -> None:
    decision = operacion("post", "/suggestions/{suggestion_id}/decisions")
    assert decision["requestBody"]["x-veridicus-max-bytes"] == "review_body_max_bytes"
    assert {"201", "403", "404", "409", "413", "422"} <= set(decision["responses"])
    cuerpo = decision["requestBody"]["content"]["application/json"]["schema"]
    assert cuerpo["additionalProperties"] is False
    assert cuerpo["required"] == ["state"]
    for campo in ("note", "reformulation"):
        assert cuerpo["properties"][campo]["maxLength"] == 2000
        assert cuerpo["properties"][campo]["x-veridicus-limit"] == "review_text_max_chars"
    vistas = estados("post", "/suggestions/{suggestion_id}/observation-views")
    assert {"204", "401", "403", "404"} <= vistas


def test_nfr_u7_02_las_rutas_de_reportes_documentan_403_409_422_y_503() -> None:
    for ruta in (
        "/sessions/{session_id}/finalize",
        "/sessions/{session_id}/correction-rounds",
        "/sessions/{session_id}/correction-rounds/current/discard",
    ):
        assert {"403", "409", "422", "503"} <= estados("post", ruta), ruta
    assert {"403", "413", "422", "503"} <= estados("post", "/sessions/{session_id}/reports")
    descarga = estados("get", "/reports/{report_version_id}/download")
    assert {"200", "403", "409", "422", "503"} <= descarga


def test_nfr_u7_02_descarga_y_exportacion_declaran_las_cabeceras_de_nfr10_4() -> None:
    descarga = operacion("get", "/reports/{report_version_id}/download")["responses"]["200"]
    cabeceras = descarga["headers"]
    assert cabeceras["Content-Disposition"]["schema"] == {"type": "string", "const": "inline"}
    assert cabeceras["X-Content-Type-Options"]["schema"]["const"] == "nosniff"
    assert cabeceras["Cache-Control"]["schema"]["const"] == "no-store"
    assert re.fullmatch(
        r"\^\[a-f0-9\]\{64\}\$", cabeceras["X-Veridicus-SHA256"]["schema"]["pattern"]
    )
    exportacion = operacion("post", "/reports/{report_version_id}/exports")["responses"]
    cabeceras = exportacion["201"]["headers"]
    disposicion = cabeceras["Content-Disposition"]["schema"]["pattern"]
    assert (
        re.fullmatch(disposicion, 'attachment; filename="veridicus-reporte-' + "a" * 8 + '.md"')
        is None
    )
    uuid = "2e9f7b4d-c5a1-4a8e-b3c6-8d2f5a1e9c7b"
    valido = f'attachment; filename="veridicus-reporte-{uuid}-{uuid}.md"'
    assert re.fullmatch(disposicion, valido)
    assert re.fullmatch(disposicion, valido.replace(".md", "/../x.md")) is None
    assert cabeceras["X-Content-Type-Options"]["schema"]["const"] == "nosniff"
    assert cabeceras["Cache-Control"]["schema"]["const"] == "no-store"
    assert "X-Veridicus-Export-SHA256" in cabeceras
    assert {"201", "403", "404", "409", "422", "503"} <= set(exportacion)


def test_nfr_u12_02_subir_un_reporte_que_no_es_multipart_es_415_research_invalid_type() -> None:
    op = operacion("post", "/research-reports")
    assert "research.invalid_type" in op["description"]
    assert "research.invalid_type" in op["responses"]["415"].get("description", "")
    assert {"201", "403", "409", "413", "415", "422"} <= set(op["responses"])
    assert op["requestBody"]["x-veridicus-max-bytes"] == "research_report_max_bytes"
    assert "research.invalid_type" in c1()["components"]["schemas"]["ErrorCode"]["enum"]


def test_nfr_u13_03_las_tres_rutas_de_u13_tienen_tope_de_bytes_y_413() -> None:
    rutas = [
        ("patch", "/sessions/{session_id}/retention"),
        ("post", "/acknowledgements"),
        ("post", "/problem-reports"),
    ]
    for metodo, ruta in rutas:
        op = operacion(metodo, ruta)
        assert op["requestBody"]["x-veridicus-max-bytes"] == "ethics_body_max_bytes", ruta
        assert es_problema(op["responses"]["413"]), ruta
        assert op["x-veridicus-demo"] is True, ruta
    nota = operacion("post", "/problem-reports")["requestBody"]["content"]["application/json"][
        "schema"
    ]
    assert nota["properties"]["note"]["maxLength"] == 2000
    assert nota["properties"]["note"]["x-veridicus-limit"] == "problem_report_note_max_chars"
    assert nota["additionalProperties"] is False


def test_c_3_reanudar_analisis_responde_202_con_la_vista_de_la_sesion() -> None:
    op = operacion("patch", "/sessions/{session_id}/analysis")
    assert op["operationId"] == "set_analysis_paused"
    assert op["responses"]["202"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/SessionView"
    }
    assert op["x-veridicus-roles"] == ["analista"]
    assert op["x-veridicus-owner-only"] is True
    cuerpo = op["requestBody"]["content"]["application/json"]["schema"]
    assert cuerpo["required"] == ["paused"]
    assert cuerpo["additionalProperties"] is False


def test_las_seis_operaciones_que_encolan_solo_declaran_202_como_2xx() -> None:
    por_id = {op["operationId"]: (m, r, op) for m, r, op in operaciones(c1())}
    for identificador, (metodo, ruta) in ENCOLAN.items():
        assert por_id[identificador][:2] == (metodo, ruta), identificador
        dosxx = [e for e in por_id[identificador][2]["responses"] if e.startswith("2")]
        assert dosxx == ["202"], identificador
    otras = {
        (m, r) for i, (m, r, op) in por_id.items() if i not in ENCOLAN and "202" in op["responses"]
    }
    assert otras == set()


def test_las_operaciones_de_lectura_y_de_cierre_no_encolan_con_202() -> None:
    for metodo, ruta, op in operaciones(c1()):
        if metodo == "get":
            assert "202" not in op["responses"], f"{metodo} {ruta}"


# --- fechas, patrones y referencias --------------------------------------------------------------


def test_toda_fecha_tiene_el_formato_unico_con_el_mismo_patron() -> None:
    """BR8.1: el componente `DateTime` es el único que declara `date-time` y lleva el patrón."""
    documento = c1()
    declaraciones = 0
    for ruta, _, valor in recorrer(documento):
        if isinstance(valor, dict) and valor.get("format") == "date-time":
            declaraciones += 1
            assert valor.get("type") == "string", ruta
            assert valor.get("pattern") == PATRON_DE_FECHA, ruta
    assert declaraciones >= 1
    assert documento["components"]["schemas"]["DateTime"]["format"] == "date-time"
    usos = [
        v for _, c, v in recorrer(documento) if c == "$ref" and v == "#/components/schemas/DateTime"
    ]
    assert len(usos) >= 15
    campos = {
        ruta.rsplit(".", 2)[-2]
        for ruta, c, v in recorrer(documento)
        if c == "$ref" and v == "#/components/schemas/DateTime"
    }
    assert {
        "created_at",
        "submitted_at",
        "requested_at",
        "consolidated_at",
        "uploaded_at",
    } <= campos


def test_las_fechas_reales_pasan_y_las_imposibles_o_con_otra_forma_no() -> None:
    validador = validador_de(C1, "#/components/schemas/ReportVersion/properties/consolidated_at")
    assert errores_de(validador, "2026-11-09T21:40:00Z") == []
    for mala in (
        "2026-11-09T21:40:00+00:00",
        "2026-11-09T21:40:00.5Z",
        "2026-11-09 21:40:00Z",
        "2026-02-30T21:40:00Z",
        "2026-11-09T25:40:00Z",
        "09/11/2026",
    ):
        assert errores_de(validador, mala), mala


def test_todo_pattern_es_anclado_y_del_subconjunto_portatil() -> None:
    patrones = 0
    for ruta, valor in esquemas_con(c1(), "pattern"):
        patron = valor["pattern"]
        patrones += 1
        assert patron.startswith("^") and patron.endswith("$"), f"{ruta}: {patron}"
        assert not re.search(r"\\[dDwWsSbB]", patron), f"{ruta}: {patron}"
        assert "(?P<" not in patron and "(?<" not in patron, f"{ruta}: {patron}"
        assert not re.search(r"\(\?[a-zA-Z]", patron), f"{ruta}: bandera en línea {patron}"
        re.compile(patron)
        sin_clases = re.sub(r"\[[^\]]*\]", "[]", patron)
        if re.search(r"[*+]|,\}", sin_clases):
            assert "maxLength" in valor, f"{ruta}: repetición ilimitada sin maxLength"
    assert patrones >= 8


def test_cada_ref_estructural_apunta_a_un_componente_existente_de_su_tipo() -> None:
    documento = c1()
    componentes = documento["components"]
    comprobados = 0
    for ruta, clave, valor in recorrer(documento):
        if clave != "$ref" or not isinstance(valor, str) or not valor.startswith("#/"):
            continue
        partes = valor.split("/")
        assert partes[:2] == ["#", "components"], f"{ruta}: {valor}"
        tipo, nombre = partes[2], partes[3]
        assert re.fullmatch(r"[A-Za-z0-9._-]+", nombre), f"{ruta}: nombre {nombre}"
        assert len(partes) == 4, f"{ruta}: {valor}"
        assert nombre in componentes.get(tipo, {}), f"{ruta}: {valor} no existe"
        if re.search(r"\.parameters\[[0-9]+\]\.\$ref$", ruta):
            assert tipo == "parameters", f"{ruta}: {valor}"
        elif re.search(r"\.responses\.'?[0-9]{3}'?\.\$ref$", ruta):
            assert tipo == "responses", f"{ruta}: {valor}"
        else:
            assert tipo == "schemas", f"{ruta}: {valor}"
        comprobados += 1
    assert comprobados >= 100


def test_los_ref_de_parametros_y_esquemas_son_de_su_tipo() -> None:
    for metodo, ruta, op in operaciones(c1()):
        for parametro in op.get("parameters", []):
            if "$ref" in parametro:
                assert parametro["$ref"].startswith("#/components/parameters/"), f"{metodo} {ruta}"
        for estado, respuesta in op["responses"].items():
            if "$ref" in respuesta:
                assert respuesta["$ref"].startswith("#/components/responses/"), f"{metodo} {ruta}"
            for _, contenido in contenidos(respuesta):
                ref = contenido.get("schema", {}).get("$ref")
                assert ref is None or ref.startswith("#/components/schemas/"), f"{estado}"


def test_las_referencias_a_otros_contratos_son_por_id_canonico_y_resuelven() -> None:
    externas = {
        valor
        for _, clave, valor in recorrer(c1())
        if clave == "$ref" and isinstance(valor, str) and not valor.startswith("#/")
    }
    assert externas == {
        "/veridicus/contracts/integrity/review-suggestion/v2",
        "/veridicus/contracts/analyzer/v1/salida#/$defs/registro/properties/fragmentado",
        "/veridicus/contracts/model_calls/model-call.v1",
        "/veridicus/contracts/cli/report.schema.v2#/properties/totals",
        "/veridicus/contracts/cli/report.schema.v2#/properties/metrics",
        "/veridicus/contracts/cli/report.schema.v2#/properties/bias_table",
    }
    for esquema in ("ReviewSuggestion", "ResearchReportDetail", "Run"):
        errores_de(validador_de(C1, f"#/components/schemas/{esquema}"), {})


def test_review_suggestion_de_c1_acepta_la_sugerencia_valida_de_c7() -> None:
    fixture = cargar_fixture(SUGERENCIA_VALIDA, "C7")
    validador = validador_de(C1, "#/components/schemas/ReviewSuggestion")
    assert errores_de(validador, fixture["payload"]) == []
    assert errores_de(validador, {**fixture["payload"], "is_truthful": False})


def test_model_call_copia_el_enum_de_papel_de_c6() -> None:
    c6 = load_contract(SALIDA_C6)["$defs"]["registro"]["properties"]["llamadas"]["items"]
    papel = c1()["components"]["schemas"]["ModelCall"]["properties"]["papel"]
    assert papel["enum"] == c6["properties"]["papel"]["enum"]


# --- formas de los cuerpos -----------------------------------------------------------------------


def test_los_cuerpos_json_de_c1_son_estrictos() -> None:
    cuerpos = 0
    for metodo, ruta, op in operaciones(c1()):
        for tipo, contenido in contenidos(op.get("requestBody", {})):
            if tipo != "application/json":
                continue
            cuerpos += 1
            esquema = contenido["schema"]
            assert esquema["type"] == "object", f"{metodo} {ruta}"
            assert esquema["additionalProperties"] is False, f"{metodo} {ruta}"
    assert cuerpos >= 13


def test_consentimiento_es_estricto_y_exige_constancia_segun_el_tipo() -> None:
    consentimiento = c1()["components"]["schemas"]["Consent"]
    assert consentimiento["additionalProperties"] is False
    validador = validador_de(C1, "#/components/schemas/Consent")
    base = {
        "tipo": "persona",
        "version_texto": "1.0.0",
        "autoriza_transferencia": False,
        "autoriza_voz": False,
        "autoriza_conservar_audio": False,
        "requiere_mandato": False,
    }
    assert errores_de(validador, base) == []
    assert errores_de(validador, {**base, "tipo": "autoridad"})
    assert errores_de(validador, {**base, "tipo": "autoridad", "constancia": "C-001"}) == []
    assert errores_de(validador, {**base, "requiere_mandato": True})
    assert errores_de(validador, {**base, "extra": 1})


def test_cursor_y_login_tienen_los_topes_de_nfr_u3_01_y_nfr_u4() -> None:
    cuerpo = operacion("post", "/auth/login")["requestBody"]["content"]["application/json"][
        "schema"
    ]
    assert cuerpo["properties"]["username"]["maxLength"] == 32
    assert cuerpo["properties"]["password"]["maxLength"] == 128
    turno = operacion("post", "/sessions/{session_id}/turns")["requestBody"]
    texto = turno["content"]["application/json"]["schema"]["properties"]["texto"]
    assert texto["maxLength"] == 20000
    assert estados("post", "/sessions/{session_id}/turns") >= {"202", "409", "413"}


def test_la_vista_de_sesion_lista_report_final_mode_not_launched_entre_los_bloqueos() -> None:
    bloqueos = c1()["components"]["schemas"]["SessionView"]["allOf"][1]["properties"][
        "consolidation_blockers"
    ]
    assert bloqueos["items"] == {"$ref": "#/components/schemas/ErrorCode"}
    assert "report.final_mode_not_launched" in c1()["components"]["schemas"]["ErrorCode"]["enum"]
