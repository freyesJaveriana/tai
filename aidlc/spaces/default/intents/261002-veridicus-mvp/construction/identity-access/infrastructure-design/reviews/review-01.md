## Review

**Verdict:** READY
**Reviewer:** aidlc-architecture-reviewer-agent
**Date:** 2026-10-03T10:30:00Z
**Iteration:** 1

### Findings

| ID | Severity | Location | Finding | Required action | Status |
|---|---|---|---|---|---|
| R-01 | Major | aidlc/spaces/default/intents/261002-veridicus-mvp/construction/identity-access/infrastructure-design/infrastructure-specification.md > §1.2 Sondas (fila `scripts/smoke.sh` y monitoreo); cicd-pipeline.md > §3 paso 6; monitoring-design.md > §1 fila «Redis disponible para U3» | Tras P1 = B, el `/readyz` completo es la única señal de Redis, pero no hay camino ni consumidor que lo ejecute. (a) §1.2 dice que Prometheus lo consulta «cada 30 s», mientras monitoring-design §1 dice «sin exportador ni sonda externa»; no existe ServiceMonitor, blackbox ni regla que lo haga. (b) cicd-pipeline §3 paso 6 ejecuta `smoke.sh https://veridicus.local` contra `/readyz`, pero la entrada de U3 es solo la ruta `/api/` del Ingress (spec §1 «Entrada»); `/healthz` y `/readyz` no cuelgan de `/api/`. No pude confirmar en U2 si hay otra ruta o `port-forward`: el hook de alcance impidió abrir su archivo. Efecto: con Redis caído el pod sigue «listo», `VeridicusSessionApiNotReady` no se dispara, y la caída solo se nota cuando alguien falla al iniciar sesión (`outcome="error"`). | Elegir un único mecanismo y escribirlo igual en los tres documentos. Por ejemplo, una regla o sonda que consulte `/readyz` completo en el puerto interno y una alerta propia de Redis, o retirar la frase «cada 30 s desde Prometheus». Indicar cómo `smoke.sh` llega a `/readyz` (ruta del Ingress o `kubectl port-forward`) y confirmarlo con U2. | New |
| R-02 | Major | cicd-pipeline.md > §1 jobs 1–7 y §3 paso 4; monitoring-design.md > §2 (promtool) y §6 (dashboard); infrastructure-specification.md > §2.2 (chart `create-admin-job`) | Los artefactos de despliegue propios de U3 no tienen un comando de puerta definido en `session-api.yml`. El *workflow* solo se dispara con `services/session-api/**`, `libs/**`, `contracts/**`; no con `deploy/**`. Las `PrometheusRule` con «prueba en `promtool test rules`» no tienen job con ese comando. El chart `create-admin-job`, el `ServiceMonitor`, el JSON del panel y la NetworkPolicy de §3 dependen de un `deploy-level0.yml` de U2 (§3 paso 4) sin que se diga que cubra `promtool`, las reglas de U3 ni la comprobación de que ningún flujo aplica el `Job` (AUTONOMIA-01). Incumple AUTONOMIA-02 (comando y umbral por puerta). | Añadir a `session-api.yml` o citar explícitamente en `deploy-level0.yml` los comandos: `promtool test rules`, `helm template` → `kubeconform` → Kyverno sobre el subchart y el `create-admin-job` (con `createAdmin.enabled=true` y `false`), y la comprobación estática de AUTONOMIA-01. Cada uno con su umbral de falla. | New |
| R-03 | Minor | infrastructure-specification.md > §1.2 (fragmento `readyz`) y §5 | `probe: Literal["full","kubernetes"]` hace que FastAPI responda `422` ante otro valor, y C16 solo declara `200` y `503`. La precisión sobre C16 no menciona el parámetro como contrato ni la prueba de NFR10.13, que ahora debe cubrir las dos variantes (Redis caído: `kubernetes` 200, `full` 503). | Declarar el comportamiento ante un valor desconocido (tratarlo como `full`) y listar en `test-level1` las dos variantes. | New |
| R-04 | Minor | infrastructure-specification.md > §2.1 y §2.2; cicd-pipeline.md > §3.1 y §4 | El Secret `veridicus-bootstrap-admin` con la contraseña del primer `admin` sigue en el clúster y en el `.env` después de que el `Job` termina. No hay paso de borrarlo ni de cambiar la contraseña. | Añadir al primer despliegue un paso de borrado del Secret tras `bootstrap.admin_created` (o aceptar el riesgo por escrito). | New |
| R-05 | Minor | infrastructure-specification.md > §1.1 | Argon2id: 2 × 64 MiB = 128 MiB, no los «≥ 160 MiB» que cita la fila. La cifra de logical-components §4 incluye margen, pero la tabla no lo dice. Con límite de 768 MiB no hay riesgo real. | Escribir «128 MiB + margen» o explicar el origen de 160. | New |
| R-06 | Minor | monitoring-design.md > §3 limitación conocida; infrastructure-specification.md > §1 Dirección de origen | `VERIDICUS_TRUSTED_PROXY=10.244.0.0/16` se da por cierto (CIDR de Calico en Minikube) sin verificarlo aquí. Con ingress-nginx todos llegan con la misma dirección, así que 5 fallos de cualquier cliente bloquean a todos 15 min, incluido el `admin`. Está documentado, pero equivale a una denegación de servicio trivial. | Registrar el CIDR como dato a verificar en U2 y aceptar o mitigar el bloqueo global, por ejemplo con el contador por usuario como primario. | New |
| R-07 | Minor | infrastructure-specification.md > §3 | Faltan en la tabla de red el origen de las sondas del kubelet (tráfico del nodo; depende de que Calico lo permita por defecto) y la salida a CoreDNS del `create-admin-job` (solo cita `veridicus-pg:5432`). | Anotar ambos casos para que el artefacto de NetworkPolicy no rompa el `Job` ni las sondas. | New |
| R-08 | Minor | cicd-pipeline.md > §1 job 4 `test-perf` | Una puerta bloqueante de p95 ≤ 1 s para Argon2id, «sin reintentos», corre en runners compartidos de GitHub con CPU variable. Riesgo de falsos fallos; las reglas del equipo prohíben ocultarlos con reintentos y bajar umbrales. | Fijar y documentar el tamaño del runner, o registrar el criterio para tratar una falla como inestable (aislarla con un *issue* enlazado, sin bajar el umbral). | New |

### Validation Tool Results

| Tool | Result | Interpretation |
|---|---|---|
| JSON de `traceability.json` | Válido | Parsea correctamente. |
| 28 IDs frente a `nfr-requirements/` | PASS | 28 IDs en ambos lados, sin faltantes ni sobrantes. |
| `N/A` (NFR10.4, NFR10.6, NFR10.15) | Justificados | Son lógica de aplicación y están cubiertos en security-design y reliability-design. |
| P1 = B en los tres documentos | Consistente | Aparece en infrastructure-specification §1.2 y §5, monitoring-design §1 y traceability NFR10.13; su precisión sobre C16 y NFR10.13 está registrada. La salvedad es R-01. |
| AUTONOMIA-01 | OK | `create-admin-job` y migraciones los aplica el humano, quedan fuera de Argo CD y sin `kubeconfig` en la CI. La comprobación estática depende de R-02. |
| AUTONOMIA-02 | Parcial | Casi todas las puertas tienen comando y umbral; falta `promtool` y la validación de manifiestos (R-02). |
| Recursos, sondas y conexiones frente a NFR | Coherentes | Pool 5+5 frente a 50 conexiones, timeouts de 0,5, 1 y 2 s, 2 CPU para 2 Argon2id y 768 MiB de límite. Sin hallazgos, salvo R-05. |
| Fragmentos de código | PASS | El único fragmento (`readyz`) tiene 8 líneas. |
| Alcance de lectura | Limitado | El hook impidió abrir los archivos de U2 que las instrucciones permitían, así que las referencias a U2 (Ingress, CIDR, `smoke.sh`, `deploy-level0.yml`) no se contrastaron. |

### Summary

El diseño es coherente con los NFR de U3 y la decisión P1 = B está bien registrada. Lo que más pesa antes de aprobar es que el `/readyz` completo, ahora única señal de Redis, no tiene un consumidor ni un camino definidos (R-01), y que las pruebas de alertas y de manifiestos de U3 no tienen un comando de puerta (R-02).
