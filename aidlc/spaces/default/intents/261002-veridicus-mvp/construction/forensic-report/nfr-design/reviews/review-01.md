## Review

**Verdict:** READY
**Reviewer:** aidlc-architecture-reviewer-agent
**Date:** 2026-10-03T04:01:30Z
**Iteration:** 1

### Findings

| ID | Severity | Location | Finding | Required action | Status |
|---|---|---|---|---|---|
| R-01 | Major | aidlc/spaces/default/intents/261002-veridicus-mvp/construction/forensic-report/nfr-design/reliability-design.md > §2 diagrama («I -->\|falla\| C») y §3 «Invariante» | La limpieza síncrona borra el archivo cuando falla «INSERT, lock_round y commit». El invariante «un timeout nunca deja fila, así que la limpieza nunca borra un archivo registrado» solo está demostrado para el vencimiento del plazo del almacén (la fila se inserta después de `future.result()`). Un fallo del propio `COMMIT` es ambiguo (conexión cortada o `statement_timeout`/`idle_in_transaction_session_timeout` tras aplicarse el commit en el servidor): la fila puede existir y el código borraría su archivo. Resultado: versión registrada sin archivo, descargas con `409 report.integrity_mismatch` y SHA-256 sellado inutilizable, contra «archivo antes que fila» y NFR8.8. La prueba de nivel 0 con almacén fake solo cubre el camino del timeout. | Definir qué hace la limpieza ante un fallo del commit con resultado desconocido: tras el error, abrir una transacción nueva y consultar si existe la fila por `report_version_id`; borrar el archivo solo si no existe (y si existe, devolver el resultado como consolidado o `report.conflict`, sin borrar). Añadir a la prueba de nivel 0/1 un fallo inyectado después del commit efectivo (fila presente) que exija que el archivo permanezca. | New |
| R-02 | Minor | aidlc/spaces/default/intents/261002-veridicus-mvp/construction/forensic-report/nfr-design/performance-design.md > §1 «Bloqueo retenido»; logical-components.md > §3 (fila de la sesión «consolidación ≤ 2 s bajo bloqueo») | Se afirma que el bloqueo de sesión y ronda se retiene ≤ 2 s, pero el diseño de fiabilidad permite 5 s de volumen y 10 s de consolidación antes del commit (más la espera de la cola del executor de 2 hilos). Durante ese tiempo las decisiones y la ingesta de esa sesión reciben `503` por `lock_timeout` de 2 s en vez de `review.round_locked`. No rompe la corrección, pero el presupuesto declarado no coincide con el peor caso. | Corregir el texto a «típico ≤ 2 s, máximo 10 s» y anotar en la verificación que una decisión concurrente puede recibir `503` además de `review.round_locked`. | New |
| R-03 | Minor | aidlc/spaces/default/intents/261002-veridicus-mvp/construction/forensic-report/nfr-design/security-design.md > §3 «Lo que el analista vio (P1 = A)» y reliability-design.md > §1 «Cursor del diálogo» | La corrección de P1 depende de que el `expected_cursor` entregado por el sondeo de U4 sea exactamente el `change_seq` de la fila de la sesión (`current_seq = bump − 1`). El diseño de U5 dice que el cursor es `change_seq` y que ningún cambio visible confirma con un número menor, pero no se declara que el cursor del `SessionView` se lea de `interview_session.change_seq` y no del máximo de los `change_seq` de las filas hijas. Si fuera el máximo, un `bump` sin fila marcada (por ejemplo `finalize` de U7) dejaría un cursor siempre menor y causaría `409 report.view_outdated` permanentes. | Añadir una prueba de nivel 1 de punta a punta: finalizar, sondear y consolidar sin cambios intermedios debe dar `201`; y registrar en las precisiones que U4 devuelve el `change_seq` de la sesión como cursor. | New |
| R-04 | Minor | aidlc/spaces/default/intents/261002-veridicus-mvp/construction/forensic-report/nfr-design/reliability-design.md > §3 (`add_done_callback`) y §4 | La limpieza por `add_done_callback` corre en el hilo del almacén; si el volumen queda colgado y los 2 hilos están ocupados, el callback no corre hasta que el hilo termine y el archivo del caso permanece sin dueño (el diseño solo lo reconoce como «503 en ≤ 5,5 s»). El barrido al arrancar es el único respaldo y con 1 réplica puede tardar días. | Indicar el límite explícitamente (riesgo aceptado hasta que el hilo vuelva) o añadir un barrido periódico de bajo costo con el mismo margen de 300 s, como la opción C descartada en P2. | New |

### Verificación de integración y reglas

- AUTONOMIA-03: la consolidación solo entra por la ruta del analista dueño (import-linter con control negativo), `consolidated_by` viene del principal y `consolidated_at` de un reloj único, el cuerpo cerrado rechaza campos de actor y hora, `expected_cursor` se compara bajo el bloqueo de sesión y el escaneo C8 va antes del SHA-256 (§3 de security-design). Cumple.
- AUTONOMIA-04: cada componente declara dentro/fuera del clúster y los datos que cruzan (security-design §1; logical-components §1). Cumple.
- AUTONOMIA-02: cada control cita comando o prueba con umbral. Cumple.
- Orden de bloqueo: coincide con el §1 de U5 (`bump` de la sesión y después la ronda; `open_round(for_update=True)` hace el `bump` previo). La tabla de U7 lista finalizar y descartar con `bump` y la precisión sobre C11 queda registrada en la tabla de reliability-design §9. Coherente con la restricción de U5 de un único sitio con `FOR UPDATE` sobre `review_round`.
- Precisiones: no se editó ningún artefacto aprobado; cada desviación (cuerpo de `POST /reports`, `report.view_outdated`, `CancelToken`, `bump` en `discard_correction_round` y `finalize`) figura en tablas de precisiones.
- Descarga: ruta calculada, `O_NOFOLLOW`, lectura completa con `compare_digest` antes del primer byte y cabeceras `nosniff` y `no-store`. Sin hallazgos.

### Validation Tool Results

| Tool | Result | Interpretation |
|---|---|---|
| JSON de `traceability.json` (python3 `json.load`) | PASS | JSON válido con claves `stage`, `unit`, `upstream_ids`, `coverage` |
| Cobertura de `NFRx.y` frente a las filas de tabla de los cinco `*-requirements.md` y `tech-stack-decisions.md` | PASS: 63 requeridos, 63 cubiertos, 0 faltantes, 0 sobrantes | Cobertura exacta |
| Sensores de linter, type-check, claim-sources | No aplicables a prosa (no ejecutados) | Sin código en la etapa |

### Summary

El diseño es sólido en lo que más importa: consolidación explícita ligada al estado revisado, orden de bloqueo compatible con U5 y limpieza del archivo con testigo de cancelación. El hueco real es R-01: la limpieza tras un fallo ambiguo del `COMMIT` puede borrar el archivo de una versión ya registrada. Con un solo Major y tres Minor el veredicto informativo es READY, pero conviene resolver R-01 antes de aprobar.
