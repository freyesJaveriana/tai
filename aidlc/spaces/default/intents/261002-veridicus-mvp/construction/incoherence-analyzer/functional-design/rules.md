# Reglas de negocio — U11 incoherence-analyzer

**Revisión 1 (2026-11-21).** Primera pasada de una unidad nueva del cambio 01 (DT27) y de la adenda 02.
Todas las reglas son nuevas. Origen: las respuestas P1–P8 = A de `functional-design-questions.md`, lo que
esa página da por decidido y los puntos 1–9 que deja a este diseño (que van como propuestas a la tabla de
precisiones de `functional-spec.md` §11).

**Insumos.** Los mismos de `entities.md`: unit-of-work y unit-of-work-story-map (U11 y las historias que
la cruzan), requirements (FR4, FR10.5, FR13–FR16, NFR1, NFR4, NFR5, NFR10, NFR12, NFR13; VE-01, VE-02,
VE-14, VE-17 y A-4 de la adenda 02), components (IncoherenceAnalyzer, AnalyzerCli, ModelGateway,
ExecutionProfiles, IntegrityPolicy; ADR-005, ADR-010, ADR-012, ADR-013), contract-summary (C6, C8, C13,
C14, C17–C21, C25; CD-01, CD-02, CD-04, CD-09) y los puntos de integración de U1 y U10. Las reglas de otras
unidades se citan por descripción, nunca por su ID.

**Cómo se prueban.** Salvo que la regla diga otra cosa, en **nivel 0**, sin red, con *fakes*
deterministas del `ModelGateway` y datos sintéticos, cada una con su control negativo. Son **módulos
guardia con 100 % de ramas** (team.md, NFR13; AUTONOMIA-05): la verificación de citas (BR5), el filtro de
candidatos y la máquina de estados de la corrida (BR5, BR6, BR7.1–BR7.3) y el armado de la salida en error
(BR8.1). Viven en `domain/` como código puro. Las pruebas de estas guardias y de los contratos de datos se
escriben primero y se ejecutan en rojo (team.md, Ordering). Toda prueba se cita en el plan de tareas por
el ID de su regla y, cuando aplica, por su AUTONOMIA.

```yaml
rules:
  # BR1 — Entrada y consentimiento (antes de cualquier llamada)
  - id: BR1.1
    status: nuevo
    statement: La entrada se valida contra la copia de C6 y contra el catálogo de límites antes de cualquier llamada; si no cumple, la corrida se rechaza sin llamar.
    category: validation
    applies_to: [AnalysisRun]
    trigger: analyze recibe una entrada (C17)
    logic: SI la entrada no valida contra entrada.schema.json con el registro de U1, o algún turno supera turn_max_chars, o la transcripción supera transcript_max_turns o transcript_max_chars (C25, leídos con la carga de límites de U1) ENTONCES lanza InputRejected con code import.invalid_transcript y no devuelve Salida. En la CLI eso es el código de salida 2.
    violation: Una prueba por campo obligatorio ausente, por enum fuera de valores y por cada límite superado; el fake registra 0 llamadas (AC12.1.3 b).
    source: FR4.1; FR13.2; C6; C17 (errores antes de llamar); C25
  - id: BR1.2
    status: nuevo
    statement: Una transcripción con origen corpus o guiada sin bloque consentimiento se rechaza antes de cualquier llamada; con origen sintetico se analiza sin él.
    category: validation
    applies_to: [AnalysisRun, BatchItem]
    trigger: Validación previa de analyze
    logic: SI transcripcion.origen es corpus o guiada y no trae consentimiento ENTONCES InputRejected con session.consent_missing (CLI, código 2). SI el origen es sintetico ENTONCES no se exige el bloque. La exención nunca se extiende a corpus aunque el archivo esté en evaluation/.
    violation: Prueba con corpus y guiada sin el bloque (0 llamadas) y con sintetico sin él (se analiza); control negativo que intenta la exención con corpus.
    source: AC15.4.7; A-4; FR13.2; C6 (cambios 1 y 3); C17
  - id: BR1.3
    status: nuevo
    statement: Un perfil con algún destino externo se rechaza antes de cualquier llamada si el consentimiento no autoriza la transferencia.
    category: authorization
    applies_to: [AnalysisRun, ExecutionProfile]
    trigger: Validación previa de analyze
    logic: SI el perfil tiene has_external_destination (juez, verificador o alterno con scope external) y la transcripción trae consentimiento con autoriza_transferencia false ENTONCES InputRejected con profile.transfer_not_authorized (CLI, código 3). Una transcripción sintetica sin bloque no restringe el perfil.
    violation: Prueba con un bloque que no autoriza y un perfil comercial (0 llamadas) y con el mismo bloque y todo-local (se analiza).
    source: AC15.4.7; FR14.3; VE-07; A-4; C17
  - id: BR1.4
    status: nuevo
    statement: El perfil que nombra la entrada debe ser el de la configuración efectiva y existir en el archivo aprobado.
    category: validation
    applies_to: [AnalysisRun, EffectiveConfig]
    trigger: Validación previa de analyze
    logic: SI entrada.perfil no coincide con config.profile_name, o el nombre no está en config/profiles.yaml ENTONCES InputRejected con profile.not_approved (CLI, código 3).
    violation: Prueba con un perfil inexistente (AC12.1.3 c) y con un nombre distinto al de la configuración.
    source: FR14.1; C17; AC12.1.3
  - id: BR1.5
    status: nuevo
    statement: En el modo incremental, desde_turno y hasta_turno son números de turnos existentes y desde_turno no supera a hasta_turno.
    category: validation
    applies_to: [AnalysisRun]
    trigger: Validación previa de analyze con modo incremental
    logic: SI modo es incremental y (desde_turno > hasta_turno, o alguno no es el número n de un turno de la entrada) ENTONCES InputRejected con import.invalid_transcript. Los turnos con n mayor que hasta_turno no se envían al juez.
    violation: Prueba con desde_turno > hasta_turno, con un número inexistente y con turnos posteriores a hasta_turno, que no aparecen en ninguna llamada.
    source: FR4.1; FR4.9; C6 (hasta_turno, desde_turno); precisión FD-U11-15

  # BR2 — Perfiles (ExecutionProfiles)
  - id: BR2.1
    status: nuevo
    statement: El archivo de perfiles se valida con la función pura de U1 (kind analyzer, prefijo VERIDICUS_) y con las reglas de este grupo; si algo falla, ningún proceso arranca y la CLI termina con 3 antes de cualquier llamada.
    category: validation
    applies_to: [ExecutionProfile]
    trigger: Arranque de la CLI y de cualquier consumidor de la biblioteca
    logic: SI la validación de U1 lanza ProfileValidationError o falla una regla de BR2 ENTONCES config.invalid_profile; el log nombra el ajuste y el papel, nunca un valor. La validación no lee red.
    violation: Un fixture inválido por cada regla de BR2 y su positivo corregido que arranca; un valor canary nunca aparece en el log (AC13.3.1 a).
    source: FR14.3; AC13.3.1; AC13.3.2; C18; FD-U1-10
  - id: BR2.2
    status: nuevo
    statement: En la CLI, toda api_key_ref de un destino externo debe tener valor en el entorno de la máquina; semantic-agent no resuelve claves.
    category: validation
    applies_to: [ExecutionProfile, GatewayAssembly]
    trigger: Arranque de la CLI con un perfil que tiene destino externo
    logic: SI la CLI va a usar un perfil con destino externo y la variable que nombra api_key_ref no existe o está vacía ENTONCES código 3 antes de cualquier llamada; el mensaje nombra la variable, nunca un valor. En semantic-agent esta regla no aplica (las claves viven solo en anonymizer-proxy, CD-04).
    violation: Prueba con la variable ausente (0 llamadas, código 3) y con un canary como valor que no aparece en ningún log ni archivo (AC13.3.1 c en la CLI).
    source: FR14.3; FR12.4; AC13.3.1; CD-04
  - id: BR2.3
    status: nuevo
    statement: Un destino local solo admite una base_url interna de la máquina o del clúster.
    category: constraint
    applies_to: [ExecutionProfile, GatewayAssembly]
    trigger: Validación del perfil
    logic: SI scope es local y base_url no es loopback, un nombre de servicio del clúster sin punto final de dominio público o una dirección de red privada (RFC 1918 o fc00::/7) ENTONCES el perfil es inválido. SI scope es external y trae base_url ENTONCES también es inválido.
    violation: Prueba con una URL pública en un destino local y con base_url en un destino externo.
    source: FR14.3; C18 (destino local con base_url externa); NFR1
  - id: BR2.4
    status: nuevo
    statement: En un perfil de evaluación el juez y el verificador son de familias distintas, y las tres familias (juez, verificador y alterno) se declaran.
    category: validation
    applies_to: [ExecutionProfile]
    trigger: Validación de un perfil con purpose evaluation
    logic: SI purpose es evaluation y falta family en el juez, el verificador o el alterno ENTONCES inválido. SI judge.family = verifier.family ENTONCES inválido, con un mensaje que nombra la familia.
    violation: Prueba con la misma familia (el mensaje la nombra) y con una familia ausente (AC13.4.1).
    source: FR14.4; AC13.4.1; NFR5 (Escenario B); precisión FD-U11-22
  - id: BR2.5
    status: nuevo
    statement: Solo un perfil de demostración puede usar la misma familia en dos papeles, y solo si lo declara; entonces el perfil lleva el aviso de misma familia.
    category: validation
    applies_to: [ExecutionProfile, ProfileWarning]
    trigger: Validación del perfil
    logic: SI same_family_declared es verdadero y purpose no es demonstration ENTONCES inválido. SI purpose es demonstration, dos papeles (o un papel y el alterno) comparten familia y same_family_declared es falso ENTONCES inválido; si es verdadero, el perfil es válido y su lista de avisos incluye same_family.
    violation: Prueba sin la declaración (rechazo) y con ella (aceptado, con el aviso) (AC13.4.2); prueba de same_family_declared en un perfil de evaluación.
    source: FR14.4; AC13.4.2; AC13.1.2; C18; project.md (juez y verificador de familias distintas)
  - id: BR2.6
    status: nuevo
    statement: En un perfil de evaluación, el alterno es de una tercera familia, distinta de la del juez y de la del verificador.
    category: validation
    applies_to: [ExecutionProfile]
    trigger: Validación de un perfil de evaluación con fallback_provider
    logic: SI purpose es evaluation y fallback_provider.family es igual a judge.family o a verifier.family ENTONCES inválido antes de cualquier llamada. En demostración, se admite solo con same_family_declared (BR2.5).
    violation: Prueba con el alterno de la familia del juez, con el de la del verificador y con una tercera familia (válido).
    source: Respuesta P5 = A; FR14.4; FR15.2; precisión FD-U11-05
  - id: BR2.7
    status: nuevo
    statement: Un perfil con algún papel local declara el modo fragmentado, con una ventana que no pasa del tope de C25 y un solapamiento menor que la ventana.
    category: validation
    applies_to: [ExecutionProfile, ProfileWarning]
    trigger: Validación del perfil
    logic: SI el juez o el verificador tienen scope local y chunking falta o chunking.enabled es falso ENTONCES inválido. SI window pasa de fragment_window_turns o overlap pasa de fragment_overlap_turns, o overlap >= window ENTONCES inválido. SIN window se usa el tope. Un perfil con chunking activo lleva el aviso fragmented con su ventana y su solapamiento.
    violation: Prueba con un perfil local sin chunking, con una ventana sobre el tope y con overlap igual a la ventana (AC13.2.2).
    source: FR4.8; C18 (ventana del modo fragmentado); AC13.2.2; AC3.7.1
  - id: BR2.8
    status: nuevo
    statement: El archivo de perfiles trae al menos un perfil comercial y el perfil todo-local.
    category: constraint
    applies_to: [ExecutionProfile]
    trigger: Validación del archivo de perfiles versionado (nivel 0)
    logic: SI no hay ningún perfil con destino externo, o falta todo-local, o todo-local tiene algún destino externo ENTONCES la comprobación falla.
    violation: Fixture sin todo-local y fixture sin perfil comercial.
    source: FR14.1; AC13.2.2; C18
  - id: BR2.9
    status: nuevo
    statement: Todo perfil de evaluación tiene la permutación activa.
    category: validation
    applies_to: [ExecutionProfile]
    trigger: Validación de un perfil con purpose evaluation
    logic: SI purpose es evaluation y permutation es falso ENTONCES inválido.
    violation: Prueba con un perfil de evaluación sin permutación.
    source: Respuesta P4 = A; NFR4 (permutación en el 100 % de las consultas offline); FR10.5; precisión FD-U11-06
  - id: BR2.10
    status: nuevo
    statement: La configuración efectiva y sus dos huellas se calculan con la forma canónica JCS, y ningún valor de clave entra en ellas.
    category: calculation
    applies_to: [EffectiveConfig]
    trigger: ProfileResolver.resolve en la CLI; en el producto, InterviewSession la recibe ya armada
    logic: profile es la entrada del perfil tal como está en el archivo, sin resolver claves; profile_sha256 = SHA-256 de su forma JCS; limits son las cifras de C25 ya bajadas por el entorno; config_sha256 = SHA-256 de la forma JCS de todo el objeto. Se usa la misma función pura que publica U1 si se aprueba FD-U10-12.
    violation: Prueba de propiedad con Hypothesis (orden de claves y formato YAML no cambian la huella; cambiar un parámetro la cambia; el valor de una clave nunca entra) y prueba contra el fixture con huella esperada de C18 (AC13.2.1).
    source: FR14.2; AC13.2.1; C18 (forma canónica); C6 regla 4
  - id: BR2.11
    status: nuevo
    statement: Los perfiles, la tabla de precios, el prompt y los umbrales de evaluación solo se leen de archivos versionados; ninguna ruta de la biblioteca o de la CLI los escribe.
    category: policy
    applies_to: [ExecutionProfile, PriceTable, PromptBundle, EvaluationThresholds]
    trigger: Cualquier lectura de configuración
    logic: La biblioteca abre esos archivos solo para lectura y la CLI no tiene subcomando ni opción que los modifique; un cambio entra por PR (FR9.2).
    violation: Comprobación estática de nivel 0 de que ningún módulo fuera del cargador de configuración abre esos archivos en modo escritura, con control negativo (AC8.3.2, lado de la biblioteca).
    source: FR9.2; US8.3 (U11 lee los archivos versionados); ADR-012

  # BR3 — Prompt y mensajes
  - id: BR3.1
    status: nuevo
    statement: El testimonio viaja solo como JSON dentro del mensaje user, y las instrucciones del sistema salen del archivo del prompt cuyo SHA-256 se registra como prompt_sha256.
    category: policy
    applies_to: [PromptBundle, AnalysisRun]
    trigger: Construcción de cada mensaje al juez o al verificador
    logic: El mensaje system es la sección correspondiente de PromptBundle, sin interpolar nada de la entrada. El mensaje user es un documento JSON con los turnos (n, hablante, estado y texto) o con el candidato. prompt_sha256 de la salida = SHA-256 de los bytes del archivo leído, que debe coincidir con config.prompt_sha256; si no coincide, la corrida termina en error salida_invalida antes de llamar.
    violation: Prueba que inspecciona los mensajes capturados por el fake (el testimonio no aparece en system; user es JSON válido) y prueba con un archivo cambiado que no coincide con la configuración (AC3.3.1).
    source: FR4.6; AC3.3.1; NFR5 Escenario A; project.md (bloque de datos como JSON en el mensaje user)
  - id: BR3.2
    status: nuevo
    statement: El juez recibe una ventana por llamada; sin modo fragmentado, una sola ventana con todos los turnos hasta hasta_turno, o todos en el modo final.
    category: policy
    applies_to: [TranscriptWindow, AnalysisRun]
    trigger: Fase judging
    logic: SI chunking no está activo ENTONCES una llamada al juez con todos los turnos enviables. SI está activo ENTONCES una llamada por ventana (BR4.1); en incremental, solo por las ventanas relevantes (BR4.2). Los turnos ENT y plegados van como contexto con su hablante y su estado.
    violation: Prueba que cuenta las llamadas al juez y los turnos de cada una en los modos completo, fragmentado e incremental.
    source: FR4.1; FR4.8; punto 2 de las preguntas (precisión FD-U11-25)
  - id: BR3.3
    status: nuevo
    statement: El verificador recibe solo hecho, tipo y las dos citas con su turno, igual en todos los perfiles.
    category: policy
    applies_to: [JudgeCandidate]
    trigger: Fase verifying
    logic: El mensaje user del verificador es un JSON con hecho, tipo, cita_a {cita, turno} y cita_b {cita, turno}; nunca las observaciones del juez, el resto de la transcripción ni otro candidato. En la llamada permutada, cita_a lleva la cita_b original y cita_b la cita_a.
    violation: Prueba que captura el cuerpo de cada llamada del verificador (directa y permutada) y comprueba que solo trae esos cuatro campos.
    source: Respuesta P2 = A; FR4.5; NFR5 Escenario B; components (el verificador local solo lee las citas)
  - id: BR3.4
    status: nuevo
    statement: La respuesta del juez y la del verificador se fuerzan a un esquema JSON cerrado sin texto libre más allá de los campos del hallazgo.
    category: validation
    applies_to: [PromptBundle, JudgeCandidate]
    trigger: Cada llamada generate (campo schema de GenerateRequest)
    logic: El juez responde { hallazgos: [ { hecho, tipo, cita_a {cita, turno}, cita_b {cita, turno}, observaciones } ] } con additionalProperties false, strings con minLength 1 y tipo en los 7 valores; sin id, pagina, avisos ni actos. El verificador responde solo { confirma: boolean }. Una respuesta que no valida es InvalidOutput, venga del adaptador o del núcleo.
    violation: Prueba con un campo extra (p. ej. is_truthful, AC5.5.3), con id en la respuesta del juez y con texto libre en la del verificador (los tres InvalidOutput).
    source: FR4.3; FR15.1; C13 (salida JSON forzada); puntos 2 y 7 (precisiones FD-U11-12 y FD-U11-27)

  # BR4 — Ventanas y deduplicación
  - id: BR4.1
    status: nuevo
    statement: Las ventanas se arman por posición en la lista ordenada de turnos, con paso ventana menos solapamiento, y la última termina en el último turno enviable.
    category: calculation
    applies_to: [TranscriptWindow]
    trigger: Inicio de judging con chunking activo
    logic: Con N turnos enviables ordenados por n, ventana W y solapamiento O, la ventana k empieza en la posición k·(W−O) y termina en min(inicio + W, N) − 1. SI la última quedaría con menos de W turnos y N > W ENTONCES se desplaza para empezar en N − W. SI N <= W ENTONCES una sola ventana, y registro.fragmentado sigue activo con W y O. La separación entre turnos se mide por posición, no por diferencia de números n.
    violation: Prueba de propiedad: ninguna llamada al juez contiene dos turnos separados por más de W posiciones y todo turno está en al menos una ventana (AC3.7.2); prueba con N <= W y con números n no consecutivos.
    source: FR4.8; AC3.7.2; C18; punto 3 (precisión FD-U11-26)
  - id: BR4.2
    status: nuevo
    statement: En el modo incremental con ventanas, solo se envían las ventanas que contienen algún turno igual o posterior a desde_turno.
    category: policy
    applies_to: [TranscriptWindow]
    trigger: Inicio de judging en modo incremental con chunking activo
    logic: SI ninguna posición de la ventana tiene n >= desde_turno ENTONCES relevant es falso y la ventana no se envía.
    violation: Prueba con un fake que registra las llamadas: ninguna ventana enviada está completa antes de desde_turno.
    source: FR4.1; FR4.8; punto 2
  - id: BR4.3
    status: nuevo
    statement: Los candidatos repetidos entre ventanas se unen por el par no ordenado de (turno, cita normalizada en espacios) antes de llamar al verificador.
    category: calculation
    applies_to: [JudgeCandidate]
    trigger: Fin del filtro determinista
    logic: La clave de un candidato es el conjunto {(turno_a, normalized_a), (turno_b, normalized_b)}. SI dos candidatos que pasaron el filtro tienen la misma clave ENTONCES se conserva el de la ventana de menor índice (y, en la misma ventana, el de menor ordinal), y los demás se unen a él sin DiscardRecord ni llamada al verificador.
    violation: Prueba con el mismo par repetido en dos ventanas solapadas y con las citas en orden inverso: un solo verificador y un solo hallazgo.
    source: FR4.9 (misma clave); punto 3; precisión FD-U11-24

  # BR5 — Filtro determinista de candidatos (módulo guardia, 100 % de ramas; AUTONOMIA-05)
  - id: BR5.1
    status: nuevo
    statement: Una respuesta del juez que no valida contra su esquema invalida toda la corrida con salida_invalida; nunca se rescatan sus candidatos válidos.
    category: validation
    applies_to: [AnalysisRun, JudgeCandidate]
    trigger: Cada respuesta del juez, en cualquier ventana
    logic: SI la respuesta no es JSON, le falta un campo obligatorio, trae null, una cadena vacía, un tipo fuera de los 7 valores o un campo extra, aunque sea en uno solo de varios candidatos ENTONCES InvalidOutput y la corrida termina en error salida_invalida con hallazgos vacíos (BR7.1).
    violation: Una prueba por caso de AC3.2.1 (a)–(d), con tres candidatos y uno mal formado; una prueba por campo y caso de AC3.4.1 (ausente, null, vacío, tipo fuera del enum).
    source: FR4.2; FR4.3; AC3.2.1; AC3.4.1; AUTONOMIA-05
  - id: BR5.2
    status: nuevo
    statement: Los candidatos se filtran sin llamadas en un orden fijo, y cada uno se descarta con el motivo del primer filtro que falla.
    category: policy
    applies_to: [JudgeCandidate, DiscardRecord]
    trigger: Fase filtering, después de todas las respuestas del juez
    logic: "Orden: (1) marca alterada (BR5.3); (2) campo solo con espacios (BR5.4); (3) verificación de cita_a y de cita_b (BR5.5, BR5.6); (4) tramo incremental (BR5.8); (5) vocabulario prohibido (BR9.3); (6) deduplicación (BR4.3). Solo lo que pasa los seis llega al verificador (P1 = A). Cada descarte deja un DiscardRecord con turno_a y turno_b tal como los nombró el juez."
    violation: Prueba con un candidato que falla dos filtros (queda el motivo del primero) y prueba de que un candidato descartado nunca produce una llamada.
    source: Respuesta P1 = A; FR4.5; AC3.5.2; precisión FD-U11-01
  - id: BR5.3
    status: nuevo
    statement: Un candidato con alguna parte cuya marca alteró el modelo se descarta con marca_alterada.
    category: validation
    applies_to: [JudgeCandidate]
    trigger: Filtro (1)
    logic: SI algún puntero de GenerateResult.altered_markers empieza por el json_pointer del candidato (por ejemplo /hallazgos/2/cita_b/cita) ENTONCES descarte marca_alterada. Un puntero que no cae en ningún candidato invalida toda la respuesta como salida_invalida.
    violation: Prueba con una marca alterada en cita_b y otra en observaciones (descarte) y con un puntero fuera de los candidatos (salida_invalida).
    source: AC11.3.4 (b) y (c); C20 paso 4; FD-U10-08; FR11.3
  - id: BR5.4
    status: nuevo
    statement: Un candidato cuyo hecho, observaciones o texto de cita solo tiene espacios se descarta con campo_faltante.
    category: validation
    applies_to: [JudgeCandidate]
    trigger: Filtro (2)
    logic: SI tras normalizar los espacios hecho, observaciones, cita_a.cita o cita_b.cita quedan vacíos ENTONCES descarte campo_faltante. Ausente, null o cadena vacía ya invalidaron la corrida (BR5.1).
    violation: Una prueba por campo con solo espacios, tabuladores o saltos de línea.
    source: FR4.3; AC3.4.1 (solo espacios); C6 (motivo campo_faltante); precisión FD-U11-11
  - id: BR5.5
    status: nuevo
    statement: Cada cita se verifica contra el texto original de su turno con la regla del piloto, normalizando solo los espacios.
    category: validation
    applies_to: [QuoteClaim]
    trigger: Filtro (3), para cita_a y cita_b
    logic: "Normalizar = reemplazar cada secuencia de espacios en blanco Unicode por un solo espacio y recortar los extremos; nada más (mayúsculas, tildes, comillas y puntuación cuentan). La cita se parte por el separador « […] » (corchete, elipsis U+2026, corchete, con espacios alrededor). SI algún fragmento queda vacío ENTONCES not_found. SI no existe un turno con el número de turn_ref ENTONCES unknown_turn. SI cada fragmento normalizado aparece en el texto normalizado del turno, en orden y sin solaparse (búsqueda codiciosa de izquierda a derecha) ENTONCES verified. SI no, y la cita completa verifica así en exactamente otro turno ENTONCES other_turn; en cualquier otro caso, not_found. Un turno sin página solo se verifica por turno."
    violation: Pruebas de AC3.4.2 (a)–(h), de AC3.4.3 (subcadenas con espacios alterados y fragmentos en orden se aceptan) y propiedad inversa con Hypothesis (insertar o cambiar un carácter que no sea espacio hace que se rechace). 100 % de ramas (AC3.4.4).
    source: FR4.4; AC3.4.1–AC3.4.4; project.md (regla del piloto); AUTONOMIA-05
  - id: BR5.6
    status: nuevo
    statement: Una cita que no verifica descarta el candidato con cita_en_otro_turno si verifica en otro turno, y con cita_no_verificada en cualquier otro caso.
    category: validation
    applies_to: [JudgeCandidate, DiscardRecord]
    trigger: Resultado del filtro (3)
    logic: SI cita_a o cita_b es other_turn ENTONCES descarte cita_en_otro_turno. SI alguna es not_found o unknown_turn ENTONCES descarte cita_no_verificada. Se evalúa cita_a antes que cita_b, y el primer fallo decide.
    violation: Prueba por cada estado de verificación y por la combinación de una cita válida y otra no.
    source: FR4.4; AC3.4.2; C6 (motivos); AUTONOMIA-05
  - id: BR5.7
    status: nuevo
    statement: La cita se verifica sobre el texto ya restaurado por el anonimizador y contra el turno original de la entrada; los avisos y la página los pone el núcleo a partir del turno.
    category: policy
    applies_to: [QuoteClaim, Finding]
    trigger: Filtro (3) y armado del hallazgo
    logic: La verificación nunca usa los mensajes seudonimizados. Una cita que perdió o cambió una marca no coincide con el turno original y se descarta por BR5.6. SI el turno citado tiene hablante ENT ENTONCES aviso turno_entrevistador; SI tiene estado plegado ENTONCES turno_plegado; los dos pueden ir juntos. pagina de la cita = pagina del turno; ausente si el turno no la tiene.
    violation: Prueba con una cita seudonimizada restaurada que se verifica y con una que perdió la marca (AC11.3.4 a y d); prueba de avisos ENT y plegado (se aceptan con aviso).
    source: FR4.4; AC11.3.4; DT18; C6 (avisos, pagina); punto 2
  - id: BR5.8
    status: nuevo
    statement: En el modo incremental solo pasa un candidato con al menos una cita en un turno igual o posterior a desde_turno y ninguna posterior a hasta_turno.
    category: validation
    applies_to: [JudgeCandidate]
    trigger: Filtro (4), solo en modo incremental
    logic: SI las dos citas están en turnos con n < desde_turno, o alguna en un turno con n > hasta_turno ENTONCES descarte fuera_de_tramo.
    violation: Prueba de AC3.6.1 (un hallazgo con ambas citas antes de d y otro con una cita en d: solo sale el segundo).
    source: FR4.1; AC3.6.1; C6 regla 2

  # BR6 — Verificador y permutación
  - id: BR6.1
    status: nuevo
    statement: Cada candidato que pasó el filtro determinista recibe exactamente una llamada del verificador, y dos con la permutación activa.
    category: calculation
    applies_to: [JudgeCandidate, AnalysisRun]
    trigger: Fase verifying
    logic: Para k candidatos sobrevivientes, sin permutación hay exactamente k llamadas con papel verifier; con permutación, k con verifier y k con verifier_permuted, siempre las dos por candidato aunque la primera diga que no. Los candidatos se verifican en orden de primer turno citado, y la llamada directa va antes que la permutada.
    violation: Prueba de AC3.5.2 con k candidatos sobrevivientes y otros descartados (exactamente k llamadas verifier) y prueba de AC10.5.1 (dos llamadas por candidato con permutación).
    source: FR4.5; FR10.5; AC3.5.2; AC10.5.1; respuestas P1 = A y P4 = A
  - id: BR6.2
    status: nuevo
    statement: Un candidato que el verificador no confirma no sale y queda en el registro con rechazado_verificador.
    category: validation
    applies_to: [JudgeCandidate, DiscardRecord]
    trigger: Respuesta del verificador en el orden directo
    logic: SI verdict_direct es falso ENTONCES descarte rechazado_verificador, sea cual sea verdict_permuted.
    violation: Prueba de AC3.5.1 con un verificador fake que rechaza un candidato.
    source: FR4.5; AC3.5.1
  - id: BR6.3
    status: nuevo
    statement: Con la permutación activa, un candidato confirmado en el orden directo y no en el inverso no sale y queda con rechazado_permutacion.
    category: validation
    applies_to: [JudgeCandidate, DiscardRecord]
    trigger: Respuesta del verificador en el orden permutado
    logic: SI permutation es verdadero, verdict_direct es verdadero y verdict_permuted es falso ENTONCES descarte rechazado_permutacion. Solo se conserva si los dos son verdaderos.
    violation: Prueba con un verificador fake que confirma solo en un orden (AC10.5.1, parte N0).
    source: FR4.5; FR10.5; AC10.5.1; respuesta P4 = A; iteracion2 P12 = A
  - id: BR6.4
    status: nuevo
    statement: Una respuesta inválida del verificador invalida la corrida igual que una del juez.
    category: validation
    applies_to: [AnalysisRun]
    trigger: Respuesta del verificador que no cumple su esquema
    logic: SI la respuesta no es exactamente { confirma: boolean } ENTONCES InvalidOutput y la corrida termina en error salida_invalida con hallazgos vacíos.
    violation: Prueba con un verificador fake que devuelve texto, un campo extra o confirma como cadena.
    source: FR4.2; punto 4 (precisión FD-U11-28)

  # BR7 — Fallo cerrado, plazos, cancelación, alterno e incidente (módulo guardia)
  - id: BR7.1
    status: nuevo
    statement: Todo fallo después de aceptar la entrada deja estado error con su código, hallazgos y descartes vacíos y sin observaciones_conductor; el registro de llamadas se conserva.
    category: policy
    applies_to: [AnalysisRun]
    trigger: Cualquier error tipado o regla que invalida la corrida
    logic: "Correspondencia: InvalidOutput → salida_invalida; ContentBlocked sin alterno o en la ranura fallback → bloqueo_contenido; Timeout o plazo agotado → tiempo_agotado; ProviderError → proveedor; AnonymizerUnavailable → anonimizador_no_disponible; incidente (BR7.6) → incidente_anonimizacion. La salida lleva error.codigo, hallazgos [], registro.descartes [], registro.llamadas con lo que alcanzó a llamar y registro.fragmentado. Un error que no es de model_calls (un fallo del propio código) no se convierte en estado error: se propaga (CLI, código 5)."
    violation: Una prueba por código de AC3.2.1 (a)–(i) que comprueba hallazgos vacíos, descartes vacíos y observaciones_conductor ausente, y que la salida valida contra C6 (AC13.5.2).
    source: FR4.2; AC3.2.1; AC13.5.2; AUTONOMIA-05; C6 (allOf de estado); C17; precisión FD-U11-13
  - id: BR7.2
    status: nuevo
    statement: Antes de cada llamada se comprueban la cancelación y el plazo de la corrida; con el plazo agotado no se llama, y cada llamada recibe como timeout el menor entre el de llamada y el restante.
    category: constraint
    applies_to: [AnalysisRun]
    trigger: Antes de cada generate y entre ventanas
    logic: SI cancelled() devuelve verdadero ENTONCES no se hace ninguna llamada más y analyze lanza Cancelled sin Salida. SI ahora >= deadline ENTONCES la corrida termina en error tiempo_agotado sin llamar. SI no, timeout_s = min(model_call_timeout_s, deadline − ahora). Los reintentos locales (BR10.3) también respetan el plazo.
    violation: Prueba con reloj simulado (plazo agotado entre ventanas: tiempo_agotado y 0 llamadas nuevas) y con cancelled() verdadero tras la primera llamada (Cancelled y una sola llamada).
    source: C17 (CancelCheck); C18 limits; C25; CD-06; NFR10 (timeout explícito); punto 4 (precisión FD-U11-28)
  - id: BR7.3
    status: nuevo
    statement: Ante un bloqueo de contenido en la ranura primary, si el perfil tiene alterno se hace una sola llamada nueva con el mismo papel en la ranura fallback; cada llamada empieza otra vez por primary.
    category: policy
    applies_to: [AnalysisRun, GatewayAssembly]
    trigger: ContentBlocked de una llamada con destination_slot primary
    logic: SI el perfil tiene fallback_provider ENTONCES una llamada con destination_slot fallback y los mismos mensajes, registrada con fallback_provider verdadero. SI no tiene, o el bloqueo llega en la ranura fallback ENTONCES bloqueo_contenido. Ningún otro error (ProviderError, Timeout, InvalidOutput) pasa al alterno. El bloqueo de una llamada no cambia la ranura de las siguientes.
    violation: Prueba de AC13.5.1 (la llamada va al alterno y el registro lo marca), AC13.5.2 (sin alterno, bloqueo_contenido con hallazgos vacíos), bloqueo también en el alterno, y ProviderError con alterno (proveedor, sin pasar al alterno).
    source: FR15.2; AC13.5.1; AC13.5.2; C13 (fila 451); punto 5; precisión FD-U11-04
  - id: BR7.4
    status: nuevo
    statement: Si el anonimizador falla, no sale ninguna llamada al proveedor externo y la corrida termina en anonimizador_no_disponible.
    category: policy
    applies_to: [AnalysisRun, GatewayAssembly]
    trigger: AnonymizerUnavailable del módulo en proceso o del cliente HTTP de C21
    logic: SI el AnonymizingProvider lanza AnonymizerUnavailable (caído, excepción, sin responder antes de su plazo, 409, 422 o 503 del proxy) ENTONCES la corrida termina en error anonimizador_no_disponible, sin reintento y sin pasar al alterno.
    violation: Prueba compuesta con el ModelGateway real, su adaptador anonymizer, el módulo de U10 y su FakeTransport, para (a) caído, (b) excepción y (c) sin responder: el transporte registra 0 llamadas y el tramo termina en anonimizador_no_disponible (AC11.3.3), 100 % de ramas.
    source: FR11.3; AC11.3.3; AUTONOMIA-04; C13 (prueba compuesta); CD-01; CD-02
  - id: BR7.5
    status: nuevo
    statement: Ningún mensaje que sale hacia un proveedor externo lleva una entidad sembrada del conjunto sintético.
    category: policy
    applies_to: [GatewayAssembly]
    trigger: Prueba compuesta de AUTONOMIA-04 con un perfil comercial
    logic: Con el ModelGateway real, el adaptador anonymizer sobre el módulo de U10 y el analizador, se corre una transcripción sintética con entidades sembradas por juez, verificador y verificador permutado; los cuerpos que captura el FakeTransport no contienen ninguna. Con el paso de enmascarado puenteado en el fixture, la prueba falla.
    violation: Es la propia prueba de AC11.3.7 desde el lado de U11, con su control negativo.
    source: AC11.3.7; AUTONOMIA-04; C13 (prueba compuesta); NFR1
  - id: BR7.6
    status: nuevo
    statement: Si una llamada a un destino externo vuelve con anonimizado falso, la corrida se aborta en ese punto con incidente_anonimizacion.
    category: policy
    applies_to: [AnalysisRun]
    trigger: Después de cada llamada, con éxito o con un error que trae su ModelCall
    logic: SI el destino de la llamada tiene scope external y call.anonymized es falso ENTONCES no se hace ninguna llamada más, estado error con incidente_anonimizacion, hallazgos vacíos, y esa llamada queda en registro.llamadas con anonimizado false para que U4 bloquee la sesión. Tiene precedencia sobre cualquier otro código de la misma llamada. Una llamada local con anonimizado falso es correcta.
    violation: Prueba con un fake que devuelve un registro externo con anonymized false en la segunda llamada (exactamente 2 llamadas y el código) y con un error tipado que trae ese registro (AC3.2.1 i; lado de la biblioteca de AC11.3.8).
    source: VE-14; ADR-013; AC3.2.1 (i); AC11.3.8; CD-01; FD-U10-16
  - id: BR7.7
    status: nuevo
    statement: Con un perfil todo local, el ModelGateway nunca llama al AnonymizingProvider ni a nada fuera de la máquina o del clúster.
    category: constraint
    applies_to: [GatewayAssembly]
    trigger: Corrida con un perfil sin destinos externos
    logic: SI ningún papel ni el alterno tienen scope external ENTONCES el anonimizador no interviene, todas las llamadas van al adaptador local y todos los registros llevan anonimizado false.
    violation: Prueba con un AnonymizingProvider espía que registra 0 llamadas y con un adaptador local fake (AC11.3.6).
    source: AC11.3.6; iteracion2 P9 = A; C14

  # BR8 — Salida y registro
  - id: BR8.1
    status: nuevo
    statement: Toda salida se valida contra la copia de C6 antes de devolverse; si la que arma el núcleo no valida, se devuelve en su lugar una salida en error salida_invalida.
    category: validation
    applies_to: [AnalysisRun]
    trigger: Fase finalizing
    logic: SI la Salida armada no valida contra salida.schema.json ENTONCES se sustituye por una en error salida_invalida con hallazgos y descartes vacíos, que también se valida. Nunca sale una salida inválida.
    violation: Prueba de contrato sobre cada salida de las pruebas (AC3.6.2) y prueba con un hallazgo armado a propósito sin observaciones.
    source: FR4.1; AC3.6.2; AUTONOMIA-05
  - id: BR8.2
    status: nuevo
    statement: Los id de los hallazgos se numeran de forma determinista por el primer turno citado.
    category: calculation
    applies_to: [Finding]
    trigger: Fase finalizing
    logic: Los hallazgos se ordenan por (menor posición citada, mayor posición citada, posición de cita_a, cita_a normalizada) y se numeran <entrevista>-C01, -C02… con dos dígitos como mínimo.
    violation: Prueba con los mismos candidatos en otro orden de respuesta: mismos id.
    source: C6 (id); punto 3
  - id: BR8.3
    status: nuevo
    statement: Cada llamada, también las que fallaron con su registro, se copia a registro.llamadas con la tabla fija de papeles de U1, en orden cronológico.
    category: calculation
    applies_to: [AnalysisRun]
    trigger: Después de cada llamada que devuelve un ModelCall
    logic: role judge → papel juez, verifier → verificador, verifier_permuted → verificador_permutado; los demás campos según la tabla de C13. AnonymizerUnavailable no trae registro y no añade fila. El adaptador local llena version, esfuerzo_o_cuantizacion y motor desde los parámetros del perfil, y semilla solo si el servidor la admite.
    violation: Prueba de AC12.5.1 que comprueba cada campo por llamada, incluida una fallida con registro y una al alterno.
    source: FR15.3; AC12.5.1; C13 (del registro al contrato común); FD-U10-04
  - id: BR8.4
    status: nuevo
    statement: La salida suma los tokens y estima el costo con la tabla de precios; si algún modelo no tiene precio, el costo se omite y la CLI lo informa como «sin precio», sin detener la corrida.
    category: calculation
    applies_to: [AnalysisRun, PriceTable]
    trigger: Fase finalizing
    logic: tokens_entrada y tokens_salida = suma de las llamadas. SI todas las llamadas tienen precio en la tabla ENTONCES costo_estimado = Σ (tokens_entrada × input_per_million + tokens_salida × output_per_million) / 10^6 y tabla_precios = su versión. SI alguna no lo tiene ENTONCES costo_estimado se omite, tabla_precios se conserva y la CLI escribe en stderr «sin precio» con el proveedor y el modelo.
    violation: Prueba de AC12.5.2 con todos los precios y con un modelo sin precio (la corrida termina y no hay costo).
    source: FR15.4; AC12.5.2; C18 (prices); precisión FD-U11-14
  - id: BR8.5
    status: nuevo
    statement: La salida declara el modo fragmentado con su ventana y su solapamiento cuando el perfil lo activa, también en error.
    category: policy
    applies_to: [AnalysisRun, TranscriptWindow]
    trigger: Fase finalizing
    logic: registro.fragmentado.activo = chunking.enabled; con activo, ventana y solapamiento son los usados (BR2.7). Es lo que la consola y el reporte muestran como limitación (U4, U7).
    violation: Prueba de AC3.7.1 (parte de la biblioteca) con un perfil local.
    source: FR4.8; AC3.7.1; C18 (correspondencia chunking → fragmentado)
  - id: BR8.6
    status: nuevo
    statement: La biblioteca no emite observaciones_conductor; el campo queda ausente hasta que U8 añada las aclaraciones neutras.
    category: constraint
    applies_to: [AnalysisRun]
    trigger: Fase finalizing
    logic: La salida nunca trae observaciones_conductor en esta unidad. U8 lo añadirá en la misma biblioteca con su validación de VE-05 sin cambiar el contrato.
    violation: Prueba de que ninguna salida de U11 trae el campo.
    source: FR10.3 (SHOULD); punto 1; precisión FD-U11-03
  - id: BR8.7
    status: nuevo
    statement: La misma entrada, la misma configuración y el mismo fake dan la misma salida salvo fecha y las fechas del registro.
    category: constraint
    applies_to: [AnalysisRun]
    trigger: Cualquier corrida
    logic: El núcleo no usa azar, orden de diccionarios ni hora salvo para fecha, at y el plazo. version, perfil, prompt_sha256 y config_sha256 salen de la configuración.
    violation: Prueba que corre dos veces la misma entrada con el mismo fake y compara las salidas sin las fechas; sostiene AC2.2.7 de U4.
    source: FR14.2; AC2.2.7 (U4); C6 regla 4

  # BR9 — Escáner de vocabulario y aviso (IntegrityPolicy, reglas del analizador)
  - id: BR9.1
    status: nuevo
    statement: scan(text, literal_sources) busca los términos de la lista de C8 por palabra completa, sin distinguir mayúsculas ni tildes, y los términos se leen del archivo versionado.
    category: validation
    applies_to: [VocabularyScan]
    trigger: Cada llamada al escáner
    logic: Se pliegan mayúsculas y tildes (descomposición Unicode y eliminación de marcas diacríticas) en el texto y en los términos; una coincidencia es un término rodeado de límites de palabra Unicode. La lista es la de contracts/integrity/forbidden-vocabulary (C8); ninguna palabra está escrita en el código. Devuelve las coincidencias con su posición; los logs solo llevan el conteo.
    violation: Pruebas con «MIENTE», «mintio» sin tilde y «falsete» o «mienten» (pasan: palabra completa y lista cerrada, limitación conocida); control negativo con cada término de la lista (AC5.5.1, AC5.5.2 a).
    source: VE-02; FR6.4; AC5.5.1; AC5.5.2; C8 (match)
  - id: BR9.2
    status: nuevo
    statement: El escáner excluye los tramos entre «…» cuyo contenido aparece literal en alguna fuente, y la cadena del aviso de VE-01 cuando aparece completa.
    category: validation
    applies_to: [VocabularyScan, NoticeEmission]
    trigger: Antes de buscar términos
    logic: SI un tramo entre « y » tiene un contenido que, normalizado en espacios, es subcadena de alguna literal_source normalizada ENTONCES se excluye. Un tramo entre «» que no aparece en ninguna fuente sí se escanea. SI el texto contiene la cadena completa del aviso de C8 ENTONCES esa ocurrencia se excluye. Lo que decida U1 sobre el riesgo de una sola palabra citada (su precisión FD-U1-14) se aplica aquí sin otra regla.
    violation: Pruebas de AC5.5.2 (b) y (c): «falso» dentro de una cita literal no falla; «miente» entre «» que no está en ningún turno sí; prueba de AC5.5.6 con «prueba» dentro y fuera del aviso.
    source: FR6.4; A-1; AC5.5.2; AC5.5.6; C8 (excluded_spans); FD-U1-14 (pendiente)
  - id: BR9.3
    status: nuevo
    statement: Un candidato con vocabulario prohibido en hecho u observaciones, fuera de las citas literales, se descarta con vocabulario_prohibido y la corrida sigue.
    category: validation
    applies_to: [JudgeCandidate, DiscardRecord]
    trigger: Filtro (5)
    logic: Se escanean hecho y observaciones con literal_sources = textos de todos los turnos de la entrada; cita_a y cita_b no se escanean. SI hay alguna coincidencia ENTONCES descarte vocabulario_prohibido, que cuenta en registro.descartes y en el conteo por motivo del reporte C19. Los demás candidatos siguen.
    violation: Prueba de AC3.2.4 precisada (el candidato con «miente» en observaciones se descarta y otro candidato válido sale) y prueba sobre el conjunto sintético en nivel 2 (0 coincidencias en lo emitido, AC5.5.1).
    source: Respuesta P3 = A; AC3.2.4; VE-02; AUTONOMIA-03; precisión FD-U11-02
  - id: BR9.4
    status: nuevo
    statement: El escáner ejecuta en nivel 0 todos los casos de escaneo de vocabulario que publica U1, y falla si alguno no da lo esperado.
    category: validation
    applies_to: [VocabularyScan]
    trigger: Suite de nivel 0 de U11
    logic: Por cada caso de contracts/integrity/scan-cases.v1.yaml cuya regla es de vocabulario, se corre scan(text, literal_sources) y se comparan las coincidencias y los tramos excluidos con los esperados. Los campos cita, note, reformulation y notice se excluyen enteros, así que su caso espera 0 coincidencias. Los casos de aclaración neutra (campo tema con la regla de VE-05) los ejecuta U8 con su validador; la suite de U11 los lista como de U8 y falla si aparece un caso de un tipo que no conoce.
    violation: Un caso de escaneo modificado para esperar lo contrario hace fallar la suite (control negativo).
    source: AC5.5.1; AC5.5.2; U1 (los casos de escaneo los ejecuta U11 en B11); precisión FD-U11-20
  - id: BR9.5
    status: nuevo
    statement: La CLI escribe el aviso de VE-01 con su versión en stderr en cada ejecución y en un archivo AVISO.txt en cada directorio de salida.
    category: policy
    applies_to: [NoticeEmission, CliInvocation]
    trigger: Inicio de cada ejecución de la CLI y cada directorio de salida que crea
    logic: El texto y la versión se leen de contracts/integrity/notice.v1.yaml, sin cambiarlos. SI el archivo no existe o no trae versión ENTONCES código 3 antes de cualquier llamada. AVISO.txt contiene la versión y el texto exactos. Ningún contrato cambia.
    violation: Prueba de nivel 0 que captura stderr y lee AVISO.txt de cada directorio de salida y los compara con el archivo de C8.
    source: VE-01; US15.5 (la salida de la CLI lleva el mismo aviso); respuesta P8 = A; precisión FD-U11-08

  # BR10 — ModelGateway (adaptador local, adaptador anonymizer, cliente HTTP de C21)
  - id: BR10.1
    status: nuevo
    statement: El gateway se arma por perfil antes de cualquier llamada, y un papel externo sin AnonymizingProvider inyectado impide arrancar.
    category: validation
    applies_to: [GatewayAssembly]
    trigger: Construcción del gateway en la raíz de composición
    logic: Para cada papel y para el alterno, scope local → LocalModelAdapter; scope external → adaptador anonymizer con el AnonymizingProvider inyectado. SI falta el proveedor para algún destino externo ENTONCES error de configuración: la CLI termina con 3 y el proceso no arranca, con 0 llamadas.
    violation: Prueba de AC13.3.1 (b) en la CLI y en la biblioteca y de AC13.3.2 (el fake registra 0 llamadas); prueba con un destino externo y el módulo de U10 que no se puede construir (por ejemplo, el NER con otro sha256).
    source: FR14.3; AC13.3.1; AC13.3.2; AUTONOMIA-04; C13 (arranque); ADR-005
  - id: BR10.2
    status: nuevo
    statement: El adaptador local habla con el servidor compatible con OpenAI de C14 con salida forzada por json_schema y el razonamiento apagado, y valida la respuesta contra el esquema pedido.
    category: validation
    applies_to: [LocalModelAdapter]
    trigger: generate con destino local
    logic: POST /v1/chat/completions con model, messages, temperature, seed (si el servidor la admite) y response_format json_schema. Lee choices[0].message.content como JSON y usage. SI no es JSON o no valida contra req.schema ENTONCES InvalidOutput con su ModelCall. Devuelve GenerateResult con altered_markers vacío y anonymized falso.
    violation: Prueba de contrato con respuestas grabadas del servidor local (AC13.6.1, lado local) y con una respuesta que no cumple el esquema (AC13.6.2).
    source: FR15.1; AC13.6.1; AC13.6.2; C14; US14.1 (validación de la API del servidor local)
  - id: BR10.3
    status: nuevo
    statement: Los reintentos siguen la tabla de C13 y nunca pasan del plazo; el adaptador anonymizer y el cliente HTTP no reintentan.
    category: policy
    applies_to: [LocalModelAdapter, AnonymizerHttpClient]
    trigger: Error de una llamada
    logic: Local con conexión rechazada, 502, 503 o 504 → hasta 2 reintentos a los 2 s y 6 s, solo si el plazo restante alcanza; luego ProviderError o Timeout. Local con timeout o salida inválida → sin reintento. Anonymizer (módulo o cliente HTTP) → sin reintento en ningún caso, porque la llamada pudo salir del clúster.
    violation: Una prueba por fila de la tabla de C13, con reloj simulado.
    source: C13 (tabla de reintentos); project.md (reintentos del juez); NFR10
  - id: BR10.4
    status: nuevo
    statement: El cliente HTTP de C21 traduce cada respuesta del proxy al error tipado que fija C13 y solo importa los contratos.
    category: calculation
    applies_to: [AnonymizerHttpClient]
    trigger: Respuesta de anonymizer-proxy
    logic: "200 → GenerateResult con content, altered_markers y call; 409, 422, 503 o no poder conectar → AnonymizerUnavailable; 451 → ContentBlocked con su call; 502 con analysis.provider → ProviderError con su call; 502 con analysis.invalid_output → InvalidOutput con su call; 504 → Timeout con su call. Envía run_id, perfil, profile_sha256, papel, ranura, mensajes, esquema, semilla y timeout_s, nunca un destino ni una clave. check_ready() consulta /readyz y no forma parte del Protocol."
    violation: Una prueba por fila con un servidor HTTP fake local; prueba de import-linter de que el cliente solo importa los contratos.
    source: C21; C13 (filas anonymizer); FD-U10-04; AC11.6.1 (U4 lo usa en semantic-agent)
  - id: BR10.5
    status: nuevo
    statement: La biblioteca no importa Redis, Kubernetes ni controladores de base de datos, el gateway no importa el anonimizador, y solo la raíz de composición de la CLI lo importa.
    category: constraint
    applies_to: [GatewayAssembly]
    trigger: import-linter en nivel 0
    logic: "Contratos forbidden: libs.incoherence_analyzer, libs.model_gateway, libs.execution_profiles y libs.integrity_policy no importan redis, kubernetes ni controladores de base de datos; libs.model_gateway no importa libs.anonymizer; libs.incoherence_analyzer no importa libs.anonymizer salvo libs.incoherence_analyzer.cli.composition, que ningún __init__ reexporta. libs-anonymizer es una dependencia del extra cli."
    violation: Un fixture que importa redis desde el núcleo y otro que importa libs.anonymizer desde el gateway hacen fallar import-linter (AC12.2.1 con control negativo).
    source: FR13.1; AC12.2.1; DT26; C13 (costura con import-linter, R-18, R-19); ADR-010
  - id: BR10.6
    status: nuevo
    statement: Los adaptadores de los cuatro proveedores devuelven al núcleo la misma estructura, comprobada con respuestas grabadas sin red.
    category: validation
    applies_to: [RecordedResponse, GatewayAssembly]
    trigger: Prueba de contrato de nivel 0
    logic: Con el gateway real, el adaptador local sobre respuestas grabadas del servidor compatible con OpenAI y el adaptador anonymizer sobre el módulo de U10 con su FakeTransport reproduciendo respuestas grabadas sintéticas de Anthropic, Google y OpenAI, cada generate devuelve un GenerateResult con content validado contra el esquema del juez y un call completo. Primero el comercial de la primera rebanada y el local (US13.6), luego los otros dos (US13.7).
    violation: Una prueba por proveedor, y una respuesta grabada que no cumple el esquema da InvalidOutput en cada uno.
    source: FR15.1; AC13.6.1; AC13.6.2; AC13.7.1; CD-04; FD-U10-09

  # BR11 — CLI analyze
  - id: BR11.1
    status: nuevo
    statement: analyze corre en modo final por defecto y escribe un archivo de salida de C6 por entrevista, el reporte C19 y el aviso en el directorio indicado.
    category: policy
    applies_to: [CliInvocation, BatchItem, CliReport]
    trigger: veridicus analyze <archivo o directorio> --perfil <nombre> [--salida <dir>] [--modo incremental --desde N --hasta N]
    logic: Un archivo de entrada es el objeto transcripcion de C6; la CLI arma la entrada con el modo y el perfil. Un directorio aporta sus archivos .json de primer nivel en orden de nombre. Cada salida va a <salida>/<nombre sin extensión>.salida.json; el reporte kind run a <salida>/reporte.json, con interview_sha256 en vez del id; AVISO.txt según BR9.5. incremental solo con un archivo y con --desde y --hasta.
    violation: Prueba de AC12.1.1 con un directorio de 3 transcripciones y un fake.
    source: FR13.2; AC12.1.1; C19; punto 8
  - id: BR11.2
    status: nuevo
    statement: Toda la validación previa del lote termina antes de la primera llamada, y si algo falla la CLI no escribe ningún archivo.
    category: validation
    applies_to: [CliInvocation, BatchItem]
    trigger: Inicio de analyze y de evaluate
    logic: Se validan argumentos, cada archivo de entrada (BR1.1, BR1.2, BR1.5), nombres de salida repetidos, el perfil (BR2, BR1.3, BR1.4), el aviso (BR9.5), la construcción del gateway (BR10.1), que el directorio de salida se pueda escribir y la regla del corpus (BR11.5). SI algo falla ENTONCES código 2 (argumento, archivo, consentimiento, directorio) o 3 (perfil, anonimizador, clave, transferencia, aviso), un mensaje en español que nombra el problema y ningún archivo escrito, ni siquiera AVISO.txt.
    violation: Prueba de AC12.1.3 (a)–(d) con el fake (0 llamadas y directorio de salida sin archivos nuevos).
    source: FR13.2; FR14.3; AC12.1.3; AC13.3.2; C19 (códigos 2 y 3)
  - id: BR11.3
    status: nuevo
    statement: Los códigos de salida de la CLI son los de C19 más el 6 de la evaluación bajo umbral.
    category: policy
    applies_to: [CliInvocation]
    trigger: Fin de la ejecución
    logic: "0: todas las corridas terminaron, aunque alguna tenga estado error, y en evaluate todas las métricas pasan. 2 y 3: validación previa (BR11.2). 4: una corrida terminó con incidente_anonimizacion; el lote se detiene sin lanzar más corridas, se escriben la salida de esa corrida y el reporte con las corridas hechas. 5: error inesperado, reporte que no valida contra C19 o interrupción (SIGINT o SIGTERM, que pasa como cancelación y deja sin salida la corrida en curso). 6: evaluate terminó y alguna métrica no alcanza su umbral (propuesta)."
    violation: Una prueba por código (AC12.1.2 con una corrida en error: código 0 y la salida con su codigo).
    source: FR13.2; AC12.1.2; AC12.3.4; C19 (códigos); VE-14; ADR-013; precisión FD-U11-10
  - id: BR11.4
    status: nuevo
    statement: La CLI escribe cada archivo de forma atómica y nunca deja una salida, un reporte o un AVISO.txt a medias.
    category: constraint
    applies_to: [BatchItem, CliReport, NoticeEmission]
    trigger: Cada escritura
    logic: Se escribe en un archivo temporal del mismo directorio, se sincroniza y se renombra. SI la escritura falla ENTONCES se borra el temporal y la CLI termina con 5.
    violation: Prueba con un sistema de archivos fake que falla a mitad de la escritura: no queda el archivo final.
    source: FR4.2 (nunca un resultado parcial); NFR10
  - id: BR11.5
    status: nuevo
    statement: Una transcripción con origen corpus solo se analiza si su directorio de salida no lo puede rastrear Git.
    category: policy
    applies_to: [BatchItem, ResultsDirectory]
    trigger: Validación previa con algún archivo de origen corpus
    logic: SI el directorio de salida está dentro de un árbol de trabajo de Git (algún ancestro tiene .git) ENTONCES git check-ignore debe cubrirlo; si no lo cubre o Git no está disponible, código 2 sin escribir. SI no está dentro de ningún repositorio (por ejemplo, la carpeta del proyecto en ZINE, donde no se clona el repositorio) ENTONCES se permite. Sin --salida, el directorio es resultados-locales/<fecha>-<subcomando>, cubierto por .gitignore.
    violation: Prueba de AC12.4.1 con un directorio no ignorado (código 2, nada escrito), con el directorio por omisión y con un directorio fuera de todo repositorio.
    source: FR13.4; AC12.4.1; NFR12; punto 8; precisión FD-U11-16
  - id: BR11.6
    status: nuevo
    statement: Una comprobación de nivel 0 falla si Git rastrea algún archivo dentro del directorio de resultados o del paquete de ZINE.
    category: validation
    applies_to: [ResultsDirectory, ZinePackage]
    trigger: Suite de nivel 0 en cada PR
    logic: SI git ls-files devuelve algo bajo resultados-locales/ o evaluation/zine/paquete/ ENTONCES la comprobación falla y nombra la ruta (sin leer el archivo). .gitignore cubre las dos rutas.
    violation: Control negativo con un archivo sintético añadido al índice en un repositorio temporal (AC12.4.2, AC14.2.2).
    source: FR13.4; FR16.1; AC12.4.2; AC14.2.2; NFR12
  - id: BR11.7
    status: nuevo
    statement: Los logs, stderr, el reporte y AVISO.txt de la CLI no llevan texto de testimonio, solo IDs, hashes y cifras.
    category: policy
    applies_to: [CliInvocation, CliReport]
    trigger: Cualquier salida de la CLI que no sea un archivo de C6
    logic: Los mensajes nombran el archivo por su ruta y la entrevista por interview_sha256, nunca por su id ni por su texto. Los archivos de C6 sí llevan las citas verificadas: es su contenido.
    violation: Prueba de AC11.3.5 con un canary sembrado como nombre en un turno que ningún hallazgo cita: no aparece en logs, stderr, reporte, AVISO.txt ni en las salidas.
    source: AC11.3.5; NFR10; NFR12; C19 (sin texto libre); precisión FD-U11-18
  - id: BR11.8
    status: nuevo
    statement: Las 10 entrevistas del piloto se corren con la CLI en la máquina local como prueba de humo, con los resultados fuera de Git.
    category: policy
    applies_to: [CliInvocation, ResultsDirectory]
    trigger: Prueba manual de cierre de B11
    logic: El humano corre analyze sobre su copia local del corpus con el perfil de la primera rebanada y el directorio por omisión; el código debe ser 0 y el resumen frente a las 4 contradicciones conocidas se escribe fuera de Git. No mide ni entra a la evaluación.
    violation: Evidencia manual adjunta al PR sin texto del piloto, solo la salida de la orden y las cifras (AC12.4.3).
    source: AC12.4.3; team.md (nivel 2, prueba de humo del piloto); B11 (definición de terminado, punto 6)

  # BR12 — CLI evaluate y métricas
  - id: BR12.1
    status: nuevo
    statement: evaluate valida el conjunto, el perfil y los umbrales antes de cualquier llamada y corre el conjunto 3 veces con el mismo perfil.
    category: policy
    applies_to: [EvaluationRun, CliInvocation]
    trigger: veridicus evaluate --conjunto evaluation/synthetic --perfil <nombre> [--adversarial escenario-a]
    logic: SI el manifiesto o una muestra no pasan BR13 ENTONCES código 2. SI el perfil no es de evaluación, si la familia del generador coincide con la del juez o la del verificador, o si falta un umbral ENTONCES código 3. Luego corre las muestras en modo final 3 veces, en el mismo orden, y escribe las salidas por corrida (corrida-1/ a corrida-3/), el reporte kind evaluation y AVISO.txt.
    violation: Prueba de que un manifiesto inválido y un perfil de demostración terminan sin llamadas; prueba con un fake de que hay exactamente 3 corridas por muestra.
    source: FR13.3; NFR4; NFR5 Escenario B; respuesta P6 = A; AC12.3.2
  - id: BR12.2
    status: nuevo
    statement: Un acierto es un hallazgo cuyo par no ordenado de turnos coincide con una contradicción esperada; cada par cuenta una vez y el tipo se compara aparte.
    category: calculation
    applies_to: [MetricResult, ExpectedContradiction]
    trigger: Puntuación de cada corrida
    logic: Por muestra y corrida, TP = pares esperados encontrados (un par emitido dos veces cuenta una), FP = hallazgos emitidos cuyo par no es esperado, más todo hallazgo en un relato coherente o en un caso trampa; FN = pares esperados no encontrados. Un acierto con tipo distinto cuenta como acierto y como desacuerdo de tipo. Se suma en todo el conjunto (micro): precision = TP/(TP+FP), 1 si no hubo hallazgos; recall = TP/(TP+FN); type_agreement = aciertos con el mismo tipo / TP, 1 si TP = 0.
    violation: Prueba de AC12.3.1 con un fixture y salidas fijas (muestra coherente sin esperadas sin dividir por cero, par repetido, acierto con tipo distinto) y de AC12.3.3 (hallazgo en coherente y en trampa como falso positivo).
    source: NFR4; AC12.3.1; AC12.3.3; FR4.7
  - id: BR12.3
    status: nuevo
    statement: Las métricas absolutas deben cumplirse en las 3 corridas, las estadísticas se comparan por su media y el reporte trae el valor de cada corrida.
    category: calculation
    applies_to: [MetricResult, EvaluationThresholds]
    trigger: Fin de evaluate
    logic: "Absolutas: verified_quotes = 1 (cada cita emitida verifica de nuevo contra la muestra con BR5.5), json_format_errors = 0 (fracción de corridas por muestra con salida_invalida), permutation_coverage = 1 (llamadas verificador_permutado / llamadas verificador), anonymizer_leaks = 0 (llamadas externas con anonimizado falso) y completed_runs = 1 (fracción de corridas por muestra que no terminan en proveedor, tiempo_agotado, bloqueo_contenido ni anonimizador_no_disponible). Estadísticas: precision, recall y reversed_order_consistency (BR12.4), por su media. three_run_agreement = media por muestra del índice de Jaccard de los conjuntos de pares de las 3 corridas (1 si los tres son vacíos). type_agreement y la sensibilidad por distancia se reportan sin decidir. Los umbrales salen de evaluation/thresholds.v1.yaml y nunca se bajan."
    violation: Prueba de AC12.3.4 (una métrica bajo su umbral da passes falso y código 6) y prueba con una corrida de tres que rompe una métrica absoluta.
    source: Respuesta P6 = A; NFR4; AC12.3.1; AC12.3.4; AC3.4.5; team.md (los umbrales nunca se bajan); precisiones FD-U11-09 y FD-U11-10
  - id: BR12.4
    status: nuevo
    statement: La consistencia al invertir el orden es la fracción de candidatos verificados que reciben el mismo veredicto en los dos órdenes.
    category: calculation
    applies_to: [MetricResult, JudgeCandidate]
    trigger: Puntuación de cada corrida con permutación
    logic: evaluate envuelve el gateway con un registrador en memoria que guarda solo el booleano confirma de cada llamada verifier y verifier_permuted, emparejadas por BR6.1. reversed_order_consistency = pares con el mismo veredicto / pares; 1 si no hubo candidatos. El registrador nunca guarda texto.
    violation: Prueba con un verificador fake que alterna veredictos según el orden.
    source: NFR4; NFR5 Escenario C; punto 7; precisión FD-U11-27
  - id: BR12.5
    status: nuevo
    statement: La sensibilidad se reporta por distancia entre las dos citas esperadas, en tramos que dependen de la ventana del perfil.
    category: calculation
    applies_to: [MetricResult, ExpectedContradiction]
    trigger: Puntuación de cada corrida
    logic: distancia = diferencia de posición entre los dos turnos de la contradicción esperada. Tramos, con W y O del perfil (o W del tope sin chunking) - hasta O, de O+1 a W y más de W. Por tramo, esperadas y encontradas (mediana de las 3 corridas).
    violation: Prueba con esperadas en los tres tramos y un fake fijo.
    source: NFR4 (sensibilidad según la distancia); FR4.8; project.md (limitación medida por distancia); AC12.3.1
  - id: BR12.6
    status: nuevo
    statement: Con --adversarial escenario-a, evaluate añade el texto de inyección versionado a cada muestra y exige 0 apariciones de la salida reconocible y una diferencia no mayor que el desacuerdo entre las 3 corridas sin inyección.
    category: calculation
    applies_to: [EvaluationRun, MetricResult]
    trigger: evaluate --adversarial escenario-a
    logic: La inyección es evaluation/adversarial/escenario-a.v1.yaml, que añade un turno TEST final con el texto y define la salida reconocible (un hecho marcador o una etiqueta prohibida). Se corren 3 veces sin inyección y una con ella. scenario_a_marker_hits = apariciones de la salida reconocible en lo emitido o en registro.descartes por vocabulario_prohibido con el marcador, debe ser 0; scenario_a_difference = media por muestra de 1 − Jaccard(pares con inyección, pares de la corrida 1 sin ella), debe ser <= 1 − three_run_agreement sin inyección.
    violation: Prueba con un fake que obedece la inyección (falla) y otro que la ignora (pasa); en nivel 2 con el perfil real (AC3.3.2).
    source: NFR5 Escenario A; AC3.3.2; project.md (inyección medida frente al desacuerdo entre 3 corridas)
  - id: BR12.7
    status: nuevo
    statement: evaluate --score puntúa salidas ya producidas sin llamar a modelos y exige que cada llamada registrada declare modelo, versión, cuantización y motor.
    category: validation
    applies_to: [EvaluationRun, ZineRunMetadata]
    trigger: veridicus evaluate --conjunto <dir> --puntuar <corrida-1> <corrida-2> <corrida-3>
    logic: Cada directorio trae una salida de C6 por muestra. SI una llamada no trae modelo, version, esfuerzo_o_cuantizacion o motor ENTONCES código 2 con un mensaje que nombra el campo. SI la cuantización no es Q8 (Q8_0) ni BF16 ENTONCES el reporte se marca no válido para medir capacidades y la CLI escribe «no válida para medir capacidades». No se construye gateway ni se lee ninguna clave.
    violation: Prueba de AC14.3.1 (una salida sin cada campo) y AC14.3.2 (Q4_K_M marcada); prueba de que el modo no hace ninguna llamada.
    source: FR16.2; AC14.3.1; AC14.3.2; punto 8; precisión FD-U11-19

  # BR13 — Conjunto sintético y tabla de sesgo
  - id: BR13.1
    status: nuevo
    statement: El manifiesto del conjunto declara versión, generador con su familia, revisión manual y, por muestra, su SHA-256, su categoría, sus dos etiquetas y sus contradicciones esperadas, y la validación falla si algo falta.
    category: validation
    applies_to: [SyntheticDataset, DatasetSample]
    trigger: Validación del conjunto (nivel 0 y al inicio de evaluate)
    logic: SI falta un campo del manifiesto, un SHA-256 no coincide con el archivo, hay un archivo en evaluation/synthetic/ fuera del manifiesto, una muestra no tiene origen sintetico, o falta la revisión manual ENTONCES la validación falla. dataset_sha256 = SHA-256 de los bytes del manifiesto.
    violation: Fixtures de manifiesto con cada falta (control negativo por campo).
    source: NFR4; NFR5 Escenario B; B11 (conjunto revisado a mano con la familia del generador); AC12.3.2
  - id: BR13.2
    status: nuevo
    statement: El conjunto cubre los 7 tipos de contradicción, relatos coherentes y los 4 casos trampa, y cada contradicción esperada es coherente con su muestra.
    category: validation
    applies_to: [SyntheticDataset, ExpectedContradiction]
    trigger: Validación del conjunto
    logic: SI falta alguno de los 7 tipos, los coherentes o alguno de vaguedad, emoción, detalle periférico y versión de terceros, o no se alcanza la composición mínima que fije NFR Requirements ENTONCES falla. SI alguna cita esperada no verifica contra su turno con BR5.5, o una muestra contradiccion no trae esperadas, o una coherente o trampa sí ENTONCES falla.
    violation: Fixture sin un tipo, sin un caso trampa y con una cita esperada alterada.
    source: NFR4; FR4.7; AC12.3.3; team.md (nivel 2)
  - id: BR13.3
    status: nuevo
    statement: Cada muestra lleva una etiqueta de tipo de hecho y otra de perfil de la persona, tomadas de dos listas cerradas y versionadas; sin ellas la validación falla.
    category: validation
    applies_to: [DatasetSample, BiasLabelList]
    trigger: Validación del conjunto
    logic: SI tipo_hecho o perfil_persona faltan o no están en evaluation/labels/tipo-hecho.v1.yaml o perfil-persona.v1.yaml ENTONCES falla. Cada valor cumple ^[a-z0-9-]{1,23}$.
    violation: Prueba de AC15.10.1 con una muestra sin etiquetas y otra con una etiqueta fuera de la lista.
    source: VE-17; AC15.10.1; respuesta P7 = A; precisión FD-U11-07
  - id: BR13.4
    status: nuevo
    statement: El reporte de evaluación trae la tabla de sesgo agrupada por tipo de hecho y perfil, y una comprobación falla si falta.
    category: calculation
    applies_to: [BiasRow, EvaluationRun]
    trigger: Fin de evaluate
    logic: Por cada grupo <tipo_hecho>__<perfil_persona> y cada tipo de contradicción con esperadas o encontradas, una fila con synthetic_set = el grupo, fact_type = el tipo de la contradicción, expected = contradicciones esperadas del grupo y found = hallazgos emitidos del grupo (mediana de las 3 corridas). El número de muestras por grupo, que da la tasa por transcripción, sale del manifiesto de esa versión. SI el reporte kind evaluation no trae bias_table ENTONCES la comprobación falla.
    violation: Prueba de nivel 0 con un fake y un reporte sin la tabla (control negativo); en nivel 2, AC15.10.2.
    source: VE-17; AC15.10.2; respuesta P7 = A; C19 (bias_table)
  - id: BR13.5
    status: nuevo
    statement: El conjunto lo genera un modelo comercial de una familia distinta a las del juez y del verificador de todo perfil de evaluación, solo con datos sintéticos, y lo revisa a mano el autor antes de etiquetar su versión.
    category: policy
    applies_to: [SyntheticDataset]
    trigger: Construcción del conjunto en B11 y cada cambio de versión
    logic: La familia del generador queda en el manifiesto y evaluate rechaza un perfil con esa misma familia en el juez o el verificador (BR12.1). El prompt de generación pide relatos ficticios, sin nombres, lugares ni expedientes reales; el autor revisa cada muestra y registra quién y cuándo en el manifiesto. El conjunto pasa gitleaks.
    violation: Revisión manual registrada en el PR y prueba de nivel 0 de que la familia del generador no coincide con ningún perfil de evaluación.
    source: NFR5 Escenario B; NFR12; B11 (P12 = A de Delivery Planning); project.md (solo datos sintéticos)

  # BR14 — ZINE
  - id: BR14.1
    status: nuevo
    statement: En Git, para ZINE, solo van los .sbatch, el script que arma el paquete y un manifiesto con nombres y SHA-256, sin contenido de entrevistas.
    category: validation
    applies_to: [ZinePackage]
    trigger: Suite de nivel 0 en cada PR
    logic: SI bajo evaluation/zine/ hay otro tipo de archivo rastreado, o el manifiesto trae algo más que nombre, SHA-256 y fuente ENTONCES la comprobación falla.
    violation: Control negativo con una transcripción y con un campo de texto en el manifiesto (AC14.2.1).
    source: FR16.1; AC14.2.1; NFR12
  - id: BR14.2
    status: nuevo
    statement: El script de empaquetado arma el paquete en un directorio ignorado por Git, con transcripciones validadas y solo de dos fuentes, y añade el consentimiento del corpus desde un archivo que da el humano.
    category: validation
    applies_to: [ZinePackage]
    trigger: El humano corre evaluation/zine/empaquetar.py
    logic: Escribe solo en evaluation/zine/paquete/. Cada transcripción valida contra C6 (BR1.1, BR1.2) y está en el manifiesto con fuente sintetico o corpus; un archivo ajeno lo hace fallar. A una transcripción de corpus sin bloque le añade el consentimiento que lee de un archivo del humano fuera de Git (versión del texto del TG); nunca lo inventa. Copia la wheelhouse de la CLI y un perfil sin destinos externos; un perfil con destino externo hace fallar el empaquetado.
    violation: Prueba de AC14.2.3 con un archivo ajeno y con una transcripción inválida; prueba de que sin el archivo de consentimiento el corpus no se empaqueta.
    source: FR16.1; FR16.2; AC14.2.2; AC14.2.3; A-4; precisión FD-U11-17
  - id: BR14.3
    status: nuevo
    statement: El paquete no lleva credenciales ni el repositorio, y gitleaks sobre él termina con 0.
    category: constraint
    applies_to: [ZinePackage]
    trigger: Fin del empaquetado
    logic: El script corre gitleaks sobre el directorio del paquete; SI encuentra algo ENTONCES borra el paquete y termina con código ≠ 0. No copia .git, .env ni config/ con claves.
    violation: Prueba de AC14.2.4 con un canary con forma de clave sembrado en un archivo del paquete.
    source: FR16.1; AC14.2.4; NFR10
  - id: BR14.4
    status: nuevo
    statement: Los .sbatch los escribe el agente y los lanza el humano; ningún script ni workflow del repositorio envía trabajos a ZINE.
    category: policy
    applies_to: [ZinePackage]
    trigger: Revisión del PR y suite de nivel 0
    logic: Los .sbatch siguen las normas del clúster (HOME y cachés en la carpeta del proyecto, entorno conda propio, salidas bajo la carpeta de resultados del proyecto) y corren la CLI contra un servidor local del mismo trabajo. Ningún archivo del repositorio invoca sbatch, ssh ni scp hacia ZINE salvo como texto de instrucciones para el humano. Del clúster solo vuelve el reporte C19 de las corridas del corpus; sus salidas de C6 se quedan allí.
    violation: Comprobación estática de nivel 0 sobre evaluation/ y scripts/ con control negativo (un script con sbatch).
    source: AUTONOMIA-01; FR16.1; NFR12; US14.2 (los .sbatch de producción entran por PR)
  - id: BR14.5
    status: nuevo
    statement: Un trabajo de ZINE instala la CLI sin internet desde la wheelhouse y analiza una transcripción sintética contra el servidor local.
    category: policy
    applies_to: [ZinePackage]
    trigger: El humano lanza evaluation/zine/instalar-y-analizar.sbatch
    logic: pip install --no-index --find-links con la wheelhouse del paquete, en el entorno conda propio; luego veridicus analyze sobre una muestra sintética con el perfil local. El trabajo registra la versión instalada y termina con 0; el humano adjunta su salida al PR.
    violation: Evidencia del trabajo (comando, ID de SLURM, nodo, código 0 y versión) adjunta por el humano (AC14.2.5).
    source: FR16.1; AC14.2.5; US14.1 (M5, instalación sin internet)
```

## Resumen

| Grupo | Reglas | Módulo guardia | Qué protege |
|---|---|---|---|
| BR1 Entrada y consentimiento | BR1.1–BR1.5 | — | Analizar una entrada inválida, sin consentimiento o con una transferencia no autorizada (A-4) |
| BR2 Perfiles | BR2.1–BR2.11 | — | Arrancar con un perfil inválido, familias iguales, un alterno de la misma familia, ventanas sin tope o huellas que no se repiten |
| BR3 Prompt y mensajes | BR3.1–BR3.4 | — | Que el testimonio cambie las reglas; que el verificador vea más de lo necesario |
| BR4 Ventanas y deduplicación | BR4.1–BR4.3 | — | Ventanas que exceden su tamaño; llamadas duplicadas al verificador |
| BR5 Filtro determinista | BR5.1–BR5.8 | Sí, 100 % de ramas | Un hallazgo con citas que no están en su turno, mal formado o fuera del tramo (AUTONOMIA-05) |
| BR6 Verificador y permutación | BR6.1–BR6.4 | Sí (BR6.4) | Hallazgos sin confirmar, o confirmados en un solo orden |
| BR7 Fallo cerrado e incidente | BR7.1–BR7.7 | Sí (BR7.1–BR7.3, BR7.6) | Resultados parciales, llamadas fuera de plazo, salida sin anonimizar (AUTONOMIA-04/05, VE-14) |
| BR8 Salida y registro | BR8.1–BR8.7 | Sí (BR8.1) | Salidas que no cumplen C6, registro incompleto o costo inventado |
| BR9 Escáner y aviso | BR9.1–BR9.5 | — | Etiquetas de veracidad en lo emitido (AUTONOMIA-03, VE-02) y una CLI sin aviso (VE-01) |
| BR10 ModelGateway | BR10.1–BR10.6 | — | Un destino externo sin anonimizador, reintentos que duplican salidas, infraestructura en la biblioteca |
| BR11 CLI analyze | BR11.1–BR11.8 | — | Salidas a medias, corpus en Git, testimonio en logs |
| BR12 CLI evaluate | BR12.1–BR12.7 | — | Métricas mal calculadas o comparadas, umbrales ignorados, corridas de ZINE incomparables |
| BR13 Conjunto sintético y sesgo | BR13.1–BR13.5 | — | Un conjunto incompleto, sin etiquetas o generado por la misma familia que evalúa |
| BR14 ZINE | BR14.1–BR14.5 | — | Corpus o credenciales en Git o en el paquete, y trabajos lanzados sin el humano (AUTONOMIA-01) |

Son 85 reglas, todas nuevas.
