# Ronda 1: U01-T18b

VEREDICTO: VERDE

Corrí yo los seis criterios (CA-1 a CA-6) sobre el HEAD `ca52fe5`, con el código en `c7fa2d0`, y pasan todos. La guardia `redos` de T18 da 14 hallazgos sobre la base y ninguno sobre T18b. El rojo con el archivo de prueba final se repite igual sobre la base. Solo quedan dos AMARILLO, que no bloquean.

## Criterios de aceptación, verificados por mí

| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| CA-1 | Lecturas de vuelta y validación real | `timeout 120 uv run --frozen --offline --directory /workspace/.worktrees/U01-T18b/contracts pytest tests/contracts/test_correcciones_t18b.py --no-cov -v` | pasa: `56 passed in 1.63s`. Los casos de 129 caracteres y `run.timeout.extra` pasan (11 y 4), así que el validador sí los rechaza |
| CA-2 | Suite completa | `timeout 600 uv run --frozen --offline --directory /workspace/.worktrees/U01-T18b/contracts pytest tests --no-cov -q -rs` | pasa: `2238 passed, 1 warning in 109.74s`. Ningún caso omitido. El aviso es `test_socket_bloqueado`, y es esperado. Están incluidas `limits_match` y `limits_catalog` |
| CA-3 | El diff de C25 cambia una sola línea | `git -C /workspace/.worktrees/U01-T18b diff feat/b1-contratos...HEAD -- contracts/limits.v1.yaml` | pasa: solo cambia `report_token_max_chars`, con `used_in: [C19, C5]` → `[C2, C5, C19, C21]`. El valor 128 y las demás entradas no cambian |
| CA-4 | Solo archivos permitidos | `git -C /workspace/.worktrees/U01-T18b diff --name-only feat/b1-contratos...HEAD` | pasa: los 6 contratos, `limits.v1.yaml`, `test_correcciones_t18b.py`, `test_correcciones_t15b.py` (nombrado en la bitácora) y la bitácora. No toca `analyzer/`, `src/`, `checks/` ni `conftest`/`helpers` |
| CA-5 | Instalación editable y rueda | `timeout 120 uv run --frozen --offline --directory /workspace/.worktrees/U01-T18b/contracts pytest tests/test_package_map.py --no-cov` | pasa: `8 passed` |
| CA-6 | mypy | `uv run --frozen --offline --directory /workspace/.worktrees/U01-T18b/contracts mypy --strict src` | pasa: `Success: no issues found in 30 source files` |
| CA-6 | ruff | `uv run --frozen --offline --directory /workspace/.worktrees/U01-T18b/contracts ruff check .` | pasa: `All checks passed!` |
| CA-6 | Sin cambios al clúster | `bash /workspace/.worktrees/U01-T18b/scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T18b` | pasa: `0 apariciones`, código 0 |

## Lo que pediste comprobar

1. **Los 14 hallazgos quedan corregidos.** Corrí la guardia `redos` del entorno de T18 sobre `/workspace/.worktrees/U01-T18b/contracts` y la salida sale vacía. Como control, la misma guardia sobre la base (`/workspace/contracts`, con HEAD `857049d` = `feat/b1-contratos`) devuelve exactamente los 14 hallazgos de la lista de `U01-T18.md:339-352`, con los mismos punteros. En el diff, los 14 punteros reciben `maxLength: 128` y `x-veridicus-limit: report_token_max_chars`, y los tres `code` de las colas pierden la repetición anidada.

2. **El patrón nuevo de `code`.**
   - Todos los `code` del catálogo tienen un solo punto, y el validador de C2 los acepta (`test_los_code_reales_de_las_colas_siguen_aceptandose`).
   - Los seis *fixtures* de colas usan `analysis.system` o `analysis.invalid_output`: lo comprobé con `grep -rnoP "\x22?code\x22?:\s*['\x22]?[a-z_.]+" .../contracts/queues/fixtures`.
   - Ningún contrato ni *fixture* tiene un `code` con dos puntos: `grep -rnP "...code:\s*...\.[a-z_]+\.[a-z_.]+"` no devuelve nada.
   - El validador real (`build_registry` del paquete con Draft 2020-12) rechaza 129 caracteres por `maxLength` en los 11 campos, y rechaza `run.timeout.extra` por `pattern` en los 4 `code`.

3. **`used_in`, marcas y lo que no debía cambiar.**
   - `used_in` queda `[C2, C5, C19, C21]`, que es exactamente E-25.
   - C3 (`RunResult.schema_version` y `ResultFailed.code`) y C18 (`analyzer_version`) conservan `maxLength` y la marca, y la prueba de forma lo fija.
   - El diff no toca `src/`, ninguna guardia, `analyzer/v1/` (C6) ni otra cifra o entrada de C25.

4. **Las pruebas no aflojan nada más allá de E-23 y E-25.**
   - En `test_correcciones_t15b.py` solo cambia la aserción de `used_in` de `report_token_max_chars`, más un comentario. Las de `turn_max_chars` y la de `comprobar_used_in_c5` siguen igual.
   - La prueba nueva compara el patrón exacto, el tope y la marca. Trae controles negativos sobre copias en memoria (sin `maxLength`, sin marca y con el patrón anidado) y valida con el validador real los límites 128 y 129.

5. **El rojo con el archivo final.** Saqué la base `857049d` con `git -C /workspace archive` al scratchpad, copié el archivo de prueba del HEAD y lo corrí con un `.venv` propio, sin tocar el worktree:
   - Comando: `timeout 300 uv run --frozen --offline --directory /tmp/claude-1000/-workspace/87e67c60-aa1c-4b11-8928-da89d2e300bd/scratchpad/base/contracts pytest tests/contracts/test_correcciones_t18b.py --no-cov -q --tb=line --color=no`
   - Resultado: `29 failed, 27 passed in 1.78s`, con la misma secuencia `FFFFFFFFFFFFFF.F........................FFFFFFFFFFFFFF..` y los mismos 29 nombres que la bitácora (`U01-T18b.md:283-510`).
   - Todos fallan por la regla (`maxLength None`, la marca `None`, el patrón anidado, `used_in` `['C19', 'C5']`, y el validador que no rechaza). Ninguno falla por importación ni por una precondición.
   - La pegada de la bitácora es literal y completa.

6. **Los SHA.** `git -C /workspace/.worktrees/U01-T18b log --oneline feat/b1-contratos..HEAD` lista `32f46af`, `5ff4770`, `c7fa2d0` y `ca52fe5`. `184f42a` y `857049d` son de la base. `4e3a51c` y `9a8cbab` se declaran reescritos en la línea 274, pero no en sus líneas originales (13 y 15); va como F-01.

Al terminar, `git -C /workspace/.worktrees/U01-T18b status --short` sale vacío: el worktree está limpio.

## Hallazgos

### F-01 · AMARILLO · `docs/loop/bitacoras/U01-T18b.md:13,15` · SHA reescritos sin marca en su propia línea
Las líneas 13 y 15 citan `4e3a51c` como el commit del rojo y no lo marcan como reescrito. La nota del rebase está en la línea 274 y nombra `4e3a51c` y `9a8cbab` como reescritos por `32f46af` y `5ff4770`. Las Notas de la tarea piden la marca «en la misma línea». La información está y el rojo vigente es el de la ronda 1b, así que no bloquea. Basta con añadir «(reescrito: `32f46af`)» en las líneas 13 y 15.

### F-02 · AMARILLO · `contracts/tests/contracts/test_correcciones_t18b.py:255` · El catálogo se valida solo contra C2
`test_los_code_reales_de_las_colas_siguen_aceptandose` valida todos los `code` del catálogo solo con el validador de `RunFailed` (C2). Para C3 y C5 la equivalencia sale de la prueba de patrón exacto, así que no deja ningún hueco hoy. Parametrizarla sobre `CODES_DE_COLAS` la haría resistir a una divergencia futura.

## Tareas candidatas (defectos reales fuera de alcance)
- K-49, que ya está registrada: ampliar `limits_match` (§4.4) a C3 y C18. Así `used_in` de `report_token_max_chars` reflejaría también esos contratos y la comprobación inversa cubriría sus marcas.

```
VEREDICTO: VERDE
AMARILLO|docs/loop/bitacoras/U01-T18b.md:13,15|SHA reescritos 4e3a51c sin marca en su propia linea
AMARILLO|contracts/tests/contracts/test_correcciones_t18b.py:255|codes del catalogo validados solo contra C2
INFORME: docs/loop/revisiones/U01-T18b/ronda-1.md
```
