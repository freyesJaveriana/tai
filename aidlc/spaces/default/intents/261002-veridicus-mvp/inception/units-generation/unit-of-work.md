# Unidades de trabajo — Veridicus (MVP)

**Insumos.** Componentes y ADR de `inception/domain-design/components.md` y `decisions.md`; requisitos
de `inception/requirements-analysis/requirements.md` (requirements); historias de
`inception/user-stories/stories.md` (stories); prácticas de team-practices; respuestas P1–P5 y plan
aprobado en `units-generation-questions.md`.

**Criterio.** Rebanadas verticales por capacidad (P1): cada unidad atraviesa los procesos que necesita.
Contratos y plataforma son unidades propias (P3, P2). Las funciones SHOULD y COULD tienen unidades
propias, salvo las de plataforma y de pantalla (P4). Cada unidad cumple la convención de auditoría y
de accesibilidad en lo suyo; la definición común la entregan `identity-access` y `text-flow` (P5).

Este documento describe **qué** es cada unidad. El orden de entrega lo decide Delivery Planning.

## Tabla de unidades

| Unit ID | Directory | Unidad | Tipo | Prioridad | Tamaño | Componentes que toca |
|---|---|---|---|---|---|---|
| U1 | u1-contracts | contracts | spec | MUST | M | IntegrityPolicy (esquemas y lista), contratos de cola de InterviewSession, SemanticEvaluation y SpeechProcessing, OpenAPI de ConsoleApi |
| U2 | u2-platform | platform | packaging | MUST (con partes SHOULD/COULD) | L | Dependencias externas de todos los componentes |
| U3 | u3-identity-access | identity-access | service | MUST | M | IdentityAccess, ConsoleApi (autenticación y autorización), AnalystConsole (inicio de sesión y usuarios) |
| U4 | u4-text-flow | text-flow | — (sin tipo) | MUST | XL | TruthFrame, InterviewSession, SemanticEvaluation, HumanReview (creación de sugerencias), ModelGateway, IntegrityPolicy, ConsoleApi, AnalystConsole |
| U5 | u5-human-review | human-review | service | MUST | M | HumanReview, ConsoleApi, AnalystConsole |
| U6 | u6-session-lifecycle | session-lifecycle | service | MUST (con US10.1 SHOULD y US11.2 COULD) | M | TruthFrame (versiones), InterviewSession, ConsoleApi, AnalystConsole |
| U7 | u7-forensic-report | forensic-report | service | MUST | L | ForensicReport, InterviewSession (finalizar), HumanReview (rondas), ConsoleApi, AnalystConsole |
| U8 | u8-assistant-extras | assistant-extras | service | SHOULD / COULD | M | SemanticEvaluation, InterviewSession (pregunta sugerida), AnalystConsole |
| U9 | u9-voice | voice | service | SHOULD | M | SpeechProcessing, ModelGateway, InterviewSession, ConsoleApi, AnalystConsole |
| U10 | u10-anonymizer | anonymizer | service | COULD | M | ModelGateway (adaptador anonimizador) |

## Procesos desplegables (P2)

| Proceso | Componentes | Unidades que lo modifican |
|---|---|---|
| `frontend` (estático) | AnalystConsole | U3, U4, U5, U6, U7, U8, U9 |
| `services/session-api` | ConsoleApi, IdentityAccess, TruthFrame (con indexación en segundo plano), InterviewSession, HumanReview, ForensicReport — monolito modular con fronteras vigiladas por import-linter | U3, U4, U5, U6, U7, U8, U9 |
| `services/semantic-agent` | SemanticEvaluation, con usuario de base de datos de solo lectura (AC3.3.2) | U4, U8 |
| `services/audio-worker` | SpeechProcessing (SHOULD) | U9 |
| `services/anonymizer-proxy` | Adaptador anonimizador de ModelGateway (COULD; solo si se construye) | U10 |
| `libs/` | IntegrityPolicy, puerto y adaptadores de ModelGateway, jerarquía de excepciones | U1 (esquemas), U4, U10 |
| `contracts/` | Contratos versionados | U1 |
| `deploy/` | Charts y manifiestos | U2 (base), cada unidad añade lo de su proceso |

El modelo de despliegue por unidad es **compartido**: las unidades verticales no se despliegan solas,
sino que modifican procesos compartidos y entran por PR al tronco único (team-practices). Solo U2 y U1
producen artefactos propios (manifiestos y contratos).

## Definición de cada unidad

### U1 — contracts (spec)

- **Qué entrega.** Contratos versionados en `contracts/`: mensaje de turno a evaluar (incluye la
  instantánea del umbral y de la versión de escenario, ADR-006), mensaje de resultado de evaluación
  (ADR-002), mensajes de audio y transcripción, esquema JSON de la salida del juez y de la alerta
  (`additionalProperties: false`, sin campos de veracidad, enum de tres calificaciones), lista
  versionada de vocabulario prohibido, catálogo de `code` de Problem Details, OpenAPI de ConsoleApi,
  nombres de métricas (incluida la del indicador AIR) y formato de fecha compartido.
- **Límites.** Solo contratos y sus pruebas de validación con *fixtures* positivos y negativos; ningún
  comportamiento.
- **Restricciones.** Cada cambio de contrato entra por su propio PR y sube la versión; AC2.2.3,
  AC5.5.3 y AC5.5.4 se prueban aquí en nivel 0.

### U2 — platform (packaging)

- **Qué entrega.** Chart y manifiestos en `deploy/`: Cluster de CloudNativePG con `pgvector`, Redis,
  servidores locales del juez, de *embeddings*, de Whisper y TTS (artefactos de modelo fijados por
  `sha256`), `NetworkPolicy` de salida denegada para los pods con datos sin anonimizar, etiquetas de
  clasificación de datos, `requests`/`limits`, referencias a Secrets, `Job` de migraciones, políticas de
  manifiestos (`helm template` → `kubeconform` → Kyverno CLI), comprobación estática de que ningún
  *workflow* ni *script* aplica cambios al clúster, y prueba de humo `scripts/smoke.sh`. SHOULD/COULD:
  regla AIR en Prometheus/Grafana (US10.6), `Application` de Argo CD (US10.7) y KEDA (US11.4).
- **Límites.** No contiene código de aplicación. Ningún paso aplica cambios al clúster: todo es un
  artefacto revisable que el humano aplica tras fusionar su PR (AUTONOMIA-01).
- **Restricciones.** Cada política tiene control negativo. Infrastructure Design fija distribución de
  Kubernetes, CNI y namespaces.

### U3 — identity-access (service)

- **Qué entrega.** Inicio de sesión y token, gestión de usuarios por el `admin`, matriz de roles de
  FR1.2 en ConsoleApi, ausencia de cualquier ruta que escriba el umbral (AC8.3.1, AC8.3.2) y la
  **convención común de auditoría** (ADR-003): columnas `actor`/`at`, permisos sin `UPDATE`/`DELETE` y la
  prueba compartida de nivel 1 que verifican las demás unidades (US8.4).
- **Límites.** No incluye la autorización por dueño de sesión de cada acción concreta; cada unidad la
  aplica en sus rutas con la base que deja U3 (ADR-009).
- **Restricciones.** Contraseñas con hash adaptativo y sal; mismo cuerpo de error para usuario
  inexistente y contraseña errónea.

### U4 — text-flow (sin tipo: atraviesa consola y dos servicios)

- **Qué entrega.** El flujo de texto de team-practices de punta a punta: cargar e indexar un escenario
  (US1.1) y elegirlo del catálogo (US1.3); crear la sesión ligada a versión y umbral (US2.1); enviar
  turnos sin bloquear (US2.2); evaluar cada afirmación con la guardia del umbral antes del juez, salida
  validada y sin alertas parciales (US3.1, US3.2, US3.3, US4.1, US4.3); Paquete de Contexto de
  Traspaso (US4.2); creación de sugerencias de revisión en HumanReview y su presentación con la CoT en la
  consola; escaneo de vocabulario prohibido (US5.5); y la **base de accesibilidad** de la consola con la
  suite `axe` (US5.6).
- **Límites.** Las decisiones humanas sobre las sugerencias (aceptar, editar, descartar) son de U5; la
  consolidación, de U7; la versión nueva de escenario y la reanudación, de U6.
- **Restricciones.** Contiene los módulos guardia de AUTONOMIA-05 (100 % de ramas). Se evalúa en nivel 2
  sobre el Golden Dataset. Al no tener tipo, recibe todos los documentos de diseño de Construction.

### U5 — human-review (service)

- **Qué entrega.** Aceptar con CoT consultada (US5.1), editar con reformulación propia (US5.2),
  descartar con nota (US5.3), solo el dueño cambia sus alertas y solo lectura para los demás (US5.4);
  rondas de revisión y decisiones de solo inserción (ADR-007).
- **Límites.** Bloquear una ronda y abrir una de corrección lo pide U7.
- **Restricciones.** Máquina de estados guardia de AUTONOMIA-03 con 100 % de ramas.

### U6 — session-lifecycle (service)

- **Qué entrega.** Versión nueva de un escenario (US1.2), pegar una transcripción completa (US2.3),
  lista de sesiones (US2.5), suspensión y reanudación por falta de latido (US7.1), indicadores de
  progreso (US10.1, SHOULD) e historial lateral (US11.2, COULD).
- **Límites.** Finalizar la sesión es de U7 porque abre la consolidación.
- **Restricciones.** La reanudación no duplica turnos, alertas ni filas de historial (AC7.1.3).

### U7 — forensic-report (service)

- **Qué entrega.** Finalizar la sesión e iniciar MTTV (US2.4), consolidar con sus precondiciones,
  escaneo y SHA-256 (US6.1), descarga con verificación de integridad (US6.2) y corrección con versión
  nueva (US6.3).
- **Límites.** Usa las rondas y decisiones de U5; no las define.
- **Restricciones.** Consolidación guardia de AUTONOMIA-03 con 100 % de ramas; dos consolidaciones
  simultáneas, una sola gana (AC6.1.6).

### U8 — assistant-extras (service)

- **Qué entrega.** Pregunta sugerida con aprobación del analista (US10.3), permutación del orden de
  lectura (US10.5) e indicio afectivo en el paquete (US11.1, COULD).
- **Límites.** El audio de la pregunta es de U9.
- **Restricciones.** Ninguna pregunta en un turno con afirmación «no documentada»; US10.5 duplica las
  inferencias por alerta candidata en CPU (lo cuenta Delivery Planning frente a NFR3 y NFR8).

### U9 — voice (service)

- **Qué entrega.** Grabar un turno por voz y transcribirlo con Whisper en CPU (US10.2) y escuchar la
  pregunta aprobada (US10.4).
- **Límites.** El turno transcrito sigue el mismo camino que un turno de texto (U4).
- **Restricciones.** Se agrega solo cuando el flujo de texto funciona (team-practices). El audio crudo
  no sale del clúster.

### U10 — anonymizer (service, COULD)

- **Qué entrega.** Adaptador anonimizador de ModelGateway que enmascara nombres, ubicaciones y números
  de expediente antes de cualquier llamada externa y falla cerrado, con la prueba del *payload*
  saliente y la `NetworkPolicy` que solo le da salida a él (US11.3).
- **Límites.** Solo se construye si se decide usar un modelo externo; ninguna unidad MUST depende de
  ella.
- **Restricciones.** 100 % de ramas (módulo guardia de team-practices si se construye).
