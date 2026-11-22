# Diseño de observabilidad — U10 anonymizer

**Revisión 2 (2026-11-22): segunda pasada por el cambio 01, la adenda 02 y el NFR Requirements revisión
2.** Sustituye a la revisión 1 del 2026-10-03. Salen las métricas y los campos de `embed`, de la lista del
escenario y de las cabeceras `X-Veridicus-*`. Las métricas pasan a `contracts/metrics/anonymizer.v1.yaml`
con la etiqueta `error_code` (NFRD-U10-02). Cierra el hallazgo R-08 de la revisión 1 de esta etapa (§1).

**Insumos.** `nfr-requirements/observability-requirements.md` (observability-requirements: NFR15.1–NFR15.4),
`security-requirements.md` (security-requirements: NFR10.3, NFR11.1), `performance-requirements.md`
(performance-requirements: NFR3.6), `reliability-requirements.md` (reliability-requirements),
`scalability-requirements.md` (scalability-requirements) y `tech-stack-decisions.md` (tech-stack-decisions)
de esta unidad; F1, F7, F8, §3.1 y FD-U10-14 de `functional-design/functional-spec.md` (functional-spec);
C15, C16 y C21 de `inception/contract-design/contract-summary.md` (contract-summary); NFRD-U1-05 de U1;
NFR15.2 de U2. Sin Alertmanager, Loki ni notificaciones en el MVP (`project.md`).

NFR15 es SHOULD. Lo que protege AUTONOMIA-04 (que métricas y logs no lleven texto) es MUST por NFR10.3.

## 1. Logs estructurados con lista blanca tipada (NFR10.3, NFR15.2; cierra R-08)

- JSON por línea en `stdout`, con el formateador de lista blanca de `libs/`. U10 registra su perfil de
  campos, y **cada campo declara su tipo**: enum (con sus valores), entero, decimal, UUID o marca de hora.
  Un campo de cadena libre no se puede declarar, y un valor que no cumple su tipo se descarta y cuenta en
  `log_fields_dropped`. Prueba: un campo nuevo de tipo cadena libre hace fallar el registro del perfil.
- **Evento `anonymizer.call`**, uno por `generate`, con: `timestamp`, `level`, `service`, `event`, `run_id`
  (UUID; solo en el proxy), `profile_name` (patrón de C21), `role`, `destination_slot`, `provider`, `model`
  (enum de la tabla de capacidades), `outcome`, `code`, `replacements` (enteros por categoría),
  `altered_markers_count`, `input_tokens`, `output_tokens`, `masking_ms` y `upstream_ms`.
- **Eventos `anonymizer.startup` y `anonymizer.startup_failed`** con los `schema_version` y SHA-256 de los
  datos y del NER, la versión de la API de cada adaptador, y, si falla, el nombre del *check* y del ajuste.
- **Excepciones.** Se registran con su tipo y su `code`, nunca con su mensaje, su traza con variables
  locales ni el cuerpo del proveedor. `logging.raiseExceptions = False` y el registro raíz no tiene otros
  manejadores.
- **Prueba del *canary*** (E6, E34; niveles 0 y 1). Una cadena centinela sembrada como nombre en el
  testimonio, como valor de clave, en la respuesta grabada y en el cuerpo de un error del proveedor aparece
  **0 veces** en logs, métricas, archivos y textos de excepción, en el éxito y en cada rama de error.

## 2. Métricas de Prometheus sin datos (NFR15.1; NFRD-U10-02)

`/metrics` en el puerto interno 9090, con `prometheus-client` y un registro propio, sin las métricas de
proceso por defecto que no se usan. En la CLI no se publican métricas: los mismos datos van en el
`ModelCall` y en el reporte de U11.

## 3. Catálogo de métricas para `contracts/metrics/anonymizer.v1.yaml` (por PR de U1)

```yaml
metrics:
  - name: veridicus_anonymizer_requests_total
    type: counter
    labels: [outcome, error_code, provider, role, slot]
  - name: veridicus_anonymizer_masking_seconds
    type: histogram
    labels: [outcome]
    buckets: [0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 15, 20, 30, 45]
  - name: veridicus_anonymizer_upstream_seconds
    type: histogram
    labels: [provider, role]
    buckets: [0.5, 1, 2.5, 5, 10, 20, 40, 80, 160, 320]
  - name: veridicus_anonymizer_replacements_total
    type: counter
    labels: [category]
  - name: veridicus_anonymizer_altered_markers_total
    type: counter
    labels: [provider, role]
  - name: veridicus_anonymizer_input_tokens_total
    type: counter
    labels: [provider, role]
  - name: veridicus_anonymizer_output_tokens_total
    type: counter
    labels: [provider, role]
  - name: veridicus_anonymizer_inflight
    type: gauge
    labels: []
  - name: veridicus_anonymizer_ready
    type: gauge
    labels: []
```

**Valores de las etiquetas** (todas enum, de la lista cerrada de U1): `outcome` ∈ {`restored`,
`failed_after_send`, `failed_closed`, `rejected`}, `error_code` ∈ {`ok`, `limits.exceeded`,
`anonymizer.profile_mismatch`, `anonymizer.destination_rejected`, `analysis.content_blocked`,
`analysis.provider`, `analysis.invalid_output`, `analysis.anonymizer_unavailable`, `analysis.timeout`},
`provider` ∈ {`anthropic`, `google`, `openai`}, `role` ∈ {`judge`, `verifier`, `verifier_permuted`},
`slot` ∈ {`primary`, `fallback`} y `category` ∈ {`PERSONA`, `LUGAR`, `EXPEDIENTE`, `IDENTIFICADOR`,
`ENTIDAD`}. `outcome: rejected` cuenta los `409`, `413` y `422` que el proxy da antes de `generate`; en esas
series `provider`, `role` y `slot` toman el valor resuelto si lo hay, o no se emiten. Nunca hay etiquetas
`run_id`, `model` ni `profile_name`. Los histogramas suman 20 y 45 s para ver la meta de 20 s y el
presupuesto de 40,5 s.

**Prueba.** Tras el éxito y cada rama de error, una prueba recorre todas las series: cada valor está en
su enum, la cardinalidad total es ≤ 600 series y el *canary* aparece 0 veces.

## 4. Salud (NFR15.3)

`/readyz` devuelve 503 con la lista de *checks* que fallan, por nombre (`data_files`, `ner`,
`capabilities`, `profiles`, `api_keys`, `limits`, `settings`, `warming`) y sin valores.
`veridicus_anonymizer_ready` vale 1 solo cuando `/readyz` daría 200. Ninguna abre conexiones hacia fuera
(`reliability-design.md` §4).

## 5. Correlación y trazas

- La correlación es el `run_id` del cuerpo de C21, que va **solo** al log del proxy y nunca al proveedor
  (NFR1.8). `X-Request-Id` de entrada se ignora.
- Sin trazas distribuidas en el MVP: con una llamada por corrida a la vez, `run_id`, `masking_ms` y
  `upstream_ms` bastan para separar el tiempo propio del del proveedor (NFR3.6).

## 6. Panel de Grafana (NFR15.4)

`services/anonymizer-proxy/observability/grafana-dashboard.json`, versionado. Paneles: llamadas por
`outcome` y `provider`; p95 de `masking_seconds` con líneas en 20 s y 40,5 s; p95 de `upstream_seconds`
por proveedor; reemplazos por categoría; marcas alteradas; `inflight` frente al tope; *tokens* por
proveedor; y `ready`. Una prueba de nivel 0 valida el JSON y comprueba que solo consulta métricas
`veridicus_anonymizer_*` del catálogo. U2 lo copia a su chart con el mismo SHA-256 y añade el raspado del
puerto 9090 (NFRD-U10-09). Sin alertas que notifiquen.

## 7. Indicadores de servicio

| Indicador | Cálculo | Objetivo informativo (sin alerta en el MVP) |
|---|---|---|
| Fugas | Prueba de nivel 1 de NFR1.3 | 0, bloqueante en CI |
| Llamadas cerradas por error propio | `requests_total{outcome="failed_closed"}` / total, por día | < 1 %; cada caso se mira |
| p95 de seudonimización con 250 000 caracteres | `masking_seconds` | ≤ 20 s |
| Saturación | `requests_total{error_code="analysis.anonymizer_unavailable"}` durante la prueba de NFR8 | 0 |
| Marcas alteradas | `altered_markers_total` / llamadas restauradas | Se informa en el nivel 2 de B11 (NFR4.1) |
