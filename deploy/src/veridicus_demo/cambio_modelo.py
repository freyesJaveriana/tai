"""Comparador de la prueba de cambio de modelo (scripts/humano/cambio-modelo.sh).

Lee las salidas C6 que dejó la CLI `veridicus analyze` con dos perfiles distintos sobre el mismo
conjunto sintético (`evaluation/cambio-modelo/`) y las compara contra lo esperado de cada caso.
No llama a ningún modelo ni a la red: solo lee archivos.

Por cada corrida mide:

- citas comprobadas: cada cita de cada hallazgo se vuelve a buscar, literal, en el texto de su
  turno (solo se normalizan espacios; « […] » separa fragmentos del mismo turno en orden). Es una
  comprobación independiente de la de la CLI, no la sustituye.
- contradicciones detectadas: casos sembrados con al menos un hallazgo, con el tipo esperado y
  con el par de turnos esperado.
- hallazgos de más: hallazgos en un relato coherente o en un caso trampa.
- errores (`estado: error`), llamadas, tokens y, si se pasan, los segundos de la corrida.

El reporte JSON lleva solo identificadores, cifras y nombres de modelo: nunca texto del relato ni
de las citas. Los rótulos no llevan vocabulario de veracidad (AUTONOMIA-03).

Uso:
    python -m veridicus_demo.cambio_modelo --casos DIR --esperado ARCHIVO
        --corrida NOMBRE=DIR [--corrida NOMBRE=DIR ...] [--segundos NOMBRE=N ...]
        [--reporte ARCHIVO]

Código de salida: 0 si pudo comparar; 2 si los argumentos no sirven; 5 si falta o está dañado un
archivo de entrada, de lo esperado o de salida.
"""

import argparse
import json
import re
import sys
from collections.abc import Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Final, TextIO

EXIT_OK: Final = 0
EXIT_ARGS: Final = 2
EXIT_UNREADABLE: Final = 5

FRAGMENT_SEPARATOR: Final = re.compile(r"\s*\[…\]\s*")
CLASSES: Final = frozenset({"contradiccion", "coherente", "trampa"})


class Unreadable(Exception):
    """Un archivo falta o no tiene la forma esperada. El mensaje nunca lleva texto del relato."""


@dataclass(frozen=True)
class Expected:
    case: str
    kind: str
    tipo: str | None = None
    turns: frozenset[str] = frozenset()


@dataclass
class CaseResult:
    caso: str
    clase: str
    estado: str
    hallazgos: int = 0
    citas: int = 0
    citas_comprobadas: int = 0
    tipo_esperado: bool = False
    turnos_esperados: bool = False


@dataclass
class RunSummary:
    corrida: str
    modelos: list[str] = field(default_factory=list)
    casos: list[CaseResult] = field(default_factory=list)
    llamadas: int = 0
    tokens_entrada: int = 0
    tokens_salida: int = 0
    segundos: int | None = None

    def _of(self, kind: str) -> list[CaseResult]:
        return [case for case in self.casos if case.clase == kind and case.estado == "ok"]

    @property
    def errores(self) -> int:
        return sum(1 for case in self.casos if case.estado != "ok")

    @property
    def detectadas(self) -> int:
        return sum(1 for case in self._of("contradiccion") if case.hallazgos > 0)

    @property
    def con_tipo(self) -> int:
        return sum(1 for case in self._of("contradiccion") if case.tipo_esperado)

    @property
    def con_turnos(self) -> int:
        return sum(1 for case in self._of("contradiccion") if case.turnos_esperados)

    @property
    def hallazgos_de_mas(self) -> int:
        return sum(1 for case in self._of("coherente") + self._of("trampa") if case.hallazgos > 0)

    @property
    def citas(self) -> int:
        return sum(case.citas for case in self.casos)

    @property
    def citas_comprobadas(self) -> int:
        return sum(case.citas_comprobadas for case in self.casos)


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise Unreadable(f"No se pudo leer {path.name}.") from error


def load_expected(path: Path) -> list[Expected]:
    document = _load_json(path)
    cases = document.get("casos") if isinstance(document, dict) else None
    if not isinstance(cases, dict) or not cases:
        raise Unreadable(f"{path.name} no trae casos.")
    expected: list[Expected] = []
    for case, spec in sorted(cases.items()):
        kind = spec.get("clase") if isinstance(spec, dict) else None
        if kind not in CLASSES:
            raise Unreadable(f"El caso {case} no tiene una clase válida.")
        if kind == "contradiccion":
            tipo, turns = spec.get("tipo"), spec.get("turnos")
            if not isinstance(tipo, str) or not isinstance(turns, list) or len(turns) != 2:
                raise Unreadable(f"El caso {case} no trae su tipo y sus dos turnos.")
            expected.append(Expected(case, kind, tipo, frozenset(str(t) for t in turns)))
        else:
            expected.append(Expected(case, kind))
    return expected


def _normalize(text: str) -> str:
    return " ".join(text.split())


def load_turns(path: Path) -> dict[str, str]:
    """Los turnos de una entrada C6, como `T<n>` → texto con los espacios normalizados."""
    document = _load_json(path)
    turns = document.get("turnos") if isinstance(document, dict) else None
    if not isinstance(turns, list):
        raise Unreadable(f"{path.name} no trae turnos.")
    result: dict[str, str] = {}
    for turn in turns:
        if not isinstance(turn, dict) or not isinstance(turn.get("texto"), str):
            raise Unreadable(f"{path.name} tiene un turno sin texto.")
        result[f"T{turn.get('n')}"] = _normalize(turn["texto"])
    return result


def quote_found(quote: Any, turns: dict[str, str]) -> bool:
    """La cita está, literal y en orden, en el texto de su turno."""
    if not isinstance(quote, dict):
        return False
    text, turn = quote.get("cita"), quote.get("turno")
    if not isinstance(text, str) or not isinstance(turn, str) or turn not in turns:
        return False
    haystack, start = turns[turn], 0
    fragments = [_normalize(part) for part in FRAGMENT_SEPARATOR.split(text)]
    if not all(fragments):
        return False
    for fragment in fragments:
        position = haystack.find(fragment, start)
        if position < 0:
            return False
        start = position + len(fragment)
    return True


def evaluate_case(expected: Expected, turns: dict[str, str], output: Any) -> CaseResult:
    if not isinstance(output, dict) or output.get("estado") not in ("ok", "error"):
        raise Unreadable(f"La salida de {expected.case} no tiene la forma de C6.")
    result = CaseResult(caso=expected.case, clase=expected.kind, estado=output["estado"])
    if result.estado == "error":
        return result
    findings = output.get("hallazgos")
    if not isinstance(findings, list):
        raise Unreadable(f"La salida de {expected.case} no trae la lista de hallazgos.")
    result.hallazgos = len(findings)
    for finding in findings:
        if not isinstance(finding, dict):
            raise Unreadable(f"La salida de {expected.case} trae un hallazgo sin forma.")
        quotes = (finding.get("cita_a"), finding.get("cita_b"))
        result.citas += 2
        result.citas_comprobadas += sum(1 for quote in quotes if quote_found(quote, turns))
        if finding.get("tipo") == expected.tipo:
            result.tipo_esperado = True
        pair = {q.get("turno") for q in quotes if isinstance(q, dict)}
        if expected.turns and pair == expected.turns:
            result.turnos_esperados = True
    return result


def _calls(output: Any) -> list[dict[str, Any]]:
    registro = output.get("registro") if isinstance(output, dict) else None
    calls = registro.get("llamadas") if isinstance(registro, dict) else None
    return [call for call in calls if isinstance(call, dict)] if isinstance(calls, list) else []


def evaluate_run(
    name: str, cases_dir: Path, expected: list[Expected], output_dir: Path
) -> RunSummary:
    summary = RunSummary(corrida=name)
    models: set[str] = set()
    for item in expected:
        turns = load_turns(cases_dir / f"{item.case}.json")
        output = _load_json(output_dir / f"{item.case}.salida.json")
        summary.casos.append(evaluate_case(item, turns, output))
        for call in _calls(output):
            summary.llamadas += 1
            if isinstance(call.get("modelo"), str):
                models.add(call["modelo"])
            for key in ("tokens_entrada", "tokens_salida"):
                value = call.get(key)
                if isinstance(value, int):
                    setattr(summary, key, getattr(summary, key) + value)
    summary.modelos = sorted(models)
    return summary


def _percent(part: int, whole: int) -> str:
    return "—" if whole == 0 else f"{100 * part / whole:.0f} %"


def summary_rows(runs: list[RunSummary], expected: list[Expected]) -> list[tuple[str, list[str]]]:
    seeded = sum(1 for item in expected if item.kind == "contradiccion")
    others = len(expected) - seeded
    return [
        ("modelos", [", ".join(run.modelos) or "—" for run in runs]),
        (
            "citas comprobadas",
            [
                f"{r.citas_comprobadas}/{r.citas} ({_percent(r.citas_comprobadas, r.citas)})"
                for r in runs
            ],
        ),
        ("contradicciones detectadas", [f"{r.detectadas}/{seeded}" for r in runs]),
        ("con el tipo esperado", [f"{r.con_tipo}/{seeded}" for r in runs]),
        ("con los turnos esperados", [f"{r.con_turnos}/{seeded}" for r in runs]),
        (
            "hallazgos de más (coherentes y trampa)",
            [f"{r.hallazgos_de_mas}/{others}" for r in runs],
        ),
        ("errores", [f"{r.errores}/{len(expected)}" for r in runs]),
        ("llamadas", [str(r.llamadas) for r in runs]),
        ("tokens de entrada / salida", [f"{r.tokens_entrada} / {r.tokens_salida}" for r in runs]),
        ("segundos", ["—" if r.segundos is None else str(r.segundos) for r in runs]),
    ]


def render(runs: list[RunSummary], expected: list[Expected], out: TextIO) -> None:
    names = [run.corrida for run in runs]
    print("Por caso (hallazgos; * = tipo y turnos esperados):", file=out)
    print("caso\tclase\t" + "\t".join(names), file=out)
    for index, item in enumerate(expected):
        cells = []
        for run in runs:
            case = run.casos[index]
            if case.estado != "ok":
                cells.append("error")
            else:
                mark = "*" if case.tipo_esperado and case.turnos_esperados else ""
                cells.append(f"{case.hallazgos}{mark}")
        print(f"{item.case}\t{item.kind}\t" + "\t".join(cells), file=out)
    print(file=out)
    print("Resumen:", file=out)
    for label, values in summary_rows(runs, expected):
        print(f"{label}\t" + "\t".join(values), file=out)


def report(runs: list[RunSummary], expected: list[Expected]) -> dict[str, Any]:
    return {
        "version": "1.0.0",
        "casos": len(expected),
        "corridas": [
            {
                **{k: v for k, v in asdict(run).items() if k != "casos"},
                "casos": [asdict(case) for case in run.casos],
                "resumen": {label: values[0] for label, values in summary_rows([run], expected)},
            }
            for run in runs
        ],
    }


def _pairs(values: list[str], flag: str) -> dict[str, str]:
    pairs: dict[str, str] = {}
    for value in values:
        name, sep, rest = value.partition("=")
        if not sep or not re.fullmatch(r"[a-z0-9-]{1,48}", name) or not rest or name in pairs:
            raise ValueError(
                f"{flag} espera NOMBRE=VALOR con un nombre en minúsculas, sin repetir."
            )
        pairs[name] = rest
    return pairs


class _Parser(argparse.ArgumentParser):
    """Un error de argumentos se informa con el código 2 de este módulo, no con el de argparse."""

    def error(self, message: str) -> Any:
        raise ValueError(message)


def _parser() -> argparse.ArgumentParser:
    parser = _Parser(prog="cambio_modelo", add_help=False)
    parser.add_argument("--casos", required=True, type=Path)
    parser.add_argument("--esperado", required=True, type=Path)
    parser.add_argument("--corrida", action="append", required=True)
    parser.add_argument("--segundos", action="append", default=[])
    parser.add_argument("--reporte", type=Path)
    return parser


def main_with(argv: Sequence[str], out: TextIO) -> int:
    try:
        args = _parser().parse_args(list(argv))
        runs_spec = _pairs(args.corrida, "--corrida")
        seconds = {k: int(v) for k, v in _pairs(args.segundos, "--segundos").items()}
        if not set(seconds) <= set(runs_spec):
            raise ValueError("--segundos nombra una corrida que no existe.")
    except ValueError as error:
        print(f"Argumentos inválidos: {error}", file=out)
        return EXIT_ARGS
    try:
        expected = load_expected(args.esperado)
        runs = []
        for name, directory in runs_spec.items():
            run = evaluate_run(name, args.casos, expected, Path(directory))
            run.segundos = seconds.get(name)
            runs.append(run)
        render(runs, expected, out)
        if args.reporte is not None:
            args.reporte.write_text(
                json.dumps(report(runs, expected), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            print(f"\nReporte: {args.reporte}", file=out)
    except (Unreadable, OSError) as error:
        message = str(error) if isinstance(error, Unreadable) else "No se pudo escribir el reporte."
        print(message, file=out)
        return EXIT_UNREADABLE
    return EXIT_OK


def main() -> None:
    raise SystemExit(main_with(sys.argv[1:], sys.stdout))


if __name__ == "__main__":
    main()
