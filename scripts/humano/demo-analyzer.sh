#!/usr/bin/env bash
# Lo ejecuta el humano (AUTONOMIA-01)
# Aplica la demo del analizador en Minikube, espera al Job, imprime sus resultados y comprueba que
# la NetworkPolicy cierra la red a cualquier otro pod del namespace.
#
# Uso: bash scripts/humano/demo-analyzer.sh
#
# Antes: crear los dos Secrets con crear-secret-anthropic.sh y crear-pull-secret-ghcr.sh.
# El script termina con el código de salida del Job (0 si el análisis salió bien) y termina con 1 si
# el pod de prueba, que no lleva la etiqueta del Job, SÍ llega a internet.
set -euo pipefail

namespace="veridicus-demo"
pod_sonda="veridicus-sonda-red"
# Sustituir por el digest de la imagen de curl que se elija:
#   docker buildx imagetools inspect curlimages/curl:<versión>
imagen_sonda="curlimages/curl@sha256:REEMPLAZAR_DIGEST_CURL"
raiz="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

case "$imagen_sonda" in
  *REEMPLAZAR_DIGEST_CURL*)
    echo "Falta fijar por digest la imagen de curl de la prueba de red (imagen_sonda en este script)." >&2
    exit 2
    ;;
esac

trap 'kubectl delete pod "$pod_sonda" --namespace "$namespace" --ignore-not-found > /dev/null 2>&1 || true' EXIT

for secreto in veridicus-anthropic veridicus-ghcr; do
  if ! kubectl get secret "$secreto" --namespace "$namespace" > /dev/null 2>&1; then
    echo "Falta el Secret $secreto en el namespace $namespace: cree los Secrets primero." >&2
    exit 2
  fi
done

# Un Job terminado no admite cambios en su plantilla: se borra el de la corrida anterior.
kubectl delete job veridicus-analyzer-demo --namespace "$namespace" --ignore-not-found
kubectl apply -k "$raiz/deploy/demo-analyzer"

# Espera a la primera de las dos condiciones: completo o fallido.
kubectl wait --for=condition=complete --timeout=900s --namespace "$namespace" job/veridicus-analyzer-demo > /dev/null 2>&1 &
pid_completo=$!
kubectl wait --for=condition=failed --timeout=900s --namespace "$namespace" job/veridicus-analyzer-demo > /dev/null 2>&1 &
pid_fallido=$!
wait -n || true
kill "$pid_completo" "$pid_fallido" > /dev/null 2>&1 || true

kubectl logs job/veridicus-analyzer-demo --namespace "$namespace" || true

codigo_job="$(kubectl get pods --namespace "$namespace" --selector job-name=veridicus-analyzer-demo -o jsonpath='{.items[0].status.containerStatuses[0].state.terminated.exitCode}' || true)"
if [ -z "$codigo_job" ]; then
  codigo_job=1
fi

# Prueba de red: un pod efímero del mismo namespace, sin la etiqueta del Job, intenta salir.
# curl termina con 6 (no resuelve), 7 (no conecta) o 28 (plazo) cuando la red está cerrada.
overrides='{"spec":{"securityContext":{"runAsNonRoot":true,"runAsUser":10001,"seccompProfile":{"type":"RuntimeDefault"}},"containers":[{"name":"veridicus-sonda-red","securityContext":{"allowPrivilegeEscalation":false,"readOnlyRootFilesystem":true,"capabilities":{"drop":["ALL"]}},"resources":{"requests":{"cpu":"50m","memory":"32Mi"},"limits":{"cpu":"100m","memory":"64Mi"}}}]}}'
codigo_red=0
kubectl run "$pod_sonda" --namespace "$namespace" --image="$imagen_sonda" --restart=Never --rm --stdin --quiet --override-type=strategic --overrides="$overrides" --command -- curl -sS --max-time 10 -o /dev/null https://example.com || codigo_red=$?

case "$codigo_red" in
  0)
    echo "La NetworkPolicy NO bloquea la salida: el pod de prueba SÍ llegó a https://example.com." >&2
    exit 1
    ;;
  6 | 7 | 28)
    echo "La red está cerrada para los pods sin la etiqueta del Job (curl terminó con $codigo_red)."
    ;;
  *)
    echo "La prueba de red no concluyó (código $codigo_red): revise el pod de prueba." >&2
    exit 1
    ;;
esac

exit "$codigo_job"
