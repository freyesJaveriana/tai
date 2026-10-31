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

---

# Segunda pasada — cambio 01 (DT27, 2026-10-30)

Fuentes nuevas: `specs/prd.md` (iteración 6), `pvb.md` corregido, `docs/limite-autonomia.md`
(AUTONOMIA-04 y 05 reescritas), `docs/iteracion2.md` (análisis de impacto con P1–P18 respondidas, todas
con la opción recomendada) y el cambio 01 con su contrato común v0.1 (`/insumos/app/cambios/`, fuera
del repositorio; el contrato entra al repositorio en Contract Design).

Lo que esas fuentes ya deciden no se vuelve a preguntar: objeto del análisis (contradicciones dentro del
relato, 7 tipos, dos citas verificadas), soberanía (nada sin seudonimizar sale; anonimizador MUST,
siempre local, solo delante de destinos externos), biblioteca y CLI como unidad propia (P3), páginas
opcionales en turnos `guiada` (P4), entrada de texto (P5), modos final e incremental en la consola (P6),
corpus del piloto solo en la máquina local (P7), perfiles por PR elegidos al crear la sesión (P8, P9),
`NetworkPolicy` (P10), conjunto sintético de calidad (P11), qué se permuta (P12), AIR (P13), modo
fragmentado obligatorio con modelos locales (P14), repetibilidad (P15) y contenido del reporte (P16).

## Estado de las respuestas de la primera pasada

- **Pregunta 1** (5 de 6 discrepancias sembradas): **superada**; la calidad se mide sobre el conjunto
  sintético nuevo (P11), con umbrales en NFR Requirements.
- **Pregunta 2** (turno a turno y pegado): **se mantiene**, ampliada con la importación del JSON del
  corpus (P5).
- **Preguntas 3 y 4** (escenario de control): **superadas**; no hay marco de verdad.
- **Pregunta 5** (roles): **se mantiene** sin las filas de escenarios y umbral; entra «elegir el perfil
  al crear la sesión» (P8).
- **Preguntas 6 y 7** y **Seguimiento 1**: **se mantienen** (la CoT pasa a ser las observaciones del
  hallazgo).
- **Pregunta 8**: **se mantiene** (el Golden Dataset pasa a ser el conjunto sintético de P11).

Estas 8 preguntas cubren lo que falta para escribir requisitos con criterio medible (AUTONOMIA-02).

---

## Analizador

### Pregunta 9 — ¿Qué hace el verificador cuando la permutación en línea no está activa?

Todo perfil tiene juez y verificador (PRD S8, MUST), y la permutación de las dos citas es obligatoria en
la evaluación y opcional en línea (P12). Falta decir si el verificador interviene en cada corrida o solo
cuando hay permutación.

A. El verificador **siempre** confirma cada hallazgo candidato del juez (una llamada, citas en un orden). La permutación añade la segunda llamada con las citas invertidas: obligatoria en la evaluación, activable por perfil en línea. Un candidato que el verificador no confirma no sale del analizador y queda en el registro de la corrida **(Recomendada)**
B. El verificador solo actúa cuando la permutación está activa; sin ella, el hallazgo sale con el juez más la verificación determinista de las citas.
C. El verificador es opcional por perfil: un perfil puede no tenerlo.
X. Other (please specify)

[Answer]: A

### Pregunta 10 — ¿Qué cuenta como «cita literal en su turno»?

AUTONOMIA-05 exige que cada cita exista literalmente en su turno, y el 100 % de citas verificadas solo es
comprobable con una regla exacta. El verificador del piloto (`verificar_codificacion.py`) solo normaliza
espacios, une con « […] » fragmentos del mismo turno que deben aparecer en orden, y **avisa** (sin
rechazar) si la cita está en un turno del entrevistador o en un turno plegado.

A. **La regla del piloto**, para que el contrato común se comporte igual en Veridicus y en el TG: solo se normalizan espacios; « […] » une fragmentos del mismo turno en orden; una cita en un turno del entrevistador (`ENT`) o plegado se acepta con un aviso visible para el analista; en turnos sin página (origen `guiada`) se verifica solo contra el turno **(Recomendada)**
B. Igual que A, pero una cita en un turno del entrevistador **invalida** el hallazgo (solo cuenta el relato del testimoniante).
C. Normalización más amplia: además de espacios, mayúsculas, tildes y puntuación.
X. Other (please specify)

[Answer]: A

### Pregunta 11 — Con modelos locales, ¿se buscan contradicciones entre fragmentos distintos?

P14 hace obligatorio el modo fragmentado por turnos con solapamiento para los modelos locales (ventana de
12k del juez de demostración). Una contradicción entre el turno 12 y el turno 400 cae en fragmentos
distintos, y el cambio 01 no dice cómo se detecta (conflicto C1).

A. **Solo dentro de cada ventana** (con su solapamiento). Las contradicciones más distantes que la ventana son una limitación declarada: la corrida registra el modo y el tamaño de ventana, el reporte los muestra, y la evaluación reporta la sensibilidad según la distancia entre las dos citas **(Recomendada)**
B. Requisito: una segunda pasada compara los hechos extraídos de cada fragmento para encontrar contradicciones entre fragmentos lejanos.
C. Con modelos locales solo se analizan entrevistas que caben enteras en la ventana; las más largas terminan en error.
X. Other (please specify)

[Answer]: A

### Pregunta 12 — ¿Es regla dura que juez y verificador sean de familias distintas?

El PRD (S9 módulo D y S11 escenario B) pide juez y verificador de familias distintas (DT04, DT10). El
perfil `todo-local` de la demostración, con un solo modelo Qwen en Minikube (20 GiB), no lo cumple.

A. **Obligatorio en los perfiles de evaluación** (nivel 2): su validación rechaza juez y verificador de la misma familia. Un perfil de demostración puede usar la misma familia solo si lo declara explícitamente, y la consola y el reporte lo muestran como aviso **(Recomendada)**
B. Regla dura para todo perfil: `todo-local` necesita dos modelos locales de familias distintas (más memoria en Minikube).
C. Solo se registra la familia de cada papel; no se valida.
X. Other (please specify)

[Answer]: A

## Entrada y límites

### Pregunta 13 — ¿Qué tamaño de transcripción admiten la consola y la CLI?

Los límites aprobados (100 000 caracteres por transcripción, 200 turnos, 2 000 caracteres por turno,
reporte de 2 MiB) quedan por debajo del corpus del piloto (≈ 10 000 a 186 000 caracteres), y P7 permite
importar esas entrevistas en la consola local (conflicto C2).

A. **Ambas admiten al menos la entrevista más larga del piloto, con margen**; las cifras exactas las fija NFR Requirements en el catálogo único de límites. Con perfil local se usa el modo fragmentado (P14) **(Recomendada)**
B. La consola mantiene los límites aprobados; las entrevistas largas solo entran por la CLI.
C. La CLI sin límite; la consola con los límites aprobados.
X. Other (please specify)

[Answer]: A

## Evaluación y gobierno

### Pregunta 14 — En la evaluación, ¿cuándo un hallazgo «acierta» una contradicción esperada?

El conjunto sintético (P11) trae la lista exacta de contradicciones esperadas con sus dos citas. Para
medir precisión y sensibilidad hay que fijar cuándo un hallazgo coincide con una esperada.

A. Coincide si cita **el mismo par de turnos** (sin importar el orden). El tipo se mide aparte como acuerdo de tipo. Todo hallazgo en un relato coherente o en un caso trampa es un falso positivo **(Recomendada)**
B. Coincide solo con el mismo par de turnos **y** el mismo tipo.
C. Coincide si el texto de las citas se solapa con el de las esperadas, aunque estén en otros turnos.
X. Other (please specify)

[Answer]: A

### Pregunta 15 — ¿Cuál es el criterio de aprobado del anonimizador?

AUTONOMIA-04 pide una prueba de que el payload saliente no lleva nombres ni ubicaciones del conjunto de
prueba, pero no dice cuántas fugas se toleran.

A. **Cero fugas**: sobre el conjunto sintético, el 100 % de las entidades sembradas (nombres, lugares, números de expediente, con y sin tilde) sale seudonimizado; una sola fuga hace fallar la prueba. Las marcas son coherentes en toda la entrevista y una marca alterada por el modelo invalida el hallazgo **(Recomendada)**
B. Un umbral de sensibilidad (p. ej., ≥ 95 %) que fija NFR Requirements; las fugas restantes se reportan.
C. Solo la prueba estructural (el payload pasó por el anonimizador), sin medir fugas.
X. Other (please specify)

[Answer]: A

### Pregunta 16 — ¿Se controla el costo de los proveedores comerciales?

El análisis del cambio 01 (K5) pide que cada corrida registre los *tokens* y que la evaluación declare su
costo, pero no fija ningún tope.

A. Cada llamada registra *tokens* de entrada y salida; cada corrida y cada reporte de evaluación suman *tokens* y un costo estimado según una tabla de precios versionada por PR. **Sin tope automático** en el MVP **(Recomendada)**
B. Igual que A, y además cada perfil declara un tope de *tokens* por corrida; al superarlo la corrida termina con `estado: error` sin resultado parcial.
C. Solo registrar *tokens*, sin costo estimado.
X. Other (please specify)

[Answer]: A
