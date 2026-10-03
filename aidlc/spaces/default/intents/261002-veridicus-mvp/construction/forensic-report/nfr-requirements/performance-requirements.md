# Requisitos de rendimiento — U7 forensic-report

**Insumos.** Flujos F1–F7 de `functional-design/functional-spec.md` (functional-spec) y reglas BR1.3,
BR2.5, BR3.2, BR3.3, BR4.1, BR5.1 y BR7.1 de `functional-design/rules.md` (rules); NFR2, NFR3, NFR7 y
NFR8 de `inception/requirements-analysis/requirements.md` (requirements); C1 (rutas de U7), C8 y C11 de
`inception/contract-design/contract-summary.md` (contract-summary); `nfr-requirements-questions.md`
(sin preguntas nuevas: las metas salen de lo ya decidido).

Todas las metas se miden en la **máquina de desarrollo con el perfil CPU** (NFR2), con PostgreSQL real
en contenedor y el volumen de reportes como un directorio real del sistema de archivos del contenedor
(nunca `tmpfs` ni un *mock*, porque `fsync` es parte del costo). U7 no llama a ningún modelo: sus tiempos
no dependen del juez. Las pruebas `perf` de nivel 1 corren en proceso, con `time.perf_counter` alrededor
de la llamada HTTP, como en U3, U4 y U5. Una prueba de rendimiento inestable se arregla o se pone en
cuarentena con un *issue*; nunca se reintenta ni se baja su umbral (team-practices).

## 1. Escenario de medición: el caso de 100 turnos

Todas las pruebas `perf` de U7 usan el mismo *fixture* sintético de nivel 1, construido con el catálogo
de nombres de U1 (NFR12.1):

| Elemento | Valor | Por qué |
|---|---|---|
| Turnos | **100**: 60 de testimonio de 2 000 caracteres (el máximo de BR5.1 de U4) y 40 del entrevistador de 500 caracteres | Cota superior del brief; supera los 60 turnos de testimonio que admite el pegado de U6 |
| Turnos en `error` | 3, con su `code` (BR2.6) | Recorre la rama «turno no evaluado» |
| Sugerencias de revisión | 50, todas decididas: 20 aceptadas con nota, 15 editadas con reformulación de 2 000 caracteres y 15 descartadas con nota de 2 000 caracteres | El doble de la carga esperada por sesión (NFR8.2 de U5) |
| Hechos No Documentados | 20 paquetes, cada uno con el texto del turno y 3 pasajes de 1 000 caracteres | Recorre BR3.1 completo |
| Rondas | Variante A: ronda 1 abierta (versión 1). Variante B: versiones 1 y 2 ya consolidadas y ronda 3 de corrección abierta (versión 3) | Mide la consolidación inicial y la de corrección |
| Tamaño del Markdown resultante | ≈ 470 KB (medido y registrado por la prueba; tope de NFR8.5) | Base del costo de render, escaneo, SHA-256 y descarga |

## 2. Latencia de las rutas de U7

| ID | Qué se mide | Objetivo | Carga | Cómo se mide |
|---|---|---|---|---|
| NFR3.1 | Respuesta `200` de `POST /sessions/{id}/finalize` (F1): autorización, `snapshot`, transición con historial y *commit* | **p95 ≤ 200 ms** | 50 finalizaciones, cada una sobre una sesión nueva del caso de 100 turnos, con 0 y con 5 turnos en curso | Prueba `perf` de nivel 1 |
| NFR3.2 | Respuesta `201` de `POST /sessions/{id}/reports` (F2 y F6): bloqueo de la ronda, guardia, armado, render, escaneo C8, SHA-256, archivo temporal + `fsync` + renombrado, inserción de `ReportVersion`, `lock_round`, transición de sesión y *commit* | **p95 ≤ 1 500 ms**; máximo ≤ 2 000 ms (por debajo del `lock_timeout` de 2 s de U5, NFR10.13) | 30 consolidaciones de cada variante (A y B), cada una sobre una copia nueva del *fixture* | Prueba `perf` de nivel 1; el reporte de la prueba registra también el desglose de NFR3.3 |
| NFR3.3 | Desglose de la consolidación (NFR3.2) | p95 por tramo: armado de `ReportContent` con las lecturas de C11 ≤ 300 ms; render ≤ 400 ms; escaneo C8 ≤ 200 ms; SHA-256 ≤ 20 ms; escritura + `fsync` + renombrado ≤ 300 ms; inserción + `lock_round` + transición + *commit* ≤ 150 ms (NFR3.5 de U5 para lo que toca a U5) | Las mismas corridas de NFR3.2 | Tramos medidos con `perf_counter` en la capa de aplicación, solo en la prueba (no son métricas de producción) |
| NFR3.4 | Respuesta `200` de `GET /reports/{id}/download`: lectura completa del archivo, SHA-256 recalculado, comparación y envío (F3) | **p95 ≤ 250 ms** para el caso de 100 turnos; **p95 ≤ 500 ms** para un archivo de 2 MiB (tope de NFR8.5) | 100 descargas de cada tamaño | Prueba `perf` de nivel 1 |
| NFR3.5 | Respuesta `200` de `GET /sessions/{id}/reports` | p95 ≤ 100 ms con 10 versiones | 100 llamadas | Prueba `perf` de nivel 1 |
| NFR3.6 | Rechazos sin render (`403`, `409` de BR2.2–BR2.4 y BR2.7, `409 report.not_consolidated`, `409 session.finalized`) | p95 ≤ 150 ms, 0 filas y 0 archivos (ni temporales) | 50 peticiones por cada `code` | Prueba `perf` de nivel 1 que además lista el volumen |
| NFR3.7 | Rechazo `409 report.forbidden_vocabulary` (BR3.3), que sí renderiza y escanea | p95 ≤ 1 000 ms, 0 filas y 0 archivos | 30 consolidaciones con un término de C8 sembrado en un texto del sistema (*fixture* de prueba) | Prueba `perf` de nivel 1 |
| NFR3.8 | `POST /sessions/{id}/correction-rounds` (F4) y el descarte (F5) | p95 ≤ 200 ms cada una | 50 de cada una | Prueba `perf` de nivel 1 |

## 3. Consola (NFR3, interfaz no bloqueante)

| ID | Requisito | Criterio medible |
|---|---|---|
| NFR3.9 | La consolidación no bloquea la consola ni se envía dos veces. | Desde el clic en «Consolidar» del diálogo (BR8.1), el botón pasa a «Consolidando…» deshabilitado en ≤ 100 ms y se envía **una sola** petición aunque se pulse 5 veces; el resto de la consola (transcripción, lista de versiones, cerrar sesión web) sigue respondiendo mientras tanto. Con la respuesta `201`, la vista de BR8.2 aparece en ≤ 1 s. Prueba Vitest con un servidor *fake* que tarda 2 s y prueba Playwright de nivel 3. |
| NFR3.10 | El botón «Finalizar y Consolidar» se habilita sin recargar cuando desaparecen los bloqueos. | Con el sondeo de U4 (2 s con turnos en curso, 15 s sin ellos, NFR3.7 de U4), cuando el último turno en curso termina o se decide la última sugerencia pendiente, `consolidation_blockers` se vacía y el botón se habilita en ≤ 3 s si había turnos en curso, y en ≤ 1 s tras una decisión (la decisión vuelve a pedir la sesión, NFR3.7 de U5). Prueba Playwright de nivel 3 con el *fake* del juez. |
| NFR3.11 | La descarga no congela la consola. | «Descargar reporte» usa un enlace con `Content-Disposition: attachment` (el navegador descarga solo) y la consola muestra el SHA-256 de la cabecera `X-Veridicus-SHA256` junto a la descarga en ≤ 1 s desde la respuesta. Prueba Playwright de nivel 3 que compara el SHA-256 del archivo descargado con el mostrado. |

## 4. MTTV (NFR7)

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR7.1 | El MTTV medio es < 10 minutos sobre el Golden Dataset. | El arnés `evaluation/golden/mttv.py` lee, por la API y con una cuenta de analista sintética, `finalized_at` (de `SessionSummary`, C1) y el `consolidated_at` de la **versión 1** (de `GET /sessions/{id}/reports`) de las 11 sesiones de la corrida (10 transcripciones y el caso de Hecho No Documentado), cuyos `session_id` registra el reporte JSON de la corrida de nivel 2. MTTV de cada caso = `consolidated_at(v1) − finalized_at` en segundos (BR7.1); **media < 600 s**. El reporte JSON registra cada caso, la media, el máximo, cuántos superan 600 s (informativo) y, por caso, el tiempo entre `finalized_at` y el último turno evaluado si fue posterior (espera de turnos, que sí cuenta en el MTTV). Una sesión sin versión 1 hace fallar la corrida. La revisión la hace el analista en la consola: el arnés **nunca** decide ni consolida (AUTONOMIA-03). | Nivel 2 (arnés fuera de la CI, revisión humana real); se adjunta al PR de la entrega etiquetada |
| NFR7.2 | El tiempo de servidor de U7 es una parte despreciable del MTTV. | p95 de NFR3.1 + p95 de NFR3.2 ≤ 1,7 s, es decir ≤ 0,3 % del objetivo de 600 s; sumado a los 9 s de U5 (NFR7.1 de U5), el sistema consume ≤ 2 % del MTTV. Se comprueba con las mediciones de NFR3.1 y NFR3.2. | Nivel 1 (`perf`) |
| NFR7.3 | Las marcas de MTTV las pone el servidor y se calculan igual en todas partes. | `finalized_at` y `consolidated_at` salen del reloj inyectable de U3 (D12 de U3) en UTC en la capa de aplicación de `session-api`, nunca del navegador ni del cuerpo de la petición; las correcciones no cambian `finalized_at` ni la versión 1. La función pura `forensic_report/domain/mttv.py` (`mttv_seconds(finalized_at, versions)`) es la referencia que usan el arnés y la métrica de NFR15.4. Casos de nivel 0: finalizar desde `open` y desde `suspended`; versiones 1 y 2 (solo cuenta la 1); sin versión 1 → sin muestra; reloj con segundos fraccionarios (se trunca a segundos enteros). | Nivel 0 |

## 5. Recursos

| ID | Pod | Tope medido | Cómo se mide |
|---|---|---|---|
| NFR8.1 | API de `session-api` | Una consolidación del caso de 100 turnos añade ≤ 48 MiB al pico de RSS del proceso; 3 consolidaciones simultáneas de 3 sesiones distintas (NFR8.2) añaden ≤ 96 MiB. La descarga de un archivo de 2 MiB añade ≤ 16 MiB. El `limits.memory` que fije Infrastructure Design suma este margen a los de U3, U4 y U5 | Pico de RSS durante las pruebas `perf` de NFR3.2 y NFR3.4, frente a la misma corrida sin consolidar |
