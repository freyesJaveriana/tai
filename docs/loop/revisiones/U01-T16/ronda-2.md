# Ronda 2 — U01-T16

VEREDICTO: NO-VERDE

La evidencia ya está bien. Los cinco criterios pasan en mi corrida y los dos rojos salen iguales a los de la bitácora. También están bien F-04, la prueba de los enums de C6 y el alcance. Quedan dos defectos en los tipos auxiliares de C11, y los dos chocan con contract-summary. Primero, `SuggestionWithDecision` cambió `decided_by`/`decided_at` por `actor_user_id`/`at`. Eso contradice C7 v2 y la entidad `EffectiveState` de U5, y una prueba nueva fija el nombre equivocado. Segundo, se quitó la hora de terminación, que la revisión 4 de C11 pide de forma explícita.

## Criterios de aceptación, verificados por mí

| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| 1 | CA-1 | `timeout 120 uv run --frozen --offline --directory /workspace/.worktrees/U01-T16/contracts pytest tests/typing/test_protocols.py --no-cov -v -p no:cacheprovider` | pasa: `26 passed in 0.99s` |
| 2a | CA-2, tipos | `uv run --frozen --offline --directory /workspace/.worktrees/U01-T16/contracts mypy --strict src` | pasa: `Success: no issues found in 30 source files` |
| 2b | CA-2, lint | `uv run --frozen --offline --directory /workspace/.worktrees/U01-T16/contracts ruff check .` | pasa: `All checks passed!` |
| 3 | CA-3 | `timeout 300 uv run --frozen --offline --directory /workspace/.worktrees/U01-T16/contracts pytest tests --no-cov -q -p no:cacheprovider` | pasa: `2149 passed, 1 warning in 104.93s` |
| 4 | CA-4 | `timeout 120 uv run --frozen --offline --directory /workspace/.worktrees/U01-T16/contracts pytest tests/test_package_map.py --no-cov -q -p no:cacheprovider` | pasa: `8 passed in 3.13s` |
| 5 | CA-5 | `bash /workspace/.worktrees/U01-T16/scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T16` | pasa: `0 apariciones` |
| RA | Rojo A | `git archive` de f8d9b84 más `test_protocols.py` de d856f2c, en `&lt;scratchpad&gt;/r2/rojoA`. Luego `timeout 300 uv run --frozen --offline --directory &lt;scratchpad&gt;/r2/rojoA/contracts pytest tests/typing/test_protocols.py --no-cov --tb=line -rf -q -p no:cacheprovider` | falla por la regla: `8 failed, 18 passed`. Son los mismos 8 nombres de la bitácora. mypy da `has no attribute "SessionStatus"` y `missing ... protocol members: decided_at, decided_by` |
| RB | Rojo B | `git archive` de la base 57be9d4 más la prueba de d856f2c, en `&lt;scratchpad&gt;/r2/rojoB`, con el mismo comando y `--tb=no` | falla por módulo ausente: `26 failed in 0.29s`, la misma lista de la bitácora |

- **SHA citados.** 0bb7613, f8d9b84, cbab6a3, d856f2c, 20d7ce9 y 7d270e8 están en `git log feat/b1-contratos..HEAD`. El merge-base es 57be9d4. `git diff 20d7ce9 7d270e8` solo toca `docs/loop/`, y `git diff d856f2c HEAD -- contracts` solo toca `report_ports.py`. La prueba no cambió después del rojo.
- **Hash de la tarea.** Coincide: `b080580f…`. El worktree queda limpio al terminar.
- **Alcance.** El diff trae 7 `.py` nuevos bajo `src/`, `tests/typing/test_protocols.py` y dos archivos de la bitácora. No toca nada de la lista «Fuera»: ni YAML/JSON, ni `pyproject.toml`, `uv.lock`, `hatch_build.py`, `conftest.py`, `helpers.py`, `registry.py` ni `model_calls.py`.

**F-01 (ronda 1): cerrado.**
- Las salidas del verde salen de 20d7ce9 con el árbol limpio, y mis cifras coinciden (26, 30 archivos, 8 y 2149).
- Los rojos son literales y completos. La única omisión es la de las líneas `Building`/`Installed` de `uv` en el rojo B, y está declarada fuera del bloque.

**F-04 (ronda 1): cerrado para los 7 controles de firma.** `_notas_de_conflicto` exige el miembro en las líneas `note:`. Los 7 controles nuevos de tipos auxiliares buscan el miembro en toda la salida (ver F-03).

**Enums de C6 (punto 4): correcto.** La prueba lee de verdad `analyzer/v1/salida.schema.json` con `load_contract`. Compara valor por valor y también la cardinalidad. Además comprueba que `Hallazgo.tipo` y `Cita.avisos` usan esos `Literal`.

**P-T16-8 (punto 2), campos que sí están bien.**
- `SessionSnapshot`: `status`, `origin`, `profile_name`, `config_sha256`, `blocked_code`, `finalized_at` y `owner_user_id` coinciden con `text-flow/.../entities.md:100-114`.
- `TurnView`: `n`, `speaker`, `page` y `fold_state` coinciden con `:171-176`.
- `RunView`: `mode`, `from_turn` y `to_turn` vienen de `:194-196`; `attempt` y `status` vigentes, de `:207-222`; `fragmented`, de `:237`; `covered_by_final`, de BR17.2 (`rules.md:698, 774`).
- `ModelCallView` es nuevo y tiene fuente: sus campos son los de la entidad `ModelCall` (`:258-270`) y corresponden al «registro de modelos» de la docstring de C11.
- `RoundView` coincide con `human-review/.../entities.md:66-71`.
- `same_family_declared` viene de C18 (`contract-summary.md:2303`).
- `consent_withdrawn_at` viene de contract-summary (`:1872`, C1 `:494`).
- Los 11 `Literal` coinciden con los `allowed`.

## Hallazgos

### F-01 · NARANJA · `report_ports.py:232-240` y `test_protocols.py:442-458` · `SuggestionWithDecision` renombra `decided_by`/`decided_at` en contra de C7 v2 y de `EffectiveState`

`decisions` devuelve el «estado vigente de cada sugerencia con su propia nota» (FD-U5-05). Esa es justo la entidad calculada `EffectiveState`, que en `human-review/functional-design/entities.md:122-129` lleva `state`, `note`, `reformulation`, `decided_by` y `decided_at`. C7 v2, que es la forma en la red de esta misma vista, usa también `decided_by`/`decided_at` (`contract-summary.md:1704-1709` y `contracts/integrity/review-suggestion.v2.json:89-126`).

El codificador tomó `actor_user_id` y `at` de `ReviewDecision`, que es la fila guardada y no la vista. Con eso, el mismo término queda traducido de dos formas entre C11 y C7, que es lo que P-T16-8 y el glosario de `team.md` prohíben. El rojo A lo confirma: la implementación de la ronda 1 tenía los nombres correctos (`missing ... protocol members: decided_at, decided_by`).

El control `SuggestionWithDecision_actor_user_id_se_llama_decided_by` deja fijado el error: rechaza el nombre aprobado. Hay que volver a `decided_by`/`decided_at`, invertir el control y repetir su rojo.

### F-02 · NARANJA · `report_ports.py:141-187, 255-256` · falta la hora de terminación que pide la revisión 4 de C11

`contract-summary.md:1872-1874` dice que `SessionSnapshot` declara la «terminación y retirada con su hora» (FD-U7-03). U7 la usa para el reporte: `forensic-report/functional-design/rules.md:161, 557` («SI la sesión está terminated ENTONCES la terminación con su hora»).

El codificador quitó `terminated_at` porque ninguna entidad lo nombra en la sesión. Pero aplicó la regla de forma desigual: `consent_withdrawn_at` tampoco es un nombre de entidad (la entidad dice `ConsentRecord.withdrawn_at`) y sí se quedó, porque contract-summary lo nombra. Además, la hora existe: es `SessionStatusChange.at` con `to_status: terminated` (`entities.md:155-161`). Por último, la docstring de `snapshot` se contradice: dice «declara terminación … con su hora» y dos líneas después dice «sin hora».

Mientras falte el campo, U7 no puede cumplir BR11.3 con este puerto. Lo resuelve una precisión del orquestador: `terminated_at: datetime | None`, derivado de `SessionStatusChange`, igual que `consent_withdrawn_at`.

### F-03 · AMARILLO · `test_protocols.py:487` · los controles de los tipos auxiliares buscan el miembro en toda la salida

`re.search(rf"\b{miembro}\b", salida)` revisa toda la salida de mypy, no solo las líneas `note:`, como sí hace `_notas_de_conflicto` en los controles de firma. Hoy no da falsos positivos, porque cada control cambia un solo campo. Basta usar la misma función.

### F-04 · AMARILLO · `test_protocols.py:460` · falta una línea en blanco

Hay una sola línea en blanco antes de `@pytest.mark.parametrize` (PEP 8 pide dos). Ruff no lo marca con su configuración actual. Es cosmético.

## Tareas candidatas (defectos reales fuera de alcance)

- **Hora del incidente.** U7 BR11.3 (`rules.md:557`) pide «el incidente de anonimización con su code y hora». La instantánea solo trae `blocked_code`, y contract-summary no pide esa hora. Es un defecto real, entre U4 y U7.
- **Ventana y solapamiento del modo fragmentado.** U7 escribe «ventanas de N turnos (solapamiento de M)» (`rules.md:557`). `RunView` solo trae `fragmented: bool | None`; `RunAttempt.window` y `.overlap` existen (`entities.md:238-239`). Hace falta decidir si la instantánea los expone. Es un defecto real.
- **K-41, texto de los turnos.** Sigue vigente.
- **`registro.descartes`.** No es un defecto: ninguna regla aprobada de U7 lo consume. No hace falta abrir la tarea.
- **Nombres de `PurgeReceipt`.** Es real pero menor: solo FD-U7-12 fija tres campos. Va para U13.
- **`pending_runs`.** No es un defecto: el nombre sale de la prosa de contract-summary y se deriva de `runs`.
- **K-42 (`test_package_map.py`).** Ya está registrada.

```
VEREDICTO: NO-VERDE
NARANJA|contracts/src/veridicus_contracts/report_ports.py:232-240|SuggestionWithDecision renombra decided_by/decided_at a actor_user_id/at contra C7 v2 y EffectiveState de U5; el control nuevo fija el nombre equivocado
NARANJA|contracts/src/veridicus_contracts/report_ports.py:141-187|SessionSnapshot quita la hora de terminacion que exige la revision 4 de C11 (FD-U7-03, U7 BR11.3); docstring contradictoria
AMARILLO|contracts/tests/typing/test_protocols.py:487|los controles de los tipos auxiliares buscan el miembro en toda la salida y no en las notas
AMARILLO|contracts/tests/typing/test_protocols.py:460|una sola linea en blanco antes del decorador
INFORME: docs/loop/revisiones/U01-T16/ronda-2.md
```
