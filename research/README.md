# Research — corpus documental de Veridicus

Papers, informes y normas citados por [`docs/pvb.md`](../docs/pvb.md), convertidos de PDF a Markdown para poder consultarlos, citarlos y usarlos como fuente dentro del repositorio.

Cada documento conserva el texto y las tablas del PDF original e incluye separadores `------------------------- PAGINA n --------------------------` que corresponden a la **página física del PDF**, de modo que cualquier cita puede señalar la página exacta; los documentos convertidos desde DOCX no los llevan, porque un DOCX no tiene paginación fija. Al inicio de cada archivo hay un bloque con su número de referencia en `pvb.md`, la cita bibliográfica completa y las secciones del Product Vision Board que lo invocan.

---

## Cómo mantener este README

**Al agregar un documento nuevo a `research/`, hay que agregarle aquí su ficha, con este formato exacto:**

```markdown
#### Nombre legible del documento

- **Ruta relativa:** [`carpeta-tematica/Nombre_Del_Archivo.md`](carpeta-tematica/Nombre_Del_Archivo.md)
- **Fecha:** fecha de publicación del documento original
- **Referencias:** `pvb.md [n]` · `critica.md [n]` — usar `—` donde ese documento no lo cite
- **Resumen:** de qué trata y por qué está en el corpus. **Máximo tres líneas, en español.**
```

Reglas:

1. **Nombre del archivo:** solo `A-Z`, `a-z`, `0-9` y `_`. Sin tildes, espacios ni símbolos. Máximo 60 caracteres. Debe reflejar el título real del documento, no el nombre del PDF de origen.
2. **Ubicación:** dentro de una de las carpetas temáticas listadas abajo. Si ninguna aplica, se crea una nueva con el prefijo numérico siguiente y se documenta su propósito en el índice.
3. **Fecha:** la del documento original, no la de descarga o conversión. Si solo se conoce el año, basta el año.
4. **Resumen:** tres líneas como máximo (unos **330 caracteres**), en español y en prosa. Debe decir qué contiene el documento y qué aporta al proyecto, sin copiar el abstract literalmente.
5. **Orden:** las fichas van agrupadas por carpeta y, dentro de cada carpeta, en el orden en que aparecen en el índice.
6. **Separadores de página:** los documentos convertidos desde PDF los llevan; los convertidos desde DOCX no, y deben indicarlo en su nota de cabecera para que nadie cite una página inexistente.

---

## Índice

- [`01-marco-legal-colombiano/`](#01-marco-legal-colombiano) — Normativa colombiana que define quién es víctima y qué debe repararse, y el régimen de protección de datos que rige el tratamiento de sus testimonios. Es el marco de verdad legal. (3 documentos)
- [`02-memoria-historica-y-conflicto/`](#02-memoria-historica-y-conflicto) — Corpus documental e institucional del conflicto armado: la fuente del «marco de verdad» fáctico. (5 documentos)
- [`03-llm-as-a-judge/`](#03-llm-as-a-judge) — Metodología de evaluación con LLM como juez, y sus sesgos, contaminaciones y limitaciones. (4 documentos)
- [`04-analisis-forense-del-testimonio/`](#04-analisis-forense-del-testimonio) — Técnicas de análisis de entrevistas, detección de engaño y medición de la calidad del testimonio. (4 documentos)
- [`05-etica-sesgos-y-riesgos/`](#05-etica-sesgos-y-riesgos) — Restricciones éticas, sesgos de los modelos y protección de las víctimas frente a la revictimización. (3 documentos)
- [`06-documentacion-propia/`](#06-documentacion-propia) — Documentación del propio trabajo de grado, que `pvb.md` y `critica.md` citan como fuente del proyecto. (3 documentos)

---

## Documentos

### `01-marco-legal-colombiano/`

Normativa colombiana que define quién es víctima y qué debe repararse. Es el marco de verdad legal.

#### Ley 1448 de 2011 — Ley de Víctimas y Restitución de Tierras

- **Ruta relativa:** [`01-marco-legal-colombiano/Ley_1448_de_2011_Victimas_y_Restitucion_de_Tierras.md`](01-marco-legal-colombiano/Ley_1448_de_2011_Victimas_y_Restitucion_de_Tierras.md)
- **Fecha:** 10 de junio de 2011
- **Referencias:** `pvb.md [5]` · `critica.md —`
- **Resumen:** Establece las medidas de atención, asistencia y reparación integral a las víctimas del conflicto armado interno. Define quién es víctima, crea el Registro Único de Víctimas y fija el deber de memoria del Estado. Es la norma que crea el CNMH (art. 146) y de la que dependen todos los fallos y reformas posteriores.

#### Ley 2421 de 2024 — Modificación de la Ley 1448

- **Ruta relativa:** [`01-marco-legal-colombiano/Ley_2421_de_2024_Modifica_Ley_1448_de_2011.md`](01-marco-legal-colombiano/Ley_2421_de_2024_Modifica_Ley_1448_de_2011.md)
- **Fecha:** 22 de agosto de 2024
- **Referencias:** `pvb.md [6]` · `critica.md —`
- **Resumen:** Modifica la Ley 1448 de 2011 y amplía las disposiciones sobre reparación, atención y asistencia a las víctimas. Introduce la obligación de coordinación interinstitucional y ajusta artículos clave del régimen de reparación. Es la actualización normativa vigente que debe reflejar el marco de verdad legal.

#### Ley 1581 de 2012 — Ley Estatutaria de Protección de Datos Personales

- **Ruta relativa:** [`01-marco-legal-colombiano/Ley_1581_de_2012_Proteccion_de_Datos_Personales.md`](01-marco-legal-colombiano/Ley_1581_de_2012_Proteccion_de_Datos_Personales.md)
- **Fecha:** 17 de octubre de 2012
- **Referencias:** `pvb.md —` · `critica.md —` · `icp.md [22]` · `mercado.md [22]` · `specs/prd.md [22]`
- **Resumen:** Ley estatutaria que desarrolla el derecho constitucional de hábeas data y fija los principios, deberes y sanciones para el tratamiento de datos personales en Colombia, incluida la prohibición de transferencia a países sin protección adecuada (art. 26). Es la norma que sustenta el veto de confianza del CISO/SRE Lead y el argumento de soberanía de datos frente a nubes públicas comerciales en `icp.md`, `mercado.md` y `prd.md`; antes de este documento esas menciones no tenían fuente verificable en el corpus.

### `02-memoria-historica-y-conflicto/`

Corpus documental e institucional del conflicto armado: la fuente del «marco de verdad» fáctico.

#### Hay futuro si hay verdad — Informe Final de la Comisión de la Verdad (Tomo 2)

- **Ruta relativa:** [`02-memoria-historica-y-conflicto/CEV_Informe_Final_Hallazgos_y_Recomendaciones_2022.md`](02-memoria-historica-y-conflicto/CEV_Informe_Final_Hallazgos_y_Recomendaciones_2022.md)
- **Fecha:** 2022
- **Referencias:** `pvb.md [3]` · `critica.md —`
- **Resumen:** Tomo de hallazgos y recomendaciones del Informe Final de la Comisión de la Verdad, dirigido por Carlos Martín Beristain. Consolida las conclusiones sobre el conflicto armado colombiano y las recomendaciones para la no repetición. Obra de dominio público; es la fuente documental primaria del marco de verdad.

#### Centro Nacional de Memoria Histórica — Informe de Gestión 2021

- **Ruta relativa:** [`02-memoria-historica-y-conflicto/CNMH_Informe_de_Gestion_2021.md`](02-memoria-historica-y-conflicto/CNMH_Informe_de_Gestion_2021.md)
- **Fecha:** vigencia 2021
- **Referencias:** `pvb.md —` · `critica.md [1]`
- **Resumen:** Rendición de cuentas anual del CNMH sobre la vigencia 2021, entidad creada por el artículo 146 de la Ley 1448. Detalla la ejecución misional por direcciones —Museo de la Memoria, Archivo de DD. HH., Acuerdos de la Verdad— y la gestión administrativa. Permite dimensionar el acopio real de testimonios y archivos.

#### Centro Nacional de Memoria Histórica — Informe de Gestión 2024

- **Ruta relativa:** [`02-memoria-historica-y-conflicto/CNMH_Informe_de_Gestion_2024.md`](02-memoria-historica-y-conflicto/CNMH_Informe_de_Gestion_2024.md)
- **Fecha:** vigencia 2024
- **Referencias:** `pvb.md [2]` · `critica.md [2]`
- **Resumen:** Rendición de cuentas anual del CNMH sobre la vigencia 2024, con la misma estructura por direcciones misionales y de apoyo. Incluye acopio de archivos, toma de testimonios y su puesta al servicio de la sociedad vía Archivo Virtual. Es el retrato más reciente de la capacidad institucional del CNMH.

#### Modelo semántico y computacional para análisis del conflicto armado en Colombia

- **Ruta relativa:** [`02-memoria-historica-y-conflicto/Patino_Modelo_Semantico_Conflicto_Armado_Colombia_2024.md`](02-memoria-historica-y-conflicto/Patino_Modelo_Semantico_Conflicto_Armado_Colombia_2024.md)
- **Fecha:** 2024
- **Referencias:** `pvb.md —` · `critica.md —`
- **Resumen:** Tesis doctoral (UPF, dir. Mercè Lorente) que propone un modelo semántico y computacional para construir un grafo de conocimiento del conflicto armado colombiano. Aplica PLN y reconocimiento de entidades nombradas sobre un corpus de paz, derechos humanos y memoria, en un dominio sin ontologías ni corpus anotados previos.

#### Construyendo la verdad: minería de texto en el Caso 03 de la JEP

- **Ruta relativa:** [`02-memoria-historica-y-conflicto/Construyendo_la_Verdad_Mineria_de_Texto_Caso_03_JEP.md`](02-memoria-historica-y-conflicto/Construyendo_la_Verdad_Mineria_de_Texto_Caso_03_JEP.md)
- **Fecha:** abril de 2025 (arXiv:2504.04325)
- **Referencias:** `pvb.md [13]` · `critica.md [7]`
- **Resumen:** Analiza las audiencias públicas del Caso 03 de la JEP —los llamados falsos positivos— con minería de texto y modelos de co-ocurrencia semántica. Construye redes de skipgramas y estudia su modularidad para identificar clústeres temáticos. Revela diferencias regionales y por estatus procesal entre víctimas y comparecientes.

### `03-llm-as-a-judge/`

Metodología de evaluación con LLM como juez, y sus sesgos, contaminaciones y limitaciones.

#### Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena

- **Ruta relativa:** [`03-llm-as-a-judge/Judging_LLM_as_a_Judge_MT_Bench_Chatbot_Arena_2023.md`](03-llm-as-a-judge/Judging_LLM_as_a_Judge_MT_Bench_Chatbot_Arena_2023.md)
- **Fecha:** 2023 (NeurIPS)
- **Referencias:** `pvb.md [16]` · `critica.md [9]`
- **Resumen:** Trabajo fundacional sobre el uso de LLM potentes como jueces para evaluar asistentes conversacionales en preguntas abiertas. Documenta y mitiga sus sesgos de posición, verbosidad y autopreferencia, y su razonamiento limitado. Muestra que jueces como GPT-4 superan el 80 % de concordancia con las preferencias humanas.

#### Training an LLM-as-a-Judge Model: Pipeline, Insights, and Practical Lessons

- **Ruta relativa:** [`03-llm-as-a-judge/Training_an_LLM_as_a_Judge_Model_Pipeline_Lessons_2025.md`](03-llm-as-a-judge/Training_an_LLM_as_a_Judge_Model_Pipeline_Lessons_2025.md)
- **Fecha:** abril de 2025 (WWW Companion)
- **Referencias:** `pvb.md [4]` · `critica.md —`
- **Resumen:** Presenta Themis, un LLM juez afinado que entrega evaluaciones sensibles al contexto, con su pipeline de desarrollo. Aporta prompts dependientes del escenario y dos métodos de generación controlada de instrucciones. Es la referencia sobre cómo entrenar un juez propio en vez de usar un modelo genérico.

#### JudgeBlender: Ensembling Automatic Relevance Judgments

- **Ruta relativa:** [`03-llm-as-a-judge/JudgeBlender_Ensembling_Relevance_Judgments.md`](03-llm-as-a-judge/JudgeBlender_Ensembling_Relevance_Judgments.md)
- **Fecha:** abril de 2025 (WWW Companion)
- **Referencias:** `pvb.md [11]` · `critica.md [6]`
- **Resumen:** Propone un marco que combina un ensamble de LLM para producir juicios de relevancia más robustos que los de un modelo único. Ataca los tres problemas de la anotación manual: costo, error humano y sesgo subjetivo. Es la alternativa directa a depender de un solo juez como GPT-4.

#### Preference Leakage: A Contamination Problem in LLM-as-a-judge

- **Ruta relativa:** [`03-llm-as-a-judge/Preference_Leakage_Contamination_in_LLM_as_a_Judge_2025.md`](03-llm-as-a-judge/Preference_Leakage_Contamination_in_LLM_as_a_Judge_2025.md)
- **Fecha:** febrero de 2025 (arXiv:2502.01534)
- **Referencias:** `pvb.md [7]` · `critica.md [3]`
- **Resumen:** Expone la fuga de preferencias: una contaminación del LLM-as-a-judge que aparece cuando el modelo que sintetiza los datos y el que evalúa están emparentados. Define tres formas de parentesco —mismo modelo, herencia y misma familia— y mide su efecto. Es el fundamento técnico para separar generador y evaluador en el diseño.

### `04-analisis-forense-del-testimonio/`

Técnicas de análisis de entrevistas, detección de engaño y medición de la calidad del testimonio.

#### LieXBerta: A deception detection model by using integrated LLM with emotion features

- **Ruta relativa:** [`04-analisis-forense-del-testimonio/Deception_Detection_Model_LLM_Emotion_Features_2025.md`](04-analisis-forense-del-testimonio/Deception_Detection_Model_LLM_Emotion_Features_2025.md)
- **Fecha:** 2025 (Scientific Reports 15:32135)
- **Referencias:** `pvb.md [17]` · `critica.md [10]`
- **Resumen:** Propone LieXBerta, un modelo de detección de engaño que extrae rasgos emocionales con RoBERTa desde textos de interrogatorio. Combina esos rasgos con variables faciales y de acción en un clasificador XGBoost, superando a los modelos base sin emoción. Es la base metodológica y empírica del componente forense de Veridicus.

#### Automated Question Type Coding of Forensic Interviews and Trial Testimony

- **Ruta relativa:** [`04-analisis-forense-del-testimonio/Automated_Question_Type_Coding_Forensic_Interviews_2025.md`](04-analisis-forense-del-testimonio/Automated_Question_Type_Coding_Forensic_Interviews_2025.md)
- **Fecha:** 2025 (Law and Human Behavior 49(2))
- **Referencias:** `pvb.md [14]` · `critica.md —`
- **Resumen:** Evalúa la codificación automática del tipo de pregunta en entrevistas forenses y testimonios por abuso sexual infantil. El tipo de pregunta es la medida estándar de calidad de una entrevista, pero codificarla a mano es lento. Valida que un modelo de lenguaje alcanza fiabilidad comparable a la humana.

#### When Time Matters: Recall Techniques, Educational Levels and Witness Testimony Quality

- **Ruta relativa:** [`04-analisis-forense-del-testimonio/When_Time_Matters_Recall_Techniques_Witness_Testimony.md`](04-analisis-forense-del-testimonio/When_Time_Matters_Recall_Techniques_Witness_Testimony.md)
- **Fecha:** 8 de febrero de 2025 (Information 16(2))
- **Referencias:** `pvb.md [12]` · `critica.md —`
- **Resumen:** Estudia cómo el tiempo dedicado a la reconstrucción mental y al recuerdo libre, y el nivel educativo, afectan la calidad del testimonio. Combina anotación experta de contenido con rasgos lingüísticos extraídos automáticamente. Trabaja sobre un corpus de 96 testimonios en español, lo que lo hace aplicable al caso colombiano.

#### SDD-LawLLM: Synthetic Data-Driven Fine-Tuning for Intelligent Legal Systems

- **Ruta relativa:** [`04-analisis-forense-del-testimonio/SDD_LawLLM_Synthetic_Data_Fine_Tuning_Legal_LLM_2025.md`](04-analisis-forense-del-testimonio/SDD_LawLLM_Synthetic_Data_Fine_Tuning_Legal_LLM_2025.md)
- **Fecha:** 13 de febrero de 2025 (Electronics 14(4))
- **Referencias:** `pvb.md [8]` · `critica.md [4]`
- **Resumen:** Mejora la capacidad de respuesta jurídica de un LLM (Qwen-7B) mediante síntesis de datos y generación aumentada por recuperación. Incorpora cadenas de razonamiento explícitas (CoT) para elevar la transparencia y la fiabilidad, no solo la exactitud. Sustenta el requisito de explicabilidad auditable del sistema.

### `05-etica-sesgos-y-riesgos/`

Restricciones éticas, sesgos de los modelos y protección de las víctimas frente a la revictimización.

#### On the Dangers of Stochastic Parrots: Can Language Models Be Too Big?

- **Ruta relativa:** [`05-etica-sesgos-y-riesgos/On_the_Dangers_of_Stochastic_Parrots_2021.md`](05-etica-sesgos-y-riesgos/On_the_Dangers_of_Stochastic_Parrots_2021.md)
- **Fecha:** 2021 (FAccT)
- **Referencias:** `pvb.md [1]` · `critica.md —`
- **Resumen:** Cuestiona si se ha ponderado lo suficiente el riesgo de construir modelos de lenguaje cada vez más grandes. Analiza sus costos ambientales y financieros, los sesgos hegemónicos heredados de los datos de entrenamiento y el peligro de confundir fluidez con comprensión. Es la referencia canónica sobre sesgo y daño en LLM.

#### Leveraging Victim Voices: NLP en narrativas de trauma

- **Ruta relativa:** [`05-etica-sesgos-y-riesgos/Leveraging_Victim_Voices_NLP_Trauma_Narratives_2024.md`](05-etica-sesgos-y-riesgos/Leveraging_Victim_Voices_NLP_Trauma_Narratives_2024.md)
- **Fecha:** 2024 (Journal of Victimology & Victim Justice 7(2))
- **Referencias:** `pvb.md [10]` · `critica.md [5]`
- **Resumen:** Sostiene que la lucha contra la trata y la explotación sexual infantil fracasa por no involucrar de verdad a las víctimas. Propone compartir datos y usar PLN para analizar sus narrativas sin someterlas a nuevas entrevistas. Fundamenta los principios de no revictimización y de evitar la fatiga de entrevista.

#### Recomendación sobre la Ética de la Inteligencia Artificial (UNESCO)

- **Ruta relativa:** [`05-etica-sesgos-y-riesgos/UNESCO_Recomendacion_Etica_de_la_IA_2021.md`](05-etica-sesgos-y-riesgos/UNESCO_Recomendacion_Etica_de_la_IA_2021.md)
- **Fecha:** noviembre de 2021
- **Referencias:** `pvb.md [15]` · `critica.md [8]`
- **Resumen:** Instrumento normativo adoptado por la Conferencia General de la UNESCO en su 41ª reunión (París, noviembre de 2021). Fija valores, principios y acciones para un uso de la IA conforme al derecho internacional de los derechos humanos. Es el marco de cumplimiento que condiciona el despliegue soberano de datos sensibles de víctimas.

### `06-documentacion-propia/`

Documentación del propio trabajo de grado, que `pvb.md` y `critica.md` citan como fuente del proyecto.

#### Diálogos para la Memoria — Propuesta de Trabajo de Grado (MINSC, V2)

- **Ruta relativa:** [`06-documentacion-propia/Propuesta_TG_Dialogos_para_la_Memoria_MINSC_V2.md`](06-documentacion-propia/Propuesta_TG_Dialogos_para_la_Memoria_MINSC_V2.md)
- **Fecha:** 7 de noviembre de 2025
- **Referencias:** `pvb.md [19]` · `critica.md [12]`
- **Resumen:** Propuesta de trabajo de grado que origina el proyecto: un agente conversacional basado en LLM que caracteriza el grado de participación (víctima, victimario o testigo) de un actor del conflicto armado colombiano. Fija los cinco objetivos específicos, el problema y el alcance que Veridicus implementa.

#### Estado del arte — Diálogos para la Memoria

- **Ruta relativa:** [`06-documentacion-propia/Estado_del_Arte_Dialogos_para_la_Memoria.md`](06-documentacion-propia/Estado_del_Arte_Dialogos_para_la_Memoria.md)
- **Fecha:** 7 de octubre de 2025
- **Referencias:** `pvb.md —` · `critica.md —`
- **Resumen:** Revisión del estado del arte del proyecto: marco conceptual del conflicto armado, definiciones legales de víctima, victimario y testigo, justicia transicional, aproximación tecnológica y consideraciones éticas. Es el puente entre el corpus documental y las decisiones de diseño.

#### Hoja de Ruta de Ejecución: Diálogos para la Memoria y Veridicus (2026-2027)

- **Ruta relativa:** [`06-documentacion-propia/Hoja_de_Ruta_Dialogos_para_la_Memoria_2026_2027.md`](06-documentacion-propia/Hoja_de_Ruta_Dialogos_para_la_Memoria_2026_2027.md)
- **Fecha:** 21 de agosto de 2026
- **Referencias:** `pvb.md [19]` · `critica.md [12]`
- **Resumen:** Cronograma integrado de TG1 y TG2 bajo metodología Design Science Research, de agosto de 2026 a junio de 2027. Desglosa cuatro fases en actividades, hitos y entregables, e indica en qué mes entra cada fuente del corpus. Comparte referencia bibliográfica con la propuesta de trabajo de grado.

---

## Notas sobre el corpus

- Las bibliografías de `pvb.md` y `critica.md` se depuraron: cada una lista solo lo que cita, renumerado de forma consecutiva. Por eso un mismo documento lleva números distintos en cada uno.
- La referencia `pvb.md [19]` / `critica.md [12]` (Reyes Palacio) cubre **dos documentos** del corpus: la propuesta de trabajo de grado y la hoja de ruta de ejecución.
- La hoja de ruta conserva su bibliografía propia de 21 entradas, de las cuales **6 no se citan** en su texto: Ley 2421, Patiño, Solà-Sales, Sosa, Szojka y Zheng. Se dejó íntegra por ser un documento fuente; depurarla es decisión del autor.
- **La tesis de Patiño ya no la cita `pvb.md` ni `critica.md`** (por eso su ficha muestra `—` en ambas columnas), pero sí la citan `overview.md` (sección 2, ontologías y grafos de conocimiento) y `mercado.md`. Esas dos referencias no se reflejan en la columna «Referencias» de esta ficha porque ese campo solo rastrea `pvb.md`/`critica.md`; si se necesita trazabilidad completa, hay que ampliar la convención de fichas a los demás documentos de `docs/`.
- Tres referencias no tienen documento aquí porque no son papers: Moreno (artículo de divulgación), y Fariza (repositorio de la asignatura). En `pvb.md` son `[9]` y `[18]`; en `critica.md`, `[11]`.
- **Ley 1581 de 2012** no proviene del corpus `1-papersMD` como el resto de los documentos: se añadió después, a partir de un PDF oficial descargado del Gestor Normativo EVA y suministrado directamente por el usuario, para respaldar las menciones a esa ley que ya existían en `icp.md`, `mercado.md` y `prd.md` sin ninguna fuente citable.
- El corpus convertido de `1-papersMD` tiene 27 documentos. Los que ningún documento cita —los cinco fallos de la Corte Constitucional sobre la Ley 1448, los informes de gestión del CNMH 2012, 2022 y 2023, y el cookbook de Hugging Face sobre LLM-as-a-judge— no se copiaron, pero están disponibles si el Product Vision Board llega a necesitarlos.

