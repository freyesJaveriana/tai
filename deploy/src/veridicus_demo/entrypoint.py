"""Punto de entrada del Job de la demo (U02-T01, paso 2).

`main()` llama en proceso a `run` de la CLI del analizador con el perfil `demo-anthropic`, sobre el
directorio de entrada y el de salida que fijan `VERIDICUS_DEMO_ENTRADA` (por omisión `/entrada`) y
`VERIDICUS_DEMO_SALIDA` (por omisión `/salida`). Después lee cada `<nombre>.salida.json` y escribe en
stdout, por archivo, su estado y el número de hallazgos y, por hallazgo, el hecho, el tipo y las dos
citas con su turno. En `error` añade el `motivo` (el `error.codigo` de C6), y en ambos estados un
resumen del `registro`: llamadas por papel, tokens y motivos de descarte. Son solo cifras y
vocabulario cerrado: un valor fuera del vocabulario se imprime como «otro».

Reglas que este módulo hace cumplir (todas con su prueba en `tests/test_entrypoint.py`):

- AUTONOMIA-04: el anonimizador va dentro de la CLI. Aquí no se construye ninguno ni se llama a un
  proveedor: sin clave o con el anonimizador caído la CLI termina sin ninguna llamada y este módulo
  no imprime hallazgos.
- AUTONOMIA-05: con un código distinto de 0 no se lee ninguna salida de hallazgos, y un archivo en
  estado `error` se informa con 0 hallazgos aunque su contenido traiga alguno. Las citas no se
  revalidan ni se recortan: la verificación es de la CLI.
- Sin filtraciones: no se imprime el entorno, la clave ni texto de la transcripción que no sea una
  cita; ante una excepción inesperada solo se escribe su clase.
- AUTONOMIA-03: los rótulos son fijos y no llevan vocabulario de veracidad.

Código de salida: el de la CLI si no es 0; 4 si la CLI dio 0 pero algún archivo quedó en `error`;
5 si falta una salida o está corrupta, o si hubo una excepción inesperada; 2 si recibe argumentos.
"""

import json
import os
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final, TextIO

from veridicus_incoherence_analyzer.cli.main import run

if TYPE_CHECKING:
    import httpx

PROFILE: Final = "demo-anthropic"
INPUT_VAR: Final = "VERIDICUS_DEMO_ENTRADA"
OUTPUT_VAR: Final = "VERIDICUS_DEMO_SALIDA"
DEFAULT_INPUT: Final = "/entrada"
DEFAULT_OUTPUT: Final = "/salida"

EXIT_OK: Final = 0
EXIT_ARGS: Final = 2
EXIT_ERROR_STATE: Final = 4
EXIT_UNEXPECTED: Final = 5
# Código con el que la CLI informa un incidente de anonimización (`cli.main`).
CLI_INCIDENT: Final = 4

ARGS_MESSAGE: Final = "La demo no recibe argumentos: la entrada y la salida van en el entorno."
CLI_FAILED_MESSAGE: Final = "El análisis terminó con el código {code}; no se muestran hallazgos."
NO_OUTPUT_MESSAGE: Final = "Falta un archivo de salida o está dañado; no se muestran hallazgos."
UNEXPECTED_MESSAGE: Final = "Error inesperado en la demo ({kind}); no se muestran hallazgos."


class _UnreadableOutput(Exception):
    """Un archivo de salida falta o no tiene la forma de C6; no lleva detalle a propósito."""


@dataclass(frozen=True)
class _Quote:
    turn: str
    text: str


@dataclass(frozen=True)
class _Finding:
    fact: str
    kind: str
    quote_a: _Quote
    quote_b: _Quote


# Vocabulario cerrado de C6: solo estos valores se imprimen tal cual; cualquier otro sale como «otro».
ERROR_CODES: Final = frozenset(
    {
        "salida_invalida",
        "bloqueo_contenido",
        "tiempo_agotado",
        "proveedor",
        "anonimizador_no_disponible",
        "incidente_anonimizacion",
    }
)
DISCARD_REASONS: Final = frozenset(
    {
        "cita_no_verificada",
        "cita_en_otro_turno",
        "marca_alterada",
        "campo_faltante",
        "rechazado_verificador",
        "rechazado_permutacion",
        "fuera_de_tramo",
        "vocabulario_prohibido",
    }
)
ROLES: Final = ("juez", "verificador", "verificador_permutado")


@dataclass(frozen=True)
class _Result:
    name: str
    state: str
    findings: tuple[_Finding, ...]
    reason: str = ""
    trace: tuple[str, ...] = ()


def _text(node: Any, key: str) -> str:
    value = node.get(key) if isinstance(node, dict) else None
    if not isinstance(value, str):
        raise _UnreadableOutput
    return value


def _quote(node: Any) -> _Quote:
    return _Quote(turn=_text(node, "turno"), text=_text(node, "cita"))


def _finding(node: Any) -> _Finding:
    return _Finding(
        fact=_text(node, "hecho"),
        kind=_text(node, "tipo"),
        quote_a=_quote(node.get("cita_a")),
        quote_b=_quote(node.get("cita_b")),
    )


def _closed(value: Any, allowed: frozenset[str]) -> str:
    return value if isinstance(value, str) and value in allowed else "otro"


def _reason(document: dict[str, Any]) -> str:
    """El `error.codigo` de C6, que es vocabulario cerrado y nunca lleva texto del relato."""
    error = document.get("error")
    return _closed(error.get("codigo") if isinstance(error, dict) else None, ERROR_CODES)


def _counts(values: list[str]) -> str:
    return ", ".join(f"{value}×{values.count(value)}" for value in sorted(set(values)))


def _trace(document: dict[str, Any]) -> tuple[str, ...]:
    """Resumen del `registro` de C6: cuántas llamadas por papel, tokens y motivos de descarte.

    Solo cifras y vocabulario cerrado; no se imprime ni el modelo ni ningún texto libre. Un
    `registro` ausente o con otra forma no hace fallar la demo: simplemente no se resume.
    """
    registro = document.get("registro")
    if not isinstance(registro, dict):
        return ()
    lines: list[str] = []
    calls = registro.get("llamadas")
    if isinstance(calls, list):
        roles = [
            _closed(c.get("papel") if isinstance(c, dict) else None, frozenset(ROLES))
            for c in calls
        ]
        detail = f" ({_counts(roles)})" if roles else ""
        lines.append(f"  llamadas: {len(calls)}{detail}")
    tokens_in, tokens_out = registro.get("tokens_entrada"), registro.get("tokens_salida")
    if isinstance(tokens_in, int) and isinstance(tokens_out, int):
        lines.append(f"  tokens: {tokens_in} de entrada, {tokens_out} de salida")
    discards = registro.get("descartes")
    if isinstance(discards, list) and discards:
        reasons = [
            _closed(d.get("motivo") if isinstance(d, dict) else None, DISCARD_REASONS)
            for d in discards
        ]
        lines.append(f"  descartes: {len(discards)} ({_counts(reasons)})")
    return tuple(lines)


def _read(directory: Path, name: str, *, with_findings: bool) -> _Result:
    """Lee `<nombre>.salida.json`. Sin `with_findings` solo lee el estado y nunca los hallazgos."""
    try:
        document = json.loads((directory / f"{name}.salida.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise _UnreadableOutput from error
    state = _text(document, "estado")
    if state not in ("ok", "error"):
        raise _UnreadableOutput
    if state == "error":
        return _Result(name, state, (), reason=_reason(document), trace=_trace(document))
    if not with_findings:
        return _Result(name, state, ())
    items = document.get("hallazgos")
    if not isinstance(items, list):
        raise _UnreadableOutput
    return _Result(name, state, tuple(_finding(item) for item in items), trace=_trace(document))


def _count(number: int) -> str:
    """«1 hallazgo» en singular y «N hallazgos» en cualquier otro caso (incluido 0)."""
    return f"{number} hallazgo" if number == 1 else f"{number} hallazgos"


def _lines(result: _Result) -> list[str]:
    lines = [f"{result.name}: estado={result.state}, {_count(len(result.findings))}"]
    if result.reason:
        lines.append(f"  motivo: {result.reason}")
    for item in result.findings:
        lines.append(f"  hecho: {item.fact}")
        lines.append(f"  tipo: {item.kind}")
        lines.append(f"  cita A (turno {item.quote_a.turn}): «{item.quote_a.text}»")
        lines.append(f"  cita B (turno {item.quote_b.turn}): «{item.quote_b.text}»")
    lines.extend(result.trace)
    return lines


def _say(out: TextIO, text: str) -> None:
    print(text, file=out)


def _report(out: TextIO, code: int, entrada: Path, salida: Path) -> int:
    names = sorted(path.stem for path in entrada.glob("*.json") if path.is_file())
    if code != EXIT_OK:
        _say(out, CLI_FAILED_MESSAGE.format(code=code))
        if code == CLI_INCIDENT:
            for name in names:
                try:
                    result = _read(salida, name, with_findings=False)
                except _UnreadableOutput:
                    continue
                if result.state == "error":
                    for line in _lines(result):
                        _say(out, line)
        return code
    try:
        if not names:
            raise _UnreadableOutput
        results = [_read(salida, name, with_findings=True) for name in names]
    except _UnreadableOutput:
        _say(out, NO_OUTPUT_MESSAGE)
        return EXIT_UNEXPECTED
    for result in results:
        for line in _lines(result):
            _say(out, line)
    if any(result.state == "error" for result in results):
        return EXIT_ERROR_STATE
    return EXIT_OK


def main_with(
    argv: Sequence[str],
    env: Mapping[str, str],
    *,
    transport: "httpx.BaseTransport | None" = None,
    stdout: TextIO | None = None,
) -> int:
    """Costura de las pruebas: inyecta el transporte del doble y captura stdout."""
    out = sys.stdout if stdout is None else stdout
    if argv:
        _say(out, ARGS_MESSAGE)
        return EXIT_ARGS
    entrada = env.get(INPUT_VAR, DEFAULT_INPUT)
    salida = env.get(OUTPUT_VAR, DEFAULT_OUTPUT)
    try:
        code = run(
            ["analyze", entrada, "--perfil", PROFILE, "--salida", salida], env, transport=transport
        )
        return _report(out, code, Path(entrada), Path(salida))
    except Exception as error:  # noqa: BLE001 - frontera: solo la clase, nunca el mensaje ni el entorno
        _say(out, UNEXPECTED_MESSAGE.format(kind=type(error).__name__))
        return EXIT_UNEXPECTED


def main() -> None:
    """Punto de entrada del Job: `python -m veridicus_demo.entrypoint`."""
    raise SystemExit(main_with(sys.argv[1:], os.environ))


if __name__ == "__main__":
    main()
