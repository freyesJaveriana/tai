# Preguntas — Análisis de Requisitos (Veridicus)

Fuentes leídas: `specs/prd.md` (con las 19 decisiones de `docs/coherencia-insumos.md` ya aplicadas),
`pvb.md`, `docs/limite-autonomia.md` y las prácticas afirmadas
(`inception/practices-discovery/team-practices.md`). Lo que esos documentos ya deciden no se vuelve a
preguntar: MoSCoW de voz, preguntas sugeridas y TTS; edición de alertas, consolidación, descarga,
reanudación e inicio de sesión como MUST; LieXBerta completo en TG2; umbral del Silencio Fáctico como
parámetro cuyo valor fija NFR Requirements; composición del Golden Dataset; reglas AUTONOMIA-01..05.

Estas 8 preguntas cubren lo que falta para escribir requisitos con criterio de aceptación medible
(AUTONOMIA-02).

## Cómo responder

- Escribe la letra después de `[Answer]:`, en la misma línea o en la siguiente.
- La opción **(Recomendada)** es mi propuesta; no está aplicada todavía.
- Si ninguna opción encaja, usa `X` y escribe la tuya.

---

## Detección

### Pregunta 1 — ¿Cuántas de las discrepancias sembradas debe detectar el sistema, y cuántas alertas falsas toleramos?

Viene de Practices Discovery (pregunta 9): el PRD fija la composición del Golden Dataset (4 transcripciones
alineadas al 100 % y 6 con una discrepancia sembrada: 2 de fecha, 2 de lugar, 2 de rol) pero no dice qué
porcentaje debe detectar la IA. Sin este número, la evaluación de nivel 2 no tiene criterio de aprobado.

A. Detectar **al menos 5 de las 6** discrepancias sembradas (≥ 83 %) y **como máximo 1 alerta** en total sobre las 4 transcripciones alineadas **(Recomendada)**
B. Detectar **las 6** discrepancias y **0 alertas** sobre las transcripciones alineadas.
C. Detectar al menos 4 de 6 (≥ 67 %) y como máximo 2 alertas sobre las transcripciones alineadas.
X. Other (please specify)

[Answer]: A

---

## Entrada del testimonio

### Pregunta 2 — ¿Cómo ingresa el analista un testimonio en texto?

Las alertas se emiten por fragmento y el Paquete de Contexto de Traspaso necesita «el fragmento actual y
los tres turnos previos» (Journey 4), así que el sistema debe saber qué es un turno.

A. **Turno a turno**: cada envío del analista es un turno. Además puede pegar una transcripción completa, que el sistema divide en turnos por línea vacía o por marcas de hablante, y procesa en orden **(Recomendada)**
B. Solo transcripción completa: el analista pega o sube todo el texto de una vez y el sistema lo divide en fragmentos.
C. Solo turno a turno: cada envío es un turno; no hay carga de transcripción completa.
X. Other (please specify)

[Answer]: A

---

## Escenario de control

### Pregunta 3 — ¿Qué pasa con un escenario de control una vez indexado?

Journey 1 habla de un «catálogo» de escenarios, y el PRD llama «inmutable» al marco de verdad. Hay que
decidir si se pueden tener varios y si se pueden cambiar.

A. Puede haber **varios escenarios**; cada uno queda **inmutable** al indexarse. Corregirlo crea una versión nueva, y cada sesión queda ligada a la versión exacta (identificador y SHA-256) con la que se evaluó **(Recomendada)**
B. Varios escenarios, editables en sitio; las sesiones ya evaluadas guardan una copia de los pasajes usados.
C. Un único escenario activo a la vez; cargar otro reemplaza al anterior.
X. Other (please specify)

[Answer]: A

### Pregunta 4 — ¿Qué límites tiene el documento del escenario?

El caso de uso 1 acepta Markdown o texto plano y fija la meta de indexarlo en menos de 3 minutos; sin un
tamaño máximo, esa meta no es comprobable.

A. Markdown o texto plano en UTF-8, de **hasta 1 MB**; el sistema rechaza con un mensaje en español cualquier otro formato o tamaño, y la meta de < 3 min aplica a ese tamaño máximo **(Recomendada)**
B. Igual, pero hasta 200 KB.
C. Igual, pero hasta 5 MB.
X. Other (please specify)

[Answer]: A

---

## Roles y control humano

### Pregunta 5 — ¿Qué puede hacer cada rol?

El PRD define los roles `analista` y `admin`, pero no reparte las acciones. Esto define quién puede
aplicar un cambio de umbral (Segmento 10, AIR) y quién puede tocar una sesión ajena.

A. `admin`: gestiona usuarios, carga escenarios y aplica cambios de umbral (quién, cuándo, valor anterior y nuevo). `analista`: carga escenarios, crea sesiones y **solo edita alertas y consolida sus propias sesiones**; puede leer las de otros **(Recomendada)**
B. Igual que A, pero cualquier analista puede editar y consolidar cualquier sesión.
C. Igual que A, pero solo el `admin` carga escenarios.
X. Other (please specify)

[Answer]: A

### Pregunta 6 — ¿Qué exige la interfaz antes de aceptar o descartar una alerta?

El riesgo 2 del PRD (sesgo de automatización) propone obligar a leer la CoT antes de aceptar. Hay que
decidir si eso es requisito.

A. **Obligatorio**: no se puede marcar una alerta como aceptada o editada sin haber desplegado su CoT; **descartar exige una nota**; aceptar con nota es opcional **(Recomendada)**
B. Obligatorio desplegar la CoT antes de aceptar; ninguna nota es obligatoria.
C. Ninguna restricción: la CoT es plegable y el analista decide.
X. Other (please specify)

[Answer]: A

### Pregunta 7 — ¿Qué pasa con una sesión después de «Finalizar y Consolidar»?

El reporte se guarda con su SHA-256 y el registro de quién y cuándo. Falta decidir si puede corregirse.

A. La sesión y sus alertas quedan **bloqueadas**. Una corrección crea una **versión nueva** del reporte (nuevo SHA-256, nueva consolidación con quién y cuándo) que referencia a la anterior, que se conserva intacta **(Recomendada)**
B. La sesión queda bloqueada para siempre; cualquier corrección exige una sesión nueva.
C. El analista puede reabrirla y reconsolidar; el reporte anterior se reemplaza.
X. Other (please specify)

[Answer]: A

---

## Métricas del MVP

### Pregunta 8 — ¿Qué hacemos con las métricas del PRD que el MVP académico no puede medir, y con cuántas sesiones concurrentes se mide el pipeline?

Con una sola persona y datos sintéticos no hay forma de medir «> 85 % de uso semanal» ni la tasa de
desestimación «en producción». El KPI de éxito del pipeline (> 98 %) dice «bajo ejecuciones concurrentes»
sin decir cuántas.

A. Las métricas de adopción (uso semanal, desestimación en producción) quedan como **hipótesis de producto fuera de los criterios de aceptación** del MVP. El éxito del pipeline (> 98 %) se mide con **3 sesiones concurrentes** de texto sobre el Golden Dataset en la máquina de CPU **(Recomendada)**
B. Igual, pero el pipeline se mide con 1 sola sesión a la vez.
C. Igual, pero con 5 sesiones concurrentes.
X. Other (please specify)

[Answer]: A

---

## Preguntas de seguimiento

### Seguimiento 1 — ¿Se puede consolidar con alertas todavía pendientes? (respuestas 6 y 7)

Las respuestas 6 y 7 fijan cómo se revisa cada alerta y qué pasa después de consolidar, pero no si
pueden quedar alertas en estado «pendiente» al pulsar «Finalizar y Consolidar». AUTONOMIA-03 prohíbe
consolidar el reporte final sin la validación explícita de un analista, y una alerta pendiente es un
hallazgo de la IA que nadie revisó.

A. **No**: «Finalizar y Consolidar» queda deshabilitado mientras haya alguna alerta pendiente; cada una debe estar aceptada, editada o descartada **(Recomendada)**
B. Sí, pero las alertas pendientes aparecen en una sección aparte del reporte, marcadas «sin revisar por el analista».
C. Sí, y las alertas pendientes se excluyen del reporte.
X. Other (please specify)

[Answer]: A
