# Ronda 1 — U01-T32

`revisor` (`sonnet`), 2026-11-26.

VEREDICTO: VERDE

Los cinco criterios se corrieron en el worktree `/workspace/.worktrees/U01-T32`, en el commit `5dca6d8`. Todos pasan, y no hay hallazgos ROJO ni NARANJA.

## Criterios de aceptación

| # | Comando | Resultado |
|---|---|---|
| CA-1 | `timeout 300 uv run --frozen --offline --directory /workspace/.worktrees/U01-T32/contracts pytest tests/checks/test_error_codes.py --no-cov -q` | 27 passed, código 0 |
| CA-2 | `git -C /workspace/.worktrees/U01-T32 hash-object libs/errors/src/veridicus_errors/__init__.py libs/errors/tests/test_analyzer_errors.py` | `db7b327d…449fb8ae1` y `3702f5fd…ec619`, iguales a los esperados |
| CA-3 | `timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U01-T32/libs/errors pytest` | 14 passed, cobertura 100 % |
| CA-4 | `timeout 600 uv run --frozen --offline --directory /workspace/.worktrees/U01-T32/contracts pytest -q` | 2920 passed, 0 omitidas, cobertura 97,94 %, 30,73 s |
| CA-5 | `bash /workspace/.worktrees/U01-T32/scripts/check-no-datos-personales.sh /workspace/.worktrees/U01-T32` y `bash …/check-no-cluster-ids.sh /workspace/.worktrees/U01-T32` | `0 apariciones` en ambos |

- **Diferencias con `main`:** `git -C … diff --stat main...tarea/U01-T32` muestra 6 archivos, con 134 líneas añadidas y 1 cambiada.
- **Árbol de trabajo:** `git status --short` sale vacío; el worktree quedó limpio.
- **Nombres de las clases:** son `CancelledError`, `GatewayConfigError` y `CliInterruptedError`, según la decisión posterior del orquestador. La tarea todavía dice `Cancelled` y `CliInterrupted`; la bitácora lo explica en «Hallazgo y decisión del orquestador».

## Alcance y artefactos regenerados

No hay cambios fuera de alcance.

- **`contracts/errors/error-codes.v2.yaml`:**
  - `run.cancelled`, `config.invalid_gateway` y `system.interrupted` llevan `unit: U11` y `http: false`, sin `status` ni `c6`;
  - cada uno está en el bloque de su familia (`run.*`, `config.*`, `system.*`).
- **`libs/errors`:** cambian solo los dos archivos pedidos, idénticos a los de `tarea/U11-T01` según `git hash-object`.
- **Artefactos derivados que se regeneraron:**
  - `contracts/ts/generated/error-codes.ts`: tres líneas, una por `code`;
  - `contracts/security-surface.json`: solo el hash `integrity.error_codes`.

  Los dos los exige el README («Cómo cambiar un contrato», pasos 79 y 81), y V-SURFACE falla si no se regeneran. Entran como corresponde.
- **`docs/loop/bitacoras/U01-T32.md`:** bitácora de la tarea.

## Versionado y *changelog*

- `contracts/` no tiene `CHANGELOG.md`, y el README no pide uno.
- La versión del paquete sigue en `0.1.1`. Según el README, la etiqueta `contracts-v<versión>` la pone el humano al entregar, y esta tarea no obliga a subirla.
- La versión del catálogo sigue en `version: "2.0.0"`. El cambio es aditivo y sigue el mismo patrón con que entraron `config.invalid_*` y `run.publish_failed`.

## Hallazgos

- **AMARILLO · `/workspace/docs/loop/tareas/U01-T32-codes-del-analizador-en-el-catalogo.md:16-20`.** La tabla de la tarea todavía nombra `Cancelled` y `CliInterrupted`. Conviene corregirla, o dejar la nota en el PR, para que la evidencia sea coherente. No bloquea.
- **AMARILLO · `/workspace/.worktrees/U01-T32/docs/loop/bitacoras/U01-T32.md:26`.** CA-2 se verificó con `git hash-object` y no con `sha256sum`. La bitácora lo declara y lo atribuye al orquestador. El resultado es verificable y se reprodujo.

## Tareas candidatas

Ninguna.

VEREDICTO: VERDE
