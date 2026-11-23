# Especificación de infraestructura — U7 forensic-report (módulo ReviewReport)

**Revisión 2 (2026-11-23): segunda pasada por el cambio 01 (DT27), la adenda 02 y el NFR Design revisión 2.**
Sustituye a la revisión 1 del 2026-10-03, que queda en el historial de Git.
- **Qué cambia.**
  - El paquete pasa a `review_report` y los comandos a `session_api.review_report.*` (NFR-U7-08).
  - Salen el `Job` `veridicus-verify-store`, el rol `veridicus_report_ro`, su Secret y su `NetworkPolicy`:
    `verify_store` corre por `kubectl exec` (NFR-U7-05).
  - Entran la exportación sin copias en disco, la tabla `report_export`, la purga del `Job` de retención de
    U13 y la función de bloqueo que este necesita.
  - El plazo de inactividad pasa a `SET LOCAL` por transacción (NFRD-U7-01).
  - `export_store` pasa de `backup-db.sh` al runbook.
  - Los nombres siguen a U2 y U3: `Deployment` `veridicus-session-api`, contenedor `session-api` y `ConfigMap`
    `veridicus-session-api-config`.
- **Se mantiene** P1 = A (`Recreate` y una réplica), como petición a U2 porque su revisión 2 la dejó en
  `RollingUpdate` (IDS-U7-03).
- **Numeración.** §1–§5 conservan su tema. §2.3 queda «Retirado». La tabla de precisiones de la revisión 1
  (§6) se retira entera (IDS-U7-01) y la sustituye IDS-U7-01 a IDS-U7-17. La nueva §7 cierra los hallazgos de
  `reviews/review-01.md`.
- **Supuesto de máquina.** Un solo equipo de 64 GB, solo CPU, sin GPU, con Minikube de 50 GiB y 16 CPU
  (IDS-U2-01). Hoy el trabajo corre en un contenedor sobre WSL2.
- **Preguntas.** Ninguna en esta pasada (`infrastructure-design-questions.md`, sección del 2026-11-23).

**Insumos.**
- De `nfr-design/` de esta unidad (revisión 2):
  - `performance-design.md` (performance-design): presupuestos de tiempo y de memoria, §1–§7;
  - `security-design.md` (security-design): frontera, volumen, exportación, retención y la tabla NFRD-U7-01 a
    NFRD-U7-13;
  - `scalability-design.md` (scalability-design): una réplica, cuota y señales;
  - `reliability-design.md` (reliability-design): plazos, cancelación, barrido, `/readyz`, `verify_store`,
    exportación y purga;
  - `observability-design.md` (observability-design): logs, métricas y reglas;
  - `logical-components.md` (logical-components): inventario, dominios de falla y entrega a esta etapa.
- `functional-design/functional-spec.md` (functional-spec, revisión 2): F1–F10.
- ReviewReport y ConsoleApi de `inception/domain-design/components.md` (components).
- C1, C8, C11, C12, C16, C23, C24 y C25 de `inception/contract-design/contract-summary.md`
  (contract-summary).
- `nfr-requirements/` de esta unidad (revisión 2), con la tabla NFR-U7-01 a NFR-U7-13.
- Peticiones de NFR Design de otras unidades dirigidas a U7: NFRD-U13-07 (función de bloqueo de la purga) y
  NFRD-U13-08 (`count_session`, solo código).
- Infrastructure Design revisión 2 de U2 (§1, §2, §4–§7 e IDS-U2-01 a IDS-U2-15), U3 (IDS-U3-01, -03, -06,
  -10), U4 (IDS-U4-02, -03, -07), U5 (IDS-U5-01, -02, -05, -07) y U6 (§1, §2 e IDS-U6-02).
- `## Deployment` y `## Testing Posture` de `team.md`, y las reglas de `project.md`.

U7 **no añade procesos, imágenes, servicios, Secrets ni reglas de red**. Lo propio de U7 es:
- la estrategia de la API (petición IDS-U7-03);
- el montaje y la cuota del PVC;
- siete ajustes del `ConfigMap`;
- una migración;
- sus reglas y su panel;
- los comandos que el humano ejecuta por `kubectl exec` o desde el runbook.

## 1. Despliegue

| Facet | Choice | Rationale |
|---|---|---|
| Modelo de cómputo | Módulo dentro del `Deployment` `veridicus-session-api` (API, U3), contenedor `session-api`, namespace `veridicus`. Sin `Deployment`, `CronJob` ni hilo de servicio propio. La purga corre dentro del `Job` de retención de U13 (`deploy/jobs/`), que llama a `purge_session` | logical-components §1 y §4 |
| Réplicas | **1**. Es requisito de U7 mientras el PVC sea `ReadWriteOnce` (NFR8.6) | scalability-design §4 |
| Estrategia de la API · se mantiene (P1 = A) | **`Recreate`**, con `terminationGracePeriodSeconds: 30` y Uvicorn con `--timeout-graceful-shutdown 25`. Una consolidación en curso (≤ 10 s) termina antes de soltar el volumen. El trabajador sigue con `Recreate` (IDS-U4-02). **Petición a U2** (IDS-U7-03), porque su §5 dejó la API en `RollingUpdate` | NFR8.6, NFR10.16: el barrido de un pod nuevo nunca convive con una consolidación del viejo |
| Costo de `Recreate` | Cada despliegue de la API deja la consola sin servicio durante la gracia, la descarga de las capas nuevas, el arranque, el barrido (≤ 5 s con 1 000 archivos) y la primera respuesta `200` de `/readyz`. Umbral: ≤ 90 s, medido con `scripts/measure-cutover.sh` (IDS-U7-11). Una configuración inválida deja la consola caída hasta el `git revert` (riesgo ya aceptado en P1 = A) | Cierra R-03 y R-04 |
| Imagen | La de `session-api` por digest. U7 no añade paquetes de sistema: `export_store`, `import_store` y `verify_store` son comandos Python del módulo, así que la imagen no necesita `tar` | security-design §1 |
| Puertos | Sin puertos nuevos: las rutas de U7 van en `http` 8080 bajo `/api/` y las métricas en `metrics` 8081 | observability-design §2 |
| Red | Sin reglas nuevas: la API solo usa `veridicus-pg:5432` y el volumen local. Sale la `NetworkPolicy` del `Job` de verificación (IDS-U7-02) | NFR1.1; AUTONOMIA-04 |
| Almacenamiento | PVC `veridicus-reports` (§2.2), montado en el contenedor `session-api` en `/var/lib/veridicus/reports-volume` y en el `Job` de retención con la misma ruta. `VERIDICUS_REPORTS_DIR` es su subdirectorio `reports/`, que el proceso crea con `0700` si no existe | NFR10.6; el aprovisionador hostPath ignora `fsGroup` |
| Sistema de archivos | `readOnlyRootFilesystem: true` y `/tmp` en memoria de 16 MiB (U3). El volumen de reportes es el único montaje escribible persistente. `umask 077` al arrancar. Ni la vista previa ni la exportación escriben en `/tmp` | NFR10.6, NFR10.25 |
| Configuración | Siete claves de U7 en `veridicus-session-api-config` (§1.2), validadas al arrancar. `report_max_bytes` se lee de C25, nunca del `ConfigMap`. Sin Secrets nuevos | NFR10.17, NFR10.19 |
| Sondas | Las de U3: `startupProbe` sobre `/healthz` (60 s) y `readinessProbe` sobre el `/readyz` completo (IDS-U3-01). U7 suma a `/readyz` sus chequeos: configuración, directorio con `0700`, espacio libre y cuota, barrido de arranque terminado y volumen no colgado. El barrido corre antes de que `/readyz` responda `200` | reliability-design §4 (NFR10.19, C16) |
| Recursos | Sin cambio en las cifras de U2: 0,5 CPU / 512 MiB de reserva y 2 CPU / 1,125 GiB de límite. La cuenta está en §1.1 | performance-design §6 (NFR8.1) |
| Entornos | Un solo equipo de 64 GB con `values-cpu.yaml` y el mismo digest que publica la CI. U7 no tiene valores por máquina ni pide `nvidia.com/gpu` | IDS-U2-01, IDS-U2-02 (NFR2.1) |
| IaC | El chart paraguas `deploy/veridicus` de U2 lleva la estrategia, el montaje, las claves, el PVC y su cuota. Se suman una política en `deploy/policies/`, una prueba en `deploy/tests/level0/`, la regla y su prueba en el subchart `monitoring-rules`, la migración en `db/migrations/` y `scripts/measure-cutover.sh`. Los escribe Code Generation y entran por PR | AUTONOMIA-01; `## Deployment` de `team.md` |
| Frontera (AUTONOMIA-04) | Todo dentro del clúster, salvo el respaldo en `backups/` de WSL2 y los dos *scripts* de solo HTTP (§4) | security-design §1 |
| Clasificación | `veridicus.io/data-class: sensitive` en la API y en el `Job` de retención (U2): manejan el caso completo | Tabla de clasificación de U2 |

### 1.1 Memoria de la API con U7 (NFR8.1, NFR8.9) · cambia

| Parte | Pico | Origen |
|---|---|---|
| API sin las exportaciones ni el `exec`: base ≈ 220 MiB, Argon2id 160 MiB, `/tmp` 16 MiB, U6 ≤ 100 MiB y 3 consolidaciones del caso máximo de U7 ≤ 192 MiB | ≈ 688 MiB | `session-lifecycle/infrastructure-design/infrastructure-specification.md` §1.1; performance-design §6 |
| Una vista previa o una exportación de 8 MiB en paralelo | ≤ 32 MiB | performance-design §6 |
| Medición del volumen y barrido (≤ 1 000 entradas cada 60 s) | < 1 MiB | Solo `os.scandir`, sumas y una consulta por nombre |
| Proceso de `kubectl exec` (`verify_store` o `export_store`): un segundo intérprete Python en el mismo *cgroup*, que lee un archivo de ≤ 8 MiB a la vez y transmite el `tar` en bloques sin cargarlo entero | ≤ 64 MiB | Cierra R-06 (IDS-U7-09) |
| **Suma de picos** | **≈ 785 MiB** | — |
| 1,2 × suma | ≈ 942 MiB | Regla de U2 (§4) |
| `limits.memory` de U2 | 1 152 MiB (1,125 GiB): **cabe** con ≈ 210 MiB de margen. Sustituye al límite de 768 MiB de NFR-U7-11 y de performance-design §6 (IDS-U7-09) | U2 §4 |
| `requests.memory` | 512 MiB de U2, sin cambio: U7 no añade uso en reposo apreciable | U2 §4 |

U7 **no cambia ninguna cifra de pod** ni suma al presupuesto de U2 (≈ 41 GiB y 14,5 CPU pedidos). Tampoco
choca con la petición de U12 de subir el límite a 1 792 MiB (IDS-U12-01): con ella, el margen crece. Si la
medición de NFR8.1 supera los +192 MiB de las consolidaciones o los +64 MiB del `exec`, el límite sube por PR
con la medición. La prueba de nivel 1 de `export_store` exige que el pico de RSS del proceso no pase de
64 MiB con 1 000 archivos.

### 1.2 Configuración de U7 (prefijo `VERIDICUS_`) · cambia

En el `ConfigMap` `veridicus-session-api-config` (IDS-U5-01). La API y el `Job` de retención leen las mismas
claves, porque `purge_session` usa el mismo almacén (IDS-U7-16).

| Ajuste | Valor en `values-cpu.yaml` | Regla validada al arrancar |
|---|---|---|
| `VERIDICUS_REPORTS_DIR` | `/var/lib/veridicus/reports-volume/reports` | Absoluta y bajo el montaje. Si no existe, se crea con `0700`. Si existe, debe ser un directorio del UID del proceso, escribible y `0700` |
| `VERIDICUS_REPORT_STORAGE_TIMEOUT_SECONDS` | `"5"` | Entre 1 y 30 |
| `VERIDICUS_REPORT_CONSOLIDATION_TIMEOUT_SECONDS` | `"10"` | Mayor que almacén + 2 y menor que 15, el `SET LOCAL idle_in_transaction_session_timeout` de consolidar y exportar (DS3) |
| `VERIDICUS_REPORT_ORPHAN_MIN_AGE_SECONDS` | `"300"` | Mayor que consolidación + 60 |
| `VERIDICUS_REPORT_MIN_FREE_BYTES` | `"52428800"` | ≥ 2 × `report_max_bytes` de C25 (8 MiB): 50 MiB cumple |
| `VERIDICUS_REPORT_VOLUME_QUOTA_BYTES` | Derivado de `reports.size` por el chart (`2Gi` → `"2147483648"`) | ≥ 64 MiB y ≥ 10 × `MIN_FREE_BYTES` |
| `VERIDICUS_REPORT_VOLUME_SCAN_INTERVAL_SECONDS` | `"60"` | Entre 10 y 600; también marca el ritmo del barrido periódico |

- El chart toma la cuota y el `resources.requests.storage` del PVC del mismo valor `reports.size`.
  `deploy/tests/level0/test_review_report_volume.py` falla si difieren en algún render (IDS-U7-04).
- `VERIDICUS_DB_LOCK_TIMEOUT_MS` = 2000 viene de la petición IDS-U5-02 y vale también para el `Job` de
  retención.
- Ningún manifiesto define `VERIDICUS_LIMIT_REPORT_MAX_BYTES`. Si algún día se baja, `check-limits-env.sh` de
  U2 rechaza un valor mayor que el catálogo.

## 2. Servicios de infraestructura

| Service | Role | Configuration | Notes |
|---|---|---|---|
| `veridicus-pg` (U2) | database | La API usa su *pool* de U3 con `veridicus_app`; la purga, la conexión del `Job` con `veridicus_retention`. `statement_timeout` y `lock_timeout` de 2 s por conexión (U3, U5). Consolidar y exportar abren con `SET LOCAL idle_in_transaction_session_timeout = '15s'`, mediante el parámetro `idle_timeout_s` de `session_api/shared/db.py` (aceptado en IDS-U6-02). **Nunca** en el `Cluster`, en el rol ni por conexión | NFRD-U7-01, NFRD-U7-03 (IDS-U7-05). Kyverno `cnpg-cluster-hardening` de U2 rechaza el parámetro en el `Cluster`. Cierra R-02 |
| Conexiones | database | U7 no abre conexiones propias. Con `Recreate` la API usa ≤ 10, sin el segundo pod de una rodadura: el pico de `veridicus_app` baja de 25 a 15 (API 10, trabajador 4, `create-admin` 1) | IDS-U7-03; compatible con la petición IDS-U4-03 |
| Esquema de U7 | database | Migración de U7 (§2.1), aplicada por `migrations-job` con `veridicus_owner` | Nunca al arrancar el pod (`project.md`) |
| PVC `veridicus-reports` | object-store (volumen) | `ReadWriteOnce`, **2 GiB**, `StorageClass` `standard` (hostPath de Minikube, dentro del nodo). `Prune=false` en Argo CD y `helm.sh/resource-policy: keep` (§2.2) | Lo declara U2 (§2.1, §7). La cuota de la aplicación hace cumplir el tamaño (P3 = A) |
| `verify_store` · cambia | other (comando) | `kubectl exec deploy/veridicus-session-api -c session-api -- python -m session_api.review_report.verify_store`, en la lista cerrada `readonly-exec-allowlist.yaml` de U2. Transacción `READ ONLY` y archivos con `O_RDONLY`; solo IDs y conteos por la salida estándar | NFR-U7-05 (NFR10.20). Sustituye a §2.3 de la revisión 1 |
| Respaldo conjunto · cambia | other (runbook) | `scripts/backup-db.sh` de U2 (volcado) y, justo después, `export_store` como paso del runbook (§2.4) | P2 = A; IDS-U7-07 |
| `ingress-nginx` (U2) | load-balancer | `veridicus-web` sin disco en `/api/`: `proxy-request-buffering`, `proxy-buffering` y `proxy-max-temp-file-size` en `off`/`0`. La vista previa y la exportación (≤ 8 MiB + 64 KiB) son respuestas, así que el tope de cuerpo de 2 113 536 no las limita. El único cuerpo de U7, `{expected_cursor}`, cabe de sobra. La consolidación y la exportación (≤ 10,5 s) caben en `proxy-read-timeout 30s` | NFR1.3, NFRD-U7-13 (IDS-U7-17). Las cabeceras de NFR10.4 las pone la API |
| Prometheus y Grafana (SHOULD, módulo 8) | other (observabilidad) | `ServiceMonitor` de `veridicus-session-api` de U3 (puerto 8081); reglas y fila de panel de `monitoring-design.md` en el subchart `monitoring-rules` de U2 | Sin Alertmanager (U2); IDS-U7-13 |
| `cdn`, `search`, caché, `dns`, cola | — | No aplica | U7 no usa Redis ni modelos |

### 2.1 Migración de U7 (B7, un PR propio antes del código) · cambia

| Objeto | Diseño | Requisito |
|---|---|---|
| `report_version` | Tabla de solo inserción: `report_version_id` (PK), `session_id`, `round_id`, `version_number`, `supersedes_version_id`, `sha256`, `byte_size`, `storage_path`, `format_version`, `consolidated_by`, `consolidated_at`. Únicos `(session_id, version_number)`, `(round_id)` y `(storage_path)`. CHECK `(version_number = 1) = (supersedes_version_id IS NULL)`, hex de 64 en `sha256` y `byte_size > 0`. Claves foráneas a sesión, ronda, usuario y versión; sale la del escenario | NFR8.4, NFR11.1, NFR11.5 |
| `report_export` · nuevo | `export_id` (PK), `report_version_id` (índice), `export_sha256` (hex de 64), `exported_by`, `exported_at`, `was_current` | NFR11.7, NFR8.3 |
| Permisos | `veridicus_app`: `INSERT`, `SELECT` en las dos tablas; sin `UPDATE`, `DELETE` ni `TRUNCATE`. `veridicus_retention`: `SELECT`, `DELETE`. Las dos tablas, registradas en `AuditConvention` de U3 con `purgeable: true` | NFR11.1, NFR11.8 |
| `veridicus_purge_lock_report_versions(uuid)` · nuevo | Función `SECURITY DEFINER` de `veridicus_owner` que solo hace `SELECT … FROM report_version WHERE session_id = $1 ORDER BY version_number DESC FOR UPDATE`. `EXECUTE` solo para `veridicus_retention`. PostgreSQL exige `UPDATE` para `FOR UPDATE`, y la retención no lo tiene | NFRD-U13-07 aceptada (IDS-U7-10); NFR10.27 |
| Rol `veridicus_report_ro` | **Retirado** (NFR-U7-05) | — |
| Antes de aplicar | El humano ejecuta `scripts/backup-db.sh` y, si ya hay reportes, el paso `export_store` del runbook (§2.4) | AUTONOMIA-01 |

La migración solo avanza (*expand–contract*) y corre como el `Job` de migraciones de U2: onda −1 con Argo CD o
instalación en dos pasos (IDS-U2-07). Va después de las migraciones de U4 y U5, que crean las tablas a las que
apunta.

### 2.2 Volumen de reportes · cambia

| Aspecto | Diseño | Requisito |
|---|---|---|
| Tamaño | 2 GiB (reserva de U2). Uso esperado ≈ 18 MB; caben 256 reportes del caso máximo. El aprovisionador hostPath no hace cumplir el tamaño: lo hace la cuota (P3 = A) | NFR8.5 |
| Montajes | En escritura: el contenedor `session-api` del `Deployment` `veridicus-session-api` y el `Job` de retención de U13. Kyverno `volume-consumers` de U2 (que generaliza la antigua `veridicus-reports-mounts`) falla ante cualquier otro montaje, incluso de lectura; control negativo: un `CronJob` con `veridicus-reports` | NFR1.2, NFR-U7-06 |
| Escritor único | Kyverno `veridicus-reports-single-writer` (la aporta U7 a `deploy/policies/`, petición IDS-U7-04): un `Deployment` que monta `veridicus-reports` debe tener `replicas: 1` y `strategy.type: Recreate`. Controles negativos: 2 réplicas; `RollingUpdate`. El `Job` de retención queda fuera, porque U13 nunca lanza dos purgas a la vez | NFR8.6 (P1 = A) |
| Identidad | El `Job` de retención usa el mismo `runAsUser` y `runAsGroup` que la API (Kyverno `retention-job-identity` de U2), así que borra sin cambiar permisos | NFR10.6 |
| Permisos | Raíz del montaje `root` `0777` (aprovisionador). `reports/` en `0700` del UID 10001. Archivos finales `0400`, temporales `0600` | NFR10.6, NFR11.4 |
| Ciclo de vida | `Prune=false` (Kyverno `no-prune-on-data` de U2) y `helm.sh/resource-policy: keep`: ni una sincronización ni un `helm uninstall` lo borran. Solo la purga de U13 borra reportes, sesión por sesión | NFR8.5, NFR11.8 |
| Exportaciones | No ocupan volumen: los bytes viven en memoria hasta la respuesta. Tras 100 exportaciones, `veridicus_report_volume_used_bytes` no cambia | NFR8.10, NFR10.25 |
| Escalado | Ampliar `reports.size` por PR (PVC y cuota a la vez) cuando la regla del 80 % se sostiene, o acortar la retención (U13). Más réplicas exigen antes un volumen `ReadWriteMany` o un almacén de objetos | scalability-design §5 |

### 2.3 `Job` de verificación · Retirado

Lo sustituye el comando `verify_store` por `kubectl exec` de §2 (NFR-U7-05). Salen
`deploy/jobs/verify-store.yaml`, el rol `veridicus_report_ro`, el Secret `veridicus-db-report-ro` y la
`NetworkPolicy` `veridicus-verify-store` (IDS-U7-02).

### 2.4 Respaldo y restauración (P2 = A) · cambia

| Paso | Qué se hace | Por qué |
|---|---|---|
| 1. Base | El humano ejecuta `scripts/backup-db.sh` de U2: `pg_dump -Fc` hacia `backups/veridicus-<fecha UTC>.dump`, con poda por `retention_max_days` | Sin cambio respecto de U2 §6 |
| 2. Archivos | Justo después, paso del runbook: `kubectl exec -i deploy/veridicus-session-api -c session-api -- python -m session_api.review_report.export_store > backups/veridicus-reports-<fecha UTC>.tar`. El comando escribe en la salida estándar un `tar` de solo lectura de `reports/` con un `SHA256SUMS` interno | Base antes que volumen: toda fila del volcado tiene su archivo en el `tar`. Un archivo más nuevo que el volcado queda sin fila y el barrido lo borra tras restaurar. El paso no va en el *script*: la lista cerrada de U2 deja `export_store` solo en el runbook (IDS-U7-07) |
| 3. Comprobación | El runbook extrae el `tar` en un directorio temporal `0700` de WSL2, ejecuta `sha256sum -c SHA256SUMS`, borra el directorio y guarda `sha256sum` del `tar` en `veridicus-reports-<fecha UTC>.tar.sha256` | Respaldo verificado en el momento |
| Poda | Petición a U2: la poda de `backup-db.sh` por `retention_max_days` borra también `veridicus-reports-*.tar` y su `.sha256`, porque llevan el caso completo (IDS-U7-08) | Ningún respaldo vive más que el plazo máximo de retención |
| Cuándo | Antes de la sustentación, de un cambio de esquema (incluida la migración de U7) y de recrear el nodo | RPO = último respaldo manual |
| Restauración | Paso manual del runbook: `pg_restore` (U2) → `kubectl exec -i … python -m session_api.review_report.import_store < tar` (verifica `SHA256SUMS`, crea solo archivos que no existen con `O_EXCL` y los deja `0400`) → reinicio de la API, que barre los huérfanos (petición IDS-U5-07 a U2) → `verify_store` con código 0 | RTO ≤ 30 min, medido en el ensayo previo a la sustentación. Ningún *script* restaura (AUTONOMIA-01) |
| Almacenamiento | `backups/` en WSL2, ignorado por git. `backup-db.sh` no arranca si `git check-ignore backups/` falla. Nunca sale de la máquina | Prohibiciones de `project.md` |

`export_store` e `import_store` son comandos del módulo, no rutas HTTP: no amplían la superficie de la API.
`import_store` escribe en el volumen, por eso nunca está en un *script* ni en un plan de tareas.

## 3. Red · cambia

| Política | Origen → destino | Puerto | Requisito |
|---|---|---|---|
| Sin cambio | API de `session-api` → `veridicus-pg` | 5432 | NFR1.1 |
| Sin cambio | `Job` de retención → `veridicus-pg` (y Redis, por U13) | 5432 | Regla de U2 para `retention-job` |
| `veridicus-verify-store` | **Retirado** (IDS-U7-02) | — | NFR-U7-05 |
| Entrada de `veridicus-pg` | Sale el selector del `Job` de verificación | 5432 | Mínimo acceso |
| Salida a internet | Negada para la API y el `Job` de retención (política por defecto de U2) | — | AUTONOMIA-04 |

## 4. Frontera del clúster por componente (AUTONOMIA-04) · cambia

| Componente | Dentro / fuera | Datos que cruzan su frontera | Control |
|---|---|---|---|
| Módulo `review_report` en la API | Dentro, `veridicus` | Entran las peticiones del navegador por `veridicus-web`. Salen `ReportVersion`, la vista previa y la exportación hacia el navegador de un usuario autorizado | `GuardedRoute` de U3, cabeceras de NFR10.4, `NetworkPolicy` de U2 |
| PVC `veridicus-reports` | Dentro (hostPath del nodo) | Ninguno fuera del nodo. Nunca una exportación | `volume-consumers`, `veridicus-reports-single-writer`, `0700`/`0400` |
| `Job` de retención (U13) | Dentro | IDs y SHA-256 en el recibo y en el log | `veridicus_retention`, mismo UID |
| `verify_store` (`kubectl exec`) | Dentro | IDs y conteos por la salida estándar hacia la terminal del humano | Lista cerrada de U2; `READ ONLY` |
| Respaldo en `backups/` | **Fuera del clúster**, en WSL2 de la misma máquina | Volcado de la base y `tar` de reportes | Lo ejecuta el humano; poda por `retention_max_days`; nunca sale de la máquina ni entra al repositorio |
| Arnés de MTTV (`evaluation/mttv/`) | Fuera, en WSL2 | Solo marcas de tiempo, origen e IDs, por `https://veridicus.local:8443` | Nunca pide reportes ni decide |
| `scripts/measure-cutover.sh` | Fuera, en WSL2 | Códigos de estado HTTP y marcas de tiempo | Solo HTTP; no cambia el clúster |
| Consola en el navegador | Fuera del clúster (puesto del analista), solo por ConsoleApi | Vista previa como texto; la exportación queda en el equipo del usuario | `react/no-danger`, `skipHtml`, `Cache-Control: no-store` |

Ningún componente de U7 llama fuera del clúster ni a un modelo, así que ninguno necesita el anonimizador
delante.

## 5. Infraestructura compartida · cambia

| Shared Resource | Owner Unit | Consumer Units | Access Boundary |
|---|---|---|---|
| `Deployment` `veridicus-session-api` (API) | U3 (forma), U2 (manifiesto), U7 (estrategia `Recreate`, petición IDS-U7-03) | U3–U9, U12, U13 | Capas e import-linter; un cambio de estrategia pasa por `veridicus-reports-single-writer` |
| PVC `veridicus-reports` | U7 (dimensiona y define la cuota), U2 (lo declara) | La API y el `Job` de retención de U13 | `volume-consumers`, `veridicus-reports-single-writer`, `retention-job-identity` |
| `veridicus-pg` y sus roles | U2 | U3–U7, U9, U12, U13; U7 con `veridicus_app` y, en la purga, `veridicus_retention` | Rol por proceso; entrada al 5432 solo desde sus clientes |
| Fila de la sesión (`change_cursor`) | U4 | U5, U6, U7, U9, U13 | Orden único sesión → ronda; la exportación no toma la sesión |
| `session_api/shared/db.py` | U3 (U4, U5 y U6 lo amplían) | Todos los procesos de `session-api` | `idle_timeout_s` por transacción (IDS-U6-02) |
| `scripts/backup-db.sh` y runbook | U2 | U5, U6, U7 (paso `export_store`), U13 | Solo lectura; lo ejecuta el humano |
| `readonly-exec-allowlist.yaml` | U2 | U7 (`verify_store`), U13 (consulta) | Lista cerrada; `check-no-cluster-apply.sh` |
| Prometheus, Grafana y `monitoring-rules` | U2 | U3–U7 | Solo el puerto 8081 de la API |

## 6. Precisiones y peticiones (IDS-U7-xx) · nuevo

No edité ningún artefacto aprobado ni de otra unidad. En la aprobación decides cuáles se llevan al original,
cada una en su propio commit. Las peticiones a U2 y a otras unidades no se dan por aplicadas. Todas salen de
las fuentes aprobadas o de un hecho técnico, y ninguna deja salir del clúster algo que hoy no sale.

| ID | Artefacto que precisa | Precisión | Origen |
|---|---|---|---|
| IDS-U7-01 | Revisión 1 de esta etapa, §6 (diez precisiones) | Se retira la tabla entera. `Recreate` sigue como petición (IDS-U7-03). El PVC de 2 GiB, la cuota con `/readyz`, el subdirectorio `0700` y la regla sobre los *gauges* ya están en NFR Requirements y NFR Design revisión 2. Los dos *gauges* no van a C15 (NFR-U7-04). El rol de solo lectura sale (NFR-U7-05). El paso de archivos de `backup-db.sh` pasa a IDS-U7-07. La regla de U2 sobre `kubelet_volume_stats` la resolvió U2 en su revisión 2. La ruta del chart es `deploy/veridicus` | NFR Design revisión 2; NFR-U7-04, -05, -12 |
| IDS-U7-02 | Revisión 1 de esta etapa (los cuatro artefactos) | Se retiran: el `Job` `veridicus-verify-store` con su manifiesto, su rol, su Secret y su `NetworkPolicy`; el paquete y los comandos `forensic_report`; `report.storage_failed`; `veridicus_report_downloads_total`; el `ConfigMap` `session-api-config`; `/readyz?probe=kubernetes`; `deploy/prometheus/` y `deploy/veridicus/dashboards/`; `scripts/check-report-quota.sh` (lo sustituye la prueba de IDS-U7-04); la política `veridicus-reports-mounts`, generalizada por `volume-consumers` de U2; el límite de 768 MiB; los Minikube de 20 y 28 GiB; `values-gpu.yaml`; el SLO de corte medido por `smoke.sh` | NFR-U7-03, -05, -06, -08; IDS-U2-01, -02; IDS-U3-01, -10; IDS-U5-01 |
| IDS-U7-03 | Infrastructure Design de U2 §5 (`session-api` con `RollingUpdate`); de U3 §1, de U5 §1 e IDS-U5-05, y de U6 §1 («API: `RollingUpdate`» y «el `RollingUpdate` conserva el anterior») | **Petición a U2:** el `Deployment` `veridicus-session-api` con `replicas: 1`, `strategy.type: Recreate`, `terminationGracePeriodSeconds: 30` y Uvicorn con `--timeout-graceful-shutdown 25`. Consecuencias para otras unidades: ya no conviven dos API, así que la ventana de IDS-U5-05 desaparece y el pico de conexiones de la API baja de 20 a 10. Una configuración inválida ya no deja el pod anterior: la consola queda caída hasta el `git revert` (riesgo aceptado en P1 = A) | NFR8.6; scalability-design §4; P1 = A de la revisión 1 |
| IDS-U7-04 | Infrastructure Design de U2 (`deploy/policies/`, suite de `deploy-level0.yml`) | **Petición a U2:** U7 aporta la política `veridicus-reports-single-writer` con sus dos controles negativos y `deploy/tests/level0/test_review_report_volume.py`. La prueba comprueba la cuota igual al PVC, el montaje en `/var/lib/veridicus/reports-volume` y que el contenedor de la línea de `verify_store` existe en el render. No cambia el *workflow* de U2 | NFR8.6, NFR15.3; cierra la parte de nivel 0 de R-01 |
| IDS-U7-05 | Revisión 1 de esta etapa, §2 (fila `veridicus-pg`: «15 s en las conexiones de la API») | El plazo de inactividad es `SET LOCAL` de 15 s en consolidar y exportar, con el parámetro `idle_timeout_s` de `db.py` que U6 aceptó. Nunca en el `Cluster`, en el rol ni por conexión. Prueba de nivel 1: un almacén de 4,5 s con la configuración real de conexión de la API da `201` | NFRD-U7-01, NFRD-U7-03; IDS-U6-02; cierra R-02 |
| IDS-U7-06 | `nfr-design/security-design.md` §1, `logical-components.md` §1 y `reliability-design.md` §6 de U7, y NFR Design de U2 §7.3 («contenedor `api`») | El contenedor es `session-api` y el `Deployment` `veridicus-session-api` (IDS-U2-14, IDS-U3-03). La línea de la lista cerrada es `kubectl exec deploy/veridicus-session-api -c session-api -- python -m session_api.review_report.verify_store` | IDS-U2-14; cierra R-01 |
| IDS-U7-07 | Revisión 1 de esta etapa §2.4 (P2 = A, `export_store` dentro de `backup-db.sh`) y `reliability-design.md` §6 | `export_store` es un paso del runbook justo después de `backup-db.sh`, no una línea del *script*: la lista cerrada de U2 solo admite `pg_dump`, la consulta de U13 y `verify_store`. Se conservan el orden base → volumen, el `SHA256SUMS` y la comprobación en el momento | NFR Design de U2 §9; P2 = A |
| IDS-U7-08 | NFR Design de U2 §12 (poda de «todo volcado de `backups/`») | **Petición a U2:** la poda por `retention_max_days` cubre también `veridicus-reports-*.tar` y `.tar.sha256`, con un caso de 91 días en la prueba `backup_prune` | VE-12; NFR11.8 |
| IDS-U7-09 | NFR-U7-11 y `performance-design.md` §6 (límite de 768 MiB y tope de 640 MiB) | La cuenta se hace contra el límite de 1 152 MiB de U2: ≈ 785 MiB de pico con U6 y el proceso de `kubectl exec`, por 1,2 ≈ 942 MiB. U7 no pide cambio | U2 §4; cierra R-06 |
| IDS-U7-10 | `nfr-design/security-design.md` §11 y §4 de U7 | Se acepta NFRD-U13-07: la migración de U7 crea `veridicus_purge_lock_report_versions(uuid)`, `SECURITY DEFINER`, con `EXECUTE` solo para `veridicus_retention`, y concede `DELETE` en `report_version` y `report_export` solo a `veridicus_retention` | NFRD-U13-07; NFR11.8 |
| IDS-U7-11 | Revisión 1 de esta etapa (§1 «Costo de `Recreate`»; SLO de corte ≤ 60 s medido por `smoke.sh`) | `scripts/measure-cutover.sh <url-base>` consulta cada segundo, por el `Ingress`, una ruta de C1 sin sesión. Una respuesta en Problem Details de `session-api` cuenta como «arriba»; un `502`/`503` de nginx o un error de conexión, como «abajo». Imprime la racha más larga de «abajo». Umbral: ≤ 90 s. Si se supera, se investiga el tramo (descarga, arranque o barrido); nunca se sube la cifra en silencio. Solo HTTP, dentro del alcance de `check-no-cluster-apply.sh` | Cierra R-03 y R-04 |
| IDS-U7-12 | Revisión 1 de esta etapa (§1 «Sondas») | Radio de impacto: `/readyz` en `503` (bajo 50 MiB libres, sobre la cuota o con el volumen colgado) saca del `Service` a **toda** la API, con su réplica única. Se mantiene, porque lo fija el NFR Design aprobado. La cuota (2 GiB) salta mucho antes que el disco del nodo (80 GB), y la regla del 80 % avisa antes que la cuota | reliability-design §4; cierra R-05 |
| IDS-U7-13 | Revisión 1 de `monitoring-design.md` (§2 y §5) | Las reglas de U7 viven en el subchart `monitoring-rules` de U2 y su prueba en `deploy/veridicus/tests/report-rules.yaml`. El original del panel está en `services/session-api/observability/review-report.json`. **Petición a U2:** empaquetarlo con el mismo SHA-256, comprobado por `check-config-copy.sh`, como IDS-U6-07. Todo se renderiza solo con `monitoring.enabled: true` | IDS-U3-10; observability-design §3 y §5 |
| IDS-U7-14 | NFR Design de U2 §9 (alcance de `check-no-cluster-apply.sh`) | **Petición a U2:** el alcance suma `evaluation/mttv/`, donde vive el arnés de MTTV, igual que IDS-U4-07 y IDS-U6-05. `scripts/measure-cutover.sh` ya está en el alcance (`scripts/`) | AUTONOMIA-01 |
| IDS-U7-15 | `team.md` (`## Deployment`, dos máquinas y etapa GPU) y revisión 1 §1 («Máquinas») | Un solo equipo de 64 GB, solo CPU. U7 no tiene valores por máquina. El arnés de MTTV corre en WSL2 contra `https://veridicus.local:8443` con el analista sintético del `.env` no versionado, como IDS-U4-08 | IDS-U2-01, IDS-U2-02, IDS-U2-04 |
| IDS-U7-16 | Revisión 1 de esta etapa §1.2 | Las siete claves van en `veridicus-session-api-config` y las lee también el `Job` de retención, que usa el mismo almacén en `purge_session`. **Petición a U2:** el `Job` de retención monta el `ConfigMap` (o esas siete claves) y el PVC en la misma ruta que la API | IDS-U5-01; security-design §11 |
| IDS-U7-17 | `nfr-requirements/security-requirements.md` (NFR-U7-07) | Se cumple con `veridicus-web` sin disco en todo `/api/` (U2 §2.4). La vista previa y la exportación son respuestas y no las limita el tope de cuerpo. No hace falta otro `Ingress` | NFRD-U7-13; NFR1.3 |

## 7. Cierre de los hallazgos de la revisión 1 · nuevo

| Hallazgo | Dónde se cierra |
|---|---|
| R-01 (nombre del contenedor `api` frente a `session-api`) | IDS-U7-06; la prueba de nivel 0 de IDS-U7-04 comprueba que el contenedor de la línea de `verify_store` existe en el render. `export_store` ya no está en un *script* (IDS-U7-07) |
| R-02 (alcance de `idle_in_transaction_session_timeout`) | §2 e IDS-U7-05: `SET LOCAL` de 15 s por transacción y prueba del almacén de 4,5 s |
| R-03 (el costo de `Recreate` no contaba la descarga de la imagen) | §1 e IDS-U7-11: la cifra incluye la descarga de las capas nuevas; umbral ≤ 90 s, medido |
| R-04 (SLO de corte sin comando) | IDS-U7-11 (`scripts/measure-cutover.sh`); `cicd-pipeline.md` §2 y §3 |
| R-05 (radio de impacto de `/readyz`) | IDS-U7-12 |
| R-06 (proceso de `kubectl exec` fuera de la cuenta de memoria) | §1.1 e IDS-U7-09; la prueba de nivel 1 limita el pico de `export_store` |
