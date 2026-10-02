# Project-Level Rules

> Project-specific specialisation and corrections. Loaded after `org.md` and
> `team.md` as strict-additive guidance; contradictions with broader policy
> are rejected. Populated by practices-discovery and the self-learning loop.
>
> Use sparingly: most teams don't need a project layer. Reach for it
> only when this specific project needs stable, durable guidance beyond the
> team practice (for example, package-specific release checks or an additional
> regression suite for a legacy component).

## Way of Working

<!-- Project-specific specialisation. Example: -->
<!-- This monorepo requires package-scoped branch names and a package owner -->
<!-- review in addition to the team's normal merge policy. -->

## Walking Skeleton

<!-- Project-specific specialisation. Example: -->
<!-- The walking skeleton must exercise the legacy service adapter as well -->
<!-- as the new service boundary. -->

## Testing Posture

<!-- Project-specific specialisation. -->

- La GPU es opcional: el sistema y las suites de niveles 0 y 1 funcionan completos en CPU; las pruebas que requieren GPU (máquina de hasta 4 GPU y 32 GB de RAM) se agrupan en una etapa separada que corre a demanda. (learned 2026-10-02) <!-- cid:261002-veridicus-mvp:practices-discovery:c8177cec18b3a1ab416d585839f49f063e1b8e9bb5b1dc1e2af273732a278cca -->

## Guard Policy

<!-- Project-specific. Mode: strict, relaxed, or off. Strict here holds for every intent and cannot be changed from chat. A section under the retired Change Control heading, written by an earlier release, is still read. -->

## Deployment

<!-- Project-specific specialisation. -->

## Code Style

<!-- Project-specific specialisation. -->

## Tech Stack

<!-- Technology choices locked for this project. -->

## Decided

- **QUÉ:** Veridicus, módulo de entrevista forense que contrasta testimonios orales de comparecientes con un marco de verdad documental y propone hallazgos de incongruencia con su Cadena de Pensamiento (CoT); la fuente única de requisitos es `specs/prd.md` (con `pvb.md`), nunca una copia.
- **POR QUÉ:** reducir la fatiga analítica y la revictimización en justicia transicional (Colombia) sin emitir veredictos de veracidad y sin que datos sensibles salgan del clúster local (PRD Segmentos 2 y 6).
- **CÓMO:** microservicios en Kubernetes local (todo funciona en CPU; GPU solo como perfil opcional para evaluación y demo), Whisper local, PostgreSQL + pgvector con CloudNativePG, cola Redis asíncrona, GitOps con PR y evidencia; entregado por los módulos 6–8 del curso (PRD Segmento 13).

<!-- Decisions made in earlier stages that should not be re-asked. -->
<!-- Format: DECIDED: [decision] (Stage [slug], [date]) -->

## Scope Overrides

<!-- Custom scope rules for this project. -->

## Forbidden

<!-- Populated by practices-discovery affirmation gate. -->
<!-- Format: NEVER [behavior] (affirmed [date]) -->
<!-- Example: NEVER throw exceptions across service layer boundaries (affirmed 2026-05-17) -->

- NEVER guardar datos reales (testimonios, audios, nombres o expedientes) en el repositorio ni en la CI: solo datos sintéticos (afirmada 2026-10-02). (affirmed 2026-10-02)

- NEVER versionar valores de Secret, archivos `.env`, `kubeconfig` ni claves privadas (afirmada 2026-10-02). (affirmed 2026-10-02)

- NEVER ejecutar migraciones de esquema al arrancar un pod: toda migración corre como un `Job` aparte que entra por su propio PR (afirmada 2026-10-02). (affirmed 2026-10-02)

## Mandated

<!-- Populated by practices-discovery affirmation gate. -->
<!-- Format: ALWAYS [behavior] (affirmed [date]) -->
<!-- Example: ALWAYS use Result<T,E> for fallible operations in service layer (affirmed 2026-05-17) -->

## Corrections

<!-- Project-specific corrections from human feedback. -->
<!-- Format: NEVER/ALWAYS [behavior] (learned [date]) -->
- ALWAYS leer las respuestas de los archivos de preguntas tanto en la misma línea de `[Answer]:` como en la primera línea no vacía siguiente; el humano suele escribirlas debajo. (learned 2026-10-02) <!-- cid:261002-veridicus-mvp:practices-discovery:467512cff48e83455ac80ffadca31cb414ec289375023f754a1c135e748fc925 -->
- En etapas con varios colaboradores, consolidar sus preguntas en una sola entrevista sin duplicados, y dejar los detalles finos para la etapa que los convierte en requisitos medibles. (learned 2026-10-02) <!-- cid:261002-veridicus-mvp:practices-discovery:e33bba909847029f3684a595bd16b81c5635816003fdf5841986d015e9e9b7f9 -->
- Si un archivo quedó a nombre de root tras editarlo desde el host, reemplazarlo por una copia idéntica verificada por SHA-256 antes de modificarlo, y avisar al humano. (learned 2026-10-02) <!-- cid:261002-veridicus-mvp:practices-discovery:a80ba74d7856b962f646f365ad379c8aac5b5106af8462c71999c1d8599f358d -->
- Cuando una respuesta de una etapa cambia un insumo (PRD, PVB, memoria), corregir el original en un commit propio antes de integrar la etapa. (learned 2026-10-02) <!-- cid:261002-veridicus-mvp:practices-discovery:3e8a40706c6cfd00ea2794ddbf7d5fe278398ef28ae968ea50447bc8225a41a0 -->
- La IA califica cada afirmación frente al marco de verdad solo como «congruente», «incongruente» o «no documentada», con su CoT, como sugerencia editable; nunca «falso», «verdadero» ni «miente» (AUTONOMIA-03 se mantiene, decisión de Practices Discovery 2026-10-02). (learned 2026-10-02) <!-- cid:261002-veridicus-mvp:practices-discovery:27baeece2ecd93b63f6373e00639df27d40219e3b956f0629289e965609efa79 -->
- Los archivos se intercambian entre host y contenedor con `docker cp`: si un archivo no se puede escribir, copiarlo a una ruta ignorada por git (`docker/.state/intercambio/`) para que el humano lo edite y lo devuelva, y luego moverlo a su ubicación definitiva; si hay archivos de root que no se pueden añadir a git, avisar de inmediato para corregirlos desde el host. (learned 2026-10-02) <!-- cid:261002-veridicus-mvp:practices-discovery:be9e63902ca25f9588247bfa3575271753974a8364c33551c62a5ea397bff7f7 -->
- Un insumo citado sin ruta (p. ej. `pvb.md`) se lee como el archivo de la raíz del proyecto; ante diferencias con el PVB manda `specs/prd.md` (nota H6 y `docs/coherencia-insumos.md`). (learned 2026-10-02) <!-- cid:261002-veridicus-mvp:requirements-analysis:4d1bfe642d2e18dfbe6c5854cc0868e4f063e6203f99df97e122094d67b28747 -->
- Solo una afirmación calificada «incongruente» con similitud en o por encima del umbral produce alerta; «congruente» y «no documentada» nunca la producen. (learned 2026-10-02) <!-- cid:261002-veridicus-mvp:requirements-analysis:b0f89ef151ebf2f5f69666a62f0e55ec3ef649c57ea81f3093a1de4fe8a9e96f -->
- No volver a preguntar lo que ya deciden el PRD y las 19 decisiones de `docs/coherencia-insumos.md`; preguntar solo lo que falta para criterios medibles. (learned 2026-10-02) <!-- cid:261002-veridicus-mvp:requirements-analysis:9f8c3fdf1c0d4d56371a54647353577cb1847b1cd75170a20a99df239be483f3 -->
- Como el scope `classic` omite Ideation, cada requisito se traza a un segmento del PRD (S1–S13), a una regla AUTONOMIA o a una respuesta de la etapa, y su origen queda documentado. (learned 2026-10-02) <!-- cid:261002-veridicus-mvp:requirements-analysis:2bfb7fd323d0d40cc8f495b18fc543b2e068e797412e7a1a173e125f4604dc39 -->
- Las métricas de adopción del PRD (uso semanal > 85 %, desestimación < 15 % en producción) son hipótesis de producto para el TG, no criterios de aceptación del MVP. (learned 2026-10-02) <!-- cid:261002-veridicus-mvp:requirements-analysis:4f04d2dda770fa835296aa00d4535f74ff82f251ed7800db703f55d8a188ab0b -->
