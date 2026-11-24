"""`check_package`: el paso del paquete en entorno limpio (F9, §4.16, BR12.1, BR12.3, NFR2.2).

Las piezas puras se prueban con datos sintéticos, sin red y sin construir. La única prueba que
construye es `test_rueda_contaminada_...` (CA-3): `uv build --offline` sobre una copia, sin instalar.
La corrida completa (construir, crear el entorno, instalar) es el criterio CA-2, fuera de la suite.
"""

import json
import shutil
import sys
import tomllib
from pathlib import Path
from typing import Any

import pytest
from helpers import importar_o_fallar
from test_package_map import ARCHIVOS_DE_DATOS, DIRECTORIOS_DE_DATOS

MODULO = "veridicus_contracts.tools.check_package"


def _herramienta() -> Any:
    return importar_o_fallar(MODULO, "T21, paso 22")


def _tabla() -> Any:
    herramienta = _herramienta()
    return herramienta.TablaDeRutas(
        directorios=tuple(DIRECTORIOS_DE_DATOS), archivos=tuple(ARCHIVOS_DE_DATOS)
    )


def _rueda_completa() -> list[str]:
    """Lista de una rueda sintética con el mapa completo, sin nada prohibido."""
    nombres = [
        "veridicus_contracts/py.typed",
        "veridicus_contracts/registry.py",
        "veridicus_contracts-0.1.0.dist-info/METADATA",
    ]
    nombres += [f"veridicus_contracts/{d}/dato.v1.yaml" for d in DIRECTORIOS_DE_DATOS]
    nombres += [f"veridicus_contracts/{a}" for a in ARCHIVOS_DE_DATOS]
    return nombres


def test_una_lista_de_rueda_completa_pasa() -> None:
    herramienta = _herramienta()
    assert herramienta.comparar_rueda(_rueda_completa(), _tabla()) == []


@pytest.mark.parametrize(
    "ausente",
    [f"veridicus_contracts/{d}/" for d in ("analyzer", "cli", "vendor")]
    + ["veridicus_contracts/limits.v1.yaml"],
)
def test_una_lista_sin_un_dato_de_la_tabla_falla_y_nombra_la_ruta(ausente: str) -> None:
    herramienta = _herramienta()
    nombres = [n for n in _rueda_completa() if not n.startswith(ausente)]
    assert len(nombres) < len(_rueda_completa())
    problemas = herramienta.comparar_rueda(nombres, _tabla())
    assert len(problemas) == 1, problemas
    assert ausente.rstrip("/") in problemas[0]
    assert "falta" in problemas[0]


@pytest.mark.parametrize(
    "intrusa",
    [
        "veridicus_contracts/api/fixtures/sintetico.yaml",
        "veridicus_contracts/tests/test_algo.py",
        "veridicus_contracts/.env",
        "veridicus_contracts/.env.local",
        "veridicus_contracts/clave.pem",
        "veridicus_contracts/privada.key",
    ],
)
def test_una_lista_con_una_ruta_prohibida_falla_y_nombra_la_ruta(intrusa: str) -> None:
    herramienta = _herramienta()
    problemas = herramienta.comparar_rueda([*_rueda_completa(), intrusa], _tabla())
    assert len(problemas) == 1, problemas
    assert intrusa in problemas[0]
    assert "prohibida" in problemas[0]


def test_la_tabla_derivada_de_pyproject_coincide_con_la_de_test_package_map(
    contracts_root: Path,
) -> None:
    herramienta = _herramienta()
    configuracion = tomllib.loads((contracts_root / "pyproject.toml").read_text(encoding="utf-8"))
    tabla = herramienta.tabla_de_rutas(configuracion)
    assert set(tabla.directorios) == set(DIRECTORIOS_DE_DATOS)
    assert set(tabla.archivos) == set(ARCHIVOS_DE_DATOS)


def test_el_guion_en_el_entorno_de_la_suite_valida_los_fixtures_y_rechaza_la_forma_antigua(
    contracts_root: Path,
) -> None:
    herramienta = _herramienta()
    argumentos = [json.dumps(_tabla()._asdict()), str(contracts_root)]
    resultado = herramienta.ejecutar_guion(sys.executable, herramienta.GUION, argumentos)
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr
    salida = resultado.stdout
    for contrato in ("C7", "C1", "C19"):
        assert f"{contrato}: " in salida, salida
    assert "forma antigua" in salida
    assert "socket bloqueado" in salida


def test_un_guion_que_abre_un_socket_falla_con_el_error_del_bloqueo() -> None:
    herramienta = _herramienta()
    guion = "import socket\nsocket.socket(socket.AF_INET, socket.SOCK_STREAM)\nprint('llego')\n"
    resultado = herramienta.ejecutar_guion(sys.executable, guion, [])
    assert resultado.returncode != 0
    assert herramienta.MENSAJE_SOCKET in resultado.stderr
    assert "llego" not in resultado.stdout


def test_rueda_contaminada_con_un_fixture_forzado_falla_y_nombra_la_ruta(
    contracts_root: Path, tmp_path: Path
) -> None:
    herramienta = _herramienta()
    copia = tmp_path / "contracts"
    shutil.copytree(
        contracts_root,
        copia,
        symlinks=True,
        ignore=shutil.ignore_patterns(
            ".venv", "__pycache__", ".*_cache", ".coverage", ".hypothesis", "build", "dist",
            "node_modules",
        ),
    )
    intruso = "api/fixtures/sintetico.yaml"
    (copia / "api" / "fixtures").mkdir(parents=True, exist_ok=True)
    (copia / intruso).write_text("dato: sintetico\n", encoding="utf-8")
    pyproject = copia / "pyproject.toml"
    texto = pyproject.read_text(encoding="utf-8")
    ancla = "[tool.hatch.build.targets.wheel.force-include]\n"
    assert ancla in texto
    pyproject.write_text(
        texto.replace(ancla, ancla + f'"{intruso}" = "veridicus_contracts/{intruso}"\n'),
        encoding="utf-8",
    )
    tabla = herramienta.tabla_de_rutas(tomllib.loads(texto))
    rueda = herramienta.construir(copia, tmp_path / "salida", offline=True, solo_rueda=True)
    nombres = herramienta.nombres_de_rueda(rueda)
    assert f"veridicus_contracts/{intruso}" in nombres
    problemas = herramienta.comparar_rueda(nombres, tabla)
    assert len(problemas) == 1, problemas
    assert f"veridicus_contracts/{intruso}" in problemas[0]
