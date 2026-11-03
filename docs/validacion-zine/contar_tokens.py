"""Cuenta los tokens de Qwen de las entrevistas del piloto frente al contexto del modelo (US14.1, M3, AC14.1.3).

  python contar_tokens.py --modelo <gguf> --entrevistas <dir> --prompt <archivo> --salida <dir>
                          [--contexto 163840] [--reserva-salida 16384]

Usa llama-tokenize (solo carga el vocabulario del GGUF). Cada entrevista (JSON con «turnos») se cuenta de dos formas:
el texto de los turnos unido por saltos de línea y el bloque JSON de turnos (n, hablante, página, texto) que recibiría
el analizador. Los textos temporales se borran al terminar; tokens.csv y el resumen solo llevan cifras e ID.
"""
import argparse
import csv
import json
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path

COUNT = re.compile(r"Total number of tokens:\s*(\d+)")


def count_tokens(model: Path, text_file: Path) -> int:
    result = subprocess.run(
        ["llama-tokenize", "-m", str(model), "-f", str(text_file), "--ids", "--show-count"],
        capture_output=True, text=True, check=True, timeout=1800,
    )
    match = COUNT.search(result.stdout) or COUNT.search(result.stderr)
    if match:
        return int(match.group(1))
    ids = re.search(r"\[([\d,\s]*)\]", result.stdout)  # versiones sin --show-count: se cuentan los ID
    if ids:
        return len([x for x in ids.group(1).split(",") if x.strip()])
    raise RuntimeError(f"llama-tokenize no informó el número de tokens de {text_file.name}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--modelo", type=Path, required=True)
    parser.add_argument("--entrevistas", type=Path, required=True)
    parser.add_argument("--prompt", type=Path, required=True)
    parser.add_argument("--salida", type=Path, required=True)
    parser.add_argument("--contexto", type=int, default=163840)
    parser.add_argument("--reserva-salida", type=int, default=16384)
    args = parser.parse_args()

    files = sorted(args.entrevistas.glob("*.json"))
    if not files:
        print(f"No medible: no hay entrevistas .json en {args.entrevistas}")
        return 1
    temp = Path(tempfile.mkdtemp(dir=args.salida, prefix="tmp-"))
    rows = []
    try:
        for f in files:
            data = json.loads(f.read_text(encoding="utf-8"))
            turns = data["turnos"]
            plain = "\n".join(t.get("texto") or "" for t in turns)
            block = json.dumps(
                {"turnos": [{k: t.get(k) for k in ("n", "hablante", "pagina", "texto")} for t in turns]},
                ensure_ascii=False,
            )
            (temp / "texto.txt").write_text(plain, encoding="utf-8")
            (temp / "bloque.txt").write_text(block, encoding="utf-8")
            rows.append({
                "entrevista": data.get("entrevista", f.stem),
                "turnos": len(turns),
                "caracteres": len(plain),
                "tokens_texto": count_tokens(args.modelo, temp / "texto.txt"),
                "tokens_json": count_tokens(args.modelo, temp / "bloque.txt"),
            })
            print(f"{rows[-1]['entrevista']}: {rows[-1]['tokens_json']} tokens (bloque JSON)", flush=True)
        prompt_tokens = count_tokens(args.modelo, args.prompt)
    finally:
        shutil.rmtree(temp, ignore_errors=True)

    with (args.salida / "tokens.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    longest = max(rows, key=lambda r: r["tokens_json"])
    needed = longest["tokens_json"] + prompt_tokens + args.reserva_salida
    per_interview = "; ".join(f"{r['entrevista']} {r['tokens_json']} ({r['tokens_texto']} solo texto)" for r in rows)
    lines = [
        f"Resultado: {len(rows)} entrevistas contadas: {', '.join(r['entrevista'] for r in rows)}",
        f"Resultado: tokens por entrevista (bloque JSON, entre paréntesis solo el texto): {per_interview}",
        f"Resultado: máximo {longest['tokens_json']} ({longest['entrevista']}), mediana "
        f"{statistics.median(r['tokens_json'] for r in rows):.0f} (bloque JSON); máximo solo texto "
        f"{max(r['tokens_texto'] for r in rows)}, mediana {statistics.median(r['tokens_texto'] for r in rows):.0f}",
        f"Resultado: la más larga + prompt ({prompt_tokens} tokens, {args.prompt.name}) + reserva de salida "
        f"({args.reserva_salida}) = {needed} de {args.contexto}: {'cabe' if needed <= args.contexto else 'no cabe'} "
        f"(margen {args.contexto - needed})",
    ]
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
