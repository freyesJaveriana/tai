# Especificación de interacción — Veridicus (consola del analizador de incoherencias)

**Revisión 2 — cambio 01 (DT27, 2026-11-03).** Reemplaza la aprobada el 02/10/2026. Los componentes
que siguen conservan su número; los que salen quedan marcados **Retirado** y los nuevos toman 4.11 en
adelante.

**Insumos.** `mockups.md` (pantallas M0–M8), historias de `inception/user-stories/stories.md`
(stories), requisitos de `inception/requirements-analysis/requirements.md` (requirements), prácticas de
`inception/practices-discovery/team-practices.md` (team-practices) y respuestas P1–P11 y seguimientos 7
y 8 de `refined-mockups-questions.md`. Sin `wireframes` ni `user-flow` de Ideation (scope `classic`).

Los nombres de componentes y *props* van en inglés según el glosario de team-practices (Code Style); los
textos visibles van en español y salen del catálogo de mensajes. Cada componente indica el criterio que
lo comprueba y su nivel de prueba (`[N0]` Vitest + React Testing Library, `[N1]` integración, `[N3]`
Playwright).

---

## 1. Principios de interacción

1. **La IA sugiere, el analista decide.** Ninguna acción automática cambia el estado de un hallazgo;
   todo cambio es un clic explícito del dueño de la sesión (AUTONOMIA-03, FR6.1).
2. **Nada interrumpe al analista.** Los hallazgos y los cambios de estado llegan sin ventana modal, sin
   sonido y sin mover el foco (AC3.1.3). Solo son modales las confirmaciones irreversibles (finalizar,
   consolidar, desactivar usuario, descartar copia), la pregunta de reanudación y los diálogos de entrada
   (pegar transcripción, subir reporte).
3. **Prevenir antes que corregir.** Las acciones no permitidas se deshabilitan con su motivo visible, en
   texto, junto al control, y siguen enfocables (`aria-disabled`, AC5.6.4); la API repite la misma regla
   (`409`/`413`/`422`).
4. **Envío asíncrono.** Ningún envío bloquea la interfaz: turnos, bloques, audios y modo final se aceptan
   con `202` y su avance se refleja por estado (FR3.4, AC2.7.3).
5. **Estado legible de un vistazo.** Todo estado combina icono + texto + color configurable; ninguno
   depende solo del color (AC5.6.3). Las citas A y B se distinguen por letra y por estilo de marca, no
   solo por color (AC3.1.2).
6. **Vocabulario controlado.** Los únicos rótulos de resultado son «Sugerencia de revisión»,
   «Contradicción en el relato» y los 7 rótulos de tipo (AC5.5.4); el catálogo de mensajes pasa por el
   escaneo de vocabulario prohibido (AC5.5.1).
7. **Lo que el sistema no hizo, se dice.** Tramos no evaluados, modo final con error, análisis por
   ventanas y confirmación de la misma familia se muestran siempre que aplican, en la sesión y en el
   reporte (FR4.8, FR7.2).

## 2. Actualización en vivo

- La consola consulta el estado de la sesión por sondeo (`GET`) mientras haya corridas «En cola» o
  «Procesando»; el intervalo y el mecanismo exacto los fija Functional Design. El mismo canal sirve de
  latido para la suspensión (AC7.1.1).
- Una sola región `aria-live="polite"` por pantalla anuncia, sin repetir, **cambios de corrida y
  agregados**: inicio, etapa, fin o error de cada corrida incremental o del modo final (AC10.1.1), con el
  progreso «ventana N de M» como mucho una vez cada 30 s; el contador de pendientes («1 hallazgo nuevo ·
  2 pendientes»); la sesión suspendida; y, como respuesta a una acción del usuario, el resultado de validar
  un archivo y «SHA-256 copiado». El estado de cada turno se lee al enfocarlo y nunca se anuncia uno por
  uno (AC5.6.5). La lectura de AC10.1.1 por corrida queda en la tabla de precisiones de `mockups.md`.
- Las animaciones duran ≤ 300 ms por transición y se desactivan con `prefers-reduced-motion`.

## 3. Formato de fechas y horas (P5)

- Toda fecha visible se convierte de UTC a `America/Bogota` y se formatea `DD/MM/AAAA HH:mm` (24 h) con
  una única función de formato, probada con instantes en UTC que cruzan la medianoche `[N0]`.
- El reporte usa el mismo formato y, en las marcas de consolidación, añade la hora UTC:
  `03/11/2026 15:31 (20:31 UTC)`.
- Los cronómetros de procesamiento usan `mm:ss` relativos.

---

## 4. Especificación de componentes

Formato: `.claude/knowledge/aidlc-design-agent/component-spec-template.md`. Puntos de quiebre de P3:
**escritorio ancho** (≥ 1280 px), **escritorio estrecho** (1024–1279 px) y **< 1024 px** (aviso, sin
diseño propio).

### 4.1 StatusBadge

| Campo | Valor |
|---|---|
| Component | StatusBadge |
| Description | Muestra el estado de un turno, un tramo, una corrida, un hallazgo, una sesión, una versión o un reporte subido con icono + texto + color. |
| Category | display |

**States**

| State | Description | Trigger |
|---|---|---|
| default | Icono decorativo (`aria-hidden`) + texto del estado | render |
| emphasis | Variante destacada para errores del sistema | `kind` = `segment-error` o `final-error` |

**Props / Inputs**

| Prop | Type | Required | Default | Description |
|---|---|---|---|---|
| kind | `'queued' \| 'processing' \| 'analyzed' \| 'analyzed-empty' \| 'segment-error' \| 'final-not-launched' \| 'final-queued' \| 'final-processing' \| 'final-done' \| 'final-error' \| 'pending' \| 'accepted' \| 'edited' \| 'dismissed' \| 'locked' \| 'open' \| 'suspended' \| 'finalized' \| 'consolidated' \| 'imported' \| 'guided'` | yes | — | Estado a mostrar; el texto sale del catálogo. |
| detail | string | no | — | Texto complementario («con nota», etapa, código). |

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
| Contrast ratio | Texto ≥ 4.5:1; icono y borde ≥ 3:1 sobre `--surface-card`, con cualquier valor configurado de los *tokens*. |
| Screen reader | Lee el texto del estado. |
| Focus management | No aplica. |

Verificación: AC5.6.3 `[N0]` (cada `kind` renderiza texto no vacío y un icono); prueba de contraste de
*tokens* `[N0]`.

### 4.2 TurnComposer (solo sesiones guiadas)

| Campo | Valor |
|---|---|
| Component | TurnComposer |
| Description | Entrada fija abajo a la izquierda para escribir y enviar el siguiente turno con su hablante; incluye la grabación por voz (SHOULD). |
| Category | input |

**States**

| State | Description | Trigger |
|---|---|---|
| empty-session | La transcripción muestra «Aún no hay turnos. Escribe el primer turno o pega un bloque de turnos» | sesión guiada recién creada (AC2.2.5) |
| default | Campo vacío; «Enviar turno» deshabilitado (enfocable) con «Escribe el turno para enviarlo» | sesión guiada abierta sin texto |
| ready | Texto no vacío dentro del límite; «Enviar turno» habilitado | escritura |
| over-limit | Contador «X / M caracteres» en estado de error; «Enviar turno» deshabilitado con ese motivo | texto > límite del catálogo |
| sending | Envío en curso; el campo ya está limpio y editable | `POST` pendiente |
| recording | «● Grabando mm:ss» y «Detener y enviar» | «Grabar» |
| mic-denied | «No hay acceso al micrófono. Puedes seguir escribiendo el turno» | permiso negado |
| replaced | «Sesión finalizada · quedan N sugerencias pendientes» + «Ir a la primera» | sesión finalizada |
| hidden | No se muestra | sesión importada, consolidada o ajena |
| error | «No se pudo enviar el turno. Tu texto sigue aquí.» + «Reintentar» | fallo del `POST` |

**Props / Inputs**

| Prop | Type | Required | Default | Description |
|---|---|---|---|---|
| sessionId | string | yes | — | Sesión destino. |
| nextTurnNumber | number | yes | — | Número que se muestra («Turno 9»). |
| maxChars | number | yes | — | Caracteres por turno del catálogo de límites. |
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
| ARIA role | `<form>` con `<label>` visible «Turno N»; grupo de opciones «Hablante» (`TEST` por defecto, `ENT`); área de texto nativa. |
| Keyboard interaction | `Ctrl+Enter` envía; Tab llega a «Hablante», «Grabar» y «Enviar turno»; Enter en el área de texto inserta salto de línea. |
| Label / aria-label | Etiquetas visibles; el contador y el motivo de deshabilitado se asocian con `aria-describedby`. |
| Contrast ratio | WCAG AA. |
| Screen reader | El envío se anuncia como inicio de corrida («Turno N en cola»); la grabación anuncia inicio y fin. |
| Focus management | Tras enviar, el foco permanece en el área de texto vacía. |

Verificación: AC2.2.5, AC2.2.6, AC10.2.3 `[N0]`; AC2.2.2 con *fake* bloqueado `[N1]`.

### 4.3 TurnItem

| Campo | Valor |
|---|---|
| Component | TurnItem |
| Description | Un turno de la transcripción con número, hablante, página, estado (si es `TEST` de una sesión guiada), texto literal y, cuando un hallazgo lo pide, la cita resaltada con su marca A o B. |
| Category | display |

**States**

| State | Description | Trigger |
|---|---|---|
| context | Turno `ENT`: sin estado | hablante `ENT` |
| queued / processing | Estado y etapa con cronómetro | corrida en curso |
| analyzed-empty | «Analizado · sin sugerencias de revisión» | corrida terminada sin hallazgos en el turno |
| analyzed | Enlace «N hallazgos» que filtra el panel | hallazgos con una cita en el turno |
| folded | «⋯ plegado» con su explicación al enfocarlo | `estado: plegado` del contrato |
| quote-a / quote-b | Cita marcada con `<mark>`, letra «A» o «B», barra continua (A) o discontinua (B) | hallazgo seleccionado: las dos marcas a la vez (AC3.1.2) |
| quote-target | Además, anillo de foco en el turno y «Volver al hallazgo» | «Ir a la cita A/B» |

**Props / Inputs**

| Prop | Type | Required | Default | Description |
|---|---|---|---|---|
| turn | `Turn` | yes | — | `n`, hablante, página, página final, estado del contrato, texto, estado de análisis. |
| quoteMark | `{ letter: 'A' \| 'B'; ranges: TextRange[]; findingId: string } \| null` | no | null | Cita a resaltar; varios rangos si la cita une fragmentos con « […] ». |
| onBackToFinding | `(findingId: string) => void` | no | — | Devuelve el foco a la tarjeta. |

**Responsive Behaviour**

| Breakpoint | Behaviour |
|---|---|
| escritorio ancho | Ancho de la columna izquierda; texto ajustado sin truncar. |
| escritorio estrecho | Ancho completo de la pestaña. |

**Accessibility**

| Requirement | Implementation |
|---|---|
| ARIA role | `<li>` dentro de `<ol>`; encabezado de nivel 3 «Turno N · hablante · página». |
| Keyboard interaction | «Volver al hallazgo» es un `<button>`; el turno resaltado recibe el foco programático (`tabindex="-1"`). |
| Label / aria-label | El hablante se lee completo: «entrevistador» o «testimoniante». |
| Contrast ratio | WCAG AA; la marca usa fondo + barra + letra, no solo color. |
| Screen reader | Al saltar, anuncia «Cita A, turno N» (AC3.1.2). |
| Focus management | «Ir a la cita» mueve el foco al turno; «Volver al hallazgo» lo devuelve a la tarjeta. |

Verificación: AC3.1.2, AC3.1.4, AC3.1.5, AC10.1.1 `[N0]`.

### 4.4 ReviewSuggestionCard

| Campo | Valor |
|---|---|
| Component | ReviewSuggestionCard |
| Description | Tarjeta de un hallazgo: rótulos, tipo, origen, hecho, las dos citas con contexto (QuoteBlock), observaciones plegables, recordatorio de criterio y acciones Aceptar / Editar / Descartar. |
| Category | display + input |

**States**

| State | Description | Trigger |
|---|---|---|
| pending-collapsed | Observaciones plegadas; Aceptar y Editar deshabilitados con su motivo | hallazgo nuevo |
| pending-expanded | Observaciones desplegadas; las tres acciones habilitadas | «Ver observaciones» |
| accepting | «Nota (opcional)» + «Confirmar aceptación» / «Cancelar» | «Aceptar» |
| editing | Editor a dos columnas (hallazgo de la IA en solo lectura / tu reformulación) | «Editar» |
| dismissing | Nota obligatoria | «Descartar» |
| decided | Estado final con nota, quién y cuándo; «Cambiar decisión» | decisión guardada |
| locked | Estado final sin acciones | sesión consolidada |
| read-only | Sin acciones | sesión de otro analista |
| saving | Acciones deshabilitadas, «Guardando…» | petición en curso |
| error | «No se pudo guardar tu decisión. Intenta de nuevo.»; el formulario conserva el texto | fallo de la API |

**Props / Inputs**

| Prop | Type | Required | Default | Description |
|---|---|---|---|---|
| finding | `Finding` | yes | — | Hecho, tipo, `cita_a`, `cita_b` (texto, turno, hablante, página, avisos), observaciones, origen, estado, historial. |
| contextTurns | `{ a: { before?: Turn; after?: Turn }; b: { before?: Turn; after?: Turn } }` | yes | — | Turnos de contexto de cada cita. |
| canDecide | boolean | yes | — | Dueño de la sesión y sesión no consolidada. |
| observationsViewed | boolean | yes | — | Ya existe el evento «Observaciones consultadas» del usuario. |
| onGoToQuote | `(letter: 'A' \| 'B') => void` | yes | — | Desplaza y resalta en la transcripción. |

**Responsive Behaviour**

| Breakpoint | Behaviour |
|---|---|
| escritorio ancho | Ancho de la columna derecha; el editor abre a dos columnas dentro de la tarjeta. |
| escritorio estrecho | Ancho completo de la pestaña; el editor apila el original arriba y la reformulación abajo; «Ir a la cita» cambia de pestaña. |

**Accessibility**

| Requirement | Implementation |
|---|---|
| ARIA role | `<article>` con encabezado nivel 3; las observaciones son un `Collapsible` (botón con `aria-expanded` + región). |
| Keyboard interaction | Tab recorre: Ir a la cita A, Ir a la cita B, Ver observaciones, Aceptar, Editar, Descartar; Escape cancela el formulario en línea y devuelve el foco al botón que lo abrió. |
| Label / aria-label | Los botones nombran la cita: «Aceptar sugerencia · citas en los turnos 2 y 214». |
| Contrast ratio | WCAG AA; los botones deshabilitados mantienen su motivo legible ≥ 4.5:1. |
| Screen reader | El motivo de deshabilitado se asocia con `aria-describedby`; al desplegar se anuncia «Observaciones desplegadas». |
| Focus management | Abrir un formulario en línea mueve el foco a su primer campo; guardar devuelve el foco al rótulo de estado, aunque la tarjeta cambie de grupo. |

Reglas de interacción:

- Desplegar las observaciones registra «Observaciones consultadas» una vez por usuario y hallazgo
  (AC5.1.2); plegarlas de nuevo no vuelve a deshabilitar las acciones.
- «Editar» nunca permite cambiar hecho, tipo, citas ni observaciones: el original es texto, no campos
  (AC5.2.2).
- Antes de consolidar, «Cambiar decisión» permite pasar entre aceptada, editada y descartada con las
  mismas exigencias; nunca ofrece volver a «Pendiente» (AC5.1.4).
- Junto a las acciones, siempre visible y sin *hover*: «La IA es un asistente de soporte. Su criterio
  como analista prevalece» (AC5.1.5).

Verificación: AC3.1.1, AC3.1.3, AC5.1.1, AC5.1.3, AC5.1.5, AC5.2.1, AC5.2.3, AC5.3.1, AC5.4.2 `[N0]`;
AC5.6.2 `[N3]`.

### 4.5 HandoffPanel · **Retirado** (cambio 01)

El Paquete de Contexto de Traspaso se retira con la épica 4 (FR5 retirado).

### 4.6 PasteTranscriptDialog (solo sesiones guiadas)

| Campo | Valor |
|---|---|
| Component | PasteTranscriptDialog |
| Description | Diálogo en dos pasos para pegar un bloque de turnos y confirmar los turnos detectados. |
| Category | input |

**States**

| State | Description | Trigger |
|---|---|---|
| editing | Área de texto; «Continuar» deshabilitado si está vacía | apertura |
| preview | «Se detectaron N turnos» + lista con número, hablante y primeras líneas | «Continuar» |
| over-limit | «El bloque tiene N turnos; el máximo es M» (o su equivalente en caracteres); «Confirmar» deshabilitado con ese motivo | supera un límite |
| empty-result | «No se detectaron turnos. Separa los turnos con una línea vacía o con una marca de hablante» | 0 turnos |
| creating | «Creando N turnos…» | «Confirmar» |
| error | Error del sistema; el texto se conserva | fallo de la API |

**Props / Inputs**

| Prop | Type | Required | Default | Description |
|---|---|---|---|---|
| sessionId | string | yes | — | Sesión destino. |
| splitPreview | `(text: string) => TurnPreview[]` | yes | — | División local con la misma especificación y los mismos ejemplos que el servidor (AC2.3.2). |
| limits | `Limits` | yes | — | Turnos, caracteres y caracteres por turno del catálogo. |

**Responsive Behaviour**

| Breakpoint | Behaviour |
|---|---|
| escritorio ancho | 720 px de ancho máximo. |
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

Verificación: AC2.3.1, AC2.3.4 `[N0]`; AC2.3.2 `[N0]` (Vitest y pytest con los mismos ejemplos);
AC2.3.3 `[N1]`.

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
| conflict | «La sesión cambió mientras confirmabas. Revisa el resumen» y resumen actualizado | `409` (AC6.1.9) |
| error | Error del sistema; el diálogo sigue abierto | fallo de la API |

**Props / Inputs**

| Prop | Type | Required | Default | Description |
|---|---|---|---|---|
| title | string | yes | — | Título. |
| summary | ReactNode | yes | — | Conteos, tramos no evaluados, estado del último modo final, modo fragmentado (AC6.1.2). |
| secondaryAction | `{ label: string; onSelect: () => void } \| null` | no | null | «Volver y relanzar el modo final». |
| confirmLabel | string | yes | — | «Finalizar», «Consolidar», «Desactivar», «Descartar copia». |
| onConfirm | `() => Promise<void>` | yes | — | Acción. |

**Responsive Behaviour**

| Breakpoint | Behaviour |
|---|---|
| escritorio ancho | 560 px de ancho máximo. |
| escritorio estrecho | Igual. |

**Accessibility**

| Requirement | Implementation |
|---|---|
| ARIA role | `AlertDialog` de Radix. |
| Keyboard interaction | Escape = «Cancelar»; el foco inicial va a «Cancelar» (AC6.1.2). |
| Label / aria-label | `aria-labelledby` al título, `aria-describedby` al resumen. |
| Contrast ratio | WCAG AA. |
| Screen reader | Lee título y resumen al abrir. |
| Focus management | Al cerrar, vuelve al botón que lo abrió; tras consolidar, al encabezado de M5; «Volver y relanzar» lleva el foco a «Relanzar modo final». |

Verificación: AC2.4.1, AC6.1.2 `[N0]`; AC6.1.6, AC6.1.9 `[N1]`.

### 4.8 ConsolidateAction

| Campo | Valor |
|---|---|
| Component | ConsolidateAction |
| Description | Botón «Consolidar reporte» con la lista de sus motivos de bloqueo. |
| Category | input |

| State | Description | Trigger |
|---|---|---|
| blocked | Lista de motivos en orden: «Finaliza la sesión para consolidar», «Lanza el modo final para consolidar», «Hay análisis en proceso», «Quedan N sugerencias pendientes» (+ enlace a la primera) | algún motivo |
| ready | Habilitado; abre ConfirmDialog | ningún motivo |
| hidden | No se muestra | sesión ajena o consolidada; rol `admin` o `investigador` |

Accesibilidad: `<button aria-disabled="true">` enfocable con `aria-describedby` a la lista de motivos.
Un modo final o un tramo en error **no** son motivo de bloqueo (FR7.1). Verificación: AC6.1.1 `[N0]` +
`[N1]`.

### 4.9 NeutralClarification (SHOULD)

Antes «SuggestedQuestion». Al pie del panel de hallazgos, «Aclaración sugerida · requiere tu decisión»
con el tema y los turnos, nunca el texto de las citas; «Aprobar» y «Descartar». «Escuchar audio» solo
aparece tras aprobar y solo suena al pulsarlo. Nada se registra como formulado sin acción del analista.
Verificación: AC10.3.3 `[N0]`; AC10.4.1 `[N0]`.

### 4.10 ReportView

Vista de M5: cabecera con quién y cuándo (hora de Colombia + UTC), SHA-256 completo con «Copiar SHA-256»
(anuncia «SHA-256 copiado»), «Descargar reporte», perfil, huella y versión del analizador, avisos que
apliquen, lista de versiones con la vigente marcada en texto y «Corregir reporte». El Markdown del
reporte se renderiza sin HTML crudo (`react/no-danger` es error en team-practices). Verificación:
AC6.1.4, AC6.3.4 `[N0]`; AC6.2.1 `[N3]`.

### 4.11 ProfilePicker

| Campo | Valor |
|---|---|
| Component | ProfilePicker |
| Description | Elección del perfil de modelos al crear una sesión guiada (M3) o importada (M7). |
| Category | input |

**States**

| State | Description | Trigger |
|---|---|---|
| loading | Esqueleto de dos opciones | carga de perfiles |
| none-selected | Ninguna opción marcada; el botón de crear deshabilitado con «Elige un perfil para crear la sesión» | apertura (AC13.1.4) |
| selected | Una opción marcada | elección |
| details-open | Proveedor y modelo de cada papel visibles | «Ver modelos por papel» |
| empty | «No hay perfiles aprobados. Pide al administrador que revise el archivo de perfiles.» | sin perfiles |
| error | Error del sistema + «Reintentar» | fallo de la API |

**Props / Inputs**

| Prop | Type | Required | Default | Description |
|---|---|---|---|---|
| profiles | `ApprovedProfile[]` | yes | — | Nombre, destino por papel (comercial o local), proveedor y modelo por papel, modo fragmentado (ventana y solapamiento), declaración de misma familia. |
| value | string \| null | yes | null | Perfil elegido. |
| onChange | `(name: string) => void` | yes | — | Cambio de elección. |

**Responsive Behaviour**

| Breakpoint | Behaviour |
|---|---|
| escritorio ancho | Lista vertical de opciones, 640 px de ancho máximo. |
| escritorio estrecho | Igual. |

**Accessibility**

| Requirement | Implementation |
|---|---|
| ARIA role | Radix `RadioGroup` con leyenda «Perfil de modelos»; cada desplegable es un `Collapsible`. |
| Keyboard interaction | Flechas entre perfiles; Tab entra al desplegable de detalles. |
| Label / aria-label | La línea en lenguaje llano y los avisos se asocian a cada opción con `aria-describedby`. |
| Contrast ratio | WCAG AA. |
| Screen reader | Al elegir, lee el nombre, la línea llana y los avisos de modo fragmentado y misma familia. |
| Focus management | Sin movimientos de foco automáticos. |

Verificación: AC13.1.1–AC13.1.4 `[N0]`; AC2.1.3 `[N1]`.

### 4.12 TranscriptImport (M7)

| Campo | Valor |
|---|---|
| Component | TranscriptImport |
| Description | Pantalla de dos pasos: archivo JSON del contrato con vista previa, y perfil; crea la sesión importada. |
| Category | input |

**States**

| State | Description | Trigger |
|---|---|---|
| idle | Solo el paso 1; botón deshabilitado con «Elige un archivo para continuar» | apertura |
| invalid-type | «El archivo debe ser JSON con el formato del contrato común» | archivo no JSON |
| invalid-schema | Primer problema + total («Turno 37: falta el hablante. Hay 3 problemas más») | esquema |
| over-limit | «La transcripción tiene N turnos; el máximo es M» (o su equivalente) | límite del catálogo |
| preview | «Se importarán N turnos (páginas X–Y), de ellos K del entrevistador y P plegados. La sesión no admitirá turnos nuevos» (AC2.6.5), primeros turnos y paso 2 visible | archivo válido |
| creating | «Importando N turnos…» | «Importar» |
| server-error | Error del sistema; archivo y perfil siguen elegidos | fallo de la API |

**Props / Inputs**

| Prop | Type | Required | Default | Description |
|---|---|---|---|---|
| schema | `JSONSchema` | yes | — | Esquema versionado del contrato común, el mismo que valida el servidor. |
| limits | `Limits` | yes | — | Catálogo único de límites. |
| onCreated | `(sessionId: string) => void` | yes | — | Abre M4. |

**Responsive Behaviour**

| Breakpoint | Behaviour |
|---|---|
| escritorio ancho | Columna única de 800 px de ancho máximo. |
| escritorio estrecho | Igual. |

**Accessibility**

| Requirement | Implementation |
|---|---|
| ARIA role | `<form>` con dos `<fieldset>` («Archivo», «Perfil de modelos»); campo de archivo nativo. |
| Keyboard interaction | Todo con Tab; el campo de archivo se abre con Enter o Espacio. |
| Label / aria-label | Etiqueta visible y la nota de formato antes del campo. |
| Contrast ratio | WCAG AA. |
| Screen reader | El resultado de la validación se anuncia una vez («Archivo válido: 312 turnos» o el primer problema). |
| Focus management | Tras validar, el foco va al resumen de la vista previa o al mensaje de error. |

Verificación: AC2.6.2, AC2.6.3 `[N0]` + `[N1]`; AC2.6.1 `[N1]`; AC5.6.2 `[N3]` (importar y confirmar
solo con teclado).

### 4.13 QuoteBlock

| Campo | Valor |
|---|---|
| Component | QuoteBlock |
| Description | Una cita del hallazgo dentro de la tarjeta: letra, turno, hablante, página, el turno anterior y el siguiente como contexto, la cita completa y «Ir a la cita». |
| Category | display |

**States**

| State | Description | Trigger |
|---|---|---|
| default | Contexto atenuado (primeras 2 líneas) + cita completa entre «» | render |
| with-notice | Aviso «Cita en un turno del entrevistador» o de turno plegado | cita en `ENT` o `plegado` (AC3.1.4) |
| fragments | Fragmentos unidos por « […] » visibles | cita con « […] » |
| edge | Sin turno anterior o siguiente | primer o último turno |

**Props / Inputs**

| Prop | Type | Required | Default | Description |
|---|---|---|---|---|
| letter | `'A' \| 'B'` | yes | — | Marca de la cita. |
| quote | `Quote` | yes | — | Texto, turno, hablante, página, avisos. |
| before / after | `Turn \| undefined` | no | — | Turnos de contexto. |
| onGoTo | `() => void` | yes | — | «Ir a la cita». |

**Responsive Behaviour**

| Breakpoint | Behaviour |
|---|---|
| escritorio ancho | Ancho de la tarjeta. |
| escritorio estrecho | Igual. |

**Accessibility**

| Requirement | Implementation |
|---|---|
| ARIA role | `<figure>` con `<figcaption>` «Cita A · turno N · hablante · página»; la cita en `<blockquote>`. |
| Keyboard interaction | «Ir a la cita A» es un `<button>`. |
| Label / aria-label | El contexto se marca como «Contexto: turno N». |
| Contrast ratio | El contexto atenuado mantiene ≥ 4.5:1. |
| Screen reader | Lee la letra, el turno y la cita; el contexto después. |
| Focus management | Ver TurnItem. |

Verificación: AC3.1.1, AC3.1.2, AC3.1.4 `[N0]`.

### 4.14 FinalModeBar y RunsDisclosure

| Campo | Valor |
|---|---|
| Component | FinalModeBar (+ RunsDisclosure) |
| Description | Franja fija encima del panel de hallazgos con el estado, el progreso y la acción del modo final; desplegable con todas las corridas de la sesión. |
| Category | feedback + input |

**States**

| State | Description | Trigger |
|---|---|---|
| unavailable | «No lanzado · disponible al finalizar la sesión» | guiada sin finalizar |
| not-launched | «No lanzado» + «Lanzar modo final» | finalizada o importada |
| queued / processing | Estado, etapa, ventanas o llamadas «N de M», cronómetro; «Relanzar» deshabilitado con «El modo final ya está en proceso» | corrida activa |
| done | «Modo final terminado» + N hallazgos nuevos + «Relanzar modo final» | fin correcto |
| run-detail | Fila de «Corridas» desplegada: registro de modelos en solo lectura (papel, proveedor, modelo, versión, cuantización o esfuerzo, motor, llamadas, *tokens*, costo y total; «sin precio»; «Aún no hay llamadas registradas») | botón de la fila (AC12.5.3) |
| error | Causa + «El analizador no pudo procesar la transcripción completa. Revisión manual requerida» + código + «Relanzar modo final» | `estado: error` |
| locked | Último estado, sin acción | sesión consolidada |
| conflict | «Otro lanzamiento ya está en proceso» | `409` (AC2.7.6) |

**Props / Inputs**

| Prop | Type | Required | Default | Description |
|---|---|---|---|---|
| finalRun | `Run \| null` | yes | — | Último modo final lanzado. |
| runs | `Run[]` | yes | — | Corridas de la sesión, más recientes arriba. |
| canLaunch | boolean | yes | — | Dueño, sesión finalizada o importada y no consolidada. |
| onLaunch | `() => Promise<void>` | yes | — | `POST` del modo final. |

**Responsive Behaviour**

| Breakpoint | Behaviour |
|---|---|
| escritorio ancho | Fija arriba de la columna derecha. |
| escritorio estrecho | Fija arriba de la pestaña «Hallazgos»; la pestaña «Transcripción» muestra el estado en una línea. |

**Accessibility**

| Requirement | Implementation |
|---|---|
| ARIA role | `<section>` con encabezado «Modo final»; las corridas son una `<table>` dentro de un `Collapsible`. |
| Keyboard interaction | «Lanzar/Relanzar» es un `<button>` (`aria-disabled` cuando está en proceso). |
| Label / aria-label | El progreso usa texto («ventana 5 de 8»), no solo una barra. |
| Contrast ratio | WCAG AA. |
| Screen reader | Inicio, fin y error se anuncian en la región en vivo (AC5.6.5). |
| Focus management | Lanzar deja el foco en el botón. |

Verificación: AC2.7.1, AC2.7.3, AC2.7.4, AC2.7.6, AC10.1.1, AC12.5.3 `[N0]` + `[N1]`.

### 4.15 FindingsFilters

Resumen «N pendientes · N aceptadas · N editadas · N descartadas» (siempre de toda la sesión) y tres
filtros nativos `<select>`: estado, tipo (7 rótulos) y origen («Incremental», «Final»), con «Quitar
filtros». Los grupos «Pendientes» y «Decididos» son encabezados de nivel 3. Cambiar un filtro anuncia
«N hallazgos con estos filtros». Verificación: `[N0]` Vitest (orden por turno de la cita A dentro de
cada grupo; el resumen no cambia con los filtros).

### 4.16 ProfileNotices

Franja informativa bajo la cabecera de sesión (y en la cabecera del reporte) con los avisos de modo
fragmentado y de misma familia, con los textos de AC3.7.1 y AC13.1.2. No se puede cerrar. Tratamiento
informativo (ⓘ + texto), distinto del error del sistema. Verificación: AC3.7.1, AC13.1.2, AC13.1.3
`[N0]`.

### 4.17 ResearchReports (M8)

| Campo | Valor |
|---|---|
| Component | ResearchReports (lista, UploadReportDialog, ReportDetail, ReportComparison) |
| Description | Consola de solo consulta del investigador: subir reportes JSON de la CLI, listarlos, ver su detalle y comparar dos. |
| Category | display + input |

**States**

| State | Description | Trigger |
|---|---|---|
| empty | «Aún no hay reportes. Sube el JSON que produce la línea de comandos» | sin reportes |
| list | Tabla con casillas, filtros y «Comparar seleccionados» | reportes |
| uploading | «Subiendo y validando…» | subir |
| upload-ok | «Reporte subido. Se guardaron solo metadatos y cifras; el texto de transcripciones, hallazgos y citas se descartó» | válido |
| upload-invalid | Primer problema + total; o «Falta el campo <campo>» | esquema o AC14.3.1 |
| duplicate | «Este reporte ya está subido» | mismo SHA-256 |
| detail | Metadatos, avisos, métricas («No informado» si faltan) y registro de modelos | abrir |
| compare | Tabla de dos columnas con «=» / «≠» y diferencias | dos marcados |
| not-comparable | «Conjuntos distintos: las métricas no son comparables»; solo metadatos | conjuntos o tipos distintos |

**Props / Inputs**

| Prop | Type | Required | Default | Description |
|---|---|---|---|---|
| reports | `ResearchReportSummary[]` | yes | — | Solo metadatos y cifras. |
| onUpload | `(file: File) => Promise<UploadResult>` | yes | — | Validación en el servidor. |

**Responsive Behaviour**

| Breakpoint | Behaviour |
|---|---|
| escritorio ancho | Tablas a ancho completo. |
| escritorio estrecho | Las tablas de registro de modelos y comparación se desplazan en horizontal dentro de su contenedor, con encabezados fijos. |

**Accessibility**

| Requirement | Implementation |
|---|---|
| ARIA role | `<table>` nativas con `<th scope>`; casillas nativas con etiqueta «Seleccionar reporte del <fecha>». |
| Keyboard interaction | Todo con Tab y Espacio; «Comparar seleccionados» `aria-disabled` con su motivo. |
| Label / aria-label | Las celdas «=» / «≠» tienen texto accesible «igual» / «distinto». |
| Contrast ratio | WCAG AA. |
| Screen reader | El resultado de la subida se anuncia una vez. |
| Focus management | Tras subir, foco en el mensaje de resultado; al abrir detalle o comparación, en su encabezado. |

Reglas: solo el rol `investigador` llega a M8; el servidor descarta cualquier texto de transcripción,
hallazgo o cita antes de guardar (NFR12) y lo confirma en la respuesta. Verificación: AC14.3.1 `[N0]`
(rechazo de una salida sin modelo, cuantización, motor o versión); las historias propuestas US12.6 y
US12.7 (tabla de precisiones de `mockups.md`) fijarán el resto si el humano las aprueba.

---

## 5. Flujos de usuario

### F1 — Sesión guiada de punta a punta

Persona: Analista de Verdad. Disparador: «Nueva sesión».

1. M3 → escribe la entrevista → elige un perfil (ninguno viene marcado) → «Crear sesión» → M4 vacía.
2. M4 → elige el hablante → escribe el turno → `Ctrl+Enter` → «En cola» → «Procesando» → «Analizado».
3. M4 → aparece una tarjeta en su lugar del panel (sin modal) → el contador se anuncia.
4. Tarjeta → «Ir a la cita A» / «Ir a la cita B» → «Volver al hallazgo» → «Ver observaciones» →
   «Aceptar» / «Editar» / «Descartar».
5. Cabecera → «Finalizar sesión» → confirmar → la franja ofrece «Lanzar modo final» → lanzar.
6. Modo final terminado → nuevas tarjetas en «Pendientes» → decidirlas.
7. Cabecera → «Consolidar reporte» → resumen → «Consolidar» → M5 → «Descargar reporte» → compara el
   SHA-256 visible.

Errores: tramo no evaluado → «Reintentar tramo»; consolidación bloqueada → lista de motivos y enlace a la
primera pendiente; conflicto al consolidar → resumen actualizado.

### F2 — Hecho No Documentado · **Retirado** (cambio 01)

### F3 — Reanudación

Entrada con sesión «Suspendida» → diálogo «Se detectó una interrupción inesperada…» → «Reanudar» (M4 en
el último turno) o «Más tarde» (sigue en M1 como «Suspendida»).

### F4 — Corrección de un reporte

M5 → «Corregir reporte» → M4 en copia de trabajo (solo estados y notas) → cambia decisiones →
«Consolidar reporte» → versión nueva en M5, con la anterior en la lista.

### F5 — Transcripción importada

M1 → «Importar transcripción» → M7 → elige el archivo → vista previa (o el primer problema y el total) →
elige el perfil → «Importar» → M4 importada, cerrada a turnos nuevos → «Lanzar modo final»
→ revisar → consolidar como en F1.

### F6 — Modo final con error

Franja «Modo final con error» con la causa → «Relanzar modo final» (la corrida anterior queda en
«Corridas») → o consolidar igualmente: el diálogo avisa, ofrece «Volver y relanzar el modo final», y el
reporte rotula «Modo final no completado. Revisión manual requerida» con su código.

### F7 — Comparar dos reportes (investigador)

M8 → «Subir reporte JSON» (dos veces) → marca los dos → «Comparar seleccionados» → tabla con «=» / «≠» y
diferencias; si los conjuntos difieren, solo metadatos y el aviso.

---

## 6. Mensajes del sistema (catálogo)

| Clave (inglés) | Texto visible | Tratamiento |
|---|---|---|
| `finding.label` | «Sugerencia de revisión · Contradicción en el relato» | Sugerencia de revisión |
| `finding.reminder` | «La IA es un asistente de soporte. Su criterio como analista prevalece» | Informativo |
| `finding.observations_required` | «Despliega y lee las observaciones para habilitar esta acción» | Motivo de deshabilitado |
| `finding.dismiss_note_required` | «Escribe por qué descartas esta sugerencia» | Error de campo |
| `finding.edit_required` | «Escribe tu reformulación para guardar» | Motivo de deshabilitado |
| `quote.interviewer_turn` | «Cita en un turno del entrevistador» | Aviso |
| `quote.folded_turn` | Redacción en lenguaje llano que fija Functional Design (AC3.1.4) | Aviso |
| `segment.error` | «El analizador no pudo procesar este tramo. Revisión manual requerida» | Error del sistema |
| `segment.not_evaluated` | «Tramo no evaluado» | Error del sistema (sesión y reporte) |
| `error.cause.provider` | «El servicio de modelos no respondió» | Causa |
| `error.cause.timeout` | «El análisis superó el tiempo máximo» | Causa |
| `error.cause.invalid_output` | «La respuesta del modelo no tuvo el formato esperado» | Causa |
| `error.cause.content_block` | «El filtro de contenido del proveedor rechazó la petición» | Causa |
| `error.cause.anonymizer` | «El anonimizador no respondió. No se envió ningún dato fuera del clúster» | Causa |
| `final.error` | «El analizador no pudo procesar la transcripción completa. Revisión manual requerida» | Error del sistema |
| `final.in_progress` | «El modo final ya está en proceso» | Motivo de deshabilitado |
| `final.not_completed` | «Modo final no completado. Revisión manual requerida» | Reporte |
| `consolidate.blocked.*` | «Finaliza la sesión para consolidar» · «Lanza el modo final para consolidar» · «Hay análisis en proceso» · «Quedan N sugerencias pendientes» | Motivos de deshabilitado |
| `profile.commercial` | «Comercial: el texto sale seudonimizado del clúster» | Informativo |
| `profile.local` | «Local: nada sale del clúster» | Informativo |
| `profile.immutable` | «El perfil no se puede cambiar después de crear la sesión» | Informativo |
| `profile.windowed` | «Análisis por ventanas de N turnos (solapamiento de M). No se buscaron contradicciones entre turnos separados por más de N turnos» | Informativo |
| `profile.same_family` | «El modelo que propone cada contradicción y el que la confirma son de la misma familia: la confirmación es menos independiente» | Informativo |
| `import.invalid_type` | «El archivo debe ser JSON con el formato del contrato común» | Error de campo |
| `import.preview_confirm` | «Se importarán N turnos (páginas X–Y), de ellos K del entrevistador y P plegados. La sesión no admitirá turnos nuevos» | Confirmación (AC2.6.5) |
| `session.empty` | «Aún no hay turnos. Escribe el primer turno o pega un bloque de turnos» | Estado vacío (AC2.2.5) |
| `turn.send_empty` | «Escribe el turno para enviarlo» | Motivo de deshabilitado |
| `profile.windowed_short` | «Análisis por ventanas: no busca contradicciones entre turnos separados por más de N turnos» | Informativo (AC13.1.3) |
| `profile.choose` | «Elige un perfil para crear la sesión» | Motivo de deshabilitado (AC13.1.4) |
| `import.choose_file` | «Elige un archivo para continuar» | Motivo de deshabilitado |
| `run.no_calls` | «Aún no hay llamadas registradas» | Estado vacío |
| `price.missing` | «sin precio» | Informativo (AC12.5.2) |
| `research.empty` | «Aún no hay reportes. Sube el JSON que produce la línea de comandos» | Estado vacío |
| `research.compare_needs_two` | «Marca dos reportes para compararlos» | Motivo de deshabilitado |
| `research.duplicate` | «Este reporte ya está subido» | Error de campo |
| `research.missing_field` | «Falta el campo <campo>» | Error de campo (AC14.3.1) |
| `metric.not_reported` | «No informado» | Informativo |
| `research.upload_ok` | «Reporte subido. Se guardaron solo metadatos y cifras; el texto de transcripciones, hallazgos y citas se descartó» | Confirmación |
| `research.not_comparable` | «Conjuntos distintos: las métricas no son comparables» | Aviso |
| `session.read_only` | «Sesión de <usuario>. Solo lectura» | Informativo |
| `session.resume_prompt` | «Se detectó una interrupción inesperada en la sesión. ¿Desea reanudar desde el último turno registrado?» | Diálogo |
| `report.working_copy` | «Copia de trabajo de la versión N. Solo puedes cambiar estados y notas» | Informativo |
| `layout.narrow_screen` | «Veridicus está diseñado para pantallas de escritorio (1024 px o más)» | Informativo |

Los `code` de Problem Details se muestran como «Código: <code>», en tamaño secundario, nunca como único
mensaje. Las claves `turn.error.*` y `undocumented.notice` de la primera pasada se retiran.

**Regla del catálogo.** Toda cadena visible de la consola sale del catálogo, sin excepciones: además de
las claves de esta tabla, cada texto entre «» de `mockups.md` (estados vacíos, motivos, diálogos, avisos
y rótulos de M0–M8) entra con su clave. Una prueba `[N0]` falla si un componente renderiza texto literal
que no sale del catálogo, y el escaneo de vocabulario prohibido (AC5.5.1) recorre el catálogo completo.
