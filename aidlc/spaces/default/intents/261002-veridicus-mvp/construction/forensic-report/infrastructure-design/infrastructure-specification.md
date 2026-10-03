# Especificación de infraestructura — U7 forensic-report

**Insumos.** Presupuestos de tiempo y de memoria de `nfr-design/performance-design.md`
(performance-design); frontera, montajes, permisos del volumen y cabeceras de descarga de
`nfr-design/security-design.md` (security-design); modelo de capacidad, réplica única y señales para
escalar de `nfr-design/scalability-design.md` (scalability-design); archivo antes que fila, plazos,
cancelación cooperativa, barrido, `/readyz` y `verify_store` de `nfr-design/reliability-design.md`
(reliability-design); logs, métricas y regla del volumen de `nfr-design/observability-design.md`
(observability-design); inventario, dominios de falla y entrega a Infrastructure Design de
`nfr-design/logical-components.md` (logical-components); flujos F1–F7 de
`functional-design/functional-spec.md` (functional-spec); módulo ForensicReport y fachada ConsoleApi de
`inception/domain-design/components.md` (components); C1, C8, C11, C15 y C16 de
`inception/contract-design/contract-summary.md` (contract-summary); requisitos de `nfr-requirements/`;
respuestas **P1 = A** (`Recreate` solo en la API, 30 s de gracia y política Kyverno de NFR8.6),
**P2 = A** (respaldo conjunto a pedido en `scripts/backup-db.sh` y restauración manual que termina con
`verify_store`) y **P3 = A** (cuota propia con dos *gauges* y `/readyz` con el menor entre cuota libre y
disco libre) de `infrastructure-design-questions.md`; infraestructura común de U2
(`platform/infrastructure-design/`), despliegue de `session-api` de U3 (`identity-access/`), procesos de
U4 (`text-flow/`) y lo que añadieron U5 (`human-review/`) y U6 (`session-lifecycle/`).

U7 no tiene proceso propio: es el módulo `forensic_report` de la API de `session-api` y su único estado
fuera de PostgreSQL es el PVC `veridicus-reports`. Este documento fija qué cambia U7 en el despliegue de
la API (estrategia, montaje, configuración, memoria), el volumen, su respaldo y el `Job` de verificación.

## 1. Despliegue

| Faceta | Elección | Razón |
|---|---|---|
| Modelo de cómputo | Módulo dentro del `Deployment` `session-api` (API) de U3, namespace `veridicus`; sin `Deployment`, `CronJob` ni hilo de servicio propio. Solo el `Job` revisable `veridicus-verify-store` (§2.3) | logical-components §1 y §4 |
| Réplicas | **1** (de U3), ahora también requisito de U7 mientras el PVC sea `ReadWriteOnce` | scalability-design §4 (NFR8.6) |
| Estrategia de la API (P1 = A) | **`Recreate`** en el `Deployment` de la API, con `terminationGracePeriodSeconds: 30` y apagado ordenado de Uvicorn de 25 s (`--timeout-graceful-shutdown 25`), que deja terminar una consolidación en curso (≤ 10 s) antes de soltar el volumen. El trabajador `session-api-worker` y los demás procesos siguen con `RollingUpdate` | NFR8.6, NFR10.16: el barrido de un pod nuevo nunca convive con una consolidación del viejo |
| Costo de `Recreate` | Cada despliegue de la API deja la consola sin servicio ≈ 20–40 s (gracia ≤ 30 s, arranque, barrido ≤ 5 s con 1 000 archivos y `/readyz`). El sondeo de la consola reintenta solo sus lecturas; las escrituras no se reintentan (NFR10.18). El humo posterior al despliegue confirma la vuelta | P1 = A; `## Deployment` de team.md (humo tras cada despliegue) |
| Imagen | La de `session-api` (U3) por digest; U7 no añade paquetes de sistema. El respaldo usa un comando Python propio (`export_store`, §2.4), así que la imagen no necesita `tar` | security-design §1 |
| Puertos | Sin puertos nuevos: rutas de U7 en `http` 8080 bajo `/api/`; métricas en `metrics` 8081 | observability-design §2 |
| Red | Sin reglas nuevas para la API: U7 solo usa `veridicus-pg:5432` y el volumen local (NFR1.1). Una `NetworkPolicy` nueva para el `Job` de verificación (§3) | NFR1.1; AUTONOMIA-04 |
| Almacenamiento | PVC `veridicus-reports` (§2.2) montado en el contenedor `api` en `/var/lib/veridicus/reports-volume`; `VERIDICUS_REPORTS_DIR` es su subdirectorio `reports/`, que el proceso crea con `0700` si no existe | NFR10.6; el aprovisionador hostPath crea la raíz del volumen como `root` `0777` e ignora `fsGroup`, así que el proceso sin root no podría dejarla en `0700` (§6) |
| Sistema de archivos | `readOnlyRootFilesystem: true`, `emptyDir` en memoria para `/tmp` (U3); el volumen de reportes es el único montaje escribible persistente; `umask 077` al arrancar | NFR10.6; Pod Security `restricted` de U2 |
| Configuración | Siete claves de U7 en el `ConfigMap` `session-api-config` (§1.2), validadas al arrancar; sin Secrets nuevos para la API | NFR10.17, NFR10.19 |
| Sondas | Forma de U3 sin cambios: `/readyz?probe=kubernetes` suma los chequeos de U7 (configuración, directorio con `0700`, espacio libre según P3 = A, barrido terminado). El barrido corre antes de que `/readyz` responda `200` y cabe en la `startupProbe` de 60 s de U3 | reliability-design §4 (NFR10.19, C16) |
| Recursos | Se mantienen 0,5 / 384 MiB – 2 / 768 MiB de la API (§1.1) | performance-design (NFR8.1) |
| Máquinas | Mismo chart y mismos valores de U7 en la máquina de desarrollo (Minikube 20 GiB, 10 CPU) y en la de demostración (28 GiB); U7 no cambia con `values-gpu.yaml` ni con `values-extras.yaml` | NFR2.1: U7 no usa modelos ni GPU |
| IaC | Subchart `session-api` de `deploy/veridicus` (estrategia, montaje, claves, PVC), dos políticas en `deploy/policies/`, regla y prueba en `deploy/prometheus/`, manifiesto del `Job` en `deploy/jobs/` (fuera de la `Application` de Argo CD), revisión de Alembic en `db/migrations/` y `scripts/backup-db.sh` ampliado. Los escribe Code Generation y entran por PR | AUTONOMIA-01; `## Deployment` de team.md |
| Frontera (AUTONOMIA-04) | Todo dentro del clúster, salvo el respaldo en la anfitriona y el arnés de MTTV; ver §4 | security-design §1 |

### 1.1 Memoria de la API con U7 (NFR8.1)

| Parte | Pico | Origen |
|---|---|---|
| Pico previo de la API (base + Argon2id + U4 + U5 + U6) | ≈ 410 MiB | `session-lifecycle/infrastructure-design/infrastructure-specification.md` §1.1 |
| 3 consolidaciones simultáneas del caso de 100 turnos | ≤ 96 MiB | performance-design; NFR8.1, NFR8.2 |
| Descarga de un archivo de 2 MiB en paralelo | ≤ 16 MiB | NFR8.1 |
| Medición de la cuota (recorrido de ≤ 1 000 entradas cada 60 s, P3 = A) | < 1 MiB | Solo `os.scandir` y sumas |
| **Suma de picos** | **≈ 523 MiB** | — |
| `limits.memory` | 768 MiB → margen ≈ 47 % (≥ 20 %); la suma sigue por debajo del tope de 640 MiB (768 / 1,2) que fijó U5 | Regla de ≥ 20 % de esta etapa |
| `requests.memory` | 384 MiB, sin cambio: U7 no añade uso en reposo apreciable | U3 |

Si la medición de NFR8.1 supera los 96 MiB, `limits.memory` sube por PR con la medición; el presupuesto de
Minikube de U2 y U4 no cambia.

### 1.2 Configuración de U7 (prefijo `VERIDICUS_`)

| Ajuste | Valor en los *values* | Regla validada al arrancar |
|---|---|---|
| `VERIDICUS_REPORTS_DIR` | `/var/lib/veridicus/reports-volume/reports` | Absoluta, bajo el montaje; si no existe se crea con `0700`; si existe debe ser directorio del UID del proceso, escribible y `0700` |
| `VERIDICUS_REPORT_STORAGE_TIMEOUT_SECONDS` | `"5"` | 1–30 |
| `VERIDICUS_REPORT_CONSOLIDATION_TIMEOUT_SECONDS` | `"10"` | > almacén + 2 y < 15 (`idle_in_transaction_session_timeout`) |
| `VERIDICUS_REPORT_ORPHAN_MIN_AGE_SECONDS` | `"300"` | > consolidación + 60 |
| `VERIDICUS_REPORT_MIN_FREE_BYTES` | `"52428800"` | ≥ 2 × 2 MiB |
| `VERIDICUS_REPORT_VOLUME_QUOTA_BYTES` (P3 = A) | Derivado de `reports.size` (`2Gi` → `"2147483648"`) por el chart | ≥ 64 MiB y ≥ 10 × `MIN_FREE_BYTES` |
| `VERIDICUS_REPORT_VOLUME_SCAN_INTERVAL_SECONDS` (P3 = A) | `"60"` | 10–600 |

El chart toma la cuota y el `resources.requests.storage` del PVC del mismo valor `reports.size`; una
comprobación de `deploy-level0.yml` falla si difieren en algún render (`cicd-pipeline.md` §2).

## 2. Servicios de infraestructura

| Servicio | Rol | Configuración | Notas |
|---|---|---|---|
| `veridicus-pg` | database | Pool de la API de U3 con `veridicus_app`; `statement_timeout` 2 s (U3), `lock_timeout` 2 s (U5), `idle_in_transaction_session_timeout` 15 s en las conexiones de la API | Cada consolidación usa una conexión ≤ 2 s; U7 no abre conexiones nuevas (scalability-design §2) |
| Esquema de U7 | database | Revisión de Alembic de U7 aplicada por `migrations-job` con `veridicus_owner` (§2.1) | Nunca al arrancar el pod (prohibición de `project.md`) |
| PVC `veridicus-reports` | object-store (volumen) | `ReadWriteOnce`, **2 GiB**, `StorageClass` `standard` (hostPath de Minikube, dentro del nodo), sin *prune* en Argo CD (§2.2) | Reservado por U2; la cuota de la aplicación hace cumplir el tamaño (P3 = A) |
| `veridicus-verify-store` | other (`Job` revisable) | Imagen de `session-api`; `python -m session_api.forensic_report.verify_store`; volumen en `readOnly: true`; rol `veridicus_report_ro` (§2.3) | Lo crea el humano a pedido; nunca lo aplica la CI ni Argo CD (AUTONOMIA-01) |
| Respaldo conjunto | other (*script* de la anfitriona) | `scripts/backup-db.sh`: `pg_dump` y luego `export_store` (§2.4) | P2 = A |
| `ingress-nginx` | load-balancer | Ruta `/api/` de U2/U4; la descarga ≤ 2 MiB y el cuerpo `{expected_cursor}` caben en `proxy-body-size` ≥ 1 MiB (la descarga es respuesta, no cuerpo); la consolidación ≤ 10,5 s cabe en `proxy-read-timeout` 30 s | Cabeceras de descarga de NFR10.4 las pone la API; el `Ingress` no añade caché |
| Prometheus y Grafana (SHOULD) | other (observabilidad) | `ServiceMonitor` de `session-api` de U3 (puerto 8081), reglas y fila de panel de `monitoring-design.md` | Sin Alertmanager (U2) |

### 2.1 Esquema y permisos (revisión de Alembic de U7)

| Objeto | Diseño | Requisito |
|---|---|---|
| `report_version` | Tabla de solo inserción con `report_version_id` (PK), `session_id`, `round_id`, `version_number`, `sha256`, `byte_size`, `storage_path`, `format_version`, `consolidated_by`, `consolidated_at`; únicos `(session_id, version_number)`, `(round_id)` y `(storage_path)` | NFR8.4, NFR11.1 |
| Permisos de `veridicus_app` | `INSERT, SELECT` en `report_version`; sin `UPDATE`, `DELETE` ni `TRUNCATE`; tabla registrada en `AuditConvention` de U3 | NFR11.1, NFR11.4 |
| Rol `veridicus_report_ro` | Rol gestionado de CloudNativePG (en el `Cluster` de U2, por PR) con contraseña en el Secret `veridicus-db-report-ro`; la migración le da solo `SELECT` en `report_version` | Mínimo privilegio para `verify_store` (T10) |
| Antes de aplicar | El humano ejecuta `scripts/backup-db.sh` (U2 §6, «antes de un cambio de esquema») | AUTONOMIA-01 |

### 2.2 Volumen de reportes

| Aspecto | Diseño | Requisito |
|---|---|---|
| Tamaño | 2 GiB (reserva de U2): peor caso de diseño 600 MiB, uso esperado ≈ 18 MB; el aprovisionador hostPath no lo hace cumplir, lo hace la cuota de P3 = A | NFR8.5 (§6) |
| Montajes | Solo el contenedor `api` del `Deployment` `session-api` (lectura y escritura) y el `Job` `veridicus-verify-store` (`readOnly: true`). Política Kyverno `veridicus-reports-mounts`: cualquier otro *workload* que lo monte, o el `Job` sin `readOnly`, falla | NFR1.2, NFR10.6 |
| Escritor único | Política Kyverno `veridicus-reports-single-writer`: el `Deployment` que monta `veridicus-reports` en escritura debe tener `replicas: 1` y `strategy.type: Recreate` mientras el PVC sea `ReadWriteOnce` | NFR8.6 (P1 = A) |
| Permisos | Raíz del montaje `root` `0777` (aprovisionador); `reports/` `0700` del UID 10001; archivos finales `0400`; temporales `0600` | NFR10.6, NFR11.4 |
| Ciclo de vida | Anotación de Argo CD `Prune=false` y `helm.sh/resource-policy: keep` en el PVC: ni una sincronización ni un `helm uninstall` lo borran. Sin purga en el MVP (evidencia de auditoría) | NFR8.5; `## Deployment` de team.md |
| Escalado | Ampliar `reports.size` por PR cuando la alerta del 80 % se sostiene (monitoring-design §2); más réplicas exigen antes un volumen `ReadWriteMany` o un almacén de objetos (scalability-design §5) | NFR8.6 |

### 2.3 `Job` de verificación

| Aspecto | Diseño |
|---|---|
| Manifiesto | `deploy/jobs/verify-store.yaml` con `generateName: veridicus-verify-store-`, fuera de la ruta que sincroniza Argo CD; entra por PR y lo crea el humano con `kubectl create -f` cuando lo necesita (tras una restauración, antes de la sustentación) |
| Contexto | UID 10001 y `fsGroup` como la API, `readOnlyRootFilesystem`, sin token de cuenta de servicio, `backoffLimit: 0`, `activeDeadlineSeconds: 300`, `ttlSecondsAfterFinished: 3600`; 0,1 / 128 MiB – 0,5 / 256 MiB |
| Salida | Solo identificadores y conteos por la salida estándar; código 0 solo con 0 versiones sin archivo, 0 SHA-256 distintos y 0 huérfanos de más de 300 s (NFR10.20, NFR8.8) |
| Coexistencia | En un solo nodo, `ReadWriteOnce` permite montarlo a la vez que la API; el `Job` no escribe, así que no compite con el barrido |

### 2.4 Respaldo y restauración (P2 = A)

| Paso | Qué se hace | Por qué |
|---|---|---|
| 1. Base | `scripts/backup-db.sh` hace el `pg_dump -Fc` de U2 hacia `backups/veridicus-<fecha>.dump` | Sin cambio respecto de U2 |
| 2. Archivos | Después, `kubectl exec deploy/session-api -c api -- python -m session_api.forensic_report.export_store` escribe por la salida estándar un `tar` de solo lectura de `reports/` con un `SHA256SUMS` interno, hacia `backups/veridicus-reports-<fecha>.tar`; el *script* añade `veridicus-reports-<fecha>.tar.sha256` | Base antes que volumen: toda fila del volcado tiene su archivo en el `tar`; un archivo más nuevo que el volcado queda sin fila y el barrido lo borra tras restaurar |
| 3. Comprobación | El *script* recalcula el `SHA256SUMS` del `tar` en la anfitriona y sale con código distinto de 0 si no coincide | Respaldo verificado en el momento |
| Cuándo | Los momentos de U2: antes de la sustentación y antes de un cambio de esquema (incluida la migración de U7) | RPO = último respaldo manual |
| Restauración | Paso manual del humano en `docs/operacion/instalacion.md`: `pg_restore` (U2) → `kubectl exec -i … python -m session_api.forensic_report.import_store < tar` (verifica `SHA256SUMS`, crea solo archivos que no existen con `O_EXCL` y los deja `0400`) → reinicio de la API (barrido) → `Job` `veridicus-verify-store` con código 0 | RTO objetivo ≤ 30 min con el respaldo a mano; ningún *script* restaura solo (AUTONOMIA-01) |
| Almacenamiento | `backups/` en la anfitriona, ya en `.gitignore`; solo datos sintéticos | Prohibiciones de `project.md` |

`export_store` e `import_store` son comandos del módulo, no rutas HTTP: no amplían la superficie de la API.

## 3. Red

| Política | Origen → destino | Puerto | Requisito |
|---|---|---|---|
| Sin cambio | API de `session-api` → `veridicus-pg` | 5432 | NFR1.1 |
| `veridicus-verify-store` (nueva) | Pods `app.kubernetes.io/name: veridicus-verify-store` → `veridicus-pg`, más `allow-dns` | 5432, 53 | El `Job` solo habla con la base |
| Entrada de `veridicus-pg` (U2) | Se suma el selector del `Job` a la lista de clientes de 5432 | 5432 | Mínimo acceso |
| Salida a internet | Denegada para la API y el `Job` (política por defecto de U2) | — | AUTONOMIA-04 |

## 4. Frontera del clúster por componente (AUTONOMIA-04)

| Componente | Dentro / fuera | Datos que cruzan su frontera | Control |
|---|---|---|---|
| Módulo `forensic_report` en la API | Dentro, `veridicus` | Entra: peticiones del navegador por `ingress-nginx`. Sale: `ReportVersion` y el Markdown al navegador del analista | `authorize` de U3, cabeceras de NFR10.4, `NetworkPolicy` de U2 |
| PVC `veridicus-reports` | Dentro (hostPath del nodo) | Ninguno fuera del nodo | Políticas de montaje; permisos `0700`/`0400` |
| `Job` `veridicus-verify-store` | Dentro | Identificadores y conteos por `kubectl logs` | Volumen en solo lectura; rol de solo `SELECT` |
| Respaldo en `backups/` | **Fuera del clúster**, en la anfitriona de la misma máquina | Volcado de la base y `tar` de reportes (datos sintéticos) | Lo ejecuta el humano; nunca sale de la máquina ni entra al repositorio |
| Arnés de MTTV | Fuera, en la máquina de desarrollo | Solo marcas de tiempo e identificadores por la API | Nunca descarga reportes |
| Consola en el navegador | Fuera (puesto del analista), solo por ConsoleApi | Vista del reporte como texto y descarga | `react/no-danger`, `Cache-Control: no-store` |

## 5. Infraestructura compartida

| Recurso compartido | Unidad dueña | Unidades que lo usan | Frontera de acceso |
|---|---|---|---|
| `Deployment` `session-api` (API) | U3 (forma), U7 (estrategia `Recreate`) | U3–U8 | Capas e import-linter; un cambio de estrategia pasa por la política `veridicus-reports-single-writer` |
| PVC `veridicus-reports` | U7 (dimensiona), U2 (lo declara en el chart) | Solo la API y el `Job` de verificación | Políticas `veridicus-reports-mounts` y `veridicus-reports-single-writer` |
| `veridicus-pg` y sus roles | U2 | U3–U7; U7 con `veridicus_app` y `veridicus_report_ro` | Rol por proceso; `NetworkPolicy` de entrada a 5432 |
| Fila de la sesión (`change_seq`) | U5 | U4, U6, U7 | Orden único sesión → ronda (reliability-design §1) |
| `scripts/backup-db.sh` | U2 | U5, U6, U7 (paso de archivos) | Solo lectura sobre el clúster; lo ejecuta el humano |
| Prometheus y Grafana (SHOULD) | U2 | U3–U7 | Solo el puerto 8081 |

## 6. Precisiones a artefactos ya aprobados

No edité ningún artefacto aprobado ni de otras unidades; decides en la aprobación si se actualizan.

| Artefacto | Qué precisa | Origen |
|---|---|---|
| `platform/infrastructure-design/infrastructure-specification.md` §5 (U2), `identity-access/…` §1 (U3), `human-review/…` §1 (U5) y `session-lifecycle/…` §1 y `cicd-pipeline.md` §3 (U6) | El `Deployment` de la API de `session-api` pasa de `RollingUpdate` (`maxSurge: 1`, `maxUnavailable: 0`) a `Recreate` con `terminationGracePeriodSeconds: 30`; el trabajador sigue con `RollingUpdate`. Cada despliegue de la API corta la consola ≈ 20–40 s; ya no conviven dos API (la duplicación de la serie AIR que U5 absorbía deja de ocurrir) | P1 = A; NFR8.6 |
| `forensic-report/nfr-requirements/scalability-requirements.md` (NFR8.5) y `security-requirements.md` §6 | El PVC es de **2 GiB** (reserva de U2), no de 1 GiB; el peor caso de 600 MiB sigue cubierto | Reserva de U2 |
| `forensic-report/nfr-requirements/observability-requirements.md` (NFR15.3) y `nfr-design/observability-design.md` §3 | La regla del volumen usa `veridicus_report_volume_used_bytes / veridicus_report_volume_quota_bytes`, no `kubelet_volume_stats_*`, que el aprovisionador hostPath no publica | P3 = A |
| `forensic-report/nfr-requirements/reliability-requirements.md` (NFR10.19) y `tech-stack-decisions.md` §2 | Los 50 MiB libres se miden como el menor entre «cuota − usado» y el espacio libre real del disco; dos ajustes nuevos (`VOLUME_QUOTA_BYTES`, `VOLUME_SCAN_INTERVAL_SECONDS`); `VERIDICUS_REPORTS_DIR` es el subdirectorio `reports/` del montaje y el proceso lo crea con `0700` si no existe | P3 = A; hostPath ignora `fsGroup` |
| `forensic-report/nfr-requirements/security-requirements.md` (NFR10.6) | El `fsGroup` no se aplica a un volumen hostPath; el aislamiento lo dan el subdirectorio `0700` del UID 10001, los archivos `0400` y las políticas de montaje | Aprovisionador de Minikube de U2 |
| `inception/contract-design/contract-summary.md` (C15) | Dos *gauges* nuevos `veridicus_report_volume_used_bytes` y `veridicus_report_volume_quota_bytes`, sin etiquetas, en el mismo PR de U1 que las métricas de NFR15.1 | P3 = A |
| `platform/infrastructure-design/monitoring-design.md` (U2) | La regla «Uso del PVC de la base» usa `kubelet_volume_stats_*`, que tampoco existe con hostPath; queda para que U2 la revise (por ejemplo, con `cnpg_pg_database_size_bytes`). No la cambia U7 | Hallazgo de P3 |
| `platform/infrastructure-design/infrastructure-specification.md` §6 (U2) | `scripts/backup-db.sh` añade el paso de archivos de reportes después del `pg_dump`, con `SHA256SUMS`; la restauración termina con el `Job` `veridicus-verify-store` | P2 = A |
| `platform/…` §7 (U2) | Rol gestionado `veridicus_report_ro` y Secret `veridicus-db-report-ro`; la entrada de `veridicus-pg` admite al `Job` de verificación | §2.1, §3 |
| `forensic-report/nfr-requirements/tech-stack-decisions.md` §5 | La ruta del chart es `deploy/veridicus` (la de U2), no `deploy/charts/veridicus` | Estructura de U2 |
