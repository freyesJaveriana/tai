"""Las políticas de Kyverno de `deploy/policies/` (paso 6): su estructura y su coherencia.

El contenedor no tiene Kyverno: `kyverno test deploy/policies` lo corre la CI (U02-T03). Aquí se
comprueba lo que sí se puede sin él: cada política existe como `ClusterPolicy` en modo `Enforce`,
tiene su `kyverno-test.yaml` con al menos un resultado `pass` y uno `fail`, sus resultados nombran
reglas y recursos que existen, y los recursos de paso y de fallo se comportan como dice la regla
equivalente de pytest (las reglas (a) a (d) de `policy_checks`).
"""

import copy
import json
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
import yaml
from policy_checks import (
    SECRET,
    Resource,
    image_violations,
    load,
    resources_violations,
    security_violations,
)
from support import DEPLOY

POLICIES = DEPLOY / "policies"
NAMESPACE = "veridicus-demo"

EXPECTED = {
    "veridicus-secret-solo-job": "secret",
    "veridicus-imagen-con-etiqueta": "imagen",
    "veridicus-pod-restricted": "seguridad",
    "veridicus-recursos-requeridos": "recursos",
}


def _uses_the_secret_without_being_the_job(pod: Resource) -> list[str]:
    owners = (pod.get("metadata") or {}).get("ownerReferences") or []
    is_the_job = any(
        owner.get("kind") == "Job" and owner.get("name") == "veridicus-analyzer-demo"
        for owner in owners
    )
    mentions = SECRET in json.dumps(pod.get("spec"))
    return ["usa el Secret sin ser el Job"] if mentions and not is_the_job else []


EQUIVALENT: dict[str, Callable[[Resource], list[str]]] = {
    "veridicus-secret-solo-job": _uses_the_secret_without_being_the_job,
    "veridicus-imagen-con-etiqueta": lambda pod: image_violations([pod]),
    "veridicus-pod-restricted": lambda pod: security_violations([pod]),
    "veridicus-recursos-requeridos": lambda pod: resources_violations([pod]),
}


def layout_violations(directory: Path) -> list[str]:
    """Infracciones de estructura de una carpeta de política; vacío si cumple."""
    name = directory.name
    found: list[str] = []
    policy_file = directory / "policy.yaml"
    test_file = directory / "kyverno-test.yaml"
    if not policy_file.is_file():
        return [f"{name}: falta policy.yaml"]
    policy = load(policy_file)[0]
    if policy.get("kind") != "ClusterPolicy":
        found.append(f"{name}: no es una ClusterPolicy")
    if (policy.get("metadata") or {}).get("name") != name:
        found.append(f"{name}: el nombre de la política no es el de su carpeta")
    spec = policy.get("spec") or {}
    if spec.get("validationFailureAction") != "Enforce":
        found.append(f"{name}: no está en modo Enforce")
    rules = {rule["name"]: rule for rule in spec.get("rules") or []}
    if not rules:
        found.append(f"{name}: no tiene reglas")
    for rule_name, rule in rules.items():
        scoped = yaml.safe_dump(rule.get("match"))
        if NAMESPACE not in scoped:
            found.append(f"{name}: la regla {rule_name} no se limita al namespace {NAMESPACE}")
    if not test_file.is_file():
        return [*found, f"{name}: falta kyverno-test.yaml"]
    test = load(test_file)[0]
    if test.get("kind") != "Test" or test.get("policies") != ["policy.yaml"]:
        found.append(f"{name}: kyverno-test.yaml no es un Test de policy.yaml")
    existing: dict[str, Resource] = {}
    for rel in test.get("resources") or []:
        path = directory / rel
        if not path.is_file() or Path(rel).parts[0] != "resources":
            found.append(f"{name}: el recurso {rel} no existe en resources/")
            continue
        for document in load(path):
            existing[document["metadata"]["name"]] = document
    results = test.get("results") or []
    outcomes = {item.get("result") for item in results}
    if not {"pass", "fail"} <= outcomes:
        found.append(f"{name}: kyverno-test.yaml necesita al menos un pass y un fail")
    if not outcomes <= {"pass", "fail"}:
        found.append(f"{name}: un resultado no es pass ni fail")
    for item in results:
        if item.get("policy") != name:
            found.append(f"{name}: un resultado nombra otra política")
        if item.get("rule") not in rules:
            found.append(f"{name}: un resultado nombra la regla inexistente {item.get('rule')}")
        for resource in item.get("resources") or []:
            if resource not in existing:
                found.append(f"{name}: un resultado nombra el recurso inexistente {resource}")
    return found


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_each_policy_has_its_layout(name: str) -> None:
    assert layout_violations(POLICIES / name) == []


def test_there_are_exactly_the_four_policies_and_no_other_folder() -> None:
    assert sorted(item.name for item in POLICIES.iterdir() if item.is_dir()) == sorted(EXPECTED)


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_each_policy_has_a_pass_and_a_fail_result(name: str) -> None:
    results = load(POLICIES / name / "kyverno-test.yaml")[0]["results"]
    assert {item["result"] for item in results} == {"pass", "fail"}


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_each_pass_and_fail_resource_behaves_as_the_pytest_rule_says(name: str) -> None:
    directory = POLICIES / name
    test = load(directory / "kyverno-test.yaml")[0]
    resources: dict[str, Resource] = {}
    for rel in test["resources"]:
        for document in load(directory / rel):
            resources[document["metadata"]["name"]] = document
    verdicts: dict[str, set[str]] = {}
    for item in test["results"]:
        for resource in item["resources"]:
            verdicts.setdefault(resource, set()).add(item["result"])
    assert set(verdicts) == set(resources), "cada recurso aparece en algún resultado"
    for resource, outcomes in verdicts.items():
        broken = EQUIVALENT[name](resources[resource])
        if "fail" in outcomes:
            assert broken, f"{resource} debería fallar la regla"
        else:
            assert not broken, f"{resource} debería pasar la regla: {broken}"


def _copy(tmp_path: Path, name: str) -> Path:
    target = tmp_path / name
    shutil.copytree(POLICIES / name, target)
    return target


def _edit(path: Path, change: Callable[[Any], Any]) -> None:
    document = load(path)[0]
    path.write_text(yaml.safe_dump(change(document) or document), encoding="utf-8")


def _only(result: str) -> Callable[[Any], Any]:
    def change(document: Any) -> Any:
        document["results"] = [item for item in document["results"] if item["result"] == result]

    return change


NEGATIVES: dict[str, Callable[[Path], None]] = {
    "sin policy.yaml": lambda d: (d / "policy.yaml").unlink(),
    "sin kyverno-test.yaml": lambda d: (d / "kyverno-test.yaml").unlink(),
    "solo resultados pass": lambda d: _edit(d / "kyverno-test.yaml", _only("pass")),
    "solo resultados fail": lambda d: _edit(d / "kyverno-test.yaml", _only("fail")),
    "no está en Enforce": lambda d: _edit(
        d / "policy.yaml", lambda p: p["spec"].__setitem__("validationFailureAction", "Audit")
    ),
    "no es ClusterPolicy": lambda d: _edit(
        d / "policy.yaml", lambda p: p.__setitem__("kind", "Policy")
    ),
    "nombre distinto": lambda d: _edit(
        d / "policy.yaml", lambda p: p["metadata"].__setitem__("name", "otra")
    ),
    "regla sin namespace": lambda d: _edit(
        d / "policy.yaml",
        lambda p: p["spec"]["rules"][0].__setitem__(
            "match", {"any": [{"resources": {"kinds": ["Pod"]}}]}
        ),
    ),
    "resultado con regla inexistente": lambda d: _edit(
        d / "kyverno-test.yaml", lambda t: t["results"][0].__setitem__("rule", "no-existe")
    ),
    "resultado con otra política": lambda d: _edit(
        d / "kyverno-test.yaml", lambda t: t["results"][0].__setitem__("policy", "otra")
    ),
    "resultado con recurso inexistente": lambda d: _edit(
        d / "kyverno-test.yaml", lambda t: t["results"][0].__setitem__("resources", ["nada"])
    ),
    "resultado ni pass ni fail": lambda d: _edit(
        d / "kyverno-test.yaml", lambda t: t["results"][0].__setitem__("result", "skip")
    ),
    "recurso que no existe": lambda d: _edit(
        d / "kyverno-test.yaml", lambda t: t["resources"].append("resources/falta.yaml")
    ),
    "recurso fuera de resources": lambda d: _edit(
        d / "kyverno-test.yaml", lambda t: t["resources"].append("policy.yaml")
    ),
    "no es un Test": lambda d: _edit(
        d / "kyverno-test.yaml", lambda t: t.__setitem__("kind", "Otro")
    ),
    "sin reglas": lambda d: _edit(d / "policy.yaml", lambda p: p["spec"].__setitem__("rules", [])),
}


@pytest.mark.parametrize("change", NEGATIVES.values(), ids=NEGATIVES.keys())
def test_negative_a_broken_policy_folder_fails_the_layout_check(
    tmp_path: Path, change: Callable[[Path], None]
) -> None:
    directory = _copy(tmp_path, "veridicus-pod-restricted")
    change(directory)
    assert layout_violations(directory)


def test_the_layout_check_accepts_an_untouched_copy(tmp_path: Path) -> None:
    assert layout_violations(_copy(tmp_path, "veridicus-pod-restricted")) == []


def test_the_pytest_rule_equivalents_see_a_broken_pod() -> None:
    bare: Resource = {
        "kind": "Pod",
        "metadata": {"name": "p"},
        "spec": {"containers": [{"name": "c", "image": "x"}]},
    }
    for name, rule in EQUIVALENT.items():
        assert rule(copy.deepcopy(bare)) != [] or name == "veridicus-secret-solo-job"
    with_secret = {**bare, "spec": {"containers": [], "volumes": [{"secret": SECRET}]}}
    assert EQUIVALENT["veridicus-secret-solo-job"](with_secret)
