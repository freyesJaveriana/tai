# Mapa del sistema de diseño — Veridicus

**Revisión 2 — cambio 01 (DT27, 2026-11-03).** Reemplaza la aprobada el 02/10/2026. Se retiran el
*token* rojo del Hecho No Documentado y el panel del Paquete de Traspaso. Se añaden las marcas de cita A
y B, el tratamiento informativo de los avisos de perfil y las primitivas de M3, M7 y M8.

**Insumos.** Respuestas P1–P11 y seguimientos 7 y 8 de `refined-mockups-questions.md`. Componentes de
`interaction-spec.md`. Prácticas de `inception/practices-discovery/team-practices.md` (team-practices):
React + TypeScript estricto, ESLint + Prettier, `react/no-danger`, Vitest + React Testing Library y
Playwright. Requisito de idioma NFR14 de `inception/requirements-analysis/requirements.md`
(requirements). Criterios de accesibilidad de US5.6 en `inception/user-stories/stories.md` (stories).
No hay sistema de diseño previo: el proyecto es greenfield y no hay `wireframes` ni `user-flow` de
Ideation.

---

## 1. Decisión de base (P1, se mantiene)

- **Primitivas:** Radix UI sin estilo, que resuelve el foco, el teclado y el ARIA de los componentes
  complejos.
- **Capa propia:** los componentes de Veridicus viven en `frontend/src/components/` y se estilan solo
  con *tokens* CSS (propiedades personalizadas) definidos en `frontend/src/theme/`. No se usa un tema
  visual de terceros ni una biblioteca de estilos completa.
- **Elementos nativos primero:** botones, enlaces, formularios, tablas, listas, casillas, `<select>` y
  el campo de archivo usan HTML nativo. Radix se usa solo donde HTML no basta: diálogos, plegables,
  pestañas y grupos de opciones.
- Las versiones de las dependencias se fijan en el lockfile y entran por PR, como cualquier dependencia
  (team-practices, Code Style).

## 2. Componentes de Veridicus → primitivas

| Componente (`interaction-spec.md`) | Base | Notas |
|---|---|---|
| 4.1 StatusBadge | `<span>` nativo | Icono `aria-hidden` + texto. |
| 4.2 TurnComposer | `<form>` + `<textarea>` + radios nativos «Hablante» + `<button>` | Sin Radix. |
| 4.3 TurnItem | `<li>` en `<ol>`, `<mark>` para la cita | Marca A o B por letra y por estilo de barra (§3.3). |
| 4.4 ReviewSuggestionCard | `<article>` + Radix `Collapsible` (observaciones) | Formularios en línea nativos. |
| 4.5 HandoffPanel | **Retirado** | — |
| 4.6 PasteTranscriptDialog | Radix `Dialog` modal | Atrapa el foco. |
| 4.7 ConfirmDialog | Radix `AlertDialog` | Foco inicial en «Cancelar». |
| 4.8 ConsolidateAction | `<button aria-disabled>` nativo | Lista de motivos con `aria-describedby`. |
| 4.9 NeutralClarification | `<section>` + `<button>` nativos | El audio solo se reproduce al pulsar «Escuchar audio». |
| 4.10 ReportView | Renderizador de Markdown sin HTML crudo | Cumple `react/no-danger`. |
| 4.11 ProfilePicker | Radix `RadioGroup` + `Collapsible` por opción | Ninguna opción viene marcada. |
| 4.12 TranscriptImport | `<form>` + dos `<fieldset>` + `<input type="file" accept="application/json">` | Valida con el mismo esquema que el servidor. |
| 4.13 QuoteBlock | `<figure>` + `<figcaption>` + `<blockquote>` | Contexto atenuado con contraste ≥ 4.5:1. |
| 4.14 FinalModeBar + RunsDisclosure | `<section>` + Radix `Collapsible` + `<table>` nativa | El progreso se da en texto y no solo como barra. |
| 4.15 FindingsFilters | Tres `<select>` nativos + `<button>` | El resumen no cambia con los filtros. |
| 4.16 ProfileNotices | `<div role="note">` | Tratamiento informativo (§3.1); no se puede cerrar. |
| 4.17 ResearchReports | `<table>` nativas + casillas + Radix `Dialog` (subir) | Celdas «=» / «≠» con texto accesible. |
| Pestañas a 1024–1279 px | Radix `Tabs` | Flechas para cambiar y Tab para entrar al panel. |
| Filtros de M1 | `<select>` nativos (estado, origen, perfil) | Se retira el `ToggleGroup`. |
| Copiar SHA-256 | `<button>` nativo + región en vivo | Anuncia «SHA-256 copiado». |
| Indicaciones breves | Radix `Tooltip` solo como complemento | Ninguna información necesaria vive solo en un *tooltip* (AC5.1.5). |
| Tablas (M1, M6, M8) | `<table>` nativa | Encabezados `<th scope>`. |

## 3. *Tokens* de diseño

Todos los valores viven en `frontend/src/theme/tokens.css`. Los componentes nunca usan colores ni
medidas literales; lo comprueba una regla de *lint* de estilos en la CI.

### 3.1 Colores de estado: parámetro configurable (P4)

Los colores de estado son el **valor por defecto**, no un valor fijo. Se agrupan en un único archivo
`frontend/src/theme/state-colors.css` (importado por `tokens.css`), para cambiarlos sin tocar
componentes. Cambiar un color es un PR que edita solo ese archivo, y la prueba de contraste impide
fusionar un valor que rompa WCAG 2.1 AA.

| Token | Uso | Valor por defecto (propuesto) | Icono fijo | Texto fijo |
|---|---|---|---|---|
| `--state-suggestion-fg` / `-bg` / `-border` | Sugerencia de revisión (hallazgo pendiente) | ámbar, p. ej. texto `#7A4B00` sobre `#FFF4D6`, borde `#B26B00` | ◆ | «Sugerencia de revisión» |
| `--state-system-error-fg` / `-bg` / `-border` | Error del sistema: tramo no evaluado, modo final con error, fallos de carga | borde gris oscuro `#3D3D3D`, fondo `#F2F2F2`, texto `#1F1F1F` | ⚠ | «Error», «Tramo no evaluado», «Modo final con error» |
| `--state-info-fg` / `-bg` / `-border` | Avisos de perfil (ventanas, misma familia), cita en turno del entrevistador o plegado, sesión importada | azul grisáceo, p. ej. texto `#24405E` sobre `#EEF3F8`, borde `#5B7A99` | ⓘ | según aviso |
| `--state-success-*` | Analizado, Aceptada, Modo final terminado | verde oscuro, p. ej. `#1E6B3A` | ✓ | según estado |
| `--state-neutral-*` | En cola, Pendiente, Finalizada, No lanzado | gris, p. ej. `#4A4A4A` | ◷ / ■ | según estado |
| `--state-progress-*` | Procesando | azul, p. ej. `#1F4E99` | ⟳ | según estado |
| `--state-locked-*` | Consolidada, bloqueada | gris azulado, p. ej. `#3B4A5C` | 🔒 / ▣ | según estado |
| (reutilizan `--state-success-*`) | Editada | verde oscuro | ✎ | «Editada» |
| (reutilizan `--state-neutral-*`) | Descartada, Suspendida, Desactivado | gris | ✕ / ‖ | según estado |
| (reutilizan `--state-progress-*`) | Abierta | azul | ◐ | «Abierta» |
| (sin color de estado) | Origen Importada / Guiada | texto principal | ⬆ / ✎ | «Importada» / «Guiada» |
| ~~`--state-undocumented-*`~~ | **Retirado** (cambio 01): no hay Hecho No Documentado | — | — | — |

Reglas:

- **El aviso informativo nunca usa los *tokens* de error del sistema.** Un análisis por ventanas o una
  misma familia no son fallos: se diferencian por icono (ⓘ frente a ⚠), texto y color.
- **Prueba de contraste `[N0]`.** Una prueba de Vitest lee `state-colors.css` y falla si algún par
  `fg`/`bg` baja de 4.5:1 o si algún `border` baja de 3:1 frente a `--surface-card`. Se ejecuta con
  `npm --prefix frontend run test -- theme/contrast`.
- **Prueba de distinción `[N0]`.** Falla si `--state-info-*` y `--state-system-error-*` resuelven al
  mismo valor, o si dos estados distintos comparten a la vez icono **y** texto (el icono puede repetirse
  entre familias de estado; el texto siempre los distingue).
- Los colores son de compilación (CSS), no de ejecución. Ninguna pantalla de la consola los cambia, y
  ningún cambio de color se aplica sin PR (coherente con team-practices).

### 3.2 Superficies, texto y foco

| Token | Valor propuesto | Uso |
|---|---|---|
| `--surface-page` | `#FAFAF8` | Fondo de página. |
| `--surface-card` | `#FFFFFF` | Tarjetas, paneles y diálogos. |
| `--text-primary` | `#1A1A1A` | Texto principal (≥ 15:1). |
| `--text-secondary` | `#555555` | `code` de errores, metadatos y turnos de contexto (≥ 7:1). |
| `--focus-ring` | `2px solid #1F4E99`, separación 2 px | Foco visible en todo elemento enfocable (≥ 3:1). |

### 3.3 Marcas de cita A y B (P7)

Las dos citas de un hallazgo se distinguen en la tarjeta y en la transcripción por **letra**, por
**estilo de barra** y por color. La letra y el estilo de barra bastan sin color (AC5.6.3, WCAG 1.4.1).

| Token | Cita A | Cita B |
|---|---|---|
| `--quote-a-bg` / `--quote-b-bg` | fondo `#FFE58A` | fondo `#D9ECFF` |
| `--quote-a-bar` / `--quote-b-bar` | barra izquierda **continua** de 4 px `#8A6D00` | barra izquierda **discontinua** de 4 px `#1F4E99` |
| `--quote-a-underline` / `--quote-b-underline` | subrayado continuo | subrayado punteado |
| Letra | «A» en una pastilla al inicio de la cita | «B» en una pastilla al inicio de la cita |

La prueba de contraste cubre el texto sobre cada fondo de cita (≥ 4.5:1) y cada barra (≥ 3:1). La
prueba de distinción falla si las dos citas comparten estilo de barra.

### 3.4 Tipografía y espaciado

- Familia: pila del sistema (`system-ui`), sin fuentes descargadas en ejecución. Texto base de 16 px,
  secundario de 14 px y títulos de 20/24 px, con interlineado de 1.5. Las cifras de las tablas de M8 usan
  `font-variant-numeric: tabular-nums`.
- Escala de espaciado: 4, 8, 16, 24, 32 y 48 px (`--space-1` … `--space-6`).
- Tamaño mínimo de un objetivo interactivo: 32 × 32 px en escritorio. Se toma como referencia WCAG 2.5.8
  AA de la versión 2.2, porque 2.1 AA no fija un mínimo para puntero.

## 4. Puntos de quiebre (P3, se mantiene)

| Nombre | Rango | Distribución |
|---|---|---|
| `--bp-wide` | ≥ 1280 px | Dos columnas (56 % / 44 %) en M4; es el diseño principal. |
| `--bp-narrow` | 1024–1279 px | Pestañas «Transcripción» / «Hallazgos» con la misma funcionalidad; las tablas de M8 se desplazan dentro de su contenedor. |
| fuera de alcance | < 1024 px | Aviso «Veridicus está diseñado para pantallas de escritorio (1024 px o más)», sin diseño propio. |

Con el navegador al 200 % de zoom sobre 1280 px quedan 640 px CSS. El contenido debe seguir legible y
operable (WCAG 1.4.4) aunque la distribución caiga al aviso; ver `accessibility-checklist.md` §1 (P-6) y la excepción de la tabla de precisiones de
`mockups.md`.

## 5. Fechas y horas (P5, se mantiene)

- Una sola utilidad `formatDateTime(utcIso: string, { withUtc?: boolean })` produce `DD/MM/AAAA HH:mm`
  con `Intl.DateTimeFormat` (`es-CO`, `timeZone: 'America/Bogota'`, 24 h). La opción `withUtc` añade
  ` (HH:mm UTC)` a las marcas de consolidación del reporte.
- El servidor genera las fechas del reporte con la misma regla (zona `America/Bogota`). El formato se
  fija en `contracts/` para que el frontend y el backend lo compartan.

## 6. Idioma y glosario

- El documento lleva `lang="es"`, y todos los textos visibles salen en español del catálogo de mensajes
  (NFR14). Las claves del catálogo y los nombres de componentes van en inglés según el glosario de
  team-practices (p. ej. «sugerencia de revisión» → `review_suggestion`, «contradicción en el relato» →
  `narrative_contradiction`, «cita» → `quote`, «modo final» → `final_mode`, «tramo» → `segment`).
- Los rótulos de los 7 tipos de contradicción salen del contrato común y no se traducen en la
  interfaz.
- El catálogo se escanea con la lista versionada de vocabulario prohibido (AC5.5.1 `[N0]`).
