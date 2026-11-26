"""Ayudas de las pruebas de la CLI: entradas sintéticas en disco y una corrida por `run`."""

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import httpx

from tests.support import PROFILE, ScriptedProvider, echo_finding, env, make_transcription
from veridicus_incoherence_analyzer.cli.main import run

CONSENT: dict[str, Any] = {
    "tipo": "persona",
    "version_texto": "1.0",
    "autoriza_transferencia": True,
    "autoriza_voz": False,
    "autoriza_conservar_audio": False,
    "requiere_mandato": False,
    "registrado_en": "2026-11-26T12:00:00Z",
}


def write_json(path: Path, document: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
    return path


def write_input(directory: Path, name: str = "SINT-0001.json", **changes: Any) -> Path:
    """Un archivo de entrada con la transcripción por omisión y los campos que se cambien."""
    transcription = {**make_transcription(entrevista=Path(name).stem), **changes}
    return write_json(directory / name, transcription)


def corpus_input(directory: Path, *, transfer: bool = True, name: str = "SINT-0001.json") -> Path:
    consent = {**CONSENT, "autoriza_transferencia": transfer}
    return write_input(directory, name, origen="corpus", consentimiento=consent)


def go(
    entrada: Path,
    out: Path,
    *,
    environ: Mapping[str, str] | None = None,
    transport: httpx.BaseTransport | None = None,
    perfil: str = PROFILE,
) -> int:
    """Corre `veridicus analyze` por `run`, con un proveedor guionado si no se pasa otro."""
    return run(
        ["analyze", str(entrada), "--perfil", perfil, "--salida", str(out)],
        env() if environ is None else environ,
        transport=ScriptedProvider(echo_finding) if transport is None else transport,
    )


def files_under(directory: Path) -> list[Path]:
    """Todo archivo que quedó bajo un directorio (vacío si no existe)."""
    return sorted(path for path in directory.rglob("*") if path.is_file())
