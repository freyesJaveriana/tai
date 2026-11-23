# Preguntas de Infrastructure Design — U13 ethics-governance

**Unidad.** U13 `ethics-governance` (tipo `service`): EthicsGovernance, la demostración del protocolo ético
de la adenda 02. Registra accesos y exportaciones, guarda reconocimientos, reportes de problemas y cambios de
plazo, y borra lo vencido con el `Job` de purga `veridicus-retention`. U13 no despliega un servicio propio: su
código corre en la API de `session-api` (U3), en el `Job` de retención con la misma imagen, en un comando
por `kubectl exec` dentro del contenedor de la API y en la consola (`frontend`, U4). Es la **primera pasada**
de esta etapa para U13; no hay revisión anterior que sustituir.

---

# Segunda pasada — cambio 01, adenda 02 y NFR Design revisión vigente (2026-11-23)

## Lo que ya está decidido

- **NFR Design de U13, revisión 1 (aprobado):** forma del `Job` (NFR-U13-07: mismo UID y GID que
  `session-api`, los dos PVC en escritura, `backoffLimit: 0`, sin `ttlSecondsAfterFinished`,
  `activeDeadlineSeconds` de 3 600 s hasta medirlo; `requests` 250m y 256 MiB, `limits` 1 CPU y 512 MiB);
  bloqueo de la sesión con funciones `SECURITY DEFINER` de U4 y U7 (NFRD-U13-05, NFRD-U13-07); claves de
  cancelación en Redis antes de borrar, con fallo cerrado (NFRD-U13-06); `log_error_verbosity: terse`
  (NFRD-U13-09); ningún manifiesto baja `retention_max_days` (NFRD-U13-10); comando de consulta por
  `kubectl exec` en el contenedor `session-api` con `veridicus_app` en `READ ONLY` (NFR-U13-08, NFR-U13-09);
  ninguna métrica nueva y ningún camino de red hacia fuera. La entrega a Infrastructure Design está en
  `logical-components.md` §5.
- **Lo que ya fijaron en esta etapa U2, U3, U4, U5, U6, U7 y U9:**
  - un solo equipo de 64 GB, solo CPU, con Minikube de 50 GiB y 16 CPU (IDS-U2-01);
  - el `Job` de retención con 0,25 / 256 MiB → 1 / 512 MiB y `activeDeadlineSeconds` 3 600 (U2 §4), en
    `deploy/jobs/`, fuera de la `Application` de Argo CD (U2 `cicd-pipeline.md` §4.2);
  - `log_error_verbosity: "terse"` y los parámetros de log a 0 en `veridicus-pg` (U2 §2.1), y
    `check-limits-env.sh` contra `VERIDICUS_LIMIT_RETENTION_MAX_DAYS` (U2 §2.5);
  - la consulta de U13 en `readonly-exec-allowlist.yaml` (NFR Design de U2 §9);
  - `veridicus_purge_lock_session(uuid)` en la migración de U4 y `veridicus_purge_lock_report_versions(uuid)`
    en la de U7 (IDS-U7-10);
  - las siete claves de U7 en `veridicus-session-api-config`, que el `Job` también lee, y el PVC de reportes
    en la misma ruta que la API (IDS-U7-16); `veridicus-audio` montado solo en la API y en `retention-job`
    (IDS-U9-08);
  - `VERIDICUS_DB_LOCK_TIMEOUT_MS` = 2000 también en el `Job` (IDS-U5-02); `idle_timeout_s` en
    `session_api/shared/db.py` (IDS-U6-02).
- **Supuesto de máquina** (brief del 2026-11-22): una sola máquina de 64 GB, solo CPU, sin máquina GPU; el
  tamaño de Minikube lo decidió U2, la única unidad que lo pregunta.

## Cómo se registra la revisión

Revisión 1 de los cuatro artefactos de esta carpeta (`infrastructure-specification.md`,
`monitoring-design.md`, `cicd-pipeline.md` y `traceability.json`). Las precisiones a artefactos aprobados y
las peticiones a otras unidades son IDS-U13-01 en adelante, en §8 de `infrastructure-specification.md`.
Ninguna petición se da por aplicada.

## Lo que el diseño resolverá sin preguntar

- La forma de los dos manifiestos del `Job` (borrado y simulación), que U13 dejó a esta etapa: dos
  plantillas de `deploy/jobs/` con el mismo pod y distinto nombre y argumentos; `--as-of` solo en la
  simulación.
- Cómo lee el `Job` su configuración: referencias explícitas a cada clave de `veridicus-session-api-config`
  más su propio `VERIDICUS_RETENTION_SESSION_TIMEOUT_S`, para que falte una clave y el pod no arranque.
- La comprobación de que la memoria de la API, las conexiones de `veridicus-pg`, el volumen de PostgreSQL y
  Redis bastan sin cambios con U13 (el `Job` es transitorio y U2 no suma los `Job` al presupuesto).
- El plazo de inactividad de las transacciones del `Job` (NFRD-U13-14) con el parámetro de `db.py` que U6
  ya aceptó.
- Los pasos que U13 suma a `session-api.yml`, `frontend.yml` y `deploy-level0.yml`, y el runbook del
  borrado que ejecuta el humano.

Sin preguntas: todo lo fijan las fuentes.
