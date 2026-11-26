"""Compuerta de cobertura del anonimizador (paso 14): lee el `coverage.json` de la suite.

Exige el 100 % de ramas en los módulos guardia (`domain/`, `application/`, `api.py`, `providers/` y
`testing/fake_transport.py`) y el 80 % de líneas en el paquete. Falla cerrado: un informe ilegible,
mal formado o sin archivos de un grupo guardia no pasa. Solo informa rutas de módulos y cifras.

Uso: `python -m veridicus_anonymizer.testing.coverage_gate coverage.json`.
"""

import json
import sys
from collections.abc import Collection, Mapping, Sequence
from pathlib import Path
from typing import Any

PACKAGE_MARKER = "veridicus_anonymizer/"
LINE_FLOOR_PERCENT = 80
# Grupo guardia -> prefijo del directorio (termina en "/") o ruta exacta del módulo.
GUARD_GROUPS = ("domain/", "application/", "api.py", "providers/", "testing/fake_transport.py")


def _relative(path: str) -> str | None:
    """La ruta dentro del paquete (`domain/masking.py`), o `None` si el archivo no es del paquete."""
    normalized = path.replace("\\", "/")
    index = normalized.rfind(PACKAGE_MARKER)
    if index < 0:
        return None
    return normalized[index + len(PACKAGE_MARKER) :]


def _group_of(relative: str) -> str | None:
    for group in GUARD_GROUPS:
        if relative == group or (group.endswith("/") and relative.startswith(group)):
            return group
    return None


def _counts(path: str, entry: object) -> tuple[int, int, int, int] | str:
    """(líneas, cubiertas, ramas, ramas cubiertas) del archivo, o el motivo de que no se lea."""
    summary = entry.get("summary") if isinstance(entry, dict) else None
    if not isinstance(summary, dict):
        return f"entrada sin resumen para {path}"
    names = ("num_statements", "covered_lines", "num_branches", "covered_branches")
    values: list[int] = []
    for name in names:
        value = summary.get(name)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            return f"cifras inválidas para {path}"
        values.append(value)
    return (values[0], values[1], values[2], values[3])


def guard_files(package_dir: Path) -> set[str]:
    """Los archivos que el informe debe traer: cada `.py` de los grupos guardia que hay en `src/`.

    Un grupo de archivo exacto se exige aunque no exista en disco (falla cerrado).
    """
    expected: set[str] = set()
    for group in GUARD_GROUPS:
        if group.endswith("/"):
            expected.update(
                path.relative_to(package_dir).as_posix()
                for path in (package_dir / group).rglob("*.py")
            )
        else:
            expected.add(group)
    return expected


def evaluate(report: Mapping[str, Any], expected_files: Collection[str] | None = None) -> list[str]:
    """Los fallos del informe (lista vacía si pasa), en español y sin más datos que rutas y cifras.

    `expected_files` son las rutas dentro del paquete (`domain/masking.py`) que el informe debe traer;
    un `omit` de la configuración de cobertura no puede dejar fuera un módulo guardia sin aviso.
    """
    files = report.get("files")
    if not isinstance(files, dict) or not files:
        return ["el informe no trae archivos"]
    failures: list[str] = []
    statements = covered_lines = 0
    seen_groups: set[str] = set()
    reported: set[str] = set()
    for path, entry in sorted(files.items()):
        relative = _relative(str(path))
        if relative is None:
            continue
        reported.add(relative)
        counts = _counts(str(path), entry)
        if isinstance(counts, str):
            failures.append(counts)
            continue
        file_statements, file_covered, branches, covered_branches = counts
        statements += file_statements
        covered_lines += file_covered
        group = _group_of(relative)
        if group is None:
            continue
        seen_groups.add(group)
        if covered_branches != branches:
            failures.append(
                f"módulo guardia {path}: {branches - covered_branches} de {branches} "
                "rama(s) sin cubrir (se exige el 100 % de ramas)"
            )
    failures.extend(
        f"ningún archivo del grupo guardia {group} en el informe"
        for group in GUARD_GROUPS
        if group not in seen_groups
    )
    failures.extend(
        f"el informe no trae el módulo guardia {relative}"
        for relative in sorted(set(expected_files or ()) - reported)
    )
    if statements == 0 or covered_lines * 100 < statements * LINE_FLOOR_PERCENT:
        failures.append(
            f"líneas del paquete: {covered_lines} de {statements} cubiertas "
            f"(se exige al menos el {LINE_FLOOR_PERCENT} %)"
        )
    return failures


def main(argv: Sequence[str], package_dir: Path | None = None) -> int:
    """0 si el informe pasa, 1 si falla o no se puede leer, 2 si el uso es incorrecto.

    `package_dir` es el directorio del paquete en `src/`; por defecto, el de este mismo módulo.
    """
    if len(argv) != 1:
        print(
            "uso: python -m veridicus_anonymizer.testing.coverage_gate coverage.json",
            file=sys.stderr,
        )
        return 2
    try:
        with open(argv[0], encoding="utf-8") as handle:
            report = json.load(handle)
    except (OSError, ValueError):
        print(f"no se pudo leer el informe {argv[0]}", file=sys.stderr)
        return 1
    if not isinstance(report, dict):
        print(f"no se pudo leer el informe {argv[0]}: no es un objeto JSON", file=sys.stderr)
        return 1
    root = Path(__file__).resolve().parents[1] if package_dir is None else package_dir
    failures = evaluate(report, guard_files(root))
    for failure in failures:
        print(failure, file=sys.stderr)
    if failures:
        return 1
    print(
        "compuerta de cobertura: 100 % de ramas en los módulos guardia y "
        f"al menos {LINE_FLOOR_PERCENT} % de líneas en el paquete"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
