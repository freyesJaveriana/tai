"""El *hook* `--rojo` del `conftest` (N-03): prueba con `pytester` y su control negativo."""

from pathlib import Path

import pytest

CONFTEST = Path(__file__).with_name("conftest.py")
EXECUTION_PROFILES_CONFTEST = (
    Path(__file__).parents[2] / "execution_profiles" / "tests" / "conftest.py"
)

TESTS = """
import pytest


def test_assertion_error():
    assert 1 == 2


def test_not_implemented():
    raise NotImplementedError("falta implementar")


def test_passes():
    assert True
"""


def _run(pytester: pytest.Pytester, conftest: Path, *args: str) -> pytest.RunResult:
    pytester.makeconftest(conftest.read_text("utf-8").replace('pytest_plugins = ["pytester"]', ""))
    pytester.makepyfile(test_inner=TESTS)
    return pytester.runpytest("-p", "no:cacheprovider", *args)


def test_with_rojo_an_assertion_error_is_error_and_not_implemented_is_failed(
    pytester: pytest.Pytester,
) -> None:
    result = _run(pytester, CONFTEST, "--rojo")
    result.assert_outcomes(passed=1, failed=1, errors=1)
    result.stdout.fnmatch_lines(["*ERROR test_inner.py::test_assertion_error*"])
    result.stdout.fnmatch_lines(["*FAILED test_inner.py::test_not_implemented*"])


def test_negative_control_without_rojo_an_assertion_error_stays_failed(
    pytester: pytest.Pytester,
) -> None:
    result = _run(pytester, CONFTEST)
    result.assert_outcomes(passed=1, failed=2, errors=0)


def test_the_execution_profiles_conftest_has_the_same_hook(pytester: pytest.Pytester) -> None:
    result = _run(pytester, EXECUTION_PROFILES_CONFTEST, "--rojo")
    result.assert_outcomes(passed=1, failed=1, errors=1)
