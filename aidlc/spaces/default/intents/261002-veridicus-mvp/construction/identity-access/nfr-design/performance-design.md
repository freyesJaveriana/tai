# Diseño de rendimiento — U3 identity-access

**Revisión 2 (2026-11-22), segunda pasada por el cambio 01, la adenda 02 y NFR Requirements revisión 2
de U3.** Sustituye a la revisión 1 del 2026-10-03.
- **Se mantienen:** el semáforo de 2 con espera de 5 s (P2 = A) y el *pool* de conexiones.
- **Cambian:** la escritura de actividad pasa a una cada 60 s (NFR10.3), la verificación ya no retiene
  conexión de base (cierra R-07 c) y la medición suma memoria y una prueba sin inestabilidad (cierra R-08).
- **Nuevos:** presupuesto de NFR3.4 (ruta que cambia estado) y la espera acotada de NFR8.4.

**Insumos.** `nfr-requirements/performance-requirements.md` (performance-requirements),
`security-requirements.md` (security-requirements), `scalability-requirements.md`
(scalability-requirements), `reliability-requirements.md` (reliability-requirements),
`observability-requirements.md` (observability-requirements) y `tech-stack-decisions.md`
(tech-stack-decisions, D1–D17) de esta unidad, revisión 2; flujos F1, F2, F11 y F13 de
`functional-design/functional-spec.md` (functional-spec); C1, C12 y C25 de
`inception/contract-design/contract-summary.md` (contract-summary); respuestas P1–P2 de
`nfr-design-questions.md`; `security-design.md` de esta carpeta.

## 1. Presupuestos por camino

| Camino | Meta | Desglose de diseño |
|---|---|---|
| `POST /auth/login` correcto (F1) | NFR3.1: p95 ≤ 1,0 s | `reserve` en Redis ≤ 5 ms; T1 por índice único ≤ 5 ms; semáforo 0 s sin contención; Argon2id ≈ 0,3–0,6 s; T2 (relectura bloqueada, `INSERT` de `WebSession`, `succeed`) ≤ 15 ms. Margen ≥ 0,3 s |
| Ruta de lectura autenticada (F2) | NFR3.2: p95 ≤ 25 ms | 1 `SELECT` por clave primaria con `JOIN` al usuario; en el 10 % de las peticiones, 1 `UPDATE` condicional de `last_seen_at`; rol y dueño en memoria |
| Ruta que cambia estado (F2) | NFR3.4: p95 ≤ 30 ms sobre el manejador vacío | El `SELECT` anterior; CSRF en memoria (dos SHA-256); `SELECT … FOR SHARE` del usuario; `UPDATE` condicional; validación con el validador ya compilado |
| `429` del limitador | NFR3.3: p95 ≤ 50 ms | Un `EVAL` de `reserve`; ni base ni Argon2id |

El registro de acceso no entra en estos presupuestos: con el adaptador por defecto no hace E/S, y con el
real tiene su plazo de 500 ms (NFR10.21).

## 2. Verificación de contraseñas: semáforo con espera acotada (NFR8.1, NFR8.4)

- Un `threading.BoundedSemaphore(VERIDICUS_ARGON2_MAX_CONCURRENT)` (2) por proceso envuelve solo la
  llamada a `argon2-cffi`.
- La búsqueda del usuario (T1) se confirma **antes** de pedir turno: ninguna conexión de base queda
  retenida mientras se espera o se verifica, así 10 inicios simultáneos no agotan el *pool* de 5 + 5 y
  las rutas autenticadas no esperan (cierra R-07 c).
- Espera máxima `VERIDICUS_ARGON2_QUEUE_TIMEOUT_S` (5). Sin turno a tiempo: `release` del limitador (no
  cuenta como fallo), `503` `system.unavailable` con `Retry-After` igual al ajuste (cierra R-07 a) y
  `veridicus_auth_login_total{outcome="error"}`.
- El hash señuelo pasa por el mismo semáforo (NFR10.6).
- FastAPI ejecuta la ruta síncrona en su *threadpool* de 40 hilos; con 2 verificaciones y hasta 8 en
  espera quedan hilos libres.

```python
def verify_with_budget(hasher, stored_hash: str, password: str) -> bool:
    timeout = settings.argon2_queue_timeout_s
    if not ARGON2_SLOTS.acquire(timeout=timeout):
        raise ArgonQueueTimeout(retry_after=timeout)   # 503 system.unavailable
    try:
        return hasher.verify(stored_hash, password)
    finally:
        ARGON2_SLOTS.release()
```

## 3. Acceso a datos

| Decisión | Detalle | Requisito |
|---|---|---|
| Índices | `app_user(username_normalized)` único; `web_session` con clave primaria `session_token_hash`; `web_session(user_id) WHERE revoked_at IS NULL` para revocar; `web_session(expires_at)` y `web_session(last_seen_at)` para el barrido | NFR3.1, NFR3.2, NFR8.3 |
| Actividad | `UPDATE` condicional de `security-design.md` §5.2: escribe como máximo una vez cada 60 s y solo si la sesión sigue válida | NFR10.3, NFR3.2 |
| Validadores | Un `Draft202012Validator` compilado por operación al arrancar; nada se compila por petición | NFR3.4, D13 |
| Seguridad por ruta | `RouteSecurity` construido una vez al arrancar, diccionario por `operationId` | NFR3.2, NFR3.4 |
| *Pool* de PostgreSQL | SQLAlchemy `pool_size = 5`, `max_overflow = 5`, `pool_timeout = 2 s`, `pool_pre_ping = true`, `pool_recycle = 1 800 s` | NFR10.11 |
| Redis | Un `ConnectionPool` por proceso, `socket_timeout = 0,5 s`; los scripts Lua se registran una vez (`SCRIPT LOAD`) y se llaman con `EVALSHA`, con recarga si Redis los olvidó | NFR3.3, NFR10.11 |
| Caché | Ninguna para sesiones ni usuarios: la revocación vale en la petición siguiente | NFR10.3 |

Con ≤ 20 sesiones web y el sondeo de la consola, la escritura de actividad queda en menos de una por
sesión y minuto.

## 4. Cómo se mide (cierra R-08)

| Prueba (marca `perf`, nivel 1) | Carga | Umbral |
|---|---|---|
| NFR3.1 | 30 inicios de sesión seguidos con Argon2id real | p95 ≤ 1,0 s |
| NFR3.2 | 200 `GET /auth/me`; el reloj avanza 61 s cada 10 peticiones | p95 ≤ 25 ms |
| NFR3.3 | 50 peticiones bloqueadas | p95 ≤ 50 ms |
| NFR3.4 | 200 `POST` a una ruta de control con cuerpo válido, frente al mismo manejador sin `GuardedRoute` | p95 del sobrecosto ≤ 30 ms |
| NFR8.1 memoria | Subproceso nuevo: calienta con 1 inicio, lee `resource.getrusage(RUSAGE_SELF).ru_maxrss`, lanza 10 inicios simultáneos con Argon2id real y vuelve a leer | Diferencia ≤ 160 MiB y 10 respuestas `204` |
| NFR8.1 cola | 10 inicios simultáneos con un verificador falso de 0,5 s fijos y 2 ranuras | 10 `204`; la última espera ≈ 2 s, lejos de los 5 s |
| NFR8.4 | Semáforo ocupado por un doble que tarda 6 s | `503` `system.unavailable` con `Retry-After: 5`, sin verificar y sin contar fallo |
| Pool sin agotar | 10 inicios simultáneos con el verificador falso y, a la vez, 20 `GET /auth/me` | Todas las `GET` < 25 ms |

`time.perf_counter` alrededor de la llamada HTTP en proceso (D11). El verificador falso evita que la
prueba de cola dependa de la CPU de la CI, que la política no deja reintentar. Comando:
`uv run --directory services/session-api pytest -m perf`.
