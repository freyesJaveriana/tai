"""El directorio de resultados y la regla del corpus (BR11.5, BR11.6; R-11).

Git real sobre repositorios temporales: el directorio ignorado se acepta, el que Git rastrea se
rechaza (control negativo), y fuera de todo repositorio se permite. El `.gitignore` del repositorio
cubre `resultados-locales/` y Git no rastrea nada ahí; la prueba lo comprueba con `git check-ignore` y
`git ls-files`, con su control negativo (una ruta que Git sí rastrea).
"""

import subprocess
from datetime import date
from pathlib import Path

import pytest

from tests.cli.helpers import corpus_input, files_under, go, write_input
from tests.support import ScriptedProvider, echo_finding
from veridicus_incoherence_analyzer.cli.results_dir import (
    default_output_dir,
    is_safe_for_corpus,
    is_writable,
)

pytestmark = pytest.mark.cli

ROOT = Path(__file__).resolve().parents[4]
# BR11.6: a cualquier profundidad (la corrida manual escribe bajo libs/<paquete>/resultados-locales/).
ANYWHERE = ":(glob)**/resultados-locales/**"


def _git(directory: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603 - argumentos fijos, sin entrada externa
        ["git", "-C", str(directory), *arguments],  # noqa: S607 - `git` del PATH
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )


def _repository(directory: Path, ignore: str | None) -> Path:
    directory.mkdir()
    assert _git(directory, "init", "-q").returncode == 0
    if ignore is not None:
        (directory / ".gitignore").write_text(ignore, encoding="utf-8")
    return directory


def test_the_default_directory_is_resultados_locales_with_the_date_and_the_subcommand() -> None:
    assert default_output_dir(date(2026, 11, 27)) == Path("resultados-locales/2026-11-27-analyze")


def test_a_directory_ignored_by_git_is_safe_for_the_corpus(tmp_path: Path) -> None:
    repo = _repository(tmp_path / "repo", "resultados-locales/\n")

    assert is_safe_for_corpus(repo / "resultados-locales" / "2026-11-27-analyze")


def test_negative_control_a_directory_that_git_tracks_is_not_safe_for_the_corpus(
    tmp_path: Path,
) -> None:
    repo = _repository(tmp_path / "repo", "resultados-locales/\n")

    assert not is_safe_for_corpus(repo / "docs")
    assert not is_safe_for_corpus(repo)


def test_a_directory_outside_every_repository_is_safe_for_the_corpus(tmp_path: Path) -> None:
    assert is_safe_for_corpus(tmp_path / "carpeta-del-proyecto-en-zine" / "salida")


def test_when_git_is_not_available_a_directory_inside_a_repository_is_not_safe(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _repository(tmp_path / "repo", "resultados-locales/\n")
    monkeypatch.setenv("PATH", str(tmp_path / "sin-git"))

    assert not is_safe_for_corpus(repo / "resultados-locales" / "x")


def test_a_directory_is_writable_when_its_nearest_existing_ancestor_is(tmp_path: Path) -> None:
    assert is_writable(tmp_path / "a" / "b" / "c")
    (tmp_path / "archivo").write_text("x", encoding="utf-8")
    assert not is_writable(tmp_path / "archivo" / "salida")


def test_the_cli_refuses_a_corpus_transcription_for_a_tracked_output_directory_and_writes_nothing(
    tmp_path: Path,
) -> None:
    repo = _repository(tmp_path / "repo", "resultados-locales/\n")
    provider = ScriptedProvider(echo_finding)

    code = go(corpus_input(tmp_path), repo / "docs" / "salida", transport=provider)

    assert code == 2
    assert provider.request_count == 0
    assert files_under(repo / "docs") == [], "nada escrito"


def test_the_cli_analyzes_a_corpus_transcription_into_a_directory_that_git_ignores(
    tmp_path: Path,
) -> None:
    repo = _repository(tmp_path / "repo", "resultados-locales/\n")
    out = repo / "resultados-locales" / "prueba"

    code = go(corpus_input(tmp_path), out)

    assert code == 0
    assert (out / "SINT-0001.salida.json").is_file()
    status = _git(repo, "status", "--porcelain", "--untracked-files=all")
    assert status.stdout.strip() == "?? .gitignore", "Git no ve ninguna salida"


def test_a_synthetic_transcription_may_go_to_a_tracked_directory(tmp_path: Path) -> None:
    """La regla es del origen `corpus`: lo sintético no la necesita."""
    repo = _repository(tmp_path / "repo", None)

    assert go(write_input(tmp_path), repo / "salida") == 0


def test_the_repository_ignores_resultados_locales_and_tracks_nothing_there() -> None:
    """BR11.6: `.gitignore` cubre `resultados-locales/` y `git ls-files` no devuelve nada ahí."""
    ignored = _git(ROOT, "check-ignore", "resultados-locales/x.salida.json")
    tracked = _git(ROOT, "ls-files", ANYWHERE)

    assert ignored.returncode == 0, ignored.stderr
    assert tracked.returncode == 0 and tracked.stdout == "", f"Git rastrea: {tracked.stdout}"


def test_negative_control_the_same_checks_fail_for_a_path_that_git_tracks() -> None:
    ignored = _git(ROOT, "check-ignore", "libs/incoherence_analyzer/pyproject.toml")
    tracked = _git(ROOT, "ls-files", "libs/incoherence_analyzer/pyproject.toml")

    assert ignored.returncode != 0, "una ruta rastreada no está ignorada"
    assert tracked.stdout.strip() != "", "y `git ls-files` la devuelve"


def test_negative_control_a_synthetic_tracked_file_makes_the_ls_files_check_fail(
    tmp_path: Path,
) -> None:
    """En un repositorio temporal, un archivo añadido a la fuerza bajo resultados-locales/ se ve."""
    repo = _repository(tmp_path / "repo", "resultados-locales/\n")
    stray = repo / "resultados-locales" / "sintetico.salida.json"
    stray.parent.mkdir()
    stray.write_text("{}", encoding="utf-8")
    assert _git(repo, "add", "-f", "resultados-locales/sintetico.salida.json").returncode == 0

    tracked = _git(repo, "ls-files", ANYWHERE)

    assert tracked.stdout.strip() == "resultados-locales/sintetico.salida.json"


def test_negative_control_a_tracked_file_in_a_nested_results_directory_is_seen(
    tmp_path: Path,
) -> None:
    """F-02: la corrida manual escribe en `libs/<paquete>/resultados-locales/`, no en la raíz."""
    repo = _repository(tmp_path / "repo", "resultados-locales/\n")
    stray = repo / "libs" / "paquete" / "resultados-locales" / "manual" / "x.salida.json"
    stray.parent.mkdir(parents=True)
    stray.write_text("{}", encoding="utf-8")
    assert _git(repo, "add", "-f", str(stray.relative_to(repo))).returncode == 0

    assert _git(repo, "ls-files", "resultados-locales").stdout.strip() == "", "la raíz no lo ve"
    nested = _git(repo, "ls-files", ANYWHERE)
    assert nested.stdout.strip() == "libs/paquete/resultados-locales/manual/x.salida.json"


def test_a_symbolic_link_to_a_tracked_directory_is_not_safe_for_the_corpus(
    tmp_path: Path,
) -> None:
    """F-01: se evalúa donde realmente se escribe, no por el nombre del enlace."""
    repo = _repository(tmp_path / "repo", "resultados-locales/\n")
    (repo / "docs").mkdir()
    link = tmp_path / "afuera"
    link.symlink_to(repo / "docs", target_is_directory=True)
    provider = ScriptedProvider(echo_finding)

    assert not is_safe_for_corpus(link / "salida")
    assert go(corpus_input(tmp_path), link / "salida", transport=provider) == 2
    assert provider.request_count == 0
    assert files_under(repo / "docs") == []


def test_a_symbolic_link_from_a_repository_to_an_outside_directory_is_safe(
    tmp_path: Path,
) -> None:
    repo = _repository(tmp_path / "repo", "resultados-locales/\n")
    outside = tmp_path / "fuera-de-git"
    outside.mkdir()
    (repo / "enlace").symlink_to(outside, target_is_directory=True)

    assert is_safe_for_corpus(repo / "enlace" / "salida")
