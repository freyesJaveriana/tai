# Preguntas de NFR Requirements — U10 anonymizer

**Unidad.** U10 `anonymizer` (COULD): proxy que enmascara nombres, lugares y expedientes antes de llamar
a un modelo externo y falla cerrado (`functional-design/functional-spec.md`, `rules.md`).

**Lo que ya está decidido y no se vuelve a preguntar.** Marcadores consistentes con restauración dentro
del clúster (P1), lista de nombres propios del escenario (P2), sin reintentos hacia el destino, solo el
proxy con salida, y que el juez por defecto del MVP es el interno. Los tiempos y la cobertura del módulo
guardia salen de team-practices y no necesitan pregunta.

---

## P1 — Condiciones para usar un proveedor externo

Aunque solo salgan marcadores, el destino externo recibe la estructura del testimonio. FR11.3 no fija
qué proveedor es aceptable ni cómo se habilita el proxy.

A. El proxy se entrega apagado. Habilitarlo exige un PR con un ADR del proveedor: compromiso escrito de
   no usar los datos para entrenar, retención ≤ 30 días, región declarada y TLS 1.2 o superior; el
   PR también cambia la `NetworkPolicy` para ese único destino. (Recomendada)
B. Cualquier proveedor compatible con OpenAI por HTTPS, sin más condiciones, porque los datos salen
   enmascarados.
C. No construir U10 en el MVP: se documentan sus requisitos y la unidad queda diferida.
X. Other (please specify)

[Answer]: A **Mode:** guided

---

# Segunda pasada — cambio 01, adenda 02 y Functional Design revisión vigente (2026-11-22)

**Unidad.** U10 `anonymizer` (tipo `service`, ahora **MUST**, tamaño L; Bolt B10). Ya no es un proxy
COULD apagado, sino el módulo `Anonymizer` de `libs/anonymizer/` (C20), que la CLI usa en el mismo
proceso, y el proceso `anonymizer-proxy` que lo expone en el clúster (C21). Lleva los adaptadores
nativos de Anthropic, Google y OpenAI en `libs/anonymizer/providers/` (C22, CD-04, FD-U10-03). Insumos:
el Functional Design revisión 2 (F1–F9, BR1.1–BR6.5, FD-U10-01 a FD-U10-17), requirements revisión 3
con la adenda 02 (FR11.3, FR11.4, FR12.3, FR12.4, FR14.3, FR15.1–FR15.4, NFR1–NFR15, VE-07, VE-14),
contract-summary revisión 3 (C13, C16, C18, C20–C22, C25), el NFR revisión 2 de U1 (P7 = A, NFR-U1-01,
NFR-U1-07 y su tabla de valores delegados) y `team.md`/`project.md`.

## Lo que ya está decidido

- **Supera a la revisión 1 (cambio 01, regla de `project.md`).** U10 es MUST (FR11.3), FR14.1 exige al
  menos un perfil comercial y C13 obliga a `semantic-agent` a comprobar el `/readyz` del proxy. Por eso
  sale la parte de **P1 = A** que dejaba el proxy apagado por defecto y que abría un solo destino en la
  `NetworkPolicy`: la salida la fijan los tres dominios de C22 y FR12.3, y la `NetworkPolicy` es de U2.
  Salen también `embed`, la lista de nombres del escenario y `veridicus_masking` (cambio 01, C13),
  NFR1.4, NFR9.1 y el reenvío compatible con OpenAI (C14 sale del proxy; ahora es C21).
- **Lo que se conserva de P1 = A**, porque no lo contradice ninguna fuente posterior y reduce el riesgo
  de lo que sale: un modelo comercial solo entra a `ProviderCapabilityTable` por un PR que trae el ADR
  de su proveedor, con el compromiso de no entrenar con los datos, retención ≤ 30 días, región
  declarada y TLS ≥ 1.2.
- **Ya fijado aguas arriba:** NER local más reglas, cinco categorías y red de seguridad (P3–P5 = A);
  marcas alteradas en todas las cadenas (P6 = A); `ModelCall` en todo error posterior al envío (P7 = A);
  salida estructurada nativa por proveedor (P8 = A); una llamada externa como mucho y sin reintentos
  (C13); `limits.exceeded` siempre `413` (P7 = A de U1); decimales en `ratio` y `s` (NFR-U1-01); C25 sin
  nulos (NFR-U1-07); 100 % de ramas en el módulo guardia, niveles 0–2 y CPU primero (`team.md`).

## Cómo se registra la revisión 2

Se aplica la regla de `project.md` para una segunda pasada por un cambio. Los requisitos conservan su
ID, lo que sale queda «Retirado» sin renumerar y lo nuevo toma el número siguiente de su grupo. Cada
fila dice si se mantiene, cambia o es nueva. Las precisiones a artefactos aprobados van en una tabla
NFR-U10-xx, sin editar los originales. Los artefactos se generan cuando esta pregunta tenga respuesta.

## Lo que el diseño resolverá sin preguntar

Va a la tabla NFR-U10-xx y puedes objetarlo en la aprobación:
1. **Cifras de C25 que son de U10.**
   - `anonymizer_request_max_bytes = 2 097 152` (2 MiB). La entrevista más larga del piloto (~186 000
     caracteres) cabe con margen.
   - `anonymizer_masking_budget_ratio = 0.15` del `timeout_s` de la llamada.
   - Dos comprobaciones de nivel 0 las atan a las cifras de otras unidades. El cuerpo de C21 construido
     con la transcripción de `transcript_max_chars` cabe en el tope. La seudonimización de esa
     transcripción, medida en p95, usa como mucho la mitad del presupuesto con `model_call_timeout_s`.
     Si U11 fija un plazo que no cumple esto, falla su PR, no el umbral.
2. **NER.** Un modelo de reconocimiento de entidades en español, en `safetensors`, que se carga con
   `trust_remote_code=False` y corre en CPU. `PER` se marca como `PERSONA` y `LOC` como `LUGAR`; `ORG`
   y `MISC` se ignoran, y de ellas se encarga la red de seguridad. El umbral de confianza es **0,30**
   («ante la duda se seudonimiza»). El modelo concreto y su `sha256` los fija Infrastructure Design.
   Debe pasar la prueba de cero fugas del conjunto sintético, que incluye nombres al inicio de turno,
   y el umbral no se baja.
3. **Rendimiento, recursos y concurrencia del proxy.** Se miden en CPU: el costo de la seudonimización
   por tamaño de transcripción, el sobrecosto del proxy sin contar la espera al proveedor, el pico de RSS
   con el NER cargado y un tope de peticiones simultáneas. El exceso recibe `503`
   `analysis.anonymizer_unavailable` sin seudonimizar ni enviar nada.
4. **Seguridad.** Una lista permitida de cabeceras salientes (autenticación del proveedor,
   `Content-Type` y versión de la API), sin `X-Request-Id` (cierra R-05 de la revisión 1). El plazo
   total de la llamada se aplica con `anyio.fail_after`, no por lectura (cierra R-04). El pod no guarda
   nada y lleva sistema de archivos de solo lectura. Las reglas, listas y tabla de capacidades se
   verifican por SHA-256 al arrancar. No se registra la tabla, el texto ni la clave.
5. **Observabilidad.** Métricas `veridicus_anonymizer_*` solo con etiquetas de enum: resultado,
   proveedor, papel, ranura, categoría y código. Logs JSON con los campos de BR2.3 y FD-U10-14.
6. **Frontera y propiedad.** Las políticas de manifiestos y la verificación en el clúster pasan a U2
   (BR3.3, BR3.4, US11.6). Las comprobaciones de `semantic-agent`, a U4. La validación de destinos de
   ModelGateway, a U11. Así se cierra R-06 de la revisión 1.

---

## P2 — Proveedor comercial de la primera rebanada

FD-U10 §7 deja a esta etapa el proveedor comercial de la primera rebanada (C18, pregunta abierta).
B11 la evalúa con un perfil de un proveedor comercial y uno local (US13.6). Ese proveedor será el
primero en recibir el testimonio seudonimizado. Eso incluye la corrida de humo de la CLI sobre las 10
entrevistas reales del piloto. Su adaptador se construye primero en B10 (mitigación de R14). Los otros
dos adaptadores también entran en B10, después. Ninguna fuente aprobada prefiere un proveedor: los tres
están en C22 y FR15.1. La recomendación es técnica.

A. **Anthropic** (Messages API). Es el único de los tres con una vía alterna ya diseñada (BR5.2): la
   herramienta forzada, por si su modo estructurado no admite el esquema de C6. Así la primera rebanada
   no depende de que el esquema quepa en un único modo. Su caché de *prompts* aprovecha el prefijo
   estable de F5. El generador del conjunto sintético tendría que ser de Google u OpenAI (NFR5 B).
   (Recomendada)
B. **OpenAI** (Responses API con `json_schema` estricto). Su modo estricto exige que todas las
   propiedades sean obligatorias. Los campos opcionales de C6 (`actos`, `pagina`) podrían impedir enviar
   el esquema tal cual, y BR1.1 no permite modificarlo.
C. **Google** (`generateContent` con `responseSchema`). `responseSchema` admite un subconjunto de JSON
   Schema. Las palabras clave de C6 que no admita tendrían que validarse solo después de recibir la
   respuesta. Cuáles son exactamente lo fija la prueba de contrato (AC13.6.1).
D. No fijarlo ahora. B10 construye los tres adaptadores antes de cualquier corrida y el perfil
   `comercial-piloto` de NFR Requirements de U11 elige uno. A cambio, se pierde la mitigación de R14
   (P9 = B de Delivery Planning).
X. Other (please specify)

[Answer]: A **Mode:** guided
