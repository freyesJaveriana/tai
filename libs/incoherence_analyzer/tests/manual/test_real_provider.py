"""Corrida manual con el proveedor real (paso 12, R-04, R-13). La lanza el humano; no corre por defecto.

Usa la clave de `VERIDICUS_ANTHROPIC_API_KEY`, el plazo `VERIDICUS_LIMIT_MODEL_CALL_TIMEOUT_S=300` y
una entrevista **sintética** de `tests/fixtures/`. El anonimizador real de B10a seudonimiza lo que
sale. Sale por la red, así que se lanza con `--force-enable-socket`:

    timeout 900 uv run --frozen --offline --directory libs/incoherence_analyzer pytest tests/manual -m manual --no-cov --force-enable-socket -q

Las salidas quedan en `resultados-locales/manual-real-provider/` (cubierto por `.gitignore`) y su
resultado no se versiona. Un modelo real no es determinista: la prueba no exige un número de hallazgos
y solo comprueba que la CLI termina con 0 y que cada salida es una salida C6 válida.
"""

import json
import os
import shutil
from pathlib import Path
from typing import Any

import pytest

from tests.support import KEY_REF, PROFILE, c6_problems
from veridicus_incoherence_analyzer.cli.main import run

# Sin la marca `cli`: `-m cli` sustituye al `-m 'not manual'` de addopts y la correría por defecto.
pytestmark = pytest.mark.manual

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
OUT = Path("resultados-locales") / "manual-real-provider"


def _real_env() -> dict[str, str]:
    if not os.environ.get(KEY_REF):
        pytest.fail(f"falta la variable de entorno {KEY_REF}: es la clave del proveedor real")
    return {**os.environ, "VERIDICUS_LIMIT_MODEL_CALL_TIMEOUT_S": "300"}


@pytest.fixture(scope="module")
def results() -> Path:
    shutil.rmtree(OUT, ignore_errors=True)
    return OUT


@pytest.mark.parametrize("name", ["contradiccion", "coherente"])
def test_the_cli_with_the_real_provider_ends_with_0_and_a_valid_c6_output(
    name: str, results: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = run(
        ["analyze", str(FIXTURES / f"{name}.json"), "--perfil", PROFILE, "--salida", str(results)],
        _real_env(),
    )

    salida: dict[str, Any] = json.loads((results / f"{name}.salida.json").read_text("utf-8"))
    with capsys.disabled():
        print(
            f"\n[manual] {name}: código {code}, estado {salida['estado']} "
            f"({salida.get('error', {}).get('codigo', 'sin error')}), "
            f"{len(salida['hallazgos'])} hallazgo(s), "
            f"{len(salida['registro']['descartes'])} descarte(s); salida en {results}"
        )
    assert code == 0
    assert c6_problems(salida) == []
    assert salida["estado"] in {"ok", "error"}
