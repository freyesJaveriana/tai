# Requisitos de seguridad — U5 human-review

**Insumos.** Flujos F1–F5, la frontera AUTONOMIA-04 y §8 «Errores y bordes» de
`functional-design/functional-spec.md` (functional-spec); reglas BR1–BR5 de `functional-design/rules.md`
(rules) y entidades de `entities.md`; FR1.2, FR6, FR9 y NFR1, NFR10–NFR12 de
`inception/requirements-analysis/requirements.md` (requirements); C1, C10, C11 y C15 de
`inception/contract-design/contract-summary.md` (contract-summary); respuesta P1 = A de
`nfr-requirements-questions.md`; reglas AUTONOMIA-01..05 de `team.md` y prohibiciones de `project.md`.

Cada requisito hereda el ID del NFR de Inception que detalla. Niveles de team-practices: nivel 0
(unitarias, contratos y políticas, cada PR), nivel 1 (integración con PostgreSQL real, cada PR), nivel 3
(E2E) y manual. Los comandos están en `tech-stack-decisions.md` §5. La autenticación, la sesión web, el
anti-CSRF, la autorización por rol y la convención de auditoría vienen de U3; la comprobación de dueño
vive en ConsoleApi (ADR-009). Aquí solo se exige que U5 los use y se fijan sus pruebas.

## 1. Frontera de la unidad (AUTONOMIA-04)

| Componente | Dónde corre | Qué datos cruzan su frontera | Clasificación |
|---|---|---|---|
| ConsoleApi (rutas `decisions` y `cot-views`) | `session-api`, dentro del clúster, bajo la `NetworkPolicy` de salida denegada de U2 | Decisión, nota y reformulación desde el navegador; sugerencia con su estado vigente hacia el navegador (C1), dentro del clúster | Confidencial |
| HumanReview (máquina de estados, rondas, `SuggestionProposer`, `ReviewRounds`) | Módulo de `session-api`, dentro | Llamadas en proceso de U4 (C10) y de U7 (C11); filas en PostgreSQL interno | Confidencial |
| Métricas de C15 | `/metrics` de `session-api`, puerto interno no expuesto al navegador | Solo contadores, valores de enum y `session_id` (UUID) hacia Prometheus de U2 | Interna |
| AnalystConsole (tarjeta de sugerencia) | Navegador, servido por `frontend` | Solo habla con ConsoleApi (ADR-004) | Confidencial |

**Ningún componente de U5 hace una llamada fuera del clúster ni a un modelo.** La nota y la reformulación
del analista se tratan como datos confidenciales aunque en el MVP todos los datos sean sintéticos (NFR12):
pueden mencionar personas o hechos del testimonio.

## 2. Modelo de amenazas (STRIDE)

| # | Amenaza | STRIDE | Riesgo | Mitigación |
|---|---|---|---|---|
| T1 | Otro analista, un `admin` o un `suggestion_id` de otra sesión deciden por el dueño (IDOR) | Elevation of privilege | Alto | NFR10.1 |
| T2 | Petición falsificada desde otro sitio que acepta o descarta una sugerencia | Tampering | Medio | NFR10.2 |
| T3 | Aceptar o editar a ciegas llamando a la API sin desplegar la CoT (AUTONOMIA-03) | Tampering | Alto | NFR10.3 |
| T4 | Una edición reescribe fragmento, cita, documento o CoT de la IA | Tampering | Alto | NFR10.4 |
| T5 | Suplantar al actor enviando `actor_user_id` u hora en el cuerpo | Spoofing | Medio | NFR10.1, NFR11.1 |
| T6 | Nota o reformulación enorme que agota la memoria o la base | Denial of service | Bajo | NFR10.5 |
| T7 | Nota, reformulación o CoT en logs, métricas o respuestas de error | Information disclosure | Alto | NFR10.6, NFR10.7, NFR10.8 |
| T8 | Texto libre o valores inesperados en las etiquetas de las métricas | Information disclosure | Medio | NFR10.8 |
| T9 | Una etiqueta de veracidad en los rótulos de estado o en la tarjeta | Tampering | Alto | NFR10.9 |
| T10 | Borrar o reescribir una decisión o un evento de CoT consultada | Repudiation | Alto | NFR11.1 |
| T11 | Decidir después de consolidar sin abrir una corrección | Tampering | Alto | NFR11.2 |
| T12 | Reabrir una ronda bloqueada o cambiar la versión que la bloqueó | Tampering | Alto | NFR11.3 |
| T13 | La regla AIR cambia el umbral por su cuenta (FR9.1) | Elevation of privilege | Medio | NFR11.4 |

## 3. Requisitos

### NFR1 — Soberanía de datos

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR1.1 | U5 no abre conexiones salvo a PostgreSQL. | El módulo HumanReview no importa clientes HTTP ni de Redis (contrato de import-linter con control negativo); `session-api` queda bajo la `NetworkPolicy` de salida denegada de U2, que es la defensa de fondo. | Nivel 0 (import-linter) y política estática de U2 |

### NFR10 — Seguridad de la aplicación

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR10.1 | Solo el analista dueño decide (BR1.1, ADR-009). | La ruta declara `x-veridicus-roles: [analista]` y `x-veridicus-owner-only: true`; ConsoleApi obtiene el dueño desde la sesión de la sugerencia **en el servidor** (nunca desde el cuerpo) antes de llamar a `ReviewCommands.decide`. Pruebas `403` con 0 filas nuevas en `ReviewDecision` y `CotView`: otro analista (`session.not_owner`, E6), `admin` (`auth.forbidden`, E7), sin sesión (`401`), y `suggestion_id` inexistente o de otra sesión, que recibe el mismo cuerpo que `session.not_owner` (precisión §6). El actor es siempre el principal autenticado: un cuerpo con `actor_user_id`, `at` o `previous_state` responde `422` (`additionalProperties: false` de C1). | Nivel 1 |
| NFR10.2 | Las dos rutas exigen el anti-CSRF de U3. | Sin `X-CSRF-Token` o con uno distinto: `403` `auth.csrf` y 0 filas, en `decisions` y en `cot-views`. | Nivel 1 |
| NFR10.3 | La exigencia de CoT consultada la hace el servidor, no solo la consola (BR2.2, FR6.2). | Una llamada directa a la API para aceptar o editar sin `CotView` del **mismo** actor responde `409` `review.cot_not_viewed` y 0 filas (E1); un `CotView` de otro usuario no cuenta; tras `POST cot-views` del actor, la misma petición responde `201`. Descartar no lo exige (E2). | Nivel 1 |
| NFR10.4 | Editar nunca cambia lo que dijo la IA (BR2.4). | El SHA-256 de (`fragment`, `quote`, `document_id`, `cot`) de la sugerencia es igual antes y después de 3 ediciones seguidas; una petición que trae cualquiera de esos campos responde `422` sin filas (E4). El usuario de la aplicación no tiene `UPDATE` sobre `ReviewSuggestion` (NFR11.1 de U4). | Nivel 1 |
| NFR10.5 | Las entradas de U5 tienen límites (BR2.3, BR2.4). | `state` solo `accepted`, `edited` o `dismissed`; `note` y `reformulation` de hasta **2 000 caracteres** cada una (`422` `validation.invalid_request` si pasan); el servidor deja de leer un cuerpo JSON de más de 64 KiB y responde `422` sin filas. «En blanco» es vacío tras `str.strip()` de Python (incluye espacios Unicode como U+00A0 y U+3000): nota en blanco al descartar → `422` `review.note_required` (E3); reformulación en blanco → `422` `validation.invalid_request`; `reformulation` presente con un estado distinto de `edited` → `422`. Prueba de propiedad (Hypothesis) con cadenas de solo espacios Unicode y prueba de límites (2 000 y 2 001 caracteres). | Nivel 0 y nivel 1 |
| NFR10.6 | Los logs de U5 solo llevan identificadores. | Campos permitidos: `session_id`, `suggestion_id`, `round_id`, `decision_id`, `user_id`, `state`, `previous_state`, `code`, duraciones y conteos. Prueba de nivel 1: con una cadena centinela sembrada en la nota, en la reformulación y en la CoT de la sugerencia, 0 coincidencias en los logs capturados de `session-api` en los caminos `201`, `403`, `409`, `422` y en una violación de restricción de la base (el *engine* usa `hide_parameters=True`, D5). | Nivel 1 |
| NFR10.7 | Los errores no devuelven el texto del analista. | Cada rechazo sale como Problem Details con un `code` de C1 y el `detail` en español del catálogo de U1; con la cadena centinela de NFR10.6, 0 coincidencias en los cuerpos de error. | Nivel 1 |
| NFR10.8 | Las métricas de U5 no llevan texto (C15). | `state` solo toma valores del enum de C10, `code` solo valores del catálogo de C1 y `session_id` solo un UUID; prueba de nivel 0 que recorre las series registradas y valida cada etiqueta contra su patrón, y prueba de nivel 1 con la cadena centinela: 0 coincidencias en la salida de `/metrics`. | Nivel 0 y nivel 1 |
| NFR10.9 | Los rótulos de U5 no son etiquetas de veracidad (AUTONOMIA-03). | Los rótulos de estado («Pendiente», «Aceptada», «Editada», «Descartada», «Aceptada · con nota») y el recordatorio de BR5.2 salen del catálogo de U1 y pasan el escáner `scan(text, literal_sources)` de U4 con 0 coincidencias en nivel 0. La nota y la reformulación son texto del analista: no se censuran ni se bloquean, y el escaneo de la interfaz en nivel 3 las pasa como `literal_sources` (una prueba siembra una nota con un término de C8 y comprueba que no se marca, y otra lo siembra en un rótulo y comprueba que sí). | Nivel 0 y nivel 3 |

### NFR11 — Integridad y auditoría

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR11.1 | `ReviewDecision` y `CotView` solo admiten inserciones (BR2.6). | Ambas tablas registradas en `AuditConvention` de U3; el usuario de la aplicación tiene solo `INSERT` y `SELECT`; `UPDATE`, `DELETE` y `TRUNCATE` fallan por permisos (E13); `actor_user_id`/`user_id` y `at`/`viewed_at` no nulos; la hora la pone el servidor. Restricciones `CHECK` como segunda barrera: `state <> 'dismissed' OR length(btrim(note)) > 0` y `state <> 'edited' OR length(btrim(reformulation)) > 0`. | Nivel 1 (prueba común de U3 y prueba de cada `CHECK`) |
| NFR11.2 | Nada entra en una ronda bloqueada (BR3.1, BR3.5). | Decidir sin ronda `open` → `409` `review.round_locked` y 0 filas (E8); `propose` con todas las rondas `locked` → rechazo `review.round_locked` y 0 sugerencias (E12); ninguna `ReviewDecision` tiene `at` posterior al `locked_at` de su ronda (consulta de verificación en la prueba de concurrencia de NFR10.12). | Nivel 1 |
| NFR11.3 | Una ronda bloqueada es definitiva. | El usuario de la aplicación solo tiene `UPDATE` sobre las columnas `status`, `locked_by_report_version_id` y `locked_at` de `ReviewRound`, y no tiene `DELETE`; un *trigger* rechaza cualquier `UPDATE` de una fila con `status = 'locked'`; un índice único parcial impide dos rondas `open` en la misma sesión. Pruebas: volver a `open`, cambiar `locked_by_report_version_id` y abrir una segunda ronda fallan. | Nivel 1 |
| NFR11.4 | La regla AIR solo propone (FR9.1, FR9.3). | U5 solo publica métricas; ningún código de U5 escribe el umbral (la regla estática de U3, NFR11.2 de U3, cubre también el módulo HumanReview). | Nivel 0 |

### NFR12 — Datos sintéticos

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR12.1 | Los *fixtures* de U5 son sintéticos. | Notas, reformulaciones y usuarios de prueba usan el catálogo de nombres y las marcas sintéticas de U1; la comprobación de U1 sobre `services/session-api/tests/human_review/` da 0 hallazgos. | Nivel 0 |

## 4. Trazabilidad de AUTONOMIA

| Regla | Requisitos de U5 |
|---|---|
| AUTONOMIA-01 | U5 no aplica nada al clúster; las tablas y permisos entran por la migración de su PR (`Job` aparte) y la regla AIR la escribe U2 por PR (NFR11.4) |
| AUTONOMIA-02 | Cada requisito tiene su criterio y su comando (`tech-stack-decisions.md` §5) |
| AUTONOMIA-03 | NFR10.3, NFR10.4, NFR10.9, NFR11.1–NFR11.3; máquina de estados y herencia con 100 % de ramas (NFR13.2) |
| AUTONOMIA-04 | §1, NFR1.1, NFR10.6–NFR10.8 |
| AUTONOMIA-05 | No aplica directamente: U5 solo recibe sugerencias que ya pasaron la guardia de U4; `propose` rechaza candidatas sin los 4 campos (C10) |

## 5. Riesgos aceptados

- **`cot-views` registra el despliegue, no la lectura.** Un cliente puede llamar `POST cot-views` sin
  mostrar la CoT. FR6.2 pide que la CoT haya sido desplegada; el servidor no puede comprobar la lectura.
  El evento queda a nombre del actor y con su hora (NFR11.1).
- **La nota es texto libre.** Puede contener nombres; en el MVP los datos son sintéticos (NFR12), la nota
  no sale del clúster y nunca va a logs ni métricas (NFR10.6–NFR10.8).

## 6. Precisiones a artefactos ya aprobados

Estas decisiones precisan artefactos ya aprobados. No los edité; decides en la aprobación si se
actualizan.

| Artefacto | Qué precisa | Origen |
|---|---|---|
| `contract-design/contract-summary.md` (C1, `POST /suggestions/{id}/decisions`) | Las respuestas documentadas añaden `403` (`auth.forbidden`, `session.not_owner`, `auth.csrf`) y `422` (`review.note_required`, `validation.invalid_request`); hoy solo listan `201` y `409`, y `rules.md` ya usa `422` (cambio menor de documentación) | BR1.1, BR2.3, BR2.4 |
| `contract-design/contract-summary.md` (C1, cuerpo de la decisión) | `note` y `reformulation` llevan `maxLength: 2000` (cambio menor; aún no hay consumidores) | NFR10.5 |
| `contract-design/contract-summary.md` (C1, reparto de rutas) | `/suggestions/*/cot-views` figura como ruta de U4; su comportamiento (`CotView`, `record_cot_view` de C10) es de U5. La ruta la registra U5 junto a `decisions` | F1, BR1.3 |
| `contract-design/contract-summary.md` (C1) | Un `suggestion_id` inexistente o de otra sesión responde igual que `session.not_owner` (`403`), porque C1 no tiene un `code` de «no encontrado»; no se añade ninguno | NFR10.1 |
| `contract-design/contract-summary.md` (C11) | `open_round(uow, session_id, *, for_update: bool = False)`: con `True` toma `SELECT … FOR UPDATE` sobre la ronda; U7 la llama así al empezar la consolidación, para que una decisión simultánea entre antes del reporte o reciba `review.round_locked` (cambio menor) | NFR10.12 |
| `contract-design/contract-summary.md` (C15) | *W* = 8 (P1 = A) y definición exacta de la ventana de `veridicus_session_dismissal_ratio` (`observability-requirements.md` §2); la serie se retira al bloquear la ronda; se añade `veridicus_review_rejections_total{code}`. Entra por un PR de U1, como las métricas de U3 y U4 | P1 = A; NFR15.1, NFR15.2 |
| Functional Design de U7 | La consolidación llama `open_round(..., for_update=True)` antes de leer `pending_count` y `decisions` | NFR10.12 |
