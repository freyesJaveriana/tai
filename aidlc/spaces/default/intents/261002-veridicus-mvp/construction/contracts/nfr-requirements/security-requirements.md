# Requisitos de seguridad — U1 contracts

**Revisión 2 (2026-11-22), segunda pasada por el cambio 01 (DT27), la adenda 02 y el Functional Design
vigente de U1.** Sustituye a la revisión 1 del 2026-10-03, que queda en el historial de Git.
- **IDs.** Los requisitos conservan su ID. Ninguno se retira en esta pasada. Lo nuevo toma el número
  siguiente de su grupo: NFR1.2–NFR1.4, NFR2.2, NFR10.13–NFR10.16, NFR11.4–NFR11.5 y NFR12.3. Cada fila
  dice si **se mantiene**, **cambia** o es **nuevo**.
- **Respuestas de esta pasada:** P7 = A (`limits.exceeded` siempre `413`) y P8 = A (subpaquete
  `contracts/ts/` en el mismo *job*).
- **Revisión 1:** se cierran sus hallazgos R-01 a R-05 (`reviews/review-01.md`).

**Insumos.**
- Flujos F1–F9 de `functional-design/functional-spec.md` (functional-spec, revisión 3) y reglas
  BR1.1–BR12.3 de `functional-design/rules.md` (rules) de esta unidad, con su tabla FD-U1-01 a FD-U1-14.
- NFR1–NFR15 de `inception/requirements-analysis/requirements.md` (requirements, revisión 3; NFR9
  «Retirado») y VE-01, VE-02, VE-05 y VE-14 de `requirements-adenda-02.md`.
- C1–C25, las reglas de propiedad y la tabla «Datos sensibles por contrato» de
  `inception/contract-design/contract-summary.md` (contract-summary, revisión 3).
- Lo que piden a U1 los Functional Design de U3–U13 aprobados el 2026-11-22: sus tablas FD-Ux y sus
  preguntas para NFR.
- Respuestas P1–P8 de `nfr-requirements-questions.md` y prácticas de `team.md` y `project.md`.

Cada requisito hereda el ID del NFR de Inception que detalla (`NFR10.3` detalla NFR10). Las pruebas corren
en **nivel 0** (cada PR, bloquea) salvo que la fila diga otra cosa. Los comandos exactos están en
`tech-stack-decisions.md` §4.

## 1. Alcance y frontera de la unidad (AUTONOMIA-04)

| Componente de U1 | Dónde corre | Qué datos cruzan su frontera |
|---|---|---|
| Archivos de `contracts/` (OpenAPI, AsyncAPI, JSON Schema, catálogos, `Protocol`, copia de C6) | En ningún sitio: son archivos del repositorio | Ninguno; describen datos, no los transportan |
| Paquete `veridicus-contracts`, con `profiles.validate`, `limits.load`, `registry` y la huella JCS | En el proceso de quien lo importa: `session-api`, `semantic-agent`, `anonymizer-proxy` y la CLI | Ninguno propio: son funciones puras, sin E/S (BR9.8, BR11.1, BR12.3) |
| Suite de nivel 0 en Python y su mitad TypeScript (`contracts/ts/`, P8 = A) | CI (GitHub Actions) y máquina de desarrollo, en CPU y **sin red** después de instalar | Solo *fixtures* sintéticos (NFR12.1) |
| Paso del paquete (F9) | CI, en un entorno limpio | Instala dependencias desde PyPI; no transporta datos |

U1 no corre dentro ni fuera del clúster y no maneja datos sin seudonimizar. A AUTONOMIA-04 aporta cuatro
cosas:
- ningún contrato declara un destino de internet (NFR1.1);
- el `Protocol` `AnonymizingProvider` es la única puerta a un destino externo (NFR1.2);
- la petición del proxy no deja elegir clave ni proveedor (NFR1.3);
- el reporte de la CLI, que sale del clúster hacia el investigador, no admite texto libre (NFR1.4,
  NFR12.3).

La sensibilidad de lo que transporta cada contrato en ejecución sale de la tabla de contract-summary:

| Contratos | Dato que transportan | Clase |
|---|---|---|
| C1, C2, C3, C5, C17, C20, C21 | Testimonio, hallazgos y citas, audio o CoT | **Restringido** (dentro del clúster o del proceso) |
| C22 | Solo texto seudonimizado; U1 no guarda copia | Sale del clúster |
| C19 | Ninguno: metadatos y cifras | Sale del clúster sin texto |
| C15, C16, C23, C24, C25 | Identificadores, cifras y configuración | Interno |

## 2. Activos y modelo de amenazas (STRIDE)

Los activos de U1 son tres:
- la **integridad** de los contratos, porque todo servicio valida con ellos sus fronteras;
- la integridad de la suite y de las funciones puras que los protegen;
- la ausencia de datos reales en el repositorio.

| # | Amenaza | STRIDE | Impacto si ocurre | Riesgo | Mitigación (requisito) |
|---|---|---|---|---|---|
| T1 | Un cambio de contrato relaja una regla: quita `additionalProperties: false` de C7, añade `is_truthful` o abre una ruta que escribe configuración | Tampering, Elevation | Una sugerencia sin sus 5 campos o una etiqueta de veracidad llega al analista (AUTONOMIA-03, -05) | Alto | NFR10.1, NFR10.2, NFR10.8, NFR11.3, NFR13.1 |
| T2 | Un *fixture* negativo «pasa por accidente» y deja de proteger su regla | Tampering | La regla queda sin control negativo sin que nadie lo note | Medio | NFR10.10 |
| T3 | Un *fixture* o un ejemplo versionado contiene un nombre, una cédula o un expediente reales | Information disclosure | Dato real publicado en el repositorio y en la CI | Alto | NFR12.1, NFR12.2 |
| T4 | Un `$ref` remoto o una descarga en la suite trae un esquema alterado, o la suite falla sin red | Tampering, DoS | Validación no reproducible o envenenada | Medio | NFR10.5, NFR10.9 |
| T5 | Un YAML con etiquetas de objeto o claves duplicadas ejecuta código o recorta en silencio la lista de C8 | Tampering, Elevation | Ejecución de código en la CI o lista de términos incompleta | Medio | NFR10.4 |
| T6 | Un `pattern` de un esquema con retroceso catastrófico | DoS | Un turno o un mensaje cuelga el validador del servicio | Medio | NFR10.6 |
| T7 | Un campo de texto o un cuerpo sin límite, o con un límite distinto del catálogo | DoS | Mensajes enormes en Redis, en el proxy o en el juez | Medio | NFR10.7, NFR10.14 |
| T8 | Una petición que cambia estado sin cookie, sin `X-CSRF-Token` o sin rol declarado | Spoofing, Elevation | Una ruta nueva queda abierta o sin control de rol | Alto | NFR10.11, NFR10.12 |
| T9 | Una dependencia de Python o de npm con una vulnerabilidad conocida | Tampering | Compromiso de la CI | Bajo | NFR10.9 |
| T10 | Un contrato declara un servidor externo al clúster | Information disclosure | Testimonio fuera del clúster (AUTONOMIA-04) | Alto | NFR1.1 |
| T11 | Alguien edita aquí la copia del contrato común | Tampering | Veridicus y `sistema` dejan de hablar el mismo contrato | Alto | NFR11.4 |
| T12 | El `Protocol` del anonimizador gana un segundo método o una importación, y abre otro camino a un destino externo | Elevation, Information disclosure | Una llamada externa sin seudonimizar | Alto | NFR1.2 |
| T13 | La petición del proxy acepta un destino o una clave elegidos por quien llama | Elevation, Information disclosure | Una llamada a un proveedor no aprobado | Alto | NFR1.3 |
| T14 | El reporte de la CLI admite una frase del testimonio | Information disclosure | Testimonio en la consola del investigador o en el repositorio principal | Alto | NFR1.4, NFR12.3 |
| T15 | Una variable de entorno sube una cifra de límite, o la validación de perfiles acepta una clave fuera del prefijo | Elevation | Tamaños o plazos fuera de lo aprobado; una clave ajena se usa | Medio | NFR10.13, NFR10.14 |
| T16 | Las mitades Python y TypeScript de la validación dan veredictos distintos | Tampering | La consola acepta lo que el servidor rechaza, o al revés | Medio | NFR10.15, NFR10.16 |

## 3. Requisitos

### NFR1 — Soberanía de datos

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR1.1 | cambia | Ningún contrato declara un destino externo al clúster. | Todo `servers[].url` y todo valor por defecto de variable de servidor en `contracts/` cumple una de estas formas: relativo (`/api/v1`), nombre corto de servicio `http://veridicus-<nombre>:<puerto>` (C21) o un *host* que termina en `.svc.cluster.local[:puerto]`. 0 URL a internet; C22 no se copia a `contracts/` (precisión NFR-U1-06). Control negativo: copia de C21 con `https://api.openai.com`. | Suite, comprobación `servers_internal` |
| NFR1.2 | nuevo | `AnonymizingProvider` es la única puerta a un destino externo (BR9.9). | El `Protocol` declara solo `generate(GenerateRequest) -> GenerateResult`. `model_calls` no importa nada fuera de `veridicus_contracts`. Existen `ModelCallError` y sus 5 subclases; `ContentBlocked`, `Timeout`, `ProviderError` e `InvalidOutput` llevan el `ModelCall` de la llamada, y `AnonymizerUnavailable` no lo lleva (FD-U10-04). Controles: un doble con solo `generate` pasa mypy estricto y uno sin `generate` no; un `check_ready()` añadido pone la suite en rojo. | Suite y `mypy --strict` |
| NFR1.3 | nuevo | La petición a `anonymizer-proxy` (C21) no deja elegir clave, proveedor ni modelo. | El cuerpo de `/v1/generate` y su respuesta declaran `additionalProperties: false` en todos los niveles. Un *fixture* con `destination` o con `api_key_ref` se rechaza. `role` cumple el patrón de BR9.1, `profile_sha256` tiene 64 hex, y el cuerpo declara `x-veridicus-limit: anonymizer_request_max_bytes` (NFR10.7). | Suite |
| NFR1.4 | nuevo | El reporte de la CLI (C19), que sale del clúster, no transporta testimonio. | Lo cubre NFR12.3, que fija el criterio y los controles. | Suite |

### NFR2 — CPU primero

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR2.1 | cambia | Las dos mitades de la suite corren en CPU, sin red, base de datos ni Redis, y en tiempo acotado (P6 = A, P8 = A). | La suite Python termina en ≤ 60 s bajo `timeout 60` y la mitad TypeScript en ≤ 60 s bajo su propio `timeout 60`, en la máquina de desarrollo y en la CI. La instalación (`uv sync`, `npm ci`) y las auditorías (`pip-audit`, `npm audit`) son pasos con red, fuera de esos límites (R-04 b de la revisión 1). | CI |
| NFR2.2 | nuevo | El paquete `veridicus-contracts` se construye y se usa en un entorno limpio (F9, BR12.1). | El paso del paquete construye la distribución, la instala en un entorno nuevo sin Redis, Kubernetes ni base de datos, y comprueba que `veridicus_contracts` se importa y que cada esquema y catálogo de la tabla de rutas se lee como dato. Ningún módulo del repositorio importa `contracts.` como nombre de primer nivel (E32). Los *fixtures* de C7, C1 y C19 validan sin red desde el paquete instalado (BR12.3). Plazo: ≤ 180 s bajo `timeout 180` (precisión NFR-U1-02). | CI |

### NFR3 — Interfaz no bloqueante

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR3.1 | cambia | Las operaciones de C1 que ponen trabajo de IA en cola responden sin esperarlo. | La suite guarda la lista de rutas de C1 v2 que publican en C2 o en C5: turno, bloque pegado, reintento de corrida, modo final, «Reanudar análisis» y turno de voz. Cada una declara `202` como única respuesta 2xx. Salen las rutas de escenarios (cambio 01). | Suite |

### NFR10 — Seguridad de la aplicación (fronteras validables)

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR10.1 | cambia | Todo cuerpo de petición de C1 rechaza campos adicionales, también los `multipart/form-data`. | El 100 % de los cuerpos `application/json` y de los objetos `multipart/form-data` declaran `additionalProperties: false` (BR7.3). Todo campo no binario de un `multipart` declara `maxLength` (R-01 de la revisión 1). Control negativo: un cuerpo sin la marca. | Suite |
| NFR10.2 | cambia | Los contratos estrictos lo son en todos los niveles; los sobres de cola exigen sus obligatorios e ignoran solo campos desconocidos. | Son estrictos C6 (la copia, sin editarla), C7, la configuración efectiva de C18, C19 con `model-call.v1.yaml` y C21: cada objeto declara `additionalProperties: false` o `unevaluatedProperties: false` (BR1.4). Los *fixtures* E1, E5, E7–E9, E19, E20 y E35 se rechazan por la regla que nombran (BR2.1, BR3.1, BR3.2, BR3.5, BR3.6, BR4.1, BR4.4). C2, C3 y C5 exigen tipos, obligatorios y rangos (BR1.3). | Suite |
| NFR10.3 | cambia | Todo error es Problem Details con un `code` del catálogo único, una sola clase y un solo estado HTTP por `code`. | El 100 % de las respuestas 4xx y 5xx de C1 referencian `#/components/responses/Problem`. Todo `code` usado en C1, C2, C3, C5, C17 o C21 existe en `errors/error-codes.v2.yaml` (BR7.2, BR3.4). Cada `code` tiene exactamente una clase de excepción sin lógica en `libs/` (BR7.4) y un solo estado HTTP declarado en el catálogo. `limits.exceeded` es `413` (P7 = A, precisión NFR-U1-03). Una ruta que declara un `code` con un estado distinto del catálogo pone la suite en rojo. Entran los códigos que piden FD-U3-02, FD-U3-03, FD-U4-05, FD-U4-07, FD-U5-01, FD-U6-01, FD-U6-02, FD-U7-04, FD-U7-05, FD-U8-02, FD-U9-02, FD-U12-03, FD-U12-04 y FD-U13-04, cada uno en el PR de U1 que precede al código de su unidad. | Suite |
| NFR10.4 | cambia | Los YAML de `contracts/` se cargan solo con un cargador seguro que rechaza claves duplicadas. | Python: `ruamel.yaml` en modo `safe`, YAML 1.2 y claves duplicadas prohibidas, solo desde `loaders.py`. Una prueba AST falla ante `typ='unsafe'`, ante `typ='rt'` fuera de `loaders.py` o ante cualquier otro cargador. Así `S506` deja de usarse como evidencia (R-03 de la revisión 1). TypeScript: el paquete `yaml` con `uniqueKeys: true` y sin etiquetas personalizadas. Control negativo en las dos mitades: un C8 con un término repetido falla. | Suite y prueba AST |
| NFR10.5 | cambia | Toda referencia entre esquemas usa el `$id` de destino y la suite corre sin red. | Todo `$ref` entre archivos es una ruta absoluta del `$id` de destino, como `/veridicus/contracts/analyzer/v1/salida#/$defs/cita` (BR12.3). Lo resuelven solo `veridicus_contracts.registry` y el `addSchema` de ajv, con la base `https://veridicus.invalid/`. 0 `$ref` con otro esquema `http(s)`. La suite Python corre con `--disable-socket`, y la TypeScript con un *setup* que hace fallar `fetch` y `net.connect`. Control negativo: la forma `contracts/analyzer/v1/salida.schema.json#/$defs/cita` no se resuelve (E36). | Suite |
| NFR10.6 | cambia | Ningún `pattern` admite retroceso catastrófico. | Cada `pattern` está anclado con `^…$`. Una comprobación estática sobre su árbol rechaza cuantificadores anidados y alternativas solapadas bajo un cuantificador. Además, frente a una entrada adversaria de 10 000 caracteres generada con Hypothesis, responde en < 1 s: 20 veces el margen de la revisión 1, para no depender de la carga de la CI (R-04 a). | Suite (estática y de propiedades) |
| NFR10.7 | cambia | Todo campo de texto y todo cuerpo que viene de fuera tiene un tope que es una cifra con nombre de C25. | Todo `maxLength`, `maxItems` o tope de bytes de C1, C2, C5, C19 y C21 lleva `x-veridicus-limit: <nombre de C25>`, y su valor coincide con el del catálogo (cierra R-05 de la revisión 1). Las subidas `multipart` (importación, voz, reporte de la CLI) declaran `x-veridicus-max-bytes: <nombre de C25>` y responden `413` `limits.exceeded` y `415` como Problem (R-01). La suite falla si un campo de texto de un cuerpo de C1, de un mensaje de C2 o C5 o de C21 no declara su nombre. | Suite |
| NFR10.8 | cambia | Ningún contrato permite escribir configuración: perfiles, proveedores, *prompts*, precios ni límites. | 0 operaciones POST, PUT, PATCH o DELETE con esos nombres en la ruta, en un parámetro o en el cuerpo, sin distinguir mayúsculas ni tildes (BR7.1). La lista de excepciones es explícita y lleva su motivo; hoy solo tiene `profile_name` al crear o importar una sesión. Control negativo: E15 (`PUT /profiles`). Sale el umbral de la revisión 1 (cambio 01). | Suite |
| NFR10.9 | cambia | Las dependencias de las dos mitades y los meta-esquemas copiados están fijados y auditados. | `contracts/uv.lock` con *hashes*, sin hallazgos `HIGH` o `CRITICAL` con corrección en `pip-audit`. `contracts/ts/package-lock.json` con `integrity`, sin hallazgos `HIGH` o más con corrección en `npm audit --audit-level=high`. Cada meta-esquema copiado coincide con `contracts/vendor/SHA256SUMS`. | CI y suite |
| NFR10.10 | se mantiene | Cada *fixture* negativo falla por la regla que declara. | Todo *fixture* `reject` declara `reject_reason` con un ID de regla, y la suite falla si el rechazo no ocurre o llega por otra causa (F1 paso 4). Cada regla de nivel 0 de U1 tiene al menos un *fixture* positivo y uno negativo. Quedan fuera BR5.2–BR5.6, que U1 valida solo por su forma (BR5.8) y U11 ejecuta, y BR1.5, BR1.8 y BR12.2, que se comprueban en la revisión del PR. | Suite |
| NFR10.11 | cambia | Toda operación de C1 exige la cookie de sesión, y toda petición que cambia estado exige `X-CSRF-Token`. | La seguridad global de C1 es `sessionCookie`. Solo las rutas de la lista pública declaran `security: []`, cada una con su motivo: `POST /auth/login` y, si apruebas FD-U4-08, `GET /notice`. En C16, `/healthz` y `/readyz` son públicas dentro del clúster. Toda operación POST o PATCH, salvo `/auth/login`, referencia el parámetro `CsrfToken` (`minLength: 32`). | Suite |
| NFR10.12 | cambia | Toda operación de C1 que cambia estado declara qué roles la ejecutan, y las extensiones de seguridad toman solo valores cerrados. | Toda POST o PATCH, salvo `/auth/login` y `/auth/logout`, declara `x-veridicus-roles` con valores de `Role` (`analista`, `admin`, `investigador`). `x-veridicus-owner-only-for-role` toma un valor de `Role` (FD-U13-05). `x-veridicus-access-log` toma uno de `session`, `suggestion` o `report_version` (FD-U3-05). `x-veridicus-owner-only` y `x-veridicus-demo` son booleanos. Cualquier otra extensión `x-veridicus-*` pone la suite en rojo. La prueba de cada celda de la matriz de roles es de U3. | Suite |
| NFR10.13 | nuevo | La validación de perfiles es una función pura que nunca expone una clave. | `profiles.validate(data, *, key_prefix, kind)` no abre archivos, no lee el entorno y no usa la red: la prueba lo comprueba con `open`, `os.environ` y `socket` sustituidos por funciones que fallan. `key_prefix` es obligatorio y no tiene valor por omisión (E39). El esquema no fija el prefijo (E25). Un error nombra el perfil, el papel y el ajuste, y un *canary* sembrado en `api_key_ref` no aparece en el mensaje (BR9.8). Cumple E21–E24, E26 y E38. | Suite |
| NFR10.14 | nuevo | El catálogo de límites (C25) es único, completo y el entorno solo puede bajarlo. | Cada cifra tiene un nombre único, un valor no nulo y una unidad de una lista cerrada: `chars`, `turns`, `bytes`, `s`, `ms`, `deliveries`, `suggestions`, `words`, `ratio`, `days` y `levels`. `limits.load(environ)` aplica solo las `VERIDICUS_LIMIT_<NOMBRE>` presentes. Lanza `LimitsConfigError` si una sube la cifra, si nombra un límite inexistente o si no es un número válido para su unidad: entero en general, decimal solo en `ratio` y `s` (precisión NFR-U1-01). Cumple E33 y E37. Una cifra entra al catálogo por PR de U1 cuando la unidad dueña fija su valor en su NFR (precisión NFR-U1-07). | Suite |
| NFR10.15 | nuevo | La huella JCS tiene una sola implementación por lenguaje, publicada por U1 (FD-U10-12). | `veridicus_contracts.canonical.sha256_jcs(obj)` (RFC 8785) y su par TypeScript en `contracts/ts/` dan, para `effective-config.valid.json`, exactamente la huella esperada del *fixture* (BR9.7). Una prueba de propiedades con 200 objetos generados compara las dos mitades byte a byte. | Suite (las dos mitades) |
| NFR10.16 | nuevo | La mitad TypeScript da los mismos veredictos que la de Python (P8 = A). | ajv (`Ajv2020`, `strict: true`) carga cada esquema de `contracts/` sin error (BR1.9) y resuelve las referencias con la misma base `$id` (BR12.3). Sobre el 100 % de los *fixtures* de los esquemas JSON, el veredicto (aceptar o rechazar) coincide con el de `jsonschema`, y una diferencia pone las dos suites en rojo. | Suite (las dos mitades) |

### NFR11 — Integridad y auditoría

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR11.1 | cambia | La API no ofrece borrar ni reemplazar registros. | C1 no declara ninguna operación DELETE ni PUT. Las PATCH están en una lista explícita, cada una con su motivo: `/users/{user_id}`, `/sessions/{session_id}/analysis` y `/sessions/{session_id}/retention` (FD-U13-05, solo reduce). Una PATCH fuera de la lista pone la suite en rojo. Las correcciones crean versiones (FR2.4, FR7.5). | Suite |
| NFR11.2 | se mantiene | Toda fecha de los contratos propios tiene una sola forma, para que las huellas sean reproducibles. | Todo campo `date-time` de un contrato propio cumple `AAAA-MM-DDTHH:MM:SSZ` y es una fecha real (BR8.1, E16). La copia de C6 no se toca. | Suite |
| NFR11.3 | cambia | Ningún contrato lleva campos ni rótulos de veracidad (AUTONOMIA-03). | 0 nombres de propiedad que coincidan con `categories_forbidden_in_schemas`, o con un segmento igual a un término de C8 (BR3.3). Los enum de C6 son iguales en C1, C7 y C19 (BR3.2). C8 v2 tiene exactamente la lista aprobada, con los términos de VE-02 (BR5.1). Hay exactamente nueve rótulos (BR6.1–BR6.3). El aviso de VE-01 y las reglas de uso quedan fuera del escaneo (BR5.5). | Suite |
| NFR11.4 | nuevo | La copia del contrato común nunca se edita aquí (BR1.7, BR1.8). | F7 corre antes que todo lo demás. `analyzer/v1/SHA256SUMS` tiene exactamente dos líneas, el SHA-256 recalculado de cada esquema coincide con la suya, y los dos declaran `contrato: { const: "1.0.0" }`. Control negativo: E18, un byte cambiado en una `description`. El ancla frente al principal es la revisión humana del PR de copia. | Suite y revisión del PR |
| NFR11.5 | nuevo | Una sugerencia decidida lleva quién y cuándo (BR4.4). | C7 declara las condiciones `if/then`: fuera de `pending` exige `decided_by` y `decided_at`; en `pending` los prohíbe; `dismissed` exige `note` y `edited` exige `reformulation`. Hay un *fixture* negativo por condición (E35). | Suite |

### NFR12 — Datos sintéticos

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR12.1 | cambia | Ningún *fixture*, ejemplo ni caso de escaneo contiene datos reales ni nombres de `sistema` (BR1.6). | Cada *fixture* declara `synthetic: true` y su lista `mentions`. Cada mención está en `contracts/fixtures/synthetic-names.yaml` y aparece en el texto. Aplica también a los ejemplos versionados de `transcript/speaker-markers.v1.yaml` (FD-U6-08), a `integrity/clarification-speech.v1.yaml` (FD-U9-05) y a las `literal_sources` de `integrity/scan-cases.v1.yaml` (BR5.8). Los papeles de prueba son `prueba_a` y `prueba_b`. La suite rechaza en los campos de texto una secuencia de 6 a 10 dígitos (cédula) y una de 23 dígitos con o sin separadores (radicado). | Suite |
| NFR12.2 | se mantiene | El repositorio no contiene secretos. | `gitleaks` sin hallazgos sobre `contracts/`, en pre-commit y en la CI. | CI |
| NFR12.3 | nuevo | El reporte de la CLI no tiene campos de texto libre (BR10.1, BR10.2). | En C19 v2, toda propiedad `string` es `enum`, `const` o un `pattern` sin espacios con tope de 128 caracteres. Se rechazan `report.testimony-in-model.json` y `report.testimony-in-price-table.json`, y los papeles fuera de los tres del analizador (E28, E29). C19 v2 incluye `origin` (FD-U12-07) y la sección opcional `clarifications` solo con enteros (FD-U8-09, precisión NFR-U1-05). Límite declarado: un *canary* de una palabra cabe en un patrón; lo cierra U12 (FD-U1-05, FD-U12-01). | Suite |

### NFR13 — Calidad del código de la suite y del paquete

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR13.1 | cambia | Los módulos de comprobación y las funciones puras son módulos guardia (P5 = A). | 100 % de ramas en `checks/` y en `profiles.py`, `limits.py`, `canonical.py` y `registry.py`, porque protegen AUTONOMIA-03, -04 y -05. 80 % de líneas en el resto del paquete y en `contracts/ts/src/`. Las exclusiones van en la configuración y se justifican en el PR. | `pytest --cov-branch`, `coverage report` y cobertura de Vitest |
| NFR13.2 | cambia | Las interfaces en proceso y el código de las dos mitades pasan tipos estrictos y *lint*. | `mypy --strict` sobre el paquete y sobre los `Protocol` de C10–C13, C23 y C24 (E42, E43); `ruff check` con reglas `S`. En `contracts/ts/`, `tsc --strict --noEmit` y ESLint, todo sin errores. | CI |

### NFR14 — Idioma

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR14.1 | cambia | Nombres técnicos en inglés y textos visibles en español, sin dos traducciones del mismo término. | Las propiedades, los parámetros y las métricas van en ASCII `snake_case`, salvo los bloques de C6 que la regla 8 de contract-summary nombra (CD-05). Todo `code` tiene la forma `dominio.motivo`. Los valores de enum de C6 y los roles quedan en español tal como están en el contrato. | Suite |

### NFR15 — Observabilidad (contrato de métricas)

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR15.1 | cambia | Las métricas de C15 v2 no exponen texto. | Todo nombre empieza por `veridicus_`. Las etiquetas salen de la lista declarada (`state`, `session_id`, `mode`, `outcome`, `error_code`), y cada una es un identificador o un valor de enum (BR8.2). 0 etiquetas de texto libre. | Suite |

## 4. Valores que no se detallan en U1

Cierra R-02 de la revisión 1: cada valor delegado a NFR Requirements queda con su unidad responsable.

| Valor | Dónde se fija | Por qué no aquí |
|---|---|---|
| Cifras de C25: plazos, tamaños, *W*, ventana, plazo de la sesión web | NFR Requirements de la unidad dueña de cada cifra: U3, U4, U5, U6, U7, U9, U10, U11, U12, U13 | contract-summary: U1 nombra y valida la forma; NFR10.14 impide nulos |
| Política de contraseñas | U3 | Es comportamiento en ejecución de IdentityAccess |
| Latencia por turno y *N* de la prueba de humo (NFR3) | U4 y U11 | U1 no corre; aporta solo la forma `202` (NFR3.1) |
| Umbrales de NFR4 y NFR5 | U11 (nivel 2) | U1 solo aporta los campos de `metrics` de C19 |

## 5. Correspondencia con AUTONOMIA-01..05

| Regla | Qué aporta U1 | Requisitos |
|---|---|---|
| AUTONOMIA-01 | Ningún contrato, ni la suite, ni el paso del paquete aplican cambios al clúster; la suite solo lee archivos | NFR2.1, NFR2.2, NFR10.5 |
| AUTONOMIA-02 | Cada requisito nombra su comprobación y su umbral; los comandos están fijados | Todos; `tech-stack-decisions.md` §4 |
| AUTONOMIA-03 | Sin campos ni rótulos de veracidad; sin ruta que escriba configuración; quién y cuándo en la sugerencia | NFR10.8, NFR11.3, NFR11.5 |
| AUTONOMIA-04 | Ningún destino externo en los contratos; una sola puerta al anonimizador; petición del proxy cerrada; reporte de la CLI sin texto | NFR1.1–NFR1.4, NFR12.3 |
| AUTONOMIA-05 | El hallazgo exige sus cinco campos; `estado: error` sin hallazgos; copia de C6 intacta | NFR10.2, NFR10.10, NFR11.4 |

## 6. Riesgos residuales

| Riesgo | Por qué queda | Tratamiento |
|---|---|---|
| Un nombre real que el autor no declara en `mentions` | Detectar un nombre real sin declararlo no es exacto (P4) | Revisión del autor en el PR; prohibición de `project.md` |
| Una sola palabra citada que aparece en un turno queda fuera del escaneo | BR5.3 (FD-U1-14, pendiente de tu decisión) | Si eliges la opción (b) de FD-U1-14, entra como BR5.3 revisada en el PR de B1 |
| El principal no publica huellas de C6 | Un PR que cambie un esquema y recalcule `SHA256SUMS` pasa la suite (BR1.7) | La revisión humana del PR de copia es el ancla (BR1.8) |
| Las copias de los meta-esquemas quedan viejas | P2 = A: sin herramientas de AsyncAPI en Node | Actualizarlas por PR con su SHA-256 nuevo |
| La comprobación estática de patrones usa el analizador interno de `re` de Python 3.12 | No hay una API pública estable | Fijada a 3.12; la prueba usa patrones malos conocidos como control |
| Dos mitades de validación que mantener | P8 = A | NFR10.16 pone las dos en rojo ante cualquier diferencia |

## 7. Precisiones a artefactos ya aprobados (NFR-U1-xx)

No edité ningún artefacto aprobado (regla de `project.md`). En la aprobación decides cuáles se llevan al
original, cada una en su propio commit.

| ID | Artefacto aprobado | Precisión | Origen |
|---|---|---|---|
| NFR-U1-01 | `contracts/functional-design/rules.md` (BR11.1) | `limits.load` acepta decimales en las unidades `ratio` y `s`, y exige enteros en las demás. BR11.1 dice «no es un entero», y FD-U10-13 pide `anonymizer_masking_budget_ratio` | FD-U10-13; aplicada sin preguntar |
| NFR-U1-02 | `contracts/functional-design/functional-spec.md` (F1 paso 6, F9) | La construcción e instalación del paquete (F9), `pip-audit` y `npm audit` van en pasos con red, fuera del `timeout 60` de la suite. El paso del paquete tiene su propio plazo: ≤ 180 s bajo `timeout 180` | R-04 de la revisión 1; aplicada sin preguntar |
| NFR-U1-03 | Functional Design de U5 (E21, FD-U5-02) y de U13 (§9, nota sobre el tope) | **P7 = A:** `limits.exceeded` es siempre `413`. U5 y U13 cambian su `422` en su segunda pasada de NFR Requirements; U5 además ajusta su NFR10.5 de la revisión 1. El catálogo declara un solo estado por `code` (NFR10.3) | P7 = A |
| NFR-U1-04 | Revisión 1 de este NFR (P2 = A, D1–D4) y `units-generation/unit-of-work.md` (U1, solo Python) | **P8 = A:** U1 suma `contracts/ts/` (Node LTS, ajv `strict`, Vitest, JCS) en el *job* `contracts-level0`. La consola importa de ahí la validación | P8 = A; contract-summary regla 1 |
| NFR-U1-05 | Functional Design de U8 (FD-U8-09) | La sección `clarifications` de C19 entra en C19 v2, que ya es un cambio mayor (FD-U11-09), y no como «cambio menor». C19 es estricto y todo cambio de forma es mayor (BR1.4) | BR1.4; FD-U8-09 |
| NFR-U1-06 | Revisión 1 de este NFR (NFR1.1) y `contract-summary.md` (C21 `servers`) | El nombre corto de servicio `http://veridicus-<nombre>:<puerto>` cuenta como interno, junto a `.svc.cluster.local` y las rutas relativas | C21 |
| NFR-U1-07 | `contract-summary.md` (C25, forma con `value: null`) | El catálogo entregado no admite nulos: una cifra entra cuando su unidad dueña fija el valor en su NFR. Hoy faltan las que nombran FD-U5-02, FD-U10-13, FD-U12-12 y FD-U13-03 | NFR10.14 |
| NFR-U1-08 | `contract-summary.md` (C1, C2, C5, C21) | Extensiones nuevas `x-veridicus-limit` y `x-veridicus-max-bytes`, que atan cada tope al nombre de su cifra de C25; los cuerpos `multipart` declaran `413` y `415` | R-01 y R-05 de la revisión 1; NFR10.7 |
