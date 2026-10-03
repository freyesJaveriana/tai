## Review

**Verdict:** READY
**Reviewer:** aidlc-architecture-reviewer-agent
**Date:** 2026-10-03T11:02:22Z
**Iteration:** 1

### Findings

| ID | Severity | Location | Finding | Required action | Status |
|---|---|---|---|---|---|
| R-01 | Major | aidlc/spaces/default/intents/261002-veridicus-mvp/construction/session-lifecycle/infrastructure-design/infrastructure-specification.md > §1 Despliegue, fila «Entrada HTTP» | La fila afirma que la versión de escenario de ≤ 1 048 576 bytes «cabe» en el `proxy-body-size` del `Ingress`. Pero `POST /scenarios/{scenario_id}/versions` es `multipart/form-data` en `contract-summary.md`, y nginx cuenta el cuerpo completo (con delimitadores y cabeceras de parte). U2 y U4 solo fijan «≥ 1 MiB», no un valor con holgura. Un archivo en el tope exacto superaría 1 MiB y recibiría `413` del Ingress antes de llegar a la API, sin Problem Details. NFR3.5 se mide en `pytest -m perf` contra la API, sin pasar por el Ingress, así que ninguna puerta lo detectaría. | Fijar el `proxy-body-size` en un valor explícito con margen para el *multipart* (por ejemplo 2 MiB) y registrarlo en la tabla de precisiones. Añadir una comprobación de nivel 0 en `deploy-level0.yml` que lo compare con el tope del catálogo más el margen, o una prueba que suba el archivo de tope por el Ingress. | New |
| R-02 | Minor | aidlc/spaces/default/intents/261002-veridicus-mvp/construction/session-lifecycle/infrastructure-design/cicd-pipeline.md > §2 puerta «Rendimiento»; monitoring-design.md > §3 SLI/SLO | Los SLO se declaran medidos «en la máquina de desarrollo con `values-cpu.yaml`», pero la puerta que los hace cumplir (`pytest -m perf`, p95 de NFR3.1–NFR3.5 y NFR3.9) es bloqueante en `session-api.yml`, es decir, corre en un runner de GitHub. Los umbrales de latencia (≤ 200 ms, ≤ 0,5 s) con hardware distinto producen falsos fallos o falsa confianza. | Aclarar dónde corre cada medición: en el runner, con umbrales propios y justificados, o en la máquina de desarrollo, adjuntando el resultado al PR. Registrar la decisión para que no se relaje un umbral para que pase la puerta. | New |
| R-03 | Minor | aidlc/spaces/default/intents/261002-veridicus-mvp/construction/session-lifecycle/infrastructure-design/infrastructure-specification.md > §2 fila `veridicus-pg` y §1 «Hilos del trabajador» | (a) El hilo `SuspensionSweeper` usa el pool de 3 conexiones `veridicus_app` del trabajador, que ya comparten ingesta y plazos de U4 (el indexador usa `veridicus_indexer`). Ahora hay tres hilos sobre 3 conexiones, con transacciones `FOR UPDATE SKIP LOCKED`, y U7 y U8 sumarán más. No hay análisis de agotamiento del pool ni del presupuesto de conexiones (U4: «22 de las 50»). (b) `idle_in_transaction_session_timeout` 5 s se presenta como configuración de U6, pero no dice dónde se aplica (rol, `Cluster` de U2 o sesión) ni si afecta las transacciones de U3 y U4. No figura en §6. | Indicar el tamaño de pool que resulta para el trabajador y el total de conexiones, o confirmar que 3 basta con el uso en ráfagas. Precisar el alcance del `idle_in_transaction_session_timeout` y añadirlo a la tabla de precisiones si toca un artefacto de U2. | New |
| R-04 | Minor | aidlc/spaces/default/intents/261002-veridicus-mvp/construction/session-lifecycle/infrastructure-design/monitoring-design.md > §1 fila `veridicus_sessions{status}` y §2 | La métrica `open` > 50 se lista con umbral como supuesto de capacidad (NFR8.6, NFR8.7), pero §2 no define ninguna regla `PrometheusRule` para ella. El supuesto del latido y de la revisión se puede romper sin que ninguna alerta lo muestre. | Añadir la alerta informativa (P3) o indicar que el umbral solo se mira en el panel. | New |

### Validation Tool Results

| Tool | Result | Interpretation |
|---|---|---|
| `traceability.json` (script Python) | JSON válido; 53 filas, todas `OK`; `upstream_ids` y `coverage` coinciden. Los IDs `NFR10.17-19`, `NFR4.2` y `NFR5.1` que aparecen en `nfr-requirements/` son citas de U4 o filas N/A, no requisitos de U6 | Cobertura de NFR completa |
| Redis `noeviction` | `maxmemory 384mb`, `noeviction` y AOF `everysec`; marca con `EX 86400` en el mismo `MULTI`/`EXEC` que el `XADD` | Coherente con NFR10.11 |
| Migraciones (AUTONOMIA-01) | Migración aditiva en PR propio, aplicada por el `migrations-job`; orden U5 → U6 coincide con `bolt-plan.md` (B5 antes de B7). `veridicus_now()` con hora inyectada solo en el *fixture* de CI | Cumple; el índice con `CREATE INDEX CONCURRENTLY` va fuera de transacción |
| Recursos y cuarto hilo (U4) | Límites 0,5/384 MiB–2/768 MiB y 0,5/512 MiB–1,5/960 MiB coinciden con U4 §1.1; el cuarto hilo y el `/readyz` están en la tabla de precisiones | Coherente. El +50 MiB de la API es estimación, con corrección por PR si la medición lo supera |
| Puertas con comando y umbral (AUTONOMIA-02) | Cada puerta de `cicd-pipeline.md` §2 tiene comando exacto y umbral | Cumple (ver R-02 sobre dónde corre `perf`) |
| Frontera por componente (AUTONOMIA-04) | `infrastructure-specification.md` §3 declara dentro/fuera y datos para cada componente; sin destino externo; la red reutiliza las políticas de U2 | Cumple |
| Precisiones sin editar originales | §6 registra 4 precisiones y no edita artefactos aprobados | Cumple |
| Fragmentos de código ≤ 15 líneas | Sin bloques de código en los tres artefactos | Cumple |

### Summary

El diseño es coherente con U2, U3 y U4: no añade procesos ni reglas de red, respeta `noeviction`, AUTONOMIA-01/02/04 y la cobertura de NFR. El único punto que el humano debería sopesar antes de aprobar es el límite de cuerpo del `Ingress` frente al *multipart* de la versión de escenario (R-01); el resto son aclaraciones menores.
