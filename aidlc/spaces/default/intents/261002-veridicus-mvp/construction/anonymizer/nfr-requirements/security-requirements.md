# Requisitos de seguridad — U10 anonymizer

**Insumos.** Frontera AUTONOMIA-04, flujos F1–F3 y escenarios E1–E8 de
`functional-design/functional-spec.md` (functional-spec); reglas BR1.1–BR3.4 de
`functional-design/rules.md` (rules) y entidades de `functional-design/entities.md`; FR11.3, FR12.3,
FR12.4 y NFR1, NFR5, NFR10–NFR12 de `inception/requirements-analysis/requirements.md` (requirements);
C13, C14 y C16 de `inception/contract-design/contract-summary.md` (contract-summary); respuesta P1 = A
de `nfr-requirements-questions.md`; reglas AUTONOMIA-01..05 de `team.md` y prohibiciones de
`project.md`.

Todo el módulo es **guardia de AUTONOMIA-04**. Niveles de team-practices: nivel 0 (unitarias, contratos
y políticas, cada PR), nivel 1 (integración, cada PR), nivel 2 (evaluación de IA, PR que tocan la IA y
entregas), nivel 3 (E2E y humo) y manual. Los comandos están en `tech-stack-decisions.md` §5. La
`NetworkPolicy` de salida denegada por defecto, las imágenes fijadas y el manejo de Secrets vienen de U2
(`../../platform/nfr-requirements/`); la validación de destinos internos de ModelGateway, de U4
(NFR1.1 de U4). Aquí solo se añade lo que el proxy cambia.

**Decisión P1 = A.** El proxy se entrega **apagado**: el código, sus pruebas y su plantilla de chart
existen, pero con `anonymizer.enabled: false` (valor por defecto) no se despliega nada y ningún pod
tiene salida a internet. Habilitarlo exige **un PR** que contenga a la vez: (1) un ADR del proveedor con
compromiso escrito de no usar los datos para entrenar, retención ≤ 30 días, región declarada y TLS 1.2
o superior; (2) el cambio de *values* que enciende el proxy; y (3) el cambio de la `NetworkPolicy` que
abre **ese único destino**. El juez por defecto del MVP sigue siendo el interno.

## 1. Frontera de la unidad (AUTONOMIA-04)

| Componente | Dónde corre | Qué datos cruzan su frontera | Clasificación |
|---|---|---|---|
| `anonymizer-proxy` (adaptador anonimizador) | Dentro del clúster; **no se despliega por defecto**. Habilitado, es el único pod con salida y solo hacia su destino | Entra: *prompt* o textos sin enmascarar y la lista de nombres propios, desde `semantic-agent` o `session-api`. Sale: **solo** el *payload* enmascarado (marcadores `[PERSONA_n]`, `[LUGAR_n]`, `[EXPEDIENTE_n]`), por HTTPS | Confidencial a la entrada; enmascarado a la salida |
| `MaskTable` | Memoria del proceso del proxy, durante una llamada | Nada: nunca se registra, se guarda ni sale | Confidencial |
| ModelGateway (adaptador cliente) | `libs/`, en `semantic-agent` y `session-api` | Texto sin enmascarar hacia el proxy, dentro del clúster (C13) | Confidencial |
| Destino externo | Fuera del clúster, en la región declarada en el ADR | Recibe solo marcadores y la estructura del testimonio; devuelve texto con marcadores o vectores | Enmascarado |
| Audio (C5) | — | **Nunca** pasa por el proxy: `transcribe` y `synthesize` no se admiten (NFR1.6, NFR1.8) | Restringido |

Con el proxy apagado, la tabla de fronteras de U4 y U2 queda igual: ningún componente llama fuera del
clúster.

## 2. Modelo de amenazas (STRIDE)

| # | Amenaza | STRIDE | Riesgo | Mitigación |
|---|---|---|---|---|
| T1 | Un nombre, lugar o expediente sale sin enmascarar porque ninguna regla lo detecta (límite de FR11.3) | Information disclosure | Alto | NFR1.3, NFR1.10; proxy apagado por defecto (NFR1.1) |
| T2 | Un error a mitad del enmascarado deja pasar el *payload* original | Information disclosure | Alto | NFR10.1 (falla cerrada, 100 % de ramas) |
| T3 | Otro pod (o el propio `semantic-agent`) obtiene salida a internet | Information disclosure | Alto | NFR1.5 (Kyverno con control negativo), NFR1.7 |
| T4 | Un servicio apunta su juez o *embeddings* a un destino externo saltándose el proxy | Information disclosure | Alto | NFR1.6 |
| T5 | El proxy reenvía campos o rutas no previstos (audio, campos extra) | Information disclosure | Alto | NFR1.8 |
| T6 | Texto, tabla o respuesta restaurada en logs, métricas o en el cuerpo de un error | Information disclosure | Alto | NFR10.3, NFR10.9 |
| T7 | La tabla de equivalencias persiste (disco, volcado, caché) | Information disclosure | Medio | NFR10.2, NFR10.10 |
| T8 | Redirección o certificado falso del destino lleva el *payload* a otro sitio | Spoofing | Medio | NFR10.5 |
| T9 | Fuga o versionado de la credencial del proveedor | Information disclosure | Medio | NFR10.6 |
| T10 | Un proveedor entrena con los datos o los retiene sin límite | Information disclosure | Medio | NFR1.2 (ADR con los 4 compromisos) |
| T11 | Cualquier pod usa el proxy como túnel hacia fuera | Elevation of privilege | Medio | NFR1.9 |
| T12 | Expresión regular con retroceso catastrófico o cuerpo enorme que agota CPU o memoria | Denial of service | Medio | NFR3.4, NFR10.8, D2 |
| T13 | Inyección en el testimonio que pide al juez externo «revelar» los nombres | Tampering | Bajo | El juez externo solo tiene marcadores; NFR5.1 |
| T14 | Cambio silencioso de las reglas de detección o del proveedor | Repudiation | Medio | NFR10.11, NFR11.1 |
| T15 | Salida por DNS: `kube-dns` resuelve nombres externos para cualquier pod | Information disclosure | Bajo | Riesgo transferido a Infrastructure Design (§5) |

## 3. Requisitos

### NFR1 — Soberanía de datos

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR1.1 | Apagado por defecto: el chart sin cambios no despliega nada con salida a internet. | Con `values-cpu.yaml` y `values-gpu.yaml` tal como están en `main`, el render (`helm template`) contiene **0** recursos con la etiqueta `app.kubernetes.io/name: veridicus-anonymizer-proxy` y **0** reglas de salida con `ipBlock` hacia fuera del clúster. Política Kyverno `veridicus-anonymizer-disabled-by-default` con control negativo (un render con el proxy habilitado sin ADR falla). | Nivel 0 |
| NFR1.2 | Habilitar el proxy exige un ADR del proveedor en el mismo PR. | Si un *values* tiene `anonymizer.enabled: true`, `scripts/check-provider-adr.sh` comprueba que existe el archivo de `anonymizer.providerAdr` (bajo `docs/adr/`) con las secciones «No entrenamiento», «Retención» (valor ≤ 30 días), «Región» (no vacía), «TLS» (1.2 o 1.3), «Destino» (host y CIDR iguales a los del *values*), «Modelo» (proveedor, modelo y versión) y «Riesgo residual» (la tasa medida de NFR1.10); y que la `NetworkPolicy` del proxy lleva la anotación `veridicus.io/provider-adr` con esa ruta. Controles negativos: ADR sin una sección, retención de 31 días, TLS 1.1 y host distinto. | Nivel 0 |
| NFR1.3 | El *payload* saliente no contiene ningún dato sembrado (AUTONOMIA-04, AC11.3.1). | Prueba sobre los *fixtures* de U1: por cada *fixture* con `mentions` (catálogo `contracts/fixtures/synthetic-names.yaml`) y por E1, se pasa el texto por `judge` y por `embed` con la lista de nombres del escenario cargada y un destino *fake* que captura los bytes enviados. Métrica: **apariciones de valores sembrados en el saliente = 0**, comparando sin mayúsculas ni tildes, y **0** coincidencias de secuencias de 6 o más dígitos (con o sin guiones, barras, puntos o espacios: cédulas y radicados de U1). Se cuentan también los marcadores: cada mención sembrada produce uno. | Nivel 0 |
| NFR1.4 | Los *embeddings* externos solo reciben texto enmascarado (BR1.4). | La prueba de NFR1.3 corre también para `embed` con los textos de un lote de 32 pasajes; 0 apariciones; los vectores se devuelven sin restaurar. | Nivel 0 |
| NFR1.5 | Solo el proxy tiene salida fuera del clúster, y solo hacia su destino (BR3.1, AC11.3.2). | Política Kyverno `veridicus-egress-only-anonymizer`: toda regla de salida con `ipBlock` fuera del clúster debe estar en una `NetworkPolicy` cuyo `podSelector` elige solo el proxy, con CIDR distinto de `0.0.0.0/0` y `::/0`, prefijo ≥ /24 (IPv4) o ≥ /48 (IPv6), puerto 443/TCP y la anotación de NFR1.2. Controles negativos: salida a internet en `semantic-agent` (E7), en `session-api`, el proxy con `0.0.0.0/0`, el proxy por el puerto 80 y la regla sin anotación. | Nivel 0 |
| NFR1.6 | ModelGateway solo acepta como destino externo el proxy (BR3.2, AC9.1.4). | Se mantiene NFR1.1 de U4 (toda URL de modelo debe ser interna del clúster) y se añade: la URL del proxy (`http://veridicus-anonymizer-proxy.<namespace>.svc.cluster.local:8080`) solo es válida para `VERIDICUS_JUDGE_URL` y `VERIDICUS_EMBEDDINGS_URL`; si aparece en `VERIDICUS_WHISPER_URL` o en la del TTS, el servicio no arranca (el audio nunca sale). Una URL externa sin pasar por el proxy impide arrancar (E8). Una prueba por caso y su control positivo. | Nivel 0 |
| NFR1.7 | La verificación en el clúster es manual y de solo lectura (BR3.3, AUTONOMIA-01). | Antes de la sustentación, junto con la de NFR1.1 de U2: `kubectl get deploy,networkpolicy -n veridicus -o yaml` (solo lectura) y, desde cada pod con datos sin anonimizar, `kubectl exec <pod> -- curl -sS -m 5 https://example.com` termina con código ≠ 0. Con el proxy apagado, `kubectl get deploy -l app.kubernetes.io/name=veridicus-anonymizer-proxy` no devuelve nada. Si está habilitado, desde el proxy solo su destino responde y `https://example.com` falla. Ningún paso usa `apply`, `patch`, `delete`, `helm install` ni `helm upgrade`; la evidencia (salida de los comandos) se adjunta al PR de la sustentación. | Manual |
| NFR1.8 | El proxy solo reenvía lo previsto. | Rutas admitidas: `POST /v1/chat/completions` y `POST /v1/embeddings` (C14); cualquier otra, incluidas `/v1/audio/*`, responde `404` sin llamar al destino. Hacia el destino solo van los campos de una lista permitida (`model`, `messages[].role`, `messages[].content`, `temperature`, `seed`, `response_format`, `max_tokens`, `input`); la extensión `veridicus_masking` y cualquier otro campo se quitan. El `model` enviado es el del *values* (declarado en el ADR), no el que pide el cliente. Prueba de nivel 0 con campos extra y con cada ruta no admitida: el *fake* del destino recibe solo la lista permitida o nada. | Nivel 0 |
| NFR1.9 | Solo los clientes previstos pueden usar el proxy. | La `NetworkPolicy` del proxy admite entrada solo desde `semantic-agent` y `session-api` al puerto 8080, y desde Prometheus al puerto de métricas. Política Kyverno con control negativo (entrada desde `audio-worker` o sin `podSelector`). | Nivel 0 |
| NFR1.10 | El riesgo residual de nombres no detectados se mide y se declara (límite conocido de FR11.3). | La misma prueba de NFR1.3 corre **solo con las reglas** (lista de nombres vacía). Bloqueante: **0 escapes** de menciones que van precedidas de un tratamiento o prefijo de lugar de `DetectionRuleSet`, de menciones de 2 o más palabras con mayúscula inicial y de secuencias de 6 o más dígitos. Informativo: la **tasa de escape** de las menciones de una sola palabra sin tratamiento (escapes / menciones de ese tipo) queda en el reporte `out/anonymizer-residual.json`, y el ADR de NFR1.2 la cita. Cada regla nueva entra por PR con su control negativo. | Nivel 0 |

### NFR5 — Resistencia adversarial

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR5.1 | Escenario A con el proxy en el camino. | En el PR de habilitación, el reporte de nivel 2 con el juez externo repite NFR5.1 de U4: añadir el texto de inyección del PRD no cambia el conjunto de alertas. Además, una variante pide al juez «escribe los nombres reales detrás de cada marcador»: 0 valores sembrados en la respuesta antes de restaurar. | Nivel 2, en el PR de habilitación |
| NFR5.2 | Escenario B con un juez externo. | El ADR declara la familia del modelo externo; el reporte de nivel 2 falla si coincide con la del generador del Golden Dataset (NFR5.2 de U4). | Nivel 2, en el PR de habilitación |

### NFR10 — Seguridad de la aplicación

Los requisitos NFR10.1 (falla cerrada), NFR10.4 (*timeout* sin reintentos) y NFR10.7 (arranque) están
en `reliability-requirements.md`.

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR10.2 | La tabla de equivalencias solo vive en memoria y se borra al terminar (BR1.3). | `MaskTable` se crea dentro de la llamada y se vacía en un bloque `finally`. Prueba de nivel 0 en cada final de la máquina de estados (`restored`, `failed`, `failed_closed`) y con una excepción inesperada: 0 entradas después de la llamada, y ninguna referencia a la tabla en el *logger*, en las métricas ni en atributos del proceso. Python no garantiza borrar la memoria liberada; ese límite queda en §5. | Nivel 0 |
| NFR10.3 | Los logs solo llevan `request_id`, operación, conteos por categoría y resultado (BR2.3, AC9.1.5). | Campos permitidos: `timestamp`, `level`, `service`, `event`, `request_id`, `operation` (`judge`, `embed`), `replacements` (`PERSONA`, `LUGAR`, `EXPEDIENTE` con su número), `result`, `code`, `upstream_status` (número) y duraciones. Prueba de nivel 1 con *canary* (E6): una cadena centinela sembrada en el testimonio, en la lista de nombres, en la respuesta del destino *fake* y en el cuerpo de un error 500 del destino aparece **0** veces en todos los logs capturados, incluidos los de cada rama de error. Una excepción se registra con su tipo y su `code`, nunca con su mensaje ni con el cuerpo de la respuesta del destino. | Nivel 1 |
| NFR10.5 | Solo HTTPS verificado hacia el único destino. | `VERIDICUS_ANONYMIZER_UPSTREAM_URL` debe ser `https://`, sin credenciales en la URL y con el host del ADR; TLS mínimo 1.2 (`ssl.TLSVersion.TLSv1_2`), verificación de certificado y de nombre siempre activas, sin redirecciones (`follow_redirects=False`: un 3xx es `anonymizer.upstream_error`). Pruebas de nivel 0: `http://`, URL con usuario, TLS 1.1 forzado y un 302 del *fake*: todas fallan sin reenviar. | Nivel 0 |
| NFR10.6 | La credencial del proveedor llega solo por Secret. | El *values* referencia el Secret `veridicus-anonymizer-credential` con `secretKeyRef`; el proceso lee `VERIDICUS_ANONYMIZER_API_KEY` y no arranca si falta o está vacía (BR2.2). La clave solo va en la cabecera `Authorization` hacia el destino, nunca en logs, métricas, errores ni `/readyz`. `gitleaks` en la CI y Kyverno rechazan un valor literal en el manifiesto (control negativo). El humano crea el Secret con el script revisable de U2. | Nivel 0 y CI |
| NFR10.8 | Las entradas tienen límites y un exceso falla cerrado. | Cuerpo ≤ 512 KiB (`413` `anonymizer.payload_too_large`); lista de nombres ≤ 2 000 entradas de ≤ 200 caracteres; `embed` ≤ 32 textos; respuesta del destino leída hasta 2 MiB (más → `anonymizer.upstream_error`). Una petición sin `veridicus_masking` o con esquema inválido → `422` `anonymizer.invalid_request`. En todos los casos, 0 peticiones al destino (prueba de nivel 0 por límite). | Nivel 0 |
| NFR10.9 | Los errores salen como Problem Details sin datos. | Códigos estables: `anonymizer.invalid_request` (422), `anonymizer.payload_too_large` (413), `anonymizer.masking_failed` (500), `anonymizer.busy` (503), `anonymizer.upstream_timeout` (504), `anonymizer.upstream_error` (502), con `detail` en español del catálogo y sin texto de la petición ni del destino (jerarquía de `libs/`). Prueba de nivel 0 por código. | Nivel 0 |
| NFR10.10 | El pod del proxy no guarda nada. | Contenedor sin root, `readOnlyRootFilesystem: true`, sin volúmenes salvo el `ConfigMap` de reglas montado `readOnly` y un `emptyDir` en memoria (`medium: Memory`, ≤ 16 MiB) para `/tmp`; `automountServiceAccountToken: false`; sin credencial de base de datos ni de Redis. Política Kyverno con control negativo (un PVC o un `hostPath` en el proxy). | Nivel 0 |
| NFR10.11 | Las reglas de detección son configuración versionada e inmutable. | `DetectionRuleSet` se lee de un archivo montado `readOnly` desde un `ConfigMap`; su SHA-256 debe coincidir con `VERIDICUS_ANONYMIZER_RULES_SHA256` y su `schema_version` es semver; si no, el proxy no arranca. Cambiar una regla es un PR con su control negativo (NFR1.10). | Nivel 0 |

### NFR11 — Integridad y auditoría

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR11.1 | Cada evaluación con juez externo es auditable. | La fusión del PR de NFR1.2 es la aprobación registrada (AUTONOMIA-01). Cada respuesta del proxy lleva las cabeceras `X-Veridicus-Masking-Rules` (`schema_version`) y `X-Veridicus-Model` (`<proveedor>/<modelo>@<versión>` del ADR); ModelGateway pone en `model_digest` de C3 el SHA-256 de ese identificador. Prueba de nivel 0 de ambas cabeceras y del cálculo. | Nivel 0 |

### NFR12 — Datos sintéticos

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR12.1 | Los *fixtures* de U10 son sintéticos. | Los textos, listas de nombres, respuestas del destino *fake* y la cadena *canary* usan el catálogo y las marcas de U1 (`synthetic: true`, `mentions`); la comprobación de U1 corre sobre `services/anonymizer-proxy/tests/` con 0 hallazgos. Los expedientes de prueba usan formatos inventados (p. ej. E1). | Nivel 0 |

## 4. Trazabilidad de AUTONOMIA

| Regla | Requisitos de U10 |
|---|---|
| AUTONOMIA-01 | Habilitar es un PR revisable con ADR (NFR1.2, NFR11.1); la verificación en el clúster es de solo lectura (NFR1.7) |
| AUTONOMIA-02 | Cada requisito tiene su umbral y su comando (`tech-stack-decisions.md` §5) |
| AUTONOMIA-03 | No aplica: el proxy no califica; la restauración no cambia calificaciones y el escaneo de C8 sigue en U4 después de restaurar |
| AUTONOMIA-04 | §1, NFR1.1–NFR1.10, NFR10.1–NFR10.3, NFR10.5, NFR10.10; módulo guardia con 100 % de ramas (NFR13.2) |
| AUTONOMIA-05 | No aplica: la guardia del umbral decide en U4 antes de llamar al juez (por el proxy o no) |

## 5. Riesgos aceptados o transferidos

| Riesgo | Tratamiento |
|---|---|
| **Nombres no detectados (T1).** Un nombre de una sola palabra, sin tratamiento y fuera de la lista del escenario puede salir; es el límite conocido de las expresiones regulares de FR11.3. | Aceptado con el proxy apagado por defecto y el juez interno como opción del MVP; la tasa medida (NFR1.10) va en el ADR y el humano decide al habilitar |
| **Estructura del testimonio.** Aun enmascarado, el destino ve el relato, las fechas y las relaciones entre marcadores. | Aceptado solo con los compromisos del ADR (NFR1.2) |
| **Memoria liberada.** Python no borra los bytes de las cadenas liberadas; un volcado del proceso podría contenerlas. | Pod sin volúmenes persistentes ni volcados (NFR10.10); transferido a Infrastructure Design (desactivar *core dumps* en el nodo) |
| **Salida por DNS (T15).** `kube-dns` resuelve nombres externos para todos los pods; un pod comprometido podría codificar datos en consultas. | Transferido a Infrastructure Design (U2): resolver solo nombres del clúster y del destino del proxy si el CNI lo permite |
| **IP del destino cambiante.** Una `NetworkPolicy` estándar filtra por IP, no por nombre. | El ADR declara CIDR estables; si el proveedor no los tiene, se necesita un CNI con políticas por FQDN (Infrastructure Design) o el proxy no se habilita |

## 6. Precisiones a artefactos ya aprobados

Estas decisiones precisan artefactos ya aprobados. No los edité; decides en la aprobación si se
actualizan. Todas aplican solo si se habilita el proxy.

| Artefacto | Qué precisa | Origen |
|---|---|---|
| `anonymizer/functional-design/functional-spec.md` (F1 paso 2) | El proxy **no** carga la lista de nombres de la base: la recibe del cliente en la extensión `veridicus_masking` (`scenario_version_id`, `proper_nouns`) del cuerpo y la quita antes de reenviar. Así el único pod con salida no tiene credencial de base de datos (NFR10.10) | T11, NFR1.8 |
| `contract-design/contract-summary.md` (C13, C9) | El adaptador cliente obtiene la lista de nombres propios de la versión de escenario (extraída por el indexador de U4 al indexar) con su rol de base de datos y la envía al proxy; requiere `SELECT` sobre esa lista para `veridicus_judge_ro` (cambio menor) | Precisión anterior |
| `contract-design/contract-summary.md` (C14) | El proxy expone el mismo subconjunto de C14 (`/v1/chat/completions`, `/v1/embeddings`), más la extensión `veridicus_masking`, y responde con los códigos de NFR10.9 y las cabeceras de NFR11.1 | NFR1.8, NFR10.9, NFR11.1 |
| `text-flow/nfr-requirements/reliability-requirements.md` (NFR10.16 de U4) | Si el adaptador es el proxy, `502` y `504` del proxy son **finales** (`turn.error.system` y `turn.error.timeout`) y no vuelven por `XAUTOCLAIM`, para que nada se reenvíe al destino externo; solo `503` `anonymizer.busy` (nada enviado) es recuperable | NFR10.4 |
| `contract-design/contract-summary.md` (C16) | El `/readyz` del proxy no contacta al destino externo: comprueba configuración, reglas y credencial presentes | NFR10.7 |
| `contract-design/contract-summary.md` (C15) | Se añaden las métricas `veridicus_anonymizer_*` de `observability-requirements.md` por un PR de U1 | NFR15.1 |
| `anonymizer/functional-design/rules.md` (BR1.2) | Los patrones de expediente cubren toda secuencia de 6 o más dígitos con o sin separadores (incluye cédulas y radicados de 23 dígitos), por «enmascarar ante la duda» | NFR1.3 |
| `anonymizer/functional-design/rules.md` (BR2.1) | Un texto de entrada que ya contiene algo con forma de marcador (`[PERSONA_n]`, `[LUGAR_n]`, `[EXPEDIENTE_n]`) falla cerrado con `anonymizer.masking_failed`, porque la restauración no podría distinguirlo | NFR10.1 |
| `platform/nfr-requirements/` (NFR1.1 y tabla de dependencias de U2) | La regla de salida y el `Deployment` del proxy solo se generan con `anonymizer.enabled: true`, que trae el PR con ADR; la entrada al proxy solo desde `semantic-agent`, `session-api` y Prometheus | NFR1.1, NFR1.9 |
