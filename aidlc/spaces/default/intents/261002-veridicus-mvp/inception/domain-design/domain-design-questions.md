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
