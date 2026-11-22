# Requisitos de seguridad — U5 human-review

**Revisión 2 (2026-11-22).** Es la segunda pasada por el cambio 01 (DT27), la adenda 02 y el Functional
Design revisión 2 de U5. Sustituye a la revisión 1 del 2026-10-03, que queda en el historial de Git.
- **IDs.** Los requisitos conservan su ID; cada fila dice si **se mantiene**, **cambia**, es **nuevo** o
  queda **Retirado**. Los nuevos son NFR10.19–NFR10.22, NFR11.5 y NFR11.6.
- **Qué cambia.** La CoT pasa a ser observaciones. Los campos protegidos son los 5 de C7 v2. La
  longitud responde `413` `limits.exceeded` con cifras de C25. Entran el `404` `suggestion.not_found`,
  la matriz de roles con AC5.4.4, el estado `discarded` y el borrado por retención (C24).
- **Sin preguntas** en esta pasada (ver `nfr-requirements-questions.md`). Lo que precisa artefactos
  aprobados está en §7.

**Insumos.**
- Flujos F1–F7 y escenarios E1–E33 de `functional-design/functional-spec.md` (functional-spec, revisión 2).
- Reglas BR1.1–BR6.3 de `functional-design/rules.md` (rules, revisión 2) y entidades de `entities.md`, con
  la tabla FD-U5-01 a FD-U5-10.
- FR1.2, FR6, FR7.5, FR9, NFR1, NFR10, NFR11 y NFR12 de `inception/requirements-analysis/requirements.md`
  (requirements, revisión 3). De `requirements-adenda-02.md`: VE-09, VE-10 y A-2. AC5.4.4 de
  `stories-adenda-02.md`.
- C1, C7 v2, C10, C11, C15 v2, C23, C24 y C25 de `inception/contract-design/contract-summary.md`
  (contract-summary, revisión 3).
- NFR de U1 revisión 2: NFR10.3 (`413`), NFR10.7 (`x-veridicus-limit`), NFR-U1-03 y NFR-U1-07.
- NFR de U3 revisión 2: matriz de roles, Problem Details, registro de acceso en un punto de guardado y
  usuarios de base de datos.
- Respuesta P1 = A de `nfr-requirements-questions.md` y reglas AUTONOMIA-01..05 de `team.md`.

Cada requisito hereda el ID del NFR de Inception que detalla. Niveles de `team.md`:
- nivel 0: unitarias, contratos y políticas, en cada PR;
- nivel 1: integración con PostgreSQL real, en cada PR;
- nivel 3: E2E.

Los comandos están en `tech-stack-decisions.md` §5. La autenticación, la sesión web, el anti-CSRF, la
autorización por rol, el registro de acceso y la convención de auditoría vienen de U3. La comprobación de
dueño vive en ConsoleApi (ADR-009). Aquí solo se exige que U5 los use y se fijan sus pruebas.

## 1. Frontera de la unidad (AUTONOMIA-04)

| Componente | Dónde corre | Qué datos cruzan su frontera | Clasificación |
|---|---|---|---|
| ConsoleApi (rutas `observation-views` y `decisions`) | `session-api`, dentro del clúster, bajo la `NetworkPolicy` de U2 que niega la salida | Desde el navegador: decisión, nota y reformulación. Hacia el navegador: la sugerencia con su estado vigente (C1). Al puerto `AccessLog` (C23): solo IDs | Confidencial |
| HumanReview (máquina de estados, rondas, `purge_session`) | Módulo de `session-api`, dentro del clúster | Llamadas en proceso de ConsoleApi (C10), U7 (C11) y U13 (C24); filas en el PostgreSQL interno | Confidencial |
| Métricas de C15 v2 | `/metrics` de `session-api`, en un puerto interno sin Ingress | Hacia el Prometheus de U2: contadores, valores de enum y `session_id` (UUID) | Interna |
| AnalystConsole (tarjeta de la sugerencia) | Navegador, servido por `frontend` | Solo habla con ConsoleApi (ADR-004) | Confidencial |

**Ningún componente de U5 hace una llamada fuera del clúster ni a un modelo.** La nota y la reformulación
del analista se tratan como confidenciales aunque en el MVP todos los datos sean sintéticos (NFR12),
porque pueden nombrar personas o hechos del testimonio.

## 2. Modelo de amenazas (STRIDE)

| # | Amenaza | STRIDE | Riesgo | Mitigación |
|---|---|---|---|---|
| T1 | Otro analista, un `admin`, el `investigador` o un `suggestion_id` de otra sesión deciden por el dueño (IDOR) | Elevation of privilege | Alto | NFR10.1, NFR10.19 |
| T2 | Una petición falsificada desde otro sitio acepta o descarta una sugerencia | Tampering | Medio | NFR10.2 |
| T3 | Aceptar o editar a ciegas, llamando a la API sin desplegar las observaciones (AUTONOMIA-03) | Tampering | Alto | NFR10.3 |
| T4 | Una edición reescribe el hecho, el tipo, las citas o las observaciones de la IA | Tampering | Alto | NFR10.4 |
| T5 | Suplantar al actor enviando `actor_user_id` u hora en el cuerpo | Spoofing | Medio | NFR10.1, NFR11.1 |
| T6 | Una nota, una reformulación o un cuerpo enormes agotan la memoria o la base | Denial of service | Bajo | NFR10.5 |
| T7 | La nota, la reformulación o las observaciones aparecen en logs, métricas o errores | Information disclosure | Alto | NFR10.6, NFR10.7, NFR10.8 |
| T8 | Texto libre o valores inesperados en las etiquetas de las métricas | Information disclosure | Medio | NFR10.8 |
| T9 | Una etiqueta de veracidad en los rótulos de estado o en la tarjeta | Tampering | Alto | NFR10.9 |
| T10 | Borrar o reescribir una decisión o un evento de observaciones con el usuario de la aplicación | Repudiation | Alto | NFR11.1, NFR11.5 |
| T11 | Decidir después de consolidar sin abrir una corrección | Tampering | Alto | NFR11.2 |
| T12 | Reabrir una ronda bloqueada o descartada | Tampering | Alto | NFR11.3, NFR11.6 |
| T13 | La regla AIR cambia el umbral por su cuenta (FR9.1) | Elevation of privilege | Medio | NFR11.4 |
| T14 | Una respuesta distingue «no existe» de «no es tuya» para enumerar sugerencias de otras sesiones | Information disclosure | Bajo | NFR10.20 |
| T15 | El `investigador` lee observaciones, o existe una vía para la persona entrevistada (VE-09) | Information disclosure | Alto | NFR10.19 |
| T16 | El borrado por retención deja filas de la sesión o borra las de otra | Tampering | Medio | NFR10.22, NFR11.5 |

## 3. Requisitos

### NFR1 — Soberanía de datos

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR1.1 | se mantiene | U5 no abre conexiones salvo a PostgreSQL. | El módulo HumanReview no importa clientes HTTP ni de Redis: lo prueba un contrato de import-linter con control negativo. `session-api` queda bajo la `NetworkPolicy` de U2 que niega la salida, que es la defensa de fondo. | Nivel 0 (import-linter) y política estática de U2 |

### NFR10 — Seguridad de la aplicación

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR10.1 | cambia | Solo el analista dueño decide (BR1.1, ADR-009). | La ruta declara `x-veridicus-roles: [analista]` y `x-veridicus-owner-only: true`. ConsoleApi obtiene el dueño de la sesión de la sugerencia **en el servidor**, con el resolvedor de HumanReview (nunca del cuerpo), antes de llamar a `ReviewCommands.decide`. Pruebas `403` con 0 filas nuevas en `ReviewDecision` y `ObservationsView`: otro analista (`session.not_owner`, E6), `admin` (`auth.forbidden`, E7) e `investigador` (`auth.forbidden`); sin sesión web, `401`. Vale también dentro de una ronda de corrección. El actor es siempre el principal autenticado: un cuerpo con `actor_user_id`, `at` o `previous_state` responde `422` `validation.invalid_request` (`additionalProperties: false` de C1). | Nivel 1 |
| NFR10.2 | se mantiene | Las dos rutas exigen el anti-CSRF de U3. | Sin `X-CSRF-Token`, o con uno distinto: `403` `auth.csrf` y 0 filas, en `decisions` y en `observation-views`. | Nivel 1 |
| NFR10.3 | cambia | La exigencia de observaciones desplegadas la hace el servidor, no solo la consola (BR2.2, FR6.2). | Aceptar o editar llamando directamente a la API sin un `ObservationsView` del **mismo** actor responde `409` `review.observations_not_viewed` y 0 filas (E1). El `ObservationsView` de otro usuario (también de un `admin`) no cuenta. Tras el `POST observation-views` del actor, la misma petición responde `201`. Descartar no lo exige (E2), y un evento de la ronda 1 vale en las correcciones (E10). | Nivel 1 |
| NFR10.4 | cambia | Editar nunca cambia lo que dijo la IA (BR2.4). | El SHA-256 de (`hecho`, `tipo`, `cita_a`, `cita_b`, `observaciones`) de la sugerencia es igual antes y después de 3 ediciones seguidas. Una petición que trae cualquiera de esos campos responde `422` `validation.invalid_request` sin filas (E4). Un `UPDATE` de `veridicus_app` sobre `ReviewSuggestion` falla por permisos. | Nivel 1 |
| NFR10.5 | cambia | Las entradas de U5 tienen límites, y las cifras salen de C25 (BR2.3, BR2.4, BR2.7). | **Longitud:** `note` y `reformulation` admiten hasta `review_text_max_chars` = 2 000 caracteres cada una, contados en puntos de código. Con más, responde `413` `limits.exceeded` sin filas (E21, NFR-U5-02). **Cuerpo:** el servidor deja de leer el cuerpo JSON al pasar de `review_body_max_bytes` = 65 536 bytes y responde `413` `limits.exceeded` sin filas. Ese tope cabe con holgura en el peor caso válido: las dos cadenas de 2 000 caracteres escapadas como `\uXXXX\uXXXX` suman 48 000 bytes más los campos. Una variable de entorno solo puede bajar estas cifras (NFR-U5-01). **Estado:** solo `accepted`, `edited` o `dismissed`; `pending` responde `422` `validation.invalid_request` (E5). **En blanco:** se mide con `str.strip()` de Python, que incluye U+00A0 y U+3000. Nota en blanco al descartar → `422` `review.note_required` (E3). Reformulación en blanco con `edited`, o `reformulation` con otro estado → `422` `validation.invalid_request` (E23). **Orden de los controles:** autorización, luego tope del cuerpo, luego esquema. Un rol sin permiso recibe `403` aunque el cuerpo sea grande o inválido. **Pruebas:** propiedad (Hypothesis) con cadenas de solo espacios Unicode; límites con 2 000 y 2 001 caracteres, también con caracteres de 4 bytes; cuerpo de 65 536 y 65 537 bytes. | Nivel 0 y nivel 1 |
| NFR10.6 | cambia | Los logs de U5 solo llevan identificadores. | Campos permitidos: `session_id`, `suggestion_id`, `round_id`, `decision_id`, `user_id`, `state`, `previous_state`, `code`, `kind`, duraciones y conteos. Se siembra una cadena centinela en la nota, en la reformulación y en las observaciones de la sugerencia. Resultado esperado: 0 coincidencias en los logs capturados de `session-api`. Caminos probados: `201`, `204`, `403`, `404`, `409`, `413`, `422`, una violación de restricción de la base y `purge_session`. El *engine* usa `hide_parameters=True` (D5). | Nivel 1 |
| NFR10.7 | cambia | Los errores no devuelven el texto del analista. | Cada rechazo sale por el manejador único de U3 como Problem Details, con un `code` de C1 y el estado que fija el catálogo de U1 (un estado por `code`). El `detail` es el texto en español del catálogo. Con la cadena centinela de NFR10.6: 0 coincidencias en los cuerpos de error. | Nivel 1 |
| NFR10.8 | cambia | Las métricas de U5 no llevan texto (C15 v2). | Solo dos métricas: `veridicus_review_decisions_total{state}` y `veridicus_session_dismissal_ratio{session_id}`. `state` toma solo `accepted`, `edited` o `dismissed`, y `session_id` solo un UUID. Ninguna otra etiqueta: las permitidas son las de NFR15.1 de U1. Una prueba de nivel 0 recorre las series registradas y valida cada etiqueta contra su patrón. Una prueba de nivel 1 con la cadena centinela da 0 coincidencias en `/metrics`. | Nivel 0 y nivel 1 |
| NFR10.9 | cambia | Los rótulos de U5 no son etiquetas de veracidad (AUTONOMIA-03; BR2.8, BR5.8). | Las cadenas de U5 vienen del catálogo de mensajes de la consola y pasan el escáner `scan(text, literal_sources)` con 0 coincidencias en nivel 0. Son los rótulos de estado («Pendiente», «Aceptada», «Aceptada · con nota», «Editada», «Descartada»), el recordatorio de BR5.2 y los mensajes de FD-U5-10. Un control siembra un término en un rótulo y la prueba falla. La nota y la reformulación son texto del analista: no se censuran, se guardan tal cual (E22) y el escaneo de la interfaz en nivel 3 las pasa como `literal_sources`. | Nivel 0 y nivel 3 |
| NFR10.19 | nuevo | La matriz de roles de FR1.2 vale en las rutas de U5, y no hay vía para la persona entrevistada (AC5.4.2, AC5.4.4 con la precisión NFR-U5-03, VE-09). | `observation-views` declara `x-veridicus-roles: [analista, admin]`. Responde `204` al dueño, a otro analista y al `admin` (E16), y `403` `auth.forbidden` al `investigador`, sin filas ni registro de acceso (E15). `decisions` es solo del dueño (NFR10.1). El enum `Role` tiene exactamente tres valores y ninguna ruta de U5 es pública. Una prueba de nivel 0 recorre el OpenAPI y comprueba los roles de las dos rutas celda por celda. | Nivel 0 y nivel 1 |
| NFR10.20 | nuevo | Una sugerencia inexistente responde siempre igual (BR1.4, FD-U5-01). | En las dos rutas, un UUID inexistente responde `404` `suggestion.not_found`, con 0 filas y sin entrada de acceso (E14). El `404` solo se da tras pasar la sesión web, el CSRF y el rol. Un `suggestion_id` que existe pero es de otra sesión responde `403` `session.not_owner` en `decisions` y `204` en `observation-views` a quien puede leer todas las sesiones (FR1.2). ConsoleApi no arranca si falta el resolvedor de HumanReview (control de nivel 0). | Nivel 0 y nivel 1 |
| NFR10.21 | nuevo | Cada apertura de observaciones queda en el registro de acceso (BR1.3, C23). | Tras el `204`, ConsoleApi registra `resource_type: suggestion` con `x-veridicus-access-log`, en el punto de guardado de 500 ms de U3. El dueño que despliega dos veces deja 1 `ObservationsView` y 2 entradas (E17). Si el puerto falla o vence, la respuesta sigue siendo `204` con su fila intacta, y queda un log de aviso con solo IDs (riesgo aceptado de U3). El rechazo `403` o `404` no deja entrada. | Nivel 1 |
| NFR10.22 | nuevo | `purge_session` solo borra la sesión pedida y no devuelve texto (BR6.1, C24). | Con `veridicus_retention` y en la transacción del `Job`, se borra en este orden: `ObservationsView` → `ReviewDecision` → `ReviewSuggestion` → `ReviewRound`. Después quedan 0 filas de la sesión y las filas de otras dos sesiones siguen intactas, contadas antes y después (E28). El `PurgeReceipt` solo lleva UUID y conteos: un validador estricto de su esquema lo comprueba, y la cadena centinela da 0 coincidencias. Purgar dos veces devuelve listas vacías sin error (E32). | Nivel 1 |

NFR10.10–NFR10.18 están en `reliability-requirements.md`.

### NFR11 — Integridad y auditoría

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR11.1 | cambia | `ReviewDecision`, `ObservationsView` y `ReviewSuggestion` solo admiten inserciones para la aplicación (BR2.6, BR6.3). | Las tres tablas llevan la marca `veridicus-audit` (`kind: history`, `purgeable: true`, `owner_unit: U5`). La prueba común de U3 las descubre por esa marca. `veridicus_app` tiene solo `INSERT` y `SELECT`; `UPDATE`, `DELETE` y `TRUNCATE` fallan por permisos (E13, E29). Actor y hora no son nulos (E30) y la hora la pone el servidor. Restricciones `CHECK` como segunda barrera: `state <> 'dismissed' OR length(btrim(note)) > 0` y `state <> 'edited' OR length(btrim(reformulation)) > 0`. | Nivel 1 (prueba común de U3 y prueba de cada `CHECK`) |
| NFR11.2 | cambia | Nada entra en una ronda que no está abierta (BR3.1, BR3.5). | Decidir sin ronda `open` responde `409` `review.round_locked` con 0 filas (E8). Con todas las rondas `locked` o `discarded`, `propose` rechaza con `review.round_locked` y 0 sugerencias (E12); la prueba es de U4 contra C10, y U5 suma el caso con una ronda `discarded`. Ninguna `ReviewDecision` tiene un `change_seq` mayor que el de su ronda al bloquearse; lo comprueba la consulta de la prueba de concurrencia de NFR10.12. | Nivel 1 |
| NFR11.3 | cambia | Una ronda cerrada es definitiva (BR3.4, BR3.9). | `veridicus_app` solo tiene `UPDATE` sobre `status`, `locked_at`, `discarded_by`, `discarded_at` y `change_seq` de `ReviewRound`, y no tiene `DELETE`. El disparador solo admite `open` → `locked` (cualquier `kind`) y `open` → `discarded` (solo `kind: correction`). Rechaza todo `UPDATE` de una fila `locked` o `discarded`. Un índice único parcial impide dos rondas `open` en la misma sesión. Pruebas: volver a `open` desde `locked` y desde `discarded`, descartar la ronda `initial`, cambiar `locked_at` tras bloquear y abrir una segunda ronda `open`; todas fallan. Sale la columna `locked_by_report_version_id` de la revisión 1 (BR3.4). | Nivel 1 |
| NFR11.4 | se mantiene | La regla AIR solo propone (FR9.1, FR9.3). | U5 solo publica métricas: ningún código de U5 escribe el umbral ni la regla. La regla estática de U3 de configuración por PR cubre también el módulo HumanReview. | Nivel 0 |
| NFR11.5 | nuevo | Solo el usuario de retención borra en las tablas de U5, y nunca modifica (BR6.2, A-2). | Con `veridicus_retention`, `DELETE` funciona en las cuatro tablas y `UPDATE` falla en todas. Con `veridicus_app`, `DELETE` falla en las cuatro. `ReviewRound` lleva la marca con `kind: mutable` y `purgeable: true`; si falta la marca, la prueba común falla (BR6.3). | Nivel 1 |
| NFR11.6 | nuevo | Descartar la copia de trabajo deja rastro y no cuenta (BR3.9, FD-U5-04). | `discard_correction_round` pasa la ronda `correction` `open` a `discarded`, con `discarded_by` y `discarded_at` no nulos. Sus decisiones siguen en el historial y no entran en el estado vigente (E25). Sin copia abierta, responde `report.conflict` con 0 cambios (E26). | Nivel 1 |

### NFR12 — Datos sintéticos

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR12.1 | se mantiene | Los *fixtures* de U5 son sintéticos. | Notas, reformulaciones y usuarios de prueba usan el catálogo de nombres y las marcas sintéticas de U1. La comprobación de U1 sobre `services/session-api/tests/human_review/` da 0 hallazgos. | Nivel 0 |

## 4. Correspondencia con AUTONOMIA-01..05

| Regla | Qué aporta U5 | Requisitos |
|---|---|---|
| AUTONOMIA-01 | U5 no aplica nada al clúster. Las tablas, los permisos y el disparador entran por la migración de su PR, que corre como `Job` aparte. La regla AIR la escribe U2 por PR. El borrado lo lanza el humano con el `Job` de U13 | NFR11.4, NFR10.22 |
| AUTONOMIA-02 | Cada requisito tiene su criterio y su comando (`tech-stack-decisions.md` §5) | Todos |
| AUTONOMIA-03 | Las decisiones son humanas, del dueño, con las observaciones desplegadas y con quién y cuándo. Nadie reescribe a la IA ni el historial. La máquina de estados y la herencia tienen 100 % de ramas (NFR13.2) | NFR10.1, NFR10.3, NFR10.4, NFR10.9, NFR11.1–NFR11.3, NFR11.6 |
| AUTONOMIA-04 | Sin llamadas externas; el `investigador` no lee observaciones; logs y métricas sin texto | §1, NFR1.1, NFR10.6–NFR10.8, NFR10.19 |
| AUTONOMIA-05 | No aplica directamente: U5 recibe sugerencias que ya pasaron la guardia del analizador, y `propose` (U4, C10) rechaza candidatas sin los 5 campos | — |

## 5. Respuestas a lo que piden otras unidades

| Unidad | Respuesta de U5 |
|---|---|
| U7 forensic-report (AC5.4.1 y AC5.4.4, diferidos a U5) | AC5.4.1: NFR10.1, también en la copia de corrección. AC5.4.4: NFR10.19, con la precisión NFR-U5-03 |
| U7 forensic-report (C11) | Presupuesto de las operaciones de rondas en NFR3.5, `discard_correction_round` incluido; atomicidad de `lock_round` en NFR10.12 |
| U13 ethics-governance (C24) | `purge_session` en NFR10.22 y NFR3.9; el orden de borrado de C24 (HumanReview en el paso 3, tras ReviewReport) se respeta |
| U2 platform (regla 0,25) | Definición de la ventana en NFR15.2 y series de ejemplo en NFR15.4 |
| U1 contracts (C25) | Cifras de U5 en NFR-U5-01 |

## 6. Riesgos aceptados

| Riesgo | Por qué queda | Tratamiento |
|---|---|---|
| `observation-views` registra el despliegue, no la lectura | El servidor no puede comprobar que alguien leyó | El evento queda a nombre del actor y con su hora (NFR11.1), y además en el registro de acceso (NFR10.21) |
| La nota es texto libre y puede contener nombres | Es el criterio del analista (BR2.8) | En el MVP los datos son sintéticos (NFR12). La nota no sale del clúster y nunca va a logs ni métricas (NFR10.6–NFR10.8) |
| Puede faltar una entrada del registro de acceso si el puerto falla | Riesgo aceptado de U3 (punto de guardado de 500 ms) | Log de aviso con IDs (NFR10.21) |
| Quien puede leer todas las sesiones sabe si un `suggestion_id` existe (`204` frente a `404`) | FR1.2 le da esa lectura | Sin riesgo nuevo: ya ve la sesión entera |

## 7. Precisiones a artefactos ya aprobados (NFR-U5-xx)

No edité ningún artefacto aprobado (regla de `project.md`). En la aprobación decides cuáles se llevan al
original, cada una en su propio commit. La tabla §6 de la revisión 1 queda superada por NFR-U5-06.

| ID | Artefacto aprobado | Precisión | Origen |
|---|---|---|---|
| NFR-U5-01 | `contract-design/contract-summary.md` (C25 y cuerpo de `POST /suggestions/{id}/decisions` en C1) | Cifras de U5 en C25: <br>• entran `review_text_max_chars: { value: 2000, unit: chars }` y `review_body_max_bytes: { value: 65536, unit: bytes }`; <br>• `dismissal_window_w` toma `{ value: 8, unit: suggestions }`. <br>`note` y `reformulation` declaran `maxLength` con `x-veridicus-limit: review_text_max_chars`. La ruta documenta el tope del cuerpo. Entran por un PR de U1 antes del código de B5 | FD-U5-02; P1 = A; NFR10.7, NFR10.14 y NFR-U1-07 de U1; aplicada sin preguntar |
| NFR-U5-02 | Functional Design de U5 (FD-U5-02, BR2.7, E21 y §10) | `limits.exceeded` responde `413`, no `422`, en la nota, la reformulación y el cuerpo | NFR-U1-03 (P7 = A de U1); aplicada sin preguntar |
| NFR-U5-03 | `user-stories/stories-adenda-02.md` (AC5.4.4) | «Cualquier rol distinto del dueño … responde 403» se lee con la matriz de FR1.2, como resolvió la pregunta P4 = A del Functional Design de U3: <br>• el analista no dueño y el `admin` leen los hallazgos en solo lectura (AC5.4.2) y no deciden (`403`); <br>• el `investigador` recibe `403` al leerlos; <br>• no existe ningún rol ni pantalla para la persona entrevistada. <br>Propuesta de texto: «Given el rol `investigador`, When pide los hallazgos de una sesión, Then responde 403; un rol distinto del dueño no decide. No existe un rol ni una pantalla para la persona entrevistada.» | P4 = A del Functional Design de U3; diferido a U5 por el Functional Design de U7; aplicada sin preguntar |
| NFR-U5-04 | `contract-design/contract-summary.md` (C15 v2) | Definición exacta de la ventana de `veridicus_session_dismissal_ratio` (NFR15.2): <br>• cuentan las sugerencias con estado vigente decidido en la ronda `open`, incluidas las heredadas; <br>• se ordenan por el `change_seq` de la decisión que da ese estado; <br>• la serie se retira al bloquear o descartar la ronda y al purgar. <br>La métrica de rechazos que proponía la revisión 1 se retira y no entra en C15 | C15 v2; BR4.1; cierra R-01 de la revisión 1; aplicada sin preguntar |
| NFR-U5-05 | `contract-design/contract-summary.md` (C1, respuestas de las rutas de U5) | `decisions` documenta, además de `201` y `409`: <br>• `403`: `auth.forbidden`, `session.not_owner`, `auth.csrf`; <br>• `404`: `suggestion.not_found`; <br>• `413`: `limits.exceeded`; <br>• `422`: `review.note_required`, `validation.invalid_request`. <br>`observation-views` documenta `403` y `404`. Es un cambio menor de documentación | BR1.1, BR1.4, BR2.3, BR2.4, BR2.7; aplicada sin preguntar |
| NFR-U5-06 | Revisión 1 de este NFR (§6, tabla de precisiones) | Filas superadas: <br>• respuestas y `maxLength` → NFR-U5-01 y NFR-U5-05; <br>• ruta `cot-views` → `observation-views` en C1 v2; <br>• `403` para un ID inexistente → `404` de FD-U5-01; <br>• `open_round(for_update=True)` y su uso por U7 → ya están en C11 v2 (cierra R-02); <br>• *W* y métrica de rechazos → NFR-U5-04 | C1 v2, C11 v2, FD-U5-01; aplicada sin preguntar |
