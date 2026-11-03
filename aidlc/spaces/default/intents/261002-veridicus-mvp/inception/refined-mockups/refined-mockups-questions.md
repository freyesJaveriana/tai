# Preguntas — Mockups Refinados (Veridicus)

No hay bocetos de Ideation (el scope `classic` la omite), así que diseño las pantallas directamente desde
`inception/user-stories/stories.md` y `requirements.md`. Lo que las historias ya fijan no se vuelve a
preguntar: estados de cada pantalla, textos visibles, WCAG 2.1 AA (US5.6), confirmaciones, solo lectura
de sesiones ajenas y el aviso del Hecho No Documentado.

Estas 5 preguntas cubren lo que las historias no deciden: componentes, distribución, tamaños de pantalla,
colores de estado y formato de fechas.

## Cómo responder

- Escribe la letra después de `[Answer]:`, en la misma línea o en la siguiente.
- La opción **(Recomendada)** es mi propuesta; no está aplicada todavía.
- Si ninguna opción encaja, usa `X` y escribe la tuya.

---

### Pregunta 1 — ¿Sobre qué construimos los componentes de la interfaz?

El equipo fijó React con TypeScript estricto, pero no una biblioteca de componentes. La accesibilidad AA
(US5.6) es más barata con componentes que ya resuelven foco, teclado y ARIA.

A. **Primitivas accesibles sin estilo (Radix UI)** y una capa propia de componentes con *tokens* de diseño en CSS; sin tema visual de terceros **(Recomendada)**
B. Una biblioteca completa con tema propio (MUI).
C. Solo elementos HTML nativos y CSS propio, sin biblioteca.
X. Other (please specify)

[Answer]: A

### Pregunta 2 — ¿Cómo se distribuye la pantalla de sesión?

Es la pantalla donde el analista pasa casi todo el tiempo: transcripción, alertas, CoT y paquete de
traspaso.

A. **Dos columnas**: transcripción por turnos a la izquierda y panel de sugerencias de revisión a la derecha (con la CoT plegable dentro de cada tarjeta); el Paquete de Contexto de Traspaso se abre como panel lateral sobre la columna derecha sin tapar la transcripción; la entrada de turnos queda fija abajo a la izquierda **(Recomendada)**
B. Una sola columna con pestañas «Transcripción» y «Sugerencias».
C. Tres columnas fijas: transcripción, sugerencias y paquete de traspaso.
X. Other (please specify)

[Answer]: A

### Pregunta 3 — ¿En qué tamaños de pantalla debe funcionar?

El analista trabaja en una estación de escritorio; la sustentación se hace con un proyector o una pantalla
de portátil.

A. **Escritorio**: diseño principal a 1280 px o más; usable sin pérdida de funciones hasta 1024 px (las dos columnas pasan a pestañas); sin diseño para teléfonos ni tabletas **(Recomendada)**
B. Escritorio y tableta (768 px o más).
C. Totalmente adaptable, incluidos teléfonos.
X. Other (please specify)

[Answer]: A

### Pregunta 4 — ¿Qué colores usan los estados del resultado?

El PRD (Journey 1 y 4) usa amarillo para las sugerencias de revisión y rojo para el Hecho No Documentado.
Las historias exigen que ningún estado dependa solo del color (AC5.6.3) y que el Hecho No Documentado no
use el estilo de error del sistema (AC4.2.2).

A. **Se mantienen los colores del PRD** (ámbar para las sugerencias, rojo para el Hecho No Documentado), siempre con icono y texto; los errores del sistema (turno en «Error», fallos de carga) usan otro tratamiento: borde gris oscuro, icono de advertencia y texto **(Recomendada)**
B. Se cambia el Hecho No Documentado a un color neutro de atención (azul o violeta) para no asociarlo con un error, y se corrige el PRD en su propio commit.
C. Sin colores de estado: solo iconos y texto.
X. Other (please specify)

[Answer]: X. A, pero con los colores de estado como parámetro configurable (tokens de diseño), por si no resultan adecuados al visualizarlos. Texto del humano: «Usa los colores propuestos en la etapa A, solo que déjalo como un posible parámetro configurable, en caso que los colores no sean adecuados cuando ya los visualicemos.»

### Pregunta 5 — ¿Cómo se muestran fechas y horas?

El sistema guarda todo en UTC (US2.4, US8.4); el reporte y la interfaz las muestran a personas en Colombia.

A. **Hora de Colombia** (`America/Bogota`), formato `DD/MM/AAAA HH:mm` de 24 horas, en la interfaz y en el reporte; el reporte añade también la hora UTC en las marcas de consolidación **(Recomendada)**
B. Todo en UTC, con la etiqueta «UTC».
C. La zona horaria del navegador del analista.
X. Other (please specify)

[Answer]: A

---

## Segunda pasada — cambio 01 (DT27, 2026-11-02)

Las respuestas 1, 3 y 5 siguen vigentes. La 2 y la 4 siguen con estos ajustes:

- **Respuesta 2:** la «CoT» pasa a ser las **observaciones** de cada hallazgo. El Paquete de Contexto de
  Traspaso se retira con la épica 4, y con él su panel lateral.
- **Respuesta 4:** se retira el rojo del Hecho No Documentado. El ámbar de las sugerencias y el
  tratamiento de los errores del sistema siguen, y los colores siguen siendo *tokens* configurables por PR.

Se retira la pantalla M2 (Escenarios de control, épica 1). Las historias de la revisión 2 ya fijan los
textos, los estados, los motivos de los botones deshabilitados y la accesibilidad. Estas seis preguntas
cubren lo que no deciden: dónde se importa, cómo se ven las dos citas, dónde vive el modo final, cómo se
ordena el panel de hallazgos, la experiencia de la línea de comandos y el lienzo visual.

### Pregunta 6 — ¿Dónde importa el analista una transcripción?

US2.6 pide importar un archivo del contrato común, con vista previa, y crear la sesión **cerrada a turnos
nuevos**. US13.1 pide elegir el perfil al crear la sesión.

A. **En «Nueva sesión» (M3)**: primero el origen («Guiada» o «Importar archivo»); con «Importar archivo» aparece el selector de archivo y una vista previa (entrevista, número de turnos, páginas, primeros turnos o el primer error con el total), y después el perfil; «Crear sesión» crea la sesión ya cargada **(Recomendada)**
B. Una pantalla aparte «Importar transcripción», con su propio botón en la lista de sesiones.
C. Arrastrar el archivo sobre la lista de sesiones, que abre el formulario de M3 ya relleno.
X. Other (please specify)

[Answer]: B

### Pregunta 7 — ¿Cómo ve el analista dos citas que pueden estar a cientos de turnos?

AC3.1.2 pide resaltar las dos citas con «A» y «B» y saltar de una a otra. En una transcripción importada
larga, las dos citas casi nunca caben a la vez en pantalla.

A. **La tarjeta muestra las dos citas completas, cada una con su turno anterior y siguiente como contexto, y los botones «Ir a la cita A» e «Ir a la cita B»** que desplazan la transcripción y resaltan el turno; la transcripción no se divide **(Recomendada)**
B. Al seleccionar un hallazgo, la transcripción se divide en dos paneles sincronizados: arriba la cita A y abajo la cita B.
C. Solo los botones de salto, sin contexto en la tarjeta.
X. Other (please specify)

[Answer]: A

### Pregunta 8 — ¿Dónde se lanza y se sigue el modo final?

US2.7 pide lanzar, ver el estado («En cola», «Procesando», «Terminado», «Con error») y relanzar el modo
final. AC6.1.2 menciona el registro de corridas.

A. **Una franja fija encima del panel de hallazgos** con el estado del modo final, su progreso (US10.1) y el botón «Lanzar modo final» o «Relanzar modo final»; debajo, un desplegable «Corridas» con cada corrida incremental y final, su estado, su código de error y quién la lanzó **(Recomendada)**
B. Una pestaña «Corridas» aparte, con el botón del modo final dentro.
C. Solo un botón en la barra superior de la sesión, con el estado como insignia.
X. Other (please specify)

[Answer]: A

### Pregunta 9 — ¿Cómo se ordena el panel de hallazgos?

El modo final puede traer decenas de hallazgos de una vez, y el contador de pendientes enlaza al primero
(AC6.1.1).

A. **Pendientes primero**; dentro de cada grupo, por el turno de la cita A; con filtros por estado, por tipo (los 7) y por origen (incremental o final), y un resumen «N pendientes · N aceptadas · N editadas · N descartadas» **(Recomendada)**
B. Por orden de llegada, el más reciente arriba, sin agrupar.
C. Agrupados por tipo de contradicción.
X. Other (please specify)

[Answer]: A

### Pregunta 10 — ¿Esta etapa diseña también la experiencia de la línea de comandos?

La etapa diseña las interfaces que usan personas. El Investigador del TG (P4) usa la CLI (épica 12), no
la consola.

A. **Sí, una sección corta**: los comandos y sus opciones, la ayuda, el resumen que imprime al terminar (hallazgos, citas rechazadas, modo fragmentado, *tokens* y costo), los códigos de salida y los mensajes en español; el detalle técnico queda para Functional Design **(Recomendada)**
B. No: la CLI se diseña entera en Functional Design de su unidad.
X. Other (please specify)

[Answer]: X. Texto del humano: «Si me interesaría una consola básica para el investigador + línea de comandos para todo lo demás. El momento más adecuado de diseñar la experiencia de la CLI puede ser el Functional Design de esa unidad»

### Pregunta 11 — ¿Actualizo el lienzo visual de las maquetas?

En la primera pasada se publicó un lienzo visual privado (`maqueta-visual.md`). Ahora muestra pantallas
retiradas (M2 y el Paquete de Traspaso).

A. **Sí, después de que apruebes los artefactos Markdown**: actualizo el mismo lienzo con las pantallas de la revisión 2, y la fuente de verdad sigue siendo el Markdown **(Recomendada)**
B. Sí, ahora, como parte de esta etapa y antes de la aprobación.
C. No: lo marco como desactualizado en `maqueta-visual.md`.
X. Other (please specify)

[Answer]: B

### Seguimiento 7 — ¿Qué hace la consola básica del investigador?

Respuesta 10: consola básica para el Investigador del TG; la línea de comandos sigue para todo lo demás y
su experiencia se diseña en Functional Design. Ninguna historia ni ningún requisito aprobado cubre esta
consola, así que entra como precisión en la tabla de esta etapa y tú decides en la aprobación si se
actualizan `stories.md` y `requirements.md`. La CLI corre sin infraestructura (DT26), así que la consola
solo ve lo que se le sube.

A. **Solo consulta**: el investigador sube el reporte JSON de una corrida o de una evaluación de la CLI (o de ZINE) y la consola lo muestra: perfil, `config_sha256`, `prompt_sha256`, registro de modelos, *tokens* y costo, métricas de evaluación, y la comparación lado a lado de dos reportes; no lanza análisis **(Recomendada)**
B. Consulta y lanzamiento: además de A, lanza desde la consola la evaluación sobre el conjunto sintético con un perfil aprobado.
C. Solo las corridas de la propia consola (sesiones del analista), sin subir reportes de la CLI.
X. Other (please specify)

[Answer]: A

### Seguimiento 8 — ¿Con qué rol entra el investigador?

FR1 define dos roles: `analista` y `admin`.

A. **Un rol nuevo `investigador`**: ve solo su consola; no crea sesiones, no ve las transcripciones de las sesiones ni cambia hallazgos ni usuarios **(Recomendada)**
B. El rol `analista`, con la consola del investigador como una sección más.
C. El rol `admin`.
X. Other (please specify)

[Answer]: A
