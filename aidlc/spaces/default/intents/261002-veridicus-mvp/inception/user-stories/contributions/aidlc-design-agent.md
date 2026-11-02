**Collaborator:** aidlc-design-agent

## Contribution

Ángulo: experiencia de usuario y fidelidad a las personas, segunda pasada (cambio 01). No reabro las
respuestas 1–14 ni los Seguimientos. Los textos entre «» son redacción visible propuesta. Los IDs nuevos
continúan la numeración del borrador.

### 1. Personas

- P1–P4 son fieles a PRD S3 y a la respuesta 9. Las correcciones de la primera pasada ya están integradas:
  sesgo de automatización (S12-R2), contexto de uso con la atención repartida y la comodidad técnica
  marcada como supuesto.
- **P1, «Qué no puede pasar»**: propongo añadir «quedarse sin poder entregar el reporte porque el
  análisis completo falló». Es el dolor que resuelve la pregunta 13, y así esa decisión queda trazada a
  una persona.
- **P1 y la jerga**: P1 tiene comodidad técnica media y no conoce «juez», «verificador», «papel» ni
  «plegado». Esto afecta a AC13.1.1, AC13.1.2 y AC3.1.4 (ver §3).

### 2. Huecos en flujos nuevos (MUST, integrables sin preguntar)

- **Límites al pegar y al escribir (FR3.7).** FR3.7 exige rechazar «antes de encolarse» en la consola,
  pero solo AC2.6.3 lo cubre, y solo para la importación. Propongo:
  - **AC2.3.4** Given un bloque que supera un límite del catálogo (turnos o caracteres), When veo la vista
    previa, Then leo «El bloque tiene N turnos; el máximo es M» (o «… caracteres»), «Confirmar» queda
    deshabilitado con ese motivo y la API responde `413` sin crear filas; en el límite exacto se acepta.
    `[N0]` Vitest + `[N1]`
  - **AC2.2.6** Given un turno que supera los caracteres por turno, When escribo, Then veo el contador
    «X / M caracteres» y «Enviar turno» se deshabilita con ese motivo; la API responde `413`. `[N0]` Vitest + `[N1]`
- **Importar sin confirmar cierra la sesión de forma irreversible.** AC2.6.1 crea la sesión directamente,
  y esa sesión nace cerrada a turnos nuevos. Para que sea coherente con la vista previa de AC2.3.1
  (prevención de errores), propongo:
  - **AC2.6.5** Given un archivo válido, When lo selecciono, Then antes de crear nada veo «Se importarán
    N turnos (páginas X–Y), de ellos K del entrevistador y P plegados. La sesión no admitirá turnos
    nuevos», con «Importar» y «Cancelar»; con «Cancelar» hay 0 filas. `[N0]` Vitest + `[N1]`
  - En AC2.6.2, el mensaje debe nombrar el **primer** problema y cuántos hay en total
    («Turno 37: falta el hablante. Hay 3 problemas más»). Así el analista no tiene que corregir el
    archivo a ciegas, un error cada vez.
- **Doble lanzamiento del modo final.** No hay ningún criterio para dos lanzamientos simultáneos ni para
  «Relanzar» mientras otro modo final está en curso. Propongo:
  - **AC2.7.6** Given un modo final «En cola» o «Procesando», When lo pido otra vez (doble clic o
    petición simultánea), Then exactamente una petición responde `202` y la otra `409`, con una sola
    corrida nueva; el botón queda deshabilitado con «El modo final ya está en proceso». `[N1]` + `[N0]` Vitest
- **Qué modo final cuenta después de relanzar.** La pregunta 13 permite relanzar, pero AC6.1.2 y AC6.1.3
  no dicen qué corrida decide el rótulo. Propongo fijarlo en AC6.1.2: «el estado que cuenta es el del
  **último** modo final lanzado; los intentos anteriores en error aparecen en el registro de corridas,
  pero no como "Modo final no completado"».
- **AC2.7.3 no se puede medir** («responde y veo su avance»; AUTONOMIA-02). Propongo esta redacción:
  Given un `ModelGateway` *fake* que bloquea el modo final, When está en proceso, Then un `GET` de la
  sesión y la decisión sobre un hallazgo existente responden `200` antes de liberarlo, y la sesión
  muestra «Modo final en proceso», distinto de «Modo final terminado» y de «Modo final con error».
  `[N1]` + `[N0]` Vitest. El avance por ventanas sigue en US10.1, que es SHOULD.

### 3. Textos visibles y avisos

- **La limitación del modo fragmentado debe verse antes de elegir.** US3.7 solo la muestra cuando
  termina la corrida, pero P1 elige el perfil al crear la sesión (FR14.5) y el perfil ya no cambia
  (FR3.1). Propongo:
  - **AC13.1.3** Given un perfil local, When lo veo en «Nueva sesión» y en la cabecera de la sesión, Then
    leo «Análisis por ventanas: no busca contradicciones entre turnos separados por más de N turnos».
    `[N0]` Vitest
  - **AC13.1.4** Given el formulario, When lo abro, Then ningún perfil viene preseleccionado, leo «El
    perfil no se puede cambiar después de crear la sesión» y «Crear sesión» queda deshabilitado con su
    motivo hasta que elija un perfil. `[N0]` Vitest
  - Redacción para AC3.7.1: «Análisis por ventanas de N turnos (solapamiento de M). No se buscaron
    contradicciones entre turnos separados por más de N turnos». El texto actual, «más distantes», no
    dice distantes de qué.
- **Lenguaje para P1 en lugar de jerga.**
  - En AC13.1.1, cada perfil abre con una línea en lenguaje llano: «Comercial: el texto sale
    seudonimizado del clúster» o «Local: nada sale del clúster». El detalle por papel (proveedor y
    modelo) queda en un bloque desplegable.
  - En AC13.1.2, el texto propuesto es «El modelo que propone cada contradicción y el que la confirma son
    de la misma familia: la confirmación es menos independiente».
  - En AC3.1.4, el aviso de turno plegado debe explicar qué significa «plegado» según el contrato común.
    Lo fija Functional Design; aquí basta con exigir que el texto lo explique.
- **Causa legible por código de error (heurística 9).** AC3.2.2 y AC2.7.4 solo muestran el `codigo`.
  Propongo **AC3.2.5**: cada código lleva una causa en español, sin culpar al testimonio, y debajo el
  mensaje de FR4.2:
  - `proveedor`: «El servicio de modelos no respondió».
  - `tiempo_agotado`: «El análisis superó el tiempo máximo».
  - `salida_invalida`: «La respuesta del modelo no tuvo el formato esperado».
  - `bloqueo_contenido`: «El filtro de contenido del proveedor rechazó la petición».

  Cuando la causa es la caída del anonimizador (AC11.3.3), el texto añade «No se envió ningún dato fuera
  del clúster». Contract Design decide con qué `codigo` se registra ese caso. Nivel: `[N0]` Vitest.
- **Dos «Finalizar» con significados distintos.** «Finalizar sesión» cierra el ingreso de turnos y
  «Finalizar y Consolidar» bloquea el reporte. AC6.1.1 incluso pone «Finaliza la sesión para consolidar»
  junto a un botón llamado «Finalizar y Consolidar». Propongo que el texto visible sea «Consolidar
  reporte» y que «Finalizar y Consolidar» quede como nombre de la acción en FR7.1. Como precisa el texto
  de FR7.1, va a la tabla de decisiones para que el humano decida en la aprobación.

### 4. Atención repartida y accesibilidad

- **Los botones deshabilitados deben ser enfocables.** En AC2.2.5, AC5.1.1, AC5.2.1, AC6.1.1 y AC13.1.4,
  un `disabled` nativo saca el botón del orden de tabulación, y con teclado o lector de pantalla nunca se
  oye el motivo. Propongo **AC5.6.4**: los botones con motivo usan `aria-disabled="true"`, siguen siendo
  enfocables y anuncian el motivo con `aria-describedby`. `[N0]` Vitest
- **Agregar los anuncios en `aria-live`.** Si el lector anuncia cada cambio de estado de turno, un
  bloque pegado o una importación de cientos de turnos lo saturan. Propongo **AC5.6.5**: `aria-live`
  solo anuncia cambios agregados (contador de pendientes, inicio y fin o error del modo final, sesión
  suspendida). El estado de cada turno se lee al enfocarlo. `[N0]` Vitest
- **Ampliar AC5.6.2.** El recorrido con teclado debe incluir crear la sesión eligiendo el perfil,
  importar un archivo, confirmar la vista previa, relanzar el modo final y responder al aviso de
  reanudación.
- **Diálogo de consolidación en AC6.1.2.**
  - Como la acción es irreversible, el foco inicial va a «Cancelar».
  - Con un modo final en error, el diálogo ofrece además «Volver y relanzar el modo final» y explica la
    consecuencia: «El reporte no incluirá contradicciones entre pasajes distantes».
  - Si la sesión usó el modo fragmentado, el diálogo repite la limitación.
  - En AC6.1.1, cuando hay varios motivos de bloqueo se listan todos, no solo el primero.
- **Resaltado de las citas (AC3.1.2).** El resaltado no depende solo del color: lleva una marca «A» o
  «B» junto a la cita y el turno resaltado se anuncia como «Cita A, turno 454».

### 5. Nota para Refined Mockups (sin criterio nuevo aquí)

- Según `docs/iteracion2.md` §2.3, «Pegar» pasa a «Importar transcripción». Sin embargo, FR3.3 y US2.3
  siguen vigentes, así que las maquetas deben conservar **ambas** entradas.

## Positions

- AGREE: Las personas P1–P4 son fieles a S3 y a la respuesta 9, e integran las correcciones de la primera pasada (S12-R2, contexto de uso).
- AGREE: US2.5 como MUST da a varias historias MUST el punto de entrada a la sesión que necesitan.
- AGREE: AC3.1.3 (hallazgo silencioso, sin modal ni robo de foco) protege a P1 cuando trabaja con la atención repartida.
- AGREE: AC5.1.1 y AC5.1.5 sostienen la UX escéptica frente al sesgo de automatización sin bloquear el descarte.
- AGREE: AC6.1.2 aplica bien la pregunta 13: un error no bloquea la entrega y queda rotulado.
- AGREE: AC3.1.4 muestra los avisos de cita ENT o plegada con texto e icono, en la consola y en el reporte.
- OBJECT: FR3.7 exige rechazar en la consola antes de encolar, pero pegar y escribir no tienen criterio de límite; propongo AC2.3.4 y AC2.2.6.
- OBJECT: AC2.7.3 («responde y veo su avance») no se puede medir (AUTONOMIA-02), y falta el caso del doble lanzamiento; propongo la nueva redacción y AC2.7.6.
- OBJECT: Tras relanzar el modo final, no está fijado qué corrida decide «Modo final no completado»; propongo que cuente el último lanzado (AC6.1.2).
- OBJECT: La limitación del modo fragmentado solo aparece después de la corrida, aunque el perfil se elige antes y no cambia; propongo AC13.1.3 y AC13.1.4.
- OBJECT: Importar crea una sesión cerrada sin vista previa ni confirmación, a diferencia de pegar; propongo AC2.6.5.
- OBJECT: Los botones deshabilitados con motivo no son enfocables con `disabled` nativo y el motivo no llega al lector; propongo AC5.6.4 (`aria-disabled`).
- OBJECT: «Finalizar sesión» y «Finalizar y Consolidar» se confunden; propongo el texto visible «Consolidar reporte» y llevarlo a la tabla de decisiones, porque precisa FR7.1.
