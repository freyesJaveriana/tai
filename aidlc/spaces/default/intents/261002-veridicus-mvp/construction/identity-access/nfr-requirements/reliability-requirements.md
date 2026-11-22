# Requisitos de fiabilidad — U3 identity-access

**Revisión 2 (2026-11-22), segunda pasada por el cambio 01, la adenda 02 y el Functional Design vigente
de U3.** Sustituye a la revisión 1 del 2026-10-03. Los requisitos conservan su ID; cada fila dice si **se
mantiene**, **cambia** o es **nuevo**. Entra NFR10.21 (registro de acceso). Ninguno se retira.

**Insumos.** Flujos F1–F13 y §9 «Errores y bordes» de `functional-design/functional-spec.md`
(functional-spec, revisión 2) y reglas BR2.6, BR2.11, BR2.12, BR3.1, BR8.3 y BR9.1–BR9.5 de
`functional-design/rules.md` (rules); NFR8 y NFR10 de `inception/requirements-analysis/requirements.md`
(requirements, revisión 3); C1, C12, C16 y C23 de `inception/contract-design/contract-summary.md`
(contract-summary); P4 = A de `nfr-requirements-questions.md`; preguntas 3 de U13 y de U7.

## 1. Objetivo

El MVP no tiene SLA: corre en la máquina de desarrollo y en la de demostración. El objetivo medible es
que U3 no cause fallos de punta a punta: **0 fallos atribuibles a autenticación o autorización** en las
50 sesiones de NFR8 y en cada corrida de `scripts/smoke.sh`.

## 2. Requisitos

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR10.11 | se mantiene | Toda E/S de U3 tiene *timeout* explícito. | Consultas a PostgreSQL ≤ 2 s (`statement_timeout` por conexión); operaciones de Redis ≤ 0,5 s; los valores salen de la configuración validada al arrancar. | Nivel 0 (configuración) y nivel 1 |
| NFR10.12 | cambia | Si la base o Redis no responden, U3 falla cerrado y lo dice (BR8.3). | Durante el inicio de sesión: `503` `system.unavailable` con `detail` en español, nunca `401` ni acceso concedido (E32). En una ruta autenticada sin base: `503`. El limitador sin Redis no deja pasar el inicio de sesión. Pruebas de nivel 1 que detienen cada contenedor. | Nivel 1 |
| NFR10.13 | cambia | `/readyz` refleja lo que U3 necesita y cómo está cableado. | `503` si PostgreSQL o Redis no responden. El pod no arranca con configuración inválida (duraciones fuera de rango, parámetros de Argon2id, proxy de confianza, cifras de C25 que el entorno intenta subir) ni con los casos de NFR10.16. Con el adaptador por defecto de `AccessLog`, `/readyz` responde `200` con `access_log: not_configured` (BR9.5, E38); informa también si `PendingSessions` es el real o el de por defecto (F13). | Nivel 0 y nivel 1 |
| NFR10.14 | cambia | `create-admin` es seguro de repetir y de lanzar dos veces. | Una segunda ejecución con un `admin` activo termina con código distinto de 0 y 0 filas nuevas (BR3.1, E10). Dos ejecuciones simultáneas sin `admin` activo: una crea el `admin` y la otra termina con código distinto de 0, gracias al bloqueo asesor del conjunto de admins (E26). | Nivel 1 |
| NFR10.15 | cambia | Los cambios concurrentes nunca dejan cero `admin` activos ni un cambio de rol cruzado con una acción del mismo usuario. | De dos desactivaciones simultáneas del último par de `admin`, exactamente una gana y la otra recibe `409` `user.last_admin` (BR2.6, E8); pasar al último `admin` a otro rol da `409` (E43). Un cambio de rol y una creación de sesión del mismo usuario, en los dos órdenes, terminan en «creación primero y cambio `409`» o «cambio primero y creación `403`» (BR2.12, E25). Ninguna prueba deja un interbloqueo: orden usuario → sesión → ronda. | Nivel 1 |
| NFR10.21 | nuevo | El registro de una lectura nunca rompe ni revierte la respuesta (BR9.1–BR9.5). | Tras un 2xx en una ruta marcada, `AccessLog.record` corre en un punto de guardado con plazo de 500 ms (NFR-U3-05). Si falla o vence: se revierte solo el punto de guardado, la respuesta sale con su 2xx y con las escrituras del manejador confirmadas, queda un log `WARNING` con IDs y sube `veridicus_access_log_failures_total` (BR9.3, E36). Una apertura y cinco sondeos con `since` producen una llamada (BR9.4, E37). Un rechazo (401, 403, 404, 422) no llama al puerto (BR9.1). | Nivel 1 (doble del puerto que falla, que tarda 600 ms y que funciona) |

## 3. Recuperación

- Las sesiones web viven en PostgreSQL: un reinicio del pod no cierra sesiones.
- Si Redis pierde sus datos, solo se pierden los contadores de intentos (se reinician a cero).
- El barrido de sesiones web (NFR8.3) es idempotente: si se interrumpe, el siguiente borra lo que faltó.
- Un `PATCH` de usuario que falla a mitad no deja nada aplicado (NFR11.5).
- El respaldo de la base es de CloudNativePG y lo fija Infrastructure Design.
