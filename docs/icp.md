# Perfil de Cliente Ideal (ICP) y Buyer Personas: Veridicus
*Módulo 3 — Documento de Caracterización de Clientes (`docs/icp.md`)*

Este documento define el **Perfil de Cliente Ideal (ICP - Ideal Customer Profile)** y caracteriza a los usuarios reales y decisores de compra (**Buyer Personas**) para **Veridicus: Módulo de Entrevista y Detección de Incongruencias Forenses** [21]. En entornos de alta sensibilidad política y humana, como la justicia transicional y los derechos humanos, entender a quienes usan el sistema y a quienes controlan su adopción es indispensable para evitar el rechazo tecnológico.

---

## 1. PERFIL DE CLIENTE IDEAL (ICP)

Veridicus no es una herramienta para empresas comerciales o mercadeo de consumo general. Su diseño técnico, soberano y modular está optimizado para organizaciones con las siguientes características:

*   **Sector:** Público, judicial, no gubernamental (ONGs) e internacional, con enfoque en derechos humanos y justicia transicional.
*   **Organizaciones Típicas en Colombia:** Jurisdicción Especial para la Paz (JEP) [15], Centro Nacional de Memoria Histórica (CNMH) [2, 3], Dirección de Acuerdos de Verdad (DAV) [3] y Comisiones de la Verdad [4].
*   **Problema Operativo Crítico:** Alto volumen de declaraciones orales y escritas (miles de horas de audio acumuladas) que deben ser procesadas, sistematizadas y contrastadas de manera obligatoria frente a un marco de hechos probados [4, 5].
*   **Entorno de Seguridad:** Organizaciones que manejan información de nivel confidencial o reservado (testimonios de víctimas, identidades protegidas, datos sobre violencia de género) [11], y que por lo tanto tienen estrictas prohibiciones legales para subir datos a nubes públicas comerciales de terceros [17].
*   **Infraestructura Tecnológica:** Entidades con equipos de TI internos o proveedores tecnológicos que administran nubes híbridas o centros de datos privados bajo políticas de cumplimiento estrictas [20].

---

## 2. BUYER PERSONAS: LOS ROLES CLAVE EN EL PROCESO

El éxito o fracaso de la adopción de Veridicus depende de tres perfiles bien diferenciados: el usuario que se beneficia de la herramienta cotidianamente, y los dos roles técnicos y éticos que tienen el poder de veto.

### Persona 1: El Analista de Verdad (Usuario Final)
*   **Nombre ficticio:** Dra. Clara Sanabria
*   **Cargo:** Investigadora Forense / Historiadora Analista de la Verdad.
*   **Demografía:** Profesional en Derecho, Historia, Psicología o Ciencias Sociales. Entre 30 y 55 años.
*   **Su Rol:** Escuchar testimonios, leer transcripciones, contrastar las versiones de los comparecientes con expedientes históricos documentados y clasificar hechos.
*   **Sus Dolores:**
    *   **Fatiga Conversacional y Burnout:** Agotamiento mental extremo por leer y escuchar relatos crudos y detallados de violencia y trauma [11].
    *   **Saturación de Información:** Pérdida de tiempo en tareas administrativas de transcripción manual y búsqueda de folios específicos, en lugar de realizar un análisis profundo de patrones.
    *   **Miedo al Error Humano:** Preocupación por pasar por alto una contradicción clave entre un testimonio de hoy y un hecho probado de hace cinco años por cansancio físico.
*   **Cómo Veridicus alivia su dolor:** Automatiza la transcripción oral con Whisper, asume la carga pesada del cotejo semántico básico en tiempo real y resalta posibles incongruencias de manera explicable (CoT) [9, 19], permitiendo que la Clara humana se concentre en la toma de decisiones y el análisis forense final sin el desgaste emocional continuo [11].

---

### Persona 2: El Líder de Seguridad y Operaciones (SRE Lead / CISO) (Primer Veto)
*   **Nombre ficticio:** Ing. Andrés Tejada
*   **Cargo:** Director de TI / SRE Lead / Oficial de Seguridad de la Información (CISO).
*   **Demografía:** Ingeniero de Sistemas especializado en Ciberseguridad o Infraestructura Cloud. Entre 35 y 48 años.
*   **Su Rol:** Garantizar la seguridad, estabilidad, privacidad y disponibilidad de todos los sistemas tecnológicos de la entidad judicial o del Estado.
*   **Sus Dolores:**
    *   **Fuga de Datos Sensibles:** Su mayor pesadilla es que la voz de una víctima protegida o un compareciente de alta confidencialidad sea enviada a servidores de nubes comerciales ubicados en el exterior, violando la Ley 1581/2012 [22] y atrayendo demandas internacionales [17].
    *   **Incompatibilidad de Arquitectura:** Rechaza de inmediato cualquier software que no pueda integrarse con las herramientas modernas de monitoreo e infraestructura que su equipo ya administra.
    *   **Costos Impredecibles:** Desconfía de las suscripciones basadas en consumo de tokens externos en la nube, cuyos costos pueden dispararse de la noche a la mañana.
*   **Cómo Veridicus alivia su dolor:** Se presenta como una solución nativa de **Kubernetes** que puede desplegarse en servidores locales (*on-premise*) de forma aislada (*air-gapped*) [20]. El uso de Whisper y clasificadores estilométricos locales asegura que ningún dato privado de audio o texto salga del perímetro seguro del Estado [19, 20]. La integración con herramientas de la CNCF (como KEDA para autoescala e infraestructura local) le permite auditar el tráfico, controlar el hardware y predecir los costos de forma estable [20].

---

### Persona 3: El Oficial de Cumplimiento Ético y Legal (Segundo Veto)
*   **Nombre ficticio:** Dra. Sofía Restrepo
*   **Cargo:** Asesora de Derechos Humanos / Oficial de Ética en Inteligencia Artificial.
*   **Demografía:** Abogada experta en Derecho Internacional Humanitario y Ética Tecnológica. Entre 40 y 60 años.
*   **Su Rol:** Asegurar que cualquier herramienta de IA implementada respete el debido proceso, no introduzca sesgos de discriminación y proteja la integridad moral de los declarantes.
*   **Sus Dolores:**
    *   **La Caja Negra de la IA:** Teme que el software tome decisiones sesgadas u opacas sin justificación científica, etiquetando a personas inocentes de forma discriminatoria [1, 8].
    *   **La Revictimización por Alucinación:** Preocupación por que la IA acuse falsamente a una víctima con estrés postraumático (PTSD) de estar mintiendo, confundiendo un bloqueo de memoria doloroso con engaño [11].
    *   **Falta de Explicabilidad:** No acepta un veredicto binario ("Miente" / "No miente") que un analista judicial no pueda auditar paso a paso [18].
*   **Cómo Veridicus alivia su dolor:** El sistema está diseñado bajo el principio de **Neutralidad No-Invasiva** [11]. El agente nunca declara si un usuario "miente" [11]; solo genera visualizaciones de inconsistencias semánticas con citas exactas a documentos fuentes. El modelo se apoya en el marco científico de **LieXBerta** [19], que trata el lenguaje de forma explicable mediante Cadena de Pensamiento (CoT) [9, 18], y se ajusta bajo los estándares éticos mundiales dictados por la UNESCO [17].

---

## 3. MATRIZ DE ALINEACIÓN DE VALOR

| Rol | Canal de Interacción Principal | Principal Argumento de Adopción | Métrica Clave de Valor |
| :--- | :--- | :--- | :--- |
| **Analista de Verdad** *(Clara)* | Interfaz web intuitiva con editor de testimonios lado a lado con el marco de verdad. | Reducción del 50% en el tiempo de cotejo manual y blindaje contra la fatiga analítica [11, 16]. | **MTTV** (Mean Time to Validate): Tiempo promedio de validación de un testimonio. |
| **SRE Lead / CISO** *(Andrés)* | Panel de administración del operador de Kubernetes, Grafana y CLI. | Soberanía total de datos en clúster local de Kubernetes y costo predecible [20]. | **Data Sovereignty Score:** 100% de datos sensibles procesados sin llamadas a APIs externas públicas. |
| **Oficial de Cumplimiento** *(Sofía)* | Reportes consolidados de auditoría y árboles de razonamiento basados en Chain of Thought. | Explicabilidad total fundamentada en LieXBerta y garantía ética de no-revictimización [11, 19]. | **Tasa de Explicabilidad:** 100% de alertas acompañadas por su respectiva justificación factual documentada [18]. |

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
