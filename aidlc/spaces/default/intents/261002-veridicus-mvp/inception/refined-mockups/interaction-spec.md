# Especificación de interacción — Veridicus (consola del analista)

**Insumos.** `mockups.md` (pantallas M0–M6), historias de `inception/user-stories/stories.md` (stories),
requisitos de `inception/requirements-analysis/requirements.md` (requirements), prácticas de
`inception/practices-discovery/team-practices.md` (team-practices) y respuestas P1–P5 de
`refined-mockups-questions.md`. Sin `wireframes` ni `user-flow` de Ideation (scope `classic`).

Los nombres de componentes y *props* van en inglés según el glosario de team-practices (Code Style); los
textos visibles van en español y salen del catálogo de mensajes. Cada componente indica el criterio que
lo comprueba y su nivel de prueba (`[N0]` Vitest + React Testing Library, `[N3]` Playwright).

---

## 1. Principios de interacción

1. **La IA sugiere, el analista decide.** Ninguna acción automática cambia el estado de una alerta;
   todo cambio es un clic explícito del dueño de la sesión (AUTONOMIA-03, FR6.1).
2. **Nada interrumpe al analista.** Las alertas y los cambios de estado llegan sin ventana modal, sin
   sonido y sin mover el foco (AC3.1.7). Solo son modales las confirmaciones irreversibles (finalizar,
   consolidar, desactivar usuario) y la pregunta de reanudación.
3. **Prevenir antes que corregir.** Las acciones no permitidas se deshabilitan con su motivo visible, en
   texto, junto al control (AC5.1.1, AC6.1.1, AC5.2.1); la API repite la misma regla (`409`/`422`).
4. **Envío asíncrono.** Ningún envío bloquea la interfaz: los turnos y los audios se aceptan con `202` y
   su avance se refleja por estado (FR3.4, NFR3).
5. **Estado legible de un vistazo.** Todo estado combina icono + texto + color configurable; ninguno
   depende solo del color (AC5.6.3).
6. **Vocabulario controlado.** Los únicos rótulos de resultado son «Sugerencia de revisión»,
   «Incongruencia semántica» y «Hecho No Documentado» (AC5.5.4); el catálogo de mensajes pasa por el
   escaneo de vocabulario prohibido (AC5.5.1).

## 2. Actualización en vivo

- La consola consulta el estado de la sesión por sondeo (`GET`) cada pocos segundos mientras haya turnos
  «En cola» o «Procesando»; el intervalo y el mecanismo exacto (sondeo frente a eventos del servidor)
  los fija Functional Design. El mismo canal sirve de latido para la suspensión (AC7.1.1).
- Una sola región `aria-live="polite"` por pantalla anuncia, sin repetir, los cambios agregados:
  «Turno 4 evaluado · 1 sugerencia nueva · 2 pendientes». Los errores bloqueantes de un formulario usan
  el mensaje junto al campo, no la región en vivo.
- Las animaciones (icono de procesamiento, esqueletos) duran ≤ 300 ms por transición y se desactivan con
  `prefers-reduced-motion`.

## 3. Formato de fechas y horas (P5)

- Toda fecha visible se convierte de UTC a `America/Bogota` y se formatea `DD/MM/AAAA HH:mm` (24 h) con
  una única función de formato del frontend, probada con instantes en UTC que cruzan la medianoche
  `[N0]`.
- El reporte usa el mismo formato y, en las marcas de consolidación (quién y cuándo de cada versión),
  añade la hora UTC: `02/10/2026 15:31 (20:31 UTC)`.
- Los cronómetros de procesamiento usan `mm:ss` relativos, no hora de reloj.

---

## 4. Especificación de componentes

Formato: `.claude/knowledge/aidlc-design-agent/component-spec-template.md`. Los puntos de quiebre se
limitan a los de P3: **escritorio ancho** (≥ 1280 px), **escritorio estrecho** (1024–1279 px) y
**< 1024 px** (fuera de alcance: aviso, sin diseño propio).

### 4.1 StatusBadge

| Campo | Valor |
|---|---|
| Component | StatusBadge |
| Description | Muestra el estado de un turno, una alerta, una sesión o una versión con icono + texto + color. |
| Category | display |

**States**

| State | Description | Trigger |
|---|---|---|
| default | Icono decorativo (`aria-hidden`) + texto del estado | render |
| emphasis | Variante destacada para Hecho No Documentado y Error | `kind` = `undocumented` o `system-error` |

**Props / Inputs**

| Prop | Type | Required | Default | Description |
|---|---|---|---|---|
| kind | `'queued' \| 'processing' \| 'evaluated' \| 'evaluated-empty' \| 'undocumented' \| 'system-error' \| 'pending' \| 'accepted' \| 'edited' \| 'dismissed' \| 'locked' \| 'open' \| 'suspended' \| 'finalized' \| 'consolidated'` | yes | — | Estado a mostrar; el texto sale del catálogo. |
| detail | string | no | — | Texto complementario («con nota», etapa de procesamiento). |

**Responsive Behaviour**

| Breakpoint | Behaviour |
|---|---|
| escritorio ancho | Icono + texto completo. |
| escritorio estrecho | Igual; el texto nunca se trunca. |

**Accessibility**

| Requirement | Implementation |
|---|---|
| ARIA role | Texto en línea; sin rol propio. |
| Keyboard interaction | No enfocable. |
| Label / aria-label | El texto visible es la etiqueta; el icono es `aria-hidden="true"`. |
| Contrast ratio | Texto ≥ 4.5:1; icono y borde ≥ 3:1 sobre el fondo de la tarjeta, con cualquier valor configurado de los *tokens* (`design-system-mapping.md` §3). |
| Screen reader | Lee el texto del estado. |
| Focus management | No aplica. |

Verificación: AC5.6.3 `[N0]` (cada `kind` renderiza texto no vacío y un icono), prueba de contraste de
*tokens* `[N0]`.

### 4.2 TurnComposer

| Campo | Valor |
|---|---|
| Component | TurnComposer |
| Description | Entrada fija abajo a la izquierda para escribir y enviar el siguiente turno; incluye la grabación por voz (SHOULD). |
| Category | input |

**States**

| State | Description | Trigger |
|---|---|---|
| default | Campo vacío; «Enviar turno» deshabilitado | sesión abierta sin texto |
| ready | Hay texto no vacío; «Enviar turno» habilitado | escritura |
| sending | Envío en curso; el campo ya está limpio y editable | `POST` pendiente |
| recording | Grabando audio; indicador «● Grabando mm:ss» | «Grabar» |
| mic-denied | Mensaje «No hay acceso al micrófono. Puedes seguir escribiendo el turno» | permiso negado |
| disabled | Sustituido por «Sesión finalizada · quedan N sugerencias pendientes» | sesión finalizada, consolidada o ajena |
| error | «No se pudo enviar el turno. Tu texto sigue aquí.» + «Reintentar» | fallo del `POST` |

**Props / Inputs**

| Prop | Type | Required | Default | Description |
|---|---|---|---|---|
| sessionId | string | yes | — | Sesión destino. |
| nextTurnNumber | number | yes | — | Número que se muestra («Turno 6»). |
| voiceEnabled | boolean | no | false | Muestra «Grabar» (FR10.2, SHOULD). |
| onSubmitted | `(turnId: string) => void` | yes | — | Notifica el turno creado (`202`). |

**Responsive Behaviour**

| Breakpoint | Behaviour |
|---|---|
| escritorio ancho | Fijo al pie de la columna izquierda. |
| escritorio estrecho | Fijo al pie de la pestaña «Transcripción». |

**Accessibility**

| Requirement | Implementation |
|---|---|
| ARIA role | `<form>` con `<label>` visible «Turno N»; área de texto nativa. |
| Keyboard interaction | `Ctrl+Enter` envía; Tab llega a «Grabar» y «Enviar turno»; Enter en el área de texto inserta salto de línea. |
| Label / aria-label | Etiqueta visible; el motivo de deshabilitado se asocia con `aria-describedby`. |
| Contrast ratio | WCAG AA. |
| Screen reader | Anuncia «Turno N enviado · En cola» en la región en vivo; la grabación anuncia inicio y fin. |
| Focus management | Tras enviar, el foco permanece en el área de texto vacía. |

Verificación: AC2.2.5, AC10.2.3 `[N0]`; AC2.2.2 con juez bloqueado `[N1]`.

### 4.3 TurnItem

| Campo | Valor |
|---|---|
| Component | TurnItem |
| Description | Un turno de la transcripción con su número, estado, texto literal y, según el caso, aviso de Hecho No Documentado, error con reintento o fragmentos resaltados. |
| Category | display |

**States**

| State | Description | Trigger |
|---|---|---|
| queued / processing | Estado y etapa con cronómetro | cola |
| evaluated-empty | «Evaluado · sin sugerencias de revisión» | sin alertas ni Hecho No Documentado |
| evaluated | Enlace «N sugerencias» | con alertas |
| undocumented | Aviso destacado + «Ver ▸» que abre el paquete | afirmación «no documentada» |
| error | Causa sin jerga, `code` secundario, «Reintentar evaluación» | salida inválida o *timeout* |
| highlighted | Fragmento marcado con `<mark>` | alerta seleccionada |

**Props / Inputs**

| Prop | Type | Required | Default | Description |
|---|---|---|---|---|
| turn | `Turn` | yes | — | Número, texto, estado, etapa, `code`. |
| highlights | `TextRange[]` | no | `[]` | Subcadenas literales a resaltar. |
| canRetry | boolean | yes | — | Dueño de la sesión y turno en Error (también en sesión finalizada). |
| onOpenHandoff | `() => void` | no | — | Abre el paquete del turno. |

**Responsive Behaviour**

| Breakpoint | Behaviour |
|---|---|
| escritorio ancho | Ancho de la columna izquierda; texto ajustado sin truncar. |
| escritorio estrecho | Ancho completo de la pestaña. |

**Accessibility**

| Requirement | Implementation |
|---|---|
| ARIA role | `<li>` dentro de `<ol>`; encabezado de nivel 3 «Turno N». |
| Keyboard interaction | «Ver ▸» y «Reintentar evaluación» son `<button>`. |
| Label / aria-label | «Ver paquete de contexto del turno N». |
| Contrast ratio | WCAG AA; el resaltado usa fondo + subrayado, no solo color. |
| Screen reader | El resaltado se anuncia como «resaltado» (`<mark>`). |
| Focus management | Reintentar deja el foco en el turno; el estado nuevo se anuncia. |

Verificación: AC3.1.3, AC3.1.8, AC3.2.2, AC4.2.2, AC10.1.1 `[N0]`; AC3.2.3 `[N1]`.

### 4.4 ReviewSuggestionCard

| Campo | Valor |
|---|---|
| Component | ReviewSuggestionCard |
| Description | Tarjeta de una sugerencia de revisión con fragmento, cita, ID de documento, CoT plegable, recordatorio de criterio y acciones Aceptar / Editar / Descartar. |
| Category | display + input |

**States**

| State | Description | Trigger |
|---|---|---|
| pending-collapsed | CoT plegada; Aceptar y Editar deshabilitados con su motivo | alerta nueva |
| pending-expanded | CoT desplegada; las tres acciones habilitadas | «Ver justificación (CoT)» |
| accepting | Campo «Nota (opcional)» + «Confirmar aceptación» / «Cancelar» | «Aceptar» |
| editing | Editor a dos columnas (original en solo lectura / tu reformulación) | «Editar» |
| dismissing | Campo de nota obligatoria | «Descartar» |
| decided | Estado final con nota, quién y cuándo; «Cambiar decisión» | decisión guardada |
| locked | Estado final sin acciones | sesión consolidada |
| read-only | Sin acciones | sesión de otro analista o rol `admin` |
| saving | Acciones deshabilitadas, «Guardando…» | petición en curso |
| error | «No se pudo guardar tu decisión. Intenta de nuevo.»; el formulario conserva el texto | fallo de la API |

**Props / Inputs**

| Prop | Type | Required | Default | Description |
|---|---|---|---|---|
| suggestion | `ReviewSuggestion` | yes | — | Fragmento, cita, `documentId`, CoT, estado, historial. |
| canDecide | boolean | yes | — | Dueño de la sesión y sesión no consolidada. |
| cotViewed | boolean | yes | — | Ya existe el evento «CoT consultada» del usuario. |
| onSelect | `() => void` | yes | — | Resalta el fragmento en la transcripción. |

**Responsive Behaviour**

| Breakpoint | Behaviour |
|---|---|
| escritorio ancho | Ancho de la columna derecha; el editor abre a dos columnas dentro de la tarjeta. |
| escritorio estrecho | Ancho completo de la pestaña; el editor apila original arriba y reformulación abajo. |

**Accessibility**

| Requirement | Implementation |
|---|---|
| ARIA role | `<article>` con encabezado nivel 3; la CoT es un `Collapsible` (botón con `aria-expanded` + región). |
| Keyboard interaction | Tab recorre: CoT, Aceptar, Editar, Descartar; Enter/Espacio activan; Escape cancela el formulario en línea y devuelve el foco al botón que lo abrió. |
| Label / aria-label | Los botones nombran el turno: «Aceptar sugerencia del turno 2». |
| Contrast ratio | WCAG AA; los botones deshabilitados mantienen texto legible ≥ 4.5:1 para su motivo. |
| Screen reader | El motivo de deshabilitado se asocia con `aria-describedby`; al desplegar la CoT se anuncia «Justificación desplegada». |
| Focus management | Abrir un formulario en línea mueve el foco a su primer campo; guardar devuelve el foco al rótulo de estado de la tarjeta. |

Reglas de interacción:

- Desplegar la CoT registra «CoT consultada» una vez por usuario y alerta (AC5.1.2); plegarla de nuevo no
  vuelve a deshabilitar las acciones.
- «Editar» nunca permite cambiar fragmento, cita, ID de documento ni CoT: el original es texto, no campos
  (AC5.2.2).
- Antes de consolidar, «Cambiar decisión» permite pasar entre aceptada, editada y descartada con las
  mismas exigencias; nunca ofrece volver a «Pendiente» (AC5.1.4).
- Junto a las acciones, siempre visible y sin *hover*: «La IA es un asistente de soporte. Su criterio
  como analista prevalece» (AC5.1.5).

Verificación: AC5.1.1, AC5.1.3, AC5.1.5, AC5.2.1, AC5.2.3, AC5.3.1, AC5.4.2 `[N0]`; AC5.6.2 `[N3]`.

### 4.5 HandoffPanel (Paquete de Contexto de Traspaso)

| Campo | Valor |
|---|---|
| Component | HandoffPanel |
| Description | Panel lateral con el aviso de control manual, el fragmento actual, hasta 3 turnos previos, los 3 pasajes más cercanos y la justificación interrumpida. |
| Category | feedback |

**States**

| State | Description | Trigger |
|---|---|---|
| closed | Solo el aviso en el turno | por defecto |
| open | Panel sobre la columna derecha | «Ver ▸» |
| partial | «Turnos previos disponibles: N de 3»; menos de 3 pasajes si el escenario tiene menos | turnos 1–3 o escenario corto |
| affective | Línea de fluctuación afectiva (COULD) | clasificador activo |

**Props / Inputs**

| Prop | Type | Required | Default | Description |
|---|---|---|---|---|
| handoff | `HandoffPackage` | yes | — | Fragmento, turnos previos, pasajes con coeficiente, similitud máxima y umbral. |
| onClose | `() => void` | yes | — | Cierra y devuelve el foco. |

**Responsive Behaviour**

| Breakpoint | Behaviour |
|---|---|
| escritorio ancho | Cubre la columna derecha; la transcripción sigue visible. |
| escritorio estrecho | Cubre la pestaña «Sugerencias»; el aviso en la pestaña «Transcripción» lo abre y cambia de pestaña. |

**Accessibility**

| Requirement | Implementation |
|---|---|
| ARIA role | `Dialog` no modal de Radix (`role="dialog"`, `aria-modal="false"`) con título «Paquete de Contexto de Traspaso · Turno N». |
| Keyboard interaction | Escape y «Cerrar» lo cierran; Tab puede salir hacia la transcripción (no atrapa el foco). |
| Label / aria-label | `aria-labelledby` al título. |
| Contrast ratio | WCAG AA; el aviso usa su color de estado + icono + texto. |
| Screen reader | Al abrir, lee el título y el aviso. |
| Focus management | Al abrir, foco en el título; al cerrar, vuelve a «Ver ▸» del turno. |

Verificación: AC4.2.2, AC4.2.3 `[N0]`; AC4.2.4 `[N3]`.

### 4.6 PasteTranscriptDialog

| Campo | Valor |
|---|---|
| Component | PasteTranscriptDialog |
| Description | Diálogo en dos pasos para pegar una transcripción completa y confirmar los turnos detectados. |
| Category | input |

**States**

| State | Description | Trigger |
|---|---|---|
| editing | Área de texto; «Continuar» deshabilitado si está vacía | apertura |
| preview | «Se detectaron N turnos» + lista | «Continuar» |
| empty-result | «No se detectaron turnos. Separa los turnos con una línea vacía o con una marca de hablante» | 0 turnos |
| creating | «Creando N turnos…» | «Crear N turnos» |
| error | Error del sistema; el texto se conserva | fallo de la API |

**Props / Inputs**

| Prop | Type | Required | Default | Description |
|---|---|---|---|---|
| sessionId | string | yes | — | Sesión destino. |
| splitPreview | `(text: string) => TurnPreview[]` | yes | — | División local con la misma regla que el servidor (la fija Functional Design). |

**Responsive Behaviour**

| Breakpoint | Behaviour |
|---|---|
| escritorio ancho | Diálogo de 720 px de ancho máximo. |
| escritorio estrecho | 90 % del ancho de la ventana. |

**Accessibility**

| Requirement | Implementation |
|---|---|
| ARIA role | `Dialog` modal de Radix. |
| Keyboard interaction | Escape = «Cancelar» (no crea turnos); el foco queda atrapado en el diálogo. |
| Label / aria-label | Título «Pegar transcripción». |
| Contrast ratio | WCAG AA. |
| Screen reader | El conteo de turnos detectados se anuncia al pasar a la vista previa. |
| Focus management | Al abrir, foco en el área de texto; al cerrar, vuelve a «Pegar transcripción». |

Verificación: AC2.3.1 `[N0]`; AC2.3.2 `[N1]`.

### 4.7 ConfirmDialog

| Campo | Valor |
|---|---|
| Component | ConfirmDialog |
| Description | Confirmación de una acción irreversible: finalizar sesión, consolidar, desactivar usuario, descartar copia de trabajo. |
| Category | feedback |

**States**

| State | Description | Trigger |
|---|---|---|
| open | Resumen de efectos + «Cancelar» y acción | botón de la acción |
| confirming | Acción deshabilitada, «Consolidando…» | confirmar |
| conflict | «La sesión cambió mientras confirmabas. Revisa el resumen» y resumen actualizado | `409` |
| error | Error del sistema; el diálogo sigue abierto | fallo de la API |

**Props / Inputs**

| Prop | Type | Required | Default | Description |
|---|---|---|---|---|
| title | string | yes | — | Título. |
| summary | ReactNode | yes | — | Conteos y consecuencias (p. ej. AC6.1.2). |
| confirmLabel | string | yes | — | «Finalizar», «Consolidar», «Desactivar». |
| onConfirm | `() => Promise<void>` | yes | — | Acción. |

**Responsive Behaviour**

| Breakpoint | Behaviour |
|---|---|
| escritorio ancho | 520 px de ancho máximo. |
| escritorio estrecho | Igual. |

**Accessibility**

| Requirement | Implementation |
|---|---|
| ARIA role | `AlertDialog` de Radix. |
| Keyboard interaction | Escape = «Cancelar»; el foco inicial va a «Cancelar» (acción segura). |
| Label / aria-label | `aria-labelledby` al título, `aria-describedby` al resumen. |
| Contrast ratio | WCAG AA. |
| Screen reader | Lee título y resumen al abrir. |
| Focus management | Al cerrar, vuelve al botón que lo abrió o, tras consolidar, al encabezado de M5. |

Verificación: AC2.4.1, AC6.1.2 `[N0]`; AC6.1.6 `[N1]`.

### 4.8 ConsolidateAction

| Campo | Valor |
|---|---|
| Component | ConsolidateAction |
| Description | Botón «Finalizar y Consolidar» con su motivo de bloqueo visible. |
| Category | input |

**States**

| State | Description | Trigger |
|---|---|---|
| blocked-open | «Finaliza la sesión para consolidar» | sesión no finalizada |
| blocked-pending | «Quedan N sugerencias pendientes» + enlace a la primera | alertas pendientes |
| blocked-processing | «Hay turnos en proceso» | turnos en cola o procesando |
| ready | Habilitado | todo revisado |
| hidden | No se muestra | sesión ajena, rol `admin` o ya consolidada |

Accesibilidad: `<button>` con `aria-disabled="true"` (sigue enfocable para leer el motivo) y
`aria-describedby` al motivo. Verificación: AC6.1.1 `[N0]` + `[N1]`.

### 4.9 SuggestedQuestion (SHOULD)

Pregunta sugerida al pie de la columna derecha, rotulada «Pregunta sugerida · requiere tu aprobación»
con «Aprobar» y «Descartar»; «Escuchar audio» solo aparece tras aprobar (AC10.3.1, AC10.4.1). Nunca se
muestra en un turno con alguna afirmación «no documentada» (AC10.3.2). El audio solo se reproduce al
pulsar, nunca en automático.

### 4.10 ReportView

Vista de M5: cabecera con quién y cuándo (hora de Colombia + UTC), SHA-256 completo con «Copiar
SHA-256» (anuncia «SHA-256 copiado»), «Descargar reporte», lista de versiones con la vigente marcada en
texto y «Corregir reporte». El Markdown del reporte se renderiza sin HTML crudo (`react/no-danger` es
error en team-practices). Verificación: AC6.1.4, AC6.3.4 `[N0]`; AC6.2.1 `[N3]`.

---

## 5. Flujos de usuario

### F1 — Flujo de texto de punta a punta (ruta crítica de stories)

Persona: Analista de Verdad. Disparador: «Nueva sesión».

1. M3 → elige la versión «Listo» preseleccionada → «Crear sesión» → M4 vacía.
2. M4 → escribe el turno → `Ctrl+Enter` → el turno aparece «En cola» → «Procesando» → «Evaluado».
3. M4 → aparece una tarjeta en la columna derecha (sin modal) → el contador se anuncia.
4. Tarjeta → «Ver justificación (CoT)» → «Aceptar» / «Editar» / «Descartar».
5. Cabecera → «Finalizar sesión» → confirmar.
6. Cabecera → «Finalizar y Consolidar» → resumen → «Consolidar» → M5.
7. M5 → «Descargar reporte» → compara el SHA-256 visible.

Errores: turno en Error → «Reintentar evaluación»; consolidación bloqueada → motivo visible y enlace a la
primera pendiente; conflicto al consolidar → resumen actualizado.

### F2 — Hecho No Documentado

Turno evaluado con afirmación «no documentada» → aviso en el turno (no cuenta como pendiente, sin pregunta
sugerida) → «Ver ▸» → panel con el paquete → Escape → foco de vuelta al aviso.

### F3 — Reanudación

Entrada con sesión «Suspendida» → diálogo «Se detectó una interrupción inesperada…» → «Reanudar» (M4 en
el último turno) o «Más tarde» (sigue en M1 como «Suspendida»).

### F4 — Corrección de un reporte

M5 → «Corregir reporte» → M4 en copia de trabajo (solo estados y notas) → cambia decisiones →
«Finalizar y Consolidar» → versión nueva en M5, con la anterior en la lista.

---

## 6. Mensajes del sistema (catálogo)

| Clave (inglés) | Texto visible | Tratamiento |
|---|---|---|
| `turn.error.invalid_output` | «No se pudo evaluar este turno: la respuesta de la IA no tenía el formato esperado. Puedes reintentar» | Error del sistema |
| `turn.error.timeout` | «No se pudo evaluar este turno: la evaluación tardó demasiado. Puedes reintentar» | Error del sistema |
| `undocumented.notice` | «La IA no puede validar este fragmento de forma autónoma. Control manual requerido» | Hecho No Documentado (comparado carácter por carácter) |
| `suggestion.label` | «Sugerencia de revisión · Incongruencia semántica» | Sugerencia de revisión |
| `suggestion.reminder` | «La IA es un asistente de soporte. Su criterio como analista prevalece» | Informativo |
| `suggestion.cot_required` | «Despliega y lee la justificación (CoT) para habilitar esta acción» | Motivo de deshabilitado |
| `suggestion.dismiss_note_required` | «Escribe por qué descartas esta sugerencia» | Error de campo |
| `session.read_only` | «Sesión de <usuario>. Solo lectura» | Informativo |
| `session.resume_prompt` | «Se detectó una interrupción inesperada en la sesión. ¿Desea reanudar desde el último turno registrado?» | Diálogo |
| `report.working_copy` | «Copia de trabajo de la versión N. Solo puedes cambiar estados y notas» | Informativo |
| `layout.narrow_screen` | «Veridicus está diseñado para pantallas de escritorio (1024 px o más)» | Informativo |

Los `code` de Problem Details se muestran como «Código: <code>», en tamaño secundario, nunca como único
mensaje.
