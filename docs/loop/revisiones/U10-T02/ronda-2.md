# Ronda 2 — U10-T02

**Veredicto: VERDE.** Los diez hallazgos de la ronda 1 están cerrados: nueve en el diff y F-06, por decisión del humano, queda en manos del orquestador. Corrí CA-1 a CA-7 yo mismo y todos pasan. El rojo de `afa8f20` está intacto en `074a2e1` y resiste las pruebas adversariales. Quedan tres observaciones AMARILLO; ninguna obliga a cambiar el rojo.

## Hallazgos de la ronda 1

| Hallazgo | Estado | Cómo lo comprobé |
|---|---|---|
| F-01 | cerrado | Los turnos llevan «doña …». La regla de tratamiento da `[PERSONA_1]` sin NER, como en el ejemplo de F4. `altered_markers.json` concuerda. |
| F-02 | cerrado | Repetí la sonda de la ronda 1 (abajo): ahora falla en las 15 posiciones. |
| F-03 | cerrado | `RecordingTable` anota el tamaño al llamar a `clear()`. Se exige al menos 1 tabla y al menos 1 forma en éxito, error del proveedor, restauración y `error_de_serializacion`. |
| F-04 | cerrado | E2 compara plantillas exactas, con turnos que empiezan en minúscula. |
| F-05 | cerrado | Hay 12 ramas después del envío y 4 antes. Se revisan `repr(call)` y `str(call)`. |
| F-06 | pendiente del orquestador | CG-U10-08 todavía no está en el plan de la rama del Bolt. Hay que escribirlo antes de despachar T04. |
| F-07 | cerrado | La firma es `build_anonymizer(env, transport=None)`. |
| F-08 | cerrado | La bitácora ya da la causa correcta del rojo. |
| F-09 | cerrado | 503 es `api_error`, 529 es `overloaded_error` y hay un *fixture* `max_tokens` nuevo. |
| F-10 | cerrado | `leaked_values` cubre el modelo, los dominios (el real y el alterado) y el nombre de la clave. |

## Criterios, corridos por mí en el worktree

| CA | Comando | Resultado |
|---|---|---|
| 1 | `uv sync --frozen`, `uv lock --check` y `mypy --strict src` (`--directory …/libs/anonymizer`) | 0, 0 y 0 (15 archivos) |
| 2 | `pytest tests/test_package.py -q` y `grep -n addopts pyproject.toml` | 0, 3 pruebas pasan; `--disable-socket` sin `--cov` |
| 3 | `pytest tests/guards tests/contracts --collect-only -q` | 0; 100 pruebas, 0 errores |
| 4 | El mismo `pytest -p no:cacheprovider -rf`, en una copia de `afa8f20` sacada con `git archive` al scratchpad | 1; junitxml: `tests=100 failures=100 errors=0 skipped=0`. Todas fallan con `NotImplementedError` de `load_catalogs` o de `build_anonymizer`. |
| 4b | `git log --oneline` sobre `tests/guards`, `tests/contracts`, `tests/support.py` y `tests/fixtures` | dos commits, `32317a9` (superado) y `afa8f20`, como se esperaba |
| 4c | `git show --stat afa8f20` | el commit solo toca pruebas y *fixtures*, nada de `src/` |
| 5 | `pytest tests/testing --cov=…fake_transport --cov-branch --cov-fail-under=100` | 0; 10 pruebas, 100 % de ramas |
| 6 | `mypy --strict src tests`, `ruff check .` y `ruff format --check .` | 0, 0 y 0 |
| 7 | las tres guardias `check-no-*.sh` | `0 apariciones` cada una |
| candado | `git diff --exit-code afa8f20 074a2e1` sobre `tests/guards`, `tests/contracts`, `tests/support.py` y `tests/fixtures` | 0; nada cambió |
| alcance | `git diff --stat bolt/b10a-anonymizer...tarea/U10-T02`, excluyendo `libs/anonymizer` y `docs/loop/bitacoras` | vacío |
| limpieza | `git status --short --untracked-files=all` al terminar | limpio |

## Pruebas adversariales sobre el rojo

- **Sonda de F-02.** Para cada turno del conjunto sembrado se armó un cuerpo con el nombre de pila sin enmascarar y el resto del nombre como marca, y se pasó por la aserción del payload, con escapes y sin escapes.
  - Con el nombre de pila a la vista, la aserción falla en las 15 posiciones, incluidos el salto de línea y la colisión con nombre común.
  - Con el nombre completo enmascarado, pasa en las 15.
- **`outgoing_views`.** El cambio solo añade vistas, las cadenas de cada turno ya decodificadas. No quita ninguna, así que no oculta nada ni vuelve vacía ninguna aserción. Además conserva `request_count >= 1`.
- **Costuras por `monkeypatch`.** `api.load_catalogs` y `application.generate.now` no son ninguna vía de escape: ningún parámetro las expone desde producción, igual que `bypass`.
  - El caso de dominio y puerto exige que `build_anonymizer` acepte el catálogo alterado y que `generate` falle cerrado. Eso es lo que pide el paso 4.
  - La clave se comprueba en `generate`, como dice la tabla F7 («Clave referenciada ausente · Antes · `AnonymizerUnavailable`»).
- **Datos y umbrales.** Solo hay datos sintéticos; ningún umbral bajó. En `src/` solo hay *stubs*, más dos costuras y el `MaskTable.__len__` de una línea que exige F-03.

## Hallazgos

### F-11 · AMARILLO · `tests/guards/test_autonomia_04_payload.py:80-100` (E2)
E2 exige una sola marca para un nombre completo sin tratamiento. Sin NER, eso solo pasa si la red de seguridad une en un tramo las palabras con mayúscula separadas por un espacio.
- F4, paso 3 («se tocan en su unión») lo admite, y el escenario E2 de la especificación lo pide (un nombre completo lleva una sola marca).
- Pero BR1.5 habla de «una palabra». Si T03 marca palabra por palabra, E2 no puede pasar.
- **Corrección:** fijar esa lectura en la tarea de T03 o en CG-U10-08. El rojo no cambia.

### F-12 · AMARILLO · paso 7 del plan frente a `application.generate.now`
El plan pone el presupuesto de NFR3.5 en el paso 7 (T03, dominio). Pero la prueba `presupuesto_agotado` solo puede pasar si el reloj se lee en `application/generate.py`.
- **Corrección:** anotar en las tareas de T03 y T04 que el dominio no lee el reloj y que la medición vive en la aplicación. El rojo no cambia.

### F-13 · AMARILLO · `testing/fake_transport.py:63` (`http_error`)
`http_error` devuelve el tipo `api_error` con cualquier estado, también con 529. Las pruebas usan el *fixture* `error_529.json`, así que hoy no afecta.
- **Corrección:** que T04 lo tenga en cuenta si usa `http_error(529)`. El rojo no cambia.

## Tareas candidatas
- Escribir CG-U10-08 en el plan: el candado del paso 10 se amplía a `tests/support.py` y `tests/fixtures` (F-06).

```
VEREDICTO: VERDE
AMARILLO|libs/anonymizer/tests/guards/test_autonomia_04_payload.py:80|E2 fija que la red de seguridad une las palabras con mayúscula seguidas en un tramo; hay que precisarlo en T03 (no cambia el rojo)
AMARILLO|code-generation-plan.md paso 7|el presupuesto se mide con application.generate.now; el dominio no lee el reloj (no cambia el rojo)
AMARILLO|libs/anonymizer/src/veridicus_anonymizer/testing/fake_transport.py:63|http_error da api_error también con 529
INFORME: docs/loop/revisiones/U10-T02/ronda-2.md
```
