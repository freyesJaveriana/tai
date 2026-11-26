# Ronda 1, U10-T01

**VEREDICTO: NO-VERDE.** Todos los criterios CA-1 a CA-5 pasan en mis propias corridas. Lo que bloquea es una prueba que el plan prometió y que no está: la de una instancia de C19.

## Criterios, verificados por mí

| CA | Comando (rutas absolutas del worktree) | Resultado |
|---|---|---|
| 1 | Worktree temporal en 8911f88 (ya borrado), con `pytest tests/test_validators.py -k k56 --no-cov` | código 1: 11 fallan y 3 pasan (los 3 controles negativos que ya pasaban antes). En ese commit `validators.py` es idéntico a la base, y las pruebas de 8911f88 son idénticas a las de 7d7eb1c. |
| 2 | `uv run --frozen --offline --directory …/contracts pytest tests/test_validators.py -k k56 --no-cov -q` | código 0: 14 pasan, 5 son funciones de control negativo |
| 3 | `uv run --frozen --offline --directory …/contracts pytest -q` | código 0: 2917 pasan, cobertura 97,94 % (piso del 80 %), 31 s, sin ramas parciales en el código nuevo |
| 4 | `uv lock --check --directory …/contracts` y `grep -n -P "^version = " …/pyproject.toml` | código 0; imprime `7:version = "0.1.1"` |
| 5 | `mypy --strict src`, `ruff check .` y `ruff format --check .` | los tres terminan con 0 |

**Sondas adversariales** (con `python -c` en el worktree):
- Una marca desconocida se rechaza en todos los anidamientos que probé: `items`, `$defs` con varios niveles, `allOf`, `then`, `not` y `additionalProperties`.
- Una variante con mayúscula, con espacio o con solo el prefijo también se rechaza.
- `x-veridicus-version` dentro de `$defs` o de `items` se rechaza.
- Una versión con salto de línea final o con dígitos no ASCII se rechaza.

**Lista cerrada:** coincide exactamente con PD-4. Las 10 marcas que usan hoy los esquemas de `contracts/` son esas mismas 10.

**Umbrales:** `pyproject.toml` solo cambia la versión, así que no se bajó ninguno.

**Pruebas existentes:** ninguna se debilitó.

**Worktree:** limpio al terminar (`git status --porcelain` vacío).

## Hallazgos

### F-01 · ROJO · `contracts/tests/test_validators.py:266-269` · Falta la instancia de C19 que prometían el plan y la tarea
- **Qué falta:** el paso 1 del plan (línea 149) y el plan de pruebas de la tarea piden una instancia válida de C19 que pase `validate_instance`. La prueba `k56` correspondiente solo valida el esquema con `validate_json_schema`.
- **Por qué importa:** probé el `payload` de `contracts/cli/fixtures/report.valid.json` con `validate_instance`, con y sin `build_registry()`. Las dos veces falla con «referencia sin resolver» hacia `model-call.v1`. Es decir, la prueba omitida habría salido en rojo incluso con el arreglo puesto.
- **Causa:** `validate_instance` construye el validador desde el esquema crudo, sin anclar su `$id` relativo a `BASE_URI`. `validator_for` sí lo ancla, porque envuelve el esquema en `{"$ref": uri}`.
- **La bitácora no lo declara.** Dice «Candidatas: ninguna».
- **Corrección propuesta:**
  1. Añadir `test_k56_una_instancia_valida_de_c19_pasa` con ese fixture.
  2. Hacerla pasar en `validators.py`, que está dentro del alcance: registrar el esquema bajo su URI absoluta y validar con `{"$ref": uri}`, igual que hace `validator_for`.
  3. Si el humano decide que esto excede K-56, que ajuste el plan y lo registre como candidata. Lo que no vale es omitir la prueba en silencio.

### F-02 · AMARILLO · `validators.py:77` · La comprobación semver admite ceros a la izquierda
`_SEMVER` admite «01.02.03»; lo comprobé con una sonda. SemVer 2.0 los prohíbe, y `tools/check_tag.py:27` ya es estricto. En cambio `veracity.py`, `audit_gate.py` y `limits_catalog.py` usan la forma laxa, la misma de este diff.
**Corrección propuesta:** usar el patrón de `check_tag` y añadir el caso al `parametrize` de los controles negativos.

### F-03 · AMARILLO · `test_validators.py:297-306` · La prueba de las 10 marcas recorre la constante de la propia implementación
Si alguien cambia una marca por otra, el total sigue siendo 10 y la prueba sigue pasando. Hoy la cubren de forma indirecta los esquemas reales que valida la suite.
**Corrección propuesta:** comparar `MARCAS_X_VERIDICUS` con la lista literal de PD-4 escrita en la prueba.

## Los dos cambios fuera de las notas de la tarea
- **`contracts/README.md` (pasa a `contracts-v0.1.1`):** lo exige `tests/test_readme.py`, que compara la etiqueta con la versión de `pyproject.toml`. No es desborde, y la etiqueta sigue sin crearse.
- **Sonda de `test_correcciones_t18c.py` (pasa de `x-veridicus-limit` a `x-veridicus-otra`):** conserva la intención de la prueba. PD-4 ahora admite `-limit` en cualquier nivel, incluida la raíz. La nueva sonda sigue comprobando que una marca desconocida en la raíz se rechaza, y las variantes de E-30 (mayúscula y espacios) siguen intactas.

## Tareas candidatas
- Unificar la expresión semver de `veracity.py`, `audit_gate.py`, `limits_catalog.py` y `validators.py` con la de `check_tag.py`.

```
VEREDICTO: NO-VERDE
ROJO|contracts/tests/test_validators.py:266|falta la prueba prometida de una instancia C19 con validate_instance, que además falla por un $ref sin resolver
AMARILLO|contracts/src/veridicus_contracts/validators.py:77|la comprobación semver admite ceros a la izquierda
AMARILLO|contracts/tests/test_validators.py:297|la prueba de la lista cerrada recorre la constante de la implementación en vez de la lista de PD-4
INFORME: docs/loop/revisiones/U10-T01/ronda-1.md
```
