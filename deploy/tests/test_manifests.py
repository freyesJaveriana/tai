"""Los manifiestos de la demo (pasos 4 y 5): el Job, el namespace y la NetworkPolicy.

Las pruebas leen los YAML de `deploy/demo-analyzer/`, los renderizan como lo haría
la kustomization y comprueban campo por campo. Cada regla lleva su control negativo: un
manifiesto alterado en memoria que la regla debe ver. No se ejecuta kubectl.
"""

import copy
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import policy_checks as checks
import pytest
import yaml
from policy_checks import (
    DENY_ALL,
    JOB_NAME,
    JOB_POLICY,
    SECRET,
    Resource,
    containers,
    image_violations,
    load,
    network_violations,
    pod_specs,
    render,
    resources_violations,
    secret_violations,
    security_violations,
)
from support import DEPLOY

MANIFESTS = DEPLOY / "demo-analyzer"
IMAGE = "ghcr.io/freyesjaveriana/veridicus-analyzer-cli"


@pytest.fixture(name="rendered")
def _rendered() -> list[Resource]:
    return render(MANIFESTS)


def _one(resources: list[Resource], kind: str, name: str) -> Resource:
    found = [
        item for item in resources if item.get("kind") == kind and item["metadata"]["name"] == name
    ]
    assert len(found) == 1, f"debe haber un {kind}/{name}"
    return found[0]


def _job(resources: list[Resource]) -> Resource:
    return _one(resources, "Job", JOB_NAME)


def _pod(resources: list[Resource]) -> dict[str, Any]:
    spec: dict[str, Any] = _job(resources)["spec"]["template"]["spec"]
    return spec


def _container(resources: list[Resource]) -> dict[str, Any]:
    found = list(containers(_pod(resources)))
    assert len(found) == 1
    return found[0]


def _deployment(pod: dict[str, Any], name: str = "otro") -> Resource:
    return {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {"name": name, "namespace": "veridicus-demo"},
        "spec": {"template": {"spec": pod}},
    }


def _network(resources: list[Resource]) -> list[Resource]:
    return [item for item in resources if item["kind"] == "NetworkPolicy"]


# ---------------------------------------------------------------- el paso 4: lo que hay en los archivos


def test_the_kustomization_sets_namespace_images_and_the_input_configmap() -> None:
    kustomization = load(MANIFESTS / "kustomization.yaml")[0]
    assert kustomization["namespace"] == "veridicus-demo"
    assert kustomization["images"] == [{"name": IMAGE, "newName": IMAGE, "newTag": "sha-pendiente"}]
    [generator] = kustomization["configMapGenerator"]
    assert generator["name"] == "veridicus-demo-entrada"
    assert sorted(generator["files"]) == ["entrada/coherente.json", "entrada/contradiccion.json"]
    assert {"namespace.yaml", "serviceaccount.yaml", "job.yaml", "networkpolicy.yaml"} <= set(
        kustomization["resources"]
    )


def test_the_namespace_enforces_pod_security_restricted() -> None:
    namespace = load(MANIFESTS / "namespace.yaml")[0]
    assert namespace["kind"] == "Namespace"
    assert namespace["metadata"]["name"] == "veridicus-demo"
    labels = namespace["metadata"]["labels"]
    for mode in ("enforce", "warn", "audit"):
        assert labels[f"pod-security.kubernetes.io/{mode}"] == "restricted"


def test_the_job_has_its_limits_of_time_and_retries(rendered: list[Resource]) -> None:
    job = _job(rendered)
    assert job["metadata"]["namespace"] == "veridicus-demo"
    assert job["metadata"]["labels"]["app.kubernetes.io/name"] == JOB_NAME
    assert job["spec"]["backoffLimit"] == 0
    assert job["spec"]["activeDeadlineSeconds"] == 900
    assert job["spec"]["ttlSecondsAfterFinished"] == 3600
    template = job["spec"]["template"]
    assert template["metadata"]["labels"]["app.kubernetes.io/name"] == JOB_NAME
    assert template["spec"]["restartPolicy"] == "Never"


def test_the_job_has_a_service_account_of_its_own_without_permissions(
    rendered: list[Resource],
) -> None:
    pod = _pod(rendered)
    assert pod["automountServiceAccountToken"] is False
    account = _one(rendered, "ServiceAccount", JOB_NAME)
    assert pod["serviceAccountName"] == account["metadata"]["name"]
    assert account["automountServiceAccountToken"] is False
    assert not [item for item in rendered if item["kind"] in {"Role", "RoleBinding", "ClusterRole"}]
    assert not [item for item in rendered if item["kind"].endswith("RoleBinding")]


def test_the_pod_and_the_container_have_the_restricted_security_context(
    rendered: list[Resource],
) -> None:
    pod = _pod(rendered)
    assert pod["securityContext"] == {
        "runAsNonRoot": True,
        "runAsUser": 10001,
        "runAsGroup": 10001,
        "fsGroup": 10001,
        "seccompProfile": {"type": "RuntimeDefault"},
    }
    assert _container(rendered)["securityContext"] == {
        "readOnlyRootFilesystem": True,
        "allowPrivilegeEscalation": False,
        "capabilities": {"drop": ["ALL"]},
    }


def test_the_container_has_the_requests_and_limits_of_the_design(rendered: list[Resource]) -> None:
    assert _container(rendered)["resources"] == {
        "requests": {"cpu": "250m", "memory": "256Mi"},
        "limits": {"cpu": "1", "memory": "512Mi"},
    }


def test_the_volumes_are_the_read_only_input_and_two_scratch_directories(
    rendered: list[Resource],
) -> None:
    pod = _pod(rendered)
    container = _container(rendered)
    volumes = {item["name"]: item for item in pod["volumes"]}
    assert volumes["entrada"]["configMap"]["name"] == "veridicus-demo-entrada"
    assert "emptyDir" in volumes["salida"]
    assert "emptyDir" in volumes["tmp"]
    mounts = {item["mountPath"]: item for item in container["volumeMounts"]}
    assert set(mounts) == {"/entrada", "/salida", "/tmp"}  # noqa: S108 (ruta del contenedor)
    assert mounts["/entrada"]["name"] == "entrada"
    assert mounts["/entrada"]["readOnly"] is True
    assert mounts["/salida"]["name"] == "salida"
    assert mounts["/tmp"]["name"] == "tmp"  # noqa: S108 (ruta del contenedor)
    assert len(volumes) == 3


def test_the_environment_takes_the_key_from_the_secret_and_never_holds_its_value(
    rendered: list[Resource],
) -> None:
    env = {item["name"]: item for item in _container(rendered)["env"]}
    assert env["VERIDICUS_ANTHROPIC_API_KEY"] == {
        "name": "VERIDICUS_ANTHROPIC_API_KEY",
        "valueFrom": {"secretKeyRef": {"name": SECRET, "key": "api-key", "optional": False}},
    }
    assert env["VERIDICUS_LIMIT_MODEL_CALL_TIMEOUT_S"]["value"] == "300"
    assert env["VERIDICUS_DEMO_ENTRADA"]["value"] == "/entrada"
    assert env["VERIDICUS_DEMO_SALIDA"]["value"] == "/salida"
    assert set(env) == {
        "VERIDICUS_ANTHROPIC_API_KEY",
        "VERIDICUS_LIMIT_MODEL_CALL_TIMEOUT_S",
        "VERIDICUS_DEMO_ENTRADA",
        "VERIDICUS_DEMO_SALIDA",
    }
    assert "value" not in env["VERIDICUS_ANTHROPIC_API_KEY"]


def test_the_image_comes_from_ghcr_with_the_provisional_tag_and_a_pull_secret(
    rendered: list[Resource],
) -> None:
    assert _container(rendered)["image"] == f"{IMAGE}:sha-pendiente"
    assert _pod(rendered)["imagePullSecrets"] == [{"name": "veridicus-ghcr"}]
    raw = _job(load(MANIFESTS / "job.yaml"))
    assert next(iter(containers(raw["spec"]["template"]["spec"])))["image"] == IMAGE


def test_the_configmap_carries_the_two_synthetic_inputs(rendered: list[Resource]) -> None:
    configmap = _one(rendered, "ConfigMap", "veridicus-demo-entrada")
    assert sorted(configmap["data"]) == ["coherente.json", "contradiccion.json"]
    assert configmap["metadata"]["namespace"] == "veridicus-demo"


def test_the_manifests_never_contain_the_value_of_a_secret(rendered: list[Resource]) -> None:
    assert not [item for item in rendered if item["kind"] == "Secret"]


# ---------------------------------------------------------------- el paso 5: la NetworkPolicy


def test_the_network_policies_of_the_demo_pass_the_rule(rendered: list[Resource]) -> None:
    assert network_violations(rendered) == []


def test_deny_all_selects_every_pod_in_both_directions_without_rules(
    rendered: list[Resource],
) -> None:
    deny = _one(rendered, "NetworkPolicy", DENY_ALL)
    assert deny["spec"] == {"podSelector": {}, "policyTypes": ["Ingress", "Egress"]}


def test_the_job_policy_selects_only_the_job_and_allows_443_and_dns(
    rendered: list[Resource],
) -> None:
    allow = _one(rendered, "NetworkPolicy", JOB_POLICY)
    assert allow["spec"]["podSelector"] == {"matchLabels": {"app.kubernetes.io/name": JOB_NAME}}
    assert allow["spec"]["policyTypes"] == ["Egress"]
    https, dns = allow["spec"]["egress"]
    assert https["ports"] == [{"protocol": "TCP", "port": 443}]
    assert https["to"] == [
        {
            "ipBlock": {
                "cidr": "0.0.0.0/0",
                "except": ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "169.254.0.0/16"],
            }
        }
    ]
    assert {(item["protocol"], item["port"]) for item in dns["ports"]} == {
        ("UDP", 53),
        ("TCP", 53),
    }
    assert dns["to"] == [
        {
            "namespaceSelector": {"matchLabels": {"kubernetes.io/metadata.name": "kube-system"}},
            "podSelector": {"matchLabels": {"k8s-app": "kube-dns"}},
        }
    ]


def _without(path: list[str | int]) -> Callable[[Resource], None]:
    def mutate(policy: Resource) -> None:
        target: Any = policy
        for key in path[:-1]:
            target = target[key]
        del target[path[-1]]

    return mutate


def _set(path: list[str | int], value: Any) -> Callable[[Resource], None]:
    def mutate(policy: Resource) -> None:
        target: Any = policy
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = value

    return mutate


ALLOW_MUTATIONS: dict[str, Callable[[Resource], None]] = {
    "ipBlock sin except": _without(["spec", "egress", 0, "to", 0, "ipBlock", "except"]),
    "except incompleto": _set(["spec", "egress", 0, "to", 0, "ipBlock", "except"], ["10.0.0.0/8"]),
    "puerto 80 en vez de 443": _set(["spec", "egress", 0, "ports", 0, "port"], 80),
    "sin puertos": _without(["spec", "egress", 0, "ports"]),
    "sin destino": _without(["spec", "egress", 0, "to"]),
    "cidr distinto": _set(["spec", "egress", 0, "to", 0, "ipBlock", "cidr"], "0.0.0.0/1"),
    "DNS sin namespaceSelector": _without(["spec", "egress", 1, "to", 0, "namespaceSelector"]),
    "DNS sin podSelector": _without(["spec", "egress", 1, "to", 0, "podSelector"]),
    "DNS sin destino (cualquiera)": _without(["spec", "egress", 1, "to"]),
    "DNS hacia otro namespace": _set(
        ["spec", "egress", 1, "to", 0, "namespaceSelector", "matchLabels"],
        {"kubernetes.io/metadata.name": "default"},
    ),
    "DNS hacia otros pods": _set(
        ["spec", "egress", 1, "to", 0, "podSelector", "matchLabels"], {"k8s-app": "otro"}
    ),
    "DNS con un puerto extra": _set(
        ["spec", "egress", 1, "ports"],
        [
            {"protocol": "UDP", "port": 53},
            {"protocol": "TCP", "port": 53},
            {"protocol": "TCP", "port": 22},
        ],
    ),
    "DNS solo UDP": _set(["spec", "egress", 1, "ports"], [{"protocol": "UDP", "port": 53}]),
    "endPort en el 443 abre hasta el 65535": _set(
        ["spec", "egress", 0, "ports", 0, "endPort"], 65535
    ),
    "endPort igual al puerto 443": _set(["spec", "egress", 0, "ports", 0, "endPort"], 443),
    "endPort en el 53 abre hasta el 65535": _set(
        ["spec", "egress", 1, "ports", 0, "endPort"], 65535
    ),
    "endPort igual al puerto 53": _set(["spec", "egress", 1, "ports", 1, "endPort"], 53),
    "selector de otro pod": _set(["spec", "podSelector"], {"matchLabels": {"app": "otro"}}),
    "selector vacío": _set(["spec", "podSelector"], {}),
    "abre entrada": _set(["spec", "ingress"], [{}]),
}


@pytest.mark.parametrize("change", ALLOW_MUTATIONS.values(), ids=ALLOW_MUTATIONS.keys())
def test_a_broken_job_policy_fails_the_network_rule(
    rendered: list[Resource], change: Callable[[Resource], None]
) -> None:
    broken = copy.deepcopy(rendered)
    change(_one(broken, "NetworkPolicy", JOB_POLICY))
    assert network_violations(broken)


DENY_MUTATIONS: dict[str, Callable[[Resource], None]] = {
    "sin policyTypes de salida": _set(["spec", "policyTypes"], ["Ingress"]),
    "sin policyTypes de entrada": _set(["spec", "policyTypes"], ["Egress"]),
    "selecciona solo un pod": _set(["spec", "podSelector"], {"matchLabels": {"a": "b"}}),
    "lleva reglas de salida": _set(
        ["spec", "egress"], [{"to": [{"ipBlock": {"cidr": "0.0.0.0/0"}}]}]
    ),
}


@pytest.mark.parametrize("change", DENY_MUTATIONS.values(), ids=DENY_MUTATIONS.keys())
def test_a_weakened_deny_all_fails_the_network_rule(
    rendered: list[Resource], change: Callable[[Resource], None]
) -> None:
    broken = copy.deepcopy(rendered)
    change(_one(broken, "NetworkPolicy", DENY_ALL))
    assert network_violations(broken)


@pytest.mark.parametrize("missing", [DENY_ALL, JOB_POLICY])
def test_a_missing_policy_fails_the_network_rule(rendered: list[Resource], missing: str) -> None:
    broken = [
        item
        for item in rendered
        if not (item["kind"] == "NetworkPolicy" and item["metadata"]["name"] == missing)
    ]
    assert network_violations(broken)


def _extra_policy(egress: list[dict[str, Any]], selector: dict[str, Any]) -> Resource:
    return {
        "apiVersion": "networking.k8s.io/v1",
        "kind": "NetworkPolicy",
        "metadata": {"name": "otra", "namespace": "veridicus-demo"},
        "spec": {"podSelector": selector, "policyTypes": ["Egress"], "egress": egress},
    }


def test_probe_2_a_second_egress_policy_for_every_pod_fails(rendered: list[Resource]) -> None:
    extra = _extra_policy([{"to": [{"ipBlock": {"cidr": "0.0.0.0/0"}}]}], {})
    violations = network_violations([*rendered, extra])
    assert any("selector distinto del Job" in item for item in violations)


def test_probe_2_a_second_policy_for_another_pod_fails_even_with_a_clean_rule(
    rendered: list[Resource],
) -> None:
    allow = _one(rendered, "NetworkPolicy", JOB_POLICY)
    extra = _extra_policy(copy.deepcopy(allow["spec"]["egress"]), {"matchLabels": {"a": "b"}})
    assert any(
        "selector distinto del Job" in item for item in network_violations([*rendered, extra])
    )


def test_probe_2_an_ipblock_without_except_for_the_job_fails(rendered: list[Resource]) -> None:
    extra = _extra_policy(
        [{"to": [{"ipBlock": {"cidr": "0.0.0.0/0"}}], "ports": [{"protocol": "TCP", "port": 443}]}],
        {"matchLabels": {"app.kubernetes.io/name": JOB_NAME}},
    )
    assert any("no excluye" in item for item in network_violations([*rendered, extra]))


def test_probe_3_a_port_53_rule_without_selectors_fails(rendered: list[Resource]) -> None:
    ports = [{"protocol": "UDP", "port": 53}, {"protocol": "TCP", "port": 53}]
    for destination in (None, [], [{"ipBlock": {"cidr": "0.0.0.0/0"}}]):
        rule: dict[str, Any] = {"ports": ports}
        if destination is not None:
            rule["to"] = destination
        extra = _extra_policy([rule], {"matchLabels": {"app.kubernetes.io/name": JOB_NAME}})
        assert network_violations([*rendered, extra]), destination


def test_f01_an_extra_policy_with_an_end_port_for_the_job_fails(rendered: list[Resource]) -> None:
    selector = {"matchLabels": {"app.kubernetes.io/name": JOB_NAME}}
    for port, name in ((443, "https"), (53, "dns")):
        allow = copy.deepcopy(_one(rendered, "NetworkPolicy", JOB_POLICY))
        egress = allow["spec"]["egress"][0 if name == "https" else 1]
        egress["ports"][0]["endPort"] = 65535
        extra = _extra_policy([egress], selector)
        assert any("endPort" in item for item in network_violations([*rendered, extra])), port


def test_a_rule_that_mixes_port_53_with_others_fails(rendered: list[Resource]) -> None:
    broken = copy.deepcopy(rendered)
    allow = _one(broken, "NetworkPolicy", JOB_POLICY)
    allow["spec"]["egress"][0]["ports"].append({"protocol": "UDP", "port": 53})
    assert any("mezcla" in item for item in network_violations(broken))


# ---------------------------------------------------------------- la regla (a): el Secret


def test_only_the_job_references_the_secret_and_it_does(rendered: list[Resource]) -> None:
    assert secret_violations(rendered) == []


def _mounted_pod(extra_container: dict[str, Any], volumes: list[dict[str, Any]]) -> Resource:
    return _deployment(
        {
            "containers": [{"name": "x", "image": "x:1", **extra_container}],
            "volumes": volumes,
        }
    )


SECRET_USERS: dict[str, Resource] = {
    "envFrom": _mounted_pod({"envFrom": [{"secretRef": {"name": SECRET}}]}, []),
    "secretKeyRef": _mounted_pod(
        {"env": [{"name": "K", "valueFrom": {"secretKeyRef": {"name": SECRET, "key": "api-key"}}}]},
        [],
    ),
    "volumen": _mounted_pod({}, [{"name": "s", "secret": {"secretName": SECRET}}]),
    "volumen proyectado": _mounted_pod(
        {}, [{"name": "s", "projected": {"sources": [{"secret": {"name": SECRET}}]}}]
    ),
}


@pytest.mark.parametrize("user", SECRET_USERS.values(), ids=SECRET_USERS.keys())
def test_probe_1_another_workload_with_the_secret_fails(
    rendered: list[Resource], user: Resource
) -> None:
    violations = secret_violations([*rendered, user])
    assert any("Deployment/otro referencia el Secret" in item for item in violations)


def test_a_second_job_with_the_secret_fails(rendered: list[Resource]) -> None:
    other = copy.deepcopy(_job(rendered))
    other["metadata"]["name"] = "otro-job"
    assert any("Job/otro-job" in item for item in secret_violations([*rendered, other]))


def test_a_service_account_that_lists_the_secret_fails(rendered: list[Resource]) -> None:
    broken = copy.deepcopy(rendered)
    _one(broken, "ServiceAccount", JOB_NAME)["secrets"] = [{"name": SECRET}]
    assert secret_violations(broken)


def test_the_manifests_carrying_the_secret_itself_fail(rendered: list[Resource]) -> None:
    secret = {"apiVersion": "v1", "kind": "Secret", "metadata": {"name": SECRET}, "data": {}}
    assert any("propio Secret" in item for item in secret_violations([*rendered, secret]))


def test_a_job_that_no_longer_references_the_secret_fails(rendered: list[Resource]) -> None:
    broken = copy.deepcopy(rendered)
    _container(broken)["env"] = [
        item for item in _container(broken)["env"] if item["name"] != "VERIDICUS_ANTHROPIC_API_KEY"
    ]
    assert any("no referencia" in item for item in secret_violations(broken))


# ---------------------------------------------------------------- la regla (b): las imágenes


def test_the_images_of_the_demo_pass_the_rule(rendered: list[Resource]) -> None:
    assert image_violations(rendered) == []


DIGEST = "sha256:" + "a" * 64


@pytest.mark.parametrize(
    "image",
    [f"{IMAGE}:latest", IMAGE, f"{IMAGE}:", f"{IMAGE}:latest@{DIGEST}", "localhost:5000/x"],
)
def test_an_image_that_is_latest_or_has_no_tag_fails(rendered: list[Resource], image: str) -> None:
    broken = copy.deepcopy(rendered)
    _container(broken)["image"] = image
    assert image_violations(broken)


@pytest.mark.parametrize(
    "image", [f"{IMAGE}:sha-abc1234", f"{IMAGE}@{DIGEST}", f"{IMAGE}:v1@{DIGEST}"]
)
def test_an_image_with_a_tag_or_a_digest_passes(rendered: list[Resource], image: str) -> None:
    fixed = copy.deepcopy(rendered)
    _container(fixed)["image"] = image
    assert image_violations(fixed) == []


def test_an_init_container_without_a_tag_fails(rendered: list[Resource]) -> None:
    broken = copy.deepcopy(rendered)
    _pod(broken)["initContainers"] = [{"name": "init", "image": "busybox"}]
    assert any("init" in item for item in image_violations(broken))


# ---------------------------------------------------------------- la regla (c): securityContext


def test_the_pods_of_the_demo_pass_the_security_rule(rendered: list[Resource]) -> None:
    assert security_violations(rendered) == []


def _drop_pod(key: str) -> Callable[[dict[str, Any]], None]:
    return lambda pod: pod["securityContext"].pop(key)


def _drop_container(key: str) -> Callable[[dict[str, Any]], None]:
    return lambda pod: pod["containers"][0]["securityContext"].pop(key)


def _set_pod(key: str, value: Any) -> Callable[[dict[str, Any]], None]:
    return lambda pod: pod["securityContext"].__setitem__(key, value)


def _set_container(key: str, value: Any) -> Callable[[dict[str, Any]], None]:
    return lambda pod: pod["containers"][0]["securityContext"].__setitem__(key, value)


_RESTRICTED: dict[str, Any] = {
    "readOnlyRootFilesystem": True,
    "allowPrivilegeEscalation": False,
    "capabilities": {"drop": ["ALL"]},
}

SECURITY_MUTATIONS: dict[str, Callable[[dict[str, Any]], None]] = {
    "sin runAsNonRoot": _drop_pod("runAsNonRoot"),
    "runAsNonRoot falso": _set_pod("runAsNonRoot", False),
    "runAsUser 0": _set_pod("runAsUser", 0),
    "sin seccompProfile": _drop_pod("seccompProfile"),
    "seccomp Unconfined": _set_pod("seccompProfile", {"type": "Unconfined"}),
    "sin readOnlyRootFilesystem": _drop_container("readOnlyRootFilesystem"),
    "readOnlyRootFilesystem falso": _set_container("readOnlyRootFilesystem", False),
    "sin allowPrivilegeEscalation": _drop_container("allowPrivilegeEscalation"),
    "allowPrivilegeEscalation verdadero": _set_container("allowPrivilegeEscalation", True),
    "sin capabilities": _drop_container("capabilities"),
    "drop sin ALL": _set_container("capabilities", {"drop": ["NET_RAW"]}),
    "privileged": _set_container("privileged", True),
    "hostNetwork": lambda pod: pod.__setitem__("hostNetwork", True),
    "hostPID": lambda pod: pod.__setitem__("hostPID", True),
    "hostIPC": lambda pod: pod.__setitem__("hostIPC", True),
    "runAsUser 0 en el contenedor": _set_container("runAsUser", 0),
    "runAsNonRoot falso en el contenedor": _set_container("runAsNonRoot", False),
    "seccomp Unconfined en el contenedor": _set_container("seccompProfile", {"type": "Unconfined"}),
    "capabilities.add": _set_container("capabilities", {"drop": ["ALL"], "add": ["SYS_ADMIN"]}),
    "capabilities.add vacío": _set_container("capabilities", {"drop": ["ALL"], "add": []}),
    "volumen hostPath": lambda pod: pod["volumes"].append({"name": "h", "hostPath": {"path": "/"}}),
    "contenedor de inicio como root": lambda pod: pod.__setitem__(
        "initContainers",
        [{"name": "i", "image": "x:1", "securityContext": {**_RESTRICTED, "runAsUser": 0}}],
    ),
    "contenedor efímero privilegiado": lambda pod: pod.__setitem__(
        "ephemeralContainers",
        [{"name": "e", "image": "x:1", "securityContext": {**_RESTRICTED, "privileged": True}}],
    ),
    "contenedor sin securityContext": lambda pod: pod["containers"][0].pop("securityContext"),
    "pod sin securityContext": lambda pod: pod.pop("securityContext"),
    "contenedor de inicio sin securityContext": lambda pod: pod.__setitem__(
        "initContainers", [{"name": "i", "image": "x:1"}]
    ),
}


@pytest.mark.parametrize("change", SECURITY_MUTATIONS.values(), ids=SECURITY_MUTATIONS.keys())
def test_a_pod_that_loses_a_security_field_fails(
    rendered: list[Resource], change: Callable[[dict[str, Any]], None]
) -> None:
    broken = copy.deepcopy(rendered)
    change(_pod(broken))
    assert security_violations(broken)


@pytest.mark.parametrize(
    "context",
    [
        {"runAsUser": 10001},
        {"runAsNonRoot": True},
        {"seccompProfile": {"type": "RuntimeDefault"}},
        {"seccompProfile": {"type": "Localhost", "localhostProfile": "p.json"}},
        {"capabilities": {"drop": ["ALL"]}},
    ],
)
def test_f03_a_container_that_only_repeats_the_restricted_values_passes(
    rendered: list[Resource], context: dict[str, Any]
) -> None:
    fixed = copy.deepcopy(rendered)
    _container(fixed)["securityContext"].update(context)
    assert security_violations(fixed) == []


def test_f03_an_ephemeral_container_without_security_context_fails(
    rendered: list[Resource],
) -> None:
    broken = copy.deepcopy(rendered)
    _pod(broken)["ephemeralContainers"] = [{"name": "e", "image": "x:1"}]
    assert any("contenedor e:" in item for item in security_violations(broken))


def test_another_workload_without_security_context_fails(rendered: list[Resource]) -> None:
    other = _deployment({"containers": [{"name": "x", "image": "x:1"}]})
    assert security_violations([*rendered, other])


def test_a_cronjob_and_a_bare_pod_are_checked_too() -> None:
    bare = {"kind": "Pod", "metadata": {"name": "p"}, "spec": {"containers": [{"name": "c"}]}}
    cron = {
        "kind": "CronJob",
        "metadata": {"name": "c"},
        "spec": {"jobTemplate": {"spec": {"template": {"spec": {"containers": [{"name": "c"}]}}}}},
    }
    assert security_violations([bare]) and security_violations([cron])
    assert [kind for kind, _ in pod_specs(cron)] == ["CronJob"]


# ---------------------------------------------------------------- la regla (d): requests y limits


def test_the_containers_of_the_demo_pass_the_resources_rule(rendered: list[Resource]) -> None:
    assert resources_violations(rendered) == []


RESOURCE_MUTATIONS: dict[str, Callable[[dict[str, Any]], None]] = {
    "sin resources": lambda c: c.pop("resources"),
    "sin requests": lambda c: c["resources"].pop("requests"),
    "sin limits": lambda c: c["resources"].pop("limits"),
    "sin cpu en requests": lambda c: c["resources"]["requests"].pop("cpu"),
    "sin memoria en requests": lambda c: c["resources"]["requests"].pop("memory"),
    "sin cpu en limits": lambda c: c["resources"]["limits"].pop("cpu"),
    "sin memoria en limits": lambda c: c["resources"]["limits"].pop("memory"),
}


@pytest.mark.parametrize("change", RESOURCE_MUTATIONS.values(), ids=RESOURCE_MUTATIONS.keys())
def test_a_container_that_loses_requests_or_limits_fails(
    rendered: list[Resource], change: Callable[[dict[str, Any]], None]
) -> None:
    broken = copy.deepcopy(rendered)
    change(_container(broken))
    assert resources_violations(broken)


def test_an_init_container_without_resources_fails(rendered: list[Resource]) -> None:
    broken = copy.deepcopy(rendered)
    _pod(broken)["initContainers"] = [{"name": "init", "image": "x:1"}]
    assert any("init" in item for item in resources_violations(broken))


def test_the_render_leaves_untouched_what_the_kustomization_does_not_name(
    tmp_path: Path,
) -> None:
    (tmp_path / "kustomization.yaml").write_text("resources:\n  - a.yaml\n", encoding="utf-8")
    (tmp_path / "a.yaml").write_text(
        "kind: Pod\nmetadata:\n  name: p\nspec:\n  containers:\n    - name: c\n      image: x\n",
        encoding="utf-8",
    )
    [pod] = render(tmp_path)
    assert "namespace" not in pod["metadata"]
    assert pod["spec"]["containers"][0]["image"] == "x"


# ---------------------------------------------------------------- K-102: las reglas sobre el render real
# La CI corre estas mismas pruebas con VERIDICUS_RENDER apuntando al resultado de `kustomize build`.
# Sin la variable, todo sigue como hasta ahora (la lectura de primer nivel de `render`).

RENDER_ENV = "VERIDICUS_RENDER"


def _write_render(path: Path, resources: list[Resource]) -> Path:
    path.write_text(yaml.safe_dump_all(resources), encoding="utf-8")
    return path


def test_k102_the_variable_is_named_as_the_task_says() -> None:
    assert checks.RENDER_ENV == RENDER_ENV


def test_k102_without_the_variable_the_render_is_the_first_level_reading() -> None:
    assert checks.render_resources(MANIFESTS, {}) == render(MANIFESTS)
    assert checks.render_resources(MANIFESTS, {RENDER_ENV: ""}) == render(MANIFESTS)


def test_k102_with_the_variable_the_resources_are_the_ones_of_the_file(tmp_path: Path) -> None:
    only = [{"kind": "Namespace", "metadata": {"name": "otro"}}]
    path = _write_render(tmp_path / "render.yaml", only)

    assert checks.render_resources(MANIFESTS, {RENDER_ENV: str(path)}) == only


def test_negative_k102_a_broken_real_render_fails_the_rules(tmp_path: Path) -> None:
    broken = copy.deepcopy(render(MANIFESTS))
    _container(broken)["image"] = f"{IMAGE}:latest"
    del _pod(broken)["securityContext"]
    path = _write_render(tmp_path / "render.yaml", broken)

    loaded = checks.render_resources(MANIFESTS, {RENDER_ENV: str(path)})

    assert image_violations(loaded)
    assert security_violations(loaded)
    assert image_violations(render(MANIFESTS)) == [], "la lectura de primer nivel no ve ese cambio"


def test_k102_a_clean_render_file_passes_every_rule(tmp_path: Path) -> None:
    path = _write_render(tmp_path / "render.yaml", render(MANIFESTS))
    loaded = checks.render_resources(MANIFESTS, {RENDER_ENV: str(path)})

    assert loaded == render(MANIFESTS)
    assert network_violations(loaded) == []
    assert secret_violations(loaded) == []
    assert image_violations(loaded) == []
    assert security_violations(loaded) == []
    assert resources_violations(loaded) == []


def test_k102_the_hash_suffix_kustomize_adds_to_a_generated_configmap_is_removed(
    tmp_path: Path,
) -> None:
    suffixed = copy.deepcopy(render(MANIFESTS))
    for item in suffixed:
        if item["kind"] == "ConfigMap":
            item["metadata"]["name"] = "veridicus-demo-entrada-7d9f2k5g8m"
    _pod(suffixed)["volumes"][0]["configMap"]["name"] = "veridicus-demo-entrada-7d9f2k5g8m"
    path = _write_render(tmp_path / "render.yaml", suffixed)

    loaded = checks.render_resources(MANIFESTS, {RENDER_ENV: str(path)})

    assert loaded == render(MANIFESTS)


def test_k102_a_name_that_only_looks_like_a_suffixed_one_is_left_alone(tmp_path: Path) -> None:
    other = [{"kind": "ConfigMap", "metadata": {"name": "otro-0123456789"}, "data": {}}]
    path = _write_render(tmp_path / "render.yaml", other)

    assert checks.render_resources(MANIFESTS, {RENDER_ENV: str(path)}) == other


def test_negative_k102_a_missing_or_empty_render_file_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        checks.render_resources(MANIFESTS, {RENDER_ENV: str(tmp_path / "no-existe.yaml")})
    empty = tmp_path / "vacio.yaml"
    empty.write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="sin recursos"):
        checks.render_resources(MANIFESTS, {RENDER_ENV: str(empty)})


def test_k102_the_rendered_fixture_of_this_file_reads_the_variable(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    only = [{"kind": "Namespace", "metadata": {"name": "otro"}}]
    path = _write_render(tmp_path / "render.yaml", only)
    current = sys.modules[__name__]._current_render

    monkeypatch.delenv(RENDER_ENV, raising=False)
    assert current() == render(MANIFESTS)
    monkeypatch.setenv(RENDER_ENV, str(path))
    assert current() == only
