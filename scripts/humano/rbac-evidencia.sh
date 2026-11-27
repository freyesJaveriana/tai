#!/usr/bin/env bash
# Lo ejecuta el humano (AUTONOMIA-01)
# Evidencia de mínimo privilegio para la diapositiva de seguridad: qué puede y qué no puede hacer cada
# cuenta de servicio de la demo, y el nivel de Pod Security de sus namespaces. Solo lee: kubectl auth
# can-i pregunta a la API y no cambia nada.
#
# Uso, en la VM de la demo: bash scripts/humano/rbac-evidencia.sh
set -euo pipefail

visor="system:serviceaccount:veridicus-visor:veridicus-visor"
job="system:serviceaccount:veridicus-demo:veridicus-analyzer-demo"
trap 'echo "La consulta de permisos no terminó: revise el último mensaje." >&2' ERR

puede() {
  # kubectl auth can-i termina con 1 cuando la respuesta es «no»: eso es un resultado, no un error.
  local respuesta
  respuesta="$(kubectl auth can-i "$@" 2> /dev/null || true)"
  printf '  %-4s kubectl auth can-i %s\n' "${respuesta:-no}" "$*"
}

echo "== Visor ($visor) en veridicus-demo, el único namespace donde trabaja"
kubectl auth can-i --list --as="$visor" --namespace veridicus-demo
echo
echo "== Lo que el visor NO puede hacer"
puede create deployments --as="$visor" --namespace veridicus-demo
puede create pods --as="$visor" --namespace veridicus-demo
puede create pods/exec --as="$visor" --namespace veridicus-demo
puede list secrets --as="$visor" --namespace veridicus-demo
puede get secrets/otro-secret --as="$visor" --namespace veridicus-demo
puede get pods --as="$visor" --namespace kube-system
puede delete namespaces --as="$visor"
puede create clusterrolebindings --as="$visor"
puede patch applications.argoproj.io --as="$visor" --namespace argocd
echo
echo "== Job del análisis ($job)"
kubectl auth can-i --list --as="$job" --namespace veridicus-demo
puede get pods --as="$job" --namespace veridicus-demo
echo "  automountServiceAccountToken: $(kubectl get serviceaccount veridicus-analyzer-demo --namespace veridicus-demo -o jsonpath='{.automountServiceAccountToken}')"
echo
echo "== Pod Security de los namespaces"
kubectl get namespaces veridicus-demo veridicus-visor --label-columns pod-security.kubernetes.io/enforce
