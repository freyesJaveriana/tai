# Componentes lógicos — U4 text-flow

**Revisión 2 (2026-11-22): segunda pasada por el cambio 01 (DT27), la adenda 02 y el NFR Requirements
revisión 2.** Sustituye a la revisión 1 del 2026-10-03.
- **Qué cambia.** Salen el evaluador semántico, el indexador de escenarios, el cliente de *embeddings* y el
  servidor del juez. Entran `AnalysisWorker` sobre C17, la ruta mínima del incidente, el hilo de liberación
  y la renovación del reclamo. Se añade el inventario en YAML.

**Insumos.** `nfr-requirements/tech-stack-decisions.md` (tech-stack-decisions: D9–D20, NFR2, NFR13,
NFR14), `security-requirements.md` (security-requirements), `reliability-requirements.md`
(reliability-requirements), `performance-requirements.md` (performance-requirements),
`scalability-requirements.md` (scalability-requirements), `observability-requirements.md`
(observability-requirements), `functional-design/functional-spec.md` (functional-spec),
`contract-summary.md` (contract-summary); los cinco documentos de diseño de esta revisión.

## 1. Inventario

| Componente | Proceso | Responsabilidad | Diseño |
|---|---|---|---|
| `TurnRoutes`, `SessionRoutes`, `ProfileRoutes` | API de `session-api` | C1 de U4: crear sesión, turnos, reintento, sondeo, perfiles, aviso | `security-design.md` §7; `performance-design.md` §3, §9 |
| `RunEnqueuer` | API de `session-api` | Plazo, filas, `XADD` de C2 tras `COMMIT`, publicación fallida | `reliability-design.md` §4, §10 |
| `ResultIngestor` | Trabajador de `session-api`, hilo 1 | C3: incidente, vigencia, segunda línea, `propose`, ruta mínima | `security-design.md` §2; `reliability-design.md` §9, §12 |
| `RunSupervisor` | Trabajador de `session-api`, hilo 2 | Plazos, turnos de voz, esperas, profundidad de cola | `reliability-design.md` §4 |
| `HoldReleaser` | Trabajador de `session-api`, hilo 3 | Liberar esperas en ≤ 1 s | `performance-design.md` §8 |
| `CancellationKeys` | API y trabajador de `session-api` | Escribir y reescribir las claves | `reliability-design.md` §11 |
| `AnalysisWorker` | `semantic-agent`, bucle | C2 → `analyze` (C17) → C3, tope de entregas, huella | `reliability-design.md` §3; `security-design.md` §12 |
| `ClaimRenewer` | `semantic-agent`, hilo | `XCLAIM … JUSTID` cada 15 s | `reliability-design.md` §3 |
| `HealthServer` | `semantic-agent`, hilo | `/healthz`, `/readyz`, `/metrics` | `reliability-design.md` §6 |
| `CompositionRoot` | `semantic-agent` y `session-api` | Límites, perfiles, piso de 270 s, `check_ready()`, `gateway.build` | `security-design.md` §8, §10, §11 |
| `ConsoleRunView` (M3, M4) | Navegador | Sondeo, *upsert*, reintentos | `reliability-design.md` §7; `performance-design.md` §6 |

## 2. Dominios de falla y radio de impacto

| Falla | Qué deja de funcionar | Qué sigue | Recuperación |
|---|---|---|---|
| `semantic-agent` caído | Corridas nuevas | Consola, turnos, revisión; la cola acumula | Reclamo a los 60 s; plazo |
| Trabajador de `session-api` caído | Ingesta, supervisor, liberación | API y envío de turnos | Mensajes pendientes; reclamo |
| Redis caído | Cola, cancelación; consola fuera de servicio (`/readyz` de U3) | Datos en PostgreSQL | Reescritura de claves; plazo |
| PostgreSQL caído | Todo `session-api` | `semantic-agent` termina su corrida y publica | La ingesta no consume hasta que vuelve |
| `anonymizer-proxy` caído | Corridas con perfil comercial | Perfiles locales | `analysis.anonymizer_unavailable`; reintento del analista |

## 3. Recursos compartidos

- **PostgreSQL** (U2, CloudNativePG): esquema de `session-api`; usuarios `veridicus_app` y
  `veridicus_retention`.
- **Redis** (U2): `veridicus:runs`, `veridicus:results`, sus `:failed` y `veridicus:run-cancelled:*`.
- **Catálogos de U1**: `contracts/limits.v1.yaml`, esquemas de C2, C3 y C6, `contracts/metrics/text-flow.v1.yaml`.
- **Biblioteca de U11** en proceso dentro de `semantic-agent`; escáner de U11 en `session-api`.

## 4. Entrega a Infrastructure Design

- Dos *Deployments* de `session-api` de la misma imagen (API y trabajador) y uno de `semantic-agent`, una
  réplica cada uno; `requests` y `limits` según `performance-design.md` §7.
- `semantic-agent` sin Secret de PostgreSQL ni claves de proveedor; con Secret de Redis y
  `VERIDICUS_ANONYMIZER_PROXY_URL` interna.
- La `NetworkPolicy` de U2 permite a `semantic-agent` solo Redis, los servidores locales y el proxy.
- Ajustes nuevos `VERIDICUS_RELEASE_POLL_MS` y `VERIDICUS_PUBLISH_RETRIES` (NFRD-U4-14).

## 5. Calidad, pruebas y textos (NFR2.1, NFR2.2, NFR13.1, NFR13.2, NFR14.1)

- **NFR2.1, NFR2.2.** Niveles 0 y 1 en CPU con *fakes* de C17 y del `ModelGateway`, PostgreSQL y Redis
  reales; ninguna prueba descarga modelos ni llama a proveedores. NFR3.10 y NFR8.5 con `comercial-piloto`.
- **NFR13.1.** ≥ 80 % de líneas en `services/session-api`, `services/semantic-agent` y `frontend`.
- **NFR13.2.** 100 % de ramas en `domain/output_check.py`, `domain/incident.py`, `domain/run_currency.py` y
  `domain/deadline.py` (`.coveragerc-guards`).
- **NFR14.1 y NFR10.5.** Textos de M3, M4 y el aviso solo desde el catálogo de U1; una prueba de nivel 0
  falla ante un literal visible; el escáner de U11 corre sobre catálogo y plantillas en nivel 0 y sobre el
  texto renderizado en nivel 3, con un control negativo por término.
- `NFR14.2`: Retirado (pasa a U11).

## Componentes en YAML

```yaml
components:
  - name: TurnRoutes
    path: services/session-api/session_api/interview/api/
    hosts: session-api-api
    boundary: inside
    data_out: none
    guard: false
  - name: RunEnqueuer
    path: services/session-api/session_api/interview/application/enqueue.py
    hosts: session-api-api
    boundary: inside
    data_out: none
    guard: false
  - name: ResultIngestor
    path: services/session-api/session_api/interview/application/ingest.py
    hosts: session-api-worker
    boundary: inside
    data_out: none
    guard: true
  - name: RunSupervisor
    path: services/session-api/session_api/interview/worker/supervisor.py
    hosts: session-api-worker
    boundary: inside
    data_out: none
    guard: true
  - name: HoldReleaser
    path: services/session-api/session_api/interview/worker/release.py
    hosts: session-api-worker
    boundary: inside
    data_out: none
    guard: false
  - name: AnalysisWorker
    path: services/semantic-agent/semantic_agent/worker/
    hosts: semantic-agent
    boundary: inside
    data_out: via-anonymizer-proxy
    guard: true
  - name: ClaimRenewer
    path: services/semantic-agent/semantic_agent/worker/claim.py
    hosts: semantic-agent
    boundary: inside
    data_out: none
    guard: false
  - name: CompositionRoot
    path: services/semantic-agent/semantic_agent/main.py
    hosts: semantic-agent
    boundary: inside
    data_out: none
    guard: true
  - name: ConsoleRunView
    path: frontend/src/features/session/
    hosts: browser
    boundary: browser
    data_out: none
    guard: false
```
