# Requisitos de rendimiento — U11 incoherence-analyzer

**Revisión 1 (2026-11-22): primera pasada.**
- **IDs.** Todo es **nuevo** y hereda el ID del NFR de Inception (NFR2, NFR3, NFR8, NFR15).
- **Por qué existe.** U11 es `library`, y el archivo de etapa no pide este documento para ese tipo. Se añade
  porque los plazos de C25 (NFR-U11-05), la latencia del turno de NFR3 y el *N* de la prueba de humo
  (NFR-U11-10) son cifras de U11.
- **Respuestas que lo condicionan.** P1 = A: el verificador de `comercial-piloto` es local y corre en CPU.
  FD-U8-08 (P5 = A): la permutación queda activa en todos los perfiles (NFR-U11-08).

**Insumos.** Flujos F1–F4 y BR4.1, BR6.1, BR7.2 y BR10.3 de functional-spec y rules; NFR2, NFR3, NFR8 y
NFR15 de requirements; C13, C14, C17, C18 y C25 de contract-summary; NFR-U10-04 de U10; mediciones M1–M6 de
`docs/validacion-zine/reporte.md`.

## 1. Base de cálculo

| Dato | Valor | Fuente |
|---|---|---|
| Juez local Qwen3.6-35B-A3B Q8_0 en ZINE (CPU) | Lectura 32,05 *tokens*/s (pp2048); escritura 6,77 *tokens*/s (tg128), 1,36 con contexto largo | Reporte de ZINE, M3 |
| Modo final de la entrevista más larga del piloto (67 769 *tokens*), juez local en ZINE | De 1,3 a 3,9 h | Reporte de ZINE, M3 |
| Verificador local gpt-oss-20b Q8_0 (CPU) | Lectura 7,80 *tokens*/s; escritura 5,30 *tokens*/s. Con caché del *prompt* fijo, unos 20–60 s por llamada de ~1 500 *tokens* de entrada y ≤ 150 de salida | Reporte de ZINE, M3; estimación de esta etapa |
| Seudonimización de U10 | p95 ≤ 15 s para 186 000 caracteres, con un presupuesto de 0,15 × `model_call_timeout_s` | NFR-U10-04 |
| Llamadas por corrida incremental | 1 al juez por ventana relevante y 2 por candidato sobreviviente (verificador y permutada) | BR4.2, BR6.1 |

Las cifras de los modelos comerciales no se midieron. Las de §2 son metas que el reporte de nivel 2 comprueba
(latencia por llamada en `registro.llamadas`). Si no se alcanzan, se cambia el perfil por PR; las metas no
se relajan.

## 2. Requisitos

### NFR3 — No bloqueante (latencia)

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR3.1 | nuevo | Latencia de `analyze` incremental con `comercial-piloto`. | En la máquina de desarrollo, con ≤ 60 turnos y ≤ 2 candidatos que pasan el filtro: **p95 ≤ 180 s** y mediana ≤ 120 s desde la llamada a `analyze` hasta la `Salida`, medido sobre las corridas incrementales del conjunto sintético | Nivel 2 (reporte con la latencia por corrida) |
| NFR3.2 | nuevo | Lo que es de la biblioteca, sin modelos, es despreciable. | Con el *fake* de latencia cero y la transcripción del tamaño máximo de C25: validación de entrada, armado de mensajes, verificación de citas, deduplicación y validación contra C6 suman **≤ 2 s** en total, y la verificación de una cita ≤ 50 ms. Prueba con un margen de 3× para tolerar la CI | Nivel 0 (pytest con tiempo medido) |
| NFR3.3 | nuevo | *N* de la prueba de humo (NFR-U11-10). | `frontend/e2e/smoke.spec.ts` espera **≤ 300 s** a que una transcripción sintética de ≤ 60 turnos con una contradicción sembrada produzca ≥ 1 hallazgo con sus dos citas, con `comercial-piloto`. La parte de U4 (cola, ingesta y sondeo de la consola) cabe dentro de esos 300 s | Nivel 3 |
| NFR3.4 | nuevo | Modo final con `comercial-piloto`. | Una transcripción del tamaño máximo de C25 (186 000 caracteres) termina en ≤ `run_deadline_final_s` del despliegue (3600 s en la máquina de desarrollo), con una sola llamada al juez dentro de `model_call_timeout_s` (≥ 200 s, NFR-U10-04) | Nivel 2 |
| NFR3.5 | nuevo | Modo final con `evaluacion-local-zine`. | La entrevista más larga del conjunto termina dentro de `run_deadline_final_s = 43200` (12 h) con un margen de ≥ 3× sobre la peor medición de M3 (3,9 h). El reporte registra la duración por corrida | Nivel 2 en ZINE (lo lanza el humano) |
| NFR3.6 | nuevo | La permutación cabe en el plazo incremental. | Con `permutation: true` y 2 candidatos, las 4 llamadas al verificador local más la del juez caben en `run_deadline_incremental_s` del despliegue (900 s en la máquina de desarrollo, tope 1200 s en C25). Una corrida que lo pasa termina en `tiempo_agotado` (BR7.2), nunca con un resultado parcial | Nivel 0 (reloj simulado) y nivel 2 |

### NFR2 — CPU primero

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR2.1 | nuevo | Ninguna prueba de los niveles 0 y 1 de U11 exige GPU ni red. | La suite corre en un contenedor sin GPU y con la red cortada (`--network none`); una prueba que abre un *socket* hacia fuera falla por el bloqueo de `pytest-socket` | Nivel 0 |
| NFR2.2 | nuevo | El perfil de evaluación de la primera rebanada corre en la máquina de desarrollo. | `evaluacion-comercial` usa el verificador gpt-oss-20b en CPU con ≤ 14 GB de RAM para su servidor local (Q8_0 de ~12 GB más el contexto). La evaluación de 40 muestras × 3 corridas termina en **≤ 6 h**; si no, se parte por muestras y se suman los reportes | Nivel 2 |
| NFR2.3 | nuevo | ZINE es solo CPU y por lotes. | `evaluacion-local-zine` tiene `batch_only: true`; los `.sbatch` piden solo CPU y RAM (sin `--gres=gpu`), con tiempo de pared ≥ `run_deadline_final_s` × muestras del trabajo | Nivel 0 (comprobación de los `.sbatch`) |

### NFR8 — Volumen de la evaluación por lotes

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR8.1 | nuevo | La biblioteca atiende un turno a la vez por proceso y no oculta fallos. | `analyze` no lanza llamadas en paralelo dentro de una corrida (una sola ranura del juez, `project.md`). La fracción `completed_runs` del reporte cuenta toda corrida que termina en `proveedor`, `tiempo_agotado`, `bloqueo_contenido` o `anonimizador_no_disponible` como no completada, sin reintentar la corrida | Nivel 0 |
| NFR8.2 | nuevo | Aporte de U11 a la prueba de 50 sesiones en tandas de 3 (≥ 98 %). | Con `comercial-piloto` y el conjunto sintético, `completed_runs ≥ 0,98` en la corrida de evaluación; con menos, el reporte lo marca y la prueba de carga de NFR8 (U4) no se intenta | Nivel 2 |
| NFR8.3 | nuevo | La permutación no impide el 98 %. | Si NFR8.2 no se alcanza por `tiempo_agotado` en la llamada permutada, se cambia `todo-local` o el plazo por PR con la prueba de U8 (NFR-U11-08). El umbral no se baja | Nivel 2 |

### NFR15 — Observabilidad (SHOULD)

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR15.1 | nuevo | Cada llamada queda medida. | Toda entrada de `registro.llamadas` lleva papel, proveedor, modelo, *tokens* de entrada y salida, latencia en milisegundos y costo con `config/prices.yaml` (o «sin precio»). El reporte C19 suma *tokens* y costo por proveedor y la latencia p50 y p95 por papel | Nivel 0 (con *fake* que declara *tokens*) |
| NFR15.2 | nuevo | La biblioteca no exporta métricas por sí misma. | No hay servidor de métricas ni cliente de Prometheus en los paquetes de U11 (import-linter); `semantic-agent` (U4) publica lo que necesite desde el registro | Nivel 0 |

## 3. Recursos

| Pieza | Presupuesto | Medición |
|---|---|---|
| Proceso de la biblioteca o de la CLI, sin modelos | ≤ 512 MiB de memoria residente con la transcripción máxima de C25 | Nivel 0 con `tracemalloc` |
| Servidor del verificador local en la máquina de desarrollo | ≤ 14 GB de RAM, 1 ranura | NFR2.2 |
| Disco por corrida de la CLI | Salidas de C6 y reporte; ≤ 5 MB por entrevista | Nivel 0 |
