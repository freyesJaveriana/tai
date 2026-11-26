"""Fronteras de U11 (paso 11; BR10.5, SD §1): contratos de import-linter con control negativo.

Cada contrato se prueba sobre una **copia** del paquete y de su `pyproject.toml` en un directorio
temporal: la copia limpia los cumple todos y, por cada contrato, una copia con un módulo que lo viola
hace fallar `lint-imports` (código distinto de 0) y nombra ese contrato. El árbol real no se modifica.
Los contratos viven en el `pyproject.toml` de cada paquete: `u11-no-infra` en los cuatro,
`gateway-no-anonymizer` en `model_gateway`, `core-no-anonymizer` y `layers` en este paquete.
"""

import os
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

LIBS = Path(__file__).resolve().parents[3]
LINT_IMPORTS = Path(sys.executable).parent / "lint-imports"
INFRA = ("redis", "kubernetes", "psycopg", "asyncpg", "sqlalchemy", "prometheus_client")

# paquete de `libs/` -> (nombre importable, contratos que declara su pyproject.toml)
PACKAGES = {
    "incoherence_analyzer": (
        "veridicus_incoherence_analyzer",
        ("u11-no-infra", "core-no-anonymizer", "layers"),
    ),
    "model_gateway": ("veridicus_model_gateway", ("u11-no-infra", "gateway-no-anonymizer")),
    "execution_profiles": ("veridicus_execution_profiles", ("u11-no-infra",)),
    "integrity_policy": ("veridicus_integrity_policy", ("u11-no-infra",)),
}

# Cada caso: paquete, contrato que debe romperse, archivo (relativo al paquete) y código añadido.
VIOLATIONS: dict[str, tuple[str, str, str, str]] = {}
for _package in PACKAGES:
    for _infra in INFRA:
        VIOLATIONS[f"{_package}:no-infra:{_infra}"] = (
            _package,
            "u11-no-infra",
            "violacion.py",
            f"import {_infra}  # noqa: F401\n",
        )
VIOLATIONS.update(
    {
        "model_gateway:gateway-no-anonymizer": (
            "model_gateway",
            "gateway-no-anonymizer",
            "adapters/violacion.py",
            "import veridicus_anonymizer  # noqa: F401\n",
        ),
        "model_gateway:gateway-no-anonymizer:api": (
            "model_gateway",
            "gateway-no-anonymizer",
            "gateway.py",
            "from veridicus_anonymizer.api import build_anonymizer  # noqa: F401\n",
        ),
        "core:no-anonymizer:application": (
            "incoherence_analyzer",
            "core-no-anonymizer",
            "application/violacion.py",
            "import veridicus_anonymizer  # noqa: F401\n",
        ),
        "core:no-anonymizer:api": (
            "incoherence_analyzer",
            "core-no-anonymizer",
            "api.py",
            "from veridicus_anonymizer.api import build_anonymizer  # noqa: F401\n",
        ),
        "core:no-anonymizer:only-composition-is-the-exception": (
            "incoherence_analyzer",
            "core-no-anonymizer",
            "cli/otro.py",
            "from veridicus_anonymizer.api import build_anonymizer  # noqa: F401\n",
        ),
        "layers:domain->application": (
            "incoherence_analyzer",
            "layers",
            "domain/violacion.py",
            "from veridicus_incoherence_analyzer.application import preflight  # noqa: F401\n",
        ),
        "layers:domain->cli": (
            "incoherence_analyzer",
            "layers",
            "domain/violacion.py",
            "from veridicus_incoherence_analyzer.cli import main  # noqa: F401\n",
        ),
        "layers:domain->httpx": (
            "incoherence_analyzer",
            "layers",
            "domain/violacion.py",
            "import httpx  # noqa: F401\n",
        ),
        "layers:domain->gateway": (
            "incoherence_analyzer",
            "layers",
            "domain/violacion.py",
            "import veridicus_model_gateway  # noqa: F401\n",
        ),
    }
)


def _lint(
    workdir: Path, package: str, violation: tuple[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    """Copia el paquete y su configuración a `workdir`, añade la violación y corre `lint-imports`."""
    name, _ = PACKAGES[package]
    shutil.copytree(
        LIBS / package / "src" / name,
        workdir / "src" / name,
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    shutil.copy(LIBS / package / "pyproject.toml", workdir / "pyproject.toml")
    if violation is not None:
        relative, source = violation
        target = workdir / "src" / name / relative
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


@pytest.mark.parametrize("package", list(PACKAGES))
def test_the_contracts_are_declared_in_the_package_configuration(package: str) -> None:
    config = tomllib.loads((LIBS / package / "pyproject.toml").read_text("utf-8"))["tool"]
    declared = [contract["name"] for contract in config["importlinter"]["contracts"]]

    assert declared == list(PACKAGES[package][1])
    assert config["importlinter"]["root_package"] == PACKAGES[package][0]
    assert config["importlinter"]["include_external_packages"] is True


def test_the_infrastructure_list_is_the_one_of_sd_section_1() -> None:
    for package in PACKAGES:
        config = tomllib.loads((LIBS / package / "pyproject.toml").read_text("utf-8"))["tool"]
        contract = next(
            c for c in config["importlinter"]["contracts"] if c["name"] == "u11-no-infra"
        )
        assert tuple(contract["forbidden_modules"]) == INFRA, package


def test_the_anonymizer_forbids_the_integrity_policy_package_too() -> None:
    """CG-U11-08: la lista prohibida de U10 suma `veridicus_integrity_policy`."""
    config = tomllib.loads((LIBS / "anonymizer" / "pyproject.toml").read_text("utf-8"))["tool"]
    contract = next(
        c for c in config["importlinter"]["contracts"] if c["name"] == "anonymizer-independent"
    )

    assert "veridicus_integrity_policy" in contract["forbidden_modules"]


def test_core_no_anonymizer_has_the_composition_as_its_only_exception() -> None:
    config = tomllib.loads((LIBS / "incoherence_analyzer" / "pyproject.toml").read_text("utf-8"))[
        "tool"
    ]
    contract = next(
        c for c in config["importlinter"]["contracts"] if c["name"] == "core-no-anonymizer"
    )

    assert contract["ignore_imports"] == [
        "veridicus_incoherence_analyzer.cli.composition -> veridicus_anonymizer"
    ]


@pytest.mark.parametrize("package", list(PACKAGES))
def test_a_clean_copy_keeps_every_contract(package: str, tmp_path: Path) -> None:
    contracts = PACKAGES[package][1]

    result = _lint(tmp_path, package)

    assert result.returncode == 0, result.stdout
    assert f"Contracts: {len(contracts)} kept, 0 broken." in result.stdout


@pytest.mark.parametrize("case", list(VIOLATIONS), ids=list(VIOLATIONS))
def test_negative_control_a_module_that_violates_the_contract_makes_lint_imports_fail(
    case: str, tmp_path: Path
) -> None:
    package, contract, relative, source = VIOLATIONS[case]
    total = len(PACKAGES[package][1])

    result = _lint(tmp_path, package, (relative, source))

    assert result.returncode != 0, result.stdout
    assert f"{contract} BROKEN" in result.stdout
    assert f"Contracts: {total - 1} kept, 1 broken." in result.stdout
