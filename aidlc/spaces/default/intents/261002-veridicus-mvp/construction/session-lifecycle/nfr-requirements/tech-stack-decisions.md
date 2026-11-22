# Decisiones de pila — U6 session-lifecycle

**Revisión 2 (2026-11-22).** Segunda pasada por el cambio 01 (DT27), la adenda 02 y el Functional Design
revisión 2 de U6. Sustituye a la revisión 1 del 2026-10-03.
- **IDs.** Las decisiones que siguen conservan su número; D8 queda «Retirado»; las nuevas son D11–D13.
- **Revisión 1:** D3 cierra R-02 de `reviews/review-01.md` (el reloj controlado ya está definido).

**Insumos.**
- Flujos F2–F9 de `functional-design/functional-spec.md` (functional-spec, revisión 2) y reglas de
  `functional-design/rules.md` (rules).
- FR3.3, FR3.6, FR8, NFR2, NFR13 y NFR14 de `inception/requirements-analysis/requirements.md`
  (requirements).
- C1, C2, C6, C11 y C25 de `inception/contract-design/contract-summary.md` (contract-summary).
- Las decisiones de pila de U1 (cargador seguro, `limits.load`, `contracts/ts/` con ajv), U3 (base de
  `session-api`, reloj inyectable) y U4 (trabajador de `session-api`, colas, sondeo, cancelación).

U6 no añade servicios ni dependencias de ejecución. Lo que ya fijan `team.md`, U1, U3 y U4 no se repite:
Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2 con psycopg 3 y `statement_timeout`, Alembic en un `Job`,
`redis-py`, el trabajador de `session-api`, `veridicus_contracts`, `pytest` + Hypothesis, mypy estricto,
Ruff, import-linter, React con TypeScript estricto, TanStack Query, Vitest, Playwright y
`@axe-core/playwright`.

## 1. Decisiones

| # | Estado | Decisión | Elección | Alternativas descartadas | Por qué | Requisitos |
|---|---|---|---|---|---|---|
| D1 | cambia | Escritura del latido | `UPDATE … SET last_heartbeat_at = :now WHERE id = (SELECT id FROM … WHERE id = :id AND status = 'open' AND (last_heartbeat_at IS NULL OR last_heartbeat_at <= :now − heartbeat_write_min_s) FOR UPDATE SKIP LOCKED)`, solo para el dueño, dentro del sondeo de U4 y de `POST /heartbeat`; no sube `change_cursor` | Escribir en cada sondeo; latido en Redis con `EXPIRE`; esperar el bloqueo | Con el sondeo de 2 s, escribir siempre son 30 escrituras por minuto y sesión; con la condición, ≤ 4. `SKIP LOCKED` evita que el sondeo espere a una escritura que retiene la fila (NFR3.3); un latido omitido no importa con *T* = 180 s. Redis sería una segunda fuente de verdad del estado | NFR3.3, NFR3.8, NFR8.6 |
| D2 | cambia | Revisión de suspensión | Tarea del trabajador de `session-api` cada `session_sweep_interval_s`: selección de las `open` vencidas con `FOR UPDATE SKIP LOCKED`, `change_cursor.bump`, `UPDATE` a `suspended` e inserción de `SessionStatusChange` con `session-supervisor`, en una transacción; índice parcial `WHERE status = 'open'` sobre `coalesce(last_heartbeat_at, created_at)` | Temporizador por sesión en memoria; disparador o `pg_cron` | Sin estado e idempotente; no compite con las escrituras del usuario; `pg_cron` exigiría otra extensión en CloudNativePG | NFR3.7, NFR3.9, NFR8.9, NFR10.12 |
| D3 | cambia | Reloj del latido y de la revisión | Las funciones del repositorio reciben `now: datetime \| None`; con `None` la sentencia usa `now()` de PostgreSQL (producción) y las pruebas pasan una hora explícita desde el reloj inyectable de U3. El parámetro nunca llega desde la API | `now()` fijo; hora de cada pod | Pods con relojes distintos no adelantan ni atrasan la suspensión, y las pruebas controlan los bordes (cierra R-02) | NFR3.7, NFR3.8, NFR8.9 |
| D4 | cambia | Transacción del pegado y de la importación | Bloqueo de la fila de la sesión (pegado) y `INSERT … VALUES` de varias filas en lotes de 500 turnos, con `TranscriptPaste` y la corrida (pegado) o la sesión, el consentimiento y el estado inicial (importación) en la misma transacción; restricción única `(session_id, client_request_id)` | Un `INSERT` por turno; una transacción por turno | Pocas idas y vueltas: el peor caso queda bajo 2,5 s y 3 s, todo o nada | NFR3.1, NFR3.13, NFR8.10, NFR10.15 |
| D5 | cambia | Regla de división compartida | `contracts/transcript/speaker-markers.v1.yaml` (FD-U6-08) con las marcas, los alias y los ejemplos versionados; las cifras de `contracts/limits.v1.yaml`. Python (`domain/` de InterviewSession) y TypeScript (consola, con `contracts/ts/`) se prueban contra los mismos ejemplos | Pedir la vista previa al servidor; dos especificaciones sin ejemplos comunes | Respuesta inmediata en la consola sin que las dos implementaciones discrepen; todo cambio entra por PR | NFR1.2, NFR3.6, NFR8.3, NFR13.2 |
| D6 | se mantiene | Comparación sin mayúsculas ni tildes | Python: `unicodedata.normalize("NFD")`, quitar marcas combinantes y `casefold()`; TypeScript: `normalize("NFD")`, quitar `\p{M}` y `toLocaleLowerCase("es")`. Los ejemplos incluyen «ENTREVISTADOR», «Entrevistádor» y «entrevistador» (E15) | Comparación exacta | BR2.1 exige ignorar mayúsculas y tildes, igual en los dos lados | NFR13.2 |
| D7 | cambia | Publicación de una corrida de U6 | Tras confirmar, un `XADD` por corrida a `veridicus:runs` con la tubería de U4, *timeout* de 0,5 s y sin reintento; si falla, `202` y cierre por plazo (NFR-U6-10) | Tabla *outbox*; publicar dentro de la transacción | Lo decidió el Functional Design (BR2.5, sin *outbox*); la ingesta idempotente de U4 absorbe una entrega doble | NFR10.11 |
| D8 | Retirado | Inmutabilidad de versiones y pasajes | Sale US1.2 (cambio 01) | — | — | — |
| D9 | cambia | Lista de sesiones | Una consulta con `LEFT JOIN` al consentimiento (retirada) y a `pending_counts` por lotes de C11 (NFR-U6-04), ordenada por `created_at` descendente, sin paginar en el servidor; filtro por estado en la consulta y «Solo las mías» y paginación de 25 en la consola | Consulta por fila; vista materializada; paginación en el servidor | Con ≤ 500 sesiones cumple NFR3.2 sin otra pieza; NFR8 no lo exige | NFR3.2, NFR8.5 |
| D10 | cambia | Pruebas de tiempo | Marca `perf` de `pytest` en nivel 1 y `performance.now()` en Vitest; la medición del modo final (NFR3.17) es un script de `evaluation/` que lanza el humano | k6 o Locust | Pocas peticiones en proceso; la carga real la limita el analizador | NFR3.1–NFR3.17 |
| D11 | nuevo | Lectura del archivo importado | El cuerpo se lee por bloques con tope y se guarda en memoria (sin `SpooledTemporaryFile` a disco); `json.loads` de la biblioteca estándar sobre UTF-8 estricto, con `object_pairs_hook` que rechaza claves duplicadas y una comprobación de profundidad ≤ 32; validación con el registro de esquemas de `veridicus_contracts` (`iter_errors`, ordenados por posición) y mensajes de una tabla propia (ruta y regla → texto en español) | El `UploadFile` por defecto; YAML; mensajes del validador | El archivo nunca toca el disco (BR7.9); la consola y el servidor leen el mismo objeto; el texto del validador puede citar el testimonio | NFR10.13, NFR3.13 |
| D12 | nuevo | Validación del archivo en la consola | Un Web Worker lee el archivo, comprueba el tamaño antes de leerlo, lo analiza y lo valida con ajv de `contracts/ts/` (mismo esquema y mismos mensajes que el servidor) | Validar en el hilo principal; pedir la validación al servidor | La consola no se congela con 2 MiB (NFR3.14) y no envía nada antes de «Importar» (NFR1.2) | NFR3.14, NFR1.2, NFR13.2 |
| D13 | nuevo | Cancelación | El mecanismo de U4: cambio a `cancelled` en la transacción y `SET veridicus:run-cancelled:{run_id}` con TTL = plazo restante + `cancel_key_margin_s` tras confirmar y antes de responder; reintento en la reconexión | Mensaje de cancelación por cola; acceso del trabajador a la base | CD-06; el trabajador no tiene base (ADR-002) | NFR1.3, NFR3.16, NFR10.18 |

## 2. Configuración

Toda cifra sale de `contracts/limits.v1.yaml` (C25) con `limits.load`; una `VERIDICUS_LIMIT_<NOMBRE>` solo
puede bajarla y una que la sube impide arrancar (regla de `project.md`, U1).

| Cifra de C25 | Valor | Unidad | Comprobación extra al arrancar | Proceso |
|---|---|---|---|---|
| `import_file_max_bytes` | 2 097 152 | `bytes` | — | API y consola |
| `heartbeat_timeout_s` | 180 | `s` | ≥ 4 × `poll_interval_s` | Trabajador |
| `session_sweep_interval_s` (nueva) | 30 | `s` | ≤ `heartbeat_timeout_s` / 2 | Trabajador |
| `heartbeat_write_min_s` (nueva) | 15 | `s` | Entre 1 y `heartbeat_timeout_s` / 4 | API |

Usa además, sin fijarlas: `transcript_max_turns`, `transcript_max_chars`, `turn_max_chars`,
`poll_interval_s`, `poll_interval_active_s`, `cancel_key_margin_s` (U4) y `run_deadline_final_s` (U11).
Las marcas de hablante no son variables de entorno: viven en `speaker-markers.v1.yaml`. Los *timeouts* de
PostgreSQL y Redis son los de U4.

## 3. Calidad del código (NFR2, NFR13, NFR14)

| ID | Estado | Requisito | Criterio medible |
|---|---|---|---|
| NFR2.1 | cambia | Todo U6 se prueba en CPU sin modelos reales en los niveles 0 y 1. | El analizador es el *fake* de C17; PostgreSQL y Redis son reales en contenedor; ninguna prueba de los niveles 0 y 1 descarga un modelo, usa la red ni exige GPU |
| NFR2.2 | cambia | Las metas de U6 se cumplen en el perfil CPU. | NFR3.1–NFR3.16 se miden en la máquina de desarrollo; NFR3.17 corre con `comercial-piloto` y `todo-local` en CPU; el perfil GPU es opcional |
| NFR13.1 | cambia | Cobertura. | ≥ 80 % de líneas en `services/session-api` y en `frontend` con el código de U6, medido en la CI y bloqueante. **100 % de ramas** en la tabla de transiciones de la sesión (BR9.8) y en la decisión de cancelar y de admitir corridas tras la retirada (NFR1.3), porque protegen AUTONOMIA-04 y VE-10 |
| NFR13.2 | cambia | La división y la validación del archivo son las mismas en la consola y en el servidor. | Las suites de `pytest` y Vitest pasan el 100 % de los ejemplos de `speaker-markers.v1.yaml` (incluidos E4, E5, E15 y E17) y de los *fixtures* de importación de U6; una prueba de propiedad con Hypothesis comprueba que dividir el texto armado a partir de turnos válidos devuelve esos turnos. Una diferencia entre las dos suites rompe la CI |
| NFR14.1 | cambia | Textos visibles en español y del catálogo. | M1, M7, los diálogos, la franja, la barra de M4 y el historial lateral solo usan cadenas del catálogo de U1; fechas en hora de Colombia (`America/Bogota`); prueba de nivel 0 que falla con un literal visible fuera del catálogo |
| NFR14.2 | cambia | Accesibilidad de las pantallas de U6 (BR6.1, BR6.2). | `@axe-core/playwright` en nivel 3 sobre M1 (con y sin sesiones), M7 (inicial, error y vista previa), los diálogos de pegado, reanudación, terminar y retirada, la franja del modo final y el historial lateral: 0 violaciones `serious` o `critical`. Importar, confirmar el pegado, lanzar y relanzar el modo final y responder al aviso de reanudación se completan solo con teclado. Los botones deshabilitados usan `aria-disabled` con su motivo; ningún estado se distingue solo por color; `aria-live` solo anuncia lo agregado (Vitest) |

## 4. Dependencias nuevas de U6

Ninguna de ejecución. `session-api` y `frontend` ya tienen todo por U1, U3 y U4; `speaker-markers.v1.yaml`
y los *fixtures* de importación son archivos versionados, no paquetes.

## 5. Comandos de verificación (AUTONOMIA-02)

| Qué verifica | Comando | Umbral |
|---|---|---|
| Unitarias, contratos, OpenAPI y configuración (nivel 0) | `uv run --directory services/session-api pytest -m "not integration and not perf"` | Verde (NFR10.1, NFR10.6, NFR10.10, NFR10.14, NFR8.3, NFR13.2, NFR12.1) |
| Integración (nivel 1) | `uv run --directory services/session-api pytest -m integration` | Verde (NFR1.1, NFR1.3, NFR1.4, NFR4.1, NFR8.8–NFR8.11, NFR10.1–NFR10.7, NFR10.11–NFR10.18, NFR11.1–NFR11.3, NFR15.3, NFR15.5) |
| Rendimiento en proceso | `uv run --directory services/session-api pytest -m perf` | NFR3.1–NFR3.4, NFR3.9, NFR3.13, NFR3.15, NFR3.16 |
| Cobertura de ramas de los módulos guardia | `uv run --directory services/session-api pytest --cov --cov-branch --cov-fail-under=80` y el informe por módulo | 100 % de ramas en la tabla de transiciones y en la cancelación (NFR13.1) |
| Consola | `npm --prefix frontend run test -- --coverage` y `npm --prefix frontend run typecheck` | Verde; ≥ 80 % de líneas; NFR1.2, NFR3.6, NFR3.12, NFR3.14, NFR13.2, NFR14 |
| E2E y accesibilidad (nivel 3) | `npx --prefix frontend playwright test e2e/session-lifecycle.spec.ts` | NFR3.12, NFR10.8, NFR14.2 |
| Medición del modo final (a demanda, la lanza el humano) | `uv run --directory evaluation python -m session_lifecycle.final_run_max --profiles comercial-piloto,todo-local --report out/final-run-max.json` | NFR3.17: reporte con una sección por perfil; falla si falta una |
| Tipos, *lint* y fronteras | `mypy --strict`, `ruff check` y `lint-imports` en `services/session-api` | 0 errores |

## 6. Riesgos

| Riesgo | Mitigación |
|---|---|
| El modo final sobre 2 000 turnos con `todo-local` puede pasar de `run_deadline_final_s` de desarrollo | NFR3.17 lo mide antes de la demostración; termina en error con «Relanzar modo final», nunca en silencio |
| Las dos implementaciones de la división o de la validación se separan | Ejemplos y *fixtures* únicos y CI que corre las dos suites contra ellos (NFR13.2) |
| La publicación falla tras confirmar | `202`, `ERROR` en el log y cierre por plazo con reintento manual (NFR10.11) |
| El Ingress guarda en disco el cuerpo del pegado o del archivo | NFR-U6-06 lo pide a U2; la prueba de NFR10.13 vigila el disco del pod, y la verificación manual en el clúster revisa el Ingress |
| La escritura acotada del latido adelanta la suspensión hasta 15 s | 165 s sigue muy por encima del temporizador de una pestaña en segundo plano; la cifra está en C25 |
