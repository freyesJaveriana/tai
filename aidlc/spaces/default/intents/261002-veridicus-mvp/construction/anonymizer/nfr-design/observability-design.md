# Diseño de observabilidad — U10 anonymizer

**Insumos.** `nfr-requirements/performance-requirements.md` (performance-requirements),
`nfr-requirements/security-requirements.md` (security-requirements),
`nfr-requirements/scalability-requirements.md` (scalability-requirements),
`nfr-requirements/reliability-requirements.md` (reliability-requirements),
`nfr-requirements/observability-requirements.md` (observability-requirements) y
`nfr-requirements/tech-stack-decisions.md` (tech-stack-decisions) de esta unidad; flujos F1–F3 de
`functional-design/functional-spec.md` (functional-spec); C15 y C16 de
`inception/contract-design/contract-summary.md` (contract-summary); respuestas P1 = A y P2 = A de
`nfr-design-questions.md`; formateador de logs con lista blanca de U3 y panel de U4.

Con el proxy apagado no hay nada que observar en el clúster; todo esto se prueba en niveles 0 y 1 en
cada PR.

## 1. Logs (NFR15.2, NFR15.3, NFR10.3)

- Se usa el formateador JSON único de `libs/` (U3), que descarta todo campo fuera de su lista blanca.
  U10 registra su perfil de campos: `request_id`, `operation`, `replacements` (objeto con `PERSONA`,
  `LUGAR`, `EXPEDIENTE` y su número), `result`, `code`, `reason`, `upstream_status`, `unknown_markers`,
  `masking_ms`, `upstream_ms`.
- **Una línea por llamada**, emitida en el `finally` de `MaskedCall.run`, después de borrar la tabla.
- `reason` es un valor de enum que dice en qué rama terminó cerrada la llamada: `rules`, `proper_nouns`,
  `detector`, `masking_timeout`, `marker_in_input`, `table_conflict`, `payload_shape`,
  `outbound_check`, `unexpected`. Nunca texto.
- Niveles: `failed_closed` y `rejected` → `WARNING` con `code` y `reason`; `failed` → `WARNING` con
  `upstream_status`; arranque fallido → `ERROR` con el nombre del ajuste.
- Las excepciones se registran solo con su tipo y su `code`; nunca su mensaje, el cuerpo del destino ni
  la URL con parámetros.
- **Correlación.** `AnonymizerGateway` envía `X-Request-Id` (un UUID por llamada) y registra en su
  propio log el par `turn_id` y `request_id`; el proxy registra el `request_id` y **no** lo reenvía al
  destino (`security-design.md` §6).

**Verificación (nivel 1, *canary*).** Una cadena centinela sembrada en el testimonio, en la lista de
nombres, en la respuesta del destino *fake*, en el cuerpo de un 500 del destino y en una excepción
provocada en cada `reason`: 0 apariciones en todos los logs capturados. Una segunda prueba sigue una
llamada por los logs del cliente y del proxy con el mismo `request_id`.

## 2. Métricas (NFR15.1)

Expuestas en `/metrics` del puerto interno, solo accesible desde Prometheus (`NetworkPolicy` de
entrada, `security-design.md` §5).

| Métrica | Tipo | Etiquetas |
|---|---|---|
| `veridicus_anonymizer_requests_total` | counter | `operation`, `result` (`restored`, `failed`, `failed_closed`, `rejected`, `busy`) |
| `veridicus_anonymizer_failed_closed_total` | counter | `reason` (enum de §1) |
| `veridicus_anonymizer_replacements_total` | counter | `category` |
| `veridicus_anonymizer_masking_seconds` | histogram (cubetas de NFR15.1) | `operation` |
| `veridicus_anonymizer_upstream_seconds` | histogram (cubetas de NFR15.1) | `operation`, `result` (`ok`, `timeout`, `error`) |
| `veridicus_anonymizer_unknown_markers_total` | counter | — |
| `veridicus_anonymizer_rules_info` | gauge = 1 | `schema_version` |

Las etiquetas solo llevan valores de enum o la versión de las reglas; nunca `request_id`, sesión,
texto ni host del proveedor. **Verificación (nivel 0).** Tras las pruebas de *canary*, `/metrics`
contiene 0 apariciones de la cadena centinela, y una prueba de cardinalidad comprueba que cada etiqueta
toma solo valores de su enum.

## 3. Indicadores, alertas y panel

| SLI | Cálculo | Objetivo (solo con el proxy habilitado) |
|---|---|---|
| Sobrecosto del enmascarado | p95 de `veridicus_anonymizer_masking_seconds{operation="judge"}` | ≤ 0,25 s |
| Cierres por falla | `failed_closed_total` por `reason` | 0 en una corrida de nivel 2; cada caso es un hallazgo de las reglas |
| Comprobación final | `failed_closed_total{reason="outbound_check"}` | 0: si es mayor, el enmascarado tiene un defecto aunque nada haya salido |
| Saturación | `requests_total{result="busy"}` | 0 en la corrida de NFR8.4 |

- **Alertas informativas** (ninguna despierta a nadie): más de 0 `failed_closed` en 15 minutos; más de
  0 `outbound_check` en 15 minutos; más de 3 marcadores desconocidos en 15 minutos. Ninguna regla
  cambia configuración ni apaga el proxy: eso es un PR (AUTONOMIA-01).
- **Panel (SHOULD, lo instala U2).** Fila «Anonimizador» en el panel de U4: llamadas por resultado,
  cierres por `reason`, p95 de enmascarado y de destino, `busy`; visible solo con el proxy habilitado.
- **Trazas distribuidas.** No en el MVP; basta la correlación por `request_id`.

## 4. Precisiones a artefactos ya aprobados

| Artefacto | Qué precisa | Origen |
|---|---|---|
| `anonymizer/nfr-requirements/observability-requirements.md` (NFR15.1, NFR15.2) | Nuevo campo de log `reason` y métrica `veridicus_anonymizer_failed_closed_total{reason}`, para distinguir la comprobación final de P2 = A | P2 = A |
| `contract-design/contract-summary.md` (C15) | Se suma esa métrica a las de NFR15.1 en el PR de U1 que ya añade las `veridicus_anonymizer_*` | P2 = A |
| `identity-access/nfr-design/observability-design.md` (formateador de U3) | Perfil de campos de U10 en la lista blanca | NFR15.2 |
