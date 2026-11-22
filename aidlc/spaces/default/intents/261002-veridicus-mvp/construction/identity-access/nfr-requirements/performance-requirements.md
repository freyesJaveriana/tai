# Requisitos de rendimiento — U3 identity-access

**Revisión 2 (2026-11-22), segunda pasada por el cambio 01, la adenda 02 y el Functional Design vigente
de U3.** Sustituye a la revisión 1 del 2026-10-03. Los requisitos conservan su ID; cada fila dice si **se
mantiene**, **cambia** o es **nuevo**. Entran NFR3.4 y NFR8.4. Ninguno se retira.

**Insumos.** Flujos F1, F2, F11 y F13 de `functional-design/functional-spec.md` (functional-spec,
revisión 2) y reglas BR1.4, BR1.5, BR2.12, BR8.4 y BR9.1 de `functional-design/rules.md` (rules); NFR3 y
NFR8 de `inception/requirements-analysis/requirements.md` (requirements, revisión 3); C1 y C12 de
`inception/contract-design/contract-summary.md` (contract-summary); P1 = A de
`nfr-requirements-questions.md`.

Las mediciones son en la máquina de desarrollo (CPU), con PostgreSQL y Redis reales en contenedor
(nivel 1). Los umbrales llevan margen para que la carga de la CI no los vuelva inestables; una prueba
inestable se arregla o se pone en cuarentena, nunca se reintenta (`team.md`).

## 1. Presupuesto de tiempo

| ID | Estado | Qué se mide | Objetivo | Carga | Cómo se mide |
|---|---|---|---|---|---|
| NFR3.1 | se mantiene | Inicio de sesión correcto (`POST /auth/login`, incluye Argon2id) | p95 ≤ 1,0 s | 30 inicios de sesión seguidos | Prueba `perf` de nivel 1, `time.perf_counter` alrededor de la llamada HTTP en proceso |
| NFR3.2 | cambia | Costo de F2 en una ruta autenticada de lectura (resolver sesión, rol) | p95 ≤ 25 ms | 200 peticiones `GET /auth/me`; el reloj avanza 61 s cada 10 peticiones, así que el 10 % escribe `last_seen_at` (cierra R-01) | Prueba `perf` de nivel 1 |
| NFR3.3 | se mantiene | Respuesta `429` del limitador | p95 ≤ 50 ms (no verifica la contraseña) | 50 peticiones bloqueadas | Prueba `perf` de nivel 1 |
| NFR3.4 | nuevo | Costo de F2 en una ruta que cambia estado (sesión, CSRF, bloqueo compartido del usuario, rol y validación del cuerpo contra el OpenAPI) | p95 ≤ 30 ms sobre el manejador de control vacío | 200 `POST` a una ruta de control con un cuerpo válido | Prueba `perf` de nivel 1 |

El registro de acceso (F11) no entra en estos presupuestos: con el adaptador por defecto no hace E/S, y
con el real tiene su plazo de 500 ms (NFR10.21); su latencia la mide U13.

## 2. Recursos

| ID | Estado | Requisito | Criterio medible |
|---|---|---|---|
| NFR8.1 | se mantiene | La verificación de contraseñas no agota la memoria del pod. | Como máximo 2 verificaciones Argon2id a la vez por proceso (semáforo); con 10 inicios de sesión simultáneos, el consumo extra de memoria de `session-api` no pasa de 160 MiB y todos terminan sin error. El `limits.memory` de `session-api` que fije Infrastructure Design deja ese margen. |
| NFR8.4 | nuevo | La espera del semáforo de Argon2id está acotada (T11). | Una petición que espera el semáforo más de 5 s responde `503` `system.unavailable` sin verificar la contraseña y sin contar un fallo. Prueba de nivel 1 con el semáforo ocupado por un doble lento. |

## 3. Fuera de alcance

La latencia por turno, el *N* de la prueba de humo y las latencias de exportación o de registro real de
acceso no dependen de U3: los fijan U4, U11, U7 y U13.
