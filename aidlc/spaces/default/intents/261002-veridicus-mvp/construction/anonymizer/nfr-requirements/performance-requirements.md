# Requisitos de rendimiento — U10 anonymizer

**Revisión 2 (2026-11-22): segunda pasada por el cambio 01, la adenda 02 y el Functional Design
revisión 2.** Sustituye a la revisión 1 del 2026-10-03.
- **IDs.** Se conservan los IDs. Lo retirado queda «Retirado» y lo nuevo toma el número siguiente
  (NFR3.6).
- **Cambio principal.** La revisión 1 medía un proxy apagado delante del juez interno. Ahora U10 está
  en el camino de **toda** llamada a un proveedor comercial, tanto en la CLI como en el clúster. NFR3
  pide recalcular las latencias con el anonimizador en el camino.

**Insumos.**
- F1, F3, F4, F5 y F8 y los escenarios de `functional-design/functional-spec.md` (functional-spec).
- BR1.1, BR1.5, BR2.4, BR5.2 y BR6.1 de `functional-design/rules.md` (rules).
- NFR3 y NFR8 de `inception/requirements-analysis/requirements.md` (requirements).
- C20, C21 y C25 de `inception/contract-design/contract-summary.md` (contract-summary).
- FD-U10-13 y la respuesta P2 = A de `nfr-requirements-questions.md`.

Las mediciones de nivel 0 corren en la máquina de desarrollo (CPU, sin GPU; NFR2), con el
`FakeTransport` y transcripciones sintéticas de tres tamaños: 10 000, 50 000 y 186 000 caracteres. La
mayor reproduce el tamaño de la entrevista más larga del piloto. Cada medición hace 3 corridas de
calentamiento y 20 medidas, y la prueba usa el p95. El reporte queda en `out/anonymizer-perf.json`.

## 1. Requisitos

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR3.1 | cambia | La seudonimización crece de forma lineal con el texto (F4: NER, reglas, palabras permitidas y red de seguridad). | p95 de `masking_ms` ≤ **0,8 s por cada 10 000 caracteres** en los tres tamaños, y ≤ **15 s** con 186 000 caracteres. La razón entre el p95 de 186 000 y el de 10 000 es ≤ 25: no hay crecimiento cuadrático. El NER ya está cargado; no cuenta el arranque. | Nivel 0 (`-m perf`) |
| NFR3.2 | cambia | El proxy agrega poco a la llamada, sin contar la seudonimización ni el proveedor (F8). | p95 de (tiempo total de `POST /v1/generate`) − `masking_ms` − `upstream_ms` ≤ **50 ms**, con un cuerpo de 186 000 caracteres y el `FakeTransport` respondiendo al instante. Incluye leer y validar el cuerpo, resolver el perfil, restaurar y serializar. | Nivel 0 |
| NFR3.3 | cambia | El arranque termina en un tiempo acotado (F3). | Desde que empieza el proceso hasta que `/readyz` responde 200 (NER cargado y archivos de NFR10.11 comprobados) pasan ≤ **60 s** en CPU. En la CLI, construir el módulo tarda lo mismo como máximo. La sonda de arranque que declara U2 debe tolerar ese tiempo. | Nivel 1 |
| NFR3.4 | cambia | La detección por reglas corre en tiempo lineal. | Con `google-re2`, una entrada adversaria de 100 000 caracteres (repeticiones que harían retroceder a `re`) termina la detección por reglas en < **1 s**. Una prueba confirma que ninguna regla de `DetectionRuleSet` compila con `re`. | Nivel 0 |
| NFR3.5 | cambia | La seudonimización tiene un presupuesto, y pasarlo falla cerrado (FD-U10-13). | El presupuesto es `anonymizer_masking_budget_ratio` (0,15; NFR-U10-02) × `timeout_s` de la petición. Si `masking_ms` lo supera, `generate` termina en `AnonymizerUnavailable` con **0 peticiones** al transporte (F7). Prueba con un NER *fake* lento. El valor sale de C25 y una variable de entorno solo puede bajarlo. | Nivel 0 |
| NFR3.6 | nuevo | U10 da los datos con los que U11 recalcula las latencias por turno y por modo final (NFR3). | Cada llamada deja en el log `masking_ms` y `upstream_ms` (NFR10.3), y el histograma de NFR15.1. Las comprobaciones de NFR-U10-04 atan `model_call_timeout_s` al costo de NFR3.1: con 186 000 caracteres, ese plazo debe ser ≥ 200 s. Las latencias por turno, por modo final y el *N* de la prueba de humo los fija U11 con el perfil de la primera rebanada (juez de Anthropic, P2 = A), contando la red. | Nivel 0 (comprobación); el recálculo es de U11 |
| NFR9.1 | Retirado | Latencia de los *embeddings* enmascarados. | Retirado con NFR9 y con `embed` (cambio 01). | — |
| NFR8.1 | cambia | El proxy no frena la prueba de carga de NFR8. | Durante la prueba de NFR8 (50 sesiones de texto en tandas de 3 concurrentes, con un perfil comercial), el proxy responde **0** veces `503` por saturación (NFR8.2) y su contenedor tiene **0** `OOMKilled`. Ningún fallo de la prueba tiene a U10 como causa, salvo uno que devuelva el proveedor. Lo comprueban `veridicus_anonymizer_requests_total` y los eventos del pod. | Prueba de carga de NFR8 (la corre su unidad dueña; reporte en el PR de entrega) |

## 2. Lo que este documento no fija

- **Latencia del proveedor.** Depende de la red y del modelo. La mide `upstream_ms`, y el plazo lo
  limita `timeout_s` del perfil (NFR10.4).
- **Latencias por turno, por modo final y *N* de la prueba de humo.** Son de U11 (NFR3), con los datos
  de NFR3.6.
- **Recursos (`requests`/`limits`) del pod.** Los declara U2 con el pico de memoria de NFR8.3 (ver
  `scalability-requirements.md`).
