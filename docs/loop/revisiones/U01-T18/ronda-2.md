# Ronda 2: U01-T18

VEREDICTO: NO-VERDE

Corrí yo los cinco criterios sobre `6e95ff5` (el código es `50382a0`) y todos pasan. Se cierran F-01, F-03 y F-04, y también la parte de F-05 que tocaba a esta ronda. De F-02 queda un resto: BR1.1 cita una prueba que no cubre su regla y no trae control negativo. Por eso el veredicto es NO-VERDE.

Lo comprobado sin defectos:
- **Alcance:** el diff contra `feat/b1-contratos` toca solo los 7 archivos de `checks/`, las 6 pruebas y la bitácora. No hay contratos, *fixtures*, `pyproject.toml` ni módulos de T15 o T17.
- **Nada aflojado:** entre `c014774` y `HEAD`, los cambios de `test_ci_workflows.py`, `test_synthetic.py` y `test_loader_usage.py` solo añaden casos. En `test_fixture_coverage.py` se reescribió el control de la unión con conjuntos sintéticos. La bitácora lo declara y el control no pierde fuerza.
- **SHA:** los 16 commits están en `git log feat/b1-contratos..HEAD`. Todo SHA anterior de la bitácora lleva su marca de reescrito en su línea o en las líneas que mapean cada rebase. `8a44673`, `5f36fb4`, `e55aa4d`, `f4fa5e8` y `ccd1c29` son commits de la base.
- **Worktree:** limpio al terminar; solo quedan cachés ignoradas. Borré el *worktree* temporal que usé para los rojos (`git worktree list` ya no lo muestra).

## Criterios de aceptación, verificados por mí
| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| 1 | Paso 19 | `timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U01-T18/contracts pytest tests/checks/test_loader_usage.py … test_ci_workflows.py --no-cov -q -p no:cacheprovider` | pasa: `186 passed in 5.29s` |
| 2a | Cobertura | `timeout 300 uv run … pytest tests/checks --cov-fail-under=0 -q -p no:cacheprovider --durations=5` | pasa: `1870 passed in 260.79s` (39 s de margen sobre el `timeout`; en la ronda 1 fueron 245 s) |
| 2b | 100 % en los seis | `uv run … coverage report --include=&lt;los seis y _recorrido.py&gt; --fail-under=100 --show-missing` | pasa: `TOTAL 512 0 236 0 100%` |
| 3 | Suite del Bolt | `timeout 300 uv run … pytest tests --no-cov -q -p no:cacheprovider` | pasa: `2444 passed, 1 warning in 119.14s` |
| 4 | Rueda, tipos y *lint* | `pytest tests/test_package_map.py --no-cov -q`; `mypy --strict src`; `ruff check .` | pasa: `8 passed`; `Success: no issues found in 41 source files`; `All checks passed!` |
| 5 | Sin cambios al clúster | `bash /workspace/.worktrees/U01-T18/scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T18` | pasa: `0 apariciones` |
| F-04 | Rojo de la ronda 2, repetido | *worktree* temporal en `9908ea8` (código de `c014774` y pruebas finales de esos tres archivos), corriendo `pytest test_ci_workflows.py test_synthetic.py test_fixture_coverage.py test_loader_usage.py --no-cov -q --tb=line` | `25 failed, 96 passed`, igual que la bitácora. Fallan por la regla: 10 de `ci_workflows`, 10 de `synthetic` y 4 de `fixture_coverage` por aserción. 1 falla por la forma de los datos (`ValueError`), y la bitácora lo declara así. |
| F-04 | Rojo de E-19, repetido | `loader_usage.py` de `dcdff20` con `scan` envuelto para aceptar `raiz` (`python -c "…m.scan=lambda paths, raiz=None: o(paths); pytest.main([...])"`) | `2 failed, 17 passed`. Falla por la regla: `otro/tests/test_package_map.py` queda exento por sufijo. Igual que la bitácora. |
| F-04 | Rojos de E-27 y BR8.2 | `git diff --stat 5daac1e HEAD -- contracts/tests` sale vacío | El archivo final de `test_fixture_coverage.py` es el de `5daac1e`, que es el del rojo de BR8.2 (`2 failed, 17 passed`, por aserción) |

## Hallazgos

### F-01 · NARANJA · `contracts/src/veridicus_contracts/checks/fixture_coverage.py:239` · BR1.1 cita una prueba que no cubre su regla y no trae control negativo
P-T18-13 dice que la primera prueba citada es la positiva y que las siguientes son sus controles negativos. BR1.1 cita una sola: `test_queue_messages.py::test_cada_fixture_de_cola_se_acepta_o_se_rechaza_por_su_regla`. Además, esa prueba no cubre la regla.
- `rules.md:35-43`: «Todo contrato tiene versión semántica y todo mensaje de cola declara `schema_version`. SI **falta** la versión o no tiene la forma ENTONCES es inválido».
- **Ningún *fixture* de cola se rechaza por BR1.1.** `grep -rn reject_reason contracts/queues/fixtures` solo da BR1.2, BR2.1, BR2.3, NFR10.2 y NFRD-U1-07. `grep -rn "BR1\.1\b" contracts` solo encuentra la propia lista y la línea 1 de `test_queue_messages.py`.
- **El contrato sí aplica la regla, pero nada lo fija.** Lo probé con `python -c` y `_validador('C2.RunRequested')` sobre `run.valid.yaml`: sin `schema_version` sale `['required']`, y con `'2.0'` sale `['pattern']`. Si alguien quitara `schema_version` de `required`, la prueba citada seguiría en verde.
- **La parte «todo contrato tiene versión semántica»** no la prueba ningún test del árbol. La prueba de `test_servers.py:955` mira la versión de OpenAPI o AsyncAPI, no la del contrato.
- **Cuánto cubre hoy:** solo la forma de la versión, y de rebote, porque los *rejects* de BR1.2 usan el mismo `pattern` de `$.schema_version`.

El mismo criterio de «la cubre entera» que llevó a la parada por BR1.4 aplica aquí. Además, en la ronda 1 fui yo quien afirmó que `test_queue_messages.py` cubría BR1.1, y P-T18-10 se apoyó en esa afirmación, que era inexacta. El codificador no puede escribir *fixtures* nuevos sin avisar, así que la salida pasa por el humano. Hay tres caminos:
- aceptar la cobertura parcial con una precisión explícita;
- tratar BR1.1 como BR1.4;
- abrir una tarea que añada *fixtures* `reject` con `reject_reason: BR1.1` (sin versión y con una versión sin la forma) y citarlos.

### F-02 · AMARILLO · `contracts/src/veridicus_contracts/checks/ci_workflows.py:17` · `_OPCIONES` retrocede de forma exponencial
`(?:\s+-{1,2}[\w.-]+(?:[= ]\S+)?)*` es ambiguo: un `-x` que sigue a una opción puede ser el valor de esa opción o una opción nueva. Lo medí con `python -c` y `PROHIBIDOS[1][1].search('kubectl'+' -a'*n+' x')`: con n=24 tarda 0.015 s, con 28 tarda 0.104 s, con 32 tarda 0.769 s y con 34 tarda 1.875 s. El tiempo crece unas 1.6 veces por cada opción añadida. La entrada son *workflows* propios que entran por PR, así que no es un bypass. Aun así, es el mismo defecto que `redos.py` prohíbe en los contratos. Se corrige quitando la ambigüedad, por ejemplo, con `(?:=\S+|\s+[^\s-]\S*)?` como valor de la opción.

### F-03 · AMARILLO · P-T18-12 · El límite declarado es aceptable, pero no está completo
Repetí la sonda y todas las formas de la ronda 1 salen marcadas: `-n x`, `--context=x`, `--namespace x`, `KUBE_CONFIG`, `kube_config`, `/usr/bin/kubectl apply`, `kubectl -v 9 --namespace x apply`, `kubectl -n x -- apply`. Las lecturas pasan sin falsos positivos: `kubectl -n x get pods`, `kubectl --context=m -n x get pods`, `helm -n v list`, `helm --namespace v template`, `kubectl -n x describe applyset`.

Sobre `$K apply`: un análisis estático de texto no puede resolver una variable, así que el límite es aceptable y no exime más de lo que declara. Hay otro hueco que no declara: un valor entre comillas con espacios no se detecta (`kubectl --namespace "a b" apply -f x` da `[]`). Basta con añadirlo a P-T18-12 o a K-52.

### F-04 · AMARILLO · `synthetic.py:116-130` · El año no tiene cota
Repetí los controles negativos y todos salen marcados: `1234-56-78`, `2026-13-45`, `2026-02-30`, `1234-56`, `2026-00`, `T25:00`, `T10:61`, `+25:00`, una fracción de 13 dígitos y una de 7, `T24:00`, `:60`. Pasan las fechas válidas. Queda un detalle: `1234-05` y `9999-12-31` se eximen porque son fechas que existen. Va como candidata, si se quiere acotar el año.

### Precisiones, contrastadas con su fuente
- **P-T18-11:** aceptada. Cierra F-03 de la ronda 1 con lo que pedía el informe.
- **P-T18-12:** aceptada, con lo que añade F-03 de esta ronda.
- **P-T18-13:** aceptada. BR8.1 y BR8.2 citan su prueba positiva y su control negativo, y las dos existen en el árbol: `test_console.py:640/669`, `test_metrics.py:139/198`.
- **P-T18-14:** aceptada. Recontado contra `rules.md`: 56 ID, menos BR2.2, BR2.4 y BR2.5 retiradas, dan 53 vigentes. `REGLAS` aporta 14 BR, `REGLAS_CON_CODIGO` 30 y `EXCLUIDAS` 9, sin cruces: 53 exactas.
- **P-T18-15:** aceptada. El motivo de BR1.4 es el de E-27. `SIN_PRUEBA` ya no existe y hay una prueba que lo fija.

## Tareas candidatas (defectos reales fuera de alcance)
- §4.11 habla de «un comando que aplique cambios al clúster», pero la tarea solo lista `apply`, `install` y `upgrade`. `kubectl create`, `replace`, `patch` y `delete`, y `helm uninstall` y `rollback`, no se detectan. Conviene ampliarlo junto con K-52.
- CA-2 ya tarda 260.79 s de los 300 del `timeout` (en la ronda 1 eran 245 s). Sigue vigente la candidata de la ronda 1.
- `transcript/speaker-markers.v1.yaml` e `integrity/clarification-speech.v1.yaml` siguen sin crearse.

```
VEREDICTO: NO-VERDE
NARANJA|contracts/src/veridicus_contracts/checks/fixture_coverage.py:239|BR1.1 cita una sola prueba, sin control negativo y sin ningún reject por BR1.1; no cubre «falta la versión» ni «todo contrato tiene versión semántica»
AMARILLO|contracts/src/veridicus_contracts/checks/ci_workflows.py:17|_OPCIONES ambiguo: retroceso exponencial (34 opciones tardan 1.9 s)
AMARILLO|P-T18-12|un valor de opción entre comillas con espacios también esquiva la guardia; falta declararlo
AMARILLO|contracts/src/veridicus_contracts/checks/synthetic.py:116-130|fechas exentas con un año sin cota (1234-05)
INFORME: docs/loop/revisiones/U01-T18/ronda-2.md
```
