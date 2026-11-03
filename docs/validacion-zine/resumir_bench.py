"""Resume la salida JSON de llama-bench (-o json) en la línea «Resultado:» de reporte.md (M1 y M6).

  python resumir_bench.py bench.json

Solo cifras: tokens/s de lectura (pp) y de generación (tg), con su desviación, hilos, repeticiones y versión.
"""
import json
import sys
from pathlib import Path


def main() -> int:
    rows = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    if not rows:
        print("No medible: llama-bench no devolvió filas (ver el log del trabajo)")
        return 1
    parts = []
    for row in rows:
        kind = f"pp{row['n_prompt']}" if row["n_prompt"] else f"tg{row['n_gen']}"
        parts.append(f"{kind} = {row['avg_ts']:.2f} ± {row['stddev_ts']:.2f} tokens/s")
    first = rows[0]
    reps = len(first.get("samples_ts", [])) or "?"
    print(
        f"Resultado: {'; '.join(parts)} ({reps} repeticiones, {first['n_threads']} hilos, "
        f"{first['model_type']}, llama.cpp {first.get('build_number', '?')} {first.get('build_commit', '')})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
