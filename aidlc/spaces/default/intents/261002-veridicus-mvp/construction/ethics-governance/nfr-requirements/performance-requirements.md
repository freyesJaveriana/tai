# Requisitos de rendimiento — U13 ethics-governance

**Revisión 1 (2026-11-22): primera pasada.**
- **IDs.** Todo es **nuevo** y hereda el ID del NFR de Inception (NFR2 y NFR3).
- **Qué mide.** U13 no llama a modelos. Su trabajo es síncrono y corto: calcular un estado, insertar una
  fila, comparar una nota con los turnos y escribir el registro de acceso. A eso se suman el `Job` de
  retención y el comando de consulta, que lanza el humano. NFR3 («interfaz no bloqueante») se cumple con
  respuestas rápidas y con avisos que no bloquean la consola.

**Insumos.** F1–F10, BR1.2, BR2.3, BR3.6, BR3.7, BR5.5, BR5.6, BR6.2 y BR7.1 de functional-spec y rules
(preguntas abiertas 2 a 5 de §11); NFR2 y NFR3 de requirements; C1, C23, C24 y C25 de contract-summary;
`transcript_max_turns` = 2 000 y `transcript_max_chars` = 250 000 de U4; el punto de guardado de 500 ms de
U3 (NFR10.21 de U3, «su latencia la mide U13»); NFR3.9 de U5 y NFR10.27 de U7 (sus partes del borrado).

**Cómo se mide.**
- En la **máquina de desarrollo con CPU** (NFR2), con PostgreSQL y Redis reales en contenedor.
- Con la marca `perf` de `pytest` (nivel 1), en proceso y con `time.perf_counter`, 50 repeticiones por caso
  salvo que la fila diga otra cosa. Se informa la mediana y el p95.
- En la consola, con Playwright (nivel 3) y `performance.now()`.
- Con los *fixtures* sintéticos del generador de NFR12.1 (`security-requirements.md`):
  - **sesión típica:** 100 turnos, unos 12 000 caracteres;
  - **sesión máxima:** 2 000 turnos y 250 000 caracteres (`transcript_max_turns` y `transcript_max_chars`),
    con 250 sugerencias, 7 500 decisiones, 3 versiones de reporte, 1 exportación, 10 audios conservados, 2
    reportes de problemas y 3 cambios de plazo (el peor caso de NFR3.9 de U5 y de U7);
  - **nota máxima:** 2 000 caracteres (`problem_report_note_max_chars`).
- Una prueba de rendimiento inestable se arregla o se pone en cuarentena con un *issue*. Nunca se reintenta
  ni se baja su umbral (`team.md`).

## 1. Latencia de las rutas

| ID | Estado | Qué se mide | Objetivo | Carga | Cómo se mide |
|---|---|---|---|---|---|
| NFR3.1 | nuevo | `POST /problem-reports` con sesión, de punta a punta en el servidor (rol, propiedad, lectura de turnos por `turn_texts`, comparación de BR3.6 e inserción) | Sesión típica: **p95 ≤ 150 ms**. Sesión máxima con nota máxima: **p95 ≤ 500 ms**. Sin sesión: **p95 ≤ 100 ms** | *Fixtures* típico y máximo; nota de 2 000 caracteres con y sin coincidencia | `perf`, nivel 1 |
| NFR3.2 | nuevo | La comparación local de la consola (BR3.7), desde «Enviar» hasta que se muestra el aviso o sale la petición | Sesión típica: **≤ 30 ms**. Sesión máxima con nota máxima: **≤ 150 ms**, sin tareas de más de 200 ms en el hilo principal | M4 con 2 000 turnos cargados | Playwright, nivel 3, con `performance.now()` y `PerformanceObserver` de `longtask` |
| NFR3.3 | nuevo | Costo de U13 en `GET /auth/me` (cálculo del estado de BR1.2) | **≤ 20 ms** sobre el p95 de `/auth/me` sin U13, con 1 000 reconocimientos del usuario | Usuario con 1 000 filas en `AnalystAcknowledgement` | `perf`, nivel 1 (comparación con y sin el módulo) |
| NFR3.4 | nuevo | `POST /acknowledgements` y `PATCH /sessions/{id}/retention` | `POST /acknowledgements`: **p95 ≤ 150 ms**. `PATCH`: **p95 ≤ 200 ms**. La validación del plazo dentro de `POST /sessions` y `POST /sessions/import` suma **≤ 5 ms** | 50 peticiones de cada una | `perf`, nivel 1 |
| NFR3.5 | nuevo | `AccessLog.record` con el adaptador real, dentro de la transacción de quien llama | **p95 ≤ 20 ms**, muy por debajo de su plazo de 500 ms (NFR10.13). Con 150 000 filas ya en la tabla, el mismo p95 | 200 llamadas por tipo de recurso | `perf`, nivel 1 |
| NFR3.6 | nuevo | El `Job` de retención | Una **sesión máxima** se borra, con su acta, en **p95 ≤ 10 s** (20 repeticiones con *rollback*). Una ejecución con **50 sesiones típicas** vencidas termina en **≤ 5 min**. `--dry-run` sobre **500 sesiones** (200 vencidas) termina en **≤ 60 s**. Pico de memoria del proceso **≤ 256 MiB** | *Fixtures* de sesión máxima y típica | `perf`, nivel 1, con `psutil` |
| NFR3.7 | nuevo | El comando de consulta | Con 150 000 filas de registro de acceso, `access-log --session <id>` responde en **≤ 2 s** y `--limit 10000` en **≤ 5 s**. El proceso no suma más de **64 MiB** de memoria al contenedor | 150 000 filas sembradas | `perf`, nivel 1, con `psutil` |

**Presupuesto orientativo de NFR3.1 (sesión máxima).** La medición lo confirma; no lo reemplaza.

| Tramo | Presupuesto |
|---|---|
| Rol, propiedad y resolución de la sugerencia | ≤ 30 ms |
| Lectura de 2 000 turnos (250 000 caracteres) por `turn_texts` | ≤ 150 ms |
| Normalización y búsqueda de 8 palabras seguidas (conjunto de *hashes* de las secuencias de 8 palabras de la nota, recorrido lineal de los turnos) | ≤ 200 ms |
| Inserción y confirmación | ≤ 50 ms |

Si la comparación no cabe en su tramo, se cambia el algoritmo (D2 de `tech-stack-decisions.md`), no el
umbral.

## 2. La interfaz no se bloquea

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR3.8 | nuevo | Los avisos y el panel de U13 no bloquean la consola (BR1.5, BR3.2, BR6.2, BR6.3). | Con el recordatorio de bienestar visible y con el panel de reporte abierto, escribir en la entrada de turnos y pulsar las acciones de una tarjeta responden en **≤ 100 ms** y el foco no cambia. El recordatorio aparece al cumplirse `wellness_reminder_interval_s` con un desvío **≤ 1 s** (reloj simulado) y no hace ninguna petición (0 peticiones). Tras «Más tarde», la lista de sesiones y M4 responden igual que con el reconocimiento vigente | Vitest con reloj simulado y Playwright, nivel 3 |

## 3. CPU primero

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR2.1 | nuevo | Las pruebas de U13 de los niveles 0 y 1 no exigen GPU, red ni modelos. | Corren en un contenedor sin GPU; `pytest-socket` bloquea toda conexión salvo PostgreSQL y Redis de la prueba. U13 no carga ningún modelo | Nivel 0 y nivel 1 |

Si una medición supera su umbral, es un hallazgo que se corrige por PR, no un umbral que se sube en silencio.
