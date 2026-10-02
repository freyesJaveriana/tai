# Mapa del sistema de diseño — Veridicus

**Insumos.** Respuestas P1, P3, P4 y P5 de `refined-mockups-questions.md`; componentes de
`interaction-spec.md`; prácticas de `inception/practices-discovery/team-practices.md` (team-practices:
React + TypeScript estricto, ESLint + Prettier, `react/no-danger`, Vitest + React Testing Library,
Playwright); requisito de idioma NFR14 de `inception/requirements-analysis/requirements.md`
(requirements) y criterios de accesibilidad de US5.6 en `inception/user-stories/stories.md` (stories).
No hay sistema de diseño previo: el proyecto es greenfield y no hay `wireframes` ni `user-flow` de
Ideation.

---

## 1. Decisión de base (P1)

- **Primitivas:** Radix UI (sin estilo), que resuelve foco, teclado y ARIA de los componentes complejos.
- **Capa propia:** componentes de Veridicus en `frontend/src/components/`, estilados solo con *tokens*
  CSS (propiedades personalizadas) definidos en `frontend/src/theme/`. Sin tema visual de terceros ni
  biblioteca de estilos completa.
- **Elementos nativos primero:** botones, enlaces, formularios, tablas y listas usan HTML nativo; Radix
  solo donde HTML no basta (diálogos, plegables, pestañas, grupos de opciones, avisos emergentes).
- Las versiones de las dependencias se fijan en el lockfile y entran por PR, como cualquier dependencia
  (team-practices, Code Style).

## 2. Componentes de Veridicus → primitivas

| Componente (`interaction-spec.md`) | Base | Notas |
|---|---|---|
| StatusBadge | `<span>` nativo | Icono `aria-hidden` + texto. |
| TurnComposer | `<form>` + `<textarea>` + `<button>` nativos | Sin Radix. |
| TurnItem | `<li>` en `<ol>`, `<mark>` para resaltado | Sin Radix. |
| ReviewSuggestionCard | `<article>` + Radix `Collapsible` (CoT) | Formularios en línea nativos. |
| HandoffPanel | Radix `Dialog` no modal (`modal={false}`) | No atrapa el foco; Escape cierra. |
| PasteTranscriptDialog | Radix `Dialog` modal | Atrapa el foco. |
| ConfirmDialog | Radix `AlertDialog` | Foco inicial en «Cancelar». |
| ConsolidateAction | `<button aria-disabled>` nativo | Motivo con `aria-describedby`. |
| Pestañas a 1024–1279 px | Radix `Tabs` | Flechas para cambiar, Tab para entrar al panel. |
| Selección de versión (M3) | Radix `RadioGroup` | Opciones deshabilitadas con motivo. |
| Filtro de sesiones (M1) | Radix `ToggleGroup` + `<select>` nativo | |
| Copiar SHA-256 | `<button>` nativo + región en vivo | Anuncia «SHA-256 copiado». |
| Indicaciones breves | Radix `Tooltip` solo como complemento | Ninguna información necesaria vive solo en un *tooltip* (AC5.1.5 exige el recordatorio visible sin *hover*). |
| Tablas (M1, M2, M6) | `<table>` nativa | Encabezados `<th scope="col">`. |
| Reporte (M5) | Renderizador de Markdown sin HTML crudo | Cumple `react/no-danger`. |

## 3. *Tokens* de diseño

Todos los valores viven en `frontend/src/theme/tokens.css`; los componentes nunca usan colores ni
medidas literales (regla de *lint* de estilos en CI).

### 3.1 Colores de estado: parámetro configurable (P4)

Los colores de estado del PRD son el **valor por defecto**, no un valor fijo. Se agrupan en un único
archivo `frontend/src/theme/state-colors.css` (importado por `tokens.css`) para poder cambiarlos sin
tocar componentes si, al verlos, no resultan adecuados. Cambiar un color es un PR que edita solo ese
archivo; la prueba de contraste (abajo) impide fusionar un valor que rompa WCAG 2.1 AA.

| Token | Uso | Valor por defecto (propuesto) | Icono fijo | Texto fijo |
|---|---|---|---|---|
| `--state-suggestion-fg` / `-bg` / `-border` | Sugerencia de revisión | ámbar (PRD, Journey 1) — p. ej. texto `#7A4B00` sobre fondo `#FFF4D6`, borde `#B26B00` | ◆ | «Sugerencia de revisión» |
| `--state-undocumented-fg` / `-bg` / `-border` | Hecho No Documentado | rojo (PRD, Journey 4) — p. ej. texto `#8A1C1C` sobre fondo `#FDECEC`, borde `#B42318` | ● | «Hecho No Documentado» |
| `--state-system-error-fg` / `-bg` / `-border` | Error del sistema (turno en Error, fallos de carga) | borde gris oscuro `#3D3D3D`, fondo `#F2F2F2`, texto `#1F1F1F` | ⚠ | «Error» |
| `--state-success-*` | Evaluado, Aceptada, Listo | verde oscuro, p. ej. `#1E6B3A` | ✓ | según estado |
| `--state-neutral-*` | En cola, Pendiente, Finalizada | gris, p. ej. `#4A4A4A` | ◷ / ■ | según estado |
| `--state-progress-*` | Procesando, Indexando | azul, p. ej. `#1F4E99` | ⟳ | según estado |
| `--state-locked-*` | Consolidada, bloqueada | gris azulado, p. ej. `#3B4A5C` | 🔒 | según estado |

Reglas:

- **El Hecho No Documentado nunca usa los *tokens* de error del sistema** (AC4.2.2), aunque ambos se
  configuren con tonos cercanos: su diferencia es obligatoria también en icono y texto.
- **Prueba de contraste `[N0]`.** Una prueba de Vitest lee `state-colors.css` y falla si algún par
  `fg`/`bg` baja de 4.5:1 o algún `border` baja de 3:1 frente a `--surface-card`. Ejecuta con
  `npm --prefix frontend run test -- theme/contrast`.
- **Prueba de distinción `[N0]`.** Falla si `--state-undocumented-*` y `--state-system-error-*` resuelven
  al mismo valor, o si dos estados distintos comparten icono o texto.
- Los colores son de compilación (CSS), no de ejecución: no hay pantalla de la consola para cambiarlos,
  y ningún cambio de color se aplica sin PR (coherente con team-practices).

### 3.2 Superficies, texto y foco

| Token | Valor propuesto | Uso |
|---|---|---|
| `--surface-page` | `#FAFAF8` | Fondo de página. |
| `--surface-card` | `#FFFFFF` | Tarjetas, paneles, diálogos. |
| `--text-primary` | `#1A1A1A` | Texto principal (≥ 15:1). |
| `--text-secondary` | `#555555` | `code` de errores, metadatos (≥ 7:1). |
| `--focus-ring` | `2px solid #1F4E99`, separación 2px | Foco visible en todo elemento enfocable (≥ 3:1). |
| `--highlight-fragment` | fondo `#FFE58A` + subrayado | Fragmento resaltado en la transcripción. |

### 3.3 Tipografía y espaciado

- Familia: pila del sistema (`system-ui`, sin fuentes descargadas en ejecución); texto base 16 px,
  secundario 14 px, títulos 20/24 px; interlineado 1.5.
- Escala de espaciado: 4, 8, 16, 24, 32, 48 px (`--space-1` … `--space-6`).
- Ancho mínimo de objetivo interactivo: 32 × 32 px en escritorio (WCAG 2.5.8 AA de 2.2 como referencia;
  2.1 AA no fija mínimo para puntero).

## 4. Puntos de quiebre (P3)

| Nombre | Rango | Distribución |
|---|---|---|
| `--bp-wide` | ≥ 1280 px | Dos columnas (58 % / 42 %) en M4; diseño principal. |
| `--bp-narrow` | 1024–1279 px | Pestañas «Transcripción» / «Sugerencias»; misma funcionalidad. |
| fuera de alcance | < 1024 px | Aviso «Veridicus está diseñado para pantallas de escritorio (1024 px o más)»; sin diseño propio. |

El zoom del navegador al 200 % sobre 1280 px equivale a 640 px CSS: el contenido debe seguir legible y
operable (WCAG 1.4.4), aunque la distribución caiga al aviso; ver `accessibility-checklist.md` §2.

## 5. Fechas y horas (P5)

- Una sola utilidad `formatDateTime(utcIso: string, { withUtc?: boolean })` con `Intl.DateTimeFormat`
  (`es-CO`, `timeZone: 'America/Bogota'`, 24 h) produce `DD/MM/AAAA HH:mm`; `withUtc` añade
  ` (HH:mm UTC)` para las marcas de consolidación del reporte.
- El servidor genera las fechas del reporte con la misma regla (zona `America/Bogota`); el formato se
  fija en `contracts/` para que frontend y backend lo compartan.

## 6. Idioma y glosario

- `lang="es"` en el documento; todos los textos visibles en español desde el catálogo de mensajes
  (NFR14). Las claves del catálogo y los nombres de componentes van en inglés según el glosario de
  team-practices (p. ej. «Hecho No Documentado» → `undocumented_fact`, «sugerencia de revisión» →
  `review_suggestion`).
- El catálogo se escanea con la lista versionada de vocabulario prohibido (AC5.5.1 `[N0]`).
