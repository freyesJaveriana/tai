"""stderr, registros y `AVISO.txt` no llevan testimonio (BR11.7; AC11.3.5).

Un *canary* sembrado como nombre en un turno que ningún hallazgo cita no aparece en stderr, en los
registros, en `AVISO.txt` ni en las salidas de C6 (que solo llevan las citas verificadas). Vale en una
corrida buena y en cada fallo que la CLI informa. Con su control negativo: el mismo texto sí aparece
si una cita lo lleva.
"""

import logging
import string
from pathlib import Path

import pytest
from veridicus_anonymizer.testing.fake_transport import FakeResponse, FakeTransport

from tests.cli.helpers import files_under, go, write_input
from tests.support import (
    ScriptedProvider,
    anthropic_envelope,
    default_turns,
    env,
    finding,
)
from veridicus_incoherence_analyzer.cli import messages

pytestmark = pytest.mark.cli

CANARY = "Anselmo Quintanar-Zuluaga"


def _turns_with_the_canary() -> list[dict[str, object]]:
    turns: list[dict[str, object]] = [dict(turn) for turn in default_turns()]
    turns[2]["texto"] = f"Cuénteme de {CANARY}, por favor."
    return turns


def _everything_written(out: Path) -> str:
    return "\n".join(path.read_text("utf-8") for path in files_under(out))


def test_the_canary_is_in_no_message_log_notice_or_output_of_a_good_run(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)
    out = tmp_path / "salida"

    code = go(write_input(tmp_path, turnos=_turns_with_the_canary()), out)

    seen = capsys.readouterr()
    assert code == 0
    assert (out / "SINT-0001.salida.json").is_file(), "se analizó de verdad"
    assert CANARY not in seen.err and CANARY not in seen.out
    assert CANARY not in caplog.text
    assert CANARY not in _everything_written(out), "ni AVISO.txt ni la salida de C6"


def test_negative_control_the_canary_does_appear_when_a_verified_quote_carries_it(
    tmp_path: Path,
) -> None:
    quoted = f"Cuénteme de {CANARY}, por favor."
    turns = _turns_with_the_canary()
    provider = ScriptedProvider(
        lambda seen: [finding(a=(2, seen[2]), b=(3, seen[3]))]  # la cita B es el turno del canary
    )
    out = tmp_path / "salida"

    code = go(write_input(tmp_path, turnos=turns), out, transport=provider)

    written = (out / "SINT-0001.salida.json").read_text("utf-8")
    assert code == 0
    assert quoted in written or CANARY in written, "el archivo de C6 sí lleva sus citas"


def _repeated_number(tmp: Path) -> tuple[Path, dict[str, str]]:
    turns = _turns_with_the_canary()
    turns[3]["n"] = 3
    return write_input(tmp, turnos=turns), env()


def _over_the_lowered_limit(tmp: Path) -> tuple[Path, dict[str, str]]:
    return (
        write_input(tmp, turnos=_turns_with_the_canary()),
        env(VERIDICUS_LIMIT_TURN_MAX_CHARS="10"),
    )


def _corpus_without_consent(tmp: Path) -> tuple[Path, dict[str, str]]:
    return write_input(tmp, turnos=_turns_with_the_canary(), origen="corpus"), env()


@pytest.mark.parametrize(
    "build", [_repeated_number, _over_the_lowered_limit, _corpus_without_consent]
)
def test_the_canary_is_in_no_message_of_a_rejected_input(
    build: object, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    entrada, environ = build(tmp_path)  # type: ignore[operator]  # motivo: parametrizado

    code = go(entrada, tmp_path / "salida", environ=environ)

    seen = capsys.readouterr()
    assert code == 2
    assert seen.err, "hay un mensaje"
    assert CANARY not in seen.err and CANARY not in seen.out


def test_the_canary_is_in_no_message_when_the_provider_fails(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out = tmp_path / "salida"
    leaking = FakeResponse.ok_json(anthropic_envelope({"hallazgos": [], "nota": CANARY}))

    code = go(
        write_input(tmp_path, turnos=_turns_with_the_canary()),
        out,
        transport=FakeTransport(leaking, FakeResponse.not_json()),
    )

    seen = capsys.readouterr()
    assert code == 0
    assert CANARY not in seen.err and CANARY not in _everything_written(out)


# --- El catálogo es cerrado ---------------------------------------------------------------------------


def test_every_message_declares_exactly_the_fields_its_template_uses() -> None:
    formatter = string.Formatter()
    for key, template in messages.MESSAGES.items():
        used = {name for _, name, _, _ in formatter.parse(template) if name}
        assert used == set(messages.FIELDS.get(key, frozenset())), key


def test_no_declared_field_can_carry_testimony() -> None:
    allowed = {"path", "detail", "version", "text", "id", "kind"}
    declared = {name for fields in messages.FIELDS.values() for name in fields}

    assert declared <= allowed
    assert "turno" not in declared and "cita" not in declared and "entrevista" not in declared


def test_a_field_that_the_message_does_not_declare_is_rejected() -> None:
    with pytest.raises(KeyError):
        messages.render("run.written", path="x", cita="texto de un turno")
    with pytest.raises(KeyError):
        messages.render("run.written")


def test_the_warning_text_of_an_unknown_identifier_is_the_generic_one() -> None:
    assert "same_family" in messages.warning_text("same_family")
    assert messages.warning_text("otro_aviso") == "Aviso del perfil: otro_aviso."
    assert messages.warning_text("other") == "Aviso del perfil: other."


def test_a_long_detail_is_cut_to_one_line() -> None:
    text = messages.detail(ValueError("a\n" + "b" * 1000))

    assert "\n" not in text and len(text) <= messages.MAX_DETAIL
    assert messages.detail(ValueError("corto")) == "corto"
