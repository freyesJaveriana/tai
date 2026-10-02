# Reglas descubiertas — Veridicus

Restricciones duras enunciadas por el humano en la pregunta 17 (B, C y E). Las reglas AUTONOMIA-01..05 y las de proceso siguen en `aidlc/spaces/default/memory/team.md` y no se repiten aquí.

## Mandated

<!-- El humano no enunció reglas ALWAYS nuevas en esta etapa. -->

## Forbidden

- NEVER guardar datos reales (testimonios, audios, nombres o expedientes) en el repositorio ni en la CI: solo datos sintéticos (afirmada 2026-10-02).
- NEVER versionar valores de Secret, archivos `.env`, `kubeconfig` ni claves privadas (afirmada 2026-10-02).
- NEVER ejecutar migraciones de esquema al arrancar un pod: toda migración corre como un `Job` aparte que entra por su propio PR (afirmada 2026-10-02).
