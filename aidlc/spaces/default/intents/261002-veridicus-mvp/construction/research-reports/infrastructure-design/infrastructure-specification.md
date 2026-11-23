# Especificación de infraestructura — U12 research-reports

**Revisión 1 (2026-11-23): primera pasada.** Todo es nuevo.
- **Qué despliega U12.** Nada propio. Su código corre en la API de `session-api` (`Deployment`
  `veridicus-session-api`, forma de U3) y su pantalla M8 en la imagen `frontend` (base de U4). Este documento
  fija lo que U12 necesita de ese proceso y de la plataforma, y lo que pide a U2 y a U3.
- **Supuesto de máquina.** Una sola máquina de 64 GB, solo CPU y sin máquina GPU; Minikube con 50 GiB y
  16 CPU, decidido por U2 (IDS-U2-01). Hoy el trabajo corre en un contenedor sobre WSL2.
- **Preguntas.** Ninguna (`infrastructure-design-questions.md`, sección del 2026-11-23).
- **Precisiones y peticiones.** IDS-U12-01 a IDS-U12-10, en §7.

**Insumos.**
- De `nfr-design/` de esta unidad (revisión 1): performance-design §1, §2, §4, §5 y §8; security-design §1–§3,
  §6–§8, §10, §13 y la tabla NFRD-U12-01 a NFRD-U12-07; scalability-design §1–§6; reliability-design §1, §2,
  §6–§8; observability-design §1–§5; logical-components §1, §3–§5.
- `functional-design/functional-spec.md` (functional-spec: F1, F5, §9 y la pregunta abierta 4 de §11).
- ResearchReports, ConsoleApi y la tabla de frontera del clúster de `inception/domain-design/components.md`
  (components).
- C1 (`/research-reports*`), C16, C19 y C25 de `inception/contract-design/contract-summary.md`
  (contract-summary).
- `nfr-requirements/` de esta unidad: NFR3.8, NFR3.11, NFR-U12-06 y `tech-stack-decisions.md` (D1, D2, D5,
  §2 y §5).
- Peticiones de NFR Design dirigidas a U12: el lector compartido de U6 (NFRD-U6-10) y la nota de U7 sobre
  el plazo de inactividad (NFRD-U7-02).
- Infrastructure Design de esta etapa: U2 revisión 2 (§1, §2.1, §2.4, §4, §7 e IDS-U2-01 a IDS-U2-15), U3
  revisión 2 (§1, §1.1, §2 e IDS-U3-xx) y U4 revisión 2 (IDS-U4-03, IDS-U4-09, IDS-U4-12).
- `## Deployment` y `## Testing Posture` de `team.md`, y las reglas de `project.md`.

## 1. Despliegue

| Facet | Choice | Rationale |
|---|---|---|
| Modelo de cómputo | Sin proceso propio. Las rutas, el caso de uso, la validación y el repositorio corren en el contenedor `session-api` del `Deployment` `veridicus-session-api` (namespace `veridicus`, 1 proceso Uvicorn); M8 es parte de los archivos estáticos de `veridicus-frontend` | scalability-design §1; logical-components §1 y §2 (`hosts: [session-api-api]`); forma del despliegue de U3 |
| Réplicas | 1 de la API, sin HPA ni KEDA; los 2 huecos de subida son locales al proceso y la unicidad de `source_sha256` vive en la base, así que una réplica más no rompe nada (cambiarlo es un PR) | scalability-design §1 |
| Puertos y rutas | `http` 8080 de U3; `/api/v1/research-reports` entra por el `Ingress` `veridicus-research-reports` y las lecturas (`GET /research-reports`, `/{id}`, `/compare`) por `/api/` de `veridicus-web`. Sin puerto ni métrica propios | C1; U2 §2.4; observability-design §4 |
| Estrategia de actualización | La de la API: `RollingUpdate`, `maxSurge: 1`, `maxUnavailable: 0`. Una subida en curso en el pod viejo termina dentro de su `terminationGracePeriodSeconds`; si se corta, no deja filas (T3 es atómica) y el investigador reintenta (`201` o `409`) | reliability-design §2 y §5 |
| Arranque | El catálogo de referencia y las cifras de U12 en C25 se validan **antes** de abrir el puerto; con un archivo ausente o inválido el pod nunca pasa a listo, la prueba de humo falla y se revierte | reliability-design §6; C16 |
| Sondas | Las de U3, sin comprobaciones nuevas en `/readyz` | observability-design §5 |
| Imagen | La de `session-api` (U3), por digest. U12 añade `python-multipart` fijado en `uv.lock` (ya lo trae FastAPI) y copia las dos listas de etiquetas a `/opt/veridicus/catalog/labels/` (IDS-U12-03, IDS-U12-05). Sin imagen nueva | security-design §10; tech-stack D2 |
| Almacenamiento | Ninguno propio: el cuerpo se lee en memoria con el lector compartido de U6 (IDS-U12-02), nada toca el disco (`readOnlyRootFilesystem: true`, `/tmp` en memoria de 16 MiB de U3 que U12 no usa); las filas viven en `veridicus-pg` | security-design §3 («sin disco»); NFR10.4 |
| Configuración montada | `profiles.yaml` y `prices.yaml` del `ConfigMap` `veridicus-profiles` de U2 en `/etc/veridicus/profiles/` (solo lectura, ya montado en la API por IDS-U4-09); listas `tipo-hecho.v1.yaml` y `perfil-persona.v1.yaml` dentro de la imagen; C25 dentro de la imagen (`VERIDICUS_LIMITS_PATH`) | NFR-U12-06; security-design §6; IDS-U12-03 |
| Red | Sin reglas nuevas: entrada por `ingress-nginx` a 8080 (ya existe) y salida solo a `veridicus-pg`, que la API ya tiene | security-design §2; §3 |
| Entornos | Una sola máquina de 64 GB, solo CPU, con el mismo digest que publica la CI. Sin *staging* ni producción | Supuesto del brief; IDS-U2-01 |
| IaC | Ninguna plantilla propia: el subchart `session-api` y la plantilla de `frontend` del chart paraguas de U2 con `values-cpu.yaml`; la migración de las cuatro tablas entra por el `Job` de migraciones de U2 en su propio PR | AUTONOMIA-01; `project.md` (migraciones en un `Job`) |
| Recursos | **Petición a U2:** `limits.memory` de la API de 1,125 GiB a **1,75 GiB**; `requests` y CPU sin cambios (§1.1, IDS-U12-01) | NFR3.8; performance-design §5; logical-components §5 |
| Clasificación | `veridicus.io/data-class: sensitive` en `session-api` (la de U2, por las demás unidades); U12 no maneja testimonio | security-design §1 |

### 1.1 Memoria de la API frente a dos subidas (NFR3.8)

La API de `session-api` tiene hoy 0,5 / 512 MiB → 2 / 1,125 GiB (1 152 MiB), calculado por U2 como
1,2 × (768 MiB de U7 + 160 MiB de Argon2id + 16 MiB de `/tmp`) = 1,2 × 944 MiB. Esa cifra **no incluye** las
subidas de U12.

| Cálculo | Memoria | Frente a 1 152 MiB |
|---|---|---|
| Base de U2 sin margen | 944 MiB | — |
| Base + dos subidas estimadas (2 × 230 MiB), sin margen | 1 404 MiB | **No cabe** (+252 MiB) |
| Base + tope medible de NFR3.8 (512 MiB), sin margen | 1 456 MiB | No cabe |
| 1,2 × (944 + 512) MiB, regla de U2 §4 | 1 747 MiB | — |
| **Límite pedido**, redondeado a 64 MiB | **1 792 MiB (1,75 GiB)** | +640 MiB |

- **Por qué se suman.** El *bulkhead* acota U12 a dos subidas, pero no impide que coincidan con una
  consolidación o una exportación de U7 ni con dos inicios de sesión: el proceso es compartido
  (logical-components §4) y NFR3.8 pide sumar la cifra con el margen de U4.
- **`requests` sin cambios** (0,5 CPU y 512 MiB): el pico de U12 es transitorio y raro (un investigador,
  decenas de reportes). La CPU límite de 2 alcanza: la validación corre en un solo hilo bajo el GIL.
- **Presupuesto de Minikube.** Los `requests` siguen en ≈ 41 GiB y ≈ 14,5 CPU, con el mismo margen. La suma
  de `limits` sube de ≈ 51,8 GiB a ≈ 52,4 GiB, 2,4 GiB por encima de los 50 GiB. Se apoya en lo que U2 ya
  aceptó (juez y verificador nunca generan a la vez y sus pesos son memoria recuperable) y los recortes no
  cambian: primero el monitoreo y después el juez de `todo-local`.
- **Durante un despliegue de la API** conviven dos pods: +512 MiB de `requests` transitorios, ya dentro del
  margen de 9 GiB de U2.
- **Si la medición de B12 sube el pico** por encima de 512 MiB con dos subidas, es un hallazgo que se
  corrige en el código (filas por lotes o plan B de proceso aparte, performance-design §2) y se vuelve a
  medir; el límite no se sube en silencio (scalability-design §7).

### 1.2 Tiempos de la subida frente al `Ingress`

| Tramo | Tope | De dónde |
|---|---|---|
| Lectura del cuerpo | 30 s en total (`research_report_read_timeout_s`); 8 MiB exigen ≥ 280 KiB/s, holgado con el `port-forward` local | reliability-design §1 |
| Validación tras la lectura | ≈ 7 s con el *fixture* máximo (codificación, JSON, esquema, contraste y filas) | performance-design §1 |
| T3 | ≤ 15 s (`research_report_write_timeout_s`) | reliability-design §1 |
| Respuesta tras el último byte | ≤ 22 s en el peor caso, por debajo del `proxy-read-timeout 30s` de U2 | IDS-U12-07 |

Con `proxy-request-buffering: "off"`, ingress-nginx pasa los trozos según llegan: el plazo de lectura lo
cuenta `session-api`, no el `Ingress`.

## 2. Servicios de infraestructura

| Service | Role | Configuration | Notes |
|---|---|---|---|
| `veridicus-pg` (U2) | database | Rol `veridicus_app` por el *pool* de la API de U3 (5 + 5, `pool_timeout` 2 s, `statement_timeout` 2 s por conexión). T1 y T2 por milisegundos; T3 con `SET LOCAL statement_timeout` = 15 s e `idle_in_transaction_session_timeout` = 5 s (IDS-U12-06) | U12 no abre conexiones nuevas: como mucho 2 a la vez, solo en T3 (scalability-design §6). No cambia el `connectionLimit` que fijen U2 y U4 |
| Esquema de U12 | database | `research_report` y sus hijas `research_report_model_call`, `research_report_metric` y `research_report_bias_count`, con `CHECK` por columna, índice único `source_sha256` e índice `uploaded_at DESC`; marca `veridicus-audit` (`history`, `purgeable: false`); `veridicus_apply_audit_grants()` deja a `veridicus_app` solo `SELECT` e `INSERT` y a `veridicus_retention` nada | security-design §7 y §8; entra con el `Job` de migraciones y `veridicus_owner` |
| Volumen de PostgreSQL | database | PVC de 10 GiB de U2, **sin cambio**. U12 ocupa ≤ 1,5 × `source_bytes` por reporte: ≤ 1,5 GiB con 1 000 reportes típicos (el techo de NFR3.9); con el volumen esperado del TG, de decenas a pocos cientos, ≤ 0,5 GiB | NFR3.11; scalability-design §5; IDS-U12-08 |
| Respaldo | database | `scripts/backup-db.sh` de U2 vuelca toda la base, también las cuatro tablas; RPO el último volcado manual, RTO una restauración manual; un reporte perdido se vuelve a subir (`201`) | reliability-design §7 |
| `ingress-nginx` (U2) | load-balancer | `veridicus-research-reports`: `^/api/v1/research-reports$` → `veridicus-session-api:8080`, `proxy-body-size` 8 454 144 (`research_report_max_bytes` + 64 KiB), `proxy-request-buffering: "off"`, `proxy-buffering: "off"`, `proxy-max-temp-file-size: "0"`, `proxy-read-timeout 30s`. Las lecturas, por `veridicus-web` (tope 2 113 536) | **Sin cambios** (IDS-U12-07). El `413` por `Content-Length` lo da `session-api` antes de leer; el tope del `Ingress` es la segunda barrera |
| `ConfigMap` `veridicus-profiles` (U2) | other (configuración) | `profiles.yaml` y `prices.yaml`, copias con el mismo SHA-256 que `config/` (`check-config-copy.sh`) | El mismo catálogo que usan `semantic-agent` y el proxy: el contraste de BR3 compara contra lo que de verdad corre |
| `veridicus-redis`, servidores de modelos, `anonymizer-proxy` | — | U12 no los usa | security-design §2 (`research-reports-no-egress`) |
| `cdn`, `search`, caché | — | No aplica | Filas inmutables y volumen bajo (performance-design, introducción) |

### 2.1 Ajustes del contenedor `session-api` que usa U12

| Variable | Valor en `values-cpu.yaml` | Origen |
|---|---|---|
| `VERIDICUS_PROFILES_PATH` | `/etc/veridicus/profiles/profiles.yaml` (montado) | IDS-U4-09; tech-stack §2 |
| `VERIDICUS_PRICES_PATH` | `/etc/veridicus/profiles/prices.yaml` (montado) | tech-stack §2; IDS-U12-03 |
| `VERIDICUS_LABELS_DIR` | `/opt/veridicus/catalog/labels` (dentro de la imagen) | tech-stack §2; IDS-U12-03 |
| `VERIDICUS_LIMITS_PATH` | Catálogo C25 empaquetado en la imagen | D20 de U4 |
| `VERIDICUS_LIMIT_RESEARCH_REPORT_*` | Sin definir: rigen `research_report_max_bytes`, `_max_json_depth`, `_write_timeout_s` y `_read_timeout_s` de C25 (solo se pueden bajar) | `check-limits-env.sh` de U2; scalability-design §2 |

Las tres rutas se declaran explícitas aunque coincidan con un valor por defecto: así un archivo que falte
impide arrancar y el log nombra la variable (reliability-design §6). `UPLOAD_SLOTS` (2) y
`UPLOAD_SLOT_WAIT_S` (5) son constantes del código, no variables: cambiarlas exige volver a medir NFR3.8 en
el mismo PR (scalability-design §2).

## 3. Red de U12 (NFR1.1, NFR1.2, AUTONOMIA-04)

| Proceso | Entrada | Salida |
|---|---|---|
| API de `session-api` (rutas de U12) | `ingress-nginx` → 8080 (regla de U3) | `veridicus-pg` 5432 (regla de U3). Nada más |
| M8 en el navegador | — | `https://veridicus.local:8443` por el `port-forward` del Ingress (IDS-U2-04) |

U12 no suma filas a `deploy/network-deps.yaml`. El contrato `research-reports-no-egress` de import-linter
impide en el código cualquier cliente HTTP, `socket`, `libs.model_gateway` o `libs.anonymizer`
(security-design §2), y la `NetworkPolicy` de U2 lo impide en el clúster.

### 3.1 Frontera por componente (AUTONOMIA-04)

| Componente | Dentro o fuera del clúster | Datos que cruzan su frontera |
|---|---|---|
| M8 (pantalla de la consola) | Navegador del investigador, en Windows | **Entra** al clúster el archivo C19 (solo metadatos y cifras, sin texto libre); sale hacia el navegador solo lo que guarda la base |
| Rutas `/research-reports*`, caso de uso, validación, contraste, repositorio | Dentro, en la API de `session-api` | Ninguno sale del clúster; solo filas tipadas hacia `veridicus-pg` |
| `ReferenceCatalog` | Dentro, en memoria de la API | Ninguno: lee archivos de solo lectura |
| Reporte de la CLI antes de subirlo | **Fuera**: WSL2 del humano o ZINE, copiado por el humano | Ninguno con testimonio: C19 no tiene campos de texto libre (contract-summary) |

## 4. Catálogo de referencia (NFR-U12-06, NFR10.9, NFR10.15)

| Archivo | Dónde vive en el clúster | Cómo cambia |
|---|---|---|
| `config/profiles.yaml` | `ConfigMap` `veridicus-profiles` → `/etc/veridicus/profiles/profiles.yaml` | PR que cambia `config/` y su copia en `deploy/veridicus/files/`; llega con el siguiente despliegue |
| `config/prices.yaml` | Igual → `/etc/veridicus/profiles/prices.yaml` | Igual |
| `evaluation/labels/tipo-hecho.v1.yaml` | Imagen de `session-api` → `/opt/veridicus/catalog/labels/` | PR que cambia la lista; la imagen nueva llega con su PR de despliegue |
| `evaluation/labels/perfil-persona.v1.yaml` | Igual | Igual |

- **Por qué perfiles y precios van en el `ConfigMap`.** Son los mismos archivos que leen `semantic-agent` y
  el proxy: el contraste de BR3 rechaza lo que no coincide con los perfiles que de verdad corren.
- **Por qué las etiquetas van en la imagen.** Cambian con el conjunto sintético, como C25, y no hace falta
  ampliar la lista de claves permitidas de `check-no-data.sh` ni una copia más en `check-config-copy.sh`.
- **Recarga.** El catálogo se carga una vez al arrancar. Un cambio del `ConfigMap` no reinicia el pod por sí
  solo: U12 pide a U2 la anotación de suma de comprobación en la plantilla del pod (IDS-U12-04), para que
  el `catalog_sha256` del log de arranque siempre corresponda a lo desplegado.

## 5. Consola (M8 en `frontend`)

| Aspecto | Diseño |
|---|---|
| Contenido | `frontend/src/features/research-reports/` dentro de la imagen `veridicus-frontend` de U4; sin recursos ni cabeceras nuevas (la CSP de U4 ya cubre `fetch` a `'self'`) |
| Subida | `fetch` con `AbortController` y `multipart/form-data` al mismo origen; `retry: false` en la mutación (reliability-design §4) |
| Recursos | Sin cambio en `frontend` (0,05 / 32 MiB → 0,2 / 64 MiB de U2): son archivos estáticos |
| Acceso | `https://veridicus.local:8443`, solo con rol `investigador` (T1 de `GuardedRoute`) |

## 6. Infraestructura compartida

| Shared Resource | Owner Unit | Consumer Units | Access Boundary |
|---|---|---|---|
| Proceso, `Deployment` y `Service` `veridicus-session-api` | U3 (forma), U2 (recursos) | U12 entre U4–U9 y U13 | U12 suma su parte de memoria por petición a U2 (IDS-U12-01); *bulkhead* de 2 y limitador propio para no agotar el proceso común |
| Lector `multipart` en memoria (`session_api/shared/multipart_memory.py`) | U6 (lo entrega B7) | U6, U9, U12 | Cada unidad pasa su tope y su plazo; ninguna lo copia (IDS-U12-02) |
| `veridicus-pg`, `Ingress`, `ConfigMap` `veridicus-profiles`, `Job` de migraciones | U2 | U12 entre otras | Tablas de infraestructura compartida de U2 §7 |
| Cuatro tablas de reportes | U12 (esquema por migración de `session-api`) | Solo ConsoleApi | `veridicus_app` con `SELECT` e `INSERT`; `veridicus_retention` sin permisos |
| `frontend` | U4 | U12 (M8) | Una sola imagen; textos solo del catálogo de mensajes |
| C1, C19, C25 | U1 (C19 por U11) | U12 | Cambian por PR de U1 |

## 7. Precisiones y peticiones (IDS-U12-xx)

No edité ningún artefacto aprobado ni de otra unidad. En la aprobación decides cuáles se llevan al
original, cada una en su propio commit. Las peticiones no se dan por aplicadas. Todas salen de las fuentes
aprobadas o de un hecho técnico, y ninguna deja salir del clúster algo que hoy no sale.

| ID | Artefacto que precisa | Precisión | Origen |
|---|---|---|---|
| IDS-U12-01 | Infrastructure Design de U2 §4 (API de `session-api`: 2 / 1,125 GiB) | **Petición a U2:** `limits.memory` de la API a **1 792 MiB (1,75 GiB)** = 1,2 × (944 + 512) MiB redondeado; `requests` y CPU sin cambios. Los `limits` de Minikube pasan de ≈ 51,8 a ≈ 52,4 GiB (2,4 GiB sobre los 50 GiB); los `requests` siguen en ≈ 41 GiB. Control: una prueba de `deploy/tests/level0` falla si el render baja de 1 792 MiB | NFR3.8; performance-design §5; logical-components §5; §1.1 |
| IDS-U12-02 | `nfr-design/logical-components.md` §1 (lector en `research_reports/api/multipart_reader.py`) | El lector es el compartido de U6, `session_api/shared/multipart_memory.py`; U12 solo le pasa su tope (`research_report_max_bytes` + 64 KiB), su plazo (30 s) y el *callback* que descarta el `filename` y alimenta el SHA-256. La prueba de NFR10.4 sin disco se repite con ese lector. B12 depende de que B7 lo haya entregado | NFRD-U6-10; tech-stack D2 |
| IDS-U12-03 | `nfr-requirements/security-requirements.md` NFR-U12-06 («desde la imagen o un `ConfigMap`») | Perfiles y precios desde `veridicus-profiles` en `/etc/veridicus/profiles/`; las dos listas de etiquetas dentro de la imagen en `/opt/veridicus/catalog/labels/`; `VERIDICUS_PRICES_PATH` y `VERIDICUS_LABELS_DIR` declaradas explícitas | §4; tech-stack §2 |
| IDS-U12-04 | Infrastructure Design de U2 §2.1 (`veridicus-profiles`) | **Petición a U2:** la plantilla del pod de `veridicus-session-api` lleva la anotación `checksum/veridicus-profiles` con el SHA-256 del `ConfigMap`, para que un cambio de perfiles o precios reinicie la API y el catálogo cargado coincida con lo desplegado. Sirve igual al trabajador y a `semantic-agent` | reliability-design §6; observability-design §2 (`catalog_sha256`) |
| IDS-U12-05 | Infrastructure Design de U3 (`cicd-pipeline.md`, filtro de rutas de `session-api.yml`) | **Petición a U3:** el *job* `changes` de `session-api.yml` suma `evaluation/labels/**`, porque las listas viajan en la imagen; el `Dockerfile` de `session-api` las copia desde la raíz del monorepo | IDS-U12-03 |
| IDS-U12-06 | `nfr-design/reliability-design.md` §1 («5 s o 15 s, según U6 o U7») | T3 fija sus dos plazos con `SET LOCAL`: `statement_timeout` = `research_report_write_timeout_s` (15 s) e `idle_in_transaction_session_timeout` = 5 s. T3 no tiene huecos sin sentencias (las filas ya están armadas), así que 5 s nunca corta una escritura legítima y una conexión colgada no retiene la fila del usuario | NFRD-U7-02; regla de `project.md` (plazo por transacción con `SET LOCAL`) |
| IDS-U12-07 | — | El `Ingress` `veridicus-research-reports` de U2 basta sin cambios: tope 8 454 144, sin disco, y `proxy-read-timeout 30s` frente a ≤ 22 s de respuesta tras el último byte. Si alguna vez corta a los 30 s con T3 ya confirmada, el navegador ve `504` y la nueva subida da `409`; nunca quedan dos filas | §1.2; reliability-design §2 |
| IDS-U12-08 | Infrastructure Design de U2 §2.1 (PVC de 10 GiB) | **Petición a U2 (informativa, sin cambio de tamaño):** su tabla de volúmenes registra que U12 ocupa ≤ 1,5 GiB con 1 000 reportes. Si la consulta de conteo de la revisión de B12 se acerca a 1 000, se revisa el PVC junto con la paginación | NFR3.11; scalability-design §4 y §5 |
| IDS-U12-09 | — | Regla `VeridicusSessionApiNearMemoryLimit` (memoria del contenedor `session-api` / su límite > 0,9 durante 5 min) en `charts/monitoring-rules/` de U2, con su `promtool test`; solo se renderiza con `monitoring.enabled: true`. U3 lista la señal sin regla y U4 cubre solo el trabajador y `semantic-agent` | scalability-design §7; `monitoring-design.md` §2 |
| IDS-U12-10 | `team.md` (`## Deployment`, dos máquinas y etapa GPU) | Con el supuesto del brief, U12 no tiene valores por máquina ni petición de `nvidia.com/gpu`; sus pruebas de niveles 0 y 1 corren en CPU (NFR2.1) | IDS-U2-01; IDS-U2-02 |
