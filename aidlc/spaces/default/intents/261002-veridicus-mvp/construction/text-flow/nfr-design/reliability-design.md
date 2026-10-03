# Diseño de fiabilidad — U4 text-flow

**Insumos.** `nfr-requirements/performance-requirements.md` (performance-requirements),
`security-requirements.md` (security-requirements), `scalability-requirements.md`
(scalability-requirements), `reliability-requirements.md` (reliability-requirements),
`observability-requirements.md` (observability-requirements) y `tech-stack-decisions.md`
(tech-stack-decisions) de esta unidad; flujos F5–F8 de `functional-design/functional-spec.md`
(functional-spec); C2–C4, C13, C14 y C16 de `inception/contract-design/contract-summary.md`
(contract-summary); respuestas P1–P2 de `nfr-design-questions.md`.

## 1. *Timeouts* (NFR10.14)

| Llamada | *Timeout* | Ajuste |
|---|---|---|
| Consulta a PostgreSQL | 2 s (`statement_timeout`); 5 s en la transacción de indexación | Configuración del servicio |
| Operación de Redis | 0,5 s; `XREADGROUP` con `BLOCK 5000` y *timeout* de socket de 6 s | `socket_timeout` |
| *Embeddings* | 30 s por lote | `VERIDICUS_EMBEDDINGS_TIMEOUT_SECONDS` |
| Juez | 180 s por llamada | `VERIDICUS_JUDGE_TIMEOUT_SECONDS` |
| `count_tokens` | 5 s | Fijo |
| Conexión HTTP a un modelo | 2 s | `httpx.Timeout(connect=2)` |

## 2. Fallos del juez (P1 = A, NFR10.16)

| Falla | Tratamiento |
|---|---|
| Conexión rechazada, `502`, `503`, `504` | Hasta **2 reintentos** dentro del mismo procesamiento, con espera de 2 s y 6 s más una variación aleatoria de ±20 %, solo si `ahora + espera + 180 s < deadline_at`. Si sigue fallando: no se confirma el mensaje y vuelve por `XAUTOCLAIM` a los 240 s |
| *Timeout* de 180 s | `turn.error.timeout`, sin reintento automático (BR8.2) |
| Salida inválida (JSON, C6, pasajes o vocabulario) | `turn.error.invalid_output`, sin reintento automático (contract-design P3) |
| *Prompt* que no cabe | `turn.error.system`, sin llamar al juez |
| Otro `4xx` | `turn.error.system`, sin reintento (es un defecto, no algo pasajero) |

```python
TRANSIENT = (httpx.ConnectError, Status502, Status503, Status504)
def call_judge_with_retry(gateway, request, deadline_at, clock, sleep):
    for wait in (0, 2, 6):
        if wait and clock.now() + wait * 1.2 + JUDGE_TIMEOUT >= deadline_at:
            raise LeaveUnacked()
        sleep(wait * random.uniform(0.8, 1.2)) if wait else None
        try:
            return gateway.complete(request, timeout_s=JUDGE_TIMEOUT)
        except TRANSIENT:
            continue
    raise LeaveUnacked()
```

Los reintentos se cuentan en `veridicus_judge_duration_seconds{result="unavailable"}` y en un log
`WARNING` por intento. El juez atiende una ranura, así que reintentar no le suma carga paralela.

## 3. Entrega al menos una vez sin efectos dobles (NFR10.15)

- `XACK` + `XDEL` solo después del efecto: publicar C3 (evaluador) o confirmar la transacción
  (ingesta e indexador).
- Cada consumidor reclama pendientes con `XAUTOCLAIM` a los 240 s de inactividad; el contador de
  entregas de Redis decide: a la 3.ª sin confirmar, el mensaje va a `<cola>:failed` (solo
  identificadores) y el turno a `error` con `turn.error.system`.
- Idempotencia: restricción única (`turn_id`, `attempt`) en la ingesta; un resultado de un intento
  viejo se descarta (contract-design P3).

## 4. Ningún turno queda en curso (NFR3.5, NFR3.6, NFR10.17)

- Al encolar o reintentar: `deadline_at = enqueued_at + base × (1 + n)`, con `n` los turnos `queued` o
  `processing` de todo el sistema y tope de 3 600 s.
- El hilo de plazos del trabajador corre cada 15 s: `UPDATE … SET status = 'error', code =
  'turn.error.timeout' WHERE status IN ('queued','processing') AND deadline_at < now()` con
  `change_seq` incrementado por sesión; un resultado que llega tarde se descarta por intento.

## 5. Indexación todo o nada (NFR10.18)

Todos los lotes de *embeddings* se calculan antes de escribir; un fallo en cualquier lote deja la
versión en `error` con 0 pasajes. Una reentrega de una versión `ready` o `error` se confirma sin
efectos.

## 6. Procesos y salud (NFR10.19, C16)

| Proceso | `/readyz` responde `503` si… |
|---|---|
| `semantic-agent` | Umbral ausente o inválido; SHA-256 del *prompt* distinto; PostgreSQL (rol de solo lectura), Redis, `model-judge` o `model-embeddings` no responden; el calentamiento del juez no terminó |
| API de `session-api` | Configuración de U4 inválida; PostgreSQL o Redis no responden |
| Trabajador de `session-api` | Igual que la API, más `model-embeddings`, o alguno de sus tres hilos dejó de latir |

- **Supervisión de hilos del trabajador.** Cada hilo actualiza un latido en memoria en cada vuelta; si
  un hilo termina por una excepción no controlada, el proceso registra `ERROR` y termina con código
  distinto de 0 para que Kubernetes lo reinicie. No se reinician hilos a mano dentro del proceso.
- Configuración inválida: el proceso termina al arrancar con el log que nombra el ajuste.

## 7. Consola ante cortes (NFR10.20)

TanStack Query reintenta el sondeo con espera de 2, 4, 8, 16 y 30 s; mientras falla, M4 conserva lo
que mostraba y un aviso discreto dice que está reconectando. Al primer sondeo correcto vuelve al
intervalo normal y pide `since=<último cursor>`: con el contador por sesión (P2 = A) recibe todos los
cambios pendientes, sin huecos ni duplicados.

## 8. Determinismo y calidad de la IA (NFR4.1, NFR4.2, NFR4.4, NFR4.5, NFR6.1)

- Temperatura 0, `seed = VERIDICUS_JUDGE_SEED` y una ranura; la salida con gramática JSON de
  `llama-server` más la validación de C6 en U4.
- El constructor del *prompt* acepta el orden de los pasajes (directo o invertido) para el arnés de
  nivel 2.
- Las instrucciones piden, por afirmación, qué dice la afirmación, qué dice el pasaje y por qué
  difieren o coinciden, en español y en 20 a 80 palabras.
- El barrido del umbral (`evaluation/golden/threshold_sweep.py`) aplica la regla de NFR4.1 y su reporte
  JSON acompaña al PR del valor nuevo.

## 9. Objetivos de punta a punta (NFR8.5, NFR8.6)

Los patrones anteriores apuntan a ≥ 98 % de 50 sesiones sin turnos en error en la corrida de carga y a
0 fallos atribuibles a U4 en `scripts/smoke.sh`. Un fallo en cualquiera es un hallazgo con su `code`
en el reporte, no un reintento de la corrida.

## 10. Precisiones a artefactos ya aprobados

No edité ningún artefacto aprobado; decides en la aprobación si se actualizan.

| Artefacto | Qué precisa | Origen |
|---|---|---|
| `text-flow/nfr-requirements/reliability-requirements.md` (NFR10.16) | Ante conexión rechazada o `502`–`504` hay hasta 2 reintentos en el proceso (2 s y 6 s) antes de dejar el mensaje para el reclamo de 240 s | P1 = A |
| `text-flow/nfr-requirements/tech-stack-decisions.md` (§2) | Nuevos ajustes `VERIDICUS_JUDGE_TRANSIENT_RETRIES` (2, entero 0–3) y `VERIDICUS_JUDGE_RETRY_WAITS_SECONDS` (`2,6`) | P1 = A |
| `text-flow/functional-design/entities.md` | La sesión lleva `change_seq` y los turnos, sugerencias y paquetes la columna `change_seq` de su último cambio; el cursor de C1 es ese número codificado | P2 = A |
