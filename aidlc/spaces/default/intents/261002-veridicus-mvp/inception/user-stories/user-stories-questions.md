# Plan de historias y preguntas — Historias de Usuario (Veridicus)

## Plan propuesto

- **Formato:** «Como [persona], quiero [acción], para [beneficio]», con criterios Given/When/Then
  (`ACx.y.z`), prioridad MoSCoW tomada de `requirements.md` y notas INVEST. Cada historia es una rebanada
  vertical comprobable por sí misma.
- **Identificadores:** `USx.y` por épica; las épicas siguen el recorrido del usuario.
- **Prioridad:** la de cada requisito de origen; el límite final del MVP lo fija Delivery Planning.
- **Insumo:** `inception/requirements-analysis/requirements.md` y team-practices. Lo que esos documentos
  ya deciden no se vuelve a preguntar.

Las preguntas 4 a 8 cierran hallazgos que la revisión de Análisis de Requisitos dejó abiertos y que
aceptaste como riesgo al aprobar; sin cerrarlos, los criterios de aceptación de esas historias no se
pueden escribir.

## Cómo responder

- Escribe la letra después de `[Answer]:`, en la misma línea o en la siguiente.
- La opción **(Recomendada)** es mi propuesta; no está aplicada todavía.
- Si ninguna opción encaja, usa `X` y escribe la tuya.

---

## Personas y estructura

### Pregunta 1 — ¿Qué personas modelamos?

El PRD (S3) nombra al Analista de Verdad, al Líder SRE/CISO y al Oficial de Cumplimiento Ético; la
aplicación tiene dos roles (`analista`, `admin`).

A. Tres personas: **Analista de Verdad** (principal, rol `analista`), **Administrador de plataforma** (une al Líder SRE/CISO con el rol `admin`) y **Oficial de Cumplimiento Ético** (no usa la consola; sus vetos aparecen como criterios de aceptación). El compareciente no es persona porque en el MVP no toca la interfaz **(Recomendada)**
B. Solo las dos personas con rol en la aplicación (analista y administrador).
C. Cuatro personas: las tres de A más el compareciente simulado.
X. Other (please specify)

[Answer]: A

### Pregunta 2 — ¿Cómo agrupamos las historias?

A. **Por recorrido del usuario**, en el orden de entrega: escenario de control → sesión e ingreso de texto → validación y alertas → Silencio Fáctico → revisión humana → consolidación y reporte → reanudación → administración y umbral → plataforma; las SHOULD y COULD en épicas propias al final **(Recomendada)**
B. Por prioridad MoSCoW (todas las MUST, luego SHOULD, luego COULD).
C. Por persona (todo lo del analista, luego todo lo del administrador).
X. Other (please specify)

[Answer]: A

### Pregunta 3 — ¿Cómo tratamos los requisitos de plataforma y los no funcionales?

A. Se escriben como historias del **Administrador de plataforma** solo cuando su verificación es observable por una persona (aislamiento de red, salud de los servicios, límites de recursos, Secrets); los demás NFR (calidad de IA, MTTV, cobertura, latencia) quedan como `Deferred` hacia NFR Requirements y Build and Test **(Recomendada)**
B. Todos los NFR se convierten en historias.
C. Ningún requisito de plataforma ni NFR se convierte en historia; todos quedan `Deferred`.
X. Other (please specify)

[Answer]: A

---

## Hallazgos abiertos de Análisis de Requisitos

### Pregunta 4 — ¿Cómo decide el sistema entre alerta, Hecho No Documentado o nada? (R-01)

FR4.3 evalúa la similitud por afirmación y FR5.2 por turno; un turno con dos afirmaciones, una por
encima y otra por debajo del umbral, queda sin regla.

A. **Por afirmación**: cada afirmación con similitud por debajo del umbral es «no documentada» y entra al Paquete de Contexto de Traspaso del turno; una «incongruente» en o por encima del umbral produce alerta; una «congruente» no produce nada visible. Si alguna afirmación del turno es «no documentada», se suprime la sugerencia de pregunta de ese turno **(Recomendada)**
B. **Por turno**: si la similitud máxima del turno está por debajo del umbral, todo el turno es Hecho No Documentado; si no, el juez califica cada afirmación y solo «incongruente» produce alerta.
C. Por afirmación, pero el Paquete de Traspaso solo se genera cuando todas las afirmaciones del turno están por debajo del umbral.
X. Other (please specify)

[Answer]: A

### Pregunta 5 — ¿Dónde vive el umbral de similitud y quién lo cambia? (R-03)

A. En la **configuración del despliegue**: cambiarlo es un PR revisable (AUTONOMIA-01) y la fusión en `main` es el registro de quién, cuándo, valor anterior y nuevo. Cada sesión guarda el valor con que se creó y no cambia a mitad de sesión. La consola no tiene acción de cambio de umbral **(Recomendada)**
B. En la **base de datos**, con una acción del `admin` en la consola que registra quién, cuándo, valor anterior y nuevo; aplica solo a sesiones nuevas.
C. En la configuración, pero la consola del `admin` muestra el valor vigente y el historial leído del repositorio.
X. Other (please specify)

[Answer]: A

### Pregunta 6 — ¿Qué edita el analista cuando marca una alerta como «editada»? (R-05)

A. Solo un **texto propio del analista** (su reformulación del hallazgo). El hallazgo original de la IA (fragmento, cita, identificador de documento y CoT) nunca cambia, y el reporte muestra el original y la edición con quién y cuándo **(Recomendada)**
B. Puede editar el texto del hallazgo y también la cita o el fragmento; el historial guarda la versión original.
C. «Editada» equivale a «aceptada con nota»; no hay edición de texto.
X. Other (please specify)

[Answer]: A

### Pregunta 7 — ¿Cómo se corrige un reporte ya consolidado? (R-06)

A. El analista dueño pulsa «Corregir reporte»: se abre una **copia de trabajo** donde solo puede cambiar estados y notas de las alertas (no la transcripción ni la salida de la IA); al consolidarla se crea la versión nueva con su SHA-256, que referencia a la anterior **(Recomendada)**
B. Igual que A, pero también un `admin` puede iniciar la corrección.
C. Se difiere a Functional Design; las historias solo exigen que la versión anterior se conserve intacta.
X. Other (please specify)

[Answer]: A

### Pregunta 8 — ¿Cómo se mide el éxito del pipeline frente al «> 98 %» del PRD? (R-04)

NFR8 dice «≥ 98 %» sobre 50 sesiones (1 fallo permitido), pero el PRD exige «> 98 %»: 49 de 50 es
exactamente 98 % y no cumple. Las 50 sesiones las propuse yo; no salieron de tus respuestas.

A. **50 sesiones en tandas de 3 concurrentes, 0 fallos** (cumple «> 98 %» con una muestra que se puede correr en CPU) **(Recomendada)**
B. 100 sesiones en tandas de 3, como máximo 1 fallo (99 %).
C. Se corrige el PRD a «≥ 98 %» en su propio commit y se mantiene 1 fallo cada 50.
X. Other (please specify)

[Answer]: A

---

## Decisiones que surgieron al revisar el borrador (diseño, desarrollo y calidad)

### Seguimiento 1 — ¿Qué pasa con los turnos sin evaluar al consolidar?

Un turno puede quedar en `error` incluso tras reintentarlo (con temperatura 0 y semilla fija, puede fallar
igual). Si bloquea la consolidación, la sesión podría no cerrarse nunca.

A. La consolidación se bloquea mientras haya turnos `en cola` o `procesando`; los turnos en `error` **no la bloquean**: el diálogo de confirmación los lista y el reporte los rotula «turno no evaluado» con su `code` **(Recomendada)**
B. La consolidación se bloquea mientras haya cualquier turno que no esté `evaluado`, incluidos los de `error`.
C. Nada se bloquea por turnos; el reporte marca los que no se evaluaron.
X. Other (please specify)

[Answer]: A

### Seguimiento 2 — Similitud en o sobre el umbral, pero el juez califica «no documentada»

La respuesta 4 define «no documentada» por debajo del umbral; esta combinación no tiene regla y el módulo
guardia necesita el 100 % de ramas.

A. Se trata como «no documentada»: entra al Paquete de Contexto de Traspaso, sin alerta, y suprime la pregunta sugerida del turno **(Recomendada)**
B. No produce nada visible, como una «congruente».
X. Other (please specify)

[Answer]: A

### Seguimiento 3 — ¿Qué nivel de accesibilidad fijamos?

`requirements.md` dejó esta pregunta para esta etapa o para Refined Mockups.

A. Historia SHOULD: WCAG 2.1 AA verificado con `@axe-core/playwright` (0 violaciones `serious`/`critical`), el flujo de texto completo con solo teclado, y ningún estado que dependa solo del color **(Recomendada)**
B. Pasar la decisión de forma explícita a Refined Mockups.
C. Sin meta de accesibilidad en el MVP.
X. Other (please specify)

[Answer]: A

### Seguimiento 4 — ¿El escaneo de vocabulario prohibido revisa el texto que escribe el analista?

AUTONOMIA-03 prohíbe etiquetas de veracidad producidas por la IA o por la interfaz. Las notas y
reformulaciones del analista son texto humano.

A. **No**: se escanean la salida de la IA, los textos de la interfaz y el reporte generado, excluyendo las citas literales y el texto escrito por el analista (que el reporte muestra como suyo) **(Recomendada)**
B. Sí: también se escanea y se bloquea el texto del analista.
X. Other (please specify)

[Answer]: A

### Seguimiento 5 — ¿Puede el analista cambiar una decisión antes de consolidar?

A. Sí: una alerta aceptada, editada o descartada puede pasar a otro de esos estados antes de consolidar, con las mismas exigencias (CoT desplegada, nota al descartar), y cada cambio queda en el historial; nunca vuelve a `pendiente` **(Recomendada)**
B. No: la primera decisión es definitiva hasta consolidar; corregirla exige «Corregir reporte».
X. Other (please specify)

[Answer]: A

### Seguimiento 6 — ¿Qué pasa si se carga un escenario idéntico a una versión existente?

A. Se rechaza con un mensaje que nombra la versión existente con el mismo SHA-256 **(Recomendada)**
B. Se crea igual una versión nueva.
X. Other (please specify)

[Answer]: A
