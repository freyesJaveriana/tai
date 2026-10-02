**Collaborator:** aidlc-design-agent

## Contribution

Ángulo: experiencia de usuario y fidelidad de las personas. No reabro lo que decidieron P1–P8. Los
textos entre «» son propuestas de redacción visible en español. Los IDs nuevos continúan la numeración
del borrador y el lead los puede renumerar.

### 1. Personas (fidelidad a PRD S3)

- **P2, «Objetivos» contradice P5.** Dice «gestionar usuarios y el umbral sin tocar código», pero P5
  decidió que el umbral vive en la configuración del despliegue y solo cambia por PR (US8.3, AC8.3.3).
  Redacción propuesta: «gestionar usuarios desde la consola; cambiar el umbral solo mediante un PR
  revisable, sin que el sistema se recalibre solo».
- **P1, «Dolores», invierte el riesgo 2 del PRD.** El borrador dice «miedo a aceptar a ciegas lo que diga
  la IA». El PRD (S12-R2) describe lo contrario: el analista, por fatiga, **sí** acepta a ciegas (sesgo de
  automatización). Esa diferencia es la que justifica la UX escéptica de US5.1. Redacción propuesta:
  «la fatiga lo expone a aceptar sin leer lo que propone la IA (sesgo de automatización, PRD S12-R2)».
  Añadir también el dolor literal de S3: «retraso por el cotejo manual y fragmentado de cada entrevista
  frente a expedientes extensos».
- **P1, contexto de uso (falta).** El PRD sitúa al analista en plena entrevista: la alerta llega como
  «alerta visual silenciosa» (S5-CU3, paso 4), y en S7-J4 (paso 5) el analista «interviene en caliente».
  Fila propuesta, «Contexto de uso»: «trabaja con la consola durante la entrevista o justo después, con
  la atención repartida; necesita avisos que no interrumpan y un estado del sistema que se lea de un
  vistazo».
- **P1, «Comodidad técnica: Media».** El PRD no lo dice. Marcarlo como supuesto: «(supuesto; S3 no lo
  fija)».
- **P2, dolor «pods que caen por memoria».** Viene de S12-R4, no de S3. Basta con citar el origen.
- **P3** es fiel a S3 (diagnóstico binario sobre declarantes con TEPT o vacíos de memoria, desconfianza
  ante alucinaciones, veto por falta de CoT o por juicio sin supervisión). No tengo cambios.

### 2. Historia que falta: lista de sesiones (MUST)

Varias historias MUST suponen que el analista **encuentra** una sesión: AC5.4.2 («la abro»), AC6.2.1
(descargar después), AC7.1.2 («vuelvo a entrar») y FR1.2 («Leer sesiones y reportes: Todas»). Sin
embargo, la única lista de sesiones es US11.2, que es COULD (panel lateral, FR11.2). Propongo una
historia mínima y dejar US11.2 como mejora:

**US2.5 — Ver la lista de sesiones · MUST · P1** · *Origen:* FR1.2 (leer todas), FR7.4, FR8.3. No
sustituye a FR11.2, el panel lateral.
Como Analista de Verdad, quiero ver las sesiones con su estado, para retomar las mías y consultar las de
otros.
- **AC2.5.1** Given sesiones de dos analistas, When entro a la consola como `analista`, Then veo una lista
  con escenario y versión, dueño, fecha y estado (`abierta`, `suspendida`, `finalizada`, `consolidada`),
  y las mías aparecen primero o se pueden filtrar.
- **AC2.5.2** Given que no hay sesiones, When abro la lista, Then veo «Aún no hay sesiones» y la acción
  «Nueva sesión» (para `analista`).
- **AC2.5.3** Given una sesión `suspendida` mía, When abro la lista, Then la sesión lo muestra con
  texto e icono, no solo con color, y al abrirla aparece el aviso de AC7.1.2.

### 3. Criterios nuevos o cambiados por historia

**US1.1 / US1.3, escenario**
- **AC1.1.2 (cambio).** Pedir un mensaje por causa que diga qué pasó y qué hacer, por ejemplo: «El
  archivo supera 1 MB. Divide el escenario o reduce su tamaño», «Solo se admiten archivos Markdown o
  de texto plano», «El archivo debe estar codificado en UTF-8». Con «un mensaje en español» no basta
  para comprobarlo.
- **AC1.1.5 (nuevo).** Given un escenario en indexación, When miro el catálogo, Then aparece como
  «Indexando…», no se puede elegir para una sesión y el resto de la consola sigue respondiendo.
- **AC1.1.3 (precisión).** Indicar dónde se consultan los pasajes: en una vista del escenario dentro de
  la consola o solo por la API. Hoy no se sabe si es un criterio de interfaz.
- **AC1.3.1 (precisión).** Enumerar los estados visibles (`indexando`, `listo`, `error`) y marcar cuál
  versión está preseleccionada. Propuesta: «la versión `listo` más reciente aparece preseleccionada y
  las anteriores se rotulan "versión anterior"».
- **AC1.3.3 (nuevo, estado vacío).** Given que no hay escenarios, When abro el catálogo al crear una
  sesión, Then veo «No hay escenarios de control listos» y la acción «Cargar escenario de control».
- Nota para FR1.2: el `admin` también puede cargar escenarios. US1.1 nombra solo a P1. Se puede añadir P2
  o dejar constancia de que su caso se cubre con la misma historia.

**US2.1 / US2.2 / US2.3 / US2.4, sesión e ingreso**
- **AC2.1.4 (nuevo, AC2.1.1 visible).** Given una sesión abierta, When la miro, Then la cabecera muestra
  el escenario, la versión, los primeros caracteres del SHA-256 y el umbral de la sesión, para que el
  analista sepa contra qué marco trabaja.
- **AC2.1.5 (nuevo).** Given un usuario `admin`, When recorre la consola, Then no ve la acción «Nueva
  sesión». Así se previene el error en la interfaz, no solo con el 403 de AC2.1.3.
- **AC2.2.4 (nuevo, estado vacío).** Given una sesión recién creada, When la abro, Then veo «Aún no hay
  turnos. Escribe el primer turno o pega una transcripción completa» y el botón «Enviar turno» está
  deshabilitado mientras el texto esté vacío.
- **AC2.3.3 (nuevo, prevención de errores).** Given una transcripción pegada, When el sistema la divide,
  Then veo cuántos turnos detectó y una vista previa de cada uno antes de confirmar, y puedo cancelar sin
  que se cree ningún turno. Si no encuentra separadores, la vista previa muestra «Se detectó 1 turno».
- **AC2.4.3 (nuevo, acción irreversible).** Given una sesión abierta, When pulso «Finalizar sesión»,
  Then un diálogo de confirmación dice «Después de finalizar no podrás agregar turnos», indica cuántos
  turnos siguen en proceso y ofrece «Finalizar» y «Cancelar».
- **AC2.4.4 (nuevo).** Given una sesión finalizada, When la miro, Then veo cuántas sugerencias de
  revisión quedan pendientes y un acceso a la primera.

**US3.1 / US3.2, alertas**
- **AC3.1.5 (nuevo, «alerta silenciosa», S5-CU3).** Given un turno que produce una alerta, When aparece,
  Then se agrega al panel de alertas sin ventana modal, sin sonido y sin mover el foco, el contador de
  pendientes se actualiza y una región `aria-live="polite"` lo anuncia.
- **AC3.1.6 (nuevo, rótulo).** Given cualquier alerta, When la veo, Then su rótulo es «Sugerencia de
  revisión · Incongruencia semántica» (S6-P1(b), S12-R6). Ningún rótulo usa grados de severidad que el
  sistema no calcula: el «Discrepancia nominal menor» del ejemplo de S7-J1 no se adopta.
- **AC3.1.7 (nuevo, vínculo con el turno).** Given una alerta, When la selecciono, Then el fragmento
  queda resaltado en su turno de la transcripción y la cita muestra el identificador de documento.
- **AC3.1.8 (nuevo, turno sin hallazgos).** Given un turno con todas sus afirmaciones «congruente», When
  termina, Then el turno muestra «Evaluado · sin sugerencias de revisión», distinto de `procesando` y de
  un Hecho No Documentado. No se muestra la calificación por afirmación, como decidió P4.
- **AC3.2.2 (precisión).** Precisar qué hace «reenviar». Propuesta: «Reintentar evaluación» reprocesa el
  mismo turno con el mismo número. El mensaje explica la causa sin jerga, por ejemplo: «No se pudo
  evaluar este turno: la respuesta de la IA no tenía el formato esperado. Puedes reintentar». El `code`
  aparece como referencia secundaria.
- **AC3.2.3 (nuevo, tiempo agotado).** Given un turno que supera el *timeout* de evaluación, When vence,
  Then pasa a `error` con un mensaje en español y la opción de reintentar. Nunca se queda en `procesando`
  indefinidamente. El valor del *timeout* lo fija NFR Requirements.

**US4.1, Silencio Fáctico**
- **AC4.1.6 (nuevo, distinción visual).** Given un Hecho No Documentado, When se muestra el aviso de
  FR5.4, Then se distingue de una alerta de incongruencia por texto e icono, no solo por el rojo de
  S7-J4, y no cuenta como sugerencia pendiente. Es un resultado normal (team.md, Code Style), así que no
  usa el estilo de error del sistema.
- **AC4.1.7 (nuevo, borde).** Given que la afirmación «no documentada» está en el turno 1 o 2, When se
  abre el paquete, Then muestra los turnos previos que existan e indica «Turnos previos disponibles: N de
  3».
- **AC4.1.8 (nuevo).** Given un paquete, When pulso el aviso, Then el panel lateral se abre sin tapar el
  turno al que se refiere, y se cierra con Escape o con «Cerrar».

**US5.1–US5.5, revisión (mitigación de UX escéptica, S12-R2)**
- **AC5.1.1 (precisión).** «No lo permite» tiene que verse. Propuesta: «Aceptar» y «Editar» se muestran
  deshabilitados con el texto visible «Despliega y lee la justificación (CoT) para habilitar esta
  acción», que no depende de un *tooltip*.
- **AC5.1.3 (precisión).** Fijar el texto y su posición: «La IA es un asistente de soporte. Su criterio
  como analista prevalece», visible sin *hover*, junto a los botones de decisión de cada alerta (S12-R2
  pide un descargo interactivo junto a la decisión).
- **AC5.1.4 (nuevo, «Aceptada con nota», S7-J1 paso 5).** Given una alerta aceptada con nota, When la
  veo en la lista, Then se lee «Aceptada · con nota» y la nota está visible.
- **AC5.2.4 (nuevo).** Given el editor de reformulación, When el texto está vacío, Then «Guardar» está
  deshabilitado con la explicación visible. Mientras escribo, el hallazgo original de la IA se muestra a
  un lado en solo lectura.
- **AC5.3.3 (nuevo).** Given el diálogo de descarte, When la nota está vacía, Then el error aparece junto
  al campo: «Escribe por qué descartas esta sugerencia».
- **AC5.4.4 (nuevo, solo lectura visible).** Given una sesión de otro analista, When la abro, Then veo
  «Sesión de <usuario>. Solo lectura» y no aparecen los botones de decisión ni de consolidación.
- **AC5.5.4 (nuevo, vocabulario de la interfaz).** Given todas las pantallas, When se recorren, Then los
  únicos rótulos de resultado son «Sugerencia de revisión», «Incongruencia semántica» y «Hecho No
  Documentado», y las calificaciones solo dicen «congruente», «incongruente» o «no documentada».
- **AC5.5.1 (aclaración).** Decir si el escaneo excluye las **notas y reformulaciones del analista**
  además de las citas literales. Si no las excluye, la prueba podría fallar por un texto humano legítimo.

**US6.1–US6.3, consolidación**
- **AC6.1.1 (precisión).** El botón deshabilitado muestra el motivo: «Quedan N sugerencias pendientes»,
  con un enlace a la primera. Si la sesión no está finalizada, dice «Finaliza la sesión para
  consolidar».
- **AC6.1.5 (nuevo, confirmación).** Given todas las alertas revisadas, When pulso «Finalizar y
  Consolidar», Then un diálogo resume cuántas sugerencias quedaron aceptadas, editadas y descartadas y
  cuántos Hechos No Documentados hay, y avisa: «Después de consolidar, la sesión queda bloqueada; una
  corrección creará una versión nueva». Las opciones son «Consolidar» y «Cancelar».
- **AC6.1.6 (nuevo, resultado visible).** Given un reporte recién consolidado, When termina, Then veo
  quién consolidó y cuándo, el SHA-256 completo con una acción para copiarlo y el botón «Descargar
  reporte».
- **AC6.2.3 (nuevo).** Given un reporte, When lo veo en la interfaz, Then el SHA-256 está visible junto a
  la descarga, para que cualquiera lo compare con el archivo (FR7.3).
- **AC6.3.5 (nuevo, salida).** Given una copia de trabajo, When la miro, Then un rótulo dice «Copia de
  trabajo de la versión N. Solo puedes cambiar estados y notas», y puedo «Descartar copia» sin crear una
  versión. La versión vigente no cambia.
- **AC6.3.6 (nuevo).** Given un reporte con varias versiones, When lo abro, Then veo la lista de
  versiones con su SHA-256, quién y cuándo, y la vigente está marcada.

**US7.1, reanudación (S7-J3)**
- **AC7.1.2 (precisión).** Usar el texto del PRD: «Se detectó una interrupción inesperada en la sesión.
  ¿Desea reanudar desde el último turno registrado?», con las opciones «Reanudar» y «Más tarde». Con «Más
  tarde» la sesión sigue `suspendida` y se puede reanudar desde la lista (US2.5). Quito «del compareciente
  simulado» porque el texto visible no debe nombrar al compareciente de forma innecesaria. Si el lead
  prefiere el texto literal del PRD, también vale.
- **AC7.1.4 (nuevo).** Given turnos que estaban en `procesando` al cortarse la conexión, When reanudo,
  Then muestran su estado actualizado (`evaluado` o `error`) y las alertas que generaron mientras tanto.

**US8.1, acceso**
- **AC8.1.5 (nuevo).** Given que mi sesión web expira con una sesión de entrevista abierta, When vuelvo a
  iniciar sesión, Then regreso a esa sesión sin pérdida (se enlaza con US7.1). La duración la fija NFR
  Requirements.
- **AC8.1.6 (nuevo, destino inicial).** Given un inicio de sesión válido, When entro, Then el `analista`
  llega a la lista de sesiones (US2.5) y el `admin` a la gestión de usuarios.

**Funciones SHOULD**
- **AC10.1.2 (nuevo).** Given un turno en proceso, When cambia de etapa, Then el cambio se anuncia en una
  región `aria-live="polite"`. Si supera la latencia esperada que fije NFR Requirements, el texto pasa a
  «Sigue en proceso…», sin bloquear la interfaz.
- **AC10.2.3 (nuevo).** Given que el navegador niega el micrófono, When pulso grabar, Then veo «No hay
  acceso al micrófono. Puedes seguir escribiendo el turno» y la entrada de texto sigue disponible. Mientras
  graba, hay un indicador visible y anunciado.
- **AC10.3.4 (nuevo).** Given una pregunta sugerida, When la veo, Then se rotula «Pregunta sugerida ·
  requiere tu aprobación» y ofrece «Aprobar» y «Descartar». Así AC10.3.3 depende de una acción
  explícita.
- **AC11.1.2 (nuevo, COULD).** El indicio afectivo usa el texto de S5-CU4: «Fluctuación afectiva por
  posible estrés/trauma en este fragmento. Se recomienda moderar el ritmo», y entra en el escaneo de
  vocabulario de AC5.5.1.

### 4. Accesibilidad: la etapa la tiene asignada y el borrador no la resuelve

`requirements.md` §7 asigna a **User Stories / Refined Mockups** la pregunta «Nivel de accesibilidad de
la interfaz (no lo fija el PRD)». El borrador no la cierra. Propuesta, que el humano debe confirmar porque
introduce un objetivo nuevo:

**US5.6 — Revisar alertas solo con teclado y con lector de pantalla · SHOULD · P1** · *Origen:*
`requirements.md` §7 (pregunta abierta asignada a esta etapa) y S12-R2.
- **AC5.6.1** Given la consola del analista, When corre la prueba E2E con `@axe-core/playwright` (WCAG
  2.1 AA), Then hay 0 violaciones de impacto `serious` o `critical` en login, lista de sesiones, sesión,
  panel de alertas, paquete de traspaso y consolidación.
- **AC5.6.2** Given el flujo de texto de punta a punta, When lo recorro solo con teclado (Tab, Enter,
  Espacio, Escape), Then puedo enviar un turno, desplegar la CoT, aceptar, editar, descartar y consolidar,
  con el foco siempre visible.
- **AC5.6.3** Given cualquier estado de turno, de alerta o de sesión, When lo veo, Then se identifica por
  texto o icono además del color (WCAG 1.4.1). Esto aplica al amarillo de S7-J1 y al rojo de S7-J4.

Si el humano prefiere no fijar el nivel ahora, la alternativa es dejar constancia en `stories.md` de que
la pregunta pasa a Refined Mockups, para que no quede abierta sin dueño.

### 5. Huecos que necesitan una decisión (no los resuelvo)

- **Turnos sin evaluar al consolidar.** Ninguna regla impide consolidar con turnos `en cola`,
  `procesando` o `error`. Un turno en `error` llegaría al reporte sin que la IA lo haya contrastado, y
  nada lo avisa. Recomendación: bloquear la consolidación mientras haya turnos `en cola` o `procesando`;
  listar en el diálogo de AC6.1.5 los turnos en `error` y rotularlos en el reporte como «no evaluado».
- **Cambiar una decisión antes de consolidar.** No se dice si una alerta `aceptada` puede pasar a
  `descartada` antes de consolidar. Recomendación (control del usuario): sí, y cada cambio queda en el
  historial de FR6.1.
- **Editar un turno ya enviado.** No se dice si un turno con un error de tipeo se puede corregir.
  Recomendación: no, porque la transcripción del reporte es literal. La interfaz lo avisa antes de
  enviar, y Functional Design decide si existe «anular turno».

## Positions

- AGREE: Tres personas, sin el compareciente (P1) — el compareciente no toca la interfaz; P3 como fuente de criterios es fiel a su veto en S3.
- AGREE: Épicas en el orden del recorrido y del flujo de texto primero (P2) — coincide con S7-J1 y con el orden de entrega de team.md.
- AGREE: US5.1 con la CoT plegada y aceptar o editar bloqueados hasta desplegarla — es la mitigación de UX escéptica de S12-R2; solo falta que el bloqueo y el descargo sean visibles (AC5.1.1, AC5.1.3).
- AGREE: Texto literal de FR5.4 en AC4.1.3 y supresión de la pregunta en un Hecho No Documentado — fiel a S7-J4.
- OBJECT: Objetivo de P2 «gestionar … el umbral sin tocar código» — contradice P5 y AC8.3.3; hay que reescribirlo.
- OBJECT: Dolor de P1 «miedo a aceptar a ciegas» — invierte el riesgo S12-R2 (el analista sí acepta a ciegas por fatiga), que es la razón de US5.1.
- OBJECT: No hay una lista de sesiones MUST — AC5.4.2, AC6.2.1, AC7.1.2 y FR1.2 la suponen y solo existe como COULD (US11.2); propongo US2.5.
- OBJECT: Criterios de interfaz que no se pueden observar («no lo permite», «mensaje en español», «puedo reenviarlo») — AUTONOMIA-02 pide criterios medibles; propongo textos y estados concretos.
- OBJECT: La accesibilidad queda sin resolver — `requirements.md` §7 la asigna a esta etapa; propongo US5.6 o pasarla de forma explícita a Refined Mockups.
- OBJECT: Se puede consolidar con turnos sin evaluar — un turno en `error` o `procesando` llegaría al reporte sin aviso; hace falta una decisión (sección 5).
