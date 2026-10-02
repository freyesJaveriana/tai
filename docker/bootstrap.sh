#!/usr/bin/env bash
# Preparación idempotente del contenedor tai-aidlc. aidlc.bat la ejecuta (como
# 'developer', con TTY) en cada arranque, antes de abrir Claude Code. Solo hace
# trabajo la primera vez; después cada paso detecta que ya está hecho y lo salta.
set -uo pipefail

WS=/workspace
REPO_URL="${REPO_URL:-https://github.com/freyesJaveriana/tai.git}"
REPO_BRANCH="${REPO_BRANCH:-main}"

say() { printf '\033[1;36m[tai-aidlc]\033[0m %s\n' "$*"; }

# --- 0. Dueños: los bind mounts de Windows y el volumen pueden llegar como root ---
for d in "$WS" "$CLAUDE_CONFIG_DIR" "$HOME/.config/gh" "$HOME/.config/git"; do
    [ -O "$d" ] || sudo chown -R "$(id -u):$(id -g)" "$d"
done
touch "$GIT_CONFIG_GLOBAL"

# --- 1. Identidad de git (persistida en .state/git) ---
if [ -z "$(git config --global user.name)" ]; then
    name="${GIT_USER_NAME:-}"
    [ -n "$name" ] || read -rp "Nombre para los commits de git: " name
    git config --global user.name "$name"
fi
if [ -z "$(git config --global user.email)" ]; then
    email="${GIT_USER_EMAIL:-}"
    [ -n "$email" ] || read -rp "Email para los commits de git: " email
    git config --global user.email "$email"
fi
git config --global init.defaultBranch main
git config --global pull.rebase false
git config --global core.autocrlf input

# --- 2. GitHub: login de gh (persistido en .state/gh) y git usando su token ---
if ! gh auth status -h github.com >/dev/null 2>&1; then
    say "GitHub CLI no tiene sesión. Sin ella se puede clonar (repo público) pero no hacer push."
    read -rp "¿Iniciar sesión en GitHub ahora? [S/n]: " ans
    case "$ans" in
        [nN]*) say "Omitido. Luego puedes correr:  gh auth login && gh auth setup-git" ;;
        *) gh auth login -h github.com -p https -w ;;
    esac
fi
if gh auth status -h github.com >/dev/null 2>&1; then
    git config --global --get-all credential.https://github.com.helper 2>/dev/null | grep -q gh \
        || gh auth setup-git -h github.com
fi

# --- 3. Copia del repositorio (volumen tai-aidlc-workspace) ---
if [ ! -d "$WS/.git" ]; then
    say "Clonando $REPO_URL ($REPO_BRANCH) en $WS ..."
    if [ -n "$(ls -A "$WS" 2>/dev/null)" ]; then
        say "ERROR: $WS no está vacío y no es un repo git. Revísalo con:  aidlc.bat --shell"
        exit 1
    fi
    git clone --branch "$REPO_BRANCH" "$REPO_URL" "$WS" || { say "ERROR: falló el clone."; exit 1; }
fi

# --- 4. Limpieza: plugin AI-DLC de Bushido (ai-dlc.dev) de una versión anterior ---
if claude plugin list 2>/dev/null | grep -q 'ai-dlc@ai-dlc'; then
    say "Desinstalando el plugin ai-dlc de Bushido (reemplazado por AI-DLC de AWS) ..."
    claude plugin uninstall ai-dlc@ai-dlc >/dev/null 2>&1
    claude plugin marketplace remove ai-dlc >/dev/null 2>&1
fi

# --- 5. AI-DLC de AWS en el proyecto (.claude/, aidlc/, bloque en .gitignore) ---
# Se re-aplica solo si cambió la versión del binario (marcador dentro de .git/,
# que no se versiona). 'config' conserva el proveedor actual: no activa Bedrock.
cd "$WS" || exit 1
marker="$WS/.git/aidlc-configured-version"
current=$(aidlc --version 2>/dev/null)
if [ "$(cat "$marker" 2>/dev/null)" != "$current" ] || [ ! -f "$WS/.claude/settings.json" ]; then
    say "Configurando AI-DLC ($current) para Claude Code en $WS ..."
    if aidlc config --harness claude --yes; then
        printf '%s\n' "$current" > "$marker"
    else
        say "AVISO: 'aidlc config' falló. Revísalo con:  aidlc.bat --shell  y  aidlc doctor"
    fi
fi

# --- 6. Statusline (AI-DLC + contexto + cuotas 5h/7d) en settings.local.json ---
# settings.local.json gana sobre .claude/settings.json (que reescribe 'aidlc
# config') y está en el .gitignore que genera AI-DLC.
local_settings="$WS/.claude/settings.local.json"
[ -s "$local_settings" ] || echo '{}' > "$local_settings"
if [ "$(jq -r '.statusLine.command // empty' "$local_settings")" != "aidlc-statusline" ]; then
    tmp=$(mktemp)
    jq '.statusLine = {"type": "command", "command": "aidlc-statusline", "padding": 0}' \
        "$local_settings" > "$tmp" && mv "$tmp" "$local_settings"
fi

exit 0
