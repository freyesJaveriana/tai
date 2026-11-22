# Diseño de rendimiento — U12 research-reports

**Revisión 1 (2026-11-22): primera pasada.** Todo es nuevo. Las precisiones están en la tabla NFRD-U12-xx de
`security-design.md` §14.

**Insumos.** `nfr-requirements/performance-requirements.md` (performance-requirements: NFR2.1, NFR3.1–NFR3.8
y el presupuesto de NFR3.2), `scalability-requirements.md` (scalability-requirements, §1) y
`tech-stack-decisions.md` (tech-stack-decisions, D1–D7) de esta unidad; F1–F4 y §6 de
`functional-design/functional-spec.md` (functional-spec); C1 y C19 de
`inception/contract-design/contract-summary.md` (contract-summary); pool, separación de procesos y
virtualización de la consola del NFR Design de U4 (`performance-design.md` §3, §5 y §6).

U12 no llama a modelos. Su trabajo es síncrono y acotado: leer y validar una subida, y leer filas inmutables.
No hay caché: las filas no cambian, pero el volumen es bajo y cada lectura cabe en su presupuesto sin ella.

## 1. Presupuesto de la subida (NFR3.1, NFR3.2, NFR3.3)

| Tramo | Presupuesto con el *fixture* máximo (8 MiB) | Diseño |
|---|---|---|
| T1 de `GuardedRoute` | ≤ 20 ms | Consultas por clave primaria de U3 |
| Lectura del cuerpo y SHA-256 | ≤ 0,5 s en la red local | Trozos de `request.stream()` al `MultipartParser`; `hashlib.sha256` incremental en el *callback*, sin segunda pasada |
| T2 (duplicado) | ≤ 10 ms | Índice único de `source_sha256` |
| Codificación y profundidad | ≤ 0,3 s | Decodificación del `bytearray`; expresión regular compilada que salta cadenas (DS4) |
| `json.loads` con *hooks* | ≤ 1,2 s | Analizador en C; los *hooks* solo actúan en flotantes, constantes y objetos |
| Esquema C19 | ≤ 4 s | Validador compilado al arrancar (D3); errores reducidos a `(path, rule)` |
| Coherencia, contraste y validez | ≤ 1 s | Funciones puras con búsquedas en `frozenset` y `dict` del catálogo |
| Armado de filas | ≤ 0,5 s | Tuplas por tabla hija; el documento se suelta al terminar |
| T3 (escritura) | ≤ 4,4 s, dentro de `research_report_write_timeout_s` (15 s) | `insert()` de SQLAlchemy Core con `insertmanyvalues` (lotes de 1 000 filas) |
| **Total** | **≤ 12 s (p95 de NFR3.2)** | — |

- **Rechazos tempranos (NFR3.3).** `413` por `Content-Length` sin leer nada; `413` al pasar el tope mientras
  se lee, en ≤ 1 s. `409` solo calcula el SHA-256 durante la lectura y hace T2. `json_depth` corta en el
  noveno nivel; `encoding` falla al decodificar, antes de analizar.
- **Típico (NFR3.1, ≈ 1 MiB) y peor caso estimado (NFR3.2, ≈ 3,3 MB).** Los mismos tramos, que escalan con
  el tamaño: ≈ 1,5 s y ≈ 5 s.
- **Si el esquema no cabe en su tramo**, se mide `fastjsonschema` en un PR aparte, sin cambiar el esquema ni
  el umbral (riesgo de tech-stack-decisions §6).

```text
# Ilustrativo: el orden y lo que retiene cada fase
autorizar_y_confirmar()                 # T1 de GuardedRoute
with hueco_de_subida(espera=5):         # bulkhead de 2
    buf, sha = leer_multipart(tope, plazo=read_timeout)
    if existe(sha): raise Duplicado     # T2
    filas = await to_thread(validar_y_armar, buf, catalogo)  # sin conexión
    del buf
    escribir_en_una_transaccion(filas)  # T3
```

## 2. La API sigue atendiendo durante una subida (NFR3.7, NFR3.10)

- La ruta es `async`. La lectura del cuerpo cede el bucle de eventos en cada trozo.
- La validación (pasos 3–7 de BR2.1) es CPU pura y corre en un hilo con `anyio.to_thread.run_sync`, con un
  `CapacityLimiter` propio de 2 (los mismos huecos). No ocupa el *threadpool* por defecto que usan las rutas
  síncronas de las demás unidades.
- La API y el trabajador de `session-api` son procesos distintos (D11 de U4), así que una subida no frena la
  ingesta ni el supervisor.
- **Contención del GIL.** El hilo de validación compite con las rutas por el intérprete. NFR3.10 lo mide en
  nivel 1: el p95 de `GET /sessions/{id}` con `since` no sube más de 200 ms con una subida máxima en curso.
  Si no se cumple, **plan B** por PR: la validación pasa a un `ProcessPoolExecutor` de 1 proceso
  (`forkserver`) que recibe los bytes y devuelve las filas; su memoria se suma a NFR3.8. El umbral no se
  cambia.

## 3. Lecturas (NFR3.4, NFR3.5, NFR3.6)

| Ruta | Consultas | Índice | Presupuesto |
|---|---|---|---|
| `GET /research-reports` | 1 `SELECT` de las columnas de `ResearchReportSummary` sobre `research_report`, sin tablas hijas, ordenado por `uploaded_at DESC`; 1 consulta a `UserDirectory` con los `uploaded_by` distintos para `uploaded_by_username` (FD-U12-05) | `research_report (uploaded_at DESC)` | p95 ≤ 500 ms con 1 000 reportes |
| `GET /research-reports/{id}` | 1 `SELECT` de la fila y 1 por tabla hija, en orden de `ordinal` | Claves primarias `(research_report_id, ordinal)` de las hijas | Típico ≤ 500 ms; peor caso (≈ 7 200 llamadas) ≤ 2 s |
| `GET /research-reports/compare` | Las dos filas en un `SELECT … WHERE research_report_id IN (:a, :b)`; las hijas de los dos en una consulta por tabla | Los mismos | ≤ 1 s típicos; ≤ 4 s con dos del peor caso |

- Cada sentencia cabe en el `statement_timeout` común de 2 s (NFRD-U12-07). El peor caso del detalle es una
  consulta de ≈ 7 200 filas angostas por índice, de decenas de milisegundos.
- La respuesta se serializa con `orjson`, como la carga completa de U4. Las filas llegan como tuplas de
  SQLAlchemy Core, sin objetos del ORM.
- En la comparación, BR7.2 se comprueba con las dos filas antes de leer las hijas: `404`, `409` o `422`
  salen sin leerlas.

## 4. Base de datos

- **Pool.** El de la API de U3 (5 + 5, `pool_timeout` 2 s). Una subida usa una conexión tres veces y por poco
  tiempo (`security-design.md` §3); ninguna queda retenida mientras se lee o se valida.
- **Inserción.** Una sola transacción T3: la fila padre y cada tabla hija con `insertmanyvalues` en lotes
  de 1 000. Las hijas llevan `ordinal` para devolver el orden del archivo sin ordenar en memoria.
- **Índices.** Únicos: `research_report (source_sha256)`. De lectura: `research_report (uploaded_at DESC)`.
  Las hijas, por su clave primaria compuesta. Sin más índices: cada índice cuenta en NFR3.11.

## 5. Recursos (NFR3.8)

| Copia en memoria | Tamaño con el *fixture* máximo | Cuándo se suelta |
|---|---|---|
| `bytearray` de la parte `file` | 8 MiB | Tras decodificar |
| `str` decodificado | ≈ 8 MiB (JSON ASCII) | Tras `json.loads` |
| Documento de Python | ≈ 120–180 MiB (≈ 15–20 × el JSON) | Tras armar las filas |
| Tuplas de filas | ≈ 20–40 MiB | Tras T3 |

- Pico estimado por subida ≈ 230 MiB en el peor reparto (cadena, documento y filas a la vez, porque el
  `bytearray` ya se soltó), dentro de los 256 MiB de NFR3.8; con dos huecos, ≈ 460 MiB dentro de los
  512 MiB. El margen es corto: si la medición lo supera, el primer ajuste es armar las filas de las llamadas
  por lotes mientras se recorre el documento. La prueba `perf` mide el RSS con `psutil` y el pico con `tracemalloc`; un pico mayor es un
  hallazgo que se corrige por PR, nunca un tope que se sube.
- El *bulkhead* de 2 huecos hace que la tercera subida simultánea no sume memoria (`scalability-design.md`
  §3).
- Infrastructure Design suma 512 MiB con el 20 % de margen de U4 al `limits.memory` de la API de
  `session-api` (`logical-components.md` §5).

## 6. Consola M8 (NFR3.7)

- Lista con TanStack Query; los filtros Tipo, Perfil y Origen se aplican en memoria con `useMemo` sobre la
  lista recibida. A partir de 200 filas la tabla se virtualiza con el mismo mecanismo que la lista de turnos
  de U4, conservando `aria-rowcount` y `aria-rowindex` para la suite `axe`.
- La subida es un `fetch` con `AbortController`: no bloquea la consola, y «Cancelar» y Escape responden
  durante `uploading` (NFRD-U12-06). Tras un `201` se invalida la consulta de la lista.
- Medición en nivel 3 con Playwright y `performance.now()`: cambiar un filtro o marcar una casilla con
  1 000 filas en ≤ 300 ms.

## 7. CPU primero (NFR2.1)

Las pruebas de U12 de los niveles 0 y 1 corren en un contenedor sin GPU, con `pytest-socket` que solo deja
la conexión a PostgreSQL de la prueba. U12 no carga modelos.

## 8. Cómo se mide

| Medición | Comando | Umbral |
|---|---|---|
| NFR3.1–NFR3.6, NFR3.8 | `uv run --directory services/session-api pytest -m perf tests/research_reports` (50 repeticiones, mediana y p95) | Los de performance-requirements |
| NFR3.7 | `npx --prefix frontend playwright test e2e/research-reports.spec.ts` | ≤ 300 ms; «Cancelar» responde durante `uploading` |
| NFR3.10 (contención) | Misma marca `perf`, caso `test_upload_does_not_slow_polling` | + ≤ 200 ms en el p95 del sondeo |

Una prueba de rendimiento inestable se arregla o se pone en cuarentena con un *issue*; nunca se reintenta ni
se baja su umbral (`team.md`).
