# Requisitos de escalado — U8 assistant-extras

**Revisión 2 (2026-11-22), segunda pasada por el cambio 01 (DT27), la adenda 02 y el Functional Design
revisión 2 de U8.** Sustituye a la revisión 1 del 2026-10-03. Los IDs se conservan; ninguno se retira.
NFR8.6 y NFR8.7 están en `reliability-requirements.md`.

**Insumos.**
- Flujos F5, F6 y F8 y §9 de `functional-design/functional-spec.md` (functional-spec); reglas BR5.8,
  BR5.10, BR5.12, BR6.1 y BR6.2 de `functional-design/rules.md` (rules).
- NFR2 y NFR8 y los supuestos de `inception/requirements-analysis/requirements.md` (requirements).
- C3, C6 y C25 de `inception/contract-design/contract-summary.md` (contract-summary).
- Lo que fijaron hoy U4 (una corrida a la vez en todo el sistema, cola de hasta 60 incrementales, prueba
  de carga con `comercial-piloto`) y U11 (98 % de corridas completas, verificador local con una ranura).

## 1. Carga esperada

| Dimensión | Valor | Origen |
|---|---|---|
| Permutación | Activa en todos los perfiles | P5 = A; BR6.1 |
| Llamadas al verificador por candidato | 2 en serie (directa y permutada), en la misma ranura del servidor local | BR6.2; decisión de U11 |
| Aclaraciones por corrida | ≤ 1 por hallazgo emitido, deduplicadas | BR5.1, BR5.8 |
| Aclaraciones por sesión | ≤ hallazgos de la sesión (deduplicadas por sesión); se prueba con 100 | BR5.10; NFR-U8-03 |
| Decisiones por aclaración | Exactamente 1 | BR5.12 |
| Prueba de carga de NFR8 | 50 sesiones en tandas de 3, con `comercial-piloto` y la permutación activa | NFR8; decisión de U4; NFR-U8-06 |

## 2. Requisitos

| ID | Estado | Requisito | Criterio medible |
|---|---|---|---|
| NFR8.1 | cambia | La prueba de carga de NFR8 corre con la permutación activa (P5 = A). | `evaluation/load/run_batches.py` registra `config_sha256` y el perfil de cada sesión y falla si alguna usa un perfil con `permutation: false`. El umbral de ≥ 98 % se mide así (NFR-U8-06) |
| NFR8.2 | cambia | La cola de U4 absorbe la permutación sin un tope propio de U8. | La capacidad de la cola de U4 (60 incrementales por delante con el p95 de 180 s de U11) ya cuenta la permutación: U8 no añade llamadas al juez ni corridas. La cifra es **orientativa**, porque toma el p95 como media; el criterio medible es NFR8.7 (`reliability-requirements.md`) y 0 corridas vencidas por plazo en la prueba de carga |
| NFR8.3 | cambia | La permutación y las aclaraciones no suben los picos de memoria. | Durante la medición de BR6.5 y la prueba de carga: `semantic-agent` ≤ 768 MiB y el trabajador de `session-api` ≤ 512 MiB (topes de U4); el servidor del verificador local sin cambio de memoria entre la llamada directa y la permutada (misma ranura). El reporte registra el pico de cada pod. Superar un tope es un hallazgo que se corrige por PR |
| NFR8.4 | cambia | U8 no impide más réplicas. | Ni `semantic-agent` ni `session-api` guardan estado de las aclaraciones en memoria; la deduplicación de la sesión la hace la base (`(session_id, turnos, tema_key)` único) y la decisión bloquea la fila. Prueba de nivel 1: dos ingestas simultáneas de corridas con la misma aclaración dejan una fila, y dos decisiones simultáneas dan una `200` y una `409` |
| NFR8.5 | cambia | Las tablas de U8 crecen de forma acotada. | Como mucho una `ConductorObservation` por hallazgo distinto de la sesión y una `ConductorObservationDecision` por aclaración; estimado < 5 MB en el MVP. Se conservan como historial (NFR11) y las purga la retención con la sesión (NFR11.5) |

## 3. Efecto de la permutación en la cola

- **Rendimiento.** La permutación duplica las llamadas al verificador local por candidato. Con
  `comercial-piloto`, U11 ya la cuenta en su p95 de 180 s y en el plazo de 900 s. Con `todo-local`, el
  juez también es local y la corrida tarda más; el criterio para mantenerla es NFR8.7.
- **Señal.** Las de U4: `veridicus_run_queue_depth` sostenido por encima de 10 o
  `veridicus_run_queue_wait_seconds` cerca de su tope.
- **Qué hacer si no alcanza**, en este orden, cada paso por PR con su medición:
  1. apagar la permutación en `todo-local` si incumple NFR8.7 (NFR-U8-01);
  2. usar en la demostración un perfil más rápido (GPU o comercial);
  3. las opciones de escalado de U4.
  Nunca se suben los plazos ni se baja el 98 % para que pase.
