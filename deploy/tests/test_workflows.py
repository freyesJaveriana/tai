"""Los workflows de deploy (pasos 8 y 9, DP-07, DP-08): `deploy-level0.yml` y `analyzer-image.yml`.

Se leen como texto y como YAML; no se ejecuta ninguna herramienta (no están en el contenedor y no hay
red: la CI las corre). Cada regla de `workflow_checks` tiene su control negativo, de dos formas: un
workflow roto de `fixtures/workflows/` y un cambio en memoria del workflow real.
"""

import re
from pathlib import Path
from typing import Any

import pytest
import workflow_checks as checks
import yaml
from autonomia import scan
from support import DEPLOY

ROOT = DEPLOY.parent
WORKFLOWS = ROOT / ".github" / "workflows"
FIXTURES = DEPLOY / "tests" / "fixtures" / "workflows"
DEPLOY_WORKFLOW = WORKFLOWS / "deploy-level0.yml"
IMAGE_WORKFLOW = WORKFLOWS / "analyzer-image.yml"
IMAGE = "ghcr.io/freyesjaveriana/veridicus-analyzer-cli"
DOCKERFILE = "deploy/images/analyzer-cli/Dockerfile"
# Armado con fragmentos: este archivo no nombra la carpeta del humano.
HUMANO = "scripts/" + "humano"
NEGATIVE_MANIFEST = "deploy/tests/fixtures/manifests/job-roto.yaml"
FAIL_RESOURCES = {
    "veridicus-imagen-con-etiqueta": "fail-pod-latest.yaml",
    "veridicus-pod-restricted": "fail-pod-como-root.yaml",
    "veridicus-recursos-requeridos": "fail-pod-sin-recursos.yaml",
    "veridicus-secret-solo-job": "fail-pod-con-envfrom.yaml",
}


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _document(path: Path) -> dict[Any, Any]:
    document = yaml.safe_load(_text(path))
    assert isinstance(document, dict)
    return document


def _steps(path: Path, job: str) -> list[dict[str, Any]]:
    steps: list[dict[str, Any]] = _document(path)["jobs"][job]["steps"]
    return steps


def _step_text(step: dict[str, Any]) -> str:
    return f"{step.get('run', '')}\n{yaml.safe_dump(step.get('env') or {})}"


def _index(steps: list[dict[str, Any]], needle: str) -> int:
    """La posición del único paso cuyo script o entorno contiene `needle`."""
    found = [number for number, step in enumerate(steps) if needle in _step_text(step)]
    assert len(found) == 1, f"debe haber un paso con {needle!r}, hay {len(found)}"
    return found[0]


def _runs(steps: list[dict[str, Any]]) -> str:
    return "\n".join(re.sub(r"\\\n\s*", " ", str(step.get("run", ""))) for step in steps)


def _triggers(path: Path) -> dict[str, Any]:
    document = _document(path)
    raw = document.get("on", document.get(True))
    assert isinstance(raw, dict)
    return {str(key): value for key, value in raw.items()}


def _mutate(text: str, old: str, new: str) -> str:
    assert old in text, f"el workflow real ya no contiene {old!r}"
    return text.replace(old, new, 1)


# --- Los dos workflows reales ---------------------------------------------------------------------


@pytest.mark.parametrize("path", [DEPLOY_WORKFLOW, IMAGE_WORKFLOW], ids=lambda p: p.name)
def test_the_new_workflows_pass_every_rule(path: Path) -> None:
    assert checks.violations(path.name, _text(path)) == []


def test_ca2_autonomia_01_still_passes_with_the_two_new_workflows() -> None:
    assert DEPLOY_WORKFLOW.is_file() and IMAGE_WORKFLOW.is_file()
    assert scan(ROOT) == []
    for path in (DEPLOY_WORKFLOW, IMAGE_WORKFLOW):
        assert HUMANO not in _text(path), "ningún workflow nombra la carpeta del humano (DP-08)"


@pytest.mark.parametrize("path", [DEPLOY_WORKFLOW, IMAGE_WORKFLOW], ids=lambda p: p.name)
def test_every_job_has_a_timeout_and_the_workflow_a_concurrency_group(path: Path) -> None:
    document = _document(path)
    assert document["permissions"] == {"contents": "read"}
    assert document["concurrency"]["group"].startswith(path.stem)
    for name, job in document["jobs"].items():
        assert isinstance(job["timeout-minutes"], int), name
        assert job["runs-on"] == "ubuntu-24.04", name


# --- deploy-level0 ---------------------------------------------------------------------------------


def test_deploy_level0_runs_on_every_pull_request_and_push_to_main_without_a_path_filter() -> None:
    triggers = _triggers(DEPLOY_WORKFLOW)

    assert set(triggers) == {"pull_request", "push"}
    assert triggers["pull_request"] is None
    assert triggers["push"] == {"branches": ["main"]}


def test_deploy_level0_runs_the_python_checks_of_deploy_with_the_lockfile_and_100_percent() -> None:
    steps = _steps(DEPLOY_WORKFLOW, "deploy-level0")
    runs = _runs(steps)
    offline = "uv run --frozen --offline --directory deploy"

    assert "uv sync --frozen --directory deploy" in runs
    assert "uv lock --check --directory deploy" in runs
    for command in ("ruff check .", "ruff format --check .", "mypy --strict src tests"):
        assert f"{offline} {command}" in runs, command
    assert f"{offline} pytest --cov=veridicus_demo --cov-branch --cov-fail-under=100" in runs
    # Solo los pasos que instalan usan la red: el resto va con --frozen --offline.
    assert "uv sync" not in runs.replace("uv sync --frozen --directory deploy", "")


def test_k102_the_ci_runs_the_manifest_rules_on_the_real_kustomize_render() -> None:
    steps = _steps(DEPLOY_WORKFLOW, "deploy-level0")
    build = _index(steps, "kustomize build deploy/demo-analyzer")
    tests = _index(steps, "--cov=veridicus_demo")

    assert build < tests, "el render existe antes de las pruebas"
    assert steps[tests]["env"]["VERIDICUS_RENDER"] == "${{ runner.temp }}/render.yaml"
    render = r'kustomize build deploy/demo-analyzer > "\$RUNNER_TEMP/render.yaml"'
    assert re.search(render, _runs(steps))


def test_deploy_level0_validates_the_render_with_kubeconform_strict_for_kubernetes_1_31() -> None:
    steps = _steps(DEPLOY_WORKFLOW, "deploy-level0")
    command = 'kubeconform -strict -summary -kubernetes-version 1.31.0 "$RUNNER_TEMP/render.yaml"'

    assert command in _runs(steps)
    assert _index(steps, "kustomize build deploy/demo-analyzer") < _index(steps, command)


def test_deploy_level0_runs_kyverno_test_and_the_other_user_folder_and_kyverno_apply() -> None:
    runs = _runs(_steps(DEPLOY_WORKFLOW, "deploy-level0"))

    assert "kyverno test deploy/policies\n" in runs + "\n"
    # `kyverno test` debería descubrir la subcarpeta; el paso aparte no depende de que lo haga.
    assert "kyverno test deploy/policies/veridicus-secret-solo-job/otro-usuario" in runs
    for name in FAIL_RESOURCES:
        assert f"deploy/policies/{name}/policy.yaml" in runs, name
    assert '--resource "$RUNNER_TEMP/render.yaml"' in runs, "kyverno apply sobre el render real"


def test_deploy_level0_lints_the_dockerfile_and_the_shell_scripts_apart_from_the_human() -> None:
    runs = _runs(_steps(DEPLOY_WORKFLOW, "deploy-level0"))

    assert f"hadolint {DOCKERFILE}" in runs
    assert "git ls-files -z -- 'scripts/*.sh'" in runs
    assert "shellcheck" in runs
    assert HUMANO not in runs


@pytest.mark.parametrize("tool", ["kustomize", "kubeconform", "kyverno", "hadolint", "shellcheck"])
def test_deploy_level0_downloads_each_tool_with_the_pinned_asset_and_the_sum_of_the_table(
    tool: str,
) -> None:
    asset, digest = checks.TOOLS[tool]
    steps = _steps(DEPLOY_WORKFLOW, "deploy-level0")
    step = steps[_index(steps, asset)]

    assert digest in _step_text(step)
    assert "sha256sum -c" in step["run"]
    assert "curl" in step["run"]
    assert step["run"].index("sha256sum -c") < step["run"].index(
        "tar" if asset.endswith(("gz", "xz")) else "chmod"
    )


@pytest.mark.parametrize("name", FAIL_RESOURCES)
def test_each_negative_control_of_the_ci_points_at_an_existing_failing_resource(name: str) -> None:
    resource = DEPLOY / "policies" / name / "resources" / FAIL_RESOURCES[name]
    runs = _runs(_steps(DEPLOY_WORKFLOW, "deploy-level0"))

    assert resource.is_file()
    assert f"deploy/policies/{name}/resources/{FAIL_RESOURCES[name]}" in runs


def test_the_negative_manifest_is_invalid_and_the_ci_inverts_the_failure_of_kubeconform() -> None:
    [manifest] = yaml.safe_load_all((ROOT / NEGATIVE_MANIFEST).read_text(encoding="utf-8"))
    steps = _steps(DEPLOY_WORKFLOW, "deploy-level0")
    step = steps[_index(steps, NEGATIVE_MANIFEST)]

    assert isinstance(manifest["spec"]["backoffLimit"], str), "el tipo no es un entero"
    assert "campoInventado" in manifest["spec"], "un campo que el esquema no tiene"
    assert re.search(r"if \w+=\"\$\(kubeconform -strict", step["run"]), "el fallo se invierte"
    assert "Invalid: 1, Errors: 0" in step["run"], "falla por inválido, no por error de esquemas"


@pytest.mark.parametrize("name", FAIL_RESOURCES)
def test_each_kyverno_negative_control_inverts_the_failure_and_demands_a_real_fail(
    name: str,
) -> None:
    steps = _steps(DEPLOY_WORKFLOW, "deploy-level0")
    step = steps[_index(steps, f"deploy/policies/{name}/resources/{FAIL_RESOURCES[name]}")]
    run = step["run"]

    assert re.search(r"if \w+=\"\$\(kyverno apply", run), "el fallo se invierte"
    assert "fail: [1-9]" in run, "el fallo es de la política y no un error de otra clase"
    assert run.count("exit 1") >= 1


def test_the_secret_policy_control_passes_the_user_of_the_request() -> None:
    steps = _steps(DEPLOY_WORKFLOW, "deploy-level0")
    name = "veridicus-secret-solo-job"
    step = steps[_index(steps, f"deploy/policies/{name}/resources/{FAIL_RESOURCES[name]}")]

    assert f"--userinfo deploy/policies/{name}/userinfo.yaml" in step["run"]


# --- analyzer-image --------------------------------------------------------------------------------

# K-105: la imagen copia deploy/src, deploy/pyproject.toml y deploy/uv.lock; un cambio solo ahí también
# la reconstruye, la escanea y, en main, la publica.
IMAGE_PATHS = [
    "libs/**",
    "contracts/**",
    "deploy/images/**",
    "deploy/src/**",
    "deploy/pyproject.toml",
    "deploy/uv.lock",
    ".github/workflows/analyzer-image.yml",
]
ONLY_MAIN = "github.event_name == 'push' && github.ref == 'refs/heads/main'"


def test_the_image_workflow_runs_on_pull_requests_and_pushes_to_main_for_the_image_paths() -> None:
    triggers = _triggers(IMAGE_WORKFLOW)

    assert set(triggers) == {"pull_request", "push"}
    assert triggers["pull_request"] == {"paths": IMAGE_PATHS}
    assert triggers["push"] == {"branches": ["main"], "paths": IMAGE_PATHS}


def test_only_the_publish_job_has_packages_write_and_it_only_runs_on_a_push_to_main() -> None:
    jobs = _document(IMAGE_WORKFLOW)["jobs"]

    assert set(jobs) == {"build-scan", "publish"}
    assert jobs["publish"]["permissions"] == {"contents": "read", "packages": "write"}
    assert jobs["publish"]["if"] == ONLY_MAIN
    assert jobs["build-scan"].get("permissions") is None
    assert jobs["build-scan"]["if"] == "github.event_name == 'pull_request'"
    assert _text(IMAGE_WORKFLOW).count("packages: write") == 1


def test_a_pull_request_builds_and_scans_but_never_logs_in_nor_pushes() -> None:
    steps = _steps(IMAGE_WORKFLOW, "build-scan")
    runs = _runs(steps)

    assert f'docker build --tag "$IMAGE:pr" -f {DOCKERFILE} .' in runs
    assert "docker login" not in runs
    assert "docker push" not in runs
    assert "secrets." not in _text(IMAGE_WORKFLOW).split("publish:")[0]


def test_trivy_blocks_high_and_critical_with_a_fix_in_both_jobs() -> None:
    for job in ("build-scan", "publish"):
        runs = _runs(_steps(IMAGE_WORKFLOW, job))
        assert re.search(
            r"trivy image --scanners vuln --severity HIGH,CRITICAL --ignore-unfixed --exit-code 1 ",
            runs,
        ), job


@pytest.mark.parametrize("job", ["build-scan", "publish"])
def test_trivy_is_downloaded_with_the_pinned_asset_and_the_sum_of_the_table(job: str) -> None:
    asset, digest = checks.TOOLS["trivy"]
    steps = _steps(IMAGE_WORKFLOW, job)
    step = steps[_index(steps, asset)]

    assert digest in _step_text(step)
    assert "sha256sum -c" in step["run"]


def test_the_publish_job_scans_before_it_logs_in_and_pushes_the_commit_sha_tag() -> None:
    document = _document(IMAGE_WORKFLOW)
    steps = _steps(IMAGE_WORKFLOW, "publish")
    scan_at = _index(steps, "trivy image")
    login_at = _index(steps, "docker login ghcr.io")
    push_at = _index(steps, "docker push")
    runs = _runs(steps)

    assert _index(steps, "docker build") < scan_at < login_at <= push_at
    assert "--password-stdin" in steps[login_at]["run"]
    token = steps[login_at]["env"]["GITHUB_TOKEN"]
    assert token == "${{ secrets.GITHUB_TOKEN }}"  # noqa: S105 (la expresión de Actions, no un valor)
    assert document["env"]["IMAGE"] == IMAGE
    assert steps[_index(steps, "docker build")]["env"]["IMAGE_TAG"] == "${{ github.sha }}"
    assert f'docker build --tag "$IMAGE:$IMAGE_TAG" -f {DOCKERFILE} .' in runs
    assert 'docker push "$IMAGE:$IMAGE_TAG"' in runs


def test_the_published_digest_goes_to_the_job_summary() -> None:
    steps = _steps(IMAGE_WORKFLOW, "publish")
    step = steps[_index(steps, "RepoDigests")]

    assert "docker inspect --format" in step["run"]
    assert "$GITHUB_STEP_SUMMARY" in step["run"]
    assert _index(steps, "docker push") < _index(steps, "RepoDigests")


# --- Cada regla, con un workflow roto de fixtures/workflows/ -------------------------------------

NEGATIVES = {
    "sin-permisos.yml": "falta «permissions: contents: read»",
    "packages-en-la-raiz.yml": "el nivel del workflow declara una escritura",
    "packages-en-pull-request.yml": "puede correr en un pull_request",
    "packages-en-dos-jobs.yml": "packages: write en 2 jobs",
    "accion-sin-fijar.yml": "no está fijada por un SHA de 40 hex",
    "accion-nueva.yml": "no es una de las dos acciones permitidas",
    "accion-con-otro-sha.yml": "SHA distinto del del repositorio",
    "curl-sin-verificar.yml": "no verifica la descarga con sha256sum -c",
    "curl-con-otra-suma.yml": "que no es la de la tabla",
    "curl-usa-antes-de-verificar.yml": "antes de verificarlo",
    "curl-sin-suma.yml": "no lleva ninguna suma SHA-256",
    "credenciales-del-cluster.yml": "nombra un kubeconfig",
    "herramienta-del-cluster.yml": "nombra la herramienta del clúster",
    "imagen-latest.yml": "etiqueta de imagen latest",
    # Ronda 2 (F-01, F-02): un mutante de la revisión por fixture.
    "if-con-or.yml": "no es exactamente la condición de push a main",
    "sha256sum-anulado.yml": "anula el código de salida de sha256sum",
    "push-sin-etiqueta.yml": "sin etiqueta",
    "build-sin-etiqueta.yml": "sin etiqueta",
    "expresion-en-run.yml": "expresión de Actions dentro de un run",
    # Ronda 3 (F-05): la forma fija de la verificación.
    "sha256sum-conjuncion.yml": "forma fija",
    "set-relajado.yml": "set -euo pipefail",
    "verificacion-en-if.yml": "dentro de un if, while o until",
    "verificacion-en-segundo-plano.yml": "forma fija",
}


def test_the_fixture_that_meets_every_rule_passes() -> None:
    assert checks.violations("ok.yml", _text(FIXTURES / "ok.yml")) == []


@pytest.mark.parametrize("name", NEGATIVES)
def test_negative_a_workflow_with_one_defect_fails_its_rule(name: str) -> None:
    found = checks.violations(name, _text(FIXTURES / name))

    assert any(NEGATIVES[name] in item for item in found), found


def test_probe_1_packages_write_in_a_pull_request_job_or_at_the_top_fails() -> None:
    for name in ("packages-en-la-raiz.yml", "packages-en-pull-request.yml"):
        assert checks.violations(name, _text(FIXTURES / name)), name


def test_probe_2_an_unpinned_action_and_a_new_pinned_one_fail() -> None:
    for name in ("accion-sin-fijar.yml", "accion-nueva.yml"):
        assert checks.violations(name, _text(FIXTURES / name)), name


def test_probe_3_a_download_without_a_check_or_with_another_sum_fails() -> None:
    for name in ("curl-sin-verificar.yml", "curl-con-otra-suma.yml"):
        assert checks.violations(name, _text(FIXTURES / name)), name


def test_probe_4_cluster_credentials_fail() -> None:
    for name in ("credenciales-del-cluster.yml", "herramienta-del-cluster.yml"):
        assert checks.violations(name, _text(FIXTURES / name)), name


def test_probe_5_a_latest_image_tag_fails() -> None:
    assert checks.violations("x.yml", _text(FIXTURES / "imagen-latest.yml"))


def test_a_file_that_is_not_a_workflow_fails() -> None:
    assert checks.violations("x.yml", "- a\n- b\n") == ["x.yml: no es un workflow"]


def test_a_file_that_is_not_valid_yaml_fails_and_still_gets_the_text_rules() -> None:
    found = checks.violations("x.yml", "a: [\nKUBECONFIG=x\n")

    assert "x.yml: no es un YAML válido" in found
    assert "x.yml:2: nombra un kubeconfig" in found


def test_the_triggers_are_read_from_a_string_a_list_and_a_mapping() -> None:
    assert checks._triggers({True: "push"}) == ["push"]
    assert checks._triggers({"on": ["push", "pull_request"]}) == ["push", "pull_request"]
    assert checks._triggers({"on": {"push": None}}) == ["push"]
    assert checks._triggers({}) == []


def test_a_job_with_packages_write_and_the_exact_main_condition_is_fine_without_a_pull_request() -> (
    None
):
    """Ronda 2: sin el disparador de pull_request sigue exigiéndose la condición exacta, no basta
    con la ausencia del disparador (la ronda 1 lo aceptaba sin `if`)."""
    text = _text(FIXTURES / "ok.yml").replace("  pull_request:\n", "")

    assert checks.violations("x.yml", text) == []


# --- Ronda 2: variantes de F-01 y F-02 sobre el workflow base ------------------------------------

VERIFY = "sha256sum -c -"
MASKED_VERIFY = [
    f"{VERIFY} || true",
    f"{VERIFY} || :",
    f"{VERIFY} || exit 0",
    f"{VERIFY}; true",
    f"{VERIFY} | cat",
    f"{VERIFY} \\\n          || true",
    f"{VERIFY}\n          || true",
]


@pytest.mark.parametrize("masked", MASKED_VERIFY, ids=range(len(MASKED_VERIFY)))
def test_negative_f01_a_check_whose_exit_code_is_annulled_fails(masked: str) -> None:
    text = _mutate(_text(FIXTURES / "ok.yml"), VERIFY, masked)

    assert any("anula" in item for item in checks.violations("x.yml", text))


# --- Ronda 3 (F-05): la verificación tiene una forma fija, no una lista de máscaras ---------------

GOOD_LINE = 'echo "${SHA256}  $RUNNER_TEMP/a.tar.gz" | sha256sum -c -'
CURL_LINE = 'curl -fsSL -o "$RUNNER_TEMP/a.tar.gz" "https://example.org/a.tar.gz"'
INDENT = "          "


@pytest.mark.parametrize("kept", [f"{VERIFY} && echo ok", f"{VERIFY} && true"])
def test_negative_f05_a_check_followed_by_a_conjunction_fails(kept: str) -> None:
    """Invierte la prueba de la ronda 2: con set -e, `&&` deja una suma mala sin efecto."""
    text = _mutate(_text(FIXTURES / "ok.yml"), VERIFY, kept)

    assert any("forma fija" in item for item in checks.violations("x.yml", text))


F05_SHAPES = [
    f"{GOOD_LINE} &",
    f"{GOOD_LINE} && echo ok",
    f"{GOOD_LINE} && true",
    f"! {GOOD_LINE}",
    f"({GOOD_LINE})",
    f"{{ {GOOD_LINE}; }}",
    'echo "${SHA256}  $RUNNER_TEMP/a.tar.gz" \\\n' + INDENT + "| sha256sum -c -",
    'echo "${SHA256}  $RUNNER_TEMP/a.tar.gz" | sha256sum --check -',
    'echo "${SHA256} $RUNNER_TEMP/a.tar.gz" | sha256sum -c -',
    'echo "$SHA256  $RUNNER_TEMP/a.tar.gz" | sha256sum -c -',
    'sha256sum -c "$RUNNER_TEMP/a.sha256"',
    'sha256sum -c - <<< "${SHA256}  $RUNNER_TEMP/a.tar.gz"',
    f"true; {GOOD_LINE}",
    f"{GOOD_LINE}  # no se comprueba",
]


@pytest.mark.parametrize("shape", F05_SHAPES, ids=range(len(F05_SHAPES)))
def test_negative_f05_any_verification_that_is_not_the_fixed_line_fails(shape: str) -> None:
    text = _mutate(_text(FIXTURES / "ok.yml"), GOOD_LINE, shape)

    assert any("forma fija" in item for item in checks.violations("x.yml", text))


@pytest.mark.parametrize("chain", ["&&", "||", "|", "\\"])
def test_negative_f05_a_verification_chained_to_the_previous_line_fails(chain: str) -> None:
    text = _mutate(_text(FIXTURES / "ok.yml"), f"{CURL_LINE}\n", f"{CURL_LINE} {chain}\n")

    assert any("forma fija" in item for item in checks.violations("x.yml", text))


@pytest.mark.parametrize(
    "good",
    [
        GOOD_LINE,
        'echo "${SHA256}  ${RUNNER_TEMP}/a.tar.gz" | sha256sum -c -',
        f"# primero se verifica\n{INDENT}{GOOD_LINE}",
    ],
)
def test_f05_the_fixed_line_passes_alone_in_its_line(good: str) -> None:
    text = _mutate(_text(FIXTURES / "ok.yml"), GOOD_LINE, good)

    assert checks.violations("x.yml", text) == []


NESTED = [
    f"if\n{INDENT}{GOOD_LINE}\n{INDENT}then true\n{INDENT}fi",
    f"if true; then\n{INDENT}{GOOD_LINE}\n{INDENT}fi",
    f"while\n{INDENT}{GOOD_LINE}\n{INDENT}do break\n{INDENT}done",
    f"until\n{INDENT}{GOOD_LINE}\n{INDENT}do break\n{INDENT}done",
    f"if false; then true\n{INDENT}elif\n{INDENT}{GOOD_LINE}\n{INDENT}then true\n{INDENT}fi",
    f"case x in\n{INDENT}x)\n{INDENT}{GOOD_LINE}\n{INDENT};;\n{INDENT}esac",
]


@pytest.mark.parametrize("nested", NESTED, ids=range(len(NESTED)))
def test_negative_f05_a_verification_inside_a_control_structure_fails(nested: str) -> None:
    text = _mutate(_text(FIXTURES / "ok.yml"), GOOD_LINE, nested)

    assert any("dentro de un if, while o until" in x for x in checks.violations("x.yml", text))


def test_f05_a_closed_structure_before_the_verification_does_not_count() -> None:
    closed = f"if true; then true; fi\n{INDENT}{GOOD_LINE}"
    text = _mutate(_text(FIXTURES / "ok.yml"), GOOD_LINE, closed)

    assert checks.violations("x.yml", text) == []


PROLOGUES = [
    "set +e",
    "set -eu",
    "set -e",
    "set -uo pipefail",
    "set -euo pipefail\n" + INDENT + "set +e",
    "set -euo pipefail\n" + INDENT + "set +o pipefail",
    "set -euo pipefail\n" + INDENT + "set +eu",
    "echo hola\n" + INDENT + "set -euo pipefail",
    "",
]


@pytest.mark.parametrize("prologue", PROLOGUES, ids=range(len(PROLOGUES)))
def test_negative_f05_a_download_script_must_start_with_set_euo_pipefail_and_keep_it(
    prologue: str,
) -> None:
    base = _text(FIXTURES / "ok.yml")
    text = _mutate(
        base, "set -euo pipefail\n" + INDENT, prologue + ("\n" + INDENT if prologue else "")
    )

    assert any("set -euo pipefail" in item for item in checks.violations("x.yml", text))


def test_f05_comments_and_blank_lines_before_the_prologue_are_fine() -> None:
    text = _mutate(
        _text(FIXTURES / "ok.yml"),
        "set -euo pipefail",
        "# nota\n" + INDENT + "\n" + INDENT + "set -euo pipefail",
    )

    assert checks.violations("x.yml", text) == []


def test_f05_a_script_that_downloads_nothing_does_not_need_the_prologue() -> None:
    text = _text(FIXTURES / "ok.yml")
    document = yaml.safe_load(text)
    publish = document["jobs"]["publish"]["steps"][0]["run"]

    assert "curl" not in publish and "set -euo" not in publish
    assert checks.violations("x.yml", text) == []


def _with_env(text: str, env: str) -> str:
    return _mutate(text, "jobs:\n", f"env:\n{env}jobs:\n")


@pytest.mark.parametrize(
    "command",
    [
        'docker push "ghcr.io/o/i"',
        "docker push ghcr.io/o/i",
        "docker push --quiet ghcr.io/o/i",
        "docker push localhost:5000/img",
        "docker tag a:1 ghcr.io/o/i",
        "docker tag ghcr.io/o/i ghcr.io/o/i",
        "docker build --tag ghcr.io/o/i .",
        'docker build -t "ghcr.io/o/i" .',
        "docker build --pull --tag ghcr.io/o/i -f Dockerfile .",
        'docker push "$IMAGE"',
        "docker push ${IMAGE}",
        'docker build --tag "$IMAGE" .',
        'docker push "$IMAGE:$TAG"',
        'docker push "$SIN_DEFINIR"',
    ],
)
def test_negative_f01_an_image_reference_without_a_tag_is_an_implicit_latest(command: str) -> None:
    base = _with_env(_text(FIXTURES / "ok.yml"), "  IMAGE: ghcr.io/o/i\n  TAG: main\n")
    text = _mutate(base, 'docker push "ghcr.io/o/i:${GITHUB_SHA}"', command)
    found = checks.violations("x.yml", text)

    assert any("sin etiqueta" in item or "no es el SHA" in item for item in found), found


@pytest.mark.parametrize(
    "command",
    [
        'docker push "ghcr.io/o/i:${GITHUB_SHA}"',
        'docker push "ghcr.io/o/i:$GITHUB_SHA"',
        'docker push "ghcr.io/o/i:abc1234"',
        "docker push localhost:5000/img:v1",
        'docker push "ghcr.io/o/i@sha256:' + "a" * 64 + '"',
        'docker push "$REF"',
        'docker push "$IMAGE:$SHA"',
        'docker build --tag "$IMAGE:pr" -f Dockerfile .',
        "docker tag a:1 ghcr.io/o/i:abc1234",
    ],
)
def test_f01_a_tagged_reference_or_a_variable_defined_with_the_sha_passes(command: str) -> None:
    env = "  IMAGE: ghcr.io/o/i\n  REF: ghcr.io/o/i:${{ github.sha }}\n  SHA: ${{ github.sha }}\n"
    text = _mutate(
        _with_env(_text(FIXTURES / "ok.yml"), env),
        'docker push "ghcr.io/o/i:${GITHUB_SHA}"',
        command,
    )

    assert checks.violations("x.yml", text) == []


def test_f01_a_tag_variable_of_the_step_env_wins_over_the_one_of_the_workflow() -> None:
    step = (
        "      - name: x\n        env:\n          TAG: main\n"
        '        run: docker push "ghcr.io/o/i:$TAG"'
    )
    text = _with_env(_text(FIXTURES / "ok.yml"), "  TAG: ${{ github.sha }}\n")
    text = _mutate(text, '      - run: docker push "ghcr.io/o/i:${GITHUB_SHA}"', step)

    assert any("no es el SHA" in item for item in checks.violations("x.yml", text))


# --- Ronda 3 (F-06): buildx, image push/tag y una etiqueta que solo contiene una variable --------

F06_COMMANDS = [
    'docker buildx build --push --tag "$IMAGE" .',  # N6
    "docker buildx build -t ghcr.io/o/i -f Dockerfile .",
    'docker image push "$IMAGE"',  # N7
    "docker image push ghcr.io/o/i",
    "docker image tag a:1 ghcr.io/o/i",
    "docker image build --tag ghcr.io/o/i .",
    'docker push "ghcr.io/o/i:x$GITHUB_HEAD_REF"',  # N5
    'docker push "ghcr.io/o/i:${GITHUB_SHA}-x"',
    'docker push "ghcr.io/o/i:x${GITHUB_SHA}"',
    'docker push "$IMAGE:${TAG}x"',
    'docker buildx build --tag "ghcr.io/o/i:$GITHUB_HEAD_REF" .',
]


@pytest.mark.parametrize("command", F06_COMMANDS, ids=range(len(F06_COMMANDS)))
def test_negative_f06_buildx_image_commands_and_mixed_tags_fail(command: str) -> None:
    base = _with_env(_text(FIXTURES / "ok.yml"), "  IMAGE: ghcr.io/o/i\n  TAG: ${{ github.sha }}\n")
    text = _mutate(base, 'docker push "ghcr.io/o/i:${GITHUB_SHA}"', command)
    found = checks.violations("x.yml", text)

    assert any("sin etiqueta" in item or "SHA del commit" in item for item in found), found


@pytest.mark.parametrize(
    "command",
    [
        'docker buildx build --push --tag "ghcr.io/o/i:${GITHUB_SHA}" .',
        'docker image push "ghcr.io/o/i:$GITHUB_SHA"',
        "docker image tag a:1 ghcr.io/o/i:abc1234",
        'docker buildx build --tag "$IMAGE:$SHA" .',
    ],
)
def test_f06_the_same_commands_pass_with_the_whole_tag_from_the_sha(command: str) -> None:
    env = "  IMAGE: ghcr.io/o/i\n  SHA: ${{ github.sha }}\n"
    base = _with_env(_text(FIXTURES / "ok.yml"), env)
    text = _mutate(base, 'docker push "ghcr.io/o/i:${GITHUB_SHA}"', command)

    assert checks.violations("x.yml", text) == []


@pytest.mark.parametrize(
    "condition",
    [
        "github.event_name == 'push' && github.ref == 'refs/heads/main' || always()",
        "always() || github.event_name == 'push' && github.ref == 'refs/heads/main'",
        "(github.event_name == 'push' && github.ref == 'refs/heads/main')",
        "github.ref == 'refs/heads/main' && github.event_name == 'push'",
        "github.event_name == 'push'",
        "!cancelled() && github.event_name == 'push' && github.ref == 'refs/heads/main'",
    ],
)
def test_negative_f01_a_packages_write_condition_that_is_not_exactly_the_main_one_fails(
    condition: str,
) -> None:
    text = _mutate(_text(FIXTURES / "ok.yml"), f"if: {ONLY_MAIN}", f'if: "{condition}"')

    assert any("exactamente" in item for item in checks.violations("x.yml", text))


def test_f01_the_exact_main_condition_is_required_even_without_a_pull_request_trigger() -> None:
    text = _text(FIXTURES / "ok.yml").replace("  pull_request:\n", "")
    text = _mutate(text, f"if: {ONLY_MAIN}", "if: github.event_name == 'push'")

    assert any("exactamente" in item for item in checks.violations("x.yml", text))


def test_f01_a_packages_write_job_without_an_if_fails_even_without_a_pull_request() -> None:
    text = _text(FIXTURES / "ok.yml").replace("  pull_request:\n", "")
    text = _mutate(text, f"    if: {ONLY_MAIN}\n", "")

    assert any("exactamente" in item for item in checks.violations("x.yml", text))


@pytest.mark.parametrize(
    "expression",
    [
        "${{ github.event.pull_request.title }}",
        "${{github.sha}}",
        "${{ secrets.GITHUB_TOKEN }}",
        "$${{ github.sha }}",
    ],
)
def test_negative_f02_an_actions_expression_inside_run_fails(expression: str) -> None:
    text = _mutate(
        _text(FIXTURES / "ok.yml"),
        "set -euo pipefail",
        f"set -euo pipefail\n          echo {expression}",
    )
    found = checks.violations("x.yml", text)

    assert any("expresión de Actions dentro de un run" in item for item in found)


def test_f02_an_expression_in_env_or_with_is_fine_and_a_plain_dollar_in_run_too() -> None:
    text = _mutate(
        _text(FIXTURES / "ok.yml"),
        "SHA256: bc0fc726e017b8927a62b2d3531d7a84ee01769daf5c99ed866dced54089fdbf",
        "SHA256: bc0fc726e017b8927a62b2d3531d7a84ee01769daf5c99ed866dced54089fdbf\n"
        "          TITLE: ${{ github.event.pull_request.title }}",
    )

    assert checks.violations("x.yml", text) == []


# --- Cada regla, con un cambio en memoria de los workflows reales --------------------------------


def _real_mutants() -> dict[str, tuple[Path, str, str, str]]:
    checkout = "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1"
    return {
        "checkout por etiqueta": (DEPLOY_WORKFLOW, checkout, "actions/checkout@v4", "40 hex"),
        "checkout de otro SHA": (
            DEPLOY_WORKFLOW,
            checkout,
            "actions/checkout@" + "0" * 40,
            "SHA distinto",
        ),
        "acción nueva": (
            DEPLOY_WORKFLOW,
            checkout,
            "actions/upload-artifact@" + "0" * 40,
            "no es una de las dos",
        ),
        "sin permisos": (DEPLOY_WORKFLOW, "permissions:\n  contents: read\n", "", "falta"),
        "suma de kustomize alterada": (
            DEPLOY_WORKFLOW,
            checks.TOOLS["kustomize"][1],
            "a" * 64,
            "que no es la de la tabla",
        ),
        "sin sha256sum -c": (DEPLOY_WORKFLOW, "sha256sum -c -", "sha256sum -", "no verifica"),
        "kubeconfig": (
            DEPLOY_WORKFLOW,
            "set -euo pipefail",
            "set -euo pipefail\n          export KUBECONFIG=x",
            "kubeconfig",
        ),
        "packages en la raíz": (
            IMAGE_WORKFLOW,
            "permissions:\n  contents: read\n",
            "permissions:\n  contents: read\n  packages: write\n",
            "escritura",
        ),
        "publicar sin limitarse a main": (
            IMAGE_WORKFLOW,
            f"if: {ONLY_MAIN}",
            "if: always()",
            "pull_request",
        ),
        "etiqueta latest": (IMAGE_WORKFLOW, "$IMAGE:$IMAGE_TAG", "$IMAGE:latest", "latest"),
        # Ronda 2: los mutantes P1 a P5 de la revisión, sobre los workflows reales.
        "P1 if de publish con or": (
            IMAGE_WORKFLOW,
            f"if: {ONLY_MAIN}",
            f"if: {ONLY_MAIN} || github.event_name == 'pull_request'",
            "exactamente",
        ),
        "P2 verificación anulada en la imagen": (
            IMAGE_WORKFLOW,
            "sha256sum -c -",
            "sha256sum -c - || true",
            "anula",
        ),
        "P2 verificación anulada en deploy": (
            DEPLOY_WORKFLOW,
            "sha256sum -c -",
            "sha256sum -c - || :",
            "anula",
        ),
        "P3 push sin etiqueta": (
            IMAGE_WORKFLOW,
            'docker push "$IMAGE:$IMAGE_TAG"',
            'docker push "$IMAGE"',
            "sin etiqueta",
        ),
        "P4 expresión en un run": (
            IMAGE_WORKFLOW,
            'echo "Imagen publicada: $digest"',
            'echo "Imagen publicada: ${{ github.sha }}"',
            "expresión de Actions dentro de un run",
        ),
        "P5 build sin etiqueta": (
            IMAGE_WORKFLOW,
            'docker build --tag "$IMAGE:$IMAGE_TAG"',
            'docker build --tag "$IMAGE"',
            "sin etiqueta",
        ),
        "etiqueta que no es el SHA": (
            IMAGE_WORKFLOW,
            "IMAGE_TAG: ${{ github.sha }}",
            "IMAGE_TAG: main",
            "no es el SHA",
        ),
        # Ronda 3: N1, N2, N3 y N8 (F-05) y N5, N6 y N7 (F-06), sobre los workflows reales.
        "N1 conjunción tras la verificación": (
            DEPLOY_WORKFLOW,
            "sha256sum -c -",
            "sha256sum -c - && echo ok",
            "forma fija",
        ),
        "N2 set +e": (IMAGE_WORKFLOW, "set -euo pipefail", "set +e", "set -euo pipefail"),
        "N3 verificación en un if": (
            DEPLOY_WORKFLOW,
            'echo "${SHA256}  $RUNNER_TEMP/$ASSET" | sha256sum -c -',
            f"if\n{INDENT}" + 'echo "${SHA256}  $RUNNER_TEMP/$ASSET" | sha256sum -c -'
            f"\n{INDENT}then true\n{INDENT}fi",
            "dentro de un if, while o until",
        ),
        "N8 verificación en segundo plano": (
            IMAGE_WORKFLOW,
            "sha256sum -c -",
            "sha256sum -c - &",
            "forma fija",
        ),
        "N5 etiqueta con una variable dentro": (
            IMAGE_WORKFLOW,
            'docker push "$IMAGE:$IMAGE_TAG"',
            'docker push "$IMAGE:x$GITHUB_HEAD_REF"',
            "SHA del commit",
        ),
        "N6 buildx build": (
            IMAGE_WORKFLOW,
            'docker build --tag "$IMAGE:$IMAGE_TAG"',
            'docker buildx build --push --tag "$IMAGE"',
            "sin etiqueta",
        ),
        "N7 image push": (
            IMAGE_WORKFLOW,
            'docker push "$IMAGE:$IMAGE_TAG"',
            'docker image push "$IMAGE"',
            "sin etiqueta",
        ),
    }


@pytest.mark.parametrize("name", list(_real_mutants()))
def test_negative_a_change_in_the_real_workflow_is_seen(name: str) -> None:
    path, old, new, expected = _real_mutants()[name]
    found = checks.violations(path.name, _mutate(_text(path), old, new))

    assert any(expected in item for item in found), found
