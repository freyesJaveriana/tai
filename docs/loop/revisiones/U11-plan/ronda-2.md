# Ronda 2 — Plan de B11a (U11 incoherence-analyzer), revisión ML-8

**VEREDICTO: READY.** La revisión la hizo `aidlc-architecture-reviewer-agent` el 2026-11-26. La guardia de Plan Approval le bloqueó Bash, así que leyó los archivos solo con Read.

**El perfil `demo-anthropic` coincide con `profile-base.schema.v1` y `profiles.schema.v1`:**
- los papeles usan `scope`, `provider`, `model`, `family` y `api_key_ref`;
- el perfil usa `purpose`, `role_aliases`, `permutation` y `same_family_declared`;
- `kind="analyzer"` es válido.

**Hallazgos de la ronda 1:**
- **Resueltos:** R-01 a R-04 y R-07 a R-15.
- **R-05, parcial:** la variante (e) es un error de configuración y no `anonimizador_no_disponible`.
- **R-06, parcial:** se trata en N-01.

**Defectos nuevos:**

| ID | Severidad | Hallazgo | Resolución en la revisión 3 |
|---|---|---|---|
| N-01 | importante | `scan-cases.v1.yaml` mezcla casos `rule: vocabulary` y `rule: clarification` | Se ejecutan solo los casos `vocabulary`, con el conjunto de valores de `rule` fijado. Los `clarification` pasan a U8 (FD-U8-09) |
| N-02 | importante | K-84 necesita `analyze`, que en el paso 8 sigue siendo *stub* | Su verificación pasa al paso 9 |
| N-03 | menor | No estaba dicho cómo `--rojo` convierte el fallo en `ERROR` | Un `hookwrapper` que reescribe el reporte con `when="setup"` |
| N-04 | menor | Orden de las filas PD-10 a PD-13 | Sin cambio: solo afecta al orden |

El humano eligió `Approve Plan` sobre la revisión 3 el 2026-11-26.
