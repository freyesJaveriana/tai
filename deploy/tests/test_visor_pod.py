"""El visor de la demo como pod (deploy/demo-visor): se leen los manifiestos, nunca se aplican.

Solo para la demo: sin contraseña y con la imagen construida en Minikube. Lo que sí se fija es que
el pod no monte la clave, que su cuenta no salga de lo que hace el visor y que el NodePort sea el que
dice el script.
"""

from typing import Any

import yaml
from support import DEPLOY

VISOR = DEPLOY / "demo-visor"
ROOT = DEPLOY.parent


def _documents() -> list[dict[str, Any]]:
    kustomization = yaml.safe_load((VISOR / "kustomization.yaml").read_text(encoding="utf-8"))
    documents: list[dict[str, Any]] = []
    for name in kustomization["resources"]:
        documents += [
            item for item in yaml.safe_load_all((VISOR / name).read_text(encoding="utf-8")) if item
        ]
    return documents


def _one(kind: str, name: str) -> dict[str, Any]:
    [item] = [x for x in _documents() if x["kind"] == kind and x["metadata"]["name"] == name]
    return item


def test_the_kustomization_lists_every_manifest_of_the_folder() -> None:
    kustomization = yaml.safe_load((VISOR / "kustomization.yaml").read_text(encoding="utf-8"))
    manifests = sorted(
        item.name for item in VISOR.glob("*.yaml") if item.name != "kustomization.yaml"
    )
    assert sorted(kustomization["resources"]) == manifests
    assert "namespace" not in kustomization
    assert "secretGenerator" not in kustomization


def test_the_service_is_a_node_port_on_30851_to_the_viewer() -> None:
    service = _one("Service", "veridicus-visor")
    assert service["spec"]["type"] == "NodePort"
    [port] = service["spec"]["ports"]
    assert port["nodePort"] == 30851
    assert port["targetPort"] == "http"
    assert service["spec"]["selector"] == {"app.kubernetes.io/name": "veridicus-visor"}
    assert "30851" in (ROOT / "scripts" / "humano" / "visor-pod.sh").read_text(encoding="utf-8")


def test_the_pod_uses_the_local_image_and_never_mounts_a_secret() -> None:
    deployment = _one("Deployment", "veridicus-visor")
    spec = deployment["spec"]["template"]["spec"]
    [container] = spec["containers"]
    assert container["image"] == "veridicus-visor:demo"
    assert container["imagePullPolicy"] == "Never"
    assert spec["serviceAccountName"] == "veridicus-visor"
    assert container["ports"] == [{"name": "http", "containerPort": 8501}]
    text = yaml.safe_dump(deployment)
    assert "secretKeyRef" not in text
    assert "secretName" not in text
    assert "envFrom" not in text


def test_the_pod_meets_pod_security_restricted() -> None:
    spec = _one("Deployment", "veridicus-visor")["spec"]["template"]["spec"]
    assert spec["securityContext"]["runAsNonRoot"] is True
    assert spec["securityContext"]["seccompProfile"] == {"type": "RuntimeDefault"}
    [container] = spec["containers"]
    assert container["securityContext"]["allowPrivilegeEscalation"] is False
    assert container["securityContext"]["capabilities"] == {"drop": ["ALL"]}
    assert container["securityContext"]["readOnlyRootFilesystem"] is True
    assert set(container["resources"]) == {"requests", "limits"}
    labels = _one("Namespace", "veridicus-visor")["metadata"]["labels"]
    assert labels["pod-security.kubernetes.io/enforce"] == "restricted"


def test_the_account_reads_only_the_two_secrets_by_name() -> None:
    role = _one("Role", "veridicus-visor")
    assert role["metadata"]["namespace"] == "veridicus-demo"
    rules = [rule for rule in role["rules"] if "secrets" in rule["resources"]]
    assert rules == [
        {
            "apiGroups": [""],
            "resources": ["secrets"],
            "resourceNames": ["veridicus-anthropic", "veridicus-ghcr"],
            "verbs": ["get"],
        }
    ]
    for rule in role["rules"]:
        assert "*" not in rule["verbs"]
        assert "*" not in rule["resources"]


def test_the_only_cluster_wide_permission_is_the_demo_namespace() -> None:
    cluster_role = _one("ClusterRole", "veridicus-visor-namespace")
    assert cluster_role["rules"] == [
        {
            "apiGroups": [""],
            "resources": ["namespaces"],
            "resourceNames": ["veridicus-demo"],
            "verbs": ["get", "patch"],
        }
    ]
    kinds = [item["kind"] for item in _documents()]
    assert kinds.count("ClusterRole") == 1
    assert kinds.count("ClusterRoleBinding") == 1


def test_the_role_covers_every_kind_that_the_demo_kustomization_applies() -> None:
    demo = DEPLOY / "demo-analyzer"
    kustomization = yaml.safe_load((demo / "kustomization.yaml").read_text(encoding="utf-8"))
    kinds = {"ConfigMap"} if kustomization.get("configMapGenerator") else set()
    for name in kustomization["resources"]:
        for item in yaml.safe_load_all((demo / name).read_text(encoding="utf-8")):
            if item:
                kinds.add(item["kind"])
    plural = {
        "Job": "jobs",
        "ConfigMap": "configmaps",
        "ServiceAccount": "serviceaccounts",
        "NetworkPolicy": "networkpolicies",
    }
    granted = {
        resource
        for rule in _one("Role", "veridicus-visor")["rules"]
        if {"create", "patch"} <= set(rule["verbs"])
        for resource in rule["resources"]
    }
    assert kinds - {"Namespace"} <= set(plural), kinds
    for kind in kinds - {"Namespace"}:
        assert plural[kind] in granted, kind


def test_every_binding_points_at_the_viewer_account() -> None:
    for item in _documents():
        if item["kind"] in ("RoleBinding", "ClusterRoleBinding"):
            assert item["subjects"] == [
                {
                    "kind": "ServiceAccount",
                    "name": "veridicus-visor",
                    "namespace": "veridicus-visor",
                }
            ]


def test_the_image_runs_without_root_and_verifies_kubectl() -> None:
    text = (VISOR / "Dockerfile").read_text(encoding="utf-8")
    assert "USER 10001:10001" in text
    assert "kubectl.sha256" in text
    assert "--host 0.0.0.0" in text
    assert "latest" not in text


def test_the_script_copies_what_the_viewer_reads() -> None:
    script = (ROOT / "scripts" / "humano" / "visor-pod.sh").read_text(encoding="utf-8")
    for source in (
        "scripts/humano/visor-demo.py",
        "deploy/demo-analyzer",
        "deploy/demo-visor/ejemplos.json",
        "deploy/demo-visor/Dockerfile",
    ):
        assert f'"$raiz/{source}"' in script, source
        assert (ROOT / source).exists(), source
    assert "minikube image build" in script
    assert "rollout restart deployment/veridicus-visor" in script
