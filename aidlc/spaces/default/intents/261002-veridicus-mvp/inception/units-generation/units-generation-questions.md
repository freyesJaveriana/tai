# Preguntas — Unidades de trabajo (Veridicus)

Esta etapa agrupa los 11 componentes de `domain-design/components.md` en **unidades de trabajo**: cada
unidad pasa después por Functional Design, NFR, Infrastructure Design y la Parte 1 (plan de tareas) de
Code Generation. Aquí solo se fija **qué unidades hay y de qué dependen**; el orden de entrega lo decide
Delivery Planning.

Ya están decididos y no se vuelven a preguntar: el monorepo y los nombres orientativos de servicios
(`frontend/`, `services/session-api`, `services/semantic-agent`, `services/audio-worker`,
`services/anonymizer-proxy`, `libs/`, `contracts/`, `deploy/`), que la **primera unidad del plan es el
flujo de texto de punta a punta** (cargar el escenario → ingresar un testimonio en texto → consultar
`pgvector` → mostrar la alerta con su CoT; team-practices, Walking Skeleton) y que la voz se agrega solo
cuando ese flujo funciona.

## Cómo responder

- Escribe la letra después de `[Answer]:`, en la misma línea o en la siguiente.
- La opción **(Recomendada)** es mi propuesta; no está aplicada todavía.
- Si ninguna opción encaja, usa `X` y escribe la tuya.

---

### Pregunta 1 — ¿Con qué criterio se parten las unidades?

team-practices pide que la primera unidad sea el flujo de texto de punta a punta, que atraviesa la
consola, la API de sesión y el evaluador. Si las unidades fueran servicios, ese flujo no cabría en una
sola unidad.

A. **Por capacidad, en rebanadas verticales** (cada unidad atraviesa los servicios que necesita), con contratos y plataforma como unidades propias. Propuesta de unidades: `contracts` (contratos compartidos), `text-flow` (el flujo de texto de team-practices), `human-review` (decisiones sobre sugerencias), `forensic-report` (finalizar, consolidar, descargar, corregir), `session-lifecycle` (versiones de escenario, pegar transcripción, lista de sesiones, reanudación, progreso), `identity-access` (inicio de sesión, usuarios, auditoría), `platform` (manifiestos, NetworkPolicy, base de datos, cola, políticas de CI) y las unidades SHOULD/COULD de la Pregunta 4 **(Recomendada)**
B. Por servicio desplegable: `frontend`, `session-api`, `semantic-agent`, `audio-worker`, más `contracts`, `integrity-lib` y `platform`; el flujo de texto sería un Bolt de varias unidades, no una unidad.
C. Una sola unidad para todo el MVP.
X. Other (please specify)

[Answer]: A

### Pregunta 2 — ¿Cuántos procesos desplegables tiene el backend?

Domain Design separó la lógica en componentes; falta decidir cuáles comparten proceso. El evaluador ya
tiene un usuario de base de datos de solo lectura y un perfil de CPU distinto (ADR-002, ADR-006).

A. **Cuatro procesos**: `session-api` (ConsoleApi, IdentityAccess, TruthFrame con su indexación en segundo plano, InterviewSession, HumanReview y ForensicReport como monolito modular, con fronteras vigiladas por import-linter), `semantic-agent` (SemanticEvaluation, con su usuario de solo lectura), `audio-worker` (SpeechProcessing, SHOULD) y `frontend` (AnalystConsole, estático); IntegrityPolicy y el puerto ModelGateway como bibliotecas en `libs/`; los servidores de modelos (juez, *embeddings*, Whisper) son dependencias externas que despliega `platform` **(Recomendada)**
B. Un proceso por componente (once microservicios).
C. Un solo proceso backend con todo, incluido el evaluador.
X. Other (please specify)

[Answer]: A

### Pregunta 3 — ¿Cómo se manejan los contratos compartidos?

Los mensajes de cola (turno, resultado, audio), los esquemas del juez y de la alerta, la lista de
vocabulario prohibido y el OpenAPI los usan varias unidades.

A. **Una unidad `contracts` (tipo `spec`)** de la que dependen las demás; cada cambio a un contrato entra por su propio PR y versiona el contrato **(Recomendada)**
B. Cada unidad define los contratos que publica, dentro de su propia carpeta.
X. Other (please specify)

[Answer]: A

### Pregunta 4 — ¿Cómo se agrupan las funciones SHOULD y COULD?

SHOULD: progreso del procesamiento (US10.1), voz (US10.2), pregunta sugerida (US10.3), audio de la
pregunta (US10.4), permutación (US10.5), propuesta de umbral AIR (US10.6), GitOps (US10.7). COULD:
indicio afectivo (US11.1), historial lateral (US11.2), anonimizador (US11.3), KEDA (US11.4).

A. **En unidades propias, separadas de las MUST**: `voice` (US10.2, US10.4), `assistant-extras` (US10.3, US10.5, US11.1), `anonymizer` (US11.3); las de plataforma (US10.6, US10.7, US11.4) dentro de `platform` y las de pantalla (US10.1, US11.2) dentro de `session-lifecycle` **(Recomendada)**
B. Cada función dentro de la unidad de la capacidad que extiende, sin unidades aparte.
C. Una sola unidad `extras` con todas las SHOULD y COULD.
X. Other (please specify)

[Answer]: A

### Pregunta 5 — ¿Dónde viven las reglas transversales (auditoría y accesibilidad)?

La convención de historial de solo inserción (ADR-003, US8.4) y WCAG 2.1 AA (US5.6) afectan a casi
todas las unidades.

A. **Cada unidad cumple la convención en sus propias entidades y pantallas**; la definición común (columnas, permisos, prueba compartida y la suite `axe` de toda la consola) la entrega una sola unidad: auditoría en `identity-access` y accesibilidad en `text-flow`, que crea la base de la consola **(Recomendada)**
B. Una unidad aparte `cross-cutting` que entrega auditoría y accesibilidad para todas.
X. Other (please specify)

[Answer]: A

---

### Aprobación del plan de descomposición

Plan presentado: 10 unidades (U1 `contracts`, U2 `platform`, U3 `identity-access`, U4 `text-flow`,
U5 `human-review`, U6 `session-lifecycle`, U7 `forensic-report`, U8 `assistant-extras`, U9 `voice`,
U10 `anonymizer`), cuatro procesos backend y frontend, con las dependencias y tamaños detallados en
`unit-of-work.md`.

- Approve Plan
- Revise Plan

[Answer]: Approve Plan
