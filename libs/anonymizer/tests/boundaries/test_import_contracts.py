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

VIOLATIONS = {
    "anonymizer-independent": (
        "application/violacion.py",
        "import model_gateway  # noqa: F401\n",
    ),
    "anonymizer-layers": (
        "providers/violacion.py",
        "from veridicus_anonymizer.domain import masking  # noqa: F401\n",
    ),
    "anonymizer-testing-not-in-production": (
        "application/violacion.py",
        "from veridicus_anonymizer.testing import bypass  # noqa: F401\n",
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
        (workdir / "src" / "veridicus_anonymizer" / relative).write_text(source, "utf-8")
    env = {**os.environ, "PYTHONPATH": str(workdir / "src")}
    return subprocess.run(  # noqa: S603 - argumentos fijos, sin entrada externa
        [str(LINT_IMPORTS), "--config", str(workdir / "pyproject.toml")],
        cwd=workdir,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )


def test_the_three_contracts_are_declared_in_the_package_configuration() -> None:
    config = (ROOT / "pyproject.toml").read_text("utf-8")

    for name in VIOLATIONS:
        assert f'name = "{name}"' in config


def test_a_clean_copy_keeps_the_three_contracts(tmp_path: Path) -> None:
    result = _lint(tmp_path)

    assert result.returncode == 0, result.stdout
    assert "Contracts: 3 kept, 0 broken." in result.stdout


@pytest.mark.parametrize("contract", list(VIOLATIONS), ids=list(VIOLATIONS))
def test_negative_control_a_module_that_violates_the_contract_makes_lint_imports_fail(
    contract: str, tmp_path: Path
) -> None:
    result = _lint(tmp_path, VIOLATIONS[contract])

    assert result.returncode != 0, result.stdout
    assert f"{contract} BROKEN" in result.stdout
    assert "Contracts: 2 kept, 1 broken." in result.stdout
