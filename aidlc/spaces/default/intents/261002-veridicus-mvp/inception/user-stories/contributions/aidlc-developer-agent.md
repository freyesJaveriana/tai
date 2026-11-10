**Collaborator:** aidlc-developer-agent

## Contribution

Revisé la revisión 3 desde la implementabilidad, contrastándola con `contract-design/contract-summary.md`
(P8, P13, C13, C20, C21, C22, CD-01, CD-02 y CD-04). CD-02 está bien reflejado: el código
`anonimizador_no_disponible` aparece igual en la tabla de decisiones, AC3.2.1 (h), AC3.2.5, AC11.3.3 y
AC11.6.2, y coincide con el enum de C6 y con la traducción `analysis.anonymizer_unavailable` del catálogo
de Problem Details. CD-04 no queda del todo reflejado. La cabecera dice que solo AC11.3.7 lo toca, pero
hay otros dos criterios cuyo punto de observación o cuyo servicio sigue el diseño anterior, cuando los
adaptadores nativos podían vivir en `semantic-agent`: AC11.3.3 y AC13.3.1. Además, AC3.2.5 deja abierto
un código del mismo enum. Son objeciones de conocimiento, sin ronda 2: se corrigen con una precisión en
el criterio y una línea en la cabecera, sin cambiar ninguna respuesta (1–19) ni ninguna historia.

## Positions

AGREE: CD-02 está aplicado igual en la tabla de decisiones («Código de error del anonimizador»), AC3.2.1 (h), AC3.2.5, AC11.3.3 y AC11.6.2, y coincide con el enum `error.codigo` de C6 y con la fila `anonimizador_no_disponible` → `analysis.anonymizer_unavailable` del catálogo; AC3.2.1 (h) sigue siendo construible con un `ModelGateway` *fake* porque solo prueba cómo se pasa del error tipado `AnonymizerUnavailable` al código.
AGREE: AC11.3.7 es construible tal como está tras CD-04: el «transporte HTTP *fake* de cada adaptador comercial» es el doble del adaptador nativo que C20 pone dentro del módulo `Anonymizer` de `libs/` (U10), y la prueba corre en la CLI con el módulo en proceso, sin red.
OBJECT: AC11.3.3 observa en el sitio equivocado tras CD-04. Con un `ModelGateway` *fake* el anonimizador ni siquiera se ejecuta, así que «registra 0 llamadas» se cumple siempre y no prueba el fallo cerrado. La llamada externa sale del adaptador nativo dentro del `Anonymizer` (C20 paso 3: «con el módulo en fallo, el doble del adaptador nativo no recibe ninguna llamada»). Propuesta: «Then el doble del adaptador nativo del proveedor (el mismo transporte HTTP *fake* de AC11.3.7) registra 0 llamadas», con el `ModelGateway` real y su adaptador `anonymizer`; hay que añadir AC11.3.3 a la lista de la cabecera que CD-04 afecta.
OBJECT: AC13.3.1 (c), «una clave de API referenciada que falta, When arranca un servicio», ya no vale para cualquier servicio. Por CD-04 y C21, `api_key_ref` se resuelve solo en `anonymizer-proxy` (y en la CLI, cuando usa el módulo), y `semantic-agent` no tiene claves ni adaptadores nativos (import-linter lo impide, C13). Propuesta: que (c) nombre `anonymizer-proxy` y la CLI, y que (b) nombre `semantic-agent` y la CLI. Así cada caso tiene su servicio y su control positivo es construible; AC13.3.1 también debe entrar en la lista de la cabecera que CD-04 afecta.
OBJECT: AC3.2.5 dice «Given cada código de error», pero el enum de C6 que fijó Contract Design tiene seis valores (P8, CD-01): también `incidente_anonimizacion`, que AC3.2.5 no lista ni le da causa en español. Así, la prueba Vitest que recorre el enum no tiene texto para ese código. Propuesta sin reabrir la pregunta 17: o se limita AC3.2.5 a los cinco códigos de FR4.2 y se registra en la tabla de decisiones que la causa de `incidente_anonimizacion` la fija la adenda 02 (AC11.3.8, VE-14), o se añade una fila con su causa en la tabla de decisiones para que el humano decida en la aprobación.
AGREE: AC11.6.2 sigue siendo construible, pero tras CD-04 conviene precisar que el servidor de proveedor *fake* solo se alcanza a través de `anonymizer-proxy` (`semantic-agent` no tiene adaptador nativo), para que «0 peticiones» mida el fallo cerrado y no la mera ausencia del adaptador. El texto de origen de US11.6 («Dónde se seudonimiza … lo decide Domain Design») ya está decidido por CD-04/P13 y basta con una nota en la cabecera, sin reescribir la historia.
