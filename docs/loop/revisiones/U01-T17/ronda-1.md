# Ronda 1 — U01-T17

VEREDICTO: NO-VERDE

Hash de la tarea `eefcb722ea4235229a280ed0b9c6bb077f860359`: coincide con el acuse de la bitácora. La rama **no está rebasada** sobre `8a44673`: su base es `574ac38`. Por eso corrí los criterios sobre el HEAD `dde20f7` y también sobre una mezcla de prueba en el scratchpad (`git merge-tree --write-tree 8a44673 dde20f7` → `da05dcb`, exportada con `git archive`). El worktree quedó limpio (`git status --porcelain` vacío).

## Criterios de aceptación, verificados por mí
| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| 1 | Paso 18 | `timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U01-T17/contracts pytest tests/checks/test_metrics.py tests/checks/test_datetime_format.py tests/checks/test_naming.py --no-cov -p no:cacheprovider` | pasa: 20 passed en 2,79 s |
| 2a | Suite de guardias con cobertura | `timeout 300 uv run … pytest tests/checks --cov-fail-under=0 -q -p no:cacheprovider` | pasa: 1684 passed en **249,31 s** (de 13:34:11 a 13:38:47 UTC; margen del 17 % frente al `timeout 300`) |
| 2b | 100 % de líneas y de ramas | `uv run … coverage report --include=…metrics.py,…datetime_format.py,…naming.py --fail-under=100 --show-missing` | pasa: 199 sentencias y 98 ramas, 100 %. Añadí `_contratos.py`: 15 y 10, también al 100 % |
| 3 | Suite del Bolt | `timeout 300 uv run … pytest tests --no-cov -q -p no:cacheprovider` | pasa: 2202 passed y 1 advertencia (`test_socket_bloqueado`), 112,77 s |
| 3' | Suite del Bolt sobre la mezcla con `8a44673` | lo mismo en `scratchpad/mezcla/contracts`, y después `pytest tests/checks/test_error_codes.py` más los tres archivos de T17 con `libs/` exportado | pasa: 2255 passed. Los 3 fallos de la primera corrida eran de mi copia (faltaba `libs/errors/src`); con `libs/` exportado pasan los 47 |
| 4 | Rueda, tipos y *lint* | `pytest tests/test_package_map.py`, `mypy --strict src`, `ruff check .`, `yamllint metrics format` | pasan: 8 passed, «no issues found in 34 source files», «All checks passed!» y yamllint sin salida |
| 5 | Sin cambios al clúster | `bash /workspace/.worktrees/U01-T17/scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T17` | pasa: `0 apariciones` |

**Rojo, repetido por mí.**
- Las tres pruebas del HEAD sobre el código de `fbd7a63` (esqueletos, sin `metrics/` ni `format/`), en `scratchpad/rojo`: **19 failed, 1 passed**, todos por aserción y ninguno por importación. Coincide con la bitácora.
- `test_metrics.py` del HEAD sobre `e33c2d6`, en `scratchpad/rojo26`: 1 failed (`['mode', 'error_code'] == ['mode', 'outcome', 'error_code']`) y 6 passed. Coincide con el rojo de E-26.
- Ninguna prueba cambió después: `git diff cc52b27 HEAD -- contracts/tests` solo trae las 8 líneas de E-26, y su rojo es el de `f7c8263`.

**SHA.** Todos los vigentes están en `git log feat/b1-contratos..HEAD`. Los reescritos aparecen marcados como «antes …, reescrito». `e70a6fe` y `574ac38` son antepasados de `8a44673`.

**Alcance.** El diff solo añade archivos: seis de `metrics/`, `format/datetime.v1.yaml`, tres módulos, `_contratos.py` (un auxiliar privado de `checks/` dentro del alcance), tres pruebas y la bitácora. No edita C15 de contract-summary, ningún NFRD, el catálogo, C25 ni ningún contrato fusionado.

**E-20, E-21, E-22 y E-26.** Están aplicadas tal como dicen:
- E-20: `none` en las cinco series con `error_code`, y `ok` pasa a `none` en U10.
- E-21: `turn_latency` está en `voice.v1.yaml`.
- E-22: el patrón coincide con `DateTime` de C1.
- E-26: `veridicus_runs_total` es una sola serie, en C15, con `mode`, `outcome` (`completed`, `error`, `cancelled`) y `error_code`, y `text-flow.v1.yaml` no la repite.

**Precisiones contrastadas.** Cumplen su fuente P-T17-4 (C18, `model-call.v1.yaml:27`), P-T17-6, P-T17-7 (`SessionStatus` de C1), P-T17-8 (la única fuente nombra `voice`), P-T17-11 en la exención de cabeceras y P-T17-12 en `analyzer/`, `vendor/`, `fixtures/`, `.venv` y `__pycache__`. P-T17-5 no cumple (F-03) y P-T17-11 tiene un hueco (F-01).

## Hallazgos

### F-01 · ROJO · `contracts/src/veridicus_contracts/checks/naming.py:72-80` · Los parámetros de `components/parameters` no se comprueban
`_recorrer` solo comprueba `parameters` cuando es una **lista**. En OpenAPI, `components/parameters` es un **mapa**, y ahí define C1 `SessionId`, `Since`, `RunId` y `SuggestionId`, que usan unas 20 rutas por `$ref`. La propia prueba lo da por bueno: `_problemas({"parameters": {"no": "una lista"}}) == []` (`test_naming.py:62`). Sonda sobre una copia en memoria de C1:
```
uv run --frozen --offline --directory …/contracts python -B -c "… d['components']['parameters']['SessionId']['name']='sessionId'; d['components']['parameters']['Since']['name']='sinceCursor'; …"
componentes: []
en linea: ['api/x.yaml: /paths/~1a/get/parameters/0/name: el nombre no es ASCII snake_case (CD-05)']
```
La regla «parámetros en ASCII `snake_case`» (§4.12, alcance de la tarea) no se cumple justo donde C1 declara sus parámetros. Para corregirlo hay que comprobar todo objeto Parameter, esté en una lista o en un mapa (`in` ∈ {`query`, `path`} con `name`). Hace falta un control negativo sobre `components/parameters` de una copia de C1, y hay que invertir la aserción de la línea 62.

### F-02 · NARANJA · `contracts/metrics/voice.v1.yaml` · Falta `veridicus_aof_rewrite_requests_total`
`construction/voice/nfr-design/observability-design.md` §2 (línea 47) dice: «Todas salvo la primera se declaran en `contracts/metrics/voice.v1.yaml` (NFRD-U9-10)». En la línea 62 de esa tabla está `veridicus_aof_rewrite_requests_total`, counter con `outcome` (`requested`, `in_progress`, `error`) (NFRD-U9-06). La alerta de `voice/infrastructure-design/monitoring-design.md:79` depende de ella. El archivo trae las otras 11 y la bitácora no explica la omisión. Lo que hay que hacer es transcribirla; la guardia no cambia.

### F-03 · NARANJA · `contracts/metrics/session-lifecycle.v1.yaml:13-92` y `:105-184` (P-T17-5) · `error_code` de U6 con todo el catálogo HTTP
Las dos series de U6 declaran los 76 `code` con `http: true`. Entre ellos hay `research.*`, `speech.*`, `conductor_observation.*`, `user.last_admin` y `report.*`, que un pegado o una importación nunca devuelven. La fuente sí da la lista de U6: `session-lifecycle/nfr-requirements/security-requirements.md:87` (NFR10.14) con `limits.exceeded`, `import.*`, `profile.*` y los 409 de la tabla §3 del Functional Design. En U9 el codificador sí usó la lista de NFR10.12; aquí no. El enum deja de acotar y se duplica en dos bloques, que derivarán juntos cada vez que crezca el catálogo. Hay que derivarlo de NFR10.14 y del FD §3, más los genéricos de autenticación, validación y sistema. Si eso no alcanza para cerrarlo, se para y se pregunta.

### F-04 · AMARILLO · `docs/loop/bitacoras/U01-T17.md:44-46` y `:136` · Rojos resumidos y recortados
El primer rojo viene resumido («… (20 fallos por aserción …)»). El segundo está recortado, y la bitácora lo declara. Lo repetí y coincide, pero la tarea pide «la salida literal».

### F-05 · AMARILLO · `_contratos.py:11-13` y `naming.py:31` · Exenciones evitables
`ts/`, `build/`, `dist/` y `node_modules/` no existen bajo `contracts/`. Tampoco hay ningún parámetro `in: cookie`. Eximirlos es preventivo: el día que alguno aparezca con un nombre que no sea `snake_case`, pasaría sin aviso.

### F-06 · AMARILLO · `metrics.py:74-79` · Etiquetas repetidas en una misma métrica
Dos etiquetas `mode` en la misma métrica pasan: la sonda devuelve `[]`. Prometheus rechaza esa métrica al registrarla.

### F-07 · AMARILLO · Rama · Sin rebasar sobre `8a44673`
La mezcla de prueba está verde. Hay que rebasar antes del PR y repetir CA-1 a CA-5.

## Tareas candidatas (defectos reales fuera de alcance)
- `queues/results.v2.yaml:85-87`: `code` de `ResultFailed` se cierra con el `pattern` `^[a-z][a-z_]*(\.[a-z][a-z_]*)+$`, que admite `a.b.c`. `naming.py` solo mira `const` y `enum`. Hay que decidir si la forma `dominio.motivo` se exige también a los `pattern` de los campos `code` (es un contrato fusionado).
- CA-2 tarda unos 250 s con `timeout 300`. Hay que repartir la suite o subir el tiempo por decisión humana, nunca en silencio.

---

Conviene corregir primero F-01: la guardia de nombres deja pasar justo los parámetros que C1 comparte entre rutas. No escribí el informe en disco; el texto de arriba es para `docs/loop/revisiones/U01-T17/ronda-1.md`. Las copias de prueba están en `/tmp/claude-1000/-workspace/87e67c60-aa1c-4b11-8928-da89d2e300bd/scratchpad/rojo`, `/tmp/claude-1000/-workspace/87e67c60-aa1c-4b11-8928-da89d2e300bd/scratchpad/rojo26` y `/tmp/claude-1000/-workspace/87e67c60-aa1c-4b11-8928-da89d2e300bd/scratchpad/mezcla`.

```
VEREDICTO: NO-VERDE
ROJO|contracts/src/veridicus_contracts/checks/naming.py:72-80|Los parámetros de components/parameters (SessionId, Since, RunId, SuggestionId de C1) no se comprueban
NARANJA|contracts/metrics/voice.v1.yaml|Falta veridicus_aof_rewrite_requests_total (observability-design de U9 §2, NFRD-U9-06/U9-10)
NARANJA|contracts/metrics/session-lifecycle.v1.yaml:13-184 (P-T17-5)|error_code de U6 con los 76 code HTTP del catálogo en vez de la lista de NFR10.14
AMARILLO|docs/loop/bitacoras/U01-T17.md:44-46,136|Rojos resumidos y recortados (reproducidos, coinciden)
AMARILLO|contracts/src/veridicus_contracts/checks/_contratos.py:11-13, naming.py:31|Exenciones evitables (ts, build, dist, node_modules, cookie)
AMARILLO|contracts/src/veridicus_contracts/checks/metrics.py:74-79|Etiquetas repetidas en una misma métrica no se rechazan
AMARILLO|rama tarea/U01-T17|Sin rebasar sobre 8a44673 (mezcla de prueba verde)
INFORME: docs/loop/revisiones/U01-T17/ronda-1.md
```
