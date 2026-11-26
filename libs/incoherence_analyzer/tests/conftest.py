"""Opción `--rojo` (paso 2, N-03): en el rojo, un fallo que no sea `NotImplementedError` es `ERROR`.

Con `--rojo`, un `pytest_runtest_makereport` con `hookwrapper=True` toma el reporte de la fase
`call` de una prueba que falló por una causa distinta de `NotImplementedError` y lo reescribe con
`when="setup"` y `outcome="failed"`, que pytest muestra como `ERROR`. Así el rojo solo cuenta como
rojo lo que falla porque falta implementar (`FAILED`), y un error de la propia prueba salta a la
vista. Sin `--rojo`, el comportamiento de pytest no cambia.

El mismo *hook* está en `libs/execution_profiles/tests/conftest.py`; `tests/test_conftest_rojo.py`
lo prueba con `pytester`, con su control negativo.
"""

from collections.abc import Generator
from typing import Any

import pytest

pytest_plugins = ["pytester"]


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--rojo",
        action="store_true",
        default=False,
        help="Cuenta como ERROR todo fallo que no sea NotImplementedError (rojo del paso 3).",
    )


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(
    item: pytest.Item, call: pytest.CallInfo[None]
) -> Generator[None, Any, None]:
    outcome = yield
    report: pytest.TestReport = outcome.get_result()
    if not item.config.getoption("--rojo"):
        return
    if report.when != "call" or not report.failed:
        return
    if call.excinfo is not None and call.excinfo.errisinstance(NotImplementedError):
        return
    report.when = "setup"
    report.outcome = "failed"
