"""Comparador de la prueba de cambio de modelo y su conjunto sintético.

No llama a ningún modelo: las salidas C6 se arman en memoria. Cada regla lleva su control
negativo (una salida o un archivo con un único defecto).
"""

import io
import json
import runpy
import sys
from pathlib import Path
from typing import Any

import pytest
from support import DEPLOY

from veridicus_demo import cambio_modelo as cm

ROOT = DEPLOY.parent
EVAL = ROOT / "evaluation" / "cambio-modelo"
CASES = EVAL / "casos"
EXPECTED = EVAL / "esperado.json"
TYPES = {"fecha", "numero", "lugar", "persona", "negacion", "secuencia", "otro"}
FORBIDDEN = ("miente", "mentir", "falso", "falsa", "verdader", "veracidad")


# --- El conjunto sintético ---------------------------------------------------------------------


def test_the_set_has_at_least_ten_cases_one_per_type_and_coherent_and_trap_cases() -> None:
    expected = cm.load_expected(EXPECTED)

    assert len(expected) >= 10
    kinds = [item.kind for item in expected]
    assert kinds.count("coherente") >= 3
    assert kinds.count("trampa") >= 2
    assert {item.tipo for item in expected if item.kind == "contradiccion"} == TYPES


def test_every_case_file_is_synthetic_c6_input_and_matches_the_expected_list() -> None:
    expected = {item.case: item for item in cm.load_expected(EXPECTED)}
    files = sorted(CASES.glob("*.json"))

    assert [path.stem for path in files] == sorted(expected)
    for path in files:
        document = json.loads(path.read_text(encoding="utf-8"))
        assert document["entrevista"] == path.stem
        assert document["origen"] == "sintetico"
        numbers = [turn["n"] for turn in document["turnos"]]
        assert numbers == list(range(1, len(numbers) + 1))
        assert {turn["hablante"] for turn in document["turnos"]} == {"ENT", "TEST"}
        turns = cm.load_turns(path)
        assert expected[path.stem].turns <= set(turns), path.stem


def test_the_seeded_turns_are_testimony_turns() -> None:
    for item in cm.load_expected(EXPECTED):
        document = json.loads((CASES / f"{item.case}.json").read_text(encoding="utf-8"))
        speakers = {f"T{turn['n']}": turn["hablante"] for turn in document["turnos"]}
        assert all(speakers[turn] == "TEST" for turn in item.turns), item.case


def test_the_set_and_its_guide_carry_no_veracity_vocabulary() -> None:
    texts = [path.read_text(encoding="utf-8").lower() for path in sorted(EVAL.rglob("*.*"))]

    for text in texts:
        assert not any(word in text for word in FORBIDDEN)


# --- Ayudantes -------------------------------------------------------------------------------


def _quote(turn: str, text: str) -> dict[str, Any]:
    return {"turno": turn, "cita": text}


def _finding(tipo: str, a: Any, b: Any) -> dict[str, Any]:
    return {"hecho": "h", "tipo": tipo, "cita_a": a, "cita_b": b, "observaciones": "o"}


def _output(findings: list[Any] | None = None, *, estado: str = "ok", calls: Any = None) -> Any:
    registro: dict[str, Any] = {"llamadas": calls if calls is not None else []}
    return {"estado": estado, "hallazgos": findings or [], "registro": registro}


def _call(model: str = "m-1", tin: Any = 10, tout: Any = 2) -> dict[str, Any]:
    return {"papel": "juez", "modelo": model, "tokens_entrada": tin, "tokens_salida": tout}


TURNS = {"T2": "llegaron un martes de marzo", "T8": "fue en diciembre, en plena novena"}
SEEDED = cm.Expected("SINT-X-01", "contradiccion", "fecha", frozenset({"T2", "T8"}))
COHERENT = cm.Expected("SINT-X-02", "coherente")


def _write(path: Path, data: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data if isinstance(data, str) else json.dumps(data), encoding="utf-8")
    return path


def _workspace(tmp_path: Path, outputs: dict[str, dict[str, Any]]) -> dict[str, Path]:
    """Un conjunto de dos casos con sus entradas, lo esperado y una carpeta por corrida."""
    cases = tmp_path / "casos"
    for case in ("SINT-X-01", "SINT-X-02"):
        _write(
            cases / f"{case}.json",
            {"turnos": [{"n": 2, "texto": TURNS["T2"]}, {"n": 8, "texto": TURNS["T8"]}]},
        )
    expected = _write(
        tmp_path / "esperado.json",
        {
            "casos": {
                "SINT-X-01": {"clase": "contradiccion", "tipo": "fecha", "turnos": ["T2", "T8"]},
                "SINT-X-02": {"clase": "coherente"},
            }
        },
    )
    paths = {"casos": cases, "esperado": expected}
    for run, by_case in outputs.items():
        for case, output in by_case.items():
            _write(tmp_path / run / f"{case}.salida.json", output)
        paths[run] = tmp_path / run
    return paths


GOOD = _finding("fecha", _quote("T2", "un martes de marzo"), _quote("T8", "en diciembre"))


# --- Comprobación de citas -------------------------------------------------------------------


def test_a_literal_quote_and_fragments_in_order_are_found() -> None:
    assert cm.quote_found(_quote("T2", "un   martes de marzo"), TURNS)
    assert cm.quote_found(_quote("T8", "fue en diciembre […] novena"), TURNS)


@pytest.mark.parametrize(
    "quote",
    [
        "no es un objeto",
        {"turno": "T2"},
        {"turno": 2, "cita": "martes"},
        _quote("T9", "martes"),
        _quote("T2", "un martes de abril"),
        _quote("T8", "novena […] fue en diciembre"),
        _quote("T8", "[…] novena"),
        _quote("T8", "martes"),
    ],
)
def test_negative_an_altered_misplaced_or_shapeless_quote_is_not_found(quote: Any) -> None:
    assert not cm.quote_found(quote, TURNS)


# --- Un caso ----------------------------------------------------------------------------------


def test_a_seeded_case_with_the_expected_type_and_turns_counts_fully() -> None:
    result = cm.evaluate_case(SEEDED, TURNS, _output([GOOD]))

    assert (result.hallazgos, result.citas, result.citas_comprobadas) == (1, 2, 2)
    assert result.tipo_esperado and result.turnos_esperados


def test_negative_another_type_or_another_turn_pair_does_not_count() -> None:
    other = _finding("lugar", _quote("T2", "un martes"), "sin forma")
    result = cm.evaluate_case(SEEDED, TURNS, _output([other]))

    assert (result.citas, result.citas_comprobadas) == (2, 1)
    assert not result.tipo_esperado and not result.turnos_esperados


def test_a_coherent_case_never_matches_turns_even_with_a_finding() -> None:
    result = cm.evaluate_case(COHERENT, TURNS, _output([GOOD]))

    assert result.hallazgos == 1
    assert not result.turnos_esperados


def test_an_error_output_counts_as_an_error_without_findings() -> None:
    result = cm.evaluate_case(SEEDED, TURNS, {"estado": "error", "hallazgos": [GOOD]})

    assert result.estado == "error"
    assert result.hallazgos == 0


@pytest.mark.parametrize(
    "output",
    [
        [],
        {"estado": "parcial"},
        {"estado": "ok", "hallazgos": "no"},
        {"estado": "ok", "hallazgos": ["no"]},
    ],
)
def test_negative_an_output_without_the_c6_shape_is_unreadable(output: Any) -> None:
    with pytest.raises(cm.Unreadable):
        cm.evaluate_case(SEEDED, TURNS, output)


# --- Lo esperado y las entradas --------------------------------------------------------------


@pytest.mark.parametrize(
    "document",
    [
        "no es JSON",
        [],
        {"casos": {}},
        {"casos": {"A": "x"}},
        {"casos": {"A": {"clase": "otra"}}},
        {"casos": {"A": {"clase": "contradiccion", "turnos": ["T1", "T2"]}}},
        {"casos": {"A": {"clase": "contradiccion", "tipo": "fecha", "turnos": "T1"}}},
        {"casos": {"A": {"clase": "contradiccion", "tipo": "fecha", "turnos": ["T1"]}}},
    ],
)
def test_negative_an_expected_file_with_one_defect_is_unreadable(
    tmp_path: Path, document: Any
) -> None:
    with pytest.raises(cm.Unreadable):
        cm.load_expected(_write(tmp_path / "e.json", document))


def test_negative_a_missing_file_is_unreadable(tmp_path: Path) -> None:
    with pytest.raises(cm.Unreadable):
        cm.load_expected(tmp_path / "no-existe.json")


@pytest.mark.parametrize(
    "document", [[], {"turnos": "x"}, {"turnos": ["x"]}, {"turnos": [{"n": 1, "texto": 3}]}]
)
def test_negative_an_input_with_one_defect_is_unreadable(tmp_path: Path, document: Any) -> None:
    with pytest.raises(cm.Unreadable):
        cm.load_turns(_write(tmp_path / "c.json", document))


# --- Una corrida y el resumen ----------------------------------------------------------------


def test_a_run_sums_calls_tokens_and_models_and_ignores_shapeless_entries(tmp_path: Path) -> None:
    calls = [_call("m-1"), _call("m-2", 5, 1), _call(None, "x", None), "no"]  # type: ignore[arg-type]
    paths = _workspace(
        tmp_path,
        {
            "a": {
                "SINT-X-01": _output([GOOD], calls=calls),
                "SINT-X-02": {"estado": "ok", "hallazgos": [], "registro": "no"},
            }
        },
    )
    expected = cm.load_expected(paths["esperado"])

    run = cm.evaluate_run("a", paths["casos"], expected, paths["a"])

    assert run.modelos == ["m-1", "m-2"]
    assert (run.llamadas, run.tokens_entrada, run.tokens_salida) == (3, 15, 3)
    assert (run.detectadas, run.con_tipo, run.con_turnos, run.hallazgos_de_mas) == (1, 1, 1, 0)
    assert (run.citas, run.citas_comprobadas, run.errores) == (2, 2, 0)


def test_summary_rows_show_dashes_when_there_is_nothing_to_count() -> None:
    run = cm.RunSummary(corrida="vacia")

    rows = dict(cm.summary_rows([run], [COHERENT]))

    assert rows["modelos"] == ["—"]
    assert rows["citas comprobadas"] == ["0/0 (—)"]
    assert rows["segundos"] == ["—"]


# --- La línea de comandos --------------------------------------------------------------------


def _argv(paths: dict[str, Path], *extra: str) -> list[str]:
    return ["--casos", str(paths["casos"]), "--esperado", str(paths["esperado"]), *extra]


def test_two_runs_are_compared_and_the_report_holds_no_quote_text(tmp_path: Path) -> None:
    paths = _workspace(
        tmp_path,
        {
            "sonnet": {"SINT-X-01": _output([GOOD], calls=[_call("s")]), "SINT-X-02": _output()},
            "opus": {
                "SINT-X-01": {"estado": "error", "hallazgos": []},
                "SINT-X-02": _output([GOOD], calls=[_call("o")]),
            },
        },
    )
    out = io.StringIO()
    reporte = tmp_path / "reporte.json"

    code = cm.main_with(
        _argv(
            paths,
            "--corrida",
            f"sonnet={paths['sonnet']}",
            "--corrida",
            f"opus={paths['opus']}",
            "--segundos",
            "sonnet=12",
            "--reporte",
            str(reporte),
        ),
        out,
    )

    text = out.getvalue()
    assert code == cm.EXIT_OK
    assert "SINT-X-01\tcontradiccion\t1*\terror" in text
    assert "SINT-X-02\tcoherente\t0\t1" in text
    assert "hallazgos de más (coherentes y trampa)\t0/1\t1/1" in text
    assert "segundos\t12\t—" in text
    data = json.loads(reporte.read_text(encoding="utf-8"))
    assert [run["corrida"] for run in data["corridas"]] == ["sonnet", "opus"]
    assert data["corridas"][0]["resumen"]["contradicciones detectadas"] == "1/1"
    raw = reporte.read_text(encoding="utf-8")
    assert "martes" not in raw and "diciembre" not in raw


def test_without_a_report_flag_only_the_table_is_printed(tmp_path: Path) -> None:
    paths = _workspace(tmp_path, {"a": {"SINT-X-01": _output(), "SINT-X-02": _output()}})
    out = io.StringIO()

    assert cm.main_with(_argv(paths, "--corrida", f"a={paths['a']}"), out) == cm.EXIT_OK
    assert "Reporte:" not in out.getvalue()


@pytest.mark.parametrize(
    "extra",
    [
        [],
        ["--corrida", "sin-igual"],
        ["--corrida", "MAYUS=dir"],
        ["--corrida", "a="],
        ["--corrida", "a=x", "--corrida", "a=y"],
        ["--corrida", "a=x", "--segundos", "a=diez"],
        ["--corrida", "a=x", "--segundos", "b=3"],
        ["--corrida", "a=x", "--desconocido"],
    ],
)
def test_negative_bad_arguments_exit_with_two(tmp_path: Path, extra: list[str]) -> None:
    paths = _workspace(tmp_path, {})
    out = io.StringIO()

    assert cm.main_with(_argv(paths, *extra), out) == cm.EXIT_ARGS
    assert out.getvalue().startswith("Argumentos inválidos:")


def test_negative_a_missing_output_exits_with_five_and_names_only_the_file(tmp_path: Path) -> None:
    paths = _workspace(tmp_path, {"a": {"SINT-X-01": _output()}})
    out = io.StringIO()

    assert cm.main_with(_argv(paths, "--corrida", f"a={paths['a']}"), out) == cm.EXIT_UNREADABLE
    assert out.getvalue().strip() == "No se pudo leer SINT-X-02.salida.json."


def test_negative_a_report_that_cannot_be_written_exits_with_five(tmp_path: Path) -> None:
    paths = _workspace(tmp_path, {"a": {"SINT-X-01": _output(), "SINT-X-02": _output()}})
    out = io.StringIO()
    blocked = tmp_path / "no-existe" / "reporte.json"

    code = cm.main_with(
        _argv(paths, "--corrida", f"a={paths['a']}", "--reporte", str(blocked)), out
    )

    assert code == cm.EXIT_UNREADABLE
    assert out.getvalue().strip().endswith("No se pudo escribir el reporte.")


def test_the_module_runs_as_a_script_and_exits_with_its_code(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "argv", ["cambio_modelo"])

    with pytest.raises(SystemExit) as stop:
        runpy.run_module("veridicus_demo.cambio_modelo", run_name="__main__")

    assert stop.value.code == cm.EXIT_ARGS
    assert "Argumentos inválidos" in capsys.readouterr().out
