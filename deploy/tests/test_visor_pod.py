"""El visor de la demo como pod (deploy/demo-visor): se leen los manifiestos, nunca se aplican.

Solo para la demo: sin contraseña y con la imagen construida en Minikube. Lo que sí se fija es que
el pod no monte la clave, que su cuenta no salga de lo que hace el visor y que el NodePort sea el que
dice el script.
"""

import re
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
    assert "secretRef" not in text
    # Lo único que entra al entorno es el ConfigMap del color de la barra (demo GitOps).
    assert container["envFrom"] == [{"configMapRef": {"name": "veridicus-visor-apariencia"}}]
    assert "env" not in container


def test_the_appearance_config_map_holds_only_a_valid_bar_color() -> None:
    kustomization = yaml.safe_load((VISOR / "kustomization.yaml").read_text(encoding="utf-8"))
    [generator] = [
        item
        for item in kustomization["configMapGenerator"]
        if item["name"] == "veridicus-visor-apariencia"
    ]
    assert generator == {
        "name": "veridicus-visor-apariencia",
        "namespace": "veridicus-visor",
        "envs": ["apariencia.properties"],
    }
    lines = (VISOR / "apariencia.properties").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert re.fullmatch(r"VERIDICUS_VISOR_COLOR_BANDA=#[0-9a-f]{6}", lines[0])


def test_the_color_scripts_only_propose_by_pr_and_only_read_the_cluster() -> None:
    humano = ROOT / "scripts" / "humano"
    color = (humano / "gitops-color.sh").read_text(encoding="utf-8")
    assert "kube" + "ctl" not in color
    assert "gh pr create" in color
    assert 'git -C "$raiz" revert --no-edit' in color
    assert "deploy/demo-visor/apariencia.properties" in color
    watch = (humano / "gitops-observar.sh").read_text(encoding="utf-8")
    commands = [line for line in watch.splitlines() if not line.lstrip().startswith("#")]
    writes = [line for line in commands if re.search(r"kubectl (annotate|label|set|scale)", line)]
    refresh = (
        'kubectl annotate application "$app" --namespace "$ns_argo" '
        "argocd.argoproj.io/refresh=normal --overwrite > /dev/null"
    )
    assert writes == [refresh]
    rbac = (humano / "rbac-evidencia.sh").read_text(encoding="utf-8")
    verbs = set(re.findall(r"\bkubectl (\w+)", rbac))
    assert verbs == {"auth", "get"}


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
    # Argo CD revertiría un «rollout restart» (cambia la plantilla): el script borra el pod.
    assert "rollout restart" not in _commands()
    assert "delete pod --selector app.kubernetes.io/name=veridicus-visor" in script
    assert "--for=condition=Ready pod" in script


def test_the_examples_come_from_a_config_map_mounted_where_the_viewer_reads_them() -> None:
    kustomization = yaml.safe_load((VISOR / "kustomization.yaml").read_text(encoding="utf-8"))
    generators = kustomization["configMapGenerator"]
    assert [item["name"] for item in generators] == [
        "veridicus-visor-ejemplos",
        "veridicus-visor-apariencia",
    ]
    assert generators[0] == {
        "name": "veridicus-visor-ejemplos",
        "namespace": "veridicus-visor",
        "files": ["ejemplos.json"],
    }
    spec = _one("Deployment", "veridicus-visor")["spec"]["template"]["spec"]
    [container] = spec["containers"]
    [mount] = [item for item in container["volumeMounts"] if item["name"] == "ejemplos"]
    assert mount["mountPath"] == "/app/deploy/demo-visor/ejemplos.json"
    assert mount["subPath"] == "ejemplos.json"
    assert mount["readOnly"] is True
    [volume] = [item for item in spec["volumes"] if item["name"] == "ejemplos"]
    assert volume["configMap"]["name"] == "veridicus-visor-ejemplos"
    viewer = (ROOT / "scripts" / "humano" / "visor-demo.py").read_text(encoding="utf-8")
    assert 'RAIZ / "deploy" / "demo-visor" / "ejemplos.json"' in viewer


ARGOCD = DEPLOY / "argocd" / "veridicus-visor.yaml"


def test_argo_cd_reconciles_the_viewer_from_main_of_this_repository() -> None:
    application = yaml.safe_load(ARGOCD.read_text(encoding="utf-8"))
    assert application["kind"] == "Application"
    assert application["metadata"] == {"name": "veridicus-visor", "namespace": "argocd"}
    source = application["spec"]["source"]
    assert source == {
        "repoURL": "https://github.com/freyesJaveriana/tai.git",
        "targetRevision": "main",
        "path": "deploy/demo-visor",
    }
    assert (ROOT / source["path"] / "kustomization.yaml").is_file()
    assert application["spec"]["syncPolicy"]["automated"] == {"prune": True, "selfHeal": True}
    assert application["spec"]["destination"]["server"] == "https://kubernetes.default.svc"


def test_argo_cd_never_manages_the_analysis_job() -> None:
    # El Job corre una vez por caso: reconciliarlo repetiría el análisis y gastaría saldo.
    application = yaml.safe_load(ARGOCD.read_text(encoding="utf-8"))
    assert "demo-analyzer" not in application["spec"]["source"]["path"]
    assert [item.name for item in (DEPLOY / "argocd").iterdir()] == ["veridicus-visor.yaml"]


def test_the_argo_cd_script_pins_a_version_tested_with_kubernetes_1_31() -> None:
    script = (ROOT / "scripts" / "humano" / "argocd-instalar.sh").read_text(encoding="utf-8")
    assert 'version="v3.2.12"' in script
    assert "argoproj/argo-cd/$version/manifests/install.yaml" in script
    assert "latest" not in script
    assert "apply --server-side --force-conflicts --namespace argocd" in script
    assert '"$raiz/deploy/argocd/veridicus-visor.yaml"' in script


def _commands() -> str:
    """El script sin sus líneas de comentario: las reglas miran solo lo que se ejecuta."""
    text = (ROOT / "scripts" / "humano" / "visor-pod.sh").read_text(encoding="utf-8")
    return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))


def test_the_script_writes_the_kubectl_version_into_the_dockerfile_without_build_args() -> None:
    # Con containerd, minikube image build rechaza --build-opt=build-arg y aun así sale con 0.
    script = _commands()
    dockerfile = (VISOR / "Dockerfile").read_text(encoding="utf-8")
    assert "--build-opt" not in script
    for name in ("KUBECTL_VERSION", "KUBECTL_ARCH"):
        assert f"s/^ARG {name}=.*/ARG {name}=" in script, name
        assert f"\nARG {name}=" in dockerfile, name
    assert '> "$contexto/Dockerfile"' in script


def test_the_script_stops_before_applying_when_the_image_is_missing() -> None:
    script = _commands()
    check = script.index('if ! minikube image ls | grep -q "veridicus-visor:demo"; then')
    assert script.index('minikube image rm "$imagen"') < script.index("minikube image build -t")
    assert script.index("minikube image build -t") < check
    assert check < script.index("apply -k")
    assert "exit 1" in script[check : script.index("apply -k")]
