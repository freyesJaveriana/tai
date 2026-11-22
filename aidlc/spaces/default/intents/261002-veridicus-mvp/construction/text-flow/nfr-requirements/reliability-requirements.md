# Requisitos de fiabilidad — U4 text-flow

**Revisión 2 (2026-11-22).** Segunda pasada por el cambio 01 (DT27), la adenda 02 y el Functional Design
revisión 2 de U4. Sustituye a la revisión 1 del 2026-10-03.

**IDs.** Los requisitos que siguen conservan su número y lo retirado queda «Retirado». Los nuevos son
NFR10.21–NFR10.23 y NFR4.6. Los de calidad de la IA (NFR4.1–NFR4.5 y NFR6.1) pasan a U11, que es dueña
del *prompt*, del juez y del verificador.

**Insumos.**
- `functional-design/functional-spec.md` (functional-spec): flujos F5–F8, F11–F15, la máquina de
  estados de la corrida, §8 «Errores y bordes» y los escenarios E10–E55.
- `functional-design/rules.md` (rules): reglas BR5.6–BR5.9, BR8.1–BR8.6, BR11.1–BR11.4, BR15.1–BR15.9 y
  BR16.1–BR16.7.
- `inception/requirements-analysis/requirements.md` (requirements): NFR4, NFR6, NFR8 y NFR10.
- `inception/contract-design/contract-summary.md` (contract-summary): C2, C3, C16, C17, C21 y C25, con
  CD-06.
- Respuestas S1 = A, P6 = A y P7 = A de `nfr-requirements-questions.md`.

## 1. Objetivos

El MVP no tiene SLA: corre en la máquina de desarrollo y en la demostración.

| ID | Estado | Objetivo | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR8.5 | cambia | El flujo de texto termina de punta a punta (NFR8). | ≥ 98 % de 50 sesiones sintéticas con `comercial-piloto`, en tandas de 3, terminan su corrida incremental y su modo final sin corridas en `error` ni `OOMKilled`; como máximo falla 1 sesión (NFR-U4-11) | Corrida de carga a demanda (`scalability-requirements.md` §3) |
| NFR8.6 | se mantiene | La prueba de humo no falla por U4. | 0 fallos atribuibles a U4 en cada corrida de `scripts/smoke.sh` tras un despliegue (NFR3.10) | Nivel 3 |

## 2. Requisitos

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR10.14 | cambia | Toda E/S propia de U4 tiene un *timeout* explícito, leído de la configuración validada al arrancar. | PostgreSQL ≤ 2 s por consulta y 5 s para la transacción de ingesta; Redis ≤ 0,5 s por operación; `check_ready()` de C21 2 s; conexión HTTP 2 s. Las llamadas a modelos usan `model_call_timeout_s` de la `effective_config` (U11), que debe ser ≥ 270 s en todo despliegue con un perfil comercial (NFR-U4-02) | Nivel 0 (configuración) y nivel 1 |
| NFR10.15 | cambia | Las colas entregan al menos una vez y sin efectos dobles (BR5.7). | `XACK` solo después de publicar C3 (trabajador) o de confirmar la transacción (ingesta). El trabajador renueva cada 15 s el reclamo de su mensaje; un mensaje sin renovar se reclama con `XAUTOCLAIM` tras `claim_idle_ms` = 60 000 (NFR-U4-06). A la entrega `run_max_deliveries` = 3 sin confirmar, el mensaje va a `<cola>:failed` y la corrida pasa a `error` con `analysis.system`. Una prueba de nivel 1 mata al trabajador a mitad de la corrida: queda un solo resultado por intento | Nivel 1 |
| NFR10.16 | cambia | Cada fallo de la corrida tiene su tratamiento, sin reintento automático. | `estado: error` de C17 deja la corrida en `error` con el mismo `code` y 0 sugerencias (BR11.3). La salida que no pasa C6 en la ingesta queda en `analysis.invalid_output`. El `503` del proxy queda en `analysis.anonymizer_unavailable` (BR16.7). La cancelación deja la corrida en `cancelled`. El reintento es una acción del analista, que crea `attempt + 1` (BR5.9). Los reintentos de transporte del juez son de U11 (NFR10 de U11). Hay una prueba de nivel 0 por caso con el *fake* de C17 | Nivel 0 |
| NFR10.17 | cambia | Ninguna corrida queda «en curso» para siempre. | El supervisor (NFR3.6) cubre las corridas huérfanas (mensaje perdido o Redis reiniciado): toda corrida en `queued` o `processing` termina en `completed`, `error` o `cancelled` antes de `deadline_at + 30 s`. Una corrida en espera (NFR3.13) se libera o termina según FD-U9-07, y una prueba comprueba que ninguna queda en espera sin fin | Nivel 1 con reloj controlado |
| NFR10.18 | Retirado | La indexación es todo o nada. | Sale el escenario (cambio 01) | — |
| NFR10.19 | cambia | `/readyz` refleja lo que U4 necesita (C16). | `semantic-agent` responde `503` en estos casos: el archivo de perfiles o `contracts/limits.v1.yaml` faltan o no son válidos; Redis no responde; un perfil con destino externo tiene el proxy caído (`check_ready()` falla, NFR1.4); o U11 informa que un servidor local de un perfil habilitado no responde. `session-api` y su trabajador responden `503` si falta su configuración o si PostgreSQL o Redis no responden. Una configuración inválida termina el proceso con un código distinto de 0 (NFR10.25) | Nivel 1 |
| NFR10.20 | cambia | La consola sobrevive a cortes breves. | Si un sondeo falla (red o 5xx), M4 conserva lo que ya mostraba y reintenta tras 2 s, 4 s, 8 s… hasta 30 s. Al primer sondeo correcto vuelve al intervalo de NFR3.7 y aplica los cambios desde su último `cursor` sin perder ninguno | Vitest con un servidor *fake* que falla 3 veces |
| NFR10.21 | nuevo | La cancelación llega al trabajador antes de la siguiente llamada (CD-06). | Pausar, terminar, retirar el consentimiento, bloquear o vencer el plazo escribe la clave `veridicus:run-cancelled:{run_id}` antes de responder, con TTL igual al plazo restante más `cancel_key_margin_s` = 120. El trabajador la consulta antes de empezar y antes de cada llamada (BR15.4). Si Redis pierde la clave, el plazo detiene la corrida igual (E52, NFR1.6) | Nivel 1 |
| NFR10.22 | nuevo | La ingesta es idempotente. | Un `RunResult` repetido para el mismo (`run_id`, `attempt`) se confirma sin efectos. Un `RunStarted` o un `RunResult` que llega cuando la corrida ya es terminal se confirma sin cambiar su estado, salvo el registro del incidente (NFR-U4-09). Hay prueba de nivel 1 con dos consumidores de C3 | Nivel 1 |
| NFR10.23 | nuevo | Un límite de C25 se comprueba antes de encolar, nunca a mitad de la corrida. | Turno, número de turnos y caracteres se validan al recibir el turno (NFR10.1). El trabajador no recorta ni parte la transcripción: lo que U11 no puede procesar vuelve como `estado: error` con su `code`. Hay una prueba de nivel 1 con la transcripción máxima de P6 = A y P7 = A que termina `completed` con el *fake* | Nivel 1 |

## 3. Calidad de la IA

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR4.1 | Retirado | Umbral y calibración | Sale el umbral (cambio 01) | — |
| NFR4.2 | Retirado | Repetibilidad | Pasa a U11 (acuerdo entre 3 corridas) | — |
| NFR4.4 | Retirado | Formato JSON | Pasa a U11; U4 conserva la segunda línea de NFR10.4 | — |
| NFR4.5 | Retirado | Permutación | Pasa a U11 | — |
| NFR4.6 | nuevo | El trabajador y la CLI dan el mismo resultado (BR15.9), y un error nunca deja sugerencias. | Con el mismo `AnalyzerInput`, perfil y *fake* de modelos, la salida de `analyze` vía `AnalysisWorker` y vía la CLI de U11 es idéntica campo a campo. Por eso el nivel 2 de U11 vale para el trabajador. Si la salida es `estado: error`, quedan 0 sugerencias y 0 descartes visibles | Nivel 0 y nivel 1 |
| NFR6.1 | Retirado | Legibilidad de la CoT | Pasa a U11 (`observaciones`) | — |

## 4. Recuperación

| Falla | Qué se pierde | Cómo se recupera |
|---|---|---|
| Reinicio de `semantic-agent` a mitad de una corrida | Las llamadas de ese intento | El mensaje vuelve por `XAUTOCLAIM` tras 60 s (NFR10.15). Las llamadas ya hechas quedan contadas en su intento |
| Reinicio del trabajador de `session-api` | Nada | C3 pendiente se reclama; el supervisor y las liberaciones se reanudan |
| Caída de un servidor local o del proveedor comercial | Nada; la corrida espera o falla | U11 aplica sus reintentos. Si no basta, la corrida termina en `error` con su `code` o por plazo, y el analista reintenta |
| Caída de `anonymizer-proxy` | Nada; no sale ninguna llamada | `/readyz` de `semantic-agent` en `503`. La corrida termina en `analysis.anonymizer_unavailable` |
| Redis pierde hasta 1 s de mensajes (AOF `everysec` de U2) | Mensajes y claves de ese segundo | Las corridas afectadas terminan por plazo (NFR10.17) y se reintentan a mano; la cancelación la cubre el plazo (NFR10.21) |
| Pérdida de la base | Según el respaldo de CloudNativePG | Lo fija Infrastructure Design |

## 5. Degradación

- **Sin trabajador o sin modelos.** La consola sigue respondiendo (NFR3.9): se pueden crear sesiones,
  enviar turnos y revisar sugerencias ya emitidas. Las corridas nuevas esperan en cola hasta su plazo.
- **Sin anonimizador.** Solo pueden analizar las sesiones con perfiles locales. Las de perfil comercial
  terminan en `analysis.anonymizer_unavailable` y nunca salen sin seudonimizar (AUTONOMIA-04).
