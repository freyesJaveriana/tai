#!/usr/bin/env bash
# Statusline de Claude Code para el contenedor tai-aidlc. Dos líneas:
#   1) la statusline propia de AI-DLC (fase/etapa/intent), tal como la registra
#      'aidlc config' en /workspace/.claude/settings.json;
#   2) modelo · contexto usado (barra) · cuota 5h y 7d de la cuenta, con su reinicio.
# Se registra en .claude/settings.local.json (gana sobre settings.json del
# proyecto) desde bootstrap.sh. Claude Code entrega el JSON de la sesión por stdin.
input=$(cat)

R=$'\033[0m'; DIM=$'\033[2m'; CYAN=$'\033[36m'
GREEN=$'\033[32m'; YELLOW=$'\033[33m'; RED=$'\033[31m'

color_for() {  # % usado -> verde < 50 <= amarillo < 80 <= rojo
    if   [ "$1" -ge 80 ]; then printf '%s' "$RED"
    elif [ "$1" -ge 50 ]; then printf '%s' "$YELLOW"
    else printf '%s' "$GREEN"; fi
}

# --- Línea 1: AI-DLC ------------------------------------------------------------
proj=$(jq -r '.workspace.project_dir // .workspace.current_dir // .cwd // empty' <<<"$input")
[ -n "$proj" ] || proj=/workspace
aidlc_cmd=$(jq -r '.statusLine.command // empty' "$proj/.claude/settings.json" 2>/dev/null)
line1=""
if [ -n "$aidlc_cmd" ]; then
    line1=$(cd "$proj" && CLAUDE_PROJECT_DIR="$proj" timeout 5 bash -c "$aidlc_cmd" <<<"$input" 2>/dev/null)
fi

# --- Línea 2: contexto y cuotas --------------------------------------------------
IFS=$'\t' read -r model ctx_pct ctx_size five five_rst week week_rst < <(jq -r '[
    (.model.display_name // .model.id // "?"),
    (.context_window.used_percentage // "" | tostring),
    (.context_window.context_window_size // "" | tostring),
    (.rate_limits.five_hour.used_percentage // "" | tostring),
    (.rate_limits.five_hour.resets_at // "" | tostring),
    (.rate_limits.seven_day.used_percentage // "" | tostring),
    (.rate_limits.seven_day.resets_at // "" | tostring)
] | @tsv' <<<"$input" 2>/dev/null)

parts=("${CYAN}${model}${R}")

if [ -n "$ctx_pct" ]; then
    p=${ctx_pct%.*}
    filled=$(( p / 10 )); [ "$filled" -gt 10 ] && filled=10
    bar=$(printf '%*s' "$filled" '' | tr ' ' '#')$(printf '%*s' $(( 10 - filled )) '' | tr ' ' '-')
    size=""
    [ -n "$ctx_size" ] && size=" de $(( ctx_size / 1000 ))k"
    parts+=("ctx $(color_for "$p")[${bar}] ${p}%${R}${DIM}${size}${R}")
else
    parts+=("${DIM}ctx --${R}")
fi

quota() {  # etiqueta, % usado, epoch de reinicio, formato de fecha
    local label=$1 pct=$2 rst=$3 fmt=$4 p when=""
    if [ -z "$pct" ]; then
        printf '%s' "${DIM}${label} --${R}"; return
    fi
    p=$(printf '%.0f' "$pct")
    [ -n "$rst" ] && when=" ${DIM}↻$(date -d "@${rst}" +"$fmt" 2>/dev/null)${R}"
    printf '%s' "${label} $(color_for "$p")${p}%${R}${when}"
}
parts+=("$(quota 5h "$five" "$five_rst" '%H:%M')")
parts+=("$(quota 7d "$week" "$week_rst" '%a %H:%M')")

line2=""
for s in "${parts[@]}"; do line2="${line2}${line2:+  ${DIM}│${R}  }${s}"; done

[ -n "$line1" ] && printf '%s\n' "$line1"
printf '%s\n' "$line2"
