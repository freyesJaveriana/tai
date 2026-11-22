# Requisitos de seguridad — U13 ethics-governance

**Revisión 1 (2026-11-22): primera pasada de una unidad nueva del cambio 01 (DT27) y de la adenda 02.**
- **IDs.** Todo es **nuevo**. Cada requisito hereda el ID del NFR de Inception que detalla y le añade un
  número (`NFR10.3` detalla NFR10). Los números no se repiten entre los seis documentos de la unidad.
- **Preguntas.** Ninguna: todo lo fijan las fuentes (`nfr-requirements-questions.md` §3). Lo que esta etapa
  aplicó sin preguntar está en la sección 2 de ese archivo y en la tabla NFR-U13-xx (§7).
- **Demostración (ADR-016).** U13 no pone compuertas. Sus requisitos de seguridad protegen lo que guarda
  (la nota, el registro y las actas) y cómo borra, no el acceso a las sesiones.

**Insumos.**
- Flujos F1–F10, errores §9, escenarios E1–E54, preguntas abiertas §11 y tabla FD-U13-01 a FD-U13-13 de
  `functional-design/functional-spec.md` (functional-spec, revisión 1).
- Reglas BR1.1–BR9.2 de `functional-design/rules.md` (rules) y entidades de `functional-design/entities.md`.
- FR1.2, FR1.3 y NFR1–NFR15 de `inception/requirements-analysis/requirements.md` (requirements, revisión 3;
  NFR9 «Retirado»), y VE-04, VE-11, VE-12, VE-15, VE-16, A-2 y A-3 de `requirements-adenda-02.md`.
- C1 (`/acknowledgements`, `/problem-reports`, `/auth/me`), C8, C23, C24 y C25 de
  `inception/contract-design/contract-summary.md` (contract-summary, revisión 3).
- Lo que fijaron hoy otras unidades:
  - **U1:** `limits.exceeded` siempre `413` (NFR-U1-03), C25 sin nulos (NFR-U1-07) y extensiones
    `x-veridicus-limit` y `x-veridicus-owner-only-for-role`.
  - **U2:** tres usuarios de base de datos y el `Job` en `deploy/jobs/` con `backoffLimit: 0`
    (NFR10.16, NFR-U2-09).
  - **U3:** `AccessLog.record` con 500 ms en un punto de guardado (NFR-U3-05), la prueba común de auditoría
    (NFR11.3) y `ActorSystem` con `retention-job`.
  - **U4:** `EthicsSessionPort`, la clave de cancelación de CD-06 y el descarte en la ingesta (NFR-U4-09).
  - **U5:** el tope del cuerpo de sus rutas (`review_body_max_bytes`).
  - **U7:** 500 ms en la exportación con `503 report.export_not_recorded` (NFR-U7-09) y `verify_store`
    con `kubectl exec` (NFR-U7-05).
  - **U9:** el audio conservado sin cifrar en reposo, que borra la retención.
- Reglas AUTONOMIA-01..05 de `team.md` y prohibiciones de `project.md`.

Las pruebas corren en **nivel 0** (cada PR, sin red ni GPU) salvo que la fila diga otra cosa. El **nivel 1**
usa PostgreSQL y Redis reales en contenedor. Todos los datos de prueba son **sintéticos** y llevan el
*canary* «CANARIO-7f3a» donde la fila lo pide. Cada prueba lleva su control negativo. Los comandos están en
`tech-stack-decisions.md` §5.

## 1. Frontera de la unidad (AUTONOMIA-04)

| Componente | Dónde corre | Datos sensibles que maneja | Qué cruza la frontera del clúster |
|---|---|---|---|
| Diálogo, franja, panel, plazo y avisos de bienestar (AnalystConsole) | Navegador del analista | Los turnos ya cargados en M4, para la comparación local de la nota (BR3.7) | Nada nuevo: la consola ya muestra esos turnos; la comparación no envía nada |
| Rutas `/acknowledgements`, `/problem-reports`, `PATCH /sessions/{id}/retention` y `retention_days` de la creación (ConsoleApi) | `session-api`, dentro del clúster | La nota del reporte | Nada |
| Módulo EthicsGovernance (fachada y adaptador de `AccessLog`) | `session-api`, dentro del clúster | La nota y, durante una petición, los turnos de la sesión (`turn_texts`) | Nada: no llama a modelos, al anonimizador ni a internet |
| Tablas `AnalystAcknowledgement`, `AccessLogEntry`, `ProblemReport`, `RetentionChange` y `RetentionAct` | PostgreSQL (CloudNativePG), dentro del clúster | La nota (solo en `ProblemReport`) | Nada |
| `Job` de retención | Pod de la imagen de `session-api`, dentro del clúster | Borra testimonio; su salida y sus actas solo llevan IDs, reglas, conteos y SHA-256 | Nada: sale solo a PostgreSQL y a Redis (U2) |
| Comando de consulta | Contenedor de `session-api`, por `kubectl exec` del humano | La nota de los reportes de problemas (BR7.1) | Su salida llega a la terminal del humano en la máquina local, igual que la consola en su navegador. No se escribe en ningún archivo (NFR10.10) |

## 2. Modelo de amenazas (STRIDE)

| # | Amenaza | STRIDE | Riesgo | Mitigación |
|---|---|---|---|---|
| T1 | Un rol sin permiso reconoce, reporta o reduce un plazo | Elevation of privilege | Medio | NFR10.1 |
| T2 | Una petición forjada desde otra página (CSRF) reduce un plazo o envía un reporte | Spoofing | Medio | NFR10.2 |
| T3 | Un analista reporta o reduce el plazo de una sesión ajena | Elevation of privilege | Medio | NFR10.1 |
| T4 | Un cuerpo enorme o una nota muy larga agota memoria o vuelve lenta la comparación | Denial of service | Bajo | NFR10.3; NFR3.1 |
| T5 | La nota (que puede traer testimonio) llega a los logs, a un Problem Details, a una métrica o al log de PostgreSQL | Information disclosure | Alto | NFR10.5 |
| T6 | La comparación de testimonio filtra el tramo coincidente o deja los turnos en memoria o en caché | Information disclosure | Medio | NFR10.6 |
| T7 | El texto de las reglas de uso se cambia en ejecución o se carga con un YAML inseguro | Tampering | Bajo | NFR10.7 |
| T8 | Se borra o se edita el registro de acceso, un reconocimiento o un acta | Tampering, Repudiation | Alto | NFR11.1, NFR11.2 |
| T9 | El `Job` borra lo que no debe (otra sesión, una tabla no purgable) o se lanza solo | Tampering | Alto | NFR10.11, NFR11.2; NFR10.17 de `reliability-requirements.md` |
| T10 | El `Job` borra con una fecha falsa (`--as-of` en el borrado real) | Tampering | Medio | NFR10.11 |
| T11 | El acta, la salida del `Job` o el registro de acceso llevan texto | Information disclosure | Medio | NFR11.4; NFR10.22 de `observability-requirements.md` |
| T12 | El comando de consulta escribe la nota en un archivo o en el repositorio | Information disclosure | Medio | NFR10.10, NFR12.2 |
| T13 | Un plazo se amplía, o se reduce sin dejar quién y cuándo | Tampering, Repudiation | Medio | NFR11.6, NFR11.3 |
| T14 | Una corrida de una sesión vencida sigue llamando a un modelo después del borrado | Information disclosure | Medio | NFR10.18 de `reliability-requirements.md` |
| T15 | Un texto de U13 muestra una etiqueta de veracidad | Tampering (AUTONOMIA-03) | Bajo | NFR11.5 |
| T16 | Un valor guardado se interpreta como HTML en la consola | Tampering (XSS) | Bajo | NFR10.12 |
| T17 | EthicsGovernance abre un camino de red hacia fuera | Information disclosure | Bajo | NFR1.2, NFR1.3 |
| T18 | Una dependencia con una vulnerabilidad conocida | Tampering | Bajo | NFR10.9 |

## 3. Requisitos

### NFR1 — Soberanía de datos

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR1.1 | nuevo | El diseño declara la frontera por componente. | La tabla de §1 está en este documento y en el README del módulo EthicsGovernance. Un componente nuevo de U13 entra con su fila en el mismo PR | Revisión del PR |
| NFR1.2 | nuevo | EthicsGovernance no abre ningún camino de red hacia fuera del clúster. | Un contrato de import-linter prohíbe que `ethics_governance` (fachada, adaptador, `Job` y comando) importe `httpx`, `requests`, `urllib.request`, `libs.model_gateway` y `libs.anonymizer`, y que importe `console_api` (BR2.1). Un módulo de prueba que los importa hace fallar el contrato | Nivel 0 |
| NFR1.3 | nuevo | El `Job` de retención solo alcanza PostgreSQL y Redis. | El render de `deploy/jobs/` lleva una `NetworkPolicy` de salida solo hacia `veridicus-pg-rw:5432`, el Redis de `veridicus` y DNS (NFR10.16 de U2). La política estática de U2 falla si el `Job` declara otra salida | Nivel 0 (política de manifiestos) |

### NFR10 — Seguridad de la aplicación

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR10.1 | nuevo | Cada ruta de U13 aplica su matriz de roles y la propiedad de la sesión en ConsoleApi (BR1.7, BR3.3, BR3.4, BR4.4; ADR-009). | **`POST /acknowledgements`:** solo `analista`; `admin` e `investigador` → `403` `auth.forbidden`. **`POST /problem-reports`:** `analista` y `admin`; `investigador` → `403`; con sesión, un analista que no es el dueño recibe el mismo `403` o `404` que la ruta de la sesión. **`PATCH /sessions/{id}/retention`:** el analista dueño o `admin`; otro analista y el `investigador` → `403`. Sin cookie: `401`. Cada rechazo deja 0 filas y no llama a `AccessLog`. Orden de los controles: autenticación, rol, CSRF, tope del cuerpo, esquema y propiedad | Nivel 1 (una prueba por celda) |
| NFR10.2 | nuevo | Las tres rutas que escriben exigen el token CSRF (BR1.3, BR3.3, BR4.4). | Sin `X-CSRF-Token` y con el de otra sesión web: `403` `auth.csrf`, 0 filas, y el cuerpo no se lee | Nivel 1 |
| NFR10.3 | nuevo | Toda entrada de U13 tiene un tope de C25, y pasarlo responde `413` (BR3.5; NFR-U13-01, NFR-U13-02). | **Nota:** hasta `problem_report_note_max_chars` = 2 000 caracteres, contados en puntos de código. Con 2 001 (también con caracteres de 4 bytes) → `413` `limits.exceeded` sin filas; la consola deshabilita «Enviar» antes. **Cuerpo:** en las tres rutas, el servidor deja de leer el cuerpo JSON al pasar `ethics_body_max_bytes` = 32 768 bytes y responde `413` `limits.exceeded` sin filas. El peor caso válido cabe: 2 000 caracteres escapados como `\uXXXX\uXXXX` suman 24 000 bytes más los campos. Una variable de entorno solo puede bajar estas cifras. **Pruebas:** nota de 2 000 y 2 001; cuerpo de 32 768 y 32 769 bytes; `Content-Length` falso; cuerpo por trozos | Nivel 0 y nivel 1 |
| NFR10.4 | nuevo | Toda entrada se valida con su esquema en la frontera (BR1.3, BR3.1, BR3.4, BR4.1). | `category` es uno de los seis valores; `session_id` y `suggestion_id` son UUID; `retention_days` es un entero entre `retention_min_days` y `retention_max_days`; `text_version` cumple `^[0-9]+\.[0-9]+\.[0-9]+$`; los cuerpos rechazan campos adicionales. Fuera de eso: `422` con el `code` de §9 del Functional Design y 0 filas. Una nota en blanco (medida con `str.strip()`, que incluye U+00A0 y U+3000) se guarda nula. Prueba de propiedades (Hypothesis) con días negativos, decimales, cadenas y `null` | Nivel 0 y nivel 1 |
| NFR10.5 | nuevo | La nota nunca sale de su columna (BR3.9, FR1.3, NFR10 de requirements). | Con una nota que lleva el *canary*, se provocan el camino feliz, un `413`, un `422`, un `503` (base caída) y una violación de `CHECK` en la base. En todos: 0 coincidencias del *canary* en los logs capturados (aplicación, `uvicorn.access` y `uvicorn.error`), en las respuestas de error, en las métricas expuestas y en el log del contenedor de PostgreSQL de la prueba. Los parámetros van enlazados en el servidor (psycopg 3 sin `ClientCursor`) y PostgreSQL no registra parámetros en los errores (NFR-U13-12). El manejador único registra solo `code`, `problem_report_id`, `session_id`, `suggestion_id`, `category` y `testimony_warning` | Nivel 1 |
| NFR10.6 | nuevo | La comparación de testimonio no filtra ni guarda turnos (BR3.6, BR3.7). | La respuesta de `POST /problem-reports` lleva solo `problem_report_id` y `testimony_warning`: nunca el tramo coincidente, el turno ni la nota. `turn_texts` devuelve un iterador que se consume dentro de la petición y no se guarda en ninguna caché ni variable de módulo (prueba que, tras la petición, no encuentra el texto de un turno con *canary* en `gc.get_objects()` del proceso de prueba). En la consola, la comparación es una función pura sobre los turnos ya cargados y no hace peticiones (Vitest cuenta 0) | Nivel 1 y Vitest |
| NFR10.7 | nuevo | El texto de las reglas de uso es de solo lectura y se carga con el cargador seguro de U1 (BR1.1). | `contracts/integrity/usage-rules.v1.yaml` se lee con los cargadores de `veridicus_contracts` (YAML seguro, sin claves duplicadas) al arrancar. Si falta, no valida o no trae exactamente tres puntos, `session-api` no arranca y el log nombra el archivo, nunca su contenido (E9). Ninguna ruta lo escribe (NFR10.8 de U1). Se sirve desde la imagen, de solo lectura | Nivel 0 |
| NFR10.8 | nuevo | Todo error es Problem Details con un `code` estable del catálogo y un `detail` en español. | Cada `401`, `403`, `404`, `413`, `422` y `503` de las rutas de U13 valida contra `Problem` de C1 y usa un `code` del catálogo de U1: `auth.*`, `validation.invalid_request`, `limits.exceeded`, `ethics.text_version_outdated`, `problem_report.ids_mismatch`, `retention.above_maximum`, `retention.below_minimum`, `retention.cannot_extend` y `system.unavailable`. El `detail` sale de una plantilla del catálogo de mensajes y nunca repite un valor de la petición | Nivel 1 |
| NFR10.9 | nuevo | Dependencias fijadas y auditadas. | `services/session-api/uv.lock` y `frontend/package-lock.json` con *hashes*; `pip-audit` y `npm audit --audit-level=high` sin hallazgos `HIGH` o `CRITICAL` con corrección; Trivy sobre la imagen de `session-api`, que también usa el `Job` | CI |
| NFR10.10 | nuevo | El comando de consulta es de solo lectura, acotado y no deja copias (BR7.1, BR7.2; NFR-U13-09). | Corre con `kubectl exec` en el contenedor `session-api`, con `veridicus_app`, en una transacción `READ ONLY` (un `INSERT` dentro de ella falla). Devuelve como mucho `--limit` filas, 1 000 por defecto y 10 000 como máximo, ordenadas por hora descendente, y avisa con `truncated: true` si hay más. Escribe solo en la salida estándar: no tiene opción de archivo de salida ni abre archivos en escritura (prueba con `open` en modo escritura sustituido por una función que falla). El OpenAPI no tiene rutas de lectura del registro, de los reportes ni de las actas (prueba de nivel 0) | Nivel 0 y nivel 1 |
| NFR10.11 | nuevo | El `Job` de retención solo corre cuando lo lanza el humano, con su usuario y su fecha real (BR5.1, BR5.3; AUTONOMIA-01). | (a) El manifiesto vive en `deploy/jobs/`, nunca es un `CronJob` y ningún *workflow* ni *script* lo aplica (comprobación estática de U2, E49). (b) Su conexión usa `veridicus_retention` desde un `Secret` que crea el humano, por `secretKeyRef`; la prueba de nivel 1 comprueba `current_user`. (c) `--as-of` sin `--dry-run` termina con código 2 antes de abrir la base (E44). (d) El reloj simulado de las pruebas se inyecta en el código y no existe ningún argumento ni variable que lo cambie en el borrado real | Nivel 0 y nivel 1 |
| NFR10.12 | nuevo | La consola no interpreta como HTML ningún texto de U13. | Los componentes de U13 no usan `dangerouslySetInnerHTML` (`react/no-danger` como error). Una prueba Vitest dibuja el panel con una nota `<img src=x onerror=alert(1)>` y el diálogo con un punto de reglas con el mismo valor (*fixture* del componente) y comprueba que aparecen como texto | Vitest |

NFR10.13–NFR10.21 están en `reliability-requirements.md` y NFR10.22–NFR10.24 en
`observability-requirements.md`.

### NFR11 — Integridad y auditoría

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR11.1 | nuevo | Las tablas `history` de U13 son de solo inserción para la aplicación (BR2.4, BR9.1; AC15.6.2). | Con `veridicus_app`, un `UPDATE` y un `DELETE` sobre `AnalystAcknowledgement`, `AccessLogEntry`, `RetentionChange` y `RetentionAct` fallan con permiso denegado; sobre `ProblemReport` también (solo `SELECT` e `INSERT`). Lo comprueba la prueba común de auditoría de U3, que descubre las tablas por su marca (E16) | Nivel 1 |
| NFR11.2 | nuevo | `veridicus_retention` solo borra lo purgable y solo inserta actas (BR9.2, A-2). | Con `veridicus_retention`: `DELETE` funciona en `ProblemReport` y `RetentionChange` y falla en `AnalystAcknowledgement`, `AccessLogEntry` y `RetentionAct` (E48); `UPDATE` falla en las cinco; `INSERT` solo funciona en `RetentionAct`. Tras el `Job`, las filas de `AccessLogEntry` y `RetentionAct` de la sesión borrada siguen (BR5.10) | Nivel 1 |
| NFR11.3 | nuevo | Toda fila de U13 guarda quién y cuándo (FR1.3, AC8.4.1). | `actor_user_id` y `at` son `NOT NULL` en `AnalystAcknowledgement`, `AccessLogEntry` y `RetentionChange`; `reported_by` y `reported_at` en `ProblemReport`; `executed_at` y `actor_system = 'retention-job'` en `RetentionAct`. La hora la pone el servidor. Un `INSERT` con el actor o la hora nulos falla | Nivel 1 |
| NFR11.4 | nuevo | El acta y el registro de acceso no tienen texto y no dependen de las filas que nombran (BR2.2, BR5.7, A-3). | Una prueba sobre la migración falla si `AccessLogEntry` o `RetentionAct` tienen una columna `text` o `varchar` sin `CHECK` de patrón (UUID, `^[a-f0-9]{64}$` o enum) o una clave foránea. `deleted_ids`, `deleted_report_sha256s` y `deleted_audio` se validan antes de insertar con un modelo de tipos cerrados (UUID, hex, booleanos) y un `CHECK` de `jsonb_typeof`. El `CHECK` de `AccessLogEntry` une `export_sha256` con `report_export`. Con datos sintéticos con *canary*, el acta no lo contiene (E47) | Nivel 0 y nivel 1 |
| NFR11.5 | nuevo | Ningún texto de U13 lleva una etiqueta de veracidad (AUTONOMIA-03). | Los textos del diálogo, la franja, el panel, el plazo, los errores y los avisos salen del catálogo de mensajes y entran en el escaneo de vocabulario de la interfaz de U4 con 0 coincidencias. Las reglas de uso se excluyen como `notice_text`, igual que el aviso de VE-01, porque dicen «prueba» (FD-U13-02). Ninguna categoría de reporte es un rótulo de veracidad | Nivel 0 |
| NFR11.6 | nuevo | Un plazo solo baja y la API no borra ni reemplaza nada de U13 (BR4.4, VE-12). | `RetentionChange` lleva `CHECK (to_until < from_until)`. Ampliar o igualar → `422` `retention.cannot_extend` y 0 filas (E32). El OpenAPI no declara `DELETE` ni `PUT` en las rutas de U13, y la única `PATCH` es `/sessions/{id}/retention`, en la lista de U1 (NFR11.1 de U1) | Nivel 0 y nivel 1 |

NFR11.7 y NFR11.8 (atomicidad) están en `reliability-requirements.md`.

### NFR12 — Datos reales fuera del repositorio

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR12.1 | nuevo | Los datos de prueba y de la demo de U13 son sintéticos. | Los turnos, notas y sesiones de las pruebas los genera `services/session-api/tests/fixtures/make_ethics_fixtures.py` con los nombres de `contracts/fixtures/synthetic-names.yaml`. Los ejemplos compartidos de la comparación de testimonio viven en un archivo versionado y sintético (NFR-U13-10). La sesión de la demo de B13 es sintética (FD-U13-09) | Nivel 0 (comprobación `synthetic: true` de U1) |
| NFR12.2 | nuevo | La salida del `Job` y del comando de consulta nunca entra al repositorio. | El runbook (`docs/operacion/`) dice que la salida de `--dry-run` y del comando no se redirige a archivos dentro del repositorio. `gitleaks` y la comprobación de `project.md` siguen en la CI. La salida del `Job` no tiene texto (NFR10.22) y la del comando solo trae notas en `problem_reports` | Revisión del PR del runbook y CI |

### NFR14 — Idioma

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR14.1 | nuevo | Los textos visibles y los `detail` de U13 están en español y salen del catálogo. | Una prueba de nivel 0 falla si un componente de U13 tiene un literal visible fuera del catálogo de mensajes (FD-U13-12) o si un `detail` no es una plantilla del catálogo. Los identificadores siguen el glosario en inglés | Nivel 0 |

## 4. Correspondencia con AUTONOMIA

| Regla | Requisitos de U13 |
|---|---|
| AUTONOMIA-01 | NFR10.11: el `Job` lo lanza el humano y nunca es un `CronJob`. El comando de consulta es de solo lectura por `kubectl exec` (NFR10.10, NFR-U13-08). Las tablas entran por la migración de su PR, que corre como `Job` aparte (`project.md`) |
| AUTONOMIA-02 | Cada requisito nombra su umbral; los comandos están en `tech-stack-decisions.md` §5 |
| AUTONOMIA-03 | NFR11.5 |
| AUTONOMIA-04 | §1; NFR1.1–NFR1.3; NFR10.5, NFR10.6 (la nota y los turnos no salen de su sitio); NFR10.18 (ninguna llamada más tras la retención) |
| AUTONOMIA-05 | No aplica: U13 no emite hallazgos |

## 5. Cumplimiento

- **Reconocimiento (VE-04).** Fila de solo inserción con quién, cuándo y la versión (NFR11.1, NFR11.3). El
  día 90 sigue vigente y el 91 no (BR1.2).
- **Registro de acceso (VE-11, A-3).** Solo IDs y el `export_sha256` de cada exportación; solo inserción;
  sobrevive a la retención (NFR11.1, NFR11.2, NFR11.4).
- **Retención (VE-12, A-2).** El `Job` es la única vía de borrado, con su usuario, en el orden de C24, y
  deja un acta sin texto (NFR10.11, NFR11.2, NFR11.4; `reliability-requirements.md`).
- **Reporte de problemas (VE-15).** La nota puede traer testimonio: no sale de su columna (NFR10.5) y la
  retención la borra con la sesión o por antigüedad (BR5.5, BR5.8).
- **Bienestar (VE-16).** Solo en la consola, sin datos (BR6.3).
- **Repositorio público (`project.md`).** Ningún dato real entra al repositorio (NFR12.1, NFR12.2).

## 6. Riesgos aceptados o transferidos

| Riesgo | Tratamiento |
|---|---|
| **La nota se guarda sin cifrar en reposo** en PostgreSQL | Aceptado, igual que el audio conservado de U9: el volumen es local, los datos de prueba son sintéticos y la retención la borra. Nunca sale de su columna (NFR10.5) |
| **Los respaldos conservan lo que la retención borra.** `scripts/backup-db.sh` (U2) deja un `pg_dump` en `backups/` de la anfitriona | Transferido a U2 (NFR-U13-11): el runbook pide borrar todo respaldo con más de `retention_max_days` días y no hacer respaldos de datos reales fuera de la máquina local |
| **El comando de consulta muestra notas** en la terminal del humano | Aceptado (P7 = A): es lo que pide BR7.1, como la consola muestra los turnos. Sin archivos de salida (NFR10.10) |
| **Una nota con testimonio parafraseado** no activa `testimony_warning` | Aceptado (DD-04): el aviso no rechaza y la comparación es literal por diseño (regla del piloto, solo espacios). La retención la borra igual |
| **Un reporte sin sesión puede traer testimonio durante 90 días** (P6 = A) | Se decide en la aprobación (pregunta 6 del Functional Design). Mitigación: el aviso fijo de BR3.8 y el borrado por antigüedad |
| **Un `kubectl exec` fuera del runbook** podría ejecutar otro código en el contenedor | Transferido a U2: el humano es el único con `kubeconfig` y la CI no lo tiene (`team.md`) |

## 7. Precisiones a artefactos ya aprobados (NFR-U13-xx)

No edité ningún artefacto aprobado (regla de `project.md`). En la aprobación decides cuáles se llevan al
original, cada una en su propio commit. Todas salen de las fuentes; no hubo preguntas.

| ID | Artefacto aprobado | Precisión | Origen |
|---|---|---|---|
| NFR-U13-01 | `contract-summary.md` (C25) y U1 (catálogo de límites) | Cifras de U13: `retention_max_days = 90` (`days`), `retention_min_days = 1` (`days`), `acknowledgement_validity_days = 90` (`days`), `testimony_warning_words = 8` (`words`), `problem_report_note_max_chars = 2000` (`chars`), `wellness_reminder_interval_s = 2700` (`s`) y una cifra nueva, `ethics_body_max_bytes = 32768` (`bytes`). Los 2 700 s del recordatorio son una **propuesta** de esta etapa: el repositorio no trae una cifra del protocolo del TG; el entorno puede bajarla para la demostración. Entran por PR de U1 antes del código de B13 | Preguntas abiertas 1 y 2 del Functional Design; FD-U13-03; NFR-U1-07; U5 (tope del cuerpo) |
| NFR-U13-02 | `functional-spec.md` de U13 (§9, «Nota sobre el tope») y `rules.md` (BR3.5) | La nota sobre el tope y el cuerpo sobre `ethics_body_max_bytes` responden **`413`** `limits.exceeded`, no `422` | NFR-U1-03 (P7 = A de U1) |
| NFR-U13-03 | `contract-summary.md` (C1: `/acknowledgements`, `/problem-reports`, `PATCH /sessions/{id}/retention`) | `note` declara `maxLength: 2000` con `x-veridicus-limit: problem_report_note_max_chars`. Las tres rutas documentan el tope del cuerpo (`ethics_body_max_bytes`) y declaran `413` como Problem, además de las respuestas de FD-U13-05 y FD-U13-06 | NFR10.7 de U1; NFR10.3 |
| NFR-U13-04 | `entities.md` (`RetentionJobRun.exit_code`) y `functional-spec.md` (F7) | Código de salida **3** cuando otra ejecución del `Job` ya tiene el bloqueo: termina sin borrar nada ni escribir actas (NFR10.19). Los códigos quedan 0, 1, 2 y 3 | NFR8.6 de U7 («el `Job` no se lanza mientras otra purga corre»); BR5.6 |
| NFR-U13-05 | `rules.md` (BR5.4) y `functional-spec.md` (F7, paso 4.1) | Si la clave de cancelación no se puede escribir en Redis (caído o vencido su plazo de 0,5 s), esa sesión **no se borra**: queda `failed` con `system.unavailable` y el `Job` sigue con las demás (NFR10.18). Así nunca se borra una sesión con una corrida que aún podría llamar a un modelo | BR5.4 («para que no salga ninguna llamada más»); NFR10.11 de U3 |
| NFR-U13-06 | Functional Design de U4 (`InterviewSessionRecord`, `EthicsSessionPort`) | `expired_sessions(as_of)` usa índices sobre `retention_until` y sobre `created_at` para las sesiones de plazo nulo, y devuelve solo IDs y plazos efectivos. `turn_texts(session_id)` devuelve los turnos de los dos papeles en orden, como iterador, dentro del `statement_timeout` de 2 s (NFR3.1, NFR3.10) | FD-U13-08; NFR3.1 |
| NFR-U13-07 | Infrastructure Design de U2 y de U13 (`Job` de retención) | El `Job` corre con el **mismo UID y GID** que el contenedor `session-api`, porque `reports/` y `audio/` son `0700` del proceso y el aprovisionador de Minikube ignora `fsGroup`. Monta los dos PVC en escritura en el nodo único. `activeDeadlineSeconds` ≥ 2 × la ejecución medida en NFR3.6 (propuesta: 3 600 s). Recursos desde NFR3.6 con un 20 % de margen (propuesta: `requests` 250m y 256 MiB; `limits` 1 CPU y 512 MiB). El Secret de `veridicus_retention` lo crea el humano con el *script* de U2 | Pregunta abierta 4 del Functional Design; NFR10.16 de U2; `project.md` (Minikube ignora `fsGroup`) |
| NFR-U13-08 | Infrastructure Design de U2 (`check-no-cluster-apply.sh`, R-09) | La lista de excepciones de solo lectura admite `kubectl exec deploy/veridicus-session-api -c session-api -- python -m session_api.ethics_governance.query …`. El lanzamiento del `Job` de retención nunca está en un *script* | BR7.2; AUTONOMIA-01; NFR-U13-09 |
| NFR-U13-09 | `functional-spec.md` de U13 (F10) y `rules.md` (BR7.1) | El comando corre con `kubectl exec` en el contenedor `session-api`, como `verify_store` de U7, sin `Job` ni rol propio. `--limit` vale 1 000 por defecto y 10 000 como máximo, y la salida lleva `truncated` | Pregunta abierta 5 del Functional Design; NFR-U7-05; tres usuarios de base de U2 |
| NFR-U13-10 | `contract-summary.md` (C8) y U1 | Entra `contracts/integrity/testimony-warning-cases.v1.yaml`, con los ejemplos sintéticos de BR3.6 (8 palabras, 7, dos turnos y espacios distintos) que comparten la prueba del servidor y la de la consola, con `synthetic: true` | BR3.6, BR3.7 («el mismo conjunto de ejemplos»); igual que `speaker-markers.v1.yaml` (FD-U6-08) |
| NFR-U13-11 | Infrastructure Design de U2 (respaldos y runbook) | El runbook de respaldos dice que un respaldo vive como mucho `retention_max_days` días y que con datos reales no sale de la máquina local, para que la retención (VE-12) no quede anulada por una copia | VE-12; §6 |
| NFR-U13-12 | Infrastructure Design de U2 (configuración de CloudNativePG) | `log_parameter_max_length_on_error = 0` y `log_parameter_max_length = 0` en el clúster, para que un error no deje en el log de PostgreSQL la nota ni un turno | NFR10.5; revisión R-07 del NFR Design de U4 |
