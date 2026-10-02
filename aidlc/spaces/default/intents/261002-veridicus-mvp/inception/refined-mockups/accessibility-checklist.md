# Lista de accesibilidad — Veridicus (WCAG 2.1 AA)

**Insumos.** US5.6 y sus criterios AC5.6.1–AC5.6.3 en `inception/user-stories/stories.md` (stories);
la pregunta abierta de accesibilidad de `inception/requirements-analysis/requirements.md` §7
(requirements), cerrada en User Stories como SHOULD con WCAG 2.1 AA; herramientas de
`inception/practices-discovery/team-practices.md` (team-practices: Vitest + React Testing Library,
Playwright); pantallas de `mockups.md` y componentes de `interaction-spec.md`. Sin `wireframes` ni
`user-flow` de Ideation (scope `classic`).

**Alcance.** Las pantallas M0–M6. Nivel objetivo: WCAG 2.1 AA. Prioridad SHOULD (US5.6); los criterios
que además protegen AUTONOMIA-03 (estados no solo por color, recordatorio visible, rótulos controlados)
se comprueban en nivel 0 en cada PR.

Cada fila nombra cómo se comprueba (AUTONOMIA-02): `[N0]` Vitest + React Testing Library, `[N3]`
Playwright con `@axe-core/playwright`, `[Manual]` con evidencia adjunta al PR.

---

## 1. Perceptible

| # | Criterio WCAG | Aplicación en Veridicus | Comprobación |
|---|---|---|---|
| P-1 | 1.1.1 Contenido no textual | Iconos de estado `aria-hidden="true"` con texto visible al lado; ningún icono es el único portador de información. | `[N0]` cada StatusBadge renderiza texto no vacío |
| P-2 | 1.3.1 Información y relaciones | Turnos en `<ol>`, tablas con `<th scope>`, formularios con `<label>`, encabezados en orden (h1 pantalla, h2 columna, h3 turno/tarjeta). | `[N3]` axe sin violaciones `serious`/`critical` |
| P-3 | 1.3.2 Secuencia con significado | Orden del DOM = orden visual: cabecera → transcripción → entrada de turnos → sugerencias. | `[N3]` recorrido con Tab |
| P-4 | 1.4.1 Uso del color | Todo estado de turno, alerta, sesión y versión = icono + texto + color (AC5.6.3); el Hecho No Documentado se distingue del error del sistema por icono y texto (AC4.2.2); el resaltado del fragmento usa fondo + subrayado. | `[N0]` AC5.6.3; `[N0]` prueba de distinción de *tokens* |
| P-5 | 1.4.3 Contraste mínimo | Texto ≥ 4.5:1, incluido el motivo visible de los botones deshabilitados. Los colores de estado son configurables (P4) y la prueba de contraste impide un valor que no cumpla. | `[N0]` prueba de contraste de `state-colors.css`; `[N3]` axe |
| P-6 | 1.4.4 Cambio de tamaño del texto | Al 200 % de zoom el texto sigue legible y ninguna función se pierde; unidades `rem`. | `[Manual]` captura a 200 % en M4 |
| P-7 | 1.4.10 Reajuste | A 1024 px las dos columnas pasan a pestañas sin desplazamiento horizontal; por debajo, aviso sin ocultar contenido. | `[N3]` *viewport* 1024 × 768 |
| P-8 | 1.4.11 Contraste no textual | Bordes de estado, anillo de foco y controles ≥ 3:1. | `[N0]` prueba de contraste |
| P-9 | 1.4.13 Contenido en *hover* o foco | Los *tooltips* se pueden descartar con Escape y no contienen información necesaria; el recordatorio de criterio está visible sin *hover* (AC5.1.5). | `[N0]` AC5.1.5 |

## 2. Operable

| # | Criterio WCAG | Aplicación en Veridicus | Comprobación |
|---|---|---|---|
| O-1 | 2.1.1 Teclado | Flujo de texto completo solo con teclado: enviar turno, desplegar CoT, aceptar, editar, descartar, finalizar y consolidar (AC5.6.2). `Ctrl+Enter` envía el turno. | `[N3]` AC5.6.2 |
| O-2 | 2.1.2 Sin trampas de teclado | El panel del Paquete de Traspaso es no modal y no atrapa el foco; los diálogos modales sí lo atrapan y se cierran con Escape. | `[N3]` |
| O-3 | 2.2.1 Tiempo ajustable | Ninguna acción del analista tiene límite de tiempo; la suspensión por falta de latido conserva todo y se reanuda (US7.1). | `[N0]` AC7.1.2 |
| O-4 | 2.2.2 Pausar, detener, ocultar | El cronómetro de procesamiento y los iconos animados respetan `prefers-reduced-motion`; no hay contenido que parpadee. | `[N0]` |
| O-5 | 2.4.1 Evitar bloques | «Saltar al contenido» es el primer elemento enfocable. | `[N3]` |
| O-6 | 2.4.2 Título de página | Cada pantalla tiene `<title>` propio («Sesión · Masacre-X v2 · Veridicus»). | `[N0]` |
| O-7 | 2.4.3 Orden del foco | Abrir un formulario en línea lleva el foco a su primer campo; cerrar paneles y diálogos devuelve el foco al disparador; una alerta nueva **no** mueve el foco (AC3.1.7). | `[N0]` AC3.1.7, AC4.2.3 |
| O-8 | 2.4.6 Encabezados y etiquetas | Botones con nombre que incluye el turno («Aceptar sugerencia del turno 2»). | `[N3]` axe |
| O-9 | 2.4.7 Foco visible | `--focus-ring` en todo elemento enfocable; prohibido `outline: none` sin reemplazo (regla de *lint* de estilos). | `[N3]` AC5.6.2 |

## 3. Comprensible

| # | Criterio WCAG | Aplicación en Veridicus | Comprobación |
|---|---|---|---|
| C-1 | 3.1.1 Idioma de la página | `lang="es"`. | `[N0]` |
| C-2 | 3.2.1 / 3.2.2 Al recibir el foco / al introducir datos | Nada cambia de contexto al enfocar o escribir; enviar, guardar y consolidar son acciones explícitas. | `[N3]` |
| C-3 | 3.2.3 Navegación coherente | Cabecera global idéntica en todas las pantallas autenticadas. | `[N3]` |
| C-4 | 3.3.1 Identificación de errores | Errores en texto junto al campo («Escribe por qué descartas esta sugerencia», mensajes de carga de AC1.1.2), no solo con borde rojo. | `[N0]` AC5.3.1, AC1.1.2 |
| C-5 | 3.3.2 Etiquetas o instrucciones | Formato de carga visible antes de elegir archivo; motivo visible de cada acción deshabilitada (AC5.1.1, AC6.1.1). | `[N0]` |
| C-6 | 3.3.3 Sugerencias ante errores | Cada error del sistema dice qué pasó y qué hacer («Puedes reintentar»). | `[N0]` AC3.2.2 |
| C-7 | 3.3.4 Prevención de errores (legales) | Finalizar y consolidar piden confirmación con el resumen de efectos; consolidar no se deshace, se corrige con versión nueva (AC6.1.2, AC6.3.3). | `[N0]` AC6.1.2 |

## 4. Robusto

| # | Criterio WCAG | Aplicación en Veridicus | Comprobación |
|---|---|---|---|
| R-1 | 4.1.1 Procesamiento | HTML válido, IDs únicos, sin HTML crudo en el reporte (`react/no-danger` es error). | `[N0]` ESLint |
| R-2 | 4.1.2 Nombre, función, valor | Radix aporta roles y estados (`aria-expanded` de la CoT, `aria-selected` de pestañas); botones bloqueados con `aria-disabled` + `aria-describedby` al motivo. | `[N3]` axe |
| R-3 | 4.1.3 Mensajes de estado | Una región `aria-live="polite"` por pantalla anuncia turnos evaluados, contador de pendientes, etapa de procesamiento y SHA-256 copiado, sin robar el foco (AC3.1.7, AC10.1.1). | `[N0]` AC3.1.7, AC10.1.1 |

## 5. Comprobaciones específicas de Veridicus

| # | Comprobación | Origen | Nivel |
|---|---|---|---|
| V-1 | Los únicos rótulos de resultado son «Sugerencia de revisión», «Incongruencia semántica» y «Hecho No Documentado». | AC5.5.4 | `[N0]` |
| V-2 | El catálogo de mensajes y la interfaz renderizada pasan el escaneo de vocabulario prohibido (excluye citas literales y texto del analista). | AC5.5.1 | `[N0]` + `[N3]` |
| V-3 | El aviso del Hecho No Documentado coincide carácter por carácter con «La IA no puede validar este fragmento de forma autónoma. Control manual requerido». | AC4.2.2 | `[N0]` |
| V-4 | Ninguna alerta abre ventana modal, emite sonido ni mueve el foco. | AC3.1.7 | `[N0]` |
| V-5 | Aceptar y Editar están deshabilitados con su motivo visible hasta desplegar la CoT. | AC5.1.1 | `[N0]` |
| V-6 | Ningún control de la consola cambia el umbral, con ambos roles. | AC8.3.1 | `[N3]` |
| V-7 | Fechas visibles en hora de Colombia `DD/MM/AAAA HH:mm`; marcas de consolidación del reporte con hora UTC añadida. | P5 | `[N0]` |
| V-8 | Cambiar un color de estado que rompa el contraste o iguale el Hecho No Documentado con el error del sistema hace fallar la CI. | P4, AC4.2.2 | `[N0]` con control negativo (un *fixture* de colores inválidos) |

## 6. Pantallas cubiertas por el barrido automático

AC5.6.1 exige 0 violaciones `serious` o `critical` con `@axe-core/playwright` (etiquetas `wcag2a`,
`wcag2aa`, `wcag21a`, `wcag21aa`) en: M0 inicio de sesión, M1 lista de sesiones, M4 sesión con al menos
una sugerencia pendiente, M4 con el Paquete de Traspaso abierto, el diálogo de consolidación y M5
reporte consolidado. Se añaden M2 escenarios y M6 usuarios por cobertura. Comando previsto:
`npx --prefix frontend playwright test e2e/a11y.spec.ts` `[N3]`.

## 7. Verificación manual antes de la sustentación

- Recorrido del flujo de texto con NVDA o Orca leyendo cada estado y cada anuncio en vivo; evidencia:
  grabación o notas adjuntas al PR de la entrega `[Manual]`.
- Zoom al 200 % en M4 a 1280 px; evidencia: captura `[Manual]`.
- Revisión visual de los colores de estado por defecto; si no resultan adecuados, se ajustan en
  `state-colors.css` mediante PR (P4) y la prueba de contraste debe seguir en verde.
