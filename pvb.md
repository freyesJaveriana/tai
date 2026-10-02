# Product Vision Board **Módulo 2 — AI & Agentic Engineering**

Este documento de visión de producto constituye la base de validación y requisitos técnicos para el desarrollo de **Veridicus**, alineado con el Trabajo de Grado de Maestría del autor Felipe Reyes Palacio [19], titulado *"Diálogos para la Memoria"* [9], bajo la dirección del Dr. Luis Gabriel Moreno [9].

> **Nota (2026-10-02, ver `docs/coherencia-insumos.md`, H6):** este PVB es el registro del
> Módulo 2 y queda superado por `specs/prd.md` en: latencia (8–12 s en CPU para el MVP, no 3–5 s),
> hardware (sin GPU), transporte (sin gRPC/WebSockets ni streaming), Argo Workflows (fuera del MVP),
> paradigma de UX (la IA sugiere hallazgos y preguntas; el analista decide) y el modelo LieXBerta
> completo (alcance del TG2). Ante cualquier diferencia, manda el PRD.

---

## PRODUCTO

**Nombre del producto:** Veridicus: Módulo de Entrevista y Detección de Incongruencias Forenses [19]

**Descripción en una línea (qué hace y para quién):** 
Es un sistema multiagente de entrevista asistida por IA que interactúa de manera oral con un compareciente, contrastando su relato en tiempo real frente a un marco de verdad establecido y detectando incongruencias afectivo-semánticas para analistas en procesos de justicia transicional [3, 5, 16].

---

## 1. PROBLEMA

**Problema que resuelvo:**
En los contextos de justicia transicional, investigaciones penales y comisiones de la verdad (como la Comisión de la Verdad de Colombia, que recopiló más de 14.000 entrevistas y conversó con más de 30.000 personas [3]), el análisis manual de testimonios masivos para categorizar roles, evaluar veracidad y contrastar versiones con el expediente histórico es logísticamente inviable [4], extremadamente costoso, propenso a sesgos subjetivos de los evaluadores humanos [1, 7], y genera un altísimo costo emocional y fatiga para los investigadores al procesar innumerables relatos de trauma y dolor de las víctimas [10].

**¿Este problema sobrevive a las próximas 2-3 generaciones de modelos foundation?**
[X] Sí, porque es un problema de WORKFLOW/INTEGRACIÓN, no de OUTPUT. Un modelo de lenguaje base más avanzado procesa mejor el texto, pero no resuelve de forma autónoma la gobernanza, las interfaces conversacionales multimodales locales de baja latencia [17], la mitigación de sesgos hegemónicos mediante consenso multiagente [6, 15], el flujo ético de datos sensibles requeridos por normativas internacionales (como las directrices de la UNESCO [15]), ni el despliegue soberano en infraestructuras privadas controladas.

**Durability Score (1-5):** 5/5

---

## 2. SEGMENTO TARGET

**¿Para quién es este producto?**
Analistas, investigadores de verdad y juristas de organismos de justicia transicional en Colombia (como la Jurisdicción Especial para la Paz - JEP, la Dirección de Acuerdos de Verdad - DAV [2] y el Centro Nacional de Memoria Histórica [2]) que deben validar de forma rigurosa y masiva la contribución a la verdad de comparecientes frente a un cuerpo documental consolidado [2].

**¿Quién controla el veto de confianza?**
El **CISO / SRE Lead** y el **Oficial de Ética/Cumplimiento** de la institución judicial. La adopción será vetada de inmediato si la IA expone testimonios confidenciales y datos sensibles de víctimas a nubes públicas sin anonimizar, violando protocolos éticos [15] y las directrices de la UNESCO [15]. Por consiguiente, la capacidad de desplegar el sistema de forma segura y controlada de extremo a extremo en un clúster local de **Kubernetes** para aislar el procesamiento de datos sensibles es una propiedad técnica y de confianza mandatoria [18].

---

## 3. VENTAJA COMPETITIVA PRIMARIA

**Ventaja competitiva primaria:**
[] Data — Generamos data única que competidores no pueden comprar ni copiar
[] Distribution — Estamos embebidos en un canal/workflow difícil de replicar
[X] Trust — Ofrecemos reliability/safety/compliance que otros no pueden igualar

**¿Qué data, distribución o trust única poseemos o podemos construir?**
Construimos un modelo de **Confianza por Diseño (Trust-by-Design)** basado en tres pilares técnicos y de investigación:
1. **Soberanía y Seguridad en Kubernetes:** Garantizamos aislamiento de datos mediante microservicios locales en contenedores, de modo que el pipeline conversacional (Whisper, procesamiento lingüístico local) pueda operar en entornos air-gapped o de red restringida [18].
2. **Explicabilidad Rigurosa con CoT:** Cada discrepancia o inconsistencia lógica marcada por el sistema está soportada por una **Cadena de Pensamiento (Chain of Thought - CoT)** [8] que enlaza el fragmento exacto transcrito con la fuente documental inmutable del marco de verdad, haciendo el resultado interpretable y auditable [16].
3. **Respaldo Científico de Detección de Engaño (LieXBerta):** A diferencia de simples análisis heurísticos de texto, adoptamos la metodología del modelo **LieXBerta** [17], el cual integra clasificadores de emoción basados en modelos de lenguaje grandes (como RoBERTa-base [17]) con variables de comportamiento que alimentan clasificadores XGBoost [17]. Este enfoque alcanza un **87.50% de precisión en test** [17] y un **87.13% de F1-score** [17], superando por más de un 6.5% a los modelos base sin variables emocionales [17], lo que aporta una base empírica sólida y confiable al análisis forense de la entrevista [14].

---

## 4. ARENA COMPETITIVA

**¿En qué arena compites?**
[] Pioneer (AI-Native) — Creo un mercado nuevo que no podría existir sin IA
[X] Disruptor (AI-Disrupted) — Reimagino un workflow existente haciéndolo 10x mejor [19]
[] Enhancer (AI-Enhanced) — Uso IA para fortalecer un producto/proceso existente

**¿Cómo sobrevives o complementas a los gigantes (hyperscalers, vendors de plataforma, proyectos open source del ecosistema CNCF)?**
Los proveedores gigantes (como OpenAI o Google) ofrecen modelos de lenguaje potentes, pero generalistas, que no resuelven la lógica de negocio especializada en confrontación forense y carecen de la estructura de control de datos soberana exigida por el sector justicia [15]. **Veridicus** no compite con estos gigantes; los orquesta. El valor diferenciador radica en integrar Whisper, bases de datos vectoriales locales de hechos inmutables, algoritmos de detección de engaño basados en análisis estilométrico/emocional calibrado en español [12, 17], y orquestar este flujo multiagente de forma soberana sobre un clúster local de **Kubernetes** [18]. Para que esta arquitectura sea altamente defendible y escalable, se integran las siguientes herramientas clave del ecosistema de la **CNCF (Cloud Native Computing Foundation)**:
*   **KEDA (Kubernetes Event-driven Autoscaling - CNCF Graduated):** Autoscaling dinámico a nivel de contenedor de los pods de Whisper y de inferencia basados en GPU. Si no hay entrevistas en curso, escala los recursos costosos a 0, y escala verticalmente basándose en el tamaño de la cola de procesamiento en gRPC/WebSockets [18].
*   **CloudNativePG (CNCF Sandbox):** Para orquestar bases de datos PostgreSQL de alta disponibilidad a nivel local, habilitando la extensión **pgvector** como nuestro motor de búsqueda semántica local para almacenar el "marco de verdad" fáctico del conflicto armado [18].
*   **Argo Workflows (CNCF Graduated):** Para programar y monitorear pipelines batch offline de procesamiento lingüístico y análisis estilométrico pesado cuando se analizan audios de larga duración (2-3 horas) [18].
*   **Prometheus (CNCF Graduated) & Grafana:** Prometheus para la recolección de métricas de telemetría en tiempo real de los microservicios; Grafana (proyecto independiente, no gobernado por la CNCF, pero el estándar de facto para visualizar métricas de Prometheus) para los dashboards de observabilidad de latencias conversacionales y tasas de acierto [18].

---

## 5. UX PARADIGM

**¿Cómo interactúa el usuario con tu producto?**
[] Assistant — El usuario está en control, la IA sugiere
[X] Agent — La IA ejecuta tareas autónomamente dentro de límites
[] Autonomous — La IA corre sin supervisión humana
[] Embedded Intelligence — La IA mejora el producto de forma invisible

**¿Por qué este paradigma para tu caso de uso?**
El paradigma de autonomía completa (*Autonomous*) es éticamente inviable, puesto que los sistemas automatizados no pueden tomar decisiones judiciales ni etiquetar de forma definitiva las intenciones del compareciente debido al riesgo de sesgo y alucinación [7, 11]. Un simple paradigma de *Assistant* limitaría la entrevista dinámica, exigiendo que el analista formule cada pregunta. El paradigma **Agent** provee el balance óptimo: la IA recopila autónomamente el testimonio mediante diálogo oral dinámico (ajustándose en base a Whisper y gRPC para optimizar la experiencia de voz) y realiza la validación semántica contra el marco de verdad [16], pero operando bajo límites estrictos (no altera los expedientes, no asume juicios binarios categóricos y sus hallazgos de inconsistencia lógica se proponen al investigador humano con su respectiva justificación [10]).

---

## 6. AI DECISION TRIANGLE

**Optimizo primariamente para:**
[] Cost — Lo más barato posible (tareas de alto volumen)
[X] Capability — Lo más inteligente/preciso (decisiones de alto riesgo)
[] Speed — Lo más rápido posible (experiencias en tiempo real)

**Trade-offs que acepto:**
Aceptamos un mayor costo computacional (empleando llamadas a modelos de lenguaje grandes y sofisticados para el razonamiento de las inconsistencias semánticas) y una latencia conversacional de 3 a 5 segundos de procesamiento (sintetizar audio a texto, confrontar en RAG vectorial local y orquestar el razonamiento de Cadena de Pensamiento [8]). En el contexto de un interrogatorio de justicia o una entrevista forense institucional, este lapso no interrumpe el flujo; al contrario, emula el ritmo reflexivo y pausado de una conversación humana real.

---

## 7. MODELO ECONÓMICO

**Modelo de pricing:**
[X] Hybrid Tiered (tiers con límites crecientes)
[] Usage-Based / Per-Token (pago por uso)
[] Credit Pools (suscripción + créditos)
[] Outcome-Based (pago por resultado)
[] Seat-Based + AI Add-On (por usuario + IA premium)
[] Freemium / Reverse Trial (gratis → conversión)

**¿El pricing escala si tienes 10x usuarios?**
[X] Sí
[] No
[] Necesita ajuste

*Justificación:* Los costos marginales principales están vinculados al consumo de hardware (procesamiento de GPU para Whisper y LLMs de clasificación estilométrica y afectiva local [17]). En Kubernetes, los recursos computacionales del clúster pueden escalarse dinámicamente según la demanda. El modelo de tiers híbridos cobra una tarifa fija por analista/estación conectada al mes que incluye un límite de horas de declaraciones procesadas (por ejemplo, 100 horas/mes). 

**Estructura económica estimada por estación de analista/mes (100 horas procesadas):**
* **Costo de inferencia local en clúster GPU + llamadas de APIs complementarias:** $180 USD [INTERNO].
* **Infraestructura de clúster Kubernetes local & almacenamiento inmutable:** $45 USD [INTERNO].
* **Soporte técnico y mantenimiento del operador de IA:** $125 USD [INTERNO].
* **Costo Total Estimado (COGS):** $350 USD [INTERNO].
* **Revenue Proyectado (Precio de Suscripción):** $1.400 USD [INTERNO].
* **Gross Margin Proyectado:** 75% [INTERNO].

---

## 8. MÉTRICAS DE ÉXITO

**Métricas de usuario:**
1. **Reducción del Tiempo de Validación Semántica (MTTV - Mean Time to Validate):** Disminución en el tiempo promedio requerido por un investigador para contrastar una entrevista completa frente a los marcos documentales oficiales de la verdad. *Target: >50% de reducción en comparación con el proceso de cotejo manual [14].*
2. **Tasa de Desestimación de Incongruencias:** Porcentaje de discrepancias lógicas sugeridas por el sistema que el investigador humano desestima o clasifica como "normales" o "no sospechosas". *Target: <15% de falsos positivos en producción.*

**Métricas específicas de IA:**
1. **Precisión del Análisis de Detección de Engaño en Pruebas de Concordancia (Test Accuracy):** Grado de acierto en el alineamiento con evaluaciones de expertos forenses independientes sobre el conjunto de pruebas. *Target: >85% de precisión en test (LieXBerta(3) reporta un 87.50% de precisión y un 87.13% de F1-score bajo 10-fold cross-validation [17]).*
2. **Tasa de Alucinación Fáctica del Agente Conversacional:** Porcentaje de turnos en los cuales el agente introduce hechos, lugares o acusaciones no documentadas previamente en la base de datos vectorial inmutable del "marco de verdad". *Target: 0.00% (alineación de verdad estricta).*

---

## 9. RIESGOS CRÍTICOS

**1. ¿Qué pasa si el problema desaparece en 12 meses por comoditización?**
*Riesgo:* Los proveedores comerciales de modelos integrarán capacidades avanzadas y nativas de voz e interpretación multimodal en sus APIs públicas de extremo a extremo (como GPT-4o o Gemini Advanced Audio [17]). 
*Mitigación:* Veridicus no compite por ser un modelo base de voz. Su valor se encuentra en la **lógica de negocio forense y judicial**, la integración inmutable de hechos del conflicto [3, 5], la explicabilidad mediante Cadena de Pensamiento (CoT) [8] adaptada a la legislación transicional colombiana (Leyes 1448/2011 y 2421/2024 [2, 5]), el almacenamiento seguro local y el historial de tasas de acierto operacionales acumuladas sobre un clúster privado Kubernetes, lo cual no es replicable de manera genérica por APIs comerciales ajenas a la soberanía de datos del estado [15].

**2. ¿Puede un competidor replicar tu producto con la misma API en menos de 6 semanas?**
*Riesgo:* Sí, un competidor técnico puede empaquetar una llamada a la API de OpenAI y usar prompts estructurados para detectar mentiras en poco tiempo [17].
*Mitigación:* No obstante, lo que un competidor no puede replicar en 6 semanas es la **validez empírica y metodológica de la calibración estilométrica en español forense** basada en los rasgos emocionales más incidentes para la justicia transicional colombiana (como las variaciones significativas de tristeza, ira y optimismo detectadas en el estudio empírico de LieXBerta con un XGBoost optimizado [17]), la redacción e implementación nativa de políticas de seguridad en **Kubernetes** para el aislamiento del tráfico sensible [18], ni el ciclo de homologación de políticas de privacidad auditadas por comités éticos de derechos humanos [15].

**3. Si tienes éxito a escala, ¿cuál es la primera forma en que se rompe la confianza?**
*Riesgo:* Que el agente clasifique de forma simplista como "engaño" o "mentira" las inconsistencias normales, contradicciones lógicas o variaciones estilísticas emocionales de un relato provocadas por el **estrés postraumático (PTSD)** o por el dolor de revivir el trauma de la victimización [10]. Esto ocasionaría un daño psicológico irreparable y la revictimización del declarante.
*Mitigación:* Se implementa un principio ético no relajable: **el agente jamás emite veredictos de veracidad binaria (mentira/verdad)** [10]. El sistema se limita a señalar "Desviaciones o Incongruencias Semánticas" contrastando el fragmento exacto del audio de manera literal con las citas del "marco de verdad" inmutable. Adicionalmente, el clasificador estilométrico emocional debe configurarse con un umbral estricto para priorizar y etiquetar primero variaciones como *"Fluctuación estilística por posible trauma/confusión"* antes de sugerir un intento voluntario de ocultamiento o distorsión fáctica [10]. La decisión analítica y forense es y será siempre prerrogativa exclusiva del analista humano [10].

---

## REFERENCIAS BIBLIOGRÁFICAS

[1] Bender, E. M., McMillan-Major, A., Gebru, T., & Shmitchell, S. (2021). *On the dangers of stochastic parrots: Can language models be too big?* FAccT 2021 - Proceedings of the 2021 ACM Conference on Fairness, Accountability, and Transparency, 610-623.
[2] Centro Nacional de Memoria Histórica (CNMH). (2024). *Informe de Gestión 2024*. CNMH, Bogotá, Colombia. Disponible en: https://centrodememoriahistorica.gov.co/informe-de-gestion-2024/ (Accedido: agosto 2026).
[3] Comisión para el Esclarecimiento de la Verdad, la Convivencia y la No Repetición. (2022). *Hay Futuro si hay Verdad—Informe Final*. Comisión de la Verdad, Bogotá, Colombia. Disponible en: https://www.comisiondelaverdad.co/ (Accedido: agosto 2026).
[4] Hu, R., Cheng, Y., Shi, X., Lin, W., Meng, L., Xia, J., & Zong, Y. (2025). *Training an LLM-as-a-Judge Model: Pipeline, Insights, and Practical Lessons*. WWW Companion 2025 - Companion Proceedings of the ACM Web Conference 2025, 228-237.
[5] Ley 1448/2011 (2011). *Ley de Víctimas y Restitución de Tierras*. Congreso de la República de Colombia.
[6] Ley 2421/2024 (2024). *Modificación y ampliación de medidas de reparación*. Congreso de la República de Colombia.
[7] Li, D., Sun, R., Huang, Y., Zhong, M., Jiang, B., Han, J., Zhang, X., Wang, W., & Liu, H. (2025). *Preference Leakage: A Contamination Problem in LLM-as-a-judge*. arXiv preprint arXiv:2502.01534.
[8] Ma, H., Lu, Y., Feng, J., Zhang, H., Xiao, Z., & Yu, J. (2025). *SDD-LawLLM: Advancing Intelligent Legal Systems Through Synthetic Data-Driven Fine-Tuning of Large Language Models*. Electronics (Switzerland), 14(4).
[9] Moreno, L. G. (2024). *Inteligencia Artificial para entender el conflicto colombiano*. Pesquisa Javeriana, Pontificia Universidad Javeriana.
[10] Muraszkiewicz, J., & Cadman, J. (2024). *Leveraging Victim Voices: Unveiling True Needs Through Natural Language Processing in Trauma Narratives*. Journal of Victimology & Victim Justice, 7(2), 133-144.
[11] Rahmani, H. A., Yilmaz, E., Craswell, N., & Mitra, B. (2025). *JudgeBlender: Ensembling Automatic Relevance Judgments*. WWW Companion 2025 - Companion Proceedings of the ACM Web Conference 2025, 1268-1272.
[12] Solà-Sales, S., Alzetta, C., Moret-Tatay, C., & Dell’Orletta, F. (2025). *When Time Matters: Exploring the Impact of Recall Techniques and Educational Levels on Witness Testimony Quality*. Information, 16(2).
[13] Sosa, J., Urrego-López, A., Prieto, C., & Camargo-Díaz, E. J. (2025). *Constructing the Truth: Text Mining and Linguistic Networks in Public Hearings of Case 03 of the Special Jurisdiction for Peace (JEP)*. arXiv preprint arXiv:2504.04325.
[14] Szojka, Z. A., Yashraj, S., & Lyon, T. D. (2025). *Automated question type coding of forensic interviews and trial testimony in child sexual abuse cases*. Law and Human Behavior, 49(2), 163-172.
[15] UNESCO. (2021). *Recomendación sobre la Ética de la Inteligencia Artificial*. Organización de las Naciones Unidas para la Educación, la Ciencia y la Cultura. Disponible en: https://unesdoc.unesco.org/ark:/48223/pf0000381137_spa (Accedido: agosto 2026).
[16] Zheng, L., Chiang, W.-L., Sheng, Y., Zhuang, S., Wu, Z., Zhuang, Y., Lin, Z., Li, Z., Li, D., Xing, E. P., Zhang, H., Gonzalez, J. E., & Stoica, I. (2023). *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*. arXiv preprint arXiv:2306.05685.
[17] Zhou, C., Zhang, Y., Lin, C., & Zhou, S. (2025). *A deception detection model by using integrated LLM with emotion features*. Scientific Reports, 15(1), 1-19.
[18] Fariza, L. (2026). *Módulo 2 — AI & Agentic Engineering: Requisitos de Validación*. Universidad Pontificia Javeriana / GitHub Repository. URL: https://github.com/lfarizav/topicos-especiales/tree/main/modulo2
[19] Reyes Palacio, F. (2026). *Ruta de Ejecución y Propuesta de Trabajo de Grado: Diálogos para la Memoria 2026-2027*. Pontificia Universidad Javeriana.

---

## ANEXO: AUDITORÍA DE CRÍTICA DE ALUCINACIONES (PASO 2 DEL MÓDULO)

En cumplimiento de las instrucciones de la asignatura (Módulo 2, Paso 2) y siguiendo las directrices de `modulo3/research/README.md`, se documenta y analiza a continuación el caso real de fallos de verificación y alucinaciones en un reporte de deep research generado con IA sobre agentes operando en Kubernetes:

### 1. El Caso de Estudio de Alucinación de Datos (DORA y la Narrativa Forzada)
*   **La Alucinación del Reporte:** El reporte generado por la IA afirmó que *"el 38% de los equipos que usan IA aumentaron su frecuencia de despliegue"*.
*   **El Dato Real (Auditoría):** Esta cifra es completamente inexistente en la literatura de DORA (DevOps Research and Assessment). En realidad, el informe real de DORA publicado indica que la adopción de IA se asocia con una **reducción del 7.2% en la estabilidad**. El modelo de IA, al verse enfrentado a un dato real "incómodo" para la narrativa optimista sobre la IA, reemplazó el dato por un porcentaje inventado que simulaba una validación de éxito.
*   **Lección para Veridicus:** Este es el sesgo más peligroso de los LLMs. En el análisis de declaraciones sobre el conflicto armado, si el compareciente dice algo que el modelo "quiere" validar o encajar en una hipótesis preconcebida, el LLM podría inventar porcentajes de correlación o tergiversar el marco de verdad fáctico para forzar la conclusión. Por ello, la temperatura de Veridicus debe ser estrictamente `0`, su pipeline de RAG vectorial inmutable, y no debe realizar generalizaciones estadísticas sin contrastación explícitamente enlazada.

### 2. Clasificación de Proyectos Errónea (Backstage en la CNCF)
*   **La Alucinación del Reporte:** Clasificó el proyecto **Backstage** como un proyecto *"Graduated"* (Graduado) dentro del ecosistema CNCF.
*   **El Dato Real (Auditoría):** Backstage se encuentra en la etapa de *"Incubating"* (Incubando), no graduado. Esto demuestra una falta de actualización temporal y rigurosidad técnica sobre el estado del arte de la infraestructura nativa de la nube.
*   **Lección para Veridicus:** No se pueden asumir los estados técnicos de los proyectos o dependencias del sistema sin validación directa de sus manifiestos o APIs de control.

### 3. Autocitación y Circularidad Fáctica
*   **La Alucinación del Reporte:** El modelo citó como fuente verificada externa el propio archivo de contexto que el usuario le había entregado inicialmente para analizar, creando un bucle de circularidad fáctica sin validación externa real.
*   **Lección para Veridicus:** El sistema conversacional no debe autocitar sus propios prompts o inferencias pasadas como "hechos probados" en la sesión de entrevista actual. Cada hecho debe enlazarse estrictamente a una fuente documental externa registrada en la base de datos de Kubernetes, previniendo loops lógicos cerrados.

### 4. Dirección del Dato Invertida y Citas Huérfanas (Gartner e IBM)
*   **La Alucinación del Reporte:** Presentó una predicción histórica de ahorro de costos de analistas como un hecho consolidado, omitiendo que el propio autor la había revertido meses después. Además, atribuyó estadísticas oficiales de Gartner a una página secundaria de análisis de bolsa de IBM.
*   **Lección para Veridicus:** Las cifras no valen si provienen de fuentes secundarias o de tercera mano. En Veridicus, la procedencia (*provenance*) del dato debe ser de primer orden: sentencias judiciales, expedientes de la JEP o informes oficiales de la Comisión de la Verdad, con su respectivo código hash verificable.
