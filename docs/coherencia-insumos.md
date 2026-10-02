# Auditoría de coherencia de los insumos — Veridicus

*Paso 1 de `plan-aidlc.md` · 2026-10-02 · antes de abrir Inception*

Cruce de `pvb.md` (idéntico a `docs/pvb.md`), `specs/prd.md`, `docs/critica.md`, `docs/icp.md`,
`docs/mercado.md`, `docs/overview.md`, `docs/iteracion1.md` y `docs/limite-autonomia.md`, más una
verificación puntual de las cifras citadas contra el texto de `research/`.

**Regla de precedencia usada:** cuando dos documentos chocan, manda el más reciente y más
específico: `specs/prd.md` (con su Anexo, Iteración 4) por encima de `docs/iteracion1.md`, y este
por encima de `pvb.md`, `critica.md`, `mercado.md`, `icp.md` y `overview.md`. Las preguntas piden
confirmar o corregir esa precedencia caso por caso.

## Cómo responder

- Escribe la letra después de `[Answer]:`. Si eliges `X`, añade el texto en la misma línea.
- La opción marcada **(Recomendada)** es mi propuesta; no está aplicada todavía.
- «Depende» o «una mezcla de A y B» no valen: si ninguna opción encaja, usa `X` y escríbela.
- Cuando respondas todo, aplico las correcciones a los **originales**, con un commit por documento.

## Resumen de hallazgos

| # | Tipo | Tema | Documentos | Impacto en AI-DLC |
|---|---|---|---|---|
| H1 | Contradicción | Entrada del testimonio: texto o voz | PRD S5, S7, S8 | Requirements, User Stories |
| H2 | Hueco de alcance | Agente conversacional que formula preguntas | PRD S5, S7, S8, S13; PVB §5 | Requirements, Units |
| H3 | Contradicción | Edición de alertas y descarga del reporte en SHOULD | PRD S6, S8; `limite-autonomia` | Requirements (AUTONOMIA-03) |
| H4 | Contradicción | Análisis afectivo LieXBerta: dentro o fuera del MVP | PRD S5, S7, S8, S10, S12 | Requirements, NFR |
| H5 | Hueco de alcance | Codificador de tipos de pregunta (Szojka) | PRD S10; `overview` §3 | Requirements |
| H6 | Contradicción | PVB y crítica desactualizados (latencia, GPU, streaming, Argo) | PVB §4–7; `critica` R3; `iteracion1` #3 | Trazabilidad de Inception |
| H7 | Hueco de alcance | Plataforma (KEDA, Argo CD, Prometheus, NetworkPolicy, proxy) fuera de MoSCoW | PRD S7 J2, S8, S12, S13 | Units, Delivery Planning |
| H8 | Hueco | Ruta al LLM externo y proxy de anonimización en el MVP | PRD S6 P3, S9, S11-B | Domain Design (AUTONOMIA-04) |
| H9 | Hueco | Modelo local del juez y de embeddings en CPU | PRD S9, S11-B | NFR, Domain Design |
| H10 | Hueco | Umbral de similitud del Silencio Fáctico sin valor | PRD S7 J4; AUTONOMIA-05 | Requirements, Contract Design |
| H11 | Contradicción | Recalibración automática de umbrales por AIR | PRD S10 §4; S6 P1 | Requirements (AUTONOMIA-03) |
| H12 | Contradicción | Firma digital / criptográfica del reporte | PRD S6 P1, S7 J1, S10 MTTV | Requirements |
| H13 | Contradicción | Métrica MTTV: meta y línea base | PRD S5 CU5, S10; PVB §8 | Requirements (NFR medibles) |
| H14 | Hueco de alcance | Reanudación de sesión (Journey 3) | PRD S7 J3, S8 | User Stories |
| H15 | Contradicción | «Marco de verdad» en variables de entorno vs. en `pgvector` | PRD S12 R7, S5 CU1, S13 | Domain Design |
| H16 | Riesgo / hueco | Protocolo de permutación (doble llamada) en CPU | PRD S11-C, S2 P2 | NFR |
| H17 | Hueco | Autenticación y roles de la consola | PRD S5 CU1, S7 J1–J2 | Requirements, Contract Design |
| H18 | Hueco | Composición del Golden Dataset y evaluadores | PRD S11 §1–2 | Build and Test, NFR |
| H19 | Sin fuente | Cifras mal atribuidas o sin respaldo en `research/` | PRD S5, S7, S10, S11, S12; `critica`, `mercado`, `overview` | Sensores de trazabilidad (claim-sources) |

---

## H1 — Entrada del testimonio: texto o voz

**Evidencia.**
- PRD S8 MUST: «Entrada de Texto Plano en Español… asumiendo la transcripción por audio como un pipeline externo».
- En el mismo bloque MUST: «Grabación por Demanda **Opcional**… procesándose mediante un modelo Whisper ligero en CPU».
- CU2, Journey 1 y J3 describen la **voz** como flujo principal. La sustentación (S13 §5) usa solo texto.

**Problema.** Una función «opcional» dentro de MUST hace ambiguo el criterio de terminado, y Whisper
arrastra un pod, un PVC de audio y la latencia de 8–12 s.

Question: ¿Qué nivel MoSCoW tiene la entrada por voz (push-to-talk + Whisper en CPU)?

A. MUST: el texto y la voz son obligatorios en el MVP.
B. SHOULD: el texto es el único MUST; la voz es lo primero que se añade si el texto funciona **(Recomendada)**
C. COULD: solo si sobra tiempo.
D. WON'T: se quita del MVP; Whisper queda para el TG.
X. Other (please specify)

[Answer]:

B

## H2 — Agente conversacional que formula la siguiente pregunta

**Evidencia.**
- CU2 paso 3, Journey 1 paso 4 y Journey 4 paso 3 tienen un «Agente Conversacional» que decide la siguiente pregunta.
- El PVB §5 elige el paradigma *Agent* («la IA recopila autónomamente el testimonio mediante diálogo oral dinámico»).
- En cambio, S8 MUST no lista esa función, el S9 no le da módulo propio y la sustentación (S13) no la muestra.
- S6 P1 define la IA como «consultor».

**Problema.** Sin decidirlo, Units Generation puede crear o no una unidad conversacional, y el
paradigma del PVB choca con el Principio 1.

Question: ¿Entra en el MVP un agente que genere la siguiente pregunta al compareciente?

A. Sí, como MUST: el sistema propone y lanza la siguiente pregunta en cada turno.
B. Sí, como SHOULD pero solo como **sugerencia** al analista, que decide si la formula; si se omite, no se rompe ningún MUST **(Recomendada)**
C. COULD: solo si sobra tiempo, también como sugerencia al analista.
D. WON'T: el MVP solo contrasta testimonios; el diálogo dinámico queda para el TG, y el PVB §5 se corrige a *Assistant*.
X. Other (please specify)

[Answer]:

B

## H3 — Edición de alertas y descarga del reporte en SHOULD

**Evidencia.**
- S8 SHOULD: «Edición y Descarte Manual de Alertas» y «Descarga de Reporte Final».
- S6 P1 y AUTONOMIA-03 exigen que todo hallazgo sea una sugerencia con estado editable, cambiado por un humano.
- Además, que la consolidación sea una acción explícita del analista.
- La sustentación (S13 §5, paso 5) incluye la descarga del reporte.

**Problema.** Una regla bloqueante no puede depender de una función SHOULD. Si se omite, el MVP viola
AUTONOMIA-03.

Question: ¿Cómo se reclasifican estas dos funciones?

A. Ambas pasan a MUST, junto con «Consolidar reporte» como acción explícita del analista con registro de quién y cuándo **(Recomendada)**
B. Solo la edición y descarte pasa a MUST; la descarga sigue en SHOULD.
C. Se dejan en SHOULD y se acepta el riesgo frente a AUTONOMIA-03.
X. Other (please specify)

[Answer]:

A

## H4 — Análisis afectivo LieXBerta: dentro o fuera del MVP

**Evidencia.**
- S8 WON'T excluye el modelo completo RoBERTa + XGBoost. El COULD solo admite palabras clave en el prompt.
- Sin embargo, CU4 usa RoBERTa + XGBoost con un umbral de vacilación de 0.4166 (KPI > 85 %).
- Journey 4 muestra picos de vacilación de 0.78.
- S10 §3 fija como «Meta del MVP» un 87.50 % de *accuracy* y un 87.13 % de F1.
- S12 R10 propone calibración regional del modelo. J2 escala pods de RoBERTa con KEDA.

**Problema.** Requirements Analysis tomaría metas y casos de uso de algo que el propio PRD excluye.

Question: ¿Cómo se alinea el PRD con el WON'T del modelo afectivo?

A. Se mantiene el WON'T. CU4, J4 (dato 0.78), S10 §3 (LieXBerta), R10 y el escalado de RoBERTa se marcan «Alcance TG2, fuera del MVP». El COULD de palabras clave queda sin meta numérica **(Recomendada)**
B. Igual que A, pero el COULD de palabras clave lleva una meta medible contra las etiquetas estilométricas del Golden Dataset.
C. Se sube el modelo completo a SHOULD y se conservan sus metas.
X. Other (please specify)

[Answer]:

A

## H5 — Codificador de tipos de pregunta (Szojka)

**Evidencia.** S10 §3 fija una meta del 95 % de acuerdo (κ 0.93) para un «Codificador de Preguntas
Conversacionales». Ningún módulo de S9 ni ninguna fila de S8 lo implementa. `overview.md` §3 lo usa
como justificación del agente conversacional.

Question: ¿Qué se hace con esa métrica?

A. Se mueve a «Alcance TG», fuera del MVP, junto con el agente conversacional si H2 = D.
B. Se conserva solo si H2 es A o B, como meta del agente que sugiere preguntas, y se marca «sin implementación en el MVP» en caso contrario **(Recomendada)**
C. Se añade como función COULD con esa meta.
X. Other (please specify)

[Answer]:

B

## H6 — PVB y crítica desactualizados frente al PRD

**Evidencia.**
- PVB §6: latencia de 3–5 s. `iteracion1.md` #3: < 1.5 s. PRD S6 P2 y S8: 8–12 s en CPU.
- PVB §4 y §7: KEDA «basado en GPU», colas «gRPC/WebSockets», Argo Workflows para audios de 2–3 h, COGS con «clúster GPU».
- PRD S8 WON'T: sin GPU, sin streaming.
- `critica.md` R3 mitiga con «gRPC y WebSockets para transmitir el sonido en tiempo real», que el PRD excluye.
- `iteracion1.md` ya tiene nota de que fue superada; el PVB y la crítica no.

**Problema.** La regla de trazabilidad de Inception pide que cada requisito trace a un insumo de
ideación. Si el PVB contradice al PRD, los sensores y el revisor marcarán falsos conflictos.

Question: ¿Cómo se tratan el PVB y la crítica?

A. Se conservan como registro histórico (módulos 2–3) y se les añade al inicio una nota «Superado por `specs/prd.md` en: latencia, GPU, streaming, Argo Workflows», como ya tiene `iteracion1.md` **(Recomendada)**
B. Se editan en el cuerpo para alinearlos con el PRD.
C. Se dejan intactos y se excluyen de los insumos de AI-DLC: solo el PRD alimenta Inception.
X. Other (please specify)

[Answer]:

A

## H7 — Plataforma fuera del MoSCoW

**Evidencia.**
- El MoSCoW (S8) solo cubre funciones de usuario.
- KEDA, Argo CD, Prometheus/Grafana (con el panel AIR), NetworkPolicies, el pod proxy, la separación de namespaces y los Secrets aparecen en J2, S12 y S13 como plan de entrega.
- No tienen prioridad.
- AUTONOMIA-04 exige la `NetworkPolicy` como tarea.

**Problema.** Units Generation y Delivery Planning necesitan saber qué de la plataforma es obligatorio.

Question: ¿Cómo se prioriza la plataforma?

A. Se añade al S8 una subsección «Plataforma». MUST: CloudNativePG + pgvector, Redis, manifiestos/Helm con `resources`, NetworkPolicy sin salida para datos sin anonimizar, Secrets. SHOULD: Argo CD, Prometheus/Grafana. COULD: KEDA **(Recomendada)**
B. Igual que A, pero KEDA también en SHOULD (módulo 6 del curso).
C. Todo lo de S13 es MUST, porque lo exige el curso.
X. Other (please specify)

[Answer]:

A

## H8 — Ruta al LLM externo y proxy de anonimización en el MVP

**Evidencia.**
- S6 P3 y el diagrama de S9 tienen una salida opcional a un LLM comercial a través del proxy.
- S11-B pide que el juez sea local (LLaMA/Mistral en CPU).
- S8 no menciona ni el proxy ni el LLM externo.
- AUTONOMIA-04 pide una prueba de anonimización solo «si se integra un servicio externo».

Question: ¿Qué alcance tiene la salida a un LLM externo en el MVP?

A. WON'T: el MVP funciona sin salida a internet; el proxy queda diseñado como frontera, pero no se implementa. La NetworkPolicy niega toda salida.
B. COULD: se implementa el proxy de anonimización (regex en español) con su prueba de payload, pero sin depender de él para ningún MUST **(Recomendada)**
C. MUST: el juez usa un LLM externo a través del proxy.
X. Other (please specify)

[Answer]:

B

## H9 — Modelo local del juez y de embeddings en CPU

**Evidencia.**
- S9 dice «LLM-as-a-judge local» sin nombrar el modelo.
- S11-B pone de ejemplo «Meta LLaMA 3.3 o Mistral fine-tuned local en CPU». LLaMA 3.3 solo existe en 70B, inviable en un clúster académico sin GPU.
- No hay modelo de embeddings definido para `pgvector`.
- S10 pide 0 % de error de formato.

Question: ¿Qué se fija en el PRD sobre los modelos?

A. Se fija una clase de modelo: juez cuantizado de ≤ 8B parámetros en CPU (p. ej., Llama 3.1 8B o Mistral 7B vía Ollama/llama.cpp), embeddings multilingües locales (p. ej., `multilingual-e5-small`), y la elección exacta queda para NFR Requirements con un benchmark sobre el Golden Dataset **(Recomendada)**
B. Se fija ya un modelo concreto (escríbelo en `X`).
C. No se fija nada; lo decide Domain Design.
X. Other (please specify)

[Answer]:

A

## H10 — Umbral de similitud del Silencio Fáctico

**Evidencia.** J4 y AUTONOMIA-05 dependen de un «umbral mínimo del sistema» configurable que no
tiene valor ni métrica de similitud.

Question: ¿Cómo se define el umbral?

A. Similitud coseno con un valor inicial de 0.75, configurable, calibrado con el Golden Dataset en Build and Test.
B. Sin valor inicial en el PRD: se especifica como parámetro obligatorio y su valor se fija y documenta en NFR Requirements tras medirlo contra el Golden Dataset **(Recomendada)**
C. Valor fijo no configurable.
X. Other (please specify)

[Answer]:

B

## H11 — Recalibración automática de umbrales por AIR

**Evidencia.** S10 §4: si el AIR supera el 25 %, «se activa automáticamente un disparador de
re-calibración en caliente de los umbrales». Eso cambia el comportamiento de la IA sin decisión
humana (S6 P1) y altera la base de AUTONOMIA-05.

Question: ¿Qué ocurre cuando el AIR supera el umbral?

A. Se alerta al analista o al administrador en Grafana con una propuesta de nuevo umbral; el cambio lo aplica un humano **(Recomendada)**
B. Se mantiene la recalibración automática.
C. Se elimina la reacción; el AIR solo se mide.
X. Other (please specify)

[Answer]:

A

## H12 — Firma digital / criptográfica del reporte

**Evidencia.**
- J1 paso 6 exporta un Markdown «con firmas criptográficas».
- S10 define el MTTV hasta que el reporte es «firmado digitalmente».
- S6 P1 habla de «firma digital» para cambios en producción.
- No hay función de firma en S8 ni en S9.

Question: ¿Qué significa «firma» en el MVP?

A. Registro de quién consolidó y cuándo, más un hash SHA-256 del Markdown guardado junto al reporte; sin firma criptográfica con llave del analista **(Recomendada)**
B. Firma criptográfica real (p. ej., llave por analista) como MUST.
C. Se elimina toda mención de firma.
X. Other (please specify)

[Answer]:

A

## H13 — Métrica MTTV: meta y línea base

**Evidencia.**
- S10: meta «menos de 10 minutos» y «reducción de más del 50 % al 80 %», sobre una línea base de «30 minutos a varias horas» [16].
- CU5 y PVB §8: > 50 %.
- La cifra de 30 min de [16] (Szojka) mide la **codificación manual de tipos de pregunta**, no el cotejo de un testimonio.

Question: ¿Cómo queda la métrica?

A. Meta única: < 10 min por caso del Golden Dataset, medida desde «Finalizar sesión» hasta «Consolidar». La línea base se declara supuesto «[VERIFICAR] sin fuente directa» y se cita [16] solo como referencia análoga **(Recomendada)**
B. Meta relativa: > 50 % de reducción frente a una línea base que se medirá cronometrando un cotejo manual del Golden Dataset.
C. Se dejan las dos metas como están.
X. Other (please specify)

[Answer]:

A

## H14 — Reanudación de sesión (Journey 3)

**Evidencia.** J3 exige retener el estado en Redis, un *snapshot* en PostgreSQL y un modal de
reanudación. S8 no lo prioriza. El plan (§4) exige que User Stories cubra J3.

Question: ¿Qué prioridad tiene la reanudación?

A. MUST: el estado de sesión se persiste en PostgreSQL en cada turno y la sesión se reanuda tras la desconexión **(Recomendada)**
B. SHOULD.
C. WON'T: J3 queda como mejora futura.
X. Other (please specify)

[Answer]:

A

## H15 — «Marco de verdad» en variables de entorno vs. en `pgvector`

**Evidencia.**
- S12 R7: el «marco de verdad» sintético se inyecta «de solo lectura en variables de entorno inmutables».
- CU1 y S13 lo cargan el analista y la base `pgvector`.
- S13 §3 dice que los secretos se inyectan «en tiempo de compilación», lo que contradice el uso de Kubernetes Secrets en tiempo de ejecución.

Question: ¿Cómo se corrige?

A. R7: solo el *system prompt* va en configuración inmutable (ConfigMap de solo lectura); el marco de verdad vive en `pgvector` con permisos de solo lectura para el juez. S13: secretos «en tiempo de ejecución» **(Recomendada)**
B. Se mantiene el texto actual.
X. Other (please specify)

[Answer]:

A

## H16 — Protocolo de permutación (doble llamada) en CPU

**Evidencia.** S11-C exige evaluar cada incongruencia «compleja» dos veces, invirtiendo el orden.
En CPU duplica la latencia de 8–12 s, y «compleja» no está definida.

Question: ¿Qué alcance tiene el *swapping*?

A. MUST en la evaluación offline del Golden Dataset y SHOULD en línea, asíncrono, sin bloquear la interfaz (S6 P2) **(Recomendada)**
B. MUST en línea para toda alerta.
C. Solo en la evaluación offline.
X. Other (please specify)

[Answer]:

A

## H17 — Autenticación y roles de la consola

**Evidencia.** CU1 y J1 dicen «inicia sesión» y «accede de manera segura». J2 tiene un rol de
administrador. El PRD no define mecanismo de autenticación ni roles, aunque AUTONOMIA-03 exige
registrar **quién** consolidó.

Question: ¿Qué se exige en el MVP?

A. Inicio de sesión local con usuario y contraseña (hash), dos roles (`analista`, `admin`) y la identidad registrada en cada cambio de estado de alerta y en la consolidación **(Recomendada)**
B. Integración con un IdP (OIDC/Keycloak) en el clúster.
C. Sin autenticación: un único analista implícito y su nombre configurado.
X. Other (please specify)

[Answer]:

A

## H18 — Composición del Golden Dataset y evaluadores

**Evidencia.**
- S11 §1 pide 10 transcripciones «balanceadas» entre verdaderas y con discrepancias sembradas, sin número exacto ni número de escenarios de control.
- S11 §2 pide «dos analistas» para el Likert de CoT sin decir quiénes.

Question: ¿Cómo se fija el Golden Dataset?

A. Un escenario de control sintético; 10 transcripciones: 4 alineadas y 6 con discrepancias sembradas (2 de fecha, 2 de lugar, 2 de rol), más 1 caso de Hecho No Documentado (J4). Los evaluadores Likert son el autor y un par del curso **(Recomendada)**
B. Dos escenarios con 5 transcripciones cada uno, misma proporción.
C. Se deja como está y lo decide Requirements Analysis.
X. Other (please specify)

[Answer]:

A

## H19 — Cifras mal atribuidas o sin respaldo en `research/`

Verificado contra el texto de `research/` (búsqueda literal):

| Afirmación | Dónde | Lo que dice la fuente |
|---|---|---|
| Umbral de vacilación «0.4166» [19] | PRD CU4 | No aparece en Zhou et al. |
| «Picos de vacilación de 0.78» [19] | PRD J4 | En Zhou et al., 0.72–0.78 es el **AUC de SVM** de otro estudio, no una medida de vacilación |
| Sesgo de posición «hasta el 53.8 %» [18] | PRD S10 §3 | No aparece en Zheng et al. |
| Sesgo de posición «hasta el 75 % en modelos comerciales» | PRD S11-C | En Zheng et al., el 75 % es el acuerdo de humanos con los juicios de GPT-4 |
| Fuga de preferencias «27.9 % en promedio» | PRD S11-B | Li et al. reportan promedios de 19.3 % y 23.6 %; 27.9 solo aparece en celdas de tabla |
| Likert > 4.5/5 «emulando SDD-LawLLM» | PRD S11 §2 | No hay escala Likert en Ma et al. |
| Línea base MTTV «30 min a varias horas» [16] | PRD S10 | La cifra es de codificación de preguntas, no de cotejo (ver H13) |
| «Reduciendo los costos hasta en un 60 %» | PRD S12 R8 | Sin cita |
| «Más de 9 millones de víctimas» [2]/[3] | `critica.md`, `mercado.md` | No aparece en los informes CNMH del corpus |
| LieXBerta «demuestra de manera categórica… mejor indicador para detectar la mentira» | `overview.md` §4 | El paper reporta una mejora; «categórica» y «mentira» contradicen el vocabulario neutral de S6 P1 |

Verificadas y correctas: 87.50 % / 87.13 % / +6.5 % (LieXBerta), 351 920 muestras, 95 % (κ .93) y
98 % (κ .97) (Szojka), error de formato del 22.5 % al 78.8 % y consistencia del 65 % (Zheng),
«cerca de 14 000 entrevistas» (CEV).

Question: ¿Cómo se corrigen estas cifras?

A. Se corrige cada una en el original: se reemplaza por el dato real de la fuente cuando existe, y si no, se elimina el número o se marca `[VERIFICAR]` en el texto. El vocabulario de `overview.md` §4 se neutraliza **(Recomendada)**
B. Solo se marcan con `[VERIFICAR]`, sin cambiar el texto.
C. Se dejan como están.
X. Other (please specify)

[Answer]:

A

## Fuera de esta auditoría

- **COGS `[INTERNO]` del PVB §7.** Son estimaciones propias declaradas como tales y no afectan a Inception. Se dejan.
- **Plan por módulos (S13).** Ubica los módulos 4–5 en las semanas 6–9, ya transcurridas. Delivery Planning debe ordenar los Bolts según los módulos 6–8 (plan §4). No requiere cambiar el PRD.
