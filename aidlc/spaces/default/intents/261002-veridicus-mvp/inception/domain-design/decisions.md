# Decisiones de arquitectura — Diseño del dominio (Veridicus)

**Insumos.** `components.md` de esta etapa; requisitos de
`inception/requirements-analysis/requirements.md` (requirements); historias de
`inception/user-stories/stories.md` (stories); prácticas de
`inception/practices-discovery/team-practices.md` (team-practices); respuestas P1–P5 de
`domain-design-questions.md`. Fecha de todas: 02/10/2026.

| ADR | Título | Origen |
|---|---|---|
| ADR-001 | Núcleo partido en InterviewSession, HumanReview y ForensicReport | P1 |
| ADR-002 | El resultado de la evaluación vuelve por la cola de resultados | P2 |
| ADR-003 | Cada componente es dueño de su historial de solo inserción | P3 |
| ADR-004 | Una sola fachada (ConsoleApi) para la consola | P4 |
| ADR-005 | Toda llamada a un modelo pasa por ModelGateway | P5 |
| ADR-006 | SemanticEvaluation sin estado, con la instantánea del umbral en el mensaje | AC2.1.2, AC3.3.2, AC4.1.2 |
| ADR-007 | Las decisiones de revisión pertenecen a una ronda de revisión | AC5.1.4, AC6.3.2, AC6.3.4 |
| ADR-008 | IntegrityPolicy como biblioteca compartida de reglas puras | AC5.5.1–AC5.5.4 |
| ADR-009 | La autorización por dueño de sesión se aplica en ConsoleApi | FR1.2, AC5.4.1, ADR-004 |

---

## ADR-001: Núcleo partido en InterviewSession, HumanReview y ForensicReport

**Context.** Sesión y turnos, sugerencias de revisión, y consolidación con reporte cambian a ritmos
distintos. Dos de ellos son módulos guardia de AUTONOMIA-03 con 100 % de ramas (team-practices): la
máquina de estados de la decisión y la consolidación con SHA-256. Mezclarlos en un mismo bloque hace
más difícil aislar y medir esas guardias.

**Decision.** Tres componentes: `InterviewSession` (sesión, turnos, reanudación y resultados por turno),
`HumanReview` (sugerencias, rondas y decisiones) y `ForensicReport` (consolidación, versiones del reporte
y descarga). Respuesta P1 = A.

**Consequences.**
- Positivas: cada módulo guardia vive en un componente con una sola razón de cambio; sus pruebas de
  100 % de ramas no arrastran código ajeno. Las dependencias quedan en una sola dirección:
  ForensicReport lee de HumanReview e InterviewSession, nunca al revés.
- Negativas: consolidar exige coordinar tres componentes (leer estado de sesión, bloquear la ronda,
  escribir la versión) en una sola transacción; Functional Design debe fijar esa transacción y la
  regla de «una sola consolidación gana» (AC6.1.6).
- Seguridad y cumplimiento: aislar la decisión humana y la consolidación facilita demostrar
  AUTONOMIA-03 ante la Oficial de Cumplimiento Ético: cada guardia tiene un dueño y una suite propia.

**Alternatives Rejected.**
- Dos componentes (`InterviewSession` + `Review` con consolidación): junta dos guardias distintas y hace
  que un cambio en el reporte toque la máquina de estados de la decisión.
- Un componente `Session`: concentra todas las reglas y todos los cambios; el más simple al principio,
  pero el más difícil de probar por partes.

## ADR-002: El resultado de la evaluación vuelve por la cola de resultados

**Context.** El usuario de base de datos del juez no puede hacer `INSERT`, `UPDATE` ni `DELETE` en
ninguna tabla (AC3.3.2). Alguien debe persistir la evaluación, el Paquete de Contexto de Traspaso y las
sugerencias. La evaluación es asíncrona y un trabajador puede morir a mitad de un turno (AC2.2.4).

**Decision.** `SemanticEvaluation` publica un mensaje de resultado en una cola Redis con contrato
versionado en `contracts/`. `InterviewSession` lo consume, lo valida contra el contrato y lo persiste de
forma idempotente por ID de turno (y número de intento); luego entrega las alertas candidatas a
`HumanReview`. Respuesta P2 = A. En el grafo de componentes la flecha va solo de InterviewSession a
SemanticEvaluation: el resultado es la respuesta de esa interacción, no una llamada de vuelta.

**Consequences.**
- Positivas: el evaluador mantiene permisos mínimos (solo lee el marco de verdad); entrega al menos una
  vez con idempotencia cumple AC2.2.4 y AC3.2.3; el mismo patrón sirve para la transcripción de voz.
- Negativas: hay dos contratos de cola que versionar (turno y resultado) y un consumidor más que probar
  en nivel 1; un mensaje mal formado debe rechazarse sin crear filas (AC2.2.3).
- Seguridad y cumplimiento: el resultado viaja por Redis dentro del clúster; contiene testimonio, así que
  Redis queda bajo la `NetworkPolicy` de salida denegada (AUTONOMIA-04).

**Alternatives Rejected.**
- API interna de InterviewSession llamada por el evaluador: crea una dependencia de vuelta (ciclo) y
  pierde la reentrega automática si InterviewSession no responde.
- Un segundo usuario de base de datos con escritura dentro del evaluador: el proceso que maneja el
  testimonio y el prompt tendría permisos de escritura, justo lo que AC3.3.2 quiere impedir.

## ADR-003: Cada componente es dueño de su historial de solo inserción

**Context.** AC8.4.1 y AC8.4.2 exigen historiales con actor y hora no nulos y sin `UPDATE` ni `DELETE`
para el usuario de la aplicación, sobre alertas, consolidaciones, versiones de reporte, umbral de sesión
y «CoT consultada». FR6.1 pide guardar estado anterior y nuevo de cada decisión.

**Decision.** Cada componente guarda el historial de sus propias entidades en tablas de solo inserción
junto a la entidad (UserChange, SessionStatusChange, ReviewDecision, CotView, ReportVersion). Una
convención común (columnas `actor` y `at` no nulas, permisos sin `UPDATE`/`DELETE`) y una prueba común
de nivel 1 la verifican en todas. Respuesta P3 = A.

**Consequences.**
- Positivas: el historial se escribe en la misma transacción que el cambio, sin posibilidad de que uno
  exista sin el otro; cada componente sigue siendo dueño de sus datos.
- Negativas: no hay una vista única de «todo lo que pasó»; si se necesita, se arma con una consulta de
  solo lectura o con el reporte consolidado.
- Seguridad y cumplimiento: la inmutabilidad la hace cumplir la base de datos (permisos y restricciones),
  no solo el código, lo que fortalece AUTONOMIA-03 y NFR11.

**Alternatives Rejected.**
- Componente central `AuditTrail`: añade una dependencia de todos hacia él y una escritura fuera de la
  transacción del cambio (riesgo de rastro incompleto).
- Historial propio más copia central: duplica datos y pruebas sin un requisito que lo pida.

## ADR-004: Una sola fachada (ConsoleApi) para la consola

**Context.** La consola muestra datos de seis componentes. Exponer cada uno al navegador multiplica las
superficies que deben autenticar, autorizar y traducir errores a Problem Details en español.

**Decision.** `AnalystConsole` solo habla con `ConsoleApi`, que delega en los demás componentes. El
navegador nunca llama al evaluador, al transcriptor ni a la base vectorial. Respuesta P4 = A.

**Consequences.**
- Positivas: un solo lugar para el token (AC8.1.4), la matriz de roles (FR1.2), la traducción de
  errores y el OpenAPI que AC8.3.1 enumera para probar que no hay ruta de escritura del umbral.
- Negativas: ConsoleApi puede crecer como capa de composición; debe mantenerse delgada (sin reglas de
  negocio propias más allá de autorización).
- Seguridad y cumplimiento: la superficie expuesta fuera del clúster es una sola API; los demás
  componentes no publican puertos hacia el navegador.

**Alternatives Rejected.**
- La consola llama a cada componente: más rutas que proteger, CORS y autenticación repetidos, y más
  difícil demostrar AC8.3.1.

## ADR-005: Toda llamada a un modelo pasa por ModelGateway

**Context.** AUTONOMIA-04 prohíbe que salga del clúster testimonio sin anonimizar y exige probar el
*payload* saliente de toda integración externa. En el MVP no hay llamadas externas y el anonimizador es
COULD (FR11.3).

**Decision.** Un puerto propio, `ModelGateway`, es el único camino hacia juez, *embeddings*, Whisper y
TTS. Sus adaptadores actuales apuntan solo a servidores internos; si la configuración trae un destino no
interno, el servicio no arranca (AC9.1.4). El anonimizador se añadirá como otro adaptador que falla
cerrado. Respuesta P5 = A.

**Consequences.**
- Positivas: un solo punto donde probar el destino y el *payload*; el dominio no cambia si un día se usa
  un modelo externo; los *fakes* deterministas de niveles 0 y 1 (team-practices) se enchufan aquí.
- Negativas: una capa más de indirección que mantener aunque hoy solo haya destinos locales.
- Seguridad y cumplimiento: hace verificable AUTONOMIA-04 por diseño, no solo por `NetworkPolicy`.

**Alternatives Rejected.**
- No modelar nada hasta decidir el anonimizador: cada componente llamaría a sus modelos a su manera y
  añadir el anonimizador después obligaría a tocar varios.

## ADR-006: SemanticEvaluation sin estado, con la instantánea del umbral en el mensaje

**Context.** Cada sesión se evalúa con el umbral vigente al crearla, aunque el servicio se reinicie con
otro (AC2.1.2). El usuario del juez no puede leer nada fuera del marco de verdad (AC3.3.2), así que el
evaluador no puede consultar la tabla de sesiones. La guardia del umbral decide antes que el juez
(AC4.1.2) y la CoT interrumpida es determinista, sin LLM (project.md).

**Decision.** `SemanticEvaluation` no guarda datos. El mensaje de turno lleva la instantánea del umbral
de la sesión y la versión del escenario; el evaluador recupera pasajes con un usuario de solo lectura,
aplica la guardia del umbral por afirmación antes de cualquier llamada al juez, y devuelve todo en el
mensaje de resultado. El umbral configurado en el despliegue solo lo lee `InterviewSession` al crear la
sesión; el cargador de configuración de cada servicio que lo necesite impide arrancar sin un valor
válido (AC4.3.1).

**Consequences.**
- Positivas: el evaluador escala sin coordinación y sus permisos son mínimos; AC2.1.2 se cumple por
  construcción; la guardia es código puro de dominio con 100 % de ramas.
- Negativas: el contrato del mensaje de turno crece (umbral, versión, turnos previos para el paquete);
  cambiarlo exige versionar el contrato.
- Seguridad y cumplimiento: AUTONOMIA-05 queda en el único componente que decide si hay alerta, antes de
  que exista una salida del juez.

**Alternatives Rejected.**
- Leer el umbral de la configuración en cada evaluación: viola AC2.1.2 tras un reinicio.
- Leer la sesión desde la base de datos: exige ampliar los permisos del usuario del juez, contra AC3.3.2.

## ADR-007: Las decisiones de revisión pertenecen a una ronda de revisión

**Context.** Cada versión del reporte conserva sus propios estados de alertas (AC6.3.4). Antes de
consolidar se puede cambiar entre aceptada, editada y descartada, nunca volver a pendiente (AC5.1.4).
Nunca hay dos copias de trabajo abiertas por sesión (AC6.3.2).

**Decision.** `HumanReview` es dueño de `ReviewRound`. La ronda 1 es la revisión inicial; «Corregir
reporte» abre (o retoma) la única ronda de corrección abierta, que parte de la versión vigente.
`ReviewDecision` pertenece a una ronda y es de solo inserción; el estado actual de una sugerencia en una
ronda es su última decisión. `ForensicReport` consolida exactamente una ronda y la bloquea.

**Consequences.**
- Positivas: cada versión del reporte apunta a una ronda cerrada con todas sus decisiones intactas;
  corregir no reescribe nada.
- Negativas: la sugerencia no tiene un campo «estado» directo; las consultas lo calculan por ronda.
  Functional Design fija cómo hereda una ronda de corrección las decisiones de la anterior.
- Seguridad y cumplimiento: ninguna decisión humana se pierde ni se sobrescribe (AUTONOMIA-03, NFR11).

**Alternatives Rejected.**
- Estado guardado en la propia sugerencia: una corrección borraría el estado que vio la versión
  anterior.
- Decisiones dueñas de ForensicReport: el reporte pasaría a depender de sí mismo para validar decisiones
  y mezclaría las dos guardias que ADR-001 separa.

## ADR-008: IntegrityPolicy como biblioteca compartida de reglas puras

**Context.** El escaneo de vocabulario prohibido se aplica a la salida del juez, al reporte y a las
cadenas de la interfaz (AC5.5.1), y los esquemas de la alerta y del juez deben ser idénticos donde se
validen (AC5.5.3, AC5.5.4). team-practices solo comparte código entre servicios en `libs/`.

**Decision.** `IntegrityPolicy` es un componente sin estado, publicado como biblioteca en `libs/`, que
lee la lista versionada de `contracts/` y expone el escáner y los esquemas. La consola usa la misma lista
en su prueba del catálogo de mensajes.

**Consequences.**
- Positivas: una sola definición de las reglas de AUTONOMIA-03; un control negativo común.
- Negativas: cambiar la biblioteca obliga a reconstruir los servicios que la usan.
- Seguridad y cumplimiento: evita que el reporte y la salida del juez apliquen listas distintas.

**Alternatives Rejected.**
- Copiar la regla en cada servicio: las copias divergen y AC5.5.1 dejaría de ser verificable en un solo
  lugar.
- Un servicio de validación aparte: una llamada de red para una función pura, sin beneficio.

## ADR-009: La autorización por dueño de sesión se aplica en ConsoleApi

**Context.** Solo el analista dueño cambia alertas, consolida o corrige (FR1.2, AC5.4.1, AC6.1.7); el
`admin` nunca. Si `HumanReview` consultara a `InterviewSession` para conocer al dueño, aparecería un ciclo
(InterviewSession ya entrega sugerencias a HumanReview).

**Decision.** `ConsoleApi`, única entrada (ADR-004), verifica rol y propiedad de la sesión antes de
delegar. `HumanReview` y `ForensicReport` reciben el actor ya autorizado y registran quién y cuándo.

**Consequences.**
- Positivas: el grafo sigue sin ciclos; la matriz de FR1.2 se prueba en un solo lugar (una prueba por
  celda «No» o «Solo propias»).
- Negativas: cualquier entrada futura distinta de ConsoleApi tendría que repetir la verificación; se
  mitiga porque no hay otra ruta desde el navegador y los trabajadores no exponen API.
- Seguridad y cumplimiento: el rechazo es `403` con Problem Details y sin filas nuevas; las pruebas de
  nivel 1 lo comprueban por cada acción.

**Alternatives Rejected.**
- Verificación dentro de HumanReview consultando a InterviewSession: crea un ciclo de dependencias.
- Copiar el dueño en cada sugerencia y verificar allí: duplica un dato que puede quedar inconsistente.
