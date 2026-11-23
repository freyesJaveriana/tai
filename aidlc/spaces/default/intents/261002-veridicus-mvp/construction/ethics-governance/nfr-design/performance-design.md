# Diseño de rendimiento — U13 ethics-governance

**Revisión 1 (2026-11-22): primera pasada.** Todo es nuevo. Las precisiones están en la tabla NFRD-U13-xx de
`security-design.md` §17.

**Insumos.** `nfr-requirements/performance-requirements.md` (performance-requirements: NFR2.1,
NFR3.1–NFR3.8 y el presupuesto de NFR3.1), `scalability-requirements.md` (scalability-requirements, §1 y
NFR3.9–NFR3.12) y `tech-stack-decisions.md` (tech-stack-decisions, D2, D3, D5 y D8) de esta unidad; F1,
F3, F4, F7, F9, F10 y §6 de `functional-design/functional-spec.md` (functional-spec); C1, C23, C24 y C25
de `inception/contract-design/contract-summary.md` (contract-summary); `turn_texts` con `yield_per`
(NFRD-U4-12) y la carga de M4 del NFR Design de U4.

U13 no llama a modelos. Su trabajo es síncrono y corto: calcular un estado, insertar una fila, comparar una
nota con los turnos y registrar un acceso; a eso se suman el `Job` y el comando, que lanza el humano. No hay
caché: lo único que se guarda en memoria es el texto inmutable de las reglas de uso.

## 1. `POST /problem-reports` (NFR3.1)

| Tramo | Presupuesto con la sesión máxima y la nota máxima | Diseño |
|---|---|---|
| `GuardedRoute` hasta el manejador | ≤ 15 ms | Pasos 1–7 de U3 por clave primaria; cuerpo ≤ 32 KiB |
| Resolvedor de sugerencia y de dueño | ≤ 15 ms | Dos `SELECT` por clave primaria |
| Lectura de 2 000 turnos (250 000 caracteres) | ≤ 150 ms | `turn_texts` con `yield_per(200)` y el índice `turn (session_id, n)` (NFRD-U4-11); solo la columna del texto |
| Normalización y búsqueda | ≤ 200 ms | §1.1 |
| Inserción y `COMMIT` | ≤ 50 ms | Una fila; índices de NFR3.10 |
| **Total** | **p95 ≤ 500 ms** | Típica (100 turnos): ≤ 150 ms; sin sesión: ≤ 100 ms (sin lectura ni búsqueda) |

### 1.1 La búsqueda

- La nota se parte una vez (`str.split()`) y sus secuencias de 8 palabras van a un `frozenset` de tuplas:
  ≤ 1 000 elementos con 2 000 caracteres.
- Cada turno se parte y se recorre con una ventana de 8 palabras; cada paso arma una tupla de 8 referencias
  y consulta el conjunto. Con 250 000 caracteres son ≈ 40 000 ventanas: decenas de milisegundos en CPython.
- Corte temprano: la primera coincidencia devuelve `True` y cierra el iterador (el cursor del servidor se
  cierra con él).
- Si la medición pasa los 200 ms, el plan es el de D2: palabras convertidas a enteros con un diccionario
  de la nota y ventana con *hash* rodante. El umbral no cambia.

```text
# Ilustrativo: el corte temprano y lo que retiene
grams = frozenset(windows(note.split(), 8))
for text in turn_texts(session_id):          # iterador; un turno a la vez
    if any(w in grams for w in windows(text.split(), 8)):
        return True
return False
```

## 2. Consola (NFR3.2, NFR3.8)

- **Comparación local.** `findLiteralOverlap` arma un `Set` de claves de 8 palabras unidas con un espacio (no
  aparecen espacios dentro de una palabra tras partir) y recorre los turnos que ya tiene TanStack Query. Corre
  en trozos de 250 turnos con una cesión al bucle de eventos entre trozos (`await` de una tarea vacía), así
  ninguna tarea del hilo principal pasa de 200 ms aunque la sesión sea la máxima. Presupuesto: típica
  ≤ 30 ms; máxima ≤ 150 ms.
- **Contador de la nota.** `Array.from(nota).length` en cada `input`, sin recorrer los turnos: la comparación
  solo corre al pulsar «Enviar».
- **Avisos que no bloquean.** El panel y el recordatorio no son modales y no atrapan el foco (BR8.2). El
  recordatorio usa un temporizador con el `Clock` inyectable de la consola; al cerrarlo se reprograma y al
  salir de M4 se cancela. 0 peticiones (BR6.3).
- **Reconocimiento.** Tras «Más tarde», la franja es un componente estático; la lista de sesiones y M4 no
  esperan nada de U13.
- Medición en nivel 3 con Playwright: `performance.now()` desde «Enviar» hasta el aviso o la petición, y
  `PerformanceObserver` de `longtask` (0 tareas > 200 ms); con el recordatorio visible y el panel abierto,
  escribir en la entrada y pulsar una acción de una tarjeta en ≤ 100 ms y sin cambio de foco. Vitest con
  reloj simulado para el desvío del recordatorio (≤ 1 s).

## 3. Rutas cortas (NFR3.3, NFR3.4, NFR3.5)

| Operación | Consultas | Índice | Presupuesto |
|---|---|---|---|
| Estado en `GET /auth/me` (BR1.2) | Solo para `analista`: `SELECT text_version, at FROM analyst_acknowledgement WHERE actor_user_id = :u ORDER BY at DESC LIMIT 1`; el estado se calcula en memoria con el reloj y la versión cargada | `(actor_user_id, at DESC)` | ≤ 20 ms sobre el p95 de `/auth/me` con 1 000 filas del usuario |
| `POST /acknowledgements` | Comparación de versión en memoria e `INSERT` | — | p95 ≤ 150 ms |
| `PATCH /sessions/{id}/retention` | `change_cursor.bump`, `retention_of`, `set_retention`, `INSERT retention_change` | Clave primaria de la sesión | p95 ≤ 200 ms |
| Validación del plazo al crear o importar | Función pura sin E/S | — | ≤ 5 ms |
| `AccessLog.record` | `current_setting`, `set_config`, `INSERT`, `set_config` (§2 de `reliability-design.md`) | Los de `access_log_entry` (NFR3.10) | p95 ≤ 20 ms, también con 150 000 filas |

`admin` e `investigador` no hacen la consulta del reconocimiento (BR1.7): su estado no se calcula.

## 4. `Job` de retención (NFR3.6, NFR3.11)

- **Una conexión y un cliente de Redis** para toda la ejecución; ningún *pool*.
- **Selección** por los índices de NFRD-U4-11: devuelve solo IDs y plazos efectivos, en orden de vencimiento.
- **Borrado de la sesión máxima** (2 000 turnos, 250 sugerencias, 7 500 decisiones, 3 versiones, 1
  exportación, 10 audios, 2 reportes de problemas, 3 cambios de plazo): `DELETE … RETURNING` por tabla en
  cada unidad, cada uno dentro de los 2 s de `statement_timeout`, más ≤ 14 archivos de ≤ 5 s cada uno en el
  peor caso. Objetivo: p95 ≤ 10 s.
- **Memoria.** El proceso solo retiene los recibos de la sesión en curso (≈ 20 000 UUID en la sesión
  máxima, unos pocos MiB) y los suelta tras el `COMMIT`. Objetivo: pico ≤ 256 MiB con `psutil`.
- **Acta.** Con ≈ 20 000 UUID, `deleted_ids` ocupa ≈ 0,8 MiB en `jsonb`, dentro de 1 MiB (NFR3.9). Si la
  medición lo pasa, es un hallazgo que se corrige por PR (por ejemplo, UUID en binario dentro de la lista),
  nunca un umbral que se sube.
- **`--dry-run`.** Una transacción de solo lectura; por candidata, los `count_session` de cada unidad, que
  son `SELECT count(*)` por índice de sesión. Objetivo: 500 sesiones (200 vencidas) en ≤ 60 s.
- **Escala lineal.** 50 sesiones típicas en ≤ 5 min; la duración crece con las candidatas.
  `activeDeadlineSeconds` se ajusta por PR con la medición de 500 típicas (NFR3.11, NFR-U13-07).

## 5. Comando de consulta (NFR3.7)

| Subcomando | Consulta | Índice |
|---|---|---|
| `access-log --session <id>` | `WHERE resource_id = :id ORDER BY at DESC LIMIT n + 1` (los accesos registrados con el ID de la sesión; el registro no guarda a qué sesión pertenece una sugerencia, porque no tiene claves foráneas) | `(resource_id, at)` |
| `access-log --user <id>` | `WHERE actor_user_id = :u ORDER BY at DESC LIMIT n + 1` | `(actor_user_id, at)` |
| `access-log` sin filtro | `ORDER BY at DESC LIMIT n + 1` | `(at DESC)` (NFRD-U13-12) |
| `problem-reports [--session]` | Por sesión o por hora | `(session_id)`; `(reported_at DESC)` (NFRD-U13-12) |
| `retention-acts [--session \| --job-run]` | Por sesión borrada, por ejecución o por hora | `(deleted_session_id)`; `(job_run_id)`; `(executed_at DESC)` (NFRD-U13-12) |

- Cursor del servidor con `yield_per(1000)` y salida línea a línea: la memoria no crece con `--limit`.
  Objetivo: ≤ 2 s con `--session` y ≤ 5 s con `--limit 10000` sobre 150 000 filas; ≤ 64 MiB más en el
  contenedor.
- `--format json` escribe una línea JSON por fila; `text`, columnas fijas.

## 6. CPU primero (NFR2.1)

Las pruebas de U13 de los niveles 0 y 1 corren en un contenedor sin GPU, con `pytest-socket` que solo deja
PostgreSQL y Redis de la prueba. U13 no carga modelos.

## 7. Cómo se mide

| Medición | Comando | Umbral |
|---|---|---|
| NFR3.1, NFR3.3–NFR3.7, NFR3.9–NFR3.12 | `uv run --directory services/session-api pytest -m perf tests/ethics_governance` (50 repeticiones salvo NFR3.6, mediana y p95; `psutil` y `tracemalloc` para la memoria) | Los de performance-requirements y scalability-requirements |
| NFR3.2, NFR3.8 | `npx --prefix frontend playwright test e2e/ethics-governance.spec.ts` | ≤ 30 ms y ≤ 150 ms; 0 tareas > 200 ms; ≤ 100 ms con avisos |
| Desvío del recordatorio | `npm --prefix frontend run test -- ethics-governance` | ≤ 1 s con reloj simulado; 0 peticiones |

Una prueba de rendimiento inestable se arregla o se pone en cuarentena con un *issue*; nunca se reintenta ni
se baja su umbral (`team.md`).
