# Componentes de la consola — U4 text-flow

**Insumos.** Especificación de componentes y flujos de `inception/refined-mockups/interaction-spec.md`
(interaction-spec) y pantallas M2, M3 y M4 de `mockups.md`; contrato C1 de
`inception/contract-design/contract-summary.md`; reglas BR1–BR13 de `rules.md`. El aspecto, los
estados visuales, los puntos de quiebre y la accesibilidad de cada componente ya están en
interaction-spec §4 y no se repiten; este documento fija la **jerarquía**, los **datos** que recibe
cada componente, de qué **ruta de C1** salen, el **estado** de la consola y la **validación** de los
formularios de U4.

## 1. Jerarquía

```text
AppShell (cabecera común: secciones, usuario, rol, «Cerrar sesión» — U3)
├── ScenariosPage (M2)
│   ├── ScenarioCatalog
│   │   └── ScenarioRow ── StatusBadge (indexing | ready | error)
│   └── UploadScenarioDialog
├── NewSessionPage (M3)
│   └── ScenarioVersionPicker ── StatusBadge
└── SessionPage (M4)
    ├── SessionHeader (escenario, versión, SHA-256 corto, umbral; acciones de U6/U7)
    ├── TranscriptColumn
    │   ├── EmptyState
    │   ├── TurnItem* ── StatusBadge, UndocumentedNotice, RetryAction
    │   └── TurnComposer
    ├── SuggestionsColumn
    │   ├── PendingCounter
    │   └── ReviewSuggestionCard* (vista de U4; acciones de U5)
    ├── HandoffPanel (panel lateral no modal)
    └── LiveRegion (aria-live="polite", una por pantalla)
```

<!-- Texto alternativo: la consola tiene una cabecera común y tres páginas de U4: escenarios (catálogo con filas y diálogo de carga), nueva sesión (selector de versión) y sesión (cabecera, columna de transcripción con estado vacío, turnos y redactor, columna de sugerencias con contador y tarjetas, panel lateral del paquete y región en vivo). -->

## 2. Componentes y sus datos

| Componente | Props / datos | Ruta de C1 | Reglas |
|---|---|---|---|
| ScenarioCatalog | lista de `ScenarioVersion` agrupada por escenario | `GET /scenarios` | BR3.1, BR3.2 |
| UploadScenarioDialog | `name`, `file` | `POST /scenarios` (multipart) | BR1.1–BR1.4 |
| ScenarioVersionPicker | versiones `ready`, la más reciente preseleccionada; las demás «versión anterior»; `indexing` y `error` visibles pero no elegibles | `GET /scenarios`, `POST /sessions` | BR2.3, BR3.1, BR4.1 |
| SessionHeader | `scenario_name`, `version_number`, `scenario_sha256` (12 primeros caracteres), `similarity_threshold` | `GET /sessions/{id}` | BR4.1 |
| TurnComposer | `disabled` si el texto está vacío, si supera 2 000 caracteres, si la sesión no está `open` o si el usuario no es el dueño | `POST /sessions/{id}/turns` | BR5.1, BR5.5, BR13.6 |
| TurnItem | `Turn` (número, texto, estado, etapa, `error_code`), resaltado del fragmento seleccionado | `GET /sessions/{id}` | BR13.2–BR13.4 |
| RetryAction | visible solo para el dueño y solo con el turno en `error` | `POST /sessions/{id}/turns/{n}/retry` | BR5.9 |
| UndocumentedNotice | texto exacto del catálogo `undocumented.notice`; no cuenta como pendiente | — | BR13.5 |
| ReviewSuggestionCard | `ReviewSuggestion` (fragmento, cita, `document_id`, CoT plegable); rótulo del catálogo de rótulos | `GET /sessions/{id}`; `POST /suggestions/{id}/cot-views` | BR12.4, BR13.1 |
| PendingCounter | número de sugerencias en `pending` | `GET /sessions/{id}` | BR13.1 |
| HandoffPanel | `HandoffPackage` (fragmento, turnos previos, «Turnos previos disponibles: N de 3», 3 pasajes con coeficiente, CoT interrumpida) | `GET /sessions/{id}` | BR10.2–BR10.4, BR13.5 |
| LiveRegion | mensaje agregado del último sondeo | — | BR13.1 |

Las acciones «Aceptar», «Editar» y «Descartar» de la tarjeta son de U5; U4 entrega la tarjeta en modo
lectura y el registro de «CoT consultada» al desplegarla.

## 3. Estado de la consola

- **Sondeo de la sesión** (`useSessionPolling`): mientras haya turnos `queued` o `processing`, pide
  `GET /sessions/{id}?since=<cursor>` cada *N* segundos (NFR Requirements); con todo evaluado, baja a
  un sondeo lento que sigue sirviendo de latido (U6). Fusiona los cambios por `turn_id` y
  `suggestion_id`; nunca reordena los turnos (orden por `number`).
- **Anuncio agregado**: tras cada sondeo calcula «Turno N evaluado · K sugerencias nuevas · P
  pendientes» y lo publica una sola vez en la LiveRegion; no anuncia sondeos sin cambios.
- **Selección**: la tarjeta seleccionada guarda `turn_id` y la posición del fragmento para resaltarlo
  en su TurnItem; el foco no se mueve por la llegada de datos.
- **Envío**: cada envío genera un `client_request_id` (UUID) que se reutiliza si el navegador repite la
  petición; el turno se agrega de inmediato con la respuesta 202.
- **Errores de red**: un fallo de sondeo no borra lo mostrado; tras varios fallos seguidos se muestra el
  error del sistema «No se pudo conectar con el servidor. Intenta de nuevo.»; un 401 lleva a M0 con la
  ruta guardada (U3).

## 4. Validación de formularios

| Formulario | Campo | Regla en la consola | Regla repetida en la API |
|---|---|---|---|
| UploadScenarioDialog | `name` | Obligatorio, 1–120 caracteres | 422 `validation.invalid_request` |
| UploadScenarioDialog | `file` | Extensión `.md` o `.txt`; tamaño ≤ 1 048 576 bytes antes de enviar | 413 / 415 / 422 con los mensajes de AC1.1.2 |
| TurnComposer | texto | 1–2 000 caracteres tras quitar espacios de los bordes; contador visible desde 1 800 | 422 `turn.too_long` / `validation.invalid_request` |

La consola valida antes de enviar para prevenir el error, pero la API es la autoridad (interaction-spec
§1, principio 3).

## 5. Flujos de interacción

| Flujo de interaction-spec | Componentes | Ruta de C1 |
|---|---|---|
| F1 pasos 1–4 (crear sesión, enviar turno, ver tarjeta, ver CoT) | ScenarioVersionPicker, TurnComposer, TurnItem, ReviewSuggestionCard | `POST /sessions`, `POST …/turns`, `GET /sessions/{id}`, `POST …/cot-views` |
| F2 Hecho No Documentado | UndocumentedNotice, HandoffPanel | `GET /sessions/{id}` |
| Turno en error | TurnItem, RetryAction | `POST …/retry` |

## 6. Accesibilidad y vocabulario

- Todos los componentes de U4 entran en la suite `@axe-core/playwright` (WCAG 2.1 AA) que esta unidad
  crea y que las demás amplían con sus pantallas (BR13.7).
- El flujo F1 se recorre solo con teclado: `Tab`, `Enter`, `Espacio`, `Escape` y `Ctrl+Enter` para
  enviar; el foco siempre visible; Escape cierra el HandoffPanel y devuelve el foco al aviso.
- Ningún componente escribe rótulos de resultado propios: los lee del catálogo de rótulos de U1; todos
  los textos salen del catálogo de mensajes, que pasa el escaneo de vocabulario prohibido (BR12.2).
- Los atributos `data-testid` siguen `<componente>-<rol>` (p. ej. `turn-composer-submit-button`).
