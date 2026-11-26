"""Códigos de salida de la CLI (BR11.3) y salidas de un lote (BR11.1, BR11.2); F9, AC12.1.x.

Una prueba por código (0, 2, 3, 4 y 5) y una por situación que lo produce. Toda validación previa
termina sin ninguna llamada y sin ningún archivo, ni siquiera `AVISO.txt` (BR11.2).
"""

import json
import signal
from collections.abc import Callable
from pathlib import Path
from typing import Any

import httpx
import pytest
from veridicus_anonymizer.api import Anonymizer
from veridicus_anonymizer.testing.fake_transport import FakeResponse, FakeTransport
from veridicus_contracts.model_calls import GenerateRequest, GenerateResult

from tests.cli.helpers import corpus_input, files_under, go, write_input, write_json
from tests.support import (
    KEY_REF,
    PROFILE,
    ScriptedProvider,
    c6_problems,
    default_turns,
    echo_finding,
    env,
    make_call,
    make_transcription,
)
from veridicus_incoherence_analyzer.cli import main as cli_main
from veridicus_incoherence_analyzer.cli.io_atomic import AtomicWriteError
from veridicus_incoherence_analyzer.cli.main import run

pytestmark = pytest.mark.cli


def _assert_nothing_was_done(tmp_path: Path, provider: ScriptedProvider) -> None:
    assert provider.request_count == 0, "0 llamadas (BR11.2)"
    assert files_under(tmp_path / "salida") == [], "ningún archivo, ni siquiera AVISO.txt (BR11.2)"


# --- Código 0 (BR11.1, AC12.1.1, AC12.1.2) -----------------------------------------------------------


def test_exit_0_a_directory_of_three_transcriptions_writes_three_outputs_and_the_notice(
    tmp_path: Path,
) -> None:
    entradas = tmp_path / "entradas"
    for index in (3, 1, 2):
        write_input(entradas, f"SINT-000{index}.json")
    write_json(entradas / "notas.txt", {"no": "es una entrevista"})
    out = tmp_path / "salida"
    provider = ScriptedProvider(echo_finding)

    code = go(entradas, out, transport=provider)

    names = [path.name for path in files_under(out)]
    assert code == 0
    assert names == [
        "AVISO.txt",
        "SINT-0001.salida.json",
        "SINT-0002.salida.json",
        "SINT-0003.salida.json",
    ]
    assert provider.request_count == 9, "juez, verificador y verificador permutado por entrevista"
    for name in names[1:]:
        salida = json.loads((out / name).read_text("utf-8"))
        assert salida["estado"] == "ok" and len(salida["hallazgos"]) == 1
        assert c6_problems(salida) == []


def test_exit_0_when_a_run_ends_in_error_state_with_its_code_in_the_output(tmp_path: Path) -> None:
    entrada = write_input(tmp_path)
    out = tmp_path / "salida"

    code = go(entrada, out, transport=FakeTransport(FakeResponse.not_json()))

    salida = json.loads((out / "SINT-0001.salida.json").read_text("utf-8"))
    assert code == 0, "AC12.1.2: una corrida en error no cambia el código"
    assert salida["estado"] == "error" and salida["error"]["codigo"]
    assert salida["hallazgos"] == []
    assert c6_problems(salida) == []


# --- Código 2: argumento, archivo, consentimiento, límite, directorio (BR11.2) ------------------------


def _missing(tmp: Path) -> Path:
    return tmp / "no-existe.json"


def _empty_directory(tmp: Path) -> Path:
    (tmp / "vacio").mkdir()
    return tmp / "vacio"


def _not_json(tmp: Path) -> Path:
    path = tmp / "roto.json"
    path.write_text("{ esto no es json", encoding="utf-8")
    return path


def _not_object(tmp: Path) -> Path:
    return write_json(tmp / "lista.json", [1, 2, 3])


def _without_turns(tmp: Path) -> Path:
    transcription = make_transcription()
    del transcription["turnos"]
    return write_json(tmp / "sin-turnos.json", transcription)


def _consent_missing(tmp: Path) -> Path:
    return write_input(tmp, origen="corpus")


def _repeated_turn_number(tmp: Path) -> Path:
    turns = default_turns()
    turns[2]["n"] = 2
    return write_input(tmp, turnos=turns)


@pytest.mark.parametrize(
    "build",
    [
        _missing,
        _empty_directory,
        _not_json,
        _not_object,
        _without_turns,
        _consent_missing,
        _repeated_turn_number,
    ],
)
def test_exit_2_for_an_input_that_cannot_be_analyzed_with_no_calls_and_no_files(
    build: Callable[[Path], Path], tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    provider = ScriptedProvider(echo_finding)

    code = go(build(tmp_path), tmp_path / "salida", transport=provider)

    assert code == 2
    _assert_nothing_was_done(tmp_path, provider)
    assert capsys.readouterr().err, "un mensaje en español nombra el problema"


def test_exit_2_for_a_repeated_turn_number_names_the_turn_number_rule(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A-02 de U11-T04: `import.invalid_transcript` por un `n` repetido es el código 2."""
    code = go(_repeated_turn_number(tmp_path), tmp_path / "salida")

    assert code == 2
    assert "se repite" in capsys.readouterr().err


def test_exit_2_when_a_figure_lowered_from_the_environment_is_exceeded(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Los límites de C25 se componen desde el entorno: una bajada por VERIDICUS_LIMIT_* se aplica."""
    entrada = write_input(tmp_path)
    provider = ScriptedProvider(echo_finding)

    code = go(
        entrada,
        tmp_path / "salida",
        environ=env(VERIDICUS_LIMIT_TURN_MAX_CHARS="10"),
        transport=provider,
    )

    assert code == 2
    _assert_nothing_was_done(tmp_path, provider)
    assert "caracteres de un turno" in capsys.readouterr().err
    assert go(entrada, tmp_path / "otra") == 0, "control positivo: sin la bajada se analiza"


@pytest.mark.parametrize(
    ("figure", "value"),
    [
        ("VERIDICUS_LIMIT_TRANSCRIPT_MAX_TURNS", "3"),
        ("VERIDICUS_LIMIT_TRANSCRIPT_MAX_CHARS", "50"),
    ],
)
def test_exit_2_for_the_other_lowered_transcription_figures(
    figure: str, value: str, tmp_path: Path
) -> None:
    provider = ScriptedProvider(echo_finding)

    code = go(
        write_input(tmp_path),
        tmp_path / "salida",
        environ=env(**{figure: value}),
        transport=provider,
    )

    assert code == 2
    _assert_nothing_was_done(tmp_path, provider)


@pytest.mark.parametrize(
    "argv",
    [
        [],
        ["no-existe"],
        ["analyze"],
        ["analyze", "x.json"],
        ["analyze", "x.json", "--perfil", PROFILE, "--opcion-que-no-existe"],
    ],
)
def test_exit_2_for_arguments_that_do_not_parse(argv: list[str], tmp_path: Path) -> None:
    provider = ScriptedProvider(echo_finding)

    assert run(argv, env(), transport=provider) == 2
    assert provider.request_count == 0


def test_help_ends_with_0_and_calls_nobody(capsys: pytest.CaptureFixture[str]) -> None:
    provider = ScriptedProvider(echo_finding)

    assert run(["--help"], env(), transport=provider) == 0
    assert "analyze" in capsys.readouterr().out
    assert provider.request_count == 0


def test_exit_2_when_the_output_directory_cannot_be_created(tmp_path: Path) -> None:
    blocker = tmp_path / "es-un-archivo"
    blocker.write_text("x", encoding="utf-8")
    provider = ScriptedProvider(echo_finding)

    code = go(write_input(tmp_path), blocker / "salida", transport=provider)

    assert code == 2
    assert provider.request_count == 0


# --- Código 3: perfil, anonimizador, clave, transferencia, aviso (BR11.2, BR10.1) ---------------------


def _without_key() -> dict[str, str]:
    return {name: value for name, value in env().items() if name != KEY_REF}


@pytest.mark.parametrize(
    ("environ", "perfil"),
    [
        (env(), "perfil-que-no-existe"),
        (_without_key(), PROFILE),
        (env(VERIDICUS_LIMIT_MODEL_CALL_TIMEOUT_S="269"), PROFILE),
        (env(VERIDICUS_LIMIT_MODEL_CALL_TIMEOUT_S="no-es-un-numero"), PROFILE),
        (env(VERIDICUS_LIMIT_TURN_MAX_CHARS="99999999"), PROFILE),
    ],
    ids=["perfil", "clave", "piso-270", "cifra-invalida", "techo-subido"],
)
def test_exit_3_for_a_configuration_that_does_not_allow_starting_with_no_calls_and_no_files(
    environ: dict[str, str], perfil: str, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    provider = ScriptedProvider(echo_finding)

    code = go(
        write_input(tmp_path),
        tmp_path / "salida",
        environ=environ,
        transport=provider,
        perfil=perfil,
    )

    assert code == 3
    _assert_nothing_was_done(tmp_path, provider)
    assert capsys.readouterr().err, "un mensaje en español nombra el ajuste"


def test_exit_3_when_the_consent_does_not_authorize_the_transfer_and_the_profile_is_external(
    tmp_path: Path,
) -> None:
    provider = ScriptedProvider(echo_finding)

    code = go(corpus_input(tmp_path, transfer=False), tmp_path / "salida", transport=provider)

    assert code == 3
    _assert_nothing_was_done(tmp_path, provider)


# --- Código 4: incidente de anonimización (BR11.3, CG-U11-13) -----------------------------------------


def test_exit_4_stops_the_batch_and_writes_only_the_error_output_of_the_incident(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def unanonymized(self: Anonymizer, request: GenerateRequest) -> GenerateResult:
        return GenerateResult(
            content={"hallazgos": []},
            altered_markers=[],
            call=make_call(request.role, anonymized=False),
        )

    monkeypatch.setattr(Anonymizer, "generate", unanonymized)
    entradas = tmp_path / "entradas"
    write_input(entradas, "SINT-0001.json")
    write_input(entradas, "SINT-0002.json")
    out = tmp_path / "salida"
    provider = ScriptedProvider(echo_finding)

    code = go(entradas, out, transport=provider)

    assert code == 4
    assert [path.name for path in files_under(out)] == ["AVISO.txt", "SINT-0001.salida.json"]
    assert json.loads((out / "SINT-0001.salida.json").read_text("utf-8"))["estado"] == "error"
    assert not (out / "reporte.json").exists(), "B11a no escribe reporte.json (CG-U11-13)"


# --- Código 5: error inesperado, escritura fallida e interrupción (BR11.3, BR11.4) --------------------


def test_exit_5_for_an_unexpected_error_and_stderr_names_only_its_class(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def boom(*args: object, **kwargs: object) -> Any:
        raise RuntimeError("detalle interno con Anselmo Quintanar")

    monkeypatch.setattr(cli_main, "analyze", boom)
    out = tmp_path / "salida"

    code = go(write_input(tmp_path), out)

    err = capsys.readouterr().err
    assert code == 5
    assert "RuntimeError" in err and "Anselmo Quintanar" not in err
    assert [path.name for path in files_under(out)] == ["AVISO.txt"], "ninguna salida parcial"


def test_exit_5_when_an_output_cannot_be_written(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def failing(path: Path, data: bytes) -> None:
        raise AtomicWriteError("sin espacio")

    monkeypatch.setattr(cli_main, "write_atomic", failing)

    assert go(write_input(tmp_path), tmp_path / "salida") == 5


class _SignalingProvider(ScriptedProvider):
    """Un proveedor que envía señales al proceso durante su primera llamada."""

    def __init__(self, *numbers: signal.Signals, at: int = 1) -> None:
        super().__init__(echo_finding)
        self._numbers = numbers
        self._at = at

    def _handle(self, request: httpx.Request) -> httpx.Response:
        response = super()._handle(request)
        if self.request_count == self._at:
            for number in self._numbers:
                signal.raise_signal(number)
        return response


@pytest.mark.parametrize("number", [signal.SIGINT, signal.SIGTERM])
def test_exit_5_when_interrupted_the_run_in_progress_has_no_output_and_no_more_calls(
    number: signal.Signals, tmp_path: Path
) -> None:
    provider = _SignalingProvider(number)
    out = tmp_path / "salida"
    before = signal.getsignal(number)

    code = go(write_input(tmp_path), out, transport=provider)

    assert code == 5
    assert provider.request_count == 1, "tras la señal no sale ninguna llamada más"
    assert [path.name for path in files_under(out)] == ["AVISO.txt"], "sin salida de esa corrida"
    assert signal.getsignal(number) is before, "los manejadores se restauran"


def test_exit_5_when_the_signal_arrives_after_the_last_call_of_the_last_run(
    tmp_path: Path,
) -> None:
    """F-05: una señal tras la última llamada también es una interrupción, no un código 0."""
    provider = _SignalingProvider(
        signal.SIGTERM, at=3
    )  # la tercera es la del verificador permutado

    code = go(write_input(tmp_path), tmp_path / "salida", transport=provider)

    assert code == 5
    assert provider.request_count == 3


def test_exit_5_when_a_second_signal_arrives_during_the_shutdown(tmp_path: Path) -> None:
    provider = _SignalingProvider(signal.SIGTERM, signal.SIGTERM)

    code = go(write_input(tmp_path), tmp_path / "salida", transport=provider)

    assert code == 5
    assert provider.request_count == 1
    assert not list((tmp_path / "salida").glob("*.salida.json"))
