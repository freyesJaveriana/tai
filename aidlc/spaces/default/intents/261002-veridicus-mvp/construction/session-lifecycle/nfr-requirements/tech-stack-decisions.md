# Decisiones de pila — U6 session-lifecycle

**Insumos.** Flujos F1–F6 de `functional-design/functional-spec.md` (functional-spec) y reglas de
`functional-design/rules.md` (rules); FR2.4, FR3.3, FR8 y NFR2, NFR13 y NFR14 de
`inception/requirements-analysis/requirements.md` (requirements); C1, C2 y C4 de
`inception/contract-design/contract-summary.md` (contract-summary); respuestas P1 y P2 de
`nfr-requirements-questions.md`; `security-requirements.md`; las decisiones de pila ya aprobadas de U3
(base de `session-api`) y de U4 (trabajador de `session-api`, colas, sondeo con TanStack Query,
accesibilidad con axe).

U6 no añade servicios ni dependencias de ejecución. Lo que ya fijan `team.md`, U3 y U4 no se repite:
Python 3.12, FastAPI, Pydantic v2 y `pydantic-settings`, SQLAlchemy 2 con psycopg 3 y
`statement_timeout`, Alembic en un `Job`, `redis-py`, el trabajador de `session-api` (D11 de U4), reloj
inyectable (D12 de U3), `pytest` + Hypothesis, mypy estricto, Ruff, import-linter, React con TypeScript
estricto, TanStack Query, Vitest, Playwright y `@axe-core/playwright`.

## 1. Decisiones

| # | Decisión | Elección | Alternativas descartadas | Por qué | Requisitos |
|---|---|---|---|---|---|
| D1 | Escritura del latido | `UPDATE … SET last_heartbeat_at = now() WHERE id = :id AND status = 'open' AND (last_heartbeat_at IS NULL OR last_heartbeat_at <= now() − interval '15 s')`, solo para el dueño, dentro del sondeo de U4 y de `POST /heartbeat` | Escribir en cada sondeo; guardar el latido en Redis con `EXPIRE` | Con el sondeo de 2 s, escribir siempre son 30 escrituras por minuto y sesión; con la condición, ≤ 4. A cambio, la suspensión puede llegar desde 165 s tras el último sondeo real en vez de 180 s (NFR3.8). Redis añadiría una segunda fuente de verdad del estado de la sesión | NFR3.3, NFR3.8, NFR8.6 |
| D2 | Revisión de suspensión | Una tarea más del trabajador de `session-api`, cada 30 s: `UPDATE … RETURNING` condicional e inserción de `SessionStatusChange` (`actor_kind = system`) en la misma transacción; índice parcial `WHERE status = 'open'` sobre `last_heartbeat_at` | Temporizador por sesión en memoria; disparador o `pg_cron` en la base | Sin estado e idempotente: se puede reiniciar o duplicar sin efectos dobles; `pg_cron` exigiría una extensión más en CloudNativePG | NFR3.7, NFR3.9, NFR8.9, NFR10.12 |
| D3 | Reloj del latido y de la revisión | `now()` de PostgreSQL en ambas sentencias; en las pruebas, el reloj se controla con una función de hora inyectada en la sesión de base de datos | Hora de cada pod | Pods con relojes distintos no adelantan ni atrasan la suspensión | NFR3.7 |
| D4 | Transacción del pegado | Bloqueo de la fila de la sesión (`SELECT … FOR UPDATE`), inserción de todos los turnos con un solo `INSERT … VALUES` de varias filas, `TranscriptPaste` y plazos de NFR3.10 en la misma transacción; restricción única `(session_id, client_request_id)` | Un `INSERT` por turno; una transacción por turno | Una sola ida y vuelta mantiene el peor caso bajo 2 s y el lote es todo o nada | NFR3.1, NFR3.10, NFR8.10 |
| D5 | Regla de división compartida | El archivo versionado `transcript-split.v1.json` (se propone en `contracts/fixtures/`, carpeta de U1) guarda los límites de NFR8.3, las etiquetas del entrevistador y los ejemplos de entrada y salida de BR2.1; la implementación de Python (`domain/` de InterviewSession) y la de TypeScript (consola) se prueban contra los mismos ejemplos | Pedir la vista previa al servidor; dos especificaciones sin ejemplos comunes | Respuesta inmediata en la consola (decisión ya tomada en Functional Design) sin que las dos implementaciones discrepen; un cambio de etiquetas o límites entra por PR y cambia ambas a la vez | NFR1.2, NFR3.6, NFR8.3, NFR13.2 |
| D6 | Comparación sin mayúsculas ni tildes | Python: `unicodedata.normalize("NFD")`, quitar marcas combinantes y `casefold()`; TypeScript: `normalize("NFD")`, quitar `\p{M}` y `toLocaleLowerCase("es")`. Los ejemplos del archivo de D5 incluyen «ANALISTA», «Analísta» y «analista» | Comparación exacta; listas con todas las variantes | BR2.2 exige ignorar mayúsculas y tildes, igual en ambos lados | NFR13.2 |
| D7 | Publicación del pegado | Tras confirmar, canalización `MULTI`/`EXEC` de `redis-py` con todos los `XADD` de testimonio en orden, *timeout* de 0,5 s y un reintento; el reenvío idempotente vuelve a publicar lo pendiente | Una tabla *outbox* con su publicador; publicar dentro de la transacción | Ordenado y casi todo o nada sin una tabla más; el *outbox* sería más robusto pero no cabe en una unidad de tamaño M y el reenvío cubre el caso | NFR10.11, NFR8.10 |
| D8 | Inmutabilidad de versiones y pasajes | Permisos de la base: el rol de la aplicación sin `UPDATE`/`DELETE` sobre pasajes ni `DELETE` sobre versiones (columna de estado solo para el indexador, como U4); restricciones únicas `(scenario_id, version_number)` y `source_sha256`; el OpenAPI sin rutas de modificación | Solo validación en la aplicación | La base hace cumplir FR2.4 aunque falle el código | NFR10.6, NFR11.1, NFR8.12 |
| D9 | Lista de sesiones | Una consulta con `LEFT JOIN` a un agregado de sugerencias pendientes por sesión, ordenada por `created_at` descendente, sin paginación; el filtro «Solo las mías» se aplica en la consola (F3) | Consulta por fila; vista materializada | Con ≤ 500 sesiones cumple NFR3.2 sin otra pieza que mantener | NFR3.2, NFR8.5 |
| D10 | Pruebas de tiempo | Marca `perf` de `pytest` en nivel 1 (como U3 y U4) y `performance.now()` en Vitest para la vista previa; la corrida de 60 turnos (NFR3.11) se añade al arnés de nivel 2 de U4 | k6 o Locust | Pocas peticiones en proceso; la carga real la limita el juez | NFR3.1–NFR3.12 |

## 2. Configuración (prefijo `VERIDICUS_`)

| Ajuste | Valor por defecto | Validación al arrancar | Proceso |
|---|---|---|---|
| `VERIDICUS_HEARTBEAT_TIMEOUT_SECONDS` | 180 | Entero entre 60 y 1 800; ≥ 4 × 15 s (sondeo lento de U4) | trabajador de `session-api` |
| `VERIDICUS_SUSPENSION_SWEEP_SECONDS` | 30 | Entero entre 5 y la mitad de *T* | trabajador de `session-api` |
| `VERIDICUS_HEARTBEAT_WRITE_MIN_SECONDS` | 15 | Entero entre 1 y la cuarta parte de *T* | API de `session-api` |

Los límites del pegado y las etiquetas del entrevistador **no** son variables de entorno: viven en el
archivo de D5 para que la consola y el servidor usen siempre los mismos (precisión en
`security-requirements.md` §6). Los *timeouts* de PostgreSQL y Redis son los de U4 (NFR10.9).

## 3. Calidad del código (NFR2, NFR13, NFR14)

| ID | Requisito | Criterio medible |
|---|---|---|
| NFR2.1 | Todo U6 se prueba en CPU sin modelos reales en los niveles 0 y 1. | El juez y los *embeddings* son los *fakes* de U4; PostgreSQL y Redis son reales en contenedor; ninguna prueba de los niveles 0 y 1 descarga un modelo ni exige GPU. |
| NFR2.2 | Las metas de U6 se cumplen en el perfil CPU. | NFR3.11, NFR4.1 (nivel 2) y NFR9.1 se miden con `values-cpu.yaml`; el perfil GPU es opcional. |
| NFR13.1 | Cobertura de líneas. | ≥ 80 % en `services/session-api` y en `frontend` con el código de U6 incluido, medido en la CI y bloqueante. U6 no tiene módulos guardia de la lista de team-practices; los turnos pegados pasan por los de U4, que mantienen su 100 % de ramas. |
| NFR13.2 | La división es la misma en la consola y en el servidor. | Las suites de `pytest` y de Vitest leen el archivo de D5 y pasan el 100 % de sus ejemplos (incluidos E4, E5 y los de D6); además, una prueba de propiedad con Hypothesis comprueba que dividir el texto armado a partir de turnos válidos devuelve esos mismos turnos. Una diferencia entre ambas suites rompe la CI. |
| NFR14.1 | Textos visibles en español y del catálogo. | M1, el diálogo de pegado, el de reanudación, el historial lateral y TurnItem solo usan cadenas del catálogo de U1 (incluido «Se detectó una interrupción inesperada en la sesión. ¿Desea reanudar desde el último turno registrado?»); fechas en hora de Colombia (`America/Bogota`); prueba de nivel 0 que falla con un literal visible fuera del catálogo. |
| NFR14.2 | Accesibilidad de las pantallas de U6 (BR6.1, BR5.1). | `@axe-core/playwright` en nivel 3 sobre M1 (con y sin sesiones), el diálogo de pegado (vista previa y error), el de reanudación y el historial lateral: 0 violaciones `serious` o `critical`. Cada flujo (pegar y confirmar, cancelar con Escape, reanudar, «Más tarde») se completa solo con teclado en Playwright. «Suspendida» y los demás estados llevan icono y texto (prueba Vitest que falla si un estado solo cambia de color). La región `aria-live` anuncia cada cambio de etapa del turno una sola vez (Vitest). |

## 4. Dependencias nuevas de U6

Ninguna de ejecución. `session-api` y `frontend` ya tienen todo por U3 y U4; el archivo de D5 es un
*fixture* versionado, no un paquete.

## 5. Comandos de verificación (AUTONOMIA-02)

| Qué verifica | Comando | Umbral |
|---|---|---|
| Unitarias, contratos, OpenAPI y configuración (nivel 0) | `uv run --directory services/session-api pytest -m "not integration and not perf"` | Verde (NFR10.6, NFR10.10, NFR3.10, NFR8.3, NFR13.2, NFR12.1) |
| Integración (nivel 1) | `uv run --directory services/session-api pytest -m integration` | Verde (NFR8.8–NFR8.12, NFR10.1–NFR10.5, NFR10.7, NFR10.11, NFR10.12, NFR11.1, NFR11.2, NFR4.1 con el *fake*) |
| Rendimiento en proceso | `uv run --directory services/session-api pytest -m perf` | NFR3.1–NFR3.5, NFR3.9 |
| Consola | `npm --prefix frontend run test -- --coverage` y `npm --prefix frontend run typecheck` | Verde; ≥ 80 % de líneas; NFR3.6, NFR13.2, NFR14 |
| E2E y accesibilidad (nivel 3) | `npx --prefix frontend playwright test e2e/session-lifecycle.spec.ts` | NFR3.12, NFR10.8, NFR14.2 |
| Equivalencia pegado/escrito (nivel 2, fuera de la CI) | `uv run --directory evaluation python -m golden.run --profile cpu --paste-parity --report out/level2-paste.json` | NFR4.1: 100 % de coincidencia |
| Pegado de 60 turnos (nivel 2, a demanda) | `uv run --directory evaluation python -m golden.paste_max --turns 60 --profile cpu --report out/paste60.json` | NFR3.11: 0 `turn.error.timeout` |
| Tipos, *lint* y fronteras | `mypy --strict`, `ruff check`, `lint-imports` en `services/session-api` | 0 errores |

## 6. Riesgos

| Riesgo | Mitigación |
|---|---|
| El pegado de 60 turnos llega al tope de 3 600 s sin margen si el juez va al p95 de 60 s | NFR3.11 lo mide antes de cada entrega; si falla, se baja el límite por PR o se usa el perfil GPU, nunca se sube el tope en silencio |
| Las dos implementaciones de la división se separan con el tiempo | Archivo de ejemplos único y CI que corre ambas suites contra él (NFR13.2) |
| La publicación falla tras confirmar y el navegador no reenvía | `503` explícito al navegador, reenvío idempotente y, en el peor caso, el plazo de U4 cierra los turnos en `error` con reintento manual (NFR10.11) |
| La escritura acotada del latido adelanta la suspensión hasta 15 s | 165 s sigue muy por encima del temporizador de una pestaña en segundo plano; el valor es configuración |
| Las líneas del entrevistador cambian lo que ve el juez (turnos previos) y la equivalencia con ellas no es exacta | La equivalencia se exige sin esas líneas y con ellas se mide y se reporta (NFR4.1) |
