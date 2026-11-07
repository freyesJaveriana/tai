# Iteración 2 — Análisis de impacto del cambio 01 (analizador de incoherencias)

**Fecha:** 2026-10-30 · **Estado:** aprobado por el autor el 2026-10-30, con P1–P18 respondidas
(todas con la opción recomendada, sección 6) · **Decisión de origen:** DT27 (2026-10-27) [INTERNO]

> DT28 (2026-10-30, un codificador más un verificador de otra familia; el ensamble queda como modo
> *Could* de `sistema`) llegó después de este análisis. Es coherente con él: el analizador usa juez y
> verificador de familias distintas, y no cambia ninguna propuesta.

Este documento es el análisis de impacto del cambio 01, al estilo del Paso 0 de
[`iteracion1.md`](./iteracion1.md). No cambia nada por sí mismo: ni los originales (`pvb.md`,
`specs/prd.md`, `docs/limite-autonomia.md`, la memoria de AI-DLC, `plan-aidlc.md`) ni los artefactos
aprobados del intent `261002-veridicus-mvp`. Las correcciones de la sección 5 son **propuestas de
texto**. Se aplican después de tu aprobación, cada una en su propio commit.

> **Repositorio público.** Este documento cita las decisiones del TG solo por su ID (DT09, DT15…) y
> no reproduce entrevistas, fragmentos ni codificaciones del piloto. Las cifras que vienen del
> repositorio principal van marcadas `[INTERNO]`.

---

## 0. Estado del flujo antes de este análisis

1. **Parche de auditoría aplicado** (`19c5e74`, `aidlc(auditoria): …`). Son las 63 líneas del
   2026-10-03 que faltaban en el clon nuevo.
2. **El flujo de AI-DLC ya no está en Code Generation.** El guardia de aprobación del plan bloqueaba
   cualquier escritura mientras el flujo estuviera en 3.5 sin un `Approve Plan`, incluso con
   `guard.plan-approval off`. Para poder escribir este documento sin aprobar el plan de U1, el autor
   ejecutó el salto atrás a **2.3 Requirements Analysis**
   (`aidlc engine jump execute --target requirements-analysis --direction backward`). Efectos:
   - En `aidlc-state.md`, las etapas 2.3 a 3.5 figuran como pendientes y 2.3 «en curso».
   - Los artefactos aprobados siguen en disco y en Git **sin ningún cambio**.
   - La etapa 2.3 **no se ha ejecutado**: no hay preguntas ni artefactos nuevos.

   Esto deja preparada la opción A de la sección 4, pero no la decide: si eliges la opción B, este
   intent se archiva tal como está.
3. El cursor `intents/active-intent` no existe en este clon (Git lo ignora). El motor encuentra el
   intent igual, porque es el único.

### Qué se leyó

- **Documentos propios:** `README.md`, `plan-aidlc.md`, `aidlc-state.md`,
  `docs/limite-autonomia.md`, `docs/iteracion1.md`, `aidlc/spaces/default/memory/`
  (`org.md`, `team.md`, `project.md`).
- **Artefactos aprobados del intent:** `requirements.md`, `stories.md`, `mockups.md`,
  `interaction-spec.md`, `components.md`, `decisions.md`, `unit-of-work*.md`,
  `contract-summary.md`, `bolt-plan.md`; los diseños 3.1–3.4 de las 10 unidades; el
  `code-generation-plan.md` de U1.
- **Insumos del TG:** el cambio 01; DT04, DT09, DT10, DT15–DT23, DT26 y DT27; el plan de
  continuación §3.3 y §4.1; la regla «Contradicción» de `codificador.py` y `TIPOS_CONTRADICCION` y
  `Fuente.verificar` de `verificar_codificacion.py`; la estructura de los datos del piloto (solo
  campos y conteos); `LEEME.md`.

---

## 1. Resumen

| Tema | Veredicto |
|---|---|
| Objeto del análisis | **Cambia por completo.** Antes se contrastaba el relato con un marco de verdad documental. Ahora se buscan contradicciones **dentro** del relato, sobre hechos centrales, con dos citas literales verificadas (DT09, DT15). |
| Requisitos | Salen FR2, FR5 y FR11.1. Se reescriben FR4, FR9, FR10.3, FR10.5, FR11.3 (pasa a MUST), FR12, NFR1, NFR4, NFR5 y NFR9. Entran FR del analizador, del contrato común y de perfiles y proveedores. |
| Historias | Salen 8 (US1.1–US1.3, US4.1–US4.3, US10.6, US11.1); cambian 23; se mantienen 13. Entran unas 10–15 nuevas. |
| Maquetas | Salen M2 (escenarios) y el Paquete de Contexto de Traspaso. M3 pasa a formulario de perfil. La tarjeta de M4 pasa a mostrar dos citas. |
| Dominio | Salen `TruthFrame` y `HandoffPackage`. Entran Transcripción, Turno con página, Contradicción, Perfil de ejecución, Proveedor y Llamada al modelo. `SemanticEvaluation` envuelve la biblioteca del analizador. |
| Unidades | U4 pierde dos tercios. U8 se reduce. U10 pasa a MUST. Falta decidir si la biblioteca y la CLI son una unidad propia (P3). |
| Contratos | Salen C4 y C9. Se reescriben C2, C3, C6 y C7 (contrato común), además de C13 y C14 (interfaz de modelos de DT21). |
| Diseño 3.1–3.4 | Se mantienen en lo esencial U3, U5 y U9. Hay que revisar U1, U2, U4, U6, U7, U8 y U10. |
| Plan de U1 | Se regenera. De sus 19 pasos se conservan la estructura (pasos 1–5, 9, 10, 13–19). Cambian los pasos 6–8, 11 y 12. |
| Reglas | Se mantienen AUTONOMIA-01, 02 y 03. Se reescriben **04** (seudonimizar antes de salir y fallar cerrado) y **05** (dos citas verificadas). Se levanta el alto antes de la Parte 2. |
| Bloqueantes | Hay 13 conflictos sin resolver (sección 3). Los más serios: la ventana de contexto del juez local frente a entrevistas de hasta ~180 000 caracteres; la `NetworkPolicy` por dominio con Calico OSS; los turnos sin página; y la falta de un criterio de calidad medible dentro de este repositorio (AUTONOMIA-02). |

---

## 2. Impacto sobre los documentos aprobados

Rutas relativas a `aidlc/spaces/default/intents/261002-veridicus-mvp/` (`I/`). «Sale» quiere decir que
deja de ser requisito; el texto aprobado queda en el historial de Git como antecedente.

### 2.1 Requisitos — `I/inception/requirements-analysis/requirements.md`

| ID | Veredicto | Qué cambia |
|---|---|---|
| §1 Intención, vocabulario, resultado del MVP | CAMBIA | El flujo de texto pasa a ser: cargar la transcripción → elegir el perfil → analizar → revisar → consolidar. Salen «escenario de control», «calificación de una afirmación» y «Silencio Fáctico». Entran «contradicción», «cita verificada», «perfil de ejecución» y «modo final / incremental». |
| FR1.2 Matriz de roles | CAMBIA | Salen las filas «Cargar escenarios» y «Aplicar un cambio de umbral». Entra «elegir el perfil de la sesión» (P8). |
| FR1.3 Auditoría | CAMBIA | Sale «cambio de umbral». Entra el registro de modelos por corrida (solo inserción). |
| **FR2** Escenario de control | **SALE** | Sin documentos externos (cambio §2). |
| FR3 Sesión y testimonio | CAMBIA | La sesión se liga a una entrevista y a un perfil con su `config_sha256`, ya no a un escenario. El turno lleva `n`, `hablante` (ENT/TEST), `pagina`, `pagina_fin` y `estado`. FR3.3 pasa a «importar una transcripción con turnos numerados» (P4, P5). |
| **FR4** Validación semántica | **SE REESCRIBE** | Pasa a ser el analizador de incoherencias: contrato común (cambio §4), 7 tipos, dos citas verificadas antes de emitir, sin puntaje, `estado: error` ⇒ `hallazgos` vacío, ningún campo de veracidad, modos final e incremental. FR4.2 (sin resultado parcial) y FR4.6 (el testimonio es dato) se conservan con otro texto. |
| **FR5** Silencio Fáctico y paquete | **SALE** | Su lugar lo toma la nueva AUTONOMIA-05. |
| FR6 Revisión humana | SE MANTIENE (con ajustes) | La CoT pasa a «observaciones» (P9). FR6.4 excluye del escaneo las dos citas y lo extiende a `observaciones_conductor`. |
| FR7 Consolidación y reporte | CAMBIA | FR7.2: salen los Hechos No Documentados y la versión del escenario; entran las dos citas con turno y página, el perfil, `config_sha256`, `prompt_sha256` y el registro de modelos. |
| FR8 Reanudación | SE MANTIENE | — |
| **FR9** Umbral | **SALE / CAMBIA** | No hay umbral. Lo que conserva es «el sistema nunca cambia su configuración por sí mismo; perfiles y proveedores solo por PR» (P8). FR9.3 (AIR) sale o se reorienta (P13). |
| FR10.1 Indicadores | CAMBIA | «Consultando marco de verdad…» pasa a «Analizando contradicciones…», más el progreso del modo final. |
| FR10.2 Voz | SE MANTIENE | El turno dictado no tiene página (P4). |
| FR10.3 Pregunta sugerida | CAMBIA | Solo aclaración neutra con tema y turnos, que nunca menciona la contradicción (DT23); solo en modo incremental. |
| FR10.4 TTS | SE MANTIENE | — |
| FR10.5 Permutación | CAMBIA | Hay que definir qué se permuta (P12). |
| **FR11.1** Indicio afectivo | **SALE** | DT15. |
| FR11.2 Historial | SE MANTIENE | — |
| **FR11.3** Anonimizador | **SUBE A MUST** | Diseño de DT18: NER local más reglas, marcas coherentes por entrevista, tabla de correspondencia solo en el clúster, detección de marcas alteradas, restauración de la cita antes de verificarla y fallo cerrado. |
| FR12.1 Plataforma | CAMBIA | PostgreSQL sin `pgvector` (no lo usa nadie más). |
| FR12.3 `NetworkPolicy` | CAMBIA | Salida negada a todos los pods salvo al anonimizador, solo hacia los proveedores configurados (P10). |
| FR12.4 Secrets | CAMBIA | Entran las claves de API de los proveedores, en un `Secret` que crea el humano. |
| FR12.7 Perfil GPU | CAMBIA | La calidad de los modelos locales grandes se mide en ZINE (DT26). |
| **Nuevos** | ENTRA | FR del analizador como biblioteca de Python más CLI sin Redis, Kubernetes ni base de datos (DT26). FR del perfil de ejecución por papel (juez, verificador, anonimizador) con su configuración efectiva y su huella. FR de la interfaz de modelos (DT21: adaptadores nativos y compatible con OpenAI, errores tipados, bloqueo de contenido, proveedor alterno registrado). FR de los scripts `sbatch` y del paquete de entrada para ZINE, como artefactos revisables. |
| NFR1 Soberanía | SE REESCRIBE | La nueva AUTONOMIA-04. |
| NFR2 CPU primero | SE MANTIENE | El producto funciona con el perfil `todo-local` en CPU. |
| NFR3 Interfaz no bloqueante | SE MANTIENE | Las latencias se recalculan (conflicto C3). |
| **NFR4** Calidad de la IA | **SE REESCRIBE** | Salen el escenario, las 6 discrepancias sembradas de fecha, lugar y rol, el caso de Hecho No Documentado y la trazabilidad a pasajes. Entran el 100 % de citas verificadas en lo mostrado, un conjunto sintético con contradicciones internas y casos trampa, y la precisión medida fuera del repositorio (P11). |
| NFR5 Adversarial | CAMBIA | Escenario B: juez y verificador de familias distintas, y datos sintéticos de una tercera. Escenario C: permutación redefinida. |
| NFR6 Explicabilidad (Likert) | SE MANTIENE | Se aplica a las observaciones. |
| NFR7 MTTV | SE MANTIENE | El caso de prueba cambia de naturaleza. |
| NFR8 Éxito del pipeline | CAMBIA | El modo final y los proveedores comerciales cambian la carga. |
| **NFR9** Indexación | **SALE** | — |
| NFR10 Seguridad | CAMBIA | Sale «el juez solo lee el marco de verdad». Entran claves por `Secret` y «un destino externo exige el anonimizador». |
| NFR11–NFR15 | SE MANTIENEN | En NFR13, los módulos guardia pasan a ser: la verificación de citas, la máquina de estados, la consolidación y el anonimizador. |
| §6 Fuera de alcance | CAMBIA | Entran el contraste documental (PU-17, DT24) y todo rasgo afectivo o estilométrico. Sale «la caché semántica no aplica»: ahora hay llamadas externas, y la caché del proveedor (DT21) sí aplica. |

### 2.2 Historias — `I/inception/user-stories/stories.md` (y `personas.md`)

- **Salen:** US1.1, US1.2 y US1.3 (escenarios); US4.1 y US4.2 (umbral y paquete); US4.3 (arranque sin
  umbral, que pasa a «no arrancar sin un perfil válido»); US10.6 (propuesta de umbral AIR); US11.1
  (indicio afectivo).
- **Cambian:**
  - US2.1–US2.5 (sesión ligada a entrevista y perfil; turnos con hablante y página; importar
    transcripción; qué dispara el modo final).
  - US3.1, que se reescribe como «revisar una contradicción con sus dos citas».
  - US3.2 (códigos `bloqueo_contenido` y `proveedor`) y US3.3 (sin rol de lectura del marco).
  - US5.1, US5.2, US5.5 y US5.6.
  - US6.1 (salen los conteos de HND; entran perfil y registro de modelos).
  - US8.3 («perfiles solo por PR») y US8.4.
  - US9.1–US9.4 (`NetworkPolicy`, humo, `Secret`, sin `pgvector`).
  - US10.1, US10.3, US10.5 y US11.3 (MUST).
- **Se mantienen:** US5.3, US5.4, US6.2, US6.3, US7.1, US8.1, US8.2, US9.5, US10.2, US10.4,
  US10.7, US11.2 y US11.4.
- **Nuevas (borrador):**
  - Revisar una contradicción con sus dos citas.
  - Elegir el perfil de modelos de la sesión.
  - Importar una transcripción con turnos y páginas.
  - Ejecutar el analizador por lotes desde la CLI.
  - Ver el registro de modelos de una corrida.
  - Ningún hallazgo sin dos citas verificadas.
  - Restaurar la cita seudonimizada antes de verificarla, y fallar cerrado.
  - Error tipado ante un bloqueo de contenido, con proveedor alterno.
  - Perfiles y claves solo por PR y por `Secret`.
  - Lanzar el modo final.
  - Recibir en el modo incremental solo las contradicciones con turnos nuevos.
  - Preparar el paquete `sbatch` para ZINE.
- **Personas:**
  - P1 Analista: deja de cargar escenarios; gana el perfil y la importación.
  - P2 Admin: el umbral pasa a perfiles, proveedores y claves por PR.
  - P3 Cumplimiento: «CoT y cita» pasa a dos citas verificadas.
  - Falta una persona: el **Investigador del TG** (CLI, corpus, ZINE).
- **Arrastres:**
  - La tabla de decisiones, las dependencias US2.1←US1.3, US6.1←US4.2, US9.2←US4.2 y US10.3←US4.1,
    y la fila 05 de «Cobertura AUTONOMIA».
  - La regla «ninguna MUST depende de U8–U10» deja de cumplirse (U10 pasa a MUST).

### 2.3 Maquetas — `I/inception/refined-mockups/`

| Pantalla o componente | Veredicto |
|---|---|
| Mapa §1, cabecera y enlace «Escenarios» | CAMBIA (sale el enlace) |
| M0 Inicio de sesión | Cambio leve (subtítulo) |
| M1 Lista de sesiones | CAMBIA: columna de entrevista y perfil en lugar de escenario y versión |
| **M2 Escenarios** | **SALE** (con su diálogo de carga) |
| M3 Nueva sesión | **Pasa a formulario de perfil**: entrevista (importar o en vivo) y perfil con resumen por papel, aviso de proveedor comercial y paso por el anonimizador |
| M4 §6.1 y §6.3 | CAMBIA: cabecera con perfil y huella; turnos con hablante, página y estado plegado; salen el estado HND y «Consultando marco…» |
| M4 §6.4 Tarjeta | CAMBIA: cita A y cita B (cada una con «T454 · p. 27»), tipo, hecho, observaciones; resalta dos turnos |
| **M4 §6.5 Paquete de traspaso** | **SALE** (con la línea afectiva) |
| M4 §6.6 Pegar | Pasa a «Importar transcripción» con vista previa y rechazos |
| M4 §6.7, §6.8 | CAMBIA: modo final; sale el conteo de HND |
| M5 Reporte | Cambio leve: dos citas, perfil, registro de modelos |
| M6 Usuarios | Se mantiene («sin control de perfiles ni claves») |
| Nuevas | Panel del registro de modelos; progreso del modo final |
| `interaction-spec.md` | Salen HandoffPanel (§4.5), el flujo F2 y `undocumented.notice`. Cambian StatusBadge, TurnComposer, TurnItem, ReviewSuggestionCard, PasteTranscriptDialog y SuggestedQuestion |
| `accessibility-checklist.md` | Cambian P-4, O-2, C-4, V-1, V-6 y V-8; sale V-3; sale M2 de §6 |
| `design-system-mapping.md` | Salen el token `--state-undocumented-*` y su prueba de distinción; sale «Indexando» |

### 2.4 Dominio — `I/inception/domain-design/components.md` y `decisions.md`

| Elemento | Veredicto |
|---|---|
| `TruthFrame` (Scenario, ScenarioVersion, Passage) | **SALE** |
| `InterviewSession` | CAMBIA: InterviewSessionRecord con entrevista, perfil y `config_sha256`. Turn con hablante, página y estado. TurnEvaluation pasa a ser una corrida del analizador con su registro de modelos. Salen HandoffPackage y `similarity_threshold` |
| `SemanticEvaluation` | CAMBIA: envoltura delgada de la biblioteca; ya no usa la base de datos |
| `HumanReview` | CAMBIA: ReviewSuggestion con `hecho`, `tipo`, `cita_a`, `cita_b` y `observaciones`; sin `document_id` ni `passage_id` |
| `ForensicReport` | CAMBIA: sin dependencia de TruthFrame |
| `ModelGateway` | CAMBIA: pasa de `judge`/`embed` a `generate(papel, mensajes, esquema)`, con adaptadores nativos y compatible con OpenAI; sale `embed` |
| `IntegrityPolicy` | SE MANTIENE: las fuentes literales del escáner pasan a ser los turnos |
| Nuevos | Biblioteca **IncoherenceAnalyzer** (núcleo y CLI), **ExecutionProfile**, **Provider**, **ModelCall**, **ConductorObservation** |
| Precisión de Domain Design (DD-10, 2026-11-07) | El trabajador `semantic-agent` aparece en el catálogo como **AnalysisWorker**, envoltura de cola sin reglas propias que sustituye a `SemanticEvaluation`. La verificación de citas vive dentro de **IncoherenceAnalyzer**, no como componente aparte, y la CLI es el componente **AnalyzerCli** |
| Frontera del clúster (AUTONOMIA-04) | SE REESCRIBE: proveedores externos solo vía el anonimizador |
| ADR-002, 003, 004, 007, 009 | SE MANTIENEN |
| ADR-001 | SE MANTIENE (sin TruthFrame) |
| ADR-005 | CAMBIA: el destino externo pasa a ser permitido detrás del anonimizador |
| ADR-006 | CAMBIA: la instantánea del umbral pasa a ser instantánea del perfil |
| ADR-008 | SE MANTIENE |
| ADR nuevos | Biblioteca sin infraestructura (DT26). Contrato común como fuente externa (en el repositorio principal). Perfiles por PR. |

### 2.5 Unidades — `I/inception/units-generation/`

| Unidad | Veredicto |
|---|---|
| U1 contracts | CAMBIA: contrato común, perfiles, interfaz de modelos; salen C4 y C9 |
| U2 platform | CAMBIA: sin `pgvector` ni *embeddings*; red y `Secret` nuevos; el juez local queda como modelo de demostración |
| U3 identity-access | Cambio menor: sale el umbral; entra la acción «elegir perfil» |
| U4 text-flow | **Se reduce**: pierde TruthFrame, la guardia, el paquete y los *embeddings*. Conserva sesión, turnos, ingesta, sugerencias, escáner y la consola base. Las historias del flujo de texto se recomponen |
| U5 human-review | Cambio menor (campos protegidos, observaciones) |
| U6 session-lifecycle | CAMBIA: sale US1.2; importar transcripción; modo final |
| U7 forensic-report | CAMBIA: el reporte cita dos fragmentos |
| U8 assistant-extras | Se reduce: aclaración neutra y permutación por definir; sale el indicio afectivo |
| U9 voice | SE MANTIENE (salvo la página) |
| U10 anonymizer | **COULD → MUST**; diseño de DT18; sale del condicional |
| **Nueva** | **Biblioteca y CLI del analizador** (P3) |
| Grafo `unit-of-work-dependency.md` | CAMBIA: U10 pasa a ser dependencia del camino comercial; la biblioteca depende de U1 |

### 2.6 Contratos — `I/inception/contract-design/contract-summary.md`

| Contrato | Veredicto |
|---|---|
| C1 OpenAPI | CAMBIA: salen las rutas `/scenarios*` y el umbral; entran perfiles, importación, modo final y registro de modelos |
| C2 Cola de turnos | **SE REESCRIBE** con la entrada del contrato común (`transcripcion`, `modo`, `hasta_turno`, `desde_turno`, `perfil`). `previous_turns` (máximo 3) no basta: el modo incremental necesita la transcripción hasta `hasta_turno` (conflicto C2) |
| C3 Cola de resultados | **SE REESCRIBE** con la salida del contrato común (hallazgos, `observaciones_conductor`, `error.codigo`, registro de modelos) |
| **C4** Indexación | **SALE** |
| C5 Audio | SE MANTIENE |
| C6 Salida del juez | **SE REESCRIBE**: formato de contradicción del piloto, enum de 7 tipos |
| C7 Alerta | **SE REESCRIBE**: los 4 campos obligatorios pasan a `cita_a` y `cita_b` (cada una `{cita, turno, pagina}`), `tipo`, `hecho` y `observaciones` |
| C8 Vocabulario prohibido | SE MANTIENE (alcance del escaneo ampliado) |
| **C9** Pasajes | **SALE** |
| C10–C12 | SE MANTIENEN (C11 pierde `ScenarioReader`) |
| C13 ModelGateway | **SE REESCRIBE** (DT21) |
| C14 Servidores de modelos | CAMBIA: queda solo el servidor local; los comerciales tienen sus propias API |
| C15 Métricas AIR | CAMBIA o SALE (P13) |
| C16 Salud | SE MANTIENE |
| Nuevo | Esquema del **perfil de ejecución** y de su configuración efectiva |

### 2.7 Plan de Bolts — `I/inception/delivery-planning/`

- El orden del cambio (§7): contratos → biblioteca y CLI con un proveedor comercial → anonimizador
  → consola y revisión → reporte → voz. Reemplaza al actual: contratos → acceso → flujo de texto →
  plataforma → …
- La tarea previa P0.2 (Golden Dataset con escenario y HND) se rehace como conjunto sintético de
  contradicciones internas (P11).
- B10 (anonimizador condicional) entra al plan como MUST.
- La regla aprendida «la primera unidad del plan es el flujo de texto» queda superada (sección 5.5).

### 2.8 Diseño de Construction (3.1–3.4) por unidad — `I/construction/<unidad>/`

| Unidad | Lo que sale | Lo que cambia |
|---|---|---|
| U1 contracts | BR2.2, BR2.4, BR2.5, BR3.2, BR7.1; entidad Grade; `limits`: `scenario_*`; `checks/threshold.py`; NFR10.8 | Inventario §1; BR2.3, BR3.4, BR4.1, BR5.3, BR5.5, BR6.x; entidades de cola y de alerta; NFR1.1 (destinos externos); NFR10.7 (`transcript_max_chars` = 100 000); `checks/servers.py` |
| U2 platform | `veridicus-embeddings`, `VERIDICUS_EMBEDDINGS_URL`, rol `veridicus_judge_ro`, alerta `VeridicusAirThresholdProposal` | D1 y D5 (sin `pgvector`); política `internal-model-urls`; tabla de red §3; presupuesto de memoria §4; recarga del escenario §6; `create-secrets.sh`; humo. **Nuevo:** `Secret` de proveedores y scripts `sbatch` (dueño por decidir) |
| U3 identity-access | BR5.1–BR5.3 y F9 (umbral); acciones `upload_scenario` y `apply_threshold_change`; NFR11.2 | CI con PostgreSQL sin `pgvector`; acción «elegir perfil» |
| U4 text-flow | BR1.x–BR3.x, BR6.x, BR7.x, BR8.3, BR9.2, BR10.x, BR13.5; entidades Scenario…ThresholdConfig; F1, F2 y F9; componentes ScenarioCatalog, UploadScenarioDialog, HandoffPanel y UndocumentedNotice; D3–D6 y D16; NFR4.1, NFR9.x, NFR10.6, NFR10.11, NFR10.18, NFR11.3; métricas de *claims*, *handoff* y *embeddings*; nivel 2 por `port-forward` | BR4.1, BR8.x, BR9.1, BR11.x, BR12.x, BR13.2; D1 (juez de demostración), D7, D8, D10, D12; NFR3.1 (p95 ≤ 60 s), NFR3.10–3.12 (ventana de 12 288), NFR4.2 (temperatura 0), NFR5.2, NFR10.16 (429, bloqueos y proveedor alterno); `ai-eval-gate.yml` y `eval-level2.sh` |
| U5 human-review | — | Campos protegidos al editar; «observaciones consultadas»; NFR10.4 (SHA-256 de los nuevos campos); AIR (P13) |
| U6 session-lifecycle | BR1.x (versiones de escenario), F1, NFR3.5, NFR9.1, NFR8.12, NFR10.7, T8, NFR11.1, D8 | BR2.x (pegado con hablante y página), BR2.3 (límite), BR2.6 (equivalencia, pasa a final frente a incremental), BR3.1; NFR8.3 (60/200 turnos, 100 000 caracteres) |
| U7 forensic-report | `scenario_version_id`, `scenario_sha256`, `similarity_threshold`, `undocumented_facts`, `ScenarioReader` | BR3.1, BR3.3, BR6.3; cota de 2 MiB y caso de 100 turnos |
| U8 assistant-extras | BR3.x (afectivo), D7, NFR3.11, NFR10.10, `veridicus_affective_notes_total` | BR1.x (permutación), BR2.1–BR2.2 (DT23); NFR3.1 (≤ 150 s), NFR4.3–4.4 |
| U9 voice | Convivencia con `model-embeddings` | D12 (clips del Golden Dataset); C13 generalizado; declarar que Whisper y TTS siguen siempre locales |
| U10 anonymizer | BR1.4 (*embeddings*), NFR1.4, NFR9.1, numeración por escenario | Pasa a MUST; BR1.1–BR1.3 (DT18, NER más reglas, marcas por entrevista); D1, D2, D4, D5; NFR1.5, NFR1.8, NFR10.5–10.6 (varios proveedores y credenciales). **Nuevo:** restaurar la cita antes de verificarla y detectar marcas alteradas |

Los hallazgos abiertos aceptados como riesgo en las revisiones (`reviews/`) de las unidades que cambian
se revisan otra vez en sus etapas.

### 2.9 Plan de tareas de U1 — `I/construction/contracts/code-generation/code-generation-plan.md`

| Paso | Veredicto |
|---|---|
| Decisiones PD-1 a PD-5 | PD-1 se rehace (las precisiones de U4, U6, U8 y U10 cambian); PD-3 y PD-4 se mantienen; PD-5 cambia (C14 reducido); PD-2 se mantiene |
| 1–4 Estructura, ejecutor, cargadores, validadores | SE MANTIENEN |
| 5 Pruebas en rojo de contratos y guardias | CAMBIA: *fixtures* del contrato común; AUTONOMIA-04 (destino externo solo con el anonimizador); AUTONOMIA-05 (alerta rechazada sin una de sus dos citas o con tipo fuera del enum) |
| 6 Colas C2–C5 | CAMBIA: C2 y C3 con el contrato común; sale C4; `checks/result_invariants.py` se rehace (error ⇒ hallazgos vacíos) |
| 7 Esquemas C6 y C7 | CAMBIA: formato de contradicción y 7 tipos |
| 8 Vocabulario y rótulos | CAMBIA: rótulos por tipo; salen `semantic_incongruence` y `undocumented_fact` |
| 9 Errores y límites | CAMBIA: códigos `bloqueo_contenido` y `proveedor`; límites sin escenario; `transcript_max_chars` (conflicto C2) |
| 10 Formato de fecha | SE MANTIENE |
| 11 OpenAPI de C1 | CAMBIA: rutas de perfil, importación, modo final y registro de modelos |
| 12 C9, C14, C15, C16 | CAMBIA: sale C9; C14 reducido; C15 según P13 |
| 13–19 | SE MANTIENEN en su forma |
| Nuevo | Esquema del perfil de ejecución. Si P3 = B, también el paquete Python del contrato común, que la biblioteca y `sistema` reutilizan |

---

## 3. Conflictos que el cambio no resuelve

### 3.1 Con lo aprobado o con la técnica

| # | Conflicto | Dónde | Pregunta |
|---|---|---|---|
| C1 | **Ventana del juez local.** El juez de demostración (Qwen2.5-7B Q4) corre con `--ctx-size 12288` y un bloque de ≤ 6 000 *tokens*. Su ventana nativa es de 32k. Las entrevistas del piloto van de ~10 000 a ~186 000 caracteres (≈ 3k–55k *tokens*). El modo final no cabe en el juez local, y el cambio admite fragmentos con solapamiento (DT02), pero no fija su tamaño ni cómo se detectan las contradicciones entre fragmentos. | U2 D1; U4 D1, D7, NFR3.11–3.12 | P14 |
| C2 | **Límites de tamaño.** `transcript_max_chars` = 100 000, 60/200 turnos, 2 000 caracteres por turno y un reporte de 2 MiB quedan por debajo del corpus. En modo incremental, C2 lleva solo 3 turnos previos, pero el analizador necesita la transcripción hasta `hasta_turno`. Eso hace crecer el mensaje de Redis y el *prompt* en cada turno. | U1 `limits`; U6 NFR8.3; U7; C2 | P14 |
| C3 | **Latencias sin recalcular.** p95 ≤ 60 s por turno, ≤ 150 s en U8, un plazo de 300 s × n y humo en 120 s suponían un juez local sobre un turno. Ahora se suman juez, verificador, anonimizador y red, y el *prompt* crece. | U4 NFR3.1; U8 NFR3.1; U6 NFR3.10 | Se fijan en NFR Requirements |
| C4 | **Sin criterio de calidad local.** Las 4 contradicciones aceptadas del piloto «no sirven para medir» y la medición es del repositorio principal. Sin otro conjunto, nada en este repositorio puede fallar por calidad: choca con AUTONOMIA-02 y con el nivel 2 de `team.md`. | NFR4; `team.md` Testing Posture | P11 |
| C5 | **Repetibilidad.** Temperatura 0 y semilla fija no garantizan repetir el resultado con proveedores comerciales, que además usan esfuerzo o razonamiento. | U4 NFR4.2; `team.md` nivel 2 | P15 |
| C6 | **`NetworkPolicy` por dominio.** La `NetworkPolicy` de Kubernetes y Calico OSS solo filtran por IP o CIDR. El filtro por FQDN exige otro CNI, Calico Enterprise o un proxy de salida. U10 ya lo tenía como riesgo T15. | U2 §3; U10 | P10 |
| C7 | **Perfil en manos del analista.** Que el analista elija el perfil choca con la regla aprobada de que la configuración que afecta a la IA solo cambia por PR (umbral, extras) y deja que un analista decida si un testimonio sale, seudonimizado, a un proveedor comercial. | U3, U8 NFR10.9/11.4; AUTONOMIA-04 | P8 |
| C8 | **Anonimizador «comercial».** El cambio §5 deja elegir proveedor comercial o local también para el anonimizador, pero un anonimizador comercial recibiría el texto sin seudonimizar. DT19 dice «el seudonimizador es siempre local». Tampoco está claro si con el perfil `todo-local` el anonimizador sigue siendo obligatorio. | Cambio §5 frente a DT19 | P9 |
| C9 | **Turnos sin página.** El contrato exige `pagina` y `pagina_fin`. Los turnos escritos, pegados o dictados en la consola no tienen página. Además, el verificador del piloto comprueba la cita también contra la página del PDF original (`tg.db`), que Veridicus no tiene. | Contrato §4; US2.2, US2.3, US10.2 | P4, P5 |
| C10 | **Modo final frente a incremental en la consola.** No se dice quién lanza el modo final, si conviven los hallazgos de ambos modos ni cuál consolida U7. La equivalencia aprobada «pegar = turno a turno» (U6 BR2.6) deja de ser verificable. | U6, U7 | P6 |
| C11 | **Qué consolida el reporte.** El cambio §2 dice «consolida solo lo que el analista aceptó»; lo aprobado (U7 BR3.1) incluye todas las sugerencias con su estado final. | U7 | P16 |
| C12 | **Qué se permuta.** La permutación se conserva, pero ya no hay pasajes que invertir. | U8 BR1.x; NFR5-C | P12 |
| C13 | **Datos reales en Minikube.** `project.md` prohíbe datos reales en el repositorio y en la CI, pero no en el clúster local. No está dicho si la consola puede importar entrevistas del piloto para la demostración o solo la CLI, fuera de Git. | `project.md` Forbidden; NFR12 | P7 |

### 3.2 Con las reglas del curso

| # | Conflicto | Propuesta |
|---|---|---|
| K1 | La guía del módulo 5 y `plan-aidlc.md` §1 paran antes de escribir código («nunca `Approve Plan`»), y `team.md` lo prohíbe en `## Forbidden` y `## Mandated`. DT27 levanta el alto. | Que la entrega del módulo 5 conste en el historial (commit `9ea5300`) y que el levantamiento entre como cambio documentado: `plan-aidlc.md` §1 y `team.md` (sección 5). Se mantiene «Review each checkpoint» y una aprobación por etapa. |
| K2 | PVB y PRD son entregables ya presentados en clase (módulos 2 y 3). Corregirlos cambia lo entregado. | Corregir los originales (regla de `plan-aidlc.md` §3) con una nota de iteración que diga qué cambió y por qué. La versión entregada queda en Git (P17). |
| K3 | Regla del curso: «toda cifra lleva fuente con enlace y fecha». Las decisiones DT y los resultados del piloto están en un repositorio privado. | Citarlas por ID con `[INTERNO]`. Las cifras que pierden sustento se retiran o se marcan `[VERIFICAR]`, sin inventar fuentes. |
| K4 | El repositorio del curso es público y el PRD apoyaba la soberanía en «ningún dato sale del clúster» (veto del CISO del ICP). | La nueva AUTONOMIA-04 sigue protegiendo el veto («nada sin seudonimizar sale») y el perfil `todo-local` conserva la opción sin salida. Se declara en el PRD que el riesgo de reidentificación por el relato no desaparece (DT18). |
| K5 | Costo: los proveedores comerciales en el producto y en la evaluación no estaban en el presupuesto del curso. El tope de DT12 es del piloto del TG. | Que cada corrida registre los *tokens* y que la evaluación de nivel 2 declare su costo; el tope sale de DT12 [INTERNO]. |
| K6 | Los módulos 6–8 del curso piden el loop orquestador–codificador–revisor sobre `unidades-y-tareas.md` (Paso 5 de `plan-aidlc.md`), que nunca se generó. | Se reemplaza: con el alto levantado, la construcción la hace AI-DLC por Bolts; el Paso 5 sale del plan (ver sección 5.6). |

---

## 4. Vía para reabrir las etapas en AI-DLC 2.10.0

AI-DLC 2.10.0 no tiene un comando para «revisar» una etapa ya aprobada. Las dos vías reales son estas.

### Opción A — Revisar este intent desde 2.3 (ya posicionado)

El flujo ya está en 2.3 (sección 0). Se ejecutan de nuevo 2.3 → 2.4 → … → 3.4 con sus compuertas. Cada
etapa se apoya en su artefacto aprobado anterior y lo reescribe, con un commit `aidlc(<etapa>): …`.
Construction vuelve a recorrer etapa por etapa todas las unidades; las que no cambian (U3, U5, U9) se
reaprueban con cambios menores.

- **Ventajas:**
  - Una sola historia: el registro de auditoría, la memoria y los commits muestran el cambio sobre lo
    aprobado, que es lo que pide el curso (trazabilidad).
  - No hay que repetir 0.1–0.3 ni Practices Discovery.
  - Las reglas aprendidas en `project.md` se conservan y se corrigen en el sitio.
- **Inconvenientes:**
  - El estado ya se reinició: 2.3–3.5 aparecen pendientes aunque haya artefactos aprobados en disco.
    Si se abandona a medias, el intent queda incoherente.
  - Construction recorre las 10 (u 11) unidades en las 4 etapas aunque varias casi no cambien. Es el
    mayor costo en sesiones y cuota.
  - El artefacto anterior se sobrescribe; el diff de Git es la única comparación.
  - El intent conserva su nombre `veridicus-mvp` y su descripción inicial («No escribas código…»),
    que ya no describe el trabajo.

### Opción B — Intent nuevo que parte de los artefactos aprobados

Se archiva `261002-veridicus-mvp` tal como está (`/aidlc intent archive`) y se abre un intent nuevo
(por ejemplo, `analizador-incoherencias`) con `/aidlc --new-intent`. Su descripción citaría este
documento y los artefactos del intent anterior como insumos, y su plan de etapas se compondría con
`/aidlc compose`.

- **Ventajas:**
  - El intent anterior queda intacto y legible como «versión del curso hasta el módulo 5».
  - El nuevo tiene un nombre y una descripción correctos (incluido el levantamiento del alto).
  - Con `compose` se pueden omitir etapas que no aportan (por ejemplo, rehacer 2.5 completa) y
    elegir de nuevo el *scope* y la política de guardias.
- **Inconvenientes:**
  - Se repiten 0.1–0.3 y, en `classic`, Practices Discovery (2.2), salvo que `compose` la omita.
  - Las etapas no «revisan»: generan desde cero, y hay que pedirles en cada una que partan del
    artefacto del intent anterior.
  - La trazabilidad hacia lo aprobado pasa por referencias entre intents, no por el diff.
  - Dos intents en el espacio; los artefactos viejos siguen en el árbol y pueden confundir a los
    sensores de trazabilidad.

### Recomendación

**Opción A.** El cambio conserva la consola, la revisión, el reporte, la identidad, la voz y la
plataforma; es una revisión, no un producto nuevo. Lo que el curso evalúa es la trazabilidad de
cada etapa revisada con su compuerta y su commit, y eso lo da mejor el mismo intent. El costo de
Construction se reduce si en 3.1–3.4 las unidades que no cambian solo registran sus precisiones
(P2 decide si se intenta así).

---

## 5. Correcciones propuestas a los originales

Cada bloque va en su propio commit tras tu aprobación. El texto entre comillas es la propuesta;
lo demás es contexto.

### 5.1 `docs/limite-autonomia.md` (commit `docs(autonomia): …`)

**AUTONOMIA-01, 02 y 03:** sin cambios de regla. Dos precisiones de verificación:

- AUTONOMIA-01, nueva viñeta: «Ningún plan de tareas envía trabajos al clúster ZINE ni a otro
  clúster de cómputo: los scripts `sbatch` y su paquete de entrada son artefactos revisables que el
  humano lanza (DT26)».
- AUTONOMIA-03, primera viñeta: «…y el escaneo de etiquetas de veracidad cubre las observaciones
  del hallazgo y las observaciones al conductor, excluyendo solo las dos citas literales».

**AUTONOMIA-04 (se reescribe):**

> ## Rule AUTONOMIA-04: Ningún dato sin seudonimizar sale del clúster
>
> **Rule**: (PRD Segmento 6, Principio 3; DT18, DT21) Ningún componente puede enviar fuera del clúster
> local audio crudo, transcripciones sin seudonimizar, nombres de víctimas ni identificadores reales
> del proceso. Un proveedor comercial solo recibe texto que pasó por el anonimizador. Si el
> anonimizador falla, la llamada no sale (falla cerrado). El anonimizador corre siempre dentro del
> clúster.
>
> **Verification**:
> - El diseño de aplicación declara, para cada componente, si corre dentro o fuera del clúster y qué
>   datos cruzan esa frontera.
> - Un destino externo en la configuración de modelos exige el adaptador anonimizador delante; si no
>   lo tiene, el servicio no arranca (prueba de arranque con un control negativo).
> - Toda tarea que integre un proveedor externo incluye una prueba de que el *payload* saliente pasó
>   por el anonimizador (sin nombres ni ubicaciones del conjunto de prueba) y otra de que, si el
>   anonimizador falla, no sale ninguna llamada.
> - Existe una tarea que produce la `NetworkPolicy` que niega la salida a internet a todos los pods
>   salvo al anonimizador, y a este solo hacia los proveedores configurados (artefacto revisable, ver
>   AUTONOMIA-01).
> - Las claves de API viven en un `Secret` que crea el humano; nunca en el repositorio ni en el
>   archivo de configuración.

**AUTONOMIA-05 (se reescribe):**

> ## Rule AUTONOMIA-05: Sin dos citas verificadas no hay hallazgo
>
> **Rule**: (PRD Segmento 6, Principio 4; DT04, DT09, DT15) Todo hallazgo de contradicción presenta
> dos citas literales de la misma transcripción, cada una con su turno y su página (si el turno la
> tiene), más el hecho, el tipo y las observaciones. Antes de que el hallazgo salga del analizador,
> una verificación determinista comprueba que cada cita existe en su turno; si el texto pasó por el
> anonimizador, la cita se restaura primero y se verifica después. Una cita que no aparece invalida
> el hallazgo. Un error del analizador nunca deja un resultado parcial. Las vaguedades, las emociones,
> los detalles periféricos y las versiones de terceros no son contradicciones.
>
> **Verification**:
> - El esquema de un hallazgo tiene como campos obligatorios `hecho`, `tipo` (uno de `fecha`,
>   `numero`, `lugar`, `persona`, `negacion`, `secuencia`, `otro`), `cita_a`, `cita_b` y
>   `observaciones`; un hallazgo sin cualquiera de ellos se rechaza por validación.
> - Existe una prueba con una cita alterada (y otra con una cita en un turno equivocado) que verifica
>   que el hallazgo no sale del analizador.
> - Existe una prueba que verifica que `estado: error` implica una lista de hallazgos vacía.
> - Existe una prueba de que la cita seudonimizada se restaura antes de verificarse.

### 5.2 `aidlc/spaces/default/memory/team.md`

`## Mandated` y `## Forbidden` se escribieron a mano en el Paso 0 y se corrigen igual, en el mismo
commit `docs(autonomia): …`. Las secciones de prácticas (Walking Skeleton, Testing Posture,
Deployment) son de Practices Discovery; cómo se cambian lo decide P2.

**`## Forbidden`:**

- AUTONOMIA-04: «NEVER enviar fuera del clúster local audio crudo, transcripciones sin seudonimizar,
  nombres de víctimas o identificadores reales del proceso; NEVER llamar a un proveedor externo sin
  el anonimizador delante o si este falla».
- AUTONOMIA-05: «NEVER emitir un hallazgo de contradicción sin sus dos citas literales verificadas en
  su turno, ni un resultado parcial cuando el analizador falla».
- **Se retira:** «Proceso: NEVER escribir código de aplicación en este trabajo… nunca se responde
  `Approve Plan`» (DT27).
- **Se añade:** «Proceso: NEVER copiar al repositorio entrevistas, fragmentos, codificaciones ni
  revisiones del piloto del TG, ni usar la partición `referencia`; las pruebas usan transcripciones
  sintéticas y los resultados de corridas sobre el corpus se escriben fuera de Git».
- **Se añade:** «AUTONOMIA-01: NEVER enviar trabajos a ZINE ni a otro clúster de cómputo».
- Se mantiene: «Proceso: NEVER elegir ni proponer autonomía en Construction».

**`## Mandated`:**

- AUTONOMIA-04 y AUTONOMIA-05: el texto de las nuevas «Verification» de 5.1, en forma «ALWAYS …».
- **Se añade:** «Proceso: ALWAYS `Approve Plan` solo lo elige el humano, después de revisar el plan de
  tareas regenerado de la unidad; la construcción sigue por Bolts con «Review each checkpoint»».
- Se mantiene: «una aprobación humana por etapa».

**Prácticas (según P2):**

- **Walking Skeleton:** «la primera rebanada de valor es la biblioteca del analizador con su CLI y un
  proveedor comercial, sobre transcripciones sintéticas (y, fuera de Git, las 10 del piloto); la
  consola viene después». Quita «consultar `pgvector`».
- **Testing Posture:**
  - El nivel 2 pasa a ser la CLI contra el perfil, en la anfitriona o en ZINE, sobre el conjunto
    sintético de P11.
  - Salen «trazabilidad factual», «Hecho No Documentado» y «permutación offline» en su forma actual.
  - El mapa AUTONOMIA-04/05 se alinea con 5.1.
  - La prueba de humo pasa a «contradicción sembrada ⇒ ≥ 1 hallazgo con dos citas; relato coherente ⇒
    0 hallazgos».
  - Los *fakes* del `ModelGateway` se mantienen en los niveles 0 y 1.
- **Deployment:**
  - Claves de proveedores en un `Secret`.
  - La `NetworkPolicy` con salida solo para el anonimizador.
  - Los artefactos de modelo locales se mantienen.

### 5.3 `aidlc/spaces/default/memory/project.md`

**`## Decided`** se reescribe:

> - **QUÉ:** Veridicus es el **analizador de incoherencias** del Trabajo de Grado *Diálogos para la
>   Memoria* (DT27): detecta contradicciones dentro del relato sobre hechos centrales, con dos citas
>   literales verificadas, y las propone como sugerencias de revisión en la consola del analista. La
>   fuente única de requisitos es `specs/prd.md` (con `pvb.md`); el contrato común del analizador vive
>   en el repositorio principal del TG y aquí se implementa en U1.
> - **POR QUÉ:** el mismo código sirve al producto del curso y a la app `sistema` del TG (DT20), sin
>   veredictos de veracidad (DT15) y sin que salga del clúster ningún dato sin seudonimizar (DT18).
> - **CÓMO:** biblioteca de Python con CLI sin infraestructura (DT26), que `semantic-agent` envuelve;
>   modelos comerciales y locales por papel con perfiles de ejecución (DT21); microservicios en
>   Minikube local para el producto; evaluación de modelos locales por lotes en el clúster ZINE
>   (SLURM, CPU), con scripts que el humano revisa y lanza. El repositorio es público.

**`## Forbidden`:** se añade la regla del piloto y la referencia de 5.2, si P2 prefiere tenerla aquí
y no en `team.md`.

**`## Testing Posture`:** se retira la regla aprendida «la evaluación de nivel 2 corre desde la
anfitriona con `kubectl port-forward`…» (la reemplaza el cambio §6).

**`## Corrections`:** las reglas aprendidas que el cambio deja obsoletas **no se borran a mano** (el
ritual de aprendizajes solo añade). Se propone una línea nueva que las supere:

> - El cambio 01 (DT27, `docs/iteracion2.md`) supera las reglas aprendidas sobre el marco de verdad,
>   el umbral de similitud, el Hecho No Documentado, el Paquete de Contexto de Traspaso, las tres
>   calificaciones, la indexación de escenarios, los *embeddings*, el indicio afectivo, el orden «flujo
>   de texto primero» y la evaluación por `port-forward`; donde contradigan el cambio, manda el cambio.

Las reglas afectadas son:

- **Obsoletas:** calificación de tres valores; alerta solo si es incongruente y supera el umbral;
  CoT interrumpida; panel no modal del paquete; indexación en `session-api`; US10.6 en `platform`;
  plataforma tras el flujo de texto; orden sin WSJF; U4 como primera rebanada; paquete por intento;
  dos lecturas ⇒ no documentada; *embeddings* enmascarados; un llamado al juez por turno; indicio
  afectivo; marcadores por llamada.
- **Por precisar:** Golden Dataset como tarea previa; líneas del entrevistador no evaluadas; una
  ranura y un turno a la vez; reintento del juez solo ante 502/503/504; *prompt* dentro del chart;
  Minikube de 28/20 GiB; escáner `scan(text, literal_sources)`.

Si prefieres limpiar en lugar de superar, es una decisión tuya (P18).

### 5.4 `pvb.md` (y su copia `docs/pvb.md`, en el mismo commit `fix(pvb): …`)

Propuesta **mínima** (P17). El PVB ya dice que, donde difiere, manda el PRD.

1. **Nota bajo el encabezado:**
   > **Nota (2026-10-27, DT27) [INTERNO]:** Veridicus detecta contradicciones **dentro** del relato
   > sobre hechos centrales, con dos citas literales verificadas. Ya no contrasta el relato con un
   > marco de verdad documental ni analiza emociones o estilo (DT15). Usa modelos comerciales y
   > locales por papel, siempre tras un anonimizador que falla cerrado (DT18). Las menciones que queden
   > a marco de verdad, `pgvector`, detección de engaño o LieXBerta son históricas; manda
   > `specs/prd.md` (Iteración 6).
2. **Producto (L18):** «Es un sistema multiagente de entrevista asistida por IA que, mientras el
   compareciente relata, detecta contradicciones dentro de su relato sobre hechos centrales, cada una
   con dos citas literales verificadas, y las propone como sugerencias de revisión a analistas de
   justicia transicional».
3. **Frases que contradicen DT15 y se corrigen aunque la corrección sea mínima:**
   - «evaluar veracidad» (L25).
   - El pilar LieXBerta (L55): pasa a «contrato común con el TG».
   - «detección de engaño… estilométrico/emocional» (L67).
   - La métrica de detección de engaño (L134): pasa a «citas verificadas en lo mostrado: 100 %».
   - «detectar mentiras… calibración estilométrica» (L146–151).

Si eliges la corrección **completa**, el inventario línea por línea está listo (unas 25 líneas más:
L37, L53, L54, L69, L84, L96, L115, L130, L135, L143, L186, L195…).

### 5.5 `specs/prd.md` (commit `fix(prd): …`)

Correcciones **necesarias** (contradicen el cambio), por segmento:

| Segmento (líneas) | Propuesta |
|---|---|
| S1 One-liner (L10) | «**Veridicus** es un sistema de entrevista forense asistido por microservicios de IA que ayuda a analistas de justicia transicional a detectar contradicciones dentro del relato de un compareciente sobre hechos centrales, cada una sustentada en dos citas literales verificadas de la propia transcripción. Propone hallazgos como sugerencias de revisión, sin veredictos de veracidad y sin juzgar emociones ni estilo». |
| S1 JTBD (L13–15) | «…**quiero** que el sistema me señale, turno a turno o al cierre, las contradicciones objetivas del relato sobre hechos centrales, cada una con sus dos citas verificadas, **para** revisarlas y decidir sobre cada una sin releer la entrevista completa…». |
| S1 Misión (L18) | «…ningún dato sin seudonimizar sale del clúster…», «…al señalar las contradicciones internas de los relatos con dos citas verificadas…». |
| S2 (L27, L35, L39, L44, L47) | El dolor pasa a «relectura para localizar contradicciones entre pasajes distantes» `[VERIFICAR]`. La UNESCO «orienta», no «prohíbe» `[VERIFICAR]`. APIs comerciales solo tras el anonimizador. «Ya resuelto»: PostgreSQL con CloudNativePG y servidores compatibles con OpenAI (sin `pgvector`). Competencia: *scripts* que no verifican citas. |
| S3 (L61, L76, L80) | Dolor del analista: relectura de entrevistas largas. Objeción 1: «no se muestra ningún hallazgo cuyas dos citas no aparezcan literalmente en sus turnos». Objeción 3: «Veridicus no interpreta el estilo ni las emociones (DT15)». |
| S4 (L91–97) | Ítem 2: «Detecta contradicciones internas…». Ítem 3: «Protege los datos por diseño: anonimizador que falla cerrado». Sin «soberanía absoluta» ni LieXBerta. |
| S5 CU1 (L126–135) | «Carga de la transcripción y elección del perfil de modelos»; KPI `[INTERNO]`, lo fija NFR Requirements. |
| S5 CU2 paso 3 (L147) | Aclaración neutra sobre tema y turnos; nunca menciona la contradicción (DT23). |
| S5 CU3 (L154–163) | Se reescribe: modo incremental → el juez propone → verificación determinista de las dos citas (restaurando si hubo seudonimización) → sugerencia pendiente. |
| S5 CU4 (L167–178) | Sale el caso afectivo. Lo reemplaza «Revisión de una contradicción con sus dos citas». |
| S5 CU5 (L188) | El reporte alinea cada hallazgo con sus dos citas (turno y página), tipo y observaciones. |
| S6 P1, P2 (L199, L204) | «Cada hallazgo de contradicción…»; «…Whisper o el juez del analizador…». |
| **S6 P3 (L207–210)** | Título «Soberanía de los datos identificables». (b): Whisper y PostgreSQL en el clúster; juez, verificador y anonimizador por perfil; el anonimizador siempre local y con fallo cerrado; claves en `Secret`. (c): prohibido que salga un dato sin seudonimizar o que arranque un destino externo sin el anonimizador. |
| **S6 P4 (L212–215)** | Título «Evidencia verificable: sin dos citas no hay hallazgo». (b) y (c) con el texto de la nueva AUTONOMIA-05. |
| S7 J1 (L224, L227) | «Carga la transcripción y elige el perfil»; ejemplo neutro de contradicción de lugar entre dos turnos. |
| S7 J2 (L234–235) | `NetworkPolicy` con salida solo para el anonimizador; respaldo de la base de sesiones, no del «marco de verdad». |
| S7 J3 (L239) | «…transcripciones y hallazgos…». |
| **S7 J4 (L243–252)** | Se reescribe como «La IA no puede sustentar un hallazgo»: relato vago (no es contradicción), cita no verificable (descartada antes de salir), fallo del analizador (`error`, sin parcial, proveedor alterno), fallo del anonimizador (no sale) e intervención humana. |
| **S8 MoSCoW (L259–291)** | MUST: entrada en turnos con página, **analizador** (biblioteca y CLI, contrato común, modos final e incremental), **verificación de citas**, **anonimizador**, perfil por papel `[VERIFICAR: prioridad en 2.3]`. Sale el «Agente de Validación Semántica Local (RAG)». SHOULD: textos de progreso, aclaración neutra, permutación redefinida. El clasificador afectivo pasa a WON'T. WON'T nuevos: contraste documental (PU-17, DT24) y análisis afectivo o estilométrico (DT15). WON'T GPU: la calidad de modelos locales se mide en ZINE. Datos: solo sintéticos en el repositorio. Plataforma sin `pgvector`. |
| S9 (L304–394) | Módulo A: carga de transcripción y selector de perfil. Módulo D: analizador de incoherencias con el `ModelGateway` de DT21. Módulo E: PostgreSQL relacional; el recuadro `pgvector` queda superado. Diagrama: anonimizador MUST y proveedores por papel, sin búsqueda vectorial. |
| S10 (L408, L419–424, L432) | KPI de activación sin consulta vectorial. Salen las métricas LieXBerta y Szojka. Entran «0 % de aclaraciones que mencionen la contradicción», «100 % de citas verificadas» y «precisión medida fuera del producto (DT09)». AIR sin umbral (P13). |
| S11 (L438–476) | Conjunto sintético de contradicciones internas y casos trampa (cantidades `[INTERNO]`). La adherencia factual pasa a citas verificadas. Escenario B con juez y verificador de familias distintas. Escenario C con permutación redefinida. Nueva subsección «Evaluación por lotes en ZINE». |
| S12 (R1, R5–R10) | Sin LieXBerta. R5 con fallo cerrado y marcas alteradas. R6: «Posible contradicción». R7: testimonio como dato y citas verificadas fuera del modelo. R8: caché del proveedor. R10 nuevo: bloqueo de contenido o caída del proveedor. |
| S13 (L506–533) | Sin `pgvector` ni escenario. Anonimizador MUST en el módulo 7. `Secret` de claves. La sustentación carga una transcripción sintética. |
| **Anexo, Iteración 6** | «**De contrastador documental a analizador de incoherencias del TG** (2026-10-27, DT27). *Conflicto:* construir Veridicus aparte de *Diálogos para la Memoria* duplicaba esfuerzo, y el TG necesita contradicciones dentro del relato, no contraste con documentos externos [INTERNO]. *Decisión:* contrato común como biblioteca de Python y CLI (DT17, DT26); salen el marco de verdad, `pgvector`, el umbral, el Hecho No Documentado, el paquete, las tres calificaciones y todo análisis afectivo o estilométrico (DT15); evidencia = dos citas verificadas; soberanía = nada sin seudonimizar sale del clúster, con el anonimizador MUST y fallo cerrado (DT18); calidad de modelos locales por lotes en ZINE (DT26). El diseño anterior queda en el historial de Git». |

**Opcionales** (desactualizadas, sin contradicción): el título («…Análisis de Incoherencias del
Relato»), el eje del cuadrante (L109–117), el «¿Por qué ahora?» (L33), el MTTV como `[INTERNO]`, el
Likert sobre observaciones, el ejemplo de inyección (L465), la referencia [19] y el orden de Bolts
en S13.

**Cifras que pierden sustento** y se retiran o se marcan:

- «< 3 min» de preparación del escenario.
- La composición 4 + 6 (2/2/2) + 1 HND del Golden Dataset.
- El 100 % de trazabilidad a pasajes (la cifra sigue, pero mide otra cosa).
- Las cifras de LieXBerta (87,50 %, 87,13 %, +6,5 %, «> 85 % de exactitud afectiva»).
- La «propuesta de umbral» del AIR.
- Las métricas Szojka.
- El COGS del PVB (suponía inferencia local).

### 5.6 `plan-aidlc.md` (commit `docs(plan): …`)

- **Encabezado:** «Veridicus · Módulo 5 → construcción · AI-DLC v2.10.0». Nota: «Desde el cambio 01
  (DT27, `docs/iteracion2.md`), Veridicus es el analizador de incoherencias del TG y el alto antes de
  la Parte 2 está levantado». El contenedor pasa a ser `tg-veridicus`.
- **§1 Meta y punto de parada:** se reemplazan el diagrama y el aviso. Propuesta:
  ```mermaid
  flowchart LR
      IN["pvb.md + specs/prd.md<br/>(corregidos, iteración 6)"] --> INC["Inception<br/>revisada desde 2.3"]
      INC --> CON["Construction por unidad<br/>diseño 3.1 a 3.4"]
      CON --> CG["3.5 Parte 1: plan de tareas"]
      CG --> OK{{"Approve Plan<br/>solo el humano, tras revisar"}}
      OK --> B["Parte 2: Bolts<br/>Review each checkpoint"]
  ```
  Texto alternativo: los insumos corregidos alimentan la Inception revisada y el diseño por unidad.
  Cada plan de tareas lo revisa el humano y, cuando lo aprueba con `Approve Plan`, se construye por
  Bolts con una compuerta en cada punto de control.

  **Terminado cuando:** los Bolts del plan revisado cumplen su definición de terminado. Lo primero que
  sirve al TG es la biblioteca con su CLI y un proveedor comercial (cambio §8).
- **§2:** fila nueva «Insumos del TG | — | `/insumos` (solo lectura, fuera del repositorio): cambios
  numerados en `/insumos/app/cambios/`; solo el contrato común y los ID de decisión entran al
  repositorio». Y un recordatorio: el guardia de aprobación del plan bloquea toda escritura mientras
  el flujo esté en 3.5 sin `Approve Plan` (lección de esta sesión).
- **§3 Insumos:** añadir `docs/iteracion2.md` y el contrato común. Regla: nada de `/insumos` se
  copia, salvo el contrato y los ID.
- **§4 Mapa:** en 2.3–2.9 y 3.x, vigilar la nueva AUTONOMIA-04/05, el contrato común y los perfiles.
- **§5 Paso 4:**
  - Quitar «Nunca elegir `Approve Plan`» y el `--single` para generar planes sin construir.
  - Mantener «Review each checkpoint» y stage-major.
  - Añadir: «Los scripts `sbatch` de ZINE los lanza el humano».
- **§5 Paso 5 y §8 (consolidación y ruta corta):** salen. La construcción la hace AI-DLC por Bolts
  (K6).
- **§6:** se mantiene.
- **§7 Lista del plan de tareas:** cambia AUTONOMIA-04/05 por el texto nuevo y añade «ningún
  *fixture* contiene datos del piloto».

---

## 6. Preguntas para el autor

Responde debajo de cada `[Answer]:` (en la línea siguiente, como de costumbre) con la letra o con
texto propio. La opción recomendada va marcada.

### P1 — Vía para reabrir las etapas

A. Revisar este intent desde 2.3, que ya está posicionado (**recomendada**, sección 4)
B. Archivar este intent y abrir uno nuevo con `compose`, que parta de los artefactos aprobados
C. Revisar este intent, pero con `compose` en curso para omitir etapas sin cambios (p. ej., 2.5 si
   decides ajustar las maquetas a mano)
X. Other (please specify)

[Answer]:
A

### P2 — Cómo cambian las prácticas de `team.md` (Walking Skeleton, Testing Posture, Deployment)

A. Corregirlas a mano junto con `## Mandated` / `## Forbidden`, en el commit `docs(autonomia)`, y
   dejarlo anotado en la bitácora (**recomendada**: el cambio ya decide su contenido y reabrir 2.2
   repite un ensamble de tres agentes)
B. Volver a Practices Discovery (2.2) antes de 2.3, para que las reescriba en su compuerta
C. No tocarlas ahora; que 2.3 y NFR Requirements las precisen en `project.md`
X. Other (please specify)

[Answer]:
A

### P3 — Dónde vive la biblioteca del analizador y su CLI

A. Una unidad nueva (p. ej., U11 `incoherence-analyzer`, tipo `library`), que depende de U1 y es el
   segundo Bolt (**recomendada**: es lo primero que sirve al TG y se prueba sola)
B. Dentro de U1, junto al contrato común
C. Dentro de U4, que la envuelve
X. Other (please specify)

[Answer]:
A

### P4 — Página de los turnos que no vienen del corpus (escritos, pegados o dictados en la consola)

A. `pagina` y `pagina_fin` opcionales cuando `origen: guiada`; la cita de esos turnos se verifica
   solo contra el turno (**recomendada**: no inventa datos y deja el formato del corpus intacto)
B. Página virtual (p. ej., una por sesión o un número fijo de turnos por página)
C. Exigir siempre el formato con página: la consola solo importa transcripciones del corpus
X. Other (please specify)

[Answer]:
A

### P5 — Entrada de texto en la consola

A. Se mantienen el turno a turno y el pegado de texto libre (origen `guiada`, hablante elegido por el
   analista) y se añade la importación del JSON del corpus (**recomendada**)
B. Solo importación de transcripciones en el formato del contrato
C. Solo turno a turno; el corpus entra solo por la CLI
X. Other (please specify)

[Answer]:
A

### P6 — Modo final e incremental en la consola

A. El incremental corre por turno. El final se lanza con un botón tras «Finalizar sesión»; sus
   hallazgos se unen con los del incremental, sin duplicar el mismo par de citas; consolidar exige
   que el final haya terminado (**recomendada**)
B. El final se lanza solo al finalizar la sesión; sus hallazgos reemplazan a los del incremental
C. En la consola solo el incremental; el final, solo por la CLI
X. Other (please specify)

[Answer]:
A

### P7 — Corpus del piloto dentro del producto

A. La consola en Minikube puede importar las 10 entrevistas del piloto para desarrollo y demostración
   en la máquina local, nunca en Git ni en la CI (**recomendada**)
B. Solo la CLI procesa el corpus; la consola usa solo transcripciones sintéticas
X. Other (please specify)

[Answer]:
A

### P8 — Quién elige el perfil de ejecución

A. Los perfiles se definen por PR (como antes el umbral). El analista elige uno de los aprobados al
   crear la sesión, que queda fijo; la consola muestra si el perfil usa un proveedor comercial
   (**recomendada**: conserva la gobernanza y cumple la historia «el analista elige el perfil»)
B. Un perfil fijo por despliegue; el analista no elige
C. El analista elige y además puede cambiar de perfil durante la sesión
X. Other (please specify)

[Answer]:
A

### P9 — El papel «anonimizador» y el perfil `todo-local`

A. El anonimizador es siempre local (DT19) y solo es obligatorio delante de destinos externos; con
   `todo-local` no interviene (**recomendada**)
B. El anonimizador es siempre local y todo texto pasa por él, aunque el destino sea local («el camino
   es uno solo»)
C. Se admite un anonimizador comercial (requiere precisar DT18 en el principal)
X. Other (please specify)

[Answer]:
A

### P10 — Salida a internet solo hacia los proveedores (Calico OSS no filtra por dominio)

A. `NetworkPolicy` con salida del anonimizador solo al puerto 443 y a DNS; la lista de dominios se
   impone en el propio anonimizador, con una prueba, y con la lista blanca de CoreDNS ya diseñada
   (**recomendada**: sin componentes nuevos)
B. Un proxy de salida (Squid o Envoy) con lista de dominios, como único pod con salida
C. `ipBlock` con los rangos publicados de cada proveedor
X. Other (please specify)

[Answer]:
A

### P11 — Criterio de calidad dentro de este repositorio (AUTONOMIA-02)

A. Un conjunto **sintético** nuevo, versionado en `evaluation/`: transcripciones con contradicciones
   internas sembradas de los 7 tipos, relatos coherentes y casos trampa (vaguedad, emoción, detalle
   periférico, terceros). Sus umbrales se fijan en NFR Requirements. Aparte, la CLI sobre el piloto,
   fuera de Git, como prueba de humo frente a las 4 contradicciones (**recomendada**)
B. Solo la prueba de humo con el piloto, fuera de Git; la calidad se mide solo en el principal
X. Other (please specify)

[Answer]:
A

### P12 — Qué se permuta

A. El verificador evalúa cada hallazgo candidato con las dos citas en ambos órdenes; se conserva solo
   si confirma en los dos (**recomendada**: es el sesgo de posición que mitiga)
B. Se analiza la transcripción en orden directo e inverso de fragmentos y se conserva la intersección
C. Sale la permutación
X. Other (please specify)

[Answer]:
A

### P13 — Indicador AIR (US10.6)

A. Se mantiene la métrica de razón de descartes en Grafana, como señal para revisar *prompt* o perfil
   por PR; sale la «propuesta de umbral» (**recomendada**)
B. Sale por completo con US10.6
X. Other (please specify)

[Answer]:
A

### P14 — Entrevistas largas con el juez local de demostración (ventana de 12k)

A. Para modelos locales, el modo fragmentado por turnos con solapamiento (DT02) es obligatorio y sus
   parámetros se fijan en NFR Requirements; la demostración en Minikube usa transcripciones sintéticas
   cortas (**recomendada**)
B. Subir la ventana del juez local (más memoria) y limitar la demostración a entrevistas que quepan
C. La demostración solo con un perfil comercial
X. Other (please specify)

[Answer]:
A

### P15 — Repetibilidad con modelos comerciales

A. Se registran esfuerzo, versión y semilla si el proveedor la admite; la repetibilidad se mide como
   acuerdo entre 3 corridas en el conjunto sintético, con umbral en NFR Requirements (**recomendada**)
B. Se exige temperatura 0 y semilla, y se excluyen los proveedores que no las admiten
X. Other (please specify)

[Answer]:
A

### P16 — Qué contiene el reporte consolidado

A. Todas las sugerencias con su estado final y nota, como está aprobado (**recomendada**: es la
   trazabilidad de la revisión)
B. Solo las aceptadas y editadas (lectura literal del cambio §2)
X. Other (please specify)

[Answer]:
A

### P17 — Alcance de la corrección del PVB

A. Mínima: nota de DT27, producto (L18) y frases que contradicen DT15 (**recomendada**: el PVB ya
   cede ante el PRD)
B. Completa, línea por línea (~25 líneas)
X. Other (please specify)

[Answer]:
A

### P18 — Reglas aprendidas obsoletas en `project.md`

A. Una línea nueva en `## Corrections` que las supera (5.3), sin borrar las anteriores
   (**recomendada**: respeta que el ritual de aprendizajes solo añade)
B. Borrarlas a mano en el commit `docs(autonomia)` y dejar la lista en este documento
X. Other (please specify)

[Answer]:
A

---

## 7. Lo que sigue tras tu aprobación

1. Commits de los originales: `fix(pvb): …`, `fix(prd): …`, `docs(autonomia): …` (con
   `limite-autonomia.md`, `team.md` y `project.md`) y `docs(plan): …`.
2. Reanudar el flujo en 2.3 (o el intent nuevo, según P1) y revisar cada etapa con su compuerta y su
   commit `aidlc(<etapa>): …`, con una pausa al cerrar cada una.
3. Regenerar el plan de tareas de U1 con el contrato común. Cuando lo revises, eliges `Approve Plan` y
   empieza la construcción por Bolts.
