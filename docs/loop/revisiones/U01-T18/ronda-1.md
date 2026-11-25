# Ronda 1: U01-T18

VEREDICTO: NO-VERDE

Corrí yo los cinco criterios sobre `aa6ae16` (código y pruebas en `5a85a81`) y todos pasan. El veredicto es NO-VERDE por cuatro hallazgos NARANJA. Ninguno es ROJO.

Lo comprobado sin defectos:
- **Hash de la tarea:** coincide (`2fc61365499688783288457278ed973491614321`).
- **Alcance:** el diff contra `feat/b1-contratos` toca solo los 7 archivos de `checks/` (los seis módulos y `_recorrido.py`), las 6 pruebas y la bitácora. No hay contratos, *fixtures* ni archivos prohibidos.
- **Worktree:** limpio al terminar; solo quedan cachés ignoradas.
- **SHA:** los 7 commits están en `git log feat/b1-contratos..HEAD`. Cada SHA anterior al rebase lleva su marca «reescrito» en su línea.

## Criterios de aceptación, verificados por mí
| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| 1 | Paso 19 | `timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U01-T18/contracts pytest tests/checks/test_loader_usage.py … test_ci_workflows.py --no-cov -q` | pasa: `150 passed in 4.92s` |
| 2a | Cobertura | `timeout 300 uv run … pytest tests/checks --cov-fail-under=0 -q` | pasa: `1814 passed in 245.49s` (55 s de margen sobre el `timeout`) |
| 2b | 100 % en los seis | `uv run … coverage report --include=&lt;los seis&gt; --fail-under=100 --show-missing` | pasa: `TOTAL 461 0 214 0 100%`; `_recorrido.py` también al 100 % |
| 3 | Suite del Bolt | `timeout 300 uv run … pytest tests --no-cov -q` | pasa: `2388 passed, 1 warning in 113.99s` |
| 4 | Rueda, tipos y *lint* | `pytest tests/test_package_map.py --no-cov -q`; `mypy --strict src`; `ruff check .` | pasa: `8 passed`; `Success: no issues found in 37 source files`; `All checks passed!` |
| 5 | Sin cambios al clúster | `bash /workspace/.worktrees/U01-T18/scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T18` | pasa: `0 apariciones` |
| extra | `redos` sobre los contratos | `uv run … python -c "…redos.comprobar(Path('.'))…"` | `0 []`; 19 patrones distintos recorridos |
| extra | Rojo de la ronda 1b, repetido | *worktree* temporal en `20ffe3b` con `contracts/tests/checks` de `1f50de0`, ya borrado | `24 failed, 60 passed`, igual que la bitácora |

## Hallazgos

### F-01 · NARANJA · `checks/ci_workflows.py:16-19` · La guardia de AUTONOMIA-01 se salta con las opciones globales de `kubectl` y `helm`
Los patrones exigen `kubectl\s+apply` y `helm\s+(install|upgrade)` seguidos. Una opción entre la herramienta y el verbo los esquiva, y esa es una forma habitual de escribir el comando. Lo probé con `uv run … python -c` sobre `c.PROHIBIDOS`:
- `kubectl -n veridicus apply -f x.yaml` da `[]`.
- `kubectl --context=minikube apply -f x` da `[]`.
- `helm --namespace v upgrade --install a b` da `[]`.
- `KUBE_CONFIG: x` da `[]`: una credencial con ese nombre tampoco se detecta.

Solo `kubectl apply -f x` sale marcado. Falta un control negativo para cada forma con opción intermedia.

### F-02 · NARANJA · `checks/fixture_coverage.py:219-222` · `SIN_PRUEBA` es una excepción que E-24 no autoriza, y su motivo es inexacto
E-24 da dos salidas: *fixtures* `accept` y `reject`, o la lista cerrada de reglas con su prueba. `SIN_PRUEBA` (BR1.1, BR1.4, BR8.1, BR8.2) es una tercera vía: esas cuatro reglas no tienen *fixture* ni prueba citada. Se añadió en la ronda 1b sin una parada ni una precisión P-T18-n. La tarea pedía parar y avisar si faltaba cobertura para una regla.

Además, el motivo no se sostiene para dos de ellas:
- **BR8.1:** `grep` encuentra pruebas en el árbol: `tests/contracts/test_console.py:641`, `tests/checks/test_report_closed.py:1088` y `tests/contracts/test_correcciones_t17b.py`. «Las trae T17» no basta, porque T17b ya está fusionada.
- **BR1.1:** `tests/contracts/test_queue_messages.py` declara en su línea 1 que cubre BR1.1–BR1.3.

Se corrige de una de dos formas:
- pasar BR1.1 y BR8.1 a `REGLAS_CON_CODIGO` con su prueba;
- elevar BR1.4 y BR8.2, y `SIN_PRUEBA` en sí, al humano como precisión.

### F-03 · NARANJA · `checks/synthetic.py:43-46` (P-T18-5) · La exención de fechas va más allá de K-04 y abarca de más
K-04 exime solo los uuid y las huellas de 64 caracteres hexadecimales. P-T18-5 añade por su cuenta toda forma `NNNN-NN[-NN[T…]]`, con fracciones de segundo de cualquier largo y sin comprobar que la fecha exista. Con `_sospechoso` sale `False` para:
- `1234-56-78` (8 dígitos);
- `2026-13-45` (fecha imposible);
- `1234-56` (6 dígitos);
- `2026-11-24T10:00:00.1234567890123`.

La necesidad es real: `registrado_en` y `price_table_version` son valores legítimos. Pero la exención debería exigir una fecha válida (por ejemplo, `datetime.fromisoformat` más `YYYY-MM` con un mes entre 01 y 12) y acotar la fracción. Hace falta un control negativo con una fecha imposible.

### F-04 · NARANJA · bitácora, «Rojo primero» de las rondas 1 y 1b · La evidencia del rojo está incompleta y se describe mal
- **Ronda 1, recortado:** el rojo está pegado a medias: `... (138 líneas ERROR, una por prueba; la salida de la herramienta se truncó…)`. No es literal ni completo.
- **Ronda 1, no repetido:** las pruebas cambiaron después del rojo, dentro del commit de código `94ce5f1` (`test_redos`, `test_refs`, `test_synthetic` y `test_fixture_coverage`). El paso 4 del plan de pruebas pide volver a correr el rojo con el archivo final y pegarlo; no se hizo. Revisé el diff de esas pruebas y no afloja ninguna regla.
- **Ronda 1b, mal descrita:** la bitácora dice que el rojo «falla por la regla». Al repetirlo vi que 14 de los 24 fallos son `TypeError: scan() got an unexpected keyword argument 'raiz'` y 4 son `AttributeError` por atributos que aún no existían: es una API ausente, no una regla. En particular, el rojo de E-19 por ruta completa nunca muestra la regla que falla, que era la coincidencia por sufijo de P-T18-7.

Que el rojo de la ronda 1 sea por módulo ausente se acepta: con módulos nuevos no hay otra forma, y es la convención de `importar_o_fallar`.

### F-05 · AMARILLO · Huecos menores de las guardias, agrupados
- **`loader_usage`:** no detecta `import os as o; o.system()`, `importlib.import_module("subprocess")`, `__import__("yaml")` ni `os.popen`. Ruff S6xx cubre una parte.
- **`synthetic`:**
  - no revisa los `example` numéricos (`{'example': 12345678}` da `[]`), aunque §4.10 dice «todo `example`»;
  - no revisa los valores de `default`, `const` ni `enum` (P-T18-6);
  - no toma la coma como separador (`1,234,567` pasa);
  - las secuencias de 11 a 22 dígitos pasan;
  - una mención se busca como subcadena, así que «Ana» se encuentra dentro de «Mariana».
- **`redos`:**
  - §4.5 es una lista blanca («se permiten solo…»), pero el código es una lista negra: los grupos atómicos `(?&gt;…)` y los cuantificadores posesivos `a++` no se marcan como no portátiles, y JavaScript no los admite;
  - la medición de Hypothesis usa `re.fullmatch`, mientras que `jsonschema` usa `re.search`.
- **`fixture_coverage`:**
  - ninguna prueba exige que `REGLAS`, `REGLAS_CON_CODIGO`, `EXCLUIDAS` y `SIN_PRUEBA` juntas sumen las 53 reglas vigentes. Hoy suman exactamente 53 (lo conté contra `rules.md`), pero una regla nueva quedaría fuera sin aviso;
  - un `reject` cuyo `reject_reason` no está en `REGLAS` no se revisa por su causa. Hoy no hay ninguno.
- **`test_loader_usage.py:178`:** la prueba se presenta como «un C8 con un término repetido», pero lo que siembra es una clave repetida (`schema_version`). El control del término repetido existe en `test_veracity.py:259`.
- **Pruebas citadas en E-24:** BR3.4 y BR5.1 citan una prueba solo positiva, aunque al lado existe su control negativo (`test_e34_codigo_de_c6_sin_code`, `test_c8_con_un_termino_nuevo_o_repetido_da_br51`).

### Precisiones del codificador, contrastadas con §4.5 y §4.10
- **P-T18-4** (`_recorrido.py` como módulo auxiliar): aceptada. No es un desborde y tiene 100 % de cobertura.
- **P-T18-5:** es el hallazgo F-03.
- **P-T18-6:** aceptada, con los huecos que anota F-05.
- **P-T18-8:** aceptada. Es más estricta que la fuente; dejar fuera la regla de `maxLength` en las claves de `patternProperties` está justificado.
- **P-T18-9:** aceptada. Cumple el texto de la tarea, y `^(a|a)+$` lo rechaza la regla de `BRANCH`.
- **E-23:** cerrada y exacta; solo exime `maxLength` y `x-veridicus-limit`. Tiene controles para otro puntero, otro archivo de `analyzer/v1/`, repetición anidada y patrón no portátil en un puntero exceptuado.
- **E-19:** cerrada; se compara por la ruta relativa completa. Tiene controles para otra carpeta, otro archivo que termina igual, sin raíz y con otra raíz.

## Tareas candidatas (defectos reales fuera de alcance)
- `scripts/check-no-cluster-apply.sh:25` tiene el mismo hueco que F-01 (`kubectl[[:space:]]+(apply|…)`, sin `KUBE_CONFIG`). Conviene corregirlo junto con el *workflow* de CI (paso 24).
- CA-2 tarda 245 s de los 300 del `timeout`. Cada guardia nueva lo acerca al corte; revisar el `timeout` o la cobertura por subconjuntos.
- Siguen sin crearse `transcript/speaker-markers.v1.yaml` e `integrity/clarification-speech.v1.yaml` (§4.10).

```
VEREDICTO: NO-VERDE
NARANJA|contracts/src/veridicus_contracts/checks/ci_workflows.py:16-19|kubectl -n x apply, helm --namespace x upgrade y KUBE_CONFIG esquivan la guardia de AUTONOMIA-01
NARANJA|contracts/src/veridicus_contracts/checks/fixture_coverage.py:219-222|SIN_PRUEBA es una excepción que E-24 no autoriza; BR1.1 y BR8.1 sí tienen pruebas en el árbol
NARANJA|contracts/src/veridicus_contracts/checks/synthetic.py:43-46|P-T18-5 exime fechas imposibles, fracciones sin cota y NNNN-NN, más allá de K-04
NARANJA|docs/loop/bitacoras/U01-T18.md (Rojo primero, rondas 1 y 1b)|Rojo de la ronda 1 recortado y no repetido tras cambiar las pruebas; el de la ronda 1b falla por API ausente, no por la regla
AMARILLO|checks/loader_usage.py, synthetic.py, redos.py, fixture_coverage.py, tests/checks/test_loader_usage.py:178|Huecos menores: alias de os y carga dinámica, example numérico, posesivos y atómicos, unión de las listas sin prueba, control de C8 mal rotulado
INFORME: docs/loop/revisiones/U01-T18/ronda-1.md
```
