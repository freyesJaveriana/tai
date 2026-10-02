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

- Los NFR de calidad (IA, MTTV, latencia, cobertura) no se escriben como historias; quedan diferidos a NFR Requirements y Build and Test. (learned 2026-10-02) <!-- cid:261002-veridicus-mvp:user-stories:015afe962524881fea600233bba4a427cd1fca4eebaeb8bff20ecbf7972213b1 -->

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
- En una mob, las objeciones que un experto puede resolver se integran sin ronda 2; solo las de criterio (alcance, riesgo, prioridad) se preguntan al humano. (learned 2026-10-02) <!-- cid:261002-veridicus-mvp:user-stories:24646d48e7d4b055ecc0b03ed395cf809e732015de983801ad08361b1a140d6a -->
- No editar un artefacto de AI-DLC ya aprobado: las decisiones que lo precisan se registran en una tabla del artefacto de la etapa actual y el humano decide en la aprobación si se actualiza el original. (learned 2026-10-02) <!-- cid:261002-veridicus-mvp:user-stories:e2aaf3f291e4355c3bfc5cc35be21fdebeb957adbf891d55019f63aed6b15ecc -->
- Partir en User Stories las historias grandes (como umbral frente a paquete de traspaso), porque Units Generation dimensiona con historias y no con criterios. (learned 2026-10-02) <!-- cid:261002-veridicus-mvp:user-stories:e3b459d8722232ac75bd11f7b98748718cb2624407f37713375678b851ee33c1 -->
- La «CoT interrumpida» del Hecho No Documentado la produce el sistema de forma determinista, sin llamar al LLM, porque la guardia del umbral decide antes que el juez. (learned 2026-10-02) <!-- cid:261002-veridicus-mvp:user-stories:a5d1c5ece2de99f25b7a0e630d6f02dba5342bbcc64feaf9ca1a9b0ca10cf91b -->
- Un ajuste visual «configurable» (p. ej. los colores de estado) se implementa como tokens CSS en un único archivo que solo cambia por PR y que protege una prueba de contraste y de distinción en CI; nunca como un control de la consola. (learned 2026-10-02) <!-- cid:261002-veridicus-mvp:refined-mockups:f49ae6f0db137bc2d832361d63f518e05102682f335330bf6eb771164f209db5 -->
- Sin bocetos de Ideation (scope `classic`), las pantallas se diseñan desde `stories.md` y `requirements.md`, y las preguntas de diseño solo cubren lo que las historias no deciden. (learned 2026-10-02) <!-- cid:261002-veridicus-mvp:refined-mockups:0f903b5d671ec502a1272ce31c978d9ae7103e37a736e96ffe6e43d79821d18b -->
- Las maquetas se entregan como wireframes ASCII de fidelidad media-alta en Markdown (no Figma): el humano revisa en texto y el aspecto final lo fijan los tokens. (learned 2026-10-02) <!-- cid:261002-veridicus-mvp:refined-mockups:53dee12f909730c472c965691966d4ac2594a7a474618e364cf262f2532d2b1b -->
- El Paquete de Contexto de Traspaso es un panel no modal que no atrapa el foco, para leer la transcripción a la vez; solo las confirmaciones irreversibles son modales. (learned 2026-10-02) <!-- cid:261002-veridicus-mvp:refined-mockups:4b20da09c2b40bdd2fb0ba470cd96752dcb586feacc8026d1b77a7a0cbc062a7 -->
