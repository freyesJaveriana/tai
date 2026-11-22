# Preguntas de Functional Design — U5 human-review

**Unidad.** U5 `human-review` (tipo `service`): aceptar con CoT consultada (US5.1), editar con
reformulación propia (US5.2), descartar con nota (US5.3), solo el dueño decide (US5.4); rondas y
decisiones de solo inserción (ADR-007).

**Lo que ya está decidido y no se vuelve a preguntar.** Toda sugerencia nace pendiente; nunca vuelve a
pendiente; dentro de una ronda abierta se cambia entre aceptada, editada y descartada con las mismas
exigencias; descartar exige nota; editar nunca toca fragmento, cita, documento ni CoT; una ronda
bloqueada no admite cambios; la autorización por dueño la aplica ConsoleApi (components, ADR-007,
ADR-009, AC5.1.1–AC5.4.3). La copia de trabajo de una corrección parte de las decisiones vigentes
(interaction-spec F4). Queda un solo hueco.

---

## P1 — Validez del evento «CoT consultada» en una ronda de corrección

Aceptar o editar exige que el mismo usuario haya desplegado la CoT de esa alerta (AC5.1.2). Cuando U7
abre una ronda de corrección del reporte, el analista vuelve a decidir sobre alertas que ya revisó.

A. El evento vale por usuario y alerta para siempre: si ya desplegó la CoT en la ronda 1, puede aceptar
   o editar en la corrección sin volver a desplegarla. (Recomendada)
B. El evento vale solo dentro de la ronda: en cada ronda de corrección hay que volver a desplegar la CoT
   antes de aceptar o editar.
X. Other (please specify)

[Answer]: A **Mode:** guided

---

# Segunda pasada — cambio 01, adenda 02 y revisiones 3 (2026-11-22)

**Alcance.** El cambio 01 convierte la alerta en un hallazgo de contradicción con dos citas (C6, C7 v2)
y la CoT en «observaciones»; para U5 es un cambio menor (`docs/iteracion2.md`, tabla de unidades:
«campos protegidos, observaciones»). La adenda 02 y las revisiones 3 suman la retención (C24, A-2), el
registro de acceso (C23) y la matriz de lectura de U3. La máquina de estados y las rondas siguen.

## Lo que ya está decidido y no se vuelve a preguntar

- **Máquina de estados y exigencias:** nace `pending`, nunca vuelve a `pending`; dentro de una ronda
  abierta se cambia entre `accepted`, `edited` y `dismissed` con las mismas exigencias; descartar exige
  nota; aceptar o editar admiten nota opcional; aceptar o editar exigen las observaciones desplegadas
  por el mismo usuario; cada cambio es una fila nueva con actor, hora, estado anterior y nuevo (FR6.1–FR6.3,
  AC5.1.1–AC5.3.2, ADR-003, ADR-007).
- **Campos protegidos:** editar es la reformulación propia del analista y nunca cambia `hecho`, `tipo`,
  `cita_a`, `cita_b` ni `observaciones` (FR6.1, AC5.2.2, C1 con `additionalProperties: false`).
- **Solo el dueño decide**, verificado en ConsoleApi (FR1.2, AC5.4.1–AC5.4.3, ADR-009); `analista` y
  `admin` leen, `investigador` recibe `403` y no hay rol para la persona entrevistada (U3, P4 = A,
  FD-U3-01).
- **Contratos:** rutas `/suggestions/*/observation-views` y `/suggestions/*/decisions` con sus códigos
  `review.*` (C1); sugerencia C7 v2 con `pair_key` interno; `SuggestionProposer` y `ReviewCommands`
  (C10); `ReviewRounds` con `for_update` (C11); métricas C15 v2; `Purgeable` (C24); `AccessLog` (C23).
- **Lo que ya resolvió U4 (text-flow, revisión 2):** U4 crea las tablas `ReviewSuggestion` y
  `ReviewRound` y la implementación de `propose`, con la unión por `pair_key` y la ronda 1 (BR8.6, BR11.2,
  F8); si `propose` rechaza, la corrida queda en `analysis.system` con XACK (BR16.8, FD-U4-06); en una
  sesión bloqueada por un incidente de anonimización las decisiones de U5 siguen (F11, E36).
- **Lo que ya resolvió U3:** orden de bloqueo usuario → sesión → ronda (FD-U3-13, `project.md`), marca de
  auditoría por tabla (FD-U3-07), usuarios `veridicus_app` y `veridicus_retention` (FD-U3-09), registro de
  acceso de la apertura de observaciones (FD-U3-05).
- **Primera pasada:** el evento de despliegue vale por usuario y sugerencia en todas las rondas (P1 = A);
  la herencia entre rondas es el «estado vigente»; la copia de trabajo de una corrección parte de las
  decisiones vigentes (interaction-spec F4).
- **Después de consolidar**, la sesión y sus hallazgos quedan bloqueados y solo una corrección los abre
  (FR7.5); el reporte incluye todas las sugerencias con su estado final y nota (P16 de `docs/iteracion2.md`).

## Cómo se registra la revisión 2

- `entities.md`, `rules.md` y `functional-spec.md` llevan el encabezado «Revisión 2 — cambio 01, adenda
  02 y revisiones 3 (2026-11-22)», que reemplaza la versión aprobada el 2026-10-02.
- Se conservan los ID (BR1.1–BR5.5, F1–F5, E1–E13). Lo que cambia lleva `status: cambia`; lo que sale se
  marca «Retirado» sin renumerar; lo nuevo toma el número siguiente de su grupo (p. ej. BR3.7, un grupo
  BR6 de retención, F6, E14 en adelante).
- `CotView` pasa a «Retirado» y la sustituye `ObservationsView` (nombre de components); el código
  `review.cot_not_viewed` pasa a `review.observations_not_viewed` (C1, C10).
- La tabla §9 de precisiones conserva sus tres filas de la revisión 1 (marcadas «Hecho» o «Superado») y
  suma las nuevas con ID `FD-U5-NN`. No se edita ningún artefacto aprobado.
- Los hallazgos R-01 a R-05 de la revisión 1 se cierran en esta revisión, cada uno citado donde se
  resuelve (lista de abajo).
- `traceability.json` cubre US5.1–US5.4 y las historias compartidas US5.5, US5.6, US8.4 y US15.7.

## Lo que el diseño resolverá sin preguntar

1. **CoT → observaciones** en entidades, reglas, textos y escenarios: «Despliega y lee las
   observaciones para habilitar esta acción», evento «Observaciones consultadas» (AC5.1.1, AC5.1.2,
   mockups §6.6).
2. **SHA-256 de protección** sobre (`hecho`, `tipo`, `cita_a`, `cita_b`, `observaciones`) antes y después
   de editar (AC5.2.2); como `ReviewSuggestion` es una tabla `history`, la prueba además intenta un
   `UPDATE` y falla.
3. **Reparto con U4:** U5 no reescribe `propose`; suma a `ReviewRound` las columnas que solo usa la
   revisión (`kind`, `opened_by`, `based_on_round_id`, `locked_at`) y es dueño de `ReviewDecision` y
   `ObservationsView`. BR3.5 pasa a citar la implementación de U4.
4. **Sin referencia a ReviewReport** (R-01 de Domain Design, C11): salen («Retirado»)
   `based_on_report_version_id` y `locked_by_report_version_id`; `lock_round` recibe el
   `report_version_id` pero no lo guarda como clave foránea, y la relación ronda ↔ versión la guarda U7.
5. **Consolidar sin ronda** (R-04 de la revisión 1): con un relato coherente hay 0 hallazgos y no existe la
   ronda 1. Propuesta: `open_round(..., for_update=True)` abre la ronda 1 si la sesión no tiene ninguna,
   para que U7 siempre bloquee una ronda; precisión a C11 en §9.
6. **Concurrencia y orden** (R-02 de la revisión 1): orden usuario → sesión → ronda y columna `change_seq`
   en `ReviewDecision` y `ReviewRound`, que también desempata BR3.2 (NFR Design de U5, P1 = A).
7. **Texto tras `edited` → `accepted` o `dismissed`** (R-03 de la revisión 1): manda la decisión vigente;
   `accepted` consolida el hallazgo de la IA sin reformulación y la reformulación anterior queda en el
   historial; `decisions` (C11) devuelve el estado vigente con su propia nota y reformulación.
8. **Sugerencia inexistente** (R-05 de la revisión 1): `404` `suggestion.not_found` (precisión a C1) y el
   resolvedor del dueño sugerencia → sesión para el mecanismo F2 de U3; la etiqueta `session_id` de la
   razón de descartes queda acotada como dice NFR8.6.
9. **Despliegue de observaciones:** lo pueden registrar `analista` y `admin` (C1); `ObservationsView`
   guarda solo el primero por usuario y sugerencia, y la ruta declara
   `x-veridicus-access-log: suggestion`, que registra cada apertura (FD-U3-05).
10. **Retención:** HumanReview implementa `Purgeable.purge_session` y borra, con `veridicus_retention`,
    `ObservationsView`, `ReviewDecision`, `ReviewSuggestion` y `ReviewRound`, en ese orden, devolviendo
    solo IDs (C24, A-2, US15.7). Marcas de tabla `history`, `purgeable`, `owner_unit: U5` (FD-U3-07).
11. **Métricas C15 v2:** solo `veridicus_review_decisions_total` y `veridicus_session_dismissal_ratio`,
    con *W* de C25 (`dismissal_window_w`); el umbral 0.25 vive en la regla de U2; las emite U5 (CD-07).
    Sale la propuesta de umbral AIR.
12. **Longitudes:** nota y reformulación limitadas por `review_text_max_chars` de C25 (NFR Design de U5);
    por encima, `422` `limits.exceeded`.
13. **Vocabulario:** la nota y la reformulación son texto del analista y no se rechazan por el escáner
    (FR6.4, AC5.5.2 (d)); el reporte las muestra como suyas (U7).
14. **Consola:** estados, textos y editor de mockups §6.6; botones deshabilitados con `aria-disabled` y
    motivo por `aria-describedby` (AC5.6.4); la tarjeta y sus formularios entran en la suite `axe` de U4.

## P2 — Qué se puede cambiar en una ronda de corrección

FR7.5 y el banner de la copia de trabajo (mockups §7) dicen «solo cambian estados y notas», y la salida de
la IA queda en solo lectura. No dicen si la **reformulación** del analista se puede escribir o cambiar en
una corrección; pasar a `edited` exige una reformulación (FR6.1), así que la lectura literal impediría
editar durante la corrección.

A. En la corrección valen las mismas reglas que en la ronda inicial: estados, notas y reformulaciones,
   porque la reformulación es texto del analista y no salida de la IA. Se propone a FR7.5 y al banner
   «Solo puedes cambiar estados, notas y reformulaciones». (Recomendada)
B. Lectura literal: en la corrección solo se cambian estados y notas; no se puede pasar a `edited` ni
   cambiar una reformulación existente (`409` con un código nuevo); una sugerencia `edited` puede pasar a
   `accepted` o `dismissed`.
C. Lectura literal más estricta: una sugerencia `edited` queda fija en la corrección y solo cambian las
   demás entre `accepted` y `dismissed`, con sus notas.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P3 — Decidir en una sesión terminada o con el consentimiento retirado

VE-10 (DD-06) dice que tras pausar, terminar o retirar el consentimiento no se analiza nada nuevo; no
dice nada de los hallazgos que ya existen, que vienen de turnos anteriores a la retirada. U4 ya decidió
que en una sesión bloqueada por un incidente las decisiones siguen (F11). HumanReview no conoce el
estado de la sesión (solo depende de IntegrityPolicy), así que una restricción iría en la ruta de U5 de
ConsoleApi. Si la sesión se puede consolidar en esos estados lo deciden U6 y U7.

A. Las decisiones siguen en las sesiones pausadas, suspendidas, terminadas y con el consentimiento
   retirado, igual que en las bloqueadas: solo se detiene el análisis nuevo, y los hallazgos existentes
   vienen de turnos con consentimiento. (Recomendada)
B. Siguen en las pausadas, suspendidas y terminadas, pero tras la retirada del consentimiento quedan
   congeladas: `409` `session.consent_withdrawn` y las pendientes siguen pendientes (U7 tendría que
   decidir cómo se consolida esa sesión).
C. Quedan congeladas tanto en las terminadas como tras la retirada del consentimiento, con `409`
   `session.terminated` o `session.consent_withdrawn`.
X. Other (please specify)

[Answer]: A **Mode:** guided
