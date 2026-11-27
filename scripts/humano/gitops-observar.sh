#!/usr/bin/env bash
# Lo ejecuta el humano (AUTONOMIA-01)
# Muestra el bucle GitOps cerrándose después de fusionar un PR: espera a que Argo CD tenga en el clúster
# el mismo commit que main en GitHub, a que el pod nuevo del visor esté listo, y comprueba que la página
# del visor ya sirve la barra superior con el color del ConfigMap.
#
# Uso, en la VM de la demo: bash scripts/humano/gitops-observar.sh
#
# Lo único que escribe en el clúster es la anotación de refresco de la Application (como el botón
# «Refresh» de Argo CD), para no esperar los 3 minutos del sondeo. No aplica ningún manifiesto.
set -euo pipefail

raiz="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
app="veridicus-visor"
ns_argo="argocd"
ns="veridicus-visor"
plazo_s=300
trap 'echo "La observación no terminó: revise el último mensaje." >&2' ERR

esperado="$(git -C "$raiz" ls-remote origin refs/heads/main | cut -f1)"
if [ -z "$esperado" ]; then
  echo "No se pudo leer main en GitHub (git ls-remote origin)." >&2
  exit 2
fi
echo "main en GitHub: ${esperado:0:7}"

kubectl annotate application "$app" --namespace "$ns_argo" argocd.argoproj.io/refresh=normal --overwrite > /dev/null
limite=$((SECONDS + plazo_s))
while true; do
  revision="$(kubectl get application "$app" --namespace "$ns_argo" -o jsonpath='{.status.sync.revision}')"
  sincronia="$(kubectl get application "$app" --namespace "$ns_argo" -o jsonpath='{.status.sync.status}')"
  salud="$(kubectl get application "$app" --namespace "$ns_argo" -o jsonpath='{.status.health.status}')"
  printf '\rArgo CD: revisión %s · %s · %s   ' "${revision:0:7}" "$sincronia" "$salud"
  if [ "$revision" = "$esperado" ] && [ "$sincronia" = "Synced" ] && [ "$salud" = "Healthy" ]; then
    break
  fi
  if [ "$SECONDS" -ge "$limite" ]; then
    echo
    echo "Argo CD no llegó a ${esperado:0:7} en $plazo_s s: revise la Application en la interfaz de Argo CD." >&2
    exit 1
  fi
  sleep 5
done
echo

kubectl rollout status deployment/veridicus-visor --namespace "$ns" --timeout=180s
configmap="$(kubectl get deployment veridicus-visor --namespace "$ns" -o jsonpath='{.spec.template.spec.containers[0].envFrom[0].configMapRef.name}')"
color="$(kubectl get configmap "$configmap" --namespace "$ns" -o jsonpath='{.data.VERIDICUS_VISOR_COLOR_BANDA}')"
echo "ConfigMap en uso: $configmap (VERIDICUS_VISOR_COLOR_BANDA=$color)"
kubectl get pods --namespace "$ns" --selector app.kubernetes.io/name=veridicus-visor

pagina="$(curl -sS --max-time 10 "http://$(minikube ip):30851/")"
if [[ "$pagina" == *".banda{background:$color;"* ]]; then
  echo "El visor ya sirve la barra superior en $color. Recargue el navegador para verla."
else
  echo "El visor todavía no sirve el color $color: espere unos segundos y repita el script." >&2
  exit 1
fi
