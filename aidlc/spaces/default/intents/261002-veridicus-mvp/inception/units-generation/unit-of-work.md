# Unidades de trabajo — Veridicus (MVP)

**Revisión 2 (2026-11-07), segunda pasada por el cambio 01 (DT27) y la adenda 02.** Sustituye a la
revisión 1 del 2026-10-02. U1–U10 conservan su ID y su directorio; ninguna unidad se retira; las nuevas
toman U11–U13. Lo que sale de cada unidad se nombra en su apartado «Sale». Ajustada el 2026-11-08 con
los hallazgos R-01 a R-07 de la revisión 2 (`reviews/review-02.md`).

**Insumos.**
- Componentes y ADR: `inception/domain-design/components.md` (components, revisión 2: 16 componentes) y
  `decisions.md` (ADR-001 a ADR-017).
- Requisitos: `inception/requirements-analysis/requirements.md` (requirements, revisión 2) y
  `requirements-adenda-02.md` (VE-01 a VE-17).
- Historias: `inception/user-stories/stories.md` (stories, revisión 2) y `stories-adenda-02.md`
  (US15.1–US15.10).
- Prácticas: `aidlc/spaces/default/memory/team.md`, que manda sobre `team-practices.md` donde difieren
  (P8).
- Otros documentos: `docs/iteracion2.md` §2.5–2.8 (veredicto por unidad y P3 = A).
- Respuestas: P1–P5 (primera pasada) y P6–P14 con el plan aprobado (segunda pasada) en
  `units-generation-questions.md`.

**Criterio.** Rebanadas verticales por capacidad (P1). Contratos y plataforma son unidades propias (P3,
P2). La biblioteca del analizador con su CLI es una unidad `library` sin infraestructura (iteracion2 P3
= A, P9), y el anonimizador es una unidad propia, ahora MUST (P10). El trabajador de cola que envuelve la
biblioteca vive en `text-flow` (P11). Los reportes de investigación y la demostración ética son unidades
nuevas (P12). Cada unidad cumple la convención de auditoría y de accesibilidad en lo suyo; la definición
común la entregan `identity-access` y `text-flow` (P5).

**Alcance ético.** El «analizador sin rebaja» (components, «Alcance ético»; ADR-016) son U11, U10 y el
AnalysisWorker de U4. Las VE que siguen MUST (DD-07) se cumplen en la unidad dueña del componente que las
contiene, sin rebaja; las de demostración viven en U13 (precisión UG-04).

Este documento describe **qué** es cada unidad. El orden de entrega lo decide Delivery Planning.

## Tabla de unidades

| Unit ID | Directory | Unidad | Tipo | Prioridad | Tamaño | Componentes que toca |
|---|---|---|---|---|---|---|
| U1 | u1-contracts | contracts | spec | MUST | M | IntegrityPolicy (esquemas y lista), contrato común v1.0.0, mensajes de cola de InterviewSession, AnalysisWorker y SpeechProcessing, esquema de ExecutionProfiles, OpenAPI de ConsoleApi |
| U2 | u2-platform | platform | packaging | MUST (con partes SHOULD/COULD) | L | Dependencias externas de todos los componentes |
| U3 | u3-identity-access | identity-access | service | MUST | M | IdentityAccess, ConsoleApi (autenticación y autorización), AnalystConsole (inicio de sesión y usuarios) |
| U4 | u4-text-flow | text-flow | — (sin tipo) | MUST | L | InterviewSession, AnalysisWorker, HumanReview (creación de sugerencias), IntegrityPolicy (escaneo en la salida y la interfaz, aviso), ConsoleApi, AnalystConsole |
| U5 | u5-human-review | human-review | service | MUST | M | HumanReview, ConsoleApi, AnalystConsole |
| U6 | u6-session-lifecycle | session-lifecycle | service | MUST (con US10.1 SHOULD y US11.2 COULD) | M | InterviewSession, ConsoleApi, AnalystConsole |
| U7 | u7-forensic-report | forensic-report | service | MUST | L | ReviewReport, InterviewSession (finalizar), HumanReview (rondas), ConsoleApi, AnalystConsole |
| U8 | u8-assistant-extras | assistant-extras | service | SHOULD | S | IncoherenceAnalyzer (aclaraciones y permutación), InterviewSession (ConductorObservation), AnalystConsole |
| U9 | u9-voice | voice | service | SHOULD | M | SpeechProcessing, ModelGateway, InterviewSession, ConsoleApi, AnalystConsole |
| U10 | u10-anonymizer | anonymizer | service | MUST | M | Anonymizer |
| U11 | u11-incoherence-analyzer | incoherence-analyzer | library | MUST | XL | IncoherenceAnalyzer, AnalyzerCli, ModelGateway, ExecutionProfiles, IntegrityPolicy (reglas del analizador) |
| U12 | u12-research-reports | research-reports | service | MUST (con US12.7 SHOULD) | M | ResearchReports, ConsoleApi, AnalystConsole (M8) |
| U13 | u13-ethics-governance | ethics-governance | service | Demostración | M | EthicsGovernance, ConsoleApi, AnalystConsole |

U7 conserva el directorio `u7-forensic-report` aunque su componente se llama ReviewReport (P13): la
primera pasada ya dejó diseños aprobados en `construction/forensic-report/`.

## Procesos desplegables (P2)

| Proceso | Componentes | Unidades que lo modifican |
|---|---|---|
| `frontend` (estático) | AnalystConsole | U3, U4, U5, U6, U7, U8, U9, U12, U13 |
| `services/session-api` | ConsoleApi, IdentityAccess, InterviewSession, HumanReview, ReviewReport, ResearchReports, EthicsGovernance (y su Job de retención) — monolito modular con fronteras vigiladas por import-linter | U3, U4, U5, U6, U7, U8, U9, U12, U13 |
| `services/semantic-agent` | AnalysisWorker, que envuelve la biblioteca del analizador con la cola de corridas y resultados | U4 (y U8 por la biblioteca) |
| `services/audio-worker` | SpeechProcessing (SHOULD) | U9 |
| `services/anonymizer-proxy` | Anonymizer en el clúster, única salida a internet (MUST) | U10 |
| `libs/` | Jerarquía de excepciones (traducción declarativa del catálogo de `code`), biblioteca del analizador (IncoherenceAnalyzer, AnalyzerCli, ModelGateway, ExecutionProfiles, reglas de IntegrityPolicy) y módulo del anonimizador | U1 (excepciones), U10, U11, U8 |
| `contracts/` | Contratos versionados y catálogo de límites | U1 |
| `deploy/` | Charts y manifiestos | U2 (base), cada unidad añade lo de su proceso |
| `evaluation/` | Conjunto sintético, arnés del nivel 2, scripts `sbatch` y paquete de entrada para ZINE | U11 |

Retirado de la revisión 1: TruthFrame en `session-api` y SemanticEvaluation en `semantic-agent`
(components, «Componentes retirados»).

El modelo de despliegue es **compartido**: las unidades verticales no se despliegan solas, sino que
modifican procesos compartidos y entran por PR al tronco único (team.md). U1, U2 y U11 producen
artefactos propios (contratos, manifiestos y la biblioteca con su CLI).

## Definición de cada unidad

### U1 — contracts (spec)

- **Qué entrega.** Contratos versionados en `contracts/`:
  - implementación aquí del contrato común v1.0.0 del TG (ADR-017): hallazgo con `hecho`, `tipo` (7
    valores), `cita_a`, `cita_b` y `observaciones` obligatorios (AUTONOMIA-05), `estado`, `codigo` y el
    bloque de consentimiento (A-4);
  - mensajes de corrida y de resultado (ADR-002), de audio y de transcripción;
  - esquema del perfil de ejecución y de la tabla de precios;
  - esquema del reporte JSON de la CLI, que consume U12;
  - catálogo único de límites `contracts/limits.v1.yaml`;
  - lista versionada de vocabulario prohibido y texto del aviso de VE-01;
  - catálogo de `code` de Problem Details y su jerarquía de excepciones en `libs/`, una clase por `code`
    sin lógica, que usan todas las unidades de código (R-02 de la revisión 2);
  - OpenAPI de ConsoleApi, nombres de métricas y formato de fecha.
- **Sale.** Mensaje de turno con la instantánea del umbral y de la versión de escenario, esquema del juez
  con tres calificaciones, esquema de pasajes y métrica AIR.
- **Límites.** Solo contratos, la jerarquía declarativa de excepciones y sus pruebas de validación con
  *fixtures* positivos y negativos; ningún comportamiento.
- **Restricciones.** Cada cambio de contrato entra por su propio PR y sube la versión. Comprobar que
  `anonymizer.incident` y el código del fallo cerrado están entre los códigos del contrato v1.0.0
  (UG-02).

### U2 — platform (packaging)

- **Qué entrega.** Chart y manifiestos en `deploy/`:
  - Cluster de CloudNativePG y Redis dentro del clúster (US9.4);
  - servidores locales del juez y del verificador, Whisper y TTS, con artefactos de modelo fijados por
    `sha256`;
  - `Secret` referenciado de las claves de los proveedores (lo crea el humano);
  - `NetworkPolicy` que niega la salida a todos los pods salvo al anonimizador, por 443 y DNS, y la
    lista blanca de CoreDNS (US9.1, US11.6);
  - sondas de salud, `requests`/`limits` y credenciales (US9.2, US9.3);
  - `Job` de migraciones y `Job` de retención como artefactos revisables;
  - políticas de manifiestos (`helm template` → `kubeconform` → Kyverno CLI);
  - comprobación estática de que ningún *workflow* ni *script* aplica cambios al clúster ni envía
    trabajos a ZINE (US9.5);
  - prueba de humo `scripts/smoke.sh`.
  - SHOULD/COULD: `Application` de Argo CD (US10.7), regla de descartes en Prometheus/Grafana (US10.8) y
    KEDA (US11.4).
- **Sale.** `pgvector`, servidor de *embeddings*, rol `veridicus_judge_ro` y regla AIR (US10.6).
- **Límites.** No contiene código de aplicación. Ningún paso aplica cambios al clúster: todo es un
  artefacto revisable que el humano aplica tras fusionar su PR (AUTONOMIA-01).
- **Restricciones.** Cada política tiene control negativo. Infrastructure Design fija distribución, CNI y
  namespaces.

### U3 — identity-access (service)

- **Qué entrega.** Inicio de sesión y token (US8.1), gestión de usuarios por el `admin` (US8.2), matriz de
  roles de FR1.2 en ConsoleApi (incluida «Exportar el reporte» y el rol `investigador`), ausencia de
  cualquier ruta que cambie perfiles, proveedores, *prompts* o límites (US8.3), y la **convención común
  de auditoría** (ADR-003, US8.4): columnas `actor`/`at`, permisos sin `UPDATE`/`DELETE` para el usuario de
  la aplicación y la prueba compartida de nivel 1.
- **Límites.** No incluye la autorización por dueño de sesión de cada acción; cada unidad la aplica en sus
  rutas con la base que deja U3 (ADR-009).
- **Restricciones.** Contraseñas con hash adaptativo y sal; mismo cuerpo de error para usuario
  inexistente y contraseña errónea.

### U4 — text-flow (sin tipo: atraviesa consola, `session-api` y `semantic-agent`)

- **Qué entrega.** El flujo del producto de punta a punta sobre la biblioteca de U11:
  - crear la sesión con su entrevista, su consentimiento (US15.4) y su perfil elegido (US13.1);
  - enviar turnos sin bloquear (US2.2);
  - AnalysisWorker en `semantic-agent`: consume corridas, llama a la biblioteca y publica el resultado
    sin resultados parciales (US3.2) y con solo lo nuevo en el modo incremental (US3.6);
  - creación de sugerencias de revisión en HumanReview y su presentación con las dos citas (US3.1), la
    limitación del modo fragmentado (US3.7) y el registro de modelos de la corrida en solo lectura
    (US12.5, AC12.5.3);
  - aviso de propósito limitado servido por ConsoleApi desde IntegrityPolicy (US15.5);
  - escaneo de vocabulario prohibido en la salida y en la interfaz (US5.5), con el escáner de U11;
  - **base de accesibilidad** de la consola con la suite `axe` (US5.6).
- **Sale.** Escenarios, indexación y catálogo (US1.1, US1.3), guardia del umbral, CoT interrumpida y
  Paquete de Contexto de Traspaso (US4.1–US4.3), ModelGateway (pasa a U11) y la propiedad del escáner
  (pasa a U11).
- **Límites.** Las decisiones humanas son de U5; la consolidación, de U7; importar, modo final, pausar,
  terminar y reanudar, de U6. Las reglas del analizador son de U11.
- **Restricciones.** Bloquea toda corrida tras la retirada del consentimiento (VE-10 (a), A-4). Se
  verifica en nivel 1 con *fakes* del `ModelGateway`. Al no tener tipo, recibe todos los documentos de
  diseño de Construction.

### U5 — human-review (service)

- **Qué entrega.** Aceptar tras leer las observaciones (US5.1), editar con reformulación propia (US5.2),
  descartar con nota (US5.3), solo el dueño cambia sus hallazgos y solo lectura para los demás (US5.4);
  rondas de revisión y decisiones de solo inserción (ADR-007); ObservationsView en lugar de CotView.
- **Límites.** Bloquear una ronda y abrir una de corrección lo pide U7.
- **Restricciones.** Máquina de estados guardia de AUTONOMIA-03 con 100 % de ramas.

### U6 — session-lifecycle (service)

- **Qué entrega.** Pegar un bloque de turnos (US2.3), ver la lista de sesiones (US2.5), importar una
  transcripción con turnos y páginas (US2.6), lanzar el modo final (US2.7), reanudar una sesión
  interrumpida (US7.1), pausar o terminar el análisis y registrar la retirada del consentimiento (US15.2,
  VE-10), indicadores de progreso (US10.1, SHOULD) e historial lateral (US11.2, COULD).
- **Sale.** Versión nueva de un escenario (US1.2).
- **Límites.** Finalizar la sesión es de U7 porque abre la consolidación.
- **Restricciones.** La reanudación no duplica turnos, hallazgos ni filas de historial (AC7.1.3). Pausar o
  terminar cancela las corridas en cola (DD-06).

### U7 — forensic-report (service; componente ReviewReport)

- **Qué entrega.** Finalizar la sesión (US2.4), consolidar con sus precondiciones, escaneo y SHA-256
  (US6.1), descargar con verificación de integridad (US6.2), corregir con versión nueva (US6.3), y exportar
  con marca de agua, roles y *hash* por exportación (US15.8). El reporte cita los dos fragmentos de cada
  hallazgo y muestra el aviso de VE-01.
- **Límites.** Usa las rondas y decisiones de U5; no las define. El registro de acceso lo escribe
  ConsoleApi en EthicsGovernance (U13), no ReviewReport (ADR-016): U7 avisa cada exportación por un puerto
  de ConsoleApi que no hace nada hasta que U13 lo implementa, así que U7 no depende de U13 y AC15.8.2 se
  cumple al construir U13 (UG-09).
- **Restricciones.** Consolidación guardia de AUTONOMIA-03 con 100 % de ramas; dos consolidaciones
  simultáneas, una sola gana (AC6.1.6).

### U8 — assistant-extras (service)

- **Qué entrega.** Aclaraciones neutras (US10.3): la salida `observaciones_conductor` validada en la
  biblioteca, su guardado como ConductorObservation y su presentación como «Aclaración sugerida · requiere
  tu decisión»; confirmación en ambos órdenes (US10.5): la permutación del verificador detrás de la opción
  del perfil.
- **Sale.** Pregunta sugerida por el Paquete de Contexto de Traspaso e indicio afectivo (US11.1).
- **Límites.** El audio de la aclaración es de U9. Toca el código de la biblioteca de U11 sin cambiar su
  contrato.
- **Restricciones.** El tema de una aclaración nunca contiene el texto de las citas (AC10.3.2); US10.5
  duplica las llamadas al verificador (lo cuenta Delivery Planning frente a NFR3 y NFR8).

### U9 — voice (service)

- **Qué entrega.** Grabar un turno por voz y transcribirlo con Whisper en CPU (US10.2) y escuchar la
  aclaración aprobada (US10.4).
- **Límites.** El turno transcrito sigue el mismo camino que un turno de texto (U4).
- **Restricciones.** Exige el consentimiento de voz (A-4). El audio crudo no sale del clúster y solo se
  conserva con autorización.

### U10 — anonymizer (service, MUST)

- **Qué entrega.** El módulo de seudonimización en `libs/` (NER local, marcadores consistentes por
  llamada con restauración en memoria, fallo cerrado e incidente cuando una respuesta llega con
  `anonimizado: false`), que la CLI usa en el mismo proceso, y el proceso `anonymizer-proxy` que lo expone
  en el clúster; la lista de dominios de los proveedores con su prueba (US11.5); la prueba del *payload*
  saliente y la del fallo cerrado (US11.3).
- **Límites.** La `NetworkPolicy` y la lista blanca de CoreDNS son de U2 (US11.6). Con un perfil local no
  interviene (iteracion2 P9 = A).
- **Restricciones.** Módulo guardia con 100 % de ramas. Nombrar el código del fallo cerrado y su efecto en
  la sesión (UG-02).

### U11 — incoherence-analyzer (library)

- **Qué entrega.** La biblioteca de Python con su línea de comandos, sin Redis, Kubernetes ni base de
  datos (DT26, US12.2):
  - IncoherenceAnalyzer: contrato común, verificación determinista de las dos citas en su turno con la
    regla del piloto (US3.4), verificador (US3.5), modo incremental (US3.6) y modo fragmentado con su
    limitación (US3.7), reglas fijas frente al testimonio (US3.3), `estado: error` con hallazgos vacíos
    (US3.2) e incidente de anonimización que aborta la corrida;
  - AnalyzerCli: lotes (US12.1), evaluación sobre el conjunto sintético (US12.3), corpus del piloto con
    resultados fuera de Git (US12.4), registro de modelos y costo (US12.5) y tabla de sesgo (US15.10);
  - ModelGateway: puerto, adaptadores nativo y compatible con OpenAI, errores tipados, bloqueo de
    contenido y proveedor alterno (US13.5);
  - ExecutionProfiles: carga, validación, huella y configuración efectiva (US13.2, US13.3), familias
    distintas (US13.4), primera rebanada con un proveedor comercial y uno local (US13.6) y comparación de
    proveedores (US13.7);
  - reglas de IntegrityPolicy que usa el analizador: escáner `scan(text, literal_sources)` y aviso;
  - scripts `sbatch` y paquete de entrada para ZINE en `evaluation/zine/` (US14.2, US14.3).
- **Límites.** No conoce colas, sesiones ni base de datos; eso es de U4. La seudonimización es de U10.
  Los scripts `sbatch` los lanza el humano (AUTONOMIA-01).
- **Restricciones.** Contiene los módulos guardia de AUTONOMIA-05 (100 % de ramas). Se evalúa en nivel 2
  con la propia CLI. Un destino externo sin anonimizador impide arrancar, igual que en los servicios.
  Los adaptadores externos de ModelGateway llevan las dos pruebas de AUTONOMIA-04 desde su lado: el
  *payload* saliente pasó por el anonimizador y, si este falla, no sale ninguna llamada.

### U12 — research-reports (service)

- **Qué entrega.** Subir y consultar un reporte de corrida o de evaluación de la CLI (US12.6) y comparar
  dos reportes (US12.7, SHOULD) en la consola del investigador (M8), de solo consulta, con el rol
  `investigador`.
- **Límites.** Guarda solo metadatos y cifras, nunca texto de transcripciones, hallazgos ni citas
  (NFR12).
- **Restricciones.** Rechaza un reporte que no cumpla el esquema de U1 o que traiga texto.

### U13 — ethics-governance (service, demostración)

- **Qué entrega.** Las demostraciones de la adenda 02 en EthicsGovernance, sin compuertas que bloqueen el
  uso: reconocimiento de las reglas de uso (US15.1, DD-01), reporte de problemas con aviso de testimonio
  (US15.3, DD-04), registro de quién vio cada sesión (US15.6, DD-02), Job de retención con su acta y reloj
  simulado (US15.7, DD-03) y avisos de bienestar (US15.9, DD-05).
- **Límites.** Implementa el puerto de registro de acceso de ConsoleApi que usan U7 (exportaciones,
  AC15.8.2) y las vistas de sesión (US15.6). El Job de retención lo lanza el humano como artefacto revisable (AUTONOMIA-01). Borra en el
  orden inverso de las referencias pidiéndoselo a U7, U5 y U4.
- **Restricciones.** Selecciona los reportes de problemas también por las sugerencias de la sesión
  (UG-01).

## Historias retiradas

US1.1, US1.2, US1.3, US4.1, US4.2, US4.3, US10.6 y US11.1 están «Retirada» en stories y no tienen unidad.
US14.1 se cumplió antes del diseño (`docs/validacion-zine/`) y no pertenece a ninguna unidad.

## Precisiones para decidir en la aprobación

No se edita ningún artefacto aprobado (regla de `project.md`). En la aprobación, el humano decide cuáles se
llevan al original, cada una en su propio commit.

| ID | Artefacto aprobado | Precisión propuesta | Resuelve | Origen |
|---|---|---|---|---|
| UG-01 | `domain-design/components.md` (ProblemReport, EthicsGovernance) | `session_id` es obligatorio en ProblemReport y se deriva de la sugerencia cuando el reporte se refiere a un hallazgo; el paso (1) de la retención lo cubre y AC15.7.2 añade ese caso | U13, Functional Design | review-03 R-01, P6 |
| UG-02 | `domain-design/components.md` (Anonymizer, IncoherenceAnalyzer, InterviewSession) | Nombrar el código del fallo cerrado (propuesta: `anonymizer.unavailable`) y decidir si solo falla la corrida o también bloquea la sesión; comprobar que `anonymizer.incident` y ese código están en el contrato v1.0.0 | U10, U11 y U4 (InterviewSession decide si bloquea la sesión), Functional Design; U1 | review-03 R-02, P6 |
| UG-03 | `domain-design/components.md` (ConsoleApi → InterviewSession) | Añadir «registrar la retirada del consentimiento» a la interacción de ConsoleApi y a los dependientes de InterviewSession (AC15.2.3) | U6, Functional Design | review-03 R-03, P6 |
| UG-04 | `domain-design/components.md` («Alcance ético») y `decisions.md` (ADR-016) | Una sola definición: el analizador sin rebaja son U11, U10 y el AnalysisWorker de U4; las VE de DD-07 se cumplen sin rebaja en la unidad dueña del componente que las contiene. ADR-016 remite a esta definición | Esta etapa | review-03 R-04, P6 |
| UG-05 | `domain-design/components.md` (DD-06 (b)) | Los estados `pausada` y `terminada` y la cancelación de lo encolado siguen en InterviewSession aunque VE-10 bajara a demostración; solo cambia el nivel de exigencia, no el dueño | U6 | review-03 R-05, P6 |
| UG-06 | `team.md` (AUTONOMIA-03) | Confirmado «reporte de revisión» en lugar de «reporte forense» (commit d1c687f); no hay nada más que cambiar | — | P7 |
| UG-07 | `practices-discovery/team-practices.md` | Queda superado por `team.md` donde difieren (umbral del Silencio Fáctico, Golden Dataset, Paquete de Contexto de Traspaso, módulos guardia de entonces, «flujo de texto primero») | — | P8 |
| UG-08 | `construction/forensic-report/` (primera pasada) | U7 conserva su directorio; los diseños de su segunda pasada usan ReviewReport | U7, Construction | P13 |
| UG-09 | `stories-adenda-02.md` (AC15.8.2) | El registro de la exportación en el registro de acceso entra por un puerto de ConsoleApi que implementa U13; mientras U13 no exista no se registra, y AC15.8.2 se verifica con U13 | U7 y U13, Functional Design | Revisión 2 R-01 |
