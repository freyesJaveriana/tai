# Diseño de rendimiento — U11 incoherence-analyzer

**Revisión 1 (2026-11-22): primera pasada.**
- **Por qué existe.** U11 es `library` y el archivo de etapa no pide este documento para ese tipo. Se añade
  porque `performance-requirements.md` existe: los plazos de C25, la latencia de NFR3, el *N* de la prueba de
  humo y el volumen de NFR8 son cifras de U11.
- **Escalabilidad y observabilidad.** No hay `scalability-requirements` ni `observability-requirements` para
  U11. Lo que aporta a NFR8 está en §6 y lo que aporta a NFR15, en §7.
- **Tamaños.** Las mediciones usan la transcripción máxima de C25 v1: 250 000 caracteres, 20 000 por turno y
  2 000 turnos (NFRD-U11-03).

**Insumos.** `nfr-requirements/performance-requirements.md` (performance-requirements: NFR2, NFR3, NFR8,
NFR15 y §3 de recursos), `tech-stack-decisions.md` (tech-stack-decisions: D4, D6 y §3); F2–F5 y §9 de
`functional-design/functional-spec.md` (functional-spec); C13, C14, C18 y C25 de
`inception/contract-design/contract-summary.md` (contract-summary); NFRD-U10-01 (seudonimización de
250 000 caracteres en ≤ 20 s) de U10; mediciones M3–M5 de `docs/validacion-zine/reporte.md`.

## 1. Presupuesto del modo incremental con `comercial-piloto` (NFR3.1, NFR3.3, NFR3.6)

Caso de NFR3.1: ≤ 60 turnos y ≤ 2 candidatos que pasan el filtro, en la máquina de desarrollo. Con la
permutación activa (NFR-U11-08) son 1 llamada al juez y 4 al verificador, en serie (NFR8.1).

| Tramo | Presupuesto p95 | Cómo se cumple | Dónde se mide |
|---|---|---|---|
| Validación previa, armado de mensajes, filtro, verificación de citas, salida | ≤ 2 s | §4 | Nivel 0 (NFR3.2) |
| Seudonimización de U10 (~30 000 caracteres) | ≤ 3 s | 0,8 s por 10 000 caracteres (NFRD-U10-01) | `masking_ms` de U10 |
| Juez de Anthropic | ≤ 60 s | Una sola ventana; caché del bloque `system` en el proveedor (NFRD-U10-12) | Latencia p95 del papel `juez` en C19 v2 |
| Verificador local, 4 llamadas | ≤ 100 s (≤ 25 s cada una) | §2: prefijo fijo en caché, campos en orden y salida de un booleano | p95 de `verificador` y `verificador_permutado` en C19 v2 |
| Margen | 15 s | — | — |
| **Total** | **≤ 180 s** (mediana ≤ 120 s) | — | Nivel 2, latencia por corrida |

- **Si no se alcanza.** La latencia por papel del reporte dice qué tramo se pasa. Se cambia el perfil o el
  servidor por PR; la meta no se relaja (`performance-requirements.md` §1).
- **Plazo incremental (NFR3.6).** 900 s en la máquina de desarrollo (tope 1 200 s de C25). Las 5 llamadas
  del caso caben con un margen de 5×. El plazo se comprueba antes de cada llamada (BR7.2); una corrida que lo
  pasa termina en `tiempo_agotado`, nunca con un resultado parcial. Prueba con reloj simulado: plazo agotado
  antes de la cuarta llamada al verificador da `tiempo_agotado` y 3 llamadas.
- **Prueba de humo (NFR3.3).** *N* = 300 s en `frontend/e2e/smoke.spec.ts`: los 180 s de U11 más la cola, la
  ingesta y el sondeo de U4, que caben en los 120 s restantes.

## 2. Verificador local en CPU (NFR2.2, NFR3.1)

El verificador gpt-oss-20b Q8_0 lee a ~7,8 *tokens*/s en CPU (M3). Lo que cuesta es leer, no escribir, así que
el diseño reduce lo que el servidor tiene que leer en cada llamada:

- **Prefijo fijo primero.** Los mensajes de `verifier` son `system` (texto constante del paquete) y `user`.
  Con una sola ranura y la caché de *prompt* del servidor (activa por omisión en la versión de
  `llama-server` que fija U2), el `system` se lee una vez y las llamadas siguientes solo leen `user`.
- **Orden de campos.** `user` es `{"hecho", "tipo", "cita_a", "cita_b"}` en ese orden, serializado sin espacios
  (§5 de `security-design.md`). La llamada permutada comparte el prefijo hasta `tipo` con la directa, que va
  justo antes, y solo lee las dos citas.
- **Salida mínima.** El esquema del verificador es `{"confirma": boolean}` con `response_format`
  `json_schema` y el razonamiento apagado (D6): la escritura son unos pocos *tokens*.
- **Una ranura y un turno a la vez** (`project.md`): el servidor no reparte la caché entre peticiones.
- **Estimación.** Con ~150 *tokens* variables en la directa y ~100 en la permutada, ≈ 20 s y ≈ 13 s por
  llamada, dentro de los 25 s de §1. Es una estimación: la decide la medición de nivel 2.

Recursos de la máquina de desarrollo: servidor del verificador con ≤ 14 GB de RAM y 1 ranura (NFR2.2). La
evaluación de 40 muestras × 3 corridas tiene una meta de ≤ 6 h; si se pasa, se reanuda por muestras (§6).

## 3. Modo final (NFR3.4, NFR3.5)

| Perfil | Caso | Plazo | Diseño |
|---|---|---|---|
| `comercial-piloto` | Transcripción de 250 000 caracteres | `run_deadline_final_s` = 3 600 s y `model_call_timeout_s` = 300 s en la máquina de desarrollo (mínimo 270 s, NFRD-U11-03) | Una sola llamada al juez sin fragmentar (NFR-U11-04); seudonimización ≤ 20 s, dentro de 0,15 × 300 = 45 s; luego 2 llamadas locales por candidato sobreviviente |
| `evaluacion-local-zine` | Entrevista más larga del conjunto | `run_deadline_final_s` = 43 200 s | Ventanas de 60 turnos con solapamiento 20; margen ≥ 3× sobre la peor medición de M3 (3,9 h); `model_call_timeout_s` = 3 600 s por ventana |

- **Cupo de la petición.** El cuerpo de 250 000 caracteres va serializado con `ensure_ascii=False`, que lo deja
  muy por debajo de `anonymizer_request_max_bytes` (2 097 152); U10 lo comprueba con un 30 % de caracteres
  escritos como `\uXXXX` (NFRD-U10-01).
- **Contexto del juez comercial.** 250 000 caracteres son del orden de 70 000–90 000 *tokens*, más el
  *prompt* y la reserva de salida. El PR de `config/profiles.yaml` que fija el modelo de Anthropic (NFR-U11-01)
  cita su ventana de contexto; si no cupiera, la corrida falla con `proveedor` o `salida_invalida` en nivel 2 y
  se cambia el modelo por PR.
- **Perfiles locales.** La comprobación de nivel 1 de `tech-stack-decisions.md` §3 exige que ventana,
  *prompt* y reserva de salida quepan en el contexto del servidor declarado.

## 4. Lo que hace la biblioteca sin modelos (NFR3.2)

Meta: con el *fake* de latencia cero y la transcripción máxima, ≤ 2 s en total y ≤ 50 ms por cita, con un
margen de 3× en la prueba para la CI.

| Paso | Diseño | Costo |
|---|---|---|
| Validación de C6 | Validadores de `jsonschema` compilados una vez por proceso (`functools.cache` sobre el registro de U1) | Lineal en el tamaño |
| Turnos normalizados | `domain/quotes.py` normaliza cada turno una sola vez por corrida (solo espacios, BR5.5) y guarda un índice `número de turno → texto normalizado` | Lineal, una vez |
| Verificación de una cita | Búsqueda de subcadena (`str.find`) en el turno indicado; con « […] », fragmentos buscados en orden desde la posición anterior; los turnos ENT y plegados con aviso (BR5.7) | Lineal en el turno (≤ 20 000 caracteres) |
| Deduplicación | Diccionario por par no ordenado `(turno, cita normalizada)` (BR4.3) | Constante por candidato |
| Ventanas | Por posición, paso `ventana − solapamiento` (BR4.1); en incremental se descartan las que no tocan el tramo antes de armar mensajes | Lineal |
| Escáner | Términos de C8 plegados una vez por proceso; búsqueda por palabra completa | Lineal en `hecho` y `observaciones` |

La prueba de nivel 0 mide con `time.perf_counter` sobre la transcripción máxima: 2 000 turnos que suman
250 000 caracteres, con turnos de hasta 20 000, 10 candidatos y 50 citas, de las que la mitad usa « […] ».

## 5. CPU primero (NFR2.1, NFR2.3)

- **Niveles 0 y 1.** `pytest-socket` con `--disable-socket --allow-hosts=127.0.0.1`: solo *loopback* para los
  servidores HTTP *fake*. La CI corre la suite en un contenedor sin GPU; una prueba que abre un *socket* hacia
  fuera falla.
- **ZINE.** `evaluacion-local-zine` tiene `batch_only: true`, que lee U4 para no ofrecerlo en la consola; U11 no
  lo usa para decidir (entities). Los `.sbatch` piden solo CPU y RAM, sin `--gres=gpu`, con tiempo de pared ≥
  `run_deadline_final_s` × muestras del trabajo. Una comprobación de nivel 0 lee cada `.sbatch` y falla si
  falta una de las dos condiciones.

## 6. Lotes y volumen (NFR8.1, NFR8.2, NFR8.3)

- **Una llamada a la vez.** `analyze` es síncrona y hace las llamadas en serie: ni hilos ni `asyncio` dentro
  de una corrida. La CLI procesa los archivos uno tras otro. Una prueba con un *fake* que cuenta llamadas
  concurrentes exige un máximo de 1.
- **Sin reintentar corridas.** Una corrida que termina en `proveedor`, `tiempo_agotado`, `bloqueo_contenido` o
  `anonimizador_no_disponible` cuenta como no completada en `completed_runs` y no se repite sola.
- **Reanudación por muestras (NFR2.2; NFRD-U11-11).** `evaluate` escribe cada muestra en
  `corrida-<n>/<muestra>.salida.json` y los booleanos de la permutación en
  `corrida-<n>/<muestra>.permutacion.json` (solo `true`/`false` por candidato), de forma atómica. Si se invoca
  otra vez con el mismo `--salida`, el mismo `config_sha256` y el mismo `dataset_sha256`, salta las muestras
  que ya tienen las dos salidas válidas. Con otra huella, código 2 sin escribir. Así una evaluación larga se
  parte en sesiones sin sumar reportes a mano.
- **NFR8.2 y NFR8.3.** El reporte de evaluación con `comercial-piloto` marca `completed_runs` ≥ 0,98 antes de
  que U4 intente la prueba de NFR8. Si no se alcanza por `tiempo_agotado` en la llamada permutada, se cambia el
  plazo o el perfil por PR con la prueba de U8; el umbral no baja.

## 7. Medición por llamada (NFR15.1, NFR15.2)

- **Dónde.** `gateway.py` envuelve cada `generate` con `Clock.monotonic()` antes y después, también cuando la
  llamada termina en un error con `call`. La latencia (ms enteros) y el costo (con `config/prices.yaml`) quedan
  en un registro en memoria junto al `ModelCall`; **no** van a `registro.llamadas` (NFRD-U11-07).
- **Qué va al reporte C19 v2.** *Tokens* de entrada y salida y costo por proveedor (o «sin precio»), y la
  latencia p50 y p95 por papel con el método del rango más cercano sobre todas las llamadas del papel en la
  ejecución (en `evaluate`, las 3 corridas). Son las cifras de NFR-U11-14.
- **Prueba.** Un *fake* que declara *tokens* y un reloj simulado que avanza 1 000, 2 000 y 3 000 ms dan p50 =
  2 000 y p95 = 3 000 para ese papel, y el costo esperado con la tabla de precios de prueba.
- **Sin métricas propias.** Ningún paquete de U11 importa `prometheus_client` ni abre un puerto
  (`security-design.md` §9). `semantic-agent` publica lo que necesite desde la `Salida` (U4).

## 8. Recursos

| Pieza | Presupuesto | Diseño | Medición |
|---|---|---|---|
| Proceso de la biblioteca o de la CLI, sin modelos | ≤ 512 MiB de memoria residente | Una corrida a la vez; el registro de latencias guarda solo enteros; las salidas se escriben y se sueltan antes del siguiente archivo | Nivel 0 con `tracemalloc` sobre la transcripción máxima (pico) |
| Servidor del verificador en la máquina de desarrollo | ≤ 14 GB, 1 ranura | §2 | NFR2.2 |
| Disco por corrida de la CLI | ≤ 5 MB por entrevista | Salida de C6 sin sangría y reporte cerrado | Nivel 0 sobre la salida máxima armada |

## 9. Decisiones

| # | Decisión | Alternativas descartadas | Consecuencias |
|---|---|---|---|
| DP1 | Presupuesto del modo incremental repartido por papel y diagnosticado con la latencia p95 por papel | Una sola cifra total | Se sabe qué tramo cambiar; las metas por papel no bloquean, solo explican la total |
| DP2 | Prefijo fijo y orden de campos para aprovechar la caché del servidor local | Mensajes en cualquier orden | La llamada permutada cuesta menos que la directa; a cambio, el orden de los campos es parte del diseño y tiene prueba |
| DP3 | Verificación de citas con normalización única por corrida y `str.find` | Expresiones regulares por cita | Lineal y sin riesgo de retroceso catastrófico |
| DP4 | Llamadas en serie, sin concurrencia dentro de la corrida | Verificar candidatos en paralelo | Repetible y coherente con una ranura (`project.md`); a cambio, más latencia con muchos candidatos |
| DP5 | Reanudación de `evaluate` por muestras con la misma huella | Partir el conjunto a mano y sumar reportes | La evaluación larga se parte sin tocar las métricas; a cambio, una opción más que probar |
