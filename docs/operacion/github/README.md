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

_Pendiente: salidas de las validaciones 1 y 2._
