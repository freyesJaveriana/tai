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
