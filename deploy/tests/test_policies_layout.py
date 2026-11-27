"""Las políticas de Kyverno de `deploy/policies/` (paso 6): su estructura y su coherencia.

El contenedor no tiene Kyverno: `kyverno test deploy/policies` lo corre la CI (U02-T03). Aquí se
comprueba lo que sí se puede sin él: cada política existe como `ClusterPolicy` en modo `Enforce`,
tiene su `kyverno-test.yaml` con al menos un resultado `pass` y uno `fail`, sus resultados nombran
reglas y recursos que existen, y los recursos de paso y de fallo se comportan como dice la regla
equivalente de pytest (las reglas (a) a (d) de `policy_checks`).
"""

import copy
import json
import re
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any

import policy_checks as checks
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


JOB_CONTROLLER = "system:serviceaccount:kube-system:job-controller"


def _uses_the_secret_without_being_the_job(pod: Resource, username: str) -> list[str]:
    owners = (pod.get("metadata") or {}).get("ownerReferences") or []
    is_the_job = any(
        owner.get("kind") == "Job" and owner.get("name") == "veridicus-analyzer-demo"
        for owner in owners
    )
    mentions = SECRET in json.dumps(pod.get("spec"))
    allowed = is_the_job and username == JOB_CONTROLLER
    return ["usa el Secret sin ser el Job"] if mentions and not allowed else []


EQUIVALENT: dict[str, Callable[[Resource, str], list[str]]] = {
    "veridicus-secret-solo-job": _uses_the_secret_without_being_the_job,
    "veridicus-imagen-con-etiqueta": lambda pod, _user: image_violations([pod]),
    "veridicus-pod-restricted": lambda pod, _user: security_violations([pod]),
    "veridicus-recursos-requeridos": lambda pod, _user: resources_violations([pod]),
}


def _username(directory: Path, test: Resource) -> str:
    """El usuario que admite los recursos de un `kyverno-test.yaml` (vacío si no declara uno)."""
    rel = test.get("userinfo")
    if not rel:
        return ""
    return str(load(directory / rel)[0]["userInfo"]["username"])


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
        broken = EQUIVALENT[name](resources[resource], _username(directory, test))
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
        assert rule(copy.deepcopy(bare), "") != [] or name == "veridicus-secret-solo-job"
    with_secret = {**bare, "spec": {"containers": [], "volumes": [{"secret": SECRET}]}}
    assert EQUIVALENT["veridicus-secret-solo-job"](with_secret, JOB_CONTROLLER)


# ---------------------------------------------------------------- ronda 2: F-04 y F-05
# Kyverno no corre aquí. Estas pruebas leen cada política como datos y exigen que cubra lo mismo
# que la regla de pytest: los tres tipos de contenedor, la forma de la imagen y quién admite el pod.

LISTS = ("containers", "=(initContainers)", "=(ephemeralContainers)")


def _rule(name: str, rule_name: str | None = None) -> Resource:
    policy = load(POLICIES / name / "policy.yaml")[0]
    rules = policy["spec"]["rules"]
    return next(item for item in rules if rule_name in (None, item["name"]))


def _pattern_spec(name: str) -> dict[str, Any]:
    spec: dict[str, Any] = _rule(name)["validate"]["pattern"]["spec"]
    return spec


def test_f04_the_restricted_policy_checks_the_three_kinds_of_container() -> None:
    spec = _pattern_spec("veridicus-pod-restricted")
    for key in LISTS:
        assert key in spec, key
        [element] = spec[key]
        context = element["securityContext"]
        assert context["readOnlyRootFilesystem"] is True, key
        assert context["allowPrivilegeEscalation"] is False, key
        assert context["capabilities"]["drop"] == ["ALL"], key
        assert context["capabilities"]["X(add)"] == "null", key
        assert context["=(privileged)"] == "false", key
        assert context["=(runAsUser)"] == ">0", key
        assert context["=(runAsNonRoot)"] is True, key
        assert context["=(seccompProfile)"] == {"=(type)": "RuntimeDefault | Localhost"}, key


def test_f03_the_restricted_policy_rejects_the_host_and_host_path_volumes() -> None:
    spec = _pattern_spec("veridicus-pod-restricted")
    for flag in ("=(hostNetwork)", "=(hostPID)", "=(hostIPC)"):
        assert spec[flag] == "false", flag
    assert spec["=(volumes)"] == [{"X(hostPath)": "null"}]
    assert spec["securityContext"]["=(runAsUser)"] == ">0"


def test_f04_the_resources_policy_checks_the_three_kinds_of_container() -> None:
    spec = _pattern_spec("veridicus-recursos-requeridos")
    for key in LISTS:
        assert key in spec, key
        [element] = spec[key]
        assert element["resources"] == {
            "requests": {"cpu": "?*", "memory": "?*"},
            "limits": {"cpu": "?*", "memory": "?*"},
        }, key


IMAGES = [
    "ghcr.io/o/a:v1",
    "ghcr.io/o/a",
    "ghcr.io/o/a:",
    "ghcr.io/o/a:latest",
    "ghcr.io/o/a:latest@sha256:" + "a" * 64,
    "ghcr.io/o/a:v1@sha256:" + "a" * 64,
    "ghcr.io/o/a@sha256:" + "a" * 64,
    "registry:5000/img",
    "registry:5000/img:v1",
    "registry:5000/ruta/img:v1@sha256:" + "a" * 64,
    "localhost:5000/x",
    "busybox",
    "busybox:latest",
    "a@sha256:",
]


def _image_regexes() -> tuple[str, str]:
    name = "veridicus-imagen-con-etiqueta"
    pinned = re.findall(r"regex_match\('([^']*)'", json.dumps(_rule(name, "imagen-con-etiqueta")))
    latest = re.findall(r"regex_match\('([^']*)'", json.dumps(_rule(name, "imagen-sin-latest")))
    assert len(pinned) == 1 and len(latest) == 1
    return pinned[0], latest[0]


def test_f04_the_image_policy_uses_the_regexes_of_the_pytest_rule() -> None:
    pinned, latest = _image_regexes()
    assert pinned == checks.IMAGE_PINNED
    assert latest == checks.IMAGE_LATEST


@pytest.mark.parametrize("image", IMAGES)
def test_f04_the_image_regexes_give_the_verdict_of_the_pytest_rule(image: str) -> None:
    pinned, latest = _image_regexes()
    pod: Resource = {
        "kind": "Pod",
        "metadata": {"name": "p"},
        "spec": {"containers": [{"name": "c", "image": image}]},
    }
    found = image_violations([pod])
    assert bool(re.search(pinned, image)) == (not any("no tiene etiqueta" in x for x in found))
    expected_latest = bool(re.search(latest, image)) and bool(re.search(pinned, image))
    assert expected_latest == any("es latest" in x for x in found)


def test_f04_the_image_rules_look_at_every_kind_of_container() -> None:
    name = "veridicus-imagen-con-etiqueta"
    for rule_name in ("imagen-con-etiqueta", "imagen-sin-latest"):
        [item] = _rule(name, rule_name)["validate"]["foreach"]
        assert (
            item["list"]
            == "request.object.spec.[containers, initContainers, ephemeralContainers][]"
        )
        assert "{{ element.image }}" in json.dumps(item)


def test_f05_the_secret_policy_also_checks_who_admits_the_pod() -> None:
    text = (POLICIES / "veridicus-secret-solo-job" / "policy.yaml").read_text(encoding="utf-8")
    assert "request.userInfo.username" in text
    assert JOB_CONTROLLER in text
    assert "cualquiera podría copiar" not in text
    assert "ownerReferences" in text


def test_f05_the_main_test_admits_as_the_job_controller() -> None:
    directory = POLICIES / "veridicus-secret-solo-job"
    test = load(directory / "kyverno-test.yaml")[0]
    assert _username(directory, test) == JOB_CONTROLLER


def test_f05_the_same_pod_admitted_by_another_user_fails() -> None:
    directory = POLICIES / "veridicus-secret-solo-job" / "otro-usuario"
    test = load(directory / "kyverno-test.yaml")[0]
    assert test["policies"] == ["../policy.yaml"]
    assert test["resources"] == ["../resources/pass-pod-del-job.yaml"]
    assert [item["result"] for item in test["results"]] == ["fail"]
    user = _username(directory, test)
    assert user and user != JOB_CONTROLLER
    [pod] = load(directory / test["resources"][0])
    assert pod["metadata"]["name"] == test["results"][0]["resources"][0]
    assert _uses_the_secret_without_being_the_job(pod, user)
    assert _uses_the_secret_without_being_the_job(pod, JOB_CONTROLLER) == []


def test_f04_every_new_failing_resource_is_listed_with_its_result() -> None:
    wanted = {
        "veridicus-pod-restricted": {
            "contenedor-root",
            "contenedor-no-root-falso",
            "contenedor-seccomp-unconfined",
            "contenedor-con-capacidades-add",
            "contenedor-privilegiado",
            "host-network",
            "host-pid",
            "host-ipc",
            "volumen-hostpath",
            "init-como-root",
            "init-sin-security-context",
            "efimero-privilegiado",
        },
        "veridicus-imagen-con-etiqueta": {
            "registro-con-puerto",
            "latest-con-digest",
            "init-sin-etiqueta",
            "init-latest",
            "efimero-sin-etiqueta",
            "efimero-latest",
        },
        "veridicus-recursos-requeridos": {"init-sin-recursos", "efimero-sin-limits"},
    }
    for name, resources in wanted.items():
        results = load(POLICIES / name / "kyverno-test.yaml")[0]["results"]
        listed = {r for item in results for r in item["resources"]}
        assert resources <= listed, (name, resources - listed)
