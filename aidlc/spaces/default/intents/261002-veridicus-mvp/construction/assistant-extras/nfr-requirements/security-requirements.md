# Requisitos de seguridad — U8 assistant-extras

**Revisión 2 (2026-11-22), segunda pasada por el cambio 01 (DT27), la adenda 02 y el Functional Design
revisión 2 de U8.** Sustituye a la revisión 1 del 2026-10-03, que queda en el historial de Git.
- **Qué cambia.** U8 ya no tiene segunda lectura del juez, pregunta sugerida ni indicio afectivo. Entrega
  las **aclaraciones neutras** deterministas (US10.3) y la **permutación del verificador activa en todos los
  perfiles** (US10.5, P5 = A).
- **IDs.** Los requisitos conservan su ID. Cada fila dice si **se mantiene**, **cambia**, es **nuevo** o
  está **Retirado** (sin renumerar). Lo nuevo de este documento es NFR11.5 y NFR12.2.
- **Preguntas.** Ninguna en esta pasada (`nfr-requirements-questions.md`, segunda pasada). P1 = A de la
  revisión 1 queda Superada: ya no hay extras que encender. Lo aplicado sin preguntar está en la tabla
  NFR-U8 de §6.
- **Revisión 1.** Sus hallazgos R-01 a R-05 (`reviews/review-01.md`) se cierran en §7.

**Insumos.**
- Flujos F4–F9, frontera de §1, máquina de estados de §3, textos de §6, escenarios E11–E43 y tabla
  FD-U8-01 a FD-U8-11 de `functional-design/functional-spec.md` (functional-spec, revisión 2).
- Reglas BR4.1–BR6.5 de `functional-design/rules.md` (rules) y entidades de `functional-design/entities.md`.
- FR4.5, FR6.4, FR10.3, FR10.5, FR14 y NFR1–NFR15 de `inception/requirements-analysis/requirements.md`
  (requirements, revisión 3; NFR9 «Retirado») y VE-05 y VE-10 de `requirements-adenda-02.md`.
- C1, C3, C6, C8, C15, C18, C19 y C25 de `inception/contract-design/contract-summary.md`
  (contract-summary, revisión 3).
- Lo que fijaron hoy otras unidades, citado por descripción:
  - **U1:** `limits.exceeded` siempre `413`; C25 sin nulos; la sección `clarifications` de C19 entra en
    C19 v2; las etiquetas permitidas de las métricas.
  - **U3:** mecanismo de dueño, anti-CSRF, convención de auditoría y punto de guardado del registro de
    acceso.
  - **U4:** ingesta en una transacción, orden sesión → fila, sondeo de 2 s y 15 s, U4 con ≤ 10 s del humo.
  - **U10:** el proxy como única salida, tope de 2 MiB por respuesta.
  - **U11:** verificador local gpt-oss-20b, permutación activa en todos los perfiles, p95 incremental
    ≤ 180 s, *N* = 300 s, plazo incremental de 900 s en desarrollo y la prueba que pasa de «ninguna
    salida trae `observaciones_conductor`» a «ninguna salida final ni en error».
- Reglas AUTONOMIA-01..05 de `team.md` y prohibiciones de `project.md`.

Niveles de `team.md`: nivel 0 (unitarias, contratos y guardias, cada PR, sin red ni GPU), nivel 1
(integración con PostgreSQL y Redis reales), nivel 2 (CLI de U11 sobre el conjunto sintético, fuera de la
CI), nivel 3 (E2E, `axe` y humo) y manual. Cada prueba lleva su control negativo. Los comandos están en
`tech-stack-decisions.md` §5. U8 reutiliza sin repetirlos los controles de U3 (sesión, rol, anti-CSRF,
auditoría), de U4 (validación de C6 en la ingesta, logs solo con IDs, `XDEL`) y de U11 (escáner de C8,
validación de la salida, permutación).

## 1. Frontera de la unidad (AUTONOMIA-04)

| Componente | Dónde corre | Qué datos cruzan su frontera | Clasificación |
|---|---|---|---|
| IncoherenceAnalyzer, módulo de aclaraciones, en `semantic-agent` | Dentro del clúster, bajo la `NetworkPolicy` de salida denegada | Ninguno nuevo: arma el tema en memoria con el `hecho` ya restaurado. **No hay llamada nueva a un modelo** (BR5.1) | Restringido |
| IncoherenceAnalyzer, módulo de aclaraciones, en la CLI | Máquina local o nodo de ZINE, fuera del clúster, como la CLI | Ninguno nuevo: las salidas siguen las reglas de la CLI (corpus fuera de Git) | Restringido |
| Llamada `verifier_permuted` (F8) | Mismo destino que `verifier` | El verificador de todos los perfiles actuales es local (P1 = A de U11): `hecho`, `tipo` y las dos citas hacia el servidor local, **nada sale**. Con un verificador externo futuro saldría por `anonymizer-proxy`, igual que la llamada directa | Restringido |
| InterviewSession (ConductorObservation y su historial) | `session-api`, dentro | Ninguno sale; filas en PostgreSQL interno | Restringido |
| ConsoleApi (`/conductor-observations/{id}/decision`) | `session-api`, dentro | Tema, turnos y estado hacia el navegador, dentro del clúster (C1) | Restringido |
| AnalystConsole (panel de aclaraciones en M4) | Navegador, servido por `frontend` | Solo habla con ConsoleApi; nunca recibe las citas del hallazgo de origen (BR5.15) | Restringido |
| `config/profiles.yaml` (`permutation`) | Archivo versionado | Ninguno | Interno |
| Reportes de nivel 2 de B8 (BR5.17, BR6.5) | Máquina del humano; se adjuntan al PR | Solo conteos, cifras, *hashes* y versiones (C19 v2 y su sección `clarifications`) | Interno |

**Ningún componente de U8 añade un destino, una llamada a un modelo ni un dato que cruce la frontera.**

## 2. Modelo de amenazas (STRIDE)

T1–T13 de la revisión 1 quedan **Retirado** con F1–F3, salvo las que se reescriben abajo con número nuevo.

| # | Amenaza | STRIDE | Riesgo | Mitigación |
|---|---|---|---|---|
| T14 | El tema revela la contradicción o dice «antes dijo» y orienta la respuesta del compareciente (VE-05, DT23) | Tampering | Alto | NFR10.5, NFR4.3 (`reliability-requirements.md`), guardia de NFR13.2 |
| T15 | El tema contiene el texto de una cita (meta 0 %, FR10.3) | Information disclosure | Alto | NFR4.3, NFR10.1 |
| T16 | Una aclaración lleva una etiqueta o un campo de veracidad (AUTONOMIA-03) | Tampering | Alto | NFR10.4, NFR10.5 |
| T17 | Una aclaración llega al compareciente, se escucha o entra al reporte sin la aprobación del analista | Elevation of privilege | Alto | NFR10.7 |
| T18 | Otro analista, un `admin` o una petición sin anti-CSRF decide una aclaración | Elevation of privilege | Medio | NFR10.6 |
| T19 | Se reescribe o se borra una decisión sobre una aclaración | Repudiation | Medio | NFR11.1, NFR11.2 |
| T20 | El tema, las citas o el texto de un turno aparecen en logs, métricas o eventos de descarte | Information disclosure | Alto | NFR10.8 |
| T21 | Un resultado inyectado en la cola cuela una aclaración que la biblioteca habría quitado | Tampering | Medio | NFR10.1 (segunda línea de BR5.9) |
| T22 | La permutación se apaga en un perfil sin rastro ni medición | Repudiation | Medio | NFR10.9, NFR11.4 |
| T23 | Inyección desde el testimonio que acaba en el tema | Tampering | Medio | NFR5.1 |
| T24 | Una aclaración se aprueba tras la retirada del consentimiento | Elevation of privilege | Medio | NFR10.6 (BR5.12) |
| T25 | Muchas aclaraciones o temas muy largos frenan el sondeo de M4 | Denial of service | Bajo | NFR3.9 (`performance-requirements.md`), NFR-U8-03 |

## 3. Requisitos

### NFR1 — Soberanía de datos

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR1.1 | cambia | U8 no añade destinos ni llamadas a modelos. | Con un `ModelGateway` *fake* que cuenta llamadas, la misma corrida incremental da exactamente las mismas llamadas, en el mismo orden, con el módulo de aclaraciones y sin él (E11). La configuración de U8 no tiene ningún campo URL. La tabla de §1 está en el README del módulo y un componente nuevo entra con su fila en el mismo PR | Nivel 0 y revisión del PR |
| NFR1.2 | cambia | La llamada permutada sale por el mismo camino que la directa. | Para cada perfil de `config/profiles.yaml`, una prueba comprueba que `verifier_permuted` resuelve al mismo proveedor, modelo y `base_url` que `verifier`. En la corrida con el gateway *fake* (E42), los dos registros llevan el mismo `proveedor`, `modelo` y `anonimizado`. Control negativo: un *fixture* de perfil que desvía la llamada permutada hace fallar la prueba. La verificación manual de la `NetworkPolicy` es la de U2, sin pasos propios | Nivel 0 |

### NFR5 — Resistencia adversarial

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR5.1 | cambia | La inyección no llega al tema por otro camino que el `hecho`. | Prueba de propiedad (Hypothesis): para salidas generadas, el tema de cada aclaración es función solo del `hecho` del hallazgo de origen (con turnos, citas y observaciones cambiados, el tema no cambia). Así, el 0 de marcas del Escenario A que U11 mide sobre los `hecho` emitidos vale para los temas. Una aclaración sembrada con la marca de inyección, fuera de una cita, no cambia de regla de descarte ni de salida | Nivel 0 |
| NFR5.2 | Retirado | Los extras no cambian de familia de modelo. | Sale: U8 ya no llama a ningún modelo; la familia del juez y del verificador es de U11 | — |

### NFR10 — Seguridad de la aplicación

Los plazos, la atomicidad y el fallo de la decisión (NFR10.11, NFR10.13–NFR10.17) están en
`reliability-requirements.md`.

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR10.1 | cambia | Las entradas de U8 se validan en su frontera. | (a) Cuerpo de la decisión estricto (`status` ∈ {`approved`, `discarded`}, sin otros campos) y `observation_id` UUID; si no, `422` `validation.invalid_request` sin filas. (b) En la ingesta, cada elemento de `observaciones_conductor` repite BR5.3–BR5.6 contra las citas de todos los hallazgos de la salida (BR5.9); un fallo deja la corrida entera en `analysis.invalid_output`, con **0 sugerencias y 0 aclaraciones** (E23, E24). Una prueba por regla en nivel 0 y un resultado inyectado por regla en nivel 1 | Nivel 0 y nivel 1 |
| NFR10.2 | Retirado | El testimonio no entra en las instrucciones de los extras. | Sale: U8 no tiene *prompt*; lo cubre U11 | — |
| NFR10.3 | Retirado | La pregunta solo se apoya en el marco de verdad. | Sale con la pregunta sugerida y el marco de verdad (cambio 01) | — |
| NFR10.4 | cambia | El esquema de la aclaración es estricto y sin veracidad (BR4.2, BR5.3). | Un elemento con un campo distinto de `tipo`, `tema` y `turnos` (p. ej. `is_truthful`) se quita en la biblioteca con la regla `schema` y, si llega a la ingesta, invalida la corrida. El esquema `ConductorObservation` de C1 declara `additionalProperties: false` y ninguna propiedad cae en las categorías prohibidas de C8 (precisión NFR-U8-04) | Nivel 0 |
| NFR10.5 | cambia | Nada de lo que añade U8 lleva vocabulario prohibido ni la frase de DT23 (BR4.1, BR5.4, BR5.6). | (a) El validador de la biblioteca da lo esperado en el 100 % de los casos de aclaración neutra de `contracts/integrity/scan-cases`, y un caso invertido pone la suite en rojo (BR5.16, E40). (b) Las cadenas del panel (rótulo, estados, botones, motivos y mensajes de error) pasan el escáner de C8 sin tramos excluidos, con «prueba» como control negativo. (c) El panel renderizado pasa el escaneo en el E2E. (d) En nivel 2, **0 coincidencias** de C8 y de la regla de DT23 en los temas emitidos | Niveles 0, 2 y 3 |
| NFR10.6 | cambia | Solo el analista dueño decide, y solo mientras la sesión lo admite (BR5.11, BR5.12). | La ruta declara `x-veridicus-roles: [analista]`, `x-veridicus-owner-only: true` y `X-CSRF-Token`, y U8 registra el resolvedor `observation_id → sesión`. Otro analista → `403` `session.not_owner`; `admin` → `403` `auth.forbidden`; sin anti-CSRF → `403` `auth.csrf`; inexistente → `404` `conductor_observation.not_found`; ya decidida → `409` `conductor_observation.already_decided`; aprobar con el consentimiento retirado o decidir en una sesión cerrada → `409` `conductor_observation.session_closed`. En todos, **0 filas nuevas** (E27–E34) | Nivel 1 |
| NFR10.7 | cambia | Sin la aprobación del analista, una aclaración no suena ni entra al reporte (BR5.14). | U8 expone el puerto `is_observation_approved(observation_id)`; con `proposed` o `discarded`, la consola no muestra «Escuchar audio» y la ruta de audio responde `409` `conductor_observation.not_approved` (E36). El reporte de una sesión con aclaraciones aprobadas no las lista (E37). Prueba de nivel 0 del puerto en U8; la prueba de nivel 1 de la ruta de audio es tarea de U9 en B9 (precisión NFR-U8-07) | Nivel 0 y nivel 1 |
| NFR10.8 | cambia | Los logs, las métricas y los eventos de descarte solo llevan identificadores. | Con una cadena centinela sembrada en un `hecho`, en las dos citas y en un turno: **0 apariciones** en los logs de `semantic-agent` y `session-api` (también los de error), en la salida de error de la CLI, en `/metrics` y en cada `ClarificationDiscardEvent`, que solo lleva `run_id`, `source_finding_id` y la regla (E21) | Nivel 0 (biblioteca) y nivel 1 (servicios) |
| NFR10.9 | cambia | La permutación solo se activa o se apaga por el archivo de perfiles, por PR (BR6.1). | La prueba de BR6.1 falla si un perfil tiene `permutation: false` (E41); apagarla en un perfil exige cambiar el perfil y esa prueba en el mismo PR, con el reporte de BR6.5 adjunto (NFR11.4). Ninguna ruta de C1 escribe perfiles (lo comprueba la suite de U1) | Nivel 0 y revisión del PR |
| NFR10.10 | Retirado | El indicio afectivo es determinista. | Sale con US11.1 (WON'T por DT15) | — |

### NFR11 — Integridad y auditoría

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR11.1 | cambia | `ConductorObservationDecision` entra en la convención de auditoría de U3 como historial (BR5.13). | Registrada con su marca `history`; `actor_user_id` y `at` no nulos; el usuario de la aplicación no tiene `UPDATE` ni `DELETE` sobre ella. Prueba común de nivel 1 de U3 con la tabla | Nivel 1 |
| NFR11.2 | cambia | Una aclaración decidida no cambia de nuevo. | `ConductorObservation` lleva la marca `mutable` con disparador: el usuario de la aplicación solo puede actualizar `status`, y el disparador rechaza todo `UPDATE` si el estado anterior no es `proposed`. Sin `DELETE`. Un fallo forzado al insertar el historial deja `status` en `proposed` (E35). Prueba de nivel 1 que intenta cambiar una `approved` y borrar una `discarded` | Nivel 1 |
| NFR11.3 | cambia | El resultado de la permutación no se reescribe (BR6.3). | Las dos llamadas (`verificador` y `verificador_permutado`) y el descarte `rechazado_permutacion` quedan en las tablas de solo inserción del registro de U4. Prueba de nivel 1 con el resultado de E42: dos `ModelCall`, un descarte, 0 sugerencias de ese candidato, y un `UPDATE` sobre esas filas falla | Nivel 1 |
| NFR11.4 | cambia | El estado de la permutación queda versionado y medido. | `permutation` vive en `config/profiles.yaml`, entra en `config_sha256` de cada corrida y cambia solo por PR. Apagarla en un perfil exige adjuntar el reporte de BR6.5 que muestra el criterio de NFR8.7 (`reliability-requirements.md`) | Revisión del PR y nivel 0 (huella) |
| NFR11.5 | nuevo | Solo la retención borra las tablas de U8 (NFR11, FD-U8-07). | El borrado de una sesión por el `Job` de retención incluye `ConductorObservation` y `ConductorObservationDecision`, con el usuario propio del `Job`; con el usuario de la aplicación el borrado falla. Prueba de nivel 1 común con la de U13 | Nivel 1 |

### NFR12 — Datos sintéticos

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR12.1 | cambia | Los *fixtures* de U8 son sintéticos y marcados. | Hallazgos, citas, temas y resultados inyectados usan el catálogo de nombres y las marcas sintéticas de U1; la comprobación de U1 corre sobre las carpetas de pruebas de U8 con 0 hallazgos | Nivel 0 |
| NFR12.2 | nuevo | Las mediciones de B8 usan solo el conjunto sintético y solo publican cifras. | BR5.17 y BR6.5 corren la CLI sobre `evaluation/` con `origen: sintetico`; la medición con una entrada de corpus termina con código 2. Los reportes adjuntos al PR validan contra C19 v2 (sin texto libre) y su sección `clarifications` solo trae enteros | Nivel 0 y revisión del PR |

## 4. Correspondencia con AUTONOMIA

| Regla | Requisitos de U8 |
|---|---|
| AUTONOMIA-01 | Ninguna tarea de U8 toca el clúster; los perfiles y las migraciones de sus dos tablas entran por PR, la migración en su propio PR (NFR10.9, NFR11.4) |
| AUTONOMIA-02 | Cada requisito nombra su umbral; los comandos están en `tech-stack-decisions.md` §5 |
| AUTONOMIA-03 | NFR10.4–NFR10.7, NFR11.1, NFR11.2 y la guardia de la máquina de estados (NFR13.2) |
| AUTONOMIA-04 | §1, NFR1.1, NFR1.2, NFR10.8, NFR12.2 |
| AUTONOMIA-05 | NFR4.1 y NFR4.2 (`reliability-requirements.md`), NFR11.3 y la guardia de la validación de la aclaración (NFR13.2) |

## 5. Riesgos aceptados

| Riesgo | Tratamiento |
|---|---|
| **Muchas aclaraciones descartadas.** BR5.4 y BR5.5 quitan toda aclaración cuyo `hecho` describe la contradicción o comparte 5 palabras con una cita, así que el analista puede ver pocas | Aceptado: es el costo de P4 = A y de VE-05. Se reporta en nivel 2 con una señal de revisión (NFR4.6, NFR-U8-02); las reglas no se relajan |
| **Una cita de una sola palabra** quita la aclaración si aparece en el tema | Aceptado (functional-spec §9); su frecuencia entra en el mismo conteo |
| **Permutación en CPU con `todo-local`.** Duplica las llamadas al verificador local | Aceptado mientras cumpla NFR8.7; si no, se apaga allí por PR (NFR-U8-01) |
| **Temas largos.** El `hecho` no tiene tope propio en C6 | Aceptado: lo acotan los topes existentes (NFR-U8-03) y el panel lo muestra como texto |

## 6. Precisiones a artefactos ya aprobados (NFR-U8-xx)

No edité ningún artefacto aprobado (regla de `project.md`). En la aprobación decides cuáles se llevan al
original, cada una en su propio commit. Las seis filas de la revisión 1 quedan **Superado** con el cambio
01: los `code` de la pregunta, los campos de C3, el esquema de la pregunta, las métricas de los extras en
C15, la CoT de la segunda lectura y la regla de reclamo de U4 con extras.

| ID | Artefacto aprobado | Precisión | Origen |
|---|---|---|---|
| NFR-U8-01 | Functional Design de U8 (§12, BR6.1, F8 paso 4) | **Costo de `verifier_permuted` en `todo-local`.** La permutación sigue activa en `todo-local`. Se apaga allí, por PR que cambie el perfil y la prueba de BR6.1, solo si (a) la medición de BR6.5 con `todo-local` en la máquina de desarrollo da menos del 98 % de corridas incrementales terminadas sin `tiempo_agotado` dentro de `run_deadline_incremental_s` (900 s), o (b) la prueba de NFR8 no alcanza el 98 % por la llamada permutada. No hay meta de latencia propia para `todo-local`: es un perfil de demostración y NFR3 solo exige que la interfaz no espere. Con `comercial-piloto` rige el p95 ≤ 180 s de U11 | FD §12; NFR8; decisión de U11 de hoy |
| NFR-U8-02 | Functional Design de U8 (§12, BR5.17) | **Tasa de aclaraciones descartadas por regla** = descartadas / (emitidas + descartadas) sobre el conjunto sintético. Se reporta y **no bloquea**. Por encima de **0,50** es una señal: la revisión humana del PR nombra la cifra y decide entre aceptarla o corregir por PR el *prompt* de U11 para que el `hecho` sea un tema; nunca relajar BR5.4 ni BR5.5. El 0 % de citas en los temas emitidos sí bloquea (NFR4.3) | FD §12; regla de `project.md` sobre mediciones sin umbral; `team.md` (umbrales que no se bajan) |
| NFR-U8-03 | Functional Design de U8 (§12) y `contract-summary.md` (C25) | **Sin tope nuevo en C25** para el largo del tema ni para las aclaraciones por sesión. El tema sale del `hecho`, que acotan `model_response_max_bytes` (2 MiB) y `run_message_max_bytes`; las aclaraciones de una sesión no superan sus hallazgos, porque se deduplican por sesión (BR5.10). NFR3.9 prueba el sondeo con 100 aclaraciones. Si una medición lo contradice, la cifra entra por PR de U1 | FD §12; `project.md` (catálogo único) |
| NFR-U8-04 | `contract-summary.md` (C1, `ConductorObservation`) | El esquema declara `additionalProperties: false` y suma `created_at` (`date-time`), que BR4.2 y FD-U8-03 dan por hechos y C1 no trae. Va en el PR de U1 que ya lleva FD-U8-02 | BR4.2; FD-U8-03 |
| NFR-U8-05 | `contract-summary.md` (C15) | Métricas de U8 por PR de U1, solo con etiquetas permitidas: `veridicus_conductor_observations_ingested_total` (sin etiquetas) y `veridicus_conductor_observation_decisions_total` (`state`: `approved`, `discarded`). Los descartes por regla no van a Prometheus: la biblioteca no exporta métricas (decisión de U11), así que se cuentan en el reporte de nivel 2 y en los logs | NFR15.1; decisión de U11 de hoy |
| NFR-U8-06 | NFR Requirements de U4 (prueba de carga de NFR8) | La prueba de carga corre con los perfiles tal como están, con la permutación activa (P5 = A), y su reporte registra `config_sha256` por sesión; falla si una sesión usa un perfil con `permutation: false`. Sustituye a NFR8.1 de la revisión 1 de U8 (extras apagados) | P5 = A; BR6.1 |
| NFR-U8-07 | Functional Design de U9 (ruta de audio) | La prueba de nivel 1 de `GET /conductor-observations/{id}/audio` con `proposed` y `discarded` (`409` `conductor_observation.not_approved`) es tarea de U9 en B9, sobre el puerto `is_observation_approved` de U8. Cierra R-02 de la revisión 1 | R-02 de la revisión 1; BR5.14 |
| NFR-U8-08 | `tech-stack-decisions.md` de U8, revisión 1 (comando de nivel 2) | La medición de nivel 2 de U8 usa la CLI de U11 (`veridicus analyze` en modo incremental y `veridicus evaluate`), no el arnés de U4 ni banderas `--extras` | Cambio 01; decisión de U4 de hoy (el nivel 2 lo corre la CLI) |
| NFR-U8-09 | Functional Design de U8 (BR6.5, F9 paso 2) | «Con y sin permutación» se mide **por papel en la misma corrida**, no con dos corridas: BR6.1 prohíbe un perfil con `permutation: false` y la CLI solo acepta perfiles aprobados. El costo es el de las llamadas `verificador_permutado` (cantidad, *tokens*, latencia p50 y p95 del reporte C19) y la duración sin permutación se estima restando su latencia | BR6.1; BR6.5; perfiles aprobados de U11 |

## 7. Hallazgos de la revisión 1

| Hallazgo | Cierre |
|---|---|
| R-01 (reintentos de la segunda lectura) | Caduca con NFR10.12 Retirado; los reintentos son de U11 y U4 |
| R-02 (prueba de la ruta de audio sin dueño) | NFR-U8-07 |
| R-03 (tasa en línea con pocas candidatas) | Caduca: NFR4.4 ya no mide una tasa propia; la consistencia la mide U11 con 40 muestras × 3 corridas |
| R-04 (capacidad de la cola con el p95 como media) | NFR8.2 queda orientativo y el criterio es NFR8.7 (`scalability-requirements.md`) |
| R-05 (prerrequisitos de otras unidades) | §4 de `tech-stack-decisions.md` lista NFR-U8-04, NFR-U8-05, FD-U8-01, FD-U8-02, FD-U8-04, FD-U8-07 y FD-U8-09 como prerrequisitos del plan de tareas de U8 |
