# Requisitos de rendimiento — U7 forensic-report (módulo ReviewReport)

**Revisión 2 (2026-11-22), segunda pasada por el cambio 01, la adenda 02 y el Functional Design de U7,
revisión 2.** Sustituye a la revisión 1 del 2026-10-03.
- **IDs.** Los requisitos conservan su ID; cada fila dice si **se mantiene**, **cambia** o es **nuevo**.
  Entran NFR3.12–NFR3.15 y NFR8.9. Ninguno se retira.
- **Qué cambia en el escenario.** Salen los Hechos No Documentados (cambio 01) y entra un caso máximo con
  las cifras de C25 de U4 y U5.
- **Qué responde.** Las preguntas 1, 2, 4, 5 y 6 de §12 de functional-spec.

**Insumos.**
- Flujos F1–F10 y §12 de `functional-design/functional-spec.md` (functional-spec, revisión 2).
- Reglas BR1.3, BR2.10, BR3.2, BR4.1, BR5.1, BR7.1, BR9.2–BR9.6, BR10.1 y BR11.1–BR11.3 de
  `functional-design/rules.md` (rules).
- NFR2, NFR3, NFR7 y NFR8 de `inception/requirements-analysis/requirements.md` (requirements, revisión 3).
- C1 (rutas de U7), C8, C11, C24 y C25 de `inception/contract-design/contract-summary.md`
  (contract-summary).
- `nfr-requirements-questions.md`, segunda pasada, sin preguntas.

Todas las metas se miden en la **máquina de desarrollo con el perfil CPU** (NFR2), con PostgreSQL real
en contenedor y el volumen de reportes como un directorio real del sistema de archivos del contenedor
(nunca `tmpfs` ni un *mock*, porque `fsync` es parte del costo). U7 no llama a ningún modelo. Las pruebas
`perf` de nivel 1 corren en proceso, con `time.perf_counter` alrededor de la llamada HTTP, como en U3, U4
y U5. Una prueba de rendimiento inestable se arregla o se pone en cuarentena con un *issue*; nunca se
reintenta ni se baja su umbral (`team.md`).

## 1. Escenarios de medición

Los dos *fixtures* son sintéticos y usan el catálogo de nombres de U1 (NFR12.1).

### 1.1 Caso de 100 turnos (cambia)

| Elemento | Valor | Por qué |
|---|---|---|
| Turnos | **100**: 60 de testimonio de 2 000 caracteres y 40 del entrevistador de 500 | Más que una entrevista corta del conjunto sintético; el mismo caso de la revisión 1 |
| Corridas | 1 corrida final terminada y 3 corridas incrementales; 1 aviso de sesión (familia del verificador declarada) | Recorre «Datos de la sesión y de las corridas» y «Avisos de la sesión» |
| Sugerencias de revisión | 50, todas decididas: 20 aceptadas con nota, 15 editadas con reformulación de 2 000 caracteres y 15 descartadas con nota de 2 000 caracteres; `hecho` de 300 y `observaciones` de 1 000 caracteres | El doble de la carga esperada por sesión (U5) |
| Rondas | Variante A: ronda 1 abierta (versión 1). Variante B: versiones 1 y 2 consolidadas y ronda 3 abierta (versión 3) | Consolidación inicial y de corrección |
| Puntos de página (N = 25) | 4 en la transcripción, 2 en las sugerencias y uno por sección H2 | BR11.2 |
| Tamaño del Markdown | ≈ 400 KB, medido y registrado por la prueba | Base del costo de render, escaneo, SHA-256, vista previa y exportación |

Salen los 20 paquetes de Hecho No Documentado de la revisión 1 (cambio 01).

### 1.2 Caso máximo (nuevo)

| Elemento | Valor | Origen |
|---|---|---|
| Transcripción | **2 000 turnos y 250 000 caracteres** (`transcript_max_turns`, `transcript_max_chars`), con turnos de hasta 20 000 caracteres (`turn_max_chars`) | C25, cifras de U4 |
| Sugerencias | 500, todas decididas, con nota y reformulación de 2 000 caracteres (`review_text_max_chars`) y citas de 2 000 caracteres | C25, cifra de U5; 500 es la cota que fija esta etapa para la prueba |
| Puntos de página | 80 en la transcripción y 20 en las sugerencias | BR11.2 con N = 25 |
| Tamaño del Markdown | Medido y registrado; debe quedar **≤ `report_max_bytes` = 8 MiB** (NFR8.5, NFR-U7-01) | Cálculo de NFR8.5 |

## 2. Latencia de las rutas de U7

| ID | Estado | Qué se mide | Objetivo | Carga | Cómo se mide |
|---|---|---|---|---|---|
| NFR3.1 | cambia | `200` de `POST /sessions/{id}/finalize` (F1): autorización, `snapshot`, transición con historial y *commit* | **p95 ≤ 200 ms** | 50 finalizaciones sobre sesiones nuevas del caso de 100 turnos, desde `open`, `paused`, `suspended` y `blocked`, con 0 y con 5 corridas en curso | `perf` de nivel 1 |
| NFR3.2 | cambia | `201` de `POST /sessions/{id}/reports` (F2, F6): bloqueo sesión → ronda, guardia, armado, render de `format_version` 2, escaneo C8, SHA-256, temporal + `fsync` + enlace, inserción, `lock_round`, transición y *commit* | **p95 ≤ 1 500 ms; máximo ≤ 2 000 ms** con el caso de 100 turnos. Es la meta del caso normal; si la ganadora supera el `lock_timeout` de 2 s, la perdedora recibe `503` (NFR10.13, cierra R-04) | 30 consolidaciones de cada variante (A y B) | `perf` de nivel 1 con el desglose de NFR3.3 |
| NFR3.3 | cambia | Desglose de NFR3.2 | p95 por tramo: armado con las lecturas de C11 ≤ 300 ms; render (con aviso y puntos de página) ≤ 400 ms; escaneo C8 ≤ 200 ms; SHA-256 ≤ 20 ms; escritura + `fsync` + enlace ≤ 300 ms; inserción + `lock_round` + transición + *commit* ≤ 150 ms. Los puntos de página de N = 25 añaden **< 2 %** de bytes en los dos casos (responde a la pregunta 5 de §12) | Las corridas de NFR3.2 | Tramos con `perf_counter` en la capa de aplicación, solo en la prueba |
| NFR3.4 | cambia | `200` de `GET /reports/{id}/download` (vista previa, F3): lectura del archivo, SHA-256 **recalculado sin caché**, comparación y envío | **p95 ≤ 250 ms** con el caso de 100 turnos; **p95 ≤ 500 ms** con un archivo de 8 MiB. El SHA-256 de 8 MiB cuesta < 50 ms (responde a la pregunta 2 de §12) | 100 vistas previas de cada tamaño | `perf` de nivel 1; el SHA-256 se mide aparte en nivel 0 |
| NFR3.5 | se mantiene | `200` de `GET /sessions/{id}/reports` | p95 ≤ 100 ms con 10 versiones | 100 llamadas | `perf` de nivel 1 |
| NFR3.6 | cambia | Rechazos sin render: `403`, los `409` de la guardia BR2.2–BR2.9 (incluidos `report.runs_in_progress` y `report.final_mode_not_launched`), `409 report.not_consolidated`, `404 report.not_found`, `409 session.finalized` | p95 ≤ 150 ms, 0 filas y 0 archivos (ni temporales) | 50 peticiones por cada `code` | `perf` de nivel 1 que lista el volumen |
| NFR3.7 | cambia | Rechazo `409 report.forbidden_vocabulary` (BR3.3), que sí renderiza y escanea con la lista de C8 que suma VE-02 | p95 ≤ 1 000 ms con el caso de 100 turnos; 0 filas y 0 archivos | 30 consolidaciones con un término sembrado en unas `observaciones` | `perf` de nivel 1 |
| NFR3.8 | se mantiene | `POST /sessions/{id}/correction-rounds` (F4) y el descarte (F5) | p95 ≤ 200 ms cada una | 50 de cada una | `perf` de nivel 1 |
| NFR3.12 | nuevo | `201` de `POST /reports/{id}/exports` (F8): lectura, verificación del SHA-256, marca y rótulo, `export_sha256`, inserción de `ReportExport`, `AccessLog.record` y *commit* antes de enviar | **p95 ≤ 500 ms** con el caso de 100 turnos; **p95 ≤ 2 000 ms** con 8 MiB; plazo total de 10 s (NFR10.26) | 50 exportaciones de cada tamaño, con el adaptador por defecto y con un doble del adaptador real que tarda 100 ms | `perf` de nivel 1 |
| NFR3.13 | nuevo | `201` de la consolidación del caso máximo | **p95 ≤ 6 s; máximo ≤ 8 s**, por debajo del plazo de 10 s de NFR10.17. Mientras dura, una decisión de U5 sobre la misma ronda puede recibir `503` (riesgo declarado en tech-stack §6) | 10 consolidaciones | `perf` de nivel 1 |
| NFR3.14 | nuevo | `purge_session` de ReviewReport (F10) llamada por el `Job` de retención | **p95 ≤ 2 s** con 10 versiones y 100 exportaciones; cada borrado de archivo dentro de 5 s (NFR10.17). Responde a la pregunta 4 de §12 | 20 purgas | `perf` de nivel 1 con el usuario `veridicus_retention` |

## 3. Consola (NFR3, interfaz no bloqueante)

| ID | Estado | Requisito | Criterio medible |
|---|---|---|---|
| NFR3.9 | se mantiene | La consolidación no bloquea la consola ni se envía dos veces. | Desde el clic en «Consolidar» (BR8.1), el botón pasa a «Consolidando…» deshabilitado en ≤ 100 ms y sale **una sola** petición aunque se pulse 5 veces; el resto de la consola sigue respondiendo. Con el `201`, la vista de BR8.2 aparece en ≤ 1 s. Vitest con un servidor *fake* que tarda 2 s y Playwright de nivel 3. |
| NFR3.10 | cambia | «Finalizar y Consolidar» se habilita sin recargar cuando desaparecen los bloqueos. | Con el sondeo de U4 (2 s con corridas en curso, 15 s sin ellas), cuando la última corrida termina o se decide la última pendiente, `consolidation_blockers` se vacía y el botón se habilita en ≤ 3 s con corridas en curso y en ≤ 1 s tras una decisión. Playwright de nivel 3 con el *fake* del juez. |
| NFR3.11 | cambia | La exportación no congela la consola. | «Descargar reporte» envía `POST /exports` con CSRF; el botón queda «Preparando…» deshabilitado mientras la petición está pendiente y el archivo se entrega al navegador desde la respuesta. La consola muestra el `export_sha256` de `X-Veridicus-Export-SHA256` en ≤ 1 s desde la respuesta. Playwright de nivel 3 compara el SHA-256 del archivo bajado con el mostrado y comprueba la marca del usuario en la cabecera. |
| NFR3.15 | nuevo | El sondeo no vuelve a pedir la vista previa ni exporta. | Con M5 abierta 60 s y el sondeo activo, la consola hace 0 peticiones a `/download` y 0 a `/exports` además de las que pide el usuario (Vitest que cuenta peticiones del *fake*). Así el recálculo del SHA-256 (NFR3.4) y el registro de acceso ocurren solo por acción humana. |

## 4. MTTV (NFR7)

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR7.1 | cambia | El MTTV medio es < 10 minutos sobre las sesiones **guiadas** del conjunto sintético (BR7.1, P7 = A). | El arnés `evaluation/mttv/mttv.py` lee por la API, con una cuenta de analista sintética, `finalized_at` y el `consolidated_at` de la **versión 1** de cada sesión de la corrida. La corrida carga **todas** las transcripciones del conjunto sintético versionado de `evaluation/` (40 hoy) como sesiones guiadas con un bloque pegado y registra sus `session_id` en su reporte JSON (NFR-U7-10). MTTV de cada caso = `consolidated_at(v1) − finalized_at` en segundos; **media < 600 s**. El reporte registra cada caso, la media, el máximo y cuántos superan 600 s (informativo). Una sesión importada no da muestra; una guiada sin versión 1 hace fallar la corrida. La revisión la hace el analista en la consola: el arnés **nunca** decide ni consolida (AUTONOMIA-03). | Nivel 2, fuera de la CI, con revisión humana; se adjunta al PR de la entrega etiquetada |
| NFR7.2 | se mantiene | El tiempo de servidor de U7 es una parte despreciable del MTTV. | p95 de NFR3.1 + p95 de NFR3.2 ≤ 1,7 s (≤ 0,3 % de 600 s); sumado a los 9 s de U5, el sistema consume ≤ 2 % del MTTV. | Nivel 1 (`perf`) |
| NFR7.3 | cambia | Las marcas de MTTV las pone el servidor y se calculan igual en todas partes. | `finalized_at` y `consolidated_at` salen del reloj inyectable de U3 en UTC, nunca del navegador ni del cuerpo; las correcciones no cambian `finalized_at` ni la versión 1. La función pura `review_report/domain/mttv.py` (`mttv_seconds(origin, finalized_at, versions)`) es la referencia del arnés y de la métrica de NFR15.4. Casos de nivel 0: finalizar desde `open`, `paused`, `suspended` y `blocked`; versiones 1 y 2 (solo cuenta la 1); sin versión 1 → sin muestra; sesión importada → sin muestra aunque tenga versión 1; segundos fraccionarios se truncan. | Nivel 0 |

## 5. Recursos

| ID | Estado | Pod | Tope medido | Cómo se mide |
|---|---|---|---|---|
| NFR8.1 | cambia | API de `session-api` | Una consolidación del caso de 100 turnos añade ≤ 48 MiB al pico de RSS; una del caso máximo ≤ 64 MiB; 3 simultáneas del caso máximo de sesiones distintas ≤ 192 MiB. Una vista previa o una exportación de 8 MiB añade ≤ 32 MiB (archivo, marca y respuesta en memoria). Caben bajo el `limits.memory` de 768 MiB de Infrastructure Design (NFR-U7-11) | Pico de RSS en las pruebas `perf` de NFR3.2, NFR3.4, NFR3.12 y NFR3.13 frente a la misma corrida sin ellas |
| NFR8.9 | nuevo | API de `session-api` | Un Markdown de más de `report_max_bytes` no se escribe: la consolidación responde `413` `limits.exceeded` antes de crear el temporal, con 0 filas, 0 archivos y la ronda abierta (NFR-U7-01). La consola muestra el mensaje del catálogo y conserva la copia de trabajo | Nivel 1 con `report_max_bytes` rebajado por variable de entorno (solo puede bajar, `project.md`) a 64 KiB y el caso de 100 turnos |
