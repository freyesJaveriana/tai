"""Resume en cifras la medición --array=8 de la tarea 4L (AC14.1.1): llamadas, tokens y horas del registro CSV y
velocidad del log de llama-server. Lee los archivos de la 4L sin modificarlos y no copia texto de las entrevistas.

  python resumen_4l.py --registro registro_4L_8.csv --logs /zine/.../tg4L/logs --indice 8

Escribe en la salida estándar las líneas para la sección M1 de reporte.md. Si el trabajo de la 4L no ha terminado,
lo dice: las cifras son parciales (pregunta 15 de User Stories).
"""
import argparse
import csv
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

TIMING = re.compile(r"(prompt eval|eval) time\s*=\s*([\d.]+) ms\s*/\s*(\d+) (?:tokens|runs)")
NUMERIC = ["tokens_entrada", "cache_lectura", "cache_escritura", "tokens_salida", "tokens_razonamiento", "segundos"]


def number(value: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def summarize_registry(path: Path) -> list[str]:
    if not path.exists():
        return [f"No medible: no existe {path.name} (la medición --array=8 aún no registra llamadas)"]
    with path.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        return [f"No medible: {path.name} no tiene filas"]
    totals = {k: sum(number(r.get(k)) for r in rows) for k in NUMERIC}
    errors = sum(1 for r in rows if (r.get("error") or "").strip())
    by_mode: dict[str, list[float]] = defaultdict(lambda: [0, 0.0])
    for r in rows:
        by_mode[r.get("modo", "?")][0] += 1
        by_mode[r.get("modo", "?")][1] += number(r.get("segundos"))
    dates = sorted(datetime.fromisoformat(r["fecha"]) for r in rows if r.get("fecha"))
    span = (dates[-1] - dates[0]).total_seconds() / 3600 if len(dates) > 1 else 0.0
    modes = "; ".join(f"{m}: {n} llamadas, {s / 3600:.2f} h" for m, (n, s) in by_mode.items())
    return [
        f"Registro {path.name}: {len(rows)} llamadas ({errors} con error), "
        f"{totals['segundos'] / 3600:.2f} h sumando llamadas, {span:.2f} h entre la primera y la última",
        f"Tokens: entrada {totals['tokens_entrada']:.0f} (caché leída {totals['cache_lectura']:.0f}), "
        f"salida {totals['tokens_salida']:.0f} (razonamiento {totals['tokens_razonamiento']:.0f})",
        f"Por modo: {modes}",
    ]


def summarize_server(logs: Path, index: int) -> list[str]:
    lines = []
    for log in sorted(logs.glob(f"4L_{index}_*_servidor.log")):
        sums = {"prompt eval": [0.0, 0], "eval": [0.0, 0]}
        for text in log.read_text(encoding="utf-8", errors="replace").splitlines():
            m = TIMING.search(text)
            if m:
                sums[m.group(1)][0] += float(m.group(2))
                sums[m.group(1)][1] += int(m.group(3))
        pp, tg = sums["prompt eval"], sums["eval"]
        rate = lambda s: f"{s[1] / (s[0] / 1000):.2f} tokens/s" if s[0] else "sin datos"  # noqa: E731
        lines.append(
            f"Servidor {log.name}: lectura {pp[1]} tokens en {pp[0] / 3.6e6:.2f} h ({rate(pp)}); "
            f"generación {tg[1]} tokens en {tg[0] / 3.6e6:.2f} h ({rate(tg)})"
        )
    return lines or [f"Sin log del servidor 4L_{index}_*_servidor.log"]


def job_state(logs: Path, index: int) -> list[str]:
    outs = sorted(logs.glob(f"4L_{index}_*.out"))
    if not outs:
        return [f"Sin log del trabajo 4L_{index}_*.out"]
    states = []
    for out in outs:
        job = out.stem.split("_")[-1]
        done = f"grupo {index} terminado" in out.read_text(encoding="utf-8", errors="replace")
        states.append(f"trabajo {job}: {'terminado' if done else 'sin terminar (cifras parciales)'}")
    return ["Trabajos de la medición: " + "; ".join(states)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--registro", type=Path, required=True)
    parser.add_argument("--logs", type=Path, required=True)
    parser.add_argument("--indice", type=int, default=8)
    args = parser.parse_args()
    for line in job_state(args.logs, args.indice) + summarize_registry(args.registro) + summarize_server(
        args.logs, args.indice
    ):
        print(f"Resultado (4L --array={args.indice}): {line}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
