"""Compuerta de `pip-audit` (§4.13 paso 3, NFRD-U1-11, U01-T19).

Los informes de `pip-audit` son sintéticos y se escriben en `tmp_path`; nunca se corre `pip-audit`
(la suite no tiene red).
"""

import json
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from helpers import importar_o_fallar, ruta_de

VIGENTE = "2099-12-31"
VENCIDA = "2000-01-01"


def herramienta() -> ModuleType:
    return importar_o_fallar("veridicus_contracts.tools.audit_gate", "U01-T19")


def informe(tmp_path: Path, vulns: list[dict[str, Any]]) -> Path:
    dependencias = [{"name": "paquete-sintetico", "version": "1.0.0", "vulns": vulns}]
    ruta = tmp_path / "pip-audit.json"
    ruta.write_text(json.dumps({"dependencies": dependencias, "fixes": []}), encoding="utf-8")
    return ruta


def excepciones(tmp_path: Path, texto: str) -> Path:
    ruta = tmp_path / "ignore.yaml"
    ruta.write_text(texto, encoding="utf-8")
    return ruta


VACIA = "excepciones: []\n"
VULN_CON_CORRECCION = {
    "id": "PYSEC-0000-0001",
    "fix_versions": ["1.0.1"],
    "aliases": ["CVE-0000-0001"],
    "description": "texto que no debe salir",
}
VULN_SIN_CORRECCION = {"id": "PYSEC-0000-0002", "fix_versions": [], "aliases": []}


def ejecutar(
    capsys: pytest.CaptureFixture[str], tmp_path: Path, vulns: list[dict[str, Any]], texto: str = VACIA
) -> tuple[int, str]:
    herramientas = herramienta()
    codigo = herramientas.main(
        [str(informe(tmp_path, vulns)), "--ignore", str(excepciones(tmp_path, texto))]
    )
    capturado = capsys.readouterr()
    return codigo, capturado.out + capturado.err


def test_sin_vulnerabilidades_es_verde(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    codigo, _ = ejecutar(capsys, tmp_path, [])
    assert codigo == 0


def test_una_vulnerabilidad_con_correccion_es_roja_y_nombra_paquete_e_id_sin_descripcion(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    codigo, salida = ejecutar(capsys, tmp_path, [VULN_CON_CORRECCION])
    assert codigo == 1
    assert "paquete-sintetico" in salida
    assert "PYSEC-0000-0001" in salida
    assert "texto que no debe salir" not in salida


def test_una_vulnerabilidad_sin_correccion_es_verde(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    codigo, _ = ejecutar(capsys, tmp_path, [VULN_SIN_CORRECCION])
    assert codigo == 0


def test_una_excepcion_vigente_deja_pasar_la_vulnerabilidad_por_id_o_por_alias(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    for identificador in ("PYSEC-0000-0001", "CVE-0000-0001"):
        texto = (
            f"excepciones:\n  - id: {identificador}\n    motivo: sintetico\n"
            f"    caduca: '{VIGENTE}'\n"
        )
        codigo, _ = ejecutar(capsys, tmp_path, [VULN_CON_CORRECCION], texto)
        assert codigo == 0, identificador


def test_una_excepcion_vencida_es_roja_aunque_no_haya_vulnerabilidades(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    texto = f"excepciones:\n  - id: PYSEC-0000-0001\n    motivo: sintetico\n    caduca: '{VENCIDA}'\n"
    codigo, salida = ejecutar(capsys, tmp_path, [VULN_CON_CORRECCION], texto)
    assert codigo == 1
    assert "PYSEC-0000-0001" in salida
    assert "venci" in salida
    codigo, _ = ejecutar(capsys, tmp_path, [], texto)
    assert codigo == 1


@pytest.mark.parametrize(
    "texto",
    [
        "excepciones:\n  - id: PYSEC-0000-0001\n    motivo: m\n    caduca: '2099-12-31'\n    extra: x\n",
        "excepciones:\n  - id: PYSEC-0000-0001\n    motivo: m\n",
        "excepciones:\n  - motivo: m\n    caduca: '2099-12-31'\n",
        "excepciones:\n  - id: PYSEC-0000-0001\n    caduca: '2099-12-31'\n",
        "excepciones:\n  - id: PYSEC-0000-0001\n    motivo: m\n    caduca: '31/12/2099'\n",
        "excepciones:\n  - id: PYSEC-0000-0001\n    motivo: m\n    caduca: '2099-02-30'\n",
        "excepciones:\n  - id: PYSEC-0000-0001\n    motivo: ''\n    caduca: '2099-12-31'\n",
        "excepciones:\n  - algo\n",
        "excepciones: {}\n",
        "otra_clave: []\nexcepciones: []\n",
        "- id: x\n",
    ],
    ids=[
        "clave-desconocida",
        "sin-caduca",
        "sin-id",
        "sin-motivo",
        "fecha-mal-escrita",
        "fecha-imposible",
        "motivo-vacio",
        "elemento-no-objeto",
        "excepciones-no-lista",
        "clave-raiz-desconocida",
        "raiz-no-objeto",
    ],
)
def test_una_excepcion_mal_formada_es_roja(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], texto: str
) -> None:
    codigo, _ = ejecutar(capsys, tmp_path, [], texto)
    assert codigo == 1


def test_la_lista_real_de_excepciones_se_lee_de_vuelta_y_el_informe_vacio_es_verde(
    capsys: pytest.CaptureFixture[str],
) -> None:
    herramientas = herramienta()
    vacio = ruta_de("tests/data/pip-audit-vacio.json")
    ignorar = ruta_de(".pip-audit-ignore.yaml")
    assert herramientas.main([str(vacio), "--ignore", str(ignorar)]) == 0
    assert herramientas.cargar_excepciones(ignorar) == []
    capsys.readouterr()


def test_un_informe_o_una_lista_ilegible_sale_con_dos(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    herramientas = herramienta()
    ignorar = excepciones(tmp_path, VACIA)
    assert herramientas.main([str(tmp_path / "ausente.json"), "--ignore", str(ignorar)]) == 2
    roto = tmp_path / "roto.json"
    roto.write_text("{no es json", encoding="utf-8")
    assert herramientas.main([str(roto), "--ignore", str(ignorar)]) == 2
    forma = tmp_path / "forma.json"
    forma.write_text(json.dumps({"dependencies": "no"}), encoding="utf-8")
    assert herramientas.main([str(forma), "--ignore", str(ignorar)]) == 2
    base = informe(tmp_path, [])
    assert herramientas.main([str(base), "--ignore", str(tmp_path / "ausente.yaml")]) == 2
    capsys.readouterr()


def test_crea_build_si_es_la_carpeta_del_informe_y_no_existe(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    herramientas = herramienta()
    ignorar = excepciones(tmp_path, VACIA)
    build = tmp_path / "build"
    assert not build.exists()
    assert herramientas.main([str(build / "pip-audit.json"), "--ignore", str(ignorar)]) == 2
    assert build.is_dir()
    otra = tmp_path / "otra"
    assert herramientas.main([str(otra / "pip-audit.json"), "--ignore", str(ignorar)]) == 2
    assert not otra.exists()
    capsys.readouterr()
