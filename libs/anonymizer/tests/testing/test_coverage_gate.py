"""Pruebas de `testing/coverage_gate.py` (paso 14): lee `coverage.json` y exige el 100 % de ramas
en los módulos guardia y el 80 % de líneas en el paquete. Todo es un `coverage.json` sintético."""

import json
from pathlib import Path
from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st

from veridicus_anonymizer.testing.coverage_gate import evaluate, main

PREFIX = "src/veridicus_anonymizer/"
# Un archivo por grupo guardia, más uno que no lo es (fuera de la regla de ramas).
GUARD_FILES = (
    PREFIX + "domain/masking.py",
    PREFIX + "application/generate.py",
    PREFIX + "api.py",
    PREFIX + "providers/anthropic.py",
    PREFIX + "testing/fake_transport.py",
)
OTHER_FILE = PREFIX + "testing/coverage_gate.py"


def file_entry(
    *, statements: int = 10, covered: int = 10, branches: int = 4, covered_branches: int = 4
) -> dict[str, Any]:
    return {
        "summary": {
            "num_statements": statements,
            "covered_lines": covered,
            "num_branches": branches,
            "covered_branches": covered_branches,
        }
    }


def report(**overrides: dict[str, Any]) -> dict[str, Any]:
    """Un informe que pasa; `overrides` reemplaza la entrada de un archivo (clave = ruta)."""
    files = {path: file_entry() for path in (*GUARD_FILES, OTHER_FILE)}
    files.update(overrides)
    return {"files": files}


def test_a_report_that_meets_both_floors_passes() -> None:
    assert evaluate(report()) == []


@pytest.mark.parametrize("path", GUARD_FILES)
def test_one_missing_branch_in_each_guard_group_fails_naming_the_file(path: str) -> None:
    failures = evaluate(report(**{path: file_entry(branches=4, covered_branches=3)}))
    assert len(failures) == 1
    assert path in failures[0]
    assert "rama" in failures[0]


def test_missing_branches_outside_the_guard_modules_do_not_fail() -> None:
    assert evaluate(report(**{OTHER_FILE: file_entry(branches=4, covered_branches=0)})) == []


def test_the_init_files_of_guard_directories_count_as_guard_modules() -> None:
    path = PREFIX + "domain/__init__.py"
    assert evaluate(report(**{path: file_entry(branches=2, covered_branches=1)}))


def test_line_coverage_below_eighty_percent_fails() -> None:
    low = file_entry(statements=100, covered=79, branches=0, covered_branches=0)
    failures = evaluate({"files": {path: low for path in (*GUARD_FILES, OTHER_FILE)}})
    assert any("líneas" in failure for failure in failures)


def test_line_coverage_of_exactly_eighty_percent_passes() -> None:
    exact = {path: file_entry(statements=10, covered=8) for path in GUARD_FILES}
    assert evaluate({"files": exact}) == []


def test_a_guard_group_without_any_file_fails_closed() -> None:
    files = report()["files"]
    del files[PREFIX + "providers/anthropic.py"]
    failures = evaluate({"files": files})
    assert any("providers" in failure for failure in failures)


def test_an_empty_report_fails() -> None:
    assert evaluate({"files": {}})


@pytest.mark.parametrize(
    "broken",
    [{}, {"files": []}, {"files": {"x.py": {}}}, {"files": {"x.py": {"summary": {}}}}],
)
def test_a_malformed_report_fails_instead_of_passing(broken: dict[str, Any]) -> None:
    assert evaluate(broken)


@pytest.mark.parametrize(
    "entry",
    [
        {},
        {"summary": []},
        {"summary": {}},
        {"summary": {**file_entry()["summary"], "num_branches": "4"}},
        {"summary": {**file_entry()["summary"], "covered_branches": -1}},
        {"summary": {**file_entry()["summary"], "covered_lines": True}},
    ],
)
def test_a_malformed_entry_of_a_package_file_fails(entry: dict[str, Any]) -> None:
    failures = evaluate(report(**{GUARD_FILES[0]: entry}))
    assert any(GUARD_FILES[0] in failure for failure in failures)


def test_files_outside_the_package_are_ignored() -> None:
    other = {"tests/test_x.py": file_entry(branches=4, covered_branches=0)}
    assert evaluate({"files": {**report()["files"], **other}}) == []


def write(tmp_path: Path, content: dict[str, Any]) -> Path:
    target = tmp_path / "coverage.json"
    target.write_text(json.dumps(content), encoding="utf-8")
    return target


def test_main_returns_zero_for_a_passing_report(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main([str(write(tmp_path, report()))]) == 0
    assert "100 % de ramas" in capsys.readouterr().out


def test_main_returns_one_and_names_the_failing_module(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    broken = report(**{GUARD_FILES[2]: file_entry(branches=2, covered_branches=1)})
    assert main([str(write(tmp_path, broken))]) == 1
    assert GUARD_FILES[2] in capsys.readouterr().err


def test_main_fails_when_the_file_is_missing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main([str(tmp_path / "no-existe.json")]) == 1
    assert "no se pudo leer" in capsys.readouterr().err


def test_main_fails_when_the_file_is_not_json(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    target = tmp_path / "coverage.json"
    target.write_text("esto no es json", encoding="utf-8")
    assert main([str(target)]) == 1
    assert "no se pudo leer" in capsys.readouterr().err


@pytest.mark.parametrize("argv", [[], ["a.json", "b.json"]])
def test_main_requires_exactly_one_argument(
    argv: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(argv) == 2
    assert "uso" in capsys.readouterr().err


# Propiedad (ML-11): sobre todas las formas del informe, el gate pasa si y solo si cada rama de
# cada archivo guardia está cubierta y el paquete llega al 80 % de líneas.
@given(
    st.lists(
        st.tuples(
            st.integers(min_value=0, max_value=50),
            st.integers(min_value=0, max_value=50),
            st.integers(min_value=0, max_value=20),
            st.integers(min_value=0, max_value=20),
        ),
        min_size=len(GUARD_FILES),
        max_size=len(GUARD_FILES),
    )
)
def test_gate_passes_exactly_when_branches_are_complete_and_lines_reach_eighty(
    rows: list[tuple[int, int, int, int]],
) -> None:
    files: dict[str, Any] = {}
    statements = covered_lines = 0
    branches_complete = True
    for path, (stmts, cov, branches, cov_branches) in zip(GUARD_FILES, rows, strict=True):
        cov = min(cov, stmts)
        cov_branches = min(cov_branches, branches)
        files[path] = file_entry(
            statements=stmts, covered=cov, branches=branches, covered_branches=cov_branches
        )
        statements += stmts
        covered_lines += cov
        branches_complete = branches_complete and cov_branches == branches
    lines_ok = statements > 0 and covered_lines * 100 >= statements * 80
    assert (evaluate({"files": files}) == []) == (branches_complete and lines_ok)
