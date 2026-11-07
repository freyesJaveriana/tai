# Adenda 02 de historias — protocolo ético (épica 15)

**Origen.** `inception/requirements-analysis/requirements-adenda-02.md` (VE-01 a VE-17, cambio 02
aprobado el 2026-11-05; protocolo ético del TG, parte B). Es un archivo **nuevo** que se suma a
`stories.md` (revisión 2, aprobada) **sin modificarlo** (§3.1 del cambio).

**Formato.** El de `stories.md`: «Como [persona], quiero [acción], para [beneficio]», criterios
Given/When/Then con ID `ACx.y.z`, nivel de prueba al final y textos visibles entre «» (catálogo de mensajes
en español). Personas: P1 Analista de Verdad · P2 Administrador de plataforma · P3 Oficial de Cumplimiento
Ético · P4 Investigador del TG.

**Las tres historias que nombra el cambio** son US15.1 (el analista reconoce las reglas), US15.2 (el
analista detiene la sesión) y US15.3 (el analista reporta un problema). Las demás cubren los requisitos que
no tienen una historia aprobada donde caber. Los requisitos que sí la tienen suman criterios a esa historia
en la sección «Criterios que se suman a historias aprobadas», con ID nuevos que no chocan con los
aprobados.

**Refined Mockups no se reabre.** El aviso fijo (US15.5), los botones de pausa y de terminar (US15.2) y el
formulario de reporte (US15.3) se especifican aquí, con su ubicación en las pantallas aprobadas de
`inception/refined-mockups/mockups.md`.

---

## Épica 15 — Protocolo ético (cambio 02)

### US15.1 — Reconocer las reglas de uso antes de trabajar · Demostración (DD-01) · P1
Como Analista de Verdad, quiero reconocer de forma explícita cómo se usan los hallazgos, para no tratarlos
como prueba ni confrontar a la persona.
*Origen:* VE-04 (D10.3), DT23.

- **AC15.1.1** Given un analista sin reconocimiento registrado, When entra a la consola, Then un diálogo
  modal muestra la versión vigente del texto con tres puntos: «Los hallazgos no son prueba», «Una
  contradicción puede venir del trauma» y «No se confronta a la persona con sus contradicciones». Ofrece
  «Reconozco estas reglas» y «Salir». Es una demostración (DD-01): el diálogo se muestra y el
  reconocimiento se registra, pero no impide abrir ni crear sesiones. `[N0]` Vitest
- **AC15.1.2** Given que pulso «Reconozco estas reglas», When se registra, Then queda una fila de solo
  inserción con usuario, hora UTC y versión del texto. `[N1]`
- **AC15.1.3** Given un reconocimiento de hace 90 días, When abro una sesión, Then se acepta. Given uno de
  hace 91 días (reloj simulado), Then la sesión también se abre y la consola vuelve a mostrar el diálogo
  de reconocimiento con un aviso de que venció; no hay `403` (DD-01). `[N1]`
- **AC15.1.4** Given un reconocimiento vigente de la versión 1 y un texto que pasa a la versión 2 por PR,
  When entro a la consola, Then se me pide reconocer de nuevo, aunque no hayan pasado 90 días. `[N1]`

### US15.2 — Pausar o terminar el análisis al instante · MUST · P1
Como Analista de Verdad, quiero detener el análisis cuando la persona lo necesite o retire su
consentimiento, para que nada de lo que diga después se analice.
*Origen:* VE-10. Ubicación: barra de la sesión de M2, junto a «Finalizar sesión». Sigue MUST (precisión
DD-06 de Domain Design): AC15.2.3 es el principio del analizador (A-4) y AC15.2.1, AC15.2.2 y AC15.2.4 son
los estados de la sesión, que también se mantienen.

- **AC15.2.1** Given una sesión abierta con corridas incrementales en cola, When pulso «Pausar análisis»,
  Then las corridas en cola se cancelan sin llamar a ningún modelo (el *fake* registra 0 llamadas nuevas),
  y los turnos que envío se guardan sin encolar análisis hasta que pulso «Reanudar análisis». `[N1]`
- **AC15.2.2** Given una sesión abierta, When pulso «Terminar sesión» y confirmo en el diálogo «El
  análisis se detendrá y no podrás agregar turnos», Then la sesión queda terminada, se cancelan las
  corridas en cola y un turno nuevo responde `409` sin crear filas. `[N1]`
- **AC15.2.3** Given que registro «La persona retiró su consentimiento» con la hora, When lanzo el modo
  final o llega un turno posterior, Then ningún turno posterior a la retirada entra en una corrida y los
  turnos nuevos responden `409` con `code` `session.consent_withdrawn`. `[N1]`
- **AC15.2.4** Given la sesión pausada o terminada, When la miro, Then el estado se lee como «Análisis en
  pausa» o «Sesión terminada», con texto y no solo con color. `[N0]` Vitest

### US15.3 — Reportar un problema sin copiar el testimonio · Demostración (DD-04) · P1
Como Analista de Verdad, quiero reportar un problema desde la consola, para que el equipo lo corrija sin
que el reporte exponga el testimonio.
*Origen:* VE-15. Ubicación: enlace «Reportar un problema» en la cabecera de la consola y en el menú de cada
tarjeta de hallazgo (que precarga el ID).

- **AC15.3.1** Given el formulario, When lo abro, Then ofrece exactamente las categorías «Hallazgo
  dañino», «Vocabulario indebido», «Cita que no corresponde», «Malestar de la persona entrevistada», «Falla
  de anonimización» y «Uso indebido», y una nota opcional. Es un panel no modal. `[N0]` Vitest
- **AC15.3.2** Given que envío un reporte, When se guarda, Then la fila tiene la categoría, los IDs de
  sesión y de hallazgo si los hay, quién, cuándo, la nota y la marca `testimony_warning`. `[N1]`
- **AC15.3.3** Given una nota que contiene un fragmento literal de un turno de la sesión (de 8 o más
  palabras seguidas), When la envío, Then la consola muestra el aviso «Quita el texto del testimonio de la
  nota»; si la envío igual, la fila se guarda con `testimony_warning` verdadero, sin `422` (DD-04). `[N1]`

### US15.4 — Registrar el consentimiento antes de capturar · MUST · P1
Como Analista de Verdad, quiero registrar el consentimiento de la persona entrevistada al crear la sesión,
para no analizar un relato sin su autorización.
*Origen:* VE-06, VE-07, A-4.

- **AC15.4.1** Given una sesión nueva, When la creo, Then debo elegir «Consentimiento de la persona» o
  «Constancia de la autoridad que lo exime» e indicar la versión del texto. Si la sesión usará voz, también
  marco «Autoriza grabar la voz». `[N0]` Vitest
- **AC15.4.2** Given una sesión sin el registro, When envío un turno, pego un bloque, importo una
  transcripción o grabo por voz, Then la API responde `409` con `code` `session.consent_missing` y no crea
  filas. Una transcripción importada trae el registro en su bloque `consentimiento`; sin él, la
  importación se rechaza completa. `[N1]`
- **AC15.4.7** Given una transcripción sin bloque `consentimiento` y con `origen: corpus` o `guiada`, When
  la analizo con la CLI o la biblioteca, Then termina con código ≠ 0 antes de cualquier llamada (el *fake*
  registra 0 llamadas). Con `origen: sintetico` se analiza sin el bloque, y un bloque que no autoriza la
  transferencia rechaza un perfil con proveedor comercial. `[N0]`
- **AC15.4.3** Given un consentimiento sin autorización de voz, When grabo un turno, Then la API responde
  `409` con `code` `session.voice_not_authorized`, aunque el texto sí se acepte. `[N1]`
- **AC15.4.4** Given una persona compareciente o tercero civil, When creo la sesión, Then debo registrar
  también la constancia del mandato y las garantías legales de la entidad; sin ella, la sesión no habilita
  la captura. `[N1]`
- **AC15.4.5** Given un consentimiento que no autoriza la transferencia a un proveedor comercial, When
  elijo el perfil, Then solo se ofrecen perfiles sin destino externo, y la API rechaza otro perfil con `422`.
  `[N1]`
- **AC15.4.6** Given el texto del consentimiento del TG, When se revisa frente a la lista de VE-07, Then la
  evidencia de la revisión queda adjunta al PR del Bolt. `[Manual]`

### US15.5 — Ver el aviso de propósito limitado · MUST · P3
Como Oficial de Cumplimiento Ético, quiero que la consola y el reporte digan siempre para qué sirven los
hallazgos, para que nadie los use para decidir sobre la persona.
*Origen:* VE-01, A-1. Ubicación: franja fija bajo la cabecera de todas las pantallas de la consola y pie de
cada página del reporte.

- **AC15.5.1** Given cualquier pantalla de la consola, When la abro, Then veo el aviso «Los hallazgos son
  sugerencias de revisión sobre la coherencia interna del relato. No son prueba, no indican falsedad y no
  deben usarse para decidir sobre la persona». `[N0]` Vitest, `[N3]`
- **AC15.5.2** Given un reporte consolidado, When lo genero, Then el aviso aparece en la cabecera y al
  final de cada sección de página. `[N1]`
- **AC15.5.3** Given un PR que cambia el texto del aviso, When corre la prueba, Then falla si el texto nuevo
  no contiene la frase base completa. `[N0]`

### US15.6 — Saber quién vio cada sesión · Demostración (DD-02) · P2
Como Administrador de plataforma, quiero un registro de quién abrió cada sesión, hallazgo o reporte, para
responder a una auditoría.
*Origen:* VE-11.

- **AC15.6.1** Given que un usuario abre una sesión, un hallazgo o un reporte, When consulto el registro de
  acceso, Then hay una fila con el usuario, el tipo de recurso, su ID y la hora UTC. No tiene texto. `[N1]`
- **AC15.6.2** Given el registro de acceso, When intento modificar o borrar una fila con el usuario de la
  aplicación, Then la operación falla. `[N1]`

### US15.7 — Que los datos se borren al vencer la retención · Demostración (DD-03) · P2
Como Administrador de plataforma, quiero borrar cada sesión vencida con un `Job` de retención que lanzo yo,
para no guardar testimonios más de lo debido. En el clúster el `Job` es un artefacto revisable que lanza el
humano (AUTONOMIA-01, DD-03); el sistema no lo programa.
*Origen:* VE-12 (D10.2), A-2.

- **AC15.7.1** Given el máximo de 90 días del catálogo de límites, When creo una sesión con 30 días, Then
  se acepta; Given 120 días, Then responde `422` con `code` `retention.above_maximum` y no crea filas. `[N1]`
- **AC15.7.2** Given una sesión con plazo vencido (reloj simulado), When corre el `Job` de retención, Then
  se borran la sesión, sus turnos, hallazgos, versiones de reporte (archivo y fila), reportes de problemas
  y audio conservado, en el orden inverso de las referencias (Domain Design, R-01 y R-02).
  Queda un acta con los IDs, el SHA-256 de cada reporte borrado, la hora y la regla aplicada. `[N1]`
- **AC15.7.3** Given un plazo ya fijado, When intento ampliarlo, Then responde `422`. Reducirlo se acepta
  y queda registrado quién y cuándo. `[N1]`

### US15.8 — Exportar el reporte con marca de agua · MUST · P1
Como Analista de Verdad, quiero que cada reporte exportado lleve el usuario que lo exportó, para que se
sepa quién lo sacó de la consola.
*Origen:* VE-13, A-3.

- **AC15.8.1** Given el investigador o un analista que no es el dueño de la sesión, When pide la
  descarga, Then responde `403` y no queda archivo exportado. El analista dueño y el administrador sí
  pueden exportar. `[N1]`
- **AC15.8.2** Given un rol autorizado, When descarga el reporte, Then el archivo lleva una marca visible
  con su usuario y la hora en la cabecera y en cada página, y en la cabecera el SHA-256 de la versión
  consolidada (FR7.3). La exportación queda en el registro de acceso con el SHA-256 del archivo exportado,
  que coincide con `sha256sum` del archivo descargado. `[N1]`

### US15.9 — Trabajar con avisos de bienestar · Demostración (DD-05) · P1
Como Analista de Verdad, quiero un aviso del contenido antes de abrir una sesión y recordatorios de pausa,
para cuidar mi carga emocional.
*Origen:* VE-16.

- **AC15.9.1** Given que abro una sesión, When carga, Then veo «Esta sesión contiene relatos de violencia.
  Puedes pausar cuando lo necesites» antes de la transcripción, con «Continuar». `[N0]` Vitest
- **AC15.9.2** Given el intervalo del catálogo de límites (reloj simulado), When se cumple con la sesión
  abierta, Then aparece un recordatorio no modal «Llevas un rato revisando. Considera una pausa», que se
  cierra sin perder el trabajo. `[N0]` Vitest

### US15.10 — Medir si el analizador marca más a unos relatos que a otros · MUST · P4
Como Investigador del TG, quiero la tasa de hallazgos por tipo de hecho y perfil en cada evaluación, para
detectar un sesgo contra relatos de violencia sexual o contra un perfil de persona.
*Origen:* VE-17.

- **AC15.10.1** Given el conjunto sintético, When se valida, Then cada transcripción tiene una etiqueta de
  tipo de hecho y otra de perfil, y una transcripción sin etiquetas hace fallar la validación. `[N0]`
- **AC15.10.2** Given una evaluación sobre el conjunto sintético, When termina, Then el reporte JSON trae la
  tabla de hallazgos por transcripción, agrupada por tipo de hecho y por perfil. Una comprobación con control
  negativo falla si falta la tabla. `[N2]`

---

## Criterios que se suman a historias aprobadas

| Criterio nuevo | Historia aprobada | Requisito |
|---|---|---|
| **AC5.5.5** Given la lista de vocabulario prohibido con «prueba», «probatorio», «pliego», «inculpa», «miente», «engaño» y «falso», When corre el escaneo sobre las plantillas de la interfaz y del reporte, Then hay 0 coincidencias, y un *fixture* con cada término lo hace fallar. `[N0]` | US5.5 | VE-02 |
| **AC5.5.6** Given el aviso versionado de VE-01, When corre el escaneo, Then «prueba» dentro del aviso no lo hace fallar y «prueba» en cualquier otra cadena sí. `[N0]` | US5.5 | VE-02, A-1 |
| **AC10.3.4** Given una aclaración que menciona la contradicción, dice «antes dijo» (o «antes mencionó», «había dicho») o contiene una cita de cualquier turno, When se valida, Then no se muestra y se registra como descartada por la regla de DT23. Hay un control negativo por cada caso. `[N0]` | US10.3 | VE-05 |
| **AC10.2.4** Given un turno grabado sin autorización de conservar el audio, When confirmo su transcripción, Then no queda audio en el volumen ni en la cola. Con la autorización, el audio se conserva hasta el vencimiento de la retención. `[N1]` | US10.2 | VE-08 |
| **AC10.4.2** Given un texto que no es una aclaración aprobada y validada por AC10.3.4, When se pide su audio, Then el TTS lo rechaza y no se sintetiza nada. `[N0]` | US10.4 | VE-09 |
| **AC5.4.4** Given cualquier rol distinto del dueño de la sesión, When pide sus hallazgos, Then responde `403`. No existe un rol ni una pantalla para la persona entrevistada. `[N0]` | US5.4 | VE-09 |
| **AC11.3.8** Given un registro de llamada a un proveedor comercial con `anonimizado: false` (inyectado en la prueba), When se detecta, Then la sesión pasa a bloqueada con `code` `anonymizer.incident`, se rechazan corridas nuevas y queda un incidente registrado. Cada corrida guarda si pasó por el anonimizador. `[N0]`, `[N1]` | US11.3 | VE-14 |

## Cobertura del cambio 02

| Requisito | Historias |
|---|---|
| VE-01 | US15.5 |
| VE-02 | AC5.5.5, AC5.5.6 |
| VE-03 | Hecho en el PRD (`fix(prd): …`); sin historia |
| VE-04 | US15.1 |
| VE-05 | AC10.3.4 |
| VE-06, VE-07 | US15.4 |
| VE-08 | AC10.2.4 |
| VE-09 | AC5.4.4, AC10.4.2 |
| VE-10 | US15.2 |
| VE-11 | US15.6 |
| VE-12 | US15.7 |
| VE-13 | US15.8 |
| VE-14 | AC11.3.8 |
| VE-15 | US15.3 |
| VE-16 | US15.9 |
| VE-17 | US15.10 |
