# Requisitos de seguridad — U1 contracts

**Insumos.** Flujos F1–F6 de `functional-design/functional-spec.md` (functional-spec) y reglas
BR1.1–BR8.2 de `functional-design/rules.md` (rules) de esta unidad; NFR1–NFR15 de
`inception/requirements-analysis/requirements.md` (requirements); contratos C1–C16 y la tabla
«Datos sensibles por contrato» de `inception/contract-design/contract-summary.md` (contract-summary);
respuestas P1–P6 de `nfr-requirements-questions.md`; prácticas de `team.md` y `project.md`.

Cada requisito hereda el ID del NFR de Inception que detalla (`NFR10.3` detalla NFR10). Las pruebas
corren en **nivel 0** (cada PR, bloquea) salvo que la fila diga otra cosa. Los comandos exactos están
en `tech-stack-decisions.md` §4.

## 1. Alcance y frontera de la unidad (AUTONOMIA-04)

| Componente de U1 | Dónde corre | Qué datos cruzan su frontera |
|---|---|---|
| Archivos de `contracts/` (OpenAPI, AsyncAPI, JSON Schema, catálogos, `Protocol`) | En ningún sitio: son archivos del repositorio | Ninguno; describen datos, no los transportan |
| Suite de validación de nivel 0 | CI (GitHub Actions) y máquina de desarrollo, en CPU y **sin red** | Solo *fixtures* sintéticos (NFR12.1) |
| Generador de tipos TypeScript | *Build* del frontend y CI | Solo los contratos |

U1 no corre dentro ni fuera del clúster y no maneja datos sin anonimizar. Su aporte a AUTONOMIA-04 es
que los contratos no permitan declarar un destino externo (NFR1.1). La sensibilidad de lo que
transporta cada contrato en ejecución es la de la tabla «Datos sensibles por contrato» de
contract-summary: C1, C2, C3 y C5 llevan testimonio, CoT o audio (dato **restringido**); C4, C15 y
C16 solo identificadores y contadores.

## 2. Activos y modelo de amenazas (STRIDE)

Los activos de U1 son la **integridad** de los contratos (todo servicio valida sus fronteras con
ellos), la integridad de la suite que los protege y la ausencia de datos reales en el repositorio.

| # | Amenaza | STRIDE | Impacto si ocurre | Riesgo | Mitigación (requisito) |
|---|---|---|---|---|---|
| T1 | Un cambio de contrato relaja una regla (quita `additionalProperties: false` de C7, añade `is_truthful`, una ruta que escribe el umbral) | Tampering, Elevation | Una alerta sin sus 4 campos o una etiqueta de veracidad llega al analista (AUTONOMIA-03, -05) | Alto | NFR10.1, NFR10.2, NFR10.8, NFR11.3, NFR13.1 |
| T2 | Un *fixture* negativo «pasa por accidente» y deja de proteger su regla | Tampering | La regla queda sin control negativo sin que nadie lo note | Medio | NFR10.10 |
| T3 | Un *fixture* contiene un nombre, cédula o expediente reales | Information disclosure | Dato real publicado en el repositorio y en la CI | Alto | NFR12.1, NFR12.2 |
| T4 | Un `$ref` remoto o una descarga en la suite trae un esquema alterado o falla sin red | Tampering, DoS | Validación no reproducible o envenenada | Medio | NFR10.5, NFR10.9 |
| T5 | Un YAML con etiquetas de objeto o claves duplicadas ejecuta código o sobrescribe en silencio la lista de C8 | Tampering, Elevation | Ejecución de código en la CI o lista de términos recortada | Medio | NFR10.4 |
| T6 | Un `pattern` de un esquema con retroceso catastrófico bloquea a un servicio que valida entrada del usuario | DoS | Un turno o un mensaje cuelga el validador del servicio | Medio | NFR10.6 |
| T7 | Un campo de texto sin límite de tamaño en C1 o en las colas | DoS | Mensajes enormes en Redis o en el juez | Medio | NFR10.7 |
| T8 | Una petición que cambia estado sin cookie de sesión, sin `X-CSRF-Token` o sin rol declarado | Spoofing, Elevation | Una ruta nueva queda abierta o sin control de rol | Alto | NFR10.11, NFR10.12 |
| T9 | Una dependencia de la suite con una vulnerabilidad conocida | Tampering | Compromiso de la CI | Bajo | NFR10.9 |
| T10 | Un contrato declara un servidor de modelos externo al clúster | Information disclosure | Testimonio fuera del clúster (AUTONOMIA-04) | Alto | NFR1.1 |

## 3. Requisitos

### NFR1 — Soberanía de datos

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR1.1 | Ningún contrato declara un destino externo al clúster. | Todo `servers[].url` y todo valor por defecto de variable de servidor en `contracts/` es relativo (`/api/v1`) o termina en `.svc.cluster.local[:puerto]`; 0 URL a internet. Control negativo: copia de C14 con `https://api.openai.com`. | Suite, comprobación `servers_internal` |

### NFR10 — Seguridad de la aplicación (fronteras validables)

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR10.1 | Todo cuerpo de petición `application/json` de C1 rechaza campos adicionales. | 100 % de los cuerpos declaran `additionalProperties: false` (BR7.3); control negativo con un cuerpo sin la marca. | Suite |
| NFR10.2 | C6 y C7 son estrictos en todos los niveles; C2–C5 exigen todos sus obligatorios, tipos, longitudes mínimas y rangos, e ignoran solo campos desconocidos. | *Fixtures* E1, E4, E7–E9 rechazados por la regla que nombran (BR2.1, BR2.2, BR3.1, BR4.1, BR4.2); `additionalProperties: false` en cada objeto de C6 y C7. | Suite |
| NFR10.3 | Todo error de C1 es Problem Details con un `code` del catálogo único y un `detail` sin datos sensibles. | 100 % de las respuestas 4xx y 5xx de C1 referencian `#/components/responses/Problem`; todo `code` usado en C1–C5 existe en `errors/error-codes.v1.yaml` (BR7.2, BR3.4). | Suite |
| NFR10.4 | Los YAML de `contracts/` se cargan solo con un cargador seguro que rechaza claves duplicadas. | La suite y el generador usan `ruamel.yaml` en modo `safe` con claves duplicadas prohibidas; 0 llamadas a cargadores inseguros (regla Ruff `S506`); control negativo: un C8 con `terms` repetido falla. | Suite y `ruff check` |
| NFR10.5 | Toda referencia `$ref` resuelve dentro de `contracts/` y la suite corre sin red. | 0 `$ref` con `http://` o `https://`; la suite corre con los sockets bloqueados (`--disable-socket`) y pasa. | Suite |
| NFR10.6 | Ningún `pattern` de un esquema admite retroceso catastrófico. | Cada `pattern` compila como expresión regular y, frente a una entrada adversaria de 10 000 caracteres generada con Hypothesis, responde en menos de 50 ms. | Suite (prueba de propiedades) |
| NFR10.7 | Todo campo de texto libre que viene del usuario tiene longitud máxima en el contrato. | En C1 y C2: `text` de un turno 1–2 000 caracteres, transcripción pegada ≤ 100 000 caracteres, nombre de escenario 1–120 caracteres (valores de las unidades U4 y U6). En C5, `audio_base64` declara el máximo que fije U9 (`VERIDICUS_VOICE_MAX_BYTES`) antes de construirse. La suite falla si un campo de texto de un cuerpo de C1 o de un mensaje de C2 no declara `maxLength`. | Suite |
| NFR10.8 | Ningún contrato permite escribir el umbral; solo viaja como instantánea de lectura entre 0 y 1. | 0 operaciones POST, PUT, PATCH o DELETE con `threshold` o `umbral` en ruta, parámetro o cuerpo (BR7.1, E15); `similarity_threshold` de C2 en [0, 1] (BR2.2, E4). | Suite |
| NFR10.9 | Las dependencias de la suite y los meta-esquemas copiados están fijados y auditados. | `contracts/uv.lock` con *hashes*; `pip-audit` sin hallazgos `HIGH` o `CRITICAL` con corrección; cada meta-esquema copiado coincide con el SHA-256 de `contracts/vendor/SHA256SUMS`. | CI (`pip-audit`) y suite |
| NFR10.10 | Cada *fixture* negativo falla por la regla que declara. | Todo *fixture* `reject` declara `reject_reason` con un ID de regla; la suite falla si el rechazo ocurre por otra causa o no ocurre (F1 paso 3). Cada regla BR1.1–BR8.2 que se prueba en nivel 0 tiene al menos un *fixture* positivo y uno negativo. | Suite |
| NFR10.11 | Toda operación de C1 exige la cookie de sesión y toda petición que cambia estado exige `X-CSRF-Token`. | La seguridad global de C1 es `sessionCookie` y solo `POST /auth/login` declara `security: []` (en C16, `/healthz` y `/readyz` son públicas dentro del clúster). Toda operación POST o PATCH, salvo `/auth/login`, referencia el parámetro `CsrfToken` (`minLength: 32`). | Suite |
| NFR10.12 | Toda operación de C1 que cambia estado declara qué roles la ejecutan. | Toda operación POST o PATCH, salvo `/auth/login` y `/auth/logout`, declara `x-veridicus-roles` con valores del enum `Role`. La prueba de cada celda de la matriz de roles (FR1.2) la hace U3. | Suite |

### NFR3 — Interfaz no bloqueante

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR3.1 | Las operaciones de C1 que ponen trabajo de IA en cola responden sin esperarlo. | `POST /sessions/{id}/turns`, `/transcript`, `/turns/{n}/retry`, `/voice-turns`, `POST /scenarios` y `/scenarios/{id}/versions` declaran `202` como única respuesta 2xx. | Suite |

### NFR11 — Integridad y auditoría

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR11.1 | La API no ofrece borrar ni reemplazar registros. | C1 no declara ninguna operación DELETE ni PUT; la única PATCH es `/users/{user_id}`. Las correcciones crean versiones (FR2.4, FR7.5). | Suite |
| NFR11.2 | Toda fecha de los contratos tiene una sola forma, para que el SHA-256 del reporte sea reproducible. | Todo campo `date-time` cumple `AAAA-MM-DDTHH:MM:SSZ` y es una fecha real (BR8.1, E16). | Suite |
| NFR11.3 | Ningún contrato lleva campos ni rótulos de veracidad (AUTONOMIA-03). | 0 nombres de propiedad que coincidan con `categories_forbidden_in_schemas` o con un término de C8 (BR3.3); enum de tres calificaciones en C1, C3 y C6 (BR3.2); C8 1.0.0 con exactamente los 9 términos (BR5.1); exactamente tres rótulos de resultado (BR6.1–BR6.3). | Suite |

### NFR12 — Datos sintéticos

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR12.1 | Ningún *fixture* contiene datos reales (BR1.6, P4 = A). | Cada *fixture* declara `synthetic: true` y la lista `mentions` de personas y lugares que nombra; cada mención existe en `contracts/fixtures/synthetic-names.yaml` y aparece en el texto. La suite rechaza en los campos de texto una secuencia de 6 a 10 dígitos (cédula) y una de 23 dígitos con o sin guiones o espacios entre grupos (radicado judicial). Controles negativos: una mención fuera del catálogo, una cédula y un radicado inventados. | Suite |
| NFR12.2 | El repositorio no contiene secretos. | `gitleaks` sin hallazgos sobre `contracts/` (pre-commit y CI, team-practices). | CI |

### NFR13 — Calidad del código de la suite

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR13.1 | Los módulos de comprobación de reglas son módulos guardia (P5 = A). | 100 % de ramas en `contracts/src/veridicus_contracts/checks/`; 80 % de líneas en el resto del paquete; exclusiones solo en la configuración y justificadas en el PR. | `pytest --cov-branch` + `coverage report --fail-under=100` |
| NFR13.2 | Las interfaces en proceso C10–C12 y el código de la suite pasan tipos estrictos y *lint*. | `mypy --strict` y `ruff check` (reglas `S` incluidas) sin errores. | CI |

### NFR2 — CPU primero

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR2.1 | La suite de U1 corre en CPU, sin red, base de datos ni Redis, y en tiempo acotado (P6 = A). | Termina en ≤ 60 s en la máquina de desarrollo y en la CI; el paso de CI corre bajo `timeout 60` y falla si se agota. | CI |

### NFR14 — Idioma

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR14.1 | Nombres técnicos en inglés y textos visibles en español, sin dos traducciones del mismo término. | Propiedades, parámetros y métricas en ASCII `snake_case`; `code` en `dominio.motivo`; los valores de enum que fija el PRD (calificaciones, roles) y los rótulos quedan en español exactamente como en el contrato. | Suite |

### NFR15 — Observabilidad (contrato de métricas)

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR15.1 | Las métricas de C15 no exponen texto. | Todo nombre empieza por `veridicus_`; cada etiqueta es un identificador o un valor de enum declarado (BR8.2); 0 etiquetas de texto libre. | Suite |

## 4. Correspondencia con AUTONOMIA-01..05

| Regla | Qué aporta U1 | Requisitos |
|---|---|---|
| AUTONOMIA-01 | Ningún contrato ni la suite aplican cambios al clúster; la suite solo lee archivos. | NFR2.1, NFR10.5 |
| AUTONOMIA-02 | Cada requisito nombra su comprobación y su umbral; el comando de nivel 0 está fijado. | Todas; comandos en `tech-stack-decisions.md` §4 |
| AUTONOMIA-03 | Sin campos ni rótulos de veracidad; sin ruta que escriba el umbral. | NFR10.8, NFR11.3 |
| AUTONOMIA-04 | Ningún destino externo en los contratos; frontera de U1 declarada (§1). | NFR1.1 |
| AUTONOMIA-05 | La alerta exige sus cuatro campos y el resultado no trae alertas por debajo del umbral. | NFR10.2, NFR10.10 |

## 5. Riesgos residuales

| Riesgo | Por qué queda | Tratamiento |
|---|---|---|
| Un nombre real que el autor no declara en `mentions` | Detectar un nombre real sin declararlo no es exacto (P4) | Revisión del autor en el PR; prohibición de `project.md` |
| Flexiones no listadas en C8 («mienten», «falsedad») | Lista 1.0.0 de 9 términos (P2 de Functional Design, escenario E14) | Ampliar por PR con su control negativo |
| La copia de los meta-esquemas queda vieja | P2 = A eligió no depender de herramientas de Node | Actualizar la copia por PR con su SHA-256 nuevo |
| Clasificar un cambio como aditivo o incompatible | Lo decide el autor (BR1.5) | La suite vuelve a aceptar los *fixtures* anteriores en un cambio menor (BR1.3) |

## 6. Precisiones a artefactos ya aprobados

No edité ningún artefacto aprobado; decides en la aprobación si se actualizan.

| Artefacto | Qué precisa | Origen |
|---|---|---|
| `contract-design/contract-summary.md` (C1) | Cuatro respuestas `409` están descritas sin Problem Details, lo que NFR10.3 (BR7.2) rechazaría: `/turns/{number}/retry` (`turn.not_in_error`), `/suggestions/{id}/decisions` (`review.*`), `/reports/{id}/download` (`report.integrity_mismatch`) y `/questions/{id}/audio`. U1 las escribirá con `$ref` a Problem. La última no tiene `code` en el catálogo; hace falta uno nuevo (por ejemplo `question.not_approved`) cuando U9 se construya. | NFR10.3 |
| `contract-design/contract-summary.md` (C1 y catálogo de `code`) | Las unidades U4 y U6 fijaron límites y códigos que el contrato aún no declara: `maxLength` de turno (2 000), transcripción (100 000) y nombre de escenario (120), respuestas `422` y los `code` `turn.too_long` y `transcript.too_large`. U1 los incluye en la versión 1.0.0 de C1 y del catálogo. | NFR10.7 |
| `contracts/functional-design/functional-spec.md` (§1 inventario) | Se añaden a `contracts/`: `fixtures/synthetic-names.yaml`, `vendor/` con los meta-esquemas y su `SHA256SUMS`, y el generador de tipos TypeScript. | P2, P3, P4 |
| `contracts/functional-design/functional-spec.md` (F1 paso 6) | El comando exacto de nivel 0 queda en `tech-stack-decisions.md` §4 (hallazgo R-07 de Functional Design). | AUTONOMIA-02 |
