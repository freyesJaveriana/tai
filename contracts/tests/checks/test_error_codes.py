"""Módulo guardia de errores: catálogo y clases uno a uno, tabla de C6 (E31, E34, E44, BR7.4).

Los controles negativos trabajan sobre copias en `tmp_path`; nunca se toca un archivo versionado.
"""

import copy
import json
import shutil
from pathlib import Path
from typing import Any

from helpers import CONTRACTS_ROOT, load_contract

from veridicus_contracts.checks import error_codes as guardia

ERRORS_SRC = CONTRACTS_ROOT.parent / "libs" / "errors" / "src"
SALIDA_C6 = CONTRACTS_ROOT / "analyzer" / "v1" / "salida.schema.json"
CATALOGO = CONTRACTS_ROOT / "errors" / "error-codes.v2.yaml"

CATALOGO_MINIMO = {
    "a.uno": {"status": 400, "class": "AUnoError", "unit": "U1", "http": True, "c6": "x"},
    "a.dos": {"status": 409, "class": "ADosError", "unit": "U1", "http": True},
}
FUENTE_MINIMA = '''
class VeridicusError(Exception):
    """Raíz."""


class AFamilyError(VeridicusError):
    """Familia."""


class AUnoError(AFamilyError):
    code = "a.uno"


class ADosError(AFamilyError):
    code: str = "a.dos"
'''


def _fuente(tmp_path: Path, texto: str) -> Path:
    src = tmp_path / "src"
    src.mkdir(exist_ok=True)
    (src / "mod.py").write_text(texto, encoding="utf-8")
    return src


def _problemas(tmp_path: Path, texto: str, catalogo: dict | None = None) -> list[str]:
    clases = guardia.leer_clases(_fuente(tmp_path, texto))
    return guardia.comprobar_clases(catalogo or CATALOGO_MINIMO, clases)


def test_el_arbol_versionado_cumple_todo() -> None:
    assert guardia.comprobar(CONTRACTS_ROOT, ERRORS_SRC) == []


def test_fuente_minima_correcta_con_asignacion_simple_y_anotada(tmp_path: Path) -> None:
    assert _problemas(tmp_path, FUENTE_MINIMA) == []


def test_e31_code_sin_clase(tmp_path: Path) -> None:
    fuente = FUENTE_MINIMA.replace("class ADosError(AFamilyError):", "class Otra(AFamilyError):")
    problemas = _problemas(tmp_path, fuente.replace('code: str = "a.dos"', "pass"))
    assert any("a.dos: sin clase de excepción (E31, E44)" in p for p in problemas), problemas


def test_e31_clase_sin_code(tmp_path: Path) -> None:
    problemas = _problemas(
        tmp_path, FUENTE_MINIMA + "\n\nclass Huerfana(AFamilyError):\n    pass\n"
    )
    assert any("Huerfana: clase de excepción sin code (E31)" in p for p in problemas), problemas


def test_e31_clase_con_code_fuera_del_catalogo(tmp_path: Path) -> None:
    extra = '\n\nclass Nueva(AFamilyError):\n    code = "a.tres"\n'
    problemas = _problemas(tmp_path, FUENTE_MINIMA + extra)
    assert any("Nueva: su code a.tres no está en el catálogo" in p for p in problemas), problemas


def test_e44_session_blocked_sin_clase_en_el_arbol_real(tmp_path: Path) -> None:
    copia = tmp_path / "errors-src"
    shutil.copytree(ERRORS_SRC, copia, ignore=shutil.ignore_patterns("__pycache__"))
    init = copia / "veridicus_errors" / "__init__.py"
    texto = init.read_text(encoding="utf-8")
    assert 'code: ClassVar[str] = "session.blocked"' in texto
    init.write_text(
        texto.replace('code: ClassVar[str] = "session.blocked"', "pass"), encoding="utf-8"
    )
    catalogo = guardia.cargar_catalogo(CATALOGO)
    problemas = guardia.comprobar_clases(catalogo, guardia.leer_clases(copia))
    assert any("session.blocked: sin clase de excepción (E31, E44)" in p for p in problemas)


def test_dos_clases_comparten_code(tmp_path: Path) -> None:
    extra = '\n\nclass Gemela(AFamilyError):\n    code = "a.uno"\n'
    problemas = _problemas(tmp_path, FUENTE_MINIMA + extra)
    assert any("a.uno: dos clases comparten el code: AUnoError, Gemela" in p for p in problemas)


def test_nombre_de_clase_distinto_del_catalogo(tmp_path: Path) -> None:
    problemas = _problemas(tmp_path, FUENTE_MINIMA.replace("class AUnoError", "class Renombrada"))
    assert any("la clase es Renombrada y el catálogo dice AUnoError" in p for p in problemas)


def test_clase_con_logica_o_atributos_extra(tmp_path: Path) -> None:
    con_metodo = FUENTE_MINIMA.replace(
        'code = "a.uno"', 'code = "a.uno"\n\n    def estado(self) -> int:\n        return 400'
    )
    assert any("AUnoError: define lógica" in p for p in _problemas(tmp_path, con_metodo))
    con_status = FUENTE_MINIMA.replace('code = "a.uno"', 'code = "a.uno"\n    status = 400')
    assert any("AUnoError: define lógica" in p for p in _problemas(tmp_path, con_status))


def test_code_que_no_es_texto_o_no_es_el_unico_destino_no_cuenta(tmp_path: Path) -> None:
    sin_texto = FUENTE_MINIMA.replace('code = "a.uno"', "code = 400")
    problemas_sin_texto = _problemas(tmp_path, sin_texto)
    assert any("AUnoError: su code no es un texto literal (E31)" in p for p in problemas_sin_texto)
    assert any("a.uno: sin clase" in p for p in problemas_sin_texto)
    doble = FUENTE_MINIMA.replace('code = "a.uno"', 'code = other = "a.uno"')
    assert any("a.uno: sin clase" in p for p in _problemas(tmp_path, doble))
    otro_nombre = FUENTE_MINIMA.replace('code = "a.uno"', 'codigo = "a.uno"')
    assert any("a.uno: sin clase" in p for p in _problemas(tmp_path, otro_nombre))
    atributo = FUENTE_MINIMA.replace('code = "a.uno"', 'self.code = "a.uno"')
    assert any("a.uno: sin clase" in p for p in _problemas(tmp_path, atributo))


def test_base_que_no_es_un_nombre_simple(tmp_path: Path) -> None:
    fuente = FUENTE_MINIMA + '\n\nclass Externa(otro.Base):\n    code = "a.dos"\n'
    assert any("dos clases comparten" in p for p in _problemas(tmp_path, fuente))


def _c6(tmp_path: Path, enum: list[str]) -> Path:
    ruta = tmp_path / "salida.json"
    esquema = {"properties": {"error": {"properties": {"codigo": {"enum": enum}}}}}
    ruta.write_text(json.dumps(esquema), encoding="utf-8")
    return ruta


def test_tabla_c6_del_arbol_real_completa() -> None:
    catalogo = guardia.cargar_catalogo(CATALOGO)
    assert guardia.comprobar_tabla_c6(catalogo, SALIDA_C6) == []
    assert catalogo["analysis.provider"]["c6"] == "proveedor"


def test_e34_codigo_de_c6_sin_code(tmp_path: Path) -> None:
    catalogo = guardia.cargar_catalogo(CATALOGO)
    sin = {code: dict(e) for code, e in catalogo.items()}
    del sin["anonymizer.incident"]["c6"]
    problemas = guardia.comprobar_tabla_c6(sin, SALIDA_C6)
    assert any("'incidente_anonimizacion' de C6 sin code" in p for p in problemas), problemas


def test_e34_proveedor_traducido_a_otro_code() -> None:
    catalogo = guardia.cargar_catalogo(CATALOGO)
    mal = {code: dict(e) for code, e in catalogo.items()}
    del mal["analysis.provider"]["c6"]
    mal["analysis.system"]["c6"] = "proveedor"
    problemas = guardia.comprobar_tabla_c6(mal, SALIDA_C6)
    assert any("'proveedor' debe traducirse a analysis.provider" in p for p in problemas)


def test_e34_c6_inexistente_y_repetido(tmp_path: Path) -> None:
    catalogo = guardia.cargar_catalogo(CATALOGO)
    mal = {code: dict(e) for code, e in catalogo.items()}
    mal["analysis.system"]["c6"] = "inventado"
    mal["speech.unavailable"]["c6"] = "proveedor"
    problemas = guardia.comprobar_tabla_c6(mal, SALIDA_C6)
    assert any("c6 'inventado' de analysis.system no es un error.codigo" in p for p in problemas)
    assert any("dos code traducen el mismo error.codigo" in p for p in problemas)
    enum_corto = _c6(tmp_path, ["proveedor"])
    sobrante = guardia.comprobar_tabla_c6(catalogo, enum_corto)
    assert any("no es un error.codigo de C6" in p for p in sobrante)


def test_codes_usados_existentes_y_ausentes(tmp_path: Path) -> None:
    catalogo = guardia.cargar_catalogo(CATALOGO)
    bien = tmp_path / "bien.yaml"
    bien.write_text(
        "a:\n  error_code:\n    type: string\n    enum: [analysis.system, analysis.timeout]\n"
        "b:\n  - code: limits.exceeded\n    status: 413\n    nota: x.y\n  - 7\n  - true\n",
        encoding="utf-8",
    )
    assert guardia.comprobar_codes_usados(catalogo, [bien]) == []
    mal = tmp_path / "mal.yaml"
    mal.write_text("error_code: { enum: [analysis.system, inventado.code] }\n", encoding="utf-8")
    problemas = guardia.comprobar_codes_usados(catalogo, [bien, mal])
    assert problemas == ["mal.yaml: el code inventado.code no está en el catálogo (BR7.2)"]
    assert guardia.comprobar_codes_usados(catalogo, []) == []


def test_base_de_la_clase_debe_ser_su_familia(tmp_path: Path) -> None:
    fuera = FUENTE_MINIMA.replace("class AUnoError(AFamilyError)", "class AUnoError(Exception)")
    assert any(
        "AUnoError: su base debe ser AFamilyError (BR7.4)" in p for p in _problemas(tmp_path, fuera)
    )
    otra = FUENTE_MINIMA.replace("class AUnoError(AFamilyError)", "class AUnoError(VeridicusError)")
    assert any("AUnoError: su base debe ser AFamilyError" in p for p in _problemas(tmp_path, otra))


def test_la_familia_debe_heredar_de_la_raiz(tmp_path: Path) -> None:
    suelta = FUENTE_MINIMA.replace(
        "class AFamilyError(VeridicusError)", "class AFamilyError(Exception)"
    )
    esperado = "AFamilyError: la base de familia debe heredar de VeridicusError (BR7.4)"
    assert esperado in _problemas(tmp_path, suelta)
    sin_familia = FUENTE_MINIMA.replace(
        "class AFamilyError(VeridicusError)", "class Otra(VeridicusError)"
    )
    assert esperado in _problemas(tmp_path, sin_familia)


def _copia_del_arbol(tmp_path: Path) -> tuple[Path, Path]:
    """Copia mínima de contracts/ y libs/errors/src/ en tmp_path, con un contrato por patrón."""
    contracts = tmp_path / "repo" / "contracts"
    (contracts / "errors").mkdir(parents=True)
    (contracts / "analyzer" / "v1").mkdir(parents=True)
    (contracts / "queues").mkdir()
    (contracts / "api").mkdir()
    shutil.copy(CATALOGO, contracts / "errors" / CATALOGO.name)
    shutil.copy(SALIDA_C6, contracts / "analyzer" / "v1" / SALIDA_C6.name)
    (contracts / "queues" / "x.yaml").write_text("error_code: analysis.system\n", encoding="utf-8")
    (contracts / "api" / "y.yaml").write_text("code: limits.exceeded\n", encoding="utf-8")
    src = tmp_path / "repo" / "libs" / "errors" / "src"
    shutil.copytree(ERRORS_SRC, src, ignore=shutil.ignore_patterns("__pycache__"))
    return contracts, src


def test_comprobar_sobre_una_copia_limpia_y_con_un_defecto_por_subcomprobacion(
    tmp_path: Path,
) -> None:
    contracts, src = _copia_del_arbol(tmp_path)
    assert guardia.comprobar(contracts, src) == []
    # (b) en queues/ y en api/: un code inventado
    (contracts / "queues" / "x.yaml").write_text("error_code: inventado.q\n", encoding="utf-8")
    (contracts / "api" / "y.yaml").write_text("code: inventado.a\n", encoding="utf-8")
    problemas = guardia.comprobar(contracts, src)
    assert sorted(p for p in problemas if "inventado" in p) == [
        "x.yaml: el code inventado.q no está en el catálogo (BR7.2)",
        "y.yaml: el code inventado.a no está en el catálogo (BR7.2)",
    ]
    assert len(problemas) == 2
    # E34: un error.codigo de C6 sin traducir
    catalogo = contracts / "errors" / CATALOGO.name
    texto = catalogo.read_text(encoding="utf-8")
    catalogo.write_text(texto.replace(", c6: tiempo_agotado", ""), encoding="utf-8")
    (contracts / "queues" / "x.yaml").write_text("error_code: analysis.system\n", encoding="utf-8")
    (contracts / "api" / "y.yaml").write_text("code: limits.exceeded\n", encoding="utf-8")
    assert [p for p in guardia.comprobar(contracts, src) if "tiempo_agotado" in p]
    catalogo.write_text(texto, encoding="utf-8")
    # E31: una clase sin su code
    init = src / "veridicus_errors" / "__init__.py"
    codigo = init.read_text(encoding="utf-8")
    init.write_text(codigo.replace('code: ClassVar[str] = "auth.csrf"', "pass"), encoding="utf-8")
    assert [p for p in guardia.comprobar(contracts, src) if "auth.csrf" in p]


# --- Parte de C1 y C21 (§4.7 a-d; paso 16, T15; K-05, K-18, K-19, E44) ---

CONSOLA = "api/console.v2.yaml"
PROBLEM = {"$ref": "#/components/responses/Problem"}


def _catalogo() -> dict[str, dict[str, Any]]:
    return guardia.cargar_catalogo(CATALOGO)


def _c1() -> dict[str, Any]:
    return copy.deepcopy(load_contract(CONSOLA))


def _respuestas(documento: dict[str, Any], nombre: str = CONSOLA, problem: bool = True) -> set[str]:
    return set(guardia.comprobar_respuestas(_catalogo(), nombre, documento, problem))


def _nuevas(antes: set[str], despues: set[str]) -> list[str]:
    return sorted(despues - antes)


def test_el_enum_de_error_code_es_el_de_los_codes_http_del_catalogo() -> None:
    catalogo = _catalogo()
    assert guardia.comprobar_enum_error_code(catalogo, CONSOLA, _c1()) == []
    sin_uno = _c1()
    sin_uno["components"]["schemas"]["ErrorCode"]["enum"].remove("speech.unavailable")
    de_mas = _c1()
    de_mas["components"]["schemas"]["ErrorCode"]["enum"] += ["inventado.code", "anonymizer.incident"]
    assert guardia.comprobar_enum_error_code(catalogo, CONSOLA, sin_uno) == [
        "api/console.v2.yaml: el enum ErrorCode no trae speech.unavailable (§4.7 a)"
    ]
    assert guardia.comprobar_enum_error_code(catalogo, CONSOLA, de_mas) == [
        ("api/console.v2.yaml: el enum ErrorCode trae anonymizer.incident y el catálogo no lo "
        "declara con http: true (§4.7 a)"),
        ("api/console.v2.yaml: el enum ErrorCode trae inventado.code y el catálogo no lo declara "
        "con http: true (§4.7 a)"),
    ]
    sin_enum = _c1()
    del sin_enum["components"]["schemas"]["ErrorCode"]
    assert guardia.comprobar_enum_error_code(catalogo, CONSOLA, sin_enum)[0] == (
        "api/console.v2.yaml: el enum ErrorCode no trae auth.invalid_credentials (§4.7 a)"
    )


def test_c21_y_la_ruta_de_voz_usan_los_estados_del_catalogo() -> None:
    for relativa in ("api/anonymizer-proxy.v1.yaml", "api/speech-internal.v1.yaml"):
        documento = load_contract(relativa)
        assert guardia.comprobar_respuestas(_catalogo(), relativa, documento, False) == [], relativa


def test_los_codes_de_c1_se_buscan_en_el_enum_y_en_las_descripciones(tmp_path: Path) -> None:
    catalogo = _catalogo()
    archivo = tmp_path / "console.yaml"
    archivo.write_text(
        "components:\n  schemas:\n    ErrorCode:\n      type: string\n"
        "      enum: [analysis.system, inventado.code]\n",
        encoding="utf-8",
    )
    assert guardia.comprobar_codes_usados(catalogo, [archivo]) == [
        "console.yaml: el code inventado.code no está en el catálogo (BR7.2)"
    ]
    antes = _respuestas(_c1())
    documento = _c1()
    documento["paths"]["/users"]["get"]["responses"]["403"] = {
        **PROBLEM,
        "description": "auth.forbidden o auth.inventado (E44)",
    }
    assert _nuevas(antes, _respuestas(documento)) == [
        ("api/console.v2.yaml: GET /users 403: el code auth.inventado no está en el catálogo "
        "(BR7.2, E44)")
    ]


def test_un_code_con_otro_estado_que_el_del_catalogo_es_rojo() -> None:
    antes = _respuestas(_c1())
    documento = _c1()
    respuestas = documento["paths"]["/users"]["post"]["responses"]
    respuestas["422"]["description"] = "user.weak_password o session.blocked (K-18)"
    respuestas["409"]["description"] = "anonymizer.incident no tiene estado HTTP"
    assert _nuevas(antes, _respuestas(documento)) == [
        ("api/console.v2.yaml: POST /users 409: el code anonymizer.incident no tiene estado HTTP "
        "en el catálogo (§4.7 c)"),
        ("api/console.v2.yaml: POST /users 422: el code session.blocked lleva el estado 422 y el "
        "catálogo dice 409 (§4.7 c)"),
    ]
    voz = load_contract("api/speech-internal.v1.yaml")
    mal = copy.deepcopy(voz)
    mal["paths"]["/internal/v1/speech"]["post"]["responses"]["422"]["description"] = (
        "speech.text_rejected con rule_id"
    )
    assert guardia.comprobar_respuestas(_catalogo(), "voz", mal, False) == [
        ("voz: POST /internal/v1/speech 422: el code speech.text_rejected lleva el estado 422 y el "
        "catálogo dice 409 (§4.7 c)")
    ]


def test_toda_4xx_y_5xx_de_c1_es_una_referencia_a_problem() -> None:
    antes = _respuestas(_c1())
    documento = _c1()
    documento["paths"]["/users"]["post"]["responses"]["409"] = {"description": "sin Problem"}
    documento["paths"]["/users"]["post"]["responses"]["default"] = {"description": "otra"}
    esquema = {"$ref": "#/components/schemas/Problem"}
    cabeceras = {"Retry-After": {"schema": {"type": "integer"}}}
    documento["paths"]["/auth/me"]["get"]["responses"]["401"] = {
        "description": "con cabeceras propias",
        "headers": cabeceras,
        "content": {"application/problem+json": {"schema": esquema}},
    }
    assert _nuevas(antes, _respuestas(documento)) == [
        "api/console.v2.yaml: POST /users 409: respuesta de error sin $ref a Problem (§4.7 d)"
    ]
    # C21 y la ruta de voz traen su propio cuerpo de error: no se les exige la referencia.
    assert not any("sin $ref a Problem" in p for p in _respuestas(documento, "x", False))


def test_una_respuesta_de_error_en_linea_exige_cabeceras_propias_y_problem_json() -> None:
    """P-T15-3: un control negativo por condición del cuerpo en línea."""
    esquema = {"$ref": "#/components/schemas/Problem"}
    cabeceras = {"Retry-After": {"schema": {"type": "integer"}}}
    en_linea = {
        "completa": ({"headers": cabeceras, "content": {"application/problem+json": {"schema": esquema}}}, True),
        "sin_cabeceras": ({"content": {"application/problem+json": {"schema": esquema}}}, False),
        "cabeceras_vacias": (
            {"headers": {}, "content": {"application/problem+json": {"schema": esquema}}},
            False,
        ),
        "otro_tipo": ({"headers": cabeceras, "content": {"application/json": {"schema": esquema}}}, False),
        "otro_esquema": (
            {
                "headers": cabeceras,
                "content": {
                    "application/problem+json": {"schema": {"$ref": "#/components/schemas/Otro"}}
                },
            },
            False,
        ),
    }
    antes = _respuestas(_c1())
    for nombre, (respuesta, cumple) in en_linea.items():
        documento = _c1()
        documento["paths"]["/auth/me"]["get"]["responses"]["429"] = {
            "description": nombre,
            **respuesta,
        }
        esperado = [] if cumple else [
            "api/console.v2.yaml: GET /auth/me 429: respuesta de error sin $ref a Problem (§4.7 d)"
        ]
        assert _nuevas(antes, _respuestas(documento)) == esperado, nombre


def test_en_la_prosa_solo_cuenta_un_code_con_prefijo_de_dominio_del_catalogo() -> None:
    """P-T15-4: «e.g.», versiones y nombres de archivo no son un `code`."""
    antes = _respuestas(_c1())
    ajena = _c1()
    ajena["paths"]["/users"]["get"]["responses"]["403"] = {
        **PROBLEM,
        "description": "auth.forbidden; p. ej. e.g. o i.e., v1.2, console.yaml y a.b",
    }
    assert _nuevas(antes, _respuestas(ajena)) == []
    # Control negativo: el prefijo existe en el catálogo y el code no.
    propia = _c1()
    propia["paths"]["/users"]["get"]["responses"]["403"] = {
        **PROBLEM,
        "description": "auth.forbidden o session.inventado",
    }
    assert _nuevas(antes, _respuestas(propia)) == [
        ("api/console.v2.yaml: GET /users 403: el code session.inventado no está en el catálogo "
        "(BR7.2, E44)")
    ]


def test_comprobar_api_con_contratos_ausentes_y_sobre_el_arbol_real(tmp_path: Path) -> None:
    assert sorted(guardia.comprobar_api(tmp_path)) == [
        "api/anonymizer-proxy.v1.yaml: contrato ausente (§4.7)",
        "api/console.v2.yaml: contrato ausente (§4.7)",
        "api/speech-internal.v1.yaml: contrato ausente (§4.7)",
        "errors/error-codes.v2.yaml: contrato ausente (§4.7)",
    ]
    assert guardia.comprobar_api(CONTRACTS_ROOT) == []
