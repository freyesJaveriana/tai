# Preguntas — Diseño del dominio (Veridicus)

Esta etapa define los **bloques lógicos** de software (componentes), qué entidad es dueña de cada dato y
cómo se llaman entre ellos. No decide todavía cuántos servicios se despliegan: eso lo hace Units
Generation.

Ya están decididos y no se vuelven a preguntar: la pila (FastAPI, React, PostgreSQL + `pgvector`,
Redis), los nombres orientativos de servicios de team-practices (`session-api`, `audio-worker`,
`semantic-agent`, `anonymizer-proxy`), que el usuario de base de datos del juez solo lee el marco de
verdad (AC3.3.2), que la guardia del umbral decide antes que el juez, que la revisión de alertas
pertenece a la versión del reporte (AC6.3.4) y que las invariantes de AUTONOMIA-03/05 viven como código
puro de dominio.

## Cómo responder

- Escribe la letra después de `[Answer]:`, en la misma línea o en la siguiente.
- La opción **(Recomendada)** es mi propuesta; no está aplicada todavía.
- Si ninguna opción encaja, usa `X` y escribe la tuya.

---

### Pregunta 1 — ¿Cómo se parte el núcleo de sesión, revisión y reporte?

Sesión, turnos, sugerencias de revisión y reporte cambian a ritmos distintos y tienen reglas propias:
la máquina de estados de la alerta y la consolidación con SHA-256 son módulos guardia con 100 % de ramas
(team-practices).

A. **Tres componentes**: `InterviewSession` (sesiones, turnos, suspensión y reanudación), `HumanReview` (sugerencias de revisión, sus decisiones e historial) y `ForensicReport` (consolidación, versiones del reporte, copia de trabajo y descarga) **(Recomendada)**
B. Dos componentes: `InterviewSession` (sesión y turnos) y `Review` (sugerencias, decisiones, consolidación y reporte juntos).
C. Un solo componente `Session` que lo contiene todo.
X. Other (please specify)

[Answer]: A

### Pregunta 2 — ¿Cómo vuelve el resultado de la evaluación de un turno?

El juez no puede escribir en ninguna tabla (AC3.3.2), así que el componente que evalúa no guarda por sí
mismo las alertas ni los Paquetes de Contexto de Traspaso; alguien más debe persistirlos.

A. **El evaluador publica un mensaje de resultado en la cola Redis** (con contrato versionado en `contracts/`) y el componente de sesión lo consume, valida y persiste de forma idempotente por ID de turno **(Recomendada)**
B. El evaluador llama a una API interna del componente de sesión para entregar el resultado.
C. El evaluador tiene un segundo usuario de base de datos, distinto del del juez, solo para escribir resultados.
X. Other (please specify)

[Answer]: A

### Pregunta 3 — ¿Dónde vive el rastro de auditoría (quién y cuándo)?

AC8.4.1 y AC8.4.2 exigen historiales que solo admiten inserciones, con actor y hora no nulos, para
alertas, consolidaciones, versiones de reporte, umbral de sesión y «CoT consultada».

A. **Cada componente es dueño del historial de sus propias entidades** (tablas de solo inserción junto a la entidad), con una convención común de columnas y una prueba común que verifica la restricción **(Recomendada)**
B. Un componente central `AuditTrail` recibe un evento por cada cambio y guarda todo en un solo registro.
C. Ambos: historial propio y, además, copia al registro central.
X. Other (please specify)

[Answer]: A

### Pregunta 4 — ¿Con qué componente habla la consola del analista?

La consola (React) muestra sesiones, escenarios, alertas, reportes y usuarios.

A. **Con un único componente de entrada** (la API de sesión, que actúa como fachada): la consola nunca llama directamente al evaluador, al transcriptor ni a la base vectorial **(Recomendada)**
B. Con cada componente por su cuenta (sesión, escenarios, usuarios, evaluación).
X. Other (please specify)

[Answer]: A

### Pregunta 5 — ¿Cómo se prepara el diseño para el anonimizador (COULD)?

AUTONOMIA-04 exige probar el *payload* saliente si alguna vez hay una llamada externa. En el MVP no hay
llamadas externas y el anonimizador es COULD.

A. **Toda llamada a un modelo (juez, *embeddings*, Whisper, TTS) pasa por un puerto propio (`ModelGateway`)**; hoy su adaptador apunta a modelos locales del clúster, y el anonimizador se añade más adelante como otro adaptador sin tocar el dominio **(Recomendada)**
B. No se modela nada hasta que se decida construir el anonimizador.
X. Other (please specify)

[Answer]: A

---

## Segunda pasada — cambio 01 (DT27) y adenda 02 (2026-11-06)

Las preguntas 1–5 siguen vigentes. Esta pasada revisa el catálogo por el cambio 01 (analizador de
incoherencias, `docs/iteracion2.md` §2.4) y por la adenda 02 del protocolo ético (VE-01 a VE-17,
`requirements-adenda-02.md`).

Ya están decididos y no se vuelven a preguntar:

- **Sale** `TruthFrame` (escenarios, pasajes, `pgvector`, umbral, Hecho No Documentado, Paquete de
  Contexto de Traspaso). Su ID queda «Retirado» en el catálogo, sin renumerar.
- La biblioteca del analizador **no depende** de Redis, Kubernetes ni base de datos, y `semantic-agent`
  es una envoltura delgada que la llama desde la cola (FR13.1, P3). Si la biblioteca es una unidad propia
  lo decide Units Generation.
- El anonimizador corre siempre dentro del clúster, solo interviene delante de destinos externos (P9),
  impone la lista de dominios (FR11.4, P10), restaura las citas antes de verificarlas (FR4.4) y falla
  cerrado (FR11.3). Es un módulo de la biblioteca y entra en la primera rebanada.
- `ModelGateway` pasa a `generate(papel, mensajes, esquema)` con adaptadores nativos y uno compatible
  con OpenAI; sale `embed` (FR15.1).
- Las decisiones A-1 a A-4 de la adenda 02 (aviso excluido del escáner, `Job` de retención como única
  vía de borrado, hash por exportación, consentimiento en el contrato común).
- Lo que fijó la validación en ZINE (AC14.1.7): en CPU el modo local es **por lotes**, la salida JSON se
  fuerza con `json_schema` y el verificador local solo lee citas, nunca la entrevista entera.

### Pregunta 6 — ¿Cómo se parte la biblioteca del analizador?

La biblioteca hace dos trabajos que cambian por razones distintas: **analizar** una transcripción
(juez, verificador, permutación, modo fragmentado y la verificación determinista de las dos citas, que
es un módulo guardia con 100 % de ramas) y **operarla desde la terminal** (lotes de archivos y el modo
evaluación, que calcula precisión, sensibilidad, acuerdo entre 3 corridas, costo y la tabla de sesgo de
VE-17 frente al conjunto sintético). `docs/iteracion2.md` §2.4 los proponía juntos («núcleo y CLI»).

A. **Dos componentes**: `IncoherenceAnalyzer` (el núcleo que implementa el contrato común, con la verificación de citas dentro) y `AnalyzerCli` (lotes y modo evaluación, que llama al núcleo igual que el trabajador) **(Recomendada)**
B. Un solo componente `IncoherenceAnalyzer` con la CLI y el modo evaluación dentro.
C. Tres componentes: núcleo, verificación de citas aparte (`QuoteVerification`) y CLI.
X. Other (please specify)

[Answer]: A

### Pregunta 7 — ¿Dónde vive el anonimizador frente a `ModelGateway`?

ADR-005 de la primera pasada decía que el anonimizador sería «otro adaptador» de `ModelGateway`. Desde el
cambio 01 tiene reglas propias (NER local más reglas, marcas coherentes en toda la entrevista, tabla de
correspondencia solo en memoria, detección de marcas alteradas, lista de dominios) y en el clúster es el
**único pod con salida a internet** (FR12.3). En la CLI corre en el mismo proceso.

A. **Componente propio `Anonymizer`**: `ModelGateway` lo llama antes de todo destino externo (seudonimiza la salida, restaura la respuesta y avisa de marcas alteradas); el núcleo recibe el texto ya restaurado y verifica las citas contra los turnos originales. En el clúster, ese mismo código es el pod `anonymizer-proxy` **(Recomendada)**
B. Adaptador dentro de `ModelGateway`, como decía ADR-005.
C. Lo orquesta el núcleo del analizador: seudonimiza la transcripción antes de llamar a `ModelGateway` y restaura después.
X. Other (please specify)

[Answer]: A

### Pregunta 8 — ¿Quién carga y valida los perfiles de ejecución?

Un perfil fija proveedor y modelo por papel, la permutación, el proveedor alterno y el modo fragmentado
(FR14.1); se valida igual en la biblioteca, la CLI y los servicios, que no arrancan con un perfil
inválido, un destino externo sin anonimizador o una clave de API que falta (FR14.3); exige familias
distintas en los perfiles de evaluación (FR14.4); calcula `config_sha256` (FR14.2); y la consola lista
los aprobados (FR14.5). Los perfiles solo cambian por PR (FR9.2).

A. **Componente propio `ExecutionProfiles`** (sin estado, lee el archivo versionado), que usan el núcleo, la CLI, el trabajador y `ConsoleApi` **(Recomendada)**
B. Dentro de `IncoherenceAnalyzer`.
C. Dentro de `ModelGateway`, junto a los proveedores.
X. Other (please specify)

[Answer]: A

### Pregunta 9 — ¿Quién guarda las corridas y el registro de llamadas a modelos en el producto?

La biblioteca no persiste nada: devuelve la salida del contrato con su registro de modelos (FR15.3). En
la consola hay que guardar cada corrida (modo, tramo, perfil, `config_sha256`, `prompt_sha256`,
estado, código de error) y sus llamadas (solo inserción, NFR11), y detectar el incidente de VE-14: una
llamada a un proveedor comercial **sin** anonimizar bloquea la sesión.

A. **`InterviewSession`**, al consumir el mensaje de resultado (como ADR-002): guarda `AnalysisRun` y `ModelCall`, pasa los hallazgos a `HumanReview` y, si detecta una llamada sin anonimizar a un proveedor comercial, bloquea la sesión y registra el incidente **(Recomendada)**
B. Un componente aparte `RunLedger` dueño de corridas y llamadas, que `InterviewSession` llama al ingerir el resultado.
X. Other (please specify)

[Answer]: A

### Pregunta 10 — ¿Cómo se reparte el protocolo ético (adenda 02)?

La adenda trae datos y reglas nuevas: reconocimiento del analista cada 90 días o al cambiar el texto
(VE-04), consentimiento y su retirada antes de capturar turnos (VE-06, VE-10), pausa y terminación
(VE-10), registro de acceso de solo inserción (VE-11), retención con borrado automático y acta (VE-12,
A-2), reporte de problemas sin texto del testimonio (VE-15) e incidentes de anonimización (VE-14).

A. **Dos componentes nuevos**: `EthicsGovernance` (reconocimientos, registro de acceso, reportes de problemas e incidentes) y `DataRetention` (el `Job` de retención: pide a cada componente dueño que borre lo suyo y guarda el acta). El consentimiento, su retirada y la pausa quedan en `InterviewSession`, porque condicionan cada turno **(Recomendada)**
B. Un solo componente `EthicsGovernance` con todo, incluidos el consentimiento y la retención.
C. Sin componentes nuevos: el reconocimiento en `IdentityAccess`, el acceso en `ConsoleApi`, la retención dentro de cada dueño y los problemas en `HumanReview`.
X. Other (please specify)

[Answer]: X. tg-veridicus, como aplicación de demostración, puede demostrar protocolo ético, pero es solo demostrativo: esta aplicación solo es un proyecto de investigación y demostración, más no de despliegue, así que no necesita validaciones adicionales.  El componente de validación de contradicciones, ya incluido en el trabajo de grado, debería regirse por los mismos principios éticos de la aplicación primaria.

### Pregunta 11 — ¿Dónde viven los reportes de la CLI que sube el investigador?

La consola de solo consulta del rol `investigador` (FR13.5, US12.6, US12.7) valida el JSON de una corrida o
evaluación contra su esquema, guarda **solo metadatos y cifras** (nunca texto de transcripciones,
hallazgos ni citas, NFR12), los lista, muestra el detalle y compara dos.

A. **Componente propio `ResearchReports`**, con sus entidades y su regla de no guardar texto **(Recomendada)**
B. Dentro de `ForensicReport` (el componente de los reportes).
C. Dentro de `AnalyzerCli`, reutilizando el esquema del modo evaluación.
X. Other (please specify)

[Answer]: A

### Pregunta 12 — ¿Cambia ya el nombre de `ForensicReport`?

VE-03 pasa el «reporte forense» a «reporte de revisión», y la adenda dice que el slug de U7 se revisa en
Units Generation. El nombre del componente es un identificador de diseño: lo citan Units Generation,
Contract Design y el glosario del código.

A. **Renombrar ya a `ReviewReport`** (glosario: «reporte de revisión» → `review_report`) y dejar una nota «antes `ForensicReport`» en el catálogo **(Recomendada)**
B. Conservar `ForensicReport` aquí y renombrar todo junto en Units Generation.
X. Other (please specify)

[Answer]: A

### Seguimiento 1 — Pregunta 10: ¿cómo entra la adenda 02 en el diseño?

La respuesta a la pregunta 10 dice que tg-veridicus es de investigación y demostración, que el protocolo
ético se puede demostrar pero no necesita validaciones adicionales, y que el analizador de incoherencias
se rige por los mismos principios éticos de la aplicación primaria del TG. La adenda 02 aprobada marca
VE-01..VE-17 como MUST y el 2026-11-06 se confirmaron A-1..A-4. Hace falta decidir qué hace el diseño
con esa diferencia; lo que cambie en la adenda se registra en la tabla de precisiones y se decide en la
aprobación de la etapa.

A. **El analizador (biblioteca y CLI) cumple las reglas éticas del TG sin rebaja** (vocabulario, aviso de que los hallazgos son para revisar la coherencia y no prueba, bloqueo sin consentimiento A-4, anonimizador e incidente VE-14); en la consola, el resto de la adenda (reconocimiento cada 90 días, retirada y pausa, registro de acceso, retención con acta, reporte de problemas) se diseña como **demostración en un solo componente `EthicsGovernance`**, sin compuertas que bloqueen el uso. En la tabla de precisiones se propone bajar esas VE de MUST a demostración **(Recomendada)**
B. Toda la adenda 02 sigue como MUST, repartida como en la opción A original (`EthicsGovernance` + `DataRetention`); la respuesta 10 solo deja constancia del carácter demostrativo.
C. La adenda 02 se aplica solo al analizador; la consola no lleva ningún componente ético y las VE de consola salen del MVP (marcadas «Retirado» en la tabla de precisiones).
X. Other (please specify)

[Answer]: A
