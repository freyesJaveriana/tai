# Decisiones de arquitectura — Diseño del dominio (Veridicus)

**Revisión 2 (2026-11-06), segunda pasada por el cambio 01 (DT27) y la adenda 02.** Ajustada el mismo
día con los hallazgos R-01 a R-05 de la revisión de arquitectura (ADR-003, ADR-007, ADR-008, ADR-013 y
ADR-016).

**Insumos.**
- `components.md` de esta etapa.
- Requisitos: `inception/requirements-analysis/requirements.md` (requirements, revisión 2) y
  `requirements-adenda-02.md`.
- Historias: `inception/user-stories/stories.md` (stories) y `stories-adenda-02.md`.
- Prácticas: `inception/practices-discovery/team-practices.md` (team-practices).
- Otros documentos: `docs/iteracion2.md` §2.4 y `docs/validacion-zine/reporte.md`.
- Respuestas P1–P12 y Seguimiento 1 de `domain-design-questions.md`.

**Fechas.** ADR-001 a ADR-009 son del 02/10/2026; ADR-010 a ADR-017, del 06/11/2026. Las ADR que cambian
en esta pasada llevan la marca **Revisada 2026-11-06**, y su versión anterior queda resumida en
«Antes».

| ADR | Título | Origen | Estado |
|---|---|---|---|
| ADR-001 | Núcleo partido en InterviewSession, HumanReview y ReviewReport | P1 | Vigente (nombre actualizado, P12) |
| ADR-002 | El resultado de la corrida vuelve por la cola de resultados | P2 | Revisada 2026-11-06 |
| ADR-003 | Cada componente es dueño de su historial de solo inserción | P3, A-2, R-01, R-02 | Revisada 2026-11-06 |
| ADR-004 | Una sola fachada (ConsoleApi) para la consola | P4 | Vigente |
| ADR-005 | Toda llamada a un modelo pasa por ModelGateway; un destino externo, solo detrás del anonimizador | P5, P7, DT18 | Revisada 2026-11-06 |
| ADR-006 | El trabajador no tiene estado: la instantánea del perfil viaja en el mensaje | FR3.1, FR14.2, FR13.1 | Revisada 2026-11-06 |
| ADR-007 | Las decisiones de revisión pertenecen a una ronda de revisión | FR6.1, FR7.5, R-01 | Revisada 2026-11-06 |
| ADR-008 | IntegrityPolicy como biblioteca compartida de reglas puras | FR6.4, VE-01, VE-02, VE-05, R-03 | Revisada 2026-11-06 |
| ADR-009 | La autorización por dueño de sesión se aplica en ConsoleApi | FR1.2, ADR-004 | Vigente (tres roles) |
| ADR-010 | Biblioteca sin infraestructura, partida en IncoherenceAnalyzer y AnalyzerCli | DT26, P6 | Nueva |
| ADR-011 | Anonymizer es un componente propio, único con salida a internet | P7, DT18 | Nueva |
| ADR-012 | ExecutionProfiles sin estado; los perfiles solo cambian por PR | DT21, P8 | Nueva |
| ADR-013 | InterviewSession guarda corridas y llamadas, y bloquea la sesión ante un incidente | P9, VE-14, R-04 | Nueva |
| ADR-014 | ResearchReports propio, que guarda solo cifras | P11, FR13.5 | Nueva |
| ADR-015 | ForensicReport pasa a ReviewReport, con hash por exportación | P12, VE-03, VE-13, A-3 | Nueva |
| ADR-016 | Protocolo ético en dos niveles: el analizador sin rebaja y la consola como demostración | P10, Seguimiento 1, A-2 | Nueva |
| ADR-017 | El contrato común es una fuente externa, con el consentimiento dentro | DT17, A-4 | Nueva |

---

## ADR-001: Núcleo partido en InterviewSession, HumanReview y ReviewReport

**Context.** Tres partes del núcleo cambian a ritmos distintos: la sesión con sus turnos, las sugerencias
de revisión, y la consolidación con el reporte. Dos de ellas son módulos guardia de AUTONOMIA-03 con
100 % de ramas (team-practices): la máquina de estados de la decisión y la consolidación con SHA-256.
Mezclarlas en un mismo bloque hace más difícil aislar y medir esas guardias.

**Decision.** Tres componentes, según la respuesta P1 = A:
- `InterviewSession`: sesión, turnos, reanudación y, desde la revisión 2, corridas.
- `HumanReview`: sugerencias, rondas y decisiones.
- `ReviewReport`: consolidación, versiones del reporte y exportación. Antes se llamaba `ForensicReport`;
  se renombró por P12 (ver ADR-015).

**Consequences.**
- Positivas: cada módulo guardia vive en un componente con una sola razón de cambio, y sus pruebas de
  100 % de ramas no arrastran código ajeno. Las dependencias van en una sola dirección: ReviewReport
  lee de HumanReview e InterviewSession, nunca al revés.
- Negativas: consolidar exige coordinar tres componentes en una sola transacción: leer el estado de la
  sesión, bloquear la ronda y escribir la versión. Functional Design debe fijar esa transacción y la
  regla de «una sola consolidación gana».
- Seguridad y cumplimiento: cada guardia tiene un dueño y una suite propia, lo que facilita demostrar
  AUTONOMIA-03.

**Alternatives Rejected.**
- Dos componentes (`InterviewSession` + `Review` con consolidación): junta dos guardias distintas y hace
  que un cambio en el reporte toque la máquina de estados de la decisión.
- Un componente `Session`: concentra todas las reglas y todos los cambios. Es el más simple al principio,
  pero el más difícil de probar por partes.

## ADR-002: El resultado de la corrida vuelve por la cola de resultados

**Revisada 2026-11-06.** *Antes:* `SemanticEvaluation` publicaba la evaluación de un turno. *Ahora:*
`AnalysisWorker` publica la salida del contrato común de una corrida.

**Context.** Alguien debe persistir la corrida, sus llamadas y sus hallazgos. El trabajador que maneja el
testimonio y el prompt no debe tener permisos de escritura en la base. La corrida es asíncrona y un
trabajador puede morir a mitad de una corrida.

**Decision.** `AnalysisWorker` publica la salida del contrato común en una cola Redis, con un contrato de
mensaje versionado en `contracts/`. `InterviewSession` la consume, la valida contra el contrato y la
persiste de forma idempotente por ID de corrida. Luego entrega los hallazgos a `HumanReview`. Respuesta
P2 = A. En el grafo, la flecha va solo de InterviewSession a AnalysisWorker: el resultado es la respuesta
de esa interacción, no una llamada de vuelta.

**Consequences.**
- Positivas: el trabajador no tiene usuario de base de datos. La entrega al menos una vez con
  idempotencia tolera la caída del trabajador. El mismo patrón sirve para la transcripción de voz.
- Negativas: hay dos contratos de cola que versionar (corrida y resultado) y un consumidor más que probar
  en nivel 1. Un mensaje mal formado se rechaza sin crear filas.
- Seguridad y cumplimiento: el resultado viaja por Redis dentro del clúster. Contiene testimonio, así que
  Redis queda bajo la `NetworkPolicy` de salida denegada (AUTONOMIA-04).

**Alternatives Rejected.**
- Una API interna de InterviewSession llamada por el trabajador: crea un ciclo y pierde la reentrega
  automática si InterviewSession no responde.
- Escritura directa en la base desde el trabajador: el proceso que maneja el testimonio y el prompt
  tendría permisos de escritura.

## ADR-003: Cada componente es dueño de su historial de solo inserción

**Revisada 2026-11-06.** *Antes:* sin excepciones al borrado. *Ahora:* añade la excepción del Job de
retención (A-2) y los historiales nuevos.

**Context.** NFR11 y FR1.3 exigen historiales con actor y hora no nulos y sin `UPDATE` ni `DELETE` para el
usuario de la aplicación. VE-12 exige borrar las sesiones vencidas y su reporte, y A-2 fija un `Job` de
retención como la única vía de borrado.

**Decision.** Cada componente guarda el historial de sus entidades en tablas de solo inserción, junto a la
entidad. La revisión 2 suma ModelCall, AnonymizationIncident, ObservationsView, ReportExport,
AnalystAcknowledgement, AccessLogEntry y RetentionAct. Una convención común y una prueba común de
nivel 1 verifican todas las tablas. La convención es: columnas `actor` y `at` no nulas, y permisos sin
`UPDATE` ni `DELETE`. El Job de retención tiene un usuario de base de datos propio, el único con
`DELETE`, y pide a cada componente dueño que borre lo suyo. El orden es el inverso de las referencias:
ProblemReport; ReportExport y ReportVersion, de la más nueva a la más antigua; ObservationsView,
ReviewDecision, ReviewSuggestion y ReviewRound; y por último los datos de InterviewSession. Para que ese
orden exista, ninguna referencia entre entidades forma un ciclo: ReviewRound no apunta a ReportVersion
(ADR-007, R-01). RetentionAct y AccessLogEntry guardan los IDs sin clave foránea. Respuesta P3 = A,
decisión A-2 y hallazgos R-01 y R-02.

**Consequences.**
- Positivas: el historial se escribe en la misma transacción que el cambio, y cada componente sigue
  siendo dueño de sus datos. Una prueba demuestra que el usuario de la aplicación no puede borrar y que
  el del Job sí.
- Negativas: no hay una vista única de «todo lo que pasó». FR7.5 (la versión anterior se conserva
  intacta) vale solo mientras dure la retención.
- Seguridad y cumplimiento: la inmutabilidad la hace cumplir la base de datos, no solo el código. De una
  sesión borrada sobreviven solo el acta y el registro de acceso, porque solo tienen IDs. ProblemReport
  se borra primero, porque su nota puede traer testimonio (DD-04). La prueba con reloj simulado
  (AC15.7.2) comprueba que no queda ninguna otra fila de la sesión.

**Alternatives Rejected.**
- Un componente central `AuditTrail`: añade una dependencia de todos hacia él y una escritura fuera de la
  transacción del cambio.
- Borrado criptográfico o lápida para la retención (A-2): el primero exige gestionar claves sin KMS y el
  segundo también es un `UPDATE`.
- Claves foráneas diferidas para tolerar referencias circulares (R-01): ata el diseño a una función de
  PostgreSQL y conserva un acoplamiento de HumanReview hacia ReviewReport que el grafo no declara.
- Vaciar la nota de ProblemReport y conservar la fila (R-02): añade un `UPDATE` al Job, que solo borra.

## ADR-004: Una sola fachada (ConsoleApi) para la consola

**Context.** La consola muestra datos de ocho componentes. Exponer cada uno al navegador multiplica las
superficies que deben autenticar, autorizar y traducir errores a Problem Details en español.

**Decision.** `AnalystConsole` solo habla con `ConsoleApi`, que delega en los demás componentes. El
navegador nunca llama al trabajador, al transcriptor ni al anonimizador. Respuesta P4 = A.

**Consequences.**
- Positivas: hay un solo lugar para varias cosas: el token, la matriz de tres roles (FR1.2), el registro
  de acceso (ADR-016), la traducción de errores y el OpenAPI que prueba que no hay rutas de escritura de
  configuración (FR9.2).
- Negativas: ConsoleApi puede crecer como capa de composición. Debe mantenerse delgada, sin más reglas de
  negocio propias que la autorización.
- Seguridad y cumplimiento: la superficie expuesta es una sola API.

**Alternatives Rejected.**
- La consola llama a cada componente: más rutas que proteger, CORS y autenticación repetidos.

## ADR-005: Toda llamada a un modelo pasa por ModelGateway; un destino externo, solo detrás del anonimizador

**Revisada 2026-11-06.** *Antes:* solo destinos internos, y un destino no interno impedía arrancar. El
anonimizador (COULD) sería otro adaptador. *Ahora:* se admiten destinos externos, solo detrás de
`Anonymizer` (DT18, FR11.3). Sale `embed`.

**Context.** AUTONOMIA-04 prohíbe que salga del clúster testimonio sin seudonimizar y exige probar el
*payload* saliente. Desde el cambio 01, la primera rebanada usa un proveedor comercial (team.md, orden de
entrega). FR15.1 fija `generate(papel, mensajes, esquema)` con adaptadores nativos y uno compatible con
OpenAI.

**Decision.** `ModelGateway` es el único camino hacia el juez, el verificador, Whisper y el TTS. Antes de
todo destino externo llama a `Anonymizer` (ADR-011). Si este falla, la llamada no sale y la corrida
termina con el código del anonimizador. Cada llamada devuelve su registro, con el campo `anonimizado`
(FR15.3, VE-14). En los modelos locales, la salida JSON se fuerza con `json_schema` y el razonamiento
apagado, como fijó la validación en ZINE.

**Consequences.**
- Positivas: hay un solo punto donde probar el destino y el *payload*. Los *fakes* deterministas de los
  niveles 0 y 1 se enchufan aquí. El dominio no cambia al añadir un proveedor.
- Negativas: cada proveedor nuevo exige su adaptador y su prueba de errores tipados.
- Seguridad y cumplimiento: AUTONOMIA-04 se verifica por diseño. Ninguna llamada externa existe sin
  pasar por el anonimizador, y la `NetworkPolicy` lo refuerza.

**Alternatives Rejected.**
- Mantener solo destinos internos: contradice el orden de entrega del cambio 01 (proveedor comercial en
  la primera rebanada).
- El anonimizador como adaptador dentro de ModelGateway (ADR-005 de la revisión 1): ver ADR-011.

## ADR-006: El trabajador no tiene estado: la instantánea del perfil viaja en el mensaje

**Revisada 2026-11-06.** *Antes:* `SemanticEvaluation` recibía la instantánea del umbral y leía pasajes
con un usuario de solo lectura. *Ahora:* sale el umbral (cambio 01). El mensaje lleva la configuración
efectiva del perfil y el trabajador no tiene usuario de base de datos.

**Context.** Cada sesión queda ligada a su perfil y a su `config_sha256` durante toda su vida (FR3.1),
aunque el archivo de perfiles cambie después por PR. La biblioteca no debe depender de la base (FR13.1).

**Decision.** `InterviewSession` fija la configuración efectiva al crear la sesión. Cada mensaje de
corrida lleva esa configuración, la transcripción hasta `hasta_turno`, el tramo y el bloque de
consentimiento. `AnalysisWorker` no guarda datos ni lee la base: arma la entrada del contrato y llama al
núcleo.

**Consequences.**
- Positivas: FR3.1 se cumple por construcción tras un reinicio o un PR de perfiles. El trabajador escala
  sin coordinación y sus permisos son mínimos.
- Negativas: el mensaje de corrida crece con la transcripción entera, y su tamaño lo acota el catálogo de
  límites. Cambiarlo exige versionar el contrato del mensaje.
- Seguridad y cumplimiento: el proceso que habla con los modelos no tiene credenciales de base de datos.

**Alternatives Rejected.**
- Leer el perfil vigente del archivo en cada corrida: rompe FR3.1 tras un PR de perfiles.
- Darle al trabajador un usuario de lectura sobre sesiones y turnos: amplía permisos y contradice
  FR13.1.

## ADR-007: Las decisiones de revisión pertenecen a una ronda de revisión

**Revisada 2026-11-06.** *Antes:* la ronda de corrección guardaba `based_on_report_version_id`. *Ahora:*
la ronda no guarda la versión de partida; ReviewReport la deduce (hallazgo R-01).

**Context.** Cada versión del reporte conserva sus propios estados de hallazgos (FR7.5). Antes de
consolidar se puede cambiar entre aceptada, editada y descartada, nunca volver a pendiente (FR6.1). Nunca
hay dos copias de trabajo abiertas por sesión.

**Decision.** `HumanReview` es dueño de `ReviewRound`. La ronda 1 es la revisión inicial. «Corregir
reporte» abre (o retoma) la única ronda de corrección abierta, que parte de la versión vigente.
`ReviewDecision` pertenece a una ronda y es de solo inserción. `ReviewReport` consolida exactamente una
ronda y la bloquea. La única referencia entre las dos es `ReportVersion.round_id`. La versión de la que
parte una corrección no se guarda en la ronda: es la `ReportVersion` de la ronda bloqueada anterior, y la
deduce ReviewReport. Así el grafo de datos sigue la dirección del de componentes (ReviewReport →
HumanReview) y la retención tiene un orden de borrado válido (ADR-003).

**Consequences.**
- Positivas: cada versión del reporte apunta a una ronda cerrada con todas sus decisiones intactas.
- Negativas: la sugerencia no tiene un campo «estado» directo, así que las consultas lo calculan por
  ronda. La unión de hallazgos sin duplicar (FR4.9) debe conservar la última decisión vigente.
- Seguridad y cumplimiento: ninguna decisión humana se pierde ni se sobrescribe (AUTONOMIA-03, NFR11).

**Alternatives Rejected.**
- Guardar el estado en la propia sugerencia: una corrección borraría el estado que vio la versión
  anterior.
- Que las decisiones fueran de ReviewReport: mezclaría las dos guardias que ADR-001 separa.
- Guardar `based_on_report_version_id` en la ronda, como clave foránea o como ID sin restricción (R-01):
  la primera crea un ciclo de claves foráneas con `ReportVersion.round_id`; la segunda deja una
  referencia que la base no protege y un acoplamiento que el catálogo no declara.

## ADR-008: IntegrityPolicy como biblioteca compartida de reglas puras

**Revisada 2026-11-06.** *Antes:* vocabulario y esquemas del juez y de la alerta. *Ahora:* esquemas del
contrato común, del hallazgo y del reporte de evaluación; aviso de VE-01 excluido del escáner (A-1); y
regla de DT23 para las aclaraciones neutras (VE-05). ConsoleApi depende de IntegrityPolicy para servir
el aviso a la consola (R-03).

**Context.** Varios componentes aplican las mismas reglas y deben dar el mismo resultado:
- el escaneo de vocabulario prohibido, sobre la salida del analizador, el reporte y las cadenas de la
  interfaz;
- el esquema del hallazgo, en el núcleo, en la ingesta y en HumanReview;
- la regla de DT23, en el núcleo y en el TTS.

team-practices solo comparte código entre servicios en `libs/`.

**Decision.** `IntegrityPolicy` es un componente sin estado, publicado como biblioteca en `libs/`. Lee de
`contracts/` la lista de vocabulario, la cadena del aviso y el catálogo de límites, y expone el escáner,
los esquemas y la regla de DT23. El escáner excluye las dos citas literales, el texto del analista y la
cadena del aviso, con un control negativo para cada exclusión (A-1). La consola, en TypeScript, no lee la
biblioteca: ConsoleApi le sirve el texto del aviso y su versión, leídos de IntegrityPolicy en ejecución,
y una prueba comprueba que la consola y el reporte muestran la misma versión (R-03).

**Consequences.**
- Positivas: hay una sola definición de las reglas de AUTONOMIA-03 y AUTONOMIA-05, con un control
  negativo común.
- Negativas: cambiar la biblioteca obliga a reconstruir los servicios que la usan.
- Seguridad y cumplimiento: el reporte, la interfaz y el analizador no pueden aplicar listas distintas.

**Alternatives Rejected.**
- Copiar la regla en cada servicio: las copias divergen.
- Un servicio de validación aparte: añade una llamada de red para una función pura.
- Incrustar el aviso en la consola al compilar (R-03): la imagen de la consola y la de los servicios
  podrían quedar con versiones distintas del aviso.

## ADR-009: La autorización por dueño de sesión se aplica en ConsoleApi

**Context.** Solo el analista dueño crea corridas, cambia hallazgos, consolida o corrige (FR1.2). Ni
`admin` ni `investigador` lo hacen, y la persona entrevistada no tiene rol (VE-09). Si `HumanReview`
consultara a `InterviewSession` para conocer al dueño, aparecería un ciclo.

**Decision.** `ConsoleApi`, la única entrada (ADR-004), verifica rol y propiedad de la sesión antes de
delegar. Los componentes reciben el actor ya autorizado y registran quién y cuándo.

**Consequences.**
- Positivas: el grafo sigue sin ciclos. La matriz de tres roles se prueba en un solo lugar, con una
  prueba por celda «No» o «Solo propias».
- Negativas: cualquier entrada futura distinta de ConsoleApi tendría que repetir la verificación.
  AnalyzerCli no es una entrada del producto: no toca la base.
- Seguridad y cumplimiento: el rechazo es un `403` con Problem Details y sin filas nuevas.

**Alternatives Rejected.**
- Verificar dentro de HumanReview consultando a InterviewSession: crea un ciclo.
- Copiar el dueño en cada sugerencia: duplica un dato que puede quedar inconsistente.

## ADR-010: Biblioteca sin infraestructura, partida en IncoherenceAnalyzer y AnalyzerCli

**Context.** DT26 y FR13.1 exigen un núcleo en Python sin Redis, Kubernetes ni base de datos, que comparten
el producto, el TG (DT20) y la evaluación en ZINE (FR16). Ese núcleo hace dos trabajos que cambian por
razones distintas:
- **Analizar**: juez, verificador, permutación, modo fragmentado y la verificación determinista de
  citas, que es un módulo guardia.
- **Operarlo desde la terminal**: lotes, modo evaluación y métricas, incluida la tabla de sesgo de VE-17.

**Decision.** Dos componentes, según la respuesta P6 = A:
- `IncoherenceAnalyzer`: el núcleo que implementa el contrato común, con la verificación de citas dentro.
- `AnalyzerCli`: los lotes y el modo evaluación. Llama al núcleo igual que lo hace `AnalysisWorker`.

Una comprobación de import-linter impide que el núcleo importe infraestructura. Si la biblioteca es una
unidad desplegable propia lo decide Units Generation.

**Consequences.**
- Positivas: el núcleo se prueba sin red ni contenedores en el nivel 0. La CLI evoluciona con las
  métricas sin tocar la guardia de citas. El producto y el TG ejecutan el mismo código.
- Negativas: dos componentes que versionar juntos. Un cambio del contrato obliga a actualizar el núcleo,
  la CLI y el trabajador.
- Seguridad y cumplimiento: AUTONOMIA-05 (citas verificadas, sin resultados parciales) vive en un solo
  lugar, que usan todos los caminos.

**Alternatives Rejected.**
- Un solo componente con la CLI dentro (propuesta de `docs/iteracion2.md` §2.4): mezcla métricas y
  guardia.
- Verificación de citas como componente aparte (`QuoteVerification`): divide una regla que solo usa el
  núcleo y añade una frontera sin otro consumidor.

## ADR-011: Anonymizer es un componente propio, único con salida a internet

**Context.** Desde el cambio 01, el anonimizador es MUST y tiene reglas propias: NER local más reglas,
marcas coherentes en toda la entrevista, tabla de correspondencia solo en memoria, detección de marcas
alteradas y lista de dominios. En el clúster es el único pod con salida a internet (FR12.3). En la CLI
corre en el mismo proceso.

**Decision.** `Anonymizer` es un componente propio. `ModelGateway` lo llama antes de todo destino externo.
`Anonymizer` seudonimiza lo que sale, envía la llamada al proveedor de la lista, restaura la respuesta y
marca los hallazgos con marcas alteradas. El núcleo recibe el texto restaurado y verifica las citas contra
los turnos originales (FR4.4). En el clúster, ese mismo código es el pod `anonymizer-proxy`. Respuesta
P7 = A.

**Consequences.**
- Positivas: las pruebas de AUTONOMIA-04 tienen un dueño: el *payload* saliente, el fallo cerrado, la
  lista de dominios y la fuga cero sobre el conjunto sintético. La `NetworkPolicy` se escribe para un
  solo pod.
- Negativas: en el clúster cada llamada externa da un salto de red más. La tabla en memoria obliga a que
  la restauración ocurra en la misma llamada.
- Seguridad y cumplimiento: ningún otro componente tiene salida a internet, y ningún log ni disco guarda
  la correspondencia.

**Alternatives Rejected.**
- Un adaptador dentro de ModelGateway (ADR-005 de la revisión 1): mezcla reglas de privacidad con el
  transporte, y el pod con salida tendría todo el código de los proveedores.
- Que lo orqueste el núcleo: la biblioteca tendría que conocer el transporte, y un camino que olvidara
  llamarlo dejaría salir texto sin seudonimizar.

## ADR-012: ExecutionProfiles sin estado; los perfiles solo cambian por PR

**Context.** El perfil (DT21, FR14) se valida en cuatro lugares: la biblioteca, la CLI, el trabajador y
los servicios. Debe dar el mismo resultado en todos (FR14.3), calcular `config_sha256` (FR14.2), exigir
familias distintas en evaluación (FR14.4) y listarse en la consola (FR14.5). Solo cambia por PR (FR9.2).

**Decision.** `ExecutionProfiles` es un componente sin estado que lee el archivo versionado de perfiles y
la tabla de precios. Lo usan IncoherenceAnalyzer, AnalyzerCli, AnalysisWorker, InterviewSession y
ConsoleApi. Además, rechaza un perfil con destino externo si el bloque de consentimiento no autoriza la
transferencia (A-4). Respuesta P8 = A.

**Consequences.**
- Positivas: hay una sola validación con un control negativo por caso, y la huella es idéntica en la CLI
  y en el producto.
- Negativas: una dependencia más para cada consumidor. Cambiar el formato del archivo obliga a
  reconstruir todos los consumidores.
- Seguridad y cumplimiento: ningún consumidor puede arrancar con un destino externo sin anonimizador ni
  con una clave ausente. La consola no ofrece ninguna ruta para cambiar perfiles.

**Alternatives Rejected.**
- Dentro de IncoherenceAnalyzer: ConsoleApi dependería del núcleo solo para listar perfiles.
- Dentro de ModelGateway: mezcla configuración aprobada con transporte, y la validación de familias o de
  consentimiento no es asunto del transporte.

## ADR-013: InterviewSession guarda corridas y llamadas, y bloquea la sesión ante un incidente

**Context.** La biblioteca no persiste nada. En el producto hay que guardar cada corrida y sus llamadas,
de solo inserción (FR15.3, NFR11). También hay que detectar el incidente de VE-14: una llamada a un
proveedor comercial con `anonimizado: false` bloquea la sesión. La CLI usa la misma biblioteca sin
sesión, así que la regla no puede vivir solo en el producto (R-04).

**Decision.** `InterviewSession`, al consumir el resultado (ADR-002), guarda `AnalysisRun`, `ModelCall` y
`DiscardedCandidate`, y pasa los hallazgos a `HumanReview`. El corte lo decide la biblioteca:
`IncoherenceAnalyzer` aborta la corrida ante una respuesta externa con `anonimizado: false` y la deja en
`estado: error`, `codigo: anonymizer.incident` y hallazgos vacíos. La CLI detiene el lote y termina con
un código de salida propio. InterviewSession, al recibir ese código (o una llamada sin anonimizar en el
registro), bloquea la sesión con `anonymizer.incident`, rechaza corridas nuevas y registra un
`AnonymizationIncident`. Respuesta P9 = A y hallazgo R-04.

**Consequences.**
- Positivas: la corrida, su sesión y su incidente se escriben en la misma transacción. El estado de la
  sesión y el bloqueo tienen un solo dueño.
- Negativas: InterviewSession suma diez entidades y es el componente más grande. Functional Design debe
  cuidar su partición interna.
- Seguridad y cumplimiento: un incidente de anonimización detiene la corrida en la biblioteca, tanto en
  la CLI como en el producto, y en el producto detiene además la sesión.

**Alternatives Rejected.**
- Un componente aparte, `RunLedger`: añade una llamada dentro de la ingesta, y el bloqueo de la sesión
  seguiría en InterviewSession, con el riesgo de que el registro y el bloqueo queden en transacciones
  distintas.
- Detectar el incidente solo en la CLI y en InterviewSession (R-04): la regla quedaría duplicada, y un
  tercer consumidor de la biblioteca podría omitirla.

## ADR-014: ResearchReports propio, que guarda solo cifras

**Context.** El rol `investigador` sube los reportes JSON de la CLI, los lista, los ve y los compara
(FR13.5, US12.6, US12.7). Nunca se guarda texto de transcripciones, hallazgos ni citas (NFR12).

**Decision.** `ResearchReports` es un componente propio, con su entidad `ResearchReport`. Valida el esquema
del reporte subido, descarta el texto antes de guardar y no lanza análisis. Respuesta P11 = A.

**Consequences.**
- Positivas: la regla de no guardar texto tiene un solo dueño y su prueba *canary*. Otro rol tiene otro
  ciclo de vida.
- Negativas: un componente más en la consola, para una pantalla de solo consulta.
- Seguridad y cumplimiento: sus datos quedan fuera de la retención, porque no tienen testimonio. El
  `analista` y el `admin` reciben `403` en sus rutas.

**Alternatives Rejected.**
- Dentro de ReviewReport: mezcla reportes con testimonio y reportes sin él, con reglas de retención y de
  roles opuestas.
- Dentro de AnalyzerCli: la CLI no tiene base de datos ni corre en el clúster.

## ADR-015: ForensicReport pasa a ReviewReport, con hash por exportación

**Context.** VE-03 cambia «reporte forense» por «reporte de revisión», y el nombre del componente es un
identificador que citan las etapas siguientes. VE-13 marca cada exportación con el usuario, así que el
archivo exportado cambia, mientras que FR7.3 exige comprobar el SHA-256 de lo descargado (A-3).

**Decision.** El componente se renombra ya a `ReviewReport` (glosario: «reporte de revisión» →
`review_report`), con la nota «antes `ForensicReport`». Respuesta P12 = A. Cada exportación es un
artefacto propio (`ReportExport`) que lleva varios datos:
- una marca visible con el usuario y la hora en la cabecera y en cada página;
- el aviso de VE-01;
- en la cabecera, el SHA-256 de la versión consolidada.

Se registra el SHA-256 del archivo exportado. Exportan solo el analista dueño y el `admin`.

**Consequences.**
- Positivas: el nombre deja de sugerir valor probatorio. La exportación se verifica con `sha256sum`, y el
  SHA-256 de la versión consolidada se conserva.
- Negativas: Units Generation debe revisar el slug de U7, y los artefactos aprobados que dicen
  «ForensicReport» quedan con el nombre anterior hasta que el humano decida (DD-09).
- Seguridad y cumplimiento: se sabe quién sacó cada copia del reporte (VE-13).

**Alternatives Rejected.**
- Conservar `ForensicReport` y renombrar todo en Units Generation: dos etapas con nombres distintos para
  el mismo bloque.
- Verificar el hash quitando la marca, o dejar la marca fuera del archivo (A-3): el primero exige un
  script y la segunda se pierde al descomprimir.

## ADR-016: Protocolo ético en dos niveles: el analizador sin rebaja y la consola como demostración

**Context.** La adenda 02 aprobada marca VE-01 a VE-17 como MUST. En la pregunta 10, el humano precisó dos
cosas: tg-veridicus es un proyecto de investigación y demostración, no de despliegue, y el analizador se
rige por los mismos principios éticos de la aplicación primaria del TG. En el Seguimiento 1 eligió A:
el analizador cumple sin rebaja y la consola demuestra el resto en un solo componente, sin compuertas que
bloqueen el uso.

**Decision.**
- **El analizador, sin rebaja.** Comprende IncoherenceAnalyzer, AnalyzerCli, AnalysisWorker, Anonymizer,
  IntegrityPolicy y la ingesta de InterviewSession. Aplica:
  - el vocabulario prohibido (VE-02) y el aviso de VE-01;
  - el bloqueo sin consentimiento y el control de la transferencia (A-4, VE-06, VE-07);
  - la validación de aclaraciones neutras (VE-05);
  - el audio solo con autorización (VE-08), y que la persona entrevistada no vea el análisis (VE-09);
  - la exportación con marca (VE-13) y el incidente de anonimización (VE-14);
  - la métrica de sesgo (VE-17).
- **La consola, como demostración.** Un solo componente, `EthicsGovernance`, demuestra el resto:
  - el reconocimiento del analista, con aviso en lugar de `403` (VE-04);
  - el registro de acceso (VE-11);
  - los reportes de problemas, con aviso en lugar de `422` (VE-15);
  - el Job de retención con su acta, que lanza el humano (VE-12, A-2), y que borra también los reportes
    de problemas, porque su nota puede traer testimonio (R-02).

  VE-16 son avisos de AnalystConsole.
- **Pausa y retirada.** VE-10 se mantiene en InterviewSession (DD-06). Que nada se encole ni se analice
  tras la retirada del consentimiento es un principio del analizador (A-4) y sigue siendo MUST aunque
  VE-10 baje. Si el humano la baja a demostración, solo dejan de ser obligatorios los estados `pausada`
  y `terminada`, con su registro, y la cancelación de lo encolado (R-05).
- **Registro de acceso.** Lo escribe ConsoleApi, no ReviewReport, para que la retención
  (EthicsGovernance → ReviewReport) no cierre un ciclo.

**Consequences.**
- Positivas: las guardias que el TG reutiliza no se rebajan. La demostración queda aislada y se puede
  retirar o endurecer sin tocar el analizador.
- Negativas: la adenda aprobada y el diseño difieren hasta que el humano decida las filas DD-01 a DD-07.
  Si se mantienen como MUST, EthicsGovernance tendría que convertir sus avisos en compuertas.
- Seguridad y cumplimiento: los datos del testimonio siguen protegidos por AUTONOMIA-04 y A-4, sin
  importar la demostración. La retención sigue siendo la única vía de borrado (ADR-003).

**Alternatives Rejected.**
- Toda la adenda como MUST, repartida en `EthicsGovernance` y `DataRetention` (opción B del
  Seguimiento 1): contradice la respuesta 10.
- Aplicar la adenda solo al analizador y retirar las VE de consola (opción C): se pierde la demostración
  del protocolo, que la respuesta 10 sí quiere.
- Repartir las VE en los componentes existentes (opción C de la pregunta 10): dispersa la demostración y
  crea un ciclo entre la retención y el reporte.

## ADR-017: El contrato común es una fuente externa, con el consentimiento dentro

**Context.** El contrato común del analizador (DT17) lo comparten Veridicus y el TG, y vive en el
repositorio principal del TG (`project.md`, Decided). A-4 pone el consentimiento en la entrada del
contrato para que la consola, la importación y la CLI lo traten igual.

**Decision.** Los esquemas del contrato común son una **fuente externa** que se copia versionada a
`contracts/`. El contrato de los mensajes de cola y el de los reportes de la CLI son propios de Veridicus.
IntegrityPolicy los publica, y Contract Design fija la versión 1.0.0 con el bloque `consentimiento`, que
aprueba el autor. Una transcripción `origen: sintetico` está exenta del bloque, con una prueba que impide
la exención con `origen: corpus`.

**Consequences.**
- Positivas: el TG y Veridicus validan lo mismo, y un cambio del contrato es explícito (versión y PR).
- Negativas: actualizar el contrato exige coordinar dos repositorios. La copia en `contracts/` debe
  comprobar su versión.
- Seguridad y cumplimiento: ninguna corrida sobre un relato real ocurre sin el registro de consentimiento
  (VE-06), tampoco desde la CLI.

**Alternatives Rejected.**
- Un contrato propio de Veridicus: el TG y el producto divergirían (DT20).
- Exentar la CLI sin control técnico, o limitar VE-06 a la consola (descartadas en A-4).
