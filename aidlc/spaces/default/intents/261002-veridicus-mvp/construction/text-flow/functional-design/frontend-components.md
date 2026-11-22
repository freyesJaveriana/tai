# Componentes de la consola — U4 text-flow

**Revisión 2 (2026-11-21), segunda pasada por el cambio 01 (DT27), la adenda 02 y las revisiones 3 de
Inception.** Sustituye a la revisión 1 del 2026-10-03. Los componentes que salen quedan «Retirado» sin
renumerar ni borrar (regla de `project.md`).
- **Se mantienen** (cambian): AppShell, NewSessionPage (M3), SessionPage (M4), SessionHeader,
  TranscriptColumn, EmptyState, TurnItem, TurnComposer, RetryAction, SuggestionsColumn, PendingCounter,
  ReviewSuggestionCard y LiveRegion. Origen: M3 y M4 de la revisión 3 de Refined Mockups y C1.
- **Salen** (`Retirado`): ScenariosPage (M2), ScenarioCatalog, ScenarioRow, UploadScenarioDialog,
  ScenarioVersionPicker, HandoffPanel y UndocumentedNotice. Origen: cambio 01.
- **Entran:** NoticeBand (US15.5), ConsentForm (US15.4), ProfilePicker y ProfileOption (US13.1),
  SpeakerToggle y CharCounter (US2.2), ProfileNotices (US3.7, US13.1), BlockedBanner (AC11.3.8),
  RunSpan (US3.2, P11), CitationBlock y CitationNotice (US3.1), RunsList y ModelCallsTable (US12.5).

**Insumos.** `inception/refined-mockups/interaction-spec.md` (interaction-spec) y M3 y M4 de
`mockups.md` (revisión 3); el contrato C1 de `inception/contract-design/contract-summary.md`
(contract-summary); las historias de U4 en `inception/units-generation/unit-of-work-story-map.md`
(unit-of-work-story-map) y su alcance en `unit-of-work.md` (unit-of-work); FR3, FR4 y VE-01/VE-06 de
requirements; AnalystConsole y ConsoleApi de components; reglas BR4–BR19 de `rules.md`. El aspecto, los
estados visuales, los puntos de quiebre y la accesibilidad de cada pantalla ya están en interaction-spec y
mockups y no se repiten. Este documento fija la **jerarquía**, los **datos** de cada componente, de qué
**ruta de C1** salen, el **estado** de la consola y la **validación** de los formularios de U4.

## 1. Jerarquía

```text
AppShell (cabecera común de U3) ── NoticeBand (todas las pantallas, también el inicio de sesión)
├── ScenariosPage (M2) ·································· Retirado
├── NewSessionPage (M3)
│   ├── ConsentForm
│   └── ProfilePicker ── ProfileOption* ── ProfileNotices
└── SessionPage (M4)
    ├── SessionHeader ── ProfileNotices, BlockedBanner (acciones de U6/U7)
    ├── TranscriptColumn
    │   ├── EmptyState
    │   ├── TurnItem* ── StatusBadge, CitationMark (A/B)
    │   ├── RunSpan* ── RetryAction
    │   └── TurnComposer ── SpeakerToggle, CharCounter
    ├── SuggestionsColumn
    │   ├── FinalModeStrip (U6) ── RunsList ── ModelCallsTable
    │   ├── PendingCounter
    │   └── ReviewSuggestionCard* ── CitationBlock (A, B) ── CitationNotice (acciones de U5)
    ├── HandoffPanel ······································ Retirado
    └── LiveRegion (aria-live="polite", una por pantalla)
```

<!-- Texto alternativo: la consola tiene una cabecera común con la franja del aviso de propósito limitado en todas las pantallas. Nueva sesión (M3) tiene el formulario de consentimiento y el selector de perfil con sus avisos. Sesión (M4) tiene la cabecera con avisos del perfil y el banner de bloqueo; la columna de la transcripción con estado vacío, turnos con marcas de cita, tramos en error con reintento y el redactor con hablante y contador; la columna de hallazgos con la franja del modo final de U6 que contiene la lista de corridas y su registro de modelos, el contador y las tarjetas con sus dos citas y avisos; y una región en vivo. La página de escenarios y el panel del paquete están retirados. -->

## 2. Componentes y sus datos

| Componente | Props / datos | Ruta de C1 | Reglas |
|---|---|---|---|
| ScenarioCatalog, ScenarioRow, UploadScenarioDialog, ScenarioVersionPicker | Retirado (cambio 01) | — | — |
| NoticeBand | `Notice.text`, `Notice.version`; error del sistema si falla | `GET /notice` (pública) | BR18.1 |
| ConsentForm | `tipo` (`persona` \| `autoridad`), `version_texto`, `constancia`, `autoriza_transferencia`, `autoriza_voz`, `autoriza_conservar_audio`, `requiere_mandato`, `constancia_mandato` | `POST /sessions` (bloque `consentimiento`) | BR14.1, BR14.2, BR14.5 |
| ProfilePicker | `ProfileSummary[]`, ninguno elegido; filtra los comerciales si `autoriza_transferencia` es falso | `GET /profiles` | BR14.4, BR14.5, BR14.7 |
| ProfileOption | `profile_name`, línea llana (comercial o local), `roles[]` en un desplegable | `GET /profiles` | BR14.7 |
| ProfileNotices | `chunking_enabled` con N de C25, `same_family_warning`; en M4, ventana y solapamiento de la última corrida | `GET /profiles`, `GET /sessions/{id}` | BR14.7, BR14.8, BR17.3 |
| SessionHeader | `entrevista`, `origin`, `status`, `profile_name`, `config_sha256` (12 primeros), papel comercial o local | `GET /sessions/{id}` | BR4.1, BR14.8 |
| BlockedBanner | `blocked_code`; «Sesión bloqueada por un incidente de anonimización. No se lanzan corridas nuevas» | `GET /sessions/{id}` | BR16.5 |
| TurnComposer | texto, `hablante`, `client_request_id`; deshabilitado (enfocable) con motivo si el texto está vacío, supera `turn_max_chars`, la sesión no admite turnos o no es el dueño | `POST /sessions/{id}/turns` | BR5.1, BR5.5, BR13.6, BR15.1 |
| SpeakerToggle | `TEST` (por defecto) \| `ENT` | — | BR15.1 |
| CharCounter | «X / M caracteres», M de C25 servido con la sesión | — | BR5.1 |
| TurnItem | `Turn` (número, hablante, página, plegado, texto) y su estado derivado | `GET /sessions/{id}` | BR13.4, BR17.1 |
| RunSpan | corrida incremental en error: turnos del tramo, causa, mensaje, `error_code`; o «Cubierto por el modo final» | `GET /sessions/{id}` | BR13.3, BR17.2 |
| RetryAction | solo para el dueño; deshabilitado (enfocable) con motivo si la sesión no admite corridas | `POST /sessions/{id}/runs/{run_id}/retry` | BR5.9, BR16.5, BR16.9 |
| RunsList | `Run[]` (tipo, número, estado, code, tramo, quién y cuándo; «Cubierto por el modo final») | `GET /sessions/{id}` | BR17.2 |
| ModelCallsTable | `ModelCall[]` con total; «sin precio»; «Aún no hay llamadas registradas» | `GET /sessions/{id}/runs/{run_id}/model-calls` | BR17.4 |
| ReviewSuggestionCard | `ReviewSuggestion` (`hecho`, `tipo`, `cita_a`, `cita_b`, `observaciones` plegadas, `actos`); rótulo del catálogo | `GET /sessions/{id}`; `POST /suggestions/{id}/observation-views` (U5) | BR8.6, BR12.4, BR13.1 |
| CitationBlock | cita con marca A (barra continua) o B (discontinua), turno, hablante, página, turno anterior y siguiente atenuados; «Ir a la cita» | `GET /sessions/{id}` | BR13.2 |
| CitationNotice | `avisos` de la cita: `turno_entrevistador`, `turno_plegado` | — | BR17.5 |
| PendingCounter | sugerencias pendientes de toda la sesión | `GET /sessions/{id}` | BR13.1 |
| HandoffPanel, UndocumentedNotice | Retirado (cambio 01) | — | — |
| LiveRegion | un mensaje agregado por corrida | — | BR13.1 |

Las acciones «Aceptar», «Editar» y «Descartar» de la tarjeta, y el registro de «Observaciones
consultadas», son de U5. FinalModeStrip, el pegado, finalizar, pausar, terminar y retirar el
consentimiento son de U6; consolidar, de U7. U4 deja en M4 los huecos y los datos que esas unidades usan.

## 3. Estado de la consola

- **Sondeo de la sesión** (`useSessionPolling`): mientras haya corridas `queued` o `processing`, pide
  `GET /sessions/{id}?since=<cursor>` cada `poll_interval_s` (C25); sin corridas en curso, baja a un
  sondeo lento que sigue sirviendo de latido (U6). Fusiona por `turn_id`, `run_id` y `suggestion_id`; los
  turnos siempre se ordenan por `n`.
- **Estado derivado:** la función pura `turnState(turn, runs, origin)` calcula el estado de cada turno
  (BR17.1) y `runCoverage(runs)` marca los tramos cubiertos por el modo final (BR17.2). Las dos tienen
  pruebas de nivel 0 con todas las combinaciones.
- **Anuncio por corrida:** tras cada sondeo, la consola compara corridas y sugerencias con el sondeo
  anterior y publica un solo mensaje por corrida que empezó, terminó o falló (p. ej. «Corrida del turno 4
  terminada · 1 sugerencia nueva · 2 pendientes»). Nunca anuncia un turno suelto ni un sondeo sin cambios.
- **Selección:** la tarjeta seleccionada guarda sus dos citas y las marca en sus turnos; la llegada de
  datos no mueve el foco.
- **Envío:** cada envío genera un `client_request_id` (UUID) que se reutiliza si el navegador repite la
  petición; el turno aparece de inmediato con la respuesta 202.
- **Errores de red:** un fallo de sondeo no borra lo mostrado; tras varios seguidos se muestra «No se pudo
  conectar con el servidor. Intenta de nuevo.»; un 401 lleva al inicio de sesión con la ruta guardada
  (U3).
- **Listas largas:** la transcripción se renderiza por bloques al desplazarse (ventana virtual sobre
  `<ol>` con `aria-setsize` y `aria-posinset`), sin romper la numeración ni el orden de lectura.

## 4. Validación de formularios

| Formulario | Campo | Regla en la consola | Regla repetida en la API |
|---|---|---|---|
| ConsentForm | tipo | Obligatorio: «Consentimiento de la persona» o «Constancia de la autoridad que lo exime» | 422 `validation.invalid_request` |
| ConsentForm | versión del texto | Obligatoria, 1 a 64 caracteres | 422 |
| ConsentForm | constancia | Obligatoria si el tipo es autoridad; solo un identificador (letras, números y `._:-`) | 422 |
| ConsentForm | constancia del mandato | Obligatoria si la persona es compareciente o tercero civil; mismo patrón | 422 |
| ProfilePicker | perfil | Obligatorio, ninguno preseleccionado; «Elige un perfil para crear la sesión» | 422 `profile.not_approved` / `profile.transfer_not_authorized` |
| NewSessionPage | entrevista | Obligatoria, 1 a 120 caracteres | 422 |
| TurnComposer | texto | 1 a `turn_max_chars` tras quitar espacios de los bordes; contador siempre visible | 422 vacío / 413 `limits.exceeded` |

La consola valida antes de enviar para prevenir el error, pero la API es la autoridad (interaction-spec
§1, principio 3). Un campo inválido muestra su mensaje junto al campo y el foco va al primero inválido.

## 5. Flujos de interacción

| Flujo | Componentes | Ruta de C1 |
|---|---|---|
| F3 crear sesión | ConsentForm, ProfilePicker, ProfileOption, ProfileNotices | `GET /profiles`, `POST /sessions` |
| F4 enviar turno | TurnComposer, SpeakerToggle, CharCounter, TurnItem | `POST /sessions/{id}/turns` |
| F7 tramo en error | RunSpan, RetryAction | `POST /sessions/{id}/runs/{run_id}/retry` |
| F8 ver el hallazgo | ReviewSuggestionCard, CitationBlock, CitationNotice, TurnItem, LiveRegion | `GET /sessions/{id}` |
| F11 sesión bloqueada | BlockedBanner, RunSpan, RetryAction | `GET /sessions/{id}` |
| F12 tramo cubierto | RunsList, RunSpan | `GET /sessions/{id}` |
| F13 aviso | NoticeBand | `GET /notice` |
| F15 registro de modelos | RunsList, ModelCallsTable | `GET /sessions/{id}/runs/{run_id}/model-calls` |

## 6. Accesibilidad y vocabulario

- Todos los componentes de U4 entran en la suite `@axe-core/playwright` (WCAG 2.1 AA) que esta unidad
  crea y que las demás amplían con sus pantallas (BR13.7).
- El flujo de U4 se recorre solo con teclado (`Tab`, `Enter`, `Espacio`, `Escape`, y `Ctrl+Enter` para
  enviar el turno) con el foco siempre visible. Los botones deshabilitados con motivo usan
  `aria-disabled="true"`, reciben el foco y leen su motivo con `aria-describedby` (AC5.6.4).
- Ningún estado se distingue solo por color: cada estado de turno, corrida, hallazgo y sesión lleva icono
  y texto; las citas A y B llevan letra y estilo de barra.
- Ningún componente escribe rótulos de resultado propios: los lee del catálogo de rótulos de U1. Todos los
  textos salen del catálogo de mensajes, que pasa el escaneo de vocabulario prohibido; el aviso se lee de
  `GET /notice` y es la única cadena que el escáner exceptúa (BR12.2).
- Los atributos `data-testid` siguen `<componente>-<rol>` (p. ej. `turn-composer-submit-button`,
  `citation-block-a-goto`).
