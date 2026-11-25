"""Mapa de rutas de la rueda (PD-9, D1, D15), leído de vuelta: CA-8."""

import importlib
import importlib.resources
import shutil
import subprocess
import sys
import tomllib
import zipfile
from pathlib import Path

import pytest

# Directorios de datos del mapa de functional-spec §1 que ya existen en el esqueleto.
# `limits.v1.yaml` (archivo suelto) lo añade la tarea T10 a include y sources.
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
    "vendor",
)

# Archivos sueltos de la raíz de contracts/ que entran como datos (F-12 de U01-T01, T10),
# por `force-include` de la rueda y por el hook de la instalación editable.
ARCHIVOS_DE_DATOS = ("limits.v1.yaml",)

# Directorios de la raíz de contracts/ que no se empaquetan como datos.
NO_EMPAQUETADOS = {"src", "tests", "ts", "fixtures", "build", "dist"}

IGNORAR_EN_COPIA = shutil.ignore_patterns(
    ".venv", "__pycache__", ".*_cache", ".coverage", ".hypothesis", "build", "dist", "node_modules"
)


def _copiar(contracts_root: Path, destino: Path) -> Path:
    copia = destino / "contracts"
    shutil.copytree(contracts_root, copia, symlinks=True, ignore=IGNORAR_EN_COPIA)
    return copia


def _uv() -> str:
    uv = shutil.which("uv")
    assert uv is not None, "uv no está en PATH"
    return uv


def test_inventario_del_mapa_coincide_con_el_arbol_y_con_pyproject(contracts_root: Path) -> None:
    assert not (contracts_root / "python").exists(), "PD-9: contracts/python/ ya no existe"
    configuracion = tomllib.loads((contracts_root / "pyproject.toml").read_text(encoding="utf-8"))
    rueda = configuracion["tool"]["hatch"]["build"]["targets"]["wheel"]
    en_arbol = {
        d.name
        for d in contracts_root.iterdir()
        if d.is_dir() and not d.name.startswith((".", "_")) and d.name not in NO_EMPAQUETADOS
    }
    assert en_arbol == set(DIRECTORIOS_DE_DATOS), "directorio nuevo sin registrar en el inventario"
    incluidos = {i.removeprefix("/") for i in rueda["include"]}
    assert incluidos == {"src/veridicus_contracts", *DIRECTORIOS_DE_DATOS}
    mapa = {k: v for k, v in rueda["sources"].items() if k != "src"}
    assert mapa == {n: f"veridicus_contracts/{n}" for n in DIRECTORIOS_DE_DATOS}
    # Un archivo suelto no puede ir en include/sources (sources solo reasigna directorios y
    # include lo duplicaría en la raíz de la rueda): va en force-include.
    assert rueda["force-include"] == {n: f"veridicus_contracts/{n}" for n in ARCHIVOS_DE_DATOS}
    for archivo in ARCHIVOS_DE_DATOS:
        assert (contracts_root / archivo).is_file(), archivo
    assert rueda["sources"]["src"] == ""
    # F-11: la copia editable se refresca por cache-keys; cada directorio necesita el suyo.
    claves = {
        k["file"].removesuffix("/**")
        for k in configuracion["tool"]["uv"]["cache-keys"]
        if k["file"].endswith("/**")
    }
    assert claves == set(DIRECTORIOS_DE_DATOS), "cache-keys no coincide con el inventario"
    sueltas = {
        k["file"]
        for k in configuracion["tool"]["uv"]["cache-keys"]
        if not k["file"].endswith("/**")
    }
    assert sueltas == {"pyproject.toml", "hatch_build.py", *ARCHIVOS_DE_DATOS}


def test_los_subpaquetes_del_esqueleto_se_importan_con_su_nombre_de_paquete() -> None:
    for nombre in ("checks", "tools"):
        modulo = importlib.import_module(f"veridicus_contracts.{nombre}")
        assert modulo.__name__ == f"veridicus_contracts.{nombre}"
        assert (Path(str(modulo.__file__)).parent.parent / "py.typed").is_file()


def test_datos_visibles_con_importlib_resources_en_la_instalacion_editable() -> None:
    raiz = importlib.resources.files("veridicus_contracts")
    for nombre in DIRECTORIOS_DE_DATOS:
        assert (raiz / nombre).is_dir(), nombre


def test_archivos_sueltos_visibles_con_importlib_resources_en_la_instalacion_editable(
    contracts_root: Path,
) -> None:
    raiz = importlib.resources.files("veridicus_contracts")
    for nombre in ARCHIVOS_DE_DATOS:
        leido = (raiz / nombre).read_text(encoding="utf-8")
        assert leido == (contracts_root / nombre).read_text(encoding="utf-8"), nombre


def _construir(contracts_root: Path, tmp_path: Path, argumentos: list[str]) -> set[str]:
    """Construye sobre una copia con un fixture temporal y devuelve las rutas de la rueda."""
    copia = _copiar(contracts_root, tmp_path)
    (copia / "api" / "fixtures").mkdir(parents=True, exist_ok=True)
    (copia / "api" / "fixtures" / "sintetico.yaml").write_text("dato: sintetico\n")
    salida = tmp_path / "salida"
    resultado = subprocess.run(  # noqa: S603  # motivo: argumentos fijos, sin entrada externa
        [
            _uv(),
            "build",
            *argumentos,
            "--offline",
            "--directory",
            str(copia),
            "--out-dir",
            str(salida),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert resultado.returncode == 0, resultado.stderr
    with zipfile.ZipFile(next(salida.glob("*.whl"))) as zf:
        return set(zf.namelist())


@pytest.mark.parametrize("argumentos", [["--wheel"], []], ids=["wheel-directa", "sdist-y-rueda"])
def test_la_rueda_trae_el_mapa_completo_y_sin_fixtures(
    contracts_root: Path, tmp_path: Path, argumentos: list[str]
) -> None:
    nombres = _construir(contracts_root, tmp_path, argumentos)
    assert not [n for n in nombres if "/fixtures/" in n], nombres
    assert "veridicus_contracts/py.typed" in nombres
    for directorio in DIRECTORIOS_DE_DATOS:
        assert any(n.startswith(f"veridicus_contracts/{directorio}/") for n in nombres), (
            directorio,
            sorted(nombres),
        )
    for archivo in ARCHIVOS_DE_DATOS:
        assert f"veridicus_contracts/{archivo}" in nombres, (archivo, sorted(nombres))
        assert archivo not in nombres, f"{archivo} duplicado en la raíz de la rueda"


def test_las_dos_vias_de_construccion_dan_la_misma_rueda(
    contracts_root: Path, tmp_path: Path
) -> None:
    directa = _construir(contracts_root, tmp_path / "a", ["--wheel"])
    por_sdist = _construir(contracts_root, tmp_path / "b", [])
    assert directa == por_sdist


def test_mypy_estricto_resuelve_una_importacion_cruzada(
    contracts_root: Path, tmp_path: Path
) -> None:
    copia = _copiar(contracts_root, tmp_path)
    paquete = copia / "src" / "veridicus_contracts"
    (paquete / "uno.py").write_text("def valor() -> int:\n    return 1\n")
    (paquete / "dos.py").write_text(
        "from veridicus_contracts.uno import valor\n\n\ndef doble() -> int:\n    return 2 * valor()\n"
    )
    resultado = subprocess.run(
        [sys.executable, "-m", "mypy", "--strict", "src"],
        cwd=copia,
        capture_output=True,
        text=True,
        check=False,
    )
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr
    assert "Success: no issues found" in resultado.stdout
