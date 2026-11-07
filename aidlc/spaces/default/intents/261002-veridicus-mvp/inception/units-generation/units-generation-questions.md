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

---

## Segunda pasada (2026-11-07) — cambio 01 (DT27) y adenda 02

Se eligió **Modify**: se conservan los ID U1–U10, las unidades que cambian se ajustan, lo que sale se
marca «Retirado» sin renumerar y las unidades nuevas toman U11 en adelante. No se vuelve a preguntar lo
que ya deciden `docs/iteracion2.md` (P3 = A: la biblioteca y la CLI son una unidad nueva de tipo
`library`; §2.5: veredicto por unidad) ni el Domain Design aprobado (revisión 2).

### Pregunta 6 — ¿Qué hacemos con los cinco hallazgos Minor de la revisión 3 de Domain Design?

`domain-design/reviews/review-03.md` dio READY con R-01 (ProblemReport sin `session_id` escapa de la
retención), R-02 (código del fallo cerrado del anonimizador sin nombre; `anonymizer.incident` en el
contrato v1.0.0), R-03 (ConsoleApi no declara «registrar la retirada del consentimiento»), R-04 (dos
definiciones de «analizador sin rebaja») y R-05 (DD-06(b) cambia el nivel de exigencia, no el dueño).

A. **Anotarlos como precisiones en la tabla de esta etapa**, cada uno asignado a la unidad y la etapa que
   lo resuelve (Functional Design o Contract Design de esa unidad), sin editar `components.md` aprobado; en
   la aprobación decides si alguno se lleva al original **(Recomendada)**
B. Corregir ya `components.md` y `decisions.md` en commits propios, antes de seguir.
C. Dejarlos solo en la revisión 3 y que cada Functional Design los encuentre.
X. Other (please specify)

[Answer]: A

### Pregunta 7 — ¿Confirmas el cambio de AUTONOMIA-03 en `team.md`?

Con DD-09 (commit d1c687f), AUTONOMIA-03 de `team.md` dice «consolidar el reporte de revisión final»
en vez de «reporte forense final», alineado con el glosario (`review_report`) y con VE-03.

A. **Confirmarlo**: la regla conserva su sentido (ninguna consolidación sin el analista) y usa el término
   del glosario **(Recomendada)**
B. Revertirlo a «reporte forense» y dejar el glosario como única traducción.
X. Other (please specify)

[Answer]: A

### Pregunta 8 — `team-practices.md` quedó desalineado con `team.md`

`practices-discovery/team-practices.md` (aprobado el 2026-10-02) aún describe el umbral del Silencio
Fáctico, el Golden Dataset, el Paquete de Contexto de Traspaso y los módulos guardia de entonces; el
cambio 01 actualizó `team.md`, que es lo que se carga en cada etapa.

A. **`team.md` manda**: se anota en la tabla de precisiones que `team-practices.md` queda superado donde
   difiere, sin editarlo; en la aprobación decides si se actualiza **(Recomendada)**
B. Actualizar ya `team-practices.md` en su propio commit para que repita `team.md`.
C. Añadir solo una nota al inicio de `team-practices.md` que remita a `team.md`.
X. Other (please specify)

[Answer]: A

### Pregunta 9 — ¿Qué entra en U11 `incoherence-analyzer` (library)?

La CLI debe correr sin Redis, Kubernetes ni base de datos (DT26, US12.2) y en ZINE (US14.2).

A. **Todo lo que la CLI necesita**: IncoherenceAnalyzer (con la verificación de citas), AnalyzerCli,
   ModelGateway (puerto y adaptadores nativo y compatible con OpenAI, errores tipados, proveedor alterno),
   ExecutionProfiles (carga, validación y huella) y las reglas de IntegrityPolicy que usa el analizador
   (escáner de vocabulario y aviso, que dejan U4); el modo evaluación y la métrica de sesgo (US15.10)
   **(Recomendada)**
B. ModelGateway y ExecutionProfiles como unidades `library` aparte, y U11 solo con el analizador y la CLI.
C. U11 solo con el analizador y la CLI; ModelGateway y ExecutionProfiles siguen en U4.
X. Other (please specify)

[Answer]: A

### Pregunta 10 — U10 `anonymizer` sube a MUST: ¿qué entrega y de qué tipo es?

El anonimizador es un módulo de la biblioteca (team.md, Walking Skeleton) que la CLI usa en el mismo
proceso, y en el clúster es el pod `anonymizer-proxy`, única salida a internet (US11.3, US11.5, US11.6).

A. **U10 de tipo `service`**: el módulo de seudonimización (NER local, marcadores consistentes, fallo
   cerrado, incidente), el proceso `anonymizer-proxy` que lo expone en el clúster y la lista de dominios
   con su prueba; la `NetworkPolicy` y la lista blanca de CoreDNS siguen en U2 **(Recomendada)**
B. U10 de tipo `library` solo con el módulo; el proceso `anonymizer-proxy` pasa a U2.
C. Meter el anonimizador en U11 y retirar U10.
X. Other (please specify)

[Answer]: A

### Pregunta 11 — ¿En qué unidad vive AnalysisWorker (proceso `semantic-agent`)?

A. **En U4**, que envuelve la biblioteca con la cola de corridas y resultados (iteracion2 P3, opción C
   como envoltura); U4 depende de U11 **(Recomendada)**
B. En U11, junto a la biblioteca.
X. Other (please specify)

[Answer]: A

### Pregunta 12 — ¿Dónde van ResearchReports y EthicsGovernance?

A. **Dos unidades nuevas**: U12 `research-reports` (service: subir, consultar y comparar reportes de la
   CLI, consola del investigador M8; US12.6, US12.7) y U13 `ethics-governance` (service: las
   demostraciones US15.1, US15.3, US15.6, US15.7 y US15.9). Las VE que siguen MUST quedan en la unidad
   dueña de su componente (consentimiento y retirada en InterviewSession, aviso en ConsoleApi, marca de
   agua en ReviewReport, sesgo en U11) **(Recomendada)**
B. Una sola unidad nueva U12 con los dos componentes.
C. Repartirlos en unidades existentes (ResearchReports en U11, EthicsGovernance en U3).
X. Other (please specify)

[Answer]: A

### Pregunta 13 — ¿Cambia el directorio de U7 con el renombre a ReviewReport?

A. **Mantener `u7-forensic-report`**: no se tocan los diseños aprobados de la primera pasada en
   `construction/forensic-report/`; se anota que el componente es ReviewReport **(Recomendada)**
B. Renombrar a `u7-review-report` y mover `construction/forensic-report/` con `git mv` en su propio commit.

> Corrección: la primera versión de esta pregunta recomendaba renombrar porque «Construction aún no ha
> creado nada bajo el directorio viejo». Era falso: ya hay Functional Design, NFR Requirements, NFR Design
> e Infrastructure Design aprobados en `construction/forensic-report/`. El humano respondió primero
> «u7-review-report» con esa premisa y, ya corregida, eligió mantener el nombre.
X. Other (please specify)

[Answer]: A

### Pregunta 14 — ¿Quién es dueño de los scripts `sbatch` y del paquete de entrada para ZINE?

US14.2 y US14.3; los scripts son artefactos revisables que el humano lanza (AUTONOMIA-01). US14.1 ya se
cumplió antes del diseño (`docs/validacion-zine/`).

A. **U11**, porque empaquetan y ejecutan la CLI; viven junto a la evaluación (`evaluation/zine/`)
   **(Recomendada)**
B. U2 `platform`, con el resto de artefactos de infraestructura.
X. Other (please specify)

[Answer]: A

---

### Aprobación del plan de descomposición (segunda pasada)

Plan presentado: **13 unidades** (U1–U10 conservan su ID y su directorio; U11–U13 son nuevas), con el
mismo criterio de rebanadas verticales por capacidad (P1).

| Unidad | Tipo | Prioridad | Cambio | Depende de |
|---|---|---|---|---|
| U1 contracts | spec | MUST | Contrato común v1.0.0 (hallazgo con sus campos AUTONOMIA-05, códigos con `anonymizer.incident`), mensajes de corrida, esquema del perfil, catálogo de límites, OpenAPI; salen umbral y pasajes | — |
| U2 platform | packaging | MUST (+ US10.7, US10.8 SHOULD; US11.4 COULD) | Sin `pgvector` ni *embeddings*; `Secret` de proveedores; `NetworkPolicy` con salida solo del anonimizador y CoreDNS (US9.1, US11.6) | contracts |
| U3 identity-access | service | MUST | Igual; perfiles solo por PR (US8.3) | contracts |
| U4 text-flow | sin tipo | MUST | Se reduce: sesión con consentimiento y perfil, turnos, AnalysisWorker (`semantic-agent`), sugerencias, aviso, escaneo en salida e interfaz, base de la consola | contracts, identity-access, incoherence-analyzer |
| U5 human-review | service | MUST | Observaciones en vez de CoT | text-flow |
| U6 session-lifecycle | service | MUST (+ US10.1 SHOULD, US11.2 COULD) | Sale US1.2; entran importar (US2.6), modo final (US2.7), pausar y terminar (US15.2) | text-flow |
| U7 forensic-report | service | MUST | Componente ReviewReport; dos fragmentos citados; exportación con marca de agua (US15.8); directorio sin cambio (P13) | human-review |
| U8 assistant-extras | service | SHOULD | Se reduce: aclaraciones neutras (US10.3) y ambos órdenes (US10.5); sale el indicio afectivo | text-flow |
| U9 voice | service | SHOULD | Igual | text-flow, assistant-extras |
| U10 anonymizer | service | **MUST** | Módulo de la biblioteca + `anonymizer-proxy` + lista de dominios (P10) | contracts |
| **U11 incoherence-analyzer** | library | MUST | Nueva: analizador, CLI, ModelGateway, ExecutionProfiles, reglas de IntegrityPolicy, evaluación, sesgo, `sbatch` (P9, P14) | contracts, anonymizer |
| **U12 research-reports** | service | MUST (+ US12.7 SHOULD) | Nueva: reportes de la CLI y consola del investigador (P12) | contracts, identity-access |
| **U13 ethics-governance** | service | Demostración | Nueva: US15.1, 15.3, 15.6, 15.7, 15.9 (P12) | text-flow, human-review, forensic-report |

Procesos: `frontend`, `services/session-api`, `services/semantic-agent` (AnalysisWorker),
`services/audio-worker`, `services/anonymizer-proxy` (ahora MUST), `libs/` (biblioteca del analizador
y anonimizador), `contracts/`, `deploy/`, `evaluation/`. Las precisiones R-01..R-05, AUTONOMIA-03 y
`team-practices.md` van en la tabla de precisiones de `unit-of-work.md` (P6–P8).

- Approve Plan
- Revise Plan

[Answer]: Approve Plan
