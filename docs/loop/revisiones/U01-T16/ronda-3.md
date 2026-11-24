# Ronda 3 — U01-T16

VEREDICTO: VERDE

Los cinco criterios pasan en mi corrida sobre 8e68bf0. El rojo de la ronda 3 sale igual al de la bitácora. F-01 a F-04 de la ronda 2 quedan cerrados. El diff de esta ronda no afloja nada de lo aprobado en la ronda 2. Quedan dos AMARILLO, que no bloquean: una línea vieja en la docstring del módulo y una duda de alcance de P-T16-9 que debe decidir el orquestador.

## Criterios de aceptación, verificados por mí

| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| 1 | CA-1 | `timeout 120 uv run --frozen --offline --directory /workspace/.worktrees/U01-T16/contracts pytest tests/typing/test_protocols.py --no-cov -v -p no:cacheprovider` | pasa: `27 passed in 1.07s` |
| 2a | CA-2, tipos | `uv run --frozen --offline --directory /workspace/.worktrees/U01-T16/contracts mypy --strict src` | pasa: `Success: no issues found in 30 source files` |
| 2b | CA-2, lint | `uv run --frozen --offline --directory /workspace/.worktrees/U01-T16/contracts ruff check .` | pasa: `All checks passed!` |
| 3 | CA-3 | `timeout 300 uv run --frozen --offline --directory /workspace/.worktrees/U01-T16/contracts pytest tests --no-cov -q -p no:cacheprovider` | pasa: `2150 passed, 1 warning in 106.63s`. El aviso es `test_socket_bloqueado`, que está previsto |
| 4 | CA-4 | `timeout 120 uv run --frozen --offline --directory /workspace/.worktrees/U01-T16/contracts pytest tests/test_package_map.py --no-cov -q -p no:cacheprovider` | pasa: `8 passed in 3.23s` |
| 5 | CA-5 | `bash /workspace/.worktrees/U01-T16/scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T16` | pasa: `0 apariciones` |
| R | Rojo de la ronda 3 | Saqué beca3dc (`contracts` y `scripts`) con `git archive` a `&lt;scratchpad&gt;/r3/rojo` y le puse el `test_protocols.py` de HEAD, que es igual al de 9c45a66: `git diff 9c45a66 HEAD -- contracts/tests` sale vacío. Luego corrí `timeout 300 uv run --frozen --offline --directory &lt;scratchpad&gt;/r3/rojo/contracts pytest tests/typing/test_protocols.py --no-cov --tb=line -rf -q -p no:cacheprovider` | falla por la regla: `2 failed, 25 passed`, en `SessionSnapshot_sin_terminated_at` y `SuggestionWithDecision_usa_actor_user_id_y_at_de_la_tabla` |

**Lectura del rojo.**
- `terminated_at`: mypy da `Success: no issues found` y la prueba esperaba código 1.
- `decided_by`/`decided_at`: mypy da `missing following "SuggestionWithDecision" protocol members: actor_user_id, at`.
- Es la misma salida que pega la bitácora (líneas 265-293).

**SHA citados.** Todos están en `git log feat/b1-contratos..HEAD` o llevan su marca de «reescrito» en la misma línea:
- Vigentes: f9b32fb, 0feb53f, 86d4027, 349604c, beca3dc, 17dbbd3, 9c45a66, 6978ed6 y 8e68bf0.
- Marcados «reescrito»: 7c007a4, 9cc5afc, bf873a7, 0bb7613, f8d9b84, cbab6a3, d856f2c y 20d7ce9.
- El merge-base es 5f36fb4.
- `git diff 7d270e8 17dbbd3 -- contracts` sale vacío: el rebase no cambió el código que aprobé en la ronda 2.

**Hash de la tarea.** Coincide: `b080580f…`.

**Worktree.** Queda limpio al terminar.

**Alcance.** El diff de esta ronda (`17dbbd3..HEAD`) solo toca `report_ports.py`, `test_protocols.py` y `docs/loop/bitacoras/`. No toca nada de la lista «Fuera».

**F-01 (ronda 2): cerrado.**
- `SuggestionWithDecision` usa `decided_by`/`decided_at` (`report_ports.py:240-249`). Coincide con C7 v2 (`review-suggestion.v2.json:89-96`) y con P-T16-9.
- El control está invertido: el doble correcto trae los nombres de la vista y el cambiado trae los de la tabla.
- `suggestion_id`, `state`, `note` y `reformulation` también coinciden con C7 v2.

**F-02 (ronda 2): cerrado.**
- `terminated_at: datetime | None` está en `:170-175` y la docstring cita P-T16-10.
- La docstring de `snapshot` (`:264-265`) ya no se contradice.
- El control `SessionSnapshot_sin_terminated_at` tiene su rojo.

**F-03 (ronda 2): cerrado.** El control de los tipos auxiliares usa `_notas_de_conflicto(salida)` (`test_protocols.py:497`).

**F-04 (ronda 2): cerrado.** Hay dos líneas en blanco antes del decorador.

**Nada aflojado.**
- Las dos aserciones nuevas son más estrictas.
- No se quitó ningún control: siguen los 8 de firma y los 7 auxiliares de la ronda 2, y se suma uno.
- No cambió ningún `Literal` ni ninguna firma.

**Punto 3, campos que se llaman como la tabla donde hay vista o contrato en la red.** Revisé solo lo que no di por bueno en la ronda 2:
- `Principal` (`user_id`, `username`, `role`) coincide con C1 `Me` y `User`.
- `PurgedVersion.report_version_id` y `.sha256` coinciden con C1 `ReportVersion`.
- Los campos de primer nivel de `SessionSnapshot` coinciden con C1 `SessionSummary` y `SessionView`: `status`, `origin`, `profile_name`, `owner_user_id`, `config_sha256`, `finalized_at`, `consent_withdrawn_at` y `blocked_code`.
- `RoundView` no tiene esquema en C1: `grep -n -i "round"` en `console.v2.yaml` solo encuentra rutas y un code.
- Queda un caso de alcance, que va como F-02 abajo.

## Hallazgos

### F-01 · AMARILLO · `report_ports.py:12-13` · la docstring del módulo sigue diciendo que la hora de la terminación queda como candidata

La docstring del módulo dice: «Un campo que ninguna entidad nombra no está aquí: el texto del turno (K-41) y la hora de la terminación quedan como candidatas». Con P-T16-10, `terminated_at` sí está (`:170`). Es la misma clase de contradicción que señalé en F-02 de la ronda 2, pero ahora está en la docstring del módulo. Basta con quitar «y la hora de la terminación» y citar P-T16-10 como fuente de un campo que viene de contract-summary. No rompe a ningún consumidor.

### F-02 · AMARILLO · `report_ports.py:43-138` · alcance de P-T16-9 sobre `TurnView`, `RunView` y `ModelCallView`

P-T16-9 dice: «Cuando una vista de un puerto tiene entidad calculada o contrato en la red, manda ese nombre sobre el de la tabla». Tres tipos auxiliares tienen forma en la red en C1, con nombres en español de C6 (CD-05), y usan los nombres en inglés de la tabla de U4:

| Tipo | En la instantánea (tabla de U4) | En C1 (red) |
|---|---|---|
| `TurnView` | `speaker`, `page`, `fold_state` | `hablante`, `pagina`, `estado` (`console.v2.yaml:256-260`) |
| `RunView` | `from_turn`, `to_turn`, `fragmented` | `desde_turno`, `hasta_turno`, `fragmentado` (`:276-283`) |
| `ModelCallView` | `role`, `provider`, `tokens_in`, `used_fallback`, `at`… | `papel`, `proveedor`, `tokens_entrada`, `proveedor_alterno`, `fecha`… (`:299-312`) |

En `ModelCallView` la tensión es mayor: es «una fila de registro.llamadas de C6, copiada tal cual», y `team.md`/CD-05 pide los nombres de C6 «en Python, sin alias».

No lo bloqueo, por tres razones:
- La entidad aprobada de U4 (`text-flow/functional-design/entities.md:163-270`) fija justo esos nombres en inglés y anota el nombre de C6 al lado de cada uno.
- La instantánea es una vista en proceso para U7, no la forma de C1.
- U7 no fija nombres de campo para esto (`forensic-report/functional-design/rules.md:190` solo dice «hablante y página»).

Ninguna unidad consumidora se rompe. Lo que está en duda es si P-T16-9 abarca estas vistas, y el codificador mismo lo dejó señalado en la bitácora (línea 257). Lo debe aclarar una precisión del orquestador, no esta tarea.

## Tareas candidatas (defectos reales fuera de alcance)

- **Alcance de P-T16-9 frente a CD-05** (F-02). Hay que decidir si las vistas en proceso de filas de C6 (`ModelCallView`) y de C1 (`TurnView`, `RunView`) toman los nombres en español de la red o los de la entidad de U4. Si ganan los de la red, el cambio llega a U4 (entidades) y a C11.
- **K-41, K-43, K-44 y K-46.** Siguen vigentes, sin cambios.

```
VEREDICTO: VERDE
AMARILLO|contracts/src/veridicus_contracts/report_ports.py:12-13|la docstring del modulo dice que la hora de la terminacion queda como candidata aunque terminated_at ya esta (P-T16-10)
AMARILLO|contracts/src/veridicus_contracts/report_ports.py:43-138|alcance de P-T16-9: TurnView, RunView y ModelCallView usan los nombres en ingles de la tabla de U4 donde C1 tiene forma en la red con los de C6 (CD-05); lo decide el orquestador
INFORME: docs/loop/revisiones/U01-T16/ronda-3.md
```
