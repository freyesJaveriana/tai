# Preguntas de Functional Design — U10 anonymizer

**Unidad.** U10 `anonymizer` (tipo `service`, COULD): adaptador anonimizador de ModelGateway que
enmascara nombres, ubicaciones y números de expediente antes de cualquier llamada externa y falla
cerrado, con la prueba del *payload* saliente y la `NetworkPolicy` que solo le da salida a él
(US11.3). Solo se construye si se decide usar un modelo externo.

**Lo que ya está decidido y no se vuelve a preguntar.** Expresiones regulares en español (FR11.3);
falla cerrada (AC11.3.1); misma forma que ModelGateway (C13); 100 % de ramas; solo el proxy tiene salida
(AC11.3.2). Quedan dos huecos.

---

## P1 — Cómo se enmascara

El juez externo debe poder razonar sobre «quién estuvo dónde», así que importa si dos menciones del
mismo nombre se reconocen como la misma persona, y si la respuesta vuelve con los nombres reales.

A. Marcadores consistentes por llamada (`[PERSONA_1]`, `[LUGAR_2]`, `[EXPEDIENTE_1]`): el mismo valor
   recibe el mismo marcador; la tabla de equivalencias vive solo en memoria del proxy durante la llamada
   y se usa para restaurar la respuesta dentro del clúster. (Recomendada)
B. Marcadores genéricos sin numerar (`[PERSONA]`, `[LUGAR]`) y sin restaurar la respuesta.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P2 — Qué reconoce como nombre o lugar

Un nombre propio en español no siempre se distingue con una expresión regular («San José» puede ser
persona o lugar), y un nombre que se escape sale del clúster.

A. Expresiones regulares (tratamientos como «señor», «doña», secuencias de palabras con mayúscula
   inicial, prefijos de lugar como «vereda», «municipio de», formatos de expediente) más la lista de
   nombres propios extraída de los documentos del escenario; ante la duda, se enmascara. (Recomendada)
B. Solo expresiones regulares.
X. Other (please specify)

[Answer]: A **Mode:** guided

---

# Segunda pasada — cambio 01, adenda 02 y revisiones 3 (2026-11-21)

**Unidad.** U10 `anonymizer` (tipo `service`, ahora **MUST**, tamaño L): el módulo `Anonymizer` en
`libs/anonymizer/` (C20), que la CLI usa en el mismo proceso, y el proceso `anonymizer-proxy` que lo
expone en el clúster (C21), con los adaptadores nativos de Anthropic, Google y OpenAI y sus claves
(C22, CD-04). Historias: US11.3 (AC11.3.1–AC11.3.7, más AC11.3.8 de la adenda 02) y US11.5
(AC11.5.1–AC11.5.2). La revisión 1 (2026-10-02) es anterior al cambio 01 y se revisa por Modify: los ID
que siguen se conservan y los que salen quedan «Retirado», sin renumerar.

**Lo que ya está decidido y no se vuelve a preguntar.**
- *Siguen de la revisión 1:* P1 = A (marcas numeradas y coherentes con la tabla solo en memoria y
  restauración dentro del clúster) y la parte de P2 = A sobre reglas en español y «ante la duda, se
  seudonimiza».
- *Salen de la revisión 1:* la lista de nombres propios del escenario y `scenario_version_id` (el
  cambio 01 retira los escenarios), la operación `embed` y BR1.4 (sale `embed` de C13), el código
  `turn.error.system` (lo sustituye `anonimizador_no_disponible`, CD-01/CD-02), y las reglas BR3.2–BR3.4,
  que ahora son de U11 (arranque con destino externo, FR14.3, US13.3) y de U2 (verificación en el clúster
  y tabla de fronteras, US9.1, US11.6).
- *Detección:* NER local más reglas (FR11.3, DT18; components, Anonymizer). El modelo NER es un artefacto
  fijado por `sha256`, sin código ejecutable ni `trust_remote_code` (`team.md`, Deployment); cuál modelo y
  su umbral de confianza los fijan NFR Requirements e Infrastructure Design.
- *Interfaz y flujo:* la operación única `generate` con los cinco pasos de C20, el `Protocol`
  `AnonymizingProvider` y los tipos y errores de `contracts/python/model_calls.py` (C13, revisión 3), con
  los nombres que resulten de las precisiones FD-U1-01 a FD-U1-04 de U1. El fallo cerrado ocurre antes
  del paso 3: `AnonymizerUnavailable` y 0 llamadas (AC11.3.3; C20). Un destino `local` se rechaza
  (C20). `call.anonymized = True` (C20); el incidente de VE-14 (AC11.3.8) lo detecta U11 y el bloqueo de
  la sesión es de U4 (ADR-013).
- *Proxy:* la petición, las respuestas `200/409/422/451/502/503/504` y sus `code` (C21); el proxy
  resuelve proveedor, modelo y clave en su propia copia validada de los perfiles, con
  `profiles.validate(kind: base, key_prefix="VERIDICUS_")` de U1 (C21; U1 §7); no reintenta hacia el
  proveedor y cada petición produce como mucho una llamada externa (C13); sus logs llevan solo `run_id`,
  perfil, papel, proveedor y códigos (C21; NFR10).
- *Proveedores y red:* los tres dominios de la lista (C22), solo HTTPS por 443, la lista impuesta por el
  módulo y comparada con la lista blanca de CoreDNS con control negativo (AC11.5.1, AC11.5.2); la
  `NetworkPolicy` y el `Secret` son de U2 (US11.6, AC11.6.4).
- *Pruebas del lado de U10:* *payload* sin entidades sembradas, 0 llamadas con el módulo en fallo,
  destino local rechazado y las negativas de C21, sobre el transporte HTTP *fake* de
  `libs/anonymizer/testing/` y un doble del puerto (C20); la prueba compuesta de AC11.3.3 y AC11.3.7 es
  de U11 (C13). Módulo guardia con 100 % de ramas (`team.md`).

**Lo que el diseño resolverá sin preguntar** (va como propuesta a la tabla de precisiones de
`functional-spec.md`, y puedes objetarlo en la aprobación): el nombre del subpaquete de adaptadores
nativos (`libs/anonymizer/providers/`) y del contrato de import-linter que lo excluye de `semantic-agent`
(pregunta abierta de C20); la lista de dominios como archivo versionado del módulo, que lee también la
comprobación de U2; ningún adaptador sigue redirecciones ni acepta otra URL base para un proveedor
comercial; la restauración solo toca los valores de cadena del JSON ya parseado; un texto de entrada que
ya trae algo con forma de marca (`[PERSONA_1]`) se trata como un valor más de la tabla y vuelve intacto
(hallazgo R-05 de la revisión 1); el modelo NER se carga al arrancar, y sin él el proxy no pasa `/readyz`
y la CLI termina con código ≠ 0. Quedan seis decisiones de criterio.

---

## P3 — Qué se seudonimiza y qué pasa con lo dudoso

FR11.3 nombra personas, lugares y números de expediente; AUTONOMIA-04 habla también de «identificadores
reales del proceso». El hallazgo R-02 de la revisión 1 señaló que un nombre suelto o un apodo que no
reconozca ninguna regla sale del clúster. Las fechas y las cifras no se seudonimizan en ninguna opción:
son hechos centrales que el juez compara (tipos «Fecha» y «Número»).

A. Cuatro categorías: `PERSONA` (con apodos y alias), `LUGAR`, `EXPEDIENTE` e `IDENTIFICADOR` (cédula,
   teléfono, correo, placa, cuenta). Se seudonimiza la unión de lo que detectan el NER y las reglas. Red
   de seguridad: toda palabra con mayúscula inicial que no abre oración, que ninguno clasifica y que no
   está en una lista versionada de palabras permitidas («Fiscalía», «Ejército», meses…) se seudonimiza
   como `[ENTIDAD_n]`. Las organizaciones e instituciones no se seudonimizan. (Recomendada)
B. Las mismas cuatro categorías y la unión NER ∪ reglas, sin la red de seguridad: el riesgo residual de
   un nombre que no detecta ninguno de los dos queda aceptado por escrito.
C. Como A, y además `ORGANIZACION` (grupos armados, empresas, instituciones), a costa de que el juez
   pierda contexto sobre quién actuó.
D. Solo las tres categorías de FR11.3, con la unión NER ∪ reglas.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P4 — Qué cuenta como «la misma» persona o lugar

La verificación de citas (FR4.4, AC3.4.2) es estricta con tildes y mayúsculas, así que la restauración
tiene que devolver exactamente el texto original. AC11.3.2 pide la misma marca para una persona
mencionada en varios turnos. Una transcripción puede escribir «José» y «Jose», o «Ana Pérez» y luego «Ana».

A. Una marca por forma exacta del texto: el mismo texto recibe la misma marca en cualquier turno; «José»
   y «Jose», o «Ana Pérez» y «Ana», reciben marcas distintas. La restauración es exacta y la cita verifica
   contra el turno original sin casos especiales. (Recomendada)
B. Una marca por valor normalizado (sin mayúsculas ni tildes) con subíndice de variante (`[PERSONA_3]`,
   `[PERSONA_3_2]`): el juez sabe que son la misma persona y cada variante se restaura a su forma
   exacta, a costa de una gramática de marcas más compleja.
C. Como B, y además se enlaza una mención parcial con el nombre más largo que la contiene, si es el único
   (por ejemplo, «Ana» con «Ana Pérez»).
X. Other (please specify)

[Answer]: A **Mode:** guided

## P5 — Alcance de la coherencia de las marcas entre llamadas

El PRD y FR11.3 dicen «marcas coherentes en toda la entrevista»; C20 dice «coherentes en toda la
llamada» y que la tabla vive solo durante la llamada. Una corrida hace varias llamadas (juez, verificador
y verificador permutado), y el modo incremental, varias corridas por sesión.

A. La tabla vive solo durante la llamada (C20) y la numeración es determinista, por orden de primera
   aparición en los mensajes. «Toda la entrevista» se cumple dentro de cada llamada, que lleva la
   transcripción que analiza. Entre llamadas, la misma persona puede llevar otro número, y nada depende de
   ello porque cada respuesta se restaura en su propia llamada. Se registra como precisión de FR11.3.
   (Recomendada)
B. Como A, pero numerando por el orden de los turnos del bloque de datos JSON, para que la misma
   transcripción dé las mismas marcas en todas las llamadas de una corrida (y aproveche la caché de
   *prompts* del proveedor), a costa de que el módulo conozca la forma de la entrada del contrato común.
C. Una tabla por corrida que el proxy guarda en memoria hasta que la corrida termina. Contradice C20,
   se pierde si el pod se reinicia y obliga a una sola réplica.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P6 — Dónde se buscan las marcas alteradas

FR11.3 y AC11.3.4 piden que una marca alterada o inventada invalide el hallazgo; C13 devuelve en
`altered_markers` las rutas JSON afectadas y U11 descarta el hallazgo con `marca_alterada`. La cita que
perdió una marca no la ve el anonimizador: la rechaza la verificación de U11 contra el turno original.

A. Se revisan todas las cadenas de la respuesta. Todo lo que tiene forma de marca y no coincide
   exactamente con una de la tabla (alterada, inventada o mal escrita) se deja sin restaurar, y la ruta de
   esa cadena va a `altered_markers`. U11 descarta el hallazgo que la contiene, esté la marca en una cita,
   en `hecho` o en `observaciones`. (Recomendada)
B. Solo se revisan `cita_a` y `cita_b`; en `hecho` y `observaciones`, una marca desconocida se deja como
   texto visible para el analista. El módulo tendría que conocer la forma del hallazgo.
C. Tolerante: las variantes triviales (mayúsculas, espacios o corchetes) se restauran y solo invalida la
   marca inventada. Choca con el caso (b) de AC11.3.4.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P7 — Llamadas que salieron pero fallaron

Después del paso 3 de C20 la llamada ya salió y cuesta *tokens*, pero los errores de C13 no llevan el
`ModelCall`, así que esa llamada no queda en `registro.llamadas` (FR15.3) ni en el costo (FR15.4). Además,
C21 no tiene respuesta para una salida del proveedor que no es JSON (`InvalidOutput`).

A. Todo error lanzado después de enviar (`ContentBlocked`, `Timeout`, `ProviderError`, `InvalidOutput`)
   lleva el `ModelCall` de la llamada, con los *tokens* que informe el proveedor (0 si no los informa), y el
   cuerpo de error del proxy lo incluye. La salida que no es JSON va como `502` con `code`
   `analysis.invalid_output`, y el cliente de C21 la traduce a `InvalidOutput`. Es una precisión a C13 y a
   C21 que deciden U1 y U11. (Recomendada)
B. Como hoy: las llamadas fallidas no se registran y la salida que no es JSON se informa como `502`
   `analysis.provider` (`ProviderError`). El costo y el registro quedan por debajo de lo real.
C. Se registran las llamadas fallidas, pero la salida que no es JSON sigue como `ProviderError`.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P8 — Cómo se fuerza la salida JSON en cada proveedor (pregunta abierta de C22)

C22 dejó a esta etapa la forma de forzar la salida JSON y el esfuerzo en cada proveedor, y si con OpenAI
se usa Responses o Chat Completions. En todas las opciones U11 valida la respuesta contra su esquema, y
la prueba de contrato de cada adaptador comprueba que el esquema de C6 es compatible con el modo
estructurado del proveedor.

A. Cada adaptador usa la salida estructurada nativa con el esquema de la petición: Google con
   `responseSchema`; OpenAI con la Responses API y `json_schema` estricto; Anthropic con su salida
   estructurada por esquema JSON o, si el modelo del perfil no la admite, con una herramienta forzada cuyo
   esquema es el de la respuesta. El esfuerzo del perfil va al parámetro de razonamiento de cada
   proveedor. (Recomendada)
B. Como A, pero OpenAI por Chat Completions con `json_schema`.
C. Herramienta forzada en los tres proveedores: una sola técnica, aunque no siempre la más fiable.
D. JSON pedido por instrucción, sin modo estructurado, y solo la validación posterior.
X. Other (please specify)

[Answer]: A **Mode:** guided
