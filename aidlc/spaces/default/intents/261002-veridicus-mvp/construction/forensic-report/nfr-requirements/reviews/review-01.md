## Review

**Verdict:** READY
**Reviewer:** aidlc-architecture-reviewer-agent
**Date:** 2026-10-03T02:39:37Z
**Iteration:** 1

Revisión advisory de una sola pasada. Sin hallazgos Critical y 2 Major (dentro del límite de READY).

### Findings

| ID | Severity | Location | Finding | Required action | Status |
|---|---|---|---|---|---|
| R-01 | Major | aidlc/spaces/default/intents/261002-veridicus-mvp/construction/forensic-report/nfr-requirements/reliability-requirements.md > NFR10.20 (Job de verificación) frente a security-requirements.md > NFR10.6 y NFR1.2 | El Job de verificación monta el PVC `ReadWriteOnce` en solo lectura, pero NFR10.6 deja el directorio en `0700` y los archivos en `0400` con propietario el proceso de la API. Nada exige que el Job corra con el mismo UID/`fsGroup`, y un PVC RWO solo se monta en un segundo pod si está en el mismo nodo. Este Job es la comprobación de restauración (§6 de security) y de NFR8.8, así que podría no poder leer ni un archivo. | Fijar en NFR10.20/NFR1.2 el `securityContext` del Job (mismo UID y `fsGroup` que la API) y su afinidad al nodo del PVC, o dejar `verify_store` solo como comando dentro del pod de la API; añadir una prueba de nivel 0 sobre el manifiesto y de nivel 1 con UID distinto. | New |
| R-02 | Major | .../nfr-requirements/reliability-requirements.md > NFR8.8 y NFR10.16; tech-stack-decisions.md > tabla de riesgos (fila del hilo del volumen que vence) | NFR8.8 exige 0 huérfanos de más de 300 s tras toda la suite de nivel 1, que incluye los fallos inyectados de volumen lento (NFR10.17). Pero el hilo vencido no se puede cancelar y su archivo puede aparecer después del rollback, y el barrido (NFR10.16) corre solo al arrancar; la propia tabla de riesgos lo acepta hasta el siguiente arranque. Criterio y mitigación se contradicen: en un pod de larga vida el huérfano permanece y NFR8.8 falla o se cumple solo si la suite reinicia la API. | Definir el mecanismo: barrido periódico (o al vencer el timeout) con la misma edad mínima, o relajar NFR8.8 a «tras el barrido de arranque» y decir cómo la prueba lo fuerza. | New |
| R-03 | Minor | .../nfr-requirements/traceability.json > coverage NFR8 y NFR10; reliability-requirements.md (IDs NFR8.7, NFR8.8, NFR10.12–NFR10.22) | `requirements.md` define NFR8 como éxito del pipeline (≥ 50 sesiones en tandas de 3, ≥ 98 %) y NFR10 como seguridad de aplicación. U7 usa NFR8.x para recursos, escalado y fiabilidad, y NFR10.12–22 para atomicidad, plazos y arranque. La regla «hereda el ID del NFR de Inception que detalla» no se cumple y el sensor de trazabilidad queda en OK sin que el criterio de 98 % tenga contraparte en U7. | Anotar en la trazabilidad que son sub-IDs locales (o renumerar bajo el NFR correcto) y declarar si NFR8 de Inception se cubre solo vía NFR8.2. | New |
| R-04 | Minor | .../nfr-requirements/performance-requirements.md > NFR3.2 frente a reliability-requirements.md > NFR10.13 y NFR10.17 | El máximo de la consolidación (≤ 2 000 ms) iguala el `lock_timeout` de 2 s, sin margen, mientras NFR10.17 permite hasta 10 s de consolidación. Una ganadora lenta pero válida (> 2 s) convierte a la perdedora en `503` en lugar de `409 report.conflict`; esto solo queda cubierto por la prueba de 3 s. | Declarar que `503` es el resultado esperado de la perdedora cuando la ganadora supera el `lock_timeout`, y el mensaje que ve el analista (que reintente a mano). | New |
| R-05 | Minor | .../nfr-requirements/security-requirements.md > §5 Riesgos aceptados; reliability-requirements.md > §4 | El cifrado en reposo y el RPO/RTO de los reportes se difieren a Infrastructure Design sin valores ni criterio de aceptación, a pesar de que NFR8.5 declara los archivos evidencia de auditoría sin purga. | Fijar cifras mínimas (p. ej. RPO ≤ el del respaldo de CloudNativePG) o registrarlas como entrada obligatoria de Infrastructure Design con dueño. | New |

### Validation Tool Results

| Tool | Result | Interpretation |
|---|---|---|
| traceability.json (script) | JSON válido; los 15 NFR de requirements.md están cubiertos; todos los NFRx.y citados existen como filas en los artefactos | Sin referencias rotas; R-03 es de semántica, no de existencia |

### Summary

Los siete artefactos son medibles, trazables y coherentes con las reglas AUTONOMIA y la frontera del clúster; los dos puntos a sopesar son el Job de verificación sobre un PVC con permisos del propietario (R-01) y el barrido de huérfanos solo al arrancar frente a NFR8.8 (R-02).
