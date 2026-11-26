"""Opción `--rojo` (paso 2, N-03): en el rojo, un fallo que no sea `NotImplementedError` es `ERROR`.

Es el mismo *hook* de `libs/incoherence_analyzer/tests/conftest.py`, que lo prueba con `pytester`
(`tests/test_conftest_rojo.py`). Con `--rojo`, el reporte de la fase `call` de una prueba que falló
por una causa distinta de `NotImplementedError` se reescribe con `when="setup"` y
`outcome="failed"`, que pytest muestra como `ERROR`. Sin `--rojo`, pytest no cambia.
"""

from collections.abc import Generator
from typing import Any

import pytest


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
