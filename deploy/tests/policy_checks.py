"""Comprobaciones estáticas de los manifiestos de la demo: reglas (a) a (d) y la `NetworkPolicy`.

Cada función recibe los recursos ya renderizados (lo que `kubectl apply -k` enviaría) y devuelve la
lista de infracciones; vacía quiere decir que cumple. Así una prueba puede alterar un recurso en
memoria y comprobar que la regla lo ve. No ejecuta kubectl ni kustomize: aplica a mano los tres
efectos de la kustomization que importan aquí (namespace, imágenes y generador de ConfigMap).
"""

import json
import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import yaml

Resource = dict[str, Any]

SECRET = "veridicus-anthropic"  # noqa: S105 (nombre del Secret, nunca su valor)
JOB_NAME = "veridicus-analyzer-demo"
APP_LABEL = "app.kubernetes.io/name"
JOB_SELECTOR = {"matchLabels": {APP_LABEL: JOB_NAME}}
DENY_ALL = "veridicus-deny-all"
JOB_POLICY = "veridicus-allow-analyzer-egress"
PRIVATE_RANGES = {"10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "169.254.0.0/16"}
DNS_PORTS = {("UDP", 53), ("TCP", 53)}


def load(path: Path) -> list[Resource]:
    """Documentos YAML de un archivo, sin los vacíos."""
    documents = yaml.safe_load_all(path.read_text(encoding="utf-8"))
    return [document for document in documents if document]


def render(directory: Path) -> list[Resource]:
    """Los recursos de `kustomization.yaml` con namespace, imágenes y ConfigMap ya aplicados."""
    kustomization = load(directory / "kustomization.yaml")[0]
    resources: list[Resource] = []
    for name in kustomization.get("resources", []):
        resources.extend(load(directory / name))
    for generator in kustomization.get("configMapGenerator", []):
        data = {
            Path(file).name: (directory / file).read_text(encoding="utf-8")
            for file in generator.get("files", [])
        }
        resources.append(
            {
                "apiVersion": "v1",
                "kind": "ConfigMap",
                "metadata": {"name": generator["name"]},
                "data": data,
            }
        )
    namespace = kustomization.get("namespace")
    if namespace:
        for resource in resources:
            if resource.get("kind") != "Namespace":
                resource.setdefault("metadata", {})["namespace"] = namespace
    images = {item["name"]: item for item in kustomization.get("images", [])}
    for resource in resources:
        for _, spec in pod_specs(resource):
            for container in containers(spec):
                replacement = images.get(str(container.get("image", "")))
                if replacement:
                    container["image"] = f"{replacement['newName']}:{replacement['newTag']}"
    return resources


def pod_specs(resource: Resource) -> list[tuple[str, dict[str, Any]]]:
    """Las especificaciones de pod que lleva un recurso (Pod o plantilla de un controlador)."""
    kind = str(resource.get("kind", ""))
    spec = resource.get("spec") or {}
    if kind == "Pod":
        found = spec
    elif kind in {"Deployment", "StatefulSet", "DaemonSet", "ReplicaSet", "Job"}:
        found = (spec.get("template") or {}).get("spec")
    elif kind == "CronJob":
        found = (((spec.get("jobTemplate") or {}).get("spec") or {}).get("template") or {}).get(
            "spec"
        )
    else:
        found = None
    return [(kind, found)] if isinstance(found, dict) else []


def containers(pod_spec: dict[str, Any]) -> Iterator[dict[str, Any]]:
    """Contenedores, de inicio y efímeros de un pod."""
    for key in ("containers", "initContainers", "ephemeralContainers"):
        yield from pod_spec.get(key) or []


def _where(resource: Resource, container: dict[str, Any]) -> str:
    kind = resource.get("kind")
    name = (resource.get("metadata") or {}).get("name")
    return f"{kind}/{name} contenedor {container.get('name')}"


def secret_violations(resources: list[Resource]) -> list[str]:
    """(a) Solo el Job `veridicus-analyzer-demo` referencia el Secret, y lo referencia."""
    found: list[str] = []
    referenced = False
    for resource in resources:
        kind = resource.get("kind")
        name = (resource.get("metadata") or {}).get("name")
        mentions = SECRET in json.dumps(resource)
        if kind == "Secret" and name == SECRET:
            found.append(f"el manifiesto incluye el propio Secret {SECRET}: lo crea el humano")
        elif mentions and not (kind == "Job" and name == JOB_NAME):
            found.append(f"{kind}/{name} referencia el Secret {SECRET}")
        elif mentions:
            referenced = True
    if not referenced:
        found.append(f"el Job {JOB_NAME} no referencia el Secret {SECRET}")
    return found


def _is_pinned(image: str) -> bool:
    if re.search(r"@sha256:[0-9a-f]{64}$", image):
        return True
    last = image.rsplit("/", 1)[-1]
    return ":" in last and not last.endswith(":")


def image_violations(resources: list[Resource]) -> list[str]:
    """(b) Ninguna imagen es `latest` ni va sin etiqueta o digest."""
    found: list[str] = []
    for resource in resources:
        for _, spec in pod_specs(resource):
            for container in containers(spec):
                image = str(container.get("image", ""))
                if not _is_pinned(image):
                    found.append(
                        f"{_where(resource, container)}: la imagen {image!r} no tiene etiqueta"
                    )
                elif re.search(r":latest(@|$)", image):
                    found.append(f"{_where(resource, container)}: la imagen {image!r} es latest")
    return found


def security_violations(resources: list[Resource]) -> list[str]:
    """(c) Todo pod cumple el `securityContext` restricted del paso 4."""
    found: list[str] = []
    for resource in resources:
        for kind, spec in pod_specs(resource):
            label = f"{kind}/{(resource.get('metadata') or {}).get('name')}"
            pod = spec.get("securityContext") or {}
            if pod.get("runAsNonRoot") is not True:
                found.append(f"{label}: falta runAsNonRoot: true")
            if pod.get("runAsUser") == 0:
                found.append(f"{label}: runAsUser es 0")
            if (pod.get("seccompProfile") or {}).get("type") != "RuntimeDefault":
                found.append(f"{label}: falta seccompProfile RuntimeDefault")
            for flag in ("hostNetwork", "hostPID", "hostIPC"):
                if spec.get(flag) is True:
                    found.append(f"{label}: {flag} activado")
            for container in containers(spec):
                context = container.get("securityContext") or {}
                where = _where(resource, container)
                if context.get("readOnlyRootFilesystem") is not True:
                    found.append(f"{where}: falta readOnlyRootFilesystem: true")
                if context.get("allowPrivilegeEscalation") is not False:
                    found.append(f"{where}: falta allowPrivilegeEscalation: false")
                if "ALL" not in ((context.get("capabilities") or {}).get("drop") or []):
                    found.append(f"{where}: falta capabilities.drop: [ALL]")
                if context.get("privileged") is True:
                    found.append(f"{where}: privileged activado")
    return found


def resources_violations(resources: list[Resource]) -> list[str]:
    """(d) Todo contenedor declara requests y limits de CPU y memoria."""
    found: list[str] = []
    for resource in resources:
        for _, spec in pod_specs(resource):
            for container in containers(spec):
                declared = container.get("resources") or {}
                for side in ("requests", "limits"):
                    for kind in ("cpu", "memory"):
                        if not (declared.get(side) or {}).get(kind):
                            found.append(f"{_where(resource, container)}: falta {side}.{kind}")
    return found


def _https_rule_violations(rule: dict[str, Any]) -> list[str]:
    found: list[str] = []
    ports = {(item.get("protocol", "TCP"), item.get("port")) for item in rule.get("ports") or []}
    if ports != {("TCP", 443)}:
        found.append(f"la regla de internet no es solo TCP 443: {sorted(map(str, ports))}")
    destinations = rule.get("to") or []
    if len(destinations) != 1 or set(destinations[0]) != {"ipBlock"}:
        found.append("la regla de internet no es un solo ipBlock")
        return found
    block = destinations[0]["ipBlock"]
    if block.get("cidr") != "0.0.0.0/0":
        found.append(f"el ipBlock de internet no es 0.0.0.0/0: {block.get('cidr')}")
    missing = PRIVATE_RANGES - set(block.get("except") or [])
    if missing:
        found.append(f"el ipBlock no excluye {sorted(missing)}")
    return found


def _dns_destination_ok(destination: dict[str, Any]) -> bool:
    if set(destination) != {"namespaceSelector", "podSelector"}:
        return False
    namespace = destination["namespaceSelector"].get("matchLabels") or {}
    pods = destination["podSelector"].get("matchLabels") or {}
    return namespace == {"kubernetes.io/metadata.name": "kube-system"} and pods == {
        "k8s-app": "kube-dns"
    }


def _dns_rule_violations(rule: dict[str, Any]) -> list[str]:
    found: list[str] = []
    ports = {(item.get("protocol", "TCP"), item.get("port")) for item in rule.get("ports") or []}
    if ports != DNS_PORTS:
        found.append(f"la regla de DNS no es solo UDP y TCP 53: {sorted(map(str, ports))}")
    destinations = rule.get("to") or []
    if not destinations or not all(_dns_destination_ok(item) for item in destinations):
        found.append("el DNS no va solo a los pods k8s-app=kube-dns de kube-system")
    return found


def _egress_rule_violations(rule: dict[str, Any]) -> list[str]:
    ports = {item.get("port") for item in rule.get("ports") or []}
    if ports == {53}:
        return _dns_rule_violations(rule)
    if 53 in ports:
        return ["la regla mezcla el puerto 53 con otros puertos"]
    return _https_rule_violations(rule)


def network_violations(resources: list[Resource]) -> list[str]:
    """`deny-all` existe y ninguna otra política da salida a un selector distinto del Job."""
    found: list[str] = []
    policies = [item for item in resources if item.get("kind") == "NetworkPolicy"]
    by_name = {(item.get("metadata") or {}).get("name"): item for item in policies}
    deny = by_name.get(DENY_ALL)
    if deny is None:
        found.append(f"falta la NetworkPolicy {DENY_ALL}")
    else:
        spec = deny.get("spec") or {}
        if spec.get("podSelector") != {}:
            found.append(f"{DENY_ALL} no selecciona todos los pods")
        if set(spec.get("policyTypes") or []) != {"Ingress", "Egress"}:
            found.append(f"{DENY_ALL} no cubre entrada y salida")
        if spec.get("ingress") or spec.get("egress"):
            found.append(f"{DENY_ALL} lleva reglas")
    if JOB_POLICY not in by_name:
        found.append(f"falta la NetworkPolicy {JOB_POLICY}")
    for name, policy in by_name.items():
        if name == DENY_ALL:
            continue
        spec = policy.get("spec") or {}
        gives_egress = "Egress" in (spec.get("policyTypes") or []) or "egress" in spec
        if gives_egress and spec.get("podSelector") != JOB_SELECTOR:
            found.append(f"{name} da salida a un selector distinto del Job")
        if spec.get("ingress"):
            found.append(f"{name} abre entrada")
        for rule in spec.get("egress") or []:
            found.extend(f"{name}: {item}" for item in _egress_rule_violations(rule))
    return found
