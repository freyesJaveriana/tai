# Preguntas de Functional Design — U11 incoherence-analyzer

**Unidad.** U11 `incoherence-analyzer` (tipo `library`, MUST, tamaño XL; Bolt B11). Es la biblioteca de
Python del analizador de incoherencias y su línea de comandos, sin Redis, Kubernetes ni base de datos
(DT26). Componentes: IncoherenceAnalyzer, AnalyzerCli, ModelGateway (puerto, adaptador local compatible
con OpenAI y cliente HTTP de C21), ExecutionProfiles y las reglas de IntegrityPolicy que usa el analizador
(escáner `scan(text, literal_sources)` y aviso). Incluye además el conjunto sintético de `evaluation/` y
los `.sbatch` y el paquete de entrada para ZINE. Historias, en el orden del mapa: US12.2, US13.3, US13.2,
US3.3, US3.4, US3.5, US3.2, US3.6, US3.7, US13.4, US13.5, US12.1, US12.5, US13.6, US12.3, US15.10, US12.4,
US13.7, US14.2 y US14.3. U11 participa además en US5.5 (escáner), US8.3, US10.5 (permutación), US13.3 y
US15.5 (aviso).

**Lo que ya está decidido y no se vuelve a preguntar.**
- *Contrato y salida:* la entrada y la salida del contrato común v1.0.0, con el bloque `registro`
  (llamadas, descartes sin texto, `fragmentado`, tokens y costo), los 8 motivos de descarte y los 6
  `error.codigo` (C6; FR4.1–FR4.3). `estado: error` implica `hallazgos` y `observaciones_conductor`
  vacíos (FR4.2, AUTONOMIA-05). Un candidato mal formado invalida toda la corrida con `salida_invalida`
  (AC3.2.1 d).
- *Citas:* se verifican con la regla del piloto: solo se normalizan espacios, « […] » une fragmentos del
  mismo turno en orden, y una cita en un turno `ENT` o `plegado` se acepta con aviso. La cita se restaura
  antes de verificarla (FR4.4; `project.md`; AC3.4.1–AC3.4.4). El módulo de verificación tiene 100 % de
  ramas.
- *Verificador y permutación:* el verificador hace una llamada aparte por candidato (exactamente *k*
  llamadas sin permutación, AC3.5.2). La permutación añade otra llamada con las citas invertidas, y el
  candidato solo se conserva si se confirma en los dos órdenes (FR4.5; iteracion2 P12 = A). El
  verificador local solo lee las citas (components, IncoherenceAnalyzer).
- *Modos:* en el modo incremental solo salen contradicciones con una cita `>= desde_turno`; las demás se
  descartan como `fuera_de_tramo` (AC3.6.1). El modo fragmentado por ventanas de turnos con solapamiento
  se usa con modelos locales: manda la ventana del perfil, el tope es C25, y la limitación queda
  declarada (FR4.8, C18, AC3.7.1–AC3.7.2). La ventana y el solapamiento los fija NFR Requirements.
- *Prompt:* el testimonio viaja como JSON dentro del mensaje `user`. Las instrucciones del sistema son
  un archivo de solo lectura con su `prompt_sha256` (FR4.6, AC3.3.1; `project.md`).
- *Modelos:* `generate(role, messages, schema)` (C13). Los adaptadores nativos son de U10 y se alcanzan
  solo por el `AnonymizingProvider` inyectado (CD-04). La tabla de reintentos y la de errores tipados
  (C13). El proveedor alterno solo entra tras `ContentBlocked`, con una sola llamada nueva en la ranura
  `fallback` (C13). Si un destino externo devuelve `anonymized: false`, la corrida se aborta en ese punto
  con `incidente_anonimizacion` (components; VE-14). Los marcadores alterados se descartan como
  `marca_alterada` (C20; FD-U10-08, FD-U10-16).
- *Perfiles:* esquema, configuración efectiva, forma canónica JCS y huellas `profile_sha256` y
  `config_sha256` (C18; AC13.2.1–AC13.2.2). Las reglas de validación con su control negativo (C18,
  FR14.3, FR14.4). La validación pura de U1 (`profiles.validate(kind: analyzer)`, FD-U1-10).
- *CLI:* modo final por defecto, un archivo de C6 por entrevista y los códigos de salida 0, 2, 3, 4 y 5
  (C19; FR13.2; AC12.1.1–AC12.1.3). El reporte C19 no tiene texto libre (P12 = A de Contract Design).
  Las corridas del corpus del piloto solo se escriben donde `git check-ignore` lo cubre (AC12.4.1). La
  raíz de composición `libs.incoherence_analyzer.cli.composition` es la única excepción del
  import-linter, con el *extra* `cli` (C13, R-18, R-19).
- *Evaluación:* acierto por par no ordenado de turnos; el acuerdo de tipo se reporta aparte; un
  hallazgo en un relato coherente o en un caso trampa es falso positivo; y la sensibilidad se mide según
  la distancia entre citas (NFR4; AC12.3.1–AC12.3.4). Los umbrales y la composición del conjunto los
  fija NFR Requirements. El conjunto lo genera un modelo comercial de una familia distinta a la del juez
  y a la del verificador, con datos solo sintéticos, revisado a mano y con la familia declarada en el
  manifiesto (B11, P12 = A de Delivery Planning; NFR5 B).
- *ZINE:* en Git van solo los `.sbatch`, el script de empaquetado y un manifiesto con nombres y SHA-256.
  El paquete se arma fuera de Git y lo lanza el humano (FR16.1; AC14.2.1–AC14.2.5; AUTONOMIA-01). Se
  registran el modelo, la cuantización (Q8 o BF16), el motor y la versión (FR16.2; AC14.3.1–AC14.3.2).
- *Pendiente de otras unidades:* el riesgo residual del escáner con una sola palabra citada sigue
  pendiente de la aprobación de U1 (FD-U1-14), y U11 aplicará lo que se decida allí. `Role` como texto
  con patrón (FD-U1-01 a FD-U1-04) también depende de esa aprobación. Si la sesión se bloquea o no ante
  `anonimizador_no_disponible` lo decide U4 (UG-02).

**Lo que el diseño resolverá sin preguntar** (irá como propuesta a la tabla de precisiones de
`functional-spec.md`, sin editar ningún artefacto aprobado):
1. **Aclaraciones neutras.** U11 no emite `observaciones_conductor`: el campo queda ausente. La
   validación de VE-05 y su emisión entran con U8 (US10.3), que toca la biblioteca sin cambiar su
   contrato.
2. **Contexto del juez.** En el modo completo, el juez recibe toda la transcripción hasta `hasta_turno`
   (o toda, en el modo final). En el modo fragmentado recibe cada ventana; en el incremental, solo las
   ventanas que contienen algún turno `>= desde_turno`. El juez responde con hallazgos sin `id` ni
   `pagina` ni `avisos`; esos campos los pone el núcleo de forma determinista. `pagina` viene del turno,
   así que no depende del modelo, y `avisos`, del `hablante` y el `estado` del turno.
3. **Ventanas.** Se arman en orden por número de turno, con paso `ventana − solapamiento`, y la última
   ventana termina en el último turno. Los candidatos repetidos entre ventanas que se solapan se unen por
   el par no ordenado de (turno, cita normalizada en espacios), la misma clave de FR4.9. Los `id`
   `<entrevista>-C<nn>` se numeran por el primer turno citado.
4. **Plazos y cancelación.** Antes de cada llamada se comprueban `cancelled()` y el plazo de la corrida
   (C18 `limits`). Si se agotó el plazo, la corrida termina con `tiempo_agotado` y sin hallazgos; si se
   canceló, con `Cancelled` (C17). Una salida inválida del verificador invalida la corrida igual que una
   del juez.
5. **Proveedor alterno por llamada.** Cada llamada empieza por la ranura `primary`. Que haya un bloqueo
   en una llamada no cambia la ranura de las siguientes. En la tabla de precisiones, el «o un error del
   proveedor» de US13.5 se lee según C13: el alterno solo entra tras un bloqueo de contenido.
6. **Prompts.** Un solo archivo versionado con las instrucciones del juez y del verificador, cuyo
   SHA-256 es `prompt_sha256`. La biblioteca lo lleva como dato del paquete. La copia del chart (U2/U4)
   se compara por SHA-256 en nivel 0.
7. **Respuesta del verificador.** Solo `{"confirma": boolean}`, sin texto libre. `reversed_order_consistency`
   es la fracción de candidatos con el mismo veredicto en los dos órdenes.
8. **Subcomandos.** `veridicus analyze` (lotes) y `veridicus evaluate` (evaluación). `evaluate` también
   puntúa salidas ya producidas, como las de ZINE, sin llamar a modelos (lo que necesita AC14.3.1). El
   empaquetado para ZINE es un script de `evaluation/zine/` que reutiliza la validación de la biblioteca.
   El directorio de resultados por omisión del corpus es una ruta que cubre `.gitignore`; el nombre lo
   propone el diseño.
9. **Frontera AUTONOMIA-04.** Una tabla por pieza: dónde corre (máquina local, ZINE o pod
   `semantic-agent`) y qué datos cruzan. U11 nunca abre una conexión externa por sí misma.

---

## P1 — En qué orden se filtran los candidatos del juez

La verificación determinista de las citas, el filtro del tramo incremental y la validación del esquema no
cuestan llamadas; el verificador sí cuesta una llamada por candidato (dos con la permutación), y con un
perfil comercial cada una sale seudonimizada del clúster. El texto de components pone el verificador
antes de la verificación determinista, y AC3.5.2 cuenta *k* llamadas para *k* candidatos.

A. Primero lo determinista (esquema, citas contra su turno, tramo incremental, marcas alteradas) y
   después el verificador, solo sobre los candidatos que lo pasaron. Así no se paga ni se envía una
   llamada por una cita inventada. En la tabla de precisiones, AC3.5.2 se lee como «*k* candidatos que
   pasaron la verificación determinista», y components cambia el orden. (Recomendada)
B. El orden de components: el verificador sobre todos los candidatos y después la verificación
   determinista. AC3.5.2 queda literal, a costa de más llamadas y de más texto enviado.
C. Las dos cosas en paralelo sobre todos los candidatos, y solo sale lo que pasa ambas.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P2 — Qué ve el verificador

components ya dice que el verificador local «solo lee las citas». Falta fijar si eso vale para todos los
perfiles y qué más recibe. Si el verificador ve la justificación del juez, su confirmación es menos
independiente (NFR5, Escenario B). Si ve más texto, sale más testimonio con un perfil comercial.

A. Igual en todos los perfiles: `hecho`, `tipo` y las dos citas con su turno, sin las `observaciones`
   del juez ni el resto de la transcripción. Es lo mínimo que decide y es comparable entre perfiles.
   (Recomendada)
B. Lo de A más el texto completo de los dos turnos citados.
C. Lo de A más las `observaciones` del juez.
D. Lo de A con la ventana o la transcripción que vio el juez.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P3 — Vocabulario prohibido en `hecho` u `observaciones`

AC3.2.4 dice que un candidato con vocabulario prohibido fuera de las citas se trata como
`salida_invalida`, y eso pone toda la corrida en `error`. C6 (revisión 3) tiene además el motivo de
descarte `vocabulario_prohibido`, que solo tiene sentido si se descarta ese candidato y la corrida sigue.
En los dos casos el analista nunca ve la etiqueta (AUTONOMIA-03). La diferencia es si pierde los demás
hallazgos verificados del tramo.

A. Se descarta solo ese candidato con motivo `vocabulario_prohibido`, que queda en `registro.descartes`
   y en el conteo del reporte C19, y la corrida sigue. AC3.2.4 se precisa en la tabla. Es el mismo trato
   que una cita no verificada. (Recomendada)
B. AC3.2.4 literal: toda la corrida termina en `salida_invalida`, y `vocabulario_prohibido` queda sin
   uso hasta U8 (temas de aclaración).
C. A en `observaciones` y B en `hecho`, porque `hecho` es el titular que el analista ve primero.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P4 — Si la permutación entra en B11

La nivel 2 de `team.md` exige la permutación en el 100 % de las consultas *offline* y una consistencia
mayor que 65 % al invertir el orden. C6 y C18 ya traen `verificador_permutado`, `rechazado_permutacion`
y la opción `permutation`. En cambio, US10.5 es SHOULD y su dueña es U8, y la definición de terminado de
B11 no nombra la permutación. Si no entra en B11, la evaluación de la primera rebanada no puede medir dos
umbrales de `team.md`.

A. U11 implementa la permutación en B11, detrás de `permutation`, y los perfiles de evaluación la llevan
   activa. U8 conserva US10.5 para el producto: activarla en el perfil de producción y contar su costo
   frente a NFR3 y NFR8. (Recomendada)
B. La permutación queda para U8. En B11 el reporte marca esas dos métricas como no aplicables, y la nivel
   2 completa de `team.md` se exige desde B8.
C. U11 la implementa, pero los perfiles de evaluación la dejan apagada hasta B8.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P5 — Proveedor alterno y familias distintas

C18 tiene un solo `fallback_provider` por perfil, que sirve para el juez y para el verificador. Si el
verificador cae al alterno y este es de la misma familia que el juez, la confirmación deja de ser
independiente, y FR14.4 exige familias distintas en los perfiles de evaluación.

A. ExecutionProfiles rechaza un perfil de evaluación cuyo alterno sea de la misma familia que el juez o
   que el verificador (tercera familia). En un perfil de demostración se admite solo con
   `same_family_declared` y el aviso de AC13.1.2. Se rechaza antes de cualquier llamada. (Recomendada)
B. El alterno solo vale para el juez. Un bloqueo en el verificador termina la corrida en
   `bloqueo_contenido`.
C. Se comprueba al llamar: si la familia del alterno coincide con la del otro papel, no se llama y la
   corrida termina en `bloqueo_contenido`.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P6 — Las 3 corridas de la evaluación y qué cifra se compara con el umbral

NFR4 pide acuerdo entre 3 corridas del mismo perfil, y AC12.3.4 marca `pasa: false` en una métrica bajo
su umbral. Falta fijar si `evaluate` hace las 3 corridas y qué valor de cada métrica cuenta. Los umbrales
nunca se bajan (`team.md`), pero los modelos comerciales no son deterministas (`project.md`).

A. `evaluate` corre el conjunto 3 veces. Las métricas absolutas (100 % de citas verificadas, 0 % de
   error de formato JSON, permutación en el 100 %, 0 fugas del anonimizador) deben cumplirse en las 3.
   Las estadísticas (precisión, sensibilidad, consistencia al invertir el orden) se comparan por su
   media, y el reporte trae además el valor de cada corrida. (Recomendada)
B. Las 3 corridas, y cada métrica se compara por su peor valor de las 3.
C. Las 3 corridas, pero las métricas se toman de la primera; las otras dos solo sirven para el acuerdo.
D. `evaluate` corre una vez, y el acuerdo se calcula aparte sobre 3 reportes ya escritos.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P7 — Etiquetas de sesgo (VE-17) frente a la tabla de C19

VE-17 y US15.10 piden la tasa de hallazgos por **tipo de hecho** (el hecho del relato, por ejemplo
violencia sexual) y por **perfil de la persona**. La `bias_table` de C19, que es estricta, usa como
`fact_type` los 7 valores de `hallazgo.tipo` (fecha, número…), que son el tipo de la contradicción, y una
etiqueta libre `synthetic_set`. Con la tabla tal como está no se puede agrupar por tipo de hecho del
relato.

A. El manifiesto del conjunto etiqueta cada transcripción con `tipo_hecho` y `perfil_persona`, tomados de
   dos listas cerradas y versionadas en `evaluation/`, y una transcripción sin etiquetas hace fallar la
   validación (AC15.10.1). Sin cambiar C19, `synthetic_set` lleva la combinación
   `<tipo_hecho>__<perfil_persona>` y `fact_type` sigue siendo el tipo de la contradicción; queda como
   precisión de C19. Las dos listas iniciales las propone el diseño y las aprueba el autor. (Recomendada)
B. Cambio mayor de C19 en un PR de U1: `bias_table` gana `event_type` y `person_profile` con patrón, y
   `fact_type` sale o se queda como tipo de contradicción.
C. Solo `tipo_hecho` en `synthetic_set`; el perfil de la persona queda fuera del MVP.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P8 — Cómo lleva la CLI el aviso de VE-01

El mapa de historias dice que «el reporte y la salida de la CLI llevan el mismo aviso» (US15.5). Pero la
salida C6 y el reporte C19 son estrictos y no tienen campo para el aviso: C19 no admite texto, y en C6
no se pudo añadir el campo `uso` que menciona la adenda 02.

A. La CLI escribe el aviso de `contracts/integrity/notice.v1.yaml`, con su versión, en la terminal (stderr)
   en cada ejecución, y deja un archivo `AVISO.txt` con el mismo texto y su versión en cada directorio de
   salida. No cambia ningún contrato, y una prueba de nivel 0 lo comprueba. (Recomendada)
B. Lo de A más un campo `notice_version` con patrón en C19 (cambio mayor de un contrato estricto, en un
   PR de U1).
C. Solo en la terminal, sin archivo.
X. Other (please specify)

[Answer]: A **Mode:** guided
