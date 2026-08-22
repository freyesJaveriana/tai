# Estado del arte — Diálogos para la Memoria

> **En [`docs/pvb.md`](../../docs/pvb.md): no lo cita** · **En [`docs/critica.md`](../../docs/critica.md): no lo cita**  
> Reyes Palacio, F. (2025). *Estado del arte: Diálogos para la Memoria*. Pontificia Universidad Javeriana. Director: Ing. Luis Gabriel Moreno.  
> 
> _Ningún documento del repositorio lo cita actualmente._  
> Documento origen: `Trabajo_Grado/Estado_del_arte_Dialogos_para_la_memoria.docx`


**Origen:** `Trabajo_Grado/Estado_del_arte_Dialogos_para_la_memoria.docx` — documento propio del autor  
**Fecha:** 7 de octubre de 2025  
**Nota:** convertido desde DOCX con Pandoc. **Este documento no lleva separadores de página**: un DOCX no tiene paginación fija, así que para citarlo hay que referirse a su sección o encabezado, no a un número de página.


| *Por: Ing. Felipe Reyes Palacio* | *Director: Ing. Luis Gabriel Moreno* |
|----------------------------------|--------------------------------------|

# Introducción

El informe de la comisión de la verdad, “Hay Futuro si Hay Verdad” \[4\] establece una premisa fundamental del Acuerdo de Paz: el esclarecimiento de lo ocurrido durante más de seis décadas de conflicto armado es la guía para una paz duradera en Colombia. Este proceso, que no concluyó con los acuerdos de 2016, busca 'promover el reconocimiento de responsabilidades' y exige un esfuerzo continuo para alcanzar una reconciliación completa.

La comisión invita a “alejarnos de las lecturas simplistas y binarias”\[4\] , que dividen a los actores del conflicto en “buenos” y “malos”. La realidad es más compleja: muchas víctimas fueron victimarios a fuerza, y muchos llamados victimarios -como el ejército- fueron víctimas, o sus familias.

Este ha sido un proceso largo y complejo, que ha llevado al país a la deshumanización: “o mi enemigo se muere o yo me muero, todo el que sea sospechoso es un enemigo para mí” (2022, Comisión de la verdad) y por ello, es imprescindible buscar herramientas para avanzar: para colocar la vista en el futuro, lleno de posibilidades y oportunidades.

En este contexto, crear mecanismos objetivos y eficientes para caracterizar a los actores del conflicto es un deber fundamental con las víctimas. Respondiendo al llamado del Centro Nacional de Memoria Histórica de “utilizar todas las herramientas necesarias para encontrar la verdad”, este proyecto propone un modelo conversacional para caracterizar el rol de cada actor como víctima, victimario o testigo. El objetivo es optimizar el proceso de esclarecimiento a través de entrevistas guiadas por esta herramienta tecnológica, favoreciendo así la justicia.

Se pretende el uso de un LLM porque “LLM como juez es una forma escalable y explicable de aproximarse a las preferencias humanas, que de otro modo son muy costosas de obtener.” (2023, Zheng).

# Marco Conceptual del Conflicto Armado Colombiano

Si bien, dar un marco conceptual profundo del Conflicto Armado es una tarea demasiado extensa, incluso para este trabajo completo, se hace fundamental validar las definiciones básicas de los términos más relevantes de este trabajo en los documentos que ya han profundizado en el Conflicto Armado, y que pueden dar luz para indicar el camino a seguir en el proyecto.

## Definición de víctima, victimario y testigo

La ley 1448 de 2011 define como víctima a “aquellas personas que individual o colectivamente hayan sufrido un daño por hechos ocurridos a partir del 1° de enero de 1985, como consecuencia de infracciones al Derecho Internacional Humanitario o de violaciones graves y manifiestas a las normas internacionales de Derechos Humanos, ocurridas con ocasión del conflicto armado interno” (Art. 3, Ley 1448/2011). El reconocimiento de una víctima se hace prioritario para el estado, de forma tal que éste pueda implementar las medidas en su beneficio, así como el restablecimiento de sus derechos básicos: la verdad, la justicia y la reparación integral.

Luego de la promulgación de la primera ley de reparación de víctimas (1448/2011), muchas otras leyes y decretos fueron promulgados, ampliando u corrigiendo diferentes aspectos, como los conceptos mismos. Por ejemplo, en el 2024 el concepto de víctima “se amplía con -Delitos Ambientales-, -Victimas en el Exterior-, -Familia de Crianza- y -Personas desplazadas y confinadas- (Ley 2421/2024), por lo que se hace fundamental mantener estos criterios para una correcta caracterización.

Por otra parte, se define el victimario como el “autor de la conducta punible, el directamente responsable del delito, o el miembro de un grupo armado organizado al margen de la ley.” (Ley 1448/2011). En esencia, el victimario es la persona o grupo que causa el daño a la víctima en el contexto del conflicto armado.

Finalmente, acerca del concepto de “testigo”, la ley hace referencia “como personas que tienen conocimiento de los hechos y cuya declaración es relevante en los procedimientos administrativos y judiciales relacionados con la reparación de las víctimas.” (Ley 1448/2011). La importancia del testigo radica en su papel crucial para el esclarecimiento de la verdad y la impartición de justicia, incluso si éste es víctima o victimario. El testimonio de un testigo puede ser fundamental para probar los hechos victimizantes, y para identificar a los verdaderos responsables. Es por esta razón que la ley contempla “medidas especiales de protección, para las víctimas y los testigos cuando exista un riesgo para su vida, seguridad o libertad debido a su participación en procesos judiciales o administrativos”. (Art. 16, Ley 2421/2024).

## Justicia Transicional y la Verdad

Todos estos conceptos nacen a la luz de la llamada “Justicia Transicional”; figura que nace con los acuerdos de paz. La Justicia Transicional se entiende como "los diferentes procesos, mecanismos y medidas de carácter judicial y no judicial, que se empleen para dar solución a las graves violaciones de los derechos humanos, crímenes de guerra y de lesa humanidad cometidos en el marco del conflicto armado en Colombia" (Art. 8, Ley 1448/2011) Su importancia, de acuerdo con la ley, radica en su finalidad principal: garantizar los derechos de las víctimas a la justicia, la no repetición, la verdad, el perdón y la reparación integral. Es, dentro del marco de esta justicia transicional, donde caracterizar víctimas, victimarios y testigos es fundamental para su accionar.

Es fundamental entonces, para que prevalezca la justicia, definir la verdad en este contexto. “La verdad es reconocida como un derecho fundamental e irrenunciable, tanto para las víctimas como para la sociedad en general. Su importancia radica en que es un pilar esencial del marco de justicia transicional, indispensable para lograr la reparación, la justicia y, en última instancia, la reconciliación y la paz.” (Ley 1448/2011). Se menciona también la “Reparación Simbólica, que se vincula directamente con la necesidad de asegurar (...) el esclarecimiento de la verdad" (Art. 40, Ley 2421/2024). La verdad no es solo un derecho, sino se convierte en la única forma de reparar, de sanar, de avanzar con piso firme hacia la paz. La verdad es mencionada como derecho, pero también como mecanismo, como un accionar: en los informes de la CNMH es “Indicador de Gestión”,” Insumo para el esclarecimiento” y “Base de productos concretos para lograr la reparación”. Va más allá de un derecho para ser acción necesaria.

Favorecer los objetivos de la Dirección de Acuerdos de Verdad (DAV) es también una aplicación del proyecto, los cuales se enumeran como: a) “Certificar la contribución a la verdad de las personas que fueron parte de estos grupos y que por no cometer graves violaciones a los Derechos Humanos no fueron acogidas por la Ley 975 de -Justicia y Paz-, y con ello ofrecer la posibilidad de resolver su situación jurídica”, y b) Con los relatos y testimonios de su paso por el Grupo Armado Organizado al Margen de la Ley - GAOML, contribuir al esclarecimiento de sus patrones y causas explicativas.” (Informe de Gestión CNMH, 2024). Estos dos objetivos están dentro de las posibilidades que brinda el proyecto, directamente en relación con la contribución a la verdad, mediante los relatos y testimonios.

Sin embargo, la clasificación de estos roles presenta complejidades significativas que desafían una categorización estricta. Por ejemplo, aunque la ley establece que 'los miembros de grupos armados organizados al margen de la ley no serán considerados víctimas' (Ley 1448/2011 y ley 2421/2024), introduce excepciones cruciales, como el caso de los menores de edad reclutados ilícitamente. De manera similar, miembros de la Fuerza Pública pueden ser reconocidos como víctimas bajo ciertas condiciones. Por lo tanto, en la práctica, las líneas que dividen a víctimas y victimarios son a menudo tenues. Esto sugiere que, en lugar de una clasificación rígida, se debe buscar una forma de medir el *nivel* en que un actor encarna cada uno de estos roles.

# Aproximación tecnológica 

Para abordar este proyecto, podemos referirnos, al trabajo de Szojka, Yashraj y Lyon, quienes demostraron la alta eficacia de un modelo de lenguaje grande (RoBERTa) al entrenarlo con un corpus de 351,920 declaraciones de entrevistas forenses y testimonios judiciales. El modelo logró clasificar de manera fiable distintos tipos de preguntas (invitaciones, preguntas 'wh', preguntas de opción múltiple y no-preguntas), alcanzando una precisión final del 98%. A partir de estos datos, “se puede determinar que un modelo automatizado no solo puede ser más rápido, sino también más preciso que los codificadores humanos, corrigiendo errores que se produjeron en la codificación manual inicial. Este hallazgo subraya el potencial de los LLMs para realizar tareas de clasificación de texto de manera eficiente y con una precisión superior a la humana." (Szojka, Yashraj y Lyon (2025))

Existen otros autores, como Sosa y Lopez, que ya trabajaron en diferentes aspectos del conflicto armado con IA, y que a partir de su trabajo demuestran que "…esta evidencia empírica no solo valida cuantitativamente la prevalencia del dolor y la denuncia en los relatos, sino que también aporta una dimensión emocional clave para comprender la profundidad del daño expresado en el proceso judicial y restaurativo" (Sosa, Lopez 2025).

El camino con diferentes aproximaciones de IA se ha avanzado, y los documentos necesarios para poder realizar esta investigación están ya disponibles, como lo demuestra con el trabajo de Luis Gabriel Moreno, donde afirma que se debe “Usar la Inteligencia Artificial para construir memoria” (Moreno, Luis Gabriel, 2024) donde ha recorrido ya parte de este camino, que se espera complementar a partir de esta nueva investigación.

El modelo de Patiño sobre el conflicto armado, que ha desarrollado tareas paralelas a la planteada, afirma que "…la tesis se halla en la intersección entre tecnologías del lenguaje, documentación, lingüística de corpus y terminología en lo que puede llamarse como un dominio de conocimiento que está integrado por la documentación y los discursos que alrededor del tema del conflicto armado colombiano han construido profesionales y comunidades que se han dedicado al estudio, investigación, denuncia y atención sobre este fenómeno" (Patiño, 2024). Por lo tanto, se cuenta ya con trabajos que no solo han abordado diferentes aspectos del conflicto, sino que brindan las herramientas sobre las cuales se sustentará este proyecto.

Existen grandes retos por enfrentar en el procesamiento de diálogos humanos; uno de los más importantes, es la validación y detección de engaños. Sin embargo, Zhou menciona en su trabajo que "utilizando el modelo de lenguaje grande RoBERTa, extrajimos valores de características emocionales de los textos de los interrogatorios y los combinamos con las características existentes antes de introducirlos en XGBoost para la detección de engaños." (Zhou et. Al. 2025). Esto significa que, usando trabajos recientes de otros autores, es posible complementar y apoyar el trabajo actual para detectar falsedad, incongruencia y engaño, y tratar así de filtrar las mentiras y tratar de insistir en la verdad.

Para la evaluación de testimonios, tradicionalmente se ha considerado la información de contenido. Sin embargo, un enfoque más reciente se basa en el análisis de características estilométricas para capturar el estilo de la narración. "Este enfoque se basa en la premisa de que, dado que los testimonios se transmiten a través de narrativas, las pistas lingüísticas pueden aprovecharse eficazmente para detectar el engaño. \[...\] Más recientemente, también se han explorado los modelos de lenguaje grandes para este propósito" (Sóla-Sales et.al, 2025). La perspectiva de Sola en el manejo de testimonios es muy acertada, ya que sugiere que un modelo conversacional puede no solo registrar, sino también analizar las características del lenguaje para una caracterización más profunda de los actores, que es justamente el propósito de este trabajo.

La tecnología inicialmente considerada para este proyecto es 'LLM-as-a-judge', la cual ofrece beneficios clave como la escalabilidad y la explicabilidad en la evaluación de narrativas, tal como lo plantea Zheng. Asimismo, él menciona que "LLM-as-a-judge ofrece dos beneficios clave: escalabilidad y explicabilidad: “los jueces LLM proporcionan no solo puntuaciones sino también explicaciones, haciendo que sus resultados sean interpretables..."(Zheng, 2023).

Sin embargo, aunque esta tecnología plantea un camino claro de ejecución, otras propuestas, como la de Rahmani para la caracterización de los actores, si bien se apoyan en la validación de Modelos de Lenguaje Grandes (LLMs) como "jueces" o evaluadores de narrativas, reconocen que el uso de un único LLM puede introducir sesgos y altos costos. Rahmani adopta un enfoque basado en el framework “JudgeBlender”, que “en lugar de depender de un solo modelo \[…\] propone emplear un -panel de evaluadores diversos-, utilizando un ensamble de LLMs más pequeños para generar juicios de relevancia más robustos y precisos” (Rahmani et. Al, 2025). El autor indica además que “al agregar las perspectivas de múltiples modelos, se aprovechan sus fortalezas complementarias, lo que permite minimizar las debilidades individuales y reducir los sesgos inherentes que un solo modelo podría presentar” (Rahmani et. Al, 2025). Será importante evaluar la mejor alternativa en esta investigación.

La explicabilidad del LLM también será un factor fundamental para considerar, tal como menciona Ma utilizando “Cadenas de Pensamiento”. "El enfoque de Cadena de Pensamiento (CoT) mejora significativamente las capacidades de razonamiento de los modelos de lenguaje grandes (LLMs) al generar pasos de razonamiento intermedios, que descomponen eficazmente tareas complejas en subtareas secuenciales. Este enfoque \[...\] aumenta así tanto la explicabilidad como la credibilidad del modelo" (Ma. et. al, 2025). La explicabilidad, es decir, la transparencia no solo de los resultados sino del camino seguido por el modelo para dar resultados, serán altamente relevantes en la ejecución.

Finalmente, para determinar si existe la información suficiente y relevante para realizar la tarea, se cuenta con la estadística de la CV que indicó que “se realizaron cerca de 14.000 entrevistas y se establecieron conversaciones con más de 30.000 personas de todos los sectores sociales, regiones, identidades étnicas, experiencias de vida, tanto dentro de nuestras fronteras como fuera de ellas” (2022, Comisión de la verdad), donde además, otros autores ya han hecho caracterizaciones, thesaurus y ontologías, que darán contexto y enriquecerán el modelo a desarrollar. Por tanto, se considera que se cuenta con la información necesaria para poder realizar esta investigación.

# Consideraciones éticas y Metodológicas

Un desafío ético central es el sesgo en los evaluadores automáticos. Como advierte Li et al. (2025), la relación entre los datos y los evaluadores puede 'sesgar sistemáticamente las evaluaciones, comprometiendo la equidad y fiabilidad' del sistema. Esto podría conducir a riesgos éticos en tareas posteriores de toma de decisiones. Esta preocupación resuena con la afirmación de Bender et al. (2021) de que los LLMs entrenados con datos no curados 'codifican visiones hegemónicas perjudiciales'. En esencia, se aplica el principio conocido en informática como 'Garbage In, Garbage Out': un modelo excelente no producirá resultados fiables si se alimenta con información sin validar. Para mitigar este riesgo, será indispensable un cuidadoso proceso de limpieza y validación de los datos de entrenamiento.

Otro aspecto que se deberá tener en cuenta, dadas las recomendaciones globales de entidades internacionales como la Unesco, es la privacidad. "La privacidad, que constituye un derecho esencial para la protección de la dignidad, la autonomía y la capacidad de actuar de los seres humanos, debe ser respetada, protegida y promovida a lo largo del ciclo de vida de los sistemas de IA. Es importante que los datos para los sistemas de IA se recopilen, utilicen, compartan, archiven y supriman de forma coherente con el derecho internacional y acorde con los valores y principios enunciados en la presente Recomendación" (UNESCO, 2021). El modelo finalmente utilizado, aunque entrenado con información públicamente disponible, al momento de evaluar a nuevos actores y ser utilizada en la vida real, deberá implementar mecanismos que permitan controlar la información privada de los entrevistados. El objetivo de caracterizar (y dar criterios de caracterización) a los actores es justamente buscar justicia y verdad, por lo cual será fundamental la protección de los datos personales, y la anonimización cuando sea necesaria.

Asumiendo estos riesgos controlados, la aproximación de LLM parece acertada y cercana al propósito final, dado que "…este enfoque innovador aprovecha las capacidades intrínsecas de los LLMs para proporcionar evaluaciones detalladas (fine-grained), y se ha demostrado que los LLMs pueden alcanzar altas tasas de concordancia con los evaluadores humanos , sirviendo <u>eficazmente como sustitutos</u> de las métricas de evaluación tradicionales". (Hu et. al, 2025). Es decir, aunque los riesgos existen y deben ser tenidos en cuenta, es probable que se pueda obtener un producto que sea igual o mejor que la actual metodología de evaluación.

Finalmente, Muraszkiewicz afirma acertadamente que "…existen numerosos temores éticos, que abarcan preocupaciones como la obtención del consentimiento informado de los participantes, la salvaguarda de su confidencialidad, la garantía de su seguridad durante el proceso de la entrevista y el abordaje de temas sensibles o emocionalmente cargados. La gestión de estos aspectos éticos y prácticos requiere una planificación cuidadosa y la adhesión a directrices éticas para proteger tanto a los investigadores como a los participantes" (Muraszkiewicz, 2024)

# Conclusiones Preliminares

Ciertamente, se enfoca el trabajo siempre en víctimas, victimarios y testigos, pero a veces dejamos de lado a los investigadores de estas entrevistas, que son históricamente los encargados de procesar estos relatos y extraer de ellos la verdad. "Tomando nota de todo lo anterior, los autores de este artículo y los colegas con los que trabajan se sintieron motivados a diseñar metodologías innovadoras para amplificar las voces de las víctimas, todo ello mientras se les evita soportar entrevistas prolongadas y se protege a los investigadores del coste emocional de leer innumerables relatos angustiosos" (Muraszkiewicz, 2024). Muraszkiewicz afirma que este coste emocional; que ahora sería realizada por una máquina de inferencias como lo es un LLM, se evita de forma sustancial, dado que la LLM puede buscar sus conclusiones sin que los relatos lo afecten, como afectarían a un juez humano. Por lo tanto, se puede beneficiar tanto los actores directos -victimas, victimarios y testigos- como los indirectos, en este caso, los investigadores y jueces del proceso.

Otro aspecto destacable; cuando se controlan los sesgos; es que la LLM puede ser objetiva y evitar ser manipulada, al ser instruida para ello. Se considera que podría emitir juicios que, aunque al final pudieran ser revisados por una persona quien tomaría las decisiones finales, podría acortar de forma importante el camino para este proceso.

Finalmente, una LLM, a partir de su diseño natural, podría facilitar el encontrar relaciones entre la información entregada por los actores con información de entrenamiento, o encontrar patrones que no son demasiado evidentes en la información entregada. El LLM puede ser un investigador atento, que no se cansa, siempre disponible en cualquier momento y listo para escuchar, lo que podría facilitar enormemente el trabajo de otros investigadores y jueces, así como ser quizás, para algunos actores, una forma más fácil de contar la verdad, por su carácter anónimo.

# Bibliografia

1.  Bender, E. M., McMillan-Major, A., Gebru, T., & Shmitchell, S. (2021). On the dangers of stochastic parrots: Can language models be too big? *FAccT 2021 - Proceedings of the 2021 ACM Conference on Fairness, Accountability, and Transparency*, 610-623. <https://research.ebsco.com/linkprocessor/plink?id=dfd0947b-fb09-3d5f-b3a0-eb75af55fbff>

2.  Centro Nacional de Memoria Histórica (CNMH). (2021). *Informe de Gestión 2021*. Centro Nacional de Memoria Histórica.

3.  Centro Nacional de Memoria Histórica (CNMH). (2024). *Informe de Gestión 2024*. Centro Nacional de Memoria Histórica.

4.  Comisión para el Esclarecimiento de la Verdad, la Convivencia y la No Repetición. (2022). *Hay Futuro si hay Verdad—Informe Final*. Comisión para el Esclarecimiento de la Verdad, la Convivencia y la No Repetición.

5.  Hu, R., Cheng, Y., Shi, X., Lin, W., Meng, L., Xia, J., & Zong, Y. (2025). Training an LLM-as-a-Judge Model: Pipeline, Insights, and Practical Lessons. *WWW Companion 2025 - Companion Proceedings of the ACM Web Conference 2025*, *null*, 228-237. <https://research.ebsco.com/linkprocessor/plink?id=bdb51d59-6a5c-3e24-be25-a27c87a2d142>

6.  Ley 1448/2011 (2011), República de Colombia

7.  Ley 2421/2024 (2024), República de Colombia

8.  Li, D., Sun, R., Huang, Y., Zhong, M., Jiang, B., Han, J., Zhang, X., Wang, W., & Liu, H. (2025). *Preference Leakage: A Contamination Problem in LLM-as-a-judge* (No. arXiv:2502.01534). arXiv. <https://doi.org/10.48550/arXiv.2502.01534>

9.  Ma, H., Lu, Y., Feng, J., Zhang, H., Xiao, Z., & Yu, J. (2025). SDD-LawLLM: Advancing Intelligent Legal Systems Through Synthetic Data-Driven Fine-Tuning of Large Language Models. *Electronics (Switzerland)*, *14*(4). <https://research.ebsco.com/linkprocessor/plink?id=1c798799-b7c8-3692-8751-44a6d56aa5ef>

10. Moreno. (2024, mayo 29). *Inteligencia Artificial para entender el conflicto colombiano*. <https://www.javeriana.edu.co/pesquisa/inteligencia-artificial-conflicto/>

11. Muraszkiewicz, J., & Cadman, J. (2024). Leveraging Victim Voices: Unveiling True Needs Through Natural Language Processing in Trauma Narratives. *Journal of Victimology &amp; Victim Justice*, *7*(2), 133-144.

12. Patiño, A. M. T. (2024). *Modelo semántico y computacional para análisis del conflicto armado en Colombia*.

13. Rahmani, H. A., Yilmaz, E., Craswell, N., & Mitra, B. (2025). JudgeBlender: Ensembling Automatic Relevance Judgments. *WWW Companion 2025 - Companion Proceedings of the ACM Web Conference 2025*, *null*, 1268-1272. <https://research.ebsco.com/linkprocessor/plink?id=d76c2486-b4e9-3887-bc2c-d7de22292bec>

14. Solà-Sales, S., Alzetta, C., Moret-Tatay, C., & Dell’Orletta, F. (2025). When Time Matters: Exploring the Impact of Recall Techniques and Educational Levels on Witness Testimony Quality. *Information*, *16*(2). <https://research.ebsco.com/linkprocessor/plink?id=6998a6d4-659a-315e-9fb8-7600761b5da7>

15. Sosa, J., Urrego-López, A., Prieto, C., & Camargo-Díaz, E. J. (2025). *Constructing the Truth: Text Mining and Linguistic Networks in Public Hearings of Case 03 of the Special Jurisdiction for Peace (JEP)* (No. arXiv:2504.04325). arXiv. <https://doi.org/10.48550/arXiv.2504.04325>

16. Szojka, Z. A., Yashraj, S., & Lyon, T. D. (2025). Automated question type coding of forensic interviews and trial testimony in child sexual abuse cases. *Law and Human Behavior*, *49*(2), 163-172.

17. UNESCO. (2021). *Recomendación sobre la Ética de la Inteligencia Artificial*. Organización de las Naciones Unidas para la Educación, la Ciencia y la Cultura. <https://unesdoc.unesco.org/ark:/48223/pf0000380455_spa>

18. Zheng, L., Chiang, W.-L., Sheng, Y., Zhuang, S., Wu, Z., Zhuang, Y., Lin, Z., Li, Z., Li, D., Xing, E. P., Zhang, H., Gonzalez, J. E., & Stoica, I. (2023). *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena* (No. arXiv:2306.05685). arXiv. <https://doi.org/10.48550/arXiv.2306.05685>

19. Zhou, C., Zhang, Y., Lin, C., & Zhou, S. (2025). A deception detection model by using integrated LLM with emotion features. *Scientific reports*, *15*(1). <https://research.ebsco.com/linkprocessor/plink?id=49a91e4c-fddb-3707-8821-1076c572cc75>
