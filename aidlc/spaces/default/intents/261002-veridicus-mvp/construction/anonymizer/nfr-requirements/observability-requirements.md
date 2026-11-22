# Requisitos de observabilidad — U10 anonymizer

**Revisión 2 (2026-11-22): segunda pasada por el cambio 01, la adenda 02 y el Functional Design
revisión 2.** Sustituye a la revisión 1 del 2026-10-03.
- **IDs.** Se conservan NFR15.1–NFR15.3, y lo nuevo toma el número siguiente (NFR15.4).
- **Prioridad.** NFR15 es SHOULD. Lo que aquí protege AUTONOMIA-04 (que métricas y logs no lleven
  texto) es MUST por NFR10.3.

**Insumos.**
- F1, F7 y F8, la máquina de estados §3.1 y FD-U10-14 de `functional-design/functional-spec.md`
  (functional-spec).
- BR2.3 y BR6.4 de `functional-design/rules.md` (rules).
- NFR10 y NFR15 de `inception/requirements-analysis/requirements.md` (requirements).
- C15, C16 y C21 de `inception/contract-design/contract-summary.md` (contract-summary).
- La decisión de Infrastructure Design registrada en `project.md`: sin Alertmanager, Loki ni
  notificaciones en el MVP.

## 1. Requisitos

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR15.1 | cambia | El proxy publica métricas de Prometheus sin datos (NFR-U10-11). | `/metrics` en el puerto interno publica las métricas de §2, con etiquetas **solo** de enum: `outcome` (`restored`, `failed_after_send`, `failed_closed`), `code` (los siete de C21 o `ok`), `provider` (`anthropic`, `google`, `openai`), `role` (`judge`, `verifier`, `verifier_permuted`), `slot` (`primary`, `fallback`) y `category` (`PERSONA`, `LUGAR`, `EXPEDIENTE`, `IDENTIFICADOR`, `ENTIDAD`). Una prueba recorre todas las series tras el éxito y cada rama de error: cada valor de etiqueta está en su enum, y el *canary* de NFR10.3 aparece 0 veces. Nunca hay etiquetas `run_id`, `model` ni `profile_name`. | Nivel 0 |
| NFR15.2 | cambia | Logs JSON con un evento por llamada (BR2.3; FD-U10-14). | Una línea `anonymizer.call` por `generate`, con los campos permitidos de NFR10.3, y una línea `anonymizer.startup` con las versiones y huellas de NFR11.1. `run_id` y `profile_name` solo van en el log, nunca en métricas. Prueba: el esquema de la línea valida y no tiene campos extra. | Nivel 0 |
| NFR15.3 | cambia | El estado del proxy se ve sin llamar a un proveedor (BR6.4, C16). | `/readyz` devuelve 503 con la lista de checks que fallan, por nombre y sin valores. `veridicus_anonymizer_ready` vale 1 solo cuando `/readyz` daría 200. Ninguna de las dos abre conexiones hacia fuera (NFR10.7). | Nivel 0 y nivel 1 |
| NFR15.4 | nuevo | Un panel de Grafana muestra el anonimizador. | El *dashboard* versionado (lo empaqueta U2) muestra: llamadas por resultado y proveedor; p95 de seudonimización y de proveedor; reemplazos por categoría; marcas alteradas; peticiones en curso frente al tope; y *tokens* por proveedor (NFR15). Una prueba valida su JSON y comprueba que solo consulta métricas `veridicus_anonymizer_*` existentes. Sin alertas que notifiquen (`project.md`). | Nivel 0 (validación del JSON) |

## 2. Catálogo de métricas (para C15, por PR de U1)

```yaml
metrics:
  - name: veridicus_anonymizer_requests_total
    type: counter
    labels: [outcome, code, provider, role, slot]
  - name: veridicus_anonymizer_masking_seconds
    type: histogram
    labels: [outcome]
    buckets: [0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 15, 30]
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

En la CLI, el módulo no publica métricas. Los mismos datos van en el `ModelCall` y en el reporte de la
CLI, que son de U11.
