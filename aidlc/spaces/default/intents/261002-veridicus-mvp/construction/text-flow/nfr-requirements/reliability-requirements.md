# Requisitos de fiabilidad — U4 text-flow

**Insumos.** Flujos F2, F4–F7 y §8 «Errores y bordes» de `functional-design/functional-spec.md`
(functional-spec); reglas BR2.2, BR5.6–BR5.9, BR6.1, BR6.2, BR7.3, BR8.1, BR8.2 y BR11.1–BR11.3 de
`functional-design/rules.md` (rules); NFR4, NFR6, NFR8 y NFR10 de
`inception/requirements-analysis/requirements.md` (requirements); C2, C3, C4, C14 y C16 y las reglas de
propiedad de `inception/contract-design/contract-summary.md` (contract-summary); respuestas P1, P3,
P4, S1 y S3 de `nfr-requirements-questions.md`.

## 1. Objetivos

El MVP no tiene SLA: corre en la máquina de desarrollo y en la demostración. Los objetivos medibles
son los del PRD y de team-practices:

| ID | Objetivo | Criterio medible | Verificación |
|---|---|---|---|
| NFR8.5 | Éxito del *pipeline* de texto (NFR8). | ≥ 98 % de 50 sesiones de texto del Golden Dataset, en tandas de 3 concurrentes en CPU, terminan de punta a punta sin `OOMKilled` ni turnos en `error` (como máximo 1 sesión fallida). | Corrida de carga a demanda (`scalability-requirements.md` §3) |
| NFR8.6 | La prueba de humo no falla por U4. | 0 fallos atribuibles a U4 en cada corrida de `scripts/smoke.sh` tras un despliegue (NFR3.10). | Nivel 3 |

## 2. Requisitos

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR10.14 | Toda E/S de U4 tiene *timeout* explícito, leído de la configuración validada al arrancar. | PostgreSQL ≤ 2 s por consulta (5 s para la transacción de indexación de una versión); Redis ≤ 0,5 s por operación; *embeddings* 30 s por lote; juez 180 s por llamada (3 veces el p95 de NFR3.1 y menos que el plazo base de 300 s); `count_tokens` 5 s; conexión HTTP 2 s. | Nivel 0 (configuración) y nivel 1 |
| NFR10.15 | Las colas entregan al menos una vez y sin efectos dobles (BR5.7). | `XACK` solo después de publicar C3 (evaluador) o de confirmar la transacción (ingesta e indexador). Un mensaje pendiente se reclama con `XAUTOCLAIM` tras 240 s de inactividad (más que el peor caso de un turno: *embeddings* + juez ≈ 213 s); a la 3.ª entrega sin confirmar va a `<cola>:failed` y el turno pasa a `error` con `turn.error.system`. Prueba de nivel 1 que mata al evaluador a mitad (E8): un solo resultado por intento. | Nivel 1 |
| NFR10.16 | Cada fallo del juez tiene su tratamiento. | *Timeout* (180 s) → `turn.error.timeout` sin reintento automático (BR8.2); salida inválida → `turn.error.invalid_output` sin reintento automático (contract-design P3); conexión rechazada o respuesta 5xx → no se confirma el mensaje y vuelve por `XAUTOCLAIM` (recuperable); *prompt* que no cabe → `turn.error.system` sin llamar al juez (NFR3.12). Una prueba de nivel 0 por caso con el *fake* del juez. | Nivel 0 |
| NFR10.17 | Ningún turno queda «en curso» para siempre. | La revisión de plazos (NFR3.6) cubre turnos huérfanos (mensaje perdido, Redis reiniciado); todo turno `queued` o `processing` termina `evaluated` o `error` antes de `deadline_at + 30 s`. | Nivel 1 con reloj controlado |
| NFR10.18 | La indexación es todo o nada y no se repite a medias (BR2.2). | Un fallo de *embeddings* en el lote k > 1 deja la versión en `error` con 0 pasajes (E4); una reentrega de una versión `ready` o `error` se confirma sin efectos. | Nivel 1 |
| NFR10.19 | `/readyz` refleja lo que U4 necesita (C16). | `semantic-agent`: `503` si falta o es inválido el umbral (BR6.1, E21), si el SHA-256 del *prompt* no coincide (E22), o si PostgreSQL (rol de solo lectura), Redis, `model-judge` o `model-embeddings` no responden. `session-api` y su trabajador: `503` si falta la configuración de U4, o si PostgreSQL, Redis o `model-embeddings` no responden. Configuración inválida → el proceso termina con código distinto de 0. | Nivel 1 |
| NFR10.20 | La consola sobrevive a cortes breves. | Si un sondeo falla (red o 5xx), M4 conserva lo que ya mostraba y reintenta cada 2 s, 4 s, 8 s… hasta 30 s; al primer sondeo correcto vuelve al intervalo de NFR3.7 y aplica los cambios desde su último `cursor` sin perder ninguno. | Vitest con un servidor *fake* que falla 3 veces |

## 3. Determinismo y umbral (calidad de la IA)

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR4.1 | Umbral inicial y calibración (P3). | Valor inicial provisional **0,80** (`VERIDICUS_SIMILARITY_THRESHOLD`, rango válido 0,50–0,99, extremos incluidos). En nivel 2 se barre de 0,70 a 0,95 en pasos de 0,01 sobre el Golden Dataset; un valor «cumple» si da ≥ 5 de 6 discrepancias detectadas, ≤ 1 alerta en total sobre las 4 transcripciones alineadas y 0 alertas, 0 preguntas y 1 paquete en el caso de Hecho No Documentado. Se elige el punto medio del tramo continuo más largo de valores que cumplen (empate: el tramo de valores más altos, más conservador para AUTONOMIA-05). El valor entra por PR con el reporte JSON del barrido; si ningún valor cumple, el umbral no cambia y el reporte queda como hallazgo para el humano. | Nivel 2 |
| NFR4.2 | La evaluación es repetible. | Temperatura 0, semilla fija (`VERIDICUS_JUDGE_SEED`) y un solo turno a la vez en el servidor del juez. Dos corridas de nivel 2 seguidas con el mismo modelo, *prompt* y umbral producen las mismas calificaciones, los mismos `passage_ids` y el mismo conjunto de alertas; la CoT puede diferir solo si el reporte lo declara. | Nivel 2 |
| NFR4.4 | La salida del juez cumple el formato. | 0 % de error de formato JSON sobre el Golden Dataset (todas las salidas validan contra C6 con BR8.1). | Nivel 2 |
| NFR4.5 | El orden de los pasajes es un parámetro del *prompt*. | El constructor del *prompt* acepta el orden de los pasajes (directo o invertido), para que el arnés de nivel 2 aplique la permutación al 100 % de las consultas *offline* y mida consistencia > 65 % al invertir el orden; la permutación en línea es de U8. | Nivel 0 (parámetro) y nivel 2 (métrica) |
| NFR6.1 | La CoT es legible para el analista. | Las instrucciones piden, por afirmación: qué dice la afirmación, qué dice el pasaje citado y por qué difieren o coinciden, en español y en 20 a 80 palabras. El reporte de nivel 2 registra la distribución de longitudes; la calificación Likert ≥ 4,5 de dos evaluadores es manual antes de la sustentación (NFR6). | Nivel 2 y manual |

## 4. Recuperación

| Falla | Qué se pierde | Cómo se recupera |
|---|---|---|
| Reinicio de `semantic-agent` a mitad de un turno | Nada | El mensaje vuelve por `XAUTOCLAIM` tras 240 s (NFR10.15) |
| Reinicio del trabajador de `session-api` | Nada | C3 y C4 pendientes se reclaman; la revisión de plazos se reanuda |
| Caída del servidor del juez | Nada; los turnos esperan | Vuelven por reentrega o terminan por plazo con `turn.error.timeout`; el analista usa «Reintentar evaluación» |
| Redis pierde hasta 1 s de mensajes (AOF `everysec` de U2) | Mensajes de ese segundo | Los turnos afectados terminan por plazo (NFR10.17) y se reintentan a mano |
| Pérdida de la base | Según el respaldo de CloudNativePG | Lo fija Infrastructure Design |

## 5. Degradación

Si el juez no está disponible, la consola sigue respondiendo (NFR3.9): se pueden cargar escenarios,
crear sesiones, enviar turnos y revisar alertas ya emitidas; los turnos nuevos esperan en cola hasta su
plazo. Si el servidor de *embeddings* no está disponible, no se indexan escenarios ni se evalúan
turnos, y `/readyz` de los servicios afectados responde `503`.
