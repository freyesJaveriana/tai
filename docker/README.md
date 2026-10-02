# Contenedor `tai-aidlc`

Contenedor Ubuntu 24.04 aislado para recorrer **AI-DLC de AWS v2.10.0**
([awslabs/aidlc-workflows](https://github.com/awslabs/aidlc-workflows)) sobre este repositorio
sin tocar la configuración del host (`~/.claude`, `~/.gitconfig`, login de `gh`). El plan de
trabajo está en [`../plan-aidlc.md`](../plan-aidlc.md).

Incluye git, GitHub CLI (`gh`), Node 22, Claude Code (instalador nativo) y `aidlc` 2.10.0
(fijado en el `ARG AIDLC_VERSION` del Dockerfile). En cada arranque, `bootstrap.sh` aplica
`aidlc config --harness claude` sobre la copia del repo solo si cambió la versión. Esa
configuración conserva el proveedor de la sesión de Claude: no activa Bedrock.

## Uso (Windows)

```bat
docker\aidlc.bat              :: arranca y entra a Claude Code en /workspace
docker\aidlc.bat --continue   :: cualquier argumento extra se pasa a claude
docker\aidlc.bat --shell      :: bash dentro del contenedor
docker\aidlc.bat --stop       :: detiene el contenedor (conserva todo)
docker\aidlc.bat --rebuild    :: reconstruye la imagen y recrea el contenedor
docker\aidlc.bat --reset      :: borra contenedor + copia del repo (pide confirmación)
```

Primer arranque:

1. Pide nombre y email de git (o los toma de `docker/.env`, ver `.env.example`).
2. Ofrece `gh auth login` (necesario para hacer push) y clona el repo desde GitHub.
3. Dentro de Claude Code: `/login`, aprobar los hooks de AI-DLC, reiniciar Claude y correr
   `/aidlc --doctor`.

## Statusline

`statusline.sh` (instalado como `aidlc-statusline` y registrado en
`/workspace/.claude/settings.local.json`) muestra dos líneas:

```text
[AIDLC] <etapa / intent activo>
Opus 5.5  │  ctx [######----] 63% de 200k  │  5h 24% ↻12:37  │  7d 84% ↻Mon 21:57
```

- **ctx**: % de la ventana de contexto usada en esta sesión.
- **5h / 7d**: % consumido de los límites de la cuenta y la hora en que se reinician. Son los
  mismos para **todas** las sesiones de Claude Code con esa cuenta (host, workers, este
  contenedor). Se actualizan con cada respuesta de esta sesión y solo aparecen en planes
  Pro/Max, después del primer mensaje.
- Color: verde < 50 %, amarillo < 80 %, rojo ≥ 80 %.

## Qué persiste y dónde

| Qué | Dónde (host) | En el contenedor |
|---|---|---|
| Config de Claude (login, sesiones) | `docker/.state/claude/` | `$CLAUDE_CONFIG_DIR` |
| Login de GitHub CLI | `docker/.state/gh/` | `~/.config/gh` |
| gitconfig global (identidad, helper de gh) | `docker/.state/git/` | `~/.config/git` |
| Copia del repo (con `.claude/` y `aidlc/` de AI-DLC) | volumen Docker `tai-aidlc-workspace` | `/workspace` |

`docker/.state/` y `docker/.env` están en `.gitignore` porque contienen credenciales.
La copia del repo es independiente de la carpeta del host. El trabajo vuelve a esta carpeta
solo por `git push` (en el contenedor) y `git pull` (en el host).
