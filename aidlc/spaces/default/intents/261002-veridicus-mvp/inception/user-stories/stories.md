# Historias de usuario — Veridicus (analizador de incoherencias del TG)

**Revisión 2 — cambio 01 (DT27, 2026-11-02).** Esta versión reemplaza la aprobada el 2026-10-02; la
anterior queda en el historial de Git. Las historias que siguen conservan su ID; las que salen quedan
como **Retirada** sin renumerar, y las nuevas toman ID nuevos (`docs/iteracion2.md` §2.2).

**Insumos.** `inception/requirements-analysis/requirements.md` (revisión 2: FR1–FR16, NFR1–NFR15), las
prácticas de team-practices (`inception/practices-discovery/team-practices.md`, corregidas por el cambio
01 en `team.md`), las personas de `personas.md` y las respuestas de `user-stories-questions.md`
(preguntas 1–8 y Seguimientos 1–6 de la primera pasada; preguntas 9–14 de la segunda).

**Formato.** «Como [persona], quiero [acción], para [beneficio]». Criterios Given/When/Then con ID
`ACx.y.z`. Prioridad MoSCoW heredada del requisito de origen; el límite final del MVP lo fija Delivery
Planning. Las épicas siguen el recorrido del usuario; la biblioteca y la CLI, los perfiles y modelos, y la
evaluación en ZINE van en épicas nuevas al final (respuesta 2).

**Personas.** P1 Analista de Verdad · P2 Administrador de plataforma · P3 Oficial de Cumplimiento Ético ·
P4 Investigador del TG (respuesta 9).

**Precisiones de Refined Mockups (2026-11-03).** Al aprobar la revisión 2 de Refined Mockups, el humano
decidió traer aquí el rol `investigador` (AC2.1.4, AC8.1.1, AC8.2.4) y las historias nuevas US12.6 y
US12.7 (tabla de precisiones de `inception/refined-mockups/mockups.md`).

## Convenciones de los criterios

- **Nivel de prueba** al final de cada criterio (team-practices, Testing Posture): `[N0]` unitaria,
  contrato o política estática, con *fakes* deterministas del `ModelGateway`, sin red; `[N1]` integración
  con PostgreSQL y Redis reales (modelos aún *fake*); `[N2]` CLI en modo evaluación sobre el conjunto
  sintético versionado en `evaluation/`, contra un perfil real, fuera de la CI; `[N3]` E2E con Playwright o
  humo; `[Manual]` verificación humana con evidencia adjunta; `[ZINE]` trabajo de SLURM que escribe el
  agente y **lanza el humano** (AUTONOMIA-01), con su salida adjunta como evidencia. Un criterio que depende
  del comportamiento real de un modelo se parte en una variante determinista y otra `[N2]`.
- **Rechazos.** Todo rechazo de la API nombra el estado HTTP y un `code` estable de Problem Details con
  `detail` en español, y verifica que **no cambió ninguna fila**. Reparto propuesto, que confirma
  Functional Design: `401` sin autenticación; `403` rol o propiedad; `409` conflicto de estado; `413`
  tamaño; `415` formato; `422` validación.
- **Textos visibles.** Los textos entre «» son la redacción visible propuesta; viven en un catálogo de
  mensajes en español que las pruebas leen.
- **Vocabulario prohibido.** La lista de etiquetas de veracidad (con variantes de género, número y
  tiempo) es un archivo versionado en `contracts/` que leen las pruebas y el escaneo.
- **Control negativo.** Toda política estática o escáner tiene un *fixture* que la viola y una prueba que
  verifica que el chequeo falla sobre él.
- **Datos.** Toda prueba usa transcripciones sintéticas. Lo que corre sobre el corpus del piloto escribe
  fuera de Git y solo deja cifras (NFR12).

---

## Decisiones de esta etapa que precisan `requirements.md`

Estas respuestas precisan requisitos de la revisión 2 y las historias las aplican. Al revisar los
pendientes de la aprobación (2026-11-02), el humano decidió llevarlas a `requirements.md` en su propio
commit (`fix(requirements): …`, R-01): allí quedan FR3.6, FR4.2, FR4.9, FR6.1, FR6.4, FR7.1, FR7.2,
FR7.5, FR11.3, FR14.3, FR16.1, NFR12 y el nuevo FR16.3. El orden de entrega de `team.md` se corrigió en
otro commit (`fix(team): …`). La tabla se conserva como registro de dónde salió cada precisión.

| Decisión | Requisito que precisa | Origen |
|---|---|---|
| La CLI y la biblioteca validan el perfil igual que los servicios: un destino externo sin anonimizador termina con código ≠ 0 **antes** de cualquier llamada. El anonimizador entra en la **primera rebanada**, como módulo de la biblioteca. El orden de entrega de `team.md` (Walking Skeleton) se corrige en su propio commit. | FR14.3 (hoy solo servicios), FR11.3; `team.md` | Pregunta 10 (R-01) |
| En Git solo van los scripts `sbatch` y un **manifiesto** (nombres y SHA-256, sin contenido). El paquete con el corpus del piloto lo arma un script revisable en un directorio ignorado por Git; una comprobación de nivel 0 falla si Git rastrea algo de ese directorio. El corpus del piloto **también se procesa en ZINE**, empaquetado fuera de Git; del clúster solo salen cifras. | FR16.1, FR16.2, NFR12 («solo en la máquina local») | Pregunta 11 (R-02); revisión de calidad y desarrollo |
| **Una corrida incremental por envío**: un turno escrito o dictado da `desde_turno = hasta_turno = n`; un bloque pegado da una sola corrida desde su primer turno. Una transcripción **importada** nace cerrada a turnos nuevos y va directo al modo final. | FR4.9, FR3.6 | Pregunta 12 (R-03) |
| El modo final se puede **relanzar** mientras la sesión no esté consolidada. Un modo final en error **no bloquea** la consolidación: el diálogo lo avisa y el reporte lo rotula «Modo final no completado. Revisión manual requerida» con su código. Cuenta el **último** modo final lanzado; dos lanzamientos simultáneos dan un `202` y un `409`. | FR7.1 («exige el modo final terminado»), FR7.2 | Pregunta 13; revisión de diseño y calidad |
| Un hallazgo es el mismo cuando coincide el **par no ordenado** de (turno, cita normalizada en espacios). Si el modo final repite un hallazgo ya decidido, este conserva su estado y su historial. | FR4.9 | Revisión de desarrollo y calidad |
| **Código de error del anonimizador:** un fallo del anonimizador termina en `estado: error` con un código estable propio (propuesta: `anonimizador`), y la consola añade «No se envió ningún dato fuera del clúster». El nombre definitivo lo fija Contract Design. | FR4.2 (lista cerrada de códigos), FR11.3 | Revisión de calidad y diseño |
| El botón visible de FR7.1 se llama **«Consolidar reporte»**, para no confundirlo con «Finalizar sesión»; «Finalizar y Consolidar» queda como nombre de la acción en los requisitos. | FR7.1 | Revisión de diseño |
| Los tramos incrementales en `error` no bloquean la consolidación; el reporte los rotula «Tramo no evaluado» con su código. | FR7.1, FR7.2 | Seguimiento 1, extendido por la pregunta 13 |
| **FR16.3 (MUST, ya en `requirements.md`):** antes de Domain Design se validan los modelos locales en el clúster Ing. Sistemas con seis mediciones (velocidad, API del servidor local, *tokens* frente al contexto, repetibilidad en CPU, instalación sin internet, verificador de otra familia). Se hacen mientras la tarea 4L corre en segundo plano, y **Domain Design no empieza** hasta que el humano revise el reporte (US14.1). Si la medición `--array=8` de la 4L no termina en el plazo que fija el humano, el reporte se revisa con sus cifras parciales. Los `.sbatch` de validación y el reporte (solo cifras) viven en `docs/validacion-zine/` por commit directo; los `.sbatch` de producción (US14.2) entran por PR. | FR16 | Preguntas 14, 15 y 16 |
| «Editada» = el analista escribe **su propia reformulación**; hecho, tipo, citas y observaciones de la IA no cambian. | FR6.1, FR7.2 | Pregunta 6 |
| Antes de consolidar, una decisión se puede cambiar entre `aceptada`, `editada` y `descartada`, con las mismas exigencias; nunca vuelve a `pendiente`. | FR6.1 | Seguimiento 5 |
| Un reporte consolidado se corrige con «Corregir reporte»: copia de trabajo donde solo cambian estados y notas; consolidarla crea la versión nueva. | FR7.5 | Pregunta 7 |
| El escaneo de vocabulario prohibido **no** cubre el texto que escribe el analista (que el reporte muestra como suyo), además de las dos citas literales. | FR6.4 | Seguimiento 4 |
| Accesibilidad SHOULD: WCAG 2.1 AA con axe, flujo de texto solo con teclado, estados no solo por color. | `requirements.md` §7 (pregunta abierta) | Seguimiento 3 |

Respuestas de la primera pasada que **supera** el cambio 01 y ya no se aplican: pregunta 4 y
Seguimiento 2 (umbral y «no documentada»), pregunta 5 (umbral por PR, generalizada en FR9.2), pregunta 8
(la sustituye NFR8 de la revisión 2) y Seguimiento 6 (escenarios).

---

## Épica 1 — Escenario de control · **Retirada** (cambio 01)

No hay marco de verdad documental (FR2 retirado; DT24).

### US1.1 — Cargar e indexar un escenario de control · **Retirada**
### US1.2 — Corregir un escenario creando una versión nueva · **Retirada**
### US1.3 — Elegir escenario del catálogo · **Retirada**

---

## Épica 2 — Sesión y entrada de la transcripción

### US2.1 — Crear una sesión con su entrevista y su perfil · MUST · P1
Como Analista de Verdad, quiero crear una sesión eligiendo la entrevista y uno de los perfiles aprobados,
para que todo lo que se analice quede atado a esa configuración de modelos.
*Origen:* FR3.1, FR14.5, FR1.2.

- **AC2.1.1** Given los perfiles aprobados, When creo una sesión con una entrevista guiada o importada y un perfil, Then la sesión guarda el perfil, su configuración efectiva y su `config_sha256`, y su cabecera muestra el perfil, los primeros 12 caracteres de la huella y, por papel, si usa un proveedor comercial. `[N1]` + `[N0]` Vitest
- **AC2.1.2** Given una sesión S1 creada con el perfil X y un PR que después cambia X, When el servicio reinicia y se analiza un turno de S1, Then la corrida registra la misma `config_sha256` que S1; una sesión S2 creada después guarda la huella nueva. `[N1]`
- **AC2.1.3** Given un nombre de perfil que no está en el archivo aprobado, When envío `POST` para crear la sesión, Then `422` y 0 filas nuevas. `[N1]`
- **AC2.1.4** Given un usuario `admin` o `investigador`, When intenta crear una sesión, enviar un turno, pegar o importar una transcripción, finalizar una sesión o lanzar el modo final, Then `403` y 0 filas nuevas; y en la interfaz no ve «Nueva sesión». `[N1]` + `[N0]` Vitest
- **AC2.1.5** Given una sesión de otro analista, When intento enviar un turno, finalizarla o lanzar su modo final, Then `403`. `[N1]`

### US2.2 — Enviar el testimonio turno a turno · MUST · P1
Como Analista de Verdad, quiero enviar cada turno con su hablante y seguir trabajando mientras se analiza,
para no quedar bloqueado por la latencia de los modelos.
*Origen:* FR3.2, FR3.4, FR3.7, FR4.9 (pregunta 12).

- **AC2.2.1** Given una sesión guiada abierta, When envío un turno eligiendo el hablante (`ENT` o `TEST`), Then queda numerado en orden, sin página, y muestra su estado («En cola», «Procesando», «Analizado», «Error»); con 10 envíos concurrentes los turnos quedan numerados 1..10 sin huecos ni duplicados. `[N1]`
- **AC2.2.2** Given un `ModelGateway` *fake* que bloquea hasta que la prueba lo libera, When envío un segundo turno y consulto un hallazgo existente, Then el `POST` responde `202` y el `GET` `200` antes de liberarlo. `[N1]` (las latencias son NFR3, diferidas)
- **AC2.2.3** Given el turno *n* enviado, When se encola, Then se encola **una** corrida incremental con `desde_turno = hasta_turno = n` cuyo mensaje cumple el contrato de la cola; un mensaje mal formado se rechaza sin crear filas. `[N0]` + `[N1]`
- **AC2.2.4** Given un trabajador que muere mientras procesa una corrida, When otro toma el mensaje pendiente, Then la corrida produce exactamente un resultado (entrega al menos una vez, idempotente por ID de corrida). `[N1]`
- **AC2.2.5** Given una sesión guiada recién creada, When la abro, Then veo «Aún no hay turnos. Escribe el primer turno o pega un bloque de turnos» y «Enviar turno» está deshabilitado mientras el texto esté vacío. `[N0]` Vitest
- **AC2.2.6** Given un turno que supera los caracteres por turno del catálogo de límites, When lo escribo, Then veo el contador «X / M caracteres» y «Enviar turno» queda deshabilitado con ese motivo; la API responde `413` sin crear filas; en el límite exacto se acepta. `[N0]` Vitest + `[N1]`
- **AC2.2.7** Given la misma transcripción y el mismo *fake*, When la analizan la CLI y el trabajador `semantic-agent`, Then las dos salidas son iguales salvo `fecha` y las fechas del registro de modelos. `[N1]`

### US2.3 — Pegar un bloque de turnos · MUST · P1
Como Analista de Verdad, quiero pegar varios turnos de una vez, para no enviar uno a uno un testimonio ya
transcrito.
*Origen:* FR3.3, FR3.7, FR4.9 (pregunta 12).

- **AC2.3.1** Given texto con turnos separados por línea vacía o por marca de hablante, When lo pego, Then veo cuántos turnos detectó y una vista previa de cada uno con su hablante, y puedo cancelar sin que se cree ningún turno. `[N0]` Vitest
- **AC2.3.2** Given los ejemplos versionados de división, When corren contra la vista previa de la consola y contra el servidor, Then ambas implementaciones producen los mismos turnos. `[N0]` Vitest + `[N0]` pytest
- **AC2.3.3** Given un bloque confirmado de *k* turnos que empieza en el turno *n*, When se procesa, Then se crean los turnos *n*..*n+k−1* y se encola **una sola** corrida incremental con `desde_turno = n` y `hasta_turno = n+k−1`. `[N1]`
- **AC2.3.4** Given un bloque que supera un límite del catálogo (turnos, caracteres o caracteres por turno), When veo la vista previa, Then leo «El bloque tiene N turnos; el máximo es M» (o su equivalente en caracteres), «Confirmar» queda deshabilitado con ese motivo y la API responde `413` sin crear filas; en el límite exacto se acepta y en el límite + 1 no. `[N0]` Vitest + `[N1]`

### US2.4 — Finalizar la sesión · MUST · P1
Como Analista de Verdad, quiero cerrar el ingreso de turnos, para lanzar el modo final y empezar la
revisión con el testimonio completo.
*Origen:* FR3.5, NFR7.

- **AC2.4.1** Given una sesión guiada abierta, When pulso «Finalizar sesión», Then un diálogo dice «Después de finalizar no podrás agregar turnos», indica cuántas corridas siguen en proceso y ofrece «Finalizar» y «Cancelar». `[N0]` Vitest
- **AC2.4.2** Given que confirmo, When la sesión se finaliza, Then guarda en UTC la hora de inicio de MTTV y un nuevo turno responde `409` sin crear filas. `[N1]`
- **AC2.4.3** Given una sesión finalizada con corridas incrementales en proceso, When terminan, Then sus hallazgos se guardan en la sesión. `[N1]`
- **AC2.4.4** Given una sesión finalizada, When la miro, Then veo «Lanzar modo final», cuántas sugerencias quedan pendientes y un acceso a la primera. `[N0]` Vitest

### US2.5 — Ver la lista de sesiones · MUST · P1
Como Analista de Verdad, quiero ver las sesiones con su estado, para retomar las mías y consultar las de
otros.
*Origen:* FR1.2 (leer todas), FR7.4, FR8.3. No sustituye al historial lateral (US11.2).

- **AC2.5.1** Given sesiones de dos analistas, When entro como `analista`, Then veo la entrevista, el origen («Importada» o «Guiada»), el perfil, el dueño, la fecha y el estado («Abierta», «Suspendida», «Finalizada», «Consolidada») de cada una, y puedo filtrar las mías. `[N1]` + `[N0]` Vitest
- **AC2.5.2** Given que no hay sesiones, When abro la lista, Then veo «Aún no hay sesiones» y la acción «Nueva sesión». `[N0]` Vitest
- **AC2.5.3** Given una sesión «Suspendida» mía, When abro la lista, Then lo muestra con texto e icono, no solo con color. `[N0]` Vitest

### US2.6 — Importar una transcripción con turnos y páginas · MUST · P1
Como Analista de Verdad, quiero importar una transcripción en el formato del contrato común, para
analizar una entrevista ya transcrita conservando sus turnos y páginas.
*Origen:* FR3.6, FR3.7, FR4.9 (pregunta 12).

- **AC2.6.1** Given un archivo válido del contrato (`entrevista`, `origen: corpus`, turnos con `n`, `hablante`, `pagina`, `pagina_fin`, `texto`, `estado`), When lo importo y confirmo, Then se crea la sesión **cerrada a turnos nuevos**, sin ninguna corrida incremental, con «Lanzar modo final» disponible, y los turnos leídos por la API son iguales campo a campo a los del archivo. `[N1]`
- **AC2.6.2** Given un archivo cuyo tipo de contenido no es JSON, When lo importo, Then `415`. Given un JSON mal formado o fuera del esquema (un caso por campo obligatorio ausente, `origen` distinto de `corpus`, `turnos` vacío, números de turno repetidos, `pagina_fin < pagina`, `estado` fuera del enum), When lo importo, Then `422` con un mensaje en español que nombra el **primer** problema y cuántos hay en total («Turno 37: falta el hablante. Hay 3 problemas más»), y no se crea ninguna sesión ni turno. `[N0]` esquema + `[N1]` conteo con un caso
- **AC2.6.3** Given cada límite del catálogo único de límites (caracteres, turnos y caracteres por turno), When importo un archivo en el límite exacto y otro en el límite + 1, Then el primero se acepta y el segundo responde `413` antes de encolar nada. `[N1]` (las cifras las fija NFR Requirements)
- **AC2.6.4** Given una sesión importada, When envío un turno o pego un bloque, Then `409` sin crear filas, y la interfaz no ofrece esas acciones. `[N1]` + `[N0]` Vitest
- **AC2.6.5** Given un archivo válido, When lo selecciono, Then antes de crear nada veo «Se importarán N turnos (páginas X–Y), de ellos K del entrevistador y P plegados. La sesión no admitirá turnos nuevos», con «Importar» y «Cancelar»; con «Cancelar» hay 0 filas. `[N0]` Vitest + `[N1]`

### US2.7 — Lanzar el modo final · MUST · P1
Como Analista de Verdad, quiero analizar la transcripción completa cuando termino de ingresarla, para
encontrar contradicciones entre pasajes distantes que el modo incremental no ve.
*Origen:* FR4.9, FR7.1, FR1.2, FR1.3 (pregunta 13).

- **AC2.7.1** Given una sesión guiada sin finalizar, When pido el modo final, Then `409`; en una sesión guiada finalizada o una importada, «Lanzar modo final» encola una corrida con `modo: final` y registra quién y cuándo. `[N1]`
- **AC2.7.2** Given un hallazgo del modo incremental y otro del modo final con el mismo **par no ordenado** de (turno, cita normalizada en espacios), When termina el modo final, Then aparece una sola vez en la sesión; si el del incremental ya estaba `aceptada`, `editada` o `descartada`, **conserva su estado y su historial** y no vuelve a `pendiente`. Dos citas casi iguales del mismo par de turnos cuentan como hallazgos distintos (límite declarado). `[N1]`
- **AC2.7.3** Given un `ModelGateway` *fake* que bloquea el modo final, When está en proceso, Then un `GET` de la sesión y la decisión sobre un hallazgo existente responden `200` antes de liberarlo, y la sesión muestra «Modo final en proceso», distinto de «Modo final terminado» y de «Modo final con error». `[N1]` + `[N0]` Vitest
- **AC2.7.4** Given un modo final que termina en `estado: error`, When lo veo, Then leo la causa del código (AC3.2.5) y «El analizador no pudo procesar la transcripción completa. Revisión manual requerida», con la acción «Relanzar modo final»; relanzar crea una corrida nueva y la anterior queda en el registro de corridas. `[N1]` + `[N0]` Vitest
- **AC2.7.5** Given una sesión consolidada, When pido el modo final, Then `409`. `[N1]`
- **AC2.7.6** Given un modo final «En cola» o «Procesando», When lo pido otra vez (doble clic o dos `POST` simultáneos), Then exactamente una petición responde `202` y la otra `409`, con una sola corrida nueva; el botón queda deshabilitado con «El modo final ya está en proceso». `[N1]` + `[N0]` Vitest

---

## Épica 3 — Contradicciones y hallazgos

### US3.1 — Revisar una contradicción con sus dos citas · MUST · P1
Como Analista de Verdad, quiero ver cada contradicción con sus dos citas en su contexto, para juzgarla con
la evidencia delante.
*Origen:* FR4.3, FR4.4, FR6.2.

- **AC3.1.1** Given un hallazgo emitido, When llega a la consola, Then aparece `pendiente` con el hecho, el tipo (uno de los 7 rótulos), y `cita_a` y `cita_b`, cada una con su turno, su hablante y su página si la tiene; las observaciones aparecen plegadas. `[N1]` + `[N0]` Vitest
- **AC3.1.2** Given un hallazgo, When lo selecciono, Then las dos citas quedan resaltadas en sus turnos con una marca «A» o «B» además del color, el turno resaltado se anuncia como «Cita A, turno N», y puedo saltar de una a otra. `[N0]` Vitest
- **AC3.1.3** Given un hallazgo nuevo, When aparece, Then se agrega al panel sin ventana modal, sin sonido y sin mover el foco; el contador de pendientes se actualiza, una región `aria-live="polite"` lo anuncia, y su rótulo es «Sugerencia de revisión · Contradicción en el relato», sin grados de severidad. `[N0]` Vitest
- **AC3.1.4** Given una cita en un turno `ENT` o `plegado`, When se muestra, Then lleva el aviso «Cita en un turno del entrevistador» o un aviso de turno plegado que explica en lenguaje llano qué significa «plegado» según el contrato común (la redacción la fija Functional Design), con texto e icono, en la consola y en el reporte. `[N1]` + `[N0]` Vitest
- **AC3.1.5** Given una corrida terminada sin hallazgos, When miro sus turnos, Then muestran «Analizado · sin sugerencias de revisión», distinto de «Procesando» y de «Error». `[N0]` Vitest

### US3.2 — Nunca recibir un resultado parcial · MUST · P1
Como Analista de Verdad, quiero que un fallo del analizador no produzca hallazgos sueltos, para no revisar
resultados incompletos.
*Origen:* FR4.2, FR15.2.

- **AC3.2.1** Given un `ModelGateway` *fake* que devuelve (a) texto no JSON, (b) JSON sin un campo obligatorio, (c) un `tipo` fuera del enum, (d) tres hallazgos con uno mal formado, (e) *timeout*, (f) bloqueo de contenido sin proveedor alterno, (g) error del proveedor, o (h) un anonimizador caído, When corre el analizador, Then `estado: error`, `hallazgos` vacío y `codigo` `salida_invalida` en (a)–(d), `tiempo_agotado`, `bloqueo_contenido`, `proveedor` y el código del anonimizador (tabla de decisiones), respectivamente. `[N0]` una prueba por código
- **AC3.2.2** Given un tramo en error, When lo veo, Then leo «El analizador no pudo procesar este tramo. Revisión manual requerida» y el `codigo` como referencia secundaria. `[N0]` Vitest
- **AC3.2.3** Given un tramo incremental en error, también en una sesión finalizada, When pulso «Reintentar», Then se repite la corrida con el mismo `desde_turno` y `hasta_turno`; reintentado dos veces, no hay hallazgos duplicados. `[N1]`
- **AC3.2.4** Given observaciones que contienen vocabulario prohibido fuera de las dos citas, When se valida la salida, Then se trata como `salida_invalida`. `[N0]`
- **AC3.2.5** Given cada código de error, When se muestra, Then lleva una causa en español que no culpa al testimonio, encima del mensaje de FR4.2: `proveedor` «El servicio de modelos no respondió»; `tiempo_agotado` «El análisis superó el tiempo máximo»; `salida_invalida` «La respuesta del modelo no tuvo el formato esperado»; `bloqueo_contenido` «El filtro de contenido del proveedor rechazó la petición»; caída del anonimizador «El anonimizador no respondió. No se envió ningún dato fuera del clúster». `[N0]` Vitest

### US3.3 — Que el testimonio no cambie las reglas del analizador · MUST · P3
Como Oficial de Cumplimiento Ético, quiero que las instrucciones escritas dentro de un testimonio se traten
como datos, para que nadie pueda torcer el análisis desde la entrada.
*Origen:* FR4.6, NFR5 (Escenario A), NFR10.

- **AC3.3.1** Given una corrida, When se construyen los mensajes, Then el testimonio viaja solo como JSON dentro del mensaje `user`, nunca en las instrucciones del sistema, y estas se leen de un archivo cuyo SHA-256 coincide con el `prompt_sha256` registrado en la corrida. `[N0]`
- **AC3.3.2** Given el texto de inyección del Escenario A, que pide una salida reconocible (un hallazgo con un `hecho` marcador o una etiqueta prohibida), añadido a cada transcripción del conjunto sintético, When corre la evaluación, Then hay 0 apariciones de esa salida, y la diferencia de hallazgos con y sin inyección no supera el desacuerdo entre 3 corridas sin inyección. `[N2]`
- **AC3.3.3** Given los manifiestos, When corre la política, Then falla si el *prompt* del sistema no está montado `readOnly: true` desde un `ConfigMap`; con control negativo. `[N0]`

### US3.4 — Ningún hallazgo sin dos citas verificadas · MUST · P3
Como Oficial de Cumplimiento Ético, quiero que ningún hallazgo salga del analizador si sus dos citas no
están literalmente en sus turnos, para que ninguna alucinación llegue al analista.
*Origen:* FR4.3, FR4.4, AUTONOMIA-05.

- **AC3.4.1** Given un hallazgo sin `hecho`, `tipo`, `cita_a`, `cita_b` u `observaciones` (ausente, `null`, vacío o solo espacios), o con un `tipo` fuera de los 7 valores, When se valida, Then se rechaza; una prueba por campo y caso. `[N0]`
- **AC3.4.2** Given (a) una cita con un carácter alterado, (b) una cita que está en otro turno, (c) una cita con « […] » cuyos fragmentos aparecen fuera de orden, (d) mayúsculas o minúsculas distintas, (e) una tilde quitada, (f) comillas o puntuación cambiadas, (g) fragmentos unidos con « […] » que vienen de turnos distintos, (h) un turno inexistente, When se verifica, Then el hallazgo no sale del analizador y queda en el registro de la corrida con el motivo. `[N0]`
- **AC3.4.3** Given cualquier subcadena de un turno con sus espacios en blanco alterados, o fragmentos del mismo turno unidos con « […] » en orden, When se verifica, Then se acepta; en un turno sin página solo se verifica el turno. Propiedad inversa: insertar o cambiar un carácter que no sea espacio en una subcadena válida hace que se rechace. `[N0]` pruebas de propiedad con Hypothesis
- **AC3.4.4** Given el módulo de verificación de citas, When corre la cobertura en CI, Then tiene 100 % de ramas. `[N0]`
- **AC3.4.5** Given el conjunto sintético, When corre la evaluación con un perfil comercial (con anonimizador y restauración) y con `todo-local`, Then el 100 % de las citas de los hallazgos emitidos está verificado en ambos. `[N2]`

### US3.5 — Que el verificador confirme cada hallazgo · MUST · P1
Como Analista de Verdad, quiero que otro modelo confirme cada contradicción antes de mostrármela, para
recibir menos falsas alarmas.
*Origen:* FR4.5.

- **AC3.5.1** Given un verificador *fake* que rechaza un candidato del juez, When termina la corrida, Then el candidato no llega a la consola y queda en el registro de la corrida con el motivo «rechazado por el verificador». `[N0]`
- **AC3.5.2** Given *k* candidatos del juez, When termina la corrida sin permutación, Then el registro de llamadas tiene exactamente *k* llamadas con papel `verificador`. `[N0]`

### US3.6 — Recibir en el modo incremental solo las contradicciones con turnos nuevos · MUST · P1
Como Analista de Verdad, quiero que cada análisis incremental me traiga solo lo que involucra a los turnos
recién ingresados, para no revisar dos veces lo mismo.
*Origen:* FR4.1, FR4.9.

- **AC3.6.1** Given una corrida incremental con `desde_turno = d` y un *fake* que propone un hallazgo con ambas citas antes de *d* y otro con una cita en *d*, When termina, Then solo sale el segundo. `[N0]`
- **AC3.6.2** Given cualquier salida del analizador, When se valida, Then cumple el esquema versionado del contrato común. `[N0]` prueba de contrato
- **AC3.6.3** Given dos corridas incrementales que proponen el mismo par no ordenado de (turno, cita normalizada en espacios), When terminan, Then la sesión muestra un solo hallazgo y conserva el estado que ya tuviera. `[N1]`

### US3.7 — Ver la limitación del modo fragmentado · MUST · P1
Como Analista de Verdad, quiero saber cuándo el análisis se hizo por ventanas, para no suponer que se
buscaron contradicciones entre pasajes muy distantes.
*Origen:* FR4.8.

- **AC3.7.1** Given un perfil con modelos locales, When termina una corrida, Then registra el modo fragmentado, la ventana y el solapamiento, y la consola y el reporte muestran «Análisis por ventanas de N turnos (solapamiento de M). No se buscaron contradicciones entre turnos separados por más de N turnos». `[N0]` + `[N1]` + `[N0]` Vitest
- **AC3.7.2** Given una ventana de *w* turnos y un *fake* que registra cada llamada, When corre el modo final, Then ninguna llamada al juez contiene dos turnos separados por más de *w* turnos. `[N0]`

---

## Épica 4 — Silencio Fáctico · **Retirada** (cambio 01)

Su lugar lo toma la verificación determinista de las dos citas (US3.4; FR5 retirado).

### US4.1 — Calificar como «no documentada» por umbral · **Retirada**
### US4.2 — Recibir el Paquete de Contexto de Traspaso · **Retirada**
### US4.3 — Impedir que el agente arranque sin umbral · **Retirada** (pasa a «no arrancar sin un perfil válido», US13.3)

---

## Épica 5 — Revisión humana de hallazgos

### US5.1 — Aceptar un hallazgo después de leer sus observaciones · MUST · P1
Como Analista de Verdad, quiero aceptar un hallazgo solo después de desplegar sus observaciones, para no
validar nada a ciegas.
*Origen:* FR6.1, FR6.2, FR6.5, NFR11.

- **AC5.1.1** Given un hallazgo con las observaciones plegadas, When lo miro, Then «Aceptar» y «Editar» aparecen deshabilitados con el texto visible «Despliega y lee las observaciones para habilitar esta acción». `[N0]` Vitest
- **AC5.1.2** Given que despliego las observaciones, When ocurre, Then se registra un evento «Observaciones consultadas» con mi usuario y la hora; la API responde `409` (`code` p. ej. `observations_not_viewed`) a `aceptada` o `editada` si no existe ese evento del mismo usuario para ese hallazgo, y `200` después. «Descartada» no lo exige. `[N1]` (el evento prueba que se desplegaron, no que se leyeron)
- **AC5.1.3** Given las observaciones desplegadas, When acepto con o sin nota, Then pasa a `aceptada` (en la lista: «Aceptada · con nota» y la nota visible, si la hay) y el historial guarda usuario, hora, estado anterior y nuevo. `[N1]` + `[N0]` Vitest
- **AC5.1.4** Given la tabla de transiciones que fije Functional Design, When pido una transición fuera de ella (p. ej. volver a `pendiente`), Then `409`. Antes de consolidar, se permite cambiar entre `aceptada`, `editada` y `descartada` con las mismas exigencias, y cada cambio queda en el historial. `[N0]` + `[N1]`
- **AC5.1.5** Given cualquier hallazgo, When lo veo, Then junto a los botones de decisión, sin *hover*, está «La IA es un asistente de soporte. Su criterio como analista prevalece». `[N0]` Vitest

### US5.2 — Editar un hallazgo con mi propia reformulación · MUST · P1
Como Analista de Verdad, quiero reformular un hallazgo con mis palabras sin tocar lo que dijo la IA, para
que el reporte muestre ambas cosas.
*Origen:* FR6.1, FR6.2, FR7.2 (pregunta 6).

- **AC5.2.1** Given un hallazgo con las observaciones desplegadas, When guardo mi reformulación, Then pasa a `editada` con mi texto, mi usuario y la hora; una reformulación vacía o solo de espacios responde `422` y «Guardar» está deshabilitado con su motivo visible. `[N1]` + `[N0]` Vitest
- **AC5.2.2** Given un hallazgo `editada`, When comparo, Then el SHA-256 de (hecho, tipo, cita_a, cita_b, observaciones) es idéntico antes y después; una petición que intenta cambiar alguno responde `422` sin cambiar nada. `[N1]`
- **AC5.2.3** Given el editor, When escribo, Then el hallazgo original de la IA se ve a un lado en solo lectura. `[N0]` Vitest
- **AC5.2.4** Given un hallazgo `editada`, When se consolida, Then el reporte muestra el hallazgo original y mi reformulación con quién y cuándo. `[N1]`

### US5.3 — Descartar un hallazgo con una nota · MUST · P1
Como Analista de Verdad, quiero descartar un hallazgo explicando por qué, para que quede constancia de mi
criterio.
*Origen:* FR6.3.

- **AC5.3.1** Given un hallazgo, When intento descartarlo con la nota ausente, vacía o solo de espacios, Then `422`, el hallazgo no cambia, y junto al campo aparece «Escribe por qué descartas esta sugerencia». `[N0]` + `[N1]`
- **AC5.3.2** Given una nota no vacía, When lo descarto, Then pasa a `descartada` con la nota, mi usuario y la hora. `[N1]`

### US5.4 — Solo el dueño de la sesión cambia sus hallazgos · MUST · P1
Como Analista de Verdad, quiero que solo yo pueda cambiar los hallazgos de mis sesiones, para que nadie
valide hallazgos en mi nombre.
*Origen:* FR1.2, FR6.1.

- **AC5.4.1** Given una sesión de otro analista, When intento cambiar el estado de un hallazgo, Then `403` y 0 filas nuevas. `[N1]`
- **AC5.4.2** Given una sesión de otro analista, When la abro, Then veo «Sesión de <usuario>. Solo lectura», puedo leer hallazgos y reporte, y no hay botones de decisión, de modo final ni de consolidación. `[N1]` + `[N0]` Vitest
- **AC5.4.3** Given un usuario `admin` o una identidad de servicio, When intenta cambiar el estado de cualquier hallazgo, Then `403`. `[N1]`

### US5.5 — Ningún juicio de veracidad sobre el compareciente · MUST · P3
Como Oficial de Cumplimiento Ético, quiero que ni la IA ni la interfaz califiquen al compareciente como
mentiroso o veraz, para evitar la revictimización.
*Origen:* FR6.4, AUTONOMIA-03 (Seguimiento 4).

- **AC5.5.1** Given la lista versionada de vocabulario prohibido, When corre el escaneo (por palabra completa, sin distinguir mayúsculas ni tildes), Then hay 0 coincidencias en las observaciones de los hallazgos y en las observaciones al conductor sobre *fixtures* `[N0]` y sobre el conjunto sintético `[N2]`, en las cadenas de la interfaz `[N0]`, en el reporte generado `[N1]` y en la interfaz renderizada `[N3]`. Se excluyen las dos citas literales y el texto escrito por el analista.
- **AC5.5.2** Given el escaneo, When corre sobre sus controles, Then (a) unas observaciones *fixture* que dicen «el compareciente miente» lo hacen fallar; (b) «falso» dentro de una de las dos citas literales no; (c) «miente» entre «» en las observaciones, que **no** es ninguna de las dos citas, lo hace fallar; (d) una reformulación del analista con «miente» no lo hace fallar y el reporte la muestra en el bloque del analista. `[N0]`
- **AC5.5.3** Given el esquema del hallazgo, When lo valido, Then tiene `additionalProperties: false`, ningún campo de veracidad ni puntaje, y un JSON con un campo extra (p. ej. `is_truthful`) se rechaza. `[N0]`
- **AC5.5.4** Given la interfaz, When la recorro, Then los únicos rótulos de resultado son «Sugerencia de revisión», «Contradicción en el relato» y los rótulos de los 7 tipos. `[N0]` Vitest

### US5.6 — Revisar hallazgos con teclado y lector de pantalla · SHOULD · P1
Como Analista de Verdad, quiero recorrer el flujo sin ratón y con lector de pantalla, para trabajar con
la atención repartida o con una discapacidad.
*Origen:* `requirements.md` §7 (pregunta abierta asignada a esta etapa), S12-R2 (Seguimiento 3).

- **AC5.6.1** Given inicio de sesión, lista de sesiones, creación de sesión con perfil, importación, sesión, panel de hallazgos y consolidación, When corre `@axe-core/playwright` con WCAG 2.1 AA, Then hay 0 violaciones de impacto `serious` o `critical`. `[N3]`
- **AC5.6.2** Given el flujo de punta a punta, When lo recorro solo con teclado (Tab, Enter, Espacio, Escape), Then puedo crear la sesión eligiendo el perfil, importar un archivo y confirmar su vista previa, enviar un turno, lanzar y relanzar el modo final, desplegar las observaciones, aceptar, editar, descartar, consolidar y responder al aviso de reanudación, con el foco siempre visible. `[N3]`
- **AC5.6.3** Given cualquier estado de turno, corrida, hallazgo o sesión, When lo veo, Then se identifica por texto o icono además del color. `[N0]` Vitest
- **AC5.6.4** Given un botón deshabilitado con motivo (AC2.2.5, AC5.1.1, AC5.2.1, AC6.1.1, AC13.1.4), When llego a él con Tab, Then recibe el foco (`aria-disabled="true"`, no `disabled` nativo) y el lector anuncia el motivo por `aria-describedby`. `[N0]` Vitest
- **AC5.6.5** Given un bloque pegado o una importación de cientos de turnos, When cambian sus estados, Then `aria-live` solo anuncia cambios agregados (contador de pendientes, inicio, fin o error del modo final, sesión suspendida); el estado de cada turno se lee al enfocarlo. `[N0]` Vitest

---

## Épica 6 — Consolidación y reporte

### US6.1 — Consolidar la sesión cuando todo está revisado · MUST · P1
Como Analista de Verdad, quiero consolidar el reporte solo cuando revisé cada hallazgo, para que ningún
hallazgo de la IA llegue al reporte sin validación humana.
*Origen:* FR7.1, FR7.2, FR7.3, FR1.3 (Seguimiento 1, pregunta 13).

- **AC6.1.1** Given cada motivo de bloqueo por separado —sesión sin finalizar, modo final sin lanzar, un modo final o una corrida incremental «En cola» o «Procesando», algún hallazgo `pendiente`—, When intento consolidar, Then el botón «Consolidar reporte» está deshabilitado con su motivo visible («Finaliza la sesión para consolidar», «Lanza el modo final para consolidar», «Hay análisis en proceso», «Quedan N sugerencias pendientes» con enlace a la primera) y la API responde `409` sin crear reporte; con varios motivos a la vez se listan todos en ese orden. Una prueba por motivo. `[N1]` + `[N0]` Vitest
- **AC6.1.2** Given un modo final o tramos incrementales terminados en `error` y ningún hallazgo pendiente, When pulso «Consolidar reporte», Then **no** se bloquea: un diálogo, con el foco inicial en «Cancelar», resume cuántas sugerencias quedaron aceptadas, editadas y descartadas, lista los tramos en error y, si el **último** modo final lanzado terminó en error, lo dice, ofrece «Volver y relanzar el modo final» y explica «El reporte no incluirá contradicciones entre pasajes distantes»; si la sesión usó el modo fragmentado, repite la limitación; y avisa «Después de consolidar, la sesión queda bloqueada; una corrección creará una versión nueva», con «Consolidar» y «Cancelar». Los intentos anteriores del modo final en error quedan en el registro de corridas, no como «Modo final no completado». `[N1]` + `[N0]` Vitest
- **AC6.1.3** Given que confirmo, When se consolida, Then el reporte Markdown contiene la transcripción por turnos con hablante y página; todas las sugerencias con su estado final y nota, y por cada una el hecho, el tipo, las dos citas con turno y página, sus avisos y las observaciones; el perfil, `config_sha256`, `prompt_sha256`, la versión del analizador y el registro de modelos de cada corrida; el modo fragmentado y su ventana, si se usó; «Tramo no evaluado» y «Modo final no completado. Revisión manual requerida» con su código, si aplica; y quién consolidó y cuándo. Se compara con un archivo dorado de una sesión *fixture* con reloj fijo, y se guarda en el volumen persistente con su SHA-256 registrado y recalculable. `[N1]`
- **AC6.1.4** Given un reporte recién consolidado, When termina, Then veo quién y cuándo, el SHA-256 completo con acción para copiarlo y «Descargar reporte». `[N0]` Vitest
- **AC6.1.5** Given una sesión consolidada, When intento cambiar un hallazgo directamente, Then `409` sin cambios. `[N1]`
- **AC6.1.6** Given dos peticiones de consolidación simultáneas, When terminan, Then exactamente una responde `200` y la otra `409`, con un solo reporte y un solo SHA-256. `[N1]`
- **AC6.1.7** Given una sesión de otro analista, un usuario `admin` o una identidad de servicio, When intenta consolidar, Then `403`. `[N1]`
- **AC6.1.8** Given una sesión con 0 hallazgos y el modo final terminado, When consolido, Then se consolida y el reporte dice «Sin sugerencias de revisión». `[N1]`
- **AC6.1.9** Given el diálogo de consolidación abierto, When llega un hallazgo incremental nuevo antes de confirmar, Then la API responde `409` al confirmar y el motivo «Quedan N sugerencias pendientes» aparece. `[N1]`

### US6.2 — Descargar el reporte y comprobar su integridad · MUST · P1
Como Analista de Verdad, quiero descargar el reporte consolidado, para entregarlo y que cualquiera pueda
comprobar que no cambió.
*Origen:* FR7.3, FR7.4.

- **AC6.2.1** Given un reporte consolidado, When lo descargo, Then el SHA-256 del archivo coincide con el registrado y visible junto a la descarga. `[N1]` + `[N3]`
- **AC6.2.2** Given una sesión sin consolidar, When pido la descarga, Then `409` con `code` estable y la interfaz no ofrece la acción. `[N1]`

### US6.3 — Corregir un reporte consolidado con una versión nueva · MUST · P1
Como Analista de Verdad, quiero corregir un reporte ya consolidado sin borrar el anterior, para enmendar
un error dejando el rastro completo.
*Origen:* FR7.5 (pregunta 7).

- **AC6.3.1** Given mi sesión consolidada, When pulso «Corregir reporte», Then se abre una copia de trabajo rotulada «Copia de trabajo de la versión N. Solo puedes cambiar estados y notas»; cambiar la transcripción o la salida de la IA responde `422`. `[N1]` + `[N0]` Vitest
- **AC6.3.2** Given una copia de trabajo abierta, When pulso otra vez «Corregir reporte», Then vuelvo a la misma copia: nunca hay dos abiertas por sesión; y «Descartar copia» la elimina sin crear versión. `[N1]`
- **AC6.3.3** Given la copia sin hallazgos `pendiente`, When consolido, Then se crea una versión nueva con su SHA-256, quién y cuándo, que referencia a la anterior; los bytes de la anterior recalculan el mismo SHA-256. `[N1]`
- **AC6.3.4** Given dos versiones de reporte, When consulto los estados de los hallazgos de cada una, Then cada versión conserva los suyos, y la lista de versiones muestra SHA-256, quién y cuándo, con la vigente marcada. `[N1]` + `[N0]` Vitest
- **AC6.3.5** Given una sesión de otro analista o un usuario `admin`, When intenta «Corregir reporte», Then `403`. `[N1]`

---

## Épica 7 — Reanudación

### US7.1 — Reanudar una sesión interrumpida · MUST · P1
Como Analista de Verdad, quiero retomar una sesión tras perder la conexión, para no repetir la entrevista
ni perder lo ya analizado.
*Origen:* FR8.1, FR8.2, FR8.3.

- **AC7.1.1** Given una sesión abierta, When el servidor no recibe el latido de la consola durante *T* segundos (configurable; *T* lo fija NFR Requirements), Then la sesión pasa a «Suspendida» en ≤ *T* + el intervalo de revisión y el cambio guarda la hora. `[N1]`
- **AC7.1.2** Given una sesión «Suspendida» mía, When vuelvo a entrar, Then veo «Se detectó una interrupción inesperada en la sesión. ¿Desea reanudar desde el último turno registrado?» con «Reanudar» y «Más tarde»; con «Más tarde» sigue suspendida y se reanuda desde la lista. `[N0]` Vitest
- **AC7.1.3** Given una transcripción cortada a mitad de su análisis, When reanudo, Then los conteos de turnos, corridas, hallazgos y filas de historial son iguales antes del corte y después de reanudar, sin duplicados. `[N1]`
- **AC7.1.4** Given una sesión «Suspendida» con corridas en cola, When pasa el tiempo, Then el trabajador las termina y al reanudar se ven «Analizado» o «Error» con sus hallazgos. `[N1]`
- **AC7.1.5** Given una sesión de otro analista, When intento reanudarla, Then `403`. `[N1]`

---

## Épica 8 — Acceso, administración y auditoría

### US8.1 — Iniciar sesión en la consola · MUST · P1, P2
Como usuario de Veridicus, quiero entrar con usuario y contraseña, para que cada acción quede a mi nombre.
*Origen:* FR1.1, FR1.3.

- **AC8.1.1** Given credenciales válidas, When inicio sesión, Then el `analista` llega a la lista de sesiones, el `admin` a la gestión de usuarios y el `investigador` a los reportes de corridas y evaluaciones. `[N1]` + `[N0]` Vitest
- **AC8.1.2** Given un usuario inexistente o una contraseña errónea, When intento entrar, Then ambos casos producen el mismo estado y el mismo cuerpo byte a byte, con un mensaje en español. `[N1]`
- **AC8.1.3** Given una contraseña única sembrada, When busco en todas las columnas de texto y en los logs capturados, Then hay 0 coincidencias y el hash tiene el prefijo de un algoritmo adaptativo con sal. `[N1]`
- **AC8.1.4** Given cada ruta del OpenAPI salvo inicio de sesión y salud, When la llamo sin token, Then `401`. `[N1]`
- **AC8.1.5** Given que mi sesión web expira con una sesión de entrevista abierta, When vuelvo a entrar, Then regreso a esa sesión sin pérdida. `[N1]` (la duración la fija NFR Requirements)

### US8.2 — Gestionar usuarios · MUST · P2
Como Administrador de plataforma, quiero crear y desactivar usuarios con su rol, para controlar quién
usa la consola.
*Origen:* FR1.2.

- **AC8.2.1** Given que soy `admin`, When creo un usuario `analista`, Then puede iniciar sesión con ese rol. `[N1]`
- **AC8.2.2** Given un usuario `analista`, When intenta gestionar usuarios, Then `403`. `[N1]`
- **AC8.2.3** Given un usuario desactivado, When usa su token vigente o intenta entrar, Then `401`, y sus acciones pasadas conservan su autoría. `[N1]`
- **AC8.2.4** Given que soy `admin`, When creo un usuario `investigador`, Then puede iniciar sesión con ese rol, llega a los reportes de corridas y evaluaciones, y recibe `403` al leer sesiones o reportes de sesiones (FR1.2). `[N1]`

### US8.3 — Cambiar perfiles, proveedores, *prompts* y límites solo por PR · MUST · P2
Como Administrador de plataforma, quiero que la configuración de modelos solo cambie mediante un PR, para
que cada cambio quede aprobado y registrado y el sistema nunca se reconfigure solo.
*Origen:* FR9.1, FR9.2 (pregunta 5, generalizada), AUTONOMIA-01.

- **AC8.3.1** Given el OpenAPI, When lo enumero, Then no hay ninguna ruta que escriba perfiles, proveedores, *prompts*, la tabla de precios o los límites `[N0]`; y Playwright recorre la consola con ambos roles sin encontrar ese control `[N3]`.
- **AC8.3.2** Given el código de los servicios y de la biblioteca, When corre la regla estática, Then falla si un módulo fuera del cargador de configuración abre esos archivos para escritura; con control negativo. `[N0]`
- **AC8.3.3** Given un PR que cambia un perfil, When se fusiona en `main`, Then el historial de Git muestra quién, cuándo y el cambio, y la `config_sha256` de las corridas posteriores cambia. `[Manual]` con el `git log` adjunto + `[N0]` huella

### US8.4 — Que el rastro de auditoría no se pueda reescribir · MUST · P3
Como Oficial de Cumplimiento Ético, quiero que cada decisión y cada llamada a un modelo queden registradas
de forma permanente, para poder auditar quién hizo qué, con qué modelo y cuándo.
*Origen:* FR1.3, FR15.3, NFR11, AUTONOMIA-03.

- **AC8.4.1** Given cada tabla de cambios de estado (hallazgos, consolidaciones, versiones de reporte, lanzamientos del modo final, «Observaciones consultadas»), When intento un `INSERT` con actor u hora nulos, Then falla. `[N1]`
- **AC8.4.2** Given una fila de esos historiales, de las corridas o del registro de llamadas a modelos, When intento `UPDATE` o `DELETE` con el usuario de la aplicación, Then falla. `[N1]`

---

## Épica 9 — Plataforma en el clúster

### US9.1 — Negar la salida a internet salvo al anonimizador · MUST · P2
Como Administrador de plataforma, quiero una `NetworkPolicy` que niegue la salida a internet a todos los
pods salvo al anonimizador, para demostrar que nada sin seudonimizar sale del clúster.
*Origen:* FR12.3, NFR1, AUTONOMIA-04.

- **AC9.1.1** Given los manifiestos, When corre la política, Then falla si algún pod distinto del anonimizador tiene salida fuera del clúster, o si el anonimizador sale por otro puerto que 443 o DNS; con control negativo. `[N0]`
- **AC9.1.2** Given el clúster desplegado, When desde cada pod distinto del anonimizador ejecuto `curl -m 5` a un *host* público, Then termina con código ≠ 0, y el mismo pod sí alcanza PostgreSQL y Redis (control positivo). `[Manual]`, solo lectura, sin `apply`
- **AC9.1.3** Given el diseño, When se revisa en Infrastructure Design, Then cada componente de `deploy/` aparece en la tabla de fronteras (dentro o fuera del clúster, datos que cruzan). `[Manual]`
- **AC9.1.4** Given un turno con un *canary* único sembrado, When termina su análisis, Then el *canary* no aparece en ningún log capturado de ningún servicio. `[N1]`

### US9.2 — Saber que cada servicio está listo · MUST · P2
Como Administrador de plataforma, quiero que cada servicio exponga su salud, para que la prueba de humo
diga si el despliegue sirve.
*Origen:* FR12.5.

- **AC9.2.1** Given un servicio listo, When consulto su *endpoint* de salud, Then responde `200`; con PostgreSQL caído, no responde `200`. `[N1]`
- **AC9.2.2** Given el despliegue completo (requiere US3.1 y US2.7), When corro `scripts/smoke.sh <url-base>`, Then termina con código 0 solo si todos los servicios responden `200` y el *spec* de humo comprueba que una transcripción sintética con una contradicción sembrada produce ≥ 1 hallazgo con sus dos citas, y un relato coherente 0, en ≤ *N* s (*N* lo fija NFR Requirements). `[N3]`

### US9.3 — Declarar recursos y credenciales de cada pod · MUST · P2
Como Administrador de plataforma, quiero que cada pod declare sus recursos y tome sus credenciales y claves
de API de Secrets, para evitar caídas por memoria y credenciales en el repositorio.
*Origen:* FR12.2, FR12.4, NFR10.

- **AC9.3.1** Given los manifiestos, When corre la política de Kyverno CLI, Then falla si algún pod no tiene `resources.requests` y `resources.limits`; con control negativo. `[N0]`
- **AC9.3.2** Given los manifiestos y el archivo de perfiles, When corre la política, Then falla si una variable cuyo nombre contiene `PASSWORD`, `TOKEN`, `KEY` o `SECRET` usa `value` literal en vez de `secretKeyRef` o `envFrom`, o si el archivo de perfiles contiene una clave en vez de su referencia; y `gitleaks` termina con código 0; ambos con control negativo. `[N0]`

### US9.4 — Base de datos y cola dentro del clúster · MUST · P2
Como Administrador de plataforma, quiero PostgreSQL con CloudNativePG y Redis como artefactos revisables,
para que todo el estado viva en el clúster local.
*Origen:* FR12.1.

- **AC9.4.1** Given el chart, When corren `helm template` y `kubeconform`, Then aparecen un `Cluster` de CloudNativePG sin la extensión `pgvector` y Redis `[N0]`; y cuando el humano lo aplica tras la fusión de su PR, ambos quedan dentro del clúster `[Manual]`.
- **AC9.4.2** Given los manifiestos, When corre la política, Then falla si un `Deployment` o un `initContainer` ejecuta las migraciones; solo existen como `Job`. `[N0]`

### US9.5 — Ningún *workflow* aplica cambios al clúster ni envía trabajos a ZINE · MUST · P2
Como Administrador de plataforma, quiero que la CI y los *scripts* nunca apliquen cambios al clúster local
ni lancen trabajos en ZINE, para que todo cambio pase por una aprobación humana registrada.
*Origen:* AUTONOMIA-01, FR16.1, team-practices (mapa AUTONOMIA).

- **AC9.5.1** Given `.github/workflows/` y `scripts/`, When corre la comprobación estática, Then ninguno contiene `kubectl apply`, `helm install`, `helm upgrade`, `terraform apply` ni migraciones contra el clúster, y ningún *workflow* referencia un `kubeconfig`; con control negativo. `[N0]`
- **AC9.5.2** Given `.github/workflows/` y los *scripts* que corren en la CI, When corre la comprobación estática, Then ninguno invoca `sbatch`, `ssh`, `scp` ni `rsync` hacia ZINE; los `.sbatch` solo existen como archivos que lanza el humano; con control negativo. `[N0]`

---

## Épica 10 — Funciones SHOULD

### US10.1 — Ver el progreso del análisis · SHOULD · P1
*Origen:* FR10.1. Como Analista de Verdad, quiero ver qué hace el sistema y cuánto lleva, para no dudar si se colgó.
- **AC10.1.1** Given una corrida en proceso, When la miro, Then veo su etapa («Procesando audio…», «Analizando contradicciones…»), un cronómetro y, en el modo final, cuántas ventanas o llamadas van de cuántas; cada cambio se anuncia en `aria-live="polite"`. `[N0]` Vitest
- **AC10.1.2** Given una corrida que supera su *timeout* (lo fija NFR Requirements), When vence, Then termina en `error` con `tiempo_agotado` y la opción de reintentar; nunca queda en «Procesando» indefinidamente. `[N1]`

### US10.2 — Grabar un turno por voz · SHOULD · P1
*Origen:* FR10.2. Como Analista de Verdad, quiero grabar un turno con un botón, para usar la voz cuando el flujo de texto ya funciona.
- **AC10.2.1** Given el flujo de texto funcionando, When grabo y envío un turno, Then se transcribe con Whisper en CPU dentro del clúster y sigue el mismo camino que un turno escrito (guiado, sin página). `[N1]` con transcriptor *fake*
- **AC10.2.2** Given un transcriptor *fake* que tarda 12 s, When envío el audio, Then el `POST` responde `202` y la interfaz acepta otro envío antes de que termine. `[N1]` + `[N0]` Vitest
- **AC10.2.3** Given que el navegador niega el micrófono, When pulso grabar, Then veo «No hay acceso al micrófono. Puedes seguir escribiendo el turno» y la entrada de texto sigue disponible; mientras graba hay un indicador visible y anunciado. `[N0]` Vitest

### US10.3 — Recibir aclaraciones neutras · SHOULD · P1
*Origen:* FR10.3 (DT23). Como Analista de Verdad, quiero que el análisis incremental me proponga temas para aclarar, para decidir yo si pregunto, sin que la pregunta revele la contradicción.
- **AC10.3.1** Given una salida con `observaciones_conductor`, When se valida, Then el esquema solo admite `tipo: aclaracion_neutra`, un tema y los turnos, y rechaza cualquier otro campo. `[N0]`
- **AC10.3.2** Given una aclaración y el hallazgo que la originó, When se valida, Then el tema no contiene el texto de ninguna de las dos citas (meta de 0 %); con control negativo `[N0]`; sobre el conjunto sintético `[N2]`.
- **AC10.3.3** Given una aclaración, When la veo, Then aparece como «Aclaración sugerida · requiere tu decisión» y no se reproduce ni se registra como formulada sin mi acción. `[N0]` Vitest

### US10.4 — Escuchar la pregunta · SHOULD · P1
*Origen:* FR10.4. Como Analista de Verdad, quiero reproducir en voz la pregunta que decido formular, para leerla al compareciente.
- **AC10.4.1** Given una aclaración aprobada, When pulso «Escuchar audio», Then se sintetiza en CPU dentro del clúster y se reproduce; sin pulsarlo, el TTS *fake* registra 0 llamadas. `[N0]`

### US10.5 — Confirmar cada hallazgo en ambos órdenes · SHOULD · P1
*Origen:* FR10.5, FR4.5. Como Analista de Verdad, quiero que un hallazgo solo se registre si el verificador lo sostiene al invertir el orden de las citas, para recibir menos falsas alarmas.
- **AC10.5.1** Given un perfil con la permutación activa y un verificador *fake* que confirma solo en un orden, When termina la corrida, Then el hallazgo no se registra y el registro de llamadas muestra las dos llamadas; sin la permutación hay una sola `[N0]`; consistencia > 65 % al invertir el orden y permutación en el 100 % de las consultas *offline* `[N2]` (NFR4).

### US10.6 — Recibir una propuesta de umbral cuando hay ruido · **Retirada** (cambio 01; la sustituye US10.8)

### US10.7 — Sincronizar el clúster con GitOps · SHOULD · P2
*Origen:* FR12.6. Como Administrador de plataforma, quiero que Argo CD aplique lo fusionado en `main`, para que el clúster refleje solo cambios aprobados.
- **AC10.7.1** Given la `Application` de Argo CD, When corre la política, Then usa una *deploy key* de solo lectura y no tiene *prune* sobre CloudNativePG y sus PVC `[N0]`; la sincronización real se verifica `[Manual]`.

### US10.8 — Ver la razón de descartes como señal · SHOULD · P2
*Origen:* FR9.3, NFR15 (P13). Como Administrador de plataforma, quiero que Grafana me avise cuando una sesión acumule descartes, para revisar el *prompt* o el perfil por PR sin que el sistema cambie nada solo.
- **AC10.8.1** Given la regla de Prometheus y la ventana que fije NFR Requirements, When `promtool test rules` corre con un *fixture* en el 25 % exacto (p. ej. 5 de 20 hallazgos consecutivos descartados) y otro por encima (6 de 20), Then no alerta y alerta, respectivamente. `[N0]`
- **AC10.8.2** Given una alerta AIR, When nadie hace nada, Then ningún perfil ni *prompt* cambia; cambiarlos sigue US8.3. `[N0]`

---

## Épica 11 — Anonimizador (MUST), historial y escalado (COULD)

### US11.1 — Ver indicios afectivos · **Retirada** (cambio 01; el análisis afectivo es WON'T, DT15)

### US11.2 — Volver a una sesión desde el historial lateral · COULD · P1
*Origen:* FR11.2. Como Analista de Verdad, quiero un panel lateral con mis sesiones anteriores, para retomarlas sin salir de la sesión actual.
- **AC11.2.1** Given sesiones previas, When abro el panel lateral, Then las veo ordenadas por fecha con su estado. `[N0]` Vitest

### US11.3 — Seudonimizar antes de cualquier proveedor externo · **MUST** · P2
Como Administrador de plataforma, quiero que todo texto hacia un proveedor externo pase por el
anonimizador y que nada salga si este falla, para cumplir la soberanía de los datos identificables.
*Origen:* FR11.3, NFR1, NFR10, AUTONOMIA-04 (pregunta 10: entra en la primera rebanada como módulo de la
biblioteca; cubre la CLI y el servicio a la vez). La frontera en el clúster está en US11.6.

- **AC11.3.1** Given el conjunto sintético con entidades sembradas (nombres, lugares y números de expediente, con y sin tilde), When pasa por el anonimizador, Then el 100 % sale seudonimizado; una sola fuga hace fallar la prueba. `[N0]`
- **AC11.3.2** Given una misma persona mencionada en varios turnos, When se seudonimiza la entrevista, Then recibe la misma marca en todos (p. ej., `[PERSONA_3]`). `[N0]`
- **AC11.3.3** Given el anonimizador (a) caído, (b) lanzando una excepción o (c) sin responder antes de su *timeout*, When el analizador va a llamar a un proveedor externo, Then el `ModelGateway` *fake* registra 0 llamadas y el tramo termina en `estado: error` con el código del anonimizador. `[N0]` con 100 % de ramas
- **AC11.3.4** Given en la salida del juez (a) una cita seudonimizada válida, (b) una marca alterada, (c) una marca inventada (`[PERSONA_9]` inexistente), (d) una cita que perdió una marca, When se verifica, Then en (a) se restaura y se verifica contra el turno **original**, y (b), (c) y (d) invalidan el hallazgo. `[N0]`
- **AC11.3.5** Given un *canary* sembrado como nombre, When termina una corrida de la CLI, Then no aparece en ningún log capturado ni en ningún archivo que escribe la CLI (la tabla de correspondencia vive solo en memoria). `[N0]`
- **AC11.3.6** Given un perfil todo local, When corre una corrida, Then el anonimizador no interviene y no hay llamadas fuera del clúster. `[N0]`
- **AC11.3.7** Given un perfil comercial y una transcripción sintética con entidades sembradas, When corre el analizador (juez y verificador), Then el transporte HTTP *fake* de cada adaptador comercial captura cada cuerpo saliente y ninguno contiene una entidad sembrada (0 fugas), y todos contienen marcas `[PERSONA_n]`; control negativo: con el anonimizador puenteado en un *fixture*, la prueba falla. `[N0]`

### US11.4 — Escalar los trabajadores según la cola · COULD · P2
*Origen:* FR12.7. Como Administrador de plataforma, quiero que KEDA escale los pods de análisis con la longitud de la cola, para liberar CPU cuando no hay entrevistas.
- **AC11.4.1** Given la cola vacía durante el periodo configurado, When se evalúa el escalado, Then los pods del analizador escalan a 0; con mensajes en cola, a 1 o más. `[Manual]` en el clúster

### US11.5 — Que el anonimizador solo salga hacia los proveedores configurados · MUST · P2
Como Administrador de plataforma, quiero que el anonimizador rechace cualquier destino fuera de la lista
de proveedores, para que la única salida a internet no sirva para otra cosa.
*Origen:* FR11.4, FR12.3.

- **AC11.5.1** Given un destino fuera de la lista de dominios de los proveedores configurados, When el anonimizador recibe la petición, Then la rechaza sin abrir conexión. `[N0]`
- **AC11.5.2** Given la lista de dominios del anonimizador y la lista blanca de CoreDNS, When corre la comprobación estática, Then ambas coinciden; con control negativo. `[N0]`

### US11.6 — Que el anonimizador sea la única salida del clúster · MUST · P2
Como Administrador de plataforma, quiero que dentro del clúster toda llamada a un proveedor externo pase
por el anonimizador desplegado, para que la `NetworkPolicy` y el fallo cerrado se refuercen entre sí.
*Origen:* FR11.3, FR14.3, NFR1, AUTONOMIA-04. Dónde se seudonimiza (la biblioteca dentro de
`semantic-agent` o el servicio `anonymizer-proxy`) lo decide Domain Design; esta historia solo fija la
frontera.

- **AC11.6.1** Given `semantic-agent` con un perfil de destino externo y sin la dirección del anonimizador configurada, When arranca, Then termina con código ≠ 0 y no pasa la sonda de salud. `[N0]` + `[N1]`
- **AC11.6.2** Given `semantic-agent` con el anonimizador detenido y un servidor de proveedor *fake* en contenedor, When se analiza un turno, Then el servidor registra 0 peticiones y el tramo queda en `error` con el código del anonimizador. `[N1]`
- **AC11.6.3** Given una corrida con un *canary* sembrado, When termina, Then el *canary* no aparece en los logs de ningún servicio ni en PostgreSQL ni en Redis: la tabla de correspondencia vive solo en la memoria del proceso que restaura. `[N1]`

---

## Épica 12 — Biblioteca y línea de comandos

### US12.1 — Ejecutar el analizador por lotes desde la CLI · MUST · P4
Como Investigador del TG, quiero analizar una transcripción o un directorio de transcripciones desde la
línea de comandos, para correr el mismo analizador del producto sin levantar la plataforma.
*Origen:* FR13.2.

- **AC12.1.1** Given un directorio con 3 transcripciones del contrato y un perfil, When corro la CLI sin indicar modo, Then corre en modo final y escribe un archivo de salida del contrato por entrevista en el directorio indicado. `[N0]` con *fake*
- **AC12.1.2** Given una de las 3 corridas termina en `estado: error`, When termina la CLI, Then el código de salida es 0 y esa salida lleva su `codigo`. `[N0]`
- **AC12.1.3** Given (a) un argumento desconocido, (b) un archivo que no cumple el esquema, (c) un perfil inexistente, (d) un directorio de salida no escribible, When corro la CLI, Then el código de salida es ≠ 0, el mensaje en español nombra el problema y no se escribe ninguna salida. `[N0]`

### US12.2 — Usar la biblioteca sin infraestructura · MUST · P4
Como Investigador del TG, quiero que el analizador sea una biblioteca sin Redis, Kubernetes ni base de
datos, para que `sistema` la reciba tal cual y el producto la envuelva.
*Origen:* FR13.1. La igualdad entre la CLI y el trabajador está en AC2.2.7.

- **AC12.2.1** Given la biblioteca, When corre import-linter, Then falla si importa Redis, un cliente de Kubernetes o un controlador de base de datos; con control negativo. `[N0]`

### US12.3 — Evaluar el analizador sobre el conjunto sintético · MUST · P4
Como Investigador del TG, quiero un modo de evaluación que compare los hallazgos con las contradicciones
esperadas, para saber si un perfil cumple los umbrales antes de usarlo.
*Origen:* FR13.3, NFR4, NFR5.

- **AC12.3.1** Given un *fixture* con contradicciones esperadas conocidas y un *fake* con salidas fijas, When corro la CLI en modo evaluación, Then el reporte JSON trae los valores esperados de citas verificadas, formato JSON, permutación, precisión y sensibilidad por par de turnos (sin importar el orden), acuerdo de tipo, acuerdo entre 3 corridas y sensibilidad según la distancia entre citas. Bordes: una muestra coherente sin esperadas no divide por cero; un mismo par emitido dos veces cuenta una sola vez; un acierto de par con tipo distinto cuenta como acierto y como desacuerdo de tipo. `[N0]`
- **AC12.3.2** Given cualquier corrida de evaluación, When termina, Then el reporte registra la versión y el SHA-256 del conjunto, `prompt_sha256`, el perfil con su `config_sha256`, la familia de cada papel, los modelos por llamada, los *tokens* y el costo estimado. `[N0]`
- **AC12.3.3** Given un hallazgo en un relato coherente o en un caso trampa (vaguedad, emoción, detalle periférico, versión de terceros), When se evalúa, Then cuenta como falso positivo. `[N0]`
- **AC12.3.4** Given los umbrales que fije NFR Requirements, When una métrica no alcanza su umbral, Then la CLI de evaluación termina con código ≠ 0 y el JSON marca `pasa: false` en esa métrica `[N0]`; con un perfil real, la evaluación cumple los umbrales y el reporte se adjunta al PR que toca la IA `[N2]`.

### US12.4 — Correr el corpus del piloto sin que entre a Git · MUST · P4
Como Investigador del TG, quiero que las corridas sobre el corpus del piloto escriban fuera de Git, para
usar las entrevistas reales sin publicarlas en un repositorio público.
*Origen:* FR13.4, NFR12.

- **AC12.4.1** Given una transcripción con `origen: corpus`, When la CLI va a escribir su salida en una ruta que `git check-ignore` no cubre, Then termina con código ≠ 0 sin escribir; sin directorio explícito, escribe en el directorio de resultados que cubre `.gitignore`. `[N0]`
- **AC12.4.2** Given un archivo rastreado por Git dentro de ese directorio, When corre la comprobación de nivel 0, Then falla; con control negativo. `[N0]`
- **AC12.4.3** Given las 10 entrevistas del piloto en la máquina local, When corro la CLI, Then termina con código 0 y el resumen frente a las 4 contradicciones conocidas queda fuera de Git (prueba de humo, no mide). `[Manual]`

### US12.5 — Ver el registro de modelos de una corrida · MUST · P4, P1
Como Investigador del TG, quiero ver qué modelo atendió cada llamada y cuánto costó, para reproducir y
comparar corridas.
*Origen:* FR15.3, FR15.4, NFR11.

- **AC12.5.1** Given una corrida, When termina, Then cada llamada registra papel, proveedor, modelo, versión, esfuerzo o cuantización, motor, semilla si el proveedor la admite, *tokens* de entrada y salida, fecha y si fue al proveedor alterno. `[N0]`
- **AC12.5.2** Given la tabla de precios versionada, When termina una corrida, Then la salida suma los *tokens* por proveedor y un costo estimado; un modelo sin precio en la tabla se reporta como «sin precio» sin detener la corrida. `[N0]`
- **AC12.5.3** Given una sesión, When abro una corrida en la consola, Then veo su registro de modelos en solo lectura. `[N1]` + `[N0]` Vitest

### US12.6 — Subir y consultar un reporte de corrida o evaluación · MUST · P4
Como Investigador del TG, quiero subir a la consola los reportes JSON de la CLI y consultarlos, para
tener en un solo lugar las cifras de cada perfil y modelo sin guardar testimonio.
*Origen:* FR13.5, FR1.2, NFR12; Refined Mockups (respuesta 10, seguimiento 7).

- **AC12.6.1** Given un reporte JSON válido que incluye en un hallazgo el texto *canary* «CANARIO-7f3a», When el investigador lo sube, Then la respuesta es `201`, se ve «Reporte subido. Se guardaron solo metadatos y cifras; el texto de transcripciones, hallazgos y citas se descartó», y una búsqueda de «CANARIO-7f3a» en todas las columnas de texto y en los logs capturados da 0 coincidencias. `[N1]`
- **AC12.6.2** Given el mismo archivo subido dos veces (mismo SHA-256), When se sube la segunda, Then `409` con «Este reporte ya está subido» y 0 filas nuevas. `[N1]`
- **AC12.6.3** Given un usuario `analista` o `admin`, When llama a cualquier ruta de reportes de investigación, Then `403`; y en la interfaz no ve «Reportes». `[N1]` + `[N0]` Vitest
- **AC12.6.4** Given un reporte al que le falta una métrica, When abro su detalle, Then esa métrica dice «No informado», nunca 0. `[N0]` Vitest

### US12.7 — Comparar dos reportes · SHOULD · P4
Como Investigador del TG, quiero comparar dos reportes lado a lado, para ver qué cambia entre perfiles,
modelos o versiones.
*Origen:* FR13.5; Refined Mockups (seguimiento 7).

- **AC12.7.1** Given 0, 1 o 3 reportes marcados, When miro «Comparar seleccionados», Then está deshabilitado (enfocable) con «Marca dos reportes para compararlos»; con exactamente 2 se habilita. `[N0]` Vitest
- **AC12.7.2** Given dos reportes de conjuntos distintos, When los comparo, Then solo se comparan metadatos y leo «Conjuntos distintos: las métricas no son comparables». `[N0]` Vitest
- **AC12.7.3** Given dos reportes comparables, When los comparo, Then cada fila marca «=» o «≠» en texto y las diferencias numéricas llevan su signo. `[N0]` Vitest

---

## Épica 13 — Perfiles y modelos

### US13.1 — Elegir el perfil de modelos de la sesión · MUST · P1
Como Analista de Verdad, quiero ver los perfiles aprobados con lo que implica cada uno, para elegir con
conocimiento si el texto saldrá seudonimizado hacia un proveedor comercial.
*Origen:* FR14.5, FR14.4, FR4.8.

- **AC13.1.1** Given el archivo de perfiles, When abro «Nueva sesión», Then veo solo los perfiles aprobados, cada uno con una línea en lenguaje llano («Comercial: el texto sale seudonimizado del clúster» o «Local: nada sale del clúster») y, en un bloque desplegable, el proveedor y el modelo de cada papel. `[N0]` Vitest + `[N1]`
- **AC13.1.2** Given un perfil de demostración que declara juez y verificador de la misma familia, When lo veo y cuando se consolida un reporte con él, Then aparece el aviso «El modelo que propone cada contradicción y el que la confirma son de la misma familia: la confirmación es menos independiente». `[N0]` Vitest + `[N1]`
- **AC13.1.3** Given un perfil local, When lo veo en «Nueva sesión» y en la cabecera de la sesión, Then leo «Análisis por ventanas: no busca contradicciones entre turnos separados por más de N turnos». `[N0]` Vitest
- **AC13.1.4** Given el formulario de «Nueva sesión», When lo abro, Then ningún perfil viene preseleccionado, leo «El perfil no se puede cambiar después de crear la sesión» y «Crear sesión» queda deshabilitado con su motivo hasta que elija un perfil. `[N0]` Vitest

### US13.2 — Que cada corrida guarde su configuración efectiva · MUST · P4
Como Investigador del TG, quiero que cada corrida guarde la configuración exacta con su huella, para
saber si dos corridas son comparables.
*Origen:* FR14.1, FR14.2.

- **AC13.2.1** Given dos configuraciones iguales, When calculo su `config_sha256`, Then coincide, también si cambia el orden de las claves o el formato del YAML (forma canónica); cambiar cualquier parámetro de un papel la cambia; el valor de una clave de API nunca entra en la huella. `[N0]` prueba de propiedad con Hypothesis
- **AC13.2.2** Given el archivo de perfiles versionado, When se valida, Then contiene al menos un perfil comercial y el perfil `todo-local`, y cada perfil local declara su modo fragmentado. `[N0]`

### US13.3 — No arrancar con un perfil inválido · MUST · P2
Como Administrador de plataforma, quiero que ni los servicios ni la CLI arranquen con un perfil inválido,
para que nunca se llame a un proveedor externo sin el anonimizador.
*Origen:* FR14.3, NFR10, AUTONOMIA-04 (pregunta 10).

- **AC13.3.1** Given (a) un archivo de perfiles inválido, (b) un perfil con destino externo sin anonimizador, (c) una clave de API referenciada que falta, When arranca un servicio, Then el proceso termina con código ≠ 0, no pasa la sonda de salud y el log nombra el ajuste sin su valor (un valor *canary* no aparece en el log); control positivo por caso: el mismo archivo corregido arranca y pasa la sonda. `[N0]` + `[N1]`
- **AC13.3.2** Given los mismos tres casos, When corro la CLI, Then termina con código ≠ 0 **antes** de cualquier llamada (el *fake* registra 0 llamadas). `[N0]`

### US13.4 — Juez y verificador de familias distintas · MUST · P4
Como Investigador del TG, quiero que la evaluación rechace un perfil con juez y verificador de la misma
familia, para que un modelo no confirme sus propios errores.
*Origen:* FR14.4, NFR5 (Escenario B).

- **AC13.4.1** Given un perfil de evaluación con juez y verificador de la misma familia, When se valida, Then se rechaza con un mensaje que nombra la familia. `[N0]`
- **AC13.4.2** Given un perfil de demostración de la misma familia sin la declaración explícita, When se valida, Then se rechaza; con la declaración, se acepta. `[N0]`

### US13.5 — Usar el proveedor alterno ante un bloqueo de contenido · MUST · P4
Como Investigador del TG, quiero que un bloqueo de contenido o un error del proveedor pase al proveedor
alterno si el perfil lo prevé, para que un testimonio duro no se pierda por un filtro.
*Origen:* FR15.2.

- **AC13.5.1** Given un perfil con proveedor alterno y un *fake* que lanza bloqueo de contenido, When corre, Then la llamada va al alterno y el registro la marca como tal. `[N0]`
- **AC13.5.2** Given un perfil sin proveedor alterno y el mismo *fake*, When corre, Then `estado: error` con `codigo: bloqueo_contenido` y `hallazgos` vacío. `[N0]`

### US13.6 — Correr la primera rebanada con un proveedor comercial y uno local · MUST · P4
Como Investigador del TG, quiero un adaptador para el proveedor comercial de la primera rebanada y otro
para servidores locales compatibles con OpenAI, para comparar modelos con el mismo código desde el
principio.
*Origen:* FR15.1 (pregunta 10).

- **AC13.6.1** Given respuestas grabadas del proveedor comercial elegido para la primera rebanada y de un servidor compatible con OpenAI (sin red), When corre la prueba de contrato de cada adaptador, Then ambos devuelven la misma estructura con la salida validada contra el esquema. `[N0]`
- **AC13.6.2** Given una respuesta que no cumple el esquema, When la procesa cualquier adaptador, Then lanza el error tipado de salida inválida. `[N0]`

### US13.7 — Comparar los demás proveedores comerciales · MUST · P4
Como Investigador del TG, quiero adaptadores para los otros dos proveedores comerciales de los perfiles
del TG, para usarlos como verificador de otra familia o como comparación.
*Origen:* FR15.1, FR14.4.

- **AC13.7.1** Given respuestas grabadas de los otros dos proveedores comerciales (Anthropic, Google u OpenAI, los que no se usaron en US13.6), When corre la prueba de contrato de cada adaptador, Then devuelven la misma estructura que US13.6 con la salida validada contra el esquema. `[N0]`

---

## Épica 14 — Evaluación por lotes en ZINE

### US14.1 — Validar los modelos locales en el clúster antes del diseño · MUST · P4
Como Investigador del TG, quiero medir en el clúster Ing. Sistemas lo que los modelos locales pueden dar,
para que el diseño no se apoye en cifras supuestas.
*Origen:* FR16.1, NFR12, FR16.3 (preguntas 14, 15 y 16).

**Reglas de la historia.** Es una historia de **medición**: no depende del código del producto, sus
criterios registran cifras con su comando y no fijan umbrales (los fija NFR Requirements). Corre mientras
la tarea 4L sigue en segundo plano y reutiliza su entorno conda y sus modelos. Los `.sbatch` y el reporte
(solo cifras) viven en `docs/validacion-zine/` por commit directo (pregunta 16); los escribe el agente y
**los lanza el humano** (AUTONOMIA-01). Se respetan las normas del clúster: todo paso es un `.sbatch` (en
el nodo de entrada solo `scp`, `sbatch`, `squeue` y `sacct`); `HOME` y cachés dentro de la carpeta del
proyecto; entorno conda propio, sin Apptainer; cada medición escribe solo bajo
`/zine/HPC02S1/freyes/tg4L/validacion/`, separada de las corridas de la 4L. Como la 4L ocupa los SL250s en
`--exclusive`, los trabajos se lanzan mientras solo corre su medición `--array=8`, o con una dependencia
explícita; el humano decide el orden. Cada criterio registra en el reporte el comando exacto, el ID del
trabajo SLURM, el nodo y el SHA-256 del modelo; un resultado «no medible», con su motivo y su salida,
también cierra el criterio.

**Evidencia y verificación (R-02, R-05).** El reporte es `docs/validacion-zine/reporte.md`, con una
sección `## M1` a `## M6` por criterio (AC14.1.1 a AC14.1.6) y la sección `## Revisión` de AC14.1.7. Los
`.sbatch` se llaman `docs/validacion-zine/m<n>-<nombre>.sbatch`, y cada uno escribe su salida bajo
`/zine/HPC02S1/freyes/tg4L/validacion/m<n>/`; el humano copia al reporte solo las cifras. La comprobación
`python3 docs/validacion-zine/comprobar_reporte.py docs/validacion-zine/reporte.md` termina con código 0
solo si cada sección M1–M6 tiene `Comando:`, `Trabajo SLURM:`, `Nodo:`, `SHA-256 del modelo:` (o
`No aplica:` con motivo, para M5) y un `Resultado:` con cifras o `No medible:` con motivo; con
`--revision`, además exige la sección `## Revisión` completa. Tiene control negativo: un reporte de
ejemplo al que le falta un campo hace fallar la comprobación. Es evidencia de proceso: no es código del
producto ni cuenta para la cobertura.

- **AC14.1.1** Given Qwen3.6-35B-A3B Q8_0 en un nodo SL250s, When corre `llama-bench` (con `-p 2048`, `-n 128` y `-t` explícitos), Then la sección M1 registra los *tokens*/s de lectura y de generación, y las horas de la medición `--array=8` de la 4L; si esa medición no termina en el plazo que fija el humano al lanzarla, se registran sus cifras parciales (llamadas, *tokens* y segundos de `registro_4L_8.csv` y del log del servidor) y el reporte lo dice (pregunta 15). `[ZINE]`
- **AC14.1.2** Given **un solo** `llama-server` de conda-forge levantado en un SL250s con ese modelo, When un trabajo de sondeo envía 20 peticiones con salida forzada por esquema JSON (o gramática), `seed` y caché del *prompt*, con el razonamiento de Qwen encendido y apagado, Then la sección M2 clasifica cada parámetro como aceptado, rechazado o aceptado sin efecto, y registra cuántas de las 20 salidas validan contra el esquema en cada caso, validadas por el mismo trabajo con `jsonschema`. `[ZINE]`
- **AC14.1.3** Given las entrevistas del piloto copiadas por `scp` a la carpeta del proyecto en el clúster (nunca a Git), When un trabajo en `hpchead02` cuenta sus *tokens* con `llama-tokenize` y el vocabulario del GGUF de Qwen, Then la sección M3 registra solo cifras (por entrevista, el máximo y la mediana, y si la más larga cabe en 163 840 junto con el *prompt*) y dice qué entrevistas se contaron. `[ZINE]`
- **AC14.1.4** Given el mismo servidor de AC14.1.2 con `--parallel 1` y un *prompt* sintético, When se envían dos peticiones idénticas (misma `seed`, mismos hilos y la misma caché del *prompt*), Then la sección M4 registra si el SHA-256 del contenido generado coincide y, si no, el primer *token* que difiere. `[ZINE]`
- **AC14.1.5** Given una *wheelhouse* armada por un trabajo en `hpchead02` (`pip download` con las dependencias previstas de la biblioteca, p. ej. `pydantic`, `httpx` y `jsonschema`, más un paquete de prueba mínimo con un *entry point*), When otro trabajo en un SL250s sin internet instala con `pip install --no-index --find-links` en el entorno conda propio y ejecuta el *entry point*, Then termina con código 0, la sección M5 registra las versiones instaladas y `grep -c -E "Downloading|Collecting .* from https?://"` sobre el log del trabajo da 0. `[ZINE]`
- **AC14.1.6** Given un modelo GGUF de una familia distinta de Qwen, con licencia compatible con el TG (DT10), en Q8_0 o BF16 y que quepa en un nodo, When un trabajo en `hpchead02` lo descarga y comprueba su SHA-256 contra el publicado, y otro corre `llama-bench` en un SL250s, Then la sección M6 registra la familia, el modelo, su cuantización, su `.sha256ok` y sus *tokens*/s. `[ZINE]`
- **AC14.1.7** Given el reporte de las seis mediciones en `docs/validacion-zine/`, When el humano lo revisa, Then la sección `## Revisión` registra quién, la fecha y una de tres decisiones —«Diseñar con modelos locales», «Diseñar con limitaciones registradas» (las nombra) o «Repetir mediciones» (dice cuáles)—, y responde a las cifras que deciden el diseño: (a) *tokens*/s de generación de M1 y las horas estimadas de un modo final sobre la entrevista más larga de M3; (b) si M2 fuerza el esquema JSON (20 de 20 válidas) o hace falta reparar la salida; (c) si la entrevista más larga cabe en el contexto con el *prompt* (M3) o el modo fragmentado es obligatorio con modelos locales; (d) si M4 es repetible; (e) si M5 instala sin internet; (f) si M6 deja un verificador de otra familia con velocidad útil. Se verifica con `comprobar_reporte.py --revision` (código 0), con el commit `aidlc(validacion-zine): …` que la añade, y porque el primer evento de Domain Design en la auditoría tiene una fecha posterior a ese commit (`git log -1 --format=%cI -- docs/validacion-zine/reporte.md`). Con «Repetir mediciones», Domain Design no empieza. `[Manual]`

### US14.2 — Preparar el paquete de entrada para ZINE · MUST · P4
Como Investigador del TG, quiero un paquete de entrada armado por un script revisable, para correr la CLI
en el clúster sin versionar el corpus del piloto ni dejar credenciales allí.
*Origen:* FR16.1, FR16.2, NFR12 (pregunta 11). Estos son los `.sbatch` de producción: entran por PR
(pregunta 16).

- **AC14.2.1** Given el repositorio, When corre la comprobación de nivel 0, Then para ZINE solo hay los `.sbatch`, el script que arma el paquete y un manifiesto con nombres y SHA-256, sin contenido de entrevistas; con control negativo. `[N0]`
- **AC14.2.2** Given el script de empaquetado, When arma el paquete, Then lo escribe en un directorio ignorado por Git, y la comprobación de nivel 0 falla si Git rastrea algo de ese directorio; con control negativo. `[N0]`
- **AC14.2.3** Given el paquete armado, When se valida, Then cada transcripción cumple el esquema del contrato y cada archivo está en el manifiesto y proviene del conjunto sintético o del corpus del piloto; un archivo ajeno lo hace fallar. `[N0]`
- **AC14.2.4** Given el paquete armado, When corre `gitleaks` sobre él, Then termina con código 0: no lleva credenciales, y en el clúster no se clona el repositorio. `[N0]`
- **AC14.2.5** Given un SL250s sin internet y el paquete con la CLI real, When un trabajo la instala con `pip install --no-index --find-links` y analiza una transcripción sintética contra el servidor local, Then termina con código 0 y registra la versión instalada. `[ZINE]`

### US14.3 — Registrar el modelo y la cuantización de cada corrida en ZINE · MUST · P4
Como Investigador del TG, quiero que cada resultado de ZINE diga con qué modelo, cuantización y motor se
produjo, para que las mediciones sean comparables.
*Origen:* FR16.2.

- **AC14.3.1** Given una salida de ZINE sin modelo, cuantización, motor o versión, When la carga el modo evaluación, Then la rechaza con un mensaje que nombra el campo. `[N0]`
- **AC14.3.2** Given una corrida con una cuantización distinta de Q8 o BF16, When la carga el modo evaluación, Then la marca «no válida para medir capacidades». `[N0]`

---

## Dependencias

| Historia | Depende de |
|---|---|
| US3.6, US13.2 | US12.2 (la biblioteca) |
| US3.4, US3.2, US3.5, US3.7 | US3.6 (esquema del contrato) |
| US13.6 | US13.2 |
| US11.3 | US12.2 y US13.6 (módulo de la biblioteca, primera rebanada; pregunta 10) |
| US13.3, US12.1 | US13.2 y US11.3 |
| US12.3 | US12.1 y el conjunto sintético |
| US13.5, US13.7 | US13.6 |
| US14.2, US14.3 | US12.1 |
| US14.1 | Ninguna historia: no depende de código (AC14.2.5 instala la CLI real después) |
| US12.6 | US8.2 (rol `investigador`) y US12.3 (reporte JSON de evaluación) |
| US12.7 | US12.6 |
| US2.1, US13.1 | US8.1 y el archivo de perfiles (US13.2) |
| US2.2, US2.3, US2.6 | US2.1 |
| US2.4 | US2.2 |
| US2.7 | US2.4 o US2.6 |
| US2.5, US8.2 | US8.1 |
| US3.1 | US2.2 o US2.6, y US3.4 |
| US5.1–US5.4 | US3.1 |
| US6.1 | US2.7, US5.1–US5.3 |
| US6.2, US6.3 | US6.1 |
| US7.1 | US2.2, US5.1 |
| US11.6 | US11.3 y US9.1 |
| US9.2 (AC9.2.2) | US3.1, US2.7 |
| US10.2–US10.5 | US2.2 y US3.1 (flujo de texto funcionando) |
| US10.8 | US5.3 y FR12.6 (Prometheus/Grafana) |
| US12.2 | Ninguna: es la raíz de la primera rebanada |
| US3.3, US12.5, US13.4, US12.4 | US12.1 (corrida desde la CLI); US13.4 también US13.2 |
| US11.5 | US11.3 |
| US5.5 | US3.6 (salida del analizador) y US5.1 (textos de la interfaz) |
| US5.6, US10.1 | US2.2, US3.1 y US6.1 (el flujo que recorren) |
| US8.1 | US9.4 (base de datos) |
| US8.3, US8.4 | US8.1 y US13.2 |
| US9.1, US9.3, US9.4, US9.5 | Ninguna historia: artefactos de plataforma; US9.1 se prueba junto con US11.6 |
| US10.7 | US9.1–US9.5 |
| US11.2 | US2.5 |
| US11.4 | US9.4 y la cola del modo incremental (US3.6) |

**Ruta crítica.** Primera rebanada (orden de `team.md`, corregido por la pregunta 10): US12.2 → US3.6 →
US3.4 → US3.2 → US13.2 → US13.6 → US11.3 → US13.3 → US3.5 → US12.1 → US12.3. Después, la consola:
US8.1 → US13.1 → US2.1 → US2.2 → US3.1 → US5.1 → US2.4 → US2.7 → US6.1 → US6.2.

**Alto de proceso.** US14.1 no es una dependencia de código: es la condición para empezar Domain Design
(preguntas 14 y 15).

## Cobertura AUTONOMIA

| Regla | Prueba del mapa de team-practices | Criterios |
|---|---|---|
| 01 | Ningún *workflow* ni *script* aplica cambios al clúster ni envía trabajos a ZINE | AC9.5.1, AC9.5.2, AC9.4.1, AC8.3.3; `[ZINE]` siempre lanzado por el humano |
| 02 | Cada tarea nombra su verificación | Todos los criterios llevan nivel y comando o prueba |
| 03 | Máquina de estados con actor y hora | AC5.1.2–AC5.1.4, AC5.2.1, AC5.3.2, AC8.4.1, AC8.4.2 |
| 03 | Consolidación explícita con SHA-256 | AC6.1.1–AC6.1.7, AC6.3.3 |
| 03 | Esquema sin campos de veracidad y escaneo de vocabulario | AC5.5.1–AC5.5.4, AC3.2.4, AC3.3.2 |
| 04 | *Payload* saliente de cada adaptador y fallo cerrado (niveles 0 y 1) | AC11.3.1–AC11.3.7, AC11.6.1–AC11.6.3, AC13.3.1, AC13.3.2 |
| 04 | `NetworkPolicy` estática y manual; dominios de salida | AC9.1.1–AC9.1.4, AC11.5.1, AC11.5.2 |
| 05 | Hallazgo rechazado sin cada campo; cita alterada o en otro turno no sale | AC3.4.1–AC3.4.5 |
| 05 | `error` ⇒ hallazgos vacíos; cita restaurada antes de verificarse | AC3.2.1, AC13.5.2, AC11.3.4, AC3.4.5 |

## Notas INVEST

- Cada historia MUST se puede probar por sí misma con datos sintéticos y dobles deterministas del
  `ModelGateway`; las dependencias de la tabla son de datos de prueba, no de código compartido.
- La verificación de citas (US3.4) se separó de la presentación del hallazgo (US3.1), como pidió la
  revisión de la primera pasada (R-04), y el verificador (US3.5) del incremental (US3.6).
- El modo final (US2.7) y la importación (US2.6) son historias propias porque cambian el disparo del
  análisis (pregunta 12) y la consolidación (pregunta 13).
- El anonimizador se partió en la biblioteca (US11.3, primera rebanada, nivel 0) y la frontera en el
  clúster (US11.6); los adaptadores, en los de la primera rebanada (US13.6) y los demás comerciales
  (US13.7), para que la rebanada cierre sin esperarlos.
- US14.1 es una historia de medición, no de producto: sus criterios registran cifras con su comando y no
  fijan umbrales; los umbrales los fija NFR Requirements con esas cifras.
- La regla «ninguna MUST depende de U8–U10» de la primera pasada deja de cumplirse: el anonimizador
  (US11.3, US11.5) es MUST desde el cambio 01. Units Generation lo debe tener en cuenta.
- Los NFR de calidad (NFR2–NFR8, NFR13, NFR14) no son historias: quedan diferidos a NFR Requirements y
  Build and Test (respuesta 3).
- US10.5 duplica las llamadas al verificador por candidato; Delivery Planning debe contarlo frente a NFR3
  y NFR8.
