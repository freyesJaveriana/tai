# Diseño de rendimiento — U10 anonymizer

**Revisión 2 (2026-11-22): segunda pasada por el cambio 01, la adenda 02 y el NFR Requirements revisión
2.** Sustituye a la revisión 1 del 2026-10-03, que medía un proxy apagado delante de `judge` y `embed`.
Ahora U10 está en el camino de toda llamada comercial, en la CLI y en el clúster. Sale el presupuesto de
`embed` (NFR9.1 «Retirado») y entra el tamaño de 250 000 caracteres (NFRD-U10-01).

**Insumos.** `nfr-requirements/performance-requirements.md` (performance-requirements: NFR3.1–NFR3.6,
NFR8.1), `scalability-requirements.md` (scalability-requirements), `reliability-requirements.md`
(reliability-requirements), `security-requirements.md` (security-requirements),
`observability-requirements.md` (observability-requirements) y `tech-stack-decisions.md`
(tech-stack-decisions, D2, D5, D6) de esta unidad; F1, F4, F5 y F8 de `functional-design/functional-spec.md`
(functional-spec); C20, C21 y C25 de `inception/contract-design/contract-summary.md` (contract-summary);
NFR-U4-02 de U4.

Todo se mide en la máquina de desarrollo, en CPU (`CUDA_VISIBLE_DEVICES=""`), con el `FakeTransport` y
transcripciones sintéticas de 10 000, 50 000, 186 000 y 250 000 caracteres: 3 corridas de calentamiento y
20 medidas, p95, reporte en `out/anonymizer-perf.json`. Una prueba de rendimiento inestable se arregla o
va a cuarentena con un *issue*; nunca se baja su umbral.

## 1. Presupuesto de una llamada `generate`

| Tramo | Diseño | Meta p95 con 250 000 caracteres | Requisito |
|---|---|---|---|
| Lectura y validación del cuerpo de C21 | Rechazo por `Content-Length`; lectura por bloques; Pydantic v2 con el modelo de C21 | ≤ 20 ms | NFR3.2 |
| Resolución del perfil y del destino | Diccionario en memoria con las huellas calculadas al arrancar | ≤ 1 ms | NFR3.2 |
| Seudonimización (`masking_ms`) | §2 | ≤ **20 s** (≤ 15 s con 186 000; 0,8 s por cada 10 000) | NFR3.1, NFR3.5 |
| Verificación final | §3 de `security-design.md`; una pasada lineal | Incluida en `masking_ms` | NFR3.1 |
| Proveedor (`upstream_ms`) | No lo fija U10; lo limita el plazo | — | NFR3.6 |
| Validación, restauración y serialización | `jsonschema` compilado una vez por esquema y llamada; una pasada sobre las cadenas | ≤ 25 ms | NFR3.2 |
| Sobrecosto total del proxy | Total − `masking_ms` − `upstream_ms` | ≤ **50 ms** | NFR3.2 |

**Cifras atadas (NFR-U10-04, NFR-U4-02).** Con `model_call_timeout_s` = 270 s el presupuesto de
seudonimización es 0,15 × 270 = 40,5 s, y la mitad, 20,25 s, cubre la meta de 20 s. La prueba `-m limits`
falla si una unidad fija un plazo menor con un perfil comercial.

## 2. NER en CPU (NFR3.1, NFR3.3, NFR8.5)

- **Carga única.** El modelo se carga al arrancar en `torch` solo CPU, en `eval()` y bajo
  `torch.inference_mode()`, y se calienta con un texto sintético (§4 de `reliability-design.md`).
- **Ventanas.** Cada valor de texto se tokeniza una vez y se parte en ventanas de 512 *tokens* con 128 de
  solapamiento. Las ventanas se procesan en lotes de 8; los tramos de los solapes se unen por posición de
  carácter. El costo crece de forma lineal con el texto.
- **Hilos.** `torch.set_num_threads(VERIDICUS_ANONYMIZER_NER_THREADS)` (por defecto 2) y un solo NER a la
  vez por proceso (`CapacityLimiter(1)`, NFRD-U10-07). En el MVP pasa como mucho una llamada a la vez por
  el proxy, porque el trabajador hace una corrida a la vez (NFR-U4-12); la espera del NER cuenta en el
  presupuesto y falla cerrado si se pasa.
- **Prueba de linealidad.** La razón entre el p95 de 250 000 y el de 10 000 es ≤ 25 × 1,34 (≤ 33,5), y la de
  186 000 frente a 10 000 sigue en ≤ 25 (NFR3.1).

## 3. Reglas, propagación y caminos lineales (NFR3.4, NFR10.8)

- **Reglas.** Compiladas una vez al arrancar con `re2`. Una entrada adversaria de 100 000 caracteres
  termina la detección por reglas en < 1 s; una prueba confirma que ninguna regla compila con `re`.
- **Propagación por forma exacta.** Las formas detectadas se unen en una sola alternancia de `re2` por
  llamada, con las formas escapadas y ordenadas de mayor a menor longitud; la comprobación del límite de
  palabra Unicode se hace sobre el carácter anterior y el siguiente de cada coincidencia. Una pasada por
  valor.
- **Reemplazo.** Los tramos se reemplazan de derecha a izquierda con una lista de partes y un solo
  `"".join`, sin concatenar cadenas en un bucle.
- **Palabras permitidas** en un `frozenset` cargado al arrancar.

## 4. Conexiones y salida hacia el proveedor (NFR3.2, NFR10.4)

- Un `httpx.AsyncClient` por adaptador, creado al arrancar, con `Limits(max_connections=4,
  max_keepalive_connections=2, keepalive_expiry=30)` y HTTP/1.1. Reutilizar la conexión TLS ahorra el
  saludo en llamadas seguidas; el dominio es fijo.
- **Caché de *prompts* del proveedor (FR15.1).** El punto de caché va solo en el bloque `system`, que no
  trae testimonio (NFRD-U10-12). Como la numeración es por primera aparición, el prefijo es estable entre
  llamadas. Si el prefijo no alcanza el mínimo del proveedor, simplemente no se cachea.
- **Sin caché propia de resultados.** El módulo no guarda cuerpos ni tablas entre llamadas: una caché
  retendría testimonio (BR1.8). Es una decisión explícita frente al ahorro.

## 5. Arranque (NFR3.3)

Desde que empieza el proceso hasta que `/readyz` responde 200 (datos comprobados, NER cargado y
calentado, perfiles y claves validados) pasan ≤ **60 s** en CPU. El SHA-256 del NER se calcula leyendo
por bloques de 1 MiB. En la CLI, construir el módulo tarda lo mismo como máximo. La sonda de arranque de U2
debe tolerar ese tiempo.

## 6. Prueba de carga de NFR8 (NFR8.1)

Durante las 50 sesiones de texto en tandas de 3 con un perfil comercial: 0 respuestas `503` por saturación
y 0 `OOMKilled`, comprobado con `veridicus_anonymizer_requests_total{error_code="analysis.anonymizer_unavailable"}`
y los eventos del pod. El reporte declara el perfil y los límites de la cuenta de Anthropic usados.

## 7. Decisiones y alternativas

| # | Decisión | Alternativas descartadas | Consecuencias |
|---|---|---|---|
| DP1 | NER en ventanas de 512 con solapamiento 128, en lotes de 8 | Un texto por llamada al *pipeline*; truncar | Lineal y sin perder entidades en los bordes; a cambio, unir tramos de los solapes |
| DP2 | Un NER a la vez por proceso con hilos de `torch` fijados | Varias inferencias en paralelo | Uso de CPU previsible y sin contención; a cambio, una segunda petición espera dentro de su presupuesto |
| DP3 | Una alternancia de `re2` por llamada para propagar las formas | Una búsqueda por forma | Una pasada por valor aunque haya muchas formas |
| DP4 | Sin caché de resultados en U10 | Caché por SHA-256 del cuerpo | No retiene testimonio; cada llamada paga su seudonimización |
