# Requisitos de rendimiento — U3 identity-access

**Insumos.** Flujos F1 y F2 de `functional-design/functional-spec.md` (functional-spec) y reglas de
`functional-design/rules.md` (rules); NFR3 y NFR8 de `inception/requirements-analysis/requirements.md`
(requirements); C1 y C12 de `inception/contract-design/contract-summary.md` (contract-summary);
respuesta P1 = A (Argon2id) de `nfr-requirements-questions.md`.

Las mediciones son en la máquina de desarrollo (CPU), con PostgreSQL y Redis reales en contenedor
(nivel 1). Los umbrales llevan margen para que la carga de la CI no los vuelva inestables; una prueba
inestable se arregla o se pone en cuarentena, nunca se reintenta (team-practices).

## 1. Presupuesto de tiempo

| ID | Qué se mide | Objetivo | Carga | Cómo se mide |
|---|---|---|---|---|
| NFR3.1 | Inicio de sesión correcto (`POST /auth/login`, incluye Argon2id) | p95 ≤ 1,0 s | 30 inicios de sesión seguidos | Prueba `perf` de nivel 1, `time.perf_counter` alrededor de la llamada HTTP en proceso |
| NFR3.2 | Costo de F2 en una ruta autenticada (resolver sesión, CSRF, rol) | p95 ≤ 25 ms | 200 peticiones `GET /auth/me` | Prueba `perf` de nivel 1 |
| NFR3.3 | Respuesta `429` del limitador | p95 ≤ 50 ms (no verifica la contraseña) | 50 peticiones bloqueadas | Prueba `perf` de nivel 1 |

## 2. Recursos

| ID | Requisito | Criterio medible |
|---|---|---|
| NFR8.1 | La verificación de contraseñas no agota la memoria del pod. | Como máximo 2 verificaciones Argon2id a la vez por proceso (semáforo); con 10 inicios de sesión simultáneos, el consumo extra de memoria de `session-api` no pasa de 160 MiB y todos terminan sin error. El `limits.memory` de `session-api` que fije U2 deja ese margen. |

## 3. Fuera de alcance

La latencia por turno de texto y el *N* de la prueba de humo no dependen de U3: los fija U4.
