# Project-Level Rules

> Project-specific specialisation and corrections. Loaded after `org.md` and
> `team.md` as strict-additive guidance; contradictions with broader policy
> are rejected. Populated by practices-discovery and the self-learning loop.
>
> Use sparingly: most teams don't need a project layer. Reach for it
> only when this specific project needs stable, durable guidance beyond the
> team practice (for example, package-specific release checks or an additional
> regression suite for a legacy component).

## Way of Working

<!-- Project-specific specialisation. Example: -->
<!-- This monorepo requires package-scoped branch names and a package owner -->
<!-- review in addition to the team's normal merge policy. -->

## Walking Skeleton

<!-- Project-specific specialisation. Example: -->
<!-- The walking skeleton must exercise the legacy service adapter as well -->
<!-- as the new service boundary. -->

## Testing Posture

<!-- Project-specific specialisation. -->

- La GPU es opcional: el sistema y las suites de niveles 0 y 1 funcionan completos en CPU; las pruebas que requieren GPU (máquina de hasta 4 GPU y 32 GB de RAM) se agrupan en una etapa separada que corre a demanda. (learned 2026-10-02) <!-- cid:261002-veridicus-mvp:practices-discovery:c8177cec18b3a1ab416d585839f49f063e1b8e9bb5b1dc1e2af273732a278cca -->

- Los NFR de calidad (IA, MTTV, latencia, cobertura) no se escriben como historias; quedan diferidos a NFR Requirements y Build and Test. (learned 2026-10-02) <!-- cid:261002-veridicus-mvp:user-stories:015afe962524881fea600233bba4a427cd1fca4eebaeb8bff20ecbf7972213b1 -->

## Guard Policy

<!-- Project-specific. Mode: strict, relaxed, or off. Strict here holds for every intent and cannot be changed from chat. A section under the retired Change Control heading, written by an earlier release, is still read. -->

## Deployment

<!-- Project-specific specialisation. -->

## Code Style

<!-- Project-specific specialisation. -->

## Tech Stack

<!-- Technology choices locked for this project. -->

## Decided

- **QUÉ:** Veridicus, módulo de entrevista forense que contrasta testimonios orales de comparecientes con un marco de verdad documental y propone hallazgos de incongruencia con su Cadena de Pensamiento (CoT); la fuente única de requisitos es `specs/prd.md` (con `pvb.md`), nunca una copia.
- **POR QUÉ:** reducir la fatiga analítica y la revictimización en justicia transicional (Colombia) sin emitir veredictos de veracidad y sin que datos sensibles salgan del clúster local (PRD Segmentos 2 y 6).
- **CÓMO:** microservicios en Kubernetes local (todo funciona en CPU; GPU solo como perfil opcional para evaluación y demo), Whisper local, PostgreSQL + pgvector con CloudNativePG, cola Redis asíncrona, GitOps con PR y evidencia; entregado por los módulos 6–8 del curso (PRD Segmento 13).

<!-- Decisions made in earlier stages that should not be re-asked. -->
<!-- Format: DECIDED: [decision] (Stage [slug], [date]) -->

## Scope Overrides

<!-- Custom scope rules for this project. -->

## Forbidden

<!-- Populated by practices-discovery affirmation gate. -->
<!-- Format: NEVER [behavior] (affirmed [date]) -->
<!-- Example: NEVER throw exceptions across service layer boundaries (affirmed 2026-05-17) -->

- NEVER guardar datos reales (testimonios, audios, nombres o expedientes) en el repositorio ni en la CI: solo datos sintéticos (afirmada 2026-10-02). (affirmed 2026-10-02)

- NEVER versionar valores de Secret, archivos `.env`, `kubeconfig` ni claves privadas (afirmada 2026-10-02). (affirmed 2026-10-02)

- NEVER ejecutar migraciones de esquema al arrancar un pod: toda migración corre como un `Job` aparte que entra por su propio PR (afirmada 2026-10-02). (affirmed 2026-10-02)

## Mandated

<!-- Populated by practices-discovery affirmation gate. -->
<!-- Format: ALWAYS [behavior] (affirmed [date]) -->
<!-- Example: ALWAYS use Result<T,E> for fallible operations in service layer (affirmed 2026-05-17) -->

## Corrections

<!-- Project-specific corrections from human feedback. -->
<!-- Format: NEVER/ALWAYS [behavior] (learned [date]) -->
- ALWAYS leer las respuestas de los archivos de preguntas tanto en la misma línea de `[Answer]:` como en la primera línea no vacía siguiente; el humano suele escribirlas debajo. (learned 2026-10-02) <!-- cid:261002-veridicus-mvp:practices-discovery:467512cff48e83455ac80ffadca31cb414ec289375023f754a1c135e748fc925 -->
- En etapas con varios colaboradores, consolidar sus preguntas en una sola entrevista sin duplicados, y dejar los detalles finos para la etapa que los convierte en requisitos medibles. (learned 2026-10-02) <!-- cid:261002-veridicus-mvp:practices-discovery:e33bba909847029f3684a595bd16b81c5635816003fdf5841986d015e9e9b7f9 -->
- Si un archivo quedó a nombre de root tras editarlo desde el host, reemplazarlo por una copia idéntica verificada por SHA-256 antes de modificarlo, y avisar al humano. (learned 2026-10-02) <!-- cid:261002-veridicus-mvp:practices-discovery:a80ba74d7856b962f646f365ad379c8aac5b5106af8462c71999c1d8599f358d -->
- Cuando una respuesta de una etapa cambia un insumo (PRD, PVB, memoria), corregir el original en un commit propio antes de integrar la etapa. (learned 2026-10-02) <!-- cid:261002-veridicus-mvp:practices-discovery:3e8a40706c6cfd00ea2794ddbf7d5fe278398ef28ae968ea50447bc8225a41a0 -->
- La IA califica cada afirmación frente al marco de verdad solo como «congruente», «incongruente» o «no documentada», con su CoT, como sugerencia editable; nunca «falso», «verdadero» ni «miente» (AUTONOMIA-03 se mantiene, decisión de Practices Discovery 2026-10-02). (learned 2026-10-02) <!-- cid:261002-veridicus-mvp:practices-discovery:27baeece2ecd93b63f6373e00639df27d40219e3b956f0629289e965609efa79 -->
- Los archivos se intercambian entre host y contenedor con `docker cp`: si un archivo no se puede escribir, copiarlo a una ruta ignorada por git (`docker/.state/intercambio/`) para que el humano lo edite y lo devuelva, y luego moverlo a su ubicación definitiva; si hay archivos de root que no se pueden añadir a git, avisar de inmediato para corregirlos desde el host. (learned 2026-10-02) <!-- cid:261002-veridicus-mvp:practices-discovery:be9e63902ca25f9588247bfa3575271753974a8364c33551c62a5ea397bff7f7 -->
- Un insumo citado sin ruta (p. ej. `pvb.md`) se lee como el archivo de la raíz del proyecto; ante diferencias con el PVB manda `specs/prd.md` (nota H6 y `docs/coherencia-insumos.md`). (learned 2026-10-02) <!-- cid:261002-veridicus-mvp:requirements-analysis:4d1bfe642d2e18dfbe6c5854cc0868e4f063e6203f99df97e122094d67b28747 -->
- Solo una afirmación calificada «incongruente» con similitud en o por encima del umbral produce alerta; «congruente» y «no documentada» nunca la producen. (learned 2026-10-02) <!-- cid:261002-veridicus-mvp:requirements-analysis:b0f89ef151ebf2f5f69666a62f0e55ec3ef649c57ea81f3093a1de4fe8a9e96f -->
- No volver a preguntar lo que ya deciden el PRD y las 19 decisiones de `docs/coherencia-insumos.md`; preguntar solo lo que falta para criterios medibles. (learned 2026-10-02) <!-- cid:261002-veridicus-mvp:requirements-analysis:9f8c3fdf1c0d4d56371a54647353577cb1847b1cd75170a20a99df239be483f3 -->
- Como el scope `classic` omite Ideation, cada requisito se traza a un segmento del PRD (S1–S13), a una regla AUTONOMIA o a una respuesta de la etapa, y su origen queda documentado. (learned 2026-10-02) <!-- cid:261002-veridicus-mvp:requirements-analysis:2bfb7fd323d0d40cc8f495b18fc543b2e068e797412e7a1a173e125f4604dc39 -->
- Las métricas de adopción del PRD (uso semanal > 85 %, desestimación < 15 % en producción) son hipótesis de producto para el TG, no criterios de aceptación del MVP. (learned 2026-10-02) <!-- cid:261002-veridicus-mvp:requirements-analysis:4f04d2dda770fa835296aa00d4535f74ff82f251ed7800db703f55d8a188ab0b -->
- En una mob, las objeciones que un experto puede resolver se integran sin ronda 2; solo las de criterio (alcance, riesgo, prioridad) se preguntan al humano. (learned 2026-10-02) <!-- cid:261002-veridicus-mvp:user-stories:24646d48e7d4b055ecc0b03ed395cf809e732015de983801ad08361b1a140d6a -->
- No editar un artefacto de AI-DLC ya aprobado: las decisiones que lo precisan se registran en una tabla del artefacto de la etapa actual y el humano decide en la aprobación si se actualiza el original. (learned 2026-10-02) <!-- cid:261002-veridicus-mvp:user-stories:e2aaf3f291e4355c3bfc5cc35be21fdebeb957adbf891d55019f63aed6b15ecc -->
- Partir en User Stories las historias grandes (como umbral frente a paquete de traspaso), porque Units Generation dimensiona con historias y no con criterios. (learned 2026-10-02) <!-- cid:261002-veridicus-mvp:user-stories:e3b459d8722232ac75bd11f7b98748718cb2624407f37713375678b851ee33c1 -->
- La «CoT interrumpida» del Hecho No Documentado la produce el sistema de forma determinista, sin llamar al LLM, porque la guardia del umbral decide antes que el juez. (learned 2026-10-02) <!-- cid:261002-veridicus-mvp:user-stories:a5d1c5ece2de99f25b7a0e630d6f02dba5342bbcc64feaf9ca1a9b0ca10cf91b -->
- Un ajuste visual «configurable» (p. ej. los colores de estado) se implementa como tokens CSS en un único archivo que solo cambia por PR y que protege una prueba de contraste y de distinción en CI; nunca como un control de la consola. (learned 2026-10-02) <!-- cid:261002-veridicus-mvp:refined-mockups:f49ae6f0db137bc2d832361d63f518e05102682f335330bf6eb771164f209db5 -->
- Sin bocetos de Ideation (scope `classic`), las pantallas se diseñan desde `stories.md` y `requirements.md`, y las preguntas de diseño solo cubren lo que las historias no deciden. (learned 2026-10-02) <!-- cid:261002-veridicus-mvp:refined-mockups:0f903b5d671ec502a1272ce31c978d9ae7103e37a736e96ffe6e43d79821d18b -->
- Las maquetas se entregan como wireframes ASCII de fidelidad media-alta en Markdown (no Figma): el humano revisa en texto y el aspecto final lo fijan los tokens. (learned 2026-10-02) <!-- cid:261002-veridicus-mvp:refined-mockups:53dee12f909730c472c965691966d4ac2594a7a474618e364cf262f2532d2b1b -->
- El Paquete de Contexto de Traspaso es un panel no modal que no atrapa el foco, para leer la transcripción a la vez; solo las confirmaciones irreversibles son modales. (learned 2026-10-02) <!-- cid:261002-veridicus-mvp:refined-mockups:4b20da09c2b40bdd2fb0ba470cd96752dcb586feacc8026d1b77a7a0cbc062a7 -->
- Una petición asíncrona con respuesta por cola (turno → resultado, audio → texto) se modela como una sola dependencia del solicitante hacia el que responde; la respuesta no es una llamada de vuelta. (learned 2026-10-02) <!-- cid:261002-veridicus-mvp:domain-design:2baa9b827195d4663df21b39c0268fefc2f697b041898f621fa4c357e351b67d -->
- Cuando las historias ya fijan una decisión de arquitectura, se registra como ADR en la etapa de diseño (citando el AC de origen) sin volver a preguntarla. (learned 2026-10-02) <!-- cid:261002-veridicus-mvp:domain-design:2ffbcc12343e7274bb752143e9a21bb1b1882fcbaf251b45cc2f38ef3d24cc4b -->
- La autorización por dueño de la sesión se aplica en la fachada única ConsoleApi y no en HumanReview, para no crear un ciclo de dependencias; toda entrada futura debe repetir la verificación. (learned 2026-10-02) <!-- cid:261002-veridicus-mvp:domain-design:0a7ee8b5e626c0a92f943e726a4f5e3563b4c09e559875768767250e4dc9051c -->
- «La primera unidad del plan es el flujo de texto» (team-practices) se respetó como rebanada vertical U4 text-flow (learned 2026-10-02) <!-- cid:261002-veridicus-mvp:units-generation:f0e0306e0e1d3dbdcb1dc014d1a4b1390a882582e0c677615ebef8ca39a4a00c -->
- US10.6 (propuesta de umbral AIR) quedó en platform, pero leyendo una métrica cuyo nombre fija contracts, para que platform no dependa de human-review y no aparezca un ciclo. (learned 2026-10-02) <!-- cid:261002-veridicus-mvp:units-generation:7ba9a4831d650e0674793d8a576c8c7972be65f8e8a00a2c2b537d8d3cda2d7e -->
- La indexación de escenarios corre en session-api y no en semantic-agent: así el evaluador conserva su usuario de base de datos de solo lectura (AC3.3.2) aunque los embeddings se calculen en dos procesos. (learned 2026-10-02) <!-- cid:261002-veridicus-mvp:units-generation:0a24ecfce894ac1b9428475771f88418954d269d85be89f6ad27682807ce92a4 -->
- Las fronteras en proceso dentro de session-api (C10–C12) se trataron como contratos aunque no crucen la red, porque unen módulos de unidades distintas (U4, U5, U7) y la respuesta P4 pidió interfaces tipadas. (learned 2026-10-02) <!-- cid:261002-veridicus-mvp:contract-design:bc068207530e090f5467e4f48744325303b93b0263f90d2c97a11a86b981a03e -->
- Los hallazgos R-02 y R-03 de Units Generation se resolvieron en el contrato (ronda 1 abierta por propose; métricas AIR emitidas por U5) y se anotaron en una tabla para el humano, sin editar unit-of-work.md ya aprobado. (learned 2026-10-02) <!-- cid:261002-veridicus-mvp:contract-design:46da173e2f17b94a77f2dd503f8804c23be084e4338fe718657a8eb09972eb6f -->
- El audio viaja en base64 dentro del Redis Stream (C5) para no compartir un volumen entre pods; queda como pregunta abierta cambiar a una referencia a volumen si el tamaño máximo lo hace inviable. (learned 2026-10-02) <!-- cid:261002-veridicus-mvp:contract-design:a46656a1139d217c33411d57662453beedc646c71de3039a18cb346cf5b58ed8 -->
- El Golden Dataset y la configuración de GitHub se tratan como tareas previas al primer Bolt, no como Bolts: no pertenecen a ninguna unidad del grafo aprobado y no cambian el orden de unidades. (learned 2026-10-02) <!-- cid:261002-veridicus-mvp:delivery-planning:195076b5d98be535d6c2abac978d3c89ec2d99cf5039c1fa9550caba114d09b8 -->
- Sin WSJF formal (P4 = A): el orden ya lo fijan la regla del flujo de texto, el grafo, la demo de la sustentación y los módulos 6–8 (learned 2026-10-02) <!-- cid:261002-veridicus-mvp:delivery-planning:69b4b6dd5b7fb5a66391484bfbf5c86d3dac3236575de20a6c39e11ccefa2ebe -->
- Plataforma justo después del flujo de texto (P2 = A) y no dentro de él: el flujo de texto se prueba en contenedores (niveles 0–2) y el despliegue y la NetworkPolicy se alinean con los módulos 6–7 (learned 2026-10-02) <!-- cid:261002-veridicus-mvp:delivery-planning:f6c9512a8cff1a50415cdefa333a3756a570fc20c4a0a29df763d449fc78cd2c -->
- En una unidad de tipo spec, las «entidades» son los documentos de contrato y los datos que describen; U1 no tiene comportamiento en ejecución, así que functional-spec.md documenta los flujos de validación y de cambio de contrato (F1–F6) en lugar de casos de uso. (learned 2026-10-03) <!-- cid:261002-veridicus-mvp:functional-design:5d9d96e1a30f1fe27134d8d787d1b22ed1e4bfffbfc06f09f701f37f13b15dfe -->
- La comprobación de «sesiones pendientes» del cambio de rol (P3) va en ConsoleApi y no en IdentityAccess, con el mismo criterio de ADR-009, para no crear dependencia de IdentityAccess hacia InterviewSession; hasta que U4 cree la tabla de sesiones, el puerto devuelve 0. (learned 2026-10-03) <!-- cid:261002-veridicus-mvp:functional-design:689adbf52e3f9d7e3b93c915c5bbda1ad24d1620416482bfe5f76d7fdaed4fc8 -->
- El Paquete de Contexto de Traspaso es uno por intento de turno (C3 trae un solo handoff_package): su fragmento es el texto del turno, con la lista de afirmaciones no documentadas y los 3 pasajes distintos más cercanos de esas afirmaciones. (learned 2026-10-03) <!-- cid:261002-veridicus-mvp:functional-design:5360e36f1c702465667eba7d0abd109a42b48d16a1a395caa093d3a06ce51cd1 -->
- La herencia de decisiones entre rondas que ADR-007 dejó a esta etapa se fijó como «estado vigente»: la última decisión de la ronda o, si no hay, el estado vigente en la ronda bloqueada de la que parte la corrección. (learned 2026-10-03) <!-- cid:261002-veridicus-mvp:functional-design:84dc6c1c8daffc6b73a4804e845593a280a45f1b9bcd9ebfd8e02cc15dbeed34 -->
- Las líneas del entrevistador se guardan como turnos de contexto (role interviewer) que no se evalúan pero sí cuentan como turnos previos del paquete (P2 = A). (learned 2026-10-03) <!-- cid:261002-veridicus-mvp:functional-design:e39eb184bd4bc3289c337f4fefa9e62557ddc17ac9f8c36f641a2c6a809de474 -->
- Una afirmación cuyas dos lecturas no coinciden queda «no documentada» y va al paquete (P2 = A), así el analista ve la discrepancia en vez de perderla. (learned 2026-10-03) <!-- cid:261002-veridicus-mvp:functional-design:0404f2396d921d8230a9b4c635474d1564bea7094a0fe455ab9a5c298edbc639 -->
- Los embeddings externos también se enmascaran (BR1.4); como los pasajes del escenario pasan por el mismo enmascarado, la comparación por similitud conserva sentido. (learned 2026-10-03) <!-- cid:261002-veridicus-mvp:functional-design:b9e9acc798605e27590bda2133ee2fbc7112dda52f2788eb0dc512bc5137b068 -->
- Finalizar desde `suspended` se permite (U6 lo dejó a U7): una sesión suspendida y abandonada se podría cerrar sin reanudarla. (learned 2026-10-03) <!-- cid:261002-veridicus-mvp:functional-design:bb2117916b761ed7ed334038c84afc25d17337358050693d7ac8f3b7c91cabde -->
- AC6.2.2 se cubre con un code nuevo `report.not_consolidated`, porque la descarga va por versión y no existe versión antes de consolidar. (learned 2026-10-03) <!-- cid:261002-veridicus-mvp:functional-design:3efdff9448f48b31e41e18d657c973a86fc5b960a4f53684a797e00c37d5da81 -->
- La consola codifica a WAV mono de 16 kHz porque el navegador graba en su formato nativo y el contrato solo admite WAV o MP3. (learned 2026-10-03) <!-- cid:261002-veridicus-mvp:functional-design:6930c8cacf68cbb60b30b66a00cad511213c8594f02ed60f85d90e7d93a6b43d -->
- Las decisiones P1 (delimitador «» de cita literal) y P3/P4 (catálogo de rótulos y formato de fecha nuevos) precisan contract-summary.md ya aprobado; se registraron en una tabla de functional-spec.md sin editar el original, para que el humano decida en la aprobación. (learned 2026-10-03) <!-- cid:261002-veridicus-mvp:functional-design:63df90c36e27fa54b4612ba149ddc8dc37e1884e869fa74eea8f5bb25fdba24a -->
- U3 es de tipo service y no produce frontend-components.md, pero toca M0 y M6; los estados y textos de esas pantallas quedaron en §6 de functional-spec.md, y la accesibilidad de US5.6 se cubrió con BR7.1–BR7.3 porque el mapa de historias la reparte entre unidades. (learned 2026-10-03) <!-- cid:261002-veridicus-mvp:functional-design:5e9948b2d429bca95b4586dc18fbfc391adb9fcd6c0318af2c866fff2c5ed02c -->
- El escáner de vocabulario prohibido se asignó a U4 en libs/integrity_policy con la firma scan(text, literal_sources), resolviendo el hallazgo R-01 de la revisión de U1 desde esta unidad y dejándolo en la tabla de precisiones para el humano. (learned 2026-10-03) <!-- cid:261002-veridicus-mvp:functional-design:7fba632be7b5559fc96939b09439608d2043e50faa49c24d9d90228043502394 -->
- Para cerrar el hallazgo R-02 de la revisión de U4, propose rechaza con review.round_locked cuando todas las rondas están bloqueadas, y se dejó en la tabla de precisiones que U4 limite el reintento en sesiones consolidadas. (learned 2026-10-03) <!-- cid:261002-veridicus-mvp:functional-design:66c9194891d464df51a4591b61892045d5b48b8c6ea7aef98491efad430e9247 -->
- Un rule source citaba un ID de regla de U4 y el chequeo de trazabilidad lo tomó como regla huérfana; se reemplazó por una descripción para no mezclar IDs entre unidades. (learned 2026-10-03) <!-- cid:261002-veridicus-mvp:functional-design:0c8a5135471cb18ae65805be01da6e6238541afdbe3ba80599df63f06ff15b1a -->
- El chequeo de trazabilidad pidió cubrir US5.5 y US5.6 porque el mapa de historias las cruza con U8; se añadieron BR4.1–BR4.4. (learned 2026-10-03) <!-- cid:261002-veridicus-mvp:functional-design:994252f230213e443530ede7eaf2dd811dfff945c76415573d0800738ac33059 -->
- La lista de vocabulario prohibido 1.0.0 se queda en 9 términos (P2 = A) aunque deja sin detectar flexiones como «mienten» o «falsedad»; la limitación quedó visible como escenario E14 y cada ampliación entra por su PR con control negativo. (learned 2026-10-03) <!-- cid:261002-veridicus-mvp:functional-design:e540c6dcb668f42cd67f8ad497efad3c547d85f42369bcd1523e0d90065adc5c -->
- El primer admin nace con un comando ejecutado como Job revisable que lee un Secret (P1 = A), en vez de crearse al arrancar o por migración: respeta la prohibición de migraciones al arrancar y de versionar Secrets, a costa de un paso manual en la instalación. (learned 2026-10-03) <!-- cid:261002-veridicus-mvp:functional-design:9d0d4057adf6a8da2ada9a6a2529120fc96aaed9b54c5d7f035eee2f333f1e35 -->
- Un solo llamado al juez por turno con solo las afirmaciones que pasan la guardia, en vez de uno por afirmación: menos latencia en CPU y coherente con el arreglo claims de C6, a cambio de que una afirmación mal formada invalide el turno entero (que es lo que pide FR4.2). (learned 2026-10-03) <!-- cid:261002-veridicus-mvp:functional-design:4cc3b8ff6812b25f36752a2c55f9b130082113500743d27d9b3a1b74242f76f9 -->
- El evento «CoT consultada» vale por usuario y alerta en todas las rondas (P1 = A): menos fricción en la corrección, a costa de no exigir una relectura en cada ronda. (learned 2026-10-03) <!-- cid:261002-veridicus-mvp:functional-design:bac9dcd064d70fcb2f3f5c542196a38d9dfe1b4001449c07ce1e1d89d2788d47 -->
- La división de la transcripción se repite en la consola (vista previa) y en el servidor (autoridad) con la misma especificación y los mismos ejemplos, en vez de pedir la vista previa al servidor: respuesta inmediata a cambio de mantener dos implementaciones probadas igual. (learned 2026-10-03) <!-- cid:261002-veridicus-mvp:functional-design:0c5d6f7c95e9526f3c5a26ffecfc241a438780f97cd8b25d4c65d6a70255d0c1 -->
- El indicio afectivo usa una lista versionada sin LLM (P3 = A): determinista y auditable, a costa de no captar emociones expresadas sin palabras clave. (learned 2026-10-03) <!-- cid:261002-veridicus-mvp:functional-design:b36a5fc1af11e193746ec7d3f592c289589f933bf7ce7c57d6d2b49fc25b435a -->
- Marcadores consistentes por llamada con restauración dentro del clúster (P1 = A): el juez externo puede razonar sobre quién y dónde, a costa de mantener una tabla en memoria que nunca debe registrarse. (learned 2026-10-03) <!-- cid:261002-veridicus-mvp:functional-design:6bd2f84f411fb1856e5af7755a3eef91403fb45e10ee660e3962c4d61d9fa94f -->
- Archivo antes que fila (P2 = A): nunca hay versión sin archivo, a cambio de un barrido de huérfanos al arrancar. (learned 2026-10-03) <!-- cid:261002-veridicus-mvp:functional-design:544b805a2be987f0d76aa4ef0d607747695516318042f8e08746082162ae21ff -->
- La sugerencia editada muestra IA y analista (P3 = A): más largo, pero separa lo que dijo la máquina de lo que decidió la persona. (learned 2026-10-03) <!-- cid:261002-veridicus-mvp:functional-design:c086cd9af96232fa12bf8773336d47b02204c8078313976801235b30479b35bc -->
- Sin audio guardado para reintentar (P2 = A): se pierde el reintento sobre el mismo turno a cambio de no conservar nunca audio crudo. (learned 2026-10-03) <!-- cid:261002-veridicus-mvp:functional-design:06b97ac96f6ff03cbf8e589d9f9795d61773cf83804c2c39770f44b3b3a5bdb4 -->
- Una sola ranura en el servidor del juez y un turno a la vez en semantic-agent: resultados repetibles con semilla fija, a costa de que la prueba de carga de NFR8 dure horas. (learned 2026-10-03) <!-- cid:261002-veridicus-mvp:nfr-requirements:5203cf5ffb1e2fa2c66b8a055396bf7f8d11bcd2bcd80daf19a382b81df14bdc -->
- El bloque de datos del prompt va como JSON en el mensaje user en vez de delimitadores de texto: el testimonio no puede cerrar el bloque, a costa de unos tokens más. (learned 2026-10-03) <!-- cid:261002-veridicus-mvp:nfr-requirements:b56a277f503e82ae1560e19fa721aeb368693f215e3f697fd110bac3834a30fa -->
- La atomicidad depende de open_round(for_update=True), que no está en C11 ni en el Functional Design aprobado de U7 (learned 2026-10-03) <!-- cid:261002-veridicus-mvp:nfr-requirements:549da8632cf5cadf5963d6290b4fbd3b968ffa6e350ccb4d07ea00627f6b02c0 -->
- S1 = A se leyó con la cola de todo el sistema (no solo la de la sesión), porque el juez atiende un turno a la vez para todas las sesiones (learned 2026-10-03) <!-- cid:261002-veridicus-mvp:nfr-requirements:55fe49bf1ad1fe47352055b86e4188b3fdab698b38758e5e2edb833c0a4dff2b -->
