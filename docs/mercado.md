# Análisis de Mercado y Competencia: Veridicus
*Módulo 3 — Documento de Insumo (`docs/mercado.md`)*

Este documento analiza el entorno de mercado, la competencia y los factores de diferenciación para **Veridicus: Módulo de Entrevista y Detección de Incongruencias Forenses** [21]. En el marco del Módulo 3, este análisis justifica por qué las soluciones existentes de Inteligencia Artificial (IA) comercial no logran resolver las necesidades específicas del sector justicia y de la reconstrucción histórica, abriendo una oportunidad clara para un sistema soberano local [20].

---

## 1. EL VACÍO DEL MERCADO (MARKET GAP)

La reconstrucción de la verdad histórica y judicial en contextos de posconflicto (como el de Colombia, con más de 9 millones de víctimas registradas [3]) requiere procesar y contrastar volúmenes masivos de testimonios. Por ejemplo, la Comisión de la Verdad (CEV) acumuló más de 14.000 entrevistas [4]. 

Actualmente, los investigadores se enfrentan a un **vuelo a ciegas** debido a la falta de herramientas tecnológicas que cumplan de forma simultánea con dos condiciones indispensables:

1.  **Soberanía y Privacidad de Datos Sensibles:** La ley colombiana (Ley 1581 de 2012 de Protección de Datos Personales [22]) y las directrices internacionales sobre la ética de la IA de la UNESCO [17] exigen salvaguardar con extrema rigurosidad los datos de víctimas y comparecientes. Las herramientas comerciales de IA procesan la información en nubes públicas extranjeras, lo que representa una transferencia ilegal de datos altamente confidenciales y un riesgo de veto de confianza por parte de los oficiales de seguridad de la información (CISOs).
2.  **Calibración Lingüística y Contextual Forense:** Los modelos de lenguaje generalistas no entienden las dinámicas conversacionales rurales de Colombia, las formas locales de narrar el trauma [11], ni la terminología técnica y militar del conflicto armado (taxonomías complejas del conflicto [12, 15]).

**Veridicus** llena este vacío al ofrecer un sistema de análisis forense estructurado que se despliega de forma **soberana y local en un servidor privado (Kubernetes)**, garantizando que ni un solo byte de audio o texto salga de la institución [20].

---

## 2. ANÁLISIS DE LA COMPETENCIA (ARENA COMPETITIVA)

El mercado se divide en tres tipos de soluciones, ninguna de las cuales satisface el nicho de la justicia transicional:

### A. Gigantes Tecnológicos e IA Comercial (Hyperscalers)
*   **Ejemplos:** OpenAI (APIs de GPT-4o), Google Cloud AI, Microsoft Azure Cognitive Services.
*   **Qué hacen bien:** Excelente calidad en la transcripción de voz a texto (Whisper) y potentes modelos de razonamiento conversacional.
*   **Por qué no sirven en este nicho:** 
    *   Exigen enviar audios a servidores externos (nubes públicas), rompiendo la gobernanza ética y legal del sector judicial [17].
    *   Son soluciones de propósito general; no integran bases de conocimiento inmutables de hechos históricos ni están calibradas para detectar el engaño lingüístico de forma forense.

### B. Herramientas de Análisis de Emoción en Voz (Emotion AI corporativas)
*   **Ejemplos:** Cogito, Hume AI, plataformas de análisis para centros de llamadas (call centers).
*   **Qué hacen bien:** Detección de fatiga, tono de voz de servicio al cliente y métricas de satisfacción comercial.
*   **Por qué no sirven en este nicho:**
    *   Están diseñadas para la optimización de ventas o soporte técnico corporativo.
    *   Clasifican el estrés como una señal negativa (por ejemplo, para alertar a un supervisor). En una entrevista judicial o transicional, clasificar el estrés de forma simplista como "engaño" revictimiza al declarante que sufre de trauma o trastorno de estrés postraumático (PTSD) [11].

### C. Herramientas Open Source del ecosistema Kubernetes (CNCF)
*   **Ejemplos:** K8sGPT, HolmesGPT, kagent.
*   **Qué hacen bien:** Diagnosticar problemas de infraestructura, analizar logs de servidores y proponer soluciones técnicas en clústeres de Kubernetes.
*   **Por qué no sirven en este nicho:**
    *   Están enfocados puramente en el mundo del desarrollo de software y la ingeniería de confiabilidad de sitios (SRE). No poseen lógica para interactuar humanamente por voz ni analizan contradicciones semánticas en testimonios históricos.

---

## 3. MATRIZ DE COMPARACIÓN DE ATRIBUTOS

| Atributo de Valor | APIs de IA Comercial (OpenAI / Google) | Emotion AI Corporativa (Call Centers) | Veridicus (Despliegue en Kubernetes Local) |
| :--- | :--- | :--- | :--- |
| **Soberanía del Dato** | **Nulo:** Procesamiento en nubes públicas que incumple normativas gubernamentales [17]. | **Medio/Bajo:** Modelos comerciales que exigen integración SaaS (software como servicio). | **Absoluto:** Despliegue cerrado *on-premise* bajo arquitectura segura de Kubernetes [20]. |
| **Detección Científica del Engaño** | **No disponible:** Solo realizan resúmenes o análisis de sentimiento genéricos. | **Sesgado:** Orientado a métricas comerciales; confunde dolor y estrés con mentira. | **Científico:** Implementa la metodología de LieXBerta (RoBERTa + XGBoost) calibrada para testimonios formales [19]. |
| **Integración de "Marco de Verdad"** | **Heurística (Prompts):** Alta probabilidad de inventar detalles (alucinación) [1, 8]. | **No disponible.** | **Estricta:** Conexión local a bases de datos vectoriales inmutables con parámetros de temperatura 0 [18]. |
| **Orquestación de Procesos Pesados** | **Límite de API:** Sujeto a cuotas por minuto y latencia variable de la red exterior. | **Específica de llamadas.** | **Escalable:** Control nativo de recursos en clúster mediante herramientas CNCF como KEDA y Argo [20]. |

---

## 4. BARRERAS DE ENTRADA Y FACTORES DE DEFENSA (EL MOAT)

Para evitar que un competidor replique el sistema simplemente usando mejores prompts comerciales, Veridicus construye tres barreras de defensa fundamentales:

1.  **La Arquitectura del Operador de Kubernetes:** Empaquetar la aplicación como un microservicio local, seguro, escalable (utilizando herramientas CNCF como CloudNativePG con pgvector y KEDA) crea una barrera de implementación técnica compleja que un desarrollador de soluciones sencillas en la nube no puede replicar [20].
2.  **Calibración de Nicho:** El entrenamiento y calibración del clasificador de emociones de LieXBerta con base en el dataset específico del español e idiosincrasia del conflicto colombiano genera una tasa de acierto (87.50% de precisión en pruebas [19]) que no se puede comprar de forma genérica con APIs generalistas.
3.  **Acreditación Judicial y Ética:** El cumplimiento estricto del "Principio de No-Revictimización" (no etiquetar como "mentiroso" al compareciente y priorizar la alerta de estrés postraumático) [11] facilita la homologación del software ante comités éticos institucionales, creando un monopolio de confianza y adopción en el sector gobierno [17].

---

## REFERENCIAS BIBLIOGRÁFICAS

[1] Bender, E. M., McMillan-Major, A., Gebru, T., & Shmitchell, S. (2021). *On the dangers of stochastic parrots: Can language models be too big?* FAccT 2021 - Proceedings of the 2021 ACM Conference on Fairness, Accountability, and Transparency, 610-623.
[2] Centro Nacional de Memoria Histórica (CNMH). (2021). *Informe de Gestión 2021*. CNMH, Bogotá, Colombia.
[3] Centro Nacional de Memoria Histórica (CNMH). (2024). *Informe de Gestión 2024*. CNMH, Bogotá, Colombia.
[4] Comisión para el Esclarecimiento de la Verdad, la Convivencia y la No Repetición. (2022). *Hay Futuro si hay Verdad—Informe Final*. Comisión de la Verdad, Bogotá, Colombia.
[5] Hu, R., Cheng, Y., Shi, X., Lin, W., Meng, L., Xia, J., & Zong, Y. (2025). *Training an LLM-as-a-Judge Model: Pipeline, Insights, and Practical Lessons*. WWW Companion 2025 - Companion Proceedings of the ACM Web Conference 2025, 228-237.
[6] Ley 1448/2011 (2011). *Ley de Víctimas y Restitución de Tierras*. Congreso de la República de Colombia.
[7] Ley 2421/2024 (2024). *Modificación y ampliación de medidas de reparación*. Congreso de la República de Colombia.
[8] Li, D., Sun, R., Huang, Y., Zhong, M., Jiang, B., Han, J., Zhang, X., Wang, W., & Liu, H. (2025). *Preference Leakage: A Contamination Problem in LLM-as-a-judge*. arXiv preprint arXiv:2502.01534.
[9] Ma, H., Lu, Y., Feng, J., Zhang, H., Xiao, Z., & Yu, J. (2025). *SDD-LawLLM: Advancing Intelligent Legal Systems Through Synthetic Data-Driven Fine-Tuning of Large Language Models*. Electronics (Switzerland), 14(4).
[10] Moreno, L. G. (2024). *Inteligencia Artificial para entender el conflicto colombiano*. Pesquisa Javeriana, Pontificia Universidad Javeriana.
[11] Muraszkiewicz, J., & Cadman, J. (2024). *Leveraging Victim Voices: Unveiling True Needs Through Natural Language Processing in Trauma Narratives*. Journal of Victimology & Victim Justice, 7(2), 133-144.
[12] Patiño, A. M. T. (2024). *Modelo semántico y computacional para análisis del conflicto armado en Colombia*. Tesis Doctoral, Universitat Pompeu Fabra, Barcelona.
[13] Rahmani, H. A., Yilmaz, E., Craswell, N., & Mitra, B. (2025). *JudgeBlender: Ensembling Automatic Relevance Judgments*. WWW Companion 2025 - Companion Proceedings of the ACM Web Conference 2025, 1268-1272.
[14] Solà-Sales, S., Alzetta, C., Moret-Tatay, C., & Dell’Orletta, F. (2025). *When Time Matters: Exploring the Impact of Recall Techniques and Educational Levels on Witness Testimony Quality*. Information, 16(2).
[15] Sosa, J., Urrego-López, A., Prieto, C., & Camargo-Díaz, E. J. (2025). *Constructing the Truth: Text Mining and Linguistic Networks in Public Hearings of Case 03 of the Special Jurisdiction for Peace (JEP)*. arXiv preprint arXiv:2504.04325.
[16] Szojka, Z. A., Yashraj, S., & Lyon, T. D. (2025). *Automated question type coding of forensic interviews and trial testimony in child sexual abuse cases*. Law and Human Behavior, 49(2), 163-172.
[17] UNESCO. (2021). *Recomendación sobre la Ética de la Inteligencia Artificial*. Organización de las Naciones Unidas para la Educación, la Ciencia y la Cultura.
[18] Zheng, L., Chiang, W.-L., Sheng, Y., Zhuang, S., Wu, Z., Zhuang, Y., Lin, Z., Li, Z., Li, D., Xing, E. P., Zhang, H., Gonzalez, J. E., & Stoica, I. (2023). *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*. arXiv preprint arXiv:2306.05685.
[19] Zhou, C., Zhang, Y., Lin, C., & Zhou, S. (2025). *A deception detection model by using integrated LLM with emotion features*. Scientific Reports, 15(1), 1-19.
[20] Fariza, L. (2026). *Módulo 2 — AI & Agentic Engineering: Requisitos de Validación*. Universidad Pontificia Javeriana / GitHub Repository. URL: https://github.com/lfarizav/topicos-especiales/tree/main/modulo2
[21] Reyes Palacio, F. (2026). *Ruta de Ejecución y Propuesta de Trabajo de Grado: Diálogos para la Memoria 2026-2027*. Pontificia Universidad Javeriana.
[22] Ley 1581/2012 (2012). *Ley Estatutaria de Protección de Datos Personales*. Congreso de la República de Colombia.
