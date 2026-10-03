# Requisitos de fiabilidad — U3 identity-access

**Insumos.** Flujos F1–F7 y §9 «Errores y bordes» de `functional-design/functional-spec.md`
(functional-spec) y reglas de `functional-design/rules.md` (rules); NFR10 de
`inception/requirements-analysis/requirements.md` (requirements); C1, C12 y C16 de
`inception/contract-design/contract-summary.md` (contract-summary); P4 = A de
`nfr-requirements-questions.md`.

## 1. Objetivo

El MVP no tiene SLA: corre en la máquina de desarrollo y en la demostración. El objetivo medible es que
U3 no cause fallos en las pruebas de punta a punta: **0 fallos atribuibles a autenticación** en las 50
sesiones de NFR8 y en cada corrida de `scripts/smoke.sh`.

## 2. Requisitos

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR10.11 | Toda E/S de U3 tiene *timeout* explícito. | Consultas a PostgreSQL ≤ 2 s; operaciones de Redis ≤ 0,5 s; los valores salen de la configuración validada al arrancar. | Nivel 0 (configuración) y nivel 1 |
| NFR10.12 | Si la base o Redis no responden, U3 falla cerrado y lo dice. | Durante el inicio de sesión: `503` Problem Details `system.unavailable` con un `detail` en español, nunca `401` ni acceso concedido. En una ruta autenticada sin base: `503`. El limitador sin Redis no deja pasar el inicio de sesión. Pruebas de nivel 1 que detienen cada contenedor. | Nivel 1 |
| NFR10.13 | `/readyz` refleja lo que U3 necesita. | `503` si falta o es inválida la configuración de U3 (duraciones, parámetros de Argon2id, proxy de confianza) o si PostgreSQL o Redis no responden; el pod no arranca con configuración inválida. | Nivel 1 |
| NFR10.14 | `create-admin` es seguro de repetir. | Una segunda ejecución con un `admin` activo termina con código distinto de 0 y 0 filas nuevas (BR3.1, E10). | Nivel 1 |
| NFR10.15 | Dos cambios simultáneos nunca dejan cero `admin` activos. | En la prueba de E8, de dos desactivaciones simultáneas del último par de `admin` exactamente una gana y la otra recibe `409` `user.last_admin` (BR2.6). | Nivel 1 |

## 3. Recuperación

Las sesiones web viven en PostgreSQL: un reinicio del pod no cierra sesiones. Si Redis pierde sus
datos, solo se pierden los contadores de intentos (se reinician a cero). El respaldo de la base es de
CloudNativePG y lo fija Infrastructure Design.
