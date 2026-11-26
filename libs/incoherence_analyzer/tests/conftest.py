"""Opción `--rojo` (paso 2, N-03): en el rojo, un fallo que no sea `NotImplementedError` es `ERROR`.

Con `--rojo`, un `pytest_runtest_makereport` con `hookwrapper=True` toma el reporte de la fase
`call` de una prueba que falló por una causa distinta de `NotImplementedError` y lo reescribe con
`when="setup"` y `outcome="failed"`, que pytest muestra como `ERROR`. Así el rojo solo cuenta como
rojo lo que falla porque falta implementar (`FAILED`), y un error de la propia prueba salta a la
vista. Sin `--rojo`, el comportamiento de pytest no cambia.

El mismo *hook* está en `libs/execution_profiles/tests/conftest.py`; `tests/test_conftest_rojo.py`
lo prueba con `pytester`, con su control negativo.
"""

from collections.abc import Generator, Mapping
from pathlib import Path
from typing import Any

import pytest
from veridicus_execution_profiles.loader import EffectiveConfig, load_config

from tests import support
from veridicus_incoherence_analyzer.application.messages import load_prompt_reference

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


@pytest.fixture(autouse=True)
def _config_with_the_prompt_reference(monkeypatch: pytest.MonkeyPatch) -> None:
    """La composición de las pruebas pasa la referencia del prompt, como lo hará la CLI (K-88).

    Las pruebas congeladas arman la configuración con `tests.support.make_config`, que llama a
    `load_config(perfil, env)` sin `prompt_sha256`: con el valor por omisión (64 ceros) `analyze`
    falla cerrado, y es lo correcto. Esta costura sustituye solo el nombre `load_config` del módulo
    `tests.support` por un envoltorio que pone `load_prompt_reference()` cuando la prueba no pasa
    otro valor. `load_config` real, importado directamente, conserva el valor por omisión.
    """

    def with_reference(
        profile_name: str,
        env: Mapping[str, str],
        path: Path | None = None,
        *,
        prompt_sha256: str | None = None,
    ) -> EffectiveConfig:
        reference = load_prompt_reference() if prompt_sha256 is None else prompt_sha256
        return load_config(profile_name, env, path, prompt_sha256=reference)

    monkeypatch.setattr(support, "load_config", with_reference)
