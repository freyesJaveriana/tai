"""Lecturas de vuelta de las seis correcciones de U01-T15b (E-11 a E-15, P-T15b-1).

Cada corrección tiene un caso positivo, que lee el contrato real con el cargador del paquete, y un
control negativo, que aplica la misma comprobación a una copia en memoria a la que se le quita la
marca o se le cambia la cifra. Nunca se escribe en los contratos versionados.
"""

import copy
import re
from collections.abc import Callable
from typing import Any

from helpers import load_contract

LIMITES = "limits.v1.yaml"
C1 = "api/console.v2.yaml"
C5 = "queues/speech.v2.yaml"
C13 = "model_calls/model-call.v1.yaml"
C19 = "cli/report.schema.v2.yaml"
ERRORES = "errors/error-codes.v2.yaml"

Comprobacion = Callable[[Any], list[str]]

NUEVAS = {
    "session_body_max_bytes": (32768, "bytes", "U4", ["C1"]),
    "model_call_role_max_chars": (32, "chars", "U1", ["C19"]),
    "report_per_run_items": (3, "runs", "U1", ["C19"]),
}
CODIGO = re.compile(r"\b[a-z_]+\.[a-z_]+\b")


def _copia(relativa: str) -> Any:
    return copy.deepcopy(load_contract(relativa))


# ---- 1. C25: entradas nuevas (E-11, E-14, P-T15b-1) ----------------------------------------


def comprobar_entradas(catalogo: Any) -> list[str]:
    problemas: list[str] = []
    for nombre, (valor, unidad, dueno, usos) in NUEVAS.items():
        entrada = catalogo["limits"].get(nombre)
        esperado = {"value": valor, "unit": unidad, "owner": dueno, "used_in": usos}
        if entrada != esperado:
            problemas.append(f"{nombre}: {entrada!r} distinto de {esperado!r}")
    return problemas


def test_c25_declara_las_tres_entradas_nuevas() -> None:
    assert comprobar_entradas(load_contract(LIMITES)) == []


def test_c25_control_negativo_una_cifra_cambiada_o_una_entrada_ausente_se_detecta() -> None:
    cambiada = _copia(LIMITES)
    cambiada["limits"]["session_body_max_bytes"]["value"] = 65536
    assert comprobar_entradas(cambiada)
    ausente = _copia(LIMITES)
    del ausente["limits"]["report_per_run_items"]
    assert comprobar_entradas(ausente)


# ---- 2. C25: used_in de C5 (E-15) -------------------------------------------------------------


def comprobar_used_in_c5(catalogo: Any) -> list[str]:
    return [
        f"{nombre} sin C5 en used_in"
        for nombre in ("turn_max_chars", "report_token_max_chars")
        if "C5" not in catalogo["limits"][nombre]["used_in"]
    ]


def test_c25_marca_c5_en_turn_max_chars_y_report_token_max_chars() -> None:
    catalogo = load_contract(LIMITES)
    assert comprobar_used_in_c5(catalogo) == []
    assert catalogo["limits"]["turn_max_chars"]["used_in"] == ["C1", "C2", "C5"]
    # E-25 (T18b): suma C2 y C21, los contratos nuevos que vigila §4.4
    assert catalogo["limits"]["report_token_max_chars"]["used_in"] == ["C2", "C5", "C19", "C21"]


def test_c25_control_negativo_sin_c5_se_detecta() -> None:
    copia = _copia(LIMITES)
    copia["limits"]["turn_max_chars"]["used_in"] = ["C1", "C2"]
    assert comprobar_used_in_c5(copia)


# ---- 3. C1: POST /sessions (E-14) ---------------------------------------------------------------


def comprobar_sesion(c1: Any) -> list[str]:
    problemas: list[str] = []
    op = c1["paths"]["/sessions"]["post"]
    if op["requestBody"].get("x-veridicus-max-bytes") != "session_body_max_bytes":
        problemas.append("requestBody sin x-veridicus-max-bytes: session_body_max_bytes")
    perfil = op["requestBody"]["content"]["application/json"]["schema"]["properties"]["profile_name"]
    if perfil.get("pattern") != "^[a-z0-9-]{1,48}$":
        problemas.append(f"profile_name sin el patron de /sessions/import: {perfil!r}")
    if "413" not in op["responses"]:
        problemas.append("sin respuesta 413")
    elif op["responses"]["413"].get("$ref") != "#/components/responses/Problem":
        problemas.append("413 sin $ref a Problem")
    return problemas


def test_c1_post_sessions_tiene_tope_de_bytes_patron_de_perfil_y_413() -> None:
    assert comprobar_sesion(load_contract(C1)) == []
    importacion = load_contract(C1)["paths"]["/sessions/import"]["post"]
    esquema = importacion["requestBody"]["content"]["multipart/form-data"]["schema"]
    assert esquema["properties"]["profile_name"]["pattern"] == "^[a-z0-9-]{1,48}$"


def test_c1_control_negativo_sin_marca_patron_o_413_se_detecta() -> None:
    sin_marca = _copia(C1)
    del sin_marca["paths"]["/sessions"]["post"]["requestBody"]["x-veridicus-max-bytes"]
    assert comprobar_sesion(sin_marca)
    sin_patron = _copia(C1)
    cuerpo = sin_patron["paths"]["/sessions"]["post"]["requestBody"]["content"]["application/json"]
    del cuerpo["schema"]["properties"]["profile_name"]["pattern"]
    assert comprobar_sesion(sin_patron)
    sin_413 = _copia(C1)
    del sin_413["paths"]["/sessions"]["post"]["responses"]["413"]
    assert comprobar_sesion(sin_413)


# ---- 4. C1: estados por code (E-12) ----------------------------------------------------------


def _estado_de_cada_code() -> dict[str, int]:
    codigos = load_contract(ERRORES)["codes"]
    return {codigo: datos["status"] for codigo, datos in codigos.items() if "status" in datos}


def _codes_mal_ubicados(c1: Any, metodo: str, ruta: str) -> list[str]:
    """Cada code citado en la descripción de una respuesta tiene en el catálogo ese estado."""
    estados = _estado_de_cada_code()
    problemas: list[str] = []
    for estado, respuesta in c1["paths"][ruta][metodo]["responses"].items():
        for codigo in CODIGO.findall(respuesta.get("description", "")):
            if codigo in estados and estados[codigo] != int(estado):
                problemas.append(f"{codigo}: catalogo {estados[codigo]}, C1 {estado}")
    return problemas


def comprobar_estados(c1: Any) -> list[str]:
    problemas = _codes_mal_ubicados(c1, "patch", "/users/{user_id}")
    problemas += _codes_mal_ubicados(c1, "post", "/acknowledgements")
    respuestas = c1["paths"]["/acknowledgements"]["post"]["responses"]
    if "409" in respuestas:
        problemas.append("POST /acknowledgements conserva una 409 sin code de estado 409")
    if "ethics.text_version_outdated" not in respuestas.get("422", {}).get("description", ""):
        problemas.append("la 422 de /acknowledgements no cita ethics.text_version_outdated")
    patch = c1["paths"]["/users/{user_id}"]["patch"]["responses"]
    if "validation.invalid_request" not in patch["422"].get("description", ""):
        problemas.append("la 422 de PATCH /users no cita validation.invalid_request")
    return problemas


def test_c1_cada_code_de_las_dos_operaciones_esta_en_el_estado_del_catalogo() -> None:
    assert comprobar_estados(load_contract(C1)) == []
    patch = load_contract(C1)["paths"]["/users/{user_id}"]["patch"]["responses"]
    assert "409" in patch, "la 409 de PATCH /users se queda con sus code de estado 409"


def test_c1_control_negativo_un_code_en_el_estado_equivocado_se_detecta() -> None:
    mal_patch = _copia(C1)
    patch = mal_patch["paths"]["/users/{user_id}"]["patch"]["responses"]
    patch["409"]["description"] += " validation.invalid_request"
    assert comprobar_estados(mal_patch)
    mal_ack = _copia(C1)
    ack = mal_ack["paths"]["/acknowledgements"]["post"]["responses"]
    ack["409"] = {"$ref": "#/components/responses/Problem", "description": "ethics.text_version_outdated"}
    assert comprobar_estados(mal_ack)


# ---- 5. C5: TranscriptResult (E-15) -------------------------------------------------------------


def comprobar_transcripcion(c5: Any) -> list[str]:
    propiedades = c5["components"]["messages"]["TranscriptResult"]["payload"]["properties"]
    esperado = {"text": (20000, "turn_max_chars"), "model_digest": (128, "report_token_max_chars")}
    problemas: list[str] = []
    for campo, (tope, cifra) in esperado.items():
        esquema = propiedades[campo]
        if esquema.get("maxLength") != tope:
            problemas.append(f"{campo}: maxLength {esquema.get('maxLength')!r}")
        if esquema.get("x-veridicus-limit") != cifra:
            problemas.append(f"{campo}: x-veridicus-limit {esquema.get('x-veridicus-limit')!r}")
    return problemas


def test_c5_text_y_model_digest_llevan_tope_y_marca() -> None:
    assert comprobar_transcripcion(load_contract(C5)) == []


def test_c5_control_negativo_sin_marca_o_con_otra_cifra_se_detecta() -> None:
    sin_marca = _copia(C5)
    propiedades = sin_marca["components"]["messages"]["TranscriptResult"]["payload"]["properties"]
    del propiedades["text"]["x-veridicus-limit"]
    assert comprobar_transcripcion(sin_marca)
    otra_cifra = _copia(C5)
    propiedades = otra_cifra["components"]["messages"]["TranscriptResult"]["payload"]["properties"]
    propiedades["model_digest"]["maxLength"] = 256
    assert comprobar_transcripcion(otra_cifra)


# ---- 6. C19 y C13: role, token y per_run (E-11, E-15) ------------------------------------------


def comprobar_llamada(c13: Any) -> list[str]:
    problemas: list[str] = []
    if c13["properties"]["role"].get("x-veridicus-limit") != "model_call_role_max_chars":
        problemas.append("role sin x-veridicus-limit: model_call_role_max_chars")
    if c13["properties"]["role"].get("maxLength") != 32:
        problemas.append("role sin maxLength 32")
    if c13["$defs"]["token"].get("x-veridicus-limit") != "report_token_max_chars":
        problemas.append("token sin x-veridicus-limit: report_token_max_chars")
    return problemas


def comprobar_per_run(c19: Any) -> list[str]:
    problemas: list[str] = []
    for nombre in ("metric_ratio", "metric_count"):
        per_run = c19["$defs"][nombre]["properties"]["per_run"]
        if per_run.get("x-veridicus-limit") != "report_per_run_items":
            problemas.append(f"{nombre}.per_run sin x-veridicus-limit: report_per_run_items")
        if (per_run.get("minItems"), per_run.get("maxItems")) != (3, 3):
            problemas.append(f"{nombre}.per_run sin minItems/maxItems 3")
    return problemas


def test_c19_role_token_y_per_run_llevan_su_marca() -> None:
    assert comprobar_llamada(load_contract(C13)) == []
    assert comprobar_per_run(load_contract(C19)) == []


def test_c19_control_negativo_sin_marca_o_sin_cifra_se_detecta() -> None:
    sin_rol = _copia(C13)
    del sin_rol["properties"]["role"]["x-veridicus-limit"]
    assert comprobar_llamada(sin_rol)
    sin_token = _copia(C13)
    del sin_token["$defs"]["token"]["x-veridicus-limit"]
    assert comprobar_llamada(sin_token)
    sin_per_run = _copia(C19)
    del sin_per_run["$defs"]["metric_count"]["properties"]["per_run"]["x-veridicus-limit"]
    assert comprobar_per_run(sin_per_run)
    otra_cifra = _copia(C19)
    otra_cifra["$defs"]["metric_ratio"]["properties"]["per_run"]["maxItems"] = 5
    assert comprobar_per_run(otra_cifra)
