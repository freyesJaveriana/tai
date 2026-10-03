# Requisitos de observabilidad — U10 anonymizer

**Insumos.** Flujos F1–F3 de `functional-design/functional-spec.md` (functional-spec); regla BR2.3 de
`functional-design/rules.md` (rules); NFR10 y NFR15 de
`inception/requirements-analysis/requirements.md` (requirements); C15 y C16 de
`inception/contract-design/contract-summary.md` (contract-summary); respuesta P1 = A de
`nfr-requirements-questions.md`. Con el proxy apagado (por defecto) no hay nada que observar; estos
requisitos se prueban en niveles 0 y 1 y rigen cuando se habilita.

## 1. Logs

| ID | Requisito | Criterio medible |
|---|---|---|
| NFR15.2 | Una línea por llamada, solo con identificadores y conteos. | JSON en una línea con los campos permitidos de NFR10.3 (`request_id`, `operation`, `replacements` por categoría, `result`, `code`, `upstream_status`, `unknown_markers`, `masking_ms`, `upstream_ms`); `result` toma los valores de la máquina de estados (`restored`, `failed`, `failed_closed`), `rejected` (límites o petición inválida) o `busy`. Nunca texto, nombres, marcadores con su valor, tabla, lista de nombres, URL con parámetros ni cuerpo de la respuesta del destino. Prueba de nivel 1 con *canary* (NFR10.3). |
| NFR15.3 | Los fallos se distinguen por `code` y nivel. | `failed_closed` y `rejected` dejan `WARNING` con su `code`; `failed` (destino) deja `WARNING` con `upstream_status`; un arranque fallido deja `ERROR` con el nombre del ajuste. El `request_id` lo propaga el cliente (cabecera `X-Request-Id`) para correlacionar con el `turn_id` del log de U4 sin pasar texto. Prueba de nivel 1 que sigue una llamada por los logs del cliente y del proxy. |

## 2. Métricas (Prometheus, en `/metrics` del puerto interno)

| ID | Métrica | Tipo | Etiquetas |
|---|---|---|---|
| NFR15.1 | `veridicus_anonymizer_requests_total` | counter | `operation` (`judge`, `embed`), `result` (`restored`, `failed`, `failed_closed`, `rejected`, `busy`) |
| NFR15.1 | `veridicus_anonymizer_replacements_total` | counter | `category` (`PERSONA`, `LUGAR`, `EXPEDIENTE`) |
| NFR15.1 | `veridicus_anonymizer_masking_seconds` | histogram (cubetas 0,005, 0,01, 0,025, 0,05, 0,1, 0,25, 0,5, 1, 2) | `operation` |
| NFR15.1 | `veridicus_anonymizer_upstream_seconds` | histogram (cubetas 0,5, 1, 2, 5, 10, 20, 30, 60, 120, 170) | `operation`, `result` (`ok`, `timeout`, `error`) |
| NFR15.1 | `veridicus_anonymizer_unknown_markers_total` | counter | ninguna |
| NFR15.1 | `veridicus_anonymizer_rules_info` | gauge (= 1) | `schema_version` |

Las etiquetas solo llevan valores de enum o la versión de las reglas; nunca identificadores de sesión,
texto ni el host del proveedor. Estas métricas se añaden a C15 por un PR de U1 (precisión en
`security-requirements.md` §6). Prueba de nivel 0 que lee `/metrics` tras las pruebas de *canary* y
encuentra 0 apariciones de la cadena centinela.

## 3. Indicadores y alertas

| SLI | Cálculo | Objetivo (solo con el proxy habilitado) |
|---|---|---|
| Sobrecosto del enmascarado | p95 de `veridicus_anonymizer_masking_seconds{operation="judge"}` | ≤ 0,25 s (NFR3.3) |
| Llamadas cerradas por falla | `requests_total{result="failed_closed"}` / total | Se revisa cada caso; > 0 en una corrida de nivel 2 es un hallazgo de las reglas |
| Saturación | `requests_total{result="busy"}` | 0 en la corrida de NFR8.4 |

- **Panel (SHOULD, lo instala U2).** Una fila «Anonimizador» en el panel de Grafana de U4 con las
  métricas anteriores, visible solo si el proxy está habilitado.
- **Alertas.** Ninguna despierta a alguien en el MVP. Una regla informativa: más de 0
  `failed_closed` en 15 minutos o más de 3 `veridicus_anonymizer_unknown_markers_total` en 15 minutos
  (el destino inventa marcadores o cambió el formato). Ninguna regla cambia la configuración ni apaga el
  proxy: eso es un PR (AUTONOMIA-01).
- **Trazas distribuidas.** No en el MVP: basta `request_id` correlacionado con `turn_id` (NFR15.3).
