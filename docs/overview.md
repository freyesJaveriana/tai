# Panorama del Dominio: Veridicus y el Procesamiento del Conflicto Colombiano
*Módulo 3 — Documento de Contexto General (`docs/overview.md`)*

Este documento presenta el panorama del dominio y la fundamentación teórica para **Veridicus: Módulo de Entrevista y Detección de Incongruencias Forenses** [21]. Analiza los cruces interdisciplinarios entre la justicia transicional, el procesamiento del lenguaje natural (PLN), la psicología del testimonio y los marcos ético-legales que rigen la memoria histórica en Colombia [4, 10, 11, 12, 14].

---

## 1. EL RETO DEL ANÁLISIS DE TESTIMONIOS EN LA JUSTICIA TRANSICIONAL

La justicia transicional en contextos de posconflicto se fundamenta en los pilares innegociables de **Verdad, Justicia, Reparación y No Repetición** [4, 15]. El esclarecimiento de más de seis décadas de conflicto armado interno en Colombia [12] ha demandado la recolección masiva de testimonios. Un ejemplo de este esfuerzo colosal fue la Comisión de la Verdad de Colombia (CEV), la cual conversó con más de 30.000 personas y compiló un corpus de más de 14.000 entrevistas de víctimas, comparecientes y testigos [4, 21].

### La problemática humana y operativa:
1. **Inviabilidad del análisis manual:** El volumen documental generado por instituciones como la CEV [4], la Jurisdicción Especial para la Paz (JEP) [15] y el Centro Nacional de Memoria Histórica (CNMH) [2, 3] es tan inmenso que su análisis manual exhaustivo para categorizar responsabilidades o extraer patrones geográficos es logísticamente imposible y propenso a inconsistencias por el sesgo subjetivo de los evaluadores humanos [12, 21].
2. **El costo emocional del analista:** Los investigadores judiciales y analistas de memoria histórica sufren de un profundo desgaste psicológico, fatiga cognitiva y costo emocional derivado de la lectura y escucha sistemática de miles de relatos altamente angustiosos sobre graves violaciones a los derechos humanos [11, 12].
3. **La fatiga de entrevista del declarante:** Las víctimas a menudo son sometidas a múltiples interrogatorios repetitivos por parte de la policía, organizaciones sociales, fiscalías y psicólogos forenses, reviviendo su trauma en cada turno conversacional [11]. El procesamiento automático de textos ya grabados ayuda a extraer necesidades y verdades sin someter al declarante a nuevas sesiones de entrevistas exhaustivas [11].

---

## 2. ESTRUCTURACIÓN SEMÁNTICA Y ONTOLÓGICA DEL CONFLICTO

Para que las tecnologías del lenguaje analicen de manera objetiva y escalable las narrativas del conflicto, es necesario contar con estructuras conceptuales claras de representación del conocimiento. 

### Ontologías y Sistemas de Clases:
En su investigación doctoral, Patiño (2024) demostró que el conflicto armado colombiano constituye un dominio de especialidad con fronteras lingüísticas transdisciplinares [12]. Para estructurar computacionalmente este dominio, se requiere definir ontologías (estructuras que detallan conceptos y sus relaciones lógicas) y grafos de conocimiento (mapas lógicos interconectados) [12].

En el experimento de Veridicus, adoptamos las seis categorías analíticas consolidadas en el estado del arte [12, 21]:
*   **VIO (Hechos de Violencia):** Tipificación de la modalidad de agresión (ej. masacres, desapariciones forzadas, secuestros).
*   **ARM (Actor Armado):** Grupos involucrados en la confrontación (ej. guerrillas, agentes estatales, paramilitares).
*   **AFE (Afectación):** Daños individuales, colectivos o ambientales provocados por el hecho violento.
*   **ORG (Organizaciones):** Entidades institucionales o de derechos humanos que intervienen en el proceso.
*   **PER (Personas):** Actores civiles, comparecientes o líderes sociales, caracterizando sus condiciones étnicas, de género o de edad.
*   **GEO (Localizaciones Geográficas):** Coordenadas territoriales específicas del conflicto, incluyendo veredas, ríos y parajes.

### Heterogeneidad Narrativa y Modularidad Discursiva:
La investigación semántica sobre el Caso 03 de la JEP (falsos positivos) realizada por Sosa et al. (2025) demuestra, mediante análisis de redes lingüísticas y de co-ocurrencia semántica, que las narrativas del conflicto no son uniformes [15]. Los relatos presentan variaciones significativas según la región (ej. Antioquia vs. Costa Caribe) y el rol del participante (víctimas vs. comparecientes) [15]. 

El análisis de modularidad (una medida de la claridad temática de los grupos lingüísticos en una red de palabras) revela que las víctimas tienden a estructurar sus relatos alrededor del daño, la memoria del ser querido y el dolor [15], mientras que los comparecientes militares enfocan su lenguaje en la estructura jerárquica castrense y el contexto institucional operativo [15]. Esto justifica la necesidad de que Veridicus cuente con un modelo especializado en desambiguación y análisis del español colombiano forense.

---

## 3. PROCESAMIENTO DEL LENGUAJE Y ANÁLISIS DE PREGUNTAS FORENSES

La interacción conversacional entre el sistema y el compareciente no puede dejarse al libre albedrío de un bot conversacional común. Debe imitar las mejores prácticas de una entrevista forense o judicial.

### El modelo de clasificación conversacional:
Szojka, Yashraj y Lyon (2025) entrenaron un modelo basado en la arquitectura de red neuronal Transformers (**RoBERTa-base**) con más de **350.000 declaraciones** de entrevistas reales sobre abuso sensible [16]. Su objetivo fue clasificar automáticamente los tipos de preguntas formuladas durante los interrogatorios:
1.  **Invitaciones (Invitations):** Preguntas abiertas que fomentan la narración libre y espontánea (ej. *«Cuénteme qué pasó ese día»*).
2.  **Preguntas de información (Wh-questions):** Preguntas de exploración de datos de modo, tiempo y lugar (ej. *«¿Cuándo ocurrió? ¿Dónde estaban?»*).
3.  **Preguntas de opción cerrada (Option-posing):** Preguntas restrictivas que limitan la autonomía del relato (ej. *«¿El camión era rojo o verde?»*).
4.  **No-preguntas (Nonquestions):** Comentarios o afirmaciones del entrevistador que no demandan respuesta directa.

Este estudio demostró que el modelo automatizado de IA alcanzó un **98% de nivel de concordancia** con evaluadores humanos expertos [16], superándolos en consistencia al detectar y corregir sesgos y omisiones que se produjeron en la codificación manual inicial [12, 16]. Esto provee a **Veridicus** del sustento empírico para que su agente conversacional evalúe dinámicamente si está formulando preguntas neutrales (invitaciones libres) o si está induciendo respuestas mediante preguntas cerradas (opción forzada).

---

## 4. PSICOLOGÍA DEL TESTIMONIO, ESTILOMETRÍA Y DETECCIÓN DE INCONGRUENCIAS

El núcleo funcional de Veridicus es evaluar la consistencia del relato oral frente a un marco de hechos inmutables. Esto se basa en las teorías de la psicología del testimonio y la lingüística clínica.

### El papel del tiempo de reconstrucción mental y narración:
El estudio empírico de Solà-Sales et al. (2025) sobre el impacto de las técnicas de memoria en testimonios en español arrojó hallazgos cruciales para el diseño del sistema [14]:
*   **Reconstrucción Mental del Contexto (MRC):** El tiempo que el declarante se toma para recrear mentalmente la escena antes de hablar correlaciona positivamente con la densidad de información y la riqueza léxica de su testimonio [14].
*   **Narración Libre (Free Recall - FR):** Una mayor duración de la narración espontánea y no inducida reduce de manera sustancial las lagunas de memoria y autocríticas motivacionales [14].
*   **La naturaleza de los errores:** Los humanos tienden a cometer más **errores de distorsión** (modificar de forma involuntaria un detalle existente, lo cual requiere menor esfuerzo cognitivo) que **errores de comisión** (inventar de forma deliberada un hecho completamente inexistente) [14]. Además, las inconsistencias involuntarias suelen darse en detalles periféricos, mientras que los hechos centrales se recuerdan con alta precisión [14].

Esto fundamenta por qué **Veridicus** no debe catalogar cualquier desajuste temporal o cambio de nombre menor como "engaño deliberado", sino como una fluctuación cognitiva natural o de trauma, enfocando la búsqueda de mentiras exclusivamente en incongruencias de hechos centrales inmutables [11, 14].

### Detección estilométrica y emocional con LieXBerta:
Zhou et al. (2025) proponen el modelo **LieXBerta** para solucionar el problema del sesgo subjetivo y la fatiga en interrogatorios prolongados mediante IA [19]. Su modelo demuestra que las personas que engañan deliberadamente bajo escenarios de alta presión psicológica sufren de una carga cognitiva severa que filtra patrones emocionales específicos dentro del texto [19].

El modelo extrae la intensidad emocional en **10 dimensiones lingüísticas** a través de RoBERTa y las procesa con un clasificador XGBoost optimizado [19]. Bajo este diseño, el rendimiento del sistema alcanza una **precisión de prueba del 87.50%** y un **F1-score del 87.13%** [19], demostrando de manera categórica que la integración de la tristeza, la ira y la vacilación lingüística es el mejor indicador semántico para detectar la mentira en el texto de los testimonios reales [19].

---

## 5. MARCOS NORMATIVOS Y ÉTICOS NACIONALES E INTERNACIONALES

El despliegue de cualquier sistema de inteligencia artificial en el sector de justicia y derechos humanos en Colombia debe responder a estrictas fronteras éticas y normativas:

1.  **Ley de Víctimas y Restitución de Tierras (Ley 1448 de 2011):** Define formalmente las medidas de atención, asistencia y reparación integral a las víctimas del conflicto armado interno [6]. El software de Veridicus debe alinearse conceptualmente con estas categorías legales para que sus análisis sean de utilidad procesal [12, 21].
2.  **Ley 2421 de 2024:** Amplía y actualiza el régimen de reparación para las víctimas, estableciendo las excepciones, marcos jurídicos y priorizaciones de asistencia integral de los comparecientes ante el estado [7].
3.  **Directrices Éticas de la UNESCO (2021):** El procesamiento de testimonios sensibles exige la implementación estricta de principios de **Privacidad, Soberanía de Datos, Mitigación de Sesgos y Transparencia Explicable** [17]. Cualquier sistema que transmita grabaciones confidenciales a nubes públicas comerciales de terceros viola estas directrices de forma flagrante, justificando por qué Veridicus debe desplegarse localmente bajo la infraestructura inmutable de **Kubernetes** [17, 20].

---

## REFERENCIAS BIBLIOGRÁFICAS

[1] Bender, E. M., McMillan-Major, A., Gebru, T., & Shmitchell, S. (2021). *On the dangers of stochastic parrots: Can language models be too big?* FAccT 2021 - Proceedings of the 2021 ACM Conference on Fairness, Accountability, and Transparency, 610-623. https://doi.org/10.1145/3442188.3445922
[2] Centro Nacional de Memoria Histórica (CNMH). (2021). *Informe de Gestión 2021*. CNMH, Bogotá, Colombia.
[3] Centro Nacional de Memoria Histórica (CNMH). (2024). *Informe de Gestión 2024*. CNMH, Bogotá, Colombia.
[4] Comisión para el Esclarecimiento de la Verdad, la Convivencia y la No Repetición. (2022). *Hay Futuro si hay Verdad—Informe Final*. Comisión de la Verdad, Bogotá, Colombia.
[5] Hu, R., Cheng, Y., Shi, X., Lin, W., Meng, L., Xia, J., & Zong, Y. (2025). *Training an LLM-as-a-Judge Model: Pipeline, Insights, and Practical Lessons*. WWW Companion 2025 - Companion Proceedings of the ACM Web Conference 2025, 228-237. https://doi.org/10.1145/3701716.3715265
[6] Ley 1448/2011 (2011). *Ley de Víctimas y Restitución de Tierras*. Congreso de la República de Colombia.
[7] Ley 2421/2024 (2024). *Modificación y ampliación de medidas de reparación*. Congreso de la República de Colombia.
[8] Li, D., Sun, R., Huang, Y., Zhong, M., Jiang, B., Han, J., Zhang, X., Wang, W., & Liu, H. (2025). *Preference Leakage: A Contamination Problem in LLM-as-a-judge*. arXiv preprint arXiv:2502.01534.
[9] Ma, H., Lu, Y., Feng, J., Zhang, H., Xiao, Z., & Yu, J. (2025). *SDD-LawLLM: Advancing Intelligent Legal Systems Through Synthetic Data-Driven Fine-Tuning of Large Language Models*. Electronics (Switzerland), 14(4). https://doi.org/10.3390/electronics14040742
[10] Moreno, L. G. (2024). *Inteligencia Artificial para entender el conflicto colombiano*. Pesquisa Javeriana, Pontificia Universidad Javeriana. https://www.javeriana.edu.co/pesquisa/inteligencia-artificial-conflicto/
[11] Muraszkiewicz, J., & Cadman, J. (2024). *Leveraging Victim Voices: Unveiling True Needs Through Natural Language Processing in Trauma Narratives*. Journal of Victimology & Victim Justice, 7(2), 133-144. DOI: 10.1177/25166069241281837
[12] Patiño, A. M. T. (2024). *Modelo semántico y computacional para análisis del conflicto armado en Colombia*. Tesis Doctoral, Universitat Pompeu Fabra, Barcelona.
[13] Rahmani, H. A., Yilmaz, E., Craswell, N., & Mitra, B. (2025). *JudgeBlender: Ensembling Automatic Relevance Judgments*. WWW Companion 2025 - Companion Proceedings of the ACM Web Conference 2025, 1268-1272. https://doi.org/10.1145/3701716.3715536
[14] Solà-Sales, S., Alzetta, C., Moret-Tatay, C., & Dell’Orletta, F. (2025). *When Time Matters: Exploring the Impact of Recall Techniques and Educational Levels on Witness Testimony Quality*. Information, 16(2). https://doi.org/10.3390/info16020079
[15] Sosa, J., Urrego-López, A., Prieto, C., & Camargo-Díaz, E. J. (2025). *Constructing the Truth: Text Mining and Linguistic Networks in Public Hearings of Case 03 of the Special Jurisdiction for Peace (JEP)*. arXiv preprint arXiv:2504.04325.
[16] Szojka, Z. A., Yashraj, S., & Lyon, T. D. (2025). *Automated question type coding of forensic interviews and trial testimony in child sexual abuse cases*. Law and Human Behavior, 49(2), 163-172.
[17] UNESCO. (2021). *Recomendación sobre la Ética de la Inteligencia Artificial*. Organización de las Naciones Unidas para la Educación, la Ciencia y la Cultura.
[18] Zheng, L., Chiang, W.-L., Sheng, Y., Zhuang, S., Wu, Z., Zhuang, Y., Lin, Z., Li, Z., Li, D., Xing, E. P., Zhang, H., Gonzalez, J. E., & Stoica, I. (2023). *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*. arXiv preprint arXiv:2306.05685.
[19] Zhou, C., Zhang, Y., Lin, C., & Zhou, S. (2025). *A deception detection model by using integrated LLM with emotion features*. Scientific Reports, 15(1), 1-19. https://doi.org/10.1038/s41598-025-17741-4
[20] Fariza, L. (2026). *Módulo 2 — AI & Agentic Engineering: Requisitos de Validación*. Universidad Pontificia Javeriana / GitHub Repository. URL: https://github.com/lfarizav/topicos-especiales/tree/main/modulo2
[21] Reyes Palacio, F. (2026). *Ruta de Ejecución y Propuesta de Trabajo de Grado: Diálogos para la Memoria 2026-2027*. Pontificia Universidad Javeriana.
