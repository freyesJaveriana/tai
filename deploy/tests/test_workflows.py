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


def test_a_job_with_packages_write_is_fine_when_the_workflow_has_no_pull_request_trigger() -> None:
    text = _text(FIXTURES / "packages-en-pull-request.yml").replace("  pull_request:\n", "")

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


@pytest.mark.parametrize("kept", [f"{VERIFY} && echo ok", f"{VERIFY} && true"])
def test_f01_a_check_followed_by_a_conjunction_still_passes(kept: str) -> None:
    text = _mutate(_text(FIXTURES / "ok.yml"), VERIFY, kept)

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
    text = _mutate(_text(FIXTURES / "ok.yml"), f"if: {ONLY_MAIN}", f"if: {condition}")

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
    }


@pytest.mark.parametrize("name", list(_real_mutants()))
def test_negative_a_change_in_the_real_workflow_is_seen(name: str) -> None:
    path, old, new, expected = _real_mutants()[name]
    found = checks.violations(path.name, _mutate(_text(path), old, new))

    assert any(expected in item for item in found), found
