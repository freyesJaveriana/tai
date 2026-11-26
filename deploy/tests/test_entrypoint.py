"""Punto de entrada de la demo (CA-2): corre la CLI en proceso con el doble del proveedor.

La CLI y el `Anonymizer` son los reales; el proveedor es el `FakeTransport` de B10a (sin red,
`--disable-socket`). Donde la prueba necesita un código de salida que la CLI real no produce con
facilidad (4, o 0 sin archivo de salida), sustituye `run` por un doble que escribe lo que se pida.

Cubre AUTONOMIA-04 (sin clave o con el anonimizador caído, 0 llamadas), AUTONOMIA-05 (nunca un
resultado parcial) y AUTONOMIA-03 (los rótulos propios pasan el escáner de vocabulario).
"""

import io
import json
import os
import runpy
import sys
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from support import (
    HECHO,
    KEY_CANARY,
    KEY_REF,
    QUOTE_A,
    QUOTE_B,
    TURN_CANARY,
    env,
    finding,
    judge,
    stage_input,
    verdict,
)
from veridicus_anonymizer import api as anonymizer_api
from veridicus_anonymizer.application import generate as anonymizer_generate
from veridicus_anonymizer.domain.catalogs import CatalogError
from veridicus_anonymizer.testing.fake_transport import FakeTransport
from veridicus_integrity_policy.scan import scan

from veridicus_demo import entrypoint


def _run(
    entrada: Path,
    salida: Path,
    transport: Any,
    *,
    extra: Mapping[str, str] | None = None,
    drop: str | None = None,
) -> tuple[int, str]:
    environ = env(entrada, salida, **(extra or {}))
    if drop is not None:
        del environ[drop]
    buffer = io.StringIO()
    code = entrypoint.main_with([], environ, transport=transport, stdout=buffer)
    return code, buffer.getvalue()


def _fake_run(
    code: int, files: Mapping[str, Any] | None = None, raw: Mapping[str, str] | None = None
) -> Callable[..., int]:
    """Un doble de `run`: escribe `<nombre>.salida.json` en `--salida` y devuelve `code`."""

    def fake(argv: Sequence[str], environ: Mapping[str, str], *, transport: Any = None) -> int:
        directory = Path(argv[list(argv).index("--salida") + 1])
        directory.mkdir(parents=True, exist_ok=True)
        for name, document in (files or {}).items():
            (directory / f"{name}.salida.json").write_text(json.dumps(document), encoding="utf-8")
        for name, text in (raw or {}).items():
            (directory / f"{name}.salida.json").write_text(text, encoding="utf-8")
        return code

    return fake


def _salida(estado: str = "ok", hallazgos: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {"estado": estado, "hallazgos": hallazgos or []}


def _hallazgo(quote_a: str = QUOTE_A, quote_b: str = QUOTE_B, hecho: str = HECHO) -> dict[str, Any]:
    return {
        "id": "X-C01",
        "hecho": hecho,
        "tipo": "lugar",
        "cita_a": {"cita": quote_a, "turno": "T4"},
        "cita_b": {"cita": quote_b, "turno": "T10"},
        "observaciones": "Sin juicio sobre la persona.",
    }


# --- CA-2: la corrida con el doble del proveedor ---------------------------------------------------


def test_a_scripted_finding_over_the_seeded_contradiction_prints_its_fact_type_and_two_quotes(
    tmp_path: Path,
) -> None:
    entrada = stage_input(tmp_path, "contradiccion")
    transport = FakeTransport(judge(finding()), verdict(), verdict())

    code, out = _run(entrada, tmp_path / "salida", transport)

    assert code == 0
    assert transport.request_count == 3, "juez, verificador y verificador permutado"
    assert "contradiccion: estado=ok, 1 hallazgo\n" in out, "F-05: singular con un hallazgo"
    assert "1 hallazgos" not in out
    assert f"hecho: {HECHO}" in out
    assert "tipo: lugar" in out
    assert f"cita A (turno T4): «{QUOTE_A}»" in out
    assert f"cita B (turno T10): «{QUOTE_B}»" in out


def test_a_coherent_account_with_no_findings_prints_zero_findings(tmp_path: Path) -> None:
    entrada = stage_input(tmp_path, "coherente")
    transport = FakeTransport(judge())

    code, out = _run(entrada, tmp_path / "salida", transport)

    assert code == 0
    assert transport.request_count == 1, "sin candidatos no hay verificador"
    assert "coherente: estado=ok, 0 hallazgos" in out
    assert "hecho:" not in out and "cita A" not in out


def test_two_inputs_are_reported_in_name_order(tmp_path: Path) -> None:
    entrada = stage_input(tmp_path, "contradiccion", "coherente")
    transport = FakeTransport(judge(), judge())

    code, out = _run(entrada, tmp_path / "salida", transport)

    assert code == 0
    assert out.index("coherente: estado=ok") < out.index("contradiccion: estado=ok")


# --- AUTONOMIA-04: sin clave o con el anonimizador caído no sale ninguna llamada --------------------


def test_without_the_api_key_the_code_is_3_no_call_leaves_and_no_findings_are_printed(
    tmp_path: Path,
) -> None:
    entrada = stage_input(tmp_path, "contradiccion")
    transport = FakeTransport(judge(finding()), verdict(), verdict())

    code, out = _run(entrada, tmp_path / "salida", transport, drop=KEY_REF)

    assert code == 3
    assert transport.request_count == 0
    assert "hecho:" not in out and "cita A" not in out
    assert out.strip() == entrypoint.CLI_FAILED_MESSAGE.format(code=3)


def test_with_the_anonymizer_failing_while_pseudonymizing_nothing_leaves_and_the_code_is_not_0(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def boom(*args: object, **kwargs: object) -> Any:
        raise RuntimeError("fallo sintetico")

    monkeypatch.setattr(anonymizer_generate, "pseudonymize", boom)
    entrada = stage_input(tmp_path, "contradiccion")
    transport = FakeTransport(judge(finding()), verdict(), verdict())

    code, out = _run(entrada, tmp_path / "salida", transport)

    assert code != 0
    assert transport.request_count == 0
    assert "hecho:" not in out and "cita A" not in out
    assert "contradiccion: estado=error, 0 hallazgos" in out


def test_with_an_anonymizer_that_cannot_be_built_the_code_is_3_and_no_call_leaves(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def broken(*args: object, **kwargs: object) -> Any:
        raise CatalogError("catálogo inválido")

    monkeypatch.setattr(anonymizer_api, "load_catalogs", broken)
    entrada = stage_input(tmp_path, "contradiccion")
    transport = FakeTransport(judge(finding()), verdict(), verdict())

    code, out = _run(entrada, tmp_path / "salida", transport)

    assert code == 3
    assert transport.request_count == 0
    assert "hecho:" not in out


def test_the_run_ends_without_findings_when_the_cli_does_not_give_0(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = _fake_run(2, {"contradiccion": _salida("ok", [_hallazgo()])})
    monkeypatch.setattr(entrypoint, "run", fake)
    entrada = stage_input(tmp_path, "contradiccion")

    code, out = _run(entrada, tmp_path / "salida", None)

    assert code == 2
    assert "hecho:" not in out and "cita A" not in out and "contradiccion" not in out


# --- Caso sonda 5 y AUTONOMIA-03: los rótulos propios pasan el escáner --------------------------------


def test_the_labels_the_entrypoint_adds_pass_the_forbidden_vocabulary_scan(
    tmp_path: Path,
) -> None:
    entrada = stage_input(tmp_path, "contradiccion")
    transport = FakeTransport(judge(finding()), verdict(), verdict())

    _, out = _run(entrada, tmp_path / "salida", transport)

    assert scan(out, [QUOTE_A, QUOTE_B]) == []
    assert scan("el testigo miente sobre el hecho", []) != [], "control negativo: el escáner mira"


@pytest.mark.parametrize(
    "message",
    [
        pytest.param(entrypoint.ARGS_MESSAGE, id="args"),
        pytest.param(entrypoint.CLI_FAILED_MESSAGE.format(code=4), id="cli-failed"),
        pytest.param(entrypoint.NO_OUTPUT_MESSAGE, id="no-output"),
        pytest.param(entrypoint.UNEXPECTED_MESSAGE.format(kind="RuntimeError"), id="unexpected"),
    ],
)
def test_each_fixed_message_passes_the_forbidden_vocabulary_scan(message: str) -> None:
    """F-03: los cuatro mensajes fijos, no solo los rótulos de la corrida feliz."""
    assert scan(message, []) == []


@pytest.mark.parametrize("count", [0, 1, 2, 5])
def test_every_label_line_passes_the_scan_for_any_number_of_findings(
    count: int, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """F-03: todos los rótulos (estado, hallazgos, hecho, tipo, cita A, cita B) con 0, 1 y varios."""
    salida = _salida("ok", [_hallazgo(quote_a="Una cita.", quote_b="Otra cita.") for _ in range(count)])
    monkeypatch.setattr(entrypoint, "run", _fake_run(0, {"contradiccion": salida}))
    entrada = stage_input(tmp_path, "contradiccion")

    code, out = _run(entrada, tmp_path / "salida", None)

    assert code == 0
    assert scan(out, ["Una cita.", "Otra cita.", HECHO]) == []


@pytest.mark.parametrize(
    "count, expected",
    [(0, "0 hallazgos"), (1, "1 hallazgo"), (2, "2 hallazgos"), (11, "11 hallazgos")],
)
def test_the_count_agrees_in_singular_and_plural(
    count: int, expected: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """F-05: «1 hallazgo» y «N hallazgos»; es texto que ve el público de la demo."""
    salida = _salida("ok", [_hallazgo() for _ in range(count)])
    monkeypatch.setattr(entrypoint, "run", _fake_run(0, {"contradiccion": salida}))
    entrada = stage_input(tmp_path, "contradiccion")

    _, out = _run(entrada, tmp_path / "salida", None)

    first_line = out.splitlines()[0]
    assert first_line == f"contradiccion: estado=ok, {expected}"


def test_the_test_environment_never_carries_the_real_provider_key() -> None:
    """F-04: un conftest autouse la retira de `os.environ` en cada prueba."""
    assert KEY_REF not in os.environ


# --- Secretos: ni la clave ni un turno que no es cita salen en stdout ni en stderr --------------------


def test_neither_the_key_nor_a_non_quoted_turn_appears_in_stdout_or_stderr(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    entrada = stage_input(tmp_path, "contradiccion")
    path = entrada / "contradiccion.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    document["turnos"][5]["texto"] = f"Recuerdo la tienda cerrada. {TURN_CANARY}"
    path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
    transport = FakeTransport(judge(finding()), verdict(), verdict())

    code, out = _run(entrada, tmp_path / "salida", transport)

    seen = capsys.readouterr()
    assert code == 0
    assert "hecho:" in out, "la corrida produjo salida que revisar"
    for stream in (out, seen.out, seen.err):
        assert KEY_CANARY not in stream
        assert TURN_CANARY not in stream


# --- Caso sonda 1: una excepción inesperada no filtra el entorno ni la clave ---------------------------


def test_an_unexpected_exception_prints_a_fixed_message_without_the_key_or_the_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def explodes(argv: Sequence[str], environ: Mapping[str, str], **kwargs: Any) -> int:
        raise RuntimeError(f"fallo con {dict(environ)} y {KEY_CANARY}")

    monkeypatch.setattr(entrypoint, "run", explodes)
    entrada = stage_input(tmp_path, "contradiccion")

    code, out = _run(entrada, tmp_path / "salida", None)

    seen = capsys.readouterr()
    assert code == 5
    for stream in (out, seen.out, seen.err):
        assert KEY_CANARY not in stream
        assert "VERIDICUS_ANTHROPIC_API_KEY" not in stream
    assert out.strip() == entrypoint.UNEXPECTED_MESSAGE.format(kind="RuntimeError")


# --- Caso sonda 2: salida parcial (AUTONOMIA-05) ----------------------------------------------------


def test_with_exit_4_it_prints_the_error_state_and_no_findings_of_that_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    poisoned = _salida("error", [_hallazgo(hecho="HECHO-ENVENENADO")])
    monkeypatch.setattr(entrypoint, "run", _fake_run(4, {"contradiccion": poisoned}))
    entrada = stage_input(tmp_path, "contradiccion")

    code, out = _run(entrada, tmp_path / "salida", None)

    assert code == 4
    assert "contradiccion: estado=error, 0 hallazgos" in out
    assert "HECHO-ENVENENADO" not in out
    assert "cita A" not in out and "cita B" not in out


def test_with_exit_0_but_a_file_in_error_state_the_code_is_4_and_no_findings_are_printed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    poisoned = _salida("error", [_hallazgo(hecho="HECHO-ENVENENADO")])
    monkeypatch.setattr(entrypoint, "run", _fake_run(0, {"contradiccion": poisoned}))
    entrada = stage_input(tmp_path, "contradiccion")

    code, out = _run(entrada, tmp_path / "salida", None)

    assert code == 4
    assert "contradiccion: estado=error, 0 hallazgos" in out
    assert "HECHO-ENVENENADO" not in out


# --- Caso sonda 3: archivo de salida que falta o está corrupto -------------------------------------------


@pytest.mark.parametrize(
    "raw",
    [
        pytest.param(None, id="falta"),
        pytest.param("{no es json", id="no-es-json"),
        pytest.param("[1, 2]", id="no-es-objeto"),
        pytest.param('{"estado": "ok"}', id="sin-hallazgos"),
        pytest.param('{"estado": "otro", "hallazgos": []}', id="estado-desconocido"),
        pytest.param('{"estado": "ok", "hallazgos": [{"hecho": "x"}]}', id="hallazgo-incompleto"),
    ],
)
def test_a_missing_or_corrupt_output_file_ends_non_zero_with_a_fixed_message(
    raw: str | None, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        entrypoint, "run", _fake_run(0, raw={} if raw is None else {"contradiccion": raw})
    )
    entrada = stage_input(tmp_path, "contradiccion")
    path = entrada / "contradiccion.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    document["turnos"][5]["texto"] = TURN_CANARY
    path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")

    code, out = _run(entrada, tmp_path / "salida", None)

    assert code == 5
    assert out.strip() == entrypoint.NO_OUTPUT_MESSAGE
    assert TURN_CANARY not in out, "no se lee ni se imprime la entrada"


def test_an_empty_input_directory_with_exit_0_is_a_failure_with_the_fixed_message(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(entrypoint, "run", _fake_run(0))
    entrada = tmp_path / "entrada"
    entrada.mkdir()

    code, out = _run(entrada, tmp_path / "salida", None)

    assert code == 5
    assert out.strip() == entrypoint.NO_OUTPUT_MESSAGE


@pytest.mark.parametrize(
    "files, raw",
    [
        pytest.param({}, {"contradiccion": "{dañado"}, id="salida-dañada"),
        pytest.param({"contradiccion": _salida("ok")}, {}, id="salida-en-ok"),
    ],
)
def test_with_exit_4_only_files_read_in_error_state_are_listed(
    files: dict[str, Any], raw: dict[str, str], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(entrypoint, "run", _fake_run(4, files, raw))
    entrada = stage_input(tmp_path, "contradiccion")

    code, out = _run(entrada, tmp_path / "salida", None)

    assert code == 4
    assert out.strip() == entrypoint.CLI_FAILED_MESSAGE.format(code=4)


def test_one_missing_output_among_two_inputs_is_a_failure_and_prints_no_findings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        entrypoint, "run", _fake_run(0, {"coherente": _salida("ok", [_hallazgo()])})
    )
    entrada = stage_input(tmp_path, "contradiccion", "coherente")

    code, out = _run(entrada, tmp_path / "salida", None)

    assert code == 5
    assert out.strip() == entrypoint.NO_OUTPUT_MESSAGE


# --- Caso sonda 4: no revalida ni recorta citas --------------------------------------------------------


def test_a_quote_that_is_not_in_the_transcript_is_printed_as_the_cli_gave_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    outside = "Esta cita no está en ninguna transcripción de la demo."
    salida = _salida("ok", [_hallazgo(quote_a=outside)])
    monkeypatch.setattr(entrypoint, "run", _fake_run(0, {"contradiccion": salida}))
    entrada = stage_input(tmp_path, "contradiccion")

    code, out = _run(entrada, tmp_path / "salida", None)

    assert code == 0
    assert f"cita A (turno T4): «{outside}»" in out, "la verificación es de la CLI, no de la demo"


# --- Rutas, argumentos y `main` ----------------------------------------------------------------------


def test_the_default_paths_are_entrada_and_salida_at_the_root(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: list[list[str]] = []

    def capture(argv: Sequence[str], environ: Mapping[str, str], **kwargs: Any) -> int:
        seen.append(list(argv))
        return 2

    monkeypatch.setattr(entrypoint, "run", capture)
    buffer = io.StringIO()

    code = entrypoint.main_with([], {}, stdout=buffer)

    assert code == 2
    assert seen == [
        ["analyze", "/entrada", "--perfil", "demo-anthropic", "--salida", "/salida"],
    ]


def test_arguments_are_rejected_with_code_2_before_any_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def never(*args: object, **kwargs: object) -> int:
        raise AssertionError("no debe correr la CLI")

    monkeypatch.setattr(entrypoint, "run", never)
    buffer = io.StringIO()

    code = entrypoint.main_with(["--perfil", "otro"], {}, stdout=buffer)

    assert code == 2
    assert buffer.getvalue().strip() == entrypoint.ARGS_MESSAGE


def test_main_passes_argv_and_environ_and_exits_with_its_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[Sequence[str], Mapping[str, str]]] = []

    def fake(argv: Sequence[str], environ: Mapping[str, str], **kwargs: Any) -> int:
        calls.append((argv, environ))
        return 7

    monkeypatch.setattr(entrypoint, "main_with", fake)
    monkeypatch.setattr(sys, "argv", ["entrypoint"])
    monkeypatch.setattr(entrypoint, "os", SimpleNamespace(environ={"A": "1"}))

    with pytest.raises(SystemExit) as stop:
        entrypoint.main()

    assert stop.value.code == 7
    assert calls == [([], {"A": "1"})]


def test_running_the_module_as_main_exits_with_the_cli_code(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """`python -m veridicus_demo.entrypoint` es el ENTRYPOINT de la imagen: sin entrada, código 2."""
    monkeypatch.delenv(KEY_REF, raising=False)  # F-04: ni la clave real del contenedor
    monkeypatch.setenv("VERIDICUS_DEMO_ENTRADA", str(tmp_path / "no-existe"))
    monkeypatch.setenv("VERIDICUS_DEMO_SALIDA", str(tmp_path / "salida"))
    monkeypatch.setattr(sys, "argv", ["entrypoint"])
    monkeypatch.delitem(sys.modules, "veridicus_demo.entrypoint")

    with pytest.raises(SystemExit) as stop:
        runpy.run_module("veridicus_demo.entrypoint", run_name="__main__")

    assert stop.value.code == 2
    assert entrypoint.CLI_FAILED_MESSAGE.format(code=2) in capsys.readouterr().out


def test_stdout_defaults_to_sys_stdout(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(entrypoint, "run", lambda argv, environ, **kw: 2)

    code = entrypoint.main_with([], {})

    assert code == 2
    assert entrypoint.CLI_FAILED_MESSAGE.format(code=2) in capsys.readouterr().out
