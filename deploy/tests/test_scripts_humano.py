"""Los scripts del humano (paso 7): se leen como texto y nunca se ejecutan.

Cada regla lleva su control negativo: un script de `deploy/tests/fixtures/humano/` con ese único
defecto. Las operaciones del clúster se arman con fragmentos para que este archivo no contenga
ninguna de las que prohíbe la comprobación de AUTONOMIA-01.
"""

import re
from pathlib import Path

import pytest
from autonomia import MARK
from humano_checks import PINNED, REAL_DIGEST, violations
from support import DEPLOY

ROOT = DEPLOY.parent
HUMANO = ROOT / "scripts" / "humano"
FIXTURES = DEPLOY / "tests" / "fixtures" / "humano"
K = "kube" + "ctl"
SCRIPTS = ["crear-pull-secret-ghcr.sh", "crear-secret-anthropic.sh", "demo-analyzer.sh"]


def _text(name: str) -> str:
    return (HUMANO / name).read_text(encoding="utf-8")


def _lines(name: str) -> list[str]:
    return [
        line.strip()
        for line in _text(name).splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


@pytest.mark.parametrize("name", SCRIPTS)
def test_every_human_script_passes_all_the_rules(name: str) -> None:
    assert violations(f"scripts/humano/{name}", _text(name)) == []


@pytest.mark.parametrize("name", SCRIPTS)
def test_every_human_script_opens_with_the_shebang_and_the_mark(name: str) -> None:
    lines = _text(name).splitlines()
    assert lines[0] == "#!/usr/bin/env bash"
    assert lines[1] == MARK


def test_the_fixture_that_meets_every_rule_passes() -> None:
    text = (FIXTURES / "ok.sh").read_text(encoding="utf-8")
    assert violations("ok.sh", text) == []


NEGATIVES = {
    "sin-marca.sh": "falta la marca",
    "sin-pipefail.sh": "falta «set -euo pipefail»",
    "sin-trap.sh": "falta el trap",
    "echo-clave.sh": "echo o printf de una variable secreta",
    "printf-token.sh": "echo o printf de una variable secreta",
    "from-literal.sh": "from-literal",
    "password-argumento.sh": "--docker-password o --password",
    "source-env.sh": "source o punto sobre un archivo",
    "punto-env.sh": "source o punto sobre un archivo",
    "set-x.sh": "set -x o allexport",
    "allexport.sh": "set -x o allexport",
    "clave-en-kubectl.sh": "variable secreta como argumento de kubectl",
    "eval.sh": "eval",
}


@pytest.mark.parametrize("name", NEGATIVES)
def test_negative_a_script_with_one_defect_fails_its_rule(name: str) -> None:
    text = (FIXTURES / name).read_text(encoding="utf-8")
    found = violations(name, text)
    assert any(NEGATIVES[name] in item for item in found), found


def test_probe_5_the_key_on_the_command_line_fails() -> None:
    text = (FIXTURES / "from-literal.sh").read_text(encoding="utf-8")
    assert any("from-literal" in item for item in violations("x.sh", text))


def test_a_comment_that_names_a_forbidden_form_does_not_fail() -> None:
    text = (FIXTURES / "ok.sh").read_text(encoding="utf-8")
    commented = text + "# no se usa --from-literal ni source ni echo $clave\n"
    assert violations("ok.sh", commented) == []


def test_a_continued_line_is_read_as_one() -> None:
    text = (FIXTURES / "ok.sh").read_text(encoding="utf-8")
    broken = text + f"{K} create secret generic x \\\n  --from-literal=a=b\n"
    assert any("from-literal" in item for item in violations("ok.sh", broken))


def test_the_script_that_creates_the_anthropic_secret_never_holds_the_key_in_a_variable() -> None:
    name = "crear-secret-anthropic.sh"
    text = _text(name)
    assert f"{K} create secret generic veridicus-anthropic" in text
    assert "--from-file=api-key=" in text
    assert "--dry-run=client -o yaml" in text
    assert re.search(rf"\|\s*{K} apply -f -", text)
    assert "umask 077" in text
    assert re.search(r"^temporal=\"\$\(mktemp\)\"$", text, re.MULTILINE)
    assert re.search(r"^trap 'rm -f \"\$temporal\"' EXIT$", text, re.MULTILINE)
    assert "VERIDICUS_ANTHROPIC_API_KEY" in text
    assert "grep" in text
    assert "cut -d=" in text
    assert not re.search(r"^\s*\w*(clave|key)\w*=", text, re.MULTILINE | re.IGNORECASE)


def test_the_script_that_creates_the_pull_secret_uses_a_dockerconfig_file() -> None:
    name = "crear-pull-secret-ghcr.sh"
    text = _text(name)
    assert f"{K} create secret docker-registry veridicus-ghcr" in text
    assert "--from-file=.dockerconfigjson=" in text
    assert "--dry-run=client -o yaml" in text
    assert re.search(rf"\|\s*{K} apply -f -", text)
    assert "VERIDICUS_GHCR_USER" in text
    assert "VERIDICUS_GHCR_TOKEN" in text
    assert "ghcr.io" in text


def test_both_secret_scripts_take_the_env_file_as_an_argument_and_fail_without_it() -> None:
    for name in ("crear-secret-anthropic.sh", "crear-pull-secret-ghcr.sh"):
        text = _text(name)
        assert "${1:-}" in text, name
        assert re.search(r"exit 2", text), name


def test_the_demo_script_applies_waits_prints_the_logs_and_probes_the_network() -> None:
    lines = _lines("demo-analyzer.sh")
    joined = "\n".join(lines)
    assert any(
        item.startswith(f"{K} apply -k ") and "deploy/demo-analyzer" in item for item in lines
    )
    assert f"{K} wait --for=condition=complete --timeout=900s" in joined
    assert re.search(rf"{K} logs\b.*job/veridicus-analyzer-demo", joined)
    assert re.search(rf"{K} run\b", joined)
    assert "--max-time 10" in joined
    assert "https://example.com" in joined
    assert lines[-1] == 'exit "$codigo_job"'


def test_the_network_probe_does_not_wear_the_label_of_the_job() -> None:
    joined = "\n".join(_lines("demo-analyzer.sh"))
    assert "--labels" not in joined
    assert "app.kubernetes.io/name" not in joined


def test_the_demo_script_fails_when_the_probe_reaches_the_internet() -> None:
    text = _text("demo-analyzer.sh")
    assert re.search(r'case "\$codigo_red" in\s*\n\s*0\)', text)
    assert "SÍ llegó" in text
    assert re.search(r"SÍ llegó[^\n]*\n(?:[^\n]*\n)?\s*exit 1", text)


def test_the_demo_script_refuses_a_probe_image_without_a_real_digest() -> None:
    text = _text("demo-analyzer.sh")
    assert re.search(r'case "\$imagen_sonda" in\s*\n\s*\*REEMPLAZAR_DIGEST_CURL\*\)', text)


def test_the_probe_image_is_pinned_by_digest() -> None:
    assert PINNED.search(_text("demo-analyzer.sh"))


@pytest.mark.xfail(
    strict=True,
    reason="El digest de curlimages/curl lo trae el humano (sin red aquí); ver la bitácora de U02-T02",
)
def test_the_probe_image_digest_is_a_real_one() -> None:
    assert REAL_DIGEST.search(_text("demo-analyzer.sh"))


@pytest.mark.parametrize(
    "line",
    [
        "curlimages/curl:8.11.1",
        "curlimages/curl:latest",
        "curlimages/curl",
        "curlimages/curl@sha256:abc",
        "curlimages/curl@sha256:" + "G" * 64,
    ],
)
def test_negative_a_probe_image_without_a_digest_fails(line: str) -> None:
    assert PINNED.search(line) is None
    assert REAL_DIGEST.search(line) is None


def test_the_digest_checks_accept_a_real_digest_and_the_marker() -> None:
    assert REAL_DIGEST.search("curlimages/curl@sha256:" + "a" * 64)
    assert PINNED.search("curlimages/curl@sha256:REEMPLAZAR_DIGEST_CURL")
    assert REAL_DIGEST.search("curlimages/curl@sha256:REEMPLAZAR_DIGEST_CURL") is None


def test_the_human_folder_has_only_the_three_scripts() -> None:
    assert sorted(item.name for item in Path(HUMANO).iterdir()) == SCRIPTS
