"""Comprueba que reporte.md de la validación de modelos locales (US14.1) está completo.

  python3 docs/validacion-zine/comprobar_reporte.py docs/validacion-zine/reporte.md [--revision]
  python3 docs/validacion-zine/comprobar_reporte.py --autoprueba

Termina con código 0 solo si cada sección «## M1» a «## M6» tiene «Comando:», «Trabajo SLURM:» (con un ID), «Nodo:»,
«SHA-256 del modelo:» (64 hexadecimales; en M5 vale «No aplica:» con motivo) y un «Resultado:» con cifras, o bien
«No medible:» con su motivo y «Salida:». Con --revision exige además la sección «## Revisión» de AC14.1.7: «Revisor:»,
«Fecha:» (AAAA-MM-DD), «Decisión:» con una de las tres decisiones (con «Limitaciones:» o «Repetir:» según el caso) y
las respuestas (a) a (f). --autoprueba es el control negativo: un reporte completo pasa y quitarle cualquier campo lo
hace fallar. Es evidencia de proceso, no código del producto.
"""
import re
import sys
from pathlib import Path

SECTIONS = [f"M{i}" for i in range(1, 7)]
DECISIONS = ("Diseñar con modelos locales", "Diseñar con limitaciones registradas", "Repetir mediciones")
QUESTIONS = "abcdef"
PLACEHOLDER = re.compile(r"^(<.*>|…|\.\.\.|pendiente|por completar|todo)$", re.IGNORECASE)


def split_sections(text: str) -> dict[str, str]:
    sections, current = {}, None
    for line in text.splitlines():
        heading = re.match(r"^##\s+(\S+)", line)
        if heading:
            current = heading.group(1)
            sections.setdefault(current, "")
        elif current:
            sections[current] += line + "\n"
    return sections


def fields(body: str) -> dict[str, list[str]]:
    """Campos «Nombre: valor» (admite viñeta y negrita); un campo repetido acumula sus valores."""
    found: dict[str, list[str]] = {}
    for line in body.splitlines():
        m = re.match(r"^\s*(?:[-*]\s+)?\**([^:*()][^:*]*?)\**:\**\s*(.*)$", line)
        if m:
            value = m.group(2).strip()
            if value and not PLACEHOLDER.match(value):
                found.setdefault(m.group(1).strip(), []).append(value)
    return found


def check_measurement(name: str, body: str) -> list[str]:
    f, problems = fields(body), []
    if "Comando" not in f:
        problems.append(f"{name}: falta «Comando:»")
    if not any(re.search(r"\d{3,}", v) for v in f.get("Trabajo SLURM", [])):
        problems.append(f"{name}: falta «Trabajo SLURM:» con el ID del trabajo")
    if not any(re.search(r"\bhpc[\w-]+", v) for v in f.get("Nodo", [])):
        problems.append(f"{name}: falta «Nodo:» (hpchead02 o hpc02-wNNN)")
    sha_ok = any(re.search(r"\b[0-9a-f]{64}\b", v) for v in f.get("SHA-256 del modelo", []))
    if name == "M5":
        if not sha_ok and "No aplica" not in f:
            problems.append("M5: falta «SHA-256 del modelo:» o «No aplica:» con su motivo")
    elif "No aplica" in f:
        problems.append(f"{name}: «No aplica:» solo vale para M5")
    elif not sha_ok:
        problems.append(f"{name}: falta «SHA-256 del modelo:» con 64 hexadecimales")
    with_figures = any(re.search(r"\d", v) for v in f.get("Resultado", []))
    if "No medible" in f:
        if "Salida" not in f:
            problems.append(f"{name}: «No medible:» exige «Salida:» con la salida del trabajo")
    elif not with_figures:
        problems.append(f"{name}: falta «Resultado:» con cifras o «No medible:» con su motivo")
    return problems


def check_review(body: str | None) -> list[str]:
    if body is None:
        return ["falta la sección «## Revisión»"]
    f, problems = fields(body), []
    if "Revisor" not in f:
        problems.append("Revisión: falta «Revisor:»")
    if not any(re.fullmatch(r"\d{4}-\d{2}-\d{2}", v) for v in f.get("Fecha", [])):
        problems.append("Revisión: falta «Fecha:» con formato AAAA-MM-DD")
    decision = [d for v in f.get("Decisión", []) for d in DECISIONS if v.strip("«»\"* ").startswith(d)]
    if len(decision) != 1:
        problems.append(f"Revisión: «Decisión:» debe ser exactamente una de: {', '.join(DECISIONS)}")
    elif decision[0] == DECISIONS[1] and "Limitaciones" not in f:
        problems.append("Revisión: «Diseñar con limitaciones registradas» exige «Limitaciones:» que las nombre")
    elif decision[0] == DECISIONS[2] and not any(re.search(r"M[1-6]", v) for v in f.get("Repetir", [])):
        problems.append("Revisión: «Repetir mediciones» exige «Repetir:» con las mediciones (M1–M6)")
    for q in QUESTIONS:
        if not re.search(rf"^[ \t]*(?:[-*][ \t]+)?\({q}\)[^:\n]*:[ \t]*\S", body, re.MULTILINE):
            problems.append(f"Revisión: falta la respuesta ({q})")
    return problems


def check(text: str, review: bool) -> list[str]:
    sections = split_sections(text)
    problems = []
    for name in SECTIONS:
        if name not in sections:
            problems.append(f"falta la sección «## {name}»")
        else:
            problems += check_measurement(name, sections[name])
    if review:
        problems += check_review(sections.get("Revisión"))
    return problems


SHA = "a" * 64
SAMPLE = "\n".join(
    [f"## {m}\n\nComando: sbatch trabajos/{m.lower()}.sbatch\nTrabajo SLURM: 1300{i}\nNodo: hpc02-w006\n"
     + ("No aplica: M5 no usa un modelo\n" if m == "M5" else f"SHA-256 del modelo: {SHA}\n")
     + "Resultado: tg128 = 6.70 tokens/s\n" for i, m in enumerate(SECTIONS)]
    + ["## Revisión\n\nRevisor: Felipe Reyes\nFecha: 2026-11-10\nDecisión: Diseñar con limitaciones registradas\n"
       "Limitaciones: modo fragmentado obligatorio\n"
       + "".join(f"- ({q}) Respuesta: 1 cifra\n" for q in QUESTIONS)]
)


def self_test() -> int:
    failures = []
    if check(SAMPLE, review=True):
        failures.append(f"el reporte completo de ejemplo no pasa: {check(SAMPLE, True)}")
    lines = SAMPLE.splitlines()
    removable = [i for i, line in enumerate(lines) if re.match(r"^(- \(|[A-Z][^:]*:)", line)]
    for i in removable:
        mutated = "\n".join(lines[:i] + lines[i + 1 :])
        if not check(mutated, review=True):
            failures.append(f"quitar «{lines[i]}» no hace fallar la comprobación")
    variants = {
        "un campo vacío": SAMPLE.replace("Nodo: hpc02-w006", "Nodo:", 1),
        "un marcador sin llenar": SAMPLE.replace("Trabajo SLURM: 13000", "Trabajo SLURM: <id>", 1),
        "«No aplica» fuera de M5": SAMPLE.replace(f"SHA-256 del modelo: {SHA}", "No aplica: x", 1),
        "«No medible» sin salida": SAMPLE.replace("Resultado: tg128 = 6.70 tokens/s", "No medible: sin nodo", 1),
        "una decisión ajena": SAMPLE.replace("Decisión: Diseñar con limitaciones registradas", "Decisión: Aprobar"),
        "«Repetir» sin mediciones": SAMPLE.replace("Diseñar con limitaciones registradas", "Repetir mediciones"),
        "preguntas sin responder": re.sub(r"(\(\w\) Respuesta:).*", r"\1", SAMPLE),
    }
    for label, text in variants.items():
        if not check(text, review=True):
            failures.append(f"{label} no hace fallar la comprobación")
    if check(SAMPLE.split("## Revisión")[0], review=False):
        failures.append("sin --revision, las seis mediciones completas no pasan")
    if not check(SAMPLE.split("## Revisión")[0], review=True):
        failures.append("con --revision, un reporte sin «## Revisión» pasa")
    for failure in failures:
        print(f"AUTOPRUEBA FALLÓ: {failure}")
    if not failures:
        print(f"autoprueba: {len(removable) + len(variants) + 3} casos, el control negativo funciona")
    return 1 if failures else 0


def main(argv: list[str]) -> int:
    if argv == ["--autoprueba"]:
        return self_test()
    paths = [a for a in argv if not a.startswith("--")]
    if len(paths) != 1 or set(argv) - {*paths, "--revision"}:
        print(__doc__.strip().splitlines()[2].strip())
        return 2
    path = Path(paths[0])
    if not path.is_file():
        print(f"no existe {path}")
        return 2
    problems = check(path.read_text(encoding="utf-8"), review="--revision" in argv)
    for problem in problems:
        print(f"FALTA: {problem}")
    if not problems:
        print(f"{path}: completo{' con la revisión' if '--revision' in argv else ''}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
