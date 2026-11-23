# Ronda 2 — U01-T03

VEREDICTO: VERDE

Los cinco hallazgos de la ronda 1 están corregidos y lo comprobé corriendo cada arreglo. El rojo sigue siendo el esperado: 138 fallos y 0 errores. Queda un solo detalle, AMARILLO: dos textos todavía nombran E-2 aunque ya manda E-5.

Revisé `tarea/U01-T03` en 1a08a40. El sha256 de la tarea es 6187b706…f598; el único cambio es la nota de E-5.

## Criterios de aceptación, verificados por mí
| # | Comando que corrí (con `--directory /workspace/.worktrees/U01-T03/contracts`) | Resultado |
|---|---|---|
| CA-1 | `timeout 60 uv run --frozen --offline … pytest tests/contracts tests/guards --co -q --no-cov` | pasa: 138 pruebas, código 0 |
| CA-2 | `timeout 60 uv run … pytest tests/contracts tests/guards --no-cov --junitxml=build/red.xml -q --tb=no` | pasa: `138 failed`, código 1, ninguna pasa. El informe dice `errors="0" failures="138"` |
| CA-2b | `grep -o -c -P "<failure message=\x22Failed: (contrato\|módulo) ausente" …/build/red.xml` | 138: todos los fallos son por contrato o módulo ausente |
| CA-3 | `uv run … python -m veridicus_contracts.tools.check_red build/red.xml` | pasa: `138 fallos y 0 errores`, código 0 |
| CA-4 | `timeout 60 uv run … pytest tests/tools/test_check_red.py --no-cov -q` | pasa: 8 passed |
| CA-5 | la recolección con `-m "c1 or c6 or … or asyncapi"` y `grep -n -E "strict-markers\|asyncapi" …/pyproject.toml` | pasa: 138, igual que CA-1. `--strict-markers` en la línea 127 y la lista de marcadores en la 141 |
| CA-6 | `timeout 120 uv run … pytest tests/test_runner.py … tests/test_validators.py --no-cov -q` | pasa: 76 passed |
| CA-7 | `git -C /workspace/.worktrees/U01-T03 diff --name-status feat/b1-contratos...HEAD` | pasa: solo `fixtures/`, `tests/`, `check_red.py`, `pyproject.toml` y las bitácoras. El único borrado es `contracts/fixtures/.gitkeep` |
| CA-8 | `uv run … mypy --strict src` · `uv run … ruff check .` | pasa: `Success: no issues found in 7 source files` · `All checks passed!` |
| CA-9 | `bash /workspace/.worktrees/U01-T03/scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T03` | pasa: 0 apariciones |
| — | `git -C … status --short` al terminar | limpio |

**No se revierte nada de la rama del Bolt.** La base común es 9d04b68. El diff de tres puntos no modifica ni borra ningún archivo del Bolt. A la tarea le falta un commit del Bolt (343f5ad, con E-5 y E-6), pero eso es solo atraso: el diff de tres puntos no lo toca.

## Comprobación de los hallazgos de la ronda 1
- **F-01, corregido.** Probé las funciones de la guardia con esquemas sintéticos en memoria (`uv run … python -c "exec(…)"`, sin escribir en el worktree):
  - Un documento sin `servers` y un AsyncAPI sin servidores dan `direcciones_declaradas == []`. Por tanto la nueva aserción `assert direcciones_declaradas(documento)` falla y la prueba ya no pasa en vacío.
  - `veridicus-redis:6379` se acepta como interno; `redis.example.com:6379` se marca externo.
  - Una variable OpenAPI con `default: https://api.openai.com` se detecta como externa.
- **F-02, corregido.** `_cadenas_abiertas` marca `type: [string, null]` (`$.properties.a`) y una propiedad sin `type` (`$.properties.b`). No marca la que tiene enum ni la que tiene patrón y `maxLength: 128`. `_enteros_sin_tope` marca `type: [integer, null]` sin tope.
- **F-03, corregido.** `grep` sobre `model-call.v1.yaml` en `tests/`: el marcador es `c13` en `test_model_call.py`, en `test_autonomia_03.py:150` y en `test_autonomia_04.py:211`. Ya no queda ningún `c19` sobre ese archivo.
- **F-04, corregido.**
  - `grep -rn -o -P "\d{6,}"` sobre todos los `fixtures/` solo encuentra dígitos dentro de `profile_sha256` y `config_sha256`, que son huellas SHA-256 reales y no UUID.
  - El diff del script (`--word-diff=porcelain`, filtrado con `grep -P`) no contiene ninguna línea que no sea un UUID viejo sustituido por uno v4. Son 38 archivos, con 104 líneas añadidas y 104 quitadas.
  - El script (`…/scratchpad/cambiar_uuid.py`), su mapa y su salida están registrados en la bitácora (líneas 84 a 89).
  - Corrí `check_c7.py`: los 19 fixtures de C7 y las 5 mutaciones dan la causa esperada. `check_c6.py` vuelve a dar 16 de 16.
- **F-05.** Queda para T04, como está acordado y anotado en la bitácora.
- **F-06, corregido.** La prueba ahora es estructural: `pending` → `then.not.anyOf[].required == {decided_by, decided_at}` y `else.required` igual; `dismissed` exige `note`; `edited` exige `reformulation`. Coincide exactamente con contract-summary, líneas 1707 a 1713 (FD-U1-13).

## Hallazgos

### F-07 · AMARILLO · `contracts/tests/contracts/test_queue_messages.py:9,120` y `docs/loop/bitacoras/U01-T03.md:64` · textos que todavía nombran E-2
- El docstring dice que el caso `c18` «pasa a verde en T09 (E-2)». Con E-5 pasa a verde en T05.
- El supuesto de la bitácora para T05 aún recomienda dejar `effective_config` como `type: object` y cerrarlo en T09, que es justo lo que E-5 sustituye.
- Lo mismo pasa con «Rojo hasta T09» en `test_profiles_contract.py:3`: los casos de `effective-config` pasan ahora en T05.

No cambia ninguna prueba ni ningún resultado. Se corrige el texto en T05 o en el PR.

## Tareas candidatas (defectos reales fuera de alcance)
- §4.10: aclarar en `checks/synthetic.py` que los campos de huella (patrón `^[a-f0-9]{64}$`) y los de `format: uuid` quedan exentos de la regla de 6 a 10 dígitos. Las huellas reales de los fixtures la incumplen de forma legítima.

```
VEREDICTO: VERDE
AMARILLO|contracts/tests/contracts/test_queue_messages.py:9,120 · docs/loop/bitacoras/U01-T03.md:64|docstring y supuesto de T05 siguen citando E-2/T09, sustituido por E-5
INFORME: docs/loop/revisiones/U01-T03/ronda-2.md
```
