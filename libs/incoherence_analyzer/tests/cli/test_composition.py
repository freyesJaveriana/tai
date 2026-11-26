"""La raíz de composición (PD-7, RD; módulo guardia con 100 % de ramas).

Orden de arranque: límites, perfil, *prompt*, aviso y gateway; el primer fallo detiene el arranque con
un error de configuración (código 3) sin ninguna llamada. El anonimizador se importa de forma diferida.
"""

import sys
from pathlib import Path
from typing import Any

import pytest
from veridicus_anonymizer.api import Anonymizer
from veridicus_anonymizer.testing.fake_transport import FakeTransport
from veridicus_errors import ConfigInvalidLimitError, ConfigInvalidProfileError, GatewayConfigError
from veridicus_integrity_policy import notice

from tests.application.profiles_support import local_profile
from tests.support import PROFILE, env
from veridicus_incoherence_analyzer.application import messages as prompt_messages
from veridicus_incoherence_analyzer.cli import composition
from veridicus_incoherence_analyzer.cli.composition import compose

pytestmark = pytest.mark.cli


class _Announced:
    def __init__(self) -> None:
        self.calls: list[tuple[notice.Notice, tuple[str, ...]]] = []

    def __call__(self, loaded: notice.Notice, warnings: tuple[str, ...]) -> None:
        self.calls.append((loaded, warnings))


def test_a_valid_profile_composes_the_gateway_with_the_real_anonymizer_and_the_environment_limits() -> (
    None
):
    announced = _Announced()

    result = compose(
        PROFILE, env(VERIDICUS_LIMIT_TURN_MAX_CHARS="500"), FakeTransport(), announce=announced
    )

    assert result.config.profile_name == PROFILE
    assert result.limits["turn_max_chars"] == 500, "la bajada del entorno llega a la composición"
    assert len(announced.calls) == 1
    assert announced.calls[0][0] == notice.load_notice()
    assert announced.calls[0][1] == ("same_family",)


def test_the_limits_come_first_and_an_invalid_one_stops_before_the_profile_and_the_notice() -> None:
    announced = _Announced()

    with pytest.raises(ConfigInvalidLimitError):
        compose(PROFILE, env(VERIDICUS_LIMIT_NO_EXISTE="1"), None, announce=announced)

    assert announced.calls == []


def test_an_unknown_profile_stops_before_the_notice() -> None:
    announced = _Announced()

    with pytest.raises(ConfigInvalidProfileError):
        compose("perfil-que-no-existe", env(), None, announce=announced)

    assert announced.calls == []


def test_a_prompt_that_does_not_match_its_reference_stops_before_the_notice(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    announced = _Announced()
    monkeypatch.setattr(prompt_messages, "prompt_sha256", lambda: "f" * 64)

    with pytest.raises(ConfigInvalidProfileError, match="prompt"):
        compose(PROFILE, env(), FakeTransport(), announce=announced)

    assert announced.calls == []


def test_a_missing_notice_stops_before_the_gateway(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing() -> notice.Notice:
        raise ConfigInvalidProfileError("El aviso de propósito limitado no está disponible.")

    built: list[object] = []
    monkeypatch.setattr(notice, "load_notice", missing)
    monkeypatch.setattr(composition, "build", lambda *a, **k: built.append(1))

    with pytest.raises(ConfigInvalidProfileError):
        compose(PROFILE, env(), FakeTransport(), announce=_Announced())

    assert built == [], "el gateway no se arma sin aviso"


def test_without_the_anonymizer_module_an_external_profile_does_not_start_but_the_notice_came_out(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    announced = _Announced()
    for name in [key for key in sys.modules if key.split(".")[0] == "veridicus_anonymizer"]:
        monkeypatch.setitem(sys.modules, name, None)
    monkeypatch.setitem(sys.modules, "veridicus_anonymizer", None)

    with pytest.raises(GatewayConfigError, match="anonimizador"):
        compose(PROFILE, env(), None, announce=announced)

    assert len(announced.calls) == 1, "VE-01: el aviso sale aunque el gateway no arranque"


def test_a_call_timeout_below_the_floor_is_rejected_with_the_profile_before_any_call() -> None:
    announced = _Announced()

    with pytest.raises(ConfigInvalidProfileError, match="270"):
        compose(
            PROFILE,
            env(VERIDICUS_LIMIT_MODEL_CALL_TIMEOUT_S="269"),
            FakeTransport(),
            announce=announced,
        )

    assert announced.calls == []


def test_a_profile_without_external_destinations_imports_no_anonymizer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    received: list[Any] = []
    monkeypatch.setattr(composition, "load_config", lambda *a, **k: local_profile(tmp_path))
    monkeypatch.setattr(
        composition,
        "build",
        lambda config, anonymizing_provider=None: received.append(anonymizing_provider),
    )
    monkeypatch.setitem(sys.modules, "veridicus_anonymizer", None)

    compose("todo-local", env(), None, announce=_Announced())

    assert received == [None], "sin papel externo, ni se importa ni se inyecta el anonimizador"


def test_an_external_fallback_alone_is_enough_to_require_the_anonymizer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    received: list[Any] = []
    monkeypatch.setattr(
        composition, "load_config", lambda *a, **k: local_profile(tmp_path, fallback=True)
    )
    monkeypatch.setattr(
        composition,
        "build",
        lambda config, anonymizing_provider=None: received.append(anonymizing_provider),
    )

    compose("todo-local", env(), FakeTransport(), announce=_Announced())

    assert len(received) == 1 and isinstance(received[0], Anonymizer)
