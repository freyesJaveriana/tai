"""`AnonymizingProvider` frente a mypy estricto (E42) y los tipos de C13 en ejecución (BR9.1, BR9.9).

Los dobles se escriben en `tmp_path` y se pasan por `mypy.api.run` con `--strict`, en el mismo
proceso. Nunca se escribe en `src/`.
"""

import re
from datetime import datetime
from pathlib import Path

import pytest
from helpers import importar_o_fallar, load_contract
from mypy import api as mypy_api

pytestmark = pytest.mark.c13

IMPORTACION = "from veridicus_contracts.model_calls import AnonymizingProvider"

DOBLE_CON_GENERATE = f"""{IMPORTACION}, GenerateRequest, GenerateResult


class Doble:
    def generate(self, request: GenerateRequest) -> GenerateResult:
        raise NotImplementedError


def usar(proveedor: AnonymizingProvider) -> None:
    del proveedor


usar(Doble())
"""

DOBLE_SIN_GENERATE = f"""{IMPORTACION}


class SinGenerate:
    def check_ready(self) -> bool:
        return True


def usar(proveedor: AnonymizingProvider) -> None:
    del proveedor


usar(SinGenerate())
"""


@pytest.fixture(scope="module")
def cache_de_mypy(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return tmp_path_factory.mktemp("cache-mypy")


def _mypy(tmp_path: Path, cache: Path, contracts_root: Path, fuente: str) -> tuple[str, int]:
    """Pasa `fuente` por mypy estricto con `src/` en la ruta de módulos; devuelve (salida, código)."""
    importar_o_fallar("veridicus_contracts.model_calls", "T08")
    configuracion = tmp_path / "mypy.ini"
    configuracion.write_text(
        f"[mypy]\nmypy_path = {contracts_root / 'src'}\nexplicit_package_bases = true\n",
        encoding="utf-8",
    )
    doble = tmp_path / "doble.py"
    doble.write_text(fuente, encoding="utf-8")
    salida, errores, codigo = mypy_api.run(
        ["--strict", "--config-file", str(configuracion), "--cache-dir", str(cache), str(doble)]
    )
    return salida + errores, codigo


def test_un_doble_con_solo_generate_pasa_mypy_estricto(
    tmp_path: Path, cache_de_mypy: Path, contracts_root: Path
) -> None:
    """E42: el doble mínimo cumple el `Protocol` sin heredar de él."""
    salida, codigo = _mypy(tmp_path, cache_de_mypy, contracts_root, DOBLE_CON_GENERATE)
    assert codigo == 0, salida
    assert "Success: no issues found" in salida


def test_un_doble_sin_generate_no_pasa_mypy_estricto(
    tmp_path: Path, cache_de_mypy: Path, contracts_root: Path
) -> None:
    """E42 (control negativo): sin `generate` no es un `AnonymizingProvider`."""
    salida, codigo = _mypy(tmp_path, cache_de_mypy, contracts_root, DOBLE_SIN_GENERATE)
    assert codigo == 1, salida
    assert '"SinGenerate"' in salida
    assert 'expected "AnonymizingProvider"' in salida
    assert "[arg-type]" in salida


def test_los_errores_tipados_llevan_la_llamada_salvo_el_fallo_cerrado() -> None:
    """C13 revisión 4: cuatro errores traen `call`; `AnonymizerUnavailable` no, porque no salió nada."""
    modelo = importar_o_fallar("veridicus_contracts.model_calls", "T08")
    llamada = modelo.ModelCall(
        role="prueba_a",
        provider="local",
        model="modelo-prueba-a",
        input_tokens=100,
        output_tokens=12,
        fallback_provider=False,
        anonymized=False,
        at=datetime(2026, 11, 23, 15, 0, 0),
    )
    assert llamada.version is None
    assert llamada.seed is None
    for clase in (modelo.ContentBlocked, modelo.Timeout, modelo.ProviderError, modelo.InvalidOutput):
        assert issubclass(clase, modelo.ModelCallError)
        error = clase("fallo sintético", llamada)
        assert error.call is llamada
        assert str(error) == "fallo sintético"
    cerrado = modelo.AnonymizerUnavailable("anonimizador caído")
    assert isinstance(cerrado, modelo.ModelCallError)
    assert not hasattr(cerrado, "call")
    resultado = modelo.GenerateResult(content={"ok": True}, altered_markers=[], call=llamada)
    assert resultado.call is llamada


def test_el_patron_del_papel_es_el_del_contrato_de_datos() -> None:
    """BR9.1: `Role` es `str` con el mismo patrón que `model-call.v1.yaml`, sin lista cerrada."""
    modelo = importar_o_fallar("veridicus_contracts.model_calls", "T08")
    assert modelo.Role is str
    assert load_contract("model_calls/model-call.v1.yaml")["properties"]["role"]["pattern"] == (
        modelo.ROLE_PATTERN
    )
    patron = re.compile(modelo.ROLE_PATTERN)
    assert patron.match("prueba_a") is not None
    assert patron.match("Prueba A") is None
    assert patron.match("a" * 33) is None
