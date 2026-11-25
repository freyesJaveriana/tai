"""Fronteras del paquete (paso 11; BR5.1, BR5.5, FD-U10-03): contratos de import-linter con control negativo.

Cada contrato se prueba sobre una **copia** del paquete y de su `pyproject.toml` en un directorio
temporal: la copia limpia pasa y, por cada contrato, una copia con un módulo que lo viola hace fallar
`lint-imports` (código distinto de 0). El árbol real nunca se modifica.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "src" / "veridicus_anonymizer"
LINT_IMPORTS = Path(sys.executable).parent / "lint-imports"

CONTRACTS = (
    "anonymizer-independent",
    "anonymizer-layers",
    "anonymizer-testing-not-in-production",
    "anonymizer-root-not-importing-testing",
)
FORBIDDEN_NAMES = (
    "model_gateway",
    "execution_profiles",
    "incoherence_analyzer",
    "veridicus_model_gateway",  # F-02: la convención de PD-3 lleva prefijo
    "veridicus_execution_profiles",
    "veridicus_incoherence_analyzer",
)
TESTING_IMPORT = "from veridicus_anonymizer.testing import bypass  # noqa: F401\n"

# Cada caso: contrato que debe romperse, archivo (relativo al paquete) y código que se añade a él.
VIOLATIONS = {
    **{
        f"independent:{name}": (
            "anonymizer-independent",
            "application/violacion.py",
            f"import {name}  # noqa: F401\n",
        )
        for name in FORBIDDEN_NAMES
    },
    "layers:providers->domain": (
        "anonymizer-layers",
        "providers/violacion.py",
        "from veridicus_anonymizer.domain import masking  # noqa: F401\n",
    ),
    "testing:application": (
        "anonymizer-testing-not-in-production",
        "application/violacion.py",
        TESTING_IMPORT,
    ),
    # F-03: el módulo raíz y los módulos de primer nivel también están cubiertos.
    "testing:__init__ raíz": (
        "anonymizer-root-not-importing-testing",
        "__init__.py",
        TESTING_IMPORT,
    ),
    "testing:módulo de primer nivel": (
        "anonymizer-testing-not-in-production",
        "cli.py",
        TESTING_IMPORT,
    ),
}


def _lint(
    workdir: Path, violation: tuple[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    """Copia el paquete y su configuración a `workdir`, añade la violación y corre `lint-imports`."""
    shutil.copytree(
        PACKAGE,
        workdir / "src" / "veridicus_anonymizer",
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    shutil.copy(ROOT / "pyproject.toml", workdir / "pyproject.toml")
    if violation is not None:
        relative, source = violation
        target = workdir / "src" / "veridicus_anonymizer" / relative
        existing = target.read_text("utf-8") if target.exists() else ""
        target.write_text(existing + source, "utf-8")
    env = {**os.environ, "PYTHONPATH": str(workdir / "src")}
    return subprocess.run(  # noqa: S603 - argumentos fijos, sin entrada externa
        [str(LINT_IMPORTS), str(workdir / "pyproject.toml")],
        cwd=workdir,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )


def test_the_contracts_are_declared_in_the_package_configuration() -> None:
    config = (ROOT / "pyproject.toml").read_text("utf-8")

    for name in CONTRACTS:
        assert f'name = "{name}"' in config


def test_a_clean_copy_keeps_every_contract(tmp_path: Path) -> None:
    result = _lint(tmp_path)

    assert result.returncode == 0, result.stdout
    assert f"Contracts: {len(CONTRACTS)} kept, 0 broken." in result.stdout


@pytest.mark.parametrize("case", list(VIOLATIONS), ids=list(VIOLATIONS))
def test_negative_control_a_module_that_violates_the_contract_makes_lint_imports_fail(
    case: str, tmp_path: Path
) -> None:
    contract, relative, source = VIOLATIONS[case]
    result = _lint(tmp_path, (relative, source))

    assert result.returncode != 0, result.stdout
    assert f"{contract} BROKEN" in result.stdout
    assert f"Contracts: {len(CONTRACTS) - 1} kept, 1 broken." in result.stdout
