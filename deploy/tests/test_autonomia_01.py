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
        "crear-pull-secret-ghcr.sh",
        "crear-secret-anthropic.sh",
        "demo-analyzer.sh",
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
        "docs/validacion-zine/",
        "scripts/check-no-cluster-apply.sh",
    ]


def test_a_human_script_is_exempt_from_the_verbs_but_not_from_the_mark(tmp_path: Path) -> None:
    _write(tmp_path, "scripts/humano/a.sh", f"#!/bin/sh\n{MARK}\n{K} apply -f y\n{S} x\n")
    assert scan(tmp_path) == []
