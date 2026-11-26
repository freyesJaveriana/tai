"""Escritura atómica (BR11.4): nunca queda un archivo final a medias ni un temporal."""

import os
import tempfile
from pathlib import Path
from typing import Any, Self

import pytest

from veridicus_incoherence_analyzer.cli import io_atomic
from veridicus_incoherence_analyzer.cli.io_atomic import AtomicWriteError, write_atomic

pytestmark = pytest.mark.cli


def test_a_write_leaves_the_file_with_its_content_and_no_temporary(tmp_path: Path) -> None:
    target = tmp_path / "SINT-0001.salida.json"

    write_atomic(target, b'{"estado": "ok"}\n')

    assert target.read_bytes() == b'{"estado": "ok"}\n'
    assert [path.name for path in tmp_path.iterdir()] == [target.name]


def test_a_second_write_replaces_the_first_whole(tmp_path: Path) -> None:
    target = tmp_path / "AVISO.txt"
    write_atomic(target, b"uno" * 1000)

    write_atomic(target, b"dos")

    assert target.read_bytes() == b"dos"


@pytest.mark.parametrize("failing", ["fsync", "replace", "mkstemp"])
def test_a_failure_in_any_step_leaves_no_final_file_and_no_temporary(
    failing: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """El sistema de archivos *fake* falla en `mkstemp`, en `fsync` y en `replace` (NFR de BR11.4)."""

    def broken(*args: Any, **kwargs: Any) -> Any:
        raise OSError("fallo simulado del sistema de archivos")

    target = tmp_path / "SINT-0001.salida.json"
    monkeypatch.setattr(tempfile if failing == "mkstemp" else os, failing, broken)

    with pytest.raises(AtomicWriteError):
        write_atomic(target, b"contenido")

    assert list(tmp_path.iterdir()) == [], "ni el archivo final ni un temporal"


def test_a_failure_while_writing_the_bytes_leaves_the_previous_content_intact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "AVISO.txt"
    write_atomic(target, b"anterior")
    real_fdopen = os.fdopen

    class _Failing:
        def __init__(self, handle: Any) -> None:
            self._handle = handle

        def __enter__(self) -> Self:
            return self

        def __exit__(self, *exc: object) -> None:
            self._handle.close()

        def write(self, data: bytes) -> int:
            raise OSError("disco lleno simulado")

    monkeypatch.setattr(os, "fdopen", lambda fd, mode: _Failing(real_fdopen(fd, mode)))

    with pytest.raises(AtomicWriteError):
        write_atomic(target, b"nuevo")

    assert target.read_bytes() == b"anterior"
    assert [path.name for path in tmp_path.iterdir()] == ["AVISO.txt"]


def test_a_failure_to_sync_the_directory_after_the_rename_is_reported(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def broken(*args: Any, **kwargs: Any) -> Any:
        raise OSError("no se puede abrir el directorio")

    monkeypatch.setattr(io_atomic, "_sync_directory", broken)

    with pytest.raises(AtomicWriteError):
        write_atomic(tmp_path / "x.json", b"1")

    assert [path.name for path in tmp_path.iterdir()] == ["x.json"], "ya estaba renombrado entero"
