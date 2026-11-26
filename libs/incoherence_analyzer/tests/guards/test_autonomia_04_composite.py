"""AUTONOMIA-04, prueba compuesta (AC11.3.3, AC11.3.7, BR7.4 a BR7.6, BR10.1; PD-8).

Gateway real, `Anonymizer` real de B10a y un transporte HTTP guionado, sin red. Ningún cuerpo que sale
lleva una entidad sembrada (con su control negativo `bypass`); si el anonimizador falla no sale
ninguna llamada y no se reintenta; una llamada externa con `anonymized: false` aborta la corrida.
Las pruebas que pasan por `cli.main.run` llevan `@pytest.mark.cli`.
"""

import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from veridicus_anonymizer import api as anonymizer_api
from veridicus_anonymizer.api import Anonymizer, build_anonymizer
from veridicus_anonymizer.application import generate as anonymizer_generate
from veridicus_anonymizer.domain.catalogs import CatalogError
from veridicus_anonymizer.testing.bypass import bypass_pseudonymization
from veridicus_contracts.limits import LimitsConfigError
from veridicus_contracts.model_calls import GenerateRequest, GenerateResult, ProviderError
from veridicus_errors import GatewayConfigError
from veridicus_model_gateway.gateway import build

from tests.support import (
    ENTITIES,
    KEY_REF,
    ScriptedGateway,
    ScriptedProvider,
    assert_error_output,
    assert_no_entity_in_payload,
    echo_finding,
    env,
    finding,
    make_call,
    make_config,
    make_entrada,
    write_transcription,
)
from veridicus_incoherence_analyzer.api import Salida, analyze
from veridicus_incoherence_analyzer.cli.main import run

PROFILE_ARGS = ["--perfil", "demo-anthropic"]


def _composite() -> tuple[ScriptedProvider, Salida]:
    """Una corrida completa por el gateway real y el `Anonymizer` real; llama a los *stubs*."""
    config = make_config()
    provider = ScriptedProvider(echo_finding)
    gateway = build(config, anonymizing_provider=build_anonymizer(env(), provider))
    return provider, analyze(make_entrada(), config, gateway)


def _runaway_clock() -> Any:
    state = {"now": -1000.0}

    def clock() -> float:
        state["now"] += 1000.0
        return state["now"]

    return clock


def _boom(*args: object, **kwargs: object) -> Any:
    raise RuntimeError("fallo sintetico")


# --- Un destino externo sin anonimizador no arranca ----------------------------------------------


def test_an_external_profile_without_anonymizer_does_not_start() -> None:
    config = make_config()

    with pytest.raises(GatewayConfigError):
        build(config)


@pytest.mark.cli
def test_the_cli_with_an_external_profile_and_no_anonymizer_ends_with_3_and_makes_no_call(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for name in [key for key in sys.modules if key.split(".")[0] == "veridicus_anonymizer"]:
        monkeypatch.setitem(sys.modules, name, None)
    monkeypatch.setitem(sys.modules, "veridicus_anonymizer", None)
    entrada = write_transcription(tmp_path)
    out = tmp_path / "salida"
    provider = ScriptedProvider(echo_finding)

    code = run(
        ["analyze", str(entrada), *PROFILE_ARGS, "--salida", str(out)], env(), transport=provider
    )

    assert code == 3
    assert provider.request_count == 0
    assert not list(tmp_path.rglob("*.salida.json"))
    assert not (out / "AVISO.txt").exists(), "ni siquiera AVISO.txt (BR11.2)"


# --- El payload saliente (AC11.3.7, BR7.5) ---------------------------------------------------------


def test_no_seeded_entity_leaves_in_the_bodies_of_judge_verifier_and_permuted_verifier() -> None:
    provider, salida = _composite()

    assert salida["estado"] == "ok"
    assert provider.request_count == 3, "juez, verificador y verificador permutado"
    assert_no_entity_in_payload(provider, ENTITIES)
    assert any(b"[PERSONA_" in raw or b"[ENTIDAD_" in raw for raw in provider.bodies), (
        "los cuerpos llevan marcas"
    )


def test_negative_control_the_same_assertion_fails_with_pseudonymization_bypassed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bypass_pseudonymization(monkeypatch)

    provider, _ = _composite()

    assert provider.request_count >= 1
    with pytest.raises(AssertionError, match="fuga"):
        assert_no_entity_in_payload(provider, ENTITIES)


# --- BR7.4: si el anonimizador falla, 0 llamadas y sin reintento ------------------------------------


def test_variant_a_without_the_api_key_nothing_leaves_and_the_run_ends_closed() -> None:
    config = make_config()
    provider = ScriptedProvider(echo_finding)
    without_key = {name: value for name, value in env().items() if name != KEY_REF}
    gateway = build(config, anonymizing_provider=build_anonymizer(without_key, provider))

    salida = analyze(make_entrada(), config, gateway)

    assert_error_output(salida, "anonimizador_no_disponible")
    assert provider.request_count == 0


def test_variant_b_with_the_pseudonymization_budget_exhausted_nothing_leaves(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = make_config()
    monkeypatch.setattr(anonymizer_generate, "now", _runaway_clock())
    provider = ScriptedProvider(echo_finding)
    gateway = build(config, anonymizing_provider=build_anonymizer(env(), provider))

    salida = analyze(make_entrada(), config, gateway)

    assert_error_output(salida, "anonimizador_no_disponible")
    assert provider.request_count == 0


def test_variant_c_an_unexpected_exception_while_pseudonymizing_leaves_nothing_out(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = make_config()
    monkeypatch.setattr(anonymizer_generate, "pseudonymize", _boom)
    provider = ScriptedProvider(echo_finding)
    gateway = build(config, anonymizing_provider=build_anonymizer(env(), provider))

    salida = analyze(make_entrada(), config, gateway)

    assert_error_output(salida, "anonimizador_no_disponible")
    assert provider.request_count == 0


def test_variant_d_a_provider_that_does_not_answer_in_time_is_not_retried() -> None:
    class SilentProvider:
        calls = 0

        def generate(self, request: GenerateRequest) -> GenerateResult:
            SilentProvider.calls += 1
            raise TimeoutError("sin respuesta dentro del plazo")

    config = make_config()
    gateway = build(config, anonymizing_provider=SilentProvider())

    salida = analyze(make_entrada(), config, gateway)

    assert_error_output(salida, "anonimizador_no_disponible")
    assert SilentProvider.calls == 1, "sin reintento y sin pasar a otra llamada"


@pytest.mark.cli
@pytest.mark.parametrize("failure", ["catalog", "limit"])
def test_variant_e_an_anonymizer_that_cannot_be_built_is_a_config_error_with_no_c6_output(
    failure: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def broken_catalogs(*args: object, **kwargs: object) -> Any:
        raise CatalogError("catálogo inválido")

    def broken_limits(*args: object, **kwargs: object) -> Any:
        raise LimitsConfigError("cifra de límite inválida")

    if failure == "catalog":
        monkeypatch.setattr(anonymizer_api, "load_catalogs", broken_catalogs)
    else:
        monkeypatch.setattr(anonymizer_api, "limits", SimpleNamespace(load=broken_limits))
    entrada = write_transcription(tmp_path)
    out = tmp_path / "salida"
    provider = ScriptedProvider(echo_finding)

    code = run(
        ["analyze", str(entrada), *PROFILE_ARGS, "--salida", str(out)], env(), transport=provider
    )

    assert code == 3
    assert provider.request_count == 0
    assert not list(tmp_path.rglob("*.salida.json")), "ninguna salida C6"
    assert not (out / "AVISO.txt").exists(), "ni siquiera AVISO.txt (BR11.2)"


# --- BR7.6: una llamada externa sin anonimizar es un incidente ---------------------------------------


def test_an_external_call_that_comes_back_unanonymized_aborts_the_run_at_that_call() -> None:
    config = make_config()
    gateway = ScriptedGateway(findings=[finding()], anonymized_from=2)

    salida = analyze(make_entrada(), config, gateway)

    assert_error_output(salida, "incidente_anonimizacion")
    assert gateway.roles() == ["judge", "verifier"], "exactamente 2 llamadas"
    llamadas = salida["registro"]["llamadas"]
    assert len(llamadas) == 2
    assert llamadas[-1]["anonimizado"] is False


def test_the_incident_takes_precedence_over_the_error_of_the_same_call() -> None:
    config = make_config()
    failing = ProviderError("fallo del proveedor", make_call("verifier", anonymized=False))
    gateway = ScriptedGateway(findings=[finding()], fail={"verifier": failing})

    salida = analyze(make_entrada(), config, gateway)

    assert_error_output(salida, "incidente_anonimizacion")
    assert salida["registro"]["llamadas"][-1]["anonimizado"] is False


@pytest.mark.cli
def test_the_cli_ends_with_4_and_writes_the_error_output_of_an_incident(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def unanonymized(self: Anonymizer, request: GenerateRequest) -> GenerateResult:
        return GenerateResult(
            content={"hallazgos": []},
            altered_markers=[],
            call=make_call(request.role, anonymized=False),
        )

    monkeypatch.setattr(Anonymizer, "generate", unanonymized)
    entrada = write_transcription(tmp_path)
    out = tmp_path / "salida"
    provider = ScriptedProvider(echo_finding)

    code = run(
        ["analyze", str(entrada), *PROFILE_ARGS, "--salida", str(out)], env(), transport=provider
    )

    written = json.loads((out / "SINT-0001.salida.json").read_text("utf-8"))
    assert code == 4
    assert written["estado"] == "error"
    assert written["error"]["codigo"] == "incidente_anonimizacion"
