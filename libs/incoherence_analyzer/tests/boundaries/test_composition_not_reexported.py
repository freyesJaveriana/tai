"""Ningún `__init__.py` reexporta `cli.composition` (BR10.5, SD §1; paso 11).

`cli.composition` es la única excepción de `core-no-anonymizer`: si un `__init__.py` la reexportara,
cualquier módulo que importe el paquete la arrastraría. La comprobación es un recorrido del AST de
cada `__init__.py` de `src/`, con su control negativo sobre fuentes sintéticas.
"""

import ast
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
TARGET = "composition"


def reexports_composition(source: str) -> bool:
    """Verdadero si `source` importa, de cualquier forma, el módulo `composition`."""
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module.split(".")[-1] == TARGET or any(alias.name == TARGET for alias in node.names):
                return True
        elif isinstance(node, ast.Import) and any(
            alias.name.split(".")[-1] == TARGET for alias in node.names
        ):
            return True
    return False


def test_the_tree_has_init_files_to_check() -> None:
    inits = sorted(SRC.rglob("__init__.py"))

    assert len(inits) >= 5, "application, cli, domain, testing y el paquete raíz"


def test_no_init_file_reexports_the_composition_root() -> None:
    offenders = [
        str(path.relative_to(SRC))
        for path in sorted(SRC.rglob("__init__.py"))
        if reexports_composition(path.read_text("utf-8"))
    ]

    assert offenders == []


@pytest.mark.parametrize(
    "source",
    [
        "from veridicus_incoherence_analyzer.cli.composition import compose\n",
        "from veridicus_incoherence_analyzer.cli import composition\n",
        "from .composition import compose\n",
        "from . import composition\n",
        "import veridicus_incoherence_analyzer.cli.composition\n",
        "import veridicus_incoherence_analyzer.cli.composition as raiz\n",
    ],
)
def test_negative_control_every_form_of_reexport_is_detected(source: str) -> None:
    assert reexports_composition(source)


@pytest.mark.parametrize(
    "source",
    [
        "",
        "from veridicus_incoherence_analyzer.cli.main import run\n",
        "from veridicus_incoherence_analyzer.application import messages\n",
        "import veridicus_incoherence_analyzer.cli.main\n",
    ],
)
def test_positive_control_other_imports_are_not_flagged(source: str) -> None:
    assert not reexports_composition(source)
