# Hoja de Ruta de Ejecución: Diálogos para la Memoria y Veridicus (2026-2027)

> **En [`docs/pvb.md`](../../docs/pvb.md): `[19]`** · **En [`docs/critica.md`](../../docs/critica.md): `[12]`**  
> Reyes Palacio, F. (2026). *Ruta de Ejecución y Propuesta de Trabajo de Grado: Diálogos para la Memoria 2026-2027*. Pontificia Universidad Javeriana.  
> 
> Secciones de `pvb.md`: Encabezado · PRODUCTO · 4. ARENA COMPETITIVA  
> Secciones de `critica.md`: Encabezado  
> ⚠ Esa referencia cubre **dos documentos**: esta hoja de ruta y la [propuesta de trabajo de grado](Propuesta_TG_Dialogos_para_la_Memoria_MINSC_V2.md).  
> Documento origen: `Downloads/hoja-de-ruta.md`


**Origen:** `hoja-de-ruta.md` — documento propio del autor, ya en Markdown  
**Fecha:** 21 de agosto de 2026  
**Nota:** documento nativo en Markdown; **no lleva separadores de página**. Para citarlo hay que referirse a su fase, mes o hito, no a un número de página. Se conserva íntegro, incluida su bibliografía propia de 21 entradas.


### Cronograma Integrado: Trabajo de Grado (TG1 y TG2) & Módulo Especializado de Informática (2026-2027)

Este documento constituye la **Hoja de Ruta de Ejecución** integrada para el proyecto de investigación **"Diálogos para la Memoria"** [21] y su módulo funcional de validación de testimonios, **"Veridicus: Módulo de Entrevista y Detección de Incongruencias Forenses"** [21]. 

Alineado con el Trabajo de Grado de Maestría del autor Felipe Reyes Palacio [21], bajo la dirección académica del Dr. Luis Gabriel Moreno [10], el proyecto adopta de manera estricta la metodología de **Investigación Basada en Diseño (Design Science Research - DSR)** [4] para estructurar el desarrollo del prototipo de Inteligencia Artificial (IA) en escenarios reales de posconflicto y justicia transicional en Colombia [1, 2, 4].

---

## 📅 SEMESTRE 1: Trabajo de Grado 1 (TG1) - Sentando las Bases
*Foco: Fundamentación legal, conceptual, diseño de arquitectura y preparación ética de datos (Agosto - Diciembre 2026)*

### Fase A: Análisis y Formalización de Requisitos (Agosto - Octubre 2026)
Esta fase establece los cimientos jurídicos y conceptuales del proyecto, además del marco de validación para la materia de Tópicos Avanzados de Informática [20, 21].

*   **Agosto 2026: Investigación Jurídica e Identificación de Criterios**
    *   **Actividades:**
        *   Formalizar y catalogar los criterios de graduación y puntuación de roles para **víctima, victimario y testigo** basándose en el marco del posconflicto colombiano, la Ley de Víctimas (Ley 1448/2011) y su actualización de reparación (Ley 2421/2024) [3, 6, 21].
        *   Documentar detalladamente las excepciones y salvaguardas previstas por la legislación y la Corte Constitucional (v.g., el reclutamiento ilícito de menores o condiciones específicas de la Fuerza Pública) [21].
    *   **Hito 1.1 (Fin de Agosto):** Entrega del borrador de la *Matriz de Criterios de Caracterización y Excepciones Legales* [21].
*   **Septiembre 2026: Revisión Tecnológica y Estado del Arte**
    *   **Actividades:**
        *   Comparar arquitecturas de Modelos de Lenguaje Grandes (LLMs) aplicadas al arbitraje automático (*LLM-as-a-judge*) y ensambles multiagente (v.g., *JudgeBlender*) para mitigar sesgos analíticos [5, 8, 13, 21].
        *   Evaluar tecnologías y bases científicas de detección de engaño y mentiras en testimonios forenses. Selección formal del modelo **LieXBerta** [19], el cual integra el procesamiento estilométrico de emociones con clasificadores XGBoost [19].
    *   **Hito 1.2 (Fin de Septiembre):** Presentación del *Documento Conceptual de Arquitectura* y justificación de selección de modelos [21].
*   **Octubre 2026: Diseño Conceptual de la Arquitectura de Veridicus**
    *   **Actividades:**
        *   Diseñar el diagrama de microservicios e interfaces de Veridicus sobre **Kubernetes** para aislar el flujo de datos [21].
        *   Completar el *Product Vision Board (PVB)* y validar los insumos críticos de la materia [20].
    *   **Hito 1.3 (Fin de Octubre):** Presentación del *Product Vision Board (pvb.md)* y carpeta de insumos de validación (*critica.md, overview.md, mercado.md, icp.md*) [20].

### Fase B: Preparación de Datos y Validación de Protocolos Éticos (Noviembre - Diciembre 2026)
Esta fase asegura el cumplimiento de las salvaguardas éticas y de protección de datos de especial protección constitucional [17].

*   **Noviembre 2026: Ingesta del Corpus y Anonimización**
    *   **Actividades:**
        *   Organizar y depurar el corpus documental inicial, utilizando como base de datos de referencia el archivo oficial del Legado de la Comisión de la Verdad (CEV) (~14.000 testimonios y entrevistas) [4, 21].
        *   Diseñar e implementar el algoritmo local en Kubernetes para la **anonimización de datos sensibles** (nombres propios, ubicaciones exactas), cumpliendo con la Ley 1581/2012 y las directrices éticas de la UNESCO [11, 17].
    *   **Hito 1.4 (Fin de Noviembre):** Reporte técnico del *Protocolo de Anonimización Local y Corpus de Referencia* [21].
*   **Diciembre 2026: Cierre de TG1 y Consolidación Teórica**
    *   **Actividades:**
        *   Consolidar los resultados del Semestre 1 en un informe final de Trabajo de Grado 1.
        *   Redacción del **Artículo Académico 1** centrado en el estado del arte de la detección de engaño forense y la arquitectura de IA aplicada a la memoria histórica [21].
    *   **Hito 1.5 (Mediados de Diciembre) - ENTREGABLE PRIMARIO S1:** Envío del *Artículo Académico 1* al director Dr. Luis Gabriel Moreno [21].

---

## 📅 SEMESTRE 2: Trabajo de Grado 2 (TG2) - Construcción y Validación
*Foco: Desarrollo de microservicios, integración de gRPC, entrenamiento del modelo y pruebas de concordancia (Enero - Junio 2027)*

### Fase C: Desarrollo e Integración del Modelo (Enero - Marzo 2027)
Desarrollo práctico de la plataforma e integración de agentes de conversación y análisis.

*   **Enero 2027: Desarrollo del Backend y Conversación Oral**
    *   **Actividades:**
        *   Implementar el microservicio conversacional oral usando la biblioteca Whisper de OpenAI localmente en pods de Kubernetes para evitar fugas de información [21].
        *   Construir el backend de gRPC para habilitar transmisiones de audio bidireccionales de baja latencia [21].
    *   **Hito 2.1 (Fin de Enero):** Prototipo de *Pipeline Conversacional de Voz a Texto de Baja Latencia* [21].
*   **Febrero 2027: Integración de Explicabilidad y Detección de Engaño**
    *   **Actividades:**
        *   Configurar el agente evaluador incorporando la técnica de **Cadena de Pensamiento (Chain of Thought - CoT)** para justificar de forma transparente cada hallazgo [9, 21].
        *   Integrar el motor LieXBerta para el análisis afectivo y estilométrico de las transcripciones de las entrevistas [19, 21].
    *   **Hito 2.2 (Fin de Febrero):** Demostración del *Backend Integrado de IA* (conversación, puntuación de rol, explicabilidad CoT y alertas LieXBerta) [21].
*   **Marzo 2027: Afinamiento del Modelo e Interfaz de Usuario (Frontend)**
    *   **Actividades:**
        *   Ajustar e incorporar un modelo fundacional especializado en leyes e historia transicional (como *SDD-LawLLM*) [9, 21].
        *   Desarrollar la interfaz visual adaptada para el **analista de la verdad** (panel de visualización de contradicciones) y el **compareciente** (conversación por micrófono) [11, 21].
    *   **Hito 2.3 (Fin de Marzo):** Demostración de la *Herramienta Visual (Frontend) Funcional* [21].

### Fase D: Validación y Diseño de Puesta en Operación (Abril - Junio 2027)
Fase final de evaluación científica y despliegue robusto del sistema.

*   **Abril 2027: Validación de Concordancia y Mitigación de Sesgos**
    *   **Actividades:**
        *   Medir la precisión y el índice F1 de Veridicus contrastando sus alertas semánticas y estilísticas frente a las decisiones de investigadores y expertos forenses del conflicto armado [21].
        *   Evaluar que las medidas psicosociales aplicadas prevengan de forma exitosa la revictimización o acusaciones arbitrarias ante comparecientes que sufran de desorientación temporal por trauma o estrés postraumático (PTSD) [11, 21].
    *   **Hito 2.4 (Fin de Abril):** Entrega del *Reporte Técnico de Validación de Concordancia IA vs. Humanos* [21].
*   **Mayo 2027: Despliegue en Kubernetes y Operación en Producción**
    *   **Actividades:**
        *   Configurar el plan de despliegue operativo en Kubernetes utilizando herramientas CNCF [21]:
            *   **KEDA:** Escalado automático de GPUs para Whisper.
            *   **CloudNativePG (pgvector):** Base de datos vectorial local para el marco de verdad.
            *   **Prometheus & Grafana:** Monitoreo del SLA conversacional.
        *   Elaborar el Manual del Administrador/Investigador y el Manual del Usuario [21].
    *   **Hito 2.5 (Fin de Mayo):** Entrega de la *Guía de Despliegue de Producción (Operator de Kubernetes)* y Manuales de Operación [21].
*   **Junio 2027: Sustentación y Artículo Académico 2**
    *   **Actividades:**
        *   Consolidar y redactar las conclusiones de la investigación en el informe final de tesis.
        *   Redactar el **Artículo Académico 2** enfocado en los hallazgos empíricos del modelo de IA, las métricas de concordancia y la resiliencia ética del sistema [21].
    *   **Hito 2.6 (Mediados de Junio) - ENTREGABLE PRIMARIO S2:** Envío del *Artículo Académico 2* y defensa pública de la tesis de maestría ante jurados evaluadores [21].

---

## 📚 REFERENCIAS BIBLIOGRÁFICAS

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
[12] Patiño, A. M. T. (2024). *Modelo semántico y computacional para análisis del conflicto armed en Colombia*. Tesis Doctoral, Universitat Pompeu Fabra, Barcelona.
[13] Rahmani, H. A., Yilmaz, E., Craswell, N., & Mitra, B. (2025). *JudgeBlender: Ensembling Automatic Relevance Judgments*. WWW Companion 2025 - Companion Proceedings of the ACM Web Conference 2025, 1268-1272.
[14] Solà-Sales, S., Alzetta, C., Moret-Tatay, C., & Dell’Orletta, F. (2025). *When Time Matters: Exploring the Impact of Recall Techniques and Educational Levels on Witness Testimony Quality*. Information, 16(2).
[15] Sosa, J., Urrego-López, A., Prieto, C., & Camargo-Díaz, E. J. (2025). *Constructing the Truth: Text Mining and Linguistic Networks in Public Hearings of Case 03 of the Special Jurisdiction for Peace (JEP)*. arXiv preprint arXiv:2504.04325.
[16] Szojka, Z. A., Yashraj, S., & Lyon, T. D. (2025). *Automated question type coding of forensic interviews and trial testimony in child sexual abuse cases*. Law and Human Behavior, 49(2), 163-172.
[17] UNESCO. (2021). *Recomendación sobre la Ética de la Inteligencia Artificial*. Organización de las Naciones Unidas para la Educación, la Ciencia y la Cultura.
[18] Zheng, L., Chiang, W.-L., Sheng, Y., Zhuang, S., Wu, Z., Zhuang, Y., Lin, Z., Li, Z., Li, D., Xing, E. P., Zhang, H., Gonzalez, J. E., & Stoica, I. (2023). *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*. arXiv preprint arXiv:2306.05685.
[19] Zhou, C., Zhang, Y., Lin, C., & Zhou, S. (2025). *A deception detection model by using integrated LLM with emotion features*. Scientific Reports, 15(1), 1-19.
[20] Fariza, L. (2026). *Módulo 2 — AI & Agentic Engineering: Requisitos de Validación*. Universidad Pontificia Javeriana / GitHub Repository. URL: https://github.com/lfarizav/topicos-especiales/tree/main/modulo2
[21] Reyes Palacio, F. (2026). *Ruta de Ejecución y Propuesta de Trabajo de Grado: Diálogos para la Memoria 2026-2027*. Pontificia Universidad Javeriana.
