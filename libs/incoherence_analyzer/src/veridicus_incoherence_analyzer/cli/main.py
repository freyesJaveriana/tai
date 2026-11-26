"""CLI `veridicus analyze` (F9, BR9.5, BR11.1 a BR11.7; PD-2, PD-12).

`main()` llama a `run(sys.argv[1:], os.environ)`. `run(argv, env, *, transport=None)` es la única
entrada que usan las pruebas, y `transport` solo llega a `build_anonymizer(env, transport)` por la raíz
de composición: ningún argumento ni variable de entorno lo activa (PD-12).

Orden (BR11.2): argumentos, archivos de entrada, composición (límites, perfil, *prompt*, aviso y
gateway; el aviso de VE-01 y el de `same_family` salen por stderr en cuanto se leen), validación de
cada transcripción frente al perfil y a los límites del entorno, y directorio de salida con la regla
del corpus. **Nada se escribe antes de que todo eso pase**, ni siquiera `AVISO.txt`. Después, por
archivo y en orden de nombre, `analyze` y `<nombre>.salida.json` atómico. B11a no escribe `reporte.json`
(CG-U11-13).

Códigos de salida (BR11.3): 0 todas las corridas terminaron (aunque alguna sea `estado: error`);
2 argumento, archivo, consentimiento, límite, directorio o regla del corpus; 3 perfil, anonimizador,
clave, transferencia o aviso; 4 incidente de anonimización (el lote se detiene y solo se escribe la
salida en error); 5 error inesperado, escritura fallida o interrupción.
"""

import argparse
import json
import os
import signal
import sys
import threading
from collections.abc import Mapping, Sequence
from datetime import date
from pathlib import Path
from types import FrameType, TracebackType
from typing import TYPE_CHECKING, Any, NoReturn, Self

from veridicus_errors import (
    CancelledError,
    ConfigFamilyError,
    InputRejected,
    ProfileNotApprovedError,
    ProfileTransferNotAuthorizedError,
)
from veridicus_integrity_policy import notice

from veridicus_incoherence_analyzer.api import Entrada, Salida, analyze
from veridicus_incoherence_analyzer.application import preflight
from veridicus_incoherence_analyzer.cli import messages as catalog
from veridicus_incoherence_analyzer.cli.composition import Composition, compose
from veridicus_incoherence_analyzer.cli.io_atomic import AtomicWriteError, write_atomic
from veridicus_incoherence_analyzer.cli.results_dir import (
    default_output_dir,
    is_safe_for_corpus,
    is_writable,
)

if TYPE_CHECKING:
    import httpx

CONTRACT_VERSION = "1.0.0"
INCIDENT_CODE = "incidente_anonimizacion"
CORPUS_ORIGIN = "corpus"
NOTICE_FILE = "AVISO.txt"

Document = dict[str, Any]


class _Stop(Exception):
    """Corta la ejecución con un código y un mensaje ya armado con el catálogo (vacío: ninguno)."""

    def __init__(self, code: int, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class _SecondSignal(BaseException):
    """Una segunda señal termina con 5. Es `BaseException` para que ningún `except Exception` de una
    biblioteca (por ejemplo el del anonimizador, que traduce una excepción ajena) la absorba."""


class _Parser(argparse.ArgumentParser):
    """`argparse` que no llama a `sys.exit`: un argumento inválido es el código 2 (BR11.3)."""

    def error(self, message: str) -> NoReturn:
        raise _Stop(catalog.EXIT_INPUT, catalog.render("arguments", detail=message))

    def exit(self, status: int = 0, message: str | None = None) -> NoReturn:
        raise _Stop(status, "")


class _Interrupts:
    """SIGINT y SIGTERM marcan la cancelación (NFRD-U11-10); una segunda señal corta de una vez."""

    def __init__(self) -> None:
        self.flag = threading.Event()
        self._previous: dict[signal.Signals, Any] = {}

    def __enter__(self) -> Self:
        if threading.current_thread() is threading.main_thread():
            for number in (signal.SIGINT, signal.SIGTERM):
                self._previous[number] = signal.signal(number, self._handle)
        return self

    def __exit__(
        self,
        kind: type[BaseException] | None,
        error: BaseException | None,
        trace: TracebackType | None,
    ) -> None:
        for number, handler in self._previous.items():
            signal.signal(number, handler)

    def _handle(self, number: int, frame: FrameType | None) -> None:
        if self.flag.is_set():
            raise _SecondSignal
        self.flag.set()


def _parser() -> argparse.ArgumentParser:
    parser = _Parser(prog="veridicus", description="Analizador de incoherencias de Veridicus.")
    commands = parser.add_subparsers(dest="command", required=True, parser_class=_Parser)
    analyze_parser = commands.add_parser(
        "analyze", help="Busca contradicciones dentro de una o varias transcripciones."
    )
    analyze_parser.add_argument("entrada", help="archivo .json (objeto transcripcion) o directorio")
    analyze_parser.add_argument("--perfil", required=True, help="perfil de ejecución aprobado")
    analyze_parser.add_argument(
        "--salida", help="directorio de salida (por omisión resultados-locales/<fecha>-analyze)"
    )
    return parser


def _emit(text: str) -> None:
    print(text, file=sys.stderr)


def _collect_inputs(entrada: str) -> list[Path]:
    path = Path(entrada)
    if path.is_file():
        return [path]
    if not path.is_dir():
        raise _Stop(catalog.EXIT_INPUT, catalog.render("input.missing", path=path))
    try:
        found = sorted(item for item in path.iterdir() if item.suffix == ".json" and item.is_file())
    except OSError as error:
        raise _Stop(catalog.EXIT_INPUT, catalog.render("input.unreadable", path=path)) from error
    if not found:
        raise _Stop(catalog.EXIT_INPUT, catalog.render("input.empty_directory", path=path))
    return found


def _read_document(path: Path) -> Document:
    try:
        raw = path.read_bytes()
    except OSError as error:
        raise _Stop(catalog.EXIT_INPUT, catalog.render("input.unreadable", path=path)) from error
    try:
        document = json.loads(raw)
    except ValueError as error:
        raise _Stop(catalog.EXIT_INPUT, catalog.render("input.not_json", path=path)) from error
    if not isinstance(document, dict):
        raise _Stop(catalog.EXIT_INPUT, catalog.render("input.not_object", path=path))
    return document


def _compose(
    profile: str, env: Mapping[str, str], transport: "httpx.BaseTransport | None", aviso: list[str]
) -> Composition:
    def announce(loaded: notice.Notice, warnings: tuple[str, ...]) -> None:
        aviso.append(catalog.render("notice", version=loaded.version, text=loaded.text))
        aviso.extend(catalog.warning_text(identifier) for identifier in warnings)
        _emit("\n".join(aviso))

    try:
        return compose(profile, env, transport, announce=announce)
    except ConfigFamilyError as error:
        raise _Stop(
            catalog.EXIT_CONFIG, catalog.render("config.rejected", detail=catalog.detail(error))
        ) from error


def _entrada(document: Document, profile: str) -> Entrada:
    return {
        "contrato": CONTRACT_VERSION,
        "transcripcion": document,
        "modo": "final",
        "perfil": profile,
    }


def _exceeded_limit(document: Document, figures: Mapping[str, float]) -> str | None:
    """La primera cifra de C25 (ya bajada por el entorno) que la transcripción supera."""
    texts = [turn["texto"] for turn in document["turnos"]]
    if len(texts) > figures["transcript_max_turns"]:
        return "turnos de la transcripción"
    if any(len(text) > figures["turn_max_chars"] for text in texts):
        return "caracteres de un turno"
    if sum(len(text) for text in texts) > figures["transcript_max_chars"]:
        return "caracteres de la transcripción"
    return None


def _validate(path: Path, document: Document, composition: Composition, profile: str) -> None:
    """BR1.1 a BR1.4 con la configuración efectiva, y los límites compuestos desde el entorno."""
    try:
        preflight.check(_entrada(document, profile), composition.config)
    except (ProfileTransferNotAuthorizedError, ProfileNotApprovedError) as error:
        raise _Stop(
            catalog.EXIT_CONFIG,
            catalog.render("config.profile_input", path=path, detail=catalog.detail(error)),
        ) from error
    except InputRejected as error:
        raise _Stop(
            catalog.EXIT_INPUT,
            catalog.render("input.rejected", path=path, detail=catalog.detail(error)),
        ) from error
    exceeded = _exceeded_limit(document, composition.limits)
    if exceeded is not None:
        raise _Stop(catalog.EXIT_INPUT, catalog.render("input.limit", path=path, detail=exceeded))


def _output_dir(requested: str | None, *, corpus: bool) -> Path:
    directory = Path(requested) if requested is not None else default_output_dir(date.today())
    if not is_writable(directory):
        raise _Stop(catalog.EXIT_INPUT, catalog.render("output.not_writable", path=directory))
    if corpus and not is_safe_for_corpus(directory):
        raise _Stop(catalog.EXIT_INPUT, catalog.render("output.corpus_tracked", path=directory))
    return directory


def _write(target: Path, data: bytes) -> None:
    try:
        write_atomic(target, data)
    except AtomicWriteError as error:
        raise _Stop(
            catalog.EXIT_UNEXPECTED, catalog.render("output.write_failed", path=target)
        ) from error


def _dump(salida: Salida) -> bytes:
    return (json.dumps(salida, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _is_incident(salida: Salida) -> bool:
    return bool(salida["estado"] == "error" and salida["error"]["codigo"] == INCIDENT_CODE)


def _analyze_batch(
    documents: Sequence[tuple[Path, Document]],
    composition: Composition,
    directory: Path,
    profile: str,
    interrupts: _Interrupts,
) -> int:
    for path, document in documents:
        salida = analyze(
            _entrada(document, profile),
            composition.config,
            composition.gateway,
            interrupts.flag.is_set,
        )
        target = directory / f"{path.stem}.salida.json"
        _write(target, _dump(salida))
        if _is_incident(salida):
            _emit(catalog.render("run.incident", path=target))
            return catalog.EXIT_INCIDENT
        _emit(catalog.render("run.written", path=target))
    if interrupts.flag.is_set():  # una señal tras la última llamada también es una interrupción
        raise CancelledError("interrupción tras la última corrida")
    return catalog.EXIT_OK


def _run(
    argv: Sequence[str],
    env: Mapping[str, str],
    transport: "httpx.BaseTransport | None",
    interrupts: _Interrupts,
) -> int:
    args = _parser().parse_args(list(argv))
    documents = [(path, _read_document(path)) for path in _collect_inputs(args.entrada)]
    aviso: list[str] = []
    composition = _compose(args.perfil, env, transport, aviso)
    for path, document in documents:
        _validate(path, document, composition, args.perfil)
    corpus = any(document.get("origen") == CORPUS_ORIGIN for _, document in documents)
    directory = _output_dir(args.salida, corpus=corpus)
    directory.mkdir(parents=True, exist_ok=True)
    _write(directory / NOTICE_FILE, ("\n".join(aviso) + "\n").encode("utf-8"))
    return _analyze_batch(documents, composition, directory, args.perfil, interrupts)


def run(
    argv: Sequence[str],
    env: Mapping[str, str],
    *,
    transport: "httpx.BaseTransport | None" = None,
) -> int:
    """Única entrada que usan las pruebas; devuelve el código de salida (BR11.3).

    `transport` solo llega a `build_anonymizer(env, transport)` (PD-12). Escribe el aviso de VE-01 y
    el de `same_family` en stderr y en `AVISO.txt`, y termina con 3 sin ninguna llamada si el aviso,
    el perfil o el anonimizador no están bien (BR9.5, BR10.1).
    """
    interrupts = _Interrupts()
    try:
        with interrupts:
            return _run(argv, env, transport, interrupts)
    except _Stop as stop:
        if stop.message:
            _emit(stop.message)
        return stop.code
    except (CancelledError, _SecondSignal):
        _emit(catalog.render("run.interrupted"))
        return catalog.EXIT_UNEXPECTED
    except Exception as error:  # noqa: BLE001 - frontera: todo fallo inesperado es el código 5
        _emit(catalog.render("run.unexpected", kind=type(error).__name__))
        return catalog.EXIT_UNEXPECTED


def main() -> None:
    """Punto de entrada del script `veridicus`."""
    raise SystemExit(run(sys.argv[1:], os.environ))
