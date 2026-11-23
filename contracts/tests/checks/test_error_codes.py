"""Módulo guardia de errores: catálogo y clases uno a uno, tabla de C6 (E31, E34, E44, BR7.4).

Los controles negativos trabajan sobre copias en `tmp_path`; nunca se toca un archivo versionado.
"""

import json
import shutil
from pathlib import Path

from helpers import CONTRACTS_ROOT

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
