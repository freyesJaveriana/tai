# Preguntas de Infrastructure Design — U7 forensic-report

**Unidad.** U7 `forensic-report` (tipo `service`): finalizar la sesión, consolidar el reporte con la
acción explícita del analista dueño (quién, cuándo y SHA-256 de los bytes guardados), versiones de
corrección que nunca reescriben la anterior, descarga con comprobación de integridad y barrido de
huérfanos. U7 no tiene `Deployment` propio: vive en la API de `session-api` y guarda cada reporte como
archivo en el PVC `veridicus-reports` («archivo antes que fila»).

**Lo que ya está decidido y no se vuelve a preguntar.** Minikube + Calico en ambas máquinas, un
namespace `veridicus`, `storage-provisioner` de Minikube (`StorageClass` `standard`, hostPath dentro del
nodo), el PVC de reportes `ReadWriteOnce` montado solo en la API de `session-api` (reservado por U2 con
2 GiB), 1 réplica de la API, CloudNativePG con sus roles, `pg_dump` a pedido con
`scripts/backup-db.sh`, kube-prometheus-stack sin Alertmanager (alertas informativas), sonda de la API
sin Redis, límites con ≥ 20 % sobre los picos, y Pod Security `restricted` (sin `hostPath` en los
pods). De U7 (NFR Requirements y NFR Design aprobados): render determinista, escaneo C8 antes del
SHA-256, `O_EXCL` + `fsync` + enlace sin reemplazo, plazos de 5 s (volumen) y 10 s (consolidación),
cancelación cooperativa del almacén (P2 = A), `expected_cursor` en el cuerpo (P1 = A), barrido al
arrancar con margen de 300 s, `/readyz` con mínimo de 50 MiB libres, `verify_store` como comando y
`Job` revisable con el volumen en solo lectura, y nada se reintenta solo. Quedan tres huecos que solo la
infraestructura de U7 puede cerrar y que ningún artefacto aprobado resuelve.

---

## P1 — Estrategia de actualización de la API de `session-api`: `Recreate` o `RollingUpdate`

Hay dos decisiones aprobadas que se contradicen: NFR8.6 y D8 de U7 piden `strategy: Recreate` (y una
política Kyverno de nivel 0 que falla con `RollingUpdate` mientras el PVC sea `ReadWriteOnce`), para que
el barrido de huérfanos de un pod nuevo nunca conviva con una consolidación en vuelo del viejo; pero
el Infrastructure Design de U2, U3, U5 y U6 fijó `RollingUpdate` con `maxSurge: 1` / `maxUnavailable: 0`
para la API. En Minikube de un solo nodo, `ReadWriteOnce` no lo impide (el acceso es por nodo): con
`RollingUpdate` los dos pods montan el volumen a la vez durante unos segundos.

A. `Recreate` en el `Deployment` de la API (solo la API; el trabajador de `session-api` sigue con
   `RollingUpdate`), con `terminationGracePeriodSeconds: 30` para que termine una consolidación en
   curso (≤ 10 s) antes de soltar el volumen, y la política Kyverno de NFR8.6. Cada despliegue de la
   API deja la consola sin servicio unos 20–40 s (arranque, barrido y `/readyz`); el humo posterior al
   despliegue ya lo detecta si no vuelve. Se anota como precisión en las tablas de U2, U3, U5 y U6, sin
   editarlas. (Recomendada)
B. Se mantiene `RollingUpdate` `maxSurge: 1` / `maxUnavailable: 0` y se relaja NFR8.6: sin corte en
   cada despliegue, confiando en el margen de 300 s del barrido para no borrar el archivo del otro pod.
   Obliga a reabrir un requisito aprobado de U7, a quitar la política Kyverno y a probar en nivel 1 el
   barrido con dos procesos sobre el mismo directorio.
C. `RollingUpdate` con `maxSurge: 0` / `maxUnavailable: 1`: el pod viejo se detiene antes de crear el
   nuevo, igual que `Recreate` en la práctica, pero la política Kyverno debe comprobar los dos valores
   en lugar de la estrategia.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P2 — Respaldo de los archivos del volumen de reportes

`scripts/backup-db.sh` solo hace `pg_dump`: copia las filas de `ReportVersion` pero no los archivos del
PVC, que son la evidencia descargable cuyo SHA-256 se verifica. Si se pierde el volumen (por ejemplo,
con `minikube delete`), las filas sobreviven en el volcado, pero cada descarga responde `409`
`report.integrity_mismatch` y no hay de dónde restaurar. NFR Requirements dejó el RPO y el RTO de los
reportes a esta etapa. Los datos del MVP son solo sintéticos.

A. Respaldo conjunto a pedido: `scripts/backup-db.sh` (revisable, entra por PR) hace primero el
   `pg_dump` y después copia los archivos con `kubectl exec … tar` en solo lectura desde el pod de la
   API hacia `backups/veridicus-reports-<fecha>.tar` en la anfitriona, con un `SHA256SUMS`; `backups/`
   ya está en `.gitignore`. El orden base → volumen garantiza que toda fila restaurada tenga su archivo.
   La restauración es un paso manual documentado en `docs/operacion/instalacion.md` y termina con el
   `Job` de `verify_store` (0 versiones sin archivo, 0 SHA-256 distintos). RPO = el último respaldo
   manual; se ejecuta en los mismos momentos que hoy (antes de la sustentación o de un cambio de
   esquema). (Recomendada)
B. Un `Job` revisable separado que empaqueta el volumen en solo lectura y deja el archivo en un segundo
   PVC de respaldos dentro del clúster. No necesita `kubectl exec`, pero el respaldo vive en el mismo
   nodo y se pierde igual con `minikube delete`.
C. Sin respaldo de archivos en el MVP: se acepta perder los reportes con el volumen (datos sintéticos);
   tras una pérdida, `verify_store` lista las versiones sin archivo y el analista vuelve a consolidar en
   una sesión nueva.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P3 — Cómo se mide el llenado del volumen con el aprovisionador hostPath

NFR15.3 aprobó la alerta `kubelet_volume_stats_used_bytes / kubelet_volume_stats_capacity_bytes > 0.8`
y NFR10.19 un `/readyz` en `503` bajo 50 MiB libres. Con el `storage-provisioner` de Minikube (hostPath)
el kubelet **no publica** `kubelet_volume_stats_*` para ese PVC, y el tamaño pedido no se hace cumplir:
el pod ve el disco entero del nodo (≈ 80 GB). Tal como está, la alerta nunca dispararía y el umbral de
50 MiB solo saltaría con el disco del nodo casi lleno.

A. La API mide su propio directorio frente a una cuota configurada igual a la capacidad del PVC
   (`VERIDICUS_REPORT_VOLUME_QUOTA_BYTES`, validada al arrancar): publica los *gauges*
   `veridicus_report_volume_used_bytes` y `veridicus_report_volume_quota_bytes` en el puerto 8081; la
   regla de NFR15.3 pasa a usarlos (> 0,8 durante 10 min, misma prueba `promtool` con 75 % y 85 %), y
   `/readyz` usa el menor entre «cuota − usado» y el espacio libre real del disco. El costo es recorrer
   el directorio (≤ 1 000 archivos, ≤ 50 ms) cada 60 s. Se anota como precisión a NFR15.3 y a C15.
   (Recomendada)
B. Se mantiene lo aprobado y se acepta que la alerta no funcione con hostPath; el llenado se revisa a
   mano con `verify_store`, que pasa a informar los bytes ocupados.
C. Se quita la alerta del volumen en el MVP y queda solo `/readyz` sobre el espacio libre real del
   disco del nodo, con el mínimo de 50 MiB.
X. Other (please specify)

[Answer]: A **Mode:** guided
