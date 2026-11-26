"""Compuerta de cobertura de U11 (paso 14): lee los `coverage.json` de los cuatro paquetes.

Exige el 100 % de ramas en los 9 módulos guardia (`GUARD_MODULES`) y el 80 % de líneas por paquete.
Falla cerrado: un informe ilegible, mal formado o sin alguno de los módulos guardia no pasa. Solo
informa rutas de módulos y cifras.

Uso, desde `libs/incoherence_analyzer` y con los informes en el orden de `PACKAGES`:
`python -m veridicus_incoherence_analyzer.testing.coverage_gate ../incoherence_analyzer/coverage.json
../model_gateway/coverage.json ../execution_profiles/coverage.json ../integrity_policy/coverage.json`.
"""

import json
import sys
from collections.abc import Mapping, Sequence
from typing import Any

LINE_FLOOR_PERCENT = 80
# El orden de los informes en la línea de comandos.
PACKAGES = (
    "veridicus_incoherence_analyzer",
    "veridicus_model_gateway",
    "veridicus_execution_profiles",
    "veridicus_integrity_policy",
)
# Paquete -> módulos guardia (rutas dentro del paquete) que exigen el 100 % de ramas.
GUARD_MODULES: Mapping[str, tuple[str, ...]] = {
    "veridicus_incoherence_analyzer": (
        "domain/quotes.py",
        "domain/filter.py",
        "domain/run_state.py",
        "domain/output.py",
        "application/preflight.py",
        "cli/composition.py",
    ),
    "veridicus_model_gateway": ("adapters/anonymizing.py",),
    "veridicus_execution_profiles": ("validate.py",),
    "veridicus_integrity_policy": ("scan.py",),
}


def _relative(path: str, package: str) -> str | None:
    """La ruta dentro del paquete (`domain/quotes.py`), o `None` si el archivo no es del paquete."""
    normalized = path.replace("\\", "/")
    marker = f"{package}/"
    index = normalized.rfind(marker)
    if index < 0:
        return None
    return normalized[index + len(marker) :]


def _counts(path: str, entry: object) -> tuple[int, int, int, int] | str:
    """(sentencias, cubiertas, ramas, ramas cubiertas) del archivo, o el motivo de que no se lea."""
    summary = entry.get("summary") if isinstance(entry, dict) else None
    if not isinstance(summary, dict):
        return f"entrada sin resumen para {path}"
    values: list[int] = []
    for name in ("num_statements", "covered_lines", "num_branches", "covered_branches"):
        value = summary.get(name)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            return f"cifras inválidas para {path}"
        values.append(value)
    return (values[0], values[1], values[2], values[3])


def _evaluate_package(package: str, report: Mapping[str, Any]) -> list[str]:
    files = report.get("files")
    if not isinstance(files, dict) or not files:
        return [f"{package}: el informe no trae archivos"]
    failures: list[str] = []
    guards = set(GUARD_MODULES[package])
    statements = covered_lines = 0
    reported: set[str] = set()
    for path, entry in sorted(files.items()):
        relative = _relative(str(path), package)
        if relative is None:
            continue
        reported.add(relative)
        counts = _counts(str(path), entry)
        if isinstance(counts, str):
            failures.append(f"{package}: {counts}")
            continue
        file_statements, file_covered, branches, covered_branches = counts
        statements += file_statements
        covered_lines += file_covered
        if relative in guards and covered_branches != branches:
            failures.append(
                f"módulo guardia {package}/{relative}: {branches - covered_branches} de "
                f"{branches} rama(s) sin cubrir (se exige el 100 % de ramas)"
            )
    failures.extend(
        f"el informe no trae el módulo guardia {package}/{relative}"
        for relative in sorted(guards - reported)
    )
    if statements == 0 or covered_lines * 100 < statements * LINE_FLOOR_PERCENT:
        failures.append(
            f"líneas del paquete {package}: {covered_lines} de {statements} cubiertas "
            f"(se exige al menos el {LINE_FLOOR_PERCENT} %)"
        )
    return failures


def evaluate(reports: Sequence[Mapping[str, Any]]) -> list[str]:
    """Los fallos de los cuatro informes, uno por paquete y en el orden de `PACKAGES`."""
    if len(reports) != len(PACKAGES):
        return [f"se esperan {len(PACKAGES)} informes y llegaron {len(reports)}"]
    failures: list[str] = []
    for package, report in zip(PACKAGES, reports, strict=True):
        failures.extend(_evaluate_package(package, report))
    return failures


def main(argv: Sequence[str]) -> int:
    """0 si pasan los cuatro informes, 1 si falla alguno o no se puede leer, 2 si el uso es incorrecto."""
    if len(argv) != len(PACKAGES):
        print(
            "uso: python -m veridicus_incoherence_analyzer.testing.coverage_gate "
            "<coverage.json de cada paquete, en el orden: analizador, gateway, perfiles, política>",
            file=sys.stderr,
        )
        return 2
    reports: list[Mapping[str, Any]] = []
    for path in argv:
        try:
            with open(path, encoding="utf-8") as handle:
                report = json.load(handle)
        except (OSError, ValueError):
            print(f"no se pudo leer el informe {path}", file=sys.stderr)
            return 1
        if not isinstance(report, dict):
            print(f"no se pudo leer el informe {path}: no es un objeto JSON", file=sys.stderr)
            return 1
        reports.append(report)
    failures = evaluate(reports)
    for failure in failures:
        print(failure, file=sys.stderr)
    if failures:
        return 1
    print(
        "compuerta de cobertura: 100 % de ramas en los módulos guardia y "
        f"al menos {LINE_FLOOR_PERCENT} % de líneas por paquete"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
