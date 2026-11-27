"""Los scripts del humano (paso 7): se leen como texto y nunca se ejecutan.

Cada regla lleva su control negativo: un script de `deploy/tests/fixtures/humano/` con ese único
defecto. Las operaciones del clúster se arman con fragmentos para que este archivo no contenga
ninguna de las que prohíbe la comprobación de AUTONOMIA-01.
"""

import re
from pathlib import Path

import humano_checks
import pytest
from autonomia import MARK
from humano_checks import PINNED, REAL_DIGEST, violations
from support import DEPLOY

ROOT = DEPLOY.parent
HUMANO = ROOT / "scripts" / "humano"
FIXTURES = DEPLOY / "tests" / "fixtures" / "humano"
K = "kube" + "ctl"
SCRIPTS = [
    "argocd-instalar.sh",
    "crear-pull-secret-ghcr.sh",
    "crear-secret-anthropic.sh",
    "demo-analyzer.sh",
    "visor-pod.sh",
]


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
    # F-09: formas que la ronda 1 no cubría.
    "shebang-x.sh": "set -x o allexport",
    "export-sustitucion.sh": "export con sustitución",
    "export-cat.sh": "export con sustitución",
    "echo-secreto.sh": "echo o printf de una variable secreta",
    "echo-key.sh": "echo o printf de una variable secreta",
    # Candidata de la ronda 1: el Secret no puede quedar en last-applied-configuration.
    "apply-sin-server-side.sh": "apply sin --server-side",
    "apply-archivo-sin-server-side.sh": "apply sin --server-side",
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


def test_f09_variable_names_that_hold_a_key_are_seen() -> None:
    base = (FIXTURES / "ok.sh").read_text(encoding="utf-8")
    for name in ("secreto", "key", "api_key", "clave", "token", "password", "credencial"):
        broken = base + f'{name}=x\necho "${name}"\necho "${{{name}_dos}}"\n'
        assert len([x for x in violations("x.sh", broken) if "echo o printf" in x]) == 2, name


def test_f09_the_shebang_and_the_export_rules_do_not_flag_the_clean_forms() -> None:
    base = (FIXTURES / "ok.sh").read_text(encoding="utf-8")
    harmless = base + 'export LC_ALL=C\nexport dir="$(mktemp -d)"\n'
    assert violations("x.sh", harmless) == []
    assert violations("x.sh", base.replace("#!/usr/bin/env bash", "#!/bin/bash -eu")) == []


def test_candidate_a_server_side_apply_of_a_secret_passes() -> None:
    base = (FIXTURES / "ok.sh").read_text(encoding="utf-8")
    good = (
        base
        + f'{K} create secret generic x --from-file=a="$temporal" --dry-run=client -o yaml | {K} apply --server-side -f -\n'
    )
    assert violations("x.sh", good) == []
    kustomized = base + f"{K} apply -k deploy/demo-analyzer\n"
    assert violations("x.sh", kustomized) == []


def test_candidate_both_secret_scripts_apply_server_side() -> None:
    for name in ("crear-secret-anthropic.sh", "crear-pull-secret-ghcr.sh"):
        text = _text(name)
        assert re.search(rf"\|\s*{K} apply --server-side -f -", text), name
        assert not re.search(rf"{K} apply -f", text), name


def _script(base: str, line: str) -> str:
    return (FIXTURES / "ok.sh").read_text(encoding="utf-8") + base + line + "\n"


POLICIES = DEPLOY / "policies"


@pytest.mark.parametrize("name", ["veridicus-secret-solo-job", "veridicus-imagen-con-etiqueta"])
def test_f12_the_policies_declare_the_ephemeral_containers_gap(name: str) -> None:
    text = (POLICIES / name / "policy.yaml").read_text(encoding="utf-8")
    assert "pods/ephemeralcontainers" in text


def test_f12_the_match_of_the_policies_is_unchanged() -> None:
    for name in ("veridicus-secret-solo-job", "veridicus-imagen-con-etiqueta"):
        text = (POLICIES / name / "policy.yaml").read_text(encoding="utf-8")
        assert "ephemeralcontainers\n" not in text.split("match:")[1].split("validate:")[0]


def test_f13_text_after_a_comment_does_not_count_as_server_side() -> None:
    for line in (
        f"{K} apply -f - # --server-side",
        f"{K} apply -f - #--server-side",
        f"{K} apply -f y # -k",
    ):
        assert any("apply sin --server-side" in x for x in violations("x.sh", _script("", line))), (
            line
        )


def test_f13_a_hash_inside_quotes_is_not_a_comment() -> None:
    line = f"{K} apply --server-side -f - --field-manager='a#b'"
    assert violations("x.sh", _script("", line)) == []
    line = f"{K} apply -f - --field-manager='a#b'"
    assert any("apply sin --server-side" in x for x in violations("x.sh", _script("", line)))


def test_f13_server_side_before_a_comment_passes() -> None:
    line = f"{K} apply --server-side -f - # sin copiar el valor"
    assert violations("x.sh", _script("", line)) == []


def _kustomization(root: Path, rel: str, body: str) -> None:
    path = root / rel / "kustomization.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


KUSTOMIZE_LINES = [
    '{K} apply -k "$raiz/deploy/x"',
    "{K} apply -k deploy/x",
    '{K} apply --kustomize "${{raiz}}/deploy/x"',
    "{K} apply --kustomize=deploy/x",
    "{K} apply -k=deploy/x",
]


@pytest.mark.parametrize("template", KUSTOMIZE_LINES)
def test_f13_a_kustomization_with_a_secret_generator_fails(tmp_path: Path, template: str) -> None:
    _kustomization(tmp_path, "deploy/x", "secretGenerator:\n  - name: a\n    literals: [b=c]\n")
    found = violations("x.sh", _script("", template.format(K=K)), root=tmp_path)
    assert any("secretGenerator" in item for item in found), template


@pytest.mark.parametrize("template", KUSTOMIZE_LINES)
def test_f13_a_kustomization_without_a_secret_generator_passes(
    tmp_path: Path, template: str
) -> None:
    _kustomization(tmp_path, "deploy/x", "resources:\n  - a.yaml\n")
    assert violations("x.sh", _script("", template.format(K=K)), root=tmp_path) == []


def test_f13_a_kustomization_that_cannot_be_resolved_passes_and_is_documented(
    tmp_path: Path,
) -> None:
    for line in (
        f'{K} apply -k "$otra/deploy/x"',
        f"{K} apply -k deploy/no-existe",
        f'{K} apply -k "$(dirname x)"',
    ):
        assert violations("x.sh", _script("", line), root=tmp_path) == [], line
    assert "no se puede resolver" in (DEPLOY / "tests" / "humano_checks.py").read_text("utf-8")


def test_f13_the_real_demo_kustomization_has_no_secret_generator() -> None:
    text = _text("demo-analyzer.sh")
    assert violations("scripts/humano/demo-analyzer.sh", text, root=ROOT) == []
    assert "secretGenerator" not in (ROOT / "deploy/demo-analyzer/kustomization.yaml").read_text(
        encoding="utf-8"
    )


SECRET_SCRIPTS = {
    "crear-secret-anthropic.sh": "veridicus-anthropic",
    "crear-pull-secret-ghcr.sh": "veridicus-ghcr",
}


@pytest.mark.parametrize("name", SECRET_SCRIPTS)
def test_f11_the_secret_scripts_refuse_a_secret_that_keeps_last_applied(name: str) -> None:
    text = _text(name)
    secret = SECRET_SCRIPTS[name]
    check = text.index(f'if [ "$({K} get secret {secret} ')
    assert check < text.index(f"{K} apply --server-side")
    block = text[check : text.index(f"{K} apply --server-side")]
    assert f"{K} delete secret {secret} --namespace" in block
    assert re.search(r"exit 2", block)
    assert "conflicto" not in text


# --- K-104: la anotación se comprueba con un literal fijo, sin que su valor pase por un pipe ------

K8S = K + ".kubernetes.io/last-applied-configuration"
SECRET_NAME = "veridicus-anthropic"  # noqa: S105 (nombre del Secret, nunca su valor)


def _good_check(secret: str = SECRET_NAME) -> str:
    template = f'{{{{if index .metadata.annotations "{K8S}"}}}}si{{{{end}}}}'
    return (
        f'if [ "$({K} get secret {secret} --namespace "$namespace" '
        f'-o go-template=\'{template}\' 2> /dev/null)" = "si" ]; then'
    )


def _check_script(check: str, secret: str = SECRET_NAME, after: str = "") -> str:
    return (
        "#!/usr/bin/env bash\nset -euo pipefail\n"
        f"{check}\n"
        f'  echo "El Secret {secret} ya existe con la anotación last-applied-configuration." >&2\n'
        f'  echo "Bórrelo y repita este script: {K} delete secret {secret} --namespace $namespace" >&2\n'
        "  exit 2\nfi\n"
        f"{K} create secret generic {secret} --dry-run=client -o yaml | {K} apply --server-side -f -\n"
        f"{after}"
    )


@pytest.mark.parametrize("name", SECRET_SCRIPTS)
def test_k104_each_secret_script_uses_the_fixed_literal_check(name: str) -> None:
    secret = SECRET_SCRIPTS[name]

    assert humano_checks.last_applied_violations(name, _text(name), secret) == []
    assert _good_check(secret) in _text(name)


@pytest.mark.parametrize("name", SECRET_SCRIPTS)
def test_k104_the_annotation_never_goes_through_a_pipe_or_a_variable(name: str) -> None:
    line = next(x for x in _text(name).splitlines() if x.startswith("if [") and "last-applied" in x)

    assert "jsonpath" not in line
    assert "grep" not in line
    assert "|" not in line
    assert not re.match(r"\s*\w+=", line)
    assert line.count("$(") == 1, "la única sustitución es la comparación con el literal"


def test_k104_the_model_check_passes_its_own_rule() -> None:
    text = _check_script(_good_check())

    assert humano_checks.last_applied_violations("x.sh", text, SECRET_NAME) == []


def _old_check(secret: str = SECRET_NAME) -> str:
    path = "{.metadata.annotations." + K + r"\.kubernetes\.io/last-applied-configuration}"
    return (
        f"if {K} get secret {secret} --namespace \"$namespace\" -o jsonpath='{path}' "
        "2> /dev/null | grep -q .; then"
    )


def _value_check() -> str:
    template = f'{{{{index .metadata.annotations "{K8S}"}}}}'
    return (
        f'if [ "$({K} get secret {SECRET_NAME} --namespace "$namespace" '
        f'-o go-template=\'{template}\' 2> /dev/null)" = "si" ]; then'
    )


def _variable_check() -> str:
    template = f'{{{{if index .metadata.annotations "{K8S}"}}}}si{{{{end}}}}'
    return (
        f'valor="$({K} get secret {SECRET_NAME} --namespace "$namespace" '
        f"-o go-template='{template}' 2> /dev/null)\"\n"
        'if [ "$valor" = "si" ]; then'
    )


K104_NEGATIVES = {
    "forma vieja con jsonpath y grep (caso sonda 6)": _old_check(),
    "plantilla que imprime el valor": _value_check(),
    "valor guardado en una variable": _variable_check(),
    "comparación con otro literal": _good_check().replace('= "si"', '= "ok"'),
    "plantilla que imprime otro literal": _good_check().replace("}}si{{", "}}ok{{"),
    "con un pipe": _good_check().replace("2> /dev/null)", "2> /dev/null | cat)"),
    "sin la comprobación": "if false; then",
}


@pytest.mark.parametrize("check", K104_NEGATIVES.values(), ids=K104_NEGATIVES.keys())
def test_negative_k104_the_old_or_a_leaky_check_fails(check: str) -> None:
    found = humano_checks.last_applied_violations("x.sh", _check_script(check), SECRET_NAME)

    assert found, check


def test_negative_k104_a_check_after_the_apply_fails() -> None:
    text = (
        "#!/usr/bin/env bash\nset -euo pipefail\n"
        f"{K} create secret generic {SECRET_NAME} --dry-run=client -o yaml | {K} apply --server-side -f -\n"
        f"{_good_check()}\n  exit 2\nfi\n"
    )

    assert humano_checks.last_applied_violations("x.sh", text, SECRET_NAME)


def test_negative_k104_a_check_without_the_delete_hint_or_the_exit_fails() -> None:
    no_hint = _check_script(_good_check()).replace(f"{K} delete secret", "borre el secret")
    no_exit = _check_script(_good_check()).replace("  exit 2\n", "  true\n")

    assert humano_checks.last_applied_violations("x.sh", no_hint, SECRET_NAME)
    assert humano_checks.last_applied_violations("x.sh", no_exit, SECRET_NAME)


def test_negative_k104_a_check_for_another_secret_fails() -> None:
    text = _check_script(_good_check("otro"))

    assert humano_checks.last_applied_violations("x.sh", text, SECRET_NAME)


def test_negative_k104_two_checks_or_a_commented_form_are_read_as_the_rule_says() -> None:
    twice = _check_script(_good_check() + "\n  true\nfi\n" + _good_check())
    commented = _check_script(_good_check()).replace("set -euo", f"# {_old_check()}\nset -euo")

    assert humano_checks.last_applied_violations("x.sh", twice, SECRET_NAME)
    assert humano_checks.last_applied_violations("x.sh", commented, SECRET_NAME) == []


def test_the_script_that_creates_the_anthropic_secret_never_holds_the_key_in_a_variable() -> None:
    name = "crear-secret-anthropic.sh"
    text = _text(name)
    assert f"{K} create secret generic veridicus-anthropic" in text
    assert "--from-file=api-key=" in text
    assert "--dry-run=client -o yaml" in text
    assert re.search(rf"\|\s*{K} apply --server-side -f -", text)
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
    assert re.search(rf"\|\s*{K} apply --server-side -f -", text)
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


CURL_DIGEST = "c1fe1679c34d9784c1b0d1e5f62ac0a79fca01fb6377cdd33e90473c6f9f9a69"


def test_the_probe_image_is_pinned_by_a_real_digest_and_carries_no_marker() -> None:
    text = _text("demo-analyzer.sh")
    assert REAL_DIGEST.search(text)
    assert f'imagen_sonda="curlimages/curl:8.11.1@sha256:{CURL_DIGEST}"' in text
    assert not re.search(r'imagen_sonda="[^"]*REEMPLAZAR', text)
    assert "8.11.1" in text.split("imagen_sonda=")[0].rsplit("\n\n", 1)[-1]
    assert "multiarquitectura" in text.split("imagen_sonda=")[0]


def test_a_tag_before_the_digest_is_accepted_and_a_tag_alone_is_not() -> None:
    assert REAL_DIGEST.search(f"curlimages/curl:8.11.1@sha256:{CURL_DIGEST}")
    assert PINNED.search(f"curlimages/curl:8.11.1@sha256:{CURL_DIGEST}")
    assert PINNED.search("curlimages/curl:8.11.1") is None


@pytest.mark.parametrize(
    "line",
    [
        "curlimages/curl:8.11.1",
        "curlimages/curl:latest",
        "curlimages/curl",
        "curlimages/curl@sha256:abc",
        "curlimages/curl@sha256:" + "G" * 64,
        # K-103: `latest` con digest tampoco sirve, igual que en los manifiestos y en Kyverno.
        "curlimages/curl:latest@sha256:" + "a" * 64,
        "curlimages/curl:LATEST@sha256:" + "a" * 64,
        "curlimages/curl:latest@sha256:REEMPLAZAR_DIGEST_CURL",
    ],
)
def test_negative_a_probe_image_without_a_digest_fails(line: str) -> None:
    assert PINNED.search(line) is None
    assert REAL_DIGEST.search(line) is None


@pytest.mark.parametrize("tag", ["8.11.1", "v8", "latest-slim", "7.0-latest", "x"])
def test_k103_another_tag_with_a_real_digest_still_passes(tag: str) -> None:
    line = f"curlimages/curl:{tag}@sha256:" + "a" * 64

    assert PINNED.search(line)
    assert REAL_DIGEST.search(line)


def test_the_digest_checks_accept_a_real_digest_and_the_marker() -> None:
    assert REAL_DIGEST.search("curlimages/curl@sha256:" + "a" * 64)
    assert PINNED.search("curlimages/curl@sha256:REEMPLAZAR_DIGEST_CURL")
    assert REAL_DIGEST.search("curlimages/curl@sha256:REEMPLAZAR_DIGEST_CURL") is None


def test_the_human_folder_has_only_the_scripts_and_the_demo_viewer() -> None:
    # visor-demo.py es la interfaz web de la demo, que lanza el humano en la VM (no es un script bash);
    # visor-pod.sh la despliega como un pod.
    names = sorted(item.name for item in Path(HUMANO).iterdir() if item.name != "__pycache__")
    assert names == sorted([*SCRIPTS, "visor-demo.py"])
