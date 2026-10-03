## Review

**Verdict:** READY
**Reviewer:** aidlc-architecture-reviewer-agent
**Date:** 2026-10-03T02:41:13Z
**Iteration:** 1

Revisión advisory de una sola pasada: los hallazgos son para que el humano los sopese en la aprobación.

### Findings

| ID | Severity | Location | Finding | Required action | Status |
|---|---|---|---|---|---|
| R-01 | Major | construction/voice/nfr-requirements/security-requirements.md > NFR10.4, T5, §5; tech-stack-decisions.md > D9 | El rastro del audio en Redis se declara «acotado», pero la reescritura del AOF la dispara el tamaño (`auto-aof-rewrite-min-size 16mb` más el porcentaje por defecto), no el tiempo. Con clips típicos de 10–30 s (≈ 0,3–1 MB) pasan decenas de turnos antes de reescribir, así que el audio sigue en el PVC bastante más que «tras unos 2 audios de 120 s». El criterio de NFR10.4 solo prueba que tras `BGREWRITEAOF` manual hay 0 apariciones; no prueba que la reescritura automática ocurra en un plazo definido. No rompe AUTONOMIA-04 (queda en el clúster), pero contradice el espíritu de «audio borrado tras confirmarlo» (FR10.4). | Fijar una cota temporal o de volumen que se pueda comprobar, por ejemplo `auto-aof-rewrite-percentage` bajo o un `BGREWRITEAOF` periódico, y probarla. Alternativa: aceptar el riesgo con un texto que diga «hasta 16 MB de escrituras» y no «unos 2 audios». | New |
| R-02 | Major | construction/voice/nfr-requirements/performance-requirements.md > NFR3.6, NFR3.7; security-requirements.md > §6 | U9 cambia comportamiento de U4 y de C2 y no lo recoge en la tabla de precisiones de §6: la tarea de plazos de BR5.8 pasa a cubrir la etapa `transcribing`, `deadline_at` se recalcula al publicar en C2, y existe un valor de `processing_stage` `transcribing` con estados `queued`/`processing`. §6 solo anota `Turn.transcription_model_digest` de U4. Quien implemente U4 no sabrá que debe cubrir estos casos. | Añadir a §6 las filas de BR5.8 de U4 (barrido de `transcribing`), el recálculo de `deadline_at` y la etapa `transcribing`, para que el humano decida en la aprobación si se actualiza U4. | New |
| R-03 | Minor | construction/voice/nfr-requirements/performance-requirements.md > NFR3.5; reliability-requirements.md > NFR10.14 | La base de 300 s se justifica con 90 + 120 + 90 = 300 s (dos entregas), margen cero. Pero NFR10.14 permite 3 entregas, y la 3.ª ocurriría hacia los 510 s, después del plazo. El camino «3.ª entrega → `turn.error.system`» es inalcanzable con `m = 0`, y la prueba de NFR10.14 no dice con qué plazo se ejercita. La validación de arranque solo exige base > 210 s. | Alinear las cifras: exigir base ≥ 90 + 2×120 + 90 + margen, o bajar a 2 entregas, y precisar el plazo de la prueba de NFR10.14. | New |
| R-04 | Minor | construction/voice/nfr-requirements/performance-requirements.md > NFR3.1, NFR3.3; inception/requirements-analysis/requirements.md > NFR3 (línea 239) | El requisito aprobado acepta «8–12 s por turno» de voz en CPU. U9 lo reinterpreta como solo la transcripción (p95 ≤ 12 s para 30 s de audio) y fija el turno completo en 75 s (100 s con 120 s de audio). P2 = A del humano aprobó el p95 de 12 s, no los 75 s ni los 100 s, que salen de sumar el p95 de 60 s de U4. La reinterpretación no figura en §6. | Registrar en la tabla de precisiones que «por turno» se mide como transcripción, y que los 75 s y 100 s son derivados, para que el humano lo confirme. | New |
| R-05 | Minor | construction/voice/nfr-requirements/performance-requirements.md > NFR3.1, NFR3.8; scalability-requirements.md > NFR8.5, NFR8.8 | NFR3.1 se mide «uno a la vez, cola vacía», pero Whisper `base` con 4 hilos comparte CPU con el juez cuantizado de U2 en la misma máquina. NFR8.8 lo detecta solo como «hallazgo» después. Además, si el cliente corta a los 90 s, no se dice si `model-whisper` cancela la transcripción: si no cancela, la siguiente espera detrás de un trabajo ya descartado. | Medir NFR3.1 también con un turno de texto del juez en paralelo. Declarar qué hace `model-whisper` al cortarse la conexión. | New |
| R-06 | Minor | construction/voice/nfr-requirements/security-requirements.md > NFR10.8; §6 | NFR10.8 depende del puerto `is_question_approved(question_id)` de U8 (NFR10.7 de U8). `contract-summary.md` no define ese puerto; solo declara la ruta de audio y su `409`. No pude abrir el archivo de NFR de U8 (el alcance de la revisión lo bloqueó), así que no verifiqué que el puerto exista con esa firma. | Confirmar en U8 que el puerto existe, o añadirlo a la tabla de precisiones como contrato en proceso entre U8 y U9. | New |
| R-07 | Minor | construction/voice/nfr-requirements/security-requirements.md > NFR10.9, NFR1.2 | El Bearer de la ruta interna de síntesis viaja por `http(s)`, y NFR1.2 admite `http`: dentro del clúster va en claro. | Declarar que `http` en el clúster es riesgo aceptado, o exigir `https`. | New |

### Validation Tool Results

| Tool | Result | Interpretation |
|---|---|---|
| Script de `traceability.json` | PASS: JSON válido, 67 IDs `NFRx.y` definidos en los artefactos, ninguno citado queda sin definir | Cobertura NFR1–NFR15 correcta; NFR6, NFR7 y NFR9 son N/A con motivo |
| Cruce de P1 y P2 contra los artefactos | PASS | 6 MB con base64 en el mensaje (8 000 000 de `maxLength`) y Whisper `base` int8 aparecen de forma coherente en D1, D5, NFR3.1, NFR3.2 y NFR10.1 |

### Summary

Los artefactos son completos, medibles y coherentes con P1 y P2, la frontera de AUTONOMIA-04 está declarada por componente y la trazabilidad valida. Lo que el humano debería sopesar es la cota real del audio en el AOF (R-01) y los cambios a U4 que faltan en la tabla de precisiones (R-02). Ninguno bloquea.
