# Diálogos para la Memoria — Propuesta de Trabajo de Grado (Maestría en Ingeniería de Sistemas y Computación, V2)

> **En [`docs/pvb.md`](../../docs/pvb.md): `[19]`** · **En [`docs/critica.md`](../../docs/critica.md): `[12]`**  
> Reyes Palacio, F. (2025). *Diálogos para la Memoria: modelo conversacional basado en LLMs para la caracterización de actores del conflicto armado colombiano — Propuesta de Trabajo de Grado*. Pontificia Universidad Javeriana. Director: Ing. Luis Gabriel Moreno, PhD.  
> 
> ⚠ Esa referencia cubre **dos documentos**: esta propuesta y la [hoja de ruta de ejecución](Hoja_de_Ruta_Dialogos_para_la_Memoria_2026_2027.md).  
> Secciones de `pvb.md`: Encabezado · PRODUCTO · 4. ARENA COMPETITIVA  
> Secciones de `critica.md`: Encabezado  
> Documento origen: `Trabajo_Grado/20251107-Propuesta_TG_Dialogos_para_la_memoria_MINSC_V2.pdf`


**Origen:** `Trabajo_Grado/20251107-Propuesta_TG_Dialogos_para_la_memoria_MINSC_V2.pdf` — documento propio del autor  
**Fecha:** 7 de noviembre de 2025  
**Páginas:** 9  
**Nota:** los separadores `PAGINA n` corresponden a la página física del PDF.


------------------------- PAGINA 1 --------------------------

# **FACULTAD DE INGENIERÍA**

# **MAESTRÍA EN INGENIERÍA DE SISTEMAS Y COMPUTACIÓN**

**TRABAJO DE GRADO – PROPUESTA DE PROYECTO**

# **-DIÁLOGOS PARA LA MEMORIA-**

|**TÍTULO DEL**<br>**PROYECTO**|**MODELO CONVERSACIONAL**<br>**ACTORES DEL**|**BASADO EN LLMS P**<br>**CONFLICTO ARMAD**|**ARA LA CARACTERIZACIÓN DE**<br>**O COLOMBIANO**|
|---|---|---|---|
|**DATOS DEL**|**Felipe Reyes Palacio**|**CORREO**|freyes@javeriana.edu.co|
|**ESTUDIANTE**|CC 79.955.410|**ELECTRÓNICO**|epilefreyes@gmail.com|
|**DIRECTOR DE**|Ing. Luis Gabriel Moreno PhD|**MODALIDAD**|Investigación|
|**TRABAJO DE**<br>**GRADO**|morenoluis@javeriana.edu.co|**ÁREA DE**<br>**ÉNFASIS**|Sistemas Inteligentes|

## **OBJETIVO GENERAL**

Desarrollar un agente conversacional, basado en Modelos de Lenguaje Grandes (LLMs), capaz de caracterizar el grado de participación (víctima, victimario o testigo) de un actor del conflicto armado colombiano, integrando mecanismos de explicabilidad y detección de engaño para generar resultados trazables y mitigar sesgos.

## **OBJETIVOS ESPECÍFICOS**

   1. Definir los requisitos funcionales, no funcionales, legales y éticos del sistema, formalizando los criterios cuantitativos y las excepciones legales para la caracterización de los roles de actor, víctima y testigo.

- **OBJETIVOS** 2. Diseñar la arquitectura tecnológica del agente conversacional, seleccionando la estrategia de LLM, las técnicas de IA más adecuadas para la explicabilidad y la detección de engaños, asegurando la minimización de sesgos.

   3. Implementar el prototipo funcional del agente conversacional y su motor de evaluación, integrando el corpus de datos anonimizados y las técnicas de detección de incongruencias definidas en el diseño.

   4. Validar la robustez y precisión del modelo implementado mediante pruebas de concordancia con evaluadores humanos, evaluando la efectividad de la mitigación de sesgos y la transparencia del proceso de explicabilidad.

   5. Formular el plan de despliegue operacional del modelo, que contemple los recursos requeridos y la implementación de la privacidad.


------------------------- PAGINA 2 --------------------------

## **PLANTEAMIENTO DEL PROBLEMA**

|**PROBLEMA**<br>**DE**<br>**INVESTIGACIÓN**<br>**O**<br>**APLICACIÓN**|El posconflicto en Colombia, en su búsqueda de la verdad y la reparación, ha generado un<br>volumen masivo de testimonios. La Comisión de la Verdad (CV), por ejemplo, recopiló cerca<br>de 14.000 entrevistas y conversó con más de 30.000 personas [1]. El desafío actual radica en<br>la dificultad de analizar este vasto corpus de manera escalable, objetiva y matizada, evitando<br>las "lecturas simplistas y binarias" que la propia CV insta a superar [1].<br>Aunque la legislación define los roles de víctima [2, 3], victimario [2] y testigo [2, 3], la<br>clasificación es compleja: existen excepciones [2, 3] y las líneas entre víctimas y victimarios<br>son a menudo difusas [1]. Un análisis manual exhaustivo de cada testimonio para "medir el<br>nivel de encarnación" de cada rol es logísticamente inviable y propenso a la subjetividad del<br>evaluador. Se requiere, por tanto, una herramienta tecnológica que apoye este proceso de<br>caracterización.<br>**ESTADO DEL ARTE Y BRECHA TECNOLÓGICA**<br>Los esfuerzos iniciales para procesar estos relatos han incluido análisis de minería de textos y<br>análisis de sentimientos, algunos de los cuales fueron explorados por la propia Comisión de<br>la Verdad [4]. Si bien estos enfoques son valiosos para revelar la dimensión emocional de los<br>relatos [5] o aplicar modelos semánticos [6], resultan insuficientes para la tarea de<br>"caracterizar el rol" de forma graduada y explicable, que es el núcleo de esta propuesta.<br>Para abordar esta brecha, la literatura reciente en Inteligencia Artificial propone el uso de<br>Modelos de Lenguaje Grandes (LLMs) como evaluadores, o "LLM-as-a-judge" [7]. Este<br>enfoque ha demostrado una alta concordancia con evaluadores humanos en tareas<br>complejas de juicio y clasificación [8,9]. Se han explorado arquitecturas alternativas como<br>"JudgeBlender" [10], que utilizan ensambles de LLMs para mitigar sesgos [11], un desafío<br>ético clave en esta área.<br>Paralelamente, para la detección de engaños, se integrarán técnicas que combinan<br>características emocionales con LLMs [12]. Asimismo, el proyecto se basará en los avances<br>de agentes conversacionales para la recopilación de testimonios, un área donde la IA ha<br>mostrado alta eficacia en contextos de entrevistas forenses [13,14].<br>**MARCO METODOLOGICO**<br>Dada la naturaleza del proyecto, enmarcado en dos maestrías de ingeniería, se adopta un<br>enfoque de Investigación Basada en Diseño (Design Science Research). Esta metodología se<br>centra en el desarrollo de artefactos tecnológicos innovadores (en este caso, el agente<br>conversacional) como solución a un problema del mundo real. Siguiendo los lineamientos de<br>este enfoque [15], el proyecto se estructura en las fases de identificación del problema,<br>diseño del artefacto, implementación y validación, asegurando tanto el rigor científico como<br>la relevancia práctica.<br>**CONSIDERACIONES ÉTICAS Y METODOLÓGICAS**<br>Un desafío ético clave es el sesgo en los evaluadores automáticos [11]. Dado que los LLMs<br>pueden 'codificar visiones hegemónicas perjudiciales', [11] se requiere una limpieza y<br>validación rigurosa de los datos a utilizar. Al controlar los sesgos, el LLM puede ser objetivo y<br>evitar ser manipulado.<br>Otro pilar fundamental es la privacidad, que debe respetarse a lo largo del ciclo de vida del|
|---|---|


------------------------- PAGINA 3 --------------------------

sistema de IA, según la UNESCO [16]. El modelo deberá proteger los datos personales de los entrevistados, implementando la anonimización cuando sea necesaria. Muraszkiewicz enfatiza la necesidad de una planificación cuidadosa para abordar temores como el consentimiento informado, la confidencialidad y la seguridad de los participantes en las entrevistas [17].

## **PREGUNTA DE INVESTIGACIÓN**

¿Cómo puede un agente conversacional, basado en LLMs, caracterizar el grado de participación (víctima, victimario, testigo) de un actor del conflicto armado colombiano y generar una justificación explicable de los motivos de dicha graduación?


------------------------- PAGINA 4 --------------------------

## **METODOLOGÍA**

Con el fin de alcanzar el objetivo de caracterizar el rol de los actores del conflicto armado colombiano (víctima, victimario, testigo) mediante un agente conversacional basado en **DESCRIPCIÓN** LLMs, el proyecto se desglosa en cuatro fases. Estas fases garantizan la rigurosidad ética, la **GENERAL** solidez tecnológica y la explicabilidad del modelo, dividida en 2 semestres de trabajo (TG1 y TG2) acorde a los tiempos esperados de ejecución.

Esta fase establece el marco conceptual y legal del proyecto, formalizando los criterios de **FASE 1** caracterización para abordar la complejidad de los roles y revisando las arquitecturas y tecnologías de Modelos de Lenguaje Grande (LLMs) que serían utilizadas.

|**ANÁLISIS Y**<br>**FORMALIZACIÓN**|**Aproximación Metodológica**|
|---|---|
|**DE REQUISITOS**|•<br>_Metodología Legal-Analítica_: Se utilizará la Ley 1448/2011, la Ley 2421/2024 y otra<br>documentación del Proceso de Paz, para formalizar los criterios de calificación.<br>•<br>_Revisión Sistemática_: Se evaluarán las bases teóricas de la caracterización de roles y<br>las opciones de evaluación como 'LLM-as-a-judge' y 'JudgeBlender’ para<br>caracterización de hechos.<br>•<br>_Validaciones adicionales_: Se validarán las tecnologías requeridas para el proceso de<br>detección de falsedad, así como aquello que sea adicionalmente requerido para el<br>proceso de explicabilidad.<br>**Lista de Actividades**<br>✓ Definir y formalizar criterios de puntuación, para víctima, victimario y testigo<br>✓ Documentar excepciones legales para definición de víctima, victimario y testigo<br>✓ Revisión de arquitecturas, analizando y comparar las arquitecturas de LLMs y<br>estrategias de evaluación disponibles, determinando la tecnología más apropiada<br>para utilizar<br>✓ Revisión de tecnología utilizada para detección de falsedad<br>✓ Definición conceptual del modelo a desarrollar|
|**FASE 2**|A partir de la arquitectura definitiva, se recopila el corpus de entrevistas (cerca de 14.000 de<br>la CV) y se implementan protocolos éticos para la protección de la privacidad.|
|**PREPARACIÓN**<br>**DE DATOS Y**<br>**VALIDACIÓN DE**<br>**PROTOCOLOS**<br>**ÉTICOS**|**Aproximación Metodológica**<br>•<br>_Protocolo de validación de datos_: Implementar un proceso estricto de limpieza y<br>validación de los datos para mitigar sesgos hegemónicos<br>•<br>_Establecimiento de modelo final_: Formalizar la selección final del modelo (LLM único<br>o ensamble) basándose en la explicabilidad y minimización de sesgos, de acuerdo<br>con los datos extraídos<br>•<br>_Validación y establecimiento del Marco Ético:_Validar los protocolos éticos<br>requeridos y su implementación en el proyecto<br>**Lista de Actividades**<br>✓ Selección de la arquitectura y estrategia final<br>✓ Recolección y organización del Corpus<br>✓ Limpiezaycaracterización de datos|


------------------------- PAGINA 5 --------------------------

||✓ Definición de protocolos éticos, acorde a las recomendaciones legales locales e<br>internacionales<br>✓ Incorporación de los protocolos éticos a la arquitectura a implementar|
|---|---|
|**FASE 3**|Construcción e implementación del agente conversacional y del motor de evaluación, donde<br>se integrarán las técnicas de IA requeridas, como la detección de engaño y la Cadena de<br>Pensamiento (CoT) para la explicabilidad.|
|**DESARROLLO E**<br>**INTEGRACIÓN**|**Aproximación Metodológica**|
|**DEL MODELO**|•<br>_Desarrollo Modular e Integrado_: Construir el agente conversacional y el agente de<br>validación como elementos independientes y realizar su integración como una única<br>solución<br>•<br>_Afinamiento con características de estilo_: Integrar la extracción de características<br>emocionales y estilométricas para la detección de engaño, alimentando el LLM<br>•<br>_Construcción de la herramienta visual_: Implementación de la herramienta visual,<br>que facilite la utilización del usuario final y del administrador (investigador).<br>**Lista de Actividades**<br>✓ Implementar el agente para guiar las entrevistas a partir de los relatos del corpus y<br>los requisitos definidos<br>✓ Configuración del Motor de Evaluación, que aplique la puntuación graduada de los<br>actores<br>✓ Integración de la explicabilidad, como una Cadena de Pensamiento (CoT) que<br>genere pasos de razonamiento intermedios y permita interpretar los motivos de la<br>puntuación propuesta<br>✓ Integración de modelos de detección de Engaños, que permitan detectar<br>incongruencias y falsedad usando el LLM y rasgos emocionales<br>✓ Entrenamiento y afinamiento del modelo, con los datos validados para la<br>caracterización de roles.<br>✓ Construcción final de la herramienta visual, que permita utilizar el sistema por un<br>usuario final y por un investigador de plataforma|
|**FASE 4**<br>**VALIDACIÓN Y**<br>**DISEÑO DE**<br>**PUESTA EN**<br>**OPERACIÓN**|Se lleva a cabo la fase de pruebas del modelo para asegurar el cumplimiento de la<br>funcionalidad esperada y garantizar su trazabilidad. Además, se formula el plan de<br>despliegue operacional y se elabora la documentación final, que incluye tanto el manual de<br>usuario como el informe completo del trabajo de grado.<br>**Aproximación Metodológica**<br>•<br>_Validación de Concordancia_: Evaluar que el LLM logre una concordancia idónea con<br>los criterios de evaluadores humanos<br>•<br>_Planificación de Despliegue Operacional_: Diseñar la arquitectura para una posible<br>implementación real, detallando recursos y documentación de usabilidad<br>•<br>_Informe final del trabajo de grado_: Redacción y organización del Informe Final del<br>Trabajo de Grado.<br>**Lista de Actividades**<br>✓ ValidaciónyPruebas del Modelo,midiendo laprecisión,robustezyefectividad de la|


------------------------- PAGINA 6 --------------------------

- mitigación de sesgos.

- ✓ Análisis de la explicabilidad y trazabilidad, verificando que el proceso de caracterización sea transparente y justificable

- ✓ Formulación del plan de despliegue, detallando la arquitectura, los recursos computacionales y la documentación de usabilidad/ética necesarios

- ✓ Análisis final de resultados, documentando los resultados obtenidos para generar las conclusiones

- ✓ Redacción del informe final y preparación para la presentación del Trabajo de Grado


------------------------- PAGINA 7 --------------------------

## **RESULTADOS ESPERADOS**

Documento de levantamiento de información del proyecto, que incluye:

- Criterios de puntuación para víctima, victimario y testigo, acorde a la documentación y las excepciones previstas en la ley y en la documentación de la Comisión de la Verdad

- Arquitecturas existentes de LLM como agente conversacional como juez, y los criterios de evaluación del proyecto para la decisión, estableciendo la decisión final de la arquitectura a utilizar

- Tecnología final a utilizar de detección de falsedad y la metodología de inclusión en el proyecto

## **ASIGNATURA MISyC PROYECTO 1**

- Protocolo de validación de datos, que será utilizado para la recopilación del corpus de entrevistas

Documento de diseño del proyecto, que incluye:

- Arquitectura final del modelo a implementar, integrando el agente conversacional, el agente evaluador de criterios y el agente de detección de falsedad, así como cualquier otro agente -o módulo- requerido en la implementación acorde al levantamiento detallado.

- Informe del proceso de recolección de datos, con los problemas encontrados, excepciones y limpieza realizada

- Inclusión del Protocolo Ético a utilizar en el proyecto, según las normativas vigentes

Artículo con el estado del arte del proyecto y los aspectos más relevantes del levantamiento y diseño.

Implementación del modelo acorde a la arquitectura planteada y los módulos esperados

Implementación de la aplicación visual, que le permita la utilización del modelo por los usuarios evaluados y los usuarios investigadores.

Documento de implementación, con el detalle del proceso de entrenamiento, resultados de **ASIGNATURA** las pruebas realizadas, problemas encontrados y limitaciones de la implementación. **MISyC** Documento de utilización de la aplicación final, tanto para usuarios finales como para **PROYECTO 2**

Documento de utilización de la aplicación final, tanto para usuarios finales como para investigadores.

Redacción del informe final y preparación para la presentación del Trabajo de Grado

Artículo con los aspectos más relevante de la implementación del proyecto, los resultados, la aplicación final y las conclusiones.


------------------------- PAGINA 8 --------------------------

## **PROSPECTIVA DE INNOVACIÓN**

|**POTENCIAL DE**<br>**INNOVACIÓN**|Este proyecto presenta un significativo potencial de innovación al aplicar una tecnología de<br>vanguardia como los Modelos de Lenguaje Grandes (LLMs) a un desafío social y humanístico<br>de alta complejidad: el análisis de testimonios del conflicto armado colombiano. La principal<br>innovación radica en superar las clasificaciones tradicionales y rígidas de los actores del<br>conflicto: en lugar de asignar etiquetas binarias, el modelo busca desarrollar una<br>caracterización matizada que refleje el grado de participación de una persona en los hechos,<br>reconociendo la naturaleza a menudo difusa y compleja de los roles de víctima, victimario o<br>testigo. Esta aproximación no solo responde a la necesidad de lecturas menos simplistas del<br>conflicto, sino que también ofrece una solución eficiente, al permitir procesar y analizar de<br>manera eficiente un vasto volumen de relatos, en contraste con su realización de forma<br>manual por evaluadores humanos.<br>Adicionalmente, el proyecto es innovador por su compromiso con la**transparencia y la**<br>**robustez**en un ámbito tan sensible. La propuesta no se limita a generar una clasificación,<br>sino que busca construir un sistema cuyo razonamiento sea explicable y auditable,<br>permitiendo a los investigadores comprender los motivos detrás de la caracterización<br>propuesta. Se contempla también la integración de técnicas analíticas para identificar<br>incongruencias en los testimonios, fortaleciendo la integridad del análisis. Al combinar una<br>metodología de caracterización flexible con un enfoque en la explicabilidad y la fiabilidad, la<br>iniciativa se perfila como una herramienta pionera para la construcción de la memoria<br>histórica y el esclarecimiento de la verdad en Colombia.|
|---|---|
|**PROPIEDAD**<br>**INTELECTUAL**|El proyecto se enmarca en el contexto de investigación delineado por el Ingeniero Luis<br>Gabriel Moreno PhD., con el objetivo de profundizar en la utilización de LLMs como agentes<br>conversacionales para caracterización de actores del conflicto armado colombiano. Cabe<br>destacar que este proyecto de investigación será propiedad intelectual exclusiva del<br>estudiante, y los resultados obtenidos se plasmarán en artículos de investigación destinados<br>a la difusión del conocimiento.|


------------------------- PAGINA 9 --------------------------

## **BIBLIOGRAFÍA**

- [1] Comisión para el Esclarecimiento de la Verdad, la Convivencia y la No Repetición, «Hay Futuro si hay Verdad - Informe Final», Comisión para el Esclarecimiento de la Verdad, la Convivencia y la No Repetición, Bogotá, Colombia, 2022.

- [2] Departamento Administrativo de la Función Pública - República de Colombia, Ley 1448/2011. 2011.

- [3] Departamento Administrativo de la Función Pública - República de Colombia, Ley 2421/2024. 2024.

- [4] «Archivo del Esclarecimiento de la Verdad». Accedido: 7 de noviembre de 2025. [En línea]. Disponible en: https://archivo.comisiondelaverdad.co/analisis-del-proceso-discursivo-emotivo-dentro-de-losacontecimientos-del-conflicto-armado

- [5] L. G. Moreno, «Inteligencia Artificial para entender el conflicto colombiano». Accedido: 23 de septiembre de 2025. [En línea]. Disponible en: https://www.javeriana.edu.co/pesquisa/inteligenciaartificial-conflicto/

- [6] Tangarife Patiño, Ana Maria, «Modelo semántico y computacional para análisis del conflicto armado en Colombia», Tesis Doctoral, Universitat Pompeu Fabra, Barcelona, Institut de Lingüistica Aplicada, 2024.

- [7] R. Hu et al., «Training an LLM-as-a-Judge Model: Pipeline, Insights, and Practical Lessons», en WWW Companion 2025 - Companion Proceedings of the ACM Web Conference 2025, Association for Computing Machinery, Inc, 2025, pp. 228-237.

- [8] L Zheng et al., «Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena», 24 de diciembre de 2023, arXiv: arXiv:2306.05685. doi: 10.48550/arXiv.2306.05685.

- [9] C. Jiang y X. Yang, «AgentsBench: A Multi-Agent LLM Simulation Framework for Legal Judgment Prediction.», Systems, vol. 13, n.º 8, p. 641, ago. 2025, doi: 10.3390/systems13080641.

- [10] H. A. Rahmani, E. Yilmaz, N. Craswell, y B. Mitra, «JudgeBlender: Ensembling Automatic Relevance Judgments», en WWW Companion 2025 - Companion Proceedings of the ACM Web Conference 2025, Association for Computing Machinery, Inc, 2025, pp. 1268-1272.

- [11] E. M. Bender, A. McMillan-Major, T. Gebru, y S. Shmitchell, «On the dangers of stochastic parrots: Can language models be too big?», en FAccT 2021 - Proceedings of the 2021 ACM Conference on Fairness, Accountability, and Transparency, Association for Computing Machinery, Inc, 2021, pp. 610-623.

- [12] C. Zhou, Y. Zhang, C. Lin, y S. Zhou, «A deception detection model by using integrated LLM with emotion features.», Scientific Reports, vol. 15, n.º 1, pp. 1-19, 2025.

- [13] Z. A. Szojka, S. Yashraj, y T. D. Lyon, «Automated question type coding of forensic interviews and trial testimony in child sexual abuse cases.», Law and Human Behavior, vol. 49, n.º 2, pp. 163-172, 2025.

- [14] G. M. Lucas, J. Gratch, A. King, y L.-P. Morency, «It’s only a computer: Virtual humans increase willingness to disclose», Computers in Human Behavior, vol. 37, pp. 94-100, ago. 2014, doi: 10.1016/j.chb.2014.04.043.

- [15] Gonzalez, R. & Pomares Quimbaya, A. (2012). La investigación científica basada en el diseño como eje de proyectos de investigación en ingeniería. En: Reunión Nacional ACOFI 2012 en la calidad en las facultades de ingeniería y su impacto en el desarrollo nacional.

- [16] UNESCO, «Recomendación sobre la Ética de la Inteligencia Artificial», Organización de las Naciones Unidas para la Educación, la Ciencia y la Cultura, 2021. [En línea]. Disponible en: https://unesdoc.unesco.org/ark:/48223/pf0000380455_spa

- [17] J. Muraszkiewicz y J. Cadman, «Leveraging Victim Voices: Unveiling True Needs Through Natural Language Processing in Trauma Narratives.», Journal of Victimology & Victim Justice, vol. 7, n.º 2, pp. 133-144, 2024.
