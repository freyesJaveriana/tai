## Review

**Verdict:** READY
**Reviewer:** aidlc-architecture-reviewer-agent
**Date:** 2026-10-03T02:23:10Z
**Iteration:** 1

### Findings

| ID | Severity | Location | Finding | Required action | Status |
|---|---|---|---|---|---|
| R-01 | Major | aidlc/spaces/default/intents/261002-veridicus-mvp/construction/session-lifecycle/nfr-requirements/performance-requirements.md > NFR3.10, NFR3.11; scalability-requirements.md > NFR8.4 | El límite de 60 turnos de testimonio (P2 = A) se justifica porque "caben" en el tope de 3 600 s, pero el propio NFR8.4 reconoce que al p95 de 60 s por turno el turno 60 termina justo en el tope, sin margen. Con la fórmula de NFR3.10 (300 s × posición, tope 3 600 s) el turno 60 siempre recibe el tope. Con cualquier turno ajeno en cola (n₀ > 0) o con latencia algo mayor, NFR3.11 (0 `turn.error.timeout`) falla por diseño, y el criterio de aceptación queda inestable. | Decidir antes de aprobar: bajar el límite (p. ej. 40 turnos, con margen medido), o contar el plazo desde que el turno empieza a procesarse, o fijar en NFR3.11 la latencia por turno bajo la cual se exige 0 vencimientos. Si se mantiene 60, registrar en NFR3.11 que el resultado depende de la latencia medida. | New |
| R-02 | Major | .../nfr-requirements/tech-stack-decisions.md > D3 vs D1, D2; performance-requirements.md > NFR3.7, NFR3.8; reliability-requirements.md > NFR8.8, NFR8.9 | D3 exige que latido y revisión usen `now()` de PostgreSQL y a la vez que "el reloj se controle con una función de hora inyectada en la sesión de base de datos". `now()` no se puede inyectar y es la hora de inicio de la transacción; el mecanismo no está definido. NFR3.7 (bordes 179/180 s), NFR3.8 (165 s), NFR8.8 y NFR8.9 dependen de ese reloj controlado, así que no se pueden implementar tal como están escritos sin decidir cómo. | Especificar el mecanismo: p. ej. pasar la hora como parámetro de la sentencia con valor por defecto `now()` en producción, o una función SQL propia del esquema que las pruebas sustituyen. Dejar claro que el parámetro nunca llega por la API. | New |
| R-03 | Minor | .../nfr-requirements/security-requirements.md > §6 Precisiones; rules.md BR2.3; entities.md TranscriptPaste | Las cifras nuevas (60 turnos de testimonio, 200 en total, 524 288 bytes) son normativas en estos artefactos, pero `rules.md` aprobado sigue diciendo 100 turnos. El tope de 200 turnos totales no salió de una pregunta al humano ni tiene medición propia, y los 100 000 caracteres ya acotan el pegado. Si en la aprobación no se actualiza el original, Code Generation recibirá dos valores distintos. | Pedir al humano que decida en la aprobación qué artefactos se actualizan; justificar el tope de 200 o quitarlo. | New |
| R-04 | Minor | .../nfr-requirements/reliability-requirements.md > NFR10.11 | "Una entrega doble se absorbe por la ingesta idempotente de U4" cubre los resultados (C3). Si el `EXEC` se aplicó pero la respuesta venció a los 0,5 s y luego hay reintento o reenvío, C2 recibe turnos duplicados y el juez los evalúa dos veces (45–60 s de CPU cada uno), lo que adelanta los plazos de R-01. La prueba de nivel 1 solo detiene Redis; no cubre el reenvío con entrega previa exitosa. | Añadir una prueba de nivel 1: publicación duplicada con el mismo `turn_id` y `attempt` produce una sola evaluación (o documentar que la deduplicación es de `semantic-agent`, U4, y citar la regla). | New |
| R-05 | Minor | .../nfr-requirements/observability-requirements.md > §2 (`veridicus_sessions`, `veridicus_suspension_sweep_seconds`) | Las métricas del trabajador se declaran en el `/metrics` de `session-api`, pero la API y el trabajador son procesos distintos (D11 de U4). No se dice qué endpoint o puerto raspa las del trabajador. `veridicus_sessions` se actualiza solo en cada revisión (30 s), aunque la API también cambia estados. | Indicar el endpoint de métricas del trabajador (o referir al de U4) y aceptar o corregir el desfase de 30 s del gauge. | New |

### Validation Tool Results

| Tool | Result | Interpretation |
|---|---|---|
| traceability.json (script) | JSON válido; todos los NFRx.y citados existen salvo NFR5.1, que es de U4 y está citado en una fila N/A | La cobertura es consistente. NFR5, NFR6 y NFR7 en N/A están justificados |
| Contraste de roles y rutas con contract-summary C1 | Coincide (`/scenarios/{id}/versions` para `analista` y `admin`) | Sin hallazgo |

### Summary

El paquete es coherente, trazable y cumple AUTONOMIA-03/04/05 en sus pruebas. Los dos puntos que el humano debe sopesar son el límite de 60 turnos, que no deja margen frente al plazo de 3 600 s, y el reloj controlado de la suspensión, que no se puede inyectar con `now()` tal como está escrito. Ninguno es Crítico y hay 2 Major, por lo que el veredicto es READY.
