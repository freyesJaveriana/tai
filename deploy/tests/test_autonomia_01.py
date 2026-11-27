"""AUTONOMIA-01 (DP-08, paso 6 e): solo `scripts/humano/` toca el clúster.

La comprobación recorre el repositorio real y debe dar limpio. Sus controles negativos son
árboles pequeños: unos viven en `deploy/tests/fixtures/autonomia/` y otros se arman aquí con
fragmentos, para que este archivo no contenga ninguna de las operaciones que la comprobación
prohíbe (si las contuviera, la comprobación fallaría sobre sí misma).
"""

from pathlib import Path

import pytest
from autonomia import EXCEPTIONS, FIXTURES, MARK, scan
from support import DEPLOY

ROOT = DEPLOY.parent
CASES = DEPLOY / "tests" / "fixtures" / "autonomia"

# Fragmentos: ninguno, por sí solo, es una de las operaciones prohibidas.
K = "kube" + "ctl"
H = "he" + "lm"
S = "sb" + "atch"


def _write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_the_real_repository_has_no_workflow_or_script_that_touches_the_cluster() -> None:
    assert scan(ROOT) == []


def test_scripts_humano_exists_and_every_script_carries_the_mark() -> None:
    scripts = sorted((ROOT / "scripts" / "humano").glob("*.sh"))
    assert [item.name for item in scripts] == [
        "argocd-instalar.sh",
        "crear-pull-secret-ghcr.sh",
        "crear-secret-anthropic.sh",
        "demo-analyzer.sh",
        "visor-pod.sh",
    ]
    for script in scripts:
        lines = script.read_text(encoding="utf-8").splitlines()
        assert lines[0].startswith("#!")
        assert lines[1] == MARK


def test_the_fixtures_folder_is_skipped_by_the_real_scan_and_is_named_in_the_constant() -> None:
    assert FIXTURES == "deploy/tests/fixtures"
    assert (ROOT / FIXTURES).is_dir()


def test_a_clean_tree_with_a_marked_human_script_passes() -> None:
    assert scan(CASES / "limpio") == []


def test_negative_a_workflow_that_applies_to_the_cluster_fails() -> None:
    found = scan(CASES / "workflow-con-apply")
    assert any(
        item.startswith(".github/workflows/deploy.yml:") and "kubectl" in item for item in found
    )


def test_negative_a_script_outside_scripts_humano_that_upgrades_a_chart_fails() -> None:
    found = scan(CASES / "script-con-helm")
    assert any(item.startswith("scripts/instalar.sh:") and "helm" in item for item in found)


def test_negative_a_human_script_without_the_mark_fails() -> None:
    found = scan(CASES / "humano-sin-marca")
    assert found == [f"scripts/humano/aplicar.sh:2: falta la marca «{MARK}» tras el shebang"]


def test_negative_a_workflow_that_mentions_scripts_humano_fails() -> None:
    found = scan(CASES / "workflow-menciona-humano")
    assert found == [".github/workflows/ci.yml: un workflow no puede mencionar scripts/humano/"]


def test_a_human_script_without_shebang_must_open_with_the_mark(tmp_path: Path) -> None:
    _write(tmp_path, "scripts/humano/a.sh", f"{MARK}\nset -euo pipefail\n")
    _write(tmp_path, "scripts/humano/b.sh", "set -euo pipefail\n")
    assert [item.split(":")[0] for item in scan(tmp_path)] == ["scripts/humano/b.sh"]


def test_an_empty_human_script_fails(tmp_path: Path) -> None:
    _write(tmp_path, "scripts/humano/vacio.sh", "")
    assert scan(tmp_path)


DISGUISED = {
    "espacios": f"{K}   apply -f x.yaml",
    "tabulador": f"{K}\tapply -f x.yaml",
    "namespace corto": f"{K} -n x apply -f y",
    "namespace largo": f"{K} --namespace x apply -f y",
    "contexto": f"{K} --context=minikube apply -f y",
    "varias opciones": f"{K} -v 9 -n x --context=y apply -f z",
    "ruta absoluta": f"/usr/local/bin/{K} apply -f y",
    "mayúsculas": f"{K.upper()} APPLY -f y",
    "create": f"{K} create secret generic x",
    "delete": f"{K} delete job x",
    "patch": f"{K} patch job x -p y",
    "replace": f"{K} replace -f y",
    "continuación de línea": f"{K} \\\n  -n x \\\n  apply -f y",
    "tras una tubería": f"echo x | {K} apply -f -",
    "kustomize canalizado": f"kustomize build deploy | {K} -n x apply -f -",
    "upgrade con --install": f"{H} upgrade --install veridicus charts/veridicus",
    "paquetes con opciones": f"{H} --namespace v -n w install a b",
    "instalación de un chart": f"{H} install a b",
    "envío a SLURM": f"{S} trabajos/m1.sh",
    "envío a SLURM tras un comando": f"cd x && {S} --parsable job",
}


@pytest.mark.parametrize("line", DISGUISED.values(), ids=DISGUISED.keys())
@pytest.mark.parametrize("where", ["scripts/aplicar.sh", ".github/workflows/x.yml", "ops/x.py"])
def test_probe_4_a_disguised_cluster_operation_outside_scripts_humano_fails(
    tmp_path: Path, line: str, where: str
) -> None:
    _write(tmp_path, where, f"{line}\n")
    assert scan(tmp_path)


LIST_FORMS = {
    "lista de Python": f'subprocess.run(["{K}", "apply", "-f", "x.yaml"], check=True)',
    "lista de Python con comillas simples": f"run(['{K}', 'delete', 'job', 'x'])",
    "lista con opciones": f'run(["{K}", "-n", "x", "--context=y", "create", "-f", "z"])',
    "lista de Python en varias líneas": f'run(\n    [\n        "{K}",\n        "patch",\n    ]\n)',
    "lista flujo de YAML": f'command: ["{K}","apply","-f","x"]',
    "lista flujo de YAML sin comillas": f"command: [{K}, replace, -f, x]",
    "bloque de YAML": f"command:\n  - {K}\n  - apply\n  - -f",
    "bloque de YAML con opciones y comillas": f'args:\n  - "{K}"\n  - -n\n  - x\n  - "create"',
    "paquetes en lista": f'run(["{H}", "upgrade", "--install", "x"])',
    "paquetes en lista con opciones": f'run(["{H}", "--namespace", "v", "install", "a"])',
    "paquetes en bloque de YAML": f"command:\n  - {H}\n  - install\n  - a",
    "tras una sustitución": f"(which {K}) apply -f y",
    "con una sustitución de comando": f"$(command -v {K}) create secret generic x",
}


@pytest.mark.parametrize("line", LIST_FORMS.values(), ids=LIST_FORMS.keys())
@pytest.mark.parametrize("where", ["scripts/aplicar.py", "ops/x.yaml", ".github/workflows/x.yml"])
def test_f02_an_operation_written_as_an_argument_list_fails(
    tmp_path: Path, line: str, where: str
) -> None:
    _write(tmp_path, where, f"{line}\n")
    assert scan(tmp_path)


def test_f02_the_finding_names_the_line_of_the_list(tmp_path: Path) -> None:
    _write(tmp_path, "ops/x.yaml", f"a: 1\nb: 2\ncommand:\n  - {K}\n  - apply\n")
    assert scan(tmp_path) == ["ops/x.yaml:4: kubectl fuera de scripts/humano/"]


def _container(body: str, kind: str = "Pod") -> str:
    """Un manifiesto con un contenedor cuyo cuerpo (command y args) se pasa ya sangrado."""
    if kind == "CronJob":
        head = (
            "kind: CronJob\nspec:\n  jobTemplate:\n    spec:\n      template:\n        spec:\n"
            "          containers:\n            - name: c\n"
        )
        return head + "".join(f"              {line}\n" for line in body.splitlines())
    if kind == "Deployment":
        head = "kind: Deployment\nspec:\n  template:\n    spec:\n      initContainers:\n        - name: c\n"
        return head + "".join(f"          {line}\n" for line in body.splitlines())
    head = "kind: Pod\nspec:\n  containers:\n    - name: c\n"
    return head + "".join(f"      {line}\n" for line in body.splitlines())


F10_FORMS = {
    "command y args en flujo": _container(f'command: ["{K}"]\nargs: ["apply", "-f", "x"]'),
    "command y args en bloque": _container(f"command:\n  - {K}\nargs:\n  - apply\n  - -f"),
    "command y args en flujo sin comillas": _container(f"command: [{K}]\nargs: [delete, job]"),
    "command con la ruta absoluta": _container(f'command: ["/usr/bin/{K}"]\nargs: ["create"]'),
    "CronJob": _container(f'command: ["{K}"]\nargs: ["apply", "-f", "x"]', "CronJob"),
    "contenedor de inicio de un Deployment": _container(
        f'command: ["{K}"]\nargs: ["patch", "x"]', "Deployment"
    ),
    "helm en command y args": _container(f'command: ["{H}"]\nargs: ["upgrade", "--install"]'),
    "orden completa en command": _container(f'command: ["sh", "-c", "{K} apply -f y"]'),
}


@pytest.mark.parametrize("text", F10_FORMS.values(), ids=F10_FORMS.keys())
def test_f10_command_and_args_of_a_container_are_joined(tmp_path: Path, text: str) -> None:
    _write(tmp_path, "ops/job.yaml", text)
    assert scan(tmp_path)


def test_f10_command_and_args_in_a_second_document_of_the_file(tmp_path: Path) -> None:
    other = "kind: ConfigMap\ndata:\n  a: b\n---\n"
    _write(tmp_path, "ops/job.yaml", other + F10_FORMS["command y args en flujo"])
    assert len(scan(tmp_path)) == 1


F10_SAFE = {
    "lectura": _container(f'command: ["{K}"]\nargs: ["get", "pods"]'),
    "otra herramienta": _container('command: ["echo"]\nargs: ["apply"]'),
    "solo args": _container('args: ["apply"]'),
    "command que no es lista": _container("command: hola"),
    "args con un número": _container(f'command: ["{K}"]\nargs: [1, get]'),
}


@pytest.mark.parametrize("text", F10_SAFE.values(), ids=F10_SAFE.keys())
def test_f10_read_only_commands_and_odd_shapes_do_not_fail(tmp_path: Path, text: str) -> None:
    _write(tmp_path, "ops/job.yaml", text)
    assert scan(tmp_path) == []


def test_f10_a_yaml_that_does_not_parse_still_gets_the_text_rule(tmp_path: Path) -> None:
    _write(tmp_path, "ops/roto.yaml", f"a: [\n{K} apply -f y\n")
    assert scan(tmp_path)
    _write(tmp_path, "ops/plantilla.yaml", "a: {{ .Values.x }}\nb: [\n")
    assert [item.split(":")[0] for item in scan(tmp_path)] == ["ops/roto.yaml"]


def test_f10_an_exempt_yaml_is_exempt_for_command_and_args_too(tmp_path: Path) -> None:
    _write(tmp_path, "uno.yaml", F10_FORMS["command y args en flujo"])
    assert scan(tmp_path, {"uno.yaml": frozenset({"kubectl"})}) == []


F10_TEXT = {
    "bloque con ruta absoluta": f"command:\n  - /usr/bin/{K}\n  - apply\n  - -f",
    "bloque con ruta relativa y comillas": f'command:\n  - "./bin/{K}"\n  - "apply"',
    "tupla de Python": f'subprocess.run(("{K}", "apply"))',
    "tupla con opciones": f"run(('{K}', '-n', 'x', 'delete', 'job'))",
    "tupla de helm": f'run(("{H}", "install", "a"))',
}


@pytest.mark.parametrize("line", F10_TEXT.values(), ids=F10_TEXT.keys())
@pytest.mark.parametrize("where", ["scripts/aplicar.py", "ops/x.yaml"])
def test_f10_an_absolute_path_in_a_block_and_a_tuple_fail(
    tmp_path: Path, line: str, where: str
) -> None:
    _write(tmp_path, where, f"{line}\n")
    assert scan(tmp_path)


def test_f10_a_block_with_a_path_to_another_tool_does_not_fail(tmp_path: Path) -> None:
    _write(tmp_path, "ops/x.yaml", f"command:\n  - /usr/bin/{K}-otro\n  - apply\n")
    assert scan(tmp_path) == []


SAFE_LISTS = {
    "lectura en lista": f'run(["{K}", "get", "pods", "-n", "x"])',
    "lectura en bloque": f"command:\n  - {K}\n  - get\n  - applyset",
    "listas distintas": f"command:\n  - {K}\n  - get\nenv:\n  - apply",
    "otra herramienta": 'run(["echo", "apply"])',
    "helm de lectura": f'run(["{H}", "template", "x"])',
    "bloque de otra cosa": f"args:\n  - {K}\n  - logs\n  - job/x\n",
}


@pytest.mark.parametrize("line", SAFE_LISTS.values(), ids=SAFE_LISTS.keys())
def test_f02_read_only_lists_do_not_fail(tmp_path: Path, line: str) -> None:
    _write(tmp_path, "ops/x.yaml", f"{line}\n")
    assert scan(tmp_path) == []


def test_f02_a_list_in_an_exempt_file_is_exempt_only_for_its_rule(tmp_path: Path) -> None:
    exceptions = {"uno.py": frozenset({"kubectl"})}
    _write(tmp_path, "uno.py", f'run(["{K}", "apply"])\nrun(["{H}", "install"])\n')
    found = scan(tmp_path, exceptions)
    assert [item.split(":")[0] for item in found] == ["uno.py"]
    assert "helm" in found[0]


SAFE = {
    "lectura": f"{K} get pods -n x",
    "describe": f"{K} -n x describe applyset",
    "logs": f"{K} logs job/x",
    "wait": f"{K} wait --for=condition=complete job/x",
    "helm template": f"{H} template x charts/x",
    "helm list": f"{H} list -A",
    "prosa": "aplicar el despliegue lo hace el humano",
    "palabra parecida": "unsbatchable apply",
    "tubería de otra herramienta": f"echo {K} | grep apply",
}


@pytest.mark.parametrize("line", SAFE.values(), ids=SAFE.keys())
def test_read_only_commands_and_prose_do_not_fail(tmp_path: Path, line: str) -> None:
    _write(tmp_path, "scripts/lectura.sh", f"{line}\n")
    assert scan(tmp_path) == []


def test_every_skipped_folder_is_ignored(tmp_path: Path) -> None:
    for folder in (".git", ".venv", ".worktrees", "node_modules", "pkg/__pycache__"):
        _write(tmp_path, f"{folder}/x.sh", f"{K} apply -f y\n")
    _write(tmp_path, f"{FIXTURES}/x.sh", f"{K} apply -f y\n")
    assert scan(tmp_path) == []


def test_files_of_other_kinds_outside_github_are_not_read(tmp_path: Path) -> None:
    _write(tmp_path, "docs/nota.md", f"{K} apply -f y\n")
    _write(tmp_path, ".github/pull_request_template.md", f"{K} apply -f y\n")
    assert [item.split(":")[0] for item in scan(tmp_path)] == [".github/pull_request_template.md"]


def test_a_makefile_and_a_yaml_manifest_are_read(tmp_path: Path) -> None:
    _write(tmp_path, "Makefile", f"aplicar:\n\t{K} apply -f y\n")
    _write(tmp_path, "ops/job.yaml", f'command: ["sh", "-c", "{H} install a b"]\n')
    assert sorted(item.split(":")[0] for item in scan(tmp_path)) == ["Makefile", "ops/job.yaml"]


def test_an_exception_exempts_only_the_rules_it_names(tmp_path: Path) -> None:
    exceptions = {"docs/validacion-zine/": frozenset({"slurm"}), "uno.py": frozenset({"helm"})}
    _write(tmp_path, "docs/validacion-zine/a.sh", f"{S} job\n")
    _write(tmp_path, "docs/validacion-zine/b.sh", f"{K} apply -f y\n")
    _write(tmp_path, "uno.py", f"{H} install a b\n")
    _write(tmp_path, "otro.py", f"{H} install a b\n")
    found = scan(tmp_path, exceptions)
    assert sorted(item.split(":")[0] for item in found) == ["docs/validacion-zine/b.sh", "otro.py"]


def test_the_declared_exceptions_are_only_the_known_ones() -> None:
    assert sorted(EXCEPTIONS) == [
        "contracts/src/veridicus_contracts/checks/ci_workflows.py",
        "contracts/tests/checks/test_ci_workflows.py",
        "contracts/tests/tools/test_pull_request_template.py",
        "docs/validacion-zine/comprobar_reporte.py",
        "docs/validacion-zine/comun.sh",
        "scripts/check-no-cluster-apply.sh",
    ]


def test_f08_no_exception_is_a_whole_folder_and_every_one_exists() -> None:
    for path in EXCEPTIONS:
        assert not path.endswith("/"), path
        assert (ROOT / path).is_file(), path


def test_f08_a_new_file_in_the_zine_folder_is_not_exempt(tmp_path: Path) -> None:
    _write(tmp_path, "docs/validacion-zine/comun.sh", f"{S} job\n")
    _write(tmp_path, "docs/validacion-zine/nuevo.sh", f"{S} job\n")
    found = scan(tmp_path)
    assert [item.split(":")[0] for item in found] == ["docs/validacion-zine/nuevo.sh"]


def test_a_human_script_is_exempt_from_the_verbs_but_not_from_the_mark(tmp_path: Path) -> None:
    _write(tmp_path, "scripts/humano/a.sh", f"#!/bin/sh\n{MARK}\n{K} apply -f y\n{S} x\n")
    assert scan(tmp_path) == []
