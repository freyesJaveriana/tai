# Configuración de GitHub (tarea previa P0.1)

Tarea conjunta del autor y el agente, previa a cualquier Bolt (`team.md`, Way of Working;
`bolt-plan.md`, P0.1). El agente prepara los archivos; **el humano revisa y ejecuta** la configuración con su
sesión de `gh` como administrador.

## Qué se decidió (2026-11-23)

- **Protección total, sin bypass.** `main` exige PR con *squash*, la comprobación `repo-level0`, historial
  lineal, y prohíbe *force-push* y borrado, **también para el administrador**. Como GitHub no puede proteger
  por rutas en un repositorio público personal y los *push* del agente usan la credencial del humano, la
  documentación (`docs/`, `specs/`) y los artefactos de AI-DLC (`aidlc/`) también entran por PR: el cierre de
  cada etapa va en una rama `aidlc/<etapa>` que el humano fusiona.
- **CI mínima desde hoy.** `repo-level0` corre en todo PR: `gitleaks` sobre todo el historial, `yamllint -s`
  de `.github/` y `scripts/check-no-cluster-apply.sh` (AUTONOMIA-01). Cada Bolt suma su propia comprobación
  obligatoria (`contracts-level0` con B1, `analyzer / gate` con B11, etc.).

## Archivos

| Archivo | Para qué |
|---|---|
| `.github/workflows/repo-level0.yml` | La comprobación obligatoria inicial |
| `.github/dependabot.yml` | Actualizaciones semanales de las acciones; cada Bolt suma su ecosistema |
| `.yamllint.yaml` | Reglas de `yamllint` del repositorio |
| `.gitleaks.toml` | Reglas por defecto de `gitleaks` y una sola excepción: las marcas `aidlc-wave-memory:<unidad>:<sha256>` de los diarios de AI-DLC, que la regla `generic-api-key` confundía con claves (38 falsos positivos en el primer análisis; revisar 2027-05-23) |
| `scripts/check-no-cluster-apply.sh` | Versión inicial de la guardia de AUTONOMIA-01; U2 la amplía en B4 |
| `scripts/github-p0-1.sh` | Aplica la configuración del repositorio (lo ejecuta el humano) |
| `docs/operacion/github/ruleset-main.json` | El *ruleset* `main-protegida` |

## Pasos

1. Fusionar el PR de P0.1 con `repo-level0` en verde.
2. El humano ejecuta `bash scripts/github-p0-1.sh freyesJaveriana/tai`.
3. **Validación 1, la CI bloquea:** un PR de prueba que añade `helm upgrade` a un archivo de `scripts/`.
   Esperado: `repo-level0` en rojo y el botón de fusión bloqueado. Se cierra sin fusionar.
4. **Validación 2, el *push* directo se rechaza:** un commit vacío en `main` y `git push`. Esperado: GitHub
   lo rechaza por el *ruleset*. Se descarta con `git reset --hard origin/main`.
5. Se adjuntan las dos salidas a este documento, en la sección siguiente.

## Pendiente fuera de P0.1

- **GHCR privado:** el paquete se crea al publicar la primera imagen (B3/B4); en ese momento se pone privado.
- **Deploy key de solo lectura:** la genera el humano para Argo CD en el módulo 8.
- **Comprobaciones obligatorias de cada componente:** se suman al *ruleset* con el Bolt que crea su *workflow*.
  Los nombres de *job* deben ser únicos en todo el repositorio, porque el *ruleset* los identifica solo por
  nombre de *job*.

## Evidencia

Configuración aplicada el 2026-11-23 con `bash scripts/github-p0-1.sh freyesJaveriana/tai`. Reglas
activas en `main`: `deletion`, `non_fast_forward`, `required_linear_history`, `pull_request`,
`required_status_checks`.

**Validación 1: la CI bloquea.** El PR #2 añadía `helm upgrade` en `scripts/validacion-p0-1.sh`.
`repo-level0` falló en el paso de AUTONOMIA-01:

```text
check-no-cluster-apply: AUTONOMIA-01 incumplida. Estas líneas aplican cambios a un clúster o envían trabajos a ZINE:
./scripts/validacion-p0-1.sh:3:helm upgrade veridicus deploy/veridicus
##[error]Process completed with exit code 1.
```

`gh pr view 2 --json mergeStateStatus` → `"BLOCKED"`. Se cerró sin fusionar y se borró la rama.

**Validación 2: el *push* directo se rechaza.** Un commit vacío en `main` y `git push`:

```text
remote: error: GH013: Repository rule violations found for refs/heads/main.
remote: - Changes must be made through a pull request.
remote: - Required status check "repo-level0" is expected.
 ! [remote rejected] main -> main (push declined due to repository rule violations)
```

El commit se descartó con `git reset origin/main`, sin tocar el árbol de trabajo.

**Falso positivo previo:** la primera corrida de `repo-level0` (PR #1) encontró 38 coincidencias de
`generic-api-key`. Todas eran marcas `aidlc-wave-memory` de los diarios de AI-DLC; se excluyeron en
`.gitleaks.toml`, y una clave de prueba se siguió detectando.
