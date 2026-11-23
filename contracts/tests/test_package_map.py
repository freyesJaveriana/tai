"""Mapa de rutas de functional-spec §1 (D1, D15), leído de vuelta (F-01, F-02, F-05 a F-07)."""

import importlib
import importlib.resources
import shutil
import subprocess
import tomllib
import zipfile
from pathlib import Path

import pytest

# Directorios de datos del mapa de functional-spec §1 que ya existen en el esqueleto.
# limits.v1.yaml lo añade T10 junto con su enlace.
DIRECTORIOS_DE_DATOS = (
    "analyzer",
    "api",
    "cli",
    "errors",
    "format",
    "health",
    "integrity",
    "metrics",
    "model_calls",
    "profiles",
    "queues",
    "transcript",
    "ui",
)


# Directorios de la raíz de contracts/ que no se empaquetan como datos.
NO_EMPAQUETADOS = {"src", "python", "tests", "ts", "vendor", "fixtures", "build", "dist"}


def test_inventario_del_mapa_coincide_con_el_arbol_y_con_pyproject(contracts_root: Path) -> None:
    configuracion = tomllib.loads((contracts_root / "pyproject.toml").read_text(encoding="utf-8"))
    rueda = configuracion["tool"]["hatch"]["build"]["targets"]["wheel"]
    en_arbol = {
        d.name
        for d in contracts_root.iterdir()
        if d.is_dir() and not d.name.startswith(".") and d.name not in NO_EMPAQUETADOS
    }
    assert en_arbol == set(DIRECTORIOS_DE_DATOS), "directorio nuevo sin registrar en el inventario"
    incluidos = {i.removeprefix("/") for i in rueda["include"]}
    assert set(DIRECTORIOS_DE_DATOS) <= incluidos
    for nombre in DIRECTORIOS_DE_DATOS:
        assert rueda["sources"][nombre] == f"veridicus_contracts/{nombre}", nombre
    for modulo in (contracts_root / "python").glob("*.py"):
        assert modulo.is_file()
    assert rueda["sources"]["python"] == "veridicus_contracts"


def test_modulo_de_python_se_importa_en_la_raiz_del_paquete() -> None:
    modulo = importlib.import_module("veridicus_contracts._skeleton")
    assert modulo.__name__ == "veridicus_contracts._skeleton"


def test_directorio_de_datos_se_encuentra_con_importlib_resources() -> None:
    raiz = importlib.resources.files("veridicus_contracts")
    for nombre in DIRECTORIOS_DE_DATOS:
        assert (raiz / nombre).is_dir(), nombre


def _construir(contracts_root: Path, tmp_path: Path, argumentos: list[str]) -> set[str]:
    """Construye sobre una copia que conserva los enlaces y devuelve las rutas de la rueda."""
    copia = tmp_path / "contracts"
    shutil.copytree(
        contracts_root,
        copia,
        symlinks=True,
        ignore=shutil.ignore_patterns(".venv", "__pycache__", ".*_cache", "build", "dist"),
    )
    (copia / "api" / "fixtures").mkdir(parents=True, exist_ok=True)
    (copia / "api" / "fixtures" / "sintetico.yaml").write_text("dato: sintetico\n")
    salida = tmp_path / "salida"
    uv = shutil.which("uv")
    assert uv is not None, "uv no está en PATH"
    resultado = subprocess.run(  # noqa: S603  # motivo: argumentos fijos, sin entrada externa
        [uv, "build", *argumentos, "--offline", "--directory", str(copia), "--out-dir", str(salida)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert resultado.returncode == 0, resultado.stderr
    rueda = next(salida.glob("*.whl"))
    with zipfile.ZipFile(rueda) as zf:
        return set(zf.namelist())


@pytest.mark.parametrize("argumentos", [["--wheel"], []], ids=["wheel-directa", "sdist-y-rueda"])
def test_la_rueda_trae_el_mapa_completo_y_sin_fixtures(
    contracts_root: Path, tmp_path: Path, argumentos: list[str]
) -> None:
    nombres = _construir(contracts_root, tmp_path, argumentos)
    assert not [n for n in nombres if "/fixtures/" in n], nombres
    assert "veridicus_contracts/_skeleton.py" in nombres
    for directorio in DIRECTORIOS_DE_DATOS:
        assert any(n.startswith(f"veridicus_contracts/{directorio}/") for n in nombres), (
            directorio,
            sorted(nombres),
        )


def test_las_dos_vias_de_construccion_dan_la_misma_rueda(
    contracts_root: Path, tmp_path: Path
) -> None:
    directa = _construir(contracts_root, tmp_path / "a", ["--wheel"])
    por_sdist = _construir(contracts_root, tmp_path / "b", [])
    assert directa == por_sdist
