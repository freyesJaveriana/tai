"""Dockerfile e ignorados de la imagen de la CLI (CA-3; team.md, Deployment).

Lee los archivos, no construye la imagen (el *build* real lo hace la CI). Cada regla tiene un control
negativo: un Dockerfile de prueba que la rompe debe fallar la comprobación.
"""

import re
import shlex
from pathlib import Path

import pytest

DEPLOY = Path(__file__).resolve().parents[1]
ROOT = DEPLOY.parent
DOCKERFILE = DEPLOY / "images" / "analyzer-cli" / "Dockerfile"
DOCKERIGNORE = ROOT / ".dockerignore"

DIGEST = "sha256:191083cdf6c7bda8c76158983163ead5d5cf7b77cf3033e805bb0f5296f51b4b"
UV_DIGEST = "sha256:d3b601f0c7b118bc1753febf7c41cc80981df678445e0254284eecf84db79a7d"
REAL_DIGEST = re.compile(r"@sha256:[0-9a-f]{64}(?:\s|$)")


def _instructions(text: str) -> list[tuple[str, str]]:
    """Pares (instrucción, resto) sin comentarios y con las continuaciones de línea unidas."""
    joined = re.sub(r"\\\s*\n", " ", text)
    pairs: list[tuple[str, str]] = []
    for line in joined.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        # El analizador de Dockerfile acepta cualquier espacio en blanco, también el tabulador (F-06).
        parts = re.split(r"\s+", stripped, maxsplit=1)
        pairs.append((parts[0].upper(), parts[1].strip() if len(parts) > 1 else ""))
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


def _references(keyword: str, rest: str) -> list[str]:
    """Lo que una instrucción trae de fuera de su etapa: `COPY --from=` y `RUN --mount=...from=`.

    `ONBUILD <instrucción>` se mira como la instrucción que envuelve (F-07).
    """
    if keyword == "ONBUILD":
        inner = re.split(r"\s+", rest, maxsplit=1)
        return _references(inner[0].upper(), inner[1] if len(inner) > 1 else "")
    found: list[str] = []
    for token in _tokens(rest):
        if keyword == "COPY" and token.startswith("--from="):
            found.append(token.removeprefix("--from="))
        elif keyword == "RUN" and token.startswith("--mount="):
            for item in _mount_fields(token.removeprefix("--mount=")):
                if item.lower().startswith("from="):
                    found.append(item[len("from=") :])
    return found


def _tokens(rest: str) -> list[str]:
    """Las palabras de una instrucción como las lee un shell: las comillas agrupan y se quitan (K-97).

    Si las comillas no cierran (un `RUN` con un apóstrofo en su texto), se vuelve a partir por espacios.
    """
    try:
        return shlex.split(rest)
    except ValueError:
        return rest.split()


def _mount_fields(value: str) -> list[str]:
    """Los campos `clave=valor` de un `--mount`, al estilo CSV: separados por comas y con comillas
    en cualquier campo, que se quitan (K-97). Quitar todas las comillas puede juntar de más, y eso
    solo hace la regla más estricta."""
    return [field.strip() for field in re.sub(r"[\"']", "", value).split(",")]


def check_copy_from_pinned(text: str) -> list[str]:
    """Toda imagen externa (`COPY --from`, `RUN --mount from=`, también tras `ONBUILD`) lleva un
    digest real. Una etapa solo es interna si se declara ANTES de usarse: por nombre (`AS build`)
    o por número, que debe ser menor que la cantidad de `FROM` ya vistos (F-07)."""
    stages: set[str] = set()
    declared = 0
    problems: list[str] = []
    for keyword, rest in _instructions(text):
        if keyword == "FROM":
            named = re.search(r"\sas\s+(\S+)\s*$", rest, re.IGNORECASE)
            if named:
                stages.add(named.group(1).lower())
            declared += 1
            continue
        for source in _references(keyword, rest):
            internal = source.lower() in stages or (source.isdigit() and int(source) < declared)
            if not internal and not REAL_DIGEST.search(source + " "):
                problems.append(f"{keyword} con imagen sin digest real: {source}")
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
    assert "REEMPLAZAR" not in real, "ningún marcador de digest pendiente"


def test_the_final_user_is_numeric_and_not_root(real: str) -> None:
    assert check_final_user(real) == []
    assert _instructions(real)[-2:][0] == ("USER", "10001:10001")


def test_the_entrypoint_is_the_demo_module_in_exec_form(real: str) -> None:
    last = _instructions(real)[-1]

    assert last == (
        "ENTRYPOINT",
        '["/app/.venv/bin/python", "-m", "veridicus_demo.entrypoint"]',
    )


UV_COPY = re.compile(r"^--from=ghcr\.io/astral-sh/uv:\d+\.\d+\.\d+(?:@\S+)? /uv /usr/local/bin/uv$")


def test_the_build_stage_uses_uv_sync_frozen_no_dev_no_editable(real: str) -> None:
    runs = [rest for keyword, rest in _instructions(real) if keyword == "RUN"]

    assert any("uv sync --frozen --no-dev --no-editable" in run for run in runs)
    assert not any("pip install" in run for run in runs), "F-01: uv ya no se instala con pip"


def test_uv_is_copied_from_the_official_image_pinned_by_version(real: str) -> None:
    copies = [rest for keyword, rest in _instructions(real) if keyword == "COPY"]

    assert sum(1 for copy in copies if UV_COPY.match(copy)) == 1, "uv:<versión> en una línea COPY"


def test_every_copy_from_an_external_image_has_a_real_digest(real: str) -> None:
    """F-01, estricta: sin marcador ni xfail; exige el digest real del índice de uv 0.13.9."""
    assert check_copy_from_pinned(real) == []
    assert UV_DIGEST in real
    assert "REEMPLAZAR" not in real


FIXED_LIBZSTD = "libzstd1=1.5.7+dfsg-1+deb13u1"


def test_the_final_stage_upgrades_libzstd1_to_the_fixed_version_before_the_user(real: str) -> None:
    """Trivy: CVE-2026-124851 (HIGH, con corrección) en libzstd1 de la base. El digest de la base no
    cambia, así que la etapa final actualiza ese paquete, fijado por versión (DL3008), sin
    `.trivyignore`."""
    final = "FROM " + real.rsplit("\nFROM ", 1)[1]
    instructions = _instructions(final)
    upgrades = [
        (number, rest)
        for number, (keyword, rest) in enumerate(instructions)
        if keyword == "RUN" and "apt-get install" in rest
    ]

    assert len(upgrades) == 1
    number, run = upgrades[0]
    assert run.startswith("apt-get update"), "el índice se actualiza en la misma capa"
    assert "--only-upgrade" in run
    assert "-y" in run.split()
    assert "--no-install-recommends" in run
    assert FIXED_LIBZSTD in run.split(), "versión fijada y corregida"
    assert run.index("apt-get install") < run.index("rm -rf /var/lib/apt/lists/*")
    assert run.endswith("rm -rf /var/lib/apt/lists/*"), "la capa no conserva las listas de apt"
    users = [i for i, (keyword, _) in enumerate(instructions) if keyword == "USER"]
    assert number < users[-1], "se actualiza como root, antes del USER numérico"
    assert "libzstd1" not in real.rsplit("\nFROM ", 1)[0], "solo la etapa final lo toca"
    assert not (ROOT / ".trivyignore").exists(), "ninguna excepción de Trivy"


def test_the_final_stage_stays_pinned_numeric_and_without_latest_after_the_upgrade(
    real: str,
) -> None:
    assert check_from_pinned(real) == []
    assert check_copy_from_pinned(real) == []
    assert check_final_user(real) == []
    assert check_latest_anywhere(real) == []
    assert DIGEST in real


def test_the_final_stage_copies_only_the_virtual_environment(real: str) -> None:
    final = real.rsplit("\nFROM ", 1)[1]
    copies = [rest for keyword, rest in _instructions("FROM " + final) if keyword == "COPY"]

    assert copies == ["--from=build /app/.venv /app/.venv"]


SOURCE_LABEL = 'org.opencontainers.image.source="https://github.com/freyesJaveriana/tai"'


def test_the_final_stage_carries_the_oci_source_label_that_links_the_ghcr_package(
    real: str,
) -> None:
    """Sin esta etiqueta el paquete de GHCR no se vincula al repositorio y el GITHUB_TOKEN no puede
    publicarlo (F-04)."""
    final = real.rsplit("\nFROM ", 1)[1]
    labels = [rest for keyword, rest in _instructions("FROM " + final) if keyword == "LABEL"]
    build = real.rsplit("\nFROM ", 1)[0]

    assert labels == [SOURCE_LABEL]
    assert "LABEL" not in build, "solo la etapa final lleva la etiqueta"


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


# --- Ronda 3 (F-06, F-07): cualquier espacio en blanco, ONBUILD, RUN --mount y etapas posteriores -----

PINNED_A = "img:1@sha256:" + "a" * 64


def test_negative_control_f06_user_root_separated_by_a_tab_fails() -> None:
    text = "FROM x AS a\nUSER 10001:10001\nUSER\t0\n"

    assert check_final_user(text) != []


def test_negative_control_f06_from_without_digest_separated_by_a_tab_fails() -> None:
    assert check_from_pinned("FROM\tpython:3.12-slim AS a\n") != []
    assert check_from_pinned("FROM python:3.12-slim\tAS\ta\n") != []


def test_negative_control_f06_copy_from_without_digest_separated_by_a_tab_fails() -> None:
    assert check_copy_from_pinned("FROM x AS a\nCOPY\t--from=img:1 /a /b\n") != []
    assert check_copy_from_pinned("FROM x AS a\nCOPY --from=img:1\t/a\t/b\n") != []


@pytest.mark.parametrize("keyword", ["COPY", "ADD"])
def test_negative_control_f06_copying_env_separated_by_a_tab_fails(keyword: str) -> None:
    assert check_no_forbidden_copy(f"FROM x\n{keyword}\t.env /app/.env\n") != []


def test_f06_a_well_formed_dockerfile_with_tabs_still_passes_every_check() -> None:
    text = (
        f"FROM\tpython:3.12-slim@{DIGEST}\tAS\tbuild\n"
        f"COPY\t--from={PINNED_A}\t/uv\t/usr/local/bin/uv\n"
        f"FROM\tpython:3.12-slim@{DIGEST}\tAS\tfinal\n"
        "COPY\t--from=build\t/app/.venv\t/app/.venv\n"
        "USER\t10001:10001\n"
    )

    assert check_from_pinned(text) == []
    assert check_copy_from_pinned(text) == []
    assert check_final_user(text) == []
    assert check_no_forbidden_copy(text) == []


@pytest.mark.parametrize(
    "line",
    [
        "ONBUILD COPY --from=img:1 /a /b",
        "ONBUILD\tCOPY\t--from=img:1\t/a\t/b",
        "onbuild copy --from=img:1 /a /b",
        "RUN --mount=type=bind,from=img:1,target=/x,source=/y true",
        "RUN\t--mount=type=bind,target=/x,from=img:1\ttrue",
        "RUN --network=none --mount=type=cache,target=/c --mount=from=img:1,target=/x true",
        "ONBUILD RUN --mount=type=bind,from=img:1,target=/x true",
    ],
)
def test_negative_control_f07_other_ways_to_pull_an_external_image_without_digest_fail(
    line: str,
) -> None:
    assert check_copy_from_pinned(f"FROM x AS a\n{line}\n") != []


@pytest.mark.parametrize(
    "line",
    [
        f"ONBUILD COPY --from={PINNED_A} /a /b",
        f"RUN --mount=type=bind,from={PINNED_A},target=/x true",
        "RUN --mount=type=cache,target=/c true",
        "RUN --mount=type=bind,from=a,target=/x true",
        "ONBUILD RUN true",
    ],
)
def test_f07_pinned_or_internal_references_in_onbuild_and_mounts_pass(line: str) -> None:
    assert check_copy_from_pinned(f"FROM x AS a\n{line}\n") == []


def test_negative_control_f07_a_stage_declared_after_its_use_is_not_internal() -> None:
    text = "FROM x AS a\nCOPY --from=uv /uv /usr/local/bin/uv\nFROM y AS uv\n"

    assert check_copy_from_pinned(text) != []


def test_negative_control_f07_a_mount_from_a_later_stage_is_not_internal() -> None:
    text = "FROM x AS a\nRUN --mount=from=uv,target=/x true\nFROM y AS uv\n"

    assert check_copy_from_pinned(text) != []


def test_negative_control_f07_a_numeric_stage_that_does_not_exist_yet_fails() -> None:
    assert check_copy_from_pinned("FROM x AS a\nCOPY --from=1 /a /b\nFROM y\n") != []


def test_f07_a_stage_declared_before_its_use_is_internal() -> None:
    text = "FROM x AS uv\nFROM y AS a\nCOPY --from=uv /uv /b\nRUN --mount=from=0,target=/x true\n"

    assert check_copy_from_pinned(text) == []


# --- K-97: la clave `from=` sin distinguir mayúsculas y los campos de `--mount` con comillas --------


@pytest.mark.parametrize(
    "line",
    [
        "RUN --mount=type=cache,FROM=img:latest,target=/c true",
        "RUN --mount=type=cache,FROM=img:latest",
        "RUN --mount=type=bind,From=img:1,target=/x true",
        'RUN --mount="type=bind,from=img" true',
        "RUN --mount='type=bind,from=img' true",
        'RUN --mount=type=bind,"from=img:1",target=/x true',
        'RUN --mount=type=bind,"FROM=img:1",target=/x true',
        "RUN --mount=type=bind,'from=img:1',target=/x true",
        'ONBUILD RUN --mount="type=bind,FROM=img:1" true',
        'RUN --mount="type=cache,target=/c" --mount="type=bind,from=img:1,target=/x" true',
    ],
)
def test_negative_k97_a_mount_from_an_image_without_a_digest_fails_in_any_spelling(
    line: str,
) -> None:
    assert check_copy_from_pinned(f"FROM x AS a\n{line}\n") != []


@pytest.mark.parametrize(
    "line",
    [
        f"RUN --mount=type=bind,FROM={PINNED_A},target=/x true",
        f'RUN --mount="type=bind,from={PINNED_A},target=/x" true',
        f'RUN --mount=type=bind,"from={PINNED_A}",target=/x true',
        'RUN --mount="type=cache,target=/c" true',
        'RUN --mount="type=bind,FROM=a,target=/x" true',
        "RUN --mount=type=bind,From=0,target=/x true",
    ],
)
def test_k97_a_mount_with_a_real_digest_or_from_an_internal_stage_passes_in_any_spelling(
    line: str,
) -> None:
    assert check_copy_from_pinned(f"FROM x AS a\n{line}\n") == []


@pytest.mark.parametrize(
    "line",
    [
        'RUN --mount=type=bind,"from=img:1",target=/x echo it\'s',
        'RUN --mount=type=bind,"FROM=img:1",target=/x echo it\'s',
        "RUN --mount=type=bind,'from=img:1',target=/x echo it\"s",
    ],
)
def test_negative_k97_a_run_with_an_unbalanced_quote_still_reads_the_quoted_mount_fields(
    line: str,
) -> None:
    assert check_copy_from_pinned(f"FROM x AS a\n{line}\n") != []


def test_k97_a_run_with_an_unbalanced_quote_and_a_pinned_mount_passes() -> None:
    line = f'RUN --mount=type=bind,"from={PINNED_A}",target=/x echo it\'s'

    assert check_copy_from_pinned(f"FROM x AS a\n{line}\n") == []


def test_k97_a_quoted_mount_value_with_a_space_is_read_whole() -> None:
    line = 'RUN --mount="type=bind,target=/a b,from=img:1" true'

    assert check_copy_from_pinned(f"FROM x AS a\n{line}\n") != []
