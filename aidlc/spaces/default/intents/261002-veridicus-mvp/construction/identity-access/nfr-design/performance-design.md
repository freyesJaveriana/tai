# Diseño de rendimiento — U3 identity-access

**Insumos.** `nfr-requirements/performance-requirements.md` (performance-requirements),
`security-requirements.md` (security-requirements), `scalability-requirements.md`
(scalability-requirements), `reliability-requirements.md` (reliability-requirements),
`observability-requirements.md` (observability-requirements) y `tech-stack-decisions.md`
(tech-stack-decisions, D1–D12) de esta unidad; flujos F1–F9 de `functional-design/functional-spec.md`
(functional-spec); C1, C12, C15 y C16 de `inception/contract-design/contract-summary.md`
(contract-summary); respuestas P1–P2 de `nfr-design-questions.md`; diseño de seguridad de U1 y
prácticas de `team.md` y `project.md`.

## 1. Presupuestos por camino

| Camino | Meta (performance-requirements) | Desglose de diseño |
|---|---|---|
| `POST /auth/login` correcto (F1) | NFR3.1: p95 ≤ 1,0 s | Limitador en Redis ≤ 5 ms; búsqueda del usuario por índice ≤ 5 ms; espera del semáforo 0 s sin contención; Argon2id ≈ 0,3–0,6 s en CPU; alta de `WebSession` ≤ 10 ms. Margen ≥ 0,3 s |
| Ruta autenticada (F2) | NFR3.2: p95 ≤ 25 ms | 1 consulta por clave (`token_sha256`) que trae sesión y usuario con un `JOIN`; 1 `UPDATE` de `last_seen_at` (P1 = A); comparación de CSRF y rol en memoria. Sin consultas extra por la autorización |
| `429` del limitador | NFR3.3: p95 ≤ 50 ms | Un `GET` del contador en Redis antes de tocar la base o Argon2id |

## 2. Verificación de contraseñas: semáforo con espera acotada (P2 = A)

- Un `threading.BoundedSemaphore(2)` por proceso envuelve solo la llamada a `argon2-cffi`; la búsqueda
  del usuario y el limitador corren antes, fuera del semáforo.
- La petición espera turno como máximo **5 s** (`VERIDICUS_ARGON2_QUEUE_SECONDS`, entero 1–30,
  validado al arrancar). Sin turno a tiempo: `503` `system.unavailable` con `Retry-After: 5` y
  `veridicus_auth_login_total{outcome="error"}`. Un intento que no llegó a verificar **no** cuenta
  como fallo en el limitador.
- El hash señuelo de F1 pasa por el mismo semáforo, para que el usuario inexistente cueste lo mismo
  (NFR10.6).
- FastAPI ejecuta la ruta síncrona en su *threadpool* (40 hilos por defecto); 2 verificaciones a la vez
  dejan hilos libres para las rutas autenticadas, que no esperan al semáforo.

```python
def verify_with_budget(hasher, stored_hash: str, password: str) -> bool:
    if not ARGON2_SLOTS.acquire(timeout=settings.argon2_queue_seconds):
        raise SystemUnavailable(retry_after=5)
    try:
        return hasher.verify(stored_hash, password)
    finally:
        ARGON2_SLOTS.release()
```

## 3. Acceso a datos

| Decisión | Detalle | Requisito |
|---|---|---|
| Índices | `User(username_normalized)` único; `WebSession(token_sha256)` único; `WebSession(user_id) WHERE revoked_at IS NULL` para revocar al desactivar; `WebSession(expires_at)` para el barrido | NFR3.1, NFR3.2, NFR8.3 |
| Actividad (P1 = A) | `UPDATE web_session SET last_seen_at = now() WHERE id = :id` en cada petición autenticada, en la misma transacción corta de F2 | NFR10.3 |
| Pool de conexiones | SQLAlchemy `pool_size = 5`, `max_overflow = 5`, `pool_timeout = 2 s`, `pool_pre_ping = true`, `pool_recycle = 1 800 s` | NFR3.2, NFR10.11 |
| Redis | Un `ConnectionPool` por proceso, `socket_timeout = 0,5 s` | NFR3.3, NFR10.11 |
| Caché | Ninguna para sesiones ni usuarios: la revocación debe valer en la petición siguiente | NFR10.3 |

Con ≤ 20 sesiones web y un sondeo de la consola cada pocos segundos, el `UPDATE` por petición queda en
decenas de escrituras por segundo como mucho, muy por debajo de lo que soporta PostgreSQL en la máquina.

## 4. Cómo se mide

Las pruebas `perf` de nivel 1 (D11) miden con `time.perf_counter` alrededor de la llamada HTTP en
proceso y calculan el p95 sobre las cargas de performance-requirements (30, 200 y 50 peticiones). Una
prueba adicional lanza 10 inicios de sesión simultáneos y exige 10 respuestas `204` (ningún `503`), lo
que prueba que la espera de 5 s alcanza con p95 de 1 s.
