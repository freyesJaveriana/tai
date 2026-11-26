"""Constantes TypeScript generadas en `contracts/ts/generated/` (D9, §4.14, U01-T19)."""

import json
import re
import shutil
from pathlib import Path
from types import ModuleType

import pytest
from helpers import importar_o_fallar, load_contract, ruta_de

from veridicus_contracts.checks import auth_surface

CARPETA = "ts/generated"
NOMBRES = {
    "auth-surface.ts",
    "error-codes.ts",
    "forbidden-vocabulary.ts",
    "result-labels.ts",
}


def herramienta() -> ModuleType:
    return importar_o_fallar("veridicus_contracts.tools.gen_ts", "U01-T19")


def test_genera_exactamente_los_cuatro_archivos(contracts_root: Path) -> None:
    generados = herramienta().generar(contracts_root)
    assert set(generados) == NOMBRES


def test_lo_generado_es_igual_a_lo_versionado(contracts_root: Path) -> None:
    generados = herramienta().generar(contracts_root)
    carpeta = ruta_de(CARPETA)
    for nombre, contenido in generados.items():
        archivo = carpeta / nombre
        if not archivo.is_file():
            pytest.fail(f"archivo generado ausente: {CARPETA}/{nombre}")
        assert archivo.read_bytes() == contenido, f"{nombre} difiere de la generación"


def test_dos_generaciones_seguidas_dan_bytes_identicos(contracts_root: Path) -> None:
    herramientas = herramienta()
    assert herramientas.generar(contracts_root) == herramientas.generar(contracts_root)


def test_la_salida_es_lf_utf8_sin_bom_y_declara_que_esta_generada(contracts_root: Path) -> None:
    for nombre, contenido in herramienta().generar(contracts_root).items():
        assert b"\r" not in contenido, nombre
        assert contenido.endswith(b"\n"), nombre
        assert not contenido.startswith(b"\xef\xbb\xbf"), nombre
        texto = contenido.decode("utf-8")
        assert "as const" in texto, nombre
        assert "no editar" in texto.splitlines()[0].lower(), nombre


def test_las_constantes_traen_el_contenido_de_sus_fuentes(contracts_root: Path) -> None:
    generados = {n: c.decode("utf-8") for n, c in herramienta().generar(contracts_root).items()}
    for codigo in load_contract("errors/error-codes.v2.yaml")["codes"]:
        assert json.dumps(codigo) in generados["error-codes.ts"]
    for clave, rotulo in load_contract("ui/result-labels.v2.yaml")["labels"].items():
        assert json.dumps(clave) in generados["result-labels.ts"]
        assert json.dumps(rotulo, ensure_ascii=False) in generados["result-labels.ts"]
    for termino in load_contract("integrity/forbidden-vocabulary.v2.yaml")["terms"]:
        assert json.dumps(termino, ensure_ascii=False) in generados["forbidden-vocabulary.ts"]
    superficie = generados["auth-surface.ts"]
    for rol in auth_surface.ROLES:
        assert json.dumps(rol) in superficie
    for identificador in auth_surface.ENCOLAN:
        assert json.dumps(identificador) in superficie
    for extension in auth_surface.EXTENSIONES:
        assert json.dumps(extension) in superficie
    for metodo, ruta in auth_surface.PUBLICAS:
        assert json.dumps(ruta) in superficie
        assert json.dumps(metodo) in superficie


def _bloque(texto: str, nombre: str) -> str:
    """El cuerpo de `export const <nombre> = ...;` hasta el cierre `as const`."""
    inicio = texto.index(f"export const {nombre}")
    return texto[inicio : texto.index("as const", inicio)]


def _enteros(bloque: str) -> list[int]:
    """Los enteros de un bloque, en decimal o en hexadecimal `0x…`, en el orden en que aparecen."""
    cuerpo = bloque.split("=", 1)[1]
    return [int(numero, 0) for numero in re.findall(r"0[xX][0-9A-Fa-f]+|[0-9]+", cuerpo)]


def test_el_plegado_de_c8_se_exporta_a_typescript(contracts_root: Path) -> None:
    """Caso sonda 9 (K-89): la consola (U8) lee el plegado de aquí y no lo tiene escrito en su código."""
    fold = load_contract("integrity/forbidden-vocabulary.v2.yaml")["match"]["fold"]
    texto = herramienta().generar(contracts_root)["forbidden-vocabulary.ts"].decode("utf-8")

    assert re.search(r'export const FOLD_NORMALIZATION\s*=\s*"NFKD"\s*as const', texto)
    categorias = _bloque(texto, "FOLD_DROPPED_CATEGORIES")
    assert re.findall(r'"([A-Z][a-z])"', categorias) == fold["dropped_categories"]
    rangos = _enteros(_bloque(texto, "FOLD_DROPPED_CODE_POINTS"))
    assert rangos == [punto for rango in fold["dropped_code_points"] for punto in rango]
    assert len(rangos) == 2 * 17


def test_el_typescript_versionado_trae_el_plegado() -> None:
    """La deriva: el archivo que se publica, no solo lo que la herramienta generaría."""
    texto = (ruta_de(CARPETA) / "forbidden-vocabulary.ts").read_text(encoding="utf-8")
    assert "FOLD_NORMALIZATION" in texto
    assert "FOLD_DROPPED_CODE_POINTS" in texto


def test_check_sale_con_uno_si_un_archivo_cambia_o_falta(
    contracts_root: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    herramientas = herramienta()
    copia = tmp_path / "generated"
    shutil.copytree(ruta_de(CARPETA), copia)
    assert herramientas.main(["--check", "--output-dir", str(copia)]) == 0
    capsys.readouterr()
    archivo = copia / "error-codes.ts"
    archivo.write_bytes(archivo.read_bytes() + b"// sobrante\n")
    assert herramientas.main(["--check", "--output-dir", str(copia)]) == 1
    assert "error-codes.ts" in capsys.readouterr().out
    archivo.unlink()
    assert herramientas.main(["--check", "--output-dir", str(copia)]) == 1
    assert "error-codes.ts" in capsys.readouterr().out


def test_sin_check_escribe_y_crea_la_carpeta_si_falta(tmp_path: Path) -> None:
    herramientas = herramienta()
    destino = tmp_path / "nueva" / "generated"
    assert herramientas.main(["--check", "--output-dir", str(destino)]) == 1
    assert not destino.exists()
    assert herramientas.main(["--output-dir", str(destino)]) == 0
    assert {a.name for a in destino.iterdir()} == NOMBRES
    assert herramientas.main(["--check", "--output-dir", str(destino)]) == 0


def test_los_archivos_ajenos_de_la_carpeta_no_se_tocan_ni_rompen_el_check(
    tmp_path: Path,
) -> None:
    herramientas = herramienta()
    destino = tmp_path / "generated"
    destino.mkdir()
    ajeno = destino / "console.d.ts"
    ajeno.write_bytes(b"// tipos de openapi-typescript\n")
    assert herramientas.main(["--output-dir", str(destino)]) == 0
    assert ajeno.read_bytes() == b"// tipos de openapi-typescript\n"
    assert herramientas.main(["--check", "--output-dir", str(destino)]) == 0
