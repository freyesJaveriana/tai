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


def _tabla(contracts_root: Path) -> Any:
    """La tabla real: pyproject.toml más cada archivo del árbol de origen (F-01)."""
    herramienta = _herramienta()
    configuracion = tomllib.loads((contracts_root / "pyproject.toml").read_text(encoding="utf-8"))
    return herramienta.tabla_de_rutas(configuracion, contracts_root)


def _rueda_completa(tabla: Any) -> list[str]:
    """Lista de una rueda sintética con el mapa completo, como la real: con `.gitkeep`."""
    nombres = [
        "veridicus_contracts/py.typed",
        "veridicus_contracts/registry.py",
        "veridicus_contracts-0.1.0.dist-info/METADATA",
    ]
    nombres += [f"veridicus_contracts/{d}/.gitkeep" for d in tabla.directorios]
    nombres += [f"veridicus_contracts/{d}" for d in (*tabla.datos, *tabla.archivos)]
    return nombres


def test_una_lista_de_rueda_completa_pasa(contracts_root: Path) -> None:
    herramienta = _herramienta()
    tabla = _tabla(contracts_root)
    assert herramienta.comparar_rueda(_rueda_completa(tabla), tabla) == []


@pytest.mark.parametrize(
    "ausente",
    [
        "veridicus_contracts/analyzer/v1/entrada.schema.json",
        "veridicus_contracts/errors/error-codes.v2.yaml",
        "veridicus_contracts/queues/runs.v2.yaml",
        "veridicus_contracts/queues/results.v2.yaml",
        "veridicus_contracts/ui/result-labels.v2.yaml",
        "veridicus_contracts/limits.v1.yaml",
    ],
)
def test_una_lista_sin_un_solo_catalogo_falla_y_nombra_la_ruta(
    contracts_root: Path, ausente: str
) -> None:
    """Quitar un archivo de un directorio con más de uno (y con `.gitkeep`) no pasa (F-01)."""
    herramienta = _herramienta()
    tabla = _tabla(contracts_root)
    nombres = [n for n in _rueda_completa(tabla) if n != ausente]
    assert len(nombres) == len(_rueda_completa(tabla)) - 1
    problemas = herramienta.comparar_rueda(nombres, tabla)
    assert len(problemas) == 1, problemas
    assert ausente in problemas[0]
    assert "falta" in problemas[0]


def test_solo_transcript_se_acepta_con_solo_gitkeep_y_hace_falta_su_gitkeep(
    contracts_root: Path,
) -> None:
    herramienta = _herramienta()
    tabla = _tabla(contracts_root)
    assert tabla.reservados == ("transcript",)
    assert herramienta.DIRECTORIOS_RESERVADOS.keys() == {"transcript"}
    with pytest.raises(TypeError):  # F-07: la lista cerrada es inmutable
        herramienta.DIRECTORIOS_RESERVADOS["otro"] = "no se admite"
    sin_gitkeep = [
        n for n in _rueda_completa(tabla) if n != "veridicus_contracts/transcript/.gitkeep"
    ]
    problemas = herramienta.comparar_rueda(sin_gitkeep, tabla)
    assert len(problemas) == 1, problemas
    assert "veridicus_contracts/transcript" in problemas[0]
    # Sin la excepción nombrada, un directorio sin datos es un fallo: no hay regla general.
    sin_reserva = herramienta.TablaDeRutas(
        tabla.directorios, tabla.archivos, tabla.datos, reservados=()
    )
    problemas = herramienta.comparar_rueda(_rueda_completa(tabla), sin_reserva)
    assert len(problemas) == 1, problemas
    assert "veridicus_contracts/transcript" in problemas[0]
    assert "no es reservado" in problemas[0]


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
def test_una_lista_con_una_ruta_prohibida_falla_y_nombra_la_ruta(
    contracts_root: Path, intrusa: str
) -> None:
    herramienta = _herramienta()
    tabla = _tabla(contracts_root)
    problemas = herramienta.comparar_rueda([*_rueda_completa(tabla), intrusa], tabla)
    assert len(problemas) == 1, problemas
    assert intrusa in problemas[0]
    assert "prohibida" in problemas[0]


def test_la_tabla_derivada_de_pyproject_coincide_con_la_de_test_package_map(
    contracts_root: Path,
) -> None:
    tabla = _tabla(contracts_root)
    assert set(tabla.directorios) == set(DIRECTORIOS_DE_DATOS)
    assert set(tabla.archivos) == set(ARCHIVOS_DE_DATOS)
    assert "errors/error-codes.v2.yaml" in tabla.datos
    assert not [d for d in tabla.datos if "fixtures" in d.split("/") or d.endswith(".gitkeep")]
    assert {d.split("/")[0] for d in tabla.datos} == set(DIRECTORIOS_DE_DATOS) - {"transcript"}


def test_el_guion_en_el_entorno_de_la_suite_valida_los_fixtures_y_rechaza_la_forma_antigua(
    contracts_root: Path,
) -> None:
    herramienta = _herramienta()
    argumentos = [json.dumps(_tabla(contracts_root)._asdict()), str(contracts_root)]
    resultado = herramienta.ejecutar_guion(sys.executable, herramienta.GUION, argumentos)
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr
    salida = resultado.stdout
    for rotulo in ("C7", "C1 (ReviewSuggestion, fixtures de C7)", "C19"):
        assert f"{rotulo}: " in salida, salida
    assert "forma antigua" in salida
    assert "socket bloqueado" in salida
    assert "archivo por archivo" in salida


def test_el_guion_falla_ante_un_dato_ausente_y_ante_un_socket_abierto(
    contracts_root: Path,
) -> None:
    herramienta = _herramienta()
    tabla = _tabla(contracts_root)._asdict()
    tabla["datos"] = [*tabla["datos"], "errors/no-existe.v9.yaml"]
    ausente = herramienta.ejecutar_guion(
        sys.executable, herramienta.GUION, [json.dumps(tabla), str(contracts_root)]
    )
    assert ausente.returncode != 0
    assert "errors/no-existe.v9.yaml" in ausente.stderr
    guion = "import socket\nsocket.socket(socket.AF_INET, socket.SOCK_STREAM)\nprint('llego')\n"
    socket = herramienta.ejecutar_guion(sys.executable, guion, [])
    assert socket.returncode != 0
    assert herramienta.MENSAJE_SOCKET in socket.stderr
    assert "llego" not in socket.stdout


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
            ".venv",
            "__pycache__",
            ".*_cache",
            ".coverage",
            ".hypothesis",
            "build",
            "dist",
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
    tabla = _tabla(contracts_root)
    rueda = herramienta.construir(copia, tmp_path / "salida", offline=True, solo_rueda=True)
    nombres = herramienta.nombres_de_rueda(rueda)
    assert f"veridicus_contracts/{intruso}" in nombres
    problemas = herramienta.comparar_rueda(nombres, tabla)
    assert len(problemas) == 1, problemas
    assert f"veridicus_contracts/{intruso}" in problemas[0]
