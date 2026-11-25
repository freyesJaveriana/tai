# Ronda 1 — U01-T15b

VEREDICTO: VERDE

Corrí yo mismo los seis criterios en `/workspace/.worktrees/U01-T15b` (rama `tarea/U01-T15b` en 94c075f) y todos pasan. Las seis correcciones hacen lo que dicen E-11 a E-15, sin quitar ni añadir nada. Ninguna cifra existente de C25 cambió. Quedan dos AMARILLO, que no bloquean. Al terminar, el worktree sigue limpio (`git status --porcelain` no devuelve nada).

## Criterios de aceptación, verificados por mí
| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| 1 | Lecturas de vuelta | `timeout 120 uv run --frozen --offline --directory /workspace/.worktrees/U01-T15b/contracts pytest tests/contracts/test_correcciones_t15b.py --no-cov` | pasa: 12 passed in 1.38s (6 positivos y 6 controles negativos) |
| 2 | Suite completa | `timeout 600 uv run --frozen --offline --directory /workspace/.worktrees/U01-T15b/contracts pytest tests --no-cov -q -rs` | pasa: 1995 passed, 0 omitidos, 1 warning ya conocido (`test_socket_bloqueado`). Antes había 1982; las 13 nuevas son 12 + 1 de `runs` |
| 3 | Catálogo C25 | `... pytest tests/test_limits.py tests/checks/test_limits_catalog.py --no-cov -q` y `git -C ... diff feat/b1-contratos...HEAD -- contracts/limits.v1.yaml` | pasa: 162 passed. El diff añade solo las 3 entradas y `C5` en dos `used_in`; ningún `value` cambió |
| 4 | Archivos permitidos | `git -C /workspace/.worktrees/U01-T15b diff --name-only feat/b1-contratos...HEAD` | pasa: los 11 archivos están en la lista; no se tocaron `test_limits.py`, `pyproject.toml`, `uv.lock` ni `registry.py` |
| 5 | Instalación y rueda | `... pytest tests/test_package_map.py --no-cov -q` | pasa: 8 passed |
| 6 | Tipos, lint y CI | `uv run ... mypy --strict src` / `uv run ... ruff check .` / `bash /workspace/.worktrees/U01-T15b/scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T15b` | pasa: `Success: no issues found in 18 source files`, `All checks passed!`, `0 apariciones` |

## Comprobaciones pedidas
- **E-11 y E-14 (C25).** Las tres entradas nuevas tienen exactamente las cifras de la tarea y cada una está en el bloque de su dueño (U4 o U1). `runs` entró en `UNIDADES` con su caso de prueba (P-T15b-1).
- **E-15 (`used_in`).** `C5` se añadió solo en `turn_max_chars` y en `report_token_max_chars`. No cambió ningún otro `used_in`.
- **E-14 (C1).** `POST /sessions` lleva ya la marca de bytes, el patrón en `profile_name` y su `413`. Revisé las 10 operaciones con `x-veridicus-max-bytes` y todas declaran `413`, así que añadirlo aquí era lo que pedía la tarea.
- **E-12 (estados de C1).**
  - `POST /acknowledgements`: la `409` se retiró y `ethics.text_version_outdated` pasó a la `422`.
  - `PATCH /users/{user_id}`: `validation.invalid_request` ya estaba en la `422`. El único cambio es que la descripción de la `409` ya no lo nombra; eso cierra lo que anota P-T15-4.
  - La `409` de `PATCH /users/{user_id}` cita solo `user.has_pending_sessions`, `user.self_deactivation` y `user.last_admin`. Los tres dan 409 en `error-codes.v2.yaml` (líneas 18 a 20). El catálogo no cambió.
- **E-15 (C5 y C19).** `text` lleva 20000 con `turn_max_chars`. `model_digest` y `/$defs/token` llevan `report_token_max_chars`. `role` lleva `model_call_role_max_chars`. Los dos `per_run` llevan `report_per_run_items` y conservan `minItems: 3` y `maxItems: 3`.
- **Ediciones de pruebas existentes.**
  - `test_console.py`: solo cambian dos filas de `ESTADOS`. A `("post","/sessions")` se le suma `413` (E-14) y en `("post","/acknowledgements")` el `409` pasa a `422` (E-12).
  - `test_report_closed.py`: solo cambian la aserción y la docstring de la prueba que autoriza P-T15b-2. El nombre y el resto de la prueba quedan iguales.
  - Las dos ediciones están nombradas en la bitácora.
- **Rojo primero.** El commit d2d7518 contiene solo las pruebas y la bitácora. Entre d2d7518 y HEAD los dos archivos de prueba no cambiaron (`git diff --stat d2d7518 HEAD`), así que la salida en rojo que está en la bitácora (12 failed) corresponde a los archivos finales. Los dos controles negativos que pasaron en rojo pasan sin comprobar nada mientras la marca no existe, y eso no invalida el rojo.
- **Edit y Write.** Revisé la transcripción del codificador (`/home/developer/.claude-config/projects/-workspace/87e67c60-aa1c-4b11-8928-da89d2e300bd/subagents/agent-ace08eb5c82cbf92e.jsonl`). Todos los cambios a contratos, a `limits_catalog.py` y a las pruebas se hicieron con Edit o Write. Solo la bitácora se escribió con heredoc (ver F-01).
- **Advertencia de `limits_match`.** La leí en 55455f6. `PALABRAS = (("maxItems", "turns"),)` exige la unidad `turns` para todo `maxItems`. T15b no empeora la situación: antes, `per_run` habría fallado por «maxItems sin x-veridicus-limit»; ahora fallará por la unidad (`runs` en vez de `turns`). Sí deja seguro el choque cuando T15 se rebase (ver F-02).

## Hallazgos
### F-01 · AMARILLO · docs/loop/bitacoras/U01-T15b.md · La bitácora se creó con `cat >` y no con `cat >>`
La tarea solo permite el heredoc `cat >> RUTA <<'FIN'`. La primera escritura de la bitácora usó `cat > .../U01-T15b.md <<'FIN'`. El archivo no existía antes, así que no se perdió nada, y los dos anexos siguientes sí usaron `>>`. No afecta al código ni a las pruebas. Hay además una inexactitud menor: la bitácora dice «tres controles negativos» y enumera cuatro contratos.

### F-02 · AMARILLO · contracts/limits.v1.yaml (report_per_run_items) · Choque previsible con la guardia `limits_match` de T15
`report_per_run_items` tiene la unidad `runs` (P-T15b-1) y marca un `maxItems`. La guardia de T15 (55455f6, `PALABRAS`) solo acepta `turns` con `maxItems`, así que al rebasar T15 dará «la unidad de report_per_run_items debe ser turns con maxItems (§4.4 c)». No es un defecto de T15b, que hizo lo que dice P-T15b-1, y tampoco empeora el resultado. Lo anoto para que la ronda 2 de T15 acepte `runs` junto a `turns` para `maxItems`; esa misma ampliación evitaría el choque futuro con la unidad runs.

## Tareas candidatas (defectos reales fuera de alcance)
- Ninguna nueva. La lista de objetos abiertos de C21 (E-13) y la ampliación de `PALABRAS` en `limits_match` (F-02) ya corresponden a T15.

```
VEREDICTO: VERDE
AMARILLO|docs/loop/bitacoras/U01-T15b.md|La bitácora se creó con cat > y no con cat >>
AMARILLO|contracts/limits.v1.yaml (report_per_run_items)|Choque previsible de la unidad runs con limits_match de T15 al rebasar
INFORME: docs/loop/revisiones/U01-T15b/ronda-1.md
```
