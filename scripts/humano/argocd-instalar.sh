#!/usr/bin/env bash
# Lo ejecuta el humano (AUTONOMIA-01)
# Instala Argo CD en Minikube y registra la aplicación del visor (deploy/argocd/veridicus-visor.yaml),
# que desde entonces se reconcilia sola desde main.
#
# Uso: bash scripts/humano/argocd-instalar.sh
#
# Antes: el visor desplegado una vez con scripts/humano/visor-pod.sh (la imagen la construye ese script;
# Argo CD solo aplica los manifiestos). Requiere salida a internet para descargar Argo CD y leer GitHub.
# Se puede repetir: aplica lo mismo con --server-side.
set -euo pipefail

# 3.2 es la última versión de Argo CD probada con Kubernetes 1.31, el de la VM de la demo
# (docs/operator-manual/tested-kubernetes-versions.md de Argo CD).
version="v3.2.12"
raiz="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
trap 'echo "La instalación de Argo CD no terminó: revise el último mensaje." >&2' ERR

kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply --server-side -f -
# --server-side: los CRD de Argo CD superan el tamaño de la anotación del apply de cliente.
kubectl apply --server-side --force-conflicts --namespace argocd \
  -f "https://raw.githubusercontent.com/argoproj/argo-cd/$version/manifests/install.yaml"

kubectl rollout status deployment/argocd-server --namespace argocd --timeout=300s
kubectl rollout status deployment/argocd-repo-server --namespace argocd --timeout=300s
kubectl rollout status statefulset/argocd-application-controller --namespace argocd --timeout=300s

kubectl apply --server-side -f "$raiz/deploy/argocd/veridicus-visor.yaml"

echo "Argo CD $version listo y la aplicación veridicus-visor registrada."
echo "Estado: kubectl get applications --namespace argocd"
echo "Interfaz: kubectl port-forward service/argocd-server --namespace argocd 8080:443"
echo "  (desde otra máquina: ssh -L 8080:127.0.0.1:8080 <usuario>@<vm>, y https://127.0.0.1:8080)"
echo "Usuario admin; la contraseña inicial se lee con:"
echo "  kubectl get secret argocd-initial-admin-secret --namespace argocd -o jsonpath='{.data.password}' | base64 -d"
