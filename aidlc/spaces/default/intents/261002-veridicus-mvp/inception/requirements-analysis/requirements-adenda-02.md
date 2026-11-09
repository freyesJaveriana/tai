# Adenda 02 de requisitos — protocolo ético (VE-01 a VE-17)

**Origen.** Cambio 02 de la app `veridicus`, «protocolo ético», aprobado por el investigador el 2026-11-05
(protocolo ético del TG, parte B y capítulos 5, 7, 8 y 11; decisiones D10.2, D10.3 y D10.4). El cambio y el
protocolo están fuera del repositorio. Aquí solo se copian los requisitos con sus ID y la referencia
«protocolo ético del TG, capítulo N».

**Vía.** Es la que pide el §3 del cambio: un archivo **nuevo** que se suma a `requirements.md` (revisión 2,
aprobada) **sin modificarlo** ni rehacer lo aprobado. Los ID `VE-xx` se conservan tal como vienen en el
cambio para que el TG y este repositorio citen lo mismo. Las historias que derivan de esta adenda están en
`inception/user-stories/stories-adenda-02.md`. Refined Mockups (2.5) no se reabre: el aviso fijo, los
botones de pausa y de terminar y el formulario de reporte quedan especificados en esa adenda de historias,
con sus textos visibles (§3.1 del cambio).

**Decisiones ya tomadas por el investigador** (cambio 02, §4; confirmadas por el autor el 2026-11-06):

- **Retención (D10.2):** 90 días como máximo por defecto; configurable **solo hacia abajo**.
- **Reconocimiento del analista (D10.3):** en el primer uso, **cada 90 días** y **cada vez que cambie el
  texto** de las reglas.
- **Nombre del reporte (D10.4):** «reporte de revisión», también en los entregables del curso, informando
  al profesor de TAI. Hecho en `specs/prd.md` y `docs/limite-autonomia.md` con el commit `fix(prd): …`
  (VE-03).

**Prioridad.** Todos son **MUST**: el protocolo los pide como condición para desplegar. **Excepción
(aprobación de Domain Design, 2026-11-07):** las VE marcadas «demostración» se construyen y se prueban,
pero no bloquean el uso de la consola, porque tg-veridicus es un proyecto de investigación y
demostración, no de despliegue (pregunta 10 y Seguimiento 1 = A de Domain Design; precisiones DD-xx de
`inception/domain-design/components.md`). El orden y el
límite del MVP los fija Delivery Planning al revisarse por los cambios 01 y 02.

**Niveles de prueba.** Los mismos de `stories.md` (`[N0]` a `[N3]`, `[Manual]`). VE-02, VE-05, VE-09 y
VE-14 son pruebas de nivel 0, como guardias sin red (§3.5 del cambio).

---

## 1. Uso y lenguaje (protocolo ético del TG, capítulo 11)

- **VE-01 — Propósito limitado (MUST).** El reporte y la consola muestran un aviso fijo: «Los hallazgos son
  sugerencias de revisión sobre la coherencia interna del relato. No son prueba, no indican falsedad y no
  deben usarse para decidir sobre la persona». El texto vive en un archivo versionado y solo cambia por PR,
  y solo para hacerlo más estricto: el texto nuevo contiene el anterior completo.
  *Criterio:* el aviso está en cada página del reporte `[N1]` y en la cabecera de la consola `[N0]`/`[N3]`.
  Una prueba falla si el texto versionado no contiene la frase base `[N0]`.
- **VE-02 — Vocabulario (MUST).** La lista de vocabulario prohibido de C8 (versión 1.0.0, 9 términos)
  suma «prueba», «probatorio», «pliego», «inculpa», «miente», «engaño» y «falso», con sus variantes
  (en una versión nueva de la lista, por PR), en la interfaz y en el reporte.
  *Criterio:* la prueba de la política de integridad pasa sobre las plantillas de la interfaz y del reporte
  y falla sobre un *fixture* con cada término nuevo `[N0]`. Ver la precisión **A-1** (el aviso de VE-01
  contiene «prueba»).
- **VE-03 — Corrección del PRD y del PVB (MUST).** «Rigurosidad probatoria» y «pliego de evidencias»
  pasan a «revisión de la coherencia del relato», y el reporte forense pasa a «reporte de revisión»,
  también en los entregables del curso.
  *Criterio:* diff del PRD (commit `fix(prd): …`). **Hecho** el 2026-11-06. Las etapas siguientes nombran
  la unidad del reporte «reporte de revisión». El slug `forensic-report` de U7 se revisa en Units
  Generation.
- **VE-04 — Reconocimiento del analista (demostración, D10.3; precisión DD-01).** Antes de abrir una sesión, el analista reconoce
  que los hallazgos no son prueba, que una contradicción puede venir del trauma y que no se confronta a la
  persona (DT23). Se pide en el primer uso, cuando pasaron 90 días desde el último reconocimiento y cuando
  cambia la versión del texto. Cada reconocimiento guarda quién, cuándo y la versión del texto aceptada.
  *Criterio:* sin un reconocimiento vigente, la consola muestra el diálogo y un aviso, pero no rechaza
  abrir ni crear una sesión (DD-01). Con reloj simulado, el día 90 sigue vigente y el día 91 no. Un texto
  con otra versión pide un reconocimiento nuevo `[N1]`.
- **VE-05 — Pregunta sugerida (MUST para la validación; la función sigue SHOULD, FR10.3).** Antes de
  mostrarse, la aclaración neutra se valida con la regla de DT23: nunca menciona la contradicción, nunca
  dice «antes dijo» ni sus variantes, nunca contiene una cita.
  *Criterio:* prueba con frases prohibidas, con control negativo; la aclaración que no pasa no se muestra
  `[N0]`.

## 2. La persona entrevistada en el despliegue (protocolo ético del TG, capítulos 5 y 7)

- **VE-06 — Consentimiento (MUST).** Una sesión no habilita la captura de turnos sin registrar el
  consentimiento de la persona entrevistada, o la constancia de la autoridad que lo exime, con la versión
  del texto. Si se usa la voz (FR10.2), también hace falta la autorización expresa de grabar. Si la persona
  es compareciente o tercero civil, la sesión exige constancia de que la entidad que despliega tiene
  mandato y garantías legales frente a jueces. El consentimiento viaja con la transcripción en un bloque
  `consentimiento` de la entrada del contrato común (precisión **A-4**): la consola lo registra en la
  sesión guiada; la importación y la CLI lo leen del archivo.
  *Criterio:* sin el registro, la API rechaza los turnos, el bloque pegado, la importación y la voz, y no
  crea filas. Sin la autorización de voz, la grabación se rechaza aunque haya consentimiento `[N1]`. La
  biblioteca rechaza una transcripción sin el bloque antes de cualquier llamada a un modelo, salvo con
  `origen: sintetico` `[N0]`.
- **VE-07 — Contenido del consentimiento (MUST).** El texto del consentimiento lo redacta y versiona el TG
  (protocolo ético del TG, capítulo 5). Veridicus no lo copia: registra su versión (VE-06). El texto dice
  que un sistema de IA analiza la coherencia del relato, que una persona revisa los hallazgos y que no son
  prueba. Dice también quién accede y por cuánto tiempo, y que el texto seudonimizado lo procesa un
  proveedor comercial salvo que la persona pida el modo local (con autorización expresa de la
  transferencia). Por último, dice que la confidencialidad tiene límites legales, incluido el deber de
  denunciar.
  *Criterio:* revisión humana del texto del TG frente a esta lista, con evidencia adjunta `[Manual]`. El
  perfil de la sesión es local si el consentimiento no autoriza la transferencia `[N1]`.
- **VE-08 — Audio (MUST).** El audio se borra al confirmar la transcripción del turno, salvo autorización
  expresa de conservarlo, y nunca sale a un servicio externo sin seudonimizar (NFR1).
  *Criterio:* prueba del ciclo de vida del audio. Tras confirmar el turno, no queda audio en el volumen ni
  en la cola. Con la autorización, el audio se conserva y cae bajo la retención de VE-12 `[N1]`.
- **VE-09 — La persona entrevistada no ve el análisis (MUST).** La persona entrevistada no tiene cuenta, y
  ninguna pantalla ni canal dirigido a ella muestra hallazgos, citas ni observaciones. El único canal hacia
  ella es la voz de la pregunta que el analista aprueba (FR10.4), que solo reproduce un texto que pasó
  VE-05.
  *Criterio:* prueba de permisos. Ningún rol distinto del dueño de la sesión lee sus hallazgos, y el TTS
  rechaza un texto que no sea una aclaración aprobada y validada `[N0]`.
- **VE-10 — Pausa y detención (MUST).** El analista tiene «Pausar análisis» y «Terminar sesión», que
  detienen al instante el análisis incremental. Si se retira el consentimiento, lo dicho después no se
  analiza.
  *Criterio:* tras pausar o terminar, no se encola ninguna corrida nueva y las corridas en cola se cancelan
  sin llamar a ningún modelo. Tras registrar la retirada, los turnos posteriores se rechazan y ninguno
  entra en una corrida, tampoco en el modo final `[N1]`.
  *Precisión DD-06 (aprobación de Domain Design, 2026-11-07):* VE-10 sigue MUST en InterviewSession, en
  dos partes. (a) Principio del analizador (A-4), MUST en cualquier caso: tras la retirada del
  consentimiento no se encola ni se analiza ninguna corrida nueva. (b) Los estados `pausada` y
  `terminada`, con su registro de quién y cuándo, y la cancelación de lo encolado al pausar o terminar,
  también se mantienen MUST. Si en el futuro (b) bajara a demostración, cambiaría solo el nivel de
  exigencia, no el dueño: esos estados seguirían en InterviewSession.

## 3. Acceso, retención y auditoría (protocolo ético del TG, capítulo 8)

- **VE-11 — Registro de acceso (demostración; precisión DD-02).** Un registro de solo inserción guarda quién abrió qué sesión,
  hallazgo o reporte, y cuándo. Solo lleva identificadores (NFR10).
  *Criterio:* las pruebas consultan el registro tras abrir cada recurso, y un intento de modificar o
  borrar una fila falla (como NFR11) `[N1]`. El criterio no cambia con DD-02: el registro no es una
  compuerta, y lo escribe ConsoleApi en EthicsGovernance.
- **VE-12 — Retención (demostración, D10.2; precisión DD-03).** Cada sesión tiene un plazo de retención de **90 días** como máximo
  por defecto. El plazo puede reducirse y nunca ampliarse: el máximo vive en el catálogo de límites
  (`contracts/limits.v1.yaml`, solo cambia por PR) y la sesión solo admite un valor menor o igual. Al
  vencer, el borrado lo hace el `Job` de retención, que en el clúster lanza el humano como artefacto
  revisable (AUTONOMIA-01); el sistema no lo programa (DD-03). Deja un acta de borrado.
  *Criterio:* con reloj simulado, la sesión, sus turnos, hallazgos, reportes, reportes de problemas y
  audio conservado se borran al vencer el plazo. El acta registra IDs, SHA-256 de los reportes borrados, cuándo y por qué regla. Un
  plazo mayor que el máximo se rechaza `[N1]`. Ver la precisión **A-2** frente a NFR11 y FR7.5.
- **VE-13 — Exportación (MUST).** Solo exportan el reporte el analista dueño de la sesión y el
  administrador. Cada exportación lleva una marca de agua visible con el usuario y la hora, y el SHA-256
  de la versión consolidada de la que sale (precisión **A-3**).
  *Criterio:* prueba de roles: el investigador y un analista que no es el dueño reciben `403`. La
  exportación lleva la marca del usuario que la pidió y queda en el registro de acceso con el SHA-256 del
  archivo exportado, que coincide con `sha256sum` del archivo descargado `[N1]`.
- **VE-14 — Registro de la anonimización (MUST).** Toda corrida registra modelo, versión, *prompt* y
  perfil (FR15.3) **y** si pasó por el anonimizador. Una llamada sin anonimizar a un proveedor comercial
  es un incidente que bloquea la sesión.
  *Criterio:* prueba de la falla cerrada. Con un registro de llamada a un proveedor comercial sin
  anonimizar (inyectado en la prueba), la sesión pasa a bloqueada, se rechazan nuevas corridas y queda un
  incidente registrado `[N0]`/`[N1]`.

## 4. Analista y problemas no previstos (protocolo ético del TG, capítulo 11)

- **VE-15 — Reporte de problemas (demostración; precisión DD-04).** Desde la consola, el analista reporta: hallazgo dañino,
  vocabulario indebido, cita que no corresponde, malestar de la persona entrevistada, falla de
  anonimización o uso indebido. El reporte guarda la categoría, IDs de sesión o hallazgo, quién y cuándo,
  y una nota. La nota no debería traer texto del testimonio: la consola avisa, sin rechazar (DD-04), y la
  retención la borra con la sesión.
  *Criterio:* el formulario envía y el registro guarda las seis categorías. Una nota con una cita literal
  del testimonio (coincidencia con un turno de la sesión) muestra un aviso y se guarda con
  `testimony_warning` `[N1]`.
- **VE-16 — Bienestar del analista (demostración; precisión DD-05).** Al abrir una sesión, la consola muestra un aviso de
  contenido. Además muestra un recordatorio de pausa cada cierto intervalo, configurable por PR en el
  catálogo de límites, como cualquier otro ajuste del sistema (FR9).
  *Criterio:* el aviso aparece al abrir la sesión. Con reloj simulado, el recordatorio aparece al cumplirse
  el intervalo `[N0]` Vitest. El criterio no cambia con DD-05: ya eran avisos que no bloquean.
- **VE-17 — Métrica de sesgo (MUST, en la validación y no en la consola).** El informe de evaluación da
  la tasa de hallazgos por tipo de hecho y por perfil de la persona. Así se detecta si el analizador marca
  más contradicciones en relatos de violencia sexual o en personas con un perfil dado.
  *Criterio:* el conjunto sintético etiqueta cada transcripción por tipo de hecho y perfil, y el reporte
  JSON de nivel 2 trae la tabla de tasas. Una comprobación con control negativo falla si falta la tabla
  `[N2]`.

---

## 5. Precisiones frente a lo aprobado

Son choques entre el cambio 02 y los requisitos aprobados. **No se edita** `requirements.md`. El autor
eligió la solución de cada uno el 2026-11-06 (columna «Decisión»); en la aprobación de Domain Design
decide si cada precisión se lleva al original, cada una en su propio commit.

| ID | Choque | Decisión (2026-11-06) |
|---|---|---|
| A-1 | VE-02 prohíbe «prueba» en la interfaz y el reporte, y el aviso de VE-01 dice «No son prueba». | **Excluir el aviso.** El escáner excluye solo la cadena versionada del aviso, leída del mismo archivo, igual que hoy excluye las dos citas y el texto del analista (AC5.5.1). Un control negativo comprueba que «prueba» fuera del aviso hace fallar el escaneo. Descartadas: cambiar el texto (viene literal del protocolo aprobado; «probatorio» también está prohibida) y admitir la palabra negada (abre huecos). Precisa FR6.4. |
| A-2 | VE-12 borra automáticamente sesiones y reportes. NFR11 exige que los historiales solo admitan inserciones, y FR7.5 conserva intacta la versión anterior del reporte. | **`Job` de retención.** Es la **única** vía de borrado: un `Job` con un usuario de base de datos propio, el único con `DELETE`, borra en orden de dependencias y deja el acta de VE-12 (solo inserción, sin texto). Se borran también las notas del analista en el historial de estados. Sobreviven solo el acta y el registro de acceso (VE-11), que solo tienen IDs. NFR11 se precisa como «solo inserción para el usuario de la aplicación», con una prueba de que ese usuario no puede borrar y el del `Job` sí. FR7.5 vale mientras dure la retención. Descartados: borrado criptográfico (gestión de claves sin KMS; el dato cifrado queda en disco) y lápida (también es un `UPDATE`). |
| A-3 | VE-13 marca cada exportación con el usuario, así que el archivo cambia. FR7.3 exige que el SHA-256 del archivo descargado coincida con el registrado. | **Hash por exportación.** Cada exportación es un artefacto propio con marca visible (usuario y hora en la cabecera y en cada página, junto al aviso de VE-01) y, en la cabecera, el SHA-256 de la versión consolidada. El SHA-256 del archivo exportado queda en el registro de acceso y se verifica con `sha256sum`. FR7.3 se precisa como «coincide con el registrado para esa exportación»; el SHA-256 de la versión consolidada se conserva. **Roles:** exportan el analista dueño y el administrador (no el investigador). Descartados: hash del contenido verificado quitando la marca (exige un script) y marca fuera del archivo (se pierde al descomprimir). Precisa FR7.3, FR7.4 y FR1. |
| A-4 | VE-06 exige consentimiento antes de capturar, pero la CLI (FR13) procesa el corpus del piloto sin sesión, y la importación (FR3) trae transcripciones ya hechas. | **Consentimiento en el contrato.** La entrada del contrato común lleva un bloque `consentimiento` (tipo: persona o autoridad que exime; versión del texto; autoriza transferencia a proveedor comercial; autoriza grabar la voz; `requiere_mandato`, verdadero si la persona es compareciente o tercero civil, y entonces `constancia_mandato` obligatoria, un identificador de la constancia y nunca un nombre, por VE-06; Contract Design, CD-10). La consola lo registra en la sesión guiada; la importación y la CLI lo leen del archivo. La biblioteca rechaza una transcripción sin el bloque antes de cualquier llamada, y un perfil con proveedor comercial si el bloque no autoriza la transferencia (VE-07). `origen: sintetico` queda exento, con una prueba que impide la exención con `origen: corpus`. El corpus del piloto lleva el bloque con la versión del consentimiento del TG, que se añade al empaquetarlo fuera de Git. Lo fija Contract Design (contrato común v1.0.0, lo aprueba el autor). Descartados: exentar la CLI sin control técnico y limitar VE-06 a la consola. Precisa FR3.6, FR13.2 y FR14.3. |

## 6. Ubicación propuesta por el cambio (para Units Generation)

| Requisitos | Unidad (§3.3 del cambio) |
|---|---|
| VE-04, VE-06, VE-10, VE-11, VE-12, VE-14 | Plataforma o identidad (U2/U3) y sesión |
| VE-01, VE-02, VE-13 | Reporte (U7) |
| VE-05 | Extras del asistente (U8) |
| VE-08 | Voz (U9) |
| VE-15, VE-16 | Consola |
| VE-17 | Evaluación (`evaluation/`) |

En el contrato común del analizador (Contract Design), la salida lleva un campo fijo `uso: "revision"` y el
aviso de VE-01 (§3.4 del cambio).

## 7. Trazabilidad

| ID | Relación con lo aprobado | Origen |
|---|---|---|
| VE-01 | Nuevo; amplía FR7.2 (contenido del reporte) | Cambio 02 §2.1; protocolo ético del TG, capítulo 11 |
| VE-02 | Amplía FR6.4 y la lista de C8 | Cambio 02 §2.1 |
| VE-03 | Corrige `specs/prd.md` (S1, S5-CU5, S6-P1, S13) | Cambio 02 §2.1; D10.4 |
| VE-04 | Nuevo; se suma a FR1 | Cambio 02 §2.1; D10.3; DT23 |
| VE-05 | Amplía FR10.3 | Cambio 02 §2.1; DT23 |
| VE-06 | Nuevo; condiciona FR3 y FR10.2 | Cambio 02 §2.2; protocolo ético del TG, capítulo 5 |
| VE-07 | Nuevo (texto del TG) | Cambio 02 §2.2; protocolo ético del TG, capítulo 5 |
| VE-08 | Amplía FR10.2 y NFR1 | Cambio 02 §2.2 |
| VE-09 | Amplía FR1 (roles) y FR10.4 | Cambio 02 §2.2 |
| VE-10 | Nuevo; se suma a FR3.5 | Cambio 02 §2.2 |
| VE-11 | Nuevo; se suma a NFR11 | Cambio 02 §2.3; protocolo ético del TG, capítulo 8 |
| VE-12 | Nuevo; precisa NFR11 y FR7.5 (A-2) | Cambio 02 §2.3; D10.2 |
| VE-13 | Amplía FR7.4; precisa FR7.3 (A-3) | Cambio 02 §2.3 |
| VE-14 | Amplía FR11.3 y FR15.3 | Cambio 02 §2.3 |
| VE-15 | Nuevo | Cambio 02 §2.4 |
| VE-16 | Nuevo | Cambio 02 §2.4 |
| VE-17 | Amplía NFR4 (informe de evaluación) | Cambio 02 §2.4 |
