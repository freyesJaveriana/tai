# Lista de accesibilidad — Veridicus (WCAG 2.1 AA)

**Revisión 2 — cambio 01 (DT27, 2026-11-03).** Reemplaza la aprobada el 02/10/2026. Cambios:

- Se retiran las filas del Paquete de Traspaso y del Hecho No Documentado (antes V-3).
- La CoT pasa a ser «observaciones».
- Se añaden M3 con perfil, M7 importación y M8 reportes del investigador.
- Se añaden AC5.6.4 (botones deshabilitados enfocables) y AC5.6.5 (anuncios agregados).
- Se añaden las marcas de cita A y B.

**Insumos.** US5.6 y sus criterios AC5.6.1–AC5.6.5 en `inception/user-stories/stories.md` (stories).
Accesibilidad SHOULD con WCAG 2.1 AA, según `inception/requirements-analysis/requirements.md`
(requirements) §7. Herramientas de `inception/practices-discovery/team-practices.md` (team-practices):
Vitest + React Testing Library y Playwright. Pantallas de `mockups.md` y componentes de
`interaction-spec.md`. Sin `wireframes` ni `user-flow` de Ideation (scope `classic`).

**Alcance.** Las pantallas M0, M1, M3–M8 (M2 retirada). El nivel objetivo es WCAG 2.1 AA, con prioridad
SHOULD (US5.6). Los criterios que además protegen AUTONOMIA-03 se comprueban en nivel 0 en cada PR:
estados que no dependen solo del color, recordatorio de criterio visible y rótulos controlados.

Cada fila nombra cómo se comprueba (AUTONOMIA-02):

- `[N0]` Vitest + React Testing Library.
- `[N3]` Playwright con `@axe-core/playwright`.
- `[Manual]` con la evidencia adjunta al PR.

---

## 1. Perceptible

| # | Criterio WCAG | Aplicación en Veridicus | Comprobación |
|---|---|---|---|
| P-1 | 1.1.1 Contenido no textual | Los iconos de estado llevan `aria-hidden="true"` y texto visible al lado; ningún icono es el único portador de información. | `[N0]` cada StatusBadge renderiza texto no vacío |
| P-2 | 1.3.1 Información y relaciones | Estructura semántica: turnos en `<ol>`, tablas con `<th scope>`, formularios con `<label>` y `<fieldset>`, citas en `<figure>`/`<blockquote>`. Los encabezados van en orden: h1 pantalla, h2 columna, h3 turno, tarjeta o grupo. | `[N3]` axe sin violaciones `serious`/`critical` |
| P-3 | 1.3.2 Secuencia con significado | El orden del DOM es el orden visual en M4: cabecera, avisos de perfil, transcripción, entrada de turnos, franja del modo final y hallazgos. | `[N3]` recorrido con Tab |
| P-4 | 1.4.1 Uso del color | Todo estado de turno, tramo, corrida, hallazgo, sesión y versión combina icono, texto y color (AC5.6.3). El aviso informativo se distingue del error del sistema por icono y texto. Las citas A y B se distinguen por letra y estilo de barra. | `[N0]` AC5.6.3; `[N0]` prueba de distinción de *tokens* |
| P-5 | 1.4.3 Contraste mínimo | Texto ≥ 4.5:1, incluidos el motivo de los botones deshabilitados, los turnos de contexto atenuados y el texto sobre los fondos de cita. Los colores de estado son configurables (P4), y la prueba de contraste impide un valor que no cumpla. | `[N0]` prueba de contraste; `[N3]` axe |
| P-6 | 1.4.4 Cambio de tamaño del texto | Se usan unidades `rem`. A 1280 px con zoom ≤ 150 % no se pierde ninguna función; al 200 % el texto sigue legible y la distribución cae al aviso de < 1024 px (excepción declarada en la tabla de precisiones de `mockups.md`). | `[Manual]` capturas a 150 % y 200 % en M4 y M7 |
| P-7 | 1.4.10 Reajuste | A 1024 px las dos columnas de M4 pasan a pestañas sin desplazamiento horizontal de la página. Las tablas anchas de M8 se desplazan solo dentro de su contenedor (excepción de 1.4.10 para tablas de datos). Por debajo de 1024 px se muestra el aviso sin ocultar contenido. | `[N3]` *viewport* 1024 × 768 |
| P-8 | 1.4.11 Contraste no textual | Bordes de estado, barras de cita, anillo de foco y controles ≥ 3:1. | `[N0]` prueba de contraste |
| P-10 | 1.3.4 Orientación | Ninguna pantalla fija la orientación. | `[N0]` sin reglas CSS de orientación |
| P-11 | 1.3.5 Propósito de la entrada | M0 usa `autocomplete="username"` y `"current-password"`; el diálogo de crear usuario, `"username"` y `"new-password"`. | `[N0]` |
| P-12 | 1.4.12 Espaciado del texto | Con interlineado 1.5, párrafos 2×, letras 0.12em y palabras 0.16em no se corta ni se solapa el texto. | `[N3]` con una hoja de estilos inyectada en M4 |
| P-9 | 1.4.13 Contenido en *hover* o foco | Los *tooltips* se descartan con Escape y no contienen información necesaria. El recordatorio de criterio se ve sin *hover* (AC5.1.5). | `[N0]` AC5.1.5 |

## 2. Operable

| # | Criterio WCAG | Aplicación en Veridicus | Comprobación |
|---|---|---|---|
| O-1 | 2.1.1 Teclado | El flujo completo de AC5.6.2 funciona solo con teclado. Incluye crear la sesión eligiendo perfil, importar y confirmar la vista previa, enviar un turno (`Ctrl+Enter`), lanzar y relanzar el modo final, ir a cada cita y volver, desplegar las observaciones, aceptar, editar, descartar, consolidar y responder a la reanudación. | `[N3]` AC5.6.2 |
| O-2 | 2.1.2 Sin trampas de teclado | Solo los diálogos modales atrapan el foco, y se cierran con Escape. Los paneles y franjas no lo atrapan. | `[N3]` |
| O-3 | 2.2.1 Tiempo ajustable | Ninguna acción del analista tiene límite de tiempo. La suspensión por falta de latido conserva todo y se reanuda (US7.1). | `[N0]` AC7.1.2 |
| O-4 | 2.2.2 Pausar, detener, ocultar | Los cronómetros y los iconos animados respetan `prefers-reduced-motion`, y nada parpadea. | `[N0]` |
| O-5 | 2.4.1 Evitar bloques | «Saltar al contenido» es el primer elemento enfocable. | `[N3]` |
| O-6 | 2.4.2 Título de página | Cada pantalla tiene su propio `<title>`, p. ej. «Sesión · Entrevista-07 · Veridicus», «Importar transcripción · Veridicus» o «Reportes · Veridicus». | `[N0]` |
| O-7 | 2.4.3 Orden del foco | El foco se mueve solo por una acción del usuario. Abrir un formulario en línea lo lleva al primer campo. «Ir a la cita» lo lleva al turno y «Volver al hallazgo» lo devuelve a la tarjeta. Cerrar un diálogo lo devuelve a su disparador. Un hallazgo nuevo **no** mueve el foco (AC3.1.3). | `[N0]` AC3.1.2, AC3.1.3 |
| O-8 | 2.4.6 Encabezados y etiquetas | Los botones tienen nombres que incluyen su objeto, p. ej. «Aceptar sugerencia · citas en los turnos 2 y 214», «Ir a la cita A» o «Seleccionar reporte del 02/11/2026 18:40». | `[N3]` axe |
| O-10 | 2.4.5 Varias vías | Cada pantalla se alcanza por la cabecera y por enlaces desde M1 o M8; la lista de sesiones tiene filtros. | `[N3]` |
| O-11 | 2.5.1–2.5.4 Puntero | Sin gestos de varios puntos ni de trayecto; las acciones se disparan al soltar; el nombre accesible de cada botón contiene su texto visible; no hay control por movimiento. | `[N3]` axe (`label-content-name-mismatch`) |
| O-9 | 2.4.7 Foco visible | `--focus-ring` en todo elemento enfocable, incluidos los botones `aria-disabled`. Se prohíbe `outline: none` sin reemplazo (regla de *lint* de estilos). | `[N3]` AC5.6.2 |

## 3. Comprensible

| # | Criterio WCAG | Aplicación en Veridicus | Comprobación |
|---|---|---|---|
| C-1 | 3.1.1 Idioma de la página | `lang="es"`. | `[N0]` |
| C-2 | 3.2.1 / 3.2.2 Al recibir el foco / al introducir datos | Nada cambia de contexto al enfocar, escribir o elegir un perfil o un archivo. Validar el archivo de M7 muestra la vista previa en la misma página, sin navegar. Enviar, lanzar, guardar, importar y consolidar son acciones explícitas. | `[N3]` |
| C-3 | 3.2.3 Navegación coherente | La cabecera global es idéntica en todas las pantallas autenticadas. Cada rol ve solo sus entradas: analista, M1/M7; admin, M6 y M1 en solo lectura; investigador, M8. | `[N3]` |
| C-8 | 3.2.4 Identificación coherente | El mismo control tiene el mismo nombre en todas las pantallas («Consolidar reporte», «Ir a la cita A», «Relanzar modo final»), porque todos salen del catálogo. | `[N0]` prueba del catálogo |
| C-4 | 3.3.1 Identificación de errores | Los errores se dan en texto junto al campo: nota de descarte vacía, archivo no JSON, primer problema del esquema con el total, límite superado, reporte sin modelo o cuantización. Nunca solo con un borde rojo. | `[N0]` AC5.3.1, AC2.6.2, AC14.3.1 |
| C-5 | 3.3.2 Etiquetas o instrucciones | El formato del contrato común se ve antes de elegir el archivo en M7. El perfil explica en lenguaje llano qué sale del clúster. Cada acción deshabilitada muestra su motivo (AC5.1.1, AC6.1.1, AC13.1.4). | `[N0]` |
| C-6 | 3.3.3 Sugerencias ante errores | Cada error del sistema dice qué pasó y qué hacer: causa del tramo o del modo final con «Reintentar tramo» o «Relanzar modo final» (AC3.2.2). | `[N0]` AC3.2.2 |
| C-7 | 3.3.4 Prevención de errores (legales) | Finalizar y consolidar piden confirmación con el resumen de efectos. Consolidar con un modo final en error avisa y ofrece «Volver y relanzar el modo final» (AC6.1.2). Consolidar no se deshace: se corrige con una versión nueva (AC6.3.3). | `[N0]` AC6.1.2 |

## 4. Robusto

| # | Criterio WCAG | Aplicación en Veridicus | Comprobación |
|---|---|---|---|
| R-1 | 4.1.1 Procesamiento | HTML válido, IDs únicos y sin HTML crudo en el reporte (`react/no-danger` es error). | `[N0]` ESLint |
| R-2 | 4.1.2 Nombre, función, valor | Radix aporta roles y estados: `aria-expanded` de las observaciones y de las corridas, `aria-checked` del perfil, `aria-selected` de las pestañas. Los botones bloqueados usan `aria-disabled="true"`, no `disabled` nativo, siguen enfocables y anuncian su motivo por `aria-describedby` (AC5.6.4). | `[N0]` AC5.6.4; `[N3]` axe |
| R-3 | 4.1.3 Mensajes de estado | Una región `aria-live="polite"` por pantalla anuncia solo cambios agregados: inicio, etapa, fin o error de cada corrida (AC10.1.1, leído por corrida), contador de pendientes, sesión suspendida y, como respuesta a una acción, el resultado de validar un archivo y «SHA-256 copiado». El estado de cada turno se lee al enfocarlo (AC5.6.5). La regla está en la tabla de precisiones de `mockups.md`. Nada roba el foco (AC3.1.3). | `[N0]` AC5.6.5, AC3.1.3, AC10.1.1 |

## 5. Comprobaciones específicas de Veridicus

| # | Comprobación | Origen | Nivel |
|---|---|---|---|
| V-1 | Los únicos rótulos de resultado son «Sugerencia de revisión», «Contradicción en el relato» y los 7 rótulos de tipo del contrato. | AC5.5.4 | `[N0]` |
| V-2 | El catálogo de mensajes y la interfaz renderizada pasan el escaneo de vocabulario prohibido, que excluye las citas literales y el texto del analista. | AC5.5.1 | `[N0]` + `[N3]` |
| V-3 | **Retirada** (cambio 01): el aviso del Hecho No Documentado ya no existe. | — | — |
| V-4 | Ningún hallazgo nuevo ni cambio de corrida abre una ventana modal, emite sonido o mueve el foco. | AC3.1.3 | `[N0]` |
| V-5 | Aceptar y Editar están deshabilitados, con su motivo visible y enfocables, hasta desplegar las observaciones. | AC5.1.1, AC5.6.4 | `[N0]` |
| V-6 | Ningún control de la consola cambia perfiles, proveedores, *prompts* ni límites, con cualquiera de los tres roles. | AC8.3.1 | `[N3]` |
| V-7 | Las fechas visibles están en hora de Colombia `DD/MM/AAAA HH:mm`, y las marcas de consolidación del reporte añaden la hora UTC. | P5 | `[N0]` |
| V-8 | La CI falla si un cambio de color rompe el contraste, iguala el aviso informativo con el error del sistema o iguala las barras de las citas A y B. | P4, P7 | `[N0]` con control negativo (un *fixture* de colores inválidos) |
| V-9 | La cita A y la cita B se identifican por letra y estilo de barra sin color: el *snapshot* en escala de grises las distingue. | AC3.1.2, AC5.6.3 | `[N0]` |
| V-10 | La importación de una transcripción de cientos de turnos produce como máximo un anuncio por cambio agregado, nunca uno por turno. | AC5.6.5 | `[N0]` |

## 6. Pantallas cubiertas por el barrido automático

AC5.6.1 exige 0 violaciones `serious` o `critical` con `@axe-core/playwright` (etiquetas `wcag2a`,
`wcag2aa`, `wcag21a`, `wcag21aa`) en estas pantallas:

- M0 inicio de sesión.
- M1 lista de sesiones.
- M3 nueva sesión con el perfil elegido y sus detalles abiertos.
- M7 importación con la vista previa.
- M4 con al menos un hallazgo pendiente y la cita A resaltada.
- M4 con el modo final en error.
- El diálogo de consolidación.
- M5 reporte consolidado.

Por cobertura se añaden M6 usuarios y M8 lista, detalle y comparación. Comando previsto:
`npx --prefix frontend playwright test e2e/a11y.spec.ts` `[N3]`.

## 7. Verificación manual antes de la sustentación

- Recorrido del flujo de punta a punta (guiado e importado) con NVDA u Orca, que lea cada estado, cada
  cita y cada anuncio en vivo. Evidencia: grabación o notas adjuntas al PR de la entrega `[Manual]`.
- Zoom al 200 % en M4 y M7 a 1280 px. Evidencia: captura `[Manual]`.
- Revisión visual de los colores por defecto de estado y de cita. Si no resultan adecuados, se ajustan en
  `state-colors.css` por PR (P4), y la prueba de contraste debe seguir en verde.
