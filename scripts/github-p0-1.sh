#!/usr/bin/env bash
# Tarea previa P0.1: configuración de GitHub. Lo ejecuta el humano, con su
# sesión de `gh` como administrador, después de revisar este archivo.
#
# Uso: bash scripts/github-p0-1.sh <dueño>/<repositorio>
#
# Qué hace (cada paso es idempotente):
#  1. Fusión solo por squash y borrado de la rama al fusionar.
#  2. Actions: permisos de lectura por defecto, sin aprobar PR, y solo
#     acciones de GitHub (las demás herramientas se descargan con SHA-256).
#  3. Alertas de Dependabot y actualizaciones de seguridad.
#  4. Escaneo de secretos con protección al hacer push.
#  5. Ruleset «main-protegida» sin bypass, ni siquiera para el administrador:
#     PR obligatorio con squash, comprobación repo-level0, historial lineal,
#     sin force-push ni borrado. Si ya existe, lo actualiza.
#
# Qué NO hace: GHCR privado (el paquete aún no existe; se fija al publicar la
# primera imagen) ni la deploy key de Argo CD (módulo 8). No toca ningún clúster.
set -euo pipefail

repo="${1:?Uso: bash scripts/github-p0-1.sh <dueño>/<repositorio>}"
dir="$(cd "$(dirname "$0")/.." && pwd)"
ruleset="$dir/docs/operacion/github/ruleset-main.json"

echo "1/5 Fusión solo por squash"
gh api -X PATCH "repos/$repo" \
  -F allow_squash_merge=true -F allow_merge_commit=false -F allow_rebase_merge=false \
  -F delete_branch_on_merge=true >/dev/null

echo "2/5 Permisos de Actions"
gh api -X PUT "repos/$repo/actions/permissions" \
  -F enabled=true -f allowed_actions=selected >/dev/null
gh api -X PUT "repos/$repo/actions/permissions/selected-actions" \
  -F github_owned_allowed=true -F verified_allowed=false >/dev/null
gh api -X PUT "repos/$repo/actions/permissions/workflow" \
  -f default_workflow_permissions=read -F can_approve_pull_request_reviews=false >/dev/null

echo "3/5 Dependabot"
gh api -X PUT "repos/$repo/vulnerability-alerts" >/dev/null
gh api -X PUT "repos/$repo/automated-security-fixes" >/dev/null

echo "4/5 Escaneo de secretos con protección en push"
gh api -X PATCH "repos/$repo" --input - >/dev/null <<'JSON'
{"security_and_analysis": {
  "secret_scanning": {"status": "enabled"},
  "secret_scanning_push_protection": {"status": "enabled"}
}}
JSON

echo "5/5 Ruleset main-protegida"
id="$(gh api "repos/$repo/rulesets" --jq '.[] | select(.name == "main-protegida") | .id')"
if [ -n "$id" ]; then
  gh api -X PUT "repos/$repo/rulesets/$id" --input "$ruleset" >/dev/null
else
  gh api -X POST "repos/$repo/rulesets" --input "$ruleset" >/dev/null
fi

echo "Listo. Comprobación:"
gh api "repos/$repo/rules/branches/main" --jq '.[].type'
