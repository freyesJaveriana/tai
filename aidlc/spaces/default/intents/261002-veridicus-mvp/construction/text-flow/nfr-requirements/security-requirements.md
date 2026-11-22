# Requisitos de seguridad — U4 text-flow

**Revisión 2 (2026-11-22), segunda pasada por el cambio 01 (DT27), la adenda 02 y el Functional Design
revisión 2 de U4.** Sustituye a la revisión 1 del 2026-10-03, que queda en el historial de Git.
- **IDs.** Los requisitos que siguen conservan su ID. Lo que sale queda «Retirado» sin renumerar y nombra
  a su nuevo dueño. Lo nuevo toma el número siguiente de su grupo: NFR1.3–NFR1.7, NFR10.24–NFR10.25 y
  NFR11.4–NFR11.5. Cada fila dice si **se mantiene**, **cambia**, es **nuevo** o está **Retirado**.
- **Respuestas.** P6 = A (`transcript_max_chars` = 250 000) y P7 = A (`turn_max_chars` = 20 000 y
  `transcript_max_turns` = 2 000, comprobados fuera de Git). P1–P3, S2 y S3 de la revisión 1 quedan
  superadas por el cambio 01; P4 se sustituye por las cifras de U11; P5 y S1 siguen, S1 adaptada.
- **Lo aplicado sin preguntar** está en la tabla NFR-U4 de §6.

**Insumos.**
- Flujos F3–F15, frontera AUTONOMIA-04 de §1, máquinas de estado de §3, escenarios E5–E55 y tabla
  FD-U4-01 a FD-U4-22 de `functional-design/functional-spec.md` (functional-spec, revisión 2).
- Reglas BR4.1–BR19.4 de `functional-design/rules.md` (rules) y entidades de
  `functional-design/entities.md`.
- FR3, FR4, FR9, FR13–FR15 y NFR1–NFR15 de `inception/requirements-analysis/requirements.md`
  (requirements, revisión 3; NFR9 «Retirado»), y VE-01, VE-06, VE-07, VE-10 y VE-14 de
  `requirements-adenda-02.md`.
- C1–C3, C6–C8, C10, C11, C13, C15–C18, C21, C24 y C25 de
  `inception/contract-design/contract-summary.md` (contract-summary, revisión 3), con CD-01, CD-02, CD-04,
  CD-06 y CD-11.
- Lo que fijaron hoy los NFR de U1, U2, U3, U10 y U11, y las precisiones FD-U5-04, FD-U6-07, FD-U6-15,
  FD-U6-19, FD-U9-07, FD-U9-08, FD-U13-08 y FD-U13-13.
- Respuestas de `nfr-requirements-questions.md` y reglas AUTONOMIA-01..05 de `team.md` y prohibiciones
  de `project.md`.

Niveles de `team.md`: nivel 0 (unitarias, contratos y políticas, cada PR), nivel 1 (integración con
PostgreSQL y Redis reales y *fakes* del `ModelGateway` y de C17, cada PR), nivel 3 (E2E y humo) y manual.
El nivel 2 lo corre la CLI de U11 y vale para el trabajador por la prueba de equivalencia (BR15.9). Los
comandos están en `tech-stack-decisions.md` §5.

## 1. Frontera de la unidad (AUTONOMIA-04)

| Componente | Dónde corre | Qué datos cruzan su frontera | Clasificación |
|---|---|---|---|
| ConsoleApi (rutas de U4) | `session-api`, dentro del clúster | Testimonio, hallazgos, consentimiento y registro de modelos hacia el navegador, dentro del clúster (C1) | Restringido |
| InterviewSession (sesión, turnos, encolado, ingesta, supervisor de plazos) | `session-api`, dentro | Mensajes C2 y C3 y la clave de cancelación por Redis interno; nada sale | Restringido |
| HumanReview (`propose`, U5) | `session-api`, dentro | Ninguno | Restringido |
| AnalysisWorker | `semantic-agent`, dentro, bajo la `NetworkPolicy` de salida denegada (U2) | Solo dentro de la llamada a C17: hacia los servidores locales (C14) o hacia `anonymizer-proxy` (C21). Sin credenciales de base de datos ni claves de proveedores | Restringido |
| IncoherenceAnalyzer (U11, en el proceso del trabajador) | `semantic-agent`, dentro | Igual que AnalysisWorker | Restringido |
| `anonymizer-proxy` (U10) | Pod propio, único con salida (443 y DNS) | Texto seudonimizado hacia el proveedor comercial (C22) | Sale del clúster seudonimizado |
| AnalystConsole (M3, M4, aviso) | Navegador, servido por `frontend` | Solo habla con ConsoleApi (ADR-004) | Restringido |
| PostgreSQL y Redis | Servicios del clúster | Ninguno; `ModelCall` y `AnonymizationIncident` no tienen texto | Restringido |

**Ningún componente de U4 hace una llamada fuera del clúster.** Lo único que sale es lo que el proxy de
U10 envía, ya seudonimizado, cuando el perfil de la sesión tiene un papel comercial y el consentimiento
autoriza la transferencia. Con P6 = A una sola llamada puede llevar hasta 250 000 caracteres de
testimonio seudonimizado (NFR-U4-02).

## 2. Modelo de amenazas (STRIDE)

| # | Amenaza | STRIDE | Riesgo | Mitigación |
|---|---|---|---|---|
| T1 | Inyección de instrucciones desde el testimonio | Tampering | — | **Retirado** de U4: el *prompt* es de U11 (NFR5.4 de U11) |
| T2 | *Prompt* del sistema alterado | Tampering | — | **Retirado** de U4: U11 (NFR5.4 de U11) |
| T3 | Hallazgo con una cita inventada o en otro turno llega a la consola | Tampering | Alto | NFR10.4 (segunda línea de C6) |
| T4 | Etiqueta de veracidad en la salida o en la interfaz (AUTONOMIA-03) | Tampering | Alto | NFR10.5 |
| T5 | Sugerencia parcial o sin sus campos obligatorios (AUTONOMIA-05) | Tampering | Alto | NFR10.4 |
| T6 | El trabajador escribe en la base o lee tablas ajenas | Elevation of privilege | Medio | NFR10.6 |
| T7 | Testimonio o constancias en logs, métricas o en los *streams* después de usarse | Information disclosure | Alto | NFR10.7, NFR10.9 |
| T8 | `semantic-agent` arranca con un destino externo sin el anonimizador delante | Information disclosure | Alto | NFR1.1, NFR1.4 |
| T9 | Un analista opera la sesión de otro, o `admin` o `investigador` crean sesiones | Elevation of privilege | Medio | NFR10.10 |
| T10 | Una petición enorme agota la memoria de `session-api` | Denial of service | Medio | NFR10.1, NFR10.11 |
| T11 | Un mensaje de cola mal formado o de versión mayor desconocida | Tampering | Bajo | NFR10.1 |
| T12 | Un analista autenticado inunda la cola | Denial of service | Bajo | Riesgo aceptado (§5) |
| T13 | Cambio silencioso del perfil, de los límites o del *prompt* de una sesión | Repudiation | Medio | NFR11.3, NFR10.24 |
| T14 | Borrar o reescribir el historial de corridas o de estados | Repudiation | Medio | NFR11.1, NFR11.2 |
| T15 | `semantic-agent` importa o instala `libs-anonymizer` y sus adaptadores comerciales | Elevation of privilege, Information disclosure | Alto | NFR1.3 |
| T16 | Una llamada externa sin anonimizar pasa inadvertida y la sesión sigue analizando | Information disclosure, Repudiation | Alto | NFR1.5, NFR11.4 |
| T17 | Sale una llamada después de pausar, terminar, retirar el consentimiento o bloquear | Information disclosure | Alto | NFR1.6 |
| T18 | Se analiza con un perfil comercial sin autorización de transferencia | Information disclosure | Alto | NFR1.7 |
| T19 | Una configuración faltante o un límite subido por el entorno pasan sin aviso | Tampering | Medio | NFR10.25 |

## 3. Requisitos

### NFR1 — Soberanía de datos

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR1.1 | cambia | `semantic-agent` solo habla con destinos internos. | La raíz de composición acepta como dirección de `anonymizer-proxy` solo el nombre corto `http://veridicus-anonymizer-proxy:<puerto>` o un *host* que termine en `.svc.cluster.local` (NFR-U1-06); cualquier otra forma impide arrancar con un log que nombra el ajuste sin su valor. Las `base_url` locales las valida U11 (NFR1.6 de U11). Una prueba por forma rechazada y su control positivo | Nivel 0 |
| NFR1.2 | cambia | `semantic-agent` y `session-api` no necesitan salida a internet. | Sus `/readyz` pasan con la `NetworkPolicy` de U2 aplicada; nada de U4 descarga en ejecución. Verificación manual en el clúster antes de la sustentación, junto con la de U2 | Manual |
| NFR1.3 | nuevo | `semantic-agent` no puede importar ni instalar `libs-anonymizer` (BR15.8, mitad de U4 de AC11.6.4). | El contrato `semantic-agent-no-anonymizer` de import-linter, el lockfile de `semantic-agent` sin `libs-anonymizer`, `import libs.anonymizer` con `ModuleNotFoundError` en la imagen construida y `sys.modules` sin `libs.anonymizer` tras arrancar. Control negativo con un import sembrado (E46) | Nivel 0 |
| NFR1.4 | nuevo | Un perfil con destino externo sin el anonimizador delante impide arrancar (BR14.9, BR15.7). | Sin la dirección del proxy, o con `check_ready()` de C21 fallido, `semantic-agent` termina o no pasa `/readyz` y no consume la cola (E47). Con solo perfiles locales no se llama. Control positivo con el proxy *fake* sano | Nivel 0 y nivel 1 |
| NFR1.5 | nuevo | Un incidente de anonimización bloquea la sesión (BR16.3–BR16.5). | Con un registro inyectado con una llamada `external` y `anonimizado: false`: sesión `blocked` o `blocked_code` fijo, `AnonymizationIncident` solo con IDs, 0 sugerencias, corridas en cola `cancelled` y el *fake* con 0 llamadas nuevas; turno, reintento y modo final responden `409` `session.blocked` (E36, E37, E51). 100 % de ramas en la decisión | Nivel 0 y nivel 1 |
| NFR1.6 | nuevo | Ninguna llamada nueva sale después de cancelar una corrida (VE-10 (a), CD-06). | Tras pausar, terminar, retirar el consentimiento, bloquear o vencer el plazo, el *fake* del `ModelGateway` registra 0 llamadas nuevas: el trabajador consulta la clave y el plazo antes de empezar y antes de cada llamada (BR15.4). También tras reiniciar Redis (E52) | Nivel 1 |
| NFR1.7 | nuevo | Sin `autoriza_transferencia` solo se admiten perfiles locales (BR14.5, VE-07). | M3 no ofrece perfiles comerciales y `POST /sessions` responde `422` `profile.transfer_not_authorized` con 0 filas (E26) | Nivel 1 y Vitest |

### NFR4 — Calidad de la IA (lo que toca a seguridad)

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR4.3 | Retirado | Referencias de la CoT a pasajes recuperados. | Sale el marco documental (cambio 01). La verificación de citas es de U11 (NFR4.1 de U11) y la segunda línea de U4 está en NFR10.4 | — |

### NFR5 — Resistencia adversarial

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR5.1 | Retirado | Escenario A. | Pasa a U11 (NFR5.1 de U11): el *prompt* y el juez son suyos | — |
| NFR5.2 | Retirado | Escenario B. | Pasa a U11 (NFR5.2 de U11) | — |

### NFR10 — Seguridad de la aplicación

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR10.1 | cambia | Toda entrada se valida en su frontera antes de crear filas. | Turno: 1 a `turn_max_chars` = 20 000 caracteres tras quitar los bordes; vacío `422`, uno más `413` `limits.exceeded`, 0 filas (BR5.1, E6). Un turno que llevaría la sesión por encima de `transcript_max_turns` = 2 000 o `transcript_max_chars` = 250 000 responde `413` `limits.exceeded` antes de encolarse (FR3.7). `Consent` y perfil según BR14.1–BR14.5. C2 se valida contra su esquema al publicar y al consumir, y C3 al ingerir; un mensaje inválido o de versión mayor desconocida va a `<cola>:failed` sin filas (BR5.6). Todas las cifras salen de C25 (NFR10.25) | Nivel 0 (contratos con los *fixtures* de U1) y nivel 1 |
| NFR10.2 | Retirado | El testimonio nunca entra en las instrucciones. | Pasa a U11 (NFR5.4 de U11) | — |
| NFR10.3 | Retirado | *Prompt* del sistema como configuración inmutable. | Pasa a U11 (NFR5.4 y NFR10.15 de U11); U4 solo guarda el `prompt_sha256` de cada intento (BR9.1) | — |
| NFR10.4 | cambia | Ninguna sugerencia nace parcial ni con campos que U4 arme. | La ingesta valida otra vez la salida contra C6 y su regla 2 (BR8.1) y los campos obligatorios (BR8.5); cualquier fallo deja la corrida entera en `analysis.invalid_output` con 0 sugerencias (E14 (a)–(d), E17, E45). `estado: error` nunca deja sugerencias (BR11.3). La sugerencia copia los campos tal cual (BR8.6, ida y vuelta del *fixture*). Restricciones `CHECK` en la base. 100 % de ramas | Nivel 0 y nivel 1 |
| NFR10.5 | cambia | Ni la salida ni la consola llevan etiquetas de veracidad (AUTONOMIA-03). | La ingesta pasa `hecho` y `observaciones` por el escáner de U11 con las dos citas como fuentes literales; una coincidencia invalida la corrida entera (BR8.4, E16). En nivel 0, el catálogo de mensajes, los rótulos y las plantillas; en nivel 3, el texto renderizado de M3 y M4; 0 coincidencias fuera de las citas, el texto del analista y el aviso (BR12.2, E49), con un control negativo por término. U4 no copia la lista (BR12.1) | Niveles 0, 1 y 3 |
| NFR10.6 | cambia | El trabajador no tiene acceso a la base (ADR-002). | `semantic-agent` no recibe ninguna credencial de PostgreSQL (U2) y no importa controladores de base (import-linter, BR15.6); su única escritura es en Redis (`veridicus:results`). Control negativo: un import de `psycopg` sembrado hace fallar la CI | Nivel 0 |
| NFR10.7 | cambia | Los logs solo llevan identificadores. | Campos permitidos: `session_id`, `run_id`, `turn_id`, `attempt`, `message_id`, `code`, duraciones, tamaños y conteos. Prueba de nivel 1: una cadena centinela sembrada en un turno, en `constancia` y `constancia_mandato` del consentimiento y en las `observaciones` del *fake* aparece 0 veces en los logs de `session-api`, su trabajador y `semantic-agent`, también en los de error. Una excepción se registra con su tipo y su `code`, nunca con su mensaje si puede traer texto | Nivel 1 |
| NFR10.8 | Retirado | Los servidores de modelos no registran *prompts*. | Pasa a U2 (despliegue) y a U11 (servidor local) | — |
| NFR10.9 | cambia | Los mensajes con testimonio no se quedan en Redis. | Tras `XACK` de un mensaje de C2 o C3, el consumidor lo borra (`XDEL`). Las entradas de `veridicus:runs:failed` y `veridicus:results:failed` llevan solo `message_id`, `run_id`, `attempt` y `code`, y se recortan a 1 000. La clave de cancelación no lleva valor con texto. Prueba de nivel 1: tras una corrida, `XRANGE` de los dos *streams* no contiene el texto (NFR-U4-07) | Nivel 1 |
| NFR10.10 | cambia | Las rutas de U4 aplican rol, dueño y anti-CSRF de U3. | Cada ruta de U4 declara `x-veridicus-roles` y, si aplica, `x-veridicus-owner-only`; las de escritura exigen `X-CSRF-Token`; `GET /notice` es la única pública (FD-U4-08). Pruebas `403`: `admin` o `investigador` crean sesión o envían turno (E23); otro analista envía turno o reintenta en una sesión ajena; petición sin anti-CSRF; todas con 0 filas (BR4.2, BR4.3) | Nivel 1 |
| NFR10.11 | cambia | Una petición grande se corta antes de leerse entera. | `POST /sessions/{id}/turns` deja de leer el cuerpo al pasar 4 × `turn_max_chars` + 4 096 bytes (el texto en UTF-8 más el sobre) y responde `413` `limits.exceeded`; prueba de nivel 1 con 5 MB: `413`, 0 filas y sin crecimiento de memoria del proceso por encima de 20 MiB. La carga de escenarios de la revisión 1 sale con el cambio 01 | Nivel 1 |
| NFR10.12 | Retirado | Modelos fijados y auditables. | Pasa a U2 (`deploy/models.lock`) y a U11 (registro por llamada) | — |
| NFR10.13 | se mantiene | Todo error sale como Problem Details. | Errores de U4 con `code` del catálogo de C1 y `detail` en español, sin trazas, SQL ni texto del modelo; `limits.exceeded` siempre `413` (NFR-U1-03). Los *timeouts* están en `reliability-requirements.md` §2 | Nivel 0 y nivel 1 |
| NFR10.24 | nuevo | La sesión queda ligada a su perfil y nadie cambia la configuración desde la consola (BR4.1, BR14.6). | Un disparador impide cambiar `profile_name`, `effective_config` y `config_sha256`; el OpenAPI no tiene ninguna ruta que escriba perfiles, límites, precios ni *prompts* (prueba sobre C1). Una sesión creada antes de un PR que cambia su perfil conserva su huella (E9) | Nivel 0 y nivel 1 |
| NFR10.25 | nuevo | Una configuración faltante o un límite subido impiden arrancar (BR14.9, `team.md`). | Sin archivo de perfiles válido, sin `contracts/limits.v1.yaml` o con una `VERIDICUS_LIMIT_<NOMBRE>` que sube una cifra, `session-api` y `semantic-agent` terminan con código ≠ 0 y no pasan `/readyz`; el log nombra el ajuste sin su valor (un *canary* no aparece). Toda cifra sale de `veridicus_contracts.limits.load` (NFR10.14 de U1); una prueba de nivel 0 falla si U4 usa un número de límite literal | Nivel 0 y nivel 1 |

### NFR11 — Integridad y auditoría

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR11.1 | cambia | Las tablas de U4 cumplen la convención de U3 (BR11.4). | `SessionStatusChange`, `RunStatusChange`, `AnalysisRun`, `RunAttempt`, `ModelCall`, `DiscardedCandidate`, `AnonymizationIncident` y `Turn` son `history`, con actor (`actor_kind` y, si es sistema, `actor_system` de la lista con `analysis-worker` y `run-supervisor`) y hora no nulos; `InterviewSessionRecord` y `ConsentRecord` son `mutable` con disparadores que limitan las columnas | Nivel 1 (prueba común de U3) |
| NFR11.2 | cambia | El historial de corridas no se reescribe. | El usuario de la aplicación no tiene `UPDATE` ni `DELETE` sobre las tablas `history`; un reintento crea filas nuevas con `attempt + 1` (BR5.9); solo `veridicus_retention` borra, por `purge_session` (BR19.3) | Nivel 1 |
| NFR11.3 | cambia | La configuración de una corrida es auditable. | Cada `RunAttempt` guarda `config_sha256` de la sesión, `prompt_sha256` y `analyzer_version` de la salida (BR9.1, BR16.2); el perfil, los límites y el *prompt* solo cambian por PR (FR9.2). Sale el umbral de la revisión 1 | Nivel 1 y revisión del PR |
| NFR11.4 | nuevo | El incidente sobrevive a la retención y no lleva texto (FD-U4-12). | `AnonymizationIncident` no tiene clave foránea a la sesión y guarda solo IDs, `code` y hora; tras `purge_session` sigue ahí. Un resultado de una sesión ya borrada se descarta sin filas, pero su incidente se registra igual (NFR-U4-09) | Nivel 1 |
| NFR11.5 | nuevo | El consentimiento lleva quién y cuándo, fijados por el servidor (BR14.2). | `recorded_at` es la hora del servidor y `recorded_by` el analista; un `registrado_en` de la petición se ignora (E28) | Nivel 1 |

### NFR12 — Datos sintéticos

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR12.1 | se mantiene | Los *fixtures* de U4 son sintéticos y marcados. | Sesiones, turnos, consentimientos y salidas *fake* usan el catálogo y las marcas de U1; la comprobación de U1 corre sobre las carpetas de pruebas de U4 con 0 hallazgos. El script de P7 corre fuera de Git sobre el piloto y solo imprime dos cifras (NFR-U4-03) | Nivel 0 |

## 4. Trazabilidad de AUTONOMIA

| Regla | Requisitos de U4 |
|---|---|
| AUTONOMIA-01 | U4 no aplica nada al clúster; perfiles, límites y *prompt* entran por PR (NFR11.3, NFR10.24); el script de P7 lo lanza el humano |
| AUTONOMIA-02 | Cada requisito tiene su criterio y su comando (`tech-stack-decisions.md` §5) |
| AUTONOMIA-03 | NFR10.5, NFR11.1, NFR11.2 |
| AUTONOMIA-04 | §1, NFR1.1–NFR1.7, NFR10.6, NFR10.7, NFR10.9, NFR11.4 |
| AUTONOMIA-05 | NFR10.4, NFR4.6 (`reliability-requirements.md`), 100 % de ramas en la ingesta (NFR13.2) |

## 5. Riesgo aceptado

**T12 — inundar la cola.** Un analista autenticado puede encolar muchas corridas y retrasar las de otras
sesiones. En el MVP hay un solo analista; el plazo que suma la cola (NFR3.5) evita fallos en cadena y su
tope (`run_queue_wait_max_s`) acota la espera. No se añade un límite de corridas por sesión. Se vigila con
`veridicus_run_queue_depth` (`observability-requirements.md`).

**Más testimonio por llamada (P6 = A).** Una llamada comercial puede llevar hasta 250 000 caracteres
seudonimizados. Lo acepta el consentimiento que autoriza la transferencia (NFR1.7) y lo cubren las pruebas
de 0 fugas de U10, que se repiten con esa cifra (NFR-U4-02).

## 6. Precisiones a artefactos ya aprobados (NFR-U4-xx)

No edité ningún artefacto aprobado (regla de `project.md`). En la aprobación decides cuáles se llevan al
original, cada una en su propio commit. Las filas de la revisión 1 quedan como registro, marcadas
«Superado». Todas las filas nuevas salen de las fuentes, salvo NFR-U4-01 a NFR-U4-03, que llevan P6 = A y
P7 = A.

| ID | Estado | Artefacto aprobado | Precisión | Origen |
|---|---|---|---|---|
| — (rev. 1) | Superado | `contract-summary.md` C3 | `turn.error.timeout` en `error_code`. C3 se reescribió y el plazo es `analysis.system` | Cambio 01 |
| — (rev. 1) | Superado | `contract-summary.md` C13 | `count_tokens` en `ModelGateway`. El *prompt* y el gateway pasan a U11 | Cambio 01 |
| — (rev. 1) | Superado | `contract-summary.md` C2 y C3 | Fallidos solo con IDs y `XDEL` tras confirmar. Lo sustituye NFR-U4-07 | NFR10.9 |
| — (rev. 1) | Superado | `contract-summary.md` C2 | Fórmula del plazo de S1 por turno. La sustituye NFR-U4-04 | S1 = A |
| — (rev. 1) | Superado | Catálogo de mensajes de U1 | Mensaje de `turn.error.system` para el *prompt* largo. Sale el *prompt* de U4 | Cambio 01 |
| NFR-U4-01 | Propuesta | `contract-summary.md` (C25) y U1 (catálogo de límites) | Cifras de U4: `turn_max_chars` = 20 000 (`chars`), `transcript_max_turns` = 2 000 (`turns`), `transcript_max_chars` = 250 000 (`chars`), `run_message_max_bytes` = 2 097 152 (`bytes`), `claim_idle_ms` = 60 000 (`ms`), `run_max_deliveries` = 3 (`deliveries`), `cancel_key_margin_s` = 120 (`s`) y `poll_interval_s` = 15 (`s`). Las tres primeras entran por PR de U1 antes del código de B11, que ya las usa (NFR10.1 de U11); las demás, antes de B3. `import_file_max_bytes` y `heartbeat_timeout_s` siguen en U6 | P6 = A; P7 = A; NFR-U1-07 |
| NFR-U4-02 | Propuesta | NFR Requirements de U10 (NFR-U10-01, NFR-U10-04) y de U11 (NFR3.2, NFR3.4, `tech-stack-decisions.md` §3) | **P6 = A** obliga a U10 y U11 a repetir sus comprobaciones con 250 000 caracteres donde hoy dicen 186 000: (a) el cuerpo de C21 con una transcripción de 250 000 caracteres cabe en `anonymizer_request_max_bytes`; (b) el p95 de seudonimizarla es ≤ 0,5 × `anonymizer_masking_budget_ratio` × `model_call_timeout_s`, lo que exige **`model_call_timeout_s` ≥ 270 s** en todo despliegue con un perfil comercial (los 300 s de la máquina de desarrollo alcanzan); (c) NFR3.2 y NFR3.4 de U11 se miden con la transcripción de 250 000. Si alguna no se cumple, falla el PR de esa unidad; no se bajan umbrales | P6 = A |
| NFR-U4-03 | Propuesta | `user-stories/stories.md` (AC2.6.x) y Functional Design de U6 (§11) | **P7 = A:** antes del PR de U1 que fija `turn_max_chars` y `transcript_max_turns`, el humano corre `scripts/count-transcript-limits.py` fuera de Git sobre las 10 entrevistas del piloto; el script solo imprime el turno más largo (caracteres) y el mayor número de turnos. Si alguna cifra no cabe con un 25 % de margen, se sube por ese PR. El script está en el repositorio y no lee nada de él | P7 = A; AUTONOMIA-01 |
| NFR-U4-04 | Propuesta | `contract-summary.md` (C2 `deadline_at`, C25) y Functional Design de U4 (BR5.4, BR5.8) | `deadline_at = enqueued_at + plazo propio + min(suma de los plazos propios de las corridas por delante en `queued` o `processing` de todo el sistema, run_queue_wait_max_s)`. El plazo propio es `run_deadline_incremental_s` o `run_deadline_final_s` de la `effective_config` de la sesión. Cifra nueva de C25: `run_queue_wait_max_s` = 10 800 (`s`), tres modos finales por delante. El reintento lo calcula igual | S1 = A adaptada; FD-U4-09 |
| NFR-U4-05 | Propuesta | `contract-summary.md` (C25) | Cifra nueva `poll_interval_active_s` = 2 (`s`): intervalo del sondeo con corridas `queued` o `processing`; `poll_interval_s` = 15 es el de sin corridas en curso | P5 = A |
| NFR-U4-06 | Propuesta | `contract-summary.md` (C2, «Entrega y fallos») | El trabajador renueva cada 15 s el reclamo del mensaje que procesa (`XCLAIM … JUSTID` a sí mismo), así un trabajador vivo nunca pierde su mensaje y `claim_idle_ms` = 60 000 basta aunque un modo final dure una hora | Esta etapa (NFR10.15) |
| NFR-U4-07 | Propuesta | `contract-summary.md` (C2 y C3) | Tras `XACK` el consumidor borra el mensaje (`XDEL`); los fallidos llevan solo `message_id`, `run_id`, `attempt` y `code`, y se recortan a 1 000 | NFR10.9 |
| NFR-U4-08 | Propuesta | `contract-summary.md` (C15) y las etiquetas permitidas del NFR de U1 | Métricas de U4 en C15 por PR de U1: `veridicus_run_latency_seconds`, `veridicus_run_queue_depth`, `veridicus_run_queue_wait_seconds`, `veridicus_ingest_duration_seconds`, `veridicus_model_input_tokens_total`, `veridicus_model_output_tokens_total` y `veridicus_sessions_blocked_total`; solo etiquetas de la lista (`mode`, `outcome`, `error_code`, `provider`, `role`) | NFR15.1 |
| NFR-U4-09 | Propuesta | Functional Design de U13 (FD-U13-13) y de U4 (FD-U4-11) | Un resultado de una sesión ya borrada se confirma sin filas de resultado, pero si trae un incidente se registra igual en `AnonymizationIncident`, solo con IDs | FD-U13-13; FD-U4-11; VE-14 |
| NFR-U4-10 | Propuesta | Functional Design de U9 (FD-U9-07) | Una corrida en espera no tiene `deadline_at` hasta que se libera; al liberarla se calcula con NFR-U4-04, y la liberación ocurre ≤ 1 s después de ingerir la transcripción que esperaba | FD-U9-07 |
| NFR-U4-11 | Propuesta | `requirements.md` (NFR8) | La prueba de NFR8 usa `comercial-piloto` sobre el conjunto sintético: cada sesión entra como un bloque pegado (una corrida incremental), se finaliza y corre su modo final; solo se intenta si pasa NFR8.2 de U11. Gasta llamadas a Anthropic, solo con datos sintéticos | NFR8.2 de U11 |
| NFR-U4-12 | Hecho | NFR Requirements de U10 (NFR-U10-08) | El trabajador hace una corrida a la vez, así que nunca pasa de 1 de las 4 peticiones simultáneas del proxy; si aun así recibe el `503`, la corrida termina en `analysis.anonymizer_unavailable` sin reintento (BR16.7) | NFR-U10-08 |
| NFR-U4-13 | Hecho | NFR Requirements de U11 (NFR-U11-13) | Las pruebas de la franja del modo fragmentado leen la ventana y el solapamiento de `registro.fragmentado`; el ejemplo 40/8 de E42 no fija ninguna cifra | NFR-U11-13 |
