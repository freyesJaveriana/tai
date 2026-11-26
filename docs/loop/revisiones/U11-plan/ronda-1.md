# Ronda 1 — Plan de B11a (U11 incoherence-analyzer), revisión ML-8

**VEREDICTO: NOT-READY.** La revisión la hizo `aidlc-architecture-reviewer-agent` el 2026-11-26. Leyó los archivos, pero no ejecutó `pytest`, `uv` ni `mypy`.

Hubo 2 hallazgos bloqueantes, 10 importantes y 3 menores (R-01 a R-15). Cada hallazgo y dónde se resolvió está en la sección «Revisión ML-8 del plan» de `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/incoherence-analyzer/code-generation/code-generation-plan.md`.

**Bloqueantes:**
- **R-01:** el perfil `demo-anthropic` no validaba contra `profiles.schema.v1.yaml`:
  - le faltaban `schema_version`, `role_aliases` y `family`;
  - `prompt_sha256` y `model_call_timeout_s` no son campos del perfil;
  - `kind` no tenía valor.
- **R-02:** la API de Anthropic no admite `minLength` en `output_config.format`. La corrida real habría recibido un 400.

**Cumple, según el revisor:**
- AUTONOMIA-05 en el rojo del paso 3;
- AUTONOMIA-04 compuesta, con su control negativo `bypass`;
- el plan no usa red real, clúster, `sbatch` ni datos reales;
- CG-U11-11 y la pregunta 1 = A están aplicadas de forma coherente.
