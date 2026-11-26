"""Dockerfile e ignorados de la imagen de la CLI (CA-3; team.md, Deployment).

Lee los archivos, no construye la imagen (el *build* real lo hace la CI). Cada regla tiene un control
negativo: un Dockerfile de prueba que la rompe debe fallar la comprobación.
"""

import re
from pathlib import Path

import pytest

DEPLOY = Path(__file__).resolve().parents[1]
ROOT = DEPLOY.parent
DOCKERFILE = DEPLOY / "images" / "analyzer-cli" / "Dockerfile"
DOCKERIGNORE = ROOT / ".dockerignore"

DIGEST = "sha256:191083cdf6c7bda8c76158983163ead5d5cf7b77cf3033e805bb0f5296f51b4b"
REAL_DIGEST = re.compile(r"@sha256:[0-9a-f]{64}(?:\s|$)")


def _instructions(text: str) -> list[tuple[str, str]]:
    """Pares (instrucción, resto) sin comentarios y con las continuaciones de línea unidas."""
    joined = re.sub(r"\\\s*\n", " ", text)
    pairs: list[tuple[str, str]] = []
    for line in joined.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        keyword, _, rest = stripped.partition(" ")
        pairs.append((keyword.upper(), rest.strip()))
    return pairs


def check_from_pinned(text: str) -> list[str]:
    """Cada FROM lleva un digest real (`@sha256:` de 64 hex) y ninguno usa `latest`."""
    problems: list[str] = []
    for keyword, rest in _instructions(text):
        if keyword != "FROM":
            continue
        image = rest.split()[0]
        if not REAL_DIGEST.search(image + " "):
            problems.append(f"FROM sin digest real: {image}")
        if ":latest" in image:
            problems.append(f"FROM con latest: {image}")
    return problems


def check_copy_from_pinned(text: str) -> list[str]:
    """Todo `COPY --from=<imagen>` lleva un digest real. Una etapa propia (`AS build`) no es imagen."""
    instructions = _instructions(text)
    stages = {
        rest.lower().split(" as ")[1].split()[0]
        for keyword, rest in instructions
        if keyword == "FROM" and " as " in rest.lower()
    }
    problems: list[str] = []
    for keyword, rest in instructions:
        if keyword != "COPY":
            continue
        for part in rest.split():
            if not part.startswith("--from="):
                continue
            source = part.removeprefix("--from=")
            if source.lower() in stages or source.isdigit():
                continue
            if not REAL_DIGEST.search(source + " "):
                problems.append(f"COPY --from sin digest real: {source}")
    return problems


def check_final_user(text: str) -> list[str]:
    """El último USER es numérico (uid[:gid]) y distinto de 0."""
    users = [rest for keyword, rest in _instructions(text) if keyword == "USER"]
    if not users:
        return ["sin USER: la imagen correría como root"]
    uid = users[-1].split(":")[0]
    if not uid.isdigit():
        return [f"USER no numérico: {users[-1]}"]
    if int(uid) == 0:
        return ["USER final es root (0)"]
    return []


def check_no_forbidden_copy(text: str) -> list[str]:
    """Ningún COPY/ADD trae `.env`, `tests` ni `resultados-locales`."""
    problems: list[str] = []
    for keyword, rest in _instructions(text):
        if keyword not in ("COPY", "ADD"):
            continue
        sources = [part for part in rest.split() if not part.startswith("--")][:-1]
        for source in sources:
            parts = Path(source).parts
            if any(
                part == "tests" or part == "resultados-locales" or part.startswith(".env")
                for part in parts
            ):
                problems.append(f"{keyword} de {source}")
    return problems


def check_latest_anywhere(text: str) -> list[str]:
    return [f"latest: {line.strip()}" for line in text.splitlines() if ":latest" in line]


def check_ignore(text: str) -> list[str]:
    """`.dockerignore` excluye `.env`, `**/tests`, `**/.venv` y `resultados-locales`."""
    lines = {line.strip() for line in text.splitlines() if line.strip()}
    required = {
        ".env",
        "**/.env.*",
        "**/*.pem",
        "**/*.key",
        "**/kubeconfig*",
        "**/secrets*.yaml",
        "**/tests",
        "**/.venv",
        "resultados-locales",
    }
    return [
        f"falta {rule}"
        for rule in sorted(required)
        if rule not in lines and f"{rule}/" not in lines
    ]


# --- El Dockerfile real --------------------------------------------------------------------------


@pytest.fixture(name="real")
def real_dockerfile() -> str:
    return DOCKERFILE.read_text(encoding="utf-8")


def test_every_from_of_the_real_dockerfile_has_a_real_digest_and_none_uses_latest(
    real: str,
) -> None:
    assert check_from_pinned(real) == []
    assert check_latest_anywhere(real) == []
    assert DIGEST in real, "el digest del índice multiarquitectura de python:3.12-slim"
    assert "REEMPLAZAR_DIGEST" not in real


def test_the_final_user_is_numeric_and_not_root(real: str) -> None:
    assert check_final_user(real) == []
    assert _instructions(real)[-2:][0] == ("USER", "10001:10001")


def test_the_entrypoint_is_the_demo_module_in_exec_form(real: str) -> None:
    last = _instructions(real)[-1]

    assert last == (
        "ENTRYPOINT",
        '["/app/.venv/bin/python", "-m", "veridicus_demo.entrypoint"]',
    )


UV_COPY = re.compile(
    r"^--from=ghcr\.io/astral-sh/uv:\d+\.\d+\.\d+(?:@\S+)? /uv /usr/local/bin/uv$"
)


def test_the_build_stage_uses_uv_sync_frozen_no_dev_no_editable(real: str) -> None:
    runs = [rest for keyword, rest in _instructions(real) if keyword == "RUN"]

    assert any("uv sync --frozen --no-dev --no-editable" in run for run in runs)
    assert not any("pip install" in run for run in runs), "F-01: uv ya no se instala con pip"


def test_uv_is_copied_from_the_official_image_pinned_by_version(real: str) -> None:
    copies = [rest for keyword, rest in _instructions(real) if keyword == "COPY"]

    assert sum(1 for copy in copies if UV_COPY.match(copy)) == 1, "uv:<versión> en una línea COPY"


@pytest.mark.xfail(
    strict=True,
    reason="F-01: la línea de uv lleva REEMPLAZAR_DIGEST_UV hasta que el humano traiga el digest; "
    "al ponerlo, esta prueba pasa y el xfail estricto obliga a quitar esta marca",
)
def test_every_copy_from_an_external_image_has_a_real_digest(real: str) -> None:
    assert check_copy_from_pinned(real) == []


def test_the_only_external_copy_from_without_a_real_digest_is_the_uv_placeholder(
    real: str,
) -> None:
    """Mientras dure el xfail, el único pendiente es uv y nada más se cuela sin digest."""
    problems = check_copy_from_pinned(real)

    assert all("astral-sh/uv" in problem for problem in problems)
    assert len(problems) <= 1


def test_the_final_stage_copies_only_the_virtual_environment(real: str) -> None:
    final = real.rsplit("\nFROM ", 1)[1]
    copies = [rest for keyword, rest in _instructions("FROM " + final) if keyword == "COPY"]

    assert copies == ["--from=build /app/.venv /app/.venv"]


def test_no_copy_of_env_tests_or_local_results_and_no_secret_in_the_image(real: str) -> None:
    assert check_no_forbidden_copy(real) == []
    assert not re.search(r"sk-[A-Za-z0-9_-]{6,}", real), "ninguna clave en el Dockerfile"
    assert not re.search(
        r"^\s*(ENV|ARG)\s+\S*(KEY|TOKEN|SECRET)", real, re.IGNORECASE | re.MULTILINE
    )


def test_the_dockerignore_excludes_secrets_tests_venvs_and_local_results() -> None:
    text = DOCKERIGNORE.read_text(encoding="utf-8")

    assert check_ignore(text) == []
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    assert lines[0] == "*", "se excluye todo salvo contracts/, libs/ y deploy/"
    for kept in ("!contracts", "!libs", "!deploy"):
        assert kept in lines
    for noisy in ("**/__pycache__", "coverage.json"):
        assert noisy in lines


# --- Controles negativos: cada regla falla con un Dockerfile que la rompe --------------------------


def test_negative_control_a_from_without_digest_fails(tmp_path: Path) -> None:
    bad = tmp_path / "Dockerfile"
    bad.write_text("FROM python:3.12-slim\nUSER 10001:10001\n", encoding="utf-8")

    assert check_from_pinned(bad.read_text(encoding="utf-8")) != []


def test_negative_control_the_placeholder_digest_fails(tmp_path: Path) -> None:
    bad = tmp_path / "Dockerfile"
    bad.write_text("FROM python:3.12-slim@sha256:REEMPLAZAR_DIGEST\n", encoding="utf-8")

    assert check_from_pinned(bad.read_text(encoding="utf-8")) != []


def test_negative_control_latest_fails(tmp_path: Path) -> None:
    bad = tmp_path / "Dockerfile"
    bad.write_text(f"FROM python:latest@{DIGEST}\n", encoding="utf-8")
    text = bad.read_text(encoding="utf-8")

    assert check_from_pinned(text) != []
    assert check_latest_anywhere(text) != []


def test_negative_control_user_root_fails(tmp_path: Path) -> None:
    bad = tmp_path / "Dockerfile"
    bad.write_text("FROM x\nUSER root\n", encoding="utf-8")
    zero = tmp_path / "Dockerfile.zero"
    zero.write_text("FROM x\nUSER 0:0\n", encoding="utf-8")
    none = tmp_path / "Dockerfile.none"
    none.write_text("FROM x\n", encoding="utf-8")

    assert check_final_user(bad.read_text(encoding="utf-8")) != []
    assert check_final_user(zero.read_text(encoding="utf-8")) != []
    assert check_final_user(none.read_text(encoding="utf-8")) != []


@pytest.mark.parametrize(
    "source", [".env", "deploy/tests", "libs/a/tests/x.py", "resultados-locales"]
)
def test_negative_control_copying_a_forbidden_path_fails(source: str, tmp_path: Path) -> None:
    bad = tmp_path / "Dockerfile"
    bad.write_text(f"FROM x\nCOPY {source} /app/\n", encoding="utf-8")

    assert check_no_forbidden_copy(bad.read_text(encoding="utf-8")) != []


def test_negative_control_a_dockerignore_missing_a_rule_fails(tmp_path: Path) -> None:
    bad = tmp_path / ".dockerignore"
    bad.write_text("*\n!deploy\n.env\n", encoding="utf-8")

    problems = check_ignore(bad.read_text(encoding="utf-8"))

    assert len(problems) == 8
    for rule in ("**/.env.*", "**/*.pem", "**/*.key", "**/kubeconfig*", "**/secrets*.yaml"):
        assert f"falta {rule}" in problems, "F-02: cada patrón de secretos se exige"


@pytest.mark.parametrize(
    "reference",
    [
        "ghcr.io/astral-sh/uv:0.13.9",
        "ghcr.io/astral-sh/uv:0.13.9@sha256:REEMPLAZAR_DIGEST_UV",
        "ghcr.io/astral-sh/uv:latest",
        "ghcr.io/astral-sh/uv:0.13.9@sha256:" + "a" * 63,
    ],
)
def test_negative_control_a_copy_from_without_a_real_digest_fails(reference: str) -> None:
    text = f"FROM x AS build\nCOPY --from={reference} /uv /usr/local/bin/uv\n"

    assert check_copy_from_pinned(text) != []


def test_a_copy_from_with_a_real_digest_or_from_an_own_stage_passes() -> None:
    pinned = "ghcr.io/astral-sh/uv:0.13.9@sha256:" + "a" * 64
    text = (
        "FROM x AS build\n"
        f"COPY --from={pinned} /uv /usr/local/bin/uv\n"
        "FROM x AS final\n"
        "COPY --from=build /app/.venv /app/.venv\n"
        "COPY --from=0 /a /b\n"
    )

    assert check_copy_from_pinned(text) == []
