"""Mapa de rutas de functional-spec §1 (D1, D15), leído de vuelta (F-01, F-02)."""

import importlib
import importlib.resources
import shutil
import subprocess
import zipfile
from pathlib import Path


def test_modulo_de_python_se_importa_en_la_raiz_del_paquete() -> None:
    modulo = importlib.import_module("veridicus_contracts._skeleton")
    assert modulo.__name__ == "veridicus_contracts._skeleton"


def test_directorio_de_datos_se_encuentra_con_importlib_resources() -> None:
    raiz = importlib.resources.files("veridicus_contracts")
    for nombre in ("api", "analyzer", "queues", "profiles"):
        assert (raiz / nombre).is_dir(), nombre


def test_fixtures_no_entran_en_la_rueda(contracts_root: Path, tmp_path: Path) -> None:
    copia = tmp_path / "contracts"
    shutil.copytree(
        contracts_root,
        copia,
        ignore=shutil.ignore_patterns(".venv", "__pycache__", ".*_cache", "build", "dist"),
    )
    (copia / "api" / "fixtures").mkdir(parents=True, exist_ok=True)
    (copia / "api" / "fixtures" / "sintetico.yaml").write_text("dato: sintetico\n")
    salida = tmp_path / "rueda"
    uv = shutil.which("uv")
    assert uv is not None, "uv no está en PATH"
    resultado = subprocess.run(  # noqa: S603  # motivo: argumentos fijos, sin entrada externa
        [uv, "build", "--wheel", "--offline", "--directory", str(copia), "--out-dir", str(salida)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert resultado.returncode == 0, resultado.stderr
    rueda = next(salida.glob("*.whl"))
    with zipfile.ZipFile(rueda) as zf:
        nombres = zf.namelist()
    assert not [n for n in nombres if "/fixtures/" in n], nombres
    assert "veridicus_contracts/_skeleton.py" in nombres
    assert any(n.startswith("veridicus_contracts/api/") for n in nombres)
