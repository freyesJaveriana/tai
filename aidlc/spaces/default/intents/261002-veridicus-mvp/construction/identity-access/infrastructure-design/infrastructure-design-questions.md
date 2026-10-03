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
