# Ronda 2: U01-T17

VEREDICTO: VERDE

Corrí CA-1 a CA-5 sobre el HEAD `fda2a4f`. Todos pasan, F-01 a F-07 quedan cerrados y no hay ningún ROJO ni NARANJA. Solo quedan dos AMARILLO.

Comprobaciones previas:
- **Hash de la tarea:** `eefcb722ea4235229a280ed0b9c6bb077f860359`, coincide con el acuse.
- **Base de la rama:** `git merge-base feat/b1-contratos HEAD` devuelve `ab36370`. La rama del Bolt está en `e55aa4d`, pero entre las dos solo cambian `decisiones-humano.md` (P-T18-10), `CANDIDATAS.md` y el informe de T18 (comprobado con `git diff --stat ab36370 e55aa4d`).
- **Worktree:** limpio al terminar (`git status --porcelain` sin salida).

## Criterios de aceptación, verificados por mí
| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| 1 | Paso 18 | `timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U01-T17/contracts pytest tests/checks/test_metrics.py tests/checks/test_datetime_format.py tests/checks/test_naming.py --no-cov -p no:cacheprovider` | pasa: 20 passed en 2,76 s |
| 2a | Suite de guardias con cobertura | `timeout 300 uv run … pytest tests/checks --cov-fail-under=0 -q -p no:cacheprovider` | pasa: 1684 passed en **254,13 s** (de 14:04:41 a 14:09:00 UTC aprox., con lecturas ligeras en paralelo). Margen del 15 % frente al `timeout 300` |
| 2b | 100 % de líneas y de ramas | `uv run … coverage report --include=…metrics.py,…datetime_format.py,…naming.py --fail-under=100 --show-missing` | pasa: 202 sentencias y 100 ramas, al 100 %. También lo corrí sumando `_contratos.py`: 15 sentencias y 10 ramas, al 100 % |
| 3 | Suite del Bolt | `timeout 300 uv run … pytest tests --no-cov -q -p no:cacheprovider` | pasa: 2258 passed y 1 advertencia (`test_socket_bloqueado`) en 114,91 s |
| 4 | Rueda, tipos y *lint* | `pytest tests/test_package_map.py`, `mypy --strict src`, `ruff check .` y `yamllint metrics format` | pasan: 8 passed, «no issues found in 34 source files», «All checks passed!» y yamllint sin salida |
| 5 | Sin cambios al clúster | `bash /workspace/.worktrees/U01-T17/scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T17` | pasa: `0 apariciones` |

## Rojo de la ronda 2, repetido por mí
Armé una copia en el scratchpad con el código de `bbeb73c` (la ronda 1) y las pruebas de `adc1432`, con `git archive` y `tar`.

- **Las tres pruebas juntas:** **6 failed, 14 passed**, los seis por aserción y con las mismas pruebas y líneas que la bitácora (`test_metrics.py:124`, `:185`; `test_naming.py:39`, `:70`, `:88`, `:177`).
- **Pruebas sin cambios desde el rojo:** `git diff --stat adc1432 fda2a4f -- contracts/tests` no tiene salida. El verde corre las mismas pruebas que el rojo.
- **La parte de C1, aislada.** Es cierto que en el rojo el mapa tapa la diferencia de C1. Por eso corrí `naming.comprobar_documento` sobre una copia de C1 con `SessionId` cambiado a `sessionId` y `Since` a `sinceCursor`:
  - Con el código viejo (`rojo-r2`) devuelve `c1-viejo []`.
  - Con el HEAD salen `/components/parameters/SessionId/name` y `/components/parameters/Since/name`.

  El control de C1 falla por la regla y no por otra causa. La evidencia basta.

## Comprobaciones pedidas
1. **F-01 a F-07, cerrados.**
   - F-01: `naming.py:61-63` comprueba todo objeto con `in` ∈ {`query`, `path`, `cookie`}, esté donde esté. La aserción `{"parameters": {"no": "una lista"}} == []` ya no está.
   - F-02: la métrica nueva coincide con `voice/nfr-design/observability-design.md:62`.
   - F-03: ver el punto 2.
   - F-04: el rojo de la ronda 2 está pegado literal y completo. Los de la ronda 1 dicen que están resumidos y que el revisor los repitió.
   - F-05: `EXCLUIDOS` queda en cuatro nombres.
   - F-06: `metrics.py:80-82` rechaza las etiquetas repetidas.
   - F-07: la rama está rebasada.
2. **F-03 (P-T17-13), valor por valor.**
   - **Pegado:**
     - `limits.exceeded`: BR2.3 (`rules.md:59`).
     - Los siete 409, en el mismo orden: BR2.7 (`rules.md:95`) y la tabla de `functional-spec.md:257-267`. Una sesión consolidada responde `session.finalized`, así que dejar fuera `session.consolidated` es correcto.
     - `session.not_owner` y `auth.forbidden`: BR10.1 (`rules.md:479`).
   - **Importación:**
     - `import.invalid_type`: BR7.1.
     - `limits.exceeded`: BR7.2.
     - `import.invalid_transcript`: BR7.3 y BR7.4.
     - `import.profile_mismatch`, `profile.not_approved` y `profile.transfer_not_authorized`: BR7.5.
     - Todos coinciden también con NFR10.14 (`security-requirements.md:87`).
   - **Excluidos, con razón:** `session.not_paused` y `session.not_finalized` son de la reanudación y del modo final. Un pegado en pausa responde 202, así que `session.paused` tampoco sale. `auth.invalid_credentials` y `auth.too_many_attempts` solo salen del login.
   - **Genéricos:** `auth.unauthenticated`, `auth.csrf`, `validation.invalid_request`, `system.internal` y `system.unavailable` son los que pidió la ronda 1. C1 no declara 422 en `/transcript`, pero una petición mal formada puede producirlo.
   - No encontré valores inventados ni faltantes, y todos están en el catálogo.
3. **P-T17-14 (`cookie` entra, `header` queda exento).** §4.12 dice «parámetros en ASCII `snake_case`» sin excepción. La exención de las cabeceras ya se aceptó en la ronda 1 (P-T17-11). Ahora solo exime a `in: header`; en C1 eso es únicamente `X-CSRF-Token`. Que el `name` de una cabecera siga el protocolo y no `snake_case` es razonable, y no exime de más. Lo comprobé con una sonda: `csrfToken` pasa y `sessionCookie` en `securitySchemes` se informa. Con `cookie` la guardia cubre además el `apiKey` `veridicus_session` de `securitySchemes`, que es más estricto y no está documentado. Lo anoto como observación, no como hallazgo.
4. **P-T17-15.** `analyzer`, `vendor`, `fixtures` (8 directorios) y `tests` son necesarios, y el prefijo `.` también (`.venv` y `.mypy_cache` traen JSON). El prefijo `_` no hace falta (ver F-01 de abajo).
5. **SHA.** Los doce SHA vigentes están en `git log feat/b1-contratos..HEAD`, y la tabla de la línea 294 de la bitácora da su equivalencia con los reescritos. La única mención reescrita sin marca en su línea está en la línea 194 (ver F-02 de abajo).
6. **Nada aflojado.**
   - **Código:** el diff `bbeb73c..fda2a4f` solo suma reglas en `metrics.py`, amplía `naming.py` y quita exenciones de `_contratos.py`. `datetime_format.py` no cambia.
   - **Contratos:** solo cambian dos archivos de métricas. `session-lifecycle` reduce sus valores (más estricto) y `voice` suma una métrica.
   - **Pruebas:** al unir pruebas, los cuerpos se movieron enteros. Siguen siendo 7, 6 y 7. Las pruebas que la bitácora cita para BR8.1 y BR8.2 (P-T18-10) existen con el mismo nombre.

## Hallazgos
### F-01 · AMARILLO · `contracts/src/veridicus_contracts/checks/_contratos.py:18` · El prefijo `_` es una exención de más
`find … -name "_*"` no encuentra ningún YAML ni JSON que empiece por `_`. `__pycache__` solo tiene `.pyc`, que `SUFIJOS` ya deja fuera. Hoy esa exención no protege nada. El día que aparezca un `_borrador.yaml`, pasaría sin revisarse. La bitácora (P-T17-15) dice que «no dejé ninguna» exención evitable.

### F-02 · AMARILLO · `docs/loop/bitacoras/U01-T17.md:194` · SHA reescrito sin marca en su línea
`e33c2d6` aparece solo. La aclaración general está en la línea 191 y la tabla de la 294 lo cubre, pero la línea 194 no dice que es un SHA reescrito.

## Tareas candidatas (defectos reales fuera de alcance)
- CA-2 sigue en unos 250 s con `timeout 300`, con un margen del 15 %. Es la misma candidata de la ronda 1: repartir la suite o subir el tiempo es decisión humana.
- `queues/results.v2.yaml:89`, el `pattern` de `code`: el codificador confirma que T18b lo dejó con un solo punto. Ya no hace falta como candidata, salvo que se quiera que `naming.py` compruebe también los `pattern`.

---

No escribí ningún archivo en el repositorio. La copia del rojo está en `/tmp/claude-1000/-workspace/87e67c60-aa1c-4b11-8928-da89d2e300bd/scratchpad/rojo-r2`. Las salidas de CA-2 y CA-3 están en `/tmp/claude-1000/-workspace/87e67c60-aa1c-4b11-8928-da89d2e300bd/tasks/bgikmhtt2.output` y `/tmp/claude-1000/-workspace/87e67c60-aa1c-4b11-8928-da89d2e300bd/tasks/bpsao38ad.output`.

```
VEREDICTO: VERDE
AMARILLO|contracts/src/veridicus_contracts/checks/_contratos.py:18|El prefijo _ exime sin necesidad (no hay YAML ni JSON con _; __pycache__ solo tiene .pyc)
AMARILLO|docs/loop/bitacoras/U01-T17.md:194|SHA reescrito e33c2d6 sin marca en su propia línea
INFORME: docs/loop/revisiones/U01-T17/ronda-2.md
```
