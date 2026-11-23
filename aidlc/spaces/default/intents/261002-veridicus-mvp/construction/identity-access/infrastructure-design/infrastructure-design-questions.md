# Preguntas de Infrastructure Design — U3 identity-access

**Unidad.** U3 `identity-access` (tipo `service`): inicio y cierre de sesión, sesión web revocable,
anti-CSRF, roles y gestión de usuarios dentro de `session-api`. Como U3 es el primer Bolt que construye
`session-api` (B2), esta etapa fija su despliegue (réplicas, sondas, recursos, `Job` de `create-admin`),
que después amplían U4–U7.

**Lo que ya está decidido y no se vuelve a preguntar.** Uvicorn con 1 proceso por pod y 1 réplica en el
MVP; ≥ 160 MiB de memoria extra para Argon2id; `/metrics` en un puerto interno; Secrets de la clave
HMAC y del primer `admin`; `VERIDICUS_TRUSTED_PROXY` con la red del *ingress*; falla cerrada ante base
o Redis caídos; `create-admin` como `Job` revisable (diseños de `nfr-design/` y `nfr-requirements/`).
La distribución de Kubernetes, el *ingress* y los namespaces se deciden en las preguntas de U2.

Queda una decisión.

---

## P1 — Qué hace la sonda de disponibilidad de `session-api` cuando Redis no responde

Hoy `/readyz` responde `503` si Redis no responde (C16 y NFR10.13). Si esa ruta es la `readinessProbe`
de Kubernetes y el MVP corre 1 réplica, una caída de Redis saca al único pod del Service y **toda**
`session-api` queda inalcanzable, aunque las sesiones abiertas, la revisión de alertas y la consulta de
reportes no usan Redis. La revisión de NFR Design lo señaló (R-01) y se aceptó como riesgo en la
aprobación.

A. La `readinessProbe` usa `/readyz` tal como está (base, Redis y configuración). Una caída de Redis
   deja fuera toda la API hasta que Redis vuelva; se documenta ese radio de impacto real en el diseño
   de monitoreo. No cambia nada aprobado.
B. La `readinessProbe` usa una comprobación que solo mira la base y la configuración
   (`/readyz?probe=kubernetes`); el `/readyz` completo sigue siendo el de `scripts/smoke.sh` y del
   monitoreo. Con Redis caído, el inicio de sesión y el envío de turnos responden `503` (falla cerrada)
   y lo demás sigue funcionando. Precisa C16 y NFR10.13 aprobados, en la tabla de precisiones.
   (Recomendada)
C. Sin `readinessProbe` en `session-api` (solo `livenessProbe` con `/healthz` y `startupProbe`); el
   pod siempre recibe tráfico y cada ruta responde `503` si le falta su dependencia.
X. Other (please specify)

[Answer]: B **Mode:** guided

---

# Segunda pasada — cambio 01, adenda 02 y NFR Design revisión vigente (2026-11-23)

**Sin preguntas: todo lo fijan las fuentes.** Ninguna decisión de esta pasada enfrenta dos fuentes
aprobadas ni cambia el alcance, el riesgo aceptado, los recursos de la máquina o un dato que sale del
clúster (regla de `project.md` del 2026-11-22). El cambio de máquinas sí cambia recursos, pero esa
pregunta la hace solo U2 (`platform`); U3 usa el supuesto indicado abajo. Lo que se aplica sin preguntar
queda en la tabla IDS-U3-xx de `infrastructure-specification.md` §5 y se presenta en la aprobación.

## Lo que ya está decidido

- NFR Design de U3, revisión 2 (aprobado el 2026-11-22): `readinessProbe` sobre el `/readyz` completo,
  que depende de PostgreSQL y de Redis, aunque con una réplica la caída de Redis deje fuera toda la
  consola (reliability-design §2, logical-components §2 y §4; NFR10.13 revisión 2; C16 v2). Esto supera
  P1 = B de la revisión 1 de esta etapa, y `project.md` lo confirma («Con Redis caído manda la decisión de
  U3: /readyz deja toda la consola fuera de servicio»).
- Lo que U3 entrega a Infrastructure Design (logical-components §4): ≥ 160 MiB de memoria para Argon2id,
  puertos `http` 8080 y `metrics` 8081, Ingress solo HTTPS y sin disco en `/api/`, Secrets de la clave
  HMAC y del primer `admin`, `VERIDICUS_TRUSTED_PROXY` = pod CIDR, `managed.roles` de CloudNativePG,
  `create-admin` en `deploy/jobs/` fuera de Argo CD y `readOnlyRootFilesystem`.
- NFR Design de U2, revisión 2: patrón del Ingress sin disco y grupo `veridicus-web`, tabla cerrada de
  consumidores de Secrets y de volúmenes, `deploy/jobs/` fuera de la `Application`, reglas y paneles en
  `charts/monitoring-rules/`.
- Cambio de máquinas del 2026-11-22 (supuesto de esta unidad): **una sola máquina de 64 GB, solo CPU,
  con el tamaño de Minikube por decidir en U2**. No hay máquina GPU ni perfil GPU.

## Cómo se registra la revisión

- Los cuatro documentos y `traceability.json` se reescriben como revisión 2; la revisión 1 queda en el
  historial de Git.
- Las secciones conservan su número; cada documento dice qué **se mantiene**, qué **cambia** y qué es
  **nuevo**. Lo que salía de P1 = B queda «Retirado» sin renumerar.
- Se cierran los hallazgos R-01 a R-08 de `reviews/review-01.md` en las secciones que los citan.

## Lo que el diseño resolverá sin preguntar

- Sonda de disponibilidad sobre el `/readyz` completo y retiro de `probe=kubernetes` (cierra R-01 a y
  R-03).
- Nombres de recursos con el prefijo `veridicus-` y nombres de Secrets alineados con U2; peticiones a U2
  para la tabla de consumidores y para `managed.roles`.
- Cómo llega `scripts/smoke.sh` al `/readyz` (petición a U2; cierra R-01 b).
- Comandos de puerta para los manifiestos y las reglas de U3 (cierra R-02).
- Borrado del Secret del primer `admin` tras el `Job` (cierra R-04), cifra de memoria (R-05), origen del
  pod CIDR (R-06), sondas del kubelet y DNS del `Job` (R-07) y *runner* de la prueba de rendimiento (R-08).
