# Ronda 1 — U11-T04

**Revisor:** `revisor` (opus), sobre `3fdf3b3` (base `fa06b71`). Fecha: 2026-11-26.

VEREDICTO: NO-VERDE

Los siete criterios pasan y los 11 mutantes mueren. Queda en pie un NARANJA: la huella del *prompt* se calcula sobre una lectura, pero cada llamada vuelve a leer el archivo.

## Criterios (verificados por el revisor)

| # | Resultado |
|---|---|
| CA-1 | 233 pasan; `analyze.py` 20/20 ramas, `preflight.py` 20/20, `deadline.py` 6/6, `api.py` 100 %; `test_run_perf` 0,24 s (umbral 6 s) |
| CA-2 | Contra `c7e6542`, solo cambia la línea 109 (P-T04-1); la 108 y el control negativo siguen iguales |
| CA-3 | 6 fallos (CLI, `NotImplementedError` de `run`), 105 pasan, 0 `ERROR` |
| CA-4 | Escáner: 195 pruebas; `scan.py` 26/26 y `notice.py` 6/6 |
| CA-5 | Dominio 161 y *gateway* 31 pruebas, las dos al 100 % |
| CA-6 | mypy estricto, ruff y formato con código 0 en los dos paquetes |
| CA-7 | `0 apariciones` ×3; ningún `sk-` nuevo fuera del canario; el plan aprobado no tiene cambio neto |

## Sondas adversariales

- **Fallo del modelo en cada papel:** 27 casos (Timeout, ProviderError, AnonymizerUnavailable, InvalidOutput, ContentBlocked, JSON inválido, campo extra, `confirma` como cadena). Todos dan `estado: error` sin hallazgos ni descartes y con C6 válido. Un `RuntimeError` del *gateway* guionado se propaga (BR7.1); con el *gateway* real se convierte en `AnonymizerUnavailable`.
- **Orden de llamadas:** por primer turno citado, la directa antes de su permutada, y la permutada se llama aunque la directa diga que no. Con `permutation: false` hay k llamadas.
- **Plazo:** `min(300, restante)`; si se pasa el plazo, `tiempo_agotado` sin otra llamada; la cancelación lanza `CancelledError` después de la primera llamada.
- **Mutantes M1 a M10 y K-91:** mueren todos.
- **Decisiones del codificador:** el *fixture* autouse se acepta, los rechazos del *preflight* fallan cerrado y el `Literal` ampliado es coherente con C6.

## Hallazgos

### F-01 · NARANJA · `application/analyze.py:293`, `application/messages.py:62,129`

**Qué pasa:** la huella del *prompt* no cubre los bytes que salen. `_prompt_matches` lee el *prompt* una vez, y después cada `build_messages` lo vuelve a leer sin comparar nada.

**Cómo se probó:** con una lectura alterada desde la segunda, la corrida da `ok`, el `prompt_sha256` coincide con la referencia y el `system` del juez lleva el texto inyectado (BR3.1, K-88).

**Corrección:**
- Leer `prompt_bytes()` una vez por corrida.
- Sacar de esos bytes la huella y el `system` de cada llamada.
- Añadir una prueba con una lectura que cambie después de la primera.

### A-01 · AMARILLO · `domain/output.py:141`

**Qué pasa:** ante una huella que no coincide, la salida informa la de la configuración y no la de los bytes leídos.

**Corrección:** anotarlo como precisión, o informar la de los bytes.

### A-02 · AMARILLO · `application/preflight.py:83-84`

**Qué pasa:** el rechazo de un `n` repetido no está en BR1.1.

**Corrección:** anotarlo en la tabla de precisiones de la unidad.

### A-03 · AMARILLO · `docs/loop/bitacoras/U11-T04.md:23,59`

**Qué pasa:** la bitácora dice que se marcaron casillas del plan, pero `3fdf3b3` restauró el plan aprobado.

## Candidatas

- **Literales invisibles:** en `tests/domain/test_filter.py:115` y en `libs/integrity_policy/tests/test_invisible_and_cache.py:110`.
- **Límites de turnos:** `EffectiveConfig.limits` no los trae, así que la biblioteca no ve una bajada desde el entorno. Se decide en T05 o en B11b.
- **U10:** marcar `[PERSONA_n]` sin tratamiento.
- **U10:** `TEST` y `T2` enmascarados como `[ENTIDAD_n]`.
