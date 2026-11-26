# Ronda 2: U10-T01

**VEREDICTO: VERDE.** Corrí yo mismo CA-2 a CA-5 y los dos rojos. Todo pasa, F-01, F-02 y F-03 quedan cerrados y no encontré regresiones en `validate_instance`. No queda ningún hallazgo ROJO ni NARANJA.

## Criterios, verificados por mí

| CA | Comando | Resultado |
|---|---|---|
| 2 | `timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U10-T01/contracts pytest tests/test_validators.py -k k56 --no-cov -q` | código 0: 16 pasan |
| 3 | `timeout 120 uv run --frozen --offline --directory /workspace/.worktrees/U10-T01/contracts pytest -q` | código 0: 2919 pasan, cobertura 97,94 % (piso del 80 % intacto), 31,5 s |
| 4 | `timeout 60 uv lock --check --directory /workspace/.worktrees/U10-T01/contracts` | código 0: «Resolved 79 packages» |
| 4 | `grep -n -P "^version = " /workspace/.worktrees/U10-T01/contracts/pyproject.toml` | imprime `7:version = "0.1.1"` |
| 5 | `mypy --strict src`, `ruff check .` y `ruff format --check .` (con `uv run --frozen --offline --directory …/contracts`) | los tres terminan con 0 |

## Hallazgos de la ronda 1

- **F-01 (ROJO): cerrado.**
  - En un worktree temporal en `b6a1919`, `pytest tests/test_validators.py -k k56 --no-cov -q` terminó con código 1: falla solo `test_k56_una_instancia_valida_de_c19_pasa`, con «referencia sin resolver … model-call.v1». En ese commit solo cambia el archivo de pruebas respecto de `7d7eb1c`.
  - En la punta de la rama, la prueba pasa.
- **F-02 (AMARILLO): cerrado.**
  - En `8cf4a48`, la misma corrida terminó con código 1: falla solo el caso `[01.02.03]`, con «DID NOT RAISE». Solo cambia el archivo de pruebas respecto de `5840337`.
  - En `adffa4f`, `_SEMVER` rechaza los ceros a la izquierda y se aplica con `fullmatch`, así que tampoco admite un salto de línea final.
- **F-03 (AMARILLO): cerrado.** En `test_validators.py`, la prueba de la lista cerrada compara `MARCAS_X_VERIDICUS` con la lista de PD-4 escrita a mano en la propia prueba.
- **K-77:** no lo cuento, por indicación del orquestador.

## Regresiones del cambio a `validate_instance`

Las sondas corrieron con `uv run --frozen --offline --directory …/contracts python -c …`.

- **Comparación de la versión anterior con la nueva:** usé los 9 esquemas registrados y 142 instancias (todos los *fixtures* de `contracts/`, su `payload` y 6 valores sueltos):
  - ningún caso que antes se rechazaba se acepta ahora, salvo 5 que antes fallaban por una referencia sin resolver;
  - ningún caso que antes se aceptaba se rechaza ahora;
  - en todos los casos, el resultado es igual al de `validator_for(registro, uri)` sobre el esquema registrado.
  - Cuentas: 1243 rechazos que se mantienen, 9 aceptaciones que se mantienen, 21 referencias sin resolver que siguen rechazadas y las 5 que ahora pasan.
- **Una instancia inválida de cada contrato se sigue rechazando.** Sale de la misma corrida, y también lo comprobé con una fecha mal formada en C13.
- **`$id` absoluto:** ningún esquema de `contracts/` lo tiene fuera de `vendor/`. Lo probé con esquemas sintéticos:
  - con un `$id` absoluto ajeno, una URN, uno relativo, uno que termina en `#`, uno vacío y sin `$id`, la instancia válida pasa y la inválida se rechaza en los seis casos;
  - con un `$id` absoluto ajeno que referencia un contrato, se rechaza y no sale a la red.
- **Esquema que el llamador pasa con el mismo `$id` que uno registrado:** si es una variante más estricta de C13, se valida contra la variante que se pasó. El registro compartido no queda modificado: el C13 original sigue aceptando la misma instancia.

## Hallazgos de esta ronda

- **F-01 · AMARILLO · `contracts/src/veridicus_contracts/validators.py:147-148` · El manejo de una referencia sin resolver no lo cubre ninguna prueba.**
  - En la base también quedaban sin cubrir esas mismas líneas (127-128 allí), así que no es una regresión.
  - Corrección propuesta: un control negativo `k56` con un esquema cuya `$ref` no está en el registro, que espere «referencia sin resolver».

## Otras comprobaciones

- **Alcance:** el diff solo toca `validators.py`, `test_validators.py`, `pyproject.toml`, `uv.lock` y la bitácora, más los dos cambios que la ronda 1 ya aceptó (`README.md` y `test_correcciones_t18c.py`). No toca `libs/` ni ningún esquema, y no crea la etiqueta.
- **Datos y reglas:** solo hay datos sintéticos, ningún nombre real del clúster ni dato del autor, y ninguna violación de `## Forbidden`.
- **Worktree:** `git -C /workspace/.worktrees/U10-T01 status --porcelain` quedó vacío. Usé un worktree temporal en el scratchpad para comprobar los dos rojos y ya lo eliminé.

```
VEREDICTO: VERDE
AMARILLO|contracts/src/veridicus_contracts/validators.py:147|la rama de referencia sin resolver no tiene prueba (ya estaba así en la base)
INFORME: docs/loop/revisiones/U10-T01/ronda-2.md
```
