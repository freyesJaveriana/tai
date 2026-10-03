## Review

**Verdict:** READY
**Reviewer:** aidlc-architecture-reviewer-agent
**Date:** 2026-10-03T03:42:43Z
**Iteration:** 1

### Findings

| ID | Severity | Location | Finding | Required action | Status |
|---|---|---|---|---|---|
| R-01 | Major | aidlc/spaces/default/intents/261002-veridicus-mvp/construction/assistant-extras/nfr-design/reliability-design.md > §7 «Recuperación y objetivos» y §2; performance-design.md > §3 «Plazo y reclamo con los extras» | La recuperación por `XAUTOCLAIM` no cabe en el plazo. Con reclamo de 510 s y plazo base de 600 s (turno sin cola, `deadline_at = enqueued_at + base × (1 + n)`), el turno reclamado dispone de unos 90 s, y el diseño afirma que «se evalúa entero». Con los extras activos el p95 es 150 s y el peor caso 482,2 s. La guarda de reintento (`ahora + espera + 180 s < deadline_at`) deja el mensaje sin confirmar, el contador de entregas llega a 3 y el turno acaba en `turn.error.system`, o lo vence el barrido a los 600 s. La regla «plazo base > reclamo» solo exige orden, no presupuesto restante. El cambio 480 → 510 s (P1) no arregla esto. Contradice la promesa de NFR8.6/NFR8.7 y la tabla de recuperación de §7. | Fijar una regla que garantice presupuesto tras el reclamo (por ejemplo plazo base ≥ reclamo + peor caso de un turno, o `deadline_at` renovado al reclamar, citando lo que U4 define para «reintentar»). Si se acepta que un turno reclamado con extras puede vencer, declararlo en §7 como riesgo aceptado y ajustar las pruebas de nivel 0 de la validación al arrancar. | New |
| R-02 | Minor | aidlc/spaces/default/intents/261002-veridicus-mvp/construction/assistant-extras/nfr-design/performance-design.md > §3 tabla «Presupuesto de reintento por llamada» (13,6 s) | El presupuesto de 13,6 s y la suma de 482,2 s están fijados a 2 reintentos con esperas 2 s y 6 s. U4 los hace configurables (`VERIDICUS_JUDGE_TRANSIENT_RETRIES` 0–3, `VERIDICUS_JUDGE_RETRY_WAITS_SECONDS`, según su diseño de fiabilidad §10). Con 3 reintentos o esperas mayores, la validación al arrancar quedaría desactualizada. | Que la validación calcule el presupuesto desde esos dos ajustes en vez de usar una constante, con una prueba de nivel 0 que cambie el valor. | New |
| R-03 | Minor | aidlc/spaces/default/intents/261002-veridicus-mvp/construction/assistant-extras/nfr-design/reliability-design.md > §3 «Plazo de la pregunta opcional» | La comprobación `ahora + 5 + 60 + 15 < deadline_at` omite el tiempo de publicar C3 y de la ingesta posterior; el margen real frente al barrido es menor de lo que dice. La primera llamada de la segunda lectura tampoco tiene guarda de plazo, solo sus reintentos (§2). | Sumar un margen explícito de publicación e ingesta, o documentar por qué 15 s lo cubre. Añadir la guarda de plazo a la primera llamada de la segunda lectura o justificar su omisión. | New |
| R-04 | Minor | aidlc/spaces/default/intents/261002-veridicus-mvp/construction/assistant-extras/nfr-design/security-design.md > §6 «Pregunta inmutable una vez decidida» | El disparador solo bloquea cuando `OLD.status <> 'proposed'`. No restringe `NEW.status` a `approved`/`discarded`, ni exige `decided_by` y `decided_at` no nulos al decidir. Una actualización `proposed → proposed` con `decided_by` ya rellenado pasaría, y AUTONOMIA-03 pide registrar quién y cuándo. | Añadir un `CHECK` o una condición del disparador que exija `NEW.status IN ('approved','discarded')` con `decided_by` y `decided_at` no nulos, y una prueba de nivel 1. | New |
| R-05 | Minor | aidlc/spaces/default/intents/261002-veridicus-mvp/construction/assistant-extras/nfr-design/observability-design.md > §2 `veridicus_extras_enabled` y §4 reglas informativas | La métrica se fija al arrancar desde la configuración del despliegue, pero cada sesión copia las banderas al crearse. Con sesiones abiertas de otra configuración, la regla de cola `max(veridicus_extras_enabled) == 1 and queue_depth > 20` puede dar falsos positivos o negativos. Además `status`, `reason` y `outcome` entran como campos globales de la lista blanca de logs de U3. | Medir por sesión o por turno (por ejemplo desde las opciones de C2), o declarar la limitación. Acotar los campos nuevos de la lista blanca a los eventos de U8. | New |

### Validation Tool Results

| Tool | Result | Interpretation |
|---|---|---|
| `traceability.json` (JSON válido) | PASS: `stage`, `unit`, `upstream_ids`, `coverage` presentes, 60 entradas | Parsea sin error |
| Cobertura de `NFRx.y` frente a los cinco `*-requirements.md` | PASS: 60 ids en tablas, 60 en `coverage`, diferencias vacías en ambos sentidos | Cobertura exacta |
| Referencias cruzadas (P1 = A y P2 = A, precisiones, `text-flow` fiabilidad §2) | PASS | `call_judge_with_retry` existe en U4 y se invoca por llamada; la precisión sobre `timeout_s` está en la tabla de §8 |

**Atención especial.**
- **AUTONOMIA-05.** La pregunta no se pide si alguna afirmación es «no documentada», y se evalúa después de la regla de permutación, así que las degradadas también la bloquean. `permutation.py` solo recibe candidatas sobre el umbral, con 100 % de ramas. Sin hallazgo.
- **AUTONOMIA-03.** La pregunta pasa por esquema estricto de solo `text` y por el escáner de C8. La decisión es del dueño (analista), con `authorize` de U3 y anti-CSRF. U9 y U7 solo consumen preguntas `approved`. El indicio afectivo usa texto fijo y una lista validada sin términos de C8. Sin hallazgo, salvo R-04.
- **Reintento por llamada (P1) y plazo (P2).** Son coherentes entre sí. La suma de 482,2 s se verifica aritméticamente y 510 s la supera. El problema es el presupuesto tras el reclamo (R-01).
- **Extras apagados.** El evaluador decide las ramas con `options` de C2 antes de construir nada (NFR3.2). La carga de NFR8 falla si alguna sesión trae un extra en `true`. Sin cambio de comportamiento de U4.

### Summary

El diseño es coherente con los requisitos aprobados, las guardas de AUTONOMIA-03 y -05 están bien situadas y la trazabilidad cubre los 60 requisitos. El único hallazgo de peso es R-01: tras reclamar un mensaje a los 510 s solo quedan unos 90 s de los 600 s del plazo, de modo que la recuperación prometida no cabe. Conviene que el humano decida cómo resolverlo antes de aprobar. Los demás hallazgos son menores.
