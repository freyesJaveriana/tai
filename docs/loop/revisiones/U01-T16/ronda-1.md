# Ronda 1 — U01-T16

VEREDICTO: NO-VERDE

Las firmas de las interfaces están bien. Transcriben contract-summary con sus revisiones, y mypy las hace cumplir: lo comprobé con mis propias sondas. Los cinco criterios pasan en mi corrida. Hay dos bloqueos. El primero es la evidencia de la bitácora: parte salió de un árbol anterior al commit final y el rojo no es literal. El segundo son los tipos auxiliares de C11: sus nombres no coinciden con los de las entidades aprobadas de U4 y U5, que son las unidades que los implementan, y les falta un campo que U4 ya fijó para la instantánea.

## Criterios de aceptación, verificados por mí

| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| 1 | CA-1 | `timeout 120 uv run --frozen --offline --directory /workspace/.worktrees/U01-T16/contracts pytest tests/typing/test_protocols.py --no-cov -v` | pasa: 17 passed in 0.74s. El arranque en frío de mypy tarda 0.37 s, igual que `test_anonymizing_provider.py` (0.37 s) |
| 2a | CA-2, tipos | `uv run --frozen --offline --directory /workspace/.worktrees/U01-T16/contracts mypy --strict src` | pasa: `Success: no issues found in 30 source files` |
| 2b | CA-2, lint | `uv run --frozen --offline --directory /workspace/.worktrees/U01-T16/contracts ruff check .` | pasa: `All checks passed!` |
| 3 | CA-3 | `timeout 300 uv run --frozen --offline --directory /workspace/.worktrees/U01-T16/contracts pytest tests --no-cov -q` | pasa: `2140 passed, 1 warning in 105.85s` |
| 4 | CA-4 | `timeout 120 uv run --frozen --offline --directory /workspace/.worktrees/U01-T16/contracts pytest tests/test_package_map.py --no-cov -v` | pasa: 8 passed. Aparte construí la rueda: trae los 7 `.py` nuevos y `analyzer/v1/salida.schema.json`. Al extraerla, `veridicus_contracts.analyzer.v1` se resuelve como `v1.py` y los datos siguen visibles (`is_file()` da `True`) |
| 5 | CA-5 | `bash /workspace/.worktrees/U01-T16/scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T16` | pasa: `0 apariciones` |
| R | Rojo de 7c007a4 | `git archive` de 7c007a4 (es la base más el archivo de prueba) en el scratchpad, y luego `timeout 300 uv run --frozen --offline --directory &lt;scratchpad&gt;/rojo/contracts pytest tests/typing/test_protocols.py --no-cov -q --tb=line -p no:cacheprovider` | falla: `17 failed in 0.09s`, todas por `Failed: módulo ausente` (ver F-01) |

- `git diff 7c007a4 HEAD -- contracts/tests` sale vacío: la prueba no cambió después del rojo.
- Los SHA 7c007a4 y 9cc5afc de la bitácora están en `git log feat/b1-contratos..HEAD`, junto con bf873a7.
- El hash de la tarea coincide: `b080580f…`.
- El diff solo trae 7 archivos nuevos bajo `src/`, `tests/typing/test_protocols.py` y la bitácora. No toca nada de la lista «Fuera».
- Al terminar, el worktree está limpio.

**Firmas (punto 1).**
- Las firmas coinciden con contract-summary y sus revisiones 4: `open_round(..., for_update: bool = False)`, `pending_counts -&gt; dict[UUID, int]`, `discard_correction_round(uow, session_id, actor) -&gt; None`, `mark_consolidated(..., actor, finalize_first=False)`, `count_pending -&gt; int`, `record(..., export_sha256: str | None = None)` y `count_session -&gt; Mapping[str, int]`.
- `lock_round`, `mark_consolidated`, `finalize`, `open_correction_round` y `discard_correction_round` reciben siempre `actor` (AUTONOMIA-03).
- La docstring de `propose` conserva «Rechaza un hallazgo sin sus campos obligatorios (AUTONOMIA-05)», y la prueba lo exige.
- Sonda propia con `mypy --strict -c`, con controles que la prueba no trae: `pending_counts -&gt; int`, `discard_correction_round` sin `actor` y `mark_consolidated` sin `actor`. Fallan con `[arg-type]`, y la nota de conflicto nombra exactamente esos miembros.

**`Role` y `Hallazgo` (punto 2).**
- `Role` se compara de verdad con `components.schemas.Role.enum` de `console.v2.yaml`.
- `Hallazgo` y `Cita` tienen exactamente las `properties`, las `required` y las opcionales de `$defs/hallazgo` y `$defs/cita`. Lo revisé a mano y la prueba lo exige.
- Los `Literal` de P-T16-7 (`tipo` con 7 valores, `avisos`) coinciden con los enums del esquema.
- Los controles negativos fallan por la firma, no por otra causa: parten del texto exacto del doble correcto, exigen `expected "&lt;Protocolo&gt;"` y `[arg-type]`, y el mismo doble sin cambiar pasa.

## Hallazgos

### F-01 · ROJO · `docs/loop/bitacoras/U01-T16.md:21-56, 73-74, 100` · evidencia que no sale del diff actual y rojo no literal

**Evidencia vieja.** La línea 100 dice: «Tras la última edición cosmética de `human_review.py` … CA-3 a CA-5 son de antes de esa edición». Esa edición está dentro de 9cc5afc. Por tanto CA-3, CA-4 y CA-5 salieron de un árbol que no es ningún commit de la rama. Además, eso contradice la línea 69, que dice «salidas producidas sobre el código del commit `9cc5afc`». La invariante 3 lo clasifica como ROJO. Mis corridas sobre bf873a7 pasan, así que el arreglo es solo volver a correr CA-1 a CA-5 en el HEAD final y pegar las salidas.

**Rojo no literal.**
- La línea 25 pone `...` en lugar de la cabecera.
- La línea 53 dice `FAILED (17 líneas, una por cada prueba de arriba)`. Eso no lo produce pytest: es texto escrito por el codificador dentro de un bloque presentado como salida.
- El verde de la línea 74 (`... 17 passed`) también va recortado.

**Respuesta a la pregunta 3.**
- Repetí el rojo con las pruebas de 7c007a4 sobre la base, con el comando de la fila R: `17 failed in 0.09s`.
- Las 17 fallan **solo por módulo ausente**, también los 7 controles negativos, porque `_mypy` llama a `importar_o_fallar` antes de mypy (`test_protocols.py:240-241`). Ninguna falla por la regla.
- Para esta tarea eso basta: las interfaces no existían, así que el único rojo posible es su ausencia. Que los negativos fallan por la firma se ve en el verde (ver «Firmas»).
- Lo que no basta es la forma: la regla pide el rojo literal y completo. Si se quiere un rojo corto, `--tb=line` sin recortes (como el mío) es literal.

### F-02 · NARANJA · `report_ports.py:25-130` · los tipos auxiliares de C11 no coinciden con las entidades aprobadas de las unidades que los implementan (barrido de clase)

P-T16-3 inventa nombres que U4 y U5 tendrían que deshacer o envolver. Aparecen en tres sitios:

- **`RoundView` (`:114-130`), cuyo dueño es U5.** `human-review/functional-design/entities.md:66-79` llama `status` al estado de la ronda (`open | locked | discarded`) y `kind` a su tipo (`initial | correction`). El módulo usa `state` y `is_correction: bool`. Tampoco trae `based_on_round_id`, que U7 necesita para la herencia (ADR-007).
- **`RunView` (`:41-56`), cuyo dueño es U4.** `text-flow/functional-design/rules.md:698, 774` (BR17.2) dice que la instantánea marca cada corrida con `covered_by_final` y lleva su estado vigente e intento. `text-flow/functional-spec.md:446` y `session-lifecycle/functional-spec.md:375` dicen que U7 lo lee para declarar los tramos sin evaluar. `RunView` no tiene `covered_by_final`, ni `attempt`, ni `mode` (incremental o final).
- **`SessionSnapshot` (`:59-111`) y `TurnView` (`:25-38`), cuyo dueño es U4.**
  - La entidad (`text-flow/functional-design/entities.md:103-114`) usa `status` y `profile_name`; el módulo usa `state` y `profile`.
  - `origin` tiene valores fijos (`guiada | corpus | sintetico`) y los estados de sesión y de ronda también son cerrados, pero el módulo los tipa como `str`.
  - `TurnView.state` se queda corto frente al «estado plegado» de la regla (`fold_state: visible | plegado`).

El glosario único de `team.md` dice: «ningún término se traduce de dos formas». Aquí el mismo campo se llama `status` en la entidad y `state` en el contrato. La tarea solo daba al codificador contract-summary, así que el arreglo puede venir del orquestador: le basta con citar en la ronda 2 los nombres de esas entidades. Lo que no conviene es fusionar nombres que dos unidades tendrían que traducir.

### F-03 · AMARILLO · CA-4 (`tests/test_package_map.py:129-143`) · la prueba no exige los `.py` nuevos en la rueda
CA-4 promete «los módulos nuevos están en la instalación editable y en la rueda», pero la prueba solo revisa directorios de datos, archivos sueltos y `py.typed`. Lo verifiqué a mano y están. La prueba es de otra tarea, así que va como candidata.

### F-04 · AMARILLO · `test_protocols.py:289-292` · el control negativo no comprueba qué miembro choca
La prueba exige `expected "&lt;Protocolo&gt;"`, pero no el nombre del miembro que está en conflicto. Hoy no importa, porque cada control cambia un solo texto. Si un doble rompiera dos miembros a la vez, el control seguiría pasando.

## Tareas candidatas (defectos reales fuera de alcance)
- **Texto de los turnos.** U7 F2, paso 7 (`forensic-report/functional-design/functional-spec.md:93`), escanea «con los textos de todos los turnos como fuente literal». La docstring de `snapshot` y `TurnView` no traen el texto. Hay que decidir si va en la instantánea o por otro puerto. No lo invento aquí.
- **`test_package_map.py`.** Que exija en la rueda cada `.py` de `src/` (F-03).
- **Enums de C6.** Una prueba que compare los `Literal` `HallazgoTipo` y `CitaAviso` con los enums del esquema. Ya la propuso el codificador.
- **`ruff format --check`.** Ya fallaba en archivos de `src/` desde antes. Lo informa la bitácora y no es un criterio de la unidad.

```
VEREDICTO: NO-VERDE
ROJO|docs/loop/bitacoras/U01-T16.md:21-56,73-74,100|CA-3 a CA-5 salieron de un árbol anterior al commit final; rojo y verde recortados, con una línea FAILED escrita a mano
NARANJA|contracts/src/veridicus_contracts/report_ports.py:25-130|RoundView, RunView, SessionSnapshot y TurnView no coinciden con las entidades de U4 y U5 (status/kind/based_on_round_id, covered_by_final, profile_name, enums como str)
AMARILLO|tests/test_package_map.py:129-143|CA-4 no exige los .py nuevos en la rueda (verificado a mano: están)
AMARILLO|contracts/tests/typing/test_protocols.py:289-292|el control negativo no comprueba qué miembro está en conflicto
INFORME: docs/loop/revisiones/U01-T16/ronda-1.md
```
