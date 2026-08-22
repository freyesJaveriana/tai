# Modelo semántico y computacional para análisis del conflicto armado en Colombia (tesis doctoral, Ana María Tangarife Patiño, UPF, 2024)

> **En [`docs/pvb.md`](../../docs/pvb.md): no lo cita** · **En [`docs/critica.md`](../../docs/critica.md): no lo cita**  
> Patiño, A. M. T. (2024). *Modelo semántico y computacional para análisis del conflicto armado en Colombia*. Tesis Doctoral, Universitat Pompeu Fabra, Barcelona.  
> 
> _Ningún documento del repositorio lo cita actualmente._  
> Fuente convertida: `1-papersMD/2-Pilar2-Cómo/Patino_Modelo_Semantico_Conflicto_Armado_Colombia_2024.md`


**Archivo origen:** `1-papers/2-Pilar2-Cómo/Patiño - Modelo semántico y computacional para análisis del conflicto armado en Colombia.pdf`  
**Páginas:** 253  
**Nota:** los separadores `PAGINA n` corresponden a la página física del PDF. Los encabezados y pies de página repetidos se conservan solo en su primera aparición.


------------------------- PAGINA 1 --------------------------

TESIS DOCTORAL UPF / 2024

Programa de doctorat: Doctorat en Traducció i Ciències del Llenguatge

Departament en Traducció i Ciències del Llenguatge

Modelo semántico y computacional para análisis del conflicto armado en Colombia

Ana María Tangarife Patiño

Directora: Dra. Mercè Lorente Casafont


------------------------- PAGINA 2 --------------------------

_El meollo de la cuestión es el siguiente: para nosotros la realidad es el mundo, y para las máquinas lo único real es la lengua._ Stanislaw Lem. Magnitud imaginaria

- _Lo que llamamos un mapa es un conjunto de líneas_

- _diversas que funcionan al mismo tiempo como armadura, premonición, código lingüístico y colección arbitraria de la memoria. Hay líneas que representan algo y otras que son abstractas. Las hay que forman contornos y las que no, éstas son las más hermosas. Las líneas son los_

- _elementos constitutivos de los acontecimientos, los que vivimos con otros, los que vivimos a solas, los que soñamos o tememos, algo así como un escenario_

- _dispuesto para el periplo de los deseos. También son las coordenadas que nos ayudan a perdernos, a agotar_

- _aquello que sabemos, y así llegar más rápido al cansancio y a la entrega._

- María Negroni. Pequeño mundo ilustrado

- _Oscilamos entre la ilusión de lo alcanzado y el vértigo de lo inasible. En nombre de lo alcanzado, queremos creer_

- _que existe un orden único que nos permitiría alcanzar de_

- _golpe el saber; en nombre de lo inasible, queremos pensar que el orden y desorden son dos palabras que designan_

   - _por igual el azar._

   - George Perec. Pensar/Clasificar


------------------------- PAGINA 3 --------------------------

# **Agradecimientos**

En el camino de pensar, experimentar y escribir esta tesis he tenido la fortuna de contar con invaluables apoyos y la compañía de amigos y familia especialmente. Agradezco:

A Simón, por ser fuerza y alegría e inspirarme a hacer lo mejor que puedo.

A mi madre Alba Lucía, por creerlo posible, nunca rendirse y ser sostén y fortaleza.

A mi padre Darío Antonio por su persistencia en el trabajo que ha sabido contagiar.

A José Alejandro por la prudencia y la cautela y saber observar más de lo aparente.

A Juan Andrés, por su tenacidad y persistencia para llevar a buen puerto los proyectos.

A Laurita, por ver el lado práctico y concreto y ser compañera en muchos momentos.

Quiero agradecer también a mis amigas y amigos por ser cómplices, por estar pendientes, cuidar los lazos y ayudar a sostener en momentos en que aparecían retos complicados. Gracias a quienes dispusieron de momentos para conversar y quienes me ayudaron a ver alguna cosa desde otras perspectivas. Gracias también a quienes fueron alegría o inspiración y me animaron con una palabra, un gesto, una canción, alguna historia.

Gracias a la Universidad de Antioquia, mi Alma Mater, que me ha permitido tener una comisión de estudios. Y a la Fundación Carolina por la beca que me ha permitido hacer las pasantías en España, lo cual fue una experiencia invaluable tanto en aspectos académicos como de crecimiento personal.

Gracias a mi directora, Mercè Lorente Casafont, por acompañar este trayecto y saber ver y hacer las preguntas que fueron orientando este camino.


------------------------- PAGINA 4 --------------------------

# **Resumen**

La disponibilidad de herramientas conceptuales para la descripción y la extracción en un determinado dominio de conocimiento es fundamental para garantizar el acceso a la información. En contextos de conflictos armados hay una profusa generación de documentos o materiales para la cual es importante diseñar herramientas y sistemas de gestión de la información adecuadas. Esta tesis aborda las estrategias terminológicas y computacionales necesarias para desarrollar un corpus sobre el conflicto armado en Colombia, los recursos de anotación del corpus, una ontología y un grafo de conocimiento.

La representación del conocimiento con fines de recuperación de información pasa por el ámbito de la terminología y las tecnologías de la lengua para usar recursos, técnicas y herramientas del procesamiento de lenguaje natural y de la lingüística computacional.

El reconocimiento de entidades nombradas es una tarea para la extracción de información en distintos ámbitos de conocimiento, partiendo de ontologías que recogen conceptualmente la terminología propia de dichos dominios. En esta tesis doctoral se conforma un corpus de textos o multimodales sobre el conflicto armado colombiano que son generados por instituciones, colectivos y organizaciones que trabajan en temas de paz, derechos humanos y memoria. Esta información constituye un corpus documental en el cual se usan técnicas de procesamiento de lenguaje natural para la extracción de relaciones desde el punto de vista conceptual contribuyendo al análisis y exploración de información desde su contenido.

Esta tesis propone un modelo semántico y computacional para la construcción de un grafo de conocimiento con técnicas de aprendizaje para el reconocimiento de entidades nombradas, en un campo de conocimiento en donde no existen suficientes ontologías o corpus previamente anotados. La tesis está centrada sobre el tratamiento de textos haciendo uso de técnicas de procesamiento de lenguaje natural para el descubrimiento de entidades nombradas con aprendizaje profundo que permita la construcción de un grafo de conocimiento a partir de una ontología de base, construida desde otras terminologías.


------------------------- PAGINA 5 --------------------------

Este estudio es un aporte a la construcción de herramientas para el español y para la gestión de conocimiento alrededor de temas del conflicto armado en Colombia y como metodología que puede ser extrapolable a otros dominios de conocimiento en donde no existen previamente ontologías o grafos.

**Palabras clave:** Reconocimiento de entidades nombradas, Grafos de conocimiento, Ontologías, Terminología, Conflictos armados.

# **Resum**

La disponibilitat d'eines conceptuals per a la descripció i l'extracció en un domini de coneixement determinat és fonamental per a garantir l'accés a la informació. En contextos de conflictes armats hi ha una generació profusa de documents o materials per als quals és important dissenyar eines i sistemes de gestió de la informació adequades.

Aquesta tesi aborda les estratègies terminològiques i computacionals necessàries per a desenvolupar un corpus sobre el conflicte armat a Colòmbia, els recursos d’anotació del corpus, una ontologia i un graf de coneixement.

La representació del coneixement amb finalitats de recuperació d'informació passa per l'àmbit de la terminologia i les tecnologies de la llengua per fer servir recursos, tècniques i eines del processament de llenguatge natural i de la lingüística computacional.

El reconeixement d'entitats nomenades (NER) és una tasca per a l'extracció d'informació en diferents àmbits de coneixement, partint d'ontologies que recullen conceptualment la terminologia pròpia dels dominis esmentats. En aquesta tesi doctoral es conforma un corpus de textos o multimodals sobre el conflicte armat colombià generats per institucions, col·lectius i organitzacions que treballen en temes de pau, drets humans i memòria. Aquesta informació constitueix un corpus documental en el qual es fan servir tècniques de processament de llenguatge natural per a l'extracció de relacions des del punt de vista conceptual per contribuir a l'anàlisi i exploració de la informació des del contingut.


------------------------- PAGINA 6 --------------------------

Aquesta tesi proposa un model semàntic i computacional per a la construcció d'un graf de coneixement amb tècniques d'aprenentatge per al reconeixement d'entitats nomenades, en un camp de coneixement on no hi ha prou ontologies o corpus prèviament anotats. La tesi se centra sobre el tractament de textos fent ús de tècniques de processament de llenguatge natural per al descobriment d'entitats nomenades amb aprenentatge profund, que permeti la construcció d'un graf de coneixement a partir d'una ontologia de base, construïda des d'altres terminologies.

Aquest estudi és una aportació a la construcció d'eines per a l'espanyol i per a la gestió de coneixement al voltant de temes del conflicte armat a Colòmbia i com a metodologia que pot ser extrapolable a altres dominis de coneixement on no hi ha prèviament ontologies o grafs.

**Paraules clau:** Reconeixement d'entitats anomenades, Grafs de coneixement, Ontologies, Terminologia, Conflictes armats.

# **Abstract**

The availability of conceptual tools for description and extraction in a knowledge domain is fundamental to ensure access to information. In armed conflict contexts there is a profuse generation of documents or materials for which it is important to design adequate information management tools and systems. This thesis approaches the terminological and computational strategies needed to develop a corpus on the armed conflict in Colombia, corpus annotation resources, an ontology and a knowledge graph.

Knowledge representation for information retrieval purposes goes through the field of terminology and language technologies to use resources, techniques and tools of natural language processing and computational linguistics.

The named entity recognition is a task of extraction of information from several fields of knowledge, based on ontologies that conceptually collect the terminology of these domains. In this doctoral thesis, a corpus of texts or multimodal texts on the Colombian armed conflict generated by institutions, collectives and organizations working on


------------------------- PAGINA 7 --------------------------

issues of peace, human rights and memory. This information is a documentary corpus in which natural language processing techniques are used for the extraction of relationships from a conceptual field, contributing to the analysis and exploration of information from its content.

This thesis proposes a semantic and computational model for the construction of a knowledge graph with learning techniques for the named entity recognition, in a field of knowledge where there are not enough ontologies or annotated corpora previously. The thesis is focused on the treatment of texts using natural language processing techniques for the discovery of named entities with deep learning that allows the construction of a knowledge graph from a base ontology, built from other terminologies.

This study contributes to the construction of tools for Spanish and for knowledge management around issues of the armed conflict in Colombia and as a methodology it that can be extrapolated to other knowledge domains where ontologies or graphs do not previously exist.

**Keywords:** Named entity recognition, Knowledge graphs, Ontologies, Terminology, Armed conflicts.


------------------------- PAGINA 8 --------------------------

# **Índice**

|Resumen............................................................................................................................ 3<br>|
|---|
|Índice................................................................................................................................. 7|
|Capítulo 1. Introducción..................................................................................................10|
|1.1. Justificación de la tesis....................................................................................... 10|
|1.2. Objetivos, preguntas de investigación e hipótesis..............................................14|
|1.3. Estado de la cuestión.......................................................................................... 17|
|1.4. Estructura de la tesis...........................................................................................20|
|Parte 1. Fundamentos...................................................................................................... 23|
|Capítulo 2. Corpus lingüístico sobre conflicto armado................................................... 24|
|2.1. Concepto de corpus............................................................................................ 24|
|2.2. Corpus sobre memorias en contextos de conflicto y violencia.......................... 27|
|2.3. El corpus del conflicto armado en Colombia..................................................... 29|
|Capítulo 3. Ontologías para representación de dominios................................................40|
|3.1. Clasificación de ontologías.................................................................................42|
|3.2. Métodos para desarrollar ontologías...................................................................47|
|3.3. Lenguajes para construir ontologías...................................................................51|
|Capítulo 4. Reconocimiento de entidades nombradas.....................................................58|
|4.1. Enfoques para el Reconocimiento de Entidades Nombradas............................. 59|
|4.2. Tareas para el reconocimiento de entidades de nombradas................................60|
|4.3. Tipos de entidades nombradas............................................................................64|
|4.4. Técnicas y métricas para evaluación.................................................................. 66|
|4.5. Reconocimiento de entidades nombradas para grafos de conocimiento............ 69|
|Capítulo 5. La terminología en el dominio de los conflictos armados............................74|
|5.1. Terminología metodológica de la tesis............................................................... 74|
|5.2. Valor terminológico del léxico en ámbitos de especialidad transdisciplinarios. 78|
|5.3. Entidades y clases del conflicto armado colombiano.........................................87|
|Capítulo 6. Grafos de conocimiento..............................................................................104|
|6.1. Definiciones y evolución histórica................................................................... 106|
|6.2. Componentes y tareas de un grafo de conocimiento........................................ 109|
|6.3. Metodologías, herramientas y lenguajes...........................................................111|
|6.4. Representación de conocimiento en grafos...................................................... 118|
|Capítulo 7. Aprendizaje automático para estudios del lenguaje....................................122|
|7.1. Métodos de aprendizaje y tipos de arquitectura............................................... 123|
|7.2. Aprendizaje profundo para extracción de entidades nombradas y poblamiento|
|de ontologías y grafos de conocimiento.................................................................. 125|


------------------------- PAGINA 9 --------------------------

|7.3. Modelos de lenguaje y transformers.................................................................130|
|---|
|Parte 2: Metodologías y desarrollos.............................................................................. 133|
|Capítulo 8. Corpus de entrenamiento y testeo...............................................................135|
|8.1. Fuentes de los datos y consideraciones para conformar el corpus................... 135|
|8.2. Preprocesamiento de dataset.............................................................................143|
|8.3. Características lingüísticas del corpus..............................................................145|
|Capítulo 9. Modelo para clasificación a partir del reconocimiento de entidades<br>nombradas sobre conflicto armado................................................................................150|
|9.1. Generalidades para la conformación de un modelo..........................................150|
|9.2. Clasificación de entidades a partir del corpus.................................................. 154|
|9.3. Extracción y resultados.....................................................................................158|
|Capítulo 10. Ontología sobre el dominio de conflicto armado......................................167|
|10.1. Metodología para la construcción de la ontología..........................................167|
|10.2. Estructura, conceptos y relaciones..................................................................174|
|10.3. Validación del modelamiento conceptual.......................................................195|
|Capítulo 11. Modelo para la construcción de un grafo de conocimiento sobre conflicto<br>armado........................................................................................................................... 202|
|11.1. Uso de grafos de conocimiento para representación de conocimiento sobre<br>conflictos armados...................................................................................................203|
|11.2. Metodología para la construcción del grafo................................................... 206|
|11.3. Estructura y componentes del grafo de conocimiento....................................208|
|Parte 3. Resultados........................................................................................................ 221|
|Capítulo 12. Conclusiones.............................................................................................221|
|Capítulo 13. Resultados, limitaciones y trabajo futuro................................................. 229|
|13.1. Resultados aplicados.......................................................................................229|
|13.2. Limitaciones del estudio.................................................................................231|
|13.3. Líneas de trabajo futuro..................................................................................233|
|Referencias bibliográficas............................................................................................. 237|
|Índice de anexos............................................................................................................ 251|

## **Índice de tablas y gráficos**

|Tabla 1. Recursos de información en sitios web de memoria sobre conflictos............... 31|
|---|
|Tabla 2. Recursos de información en sitios web de memoria en Colombia....................37|
|Tabla 3. Métodos clásicos para desarrollo de ontologías................................................ 48|
|Tabla 4. Lenguajes de ontologías.....................................................................................52|
|Gráfico 1. Diagrama de clases.........................................................................................90|
|Tabla 5. Clases, etiqueta, descripción y ejemplos........................................................... 91|
|Tabla 6. Metodologías de aprendizaje profundo para poblamiento de un grafo de|


------------------------- PAGINA 10 --------------------------

|conocimiento................................................................................................................. 128|
|---|
|Tabla 7. Instituciones de donde se recopilan las fuentes del corpus..............................137|
|Gráfico 2. Arquitectura general del proceso..................................................................142|
|Tabla 8. Tareas y datos de preprocesamiento................................................................ 143|
|Gráfico 3. Fases y datos sobre el preprocesamiento......................................................144|
|Gráfico 4. Ejemplos de fragmentos del corpus..............................................................147|
|Tabla 9. Ejemplos de entidades por clase con estructura sintáctica.............................. 148|
|Tabla 10. Ejemplos de anotación...................................................................................153|
|Tabla 11. Clases y_labels_para anotación....................................................................... 157|
|Gráfico 5. Ejemplos de clasificación y corrección........................................................163|
|Tabla 12. Ejemplos de tokens y clasificación por entidades......................................... 164|
|Tabla 13. Especificación de requisitos y preguntas de competencia para ontología sobre<br>conflictos armados.........................................................................................................170|
|Tabla 14. Fuentes de datos para reutilización................................................................173|
|Tabla 15. Primera clasificación de términos..................................................................176|
|Gráfico 6. Tipologías de entidades................................................................................ 180|
|Tabla 16. Descripción de fuentes conceptuales.............................................................182|
|Tabla 17. Distribución en clases de las entidades en terminologías..............................187|
|Tabla 18. Ejemplos de relación sujeto, predicado y objeto........................................... 188|
|Gráfico 7. Clases en Protègè..........................................................................................189|
|Tabla 19. Propiedades de las clases...............................................................................191|
|Gráfico 8. Diagrama de la clase Persona.......................................................................194|
|Gráfico 9. Propiedades de los objetos........................................................................... 196|
|Gráfico 10. Relación entre categorías y componentes del modelo................................205|
|Gráfico 11. Representación conceptual y representación computacional..................... 207|
|Gráfico 12. Ejemplo de nodos y aristas en el dominio..................................................212|
|Gráfico 13. Relación entre bloques del grafo................................................................213|
|Tabla 20. Lista de propiedades por clase.......................................................................214|
|Tabla 21. Relaciones entre nodos.................................................................................. 217|
|Gráfico 14. Componentes del grafo...............................................................................220|


------------------------- PAGINA 11 --------------------------

# **Capítulo 1. Introducción**

# **1.1. Justificación de la tesis**

El conocimiento es representado a partir del lenguaje y es fundamental comprenderlo para reconocer diferentes conceptos y denominaciones que existen sobre la realidad. Los estudios del lenguaje y de una terminología en dominios concretos son relevantes además para representar y organizar el conocimiento y para proveer de herramientas que faciliten los procesos de extracción y clasificación de información.

Este trabajo se plantea desde la necesidad de representar conceptualmente dominios de conocimiento explorando técnicas computacionales que permitan la extracción, clasificación y reconocimiento de entidades para el poblamiento de un grafo de conocimiento. Para ello se indaga sobre los corpus lingüísticos construidos dentro del dominio y sobre las estructuras de representación de ese conocimiento por medio de ontologías y grafos.

La tesis se halla en la intersección entre tecnologías del lenguaje, documentación, lingüística de corpus y terminología en lo que puede llamarse como un dominio de conocimiento que está integrado por la documentación y los discursos que alrededor del tema del conflicto armado colombiano han construido profesionales y comunidades que se han dedicado al estudio, investigación, denuncia y atención sobre este fenómeno.

Existe en la actualidad un desarrollo importante en los campos del procesamiento de lenguaje natural y la extracción de información, como muy recientemente se evidencia con la aparición de herramientas de inteligencia artificial que vienen a ampliar las maneras de relacionarnos con los contenidos y la información que se produce. Estos desafíos se dan en todos los niveles, pero en campos como la documentación, la lingüística y las tecnologías de lenguaje se presentan de manera aún más evidente.

La representación de conocimiento plantea una serie de desafíos que requieren una comprensión amplia de los contextos en los que la información relacionada se produce, además de reconocer los límites y alcances que la misma tecnología tiene. Cuando se


------------------------- PAGINA 12 --------------------------

pretende resolver la representación por medio del uso de herramientas computacionales los desafíos son aún mayores pues si ya la comprensión humana es compleja, proponer que la máquina “razone” y puede clasificar a partir de los sentidos de las palabras es mucho más desafiante.

El objeto de estudio de esta tesis doctoral es analizar un corpus sobre conflicto armado como dominio de especialidad con el fin de establecer un sistema de clases y entidades que permitan delimitar y estructurar conocimiento del ámbito para desarrollar aplicaciones diversas de clasificación y extracción de información. El centro del trabajo está relacionado con la terminología y las ontologías del conflicto armado, así como los desafíos de representación computacional de conocimiento en este dominio.

Este trabajo vincula tres categorías: la extracción de entidades nombradas como técnica para el reconocimiento de información significativa; las ontologías como herramienta que permite la presentación de axiomas y clases de dominios; y los grafos como herramienta de representación de conocimiento útil en la gestión de contenidos.

El aporte fundamental está en el cruce de ontologías para usos específicos en corpus sobre conflicto armado utilizando técnicas diversas que se describen en los apartados desarrollados a lo largo de la tesis. En términos generales, se realiza la exploración de técnicas para la extracción de entidades nombradas y se construye un sistema de clases a partir de la revisión de terminologías y marcos conceptuales sobre el dominio con las cuales establecer unas reglas, restricciones y clases sobre conflicto armado para la conformación de un grafo de conocimiento.

El interés por estudiar el corpus de este dominio se fundamenta en el reconocimiento de un fenómeno social que existe en Colombia ya por más de seis décadas y que ha implicado la confrontación y conflictos socio-políticos por el enfrentamiento de distintos grupos armados cuyas dinámicas son también complejas de establecer y definir. De acuerdo con cifras de la Comisión para el Esclarecimiento de la Verdad (2022), se estima que entre 1985 y 2018 perdieron la vida 450.664 personas bajo el delito de homicidio, 121.768 fueron desaparecidas forzadamente en el periodo entre 1985 y 2016, 50.770 fueron víctimas de secuestro y toma de rehenes entre 1990 y 2018,


------------------------- PAGINA 13 --------------------------

16.238 niños, niñas y adolescentes fueron reclutados entre 1990 y 2017; y 752.964 personas fueron víctimas de desplazamiento forzado entre 1985 y 2019. Y esto sin contar con el subregistro que amplía aún más las ya dramáticas cifras. Todas estas acciones fueron perpetradas tanto por grupos paramilitares, guerrilleros y agentes estatales en distintos departamentos del país y afectando a distintos grupos poblacionales.

Este marco de violencia por supuesto está representado en el discurso cotidiano y en los ámbitos especializados, lo cual ha generado un inmenso volumen de datos. Para referir sólo un ejemplo de ello, la información entregada por la Comisión de la Verdad “integró 112 bases de datos aportadas por 42 instituciones del Estado, organizaciones de víctimas y organizaciones de la sociedad civil” (Comisión de la verdad, 2022). Adicionalmente, una gran cantidad de información recopilada en distintas instituciones de la memoria, tanto del orden estatal como organizacional y comunitario da como resultado un gran universo de registros, información y discursos sobre este tema.

Este fenómeno, visto como un dominio de conocimiento, incorpora una cantidad considerable de discursos especializados con términos (denominaciones y conceptos) propios de campos involucrados en los estudios sobre el conflicto armado, como ciencia política, sociología, antropología, psicología, economía, derecho, historia, filosofía, literatura, arte, geografía, ciencias del medio ambiente, estudios de paz y conflicto, estudios de género y estudios sobre la memoria. Además, se incluyen las terminologías propias que han construido organizaciones sociales y comunitarias que trabajan por la defensa de los derechos humanos.

En este escenario complejo surgen una cantidad de acciones por parte de instituciones tanto gubernamentales como de la sociedad civil que han acompañado, defendido o atendido a la población y se han ocupado de estudiar y describir este fenómeno. Este universo documental está representado en bases de datos y repositorios que diferentes instituciones a distintos niveles recopilan y ponen a disposición. Instituciones como el Centro Nacional de Memoria Histórica (CNMH), el Legado de la Comisión de la Verdad, el banco de datos del Cinep y otras organizaciones sociales académicas y


------------------------- PAGINA 14 --------------------------

comunitarias disponen catálogos, repositorios y bases de datos. Para ello establecen estructuras a partir de tesauros, taxonomías y categorizaciones que permiten la descripción a nivel de contenido.

La organización de información plantea una serie de herramientas y métodos para los propósitos de disposición y recuperación que normalmente van desde la descripción formal hasta la descripción del contenido. Sin embargo, en ese proceso de describir, nombrar y categorizar hay dificultades que están relacionadas con el volumen mismo de la información y con los estándares mediante los cuales se definen las categorías, que normalmente se hacen bajo los criterios que la descripción documental o de contenido plantean. Sin embargo, esto puede quedarse corto para dar suficiente cuenta del alcance y contenido de la información.

Existe además una preocupación por la destrucción de los archivos, que requieren protección y preservación y una manera de aprovecharlos es poder rescatar información de ellos, hacer hablar al archivo mediante distintas técnicas de representación y reconocimiento de información. Hacer hablar al archivo pasa por reconocer la complejidad de nombrar, representar, categorizar y establecer de manera unívoca correspondencias en términos de significado, en temas particularmente sensibles como _víctima_ , _miedo_ , _daño_ , _responsable_ .

Es importante leer el conflicto pero también aprender a leer las heridas del lenguaje, entender la interconexión entre categorías, establecer un consenso sobre lo fundamental, que será decir qué son los conceptos con los que nos referimos a la realidad vivida y sufrida, cómo se construyen nociones como _paz territorial_ o qué implica nombrar un lugar/espacio o la significación que tienen términos como _vida cotidiana_ . Cómo se crea un concepto, qué dota de sentido a una categoría a la que luego se adicionan otras descripciones. Qué entendemos por _angustia_ y cómo establecer un sistema de relaciones a partir de un asunto tan concreto que se deriva de un hecho de violencia. Y cuáles son las estructuras sintácticas que nos permiten hablar de _desplazamiento_ , _tortura_ , _desaparición_ .


------------------------- PAGINA 15 --------------------------

# **1.2. Objetivos, preguntas de investigación e hipótesis**

Los **objetivos generales** planteados en esta tesis doctoral son:

1. Analizar un corpus sobre conflicto armado como dominio de especialidad con el fin de establecer un sistema de clases y entidades que permitan delimitar y estructurar conocimiento en ámbitos especializados para el desarrollo de aplicaciones diversas.

2. Examinar herramientas de procesamiento que faciliten la representación computacional de conocimiento en dominios específicos y permitan la extracción eficiente de información a partir del significativo de los datos.

3. Proponer un modelo para la constitución y exploración de corpus específicos a partir de una ontología sobre conflictos armados que facilite la exploración temática y conceptual en el dominio.

**Objetivos específicos** del objetivo general 1:

1. Conformar un corpus sobre conflicto armado con el fin de analizar lingüística y conceptualmente el dominio.

2. Recopilar y analizar la terminología relacionada con el dominio.

3. Definir un sistema de clases y entidades sobre conflicto armado para el desarrollo de herramientas de representación y extracción de información.

## **Objetivos específicos** del objetivo general 2:

1. Indagar sobre las ontologías y los grafos de conocimiento como herramientas para la estructuración de dominios.

2. Proponer un modelo de reconocimiento de entidades nombradas que use modelos de lenguaje con el fin de clasificar información a partir de entidades.


------------------------- PAGINA 16 --------------------------

## **Objetivos específicos** del objetivo general 3

1. Definir preguntas de competencia y requisitos de una ontología sobre conflicto armado.

2. Redactar una guía de anotación para el reconocimiento de entidades.

3. Proponer un modelo de grafo de conocimiento mapeando algunas clases.

## **Preguntas de investigación**

Esta tesis doctoral indaga sobre el uso de herramientas computacionales para la representación de información con fines de clasificación y extracción automáticas en un dominio de conocimiento. En ese sentido, las preguntas que guiaron la investigación fueron orientadas desde varios aspectos.

Sobre la construcción de un grafo de conocimiento se indaga por:

- ¿Cómo construir un grafo de conocimiento para el dominio del conflicto armado colombiano utilizando técnicas de aprendizaje automático para el reconocimiento de entidades nombradas?

- ¿Qué técnicas de aprendizaje profundo son más efectivas para el reconocimiento de entidades nombradas en textos sobre el conflicto armado colombiano?

- ¿Cómo integrar una ontología preexistente o construir una nueva para el grafo de conocimiento del conflicto armado colombiano?

En cuanto a la aplicación de un grafo de conocimiento se pregunta por:

- ¿Cómo utilizar un grafo de conocimiento para facilitar el análisis y la exploración y contribuir a la clasificación y extracción de información sobre el conflicto armado colombiano?

- ¿De qué manera puede un grafo de conocimiento ser utilizado para la investigación social sobre el conflicto armado colombiano y cómo esto podría contribuir a la preservación y estudio de la memoria del conflicto?


------------------------- PAGINA 17 --------------------------

También se establecen cuestiones relacionadas con las implicaciones y posibles extensiones que un grafo de esta naturaleza pueda tener y en ese sentido las preguntas son:

- ¿Cómo puede la metodología desarrollada en esta tesis ser extrapolada a otros corpus relacionados con conflictos armados en español y en dominios en los cuales no existen previamente ontologías o grafos?

Finalmente, como aporte de la tesis doctoral se buscó responder a estas preguntas:

- ¿Cómo esta investigación contribuye al desarrollo de herramientas para el procesamiento del lenguaje natural en español y a la construcción de conocimiento sobre el conflicto armado colombiano?

## **Hipótesis**

El uso de técnicas de aprendizaje profundo para el reconocimiento de entidades nombradas en un corpus de textos sobre el conflicto armado colombiano permite la construcción de un grafo de conocimiento que facilite el análisis, la exploración y la recuperación de información relevante para la investigación social, la preservación de la memoria y la gestión de conocimiento en este dominio.

Como hipótesis específicas se plantean:

1. Las técnicas de aprendizaje profundo son bastante efectivas para el reconocimiento de entidades nombradas en textos sobre el conflicto armado colombiano.

2. Para la construcción de un grafo de conocimiento es importante incorporar conocimiento del dominio a partir del análisis terminológico y discursivo del mismo.

3. El grafo de conocimiento construido a partir del corpus de textos y las entidades nombradas permite un análisis y una exploración más profunda de la información sobre el conflicto armado colombiano.


------------------------- PAGINA 18 --------------------------

4. El grafo de conocimiento es una herramienta útil para la investigación social sobre el conflicto armado colombiano, la preservación de la memoria y la gestión de conocimiento en este dominio.

# **1.3. Estado de la cuestión**

La representación de información sobre conflictos armados para su recuperación y uso puede verse materializada en bases de datos, repositorios y corpus que recogen dicha información con fines de sistematización y de disposición de esos materiales para consulta y uso, especialmente en sitios web. Esta representación se plantea desde la constitución de corpus lingüísticos cuya calidad y variedad (Molina, 2021) requieren de unos criterios claramente definidos para posteriormente hacer una anotación semántica (Sierra, 2015).

Disponer de recursos de información desde sus contenidos y los sentidos que esta información tiene demanda un estudio minucioso de la terminología (Cabré, 1993, 1999), y del discurso especializado del dominio (Estopà, 1999; Lorente, 2013), para establecer los patrones, las categorías y las relaciones entre los elementos que permitan una estructuración acorde con la realidad.

De otro lado, se abordan cuestiones relacionadas con las ontologías como una estructura de representación del conocimiento (Bergman, 2018). Allí se destacan trabajos como los de Schalley (2019) que propone el uso de ontologías terminológicas y el de Tehseen (2018) para hablar del uso de ontologías como esquemas para la recuperación de información <mark>. Además d</mark> esde los ya clásicos como Gruber (1993) y Noy y McGuinness (2001) que sentaron las bases conceptuales y metodológicas para el desarrollo de ontologías hasta propuestas más recientes como los trabajos de Blumauer y Nagy (2020), Schrader (2020) y Poveda _et al._ (2022).

En cuanto al reconocimiento de entidades nombradas con fines de clasificación de información, Marrero _et al_ . (2013), Gupta _et al_ . (2017), Liang _et al._ (2020), Li _et al_ . (2020), Goyal (2021) y Das _et al._ (2021) proponen distintas técnicas y modelos en diversos dominios de conocimiento. Este reconocimiento de entidades nombradas


------------------------- PAGINA 19 --------------------------

demanda el estudio riguroso de la terminología y la comprensión y establecimiento de las clases involucradas en el dominio (Marneffe _et al._ , 2021) y el reconocimiento de las Unidades de Significación Especializada (USE) que de acuerdo con Estopà (1999) abarcan diversos tipos de unidades sígnicas tanto lingüísticas como no lingüísticas. Así como aspectos propios de la variación terminológica y denominativa (Freixa, 2005) que también es necesario considerar.

Existen desde los ámbitos de la computación y la organización del conocimiento herramientas como las ontologías que tienen aplicaciones diversas referidas por autores como Tehseen (2018), Schrader (2020) y Vasileiadis y Fragouli (2020) que vienen luego a ampliarse en la relación de estas con los grafos de conocimiento desarrollados en los trabajos de Dou _et al_ . (2018), Xu _et al._ (2019) y Schrader (2020).

Es importante destacar el uso de aprendizaje automático en el desarrollo de ontologías (Xu _et al._ , 2019), (Kulmanov _et al._ , 2021) y el desarrollo de los grafos de conocimiento como herramientas de representación de entidades del mundo real y sus relaciones y propiedades (Kejriwal _et al_ ., 2021), (Ji _et al_ ., 2021).

Entre los autores que describen ampliamente la metodología para desarrollar grafos se destacan recientemente los trabajos de Fensel _et al_ . (2020) quienes plantean las tareas principales en la construcción de ontologías y el trabajo de Blumauer y Nagy (2020) quienes destacan la importancia de la interoperabilidad y usabilidad de los datos. Otros autores que abordan las cuestiones de los grafos son Barrasa _et al._ (2021), Hogan _et al._ (2021), Ji _et a_ l. (2021) y Kejriwal _et al._ (2021).

El reconocimiento de entidades nombradas como técnica para la extracción de datos permite la identificación y clasificación de entidades del mundo real de un texto (Liang _et al_ ., 2020). Es utilizado como tarea de extracción de información, modelación de intereses de usuarios, sistemas pregunta/respuesta y sistemas de diálogo (Kejriwal _et al._ , 2021) y sus aplicaciones incluyen clasificación de contenidos, recuperación de información, resumen automático, análisis de opiniones, entre otras (Goyal, 2021). Tanto Kejriwal _et al._ (2021) como Goyal (2021), abordan el tema de la ambigüedad que


------------------------- PAGINA 20 --------------------------

es necesario resolver para mejorar los sistemas de reconocimiento y clasificación de entidades.

Una de las bondades del trabajo con NER ( _Named Entity Recognition_ ) es la posibilidad de extraer información de textos no estructurados (Lane _et al._ , 2019), lo cual se expande a dominios no estandarizados (Gupta _et al._ , 2017).

Por otro lado, trabajos como los de Santoso _et al._ (2021) y Wang, K. _et al_ . (2021) plantean que el uso de NER es clave en el desarrollo ontológico y la construcción de grafos de conocimiento. Por su parte, Li _et al._ (2020) proponen el uso del aprendizaje profundo para la extracción de entidades y plantean la importancia de la evaluación de los modelos para valorar principalmente la precisión y recuperación de entidades.

En cuanto al uso de herramientas de aprendizaje automático se destacan los trabajos de Meng _et al._ (2019), Das _et al._ (2021) y Kulmanov _et al._ (2021) que proponen arquitecturas de redes neuronales profundas y aprendizaje autosupervisado como métodos para aprendizaje de entidades nombradas con pocos datos anotados.

El aprendizaje profundo también es utilizado para la construcción de ontologías y el poblamiento de grafos de conocimiento (Dou _et al._ , 2018), (Barrasa _et al._ , 2021). Autores como Ji _et al._ (2021) proponen el uso de modelos preentrenados como BERT ( _Bidirectional Encoder Representations from Transformers_ ) para ser utilizados en la extracción de entidades y relaciones. Por otro lado, Hogan _et al._ (2021) proponen la codificación de los grafos mediante incrustaciones de palabras y Meng _et al._ (2019) presentan el uso de modelos BERT que han sido exitosos para el reconocimiento de entidades nombradas, extracción de relaciones y sistemas de pregunta-respuesta.

Son de gran utilidad estas herramientas, sin embargo es de anotar que el desarrollo de modelos de lenguaje para el español aún es un campo en crecimiento que enfrenta desafíos como la escasez de corpus y el alto costo computacional que esto demanda (Vaca _et al.,_ 2022).

Es en este escenario que esta tesis doctoral plantea como objeto de estudio la reflexión sobre el uso de esas herramientas en los procesos de representación de conocimiento y


------------------------- PAGINA 21 --------------------------

en las implicaciones que tiene el estudio y comprensión de la terminología específica en un dominio de conocimiento concreto. Se plantea el estudio terminológico y discursivo del dominio como mecanismo para comprender las clases, categorías, entidades e instancias de la realidad que se refleja en los textos. A partir de esto, proponer un modelo de representación que integra el reconocimiento de entidades con una ontología y se materializa a partir del uso de grafos de conocimiento.

El aporte se da a partir de un enfoque mixto propuesto por Blumauer y Nagy (2020), para la conceptualización del dominio en una ontología por medio del lenguaje OWL ( _Ontology Web Language_ ) (Lamy, 202), (Debellis, 2021) y la extracción de entidades del corpus usando técnicas de aprendizaje de máquinas.

Esta tesis doctoral aporta la construcción de una ontología particular en este dominio que puede ser extrapolable para el análisis de otros conflictos y para el desarrollo de corpus anotados en español. Hay una necesidad de herramientas para el análisis y la extracción de información de grandes volúmenes y con pocos datos anotados.

Para el desarrollo de esta tesis se establecen puentes entre las ciencias del lenguaje, las ciencias computacionales, la representación de conocimiento y los dominios de especialidad. Se describen los desafíos propios de esta fusión partiendo de lo semántico y la relación de esto con el lenguaje y el discurso en un campo de especialidad. Luego se habla sobre ambigüedad, las dificultades para denominar lo preciso, especialmente en un campo como este. Finalmente, se amplían esas dificultades hacia el plano computacional explicando los desafíos en términos de desambiguación y las técnicas que son usadas para esto.

# **1.4. Estructura de la tesis**

Esta tesis está estructurada en tres partes. En la primera se desarrollan los fundamentos en donde se explican las categorías conceptuales, la segunda explica la metodología de los componentes involucrados y en la tercera se desarrollan las conclusiones, limitaciones y líneas de trabajo futuro.


------------------------- PAGINA 22 --------------------------

La parte uno está compuesta por los capítulos 2 al 7 y están distribuidos de la siguiente manera:

En el capítulo 2 se habla sobre la conformación de un corpus sobre el dominio indicando el concepto mismo de corpus, qué significa hablar de corpus de memoria y cuáles son las experiencias que son referentes para llegar a explicar qué conforma el corpus del conflicto armado como concepto en el marco de esta investigación particular.

En el capítulo 3 se explican las ontologías para representación de conocimiento en dominios indicando los tipos de ontologías, los métodos y lenguajes para su construcción y la relación de estas con los grafos de conocimiento.

En el capítulo 4 se aborda el reconocimiento de entidades nombradas explicando los enfoques y tareas que se llevan a cabo para esto, así como los tipos de entidades y métricas empleadas para evaluar el rendimiento de un clasificador. Al final se relaciona también con los grafos de conocimiento y las implicaciones y desafíos.

El capítulo 5 describe la terminología en el dominio del conflicto armado, tarea fundamental para estructuras como la ontología o la clasificación a partir del reconocimiento de entidades. Se explican las clases y entidades propias del dominio.

En el capítulo 6 se presentan los grafos de conocimiento para entender los componentes y tareas, así como las metodologías, herramientas y enfoques para su construcción. Se plantea también una reflexión sobre los grafos de conocimiento y su relación con otras estructuras de representación de conocimiento.

Para finalizar la parte teórica, en el capítulo 7 se explica el aprendizaje automático para estudios del lenguaje para entender los métodos y arquitecturas utilizados especialmente en las tareas de extracción de entidades y poblamiento de grafos de conocimiento y el uso de _transformers_ para estas tareas.

En la segunda parte, capítulos 8 a 11, se describe la metodología del trabajo, así como las tareas de experimentación sobre el corpus conformado.


------------------------- PAGINA 23 --------------------------

En el capítulo 8 se explica cómo se conformó el _dataset_ para el entrenamiento y testeo del modelo y se explican las fuentes terminológicas y conceptuales para la conformación del corpus, así como las características lingüísticas de los elementos que son identificados y seleccionados para la experimentación.

En el capítulo 9 se presentan las generalidades para la conformación de un modelo para clasificación de entidades a partir del corpus y se explican los resultados obtenidos.

En el capítulo 10 se describe la metodología para la construcción de una ontología sobre conflicto armado y se explica la estructura, conceptos y relaciones entre las clases.

El capítulo 11 está dedicado a la definición del modelo para la construcción de un grafo de conocimiento sobre conflicto armado y para ello se indaga por el uso de estos, la metodología y la estructura de modelado.

En la parte tres se presentan las conclusiones en el capítulo 12 y en el capítulo 13 se hace una relación de los resultados y las aplicaciones derivadas de la tesis. También se explican las limitaciones del estudio y se plantean líneas de trabajo de futuro. Finalmente, se presenta la bibliografía citada en la tesis.


------------------------- PAGINA 24 --------------------------

# **Parte 1. Fundamentos**

En esta parte de la tesis se exponen las cuestiones fundamentales de cada una de las categorías sobre las que se sustenta este trabajo. En el capítulo 2 se habla de la conformación de un corpus sobre conflicto armado partiendo de las consideraciones generales sobre la lingüística de corpus para definir cuales son los recursos textuales y las características de estos que permiten un estudio terminológico para el desarrollo de herramientas de representación de conocimiento.

En el capítulo 3, se abordan las ontologías como herramientas para la representación y se indaga por los métodos, técnicas y lenguajes que facilitan su construcción y uso y planteando finalmente la relación de estas con los grafos de conocimiento.

El capítulo 4 aborda el reconocimiento de entidades nombradas como técnica de extracción de información con fines semánticos. Aquí se describen los enfoques y tipos de entidades, así como las métricas que son utilizadas para evaluar modelos de extracción y clasificación. También se establece una relación entre esta técnica y los grafos de conocimiento.

En el capítulo 5 se describen las clases y entidades particulares del dominio del conflicto armado y se plantea una reflexión en torno a las cuestiones terminológicas sobre las que indagar para proponer un sistema de clases que vincule tanto a la ontología como al modelo de clasificación de entidades.

El capítulo 6 explora las definiciones y evolución de los grafos de conocimiento, así como los usos y potencialidades. También se describen las metodologías y los enfoques para poblamiento de grafos y al final se plantea una reflexión sobre los grafos en comparación con otras herramientas de representación de conocimiento.

Por último, en el capítulo 7, se describe el aprendizaje automático como técnica en donde se indaga por los métodos y enfoques y se plantea una discusión sobre modelos de lenguaje y arquitecturas, como _transformers,_ para abordar problemas de representación y extracción de conocimiento con fines de clasificación.


------------------------- PAGINA 25 --------------------------

# **Capítulo 2. Corpus lingüístico sobre conflicto armado**

Plantear un mapa de conocimiento sobre conflicto armado implica reunir y disponer recursos que permitan la integración de datos y conocimiento alrededor del tema. Sobre el conflicto armado, como se mencionó antes, se genera gran cantidad de información que describe el fenómeno, las causas, los actores, las afectaciones, las medidas de reparación, las acciones de atención y de memoria. Esta información es producida por diferentes tipos de instituciones y en ella se reconocen conceptos, terminologías y entidades concretas.

El capítulo está estructurado en tres partes. Primero se presenta el concepto de corpus para referir a la colección de textos sobre conflicto armado, indicando las características y condiciones de conformación. Posteriormente se habla sobre los corpus de memoria en contextos de conflicto y violencia para lo cual se presenta un recorrido por diferentes iniciativas que recopilan y disponen información similar. Finalmente, se describe el corpus particular del conflicto armado colombiano y cuáles son los recursos y características textuales que ellos tienen.

# **2.1. Concepto de corpus**

Un corpus puede definirse como un conjunto de datos lingüísticos que son manipulables por computador y que sirve a distintos tipos de análisis según la naturaleza misma de los datos y según intereses concretos sobre aspectos particulares del lenguaje. El corpus es una evidencia lingüística que prueba el uso del lenguaje natural en forma de colecciones organizadas de datos, que recogidas mediante un marco de ejemplos de uso de la lengua, permite el análisis de información relativa a ella. Debe contener una colección de textos producidos en situaciones reales de comunicación (bien sea oral o escrita) que cumplan con unos criterios explícitos y que puedan entenderse como muestra representativa del uso del lenguaje (Molina, 2021).

El corpus tiene como características la **representatividad** _,_ es decir que la elección de las muestras de la lengua debe corresponder con distintos tipos de textos según los criterios que hayan sido definidos; y la **sistematicidad** _,_ que se refiere a la consistencia


------------------------- PAGINA 26 --------------------------

en el vocabulario construido. El valor de representatividad “estará determinado por la calidad de la muestra y por la variedad de los textos, y no única y exclusivamente por su tamaño o extensión” (Molina, 2021, p. 121). Esta consideración es importante porque si bien el volumen puede ser relevante, lo realmente importante en este tipo de trabajos es contar con datos de calidad lo que hace que el corpus sea más adecuado. También este autor define el criterio de **variedad** _,_ que “tiene que ver con la riqueza de la muestra, en cuanto a los diferentes tipos de textos empleados, los géneros textuales, los registros de la lengua, etc.” (Molina, 2021, p. 133).

Los corpus pueden ser escritos, orales o multimodales según los criterios de compilación que se definan y el tipo y alcance de análisis que se requieran. También pueden distinguirse entre abiertos o cerrados dependiendo de si son corpus terminados o se plantean como corpus que se van ampliando en el tiempo; equilibrados o no, dependiendo de la distribución de la proporción de las unidades y del nivel léxico analizado; o según el proceso al que hayan sido sometidos los textos, en donde pueden ser simples, etiquetados o analizados.

En esta tesis se entiende el corpus como la colección de documentos recopilados que responden a un dominio concreto y son muestra del uso del lenguaje de especialidad sobre conflicto armado. Este corpus es conformado de acuerdo con criterios que son explicados más adelante pero que en todo caso representan la base de conocimiento del dominio y sirven para identificar las entidades que permitan la construcción de una herramienta de representación como un grafo de conocimiento.

Una de las tareas del tratamiento de corpus es la anotación, que hace referencia a los códigos o etiquetas que son adicionados a los datos con el fin de identificar información sobre ellos. Los tipos de anotación de corpus varían según el nivel que se busque describir, así que existe la anotación textual, fónica, morfológica y morfosintáctica, sintáctica, semántica y discursiva o pragmática. La anotación semántica implica “desambiguar las palabras del corpus, es decir, asignar a cada palabra el sentido más apropiado del diccionario, y otro objetivo es detectar las relaciones léxico-semánticas de las palabras del corpus” (Sierra, 2015, p. 127). Este autor explica que la anotación


------------------------- PAGINA 27 --------------------------

semántica usa un tipo de marcaje que es definido por el usuario según los intereses particulares de la investigación que se realice. Diferencia tipos de anotación de acuerdo con características semánticas, que pueden ser anotación ontológica y anotación de relaciones semánticas.

De acuerdo con Sierra (2015), la anotación ontológica “consiste en hacer la descripción formal de los conceptos del corpus y enlazar las relaciones entre esos conceptos” (p. 127). La importancia de la anotación es que permite reconocer en el corpus construido, aquellos elementos que facilitan tareas como la clasificación automática, la extracción, la recuperación y la representación de conocimiento. Sobre la anotación de relaciones, este autor dice que:

se refiere al marcaje de relaciones léxico-semánticas que se pueden establecer entre elementos del corpus y que van desde la sinonimia, hiperonimia, meronimia, etc., hasta las relaciones de elementos relacionables del texto tales como: agentes, pacientes y participantes de acciones concretas (Sierra, 2015, p. 128).

De acuerdo con Molina,

un corpus es un conjunto de textos establecido según un principio de documentación exhaustivo, un criterio temático o ejemplar, para su estudio lingüístico [...] una colección de textos o una recopilación de documentos que se organizan para un estudio científico, el cual está determinado por los objetivos y posibles hipótesis que se pretenden confirmar, validar o rechazar (2021, p. 120).

En este sentido la relación entre corpus y reconocimiento de entidades nombradas en esta tesis, está dada en razón de que es justamente ese conjunto de textos seleccionados bajo criterios y características determinados, la fuente principal para la identificación y etiquetación de entidades (Li _et al._ , 2020).

Es importante mencionar que la constitución de un corpus especializado como pretende ser este, pasa también por la reflexión sobre las implicaciones de los discursos especializados y cómo es que surge la organización conceptual en dominios concretos.


------------------------- PAGINA 28 --------------------------

El conocimiento está representado en terminología específica según usos y contextos de comunicación especializados. De acuerdo con Vargas,

el universo de discurso estaría constituido por los textos especializados (Feliu y otros, 2002) que se producen y circulan en un dominio dado y que conforman, en definitiva, un corpus o colección de textos, a partir del cual se procede a la extracción terminológica (2006, p. 44).

El corpus de conocimiento de un campo es la representación formal de los discursos que lo conforman, los cuales están constituidos a su vez por la terminología técnica o especializada, la cual,

se extiende a muchos otros aspectos del discurso especializado, como sus temas preferidos, formatos generales o esquemas de texto, estilo, retórica (incluyendo sus metáforas típicas), patrones de argumentación, métodos de prueba y demostración, el uso de tablas, figuras y otros aspectos no verbales del discurso (Van Dijk, 2011, p. 23).

En este corpus se encuentran esos aspectos que menciona Van Dijk muy identificables y característicos de un tipo de discurso, que aunque sea polifónico porque se alimenta de muchos campos del saber, se reconocen ciertos patrones y esquemas recurrentes en los temas, la terminología y la conceptualización.

# **2.2. Corpus sobre memorias en contextos de conflicto y violencia**

Los corpus de memoria se constituyen a partir del conjunto de recursos de información relacionada con violaciones a los derechos humanos, la defensa y lucha por la verdad y la justicia en el marco de los conflictos armados. Son utilizados para la experimentación relacionada tanto con la anotación de entidades como con la construcción de la ontología. Son documentos y objetos de información recopilados y producidos por organizaciones de investigación, atención o defensa de los derechos humanos.

Para este caso, son recursos dispuestos en la web de organizaciones que tienen diversas características formales y de contenido, desde documentos relacionados con la denuncia y el registro de hechos hasta testimonios textuales, audiovisuales, producciones escritas


------------------------- PAGINA 29 --------------------------

a partir de talleres o ejercicios que son realizados con personas que son víctimas o familiares de víctimas de los conflictos. Para este trabajo se recopilan documentos escritos y sus características se describen detalladamente en el <u>capítulo 8.</u>

Desde el punto de vista de las ciencias de la información estas colecciones documentales son nombradas como archivo, repositorio o base de datos. Estos recursos forman colecciones en instituciones que tienen como propósitos la investigación, la difusión o visibilización del conflicto y sus afectaciones; así como la pedagogía y formación, la memoria, la denuncia y la lucha por la verdad y la justicia. Se proponen en muchos casos también como redes de cooperación archivística y documental de información a partir de la integración sobre temas.

En estos archivos se encuentran recursos de información, textuales en la mayoría de los casos, pero también audiovisuales y multimodales. Estos recursos son organizados y dispuestos en colecciones y fondos documentales que se estructuran de acuerdo a clasificaciones y categorías según los propósitos institucionales y las dinámicas propias de disposición de información. En algunos casos, se explicita el uso de tesauros y recursos terminológicos para la organización temática o conceptual de la información.

El sentido de denominar corpus a esta colección de textos seleccionados se da en razón de que su compilación atiende a los propósitos específicos de esta investigación. El uso y procesamiento de esta información se da más experimentalmente pues de lo que se trata es de que estos recursos sean fuente para la identificación y extracción de entidades nombradas para poblar un grafo de conocimiento.

Para poder ofrecer una plataforma de consulta sobre un corpus de este tipo es necesario plantearse, por un lado, la estructuración y anotación de los textos para facilitar una consulta estructurada; y, por otro lado, la necesidad de desarrollar herramientas de análisis a partir de las cuales se permita una anotación semiautomática que acelere la disponibilidad de los textos en una plataforma con datos no estructurados, lo cual será de gran ayuda para la investigación.


------------------------- PAGINA 30 --------------------------

Con el propósito de tener información más amplia sobre otros corpus o repositorios que en el mundo recopilan y disponen información sobre conflictos o guerras, a continuación se describen en la <u>tabla 1</u> algunos sitios web de organizaciones que abordan asuntos relacionados con conflictos, desaparición de personas, genocidios, dictaduras, conflictos armados, guerras civiles, entre otros. En cada uno de estos sitios la clasificación de la información se da de acuerdo a los propósitos particulares en combinación con las categorías, clasificaciones y colecciones temáticas que para cada uno son relevantes. Se revisaron sitios en Colombia, Argentina, Chile, Guatemala, Perú, México, Estados Unidos, Ruanda, España, Italia, Israel, Polonia y la Unión Europea.

Sobre estos sitios, lo que interesa es reconocer las estructuras mediante las cuales los recursos de información se disponen, así como los mecanismos de indización y catalogación, es decir la descripción formal y de contenido de los registros. También se describen las herramientas terminológicas o taxonómicas que sirven como estructura conceptual, así como las formas de visualización de los recursos que en muchos casos integran información multimodal para hacer recursos más interactivos.

# **2.3. El corpus del conflicto armado en Colombia**

Sobre el caso del conflicto armado colombiano puede decirse que este ha dejado una gran cantidad de información que instancias de orden social o gubernamental, como asociaciones de víctimas e instituciones defensoras de los derechos humanos, han generado, recopilado y dispuesto. Diversas instituciones y organizaciones que trabajan por la defensa de los derechos humanos y la atención en el acompañamiento permanente a las personas, así como la elaboración de trabajos académicos, han compilado registros de hechos de violencia, entrevistas, procesos jurídicos, fuentes documentales de carácter etnográfico, documentos de prensa, informes y testimonios. Este material recoge la voz de las familias y de las personas que han sido afectadas por distintas modalidades de violencia, así como las voces de la sociedad civil y de quienes estudian e investigan estos fenómenos.


------------------------- PAGINA 31 --------------------------

En Colombia existen archivos y repositorios sobre conflicto, memoria y defensa de derechos humanos que han sido construidos y dispuestos por organizaciones sociales, colectivos comunitarios y populares, centros de investigación, instituciones académicas y organizaciones institucionales. Recogen información sobre el conflicto armado, sobre las memorias de luchas, resistencias, demanda de garantía de derechos. Esta información es acopiada o producida según los intereses y propósitos de cada archivo y, al igual que en los casos de repositorios mencionados anteriormente, son diferentes tanto el tipo de información como las colecciones, formatos y categorías mediante las que se organizan y disponen los recursos.


------------------------- PAGINA 32 --------------------------

## **Tabla 1**

_Recursos de información en sitios web de memoria sobre conflictos_

|**Sitio de memoria y**<br>**conflictos**|**Recursos de información**|**País**|**Conflicto**|
|---|---|---|---|
|Archivo<br>del Genocidio<br>de Ruanda|Se encuentran testimonios dispuestos temáticamente a partir de la<br>clasificación<br>por<br>las<br>colecciones:<br>Perpetradores,<br>Rescatistas,<br>Sobrevivientes, Personas mayores. Tiene un sistema de navegación por<br>tópicos, lugares, palabras clave, periodo, etc.|Ruanda|Genocidio (1994)|
|Infraestructura<br>Europea<br>de<br>Investigación<br>del<br>Holocausto|Iniciativa<br>que<br>desarrolla<br>y<br>promueve<br>proyectos de investigación,<br>formación, cooperación e integración. Ofrece información para la gestión<br>de archivos que incluye estándares de metadatos de descripción y<br>vocabularios controlados. Opera como red de centros y archivos que<br>recopila e integra información que tienen las organizaciones en distintos<br>países.|Unión<br>Europea|Holocausto<br>(1939-1945)|
|_Nomes e voces_|Proyecto interuniversitario de la Universidad de Santiago de Compostela,<br>que presenta una metodología para la recolección e indización y describe<br>el uso de tesauros para la estructuración de la información que recopila.|España|Dictadura franquista<br>(1936)|


------------------------- PAGINA 33 --------------------------

|**Sitio de memoria y**<br>**conflictos**|**Recursos de información**|**País**|**Conflicto**|
|---|---|---|---|
|Voces de la gran guerra|Es un proyecto que usa técnicas avanzadas de lingüística computacional,<br>minería de textos y visualización de información para disponer materiales<br>digitalizados para ser explorados en línea sobre la I Guerra Mundial.<br>Desarrollado en la Universidad de Pisa en colaboración con el Instituto de<br>Lingüística Computacional, la Universidad de Siena y la_Accademia della_<br>_Crusca_. La disposición de los textos se puede agrupar por personas,<br>lugares, organizaciones y se genera un gráfico a partir de nodos de<br>conexión entre distintos elementos de esas agrupaciones.|Italia|I<br>Guerra<br>Mundial<br>(1914-1918)|
|_Fortunoff Video archive_<br>_for holocaust testimonies_|Desarrollado por la _University of Yale_. Usa metadatos de descripción para<br>clasificar por tipo, temas y asuntos de tiempo o lugar.|Estados<br>Unidos|Holocausto<br>(1939-1945)|
|_Shoah_<br>_Foundation_<br>_Institute_<br>_for_<br>_Visual_<br>_History and Education_|Liderado por la _South Carolina University_, propone distintas actividades<br>y dispone de guías para la indización y catalogación a partir del uso de un<br>tesauro<br>para<br>la<br>organización.<br>También<br>llevan<br>a<br>cabo<br>procesos<br>pedagógicos y se dispone de otras guías también para la recopilación. Se<br>centra en la recolección de testimonios de víctimas del holocausto, pero<br>también recoge información de otros casos de genocidios en el mundo.|Estados<br>Unidos|Holocausto<br>(1939-1945)|
|E-xiliad@os: España en<br>una maleta|Proyecto interactivo acerca del exilio republicano español que recoge<br>relatos y testimonios sobre la migración.|España|Éxodo<br>republicano<br>(1939)|


------------------------- PAGINA 34 --------------------------

|**Sitio de memoria y**<br>**conflictos**|**Recursos de información**|**País**|**Conflicto**|
|---|---|---|---|
|_Yad_<br>_Vashem_.<br>Centro<br>Mundial<br>de<br>Conmemoración<br>de<br>la<br>Shoá|Recoge testimonios alrededor del mundo de los judíos asesinados por los<br>nazis a partir de varios formularios que diligencian familares con el<br>propósito de hacer perdurar en el tiempo los nombres y las historias de<br>estas personas para las generaciones venideras. Esta base de datos es<br>utilizada no solo para la preservación sino para la disposición de datos en<br>espacios de conmemoración y en ejercicios de memoria.|Israel|Holocausto<br>(1939-1945)|
|Lugar de la Memoria, la<br>Tolerancia y la Inclusión<br>Social (LUM)|Tiene tanto apuesta museográfica como documental y pedagógica y<br>recopila información de la violencia acontecida en el país entre los años<br>1980 y 2000.|Perú|Período<br>de<br>la<br>violencia<br>(1980-2000)|
|Museo de la Memoria y<br>los Derechos Humanos|Recopila y dispone información relacionada con la dictadura militar que<br>tuvo lugar entre el 11 de septiembre de 1973 y el 11 de marzo de 1990.|Chile|Dictadura<br>militar<br>(1973-1990)|
|Adondevanlosdesapareci<br>dos.org|Dispone información sobre desapariciones por cuenta de la violencia<br>asociada con el narcotráfico.|México|Violencia (actual)|
|Desaparecidos.org|Es un lugar donde poder conocer y recordar a las víctimas del terrorismo<br>de estado en América Latina y el mundo.|Argentina|Dictadura<br>cívico-militar<br>(1976-1983)|


------------------------- PAGINA 35 --------------------------

|**Sitio de memoria y**<br>**conflictos**|**Recursos de información**|**País**|**Conflicto**|
|---|---|---|---|
|Memoria Abierta|Dispone información testimonial a partir de una clasificación temática<br>según<br>el<br>esquema<br>propuesto<br>por<br>ISAD-G (_General International_<br>_Standard Archival Description)_. La gestión y visualización de los datos se<br>hace con ICA-Atom.|Argentina|Violencia política|
|Archivo Provincial de la<br>memoria de Córdoba|Colección sobre memoria oral que recoge testimonios de familiares de<br>personas desaparecidas o torturadas durante la dictadura; y que además de<br>la clasificación, estructura y forma de visualización de los datos, tiene una<br>apuesta pedagógica, por esa conservación del pasado y de la memoria.|Argentina|Dictadura<br>cívico-militar<br>(1976-1983)|
|Comisión provincial de<br>la<br>memoria.<br>Archivo<br>oral:<br>Memorias<br>encontradas|Contiene fondos documentales relacionados con el accionar represivo del<br>Estado que dispone a partir de normas de descripción de archivos.|Argentina|Dictadura<br>cívico-militar<br>(1976-1983)|


------------------------- PAGINA 36 --------------------------

<mark>En cuanto a las instituciones que conforman estos archivos se encuentran organizaciones sociales que pueden ser colectivos de víctimas, defensores de derechos humanos, centros de investigación, organizaciones populares y comunitarias. También existen instituciones académicas e instituciones del Estado como el Centro Nacional de Memoria Histórica, así como organizaciones de atención, inteligencia y judiciales. Estas instituciones son de orden local, regional, nacional o internacional.</mark>

Se reconoce en estos repositorios tanto información primaria relacionada con hechos como información mediada a partir de lenguajes y recursos variados como la imagen, lo audiovisual, los objetos, etc. En entornos web, esta información está dispuesta en forma de base de datos, repositorios, blogs y las principales categorías que pueden identificarse se refieren a la denuncia, la memoria, el reconocimiento y las modalidades de victimización. En muchos casos, esta información se cruza con datos sobre enfoques diferenciales en razón de edad, género, orientación sexual y situación de discapacidad. Esta información es igualmente multimodal y se refiere tanto a testimonios como a información factual, de análisis académicos, jurídicos, entre otros tipos.

A continuación se describen las características y especificaciones de sitios en Colombia que recopilan y disponen información relacionada con el conflicto. Se describen en dos niveles: por un lado, sitios que disponen de información general sobre memoria del conflicto armado y que explícitamente contienen archivos o repositorios cuyo objetivo es preservar y hacer pedagogía desde los recursos de información para la memoria y la defensa de los derechos humanos. En un segundo nivel, se enuncian los sitios que aunque no se reconocen como archivos, la información que producen es fundamental para complementar el conocimiento disponible sobre el dominio.

En Colombia existen muchos sitios en los que se dispone información sobre el conflicto y la memoria, entendida esta última como una “herramienta plural que permite dar cuenta de la heterogeneidad cultural del recuerdo ligado a las comunidades y a los territorios” (Giraldo, 2019, p. 24). Aquí se refieren sitios que tienen un alcance amplio en el sentido en que plantean recopilar y disponer información nacional y con diversos enfoques diferenciales. En la <u>tabla 2</u> se describen algunos sitios que explícitamente se


------------------------- PAGINA 37 --------------------------

denominan como centros de memoria y que son de carácter público y abierto para libre consulta por parte de la comunidad en general. Aquellos que trabajan sobre casos específicos o atienden a una población determinada sea por dimensión territorial, étnica o de género, serán detallados en el <u>capítulo 8</u> en donde se describen los que se seleccionaron para conformar el corpus de este trabajo que recoge información producida por organizaciones sociales e instituciones educativas, así como por organizaciones gubernamentales e internacionales.

<mark>Un referente es el trabajo que desde la Comisión para el Esclarecimiento de la Verdad y la Jurisdicción Especial para la Paz (JEP)</mark><sup>1</sup> <mark>, incorpora técnicas de procesamiento de lenguaje natural y trabajo con corpus.</mark> El informe metodológico presenta un análisis estadístico de patrones del conflicto a partir de integrar distintas bases de datos.

Estos análisis se dan a partir de información parcial dando por sentado que todas las bases de datos están incompletas y hay cosas que se relatan de manera que hacen muy difícil un registro completo. Este asunto se menciona así:

la importancia de este proyecto radica en que los registros de violaciones de derechos humanos sufren de dos tipos de vacíos de información: campos faltantes y subregistro. Por lo tanto, no es correcto analizar patrones de violencia a partir de bases de datos que registren a víctimas. Ya que los datos observados no siempre reflejan la realidad, sino la documentación realizada por cierto proyecto (Jurisdicción Especial para la Paz y Comisión de la Verdad, 2022, p. 7).

> 1 Mediante el Acto Legislativo 01 de 2017 y el Decreto 588 de 2017, se crearon la Comisión para el Esclarecimiento de la Verdad, la Convivencia y la No Repetición, como un mecanismo de carácter temporal y extrajudicial del Sistema Integral de Verdad, Justicia, Reparación y No Repetición - SIVJRNR, que integran a su vez también la Jurisdicción Especial para la Paz y la Unidad para la Búsqueda de Personas dadas por Desaparecidas (Congreso de Colombia, 2017).


------------------------- PAGINA 38 --------------------------

## **Tabla 2**

_Recursos de información en sitios web de memoria en Colombia_

|**Sitio de memoria**|**Recursos de información**|**Tipos de recursos**|
|---|---|---|
|Centro<br>Nacional<br>de<br>Memoria Histórica|Recoge, custodia y preserva material entregado por personas naturales o jurídicas que<br>documentan graves violaciones a los DD.HH. y al DIH en el marco del conflicto.<br>Dispone fondos documentales de organizaciones o personas.|Textos, Audiovisuales,<br>Interactivos, Bases de<br>datos|
|Base de datos de DD.<br>HH.<br>y<br>Violencia<br>Política en Colombia|Recoge información factual clasificada según delitos asociados y descritos en un marco<br>conceptual para aumentar la visibilidad y difundir información sobre violaciones a los<br>derechos fundamentales e infracción al Derecho Internacional Humanitario en el país.|Base de datos|
|Centro<br>de Memoria,<br>Paz y Reconciliación|Dispone de información divulgativa de actividades y programas del Centro y ofrece<br>recursos multimediales. Si bien no ofrecen repositorio o catálogo de las colecciones, esta<br>institución es importante e igual se toman recursos para la conformación del corpus.|Textos,<br>Recursos<br>audiovisuales|
|Legado Comisión de<br>la Verdad|El legado se presenta como un recurso transmedia que contiene información multimedial<br>recopilada por la Comisión. Posee y dispone además el Archivo del esclarecimiento de la<br>verdad que tiene recursos organizados en colecciones y fondos documentales. Tiene<br>también un tesauro que estructura conceptualmente la información.|Textos,<br>Recursos<br>audiovisuales,<br>Interactivos, Bases de<br>datos|
|Hacemos memoria|Proyecto de la Universidad de Antioquia que investiga, discute y propone un diálogo<br>público sobre el conflicto armado y las graves violaciones a los DD. HH.Recopila y<br>dispone información relacionada con el conflicto, el posacuerdo, las memorias y voces.|Textos,<br>Recursos<br>audiovisuales|


------------------------- PAGINA 39 --------------------------

Mucha información es recopilada de manera diferente en distintas bases de datos y por tanto se da el hecho de que, por ejemplo, haya sobre una misma víctima información que pueda estar duplicada y por tanto la revisión y contrastación de todas las fuentes se hace necesaria para minimizar todos los sesgos posibles. Los patrones definidos para la contrastación de datos tienen relación con hechos de violencia o modalidades de victimización como: homicidio, secuestro, desaparición forzada, reclutamiento de niñas, niños y adolescentes, entre otros, de los cuales se pretende hacer un análisis estadístico (Jurisdicción Especial para la Paz y Comisión de la Verdad, 2022).

También se describe detalladamente el procedimiento que a grandes rasgos incluye la preparación de los datos, la definición de pares de registro, la generación de datos de entrenamiento y de las reglas y características mediante las cuales se evaluarán los registros y la evaluación del modelo y ajustes para reclasificación de los datos cuando es necesario.

Otro trabajo a resaltar es el uso de procesamiento de lenguaje natural para analizar entrevistas que fueron recogidas y recopiladas por la Comisión para el Esclarecimiento de la Verdad y que pretendían analizar la información a partir de la identificación de organizaciones, lugares, verbos y personas. Las técnicas mencionadas en el trabajo incluyen _N-grams_ para representar en vectores las palabras que aparecen en el corpus y que guardan entre sí algún tipo de similitud semántica o de contexto. También se usaron lexicones emocionales para poder establecer relaciones entre las palabras del corpus y las categorías de emociones descritas en el _Spanish Emotion Lexicon_ SEL y en el _NRC Emotion Lexicon_ , los cuales recogen y asocian términos relativos a una de las emociones básicas como enojo, miedo, tristeza, sorpresa, entre otras (Comisión de la Verdad, 2022).

Posteriormente, después de establecer las categorías cualitativas, se incorpora un análisis cuantitativo de manera que puedan establecer los valores de intensidad, polaridad y valencia a cada una de las palabras y poder definir así promedios y probabilidad. Esto permitió algunas conclusiones que se mencionan en el texto como:


------------------------- PAGINA 40 --------------------------

Aunque cada capítulo cuenta con sus propias conclusiones, es posible determinar que a través del uso de diversas metodologías se pueden desarrollar análisis gracias al procesamiento de lenguaje natural dentro de las diversas entrevistas que componen los múltiples corpus de la Comisión de la Verdad. Gracias a ello, se pudieron obtener resultados de varias índoles donde sale a relucir el uso del lenguaje. Gracias a todos los resultados proporcionados, es evidente que en todos los estudios la importancia del lenguaje es transversal e intachable, puesto que los diferentes análisis involucraron de alguna u otra manera la forma por la cual se describen los acontecimientos producidos durante el marco del conflicto armado dentro de los diferentes corpus de la Comisión. Ya sea mediante un análisis de frecuencias, impactos, promedios o métricas, los componentes del lenguaje fueron determinantes a la hora de establecer relaciones y conclusiones dentro de cada informe (Jurisdicción Especial para la Paz y Comisión de la Verdad, 2022, p. 136).

Hasta aquí un recorrido por distintos tipos de corpus relacionados con conflictos y las características de la información que los componen. También se destaca sobre aquellas en las cuales se integran técnicas de procesamiento de lenguaje natural o análisis de datos. Esto para entender la variabilidad de los datos antes de hablar de las ontologías como estructura de representación de conocimiento y de la técnica de reconocimiento de entidades nombradas para extracción y clasificación de información.


------------------------- PAGINA 41 --------------------------

# **Capítulo 3. Ontologías para representación de dominios**

De acuerdo con Noy y Mcguinness (2001), una ontología define un vocabulario común para compartir información en un dominio, la cual deberá ser compartida por un colectivo e interpretada por máquinas. En este capítulo se exploran las distintas definiciones sobre ontología, así como los elementos que la componen. Luego se describen los métodos y lenguajes para su construcción y finalmente se plantea la relación de las ontologías con los grafos de conocimiento. Este recorrido lleva también a plantear algunas cuestiones relacionadas con el uso de aprendizaje profundo para la generación o fusión de ontologías. También sobre cómo representar información de este dominio en ontologías y las clases que han de ser definidas para tal propósito.

<mark>Tomando una definición de diccionario, se entiende que una ontología es un concepto de la metafísica que trata del ser en general y de sus propiedades trascendentales. El concepto es adoptado por la ingeniería para describir conceptualmente dominios. Lo que se refiere a los métodos, herramientas y lenguajes para construirlas es denominado como ingeniería ontológica. La definición clásica de Gruber, plantea que “una ontología es una especificación explícita de una conceptualización. El término se toma de la filosofía, donde una ontología describe sistemáticamente la existencia. En sistemas basados en el conocimiento, lo que «existe» es exactamente lo que puede representarse” (1993, p</mark> . <mark>1). Dicha descripción comprende el tratamiento del vocabulario de un dominio, y su extensión está dada por los términos, relaciones y reglas de combinación del lenguaje del dominio.</mark>

<mark>Otra definición ya clásica también plantea que:</mark>

una ontología es una descripción formal explícita de los conceptos de un dominio del discurso (clases o conceptos), las propiedades de cada concepto que describen diversas características y atributos del concepto (también llamadas roles o propiedades) y las restricciones de esos atributos (Noy y Mcguinness, 2001, p. 3).

<mark>Otros plantean que una ontología define los términos básicos y las relaciones que comprende el vocabulario de un área temática, así como las reglas de combinación y las</mark>


------------------------- PAGINA 42 --------------------------

<mark>relaciones para definir extensiones (Neches</mark> _<mark>et al.</mark>_ <mark>, 1991). Esta especificación explícita de la conceptualización debe ser compartida por un colectivo dentro del dominio en cuestión y proporciona los medios para describir explícitamente detrás de la conceptualización del conocimiento representado en una base de conocimientos (Bernaras y Laresgoiti, 1996).</mark>

<mark>La conceptualización compartida se refiere a un modelo abstracto de algún fenómeno u objeto del mundo del cual se identifican los conceptos relevantes. El carácter explícito se refiere a que el tipo de los conceptos utilizados y las restricciones de uso son explícitamente definidos. El formal hace referencia al hecho de que la ontología debe ser entendible por las máquinas. Y la noción de compartida refleja la idea de que una ontología representa el conocimiento consensuado por un colectivo en dominios específicos (Studer</mark> _<mark>et al.</mark>_ <mark>, 1998).</mark>

<mark>Más recientemente, otros autores plantean que:</mark>

una ontología es un artefacto usado para especificar formalmente el significado del vocabulario en un dominio. Las ontologías contienen conocimiento, codificado en forma de axiomas, etiquetas en lenguaje natural, sinónimos, definiciones y otros tipos de anotación de sus propiedades semánticas (Kulmanov _et al._ , 2021, p. 2).

<mark>En esta definición se destaca la cuestión de las anotaciones a partir de las propiedades semánticas.</mark>

<mark>Así pues, una ontología está compuesta por clases, relaciones, funciones, instancias y axiomas:</mark>

- <mark>Las</mark> **<mark>c</mark> lase** **<mark>s</mark>** <mark>representan los elementos o ideas a formalizar de los conceptos en el sentido más amplio. Las clases en una ontología se organizan en taxonomías a las que se les pueden aplicar propiedades lógicas y pueden representar conceptos abstractos o conceptos específicos o concretos.</mark>

- <mark>Las</mark> **<mark>r</mark> elacione** **<mark>s</mark>** <mark>son las representaciones de las interacciones que se dan entre clases o conceptos y pueden ser de tipo jerárquico, parte de, compone a, hereda de, se parece a, etc.</mark>


------------------------- PAGINA 43 --------------------------

- <mark>Las</mark> **<mark>f</mark> unciones** <mark>son restricciones o cualidades que se dan a las relaciones mediante el cálculo de una función, lo cual permitirá que efectivamente la ontología pueda inferir o “razonar” automáticamente de acuerdo con parámetros definidos.</mark>

- <mark>Las</mark> **<mark>i</mark> nstancias** <mark>son representaciones o modelos de los elementos o individuos que componen la ontología.</mark>

- <mark>Los</mark> **<mark>a</mark> xiomas** <mark>son sentencias que son siempre ciertas, como leyes o condiciones que se usan para definir formalmente el conocimiento. Esto permite que haya una adecuada consistencia y coherencia entre todos los elementos de la ontología y su eventual relación con otras, bien sean del mismo tipo o complementarias.</mark>

# **3.1. Clasificación de ontologías**

<mark>En cuanto a la clasificación y categorización de las ontologías según su función,</mark> Mizogucchi e Ikeda (1995) propusieron cuatro clases de ontologías: ontologías para reutilización de conocimiento, ontologías para intercambio de conocimiento, ontologías para tareas de indexación y recuperación y meta-ontologías, que representan distintos dominios y se complementan entre sí. Se distinguen también las siguientes categorías: ontologías terminológicas como léxicos (Schalley, 2019), ontologías que sirven como esquema de información para la recuperación semántica (Tehseen, 2018) y ontologías que especifican conceptualizaciones del conocimiento a nivel más general (Fernández-López _et al._ , 2013). Tam <mark>bién entre ontologías genéricas, de dominio y de aplicación.</mark>

<mark>Otras clasificaciones de ontologías distinguen aquellas de representación de conocimiento, ontologías generales o comunes, ontologías superiores o de alto nivel, ontologías de dominio y ontologías lingüísticas. Sobre ontología lingüística, esta se entiende como “una red interconectada de conceptos relevantes, que hace explícitos, clasifica y organiza los supuestos y términos del dominio en cuestión” (Musgrave</mark> _<mark>et al.</mark>_ <mark>, 2014). Por su parte, Schalley (2019) sugiere dos niveles para tener en cuenta en el estudio de las ontologías desde lo lingüístico como campo de estudio: el primero tiene</mark>


------------------------- PAGINA 44 --------------------------

<mark>que ver con las lenguas del mundo y las expresiones que de ellas tienen los hablantes. El segundo nivel está relacionado con el uso del aparato lingüístico para describir objetos, que no necesariamente están en la realidad sino que son también conceptuales, como es el caso de cualquier dominio de conocimiento como el que se aborda en esta tesis.</mark>

<mark>Hay un tipo de ontología que es estudiado en Silva</mark> _<mark>et al</mark>_ <mark>. (2016), Schmidt</mark> _<mark>et al.</mark>_ <mark>(2020) y Jullien</mark> _<mark>et al</mark>_ <mark>. (2022) que son las ontologías fundacionales que pueden ser consideradas como meta-ontologías en tanto que recogen conocimiento universal.</mark>

Las ontologías fundacionales contienen conceptos básicos y universales, que son meta, genéricos o filosóficos, para promover la integración de información muy general y la expresividad en una amplia gama de dominios. Su propósito general es mapear el concepto a su interpretación más fundamental (Jullien _et al.,_ 2022, p. 1).

<mark>Este tipo de ontologías son de gran utilidad y su uso tiene múltiples aplicaciones en el escenario de los datos vinculados pues algunos conocimientos de carácter universal o general son aplicables también a dominios específicos.</mark>

<mark>Este mapeo es fundamental para permitir la generalización y el razonamiento, ya que se pueden adoptar categorías de nivel superior para desligar los mecanismos de abstracción necesarios sin pérdida de significado. Las ontologías fundacionales y su relación con la lógica representan una importante conexión entre el lenguaje natural y el razonamiento (Silva</mark> _<mark>et al</mark>_ <mark>., 2016).</mark>

<mark>El trabajo con ontologías requiere un análisis semántico de los dominios. Tehssen (2018) plantea que “el análisis semántico es una representación vectorial de texto en palabras o documentos que utilizan un corpus de documentos como base de conocimientos” (p</mark> . 1), es decir llevar a un lenguaje matemático entendible por máquina la estructura que tiene el lenguaje, no sólo propiamente semántico, sino también sintáctico, porque a partir de esta estructura pueden establecerse patrones. Algunos ejemplos de trabajo con ontologías para el análisis semántico de dominios se encuentran en Wang, K. _et al._ (2021), que hacen un análisis de textos biomédicos para reconocer entidades que puedan llevarse a una ontología incorporando sublenguajes de la biología


------------------------- PAGINA 45 --------------------------

molecular, genética, bioquímica y medicina. Santoso _et al._ (2021) proponen también un análisis semántico para extracción de conceptos en lengua indonesia. O en la propuesta de construcción de una ontología sobre el patrimonio cultural inmaterial chino que trabajan Dou _et al._ (2018).

<mark>En lingüística, el análisis semántico es un proceso para relacionar estructuras sintácticas, desde el nivel de frases, cláusulas, oraciones y párrafos hasta el nivel de la escritura en su conjunto, con los significados que esto pueda tener.</mark>

La anotación consiste en asignar una nota a una porción de texto específica. Más específicamente, en el contexto de la Web Semántica, la nota asignada contiene información semántica en forma de metadatos con el objetivo de establecer un enlace entre una ontología de referencia y la parte específica del texto que está siendo marcada ( <mark>Navarro-Galindo y Samos, 2013, p</mark> . 2).

<mark>Los tipos de anotación de corpus varían según el nivel lingüístico que se busque describir. Se tiene entonces la anotación textual, fónica, morfológica y morfosintáctica,</mark> sintáctica, semántica y discursiva o pragmática.

La anotación semántica usa un tipo de marcaje mediante el cual se busca identificar dentro del texto unidades léxicas o fraseológicas que correspondan a una categoría determinada. La anotación asigna una etiqueta a un fragmento de información con el fin de que este pueda ser representado y extrapolado a otros sistemas de información. Esta anotación se corresponde con necesidades particulares del usuario, sin embargo existen algunos estándares que son importantes en la interoperabilidad de los datos, entre los que se encuentran por ejemplo, la norma ISO TC37 SC4, que propone un marco de anotación lingüística (Ide y Suderman, 2014), ISO- _TimeML_ (Pustejovsky _et al.,_ 2010), o el mismo RDF ( _Resource Description Frame)_ , que si bien no es un estándar estrictamente lingüístico, su propósito es facilitar el intercambio de datos en la web.

<mark>Se diferencian también tipos de anotación de acuerdo con características semánticas, anotación ontológica y anotación de relaciones semánticas. Sobre anotación ontológica, Sierra afirma que:</mark>


------------------------- PAGINA 46 --------------------------

en este tipo de marcaje se utilizan tanto las características como las relaciones semánticas de las palabras [...]. La anotación ontológica consiste en hacer la descripción formal de los conceptos del corpus y enlazar las relaciones entre esos conceptos. Así pues, con la anotación ontológica se pretende conseguir el acceso inteligente a diversos recursos y que la navegación y búsqueda de información en internet sea más fácil y rápida (Sierra, 2015, p. 127).

<mark>Se identifican también los trabajos de Aguado</mark> _<mark>et al.</mark>_ <mark>(2002), Eriksson (2007), Navarro Colorado (2007), Buendía (2010), Navarro-Galindo y Samos (2013) y Viltres y Rodríguez (2019), quienes han trabajado sobre los aspectos de sentido para la anotación haciendo uso de ontologías lingüísticas que describe muy bien Schalley (2019).</mark>

<mark>La anotación se hace, entre otras, con el fin de extraer de un corpus información relevante y esta búsqueda de información puede ser en diferentes niveles: consultas basadas en palabras clave, que estarían dadas por el uso de lenguajes de indización a partir de metadatos temáticos o formales que se vinculen al corpus; las búsquedas basadas en las propiedades de las anotaciones que buscan indagar en el corpus por las relaciones de jerarquía entre los conceptos y que hacen uso de ontologías; las búsquedas basadas en conceptos, que amplían mucho más ese campo de relación para hacer un mapeo de conceptos similares o cercanos; y por último, la búsqueda en lenguaje natural que implicaría la recuperación en datos no estructurados (Navarro-Galindo y Samos, 2013).</mark>

<mark>La anotación semántica hace parte del procesamiento automático de la información y actúa sobre el plano de significado e incorpora estándares como RDF, XML (</mark> _<mark>eXtensible Markup Language</mark>_ <mark>), OWL (</mark> _<mark>Ontology Web Language</mark>_ <mark>). Buendía (2010) distingue entre corpus plano y corpus codificado. El primero puede operarse a partir de búsquedas por campos o por palabras o expresiones específicas; en el corpus codificado, se opera sobre búsquedas por categorías de elementos lingüísticos, puede explicar características implícitas en los textos. En este segundo tipo de corpus, la anotación semántica sirve en</mark>


------------------------- PAGINA 47 --------------------------

<mark>procesos de indexación, recuperación, categorización, generación de metadatos y en esta tarea se incorpora el uso de ontologías.</mark>

<mark>La anotación semántica usa información a partir de estructuras conceptuales y lleva a cabo los procesos de reconocimiento de nombres de entidades a partir de categorías predefinidas como nombres propios, lugares, fechas, organizaciones. Tiene en cuenta también fenómenos como la metonimia, la polisemia y la elipsis. Se da un proceso de extracción de términos referidos a conceptos en dominios específicos en el que se vinculan ontologías que recogen conceptos, relaciones, atributos e instancias (Viltres y Rodríguez, 2019) y los cuales enriquecerán el texto. Para esto, se proponen métodos de aprendizaje supervisado, semisupervisado y no supervisado, que son explorados en trabajos como los de Jurafsky y Martin (2019).</mark>

Como afirman Kulmanov _et al.:_

la base de conocimiento en las ontologías puede utilizarse de varias maneras. Algunas aplicaciones importantes son la construcción automática y coherente de ontologías basadas en axiomas y la consulta del conocimiento del dominio o de los datos asociados a las clases de la ontología utilizando los axiomas. La construcción de ontologías basadas en axiomas y, en particular, la referencia a clases de otras ontologías en estos axiomas, permite reutilizar el conocimiento existente y verificar la consistencia (2021).

Y en este sentido, una aplicación práctica de las ontologías podría ejemplificarse en el uso de ellas en muchos dominios, tanto de conocimiento como empresariales. Un repositorio muy representativo para el campo de la biología y la biomédica, por ejemplo, es el BioPortal<sup>2</sup> que reúne más de 1000 ontologías con más de quince millones de clases que son usadas en muchas tareas de aprendizaje de máquinas, como la predicción de la asociación genotipo-fenotipo, la función de las proteínas, la predicción del fármaco y el objetivo, la interacción proteína-proteína, la asociación entre genes y enfermedades, entre otras.

> 2 Sitio web en donde se dispone conocimiento y datos biomédicos utilizando ontologías que sean semánticamente interoperables. Disponible en: <u>https://bioportal.bioontology.org/</u>


------------------------- PAGINA 48 --------------------------

# **3.2. Métodos para desarrollar ontologías**

Diversos métodos se han propuesto para el diseño y desarrollo de las ontologías. Estos métodos van desde la formulación del proyecto ontológico hasta su mantenimiento y actualización permanente. Los métodos también incluyen el abordaje de técnicas para la fusión, mezcla y aprendizaje de ontologías, que es especialmente de donde parte este trabajo para la construcción del grafo. En la <u>tabla 3 se describen brevemente algunos de</u> los más clásicos, ordenados cronológicamente.


------------------------- PAGINA 49 --------------------------

## **Tabla 3**

_Métodos clásicos para desarrollo de ontologías_

|**Método**|**Propuesta**|
|---|---|
|Método Cyc (1984)|Propuesto en el _Microelectronics and Computer Technology Corporation_<br>(MCC), es un proyecto que estuvo orientado a la construcción de una base<br>que contenga el conocimiento humano para realizar inferencias de manera<br>automática.|
|Método de Uschold y King (1995)|Este método propuso capturar el conocimiento, codificarlo e integrar la<br>ontología con otras ontologías.|
|Metodología de Grüninger y Fox (1995)|Se propuso una metodología que se inspira en el desarrollo de sistemas<br>basados en conocimiento mediante la lógica de primer orden.|
|_Sensus-Based Method_(Swartout_et al._, 1997)|Esta es una ontología que fue desarrollada en el ISI (_Information Science_<br>_Institute_) para su uso en el procesamiento del lenguaje natural, con el fin de<br>ofrecer<br>una amplia base conceptual para el desarrollo de máquinas<br>traductoras.|
|_Methontology_(Fernández_et al._, 1997)|Desarrollada por el Grupo de Ontologías de la Universidad Politécnica de<br>Madrid, es una metodología que permite la construcción de ontologías en el<br>nivel del conocimiento.|


------------------------- PAGINA 50 --------------------------

|**Método**|**Propuesta**|
|---|---|
|Método de Kietz_et al._(2000)|Propuso utilizar como base un núcleo de la ontología (Sensus, WordNet, etc.)<br>que se enriquece con las nociones aprendidas. Los nuevos conceptos se<br>identifican usando técnicas de análisis de lenguaje natural con recursos<br>previamente identificados por el usuario y analizados a partir de varios<br>enfoques basados en la estadística.|
|Método de Aussenac-Gilles_et al._(2000)|Este método se basa en la elicitación del conocimiento, permitiendo la<br>creación de un modelo de dominio mediante el análisis de un corpus con<br>herramientas de procesamiento de lenguaje natural. Este método combina la<br>adquisición de conocimientos basados en la lingüística con técnicas de<br>modelado para mantener los vínculos entre los modelos y los textos.|
|_Text-To-Onto_(Maedche y Staab, 2000)|Esta herramienta pone en práctica algunas técnicas de aprendizaje de<br>ontologías de forma semiestructurada a partir de textos. El resultado del<br>proceso de aprendizaje es una ontología que contiene el dominio específico y<br>que es independiente de los conceptos.|
|Metodología de Noy y McGuinnes (2001)|Esta metodología propuesta usando Protège parte de que las ontologías<br>definen el vocabulario común para los investigadores que necesitan compartir<br>información en un dominio.|
|_On-To-Knowledge_(Staab_et al_., 2001)|Esta metodología incluye la identificación de los objetivos de los conocimientos<br>y de las herramientas basadas en un análisis de los escenarios de uso.|


------------------------- PAGINA 51 --------------------------

|**Método**|**Propuesta**|
|---|---|
|_BERTMap_(He_et al._, 2022)|Metodología propuesta para mapear la alineación de ontologías que consiste<br>en verificar la correspondencia existente entre ontologías a partir de métodos<br>de aprendizaje profundo que incluyen la incrustación de palabras no<br>contextuales.|
|_Linked Open Terms_(LOT) (Poveda_et al._, 2022)|Esta metodología orientada a la industria propone una serie de actividades<br>para el proceso de desarrollo de ontologías basándose en un entorno<br>colaborativo que permita su validación. También propone lenguajes de<br>representación<br>formal<br>de<br>conocimiento<br>de<br>uso<br>extendido,<br>así como<br>metodologías ágiles para el desarrollo.|


------------------------- PAGINA 52 --------------------------

La construcción de ontologías conlleva muchos desafíos relacionados con aspectos conceptuales de los dominios, así como técnicos y operativos. Dado sus costes, se plantea que el acceso, reutilización y comprensión de conocimiento es fundamental para desarrollar mejores herramientas que cumplan con el propósito de representación para la extracción y gestión de información. Sin embargo, la realidad es que las ontologías y vocabularios son a veces herramientas de difícil acceso y uso. Por tanto, se hace necesario pensar el desarrollo de ontologías a partir de unos principios que permitan el desarrollo de herramientas potentes y con un menor coste de conceptualización e implementación.

En ese sentido, Garijo y Poveda (2020) proponen la incorporación de la metodología FAIR ( _Findable, Accessible, Interoperable and Reusable_ ) de modo que los desarrolladores de ontologías puedan incorporar mejores prácticas para la nomenclatura y control de versiones, la documentación y la publicación de ontologías. Poveda _et al._ (2022) proponen una serie de pasos para el desarrollo de ontologías que parte de la definición del propósito, alcance y lenguajes de implementación. Posteriormente, se deben identificar los usos y usuarios potenciales de la ontología lo cual permitirá la definición de requisitos que deberán ser validados por el colectivo de usuarios. Luego se definirá la extracción de la terminología básica del dominio que permita establecer y afinar los requisitos en relación con lo que se espera de la ontología.

# **3.3. Lenguajes para construir ontologías**

Para la implementación de una ontología es necesario seleccionar un lenguaje a partir del cual desarrollarla. A partir de los años noventa se crearon un conjunto de lenguajes de ontologías basados en técnicas de inteligencia artificial. Los primeros lenguajes de ontologías estaban basados en lógica de primer orden, marcos combinados con la lógica de primer orden y lógica de descripción (Gómez Pérez _et al._ , 2004). Con el propósito de presentar un recuento de los lenguajes desarrollados, en la <u>tabla 4</u> se describen algunas características generales.


------------------------- PAGINA 53 --------------------------

## **Tabla 4**

## _Lenguajes de ontologías_

|**Lenguaje**|**Descripción**|
|---|---|
|_Ontolingua_(Gruber, 1993)|Este lenguaje está basado en KIF (_Knowledge Interchanged Format_) y en<br>ontologías de marcos, propuestas por Gruber (1993). _Ontolingua_ es el lenguaje<br>utilizado para construir _Ontolingua Server_, proyecto creado a mediados de los 90<br>con el objetivo de ser un sistema que sirviera como repositorio de distintas<br>ontologías.|
|FLogic_(Frame Logic_) (Kifer_et al._, 1995)|Desarrollado en el departamento de Ciencias Computacionales de la _State_<br>_University of New York,_con un enfoque orientado a objetos a partir de la lógica de<br>primer<br>orden.<br>Se<br>usó principalmente para bases de datos deductivas y<br>herramientas desarrolladas a partir de objetos, para más tarde usarse en la<br>aplicación de ontologías como OntoEdit, Protégé 2000 y WebODE.|
|OKBC<br>(_Open_<br>_Knowledge_<br>_Base_<br>_Connectivity_)<br>(Chaudhri_et al.,_1998)|El objetivo de este lenguaje propuesto por el_Stanford Research Institute_-SRI- era<br>crear un protocolo para el acceso al conocimiento almacenado en diferentes<br>sistemas de representación de conocimiento. Con OKBC se importaban términos<br>de otras ontologías.|


------------------------- PAGINA 54 --------------------------

|**Lenguaje**|**Descripción**|
|---|---|
|OCML<br>(_Operational_<br>_Conceptual_<br>_Modeling_<br>_Language_) (Domingue_et al._, 1999)|Desarrollado en el _Knowledge Media Institute._ Funciona a partir de librerías de<br>ontologías.|
|XOL (XML-_based Ontology exchange Language_)<br>(Karp_et al._, 2000)|Diseñado por _Pangea Systems Inc_. y el Centro de Inteligencia Artificial de _SRI_<br>_International_. El propósito de este lenguaje fue proveer de un formato para el<br>intercambio de definiciones ontológicas entre distintos sistemas de software.|
|RDF<br>(_Resource_<br>_Description_<br>_Framework_)<br>y<br>_RDF-Schema_(Brickley y Guha, 2000)|Lenguaje para describir recursos web a partir del uso de metadatos desarrollado<br>por el W3C (_World Wide Web Consortium_). El modelo de datos propuesto<br>equivale al formalismo de redes semánticas a partir de tres tipos de objetos:<br>recursos, propiedades y sentencias.|
|OIL (_Ontology Interchange Language_) y (_Ontology_<br>_Inference Layer_) (Horrocks, 2000)|Desarrollado en el contexto del proyecto _On-To-Knowledge_, está basado en<br>lenguajes de representación de conocimiento y combina sintaxis XML y lenguajes<br>de modelado, basados en el paradigma de representación de conocimiento<br>semántico formal y razonado.|
|DAML+OIL (Mcguinness_et al._, 2002)|Desarrollado por un comité conjunto de Estados Unidos y la Unión Europea en el<br>marco del proyecto DARPA (DARPA _Agent Markup Language_), que tenía como<br>principal objetivo permitir la marcación semántica de los recursos web.<br>DAML+OIL está escrito en XML y permite igualmente la triple notación en<br>lenguaje RDF.|


------------------------- PAGINA 55 --------------------------

|**Lenguaje**||**Descripción**|
|---|---|---|
|SWRL (_Semantic Web Rule Language)_ (Lawan <br>Rakib, 2019)|y|Es una recomendación de la W3C para extender los OWL que pretende ampliar<br>las reglas para la web semántica, de modo que el lenguaje sea más flexible y tenga<br>un mayor nivel de expresividad.|
|OWL<br>(_Ontology_<br>_Web_<br>_Language)_<br>(Antoniou<br><br>Harmelen, 2004), (Kulmanov_et al._, 2021)|y|Lenguaje propuesto por el W3C que retoma elementos de DAML+OIL. De igual<br>forma que sus lenguajes antecesores, OWL pretende constituirse como el lenguaje<br>normalizado para representar ontologías para su aplicación en la red. Es una<br>extensión de RDF Schema que combina los sentidos que OWL utiliza para<br>determinar el significado de las clases y las propiedades en RDF, añadiendo<br>formas del lenguaje que permitan un mayor nivel de expresividad.|
|_Owlready2_Python (Lamy, 2021)||Este autor propone el módulo para trabajar desde Python la construcción y<br>desarrollo de la ontología en OWL que permitirá luego que esta se guarde en<br>archivos en formato RDF/XML (el más común), pero también en OWL/XML<br>N-Triples, Turtle y otros formatos.|


------------------------- PAGINA 56 --------------------------

De acuerdo con autores como Schrader (2020) o Vasileiadis y Fragouli (2020), las ontologías se entienden como una parte primordial en la construcción de un grafo. Así lo evidencian también autores como Blumauer y Nagy quienes afirman que “las ontologías se utilizan para dar más dimensionalidad a un grafo de conocimiento: las ontologías clasifican las cosas y definen relaciones y atributos más específicos” (2020, p. 103). Se plantea también que los grafos de conocimiento serían una evolución de las ontologías en el sentido en que, dados los lenguajes y técnicas avanzadas de la computación, los grafos alcanzan por fin las tan anheladas tareas de inferir conocimiento, que fue desde el inicio un propósito del desarrollo de las ontologías en el contexto de la web semántica.

Un grafo de conocimiento se construye con la ayuda de las ontologías, en donde las entidades pueden clasificarse específicamente y convertirse así en una instancia de una o más clases, de modo que se pueda presentar un conocimiento más consistente. Las ontologías también se utilizan para aprovechar los mecanismos de inferencia. Esto es esencial para las tareas de integración de datos: las ontologías no sólo son una estructura de datos perfecta para mapear modelos de datos relacionales en el mundo de los grafos, sino que también son importantes para detectar posibles incoherencias en los datos integrados. Además, las ontologías también permiten descubrir nuevas relaciones (Blumauer y Nagy, 2020, p. 104).

Esta consideración es interesante porque destaca el nivel de relación entre las ontologías y los mecanismos de inferencia que deberán incorporar, para proveerse de una herramienta de gran utilidad que facilite la integración entre los datos.

Para alimentar la base de conocimiento que requieren los grafos se utilizan diversas fuentes de datos como taxonomías, esquemas de vocabularios y ontologías, las cuales proporcionan mayor expresividad semántica y complejidad, pues contienen tanto relaciones jerárquicas como axiomas. Sin embargo, las ontologías se consideran solo una parte del grafo. Blumauer y Nagy dicen que:

Muchas ontologías no tienen en cuenta los objetivos del proyecto ni los requisitos de las aplicaciones que deben basarse en ellas. Para desarrollar


------------------------- PAGINA 57 --------------------------

ontologías universalmente válidas (a veces también llamadas «ontologías superiores»), hay que aplicar, por supuesto, principios de diseño y métodos de gestión diferentes a los de las ontologías específicas, que a menudo sólo son relevantes para un único subdominio. Esto lleva a la confusión, y algunos creen que la ontología es ya el grafo del conocimiento (2020, p. 120).

Uno de los elementos que pueden diferenciar el trabajo desde las ontologías y los grafos de conocimiento estaría dado en el método usado para la construcción de sistemas expertos, pues los grafos de conocimiento recurren a un enfoque semántico que implica el uso de técnicas de inteligencia artificial que darían mayor expresividad y eficiencia en la compilación de datos y extracción terminológica y conceptual.

Vale anotar un concepto importante en el desarrollo de un grafo de conocimiento y es lo que tiene que ver con el aprendizaje de ontologías del cual se destacan los trabajos de Maedche y Staab (2004) o Xu _et al._ (2019). El aprendizaje de ontologías se define como el conjunto de métodos y técnicas utilizados para la construcción de una ontología nueva, o para enriquecer o adaptar una ya existente de forma semiautomática usando fuentes de información y conocimiento, previamente representados; ello con el fin de permitir una reducción en tiempo y esfuerzo en el proceso de desarrollo de la ontología.

Algunos métodos que se han usado para esto son: Método de Khan y Luo (2002), que tiene como objetivo construir una ontología de dominio de documentos de texto utilizando técnicas de agrupamiento y WordNet. El usuario dispone de una selección de documentos en relación con el mismo dominio y los conceptos en el interior se asignan de acuerdo con sus nodos descendientes en hiperónimos. El tipo de relación entre los conceptos jerárquicos se omite, tomando más bien, la relación asociativa existente entre ellos. Otro método es SOAT de Wu y Hsu (2002), que proponen un modelo para la adquisición semiautomática de ontologías dentro del corpus de un dominio. El principal objetivo de esta herramienta era extraer relaciones a partir de frases y oraciones en las cuales pueda identificarse un conjunto de palabras clave que tengan una fuerte carga semántica.


------------------------- PAGINA 58 --------------------------

Algunos métodos usados en los inicios para fusión de ontologías, cuyo objetivo es la captura del conocimiento consensuado de un dominio dado en una forma genérica y formal, para ser reutilizado y compartido a través de otras aplicaciones y por grupos diversos de personas. La alineación de ontologías consiste en establecer diferentes tipos de asignaciones (o enlaces) entre dos ontologías, preservando la ontología original. La mezcla de ontologías por su parte, se refiere a la fusión de dos o más ontologías para generar una única ontología.

<mark>Tanto el grafo como la ontología se presentan por capas según la conceptualización que requiere una descripción del dominio y un modelado correcto de los datos para la resolución del problema que se plantea. El modelado de la ontología requiere la toma de decisiones para representar correctamente los valores de las propiedades y los rangos que se presentan en las clases.</mark>

<mark>Un grafo de conocimiento está construido a partir de técnicas de procesamiento de lenguaje natural y se basa en ontologías que previamente existan. Dado que sobre este domino del conflicto armado no se identificaron ontologías propiamente dichas, se plantea aquí la construcción de una vinculando las tareas de reconocimiento de entidades, sin embargo eso lleva a varias cuestiones sobre cómo etiquetar corpus para entrenar modelos de reconocimiento de entidades y cómo integrar luego esto en un grafo de conocimiento.</mark>

<mark>En síntesis, las ontologías pueden entenderse como los formalismos de representación del conocimiento, definiendo y razonando sobre la semántica de los términos utilizados para etiquetar y describir los nodos y aristas del grafo en las que se expresan las relaciones entre entidades. Y un grafo es una “intención de datos” que incorpora el conocimiento que, a modo de esquema, se presenta en las ontologías las cuales recogen el vocabulario (terminología) para proporcionar la semántica que los grafos requieren.</mark>

A continuación se describe la técnica de reconocimiento de entidades nombradas que aquí es entendida como una categoría dentro de esta tesis. Tanto la ontología como las entidades están directamente relacionadas y confluyen luego en el grafo de conocimiento.


------------------------- PAGINA 59 --------------------------

# **Capítulo 4. Reconocimiento de entidades nombradas**

En este capítulo se explica la técnica de reconocimiento de entidades nombradas como una forma de extraer información valiosa semánticamente de un conjunto de textos. En un primer apartado se explican algunas generalidades y se describen los enfoques y las tareas para ello. A continuación, se describen los tipos de entidades nombradas para establecer cómo estas están representadas en el discurso y las dificultades que en ámbitos especializados pueden presentarse para distinguirlas y hacer el proceso de desambiguación de sentidos. Luego, se describen algunas técnicas y métricas para evaluar la eficiencia de los modelos NER y, por último, se describe la relación entre el reconocimiento de entidades nombradas y los grafos de conocimiento.

<mark>Una entidad es un elemento del mundo real representado en el lenguaje como un objeto, concepto o lugar. De acuerdo con Gupta</mark> _<mark>et al.,</mark>_

<mark>en el mundo real, se añaden regularmente nuevas entidades a las bases de conocimiento, por lo que es importante que cualquier sistema de vinculación de entidades sea extensible a dichas entidades, especialmente las que no tienen ninguna mención vinculada (2017, p. 2682).</mark>

<mark>Una entidad nombrada es una palabra o sintagma que distingue un elemento de otros con atributos similares dentro de un conjunto de textos, como es el caso por ejemplo de nombres de organizaciones, personas y lugares en el ámbito general; y el nombre de objetos, conceptos y procesos en dominios específicos.</mark>

<mark>El reconocimiento de entidades nombradas hace parte del proceso de extracción de información y se refiere a la tarea concreta de detectar menciones de entidades del mundo real a partir de un texto y clasificarlas en categorías predefinidas como lugares, personas, organizaciones, que puedan ser aplicadas posteriormente en la modelación de intereses de usuarios, en sistemas pregunta/respuesta y en sistemas de diálogo (Liang</mark> _<mark>et al.</mark>_ <mark>, 2020), c</mark> omprensión de textos, recuperación de información, resumen automático de textos, traducción automática y construcción de bases de conocimiento (Li _et al_ ., 2020), desarrollo de _chatbots_ , analizadores de contenido u opiniones de consumidores (Goyal,


------------------------- PAGINA 60 --------------------------

2021) o para la anotación semántica y el poblamiento automático de ontologías (Marrero _et al.,_ 2013).

<mark>Kejriwal</mark> _<mark>et al.</mark>_ <mark>(2021) proponen que, para la resolución de entidades en un grafo de conocimiento, se atienda a los siguientes desafíos en la extracción: la ambigüedad, la cantidad de datos de entrenamiento, las variaciones propias en un dominio específico, las formas diferentes de una misma entidad. La extracción de entidades pasa también por la identificación de relaciones entre ellas, lo cual es requerido para definir patrones sintácticos (reglas), aprendizaje supervisado, extracción de información abierta. Para llevar a cabo esta tarea “</mark> un algoritmo NER identifica una entidad nombrada y el tipo al que corresponde, considerando cada palabra en la secuencia y decidiendo a cuál tipo particular pertenece” (Kochmar, 2022, p. 393).

<mark>Muchas de las tareas del procesamiento de lenguaje natural contemplan el reconocimiento de entidades nombradas para analizar estructuras textuales, extraer términos y sintagmas a partir de estadísticas del corpus, extraer palabras para lematización, clasificar textos basándose en el aprendizaje de modelos semánticos, extraer eventos, o reconocer sentidos en oraciones completas.</mark>

<mark>El término entidad nombrada fue acuñado desde los años 90 y aparece por primera vez en el procedimiento que Lisa F. Rau propuso, para extraer nombres de empresas de los textos, que aparecían regularmente pero que incluían palabras que eran desconocidas en contraste con lo que un diccionario general de la lengua pudiera proveer (Marrero</mark> _<mark>et al.,</mark>_ <mark>2013).</mark>

# **4.1. Enfoques para el Reconocimiento de Entidades Nombradas**

Un sistema para el reconocimiento de entidades nombradas está compuesto por los tipos de entidad que deberán identificarse, la identificación misma, los criterios de anotación, y los límites válidos de identificación de la entidad. Cada uno de estos elementos representan una serie de desafíos tanto semánticos como sintácticos pues se requiere tanto conocer el dominio y la terminología propia de los campos así como brindar las herramientas conceptuales que serán la base para el reconocimiento.


------------------------- PAGINA 61 --------------------------

Los enfoques bajo los cuales es abordado el reconocimiento de entidades nombradas pueden ser: basados en reglas, aprendizaje no supervisado, aprendizaje supervisado basado en características y aprendizaje profundo.

Los enfoques basados en reglas plantean que estas pueden diseñarse a partir de nomenclaturas específicas del dominio y en patrones sintáctico-léxicos que descubren las reglas semánticas y sintácticas. Los sistemas basados en reglas funcionan bien pero requieren un léxico exhaustivo, pues como afirman Li _et al._ “debido a las reglas específicas del dominio y a los diccionarios incompletos, a menudo se observa una alta precisión y una baja recuperación en estos sistemas” (2020, p. 4). Sin embargo, esto requiere la definición de esas reglas lo que demanda un amplio conocimiento en términos del dominio.

Los enfoques de aprendizaje no supervisado parten de la idea de _clusters_ que son construidos a partir de recursos léxicos, patrones léxicos y estadísticos que aportarían información sobre grandes corpus para inferir las entidades (Li _et al.,_ 2020).

El aprendizaje basado en características parte de ejemplos de entrenamiento que hayan sido etiquetados para posteriormente definir algoritmos de aprendizaje que reconozcan patrones para identificar nuevos datos no vistos anteriormente en un corpus más amplio.

Por último, el enfoque que usa el aprendizaje profundo para descubrir información de manera automática resulta de gran interés especialmente en campos en los que no se tienen tantos datos entrenados previamente. Este enfoque utiliza métodos como representación distribuida que pueda darse a nivel de palabras, caracteres o representación híbrida que varía según las propiedades semánticas y sintácticas de las palabras que son identificadas en el texto y la distribución de palabras preentrenadas.

# **4.2. Tareas para el reconocimiento de entidades de nombradas**

Dentro del reconocimiento de entidades se pueden identificar tareas en distintos niveles que se pueden adecuar a necesidades específicas según el dominio que se quiere representar. Básicamente, se pueden distinguir al menos tres tipos de tareas: extracción de entidades, extracción de relaciones y extracción de eventos. A estas tres, se suman 60


------------------------- PAGINA 62 --------------------------

otras tareas que están relacionadas con la resolución de correferencias y con la normalización de entidades, de modo que figuras léxicas como la homonimia, la antonimia, la hiperonimia o la hiponimia puedan ser resueltas para garantizar una efectiva representación unívoca del lenguaje.

Una clase puede definirse como un conjunto de elementos que guardan relación entre sí, la palabra por su parte se entiende como una unidad léxica básica para referirse a una cosa de la realidad. Se da que “a veces la presencia de palabras individuales es suficientemente informativa para que el algoritmo identifique una clase” (Kochmar, 2022, p. 397) y esto en casos en que las palabras posean una carga semántica fuerte y que no lleven a equívocos, como en el caso de nombres propios de organizaciones, por ejemplo, que pueden ubicarse como parte de una tipología de entidad concreta, o en el de palabras de la lengua común cuyo significado puede ser fácilmente atribuible a un concepto u otro, por ejemplo en palabras como _asesinato_ o en unidades fraseológicas como _desaparición forzada de personas_ . En otros casos, sin embargo, es necesario extraer más información del contexto y de la forma en que las palabras anteriores están etiquetadas, para poder determinar el sentido de estas palabras que se activa o en el caso en que estas están integradas a otras palabras cuyo valor semántico se activa según sean una cosa u otra.

Resolver las cuestiones de sentido en niveles distintos implica también desglosar las tareas que se demandan para reconocer eficazmente las palabras y agruparlas según las clases a las que pertenecen. En este sentido, Goyal (2021) propone que un modelo NER debe seguir los siguientes pasos:

1. Identificar las frases sustantivas (sintagmas nominales) a partir del análisis sintáctico de dependencias y el etiquetado de cada parte de la oración.

2. Clasificar las frases para determinar a qué categorías corresponden, según los diccionarios y otras fuentes conceptuales.

3. Desambiguar entidades que puedan estar mal clasificadas, de modo que puedan validarse los resultados.

La detección de entidades implica como tarea también la categorización de las mismas, según se refieran a nombres, localizaciones, eventos, organizaciones. Esta


------------------------- PAGINA 63 --------------------------

categorización requiere modelos de entrenamiento para lo cual se anotan manualmente un conjunto de documentos de modo que posteriormente esta anotación pueda automatizarse y también el posterior reconocimiento de entidades.

Otra tarea que es de gran importancia es la validación humana de la etiquetación previamente existente en el corpus con el fin de contrastar la efectividad del sistema de reconocimiento de entidades versus el reconocimiento y clasificación que haría un humano, quien además fuera experto en el dominio. Es importante definir cuáles son los criterios para evaluar que el reconocimiento de entidades sea adecuado. Para eso, Li _et al_ . (2020) dan cuenta de varios sistemas de evaluación: uno cuando se da la coincidencia exacta entre el sistema NER y el reconocimiento humano para lo cual se definen métricas; la segunda evaluación es de concordancia mínima en la cual se acepta una entidad como correcta siempre que sea reconocida dentro de algunos límites y que no se contradiga con la verdad básica.

Estos procesos de validación implican dos subtareas: la detección de la coincidencia del reconocimiento según los parámetros establecidos y la desambiguación que se haga de las entidades a partir de las características que tienen, sean estas falsos positivos, falsos negativos o verdaderos positivos. El falso positivo se da cuando una entidad es reconocida pero no es verdadera; el falso negativo es cuando la entidad es verdadera pero no es recuperada por el sistema de reconocimiento de entidades. El verdadero positivo se da cuando una entidad es devuelta por el sistema. El modelo NER deberá definir los parámetros de evaluación de coincidencia para determinar la validez de los resultados (Ruder, 2022).

Para desarrollar un modelo NER los pasos que deberán seguirse en términos generales son: adquirir un corpus de textos con datos etiquetados en donde se reconozcan entidades como personas, organizaciones, lugares, etc.; limpiar y procesar el corpus de texto sin etiquetar en el que se hará la etiquetación automática; dividir el corpus en conjuntos de entrenamiento, testeo y validación; definir las clases y tipos de entidades que se recuperarán y/o usar modelos de lenguaje incorporados en bibliotecas existentes


------------------------- PAGINA 64 --------------------------

tipo _Spacy_ , NLTK, _TensorFlow_ ; evaluar el modelo de prueba y ajustar los parámetros; y, por último, utilizar el modelo para etiquetar datos no entrenados.

A continuación, se explican algunas cuestiones que están relacionadas con las dificultades y retos que se enfrentan en cada subtarea y que tienen que ver con el reconocimiento desde el punto de vista semántico de los datos.

## **Extracción de información**

En términos generales, “la extracción de información consiste en convertir un texto no estructurado en información estructurada almacenada en una base de conocimientos o en un grafo de conocimientos” (Lane _et al._ 2019, p. 343). Cuando hablamos de NER, esta extracción implica definir el modo en que se recopila la información de acuerdo con las características de los datos. Siguiendo con Lane _et al.,_

la extracción de información no es más que otra forma de extracción de características de aprendizaje automático a partir de datos de lenguaje natural no estructurados, como la creación de bolsas de palabras o incrustaciones para intentar reducir las casi infinitas posibilidades de significado del texto en lenguaje natural a un vector que una máquina pueda procesar fácilmente (2019, p. 345).

## **Extracción de relaciones**

Tanto para el reconocimiento de entidades nombradas como para el grafo de conocimiento, es necesario que se puedan establecer las relaciones entre las entidades y la naturaleza de esa relación. Ello implica la identificación de los patrones en las frases y el sentido que tiene el uso de las palabras y su posición en una frase determinada. En el caso de las máquinas, ese conocimiento se almacena en un grafo, también llamado base de conocimientos. Las aristas de un grafo de conocimiento son las relaciones entre las cosas y los nodos de un grafo de conocimiento son los nombres u objetos que se encuentran en el corpus.

Típicamente, esta relación se da a partir de la identificación del patrón Sujeto - Verbo - Objeto (Lane _et al.,_ 2019) que coincide igualmente con lo que en ontologías se conoce


------------------------- PAGINA 65 --------------------------

como tripleta de la entidad que recopila la información sobre sujeto o entidad, predicado o atributo y objeto o valor.

## **Normalización de entidades**

La normalización de entidades se refiere al proceso de reconocer los sentidos que tienen las entidades y su validación en el sistema de conocimiento, de modo que haya consistencia en el tratamiento de los datos. La normalización implica tareas en donde se corrijan aspectos tanto formales como semánticos. Tal como lo explicaron Lane _et al.,_ “la normalización de las entidades con nombre y la resolución de ambigüedades suele denominarse resolución de correferencias o resolución de anáforas, especialmente en el caso de pronombres u otros «nombres» que dependen del contexto” (2019, p. 357).

Así también, en el grafo de conocimiento se debe incluir un algoritmo de normalización de modo que cada tipo de entidad tenga un único nombre que se refiera a una misma cosa y que eso sea coherente dentro de la base de conocimientos definida. Por esta razón, es necesario establecer las relaciones de tipo “es-un” para conectar las entidades con las categorías a las que se corresponden. También normalizar elementos como fechas u otros objetos que puedan ser incorporados a la base de conocimientos (Lane _et al.,_ 2019).

# **4.3. Tipos de entidades nombradas**

Una entidad se define como un nombre (propio o común) que sirve para designar algo o alguien. Típicamente son sustantivos o sintagmas nominales que representan un objeto o “cosa” del mundo. Se reconocen dos tipos de entidades: genéricas o específicas. Las primeras estarían representadas en asuntos como personas, lugares, fechas; y las específicas representan conceptos de dominios específicos (Li _et al., 2_ 020), como para este caso en entidades como _restitución de tierras_ , _actores armados_ , _dispositivos pedagógicos_ o _derecho a la verdad_ .

Las entidades nombradas pueden clasificarse en función de los cuatro criterios siguientes: nombre propio, designación rígida, identificación única y ámbito de aplicación (Marrero _et al_ ., 2013). Algunos ejemplos en este dominio son entidades 64


------------------------- PAGINA 66 --------------------------

como _Centro Nacional de Memoria Histórica_ , _Ruta Pacífica de las Mujeres_ , _Jurisdicción Especial para la Paz_ para referirse a la clase **ORG** (instituciones u organizaciones); o expresiones que se refieren a la clase **VIO** (hecho de violencia) y que aparecen en entidades como _ejecución extrajudicial_ , _desaparición forzada_ , _detención arbitraria_ o _desplazamiento forzado_ . También pueden designar una persona en particular que se identifica con su nombre pero que tiene también una serie de atributos como rol, características sociodemográficas o participación en un hecho. O pueden presentarse algunas entidades que son usadas en otros tantos dominios, como por ejemplo los nombres de lugares o fechas.

Es muy importante definir las clases o tipos de entidades que se puedan encontrar en un NER pues de acuerdo con Lane _et al._ ,

una frase típica puede contener varias entidades con nombre de varios tipos, como entidades geográficas, organizaciones, personas, entidades políticas, tiempos (incluyendo fechas), artefactos, eventos y fenómenos naturales. Una oración puede contener varias relaciones entre las entidades nombradas en la oración (2019, p. 340).

Por ejemplo, en la siguiente oración tomada del corpus:

```
el14deenerode2004,hombredelBloqueCaciqueNutibaradelas
AutodefensasUnidasdeColombia,enalianzaconbandasconocidas
comoElHuecoyLa38,alparecer,lideradasporungrupode
reinsertados,asumieronelcontrolterritorialysocialdelbarrio
PopularUnodelaciudaddeMedellín,ordenandoeldesplazamiento
forzadodevariosgruposfamiliares,
```

se identifican las entidades: _Bloque Cacique Nutibara_ / **ARM** ; _Autodefensas Unidas de Colombia_ / **ARM** ; _El Hueco_ / **ARM** ; _La 38_ / **ARM** ; _Popular Uno_ / **GEO** ; _Medellín_ / **GEO** ; _Desplazamiento forzado_ / **AFE** .

Goyal (2021) plantea que las entidades pueden ser organizaciones, cantidades, valores monetarios, porcentajes, nombres de personas, nombres de empresas, ubicaciones geográficas (tanto físicas como políticas), nombres de productos, fechas y horas, nombres de acontecimientos. En este trabajo se definirán las clases y categorías específicas en el <u>capítulo 9,</u> pues por una parte se encuentran entidades que pueden ser


------------------------- PAGINA 67 --------------------------

reconocibles fácilmente a partir de modelos de lenguaje preestablecidos, y por otra se encuentran otras que se entienden como entidades en tanto que son elementos lingüísticos que pueden atribuirse a una clase determinada.

Esta discusión es importante porque, desde el punto de vista de las ontologías, una entidad podría entenderse como clase, así entonces la ontología tendría la conceptualización y la entidad tendría los elementos. Toda entidad pertenece a una clasificación, pero dependiendo de la representación y del modelo que se propone, una entidad bien podría ser tanto una instancia como una clase.

La extracción de entidades tiene todo su sentido cuando cada entidad está relacionada con otras. Estas relaciones constituyen los grafos y, como se dijo anteriormente, comprenden los grafos de conocimiento. La relación de estas entidades son denominadas tripletas y representadas mediante el lenguaje RDF, que recoge un sujeto, relación u objeto. Una colección de estas tripletas es un grafo de conocimiento. Los lingüistas también lo llaman a veces ontología, porque almacena información estructurada sobre las palabras. Pero cuando el grafo pretende representar hechos sobre el mundo y no sólo palabras, se denomina grafo o base de conocimiento (Lane _, et al._ 2019).

# **4.4. Técnicas y métricas para evaluación**

En este apartado se describen algunos modelos para abordar el reconocimiento de entidades nombradas que dependen básicamente de los datos anotados previamente con los que se cuenta, así como algunas herramientas disponibles y las métricas utilizadas para evaluar los modelos.

## **Modelos NER**

Un modelo para el reconocimiento de entidades nombradas (NER) trabaja básicamente sobre información que ha sido anotada previamente y necesita grandes cantidades de 66


------------------------- PAGINA 68 --------------------------

datos para que pueda realizarse exitosamente el reconocimiento de patrones. Estas entidades pueden haber sido reconocidas tanto en los modelos lingüísticos que se incorporan, así como en documentos y consultas.

Cuando no es el caso de que exista tal cantidad de datos anotados, bien sea porque la lengua sobre la que se está trabajando no se dispone de tanta información o bien porque se trata de un dominio muy específico sobre el que tampoco se encuentren tantas muestras anotadas, se proponen algunas alternativas, como las siguientes:

- anotación manual, en la cual se utilizan datos propios para entrenar un modelo;

- el uso de corpus pre-entrenados que incorporan bibliotecas como _Spacy_ y que pueden adaptarse a las necesidades específicas;

- el acceso a corpus no anotados que utilizan técnicas de extracción, caso en el cual se hace necesario contar con las entidades ya muy bien descritas;

- el uso de corpus multilingües en los cuales usar técnicas de transferencia de conocimiento para analizar el campo particular.

En este trabajo se realizan varias tareas de manera híbrida, pues se hizo necesario anotar manualmente, definir las entidades y categorías e incorporar algunos modelos para automatizar alguna parte del reconocimiento. Para ello se usa, entre otras, la técnica _fine-tuning_ que permite trabajar con datos limitados y que emplea arquitecturas de redes neuronales para procesar en varios ciclos, que se conocen como _Epoch_ .

En cuanto a las herramientas para el reconocimiento de entidades, Marrero _et al_ . (2013) describen algunas que permiten reconocer las categorías de personas, organizaciones y localizaciones como entidades, que se encuentran incorporadas ya en modelos de lenguaje, porque hay cierto consenso sobre ello y son fácilmente reconocibles en un texto; pero no tanto para otro tipo de entidades más específicas como nombres propios o comunes de procesos o productos, por ejemplo. En cualquier caso, todas las herramientas necesitan definir los tipos semánticos que van a referir.

## **Métricas para evaluación**


------------------------- PAGINA 69 --------------------------

El rendimiento de un sistema de reconocimiento de entidades nombradas se evalúa según el grado de precisión en la identificación y recuperación de las entidades, que actualmente se encuentran sobre el 90 %.

- La validez experimental establece hasta qué punto un experimento cumple con los requisitos bien fundamentados del método científico, es decir, si los resultados obtenidos evalúan de forma justa y real lo que el experimentador intentó medir. La afirmación de que NER es un problema resuelto se basa, de hecho, en los resultados de varios experimentos de evaluación, que también se someten al análisis de validez (Marrero _et al.,_ 2013, p. 9).

Los parámetros para evaluar un modelo NER son:

- **Validez de contenido:** “evalúa el grado en que las unidades experimentales reflejan y representan los elementos del dominio estudiado” (Marrero _et al._ , 2013, p. 9) y esto en función de los usuarios y sus necesidades específicas para la cual se han de determinar qué categorías deberán reconocerse.

- **Validez externa:** “evalúa hasta qué punto los resultados de un experimento pueden generalizarse a otras poblaciones y entornos experimentales” (Marrero _et al._ , 2013, p. 10). Esto permite extrapolar esas categorías o bien a otros dominios o bien para resolver otras necesidades de usuarios específicos. La validez externa también podría ser valorada en función del tamaño del corpus y la heterogeneidad de los textos que lo conforman.

- **Validez de convergencia:** “evalúa en qué medida los resultados de un experimento están de acuerdo con otros resultados, teóricos o experimentales, con los que deben relacionarse” (Marrero _et al.,_ 2013, p. 10). Para ello es importante establecer un mecanismo de comparación entre anotadores, sean humanos o automáticos, para validar una correspondencia semántica en la selección y recuperación de entidades.

- **Validez de conclusiones:** “evalúa el grado de justificación de las conclusiones extraídas de los resultados de un experimento” (Marrero _et al._ , 2013, p. 11).


------------------------- PAGINA 70 --------------------------

En cuanto a las métricas, en un modelo NER se evalúan los siguientes aspectos: **precisión** _,_ que mide la cantidad de predicciones correctas que efectúa el modelo sobre todas las predicciones; **recuperación** , mide cuántos de los casos positivos predijo correctamente sobre todos los casos positivos de los datos; y **F1-score** , que combina los elementos anteriores en una sola medida y proporciona el equilibrio.

# **4.5. Reconocimiento de entidades nombradas para grafos de conocimiento**

La relación que se establece entre el reconocimiento de entidades nombradas y los grafos de conocimiento está dada en el hecho de que los grafos necesitan identificar aquellos conceptos que representan entidades en los textos, especialmente en dominios que, como se ha dicho anteriormente, no se encuentran ontologías o bases de conocimiento estandarizadas. Así mismo, los grafos deben incluir características lingüísticas como la sinonimia, la homografía o la polijerarquía y determinar los modos en que la extracción y la vinculación de las entidades pueden darse.

También se menciona que:

la vinculación de entidades, la tarea de identificar la entidad del mundo real a la que se refiere una mención en el texto, proporciona la capacidad de relacionar el texto con las bases de conocimiento existentes y, por lo tanto, apoya múltiples tareas de comprensión del lenguaje natural y de adquisición de conocimientos (Gupta _et al._ , 2017, p. 2681).

La relación más claramente establecida estaría justificada de acuerdo con Marrero _et al._ , quienes dicen que:

el Reconocimiento de Entidades Nombradas juega un papel muy importante en otras tareas de Extracción de Información como la Identificación de Relaciones, así como en las áreas de anotación semántica, población (compilación) de ontologías o minería de opiniones (2013, 13).


------------------------- PAGINA 71 --------------------------

Otra aplicación en la que puede evidenciarse la relación entre NER y grafos estaría dada por que:

la minería de textos basada en tecnologías RDF no se limita a extraer términos o grupos de palabras, sino que extrae entidades de los textos que se refieren a recursos en un grafo de conocimiento definido. Se crea automáticamente un enlace entre un pasaje de texto y un nodo de un grafo de conocimiento. Este proceso se denomina «evento de etiqueta» y puede expresarse y almacenarse como un conjunto de triples RDF (Blumauer y Nagy, 2020, p. 124).

Los modelos basados en entidades como los propuestos en Santoso _et al._ (2021) y en Wang, K. _et al_ . (2021) facilitan el proceso de detección de menciones y su correspondiente desambiguación, lo cual es una parte clave en el desarrollo ontológico y la construcción de grafos de conocimiento.

El reconocimiento y desambiguación de entidades permite trabajar con textos no estructurados y contribuir a la construcción de corpus con anotaciones de entidades y sus relaciones semánticas, lo cual permite a su vez aprovechar recursos disponibles. Sin embargo, la desambiguación no resulta ser siempre sencilla. Algunos trabajos como la Ontología de Reconocimiento de Entidades con Nombre (NERO) para anotación de entidades en el campo biomédico, propuesta por Wang, K. _et al._ (2021), desarrolla una metodología para el descubrimiento de entidades a partir de distintos niveles de ambigüedad que pueden presentarse en sublenguajes de campos conexos como la biología molecular, la genética, la bioquímica o la medicina. Este trabajo concretamente propone el uso de NER como técnica para la extracción de conceptos que amplíen una ontología. Por su parte, trabajos como el de Wang, X. _et al._ (2021) proponen CHEMNER, un método ontológico guiado por ontologías y supervisado a distancia, de modo que pueda aprovecharse la estructura ontológica existente sobre química para descubrir y extraer información en datos no estructurados.

Dentro del dominio del conflicto armado no se dispone de ontologías o de otra información que haya sido anotado previamente, por tanto la técnica de reconocimiento


------------------------- PAGINA 72 --------------------------

de entidades nombradas en esta tesis se incorpora como una tarea vinculada a la extracción terminológica y conceptual. Al no contar con recursos descritos y disponibles, NER puede detectar y categorizar entidades; la ontología por su parte puede entender el dominio específico incluyendo entidades y conceptos en sus contextos.

Como ilustran Dou _et al._ (2018), la relación entre las entidades y las tareas de reconocimiento y extracción y los grafos de conocimiento se demuestra en la arquitectura que construyen para describir el dominio de conocimiento del patrimonio cultural chino.

Una ontología incorpora las entidades de un dominio, por tanto la vinculación entre reconocimiento de entidades y la ontología. Un modelo que se utilice para extracción y representación de información en este dominio incorpora modelos de lenguaje en los que se reconozcan automáticamente entidades como militar, líder político, organización armada, lugares. El reconocimiento de entidades en un corpus de conflicto armado puede utilizar una combinación de aprendizaje automático, para detectar elementos como los enunciados antes; y revisión humana para dotar de ejemplos anotados de elementos concretos del dominio.

Las tareas involucradas en esta fase empiezan con el preprocesamiento de los datos que incluyen tareas de tokenización, lematización y eliminación de palabras vacías o que no aportan mucho significado. A continuación se entrena un modelo a partir del uso de algoritmos de aprendizaje en los que se reconozcan ejemplos de entidades anotadas en contexto que posteriormente sirvan para ayudar a predecir la aparición de estas u otras similares en nuevos datos. Luego se evalúa el rendimiento del modelo para asegurar su precisión y fiabilidad, para lo cual se establecen parámetros como precisión, recuperación y puntuación _F1_ , los cuales fueron descritos antes.

El modelo NER se entrena con un conjunto de datos etiquetados que contiene ejemplos de entidades con nombre en el contexto de un conflicto armado. A continuación, el modelo se utiliza para identificar entidades con nombre en el corpus sin etiquetar. El resultado del modelo NER es una lista de entidades con nombre y sus contextos


------------------------- PAGINA 73 --------------------------

correspondientes. Estas entidades pueden ser personas, organizaciones, lugares o unidades militares.

Basándose en los resultados de la evaluación, se puede ajustar el modelo para mejorar su rendimiento. Esto puede implicar tareas como ajustar los hiperparámetros del modelo, adquirir más datos de entrenamiento o probar diferentes algoritmos de aprendizaje automático, tareas que se describen ampliamente en el <u>capítulo 9.</u> Las entidades con nombre del corpus son revisadas y corregidas manualmente. Este paso es necesario para garantizar la precisión y coherencia del proceso de reconocimiento de entidades con nombre.

En general, el reconocimiento de entidades nombradas en un corpus de conflictos armados es una tarea compleja que requiere una combinación de aprendizaje automático y colaboración externa para validar datos, ampliar ejemplos, mejorar la precisión conceptual y de rendimiento del modelo. El resultado del proceso es una lista de entidades con nombre y sus contextos correspondientes, que puede utilizarse para el análisis y la comprensión del conflicto armado.

Para ilustrar el proceso, planteamos que, en primer lugar, puede utilizar el reconocimiento de entidades con nombre para identificar menciones de entidades en el texto, como países, regiones y organizaciones. A continuación, puede utilizar el enlace de entidades para vincular estas menciones a las entidades correspondientes de la ontología. La ontología puede utilizarse para definir las relaciones entre entidades y proporcionar información adicional sobre ellas.

Por ejemplo, la ontología puede contener información sobre las fechas de inicio y fin de los conflictos armados, los participantes en los mismos y sus resultados. Al integrar el reconocimiento de entidades con nombre y la vinculación de entidades con una ontología de conflictos armados, se puede crear un sistema capaz de identificar y vincular las menciones de entidades en el texto con las entidades correspondientes en la ontología. De este modo, se puede extraer información sobre conflictos armados a partir de un texto y obtener información sobre las relaciones entre entidades y los resultados de estos conflictos.


------------------------- PAGINA 74 --------------------------

*(página sin texto extraíble)*


------------------------- PAGINA 75 --------------------------

# **Capítulo 5. La terminología en el dominio de los conflictos armados**

En este capítulo se define tanto la terminología propia de la tesis como del dominio. Esta tesis tiene sus fronteras entre la terminología como disciplina, el tratamiento computacional del lenguaje y la representación de conocimiento, por tanto palabras como categoría, clase, entidad, atributo o dominio son utilizadas por cualquiera de estos campos y pueden llegar a tener algún grado de connotación particular en cada uno de ellos. Por esta razón, este capítulo se propone en tres partes: en la primera se explica lo que se entenderá por cada uno de estos conceptos, el segundo apartado aborda el valor terminológico del léxico que integra este corpus y presenta la naturaleza del material lingüístico encontrado para explicar aquellas unidades léxicas que son entendidas desde la representación de conocimiento como unidades léxicas con valor especializado. Por último, en el tercer apartado se presentan las entidades y clases definidas para representar información sobre conflicto armado y se muestran concretamente los atributos e instancias que permiten ampliar esa representación.

Este trabajo tiene una relación clara con la terminología, pues se plantea como un recurso terminológico en donde se han de entender las clases como heterónimos o clasificadores terminológicos y a las entidades como categorías, así como las instancias que se entienden aquí como términos aún cuando sean nombres propios o comunes de uso en la lengua general. Cuando se trabaja con aplicaciones, en este caso de representación de conocimiento, se genera terminología, bien vista esta desde el ámbito del procesamiento de lenguaje natural o la inteligencia artificial; o desde el punto de vista más lingüístico.

# **5.1. Terminología metodológica de la tesis**

En este apartado se explicarán los conceptos básicos para entender tanto la comprensión del dominio como la estructura metodológica y los elementos que componen el modelo de clasificación y la ontología sobre conflicto armado. Dentro de la estructura metodológica es importante distinguir lo que se entiende por categoría, clase, entidad,


------------------------- PAGINA 76 --------------------------

atributo o dominio, bien desde el ámbito del procesamiento de lenguaje natural, la representación del conocimiento y la terminología.

Como se ha mencionado antes, esta es una tesis que viene desde la representación del conocimiento con fines de recuperación de información, y pasa por él ámbito de las tecnologías de la lengua para usar recursos, técnicas y herramientas propuestas por el procesamiento de lenguaje natural o la lingüística computacional, pero que también tiene interés en la teoría del conocimiento y la lingüística para entender cómo se representa el mundo y cómo este se estructura en recursos terminológicos. Por tanto, la terminología propia de esta tesis está ligada a las ontologías, los grafos y la anotación de corpus.

A continuación se definen los términos más relevantes para comprender el desarrollo posterior de la construcción del modelo de clasificación de entidades, la ontología y el grafo de conocimiento.

Una **clase o categoría** hace referencia a un grupo de elementos que tienen características comunes. Como su nombre lo indica, la clase es aquello que permite distinguir una cosa de otra. En el proceso de construcción de una base de conocimiento, es importante distinguir entre una clase y su nombre. Noy y McGuinnes lo explican:

las clases representan conceptos en el dominio y no las palabras que denotan estos conceptos. El nombre de una clase puede cambiar si elegimos una terminología diferente, pero el término en sí representa la realidad objetiva en el mundo (2001, p. 13).

Dentro del ámbito de la programación, una clase es la forma de encapsular una determinada funcionalidad a partir de los rasgos de semejanza que puedan encontrarse entre los elementos que componen la clase o categoría.

Una **entidad** puede definirse léxicamente como aquello que constituye la esencia o la forma de una cosa. Desde el punto de vista del procesamiento de lenguaje natural y la representación de la información, una entidad se refiere a una palabra o conjunto de palabras que designan un objeto de la realidad, sea lugar, persona, objeto.


------------------------- PAGINA 77 --------------------------

Para el caso de las ontologías, la importancia de definir una convención para nombrar los conceptos reside en el hecho de que esto facilitará la consistencia lógica de los datos de la ontología, en la que más que las denominaciones propiamente dichas, se establecen los nombres de conceptos y sus variaciones. Es importante entonces definir claramente el modo de denominar a las clases y los atributos y diferenciar explícita y claramente cada cosa (Noy y McGuiness, 2001).

En este sentido, es importante diferenciar la entidad de un concepto propiamente dicho de la o las denominaciones que pueda tener ese objeto (variación denominativa para la terminología), pues son estas las que se materializan en el lenguaje dentro de un texto de especialidad. Sin embargo, el proceso de identificación de estas terminologías o de estas entidades está mediado por el rastreo de las terminologías específicas de un dominio concreto.

Una **entidad nombrada** puede ser un nombre propio de persona, institución o lugar que tienen unos atributos y características claramente definidos e identificables, que incluso ya han sido descritos en otras ontologías, vocabularios o taxonomías, tanto de dominios específicos como de ontologías fundacionales que recogen elementos y sus atributos prototípicos.

El reconocimiento de entidades nombradas es la tarea para localizar y extraer dichos elementos con fines de clasificación textual. Como se mencionó antes y de acuerdo con Marrero _et al._ (2013) las entidades pueden reconocerse según categoría gramatical, designación rígida, identificación única y dominio de aplicación. La categoría gramatical estaría definida por nombres propios o nombres comunes que designan entidades del mundo, por ejemplo _combatiente_ o _atención humanitaria_ . La designación rígida se refiere a entidades que adquieren un valor determinado como en entidades como _Juan Manuel Santos_ que sería una instancia de _presidente_ , el cual no sería rígido porque es una designación cuyo valor cambia. La identificación única se refiere a entidades cuyo valor semántico teóricamente no es variable, sin embargo, también se dice que hay identificadores cuyos significados dependen del conocimiento referencial o del conocimiento compartido que se tenga sobre este. Por último, el dominio de


------------------------- PAGINA 78 --------------------------

aplicación hace referencia a que “la finalidad y el ámbito de aplicación han determinado las entidades con nombre que hay que reconocer desde el principio” (Marrero _et al.,_ 2013, p. 5).

Los **atributos** son las cualidades o propiedades propias de una entidad y están representados en términos de datos que pueden ser numéricos, de texto, imagen o cualquier otro tipo de información. Son utilizados especialmente para describir y clasificar a las entidades.

Un **dominio** se entiende como el conjunto de conceptos, principios y reglas de un campo o área de especialidad, de lo cual son un claro ejemplo campos como la medicina, el derecho, la economía. En el contexto de esta tesis se entiende como el conjunto de conceptos (y por lo tanto terminología) propio de un campo como los conflictos armados. Por su parte, en el contexto de los sistemas computacionales, un dominio se entiende como el campo en el cual se desarrollan conceptualmente áreas en las que se propondrán herramientas y recursos como las ontologías.

Un **término** representa un papel fundamental en la representación y organización de conocimiento de especialidad, pero es un hecho que estos, “como toda unidad léxica, son fruto de una convención social y están sujetos a variación, que se manifiesta en las denominaciones alternativas de un concepto o en la apertura significativa de una forma” (Cabré, 1999 en Fernández-Silva y Becerra, 2015, p. 186). También puede ser entendido como unidad de valor especializado para integrar elementos del léxico general, cuyo significado particular y especializado es activado según el contexto en el que estas unidades se presentan y son dadas por la necesidad de comunicación entre expertos o de expertos hacia la sociedad para divulgación de conocimiento.

Sobre el conocimiento especializado, se apunta que,

los expertos se comunican entre sí, forman especialistas o divulgan el conocimiento experto a la sociedad mediante discursos específicos y, al mismo tiempo, muy variados. Su objeto no es la terminología, sino el conocimiento experto, que reformulan o que transmiten. La naturalidad


------------------------- PAGINA 79 --------------------------

radica entonces en que no es posible transmitir ni reformular el conocimiento especializado sin terminología (Lorente, 2013, p. 11).

Y es sobre esta terminología que se proponen herramientas de sistematización y disposición de todo ese conocimiento acumulado que es representativo de los discursos especializados.

Una **instancia** es el individuo de una clase, es decir un objeto que tiene los atributos de una clase con valores específicos y concretos. Aquí encontramos elementos como nombres propios de personas, organizaciones o eventos que son importantes para la comprensión del dominio.

Existe un punto de conexión entre lo terminológico y lo computacional en el sentido de que se hace necesario explorar el lenguaje del dominio para reconocer las entidades y traducirlas a un formato o estructura que pueda ser automatizable. En los grafos de conocimiento las entidades están definidas a partir de tripletas que se componen de Tema, Propiedad y Objeto para indicar las relaciones conceptuales a partir de las cuales se puedan expresar y encontrar dichas relaciones.

# **5.2. Valor terminológico del léxico en ámbitos de especialidad transdisciplinarios**

La organización y representación del conocimiento se ocupa de estudiar los métodos para almacenar, organizar y recuperar información, y se lleva a cabo un proceso de mediación a partir de un lenguaje de codificación de los conceptos, la cual es útil para entender y recuperar el sentido de los datos, así como para definir cuáles son las clases más genéricas y específicas de un dominio determinado. Sin embargo, existen dificultades para elegir cuándo es una u otra dado que las clases muy genéricas no son del todo aptas para discriminar información especializada, mientras que las clases más específicas atomizan en lugar de reunir.

En este escenario entonces surge la terminología como una disciplina que permite definir con máximo cuidado las clases y entidades en una estructura de conocimiento. Desde el punto de vista de la organización y recuperación de conocimiento, la


------------------------- PAGINA 80 --------------------------

terminología está relacionada con la construcción y disposición de lenguajes documentales que recogen el conjunto de términos relacionados semánticamente y que integran lenguajes de especialidad. Estos lenguajes son utilizados como base léxica para codificar y transmitir las relaciones y nociones de los dominios de conocimiento con el fin de representar para describir y recuperar información.

Se puede entender un dominio de conocimiento como un área que tiene un objeto de estudio que está acompañado por teorías, métodos y preguntas que buscan la comprensión y el análisis de un fenómeno o de una parte de la realidad. En este caso se entiende el conflicto armado colombiano como un campo al que han aportado otras disciplinas, pues se encuentran tanto estudios académicos propiamente dichos desde campos como la sociología, el derecho, el trabajo social, las ciencias de la información, la psicología, la memoria, entre otros, así como información que producen instituciones dedicadas a la defensa de los derechos humanos que cuentan con discursos profesionales pero también con el saber de las comunidades que se han dedicado al tema.

El conocimiento producido en este dominio puede entenderse como de especialidad, puesto que tiene una terminología propia que también es alimentada por las conceptualizaciones y denominaciones que han realizado otras disciplinas y las mismas comunidades afectadas por el conflicto armado o que actúan por la defensa y restitución de los derechos humanos vulnerados. Estas terminologías son la base para la extracción de las clases principales que conforman la ontología o base de conocimiento del grafo.

Una terminología está compuesta por un conjunto de nociones que están representadas en expresiones que sirven para denominarlas.

Es necesario tener en cuenta que dichas expresiones pueden ser estrictamente lingüísticas (palabras o grupos de palabras), estrictamente extralingüísticas (elementos ajenos al alfabeto) o mixtas. La característica común de estas expresiones es que se usan para denominar y no sólo para designar (Pérez Hernández, 2002).


------------------------- PAGINA 81 --------------------------

Esta denominación se hace concretamente para facilitar una comunicación especializada.

Dicha terminología a su vez estaría constituida por términos, entendidos como:

unidades sígnicas que poseen una doble cara: la de la expresión, que se hace patente por medio de la denominación (la estructura morfo-fonológica del término y las distintas posibilidades de formación y combinación de términos); y la del contenido, en la que se representa la noción o concepto a que se refiere la denominación (Cabré, 1993, p. 195).

Las unidades terminológicas se pueden evaluar en relación con el campo conceptual al cual pertenecen y los tipos de texto en los que aparecen. Pueden clasificarse también en función de la estructura morfosintáctica que dichas unidades terminológicas tienen.

Para hacer análisis automático de terminología en campos de especialidad, es importante establecer los constituyentes de las palabras que conforman los términos y establecer la diferenciación entre nombres abstractos y concretos y entre lo que Estopà (1999) plantea para diferenciar entre una unidad terminológica y una unidad de significado especializado, en la que se estaría reconociendo en el primer caso palabras monoléxicas que son claramente identificables en un campo de saber específico; y en el segundo caso, se encontrarían palabras como verbos, adjetivos o adverbios que se consideran de uso de la lengua general, pero que en el contexto del lenguaje especializado, adquieren una significación concreta para ese ámbito o dominio.

Es común que, por la riqueza propia del lenguaje, en las terminologías de un dominio se encuentren términos sinónimos o cuasisinónimos que puedan dar lugar a confusiones o imprecisiones tanto terminológicas como conceptuales. Por eso es importante reconocer que los sinónimos del mismo concepto no representan clases diferentes, sino tan sólo nombres alternativos para un concepto o término. A la hora de implementar un sistema de reconocimiento de entidades para el poblamiento del grafo, esto implica atender a lo esencial en términos del significado de los datos y lo que de ello pueda ser automatizable.


------------------------- PAGINA 82 --------------------------

La terminología estudia el lenguaje y su relación con objetos del pensamiento, con ese problema inherente de designación de los objetos de la realidad. Históricamente ha servido en el proceso de nombrar elementos de las ciencias y ha participado activamente en la descripción de los conocimientos científicos proporcionando estudios minuciosos de la relación entre concepto y denominación como una respuesta a la necesidad de crear un lenguaje preciso para la comunicación de la ciencia.

Durante la década de los setenta en el siglo pasado se reconoce internacionalmente a la terminología como un campo independiente que se nutre de otras disciplinas y que aparejada con los procesos de normalización y estandarización, contribuye con teorías, métodos y técnicas para el estudio de las lenguas de especialidad y el desarrollo de herramientas y recursos terminológicos con múltiples propósitos: la documentación, la traducción, los estudios lexicográficos, la normalización, la representación de conocimiento.

Actualmente, el paradigma dominante (Cabré, 1999) ha contribuido a la ubicación de la terminología en la encrucijada entre cognición, comunicación y lingüística, dando respuesta a las limitaciones del modelo anterior (Wüster, 1968), abriendo la puerta a la variación denominativa y conceptual como natural y necesaria y a toda una serie de principios teóricos fundamentales para la comprensión de la naturaleza de la unidad terminológica y de los discursos especializados. La terminología hoy plantea como objeto de estudio la unidad terminológica, entendida como una unidad léxica cuyo significado especializado se activa en función del uso en contextos comunicativos reconocidos como especializados.

El trabajo terminológico es fundamental en esta investigación puesto que,

el terminólogo trabaja con conceptos, y de forma sistemática elabora y define las relaciones conceptuales que existen entre esos conceptos, crea taxonomías y especifica cuáles son las unidades léxicas que se emplean en las diversas lenguas objeto de su estudio para hacer referencia a esos conceptos (Moreno Ortiz, 2008, p. 3).


------------------------- PAGINA 83 --------------------------

Así que el estudio del lenguaje especializado en este dominio particular, contribuye a la construcción del sistema de representación conceptual que pueda luego ser estandarizado y consensuado para explicitarlo en una herramienta.

El aporte concreto de la terminología a la construcción de ontologías es de gran importancia pues aporta en rigor y sistematicidad. En esta tesis, se busca definir los parámetros, características, atributos y valores que tienen tanto las clases de la ontología como las entidades nombradas en el corpus, que están representadas en las unidades léxicas o fraseológicas que aparecen en los textos del dominio.

Las unidades denominativas (unidades léxicas o lexicalizadas) o unidades fraseológicas (combinaciones no lexicalizadas) poseen estructuras lingüísticas claramente diferenciables según las categorías gramaticales de las palabras y las estructuras sintácticas de las mismas en los textos. Estas estructuras se basan en tres tipos de unidades frasales: nominales, cláusulas y modificadoras. Las nominales son a menudos sustantivos y se usan para representar objetos del mundo, las cláusulas representan eventos y por tanto hay un uso de verbos; y las modificadoras, que sirven para ampliar los significados nominales o de cláusulas y por tanto hay una aparición mayor de adjetivos y adverbios (Marneffe _et al.,_ 2021).

Ahora, reconocer estas estructuras sintagmáticas es fundamental para los procesos de automatización de lenguaje. Pero, además de eso, es necesario también reconocer las dificultades relacionadas con lo semántico, entre las que se encuentran la necesidad de establecer cuando una unidad tiene un carácter especializado en sentido estricto, es decir que es un término; o cuando es una palabra o frase que hace parte de la lengua común pero que de acuerdo al contexto adquiere un valor de significación especializada.

Sobre este asunto, Estopá (1999) plantea que para extraer automáticamente terminología, es necesario diferenciar una unidad especializada y reconocer dónde empieza y termina un sintagma terminológico. Una de las dificultades centrales que se plantea en este sentido es que:

los extractores no pueden reconocer fácilmente unidades léxicas especializadas porque éstas no presentan ningún elemento que las haga


------------------------- PAGINA 84 --------------------------

fácilmente identificables. Tampoco pueden delimitar todas las unidades especializadas de los textos especializados si utilizan exclusivamente patrones morfológicos o morfosintácticos para reconocer y delimitar las unidades terminológicas (UT) (Estopá, 1999, p. 22).

Estopá señala que en los textos de especialidad no solamente se encuentran términos propiamente dichos con una conceptualización y descripción teórica fuerte, sino que también, se aparecen otras unidades de la lengua general que dado el contexto adquieren significación especializada. En este dominio se encuentran ejemplos de esta situación pues hay elementos relacionados con el lugar o las características de personas que en este ámbito resultan de gran relevancia semántica, pero que sí que son unidades léxicas o fraseológicas de múltiples dominios o transversales a discursos de la vida cotidiana.

Estopá incorpora también un concepto que se considerara aquí fundamental y es el de incluir a las Unidades de Significación Especializada (USE) dentro de las unidades terminológicas, pues aquellas son palabras o frases que “vehiculan conocimiento especializado y que formalmente abarcan diversos tipos de unidades sígnicas tanto lingüísticas como no lingüísticas” (Estopá, 1999, p. 25). Se plantea también que el léxico especializado no está preestablecido, ni es uniforme, sino que se da una gran variación que no muestran los diccionarios especializados en los campos de estudio que analiza. Esto ocurre tanto en campos en los que existe una gran cantidad de recursos terminológicos y conceptuales, incluso ontologías de amplio reconocimiento, así como en un campo como este donde confluyen varias disciplinas y hay tanta variedad léxica.

Para ilustrar esto, Estopà plantea en su tesis varios ejemplos de conocimiento en campos muy claramente definidos como son el derecho y la medicina, y dentro de ellos reconoce unas categorías y unas estructuras muy claras y la aparición de ciertos fenómenos que también son recurrentes.

También vale la pena mencionar recursos como los de Biportal que dispone de gran cantidad de ontologías en ciencias biomédicas y campos afines. Pero en el caso del conflicto armado y de los textos que conforman este corpus se encuentra que el valor terminológico de las palabras encontradas está determinado por una serie de elementos


------------------------- PAGINA 85 --------------------------

que van más allá de lo terminológico y que se expresan en el uso concreto de expresiones de la lengua general presentes en los textos.

En este sentido, es importante describir a las categorías gramaticales que son susceptibles de ser términos en este campo, pues cuando se definieron las entidades estas reconocen tanto unidades terminológicas propias de algún ámbito temático, como palabras que llamaríamos de uso general cuyo valor de significación especializado se activa dentro del campo desde el contexto de los textos en los que ellos aparecen.

Se distingue entre unidades terminológicas y unidades de significación especializada. De las unidades terminológicas se encuentra que estas pueden ser poliléxicas o monoléxicas. En cuanto a los términos, estos pueden estar constituidos por sintagmas nominales, nombres y adjetivos o algunas preposiciones. Reconocer cuál es la estructura lingüística que tienen los términos, permite que se puedan establecer las reglas mediante las cuales un sistema de reconocimiento de entidades pueda establecer cuándo una palabra y sus palabras adyacentes, pueden convertirse en un término que pueda ser reconocido como entidad, que sea debidamente clasificado y llevado a la categoría semántica que pertenece.

Las unidades terminológicas tienen como función en el texto representar y transmitir conocimiento especializado. Si bien hacen parte del léxico general, su significado particular y especializado es activado según el contexto en el que estas unidades se presentan y son dadas por la necesidad de comunicación entre expertos o de expertos hacia la sociedad para divulgación de conocimiento. Pues como lo explica Lorente:

los expertos se comunican entre sí, forman especialistas o divulgan el conocimiento experto a la sociedad mediante discursos específicos y, al mismo tiempo, muy variados. Su objeto no es la terminología, sino el conocimiento experto, que reformulan o que transmiten. La naturalidad radica entonces en que no es posible transmitir ni reformular el conocimiento especializado sin terminología (2013, p. 11).

Es importante destacar lo del contexto porque justamente el valor de estas palabras que son recopiladas tanto en las fuentes terminológicas como en el corpus tienen su


------------------------- PAGINA 86 --------------------------

activación por el conjunto de otras palabras que se encuentran cerca y “esta activación consiste en la selección de los rasgos morfosintácticos generales de la unidad y de una serie de rasgos semánticos y pragmáticos específicos que describen su carácter de término de un determinado ámbito” (Cabré, 1999, p. 132).

Dentro de la variación terminológica, se identifica la variación denominativa para entender formas distintas (variantes) de los términos en un campo de especialidad. Esta puede ser autovariación para referirse a las denominaciones distintas que hace un mismo autor o heterovariación para indicar que hay variedad denominativa entre distintos autores (Freixa, 2005).

El valor semántico de las palabras en un corpus está determinado por la variedad y el contexto de las mismas.

La variación terminológica no se reduce a la variación denominativa, aunque ésta sea el tipo de variación mejor descrito en terminología. Además, en el ámbito aplicado de la normalización o de la creación de recursos también es la variación más representada. No obstante, la variación terminológica incluye también la variación semántica (denominada habitualmente variación conceptual, aunque no son sinónimos porque se asocian a universos distintos, aunque relacionados: el cognitivo y el lingüístico) (Lorente, 2013, p. 13).

La variación denominativa, que estaría en relación con la diferenciación que se hizo antes del tipo de entidades, puede darse por causas dialectales, funcionales, discursivas, interlingüísticas o cognitivas (Freixa, 2002), que son relativamente identificables en una lectura. Sin embargo esas causas no son evidenciables explícitamente en un texto para desarrollar tareas de reconocimiento automático, por lo que plantear modelos y técnicas de aprendizaje profundo es interesante en el reconocimiento de esas distintas variaciones y reconocer a cuáles clases semánticas podrían ser asignadas.

El valor terminológico de una unidad léxica se activa en función del contexto en una situación comunicativa determinada. De acuerdo con Cabré “esta activación consiste en la selección de los rasgos morfosintácticos generales de la unidad y de una serie de


------------------------- PAGINA 87 --------------------------

rasgos semánticos y pragmáticos específicos que describen su carácter de término de un determinado ámbito” (1999, 132).

Así entonces, el material lingüístico que se encuentra en este campo incluye tanto nombres comunes, que técnicamente no serían terminología pero que se incluyen porque representan elementos conceptuales concretos que permiten comprender el dominio en cuestión. También se encuentran nombres propios (toponimia, antroponimia), que no serían incorporados en un vocabulario terminológico, pero que dentro de una ontología o un diccionario que integre una herramienta de representación de conocimiento no se pueden obviar porque sin ellos no acabaría de ser completamente representado el dominio. Así entonces, y de acuerdo con la Teoría Comunicativa de la Terminología, TCT (Cabré, 1999) estas unidades léxicas forman parte del recurso que puede ser visto como un sector especializado, entre otras cuestiones porque existen profesionales expertos en el campo.

Es importante tener en cuenta estos elementos porque al hablar de un dominio como el conflicto armado aparecen varias de estas cuestiones. Por un lado, es un campo que está alimentado conceptual y terminológicamente con denominaciones y clases particulares de otros dominios como por ejemplo el derecho, la antropología, las ciencias políticas, o campos de estudio como la memoria que tiene también una confluencia multidisciplinar. También se entiende como un campo en donde no se encuentran taxonomías o clasificaciones tan claramente definidas y en donde se presentan fronteras difusas y terminologías no consensuadas, a diferencia de otros ámbitos de conocimiento que cuentan con ontologías o tesauros de amplia difusión, además de clases que corresponden a conceptos más universales y que estarían representados en ontologías más fundacionales.

Para el reconocimiento de las clases en el dominio del conflicto armado se recurre a distintas terminologías así como al saber propio de estudiosos e investigadores en este campo, quienes validan la base conceptual y las terminologías para el proceso de reconocimiento de entidades y la construcción del grafo. Aquí se plantean entonces cuestiones sobre las características o atributos de una clase, cómo se reconocería esta


------------------------- PAGINA 88 --------------------------

dentro de un texto y qué es necesario describir terminológicamente para que una clase sea reconocida como tal.

En este dominio particular se encuentran, además de estas entidades genéricas y transversales a muchos dominios, elementos que denominan conceptos, procesos o fenómenos incluso, así que es necesario definir qué atributos y qué valores pueden ser de alguna manera previsibles de modo que puedan posteriormente representarse y reconocerse de manera automática usando técnicas computacionales.

# **5.3. Entidades y clases del conflicto armado colombiano**

Como se vio antes, una ontología está compuesta por clases y entidades. Si bien desde algunos sectores de la terminología no se consideraría el conflicto armado como un campo de especialidad propiamente dicho a la altura de campos más claramente definidos socialmente, como la medicina, la química o la ingeniería por ejemplo, desde la visión de la TCT, la terminología aparece en cualquier texto especializado por su temática y por su propósito comunicativo, lo que permite ampliar la noción de ámbito de especialización.

Así entonces, en este apartado se describen concretamente las clases y entidades propias del dominio en cuestión. Estas unidades que se encuentran aquí se consideran terminológicas en el momento en que algunas son objeto también del ámbito jurídico o de la historia, o como un objeto de aplicación para ayudar a personas víctimas en distintas situaciones, por ejemplo. Esto justifica que lo que podría entenderse como léxico común, se puede integrar bajo la mirada de la terminología y por tanto este sentido de dominio de especialidad permite establecer elementos para plantear clasificaciones.

Aquí se definen las clases y entidades que pueden ser útiles para representar información sobre un conflicto armado, que obviamente tendrá instancias concretas porque describe un conflicto en concreto, el colombiano, pero que podría ser extrapolable a la descripción y clasificación de otros conflictos, pues en cualquier otro


------------------------- PAGINA 89 --------------------------

tendría elementos como desplazados, víctimas, intervención del estado, medidas de reparación, atención, etcétera.

En este trabajo se ha definido un dominio que, como se dijo antes, tiene fronteras difusas, pues los conceptos que son definidos en este campo son retomados de otras áreas de conocimiento colindantes, además que dadas las características propias de una dinámica de conflicto social y político, definir a veces atributos de manera permanente es complejo por la mutabilidad misma que puedan tener los fenómenos o elementos de la realidad.

Para entender el conflicto armado como un dominio de conocimiento con entidades, atributos y relaciones específicas, se definen en primer lugar las clases que han de formar la ontología a partir de las que se extienda el grafo de conocimiento. A continuación se describen las clases o categorías definidas en donde se asigna a cada una la etiqueta o _label_ usada para la anotación, el código alfabético para distinguir, una descripción de la clase y muestras del uso de esas entidades recopiladas en el corpus.

Dentro de este sistema de clases se pueden integrar posteriormente las entidades propiamente dichas de las cuales se podrían distinguir dos tipos: instancias y términos. Las instancias corresponden principalmente a nombres propios y comunes y en las que se encuentran elementos de las clases: **PER** (personas), **ORG** (organizaciones), **GEO** (localización geográfica) **, ARM** (actor armado), **DATE** (fecha), y **LEY** (legislación). El segundo tipo de entidades involucra tanto nombres abstractos y concretos, cuyo significado se activa en el contexto de especialidad y se encuentran en las clases: **AFE** (afectación), **EVE** (evento), **VIO** (hecho de violencia), **LR** (lucha y resistencia), **MEM** (memoria), **ATE** (atención), **CON** (conceptos), **PAZ** (paz) y **DER** (derecho). En el <u>gráfico 1 se muestra un diagrama de relaciones entre las clases.</u>

En la <u>tabla 5</u> se presentan algunos ejemplos de clases con las entidades que se identifican en los ejemplos tomados del corpus. Una descripción más amplia de los tipos de entidades así como de las características lingüísticas que se presentan en cada uno de los tipos, se explican en el <u>capítulo 10</u> en donde se describen también las decisiones metodológicas que fue necesario tomar para el desarrollo de la ontología.


------------------------- PAGINA 90 --------------------------

En este trabajo se define que una entidad nombrada es una palabra o sintagma que se distingue dentro de un texto y que sirve para denominar elementos de la realidad, en este caso aquellos relacionados con el conflicto armado. Hay un tipo de entidades que son de relativa fácil identificación como los nombres de organizaciones e instituciones, nombres o roles de personas, o de lugares y que justamente corresponden con algunas de las clases. Pero también se dan otros términos que se refieren más a asuntos conceptuales o que dan cuenta de fenómenos sociales o políticos sobre los que eventualmente pudiera no haber suficiente consenso desde lo denominativo.


------------------------- PAGINA 91 --------------------------

## **Gráfico 1**

_Diagrama de clases_


------------------------- PAGINA 92 --------------------------

## **Tabla 5**

_Clases, etiqueta, descripción y ejemplos_

|**Código **|**Descripción**<br>|**Ejemplos**|
|---|---|---|
|**PER**|Se incluyen aquí tanto nombres<br>propios y alias, como palabras<br>para referir características o roles<br>de una persona que luego serán<br>consideradas como atributos.<br><br>|`-Este`<br>`panorama`<br>`de`<br>`represión`<br>`cambió`<br>`durante`<br>`la`<br>`presidencia`<br>`de`<br>`Belisario`<br>`Betancur Cuartas quien con la amnistía política promulgada a través de la`<br>`Ley`<br>`35`<br>`de`<br>`1982`<br>`y`<br>`la`<br>`derogación`<br>`del`<br>`Estatuto`<br>`de`<br>`Seguridad`<br>`despertó`<br>`un`<br>`optimismo`<br>`de`<br>`cambio,`<br>`con`<br>`el`<br>`acuerdo`<br>`de`<br>`paz`<br>`con`<br>`la`<br>`FARC, y de allí el`<br>`nacimiento del partido político Unión Patriótica.`<br>`-En`<br>`1986`<br>`y`<br>`1987,`<br>`los`<br>`campesinos`<br>`cordobeses`<br>`se`<br>`unieron`<br>`a`<br>`las`<br>`Jornadas`<br>`Nacionales por la Reforma Agraria y en 1988 protagonizaron el Paro Agrario`<br>`Nacional`<br>`por`<br>`el`<br>`incumplimiento`<br>`de`<br>`acuerdos`<br>`previos`<br>`con`<br>`el`<br>`Gobierno`<br>`Nacional.`|
|**ORG**|Nombres completos o acrónimos<br>de instituciones sean de orden<br>estatal o social y de alcance<br>local, nacional o internacional.<br>Se incluyen aquí también las<br>asociaciones<br>populares<br>y<br>comunitarias de carácter social o<br>de<br>defensa<br>de<br>los<br>derechos<br>humanos.<br><br>|`-Pero la mayoría no tenía ninguna idea sobre el taller, ni tampoco sobre la`<br>`Corporación`<br>`REINICIAR`<br>`o`<br>`sobre`<br>`la`<br>`Comisión`<br>`Interamericana`<br>`de`<br>`Derechos`<br>`Humanos`<br>`(CIDH);`<br>`y`<br>`la`<br>`Unión`<br>`Patriótica`<br>`solamente`<br>`era`<br>`un`<br>`nombre`<br>`lejano,`<br>`quizá refundido en alguno de los laberintos de la memoria.`<br>`-Garantizaremos`<br>`a`<br>`las`<br>`mujeres`<br>`víctimas`<br>`el`<br>`acceso`<br>`al`<br>`sistema`<br>`de`<br>`administración`<br>`de`<br>`la`<br>`justicia;`<br>`Vamos`<br>`a`<br>`promover`<br>`el`<br>`fortalecimiento`<br>`del`<br>`Consejo Municipal de Paz, Reconciliación y Convivencia (CONPAZ), como un`<br>`escenario`<br>`de`<br>`confluencia`<br>`e`<br>`incidencia`<br>`ciudadana`<br>`en`<br>`la`<br>`construcción`<br>`de`<br>`soluciones y procesos de reconciliación.`|
|**LOC**|Nombre para referir un lugar. Se<br>incluye la denominación de un<br>sitio geográfico como aquellas<br>denominaciones<br>que<br>están<br>referidas a lugares específicos.<br><br>|`-Por su parte las Farc, a través de sus frentes 5, 18 y 58 hace presencia`<br>`en la parte alta del Nudo de Paramillo conocida como Alto San Jorge y en`<br>`algunas zonas del Alto Sinú donde proyecta su control territorial.`<br>`-Han`<br>`emprendido`<br>`procesos`<br>`de`<br>`memoria`<br>`de`<br>`gran`<br>`envergadura`<br>`como`<br>`lo`<br>`son`<br>`el`<br>`parque de la vida y el salón del nunca más, como propuestas no oficiales`<br>`de memoria.`|


------------------------- PAGINA 93 --------------------------

|**Código **|**Descripción**|**Ejemplos**|
|---|---|---|
|**ARM**|Denominaciones para referirse a<br>grupos<br>cuyo<br>accionar<br>está<br>involucrado en hechos violentos.|`-En el periodo 2000 a 2004 la guerrilla de las FARC, que tenía presencia en`<br>`el territorio, emprende una escalada de sus acciones armadas y junto con`<br>`la`<br>`incursión`<br>`de`<br>`los`<br>`paramilitares`<br>`del`<br>`Bloque`<br>`Calima`<br>`en el año 2000 se`<br>`disparan`<br>`casi`<br>`todos`<br>`los`<br>`indicadores`<br>`de`<br>`violencia`<br>`en`<br>`el`<br>`municipio`<br>`(masacres, homicidios, asesinatos selectivos, secuestros y desplazamientos`<br>`forzados.`<br>`-Al parecer el Frente 30 de las FARC, el cual fue relegado en la década`<br>`anterior a la zona rural durante la disputa con los paramilitares, y Los`<br>`Rastrojos`<br>`-uno`<br>`de`<br>`los`<br>`grupos`<br>`armados`<br>`ilegales`<br>`que`<br>`ha`<br>`tenido`<br>`fuertes`<br>`tentáculos en el municipio- han estado vinculados al negocio.`|
|**AFE**|Consecuencias<br>que<br>afectan<br>a<br>personas y comunidades a partir<br>de hechos de violencia.|`-La situación del exilio es una cosa supremamente abstracta que te carcome`<br>`el alma [llanto] y yo creo que mis hijos lo sufrieron mucho porque ellos`<br>`me veían triste o veían triste al papá.`<br>`-A`<br>`pesar`<br>`del`<br>`miedo`<br>`y`<br>`la`<br>`desolación`<br>`enfrentamos`<br>`las`<br>`amenazas,`<br>`el`<br>`desplazamiento forzado, el hambre, el frío, la incertidumbre.`|
|**DATE**|Periodos<br>de<br>tiempo o fechas<br>precisas<br>que<br>amplían<br>la<br>descripción de hechos y eventos.|`-Es precisamente en dicho comunicado fechado el 17 de octubre de 2015 en La`<br>`Habana,`<br>`donde`<br>`se`<br>`anuncia`<br>`la`<br>`creación`<br>`de`<br>`una`<br>`Unidad`<br>`especial`<br>`para`<br>`la`<br>`búsqueda de las personas dadas por desaparecidas.`<br>`-Así,`<br>`en`<br>`2007`<br>`se`<br>`ejecutó`<br>`una`<br>`estrategia`<br>`de`<br>`impulso`<br>`a`<br>`procesos`<br>`cuyas`<br>`víctimas`<br>`son`<br>`indígenas`<br>`kankuamos,`<br>`y`<br>`en`<br>`el`<br>`año`<br>`2008`<br>`se`<br>`impulsaron`<br>`117`<br>`procesos cuyas víctimas son miembros de las comunidades indígenas Wiwa y`<br>`Embera Chami.`|
|**EVE**|Nombre de hecho o evento, sea<br>este violento, de movilización o<br>resistencia<br>o<br>de<br>proceso<br>de<br>negociación.|`-En`<br>`1986`<br>`y`<br>`1987,`<br>`los`<br>`campesinos`<br>`cordobeses`<br>`se`<br>`unieron`<br>`a`<br>`las`<br>`Jornadas`<br>`Nacionales por la Reforma Agraria y en 1988 protagonizaron el Paro Agrario`<br>`Nacional`<br>`por`<br>`el`<br>`incumplimiento`<br>`de`<br>`acuerdos`<br>`previos`<br>`con`<br>`el`<br>`Gobierno`<br>`Nacional.`<br>`-El primer proyecto narrativo que realizó el equipo de 4 Ríos fue sobre la`<br>`masacre`<br>`en`<br>`la`<br>`región`<br>`del`<br>`río`<br>`Naya,`<br>`que`<br>`perpetraron`<br>`paramilitares`<br>`del`<br>`Bloque`<br>`Calima`<br>`de`<br>`las`<br>`AUC,`<br>`entre`<br>`10`<br>`y`<br>`el`<br>`13`<br>`de agosto de 2001, cuando`<br>`asesinaron a 46 personas, la mayoría indígenas.`|


------------------------- PAGINA 94 --------------------------

|**Código **|**Descripción**|**Ejemplos**|
|---|---|---|
|**LEY**|Nombre de legislación.|`-Como`<br>`se`<br>`puede`<br>`observar,`<br>`el`<br>`Programa`<br>`de`<br>`Gobierno`<br>`del`<br>`alcalde`<br>`electo`<br>`de`<br>`Medellín`<br>`para`<br>`el`<br>`próximo`<br>`cuatrienio`<br>`tiene`<br>`propuestas`<br>`relacionadas`<br>`directamente con la implementación del Acuerdo de Paz y la ley 1448 de`<br>`2011, lo que aporta a la reconstrucción del tejido social que requiere de`<br>`la`<br>`incidencia`<br>`sociocultural`<br>`y`<br>`política`<br>`de`<br>`las`<br>`víctimas`<br>`del`<br>`conflicto`<br>`armado, al igual que la voluntad política de los agentes gubernamentales`<br>`para lograr un proceso de reparación efectiva.`<br>`-El`<br>`30`<br>`de`<br>`julio`<br>`de`<br>`1998,`<br>`después`<br>`de`<br>`revisar`<br>`los`<br>`tres`<br>`fallos,`<br>`la`<br>`Corte`<br>`Constitucional ordenó suspender las operaciones y el 10 de noviembre de`<br>`1998,`<br>`emitió`<br>`la`<br>`Sentencia`<br>`T-652,`<br>`mediante`<br>`la cual resuelve tutelar los`<br>`derechos`<br>`fundamentales`<br>`a`<br>`la`<br>`supervivencia,`<br>`a`<br>`la`<br>`integridad`<br>`étnica,`<br>`cultural, social y económica, a la participación y al debido proceso del`<br>`pueblo embera katío del Alto Sinú.`|
|**VIO**|Nombre para referir hechos de<br>violencia de acuerdo con<br>denominaciones ampliamente<br>tipificadas en el DIH.|`-En diciembre de 2012, “Jorge 40” fue condenado a otros 25 años de prisión`<br>`por`<br>`la`<br>`desaparición`<br>`y`<br>`posterior`<br>`homicidio,`<br>`en`<br>`marzo`<br>`de`<br>`2000,`<br>`otros`<br>`parecidos`<br>`se`<br>`deben`<br>`en`<br>`buena`<br>`parte`<br>`a`<br>`que`<br>`las`<br>`víctimas`<br>`contaron`<br>`con`<br>`el`<br>`acompañamiento`<br>`de`<br>`siete`<br>`servidores`<br>`del`<br>`Cuerpo Técnico de Investigación,`<br>`CTI, de la FGN.`<br>`-Los actores armados se valen de “enamorar” a algunas niñas como una de las`<br>`formas para reclutar ilícitamente a esta población, y a las que consideran`<br>`“más bonitas” las exponen a realizar otro tipo de delitos, como hurtos o`<br>`secuestros.`|
|**LR**|Se refiere a acciones o iniciativas<br>como forma de respuesta ante las<br>situaciones enfrentadas con<br>ocasión del conflicto. Están<br>representadas en acciones como<br>marchas, plantones o<br>manifestaciones.|`-Él se convirtió en la persona que encabezó todas las movilizaciones de las`<br>`comunidades indígenas del Alto para defender los derechos de su pueblo al`<br>`territorio.`<br>`-La estrategia de resistencia comunitaria ha sido hablar con sus comités`<br>`veredales,`<br>`activar`<br>`las`<br>`juntas`<br>`de`<br>`acción`<br>`comunal y la guardia campesina`<br>`como mecanismos, primero de protección y segundo para el respaldo a los`<br>`líderes y lideresas, frente al trabajo que se vienen desarrollando en el`<br>`territorio, que es muy importante, así como la protección de la vida.`|


------------------------- PAGINA 95 --------------------------

|**Código **|**Descripción**|**Ejemplos**|
|---|---|---|
|**MEM**|Nombre de iniciativas, lugares y<br>acciones de memoria por parte<br>de colectivos o personas.|`-Busca crear desde el diálogo una pedagogía de la memoria.`<br>`-Se`<br>`requiere`<br>`la`<br>`cooperación`<br>`de`<br>`la`<br>`academia`<br>`para`<br>`documentar`<br>`en`<br>`memorias`<br>`escritas no solo el conflicto sino también los planes y las propuestas que`<br>`vienen presentando organizaciones de la región.`|
|**ATE**|Acciones, estrategias o<br>programas de atención a víctimas<br>de conflicto armado.|`-Fortalecimiento del Centro de Atención a las Víctimas con acompañamiento`<br>`jurídico y psicológico.`<br>`-La realización de audiencias virtuales y la ruta de atención psicojurídica`<br>`de la Defensoría del Pueblo.`|
|**CON**|Términos que refieren conceptos<br>de otras disciplinas y que se<br>encuentran con frecuencia en los<br>textos.|`-El`<br>`proceso`<br>`de`<br>`desmovilización`<br>`de`<br>`las`<br>`AUC`<br>`puso`<br>`de`<br>`manifiesto`<br>`el`<br>`papel`<br>`prominente del narcotráfico en el fenómeno paramilitar.`<br>`-En`<br>`las`<br>`partes`<br>`en`<br>`las`<br>`negociaciones`<br>`hicieron`<br>`públicos`<br>`los`<br>`acuerdos`<br>`preliminares`<br>`alcanzados`<br>`hasta`<br>`la`<br>`fecha`<br>`sobre`<br>`reforma`<br>`participación`<br>`política y drogas.`|
|**PAZ**|Términos<br>relacionados<br>con<br>procesos<br>de<br>paz,<br>acuerdos,<br>negociación.|`-El Alto Comisionado reitera su pleno apoyo las negociaciones de paz en La`<br>`Habana entre el Gobierno y las FARC.`<br>`-El reconocimiento y las garantías de no repetición y la participación en`<br>`acciones`<br>`transformadoras`<br>`podrían`<br>`vincularse`<br>`con`<br>`medidas`<br>`de`<br>`reducción`<br>`o`<br>`cumplimiento de penas para todas las partes.`|
|**DER**|Derechos y acceso a los mismos.|`-El Estado brinda a los individuos con las reparaciones a las que tienen`<br>`derecho las víctimas de violaciones de derechos humanos en razón del daño`<br>`específico generado por la violación.`<br>`-Tomar`<br>`en`<br>`cuenta`<br>`el`<br>`impacto`<br>`a`<br>`los`<br>`derechos,`<br>`económicos,`<br>`sociales,`<br>`culturales`<br>`y`<br>`ambientales`<br>`derivados`<br>`de`<br>`actividades`<br>`de`<br>`complicidad`<br>`empresarial.`|


------------------------- PAGINA 96 --------------------------

Sobre los términos que fueron identificados y clasificados según las categorías definidas, es necesario indicar que la variación se presenta en razón de la naturaleza particular de cada recurso terminológico, pues como se mencionó más atrás, algunas de estas herramientas son usadas para describir y recuperar recursos documentales, pero otras son el marco conceptual y metodológico para la recopilación de datos e información sobre fenómenos sociales y hechos de violencia. Eso implica una variación importante en términos de lo formal o lo sintagmático.

Las entidades pueden ser concretas o abstractas. Las concretas expresan cosas del mundo físico real como personas u objetos, por ejemplo _Organizaciones internacionales_ o _Departamento_ para referir un lugar. Las entidades abstractas pueden referir acciones o eventos, como _Desaparición forzada_ o _Acuerdo de paz._ Tanto las entidades concretas como las abstractas pueden a su vez ser individuales para describir elementos particulares como _Corte Penal Internacional; Cauca_ o _Acuerdo Final para la Terminación del Conflicto y la Construcción de una Paz Estable y Duradera_ .

El trabajo de clasificación de esta terminología ha implicado reconocer cuáles son los tipos de variación conceptual que se presentan, pues lo que se pretende alcanzar es una forma estándar (lo más precisa posible) del concepto y las variaciones que esta tenga para poder efectuar una tarea de automatización adecuada en el proceso de extracción de entidades para el grafo.

Antes de describir las particularidades de cada una de las clases, se muestran algunas de las variaciones que en términos generales se presentan en los textos. Hay un uso de formas extendidas y formas cortas de un término, como cuando se nombran instituciones o lugares tanto en su forma extendida como su forma abreviada, como _Centro Nacional de Memoria Histórica_ y _CNMH;_ o _Fuerzas Armadas Revolucionarias de Colombia_ y _FARC._

Se presenta también el uso de sinónimos, pues se encuentran formas alternativas para designar un concepto que puede corresponder a distintas cuestiones que van desde la necesidad de hacer más variable y rico el discurso o la intención y propósito


------------------------- PAGINA 97 --------------------------

comunicativo, según el lugar de enunciación. Aquí se encuentran términos como _Ley 975 de 2005_ y _Ley de Justicia y Paz._

También se presenta el uso de anáforas para mencionar cosas como actores o hechos o afectaciones, por ejemplo _los muchachos_ para referirse a un actor armado concreto que fue mencionado antes en el texto; o _cuando eso pasó,_ para referir un hecho de violencia concreto que está ya claramente identificado y descrito como un concepto.

El ejercicio de identificación y clasificación de entidades se ha realizado desde dos puntos: uno, es la clasificación de las entidades e instancias que fueron extraídas desde las terminologías y bases conceptuales. Esta clasificación se hace manualmente y la asociación se da a partir del análisis conceptual de los términos. Esto permite un enriquecimiento de los datos y son la estructura de conceptos que servirán al modelo para anotar los textos cuando se encuentren con las entidades que correspondan. El otro punto es la identificación de esas entidades en el corpus como tal para reconocer cómo se encuentran desde las estructuras sintácticas a las que corresponden y para establecer también cuáles son los fenómenos lingüísticos que aparecen en estas entidades y que se tendrían que tener en consideración en un modelo de anotación y clasificación automática.

A continuación se describen las clases definidas inicialmente para el proceso de etiquetado que sirvieron para identificar y clasificar información sobre conflicto.

## **Clase PER (Persona)**

Se refiere a individuos que tienen diferentes roles bien sea en los hechos de violencia propiamente dichos o en las acciones de atención, defensa de derechos, luchas y de memoria que se llevan a cabo. Poseen atributos que describen tanto sus roles en la sociedad como en el conflicto concretamente.

En esta categoría se encuentran palabras como sustantivos, sintagmas nominales; y se encuentran tanto nombres propios como comunes, así como palabras que se refieren a roles o a situaciones o condiciones específicas de las personas.


------------------------- PAGINA 98 --------------------------

En cuanto a los roles se encuentran palabras de uso general como _acusado_ , _agente_ , _párroco_ o _niña_ , que aunque son palabras de uso de la lengua general, en el dominio concreto pueden ser importantes como parte de la clase de personas que están involucradas o afectadas en un hecho de violencia o en un evento de otra índole, o que en razón de su actividad profesional o por filiación a un grupo o entidad especial, tienen una relevancia.

En cuanto a los nombres propios, se encuentran distintas formas así como alias. Sobre esto es necesario considerar el tema de la protección de los datos, pues si bien algunos nombres son personalidades políticas, actores armados o representantes de alguna organización de atención; en otros casos, estos nombres pueden estar relacionados con personas cuya identidad deba ser protegida. En el corpus que se construye para este trabajo, toda la información es pública y disponible en internet en los sitios de las organizaciones que la producen o compilan, pero a la hora de implementar un sistema de reconocimiento, esta es una cuestión que debe considerarse.

También aparece en esta categoría la cuestión de los singulares y plurales, el género o el grupo etario referido a personas. A veces en el corpus se encuentran palabras que se refieren en general a _líderes_ , _mujeres_ , _campesinos_ , _indígenas_ , _jóvenes_ ; o _guerrillero/guerrillera_ que en el contexto de la oración que se plantea es necesario reconocer.

Es importante también anotar que esta clase tiene relaciones conceptuales directas con algunas de las categorías. Por ejemplo, cuando hay referencia a elementos de la clase **PER** (personas) que son víctimas, las palabras _desaparecido_ o _persona desaparecida_ estarían relacionadas directamente con palabras de la clase **VIO** (hecho de violencia) como _desaparición forzada_ .

## **Clase ORG (Organización)**

Las organizaciones pueden clasificarse según sean académicas, religiosas, financieras, entre otras, y si son del orden regional, nacional e internacional. Sobre estas aparece


------------------------- PAGINA 99 --------------------------

información implícita relacionada con el propósito, alcance, población objetivo y sector de la sociedad desde el que actúa.

Aquí se encuentran nombres propios y comunes, que requieren además un relacionamiento de sinónimos según sus siglas o acrónimos o la manera como son denominadas estas instituciones. En muchos casos tienen también una relación directa con las clases con **EVE** (eventos), **ATE** (acciones de atención) y **MEM** (memoria).

## **Clase GEO (Localización geográfica)**

En esta clase se encuentran nombres comunes y propios de sitios geográficos. También se encuentran nombres que se refieren a localizaciones que tienen algún interés sociopolítico o en el que se dan eventos particulares.

Hay gran cantidad de sinonimia en cadenas de caracteres que según el contexto pueden significar algo particular. Por ejemplo, cuando se encuentran nombres de lugares estos pueden corresponder a distintos puntos geográficos, ser la misma palabra para referir un municipio o una vereda; y a su vez ser también una palabra que designa el nombre de una persona. Aquí es necesario definir características toponímicas de estas entidades y buscar el modo de incorporar esas entidades que ya han sido descritas en otras ontologías o taxonomías del ámbito más amplio. También se encuentran formas abreviadas o palabras sinónimas por las cuales un lugar es reconocido.

Sobre la desagregación taxonómica de los lugares, se encuentra también que muchas veces se hace uso de formas gráficas como guiones, comas, paréntesis o abreviaturas para distinguir un lugar del otro.

También aparecen en algunos textos denominaciones más genéricas para describir un fenómeno o ciertos eventos en una zona más amplia que involucra o recoge otros lugares más específicos. Por ejemplo, nombres que no corresponden a nombres propios de lugares específicos sino a nombres comunes de zonas o regiones o subregiones pero que son importantes destacar, por ejemplo: _zona bananera_ o _región Caribe_ .

Hay también varios nombres propios de lugares concretos ejemplo: _Palacio de Justicia_ , _Salón del Nunca Más_ , o el nombre exacto de un resguardo como _Resguardo Indígena_ 98


------------------------- PAGINA 100 --------------------------

_Awá El Gran Sábalo_ . Estas entidades están claramente relacionadas con las clases **VIO** (hecho de violencia) o con una acción de memoria **(MEM)** , atención **(ATE)** o lucha **(LR)** .

También aparecen nombres como _Casas de pique_ o _Casas de acogida_ relacionadas con la clase **VIO** (hechos de violencia) en la primera o **ATE** (atención a personas) en el segundo caso. O nombres comunes de lugares como _Zonas de distensión_ o _Zonas de concentración_ , que están directamente relacionados con las clases **EVE** (eventos de negociación), **ATE** (atención) o **LR** (resistencia).

Algunos nombres pueden corresponder a la denominación de un lugar o de un accidente geográfico, como un río o un cerro, y aquí es importante considerar y definir los patrones que puedan permitir a la máquina distinguir cuando se hace mención a un lugar, a partir por ejemplo de la identificación de mayúsculas cuando proceda a palabras como río, quebrada, vereda.

También hay entidades como _Corredores de movilidad_ que no refieren un lugar concreto pero sí que está relacionado con esa idea de ocupación del espacio para, por ejemplo, describir acciones de atención y asistencia humanitaria a personas; o incluso de luchas y resistencias según las circunstancias y móviles en que esos corredores ocurren o quien los gestiona.

## **Clase ARM (Grupo armado)**

Esta clase se refiere a los responsables reconocidos como actores armados en donde aparecen atributos como nombre, pertenencia a un grupo o un rol determinado y móviles de su accionar. Aquí se encuentran tanto nombres propios de grupos o facciones como _Autodefensas Unidas de Colombia_ . También aparecen nombres comunes como _Grupo armado ilegal_ , que según el contexto en el que estas palabras aparecen sirven para reconocer un **VIO** (hecho de violencia), una **AFE** (afectación) o un **EVE** (evento particular). También aparece con frecuencia el uso de siglas o denominaciones alternativas de los grupos.


------------------------- PAGINA 101 --------------------------

## **Clase AFE (Afectación)**

Las afectaciones se refieren a las consecuencias o efectos que tienen los hechos violentos sobre las personas y que alteran, perjudican, cambian de manera negativa y abrupta el curso de vida de los individuos, las familias y las comunidades. Estas afectaciones son nombradas a partir de verbos, sustantivos y adjetivos que dan cuenta del padecimiento de las personas y las comunidades. Estos daños se reconocen también en distintas dimensiones según lo individual, familiar, comunitario y social y en los ámbitos psicológicos, físicos, económicos, políticos y socioculturales. Los daños son nombrados a partir de verbos, sustantivos y adjetivos que dan cuenta del padecimiento de las personas y las comunidades (Tangarife _et. al._ , 2022).

## **Clase DATE (Fechas y tiempo)**

Esta es una clase genérica que refiere el uso de expresiones de tiempo. No tiene un listado de términos propiamente dicho de elementos que sean sacados de las terminologías y bases conceptuales estudiadas, pero evidentemente el reconocimiento de estos elementos dentro de un texto es de vital importancia en el análisis de información sobre conflicto armado. Lo que se plantea aquí es la incorporación de otras librerías en donde esto está ya desarrollado y cómo viene a relacionarse con elementos de otras clases, especialmente cuando se habla por ejemplo de **EVE** (eventos), **VIO (** hechos de violencia) o **LEY** (legislación).

## **Clase EVE (Evento)**

En esta clase se encuentran denominaciones propias para referir cosas como _Paro nacional universitario en Colombia de 2018, Toma del Palacio de Justicia_ o _Masacre del Aro._ Estas entidades tienen tanto una denominación como una serie de atributos que es necesario describir en una ontología relacionado con datos como fecha, lugar, actores, descripción de los hechos. Están relacionados con otras clases como **LR** (lucha y resistencia) en el caso del primero; o **VIO** (hecho de violencia) y **AFE** (afectación) en los otros dos.


------------------------- PAGINA 102 --------------------------

## **Clase LEY (Legislación)**

En esta clase aparecen entidades como _Ley de Justicia y Paz_ o _Ley 1448 de 2011,_ que son frecuentemente enunciadas en los textos, tanto jurídicos como de otros ámbitos dada la importancia y repercusión que tienen para comprender, describir, ampliar o explicar cuestiones específicas relacionadas con los hechos, con las víctimas o los mecanismos de atención y protección de los derechos. Tienen también unos atributos concretos como fecha, entidad que promulga la ley y también se encuentran sinónimos de la denominación de la ley. Aparecen también términos que refieren legislación en distintos niveles como por ejemplo Sentencias o Decretos.

## **Clase VIO (Hecho de violencia)**

Esta clase se refiere a lo que desde el Derecho Internacional Humanitario se define como modalidad de victimización y define el tipo de vulneración de derechos a la que son sometidas las personas o comunidades por cuenta del accionar de terceros. Estas modalidades son clasificadas según estándares internacionales de derechos humanos y son retomadas por diferentes instituciones en el país para clasificar, comprender y abordar los hechos propios del conflicto armado. Son enunciadas como sustantivos o frases sustantivas adjetivadas cuando sirven para describir o especificar elementos del fenómeno. Sin embargo, en la descripción narrada del hecho aparecen también verbos y otra información adicional relacionada con los actores, los lugares, los móviles del hecho, entre otras. En esta clase se reconocen elementos como qué, cuándo, dónde, quiénes, lo que a su vez permite definir las clases **GEO** (localización), **PER** (persona) y **AFE** (afectación).

Entre las cosas que se encuentran en esta clase, se mencionan las formas distintas de denominar un mismo tipo de violencia y especificaciones que correspondan a según quién las diga y cómo se clasifiquen.

También aparecen palabras simples y compuestas para referir los hechos de violencia, según sea necesario ampliar o especificar ciertos elementos concretos por ejemplo


------------------------- PAGINA 103 --------------------------

cuando se indica un tipo de agresión según a quién se ejecuta, quién la comete o con qué objetos o atenuantes específicos ocurre.

También se distinguen hechos de violencia a las personas especialmente, pero también a sitios o propiedades materiales o elementos más abstractos como el patrimonio natural o cultural o el territorio.

## **Clase LR (Lucha y resistencia)**

Se refiere a palabras que describen la acción propiamente dicha y están relacionadas también con las clases **EVE** (evento), **ORG** (organización) y **PER (** persona). Se encuentran palabras comunes como _Huelgas, Movimientos sociales_ , que en algunos casos también están relacionados con nombres propios para referir una acción o lucha concreta.

## **Clase MEM (Memoria)**

Aquí se incluyen entidades relacionadas con acciones o eventos de memoria. Tienen también relación con las clases **EVE** (evento), **ORG** (organización) o **GEO** (localización) cuando se hace referencia a _Sitios de memoria_ , como altares, museos o archivos.

## **Clase ATE (Atención)**

Esta clase incorpora entidades relacionadas con los mecanismos y acciones que llevan a cabo entidades de las clases **PER** (persona) u **ORG** (organización) para individuos o grupos de personas que la requieren con posterioridad a un hecho de violencia.

## **Clase CON (Concepto)**

Esta clase es bastante amplia y en ella se agrupan entidades que están relacionadas con términos propiamente dichos que pertenecen a muchos otros campos de conocimiento como el Derecho, el Trabajo Social o la Ciencia Política, entre otros. Se encuentran sintagmas (habitualmente sustantivo y adjetivo), como por ejemplo _Reintegración social, Medidas de esclarecimiento_ o _Verdad restaurativa._


------------------------- PAGINA 104 --------------------------

## **Clase PAZ (Procesos y movimientos de paz)**

Se incluyen entidades relacionadas con los procesos de paz y con los acuerdos o negociaciones que se dan hacia ese propósito. Se incluyen términos que están en línea con el trabajo pedagógico para la construcción de paz. También se encuentran entidades relacionadas con procesos de verdad, reparación y restitución como condiciones fundamentales para que la paz pueda ser consolidada.

## **Clase 15 DER (Terminología jurídica y del Derecho)**

En esta clase se recogen nombres de entidades que tienen relación con la denominación misma de los derechos en términos como _Derecho a la vida_ o _Derecho a la educación,_ así como a otras denominaciones que conceptualmente están relacionadas con estos asuntos como _Igualdad ante la ley_ o _Acceso a servicios públicos_ .

Hasta aquí el recuento de las clases y entidades en donde se explicaron los términos encontrados en la base conceptual, definiendo qué tipos de términos son y cuáles son los conceptos asociados y los fenómenos que representan.


------------------------- PAGINA 105 --------------------------

# **Capítulo 6. Grafos de conocimiento**

<mark>Un grafo de conocimiento es una gran red de objetos de la realidad que tiene sus propias ontologías e instancias de conocimiento y que permite la representación y el razonamiento sobre objetos de la realidad representados en datos que pueden estar semiestructurados (Kejriwal</mark> _<mark>et al.</mark>_ <mark>, 2021). Una definición propuesta por Ji</mark> _<mark>et al.</mark>_ <mark>plantea que un grafo de conocimiento “es una representación estructurada de hechos compuestos de entidades, relaciones y descripciones semánticas” (2021, p. 1). También se entiende como un “grafo de datos que busca acumular y transmitir conocimientos sobre el mundo real, por medio de nodos que representan entidades y aristas que representan las relaciones entre ellas” (Hogan</mark> _<mark>et al.</mark>_ <mark>, 2021, p. 2).</mark>

<mark>El grafo de conocimiento parte de la teoría de grafos que, aplicada a las ciencias de la computación, resulta útil en tareas de sistemas expertos, modelos secuenciales, planeación, bases de datos, sistemas de recomendación,</mark> _<mark>e-commerce</mark>_ <mark>y web semántica. “Las bases de datos de grafos permiten encontrar conexiones entre puntos de los datos y son una potente vía para hacer descubrimiento de información. Los grafos y la teoría de grafos son herramientas para modelar y analizar datos” (Barrasa</mark> _<mark>et al.,</mark>_ <mark>2021, p. 6). Estos parten de una comprensión contextual para construir conjuntos interrelacionados que describen entidades del mundo real, eventos o cosas.</mark>

<mark>Los grafos son muy potentes para la representación, razonamiento e inferencia del conocimiento disponible en entornos web y la exploración en bases de datos. Tienen en cuenta los siguientes elementos:</mark>

**Nodos que representan entidades en un domini** **<mark>o</mark>** <mark>, que pueden ser objetos del mundo real o conceptos abstractos, los cuales poseen una o más</mark> **<mark>propiedades o atributos</mark>** <mark>relacionados con las características de los nodos, y</mark> **<mark>relaciones</mark>** <mark>que representan cómo las entidades están conectadas desde el punto de vista del significado (Barrasa</mark> _<mark>et al.</mark>_ <mark>, 2021). Los grafos de conocimiento permiten un razonamiento sobre los datos y pueden ser creados a partir de taxonomías y ontologías, por lo cual se hace necesario que estas herramientas den buena cuenta de los dominios de conocimiento, incorporando las entidades, propiedades y relaciones de los nodos que representan el dominio.</mark>


------------------------- PAGINA 106 --------------------------

<mark>El aprendizaje de representación de conocimiento a partir de grafos es un campo de investigación que ha propuesto métodos de adquisición de conocimiento y una gran variedad de aplicaciones y metodologías, así como recursos útiles de conjuntos de datos y bibliotecas de código abierto (Ji</mark> _<mark>et al.</mark>_ <mark>, 2021). Las tareas involucradas en los grafos de conocimiento incluyen la extracción de conceptos y de relaciones, la completación de conocimiento, la clasificación, el reconocimiento de entidades. Estas tareas son útiles en el trabajo con datos complejos y aportan un esquema de relaciones flexibles dada la gran abstracción que permite realizar inferencias.</mark>

<mark>La representación de conocimiento planteada desde los grafos puede darse a partir de redes semánticas, lógicas de descripción o grafos conceptuales que tratarán de resolver especialmente la semántica referida en este caso a los significados que puede adquirir una entidad. Los grafos de conocimiento recogen esquemas de vocabularios sobre distintos dominios y son utilizados en la integración de datos para toma de decisiones, máquinas de búsqueda y exploración de información e inteligencia artificial.</mark>

El desarrollo de un grafo de conocimiento debe considerar el espacio de representación y el modelo de las relaciones que se establecen. El aprendizaje de representación de conocimiento implica la adquisición de conocimiento para saber precisamente cuáles son las relaciones entre entidades y clases.

Los grafos podrían distinguirse entre los que representan conocimiento general de datos abiertos y que se encuentran en recursos como Wikipedia, DBpedia, Schema.org, cuya pretensión es recoger conocimiento del mundo e integran datos de múltiples temas; y los recursos de dominio que recogen información especializada en campos concretos.

El grafo de conocimiento se compone de otros sistemas de gestión de información de una organización, integrando la base conceptual y relacional de los elementos que hacen parte del modelo de base de datos.

Un grafo de conocimiento, a diferencia de otras estructuras como las ontologías, no necesitan de una estructura tan jerarquizada, por lo cual se da una gran versatilidad y resolvería el asunto de no contar con tantos datos anotados. Por esto se plantea esta


------------------------- PAGINA 107 --------------------------

como una posibilidad para estructurar conceptualmente este dominio concreto. “Una de las ventajas de modelar los datos como grafos –frente, por ejemplo, al modelo relacional– es la opción de renunciar o posponer la definición de un esquema” (Hogan _et al._ , 2021).

A continuación se hace un recorrido por el desarrollo histórico de los grafos, algunas definiciones y el estado de la discusión sobre algunos elementos.

# **6.1. Definiciones y evolución histórica**

Dentro del contexto de la web semántica, los grafos de conocimiento responden al volumen de los datos incorporando métodos de razonamiento automático que permiten mayor acceso a partir del sentido de los datos.

El grafo de conocimiento representa, entre otras cosas, un modelo de un dominio de conocimiento creado por expertos mediante algoritmos inteligentes de aprendizaje automático. Proporciona una estructura y una interfaz común para todos los datos importantes y permite la creación de relaciones multifacéticas entre bases de datos (Blumauer y Nagy, 2020, p. 38).

El propósito de construir grafos de conocimiento es mapear y procesar relaciones entre entidades que representan objetos del mundo real acercándose a la manera como funciona el cerebro humano y las conexiones de significado que surgen en el pensamiento. Los grafos de conocimiento se proponen como un paradigma más avanzado de representación de conocimiento, puesto que combinan todo el acumulado sobre taxonomías, redes semánticas, bases de datos de modelos en red, bases de conocimiento, ontologías, diccionarios semánticos y datos enlazados. Los grafos de conocimiento han emergido como una herramienta para representar y razonar sobre los datos que pueden ser semiestructurados o en escala web y sobre los cuales haya potencialmente conflictos o inconsistencias. “Un grafo de conocimiento es una forma práctica y legible por máquina de representar información sobre el mundo, incluyendo


------------------------- PAGINA 108 --------------------------

entidades, relaciones, atributos, hechos, creencias e incluso procedencia, incluyendo justificaciones e incertidumbre” (Kejriwal _et al.,_ 2021, p. 43).

Los grafos de conocimiento tienen como antecedente la teoría de grafos que se propone en 1736 por Leonhard Euler. En 1976, John F. Sowa propone el término grafos conceptuales como herramienta para describir los datos según la visión del usuario que permita acceder a los datos según la visión del sistema. En 1982, C. Hoede y F.N. Stokman, plantean por primera vez una teoría de los grafos de conocimiento. En 1999, con la aparición de RDF ( _Resource Description Framework_ ) como estándar para la representación de contenido en la web se sientan las bases de lo que más adelante será todo el desarrollo de la web semántica.

Posteriormente, para 2006 surge DBPedia con la intención de compilar conocimiento integrando distintos vocabularios y terminologías. Se da un florecimiento de las ontologías como base de conocimiento para acompañar el desarrollo de la web semántica y en el 2012 Google reintroduce el concepto de grafo de conocimiento entendiendo que los motores de búsqueda no se han de centrar tanto en una cadena de caracteres que significan algo, sino que lo que interesa es la cosa en sí, el objeto, el conocimiento. Retoma la idea de cómo conocemos y busca reducir la ambigüedad a la hora de presentar conocimientos. Para 2018 y 2019 los grafos de conocimiento se consolidan como tendencia para estructurar conceptualmente dominios y enriquecer la web y con la aparición de otras tecnologías como el aprendizaje de máquinas y los algoritmos de inteligencia artificial, se da un aporte significativo para atender algunas limitaciones y dificultades propias de la conformación de las ontologías.

Los grafos de conocimiento permiten recopilar toda la información y experiencia disponibles en un campo de conocimiento, identificando las categorías, conceptos y objetos que son indispensables y describiendo la manera en que estos elementos se interrelacionan. De acuerdo con Blumauer y Nagy (2020), los grafos de conocimiento están compuestos por el modelo conceptual y su representación semántica en un esquema u ontología, y por un modelo lingüístico, que permite etiquetar y describir los elementos individuales del modelo conceptual y de las instancias individuales. Este


------------------------- PAGINA 109 --------------------------

modelo lingüístico estará constituido por los vocabularios y terminologías propias del dominio en cuestión.

Estos mismos autores plantean tres enfoques para entender los grafos de conocimiento a desarrollarse dentro de una empresa y que tienen diferencias según los principios incorporados: el conocimiento, los datos y las entidades. El primer enfoque determinado desde el **conocimiento** , plantea que un grafo es un modelo de dominio que es curado por los expertos en la materia con el apoyo de modeladores de conocimiento, quienes utilizan métodos parcialmente automatizables para crear modelos de conocimiento específicos, expresivos y semánticamente ricos, pero sólo para un ámbito limitado de la empresa. El segundo enfoque, cuyo principio son los **datos** , propone un grafo de conocimiento a partir de fuentes de datos ya existentes que están representados por ontologías, taxonomías y reglas previamente definidas para automatizar la transformación e integración de los datos. Por último, el enfoque desde las **entidades** , que entiende el grafo de conocimiento como una red multicapa y multidimensional en donde se representan los objetos y hechos que tienen equivalencia en el mundo real, los cuales pueden a su vez ser representados en instancias, taxonomías y ontologías. En este último modelo se destaca que se pueden consolidar perspectivas del conocimiento y de los datos en diálogo con los usuarios de ese conocimiento.

El surgimiento de los grafos, al menos desde 2012 que fueron propuestos por Google, consideran el trabajo de grandes compañías en cuyo caso tener una adecuada gestión y relacionamiento de los datos está más cercana a la disposición y comprensión en función del mercado. Si bien hay algunas bases de datos que recopilan y disponen bases de conocimiento abierto y genérico en múltiples campos, también se reconoce un desarrollo especial en ciertos ámbitos.

En cuanto a las cualidades o criterios que cumplen los grafos de conocimiento se destaca que “describe principalmente entidades del mundo real y sus interrelaciones, organizadas en un grafo; define posibles clases y relaciones de entidades en un esquema; permite interrelacionar potencialmente entidades arbitrarias entre sí; cubre varios dominios temáticos” (Paulheim citado por Hogan _et al.,_ 2021). No se consideran


------------------------- PAGINA 110 --------------------------

por tanto las ontologías sin instancias o los grafos de sentidos de palabras, las bases de datos relacionales o aquellos grafos que solo recogen información específica, pues lo ideal sería esa recopilación del conocimiento del mundo en términos más generales.

Llama la atención el crecimiento exponencial de la producción de artículos sobre grafos de conocimiento en los últimos años, principalmente en las áreas de salud, ingeniería, negocios, redes sociales, leyes, educación, energía y entretenimiento, entre otros. En estos artículos se destacan especialmente asuntos relacionados especialmente con la extracción de entidades y relaciones y sistemas pregunta/respuesta; y en menor medida predicción de enlaces o construcción de ontologías. En estos artículos se abordan aspectos técnicos y metodológicos a partir de la descripción de herramientas, recursos y guías (Schneider _et al._ , 2022).

# **6.2. Componentes y tareas de un grafo de conocimiento**

Los grafos de conocimiento están compuestos por unas tecnologías que involucran la representación y razonamiento del conocimiento dispuesto en lenguajes, esquemas y vocabularios estándar; el almacenamiento del conocimiento en bases de datos y repositorios de grafos; la ingeniería del conocimiento que define las metodologías, editores y patrones de diseño; y el aprendizaje del conocimiento que permite la población de esquemas (Fensel _et al._ , 2020).

Un grafo de conocimiento contiene los datos estructurados en lenguajes como JSON ( _JavaScript Object Notation_ ), semiestructurados como HTML ( _HyperText Markup Language_ ), o integrados a conocimiento explicitado mediante lenguajes OWL y XML. El grado de conocimiento integra las redes semánticas, la lógica descriptiva y los grafos conceptuales, partiendo de los esquemas que recogen vocabularios en diversos dominios. Sin embargo, una dificultad está dada por un aspecto semántico: cuáles son los significados que puede adquirir una entidad y cuál es la naturaleza de las relaciones para facilitar la búsqueda e integración de los datos y la inteligencia artificial.

Un modelo de datos de grafo incluye los nodos, las relaciones y las propiedades en donde cada nodo y relación tiene una etiqueta y un conjunto de propiedades, las cuales


------------------------- PAGINA 111 --------------------------

son pares clave-valor para determinar la relación. Los nodos representan la entidad en un dominio dentro del grafo. La relación es la información semántica sobre los nodos, o sea que tiene un tipo y posee al menos una o más propiedades. La propiedad por su parte representa los valores de los datos para indicar qué tipo de dato es.

Un grafo de conocimiento está constituido básicamente por dos modelos: uno es el modelo conceptual que incluye el esquema y ontología en donde se determina la estructura conceptual sobre el dominio. El otro es el modelo lingüístico que incluye los vocabularios controlados y las taxonomías que se precisan para describir un aspecto. Los elementos que típicamente integran un grafo son: la ontología (modelo conceptual), la taxonomía (modelo lingüístico) y el _data graph_ que hace referencia a los datos instanciados y los metadatos, documentos y anotaciones (Blumauer y Nagy, 2020).

Dentro de una organización, un grafo de conocimiento se integra a otros sistemas de gestión de información, pues aporta la base conceptual y relacional de los elementos que componen el modelo de bases de datos. Una base de conocimiento puede entenderse como una tecnología que almacena información compleja, estructurada y no estructurada y que contiene el conocimiento del dominio y la máquina de inferencia. Está compuesta por el conocimiento terminológico que da cuenta de los conceptos en un dominio; el conocimiento declarado, que se refiere a individuos o instancias particulares; y el conocimiento de los roles de las interdependencias o relaciones entre nodos e individuos. Estos tres elementos constituyen junto con el sistema de inferencias, una base de conocimientos

La creación de un grafo de conocimiento involucra las siguientes fases: creación, alojamiento, curación y despliegue de conocimiento, en las que se deben tener en cuenta los principios de encontrabilidad, accesibilidad, interoperabilidad y usabilidad entre los datos. La “ **encontrabilidad** ” ( _findability_ en inglés) se refiere a la posibilidad de encontrar los datos y que estos tengan un identificador único. La **accesibilidad** se refiere a la posibilidad de que los datos sean comprensibles para las personas y las máquinas. La **interoperabilidad** es la posibilidad de hacer que los metadatos puedan ser accesibles y compartidos y la **usabilidad** garantiza que esos datos puedan ser


------------------------- PAGINA 112 --------------------------

reutilizables en otras colecciones. También se propone un ciclo de vida de los grafos de conocimiento en los que se destacan los actores en tres ciclos: el bucle de expertos, el bucle de automatización y el bucle de usuarios y que,

abarca desde el inventario de datos, la extracción y curación, el modelado (autoría), varios pasos de transformación, hasta la vinculación y el enriquecimiento (por ejemplo, de datos inferidos), y el análisis o la retroalimentación de los datos recién adquiridos en los sistemas de bases de datos existentes (Blumauer y Nagy, 2020, p. 137).

Un grafo de conocimiento debe cumplir con los servicios de extracción de términos, etiquetado basado en conceptos, extracción de entidades nombradas, clasificación de contenidos, extracción de relaciones y hechos, enlazamiento de entidades, extracción de sentidos y extracción basada en reglas. Para ello, el grafo cuenta con la base de conocimiento en RDF, el motor SPARQL ( _SPARQL Protocol and RDF Query Language_ ) y el razonador para la ejecución de las consultas. También debe incorporar aprendizaje automático integrado para realizar análisis predictivos y plantear cómo será la administración, la conexión con otros gestores y la escalabilidad.

# **6.3. Metodologías, herramientas y lenguajes**

En términos generales, la creación de un grafo de conocimiento incluye el diseño de un esquema a partir de terminologías y tesauros que recojan la conceptualización del dominio, el poblamiento del grafo a partir de fuentes estructuradas y semiestructuradas e incluir los textos, que idealmente deberán ser curados para garantizar una calidad de los datos, y la inclusión de los enlaces de relaciones, entidades, vocabularios y otros datos.

Hay cuatro grandes fases a considerar: la creación, el almacenamiento, la curación y el despliegue de conocimiento. A continuación, se describen cada una de ellas y las tareas involucradas en cada una de ellas.


------------------------- PAGINA 113 --------------------------

## **1. Creación o generación de conocimiento**

Esta fase se refiere al proceso de extracción de información de distintas fuentes para crear conocimiento útil y presentarlo de forma estructurada (Fensel _et al._ , 2020). Este proceso tiene que ver con la recopilación del conocimiento disponible sobre el dominio para la generación del grafo y dicho conocimiento puede estar disponible ya en algunas estructuras como ontologías, taxonomías o vocabularios. En esta generación de conocimiento útil se proponen distintos métodos: el etiquetado manual o semiautomático, el mapeo de esquemas externos y la anotación automática. La elección de estos métodos está determinada por la disponibilidad y los formatos en los que la información se encuentra y, en cualquier caso, ellos requieren una evaluación que permita la verificación de que ese conocimiento construido sea útil y consensuado, pues esto es lo que da validez y solidez conceptual a la base de conocimiento.

En esta fase se define también un concepto fundamental en todo el desarrollo de los grafos de conocimiento, el de **reutilización de conocimiento** , que se encuentra disponible en iniciativas como Schema.org _,_ que es un proyecto colaborativo que procura crear, mantener y promover esquemas para datos estructurados en internet sobre entidades, relaciones y acciones en formatos RDF, JSON-LD ( _JavaScript Object Notation for Linked Data_ ). Schema.org dispone esquemas, jerarquías, modelos de datos, así como guías de estilo e información para desarrolladores y también los vocabularios y extensión en muchos dominios de conocimiento. En palabras de Fensel _et al.:_

un vocabulario compartido facilita que los webmasters y desarrolladores decidan sobre un esquema. Schema.org cubre muchos dominios de manera genérica y se crean subconjuntos extendidos (es decir, patrones específicos de dominio) para hacerlo más adecuado a dominios y tareas específicas. La comunidad ya ha actuado para proporcionar extensiones externas para schema.org, y estas extensiones pueden adoptarse junto a coreschema.org para crear patrones específicos de dominio (2020, p. 20).

Sin embargo, dados ciertos dominios en donde no existen o no son suficientes los esquemas disponibles, se plantea como una posibilidad la anotación de otras fuentes que se encuentran bajo otros formatos.


------------------------- PAGINA 114 --------------------------

## **2. Alojamiento de conocimiento**

El grafo de conocimiento implica definir el repositorio en donde se alojarán los datos, las anotaciones sobre los mismos así como las reglas y propiedades condensadas en la ontología. Esta fase implica las tareas siguientes:

- La **recolección** , en donde se hace acopio de los datos a partir o bien del rastreo de sitios o del mapeo de las fuentes de los datos en esquemas ya existentes.

- El **almacenamiento** , que implica la construcción de una base de datos basada en grafos en la que se estructuren datos en formatos y lenguajes estandarizados con el fin de garantizar los principios de los que hablamos antes.

- La tarea de **recuperación,** que implica la implementación de un protocolo para consultas, que en el caso de RDF es SPARQL.

## **3. Curación de conocimiento**

Esta fase incluye la evaluación, limpieza y enriquecimiento conceptual. “El objetivo general de la curación del conocimiento es proporcionar métodos para mejorar la calidad de los grafos de conocimiento, garantizando su utilidad para las aplicaciones previstas” (Fensel _et al._ , 2020, p. 35). Aquí se identifica información que pueda ser errónea y se complementa sobre vacíos de conocimiento que no hayan sido cubiertos en la primera fase.

La curación de conocimiento implica evaluar la formalización de los tipos, jerarquías y propiedades de los conceptos con el fin de detectar y corregir errores en las instancias, relaciones y en los valores de las propiedades. Para ello se hace uso de distintos métodos de curación según los objetivos del elemento que quiera ser validado. Estos métodos incluyen una distribución estadística de tipos y propiedades, axiomas de disyunción, aprendizaje de máquina, minería de reglas de asociación, razonadores de ontología, entre otros (Fensel _et al._ , 2020).

Dentro de esta fase también se incluye la limpieza de conocimiento en la que se da la depuración, deduplicación o fusión entre conceptos; y la completación que implica la adición de nuevas instancias o nuevas propiedades.


------------------------- PAGINA 115 --------------------------

## **4. Despliegue de conocimiento**

Esta fase está relacionada con la idea de hacer reusable el grafo de conocimiento y de que pueda visibilizarse la conceptualización y se pueda aprovechar el grafo en otros sistemas o procesos. Esta idea de desplegar el conocimiento está profundamente relacionada con el concepto de datos abiertos enlazados “que es un medio para publicar datos de forma abierta y de acuerdo con algunos principios, basados en tecnologías semánticas, que permiten que los datos sean fácilmente reutilizables debido a la lectura e interpretación implícita de la máquina” (Bizer _et al._ en Fensel _et al._ , 2020, p. 62).

Fensel _et al._ (2020) proponen una serie de iniciativas en las que se publican y disponen grafos de conocimiento sobre distintos dominios. Estos datos pueden ser estáticos, activos y dinámicos y su disponibilidad implica un alojamiento y un formato establecido. Los datos deben cumplir con los principios de encontrabilidad, accesibilidad, interoperabilidad y reusabilidad.

En el desarrollo de un grafo de conocimiento se plantean distintos caminos tanto para la creación de la base de conocimiento como para la consolidación de los servicios del grafo. A continuación, se describen algunas de las que refieren Blumauer y Nagy (2020), cuya elección de una o más, dependerá de contextos diferentes de acuerdo con las dinámicas propias de las organizaciones o los dominios de conocimiento y con la disponibilidad de estructuras conceptuales claramente definidas.

- **Clasificación de categorías.** Es una metodología por medio de la cual se identifican tópicos, nombres en categorías que dan sentido a grupos de personas (requiere trabajo colaborativo). Son en principio un listado de términos que posteriormente serán la base de la ontología o taxonomía propia de la base de conocimiento.

- **Gestión de taxonomías.** Las taxonomías corresponden a esas estructuras conceptuales que existen previamente en una organización y que luego actúan como base para los esquemas de un grafo de conocimiento y que deben ser validados por equipos de personas.


------------------------- PAGINA 116 --------------------------

- **Gestión de ontologías.** A partir de esta metodología, Blumauer y Nagy (2020) plantean desarrollar la construcción del grafo por capas como “anillos de cebolla”, de modo que se pueda primero definir un dominio, luego establecer objetivos y alcance, y seguir con la priorización de las clases, entidades y relaciones. Las ontologías, tal como se dijo antes, tienen un nivel más alto de expresividad semántica y complejidad, y su crecimiento está relacionado con la necesidad de hacer iteración.

- **_RDFización._** Esta metodología se refiere al proceso de convertir los datos estructurados previamente en taxonomías u ontologías en el lenguaje RDF, de modo que se puedan mapear entidades y relaciones en el dominio y estructurar los datos en estándares para el intercambio y la consulta.

- **Minería de texto.** Esta metodología apunta a la transformación de datos no estructurados en RDF a partir de la extracción de entidades y de eventos que implica el reconocimiento a partir de patrones predefinidos del tipo persona, compañía, entre otros.

- **Entidades vinculadas y fusión de datos.** Implica la recolección de distintas fuentes para fusionar la información y crear valores añadidos. Aquí Blumauer y Nagy (2020) explican que:

   - la ontología que define el esquema de los datos también ayuda al mapear datos estructurados y también al extraer hechos de datos no estructurados. Junto con los enfoques de aprendizaje automático, esto permitirá incluso el establecimiento de un mapeo automatizado de la información estructurada y la comprobación de la calidad de los propios datos. Además, nos permitirá reconocer más hechos e información en los datos no estructurados y hacerlos más valiosos (p. 128).

- **Consulta de grafos de conocimiento.** La consulta de grafos de conocimiento se hace a partir del lenguaje RDF y siguiendo el protocolo SPARQL, que permite además el intercambio de información.


------------------------- PAGINA 117 --------------------------

Para la generación de conocimiento las herramientas pueden ser manuales o semiautomáticas, también se da el mapeo de esquemas externos o la anotación automática. Se debe considerar además la evaluación como parte fundamental del proceso de validación de conocimientos que implican las tareas de limpieza de los datos.

En cuanto a lenguajes, un grafo de conocimiento se integra a otros sistemas de gestión de información en una organización, integrando la base conceptual y relacional de los elementos que componen un _database model_ . Las fuentes de los datos que alimentan el grafos pueden ser: datos estructurados en bases de datos relacionales (hojas de cálculo, XML, RDF); datos no estructurados en sistemas de archivo o CMS ( _Content Management System_ ) o a partir de acceso a ontología mediante algoritmos de _machine learning_ .

El RDF define los tipos de nodos e identificadores de las entidades y se propone como un modo de identificar globalmente un recurso, para que pueda reducirse la ambigüedad y por tanto facilitar procesos de extracción y clasificación con entidades.

Para ayudar a evitar tal ambigüedad, en primer lugar podemos utilizar identificadores globalmente únicos para evitar choques de nombres cuando el grafo de conocimiento se amplía con datos externos, y en segundo lugar podemos añadir enlaces de identidad externa para desambiguar un nodo con respecto a una fuente externa (Hogan _et al.,_ 2021, p. 17).

## **Creación y enriquecimiento de grafos**

En cuanto a la creación y enriquecimiento de grafos de conocimiento, puede hacerse por distintos caminos: uno es la colaboración humana que implica contar con conocimiento disponible por parte de las personas y determinar los modos de recolección de esos datos y definir qué hacer con cosas que pueden dar lugar a errores o imprecisiones. El otro camino son los recursos textuales que se trabajan a partir de corpus y en los cuales se usan técnicas de procesamiento de lenguaje natural y de extracción de información. Ambas posibilidades requieren una conceptualización sólida de los dominios que permitan la identificación unívoca de entidades.


------------------------- PAGINA 118 --------------------------

Los grafos de conocimiento son una forma de representar el conocimiento del mundo real como una red de entidades relacionadas, para lo cual Hogan _et al._ (2021) proponen varias técnicas y métodos, entre las que se encuentran:

representaciones de esquema, identidad y contexto; técnicas para aprovechar el conocimiento deductivo e inductivo; métodos para la creación, enriquecimiento, evaluación de calidad y refinamiento de grafos de conocimiento; principios y estándares para la publicación de grafos de conocimiento; y finalmente, la adopción de grafos de conocimiento en el mundo real (p. 77).

La elección de estas técnicas está directamente relacionada tanto con las características propias del dominio como con los actores implicados y las aplicaciones del grafo previstas, así como con las fuentes de datos disponibles. Cualquiera de estas técnicas involucra las tareas de preprocesamiento, reconocimiento de entidades nombradas, entidades enlazadas y extracción de relaciones, y otra muy importante relacionada con la calidad y cantidad de la recolección de los datos a partir de extracción en las fuentes por medio de recursos que han sido marcados en páginas web, así como tablas y estructuras de los datos que allí se disponen, o bien en recursos estructurados por medio de formatos como CSV ( _Comma-Separated Values_ ), JSON, XML, etc.

Una manera de aprovechar el conocimiento disponible es a partir del uso de ontologías, lo cual puede entenderse tanto desde la adopción como del desarrollo de ellas. La adopción de ontologías implica que estas por supuesto existan. Cuando no, como es el caso de esta tesis, se opta por la creación de esquemas conceptuales que retoman metodologías propias de la ingeniería ontológica o del aprendizaje de ontologías para reutilizar conocimiento ya disponible.

Otro aspecto metodológico que es útil tener en cuenta en el desarrollo de los grafos de conocimiento es el enfoque desde el cual se acerca esta tesis doctoral. Estos enfoques planteados en Hogan _et al._ (2021) tienen que ver, entre otras cosas, con las fuentes de las cuales se toma información que pueda ser reutilizada y que contribuya al enriquecimiento del grafo. Las fuentes pueden ser:


------------------------- PAGINA 119 --------------------------

1. Con colaboración humana en donde se requiere conocimiento experto permanente en el proceso de creación del grafo.

2. Enriquecimiento basado en textos como fuentes, que haría referencia a la recolección de ejemplos de uso de los textos en que se recopile el conocimiento y que darían cuenta de entidades nombradas, entidades vinculadas o extracción de relaciones.

3. Enriquecimiento basado en fuentes de marcado, que se refiere al aprovechamiento de recursos en línea que, haciendo uso de protocolos y lenguajes de marcación de la información, aportan información conceptual sobre las entidades o los asuntos que tratan.

4. Enriquecimiento basado en recursos estructurados a partir de lenguajes XML y JSON, que recogen además de información formal de los documentos, datos relacionados con el contenido de los datos.

5. Creación de grafos a partir de esquemas conceptuales y ontologías.

Obviamente cada uno de estos enfoques se atenderá a cuestiones de disponibilidad de recursos o de la descripción y especificación conceptual que se tenga en el dominio.

La aproximación realizada en esta tesis se encuentra entre el segundo y el quinto enfoque, pues en el desarrollo de la investigación se usaron como fuentes para identificar las entidades tanto textos para reconocer en lenguaje natural como terminologías. También se hace una parte de experimentación con la creación de una ontología según las entidades reconocidas en los textos más las de fuentes terminológicas.

# **6.4. Representación de conocimiento en grafos**

De acuerdo con Bergman (2018), “la representación del conocimiento es una forma abreviada de representar la información y el conocimiento simbólicos humanos a los ordenadores, preferiblemente de la forma más eficaz posible” (p. 1). El principal reto de la representación de conocimiento es encontrar formas de representar el significado y que este pueda expresarse de la manera más sencilla y eficaz posible. Además de garantizar que en lo posible este conocimiento sea compartido y respaldado por una 118


------------------------- PAGINA 120 --------------------------

comunidad, de modo que pueda minimizarse la ambigüedad, lo cual es fundamental en sistemas semánticos como taxonomías, ontologías o grafos.

Se plantea que, además de la semántica, es necesario considerar otros fenómenos cuando se plantea un sistema de gestión del conocimiento:

   - El conocimiento nunca está completo, por tanto cualquier sistema de representación de conocimiento será siempre inacabado.

   - El conocimiento está en múltiples formas, es decir reside en bases de datos estructuradas pero también en los mismos documentos, metadatos y páginas web, y un sistema de representación debe considerar esta diversidad.

   - El conocimiento está en todas partes y su incorporación deberá garantizarse reflexivamente en las estructuras de representación, de modo que puedan cubrirse nuevas conexiones a medida que el conocimiento crece.

   - Las estructuras de conocimiento evolucionan a medida que se crea e integra nueva información que debe ser nombrada y validada mediante vocabulario específico.

   - El conocimiento es consenso y por tanto es vital la incorporación de los usuarios de dichas estructuras de conocimiento para el enriquecimiento conceptual de dominios.

- Ahora, cuando se piensa en estructuras en entornos web, se entiende que: la representación del conocimiento es un campo de la inteligencia artificial dedicado a representar información sobre el mundo de forma que un sistema informático pueda utilizarla para resolver tareas complejas, mediante tecnologías semánticas y el aprendizaje automático y la inteligencia artificial hasta la integración de la información y la interoperabilidad de los datos (Bergman, 2018, p. 2).

Otras estructuras de representación de conocimiento que se destacan como tecnologías semánticas son las taxonomías y las ontologías, de las cuales se habló ampliamente en el <u>capítulo 3.</u> La taxonomía es una estructura de agrupación jerárquica que permite la agrupación de objetos o datos según un nivel de especificidad, que puede ser más o


------------------------- PAGINA 121 --------------------------

menos detallado dependiendo de las necesidades sobre el tema. La taxonomía sería el nivel más básico de estructuración de conocimiento, en donde se definen categorías y subcategorías que representan una estructura formal de clases o tipos de objetos de un dominio.

Las ontologías, por su parte, abarcan también una representación formal a partir de la definición de unas clases, propiedades y relaciones entre ellas. Las ontologías son necesarias para establecer cuáles son las estructuras conceptuales mediante las cuales se pueda garantizar interoperabilidad, accesibilidad y reutilización de los datos. Las ontologías vendrían a ampliar la estructura básica planteada desde las taxonomías, pues además de la definición de las clases y las entidades que las componen, se busca establecer las interrelaciones de significado.

Las ontologías hacen parte de un grafo de conocimiento puesto que estas incluyen el modelo conceptual que es enriquecido por los vocabularios o taxonomías del modelo lingüístico y sobre lo cual se operan posteriormente formas de relacionamiento entre esos elementos. En ese sentido, se entendería el grafo de conocimiento como una evolución de las ontologías en cuanto estos buscan conectar más cosas, no solo los conceptos sino también recursos. Los grafos de conocimiento se proponen como una herramienta para organizar, representar y almacenar el conocimiento del mundo.

Otros autores plantean que “una ontología proporciona el vocabulario y un grafo de conocimiento es una ontología combinada con datos” (Debellis, 2021, p. 90). Es interesante anotar que tanto la construcción de grafos como la de ontologías u otras estructuras conceptuales llevan a cabo tareas de extracción, fusión, inferencia y validación de conocimiento, y que en cada una de estas fases se demandan unas tareas y se requieren unos recursos particulares, cuyo desarrollo y completitud estará determinado por cuestiones relacionadas con los contextos de producción y uso del conocimiento que quiere representarse.

Los grafos de conocimiento instancian tanto la taxonomía como la ontología usando datos reales y las relaciones que puedan asociarse entre esos datos y, mediante la incorporación de técnicas de aprendizaje profundo e inteligencia artificial, buscan que


------------------------- PAGINA 122 --------------------------

esos modelos de datos puedan incrementarse y desarrollar modos de predecir respuestas de modo automático.

Las taxonomías, ontologías y grafos son la base del desarrollo de la inteligencia artificial. Los algoritmos, el aprendizaje profundo, las redes neuronales son importantes pero sin una conceptualización y descripción formal del conocimiento disponible estos no tienen la efectividad que se les promociona. De ahí que entender estas estructuras y procurar modelos semánticos acordes a la información que se representa y a las necesidades que se atiende es fundamental.

Los desarrollos y potencialidades que se plantean para este campo son múltiples, así como lo ilustra Bergman (2018) cuando afirma que,

- las ontologías de dominio hacen más hincapié en las relaciones conceptuales que en las lexicográficas para un determinado dominio de conocimiento. Además, si poblamos suficientemente un grafo de conocimiento con datos de instancia precisos, a menudo procedentes de varias bases de conocimiento, las ontologías también pueden ser las estructuras que guíen un aprendizaje automático y un aprendizaje automático eficaces (p. 7).

Algunas de las potencialidades de los grafos, en combinación con esquemas semánticos como ontologías, se encuentran en los desarrollos propios del procesamiento de lenguaje natural, la generación de texto o la traducción. El mapeo de bases de conocimiento, el enlace de entidades, el mismo desarrollo, fusión y ampliación de ontologías, el reconocimiento de patrones, análisis de relaciones semánticas. Además se proponen como una excelente herramienta para mejorar los sistemas de búsqueda y recuperación de información.


------------------------- PAGINA 123 --------------------------

# **Capítulo 7. Aprendizaje automático para estudios del lenguaje**

<mark>El aprendizaje automático o aprendizaje de máquinas permite realizar tareas de clasificación a partir de imágenes, texto o sonido por medio de la arquitectura de una red neuronal que involucra niveles de capas de información que están interconectadas a partir de las cuales se ejecutan procedimientos con modelos de abstracción sobre los datos. Una red neuronal combina múltiples capas de procesamiento, utilizando elementos simples que operan en paralelo. Las capas están interconectadas a través de nodos o neuronas, y cada capa oculta utiliza la salida de la capa anterior como entrada (Li</mark> _<mark>et al.</mark>_ <mark>, 2020).</mark>

<mark>El aprendizaje de máquinas puede ser: supervisado, no supervisado, semisupervisado y autosupervisado, según los niveles de abstracción y los algoritmos que sean utilizados. El aprendizaje de máquinas necesita conocimiento experto y requiere también buen volumen de datos etiquetados que hayan sido entrenados y una fuerte supervisión por lo que resulta costoso ejecutar tareas dependientes que sean precisas, así como la necesidad de disponer de gran capacidad computacional pues demanda memoria y procesamiento algorítmico. Tal como lo dice Kochmar, “la complejidad de las tareas de aprendizaje de máquinas supervisado depende del número de clases que puedan distinguirse” (2022, p. 394).</mark>

<mark>El aprendizaje profundo modela abstracciones de alto nivel llevando datos a estructuras matriciales que permiten una iteración de mayor sofisticación por lo cual es utilizado en procesos de más complejidad y volumen de datos.</mark>

La principal ventaja del aprendizaje profundo es la capacidad de aprendizaje de la representación y la composición semántica potenciada tanto por la representación vectorial como por el procesamiento neuronal. Esto permite alimentar una máquina con datos brutos y descubrir automáticamente las representaciones latentes y el procesamiento necesario para la clasificación o la detección ( <mark>Li</mark> _<mark>et al.,</mark>_ <mark>2020, p. 5).</mark>

<mark>Por esta razón es que estos métodos resultan de gran interés para el procesamiento de lenguaje y para la generación de representaciones semánticas.</mark>


------------------------- PAGINA 124 --------------------------

<mark>En este apartado se describen los métodos de aprendizaje y los tipos de arquitectura involucradas. Posteriormente se aborda el aprendizaje profundo como método para extracción de entidades nombradas y poblamiento de ontologías y grafos de conocimiento y finalmente se referirá a los modelos de lenguaje y los</mark> _<mark>transformers</mark>_ <mark>que son utilizados en tareas de procesamiento de lenguaje natural y de representación de conocimiento.</mark>

<mark>A continuación se describen los distintos tipos de aprendizaje así como las arquitecturas de las redes neuronales que son utilizadas y que,</mark>

a diferencia del aprendizaje no supervisado, los enfoques autosupervisados siguen dependiendo de las etiquetas de entrada para optimizar el objetivo de entrenamiento. Sin embargo, a diferencia de los métodos supervisados y semisupervisados, estas etiquetas se generan automáticamente explotando las relaciones entre las diferentes partes de los datos de entrada, sin la participación humana o de expertos <mark>(Meng</mark> _<mark>et al.</mark>_ <mark>, 2019, p.</mark> 1).

# **7.1. Métodos de aprendizaje y tipos de arquitectura**

<mark>El aprendizaje supervisado requiere de datos etiquetados y entrenados manualmente; el no supervisado incorpora técnicas que descubren patrones en los datos; el semisupervisado usa una semilla de datos que contiene ejemplos anotados manualmente y que le sirve para reconocer patrones que facilitan la inferencia de reglas sobre los datos; y por último, el aprendizaje autosupervisado no necesita ningún ejemplo anotado, sino que utiliza etiquetas libres a partir de reglas bien construidas para inducir las relaciones. En este último tipo de aprendizaje se reconocen algunas técnicas como generación autosupervisada basada en conocimiento o aprendizaje adversorial, que usa algoritmos de aprendizaje automático para incorporar conocimientos de dominio.</mark>

<mark>Estas arquitecturas de modelos de representación pueden ser: redes que ven el texto como una bolsa de palabras; modelos de redes neuronales que ven el texto como una secuencia de palabras y capturan las dependencias de las palabras en la estructura del</mark>


------------------------- PAGINA 125 --------------------------

<mark>texto; modelos de redes neuronales convolucionales que se entrenan para reconocer patrones y frases clave en el texto; mecanismos de atención para identificar palabras correlacionadas en un texto; o redes neuronales para comparación entre textos, además de modelos usados para el procesamiento de imágenes. Como tecnologías de modelado, se destaca el</mark> _<mark>autoencoder</mark>_ <mark>, entrenamiento adversarial y aprendizaje por refuerzo.</mark>

<mark>Dentro del aprendizaje autosupervisado, vale mencionar la técnica de aprendizaje contrastivo que proponen Das</mark> _<mark>et al.</mark>_ <mark>(2021) para optimizar la distancia de distribución entre</mark> _<mark>tokens</mark>_ <mark>con el fin de reconocer nuevas clases como entidades nombradas. Estos autores proponen</mark> que “la incrustación gaussiana modela explícitamente las distribuciones de clase de las entidades, lo que no sólo promueve la representación generalizada de las características, sino que también ayuda a la adaptación del dominio de destino con pocas muestras” ( <mark>Das</mark> _<mark>et al</mark>_ <mark>., 2</mark> 021, p. 2). De esta manera pueden implementarse algoritmos para el autoaprendizaje en datos no etiquetados previamente como en el modelo CONTAINER, que utiliza el aprendizaje contrastivo para optimizar la divergencia distributiva entre diferentes representaciones de entidades de _tokens._

Estas arquitecturas son base de la inteligencia artificial y entre ellas se encuentran <mark>redes neuronales convolucionales, redes neuronales recurrentes, redes neuronales recursivas y</mark> _<mark>transformers</mark>_ <mark>profundos, en donde tal como lo apunta Bergman (2018), “l</mark> a inteligencia artificial basada en el conocimiento, es el uso de grandes bases estadísticas o de conocimiento para fundamentar la selección de características para los algoritmos de aprendizaje automático utilizados en la IA” (p. 74). Es importante que estas bases de conocimiento sean correctamente expresadas para “ayudar a crear conjuntos de entrenamiento positivos y negativos, promover la generación y expresión de conjuntos de características y generar normas de referencia para el aprendizaje automático” (Bergman, 2018, p. 74).

La supervisión del conocimiento en el aprendizaje profundo proporciona mejoras en las características y calidad de los datos que conforman el conjunto de entrenamientos para aplicación en tareas de inteligencia artificial.


------------------------- PAGINA 126 --------------------------

# **7.2. Aprendizaje profundo para extracción de entidades nombradas y poblamiento de ontologías y grafos de conocimiento**

<mark>Las técnicas utilizadas para el aprendizaje profundo, pueden ser aprendizaje basado en texto, aprendizaje basado en páginas HTML, aprendizaje basado en enciclopedias y otro aprendizaje basado en fuentes.</mark>

- <mark>El</mark> **<mark>aprendizaje basado en texto</mark>** <mark>tiene su origen en</mark> _<mark>Text-to-Onto</mark>_ <mark>(Maedche y Staab, 2000) y se define como un sistema de aprendizaje de ontologías basado en la arquitectura general para descubrir estructuras conceptuales que contienen términos, sinónimos, conceptos, relaciones taxonómicas y reglas.</mark>

- <mark>El</mark> **<mark>aprendizaje basado en páginas HTML,</mark>** _<mark>OntoLearn</mark>_ <mark>aprende ontologías de dominio de sitios web, extrayendo la terminología de dominio de los documentos web y organizándola de forma jerárquica.</mark>

- <mark>El</mark> **<mark>aprendizaje basado en enciclopedia</mark>** <mark>propone las relaciones entre etiquetas que fueron usadas en la descripción de contenidos en Wikipedia relacionándolos con información proporcionada por Wordnet, lo cual permitiría mayor refinamiento semántico.</mark>

- <mark>Por último, el</mark> **<mark>aprendizaje basado en fuentes</mark>** <mark>recopila información disponible en motores de búsqueda o mapas conceptuales para relacionar los conceptos de dominios específicos (Hu</mark> _<mark>et al.,</mark>_ <mark>2014).</mark>

<mark>El aprendizaje profundo para la construcción de ontologías (Hu</mark> _<mark>et al.</mark>_ <mark>, 2014), (Dou</mark> _<mark>et al</mark>_ <mark>., 2018), (Ayadi</mark> _<mark>et al.</mark>_ <mark>, 2019) y (Kulmanov</mark> _<mark>et al</mark>_ <mark>., 2021) o para el poblamiento de un grafo de conocimiento (Barrasa</mark> _<mark>et al.</mark>_ <mark>, 2021), y (Liu</mark> _<mark>et al</mark>_ <mark>., 2021) incorpora algoritmos que procesan las relaciones entre los conceptos, a partir de las tareas de extracción de conceptos y relaciones, la clasificación y el reconocimiento de entidades.</mark>

<mark>La incorporación de aprendizaje automático a la creación de grafos de conocimiento sirve para tareas como la recomendación automática, la extracción de información, los sistemas de pregunta/respuesta o la aproximación a consultas. La codificación de los grafos de conocimiento se da a partir de incrustaciones de palabras que proporcionan</mark>


------------------------- PAGINA 127 --------------------------

<mark>una representación numérica. Otro enfoque, sin embargo, plantea la creación de “modelos de aprendizaje automático personalizados adaptados a datos estructurados en grafos” (Hogan</mark> _<mark>et al.,</mark>_ <mark>2021, p. 43).</mark>

<mark>A continuación se exploran algunas de las técnicas de aprendizaje profundo para el poblam</mark> iento de ontologías o para la construcción de grafos de conocimiento.

El aprendizaje de la representación del lenguaje mediante el preentrenamiento de modelos lingüísticos autosupervisados se ha convertido en un componente integral de muchos sistemas de procesamiento de lenguaje natural. El modelado tradicional del lenguaje no explota el conocimiento factual con entidades frecuentemente observadas en el corpus de texto. La forma de integrar el conocimiento en la representación del lenguaje ha atraído cada vez más atención (Ji _et al._ , 2021).

<mark>En la</mark> <u><mark>tab</mark> la 6</u> se <mark>especifican los modelos y técnicas propuestas por diversos actores, identificando el dominio de conocimiento en el que surgen, la fuente de los datos, así como los lenguajes de ontologías que son propuestos y las técnicas implementadas.</mark>

Ahora, cuando no se tienen suficientes datos anotados previamente que sirvan para el entrenamiento, se plantean métodos para trabajar con pocos datos preetiquetados pues,

el aprendizaje a partir de unos pocos ejemplos sigue siendo un reto clave en el aprendizaje automático. A pesar de los recientes avances en dominios importantes como la visión y el lenguaje, el paradigma estándar de aprendizaje profundo supervisado no ofrece una solución satisfactoria para aprender nuevos conceptos rápidamente a partir de pocos datos (Vinyals _et al._ , 2017).

Un aspecto importante de las tareas de procesamiento tiene que ver con la necesidad de tener datos preentrenados pues la máquina, a diferencia del aprendizaje humano, requiere cientos de miles de ejemplos para poder llegar a una inferencia, que los humanos incluso en la niñez hacemos de manera sencilla por abstracción de conceptos,


------------------------- PAGINA 128 --------------------------

por lo que no se requiere tanta supervisión, como sí ocurre en los sistemas a los cuales es necesario incorporar muchos ejemplos para llegar a generalizaciones.


------------------------- PAGINA 129 --------------------------

## **Tabla 6**

_Metodologías de aprendizaje profundo para poblamiento de un grafo de conocimiento_

|**Autores**|**Dominio**|**Propósito**|**Fuente de datos**|**Lenguaje de**<br>**ontología**|**Técnica**|
|---|---|---|---|---|---|
|Ayadi_et al._<br>(2019)|_Biology._<br>_Biomolecular_|Poblar de conceptos una ontología y<br>aprovechar conocimiento biológico en<br>datos no estructurados.|15 artículos a texto<br>completo de<br>PubMed|Ontología<br>BNO|_Word2Vec_|
|Barrasa_et_<br>_al._(2021)|_Decision_<br>_making in_<br>_Businesses_|Uso de grafos como herramienta que<br>aporta información contextualizada de<br>los datos para mejorar predicciones en<br>entornos empresariales.|No se describe|_Resource Description_<br>_Framework (RDF)_|No se describe|
|Dou_et al._<br>(2018)|_Chinese_<br>_intangible_<br>_cultural_<br>_heritage_|Extraer conocimiento de patrimonio<br>cultural intangible para apoyar la<br>organización, gestión y protección<br>descubriendo conocimiento vinculado.|Web del instituto<br>nacional y de cada<br>provincia sobre<br>patrimonio cultural<br>intangible|CIDOC<br>_Conceptual Reference_<br>_Model_<br>(CIDOC CRM)<br>_ontology/schema_|_Character-level_<br>_attention-based_<br>_Bi-GRU model and_<br>_the sentence-level_<br>_attention-based_<br>_Bi-GRU model_<br>_cluster/_<br>_classification_<br>_algorithm_<br>_methods_<br>_Probability model_|


------------------------- PAGINA 130 --------------------------

|**Autores**|**Dominio**|**Propósito**|**Fuente de datos**|**Lenguaje de**<br>**ontología**|**Técnica**|
|---|---|---|---|---|---|
|Hu_et al._<br>(2014)|_Chinese_<br>_language_|Construir una ontología para el chino con<br>técnicas de autosupervisado|Tres enciclopedias<br>en línea<br>Más de 5 millones<br>de artículos|SSCO. 255 mil<br>conceptos, 5 millones<br>de entidades, 40<br>millones de hechos|_Conditional_<br>_Random Field_<br>(NER),_Support_<br>_Vector Machine_<br>(clasificación)<br>_Self-supervised_<br>_ontology learning_<br>_Probabilistic model_|
|Kulmanov<br>_et al._(2021)|_Life_<br>_sciences_|Combinación de clases de diferentes<br>ontologías para inducir conocimiento en<br>el análisis predictivo|Bases de datos<br>biológicas<br>BioPortal (800<br>ontologías)|OWL_biomedical_<br>_ontologies_|OWL2Vec<br>_Embedding_<br>_ontologies_<br>_semantic similarity_|
|Lan_et al._<br>(2020)||Propuesta de reducción de parámetros<br>para escalar modelos preentrenadospara<br>optimizar|_Stanford Question_<br>_Answering Dataset._<br>_SQuAD ReAding_<br>_Comprehension_<br>_from Examinations_<br>_(RACE) dataset_|No se describe|BERT<br>ALBERT|
|Liu_et al._<br>(2021)|_Heterogeneous_<br>_knowledge_|Marco de aprendizaje de_embeddings_con<br>técnicas de autosupervisado para enlazar<br>conceptos de conocimiento heterogéneo|_Microsoft Academic_<br>_Graph taxonomy,_<br>_English Wikipedia_|No se describe|No se describe|


------------------------- PAGINA 131 --------------------------

Por su parte, el aprendizaje de representación autosupervisado en tareas de procesamiento de lenguaje natural sirven para el desarrollo de tareas como predicción de la palabra central, predicción de palabras vecinas, predicción de frases vecinas, modelado autorregresivo del lenguaje, modelado lingüístico enmascarado, predicción de la frase siguiente, predicción del orden de las frases, permutación de sentenciadores, notación de documentos, predicción de _emojis_ .

# **7.3. Modelos de lenguaje y** **_transformers_**

Los modelos de lenguaje funcionan a partir de la definición de millones de parámetros y el entrenamiento de ejemplos que le permitan al _transformer_ predecir cuál palabra es la siguiente en una oración. Lo primero que se hace en un modelo de lenguaje es representar el vocabulario con un número, es decir, traducir palabras a lenguaje matemático de modo que los números lleven a matrices y vectores que luego puedan traducirse nuevamente a lenguaje.

Esta estructura, que parece magia, requiere sin embargo una cantidad importante de ejemplos y por eso cuando se intenta usar en procesos de análisis más específicos en dominios concretos, no contar con suficientes ejemplos anotados que permitan distinguir cosas entre sí supone un reto importante.

En la modelación de lenguaje es importante asignar a una fuente de datos de entrada los esquemas de la base de conocimiento definiendo los atributos y propiedades de las clases que son incorporadas. Esta definición explícita permite que pueda hacerse una clasificación correcta de acuerdo con la coincidencia lingüística tanto sintáctica como semánticamente. Este proceso permite mapear los sinónimos, hiperónimos o emparejar la descripción de atributos a través de técnicas de similitud semántica.


------------------------- PAGINA 132 --------------------------

La modelación del lenguaje se traduce siempre a modelos matemáticos que calculan las posibles combinaciones entre las palabras para reconocer aquellas que son entidades y a cuál clase pertenecen. Esta modelación requiere que se tengan muchos ejemplos anotados. Cuando esto no ocurre se recurre a técnicas como _fine-tuning_ que son utilizadas como alternativa cuando no se tiene tanta información anotada previamente o datos de calidad. Su utilidad radica en que son efectivos para una tarea determinada, son eficientes y con pocos ejemplos basta para resolver cierta cantidad de tareas.

Los grandes modelos de lenguaje que son utilizados en herramientas como chat GPT ( _Generative pre-trained transformers_ ), u otros que incorporan inteligencia artificial, usan lo que se conoce como ingeniería de PROMPT, la cual se entiende como una instrucción o pregunta que deberá ser lo más clara y concisa posible para obtener mejores resultados. Un modelo de lenguaje se entrena a partir de PROMPT indicando instrucción, contexto, datos de entrada e indicador de salida. Se plantea como un proceso iterativo que comenzaría por una tarea simple que puede ir haciéndose más compleja a medida que se ajustan parámetros del modelo.

Un modelo de lenguaje involucra dentro de su arquitectura al menos estas tareas: la tokenización, que se refiere a la fragmentación del texto en unidades más pequeñas (desde sentencias hasta palabras); incrustación ( _embeddings_ ), que se refiere a la traducción del lenguaje a una codificación numérica; codificación posicional, que se refiere a la ubicación de estos códigos numéricos en vectores; bloque transformador, que se ejecuta varias veces mediante mecanismos de atención y retroalimentación; y _softmax_ , que es una función que convierte los datos numéricos en probabilidades dando como resultado las respuestas a las cuestiones que se plantean.

Un _transformer_ es una gran red neuronal que dada su potencia brinda mayor precisión, sin embargo su funcionamiento requiere una GPU ( _Graphics Processing Unit_ ) que pueda funcionar de manera efectiva por lo que su implementación es costosa. La riqueza de un _transformer_ está dada en que los vectores de palabras van más allá de la distribución simple de _tokens_ , es decir que más que _tokens_ modela tipos de léxicos


------------------------- PAGINA 133 --------------------------

según el contexto en el que estos aparecen, acercándose de manera importante al proceso de representación semántica.

<mark>Uno de los modelos de lenguaje de representación que surgen en el campo del procesamiento de lenguaje natural y el aprendizaje de máquinas es el modelo BERT, que es utilizado para las tareas de reconocimiento de entidades nombradas, extracción de relaciones y sistemas de pregunta-respuesta en dominios como el campo de la ciencia biomédica (Meng</mark> _<mark>et al.,</mark>_ <mark>2019). Los</mark> _<mark>transformers</mark>_ <mark>vienen a ampliar el uso de las redes neuronales, porque permiten preentrenar eficientemente modelos lingüísticos a través de diferentes arquitecturas, entre las que se destacan las arquitecturas de atención (Rothman, 2021).</mark>

Existen modelos de lenguaje muy potentes para el inglés. Sin embargo, para el español o para lenguas minorizadas es más difícil el desarrollo, dada la escasez de corpus en términos de calidad y volumen comparados con el inglés y el costo computacional que tiene el preentrenamiento, por lo que justamente los mayores desarrollos son los que se hacen en grandes compañías (Vaca _et al._ , 2022). De acuerdo con datos presentados por la Red SomosNLP, en 2022 el número de modelos de lenguaje existentes para inglés y español correspondía a 5.486 y 453, respectivamente, lo cual alerta sobre una demanda importante de desarrollo de recursos para el español que sirva a los más de 540 millones de hablantes de esta lengua.

Algunas de las razones sobre el menor avance en recursos para el español lo explican Vaca _et al._ (2022) cuando afirman que los modelos

no son tan eficaces como los modelos para el inglés por las siguientes razones: 1. Escasez de corpus en español de la misma calidad y volumen que los utilizados por los modelos en inglés. 2. Los costes de preentrenamiento de grandes modelos lingüísticos son considerables, del orden de cientos de miles de dólares, asequibles para las grandes empresas multinacionales (p. 2).

Entre los modelos de lenguaje para el español, se mencionan BETO, BERTIN, MarIA y RigoBERTa, además de la versión en español de BERT. BETO tiene 110M de parámetros y un vocabulario de 32.000 palabras y fue entrenado a partir del corpus SUC


------------------------- PAGINA 134 --------------------------

( _Spanish Unannotated Corpora_ ), BERTIN contiene 50M de documentos que forman el corpus, y MarIA está formado por 570GB de textos depurados y tiene un vocabulario de 50.262 palabras. RigoBERTa tiene 413GB de textos depurados de múltiples dominios (Vaca _et al_ ., 2022).

Ahora, la aplicación de modelos de lenguaje es muy interesante en tareas de reconocimiento de entidades nombradas porque suponen un ahorro de esfuerzo significativo en el diseño de características de NER, dando lugar al aprendizaje automático de representaciones útiles de los datos brutos o sin anotar. Sin embargo, será necesario continuar con la tarea de ampliar los tamaños de corpus de referencia que incluyan información realmente útil, es decir cumpliendo con datos de calidad limpios y preprocesados.

# **Parte 2: Metodologías y desarrollos**

En este apartado se describe el proceso de experimentación para la construcción de un grafo de conocimiento sobre el dominio del conflicto armado. Autores como Dou _et al_ . (2018), Kulmanov _et al._ (2021), Moreno Schneider _et al_ . (2022), Musgrave _et al._ (2014), Santoso _et al_ . (2021), Schmidt _et al._ , (2020), Villazón Terrazas (2011), Wang, K. _et al._ (2021), Wang, X. _et al._ (2021), Wu y Hsu (2002) y Xu _et al._ (2019) abordan el problema de representación a partir de la elaboración de ontologías. En este trabajo se plantea la combinación de varias técnicas: por un lado el reconocimiento de entidades para identificar elementos de la realidad que sirven para describir un fenómeno y a partir de los cuales se puede hacer una clasificación. Por otro lado, estarían las ontologías como herramientas para la representación de las clases en un dominio. El uso de estas dos herramientas y técnicas, permiten la construcción de un grafo de conocimiento.

Para alcanzar los objetivos propuestos en esta tesis, se definieron las siguientes fases en las cuales se exploran diferentes técnicas y herramientas que dan como resultado un producto en cada etapa.


------------------------- PAGINA 135 --------------------------

En el capítulo 8 se describen las fuentes para construir el _dataset_ que conforma el corpus, el cual está integrado, por un lado, por la base conceptual que está contenida en terminologías, ontologías y tesauros sobre el dominio; y por otro lado, una muestra de textos variados que se recopilaron como evidencia del uso del lenguaje y en los cuales se analizan las características y particularidades de términos y entidades.

El capítulo 9 se centra en la construcción de un modelo para clasificación de textos a partir del reconocimiento de entidades nombradas. Aquí se describe todo el proceso de entrenamiento y testeo, así como las tareas de anotación y etiquetado y los desafíos que se presentaron en la construcción del algoritmo. También se presentan las métricas para valorar la clasificación realizada.

El capítulo 10 aborda la ontología sobre conflicto armado indicando la metodología y lenguajes implementados así como el sistema de clases, propiedades e instancias que fueron definidas en términos amplios y en una muestra de representación de unas clases seleccionadas.

Por último, en el capítulo 11 se describen las bases para el modelo de un grafo de conocimiento sobre conflicto armado que integra tanto el reconocimiento de entidades como la ontología. Se definen las reglas y restricciones a tener en cuenta en el desarrollo y ampliación de este modelo.


------------------------- PAGINA 136 --------------------------

# **Capítulo 8. Corpus de entrenamiento y testeo**

Las fuentes de datos para la conformación del corpus, entendido como el conjunto de recursos con información sobre conflicto armado y defensa de los derechos humanos, está compuesto por más de treinta instituciones, cuyas páginas web ofrecen recursos como noticias, testimonios, relatos, galerías, información institucional, informes de investigación, revistas, información sobre casos, hechos, análisis, recursos digitales, información museográfica, material pedagógico, material audiovisual, entre otros textos variados. Si bien esta información se encuentra en formatos web, blogs, catálogos o repositorios que incluyen información textual en HTML o PDF, así como recursos audiovisuales y multimediales e interactivos, este corpus recopila solamente información producida como texto completo y disponible en PDF.

Dentro de estas instituciones están tanto aquellas que se dedican específicamente a la recopilación y la preservación de la memoria del conflicto como otras instituciones que dedicadas a asuntos como la defensa de derechos desde lo jurídico o la atención y acompañamiento a comunidades específicas, pero se considera que la información que producen da cuenta de las dinámicas del conflicto y de las formas para representación de las memorias.

# **8.1. Fuentes de los datos y consideraciones para conformar el corpus**

Las fuentes provienen de sitios que presentan tanto información institucional o de acompañamiento e intervención con comunidades, así como noticias sobre las actividades de estas organizaciones, por tanto las tipologías textuales y los alcances de los recursos al ser tan variados dan cuenta del uso natural del lenguaje en textos de especialidad sobre conflicto armado.

Algunos de los temas sobre los que se ofrece información son migración, desaparición, defensa del territorio y defensas ambientales para la conservación de la biodiversidad y el agua; luchas agrícolas, campesinas, indígenas, comunidad afrocolombiana, desarme, minas, vinculación de niños, niñas y adolescentes al conflicto armado, presos políticos,


------------------------- PAGINA 137 --------------------------

educación política, democracia, sindicalismo e incluso información de instituciones religiosas que acompañan a comunidades afectadas por el conflicto armado.

Las instituciones de las cuales se compilan los datos son del orden nacional o regional, oficiales, organizaciones no gubernamentales, asociaciones de víctimas, así como algunas organizaciones internacionales que trabajan en la defensa de los derechos humanos. La selección de estos sitios se hace atendiendo al tipo de información que disponen y si esta tiene posibilidad de descarga para la manipulación del texto y la construcción del corpus. En la <u>tabla 7</u> se relacionan las instituciones, su alcance, los temas que trabajan y el volumen de datos que se recopilaron de cada una.

Otra fuente importante para la construcción de la ontología y para la identificación de las clases y entidades son los tesauros, terminologías y bases conceptuales, descritos más ampliamente en el <u>capítulo 9,</u> y a partir de los cuales se recopila toda la información conceptual y terminológica.

En el <u>gráfico 2</u> se representan, por un lado, la construcción del modelo para reconocimiento de entidades nombradas en el corpus; el proceso de creación de la ontología; y la construcción del grafo de conocimiento con las clases que fueron priorizadas para representar el dominio.


------------------------- PAGINA 138 --------------------------

## **Tabla 7**

_Instituciones de donde se recopilan las fuentes del corpus_

|**Institución**|**Alcance**|**Temas**|**Volumen**|
|---|---|---|---|
|Alto Comisionado de las Naciones Unidas para<br>los Refugiados (Acnur) (Bogotá)|Internacional|Atención a migrantes y refugiados en<br>América Latina<br>Desplazamiento forzado|39 textos<br>1.609.154_tokens_|
|Asociación Minga (Bogotá)|Nacional|Información sobre casos de violación de<br>derechos humanos a los pueblos indígenas<br>en el marco del conflicto armado|21 textos<br>542.949_tokens_|
|Asociación de Víctimas Unidas del Municipio<br>de Granada -Asovida- (Granada, Antioquia)|Local|Memoria y víctimas del conflicto armado en<br>el municipio<br>Procesos de resistencia|131 textos<br>360.904_tokens_|
|Campaña Colombiana contra Minas (Bogotá)|Nacional|Desarme y minas|8 textos<br>59.764_tokens_|
|Centro<br>de<br>Memoria,<br>Paz<br>y<br>Reconciliación<br>(Bogotá)|Nacional|Iniciativas de memoria del conflicto<br>Procesos de paz<br>Iniciativas de reconciliación|19 textos<br>1.380.513_tokens_|
|Centro Nacional de Memoria Histórica (Bogotá)|Nacional|Memoria<br>Casos de conflicto armado<br>Luchas y procesos locales de resistencia|148 textos<br>12.640.571<br>_tokens_|


------------------------- PAGINA 139 --------------------------

|**Institución**|**Alcance**|**Temas**|**Volumen**|
|---|---|---|---|
|Centro de Investigación y Educación Popular<br>-CINEP- (Bogotá)|Nacional|Defensa de los derechos humanos<br>Sistematización de violaciones a los<br>derechos humanos|96 textos<br>11.942.841<br>_tokens_|
|Coalición contra la Vinculación de Niñas, Niños<br>y Jóvenes al Conflicto Armado en Colombia<br>-COALICO- (Bogotá)|Nacional|Información sobre vinculación de niños,<br>niñas y adolescentes al conflicto armado<br>Reclutamiento forzado de menores|9 textos<br>211.979_tokens_|
|Colombia Diversa (Bogotá)|Nacional|Violación de derechos humanos a<br>poblaciones diversas.|15 textos<br>437.722_tokens_|
|Comisión Colombiana de Juristas (Bogotá)|Nacional|Derecho Internacional Humanitario y<br>Defensa de los derechos humanos|512 textos<br>7.013.091_tokens_|
|Comisión para el Esclarecimiento de la Verdad<br>(Bogotá)|Nacional|Memoria y verdad<br>Violación de derechos humanos en el marco<br>del conflicto armado|1017 textos<br>34.350.463<br>_tokens_|
|Comité de Solidaridad con los Presos Políticos<br>-CSPP- (Bogotá)|Nacional|Garantías de los derechos humanos<br>Presos políticos|18 textos<br>684.823_tokens_|
|Comité Internacional de La Cruz Roja -CIRC-<br>(Bogotá)|Internacional|Asistencia humanitaria<br>Atención a comunidades en contextos de<br>emergencia|31 textos<br>134.986_tokens_|


------------------------- PAGINA 140 --------------------------

|**Institución**|**Alcance**|**Temas**|**Volumen**|
|---|---|---|---|
|Consejería<br>Presidencial<br>para<br>los<br>Derechos<br>Humanos (Bogotá)|Nacional|Derechos humanos|177 textos<br>3.399.843_tokens_|
|Coordinación Colombia-Europa-Estados Unidos<br>-CCEEU- (Bogotá)|Internacional|Derechos humanos y defensa de la<br>democracia|21 textos<br>1.447.985_tokens_|
|Corporación<br>Acompañamiento<br>Psicosocial<br>y<br>Atención en Salud Mental a Víctimas de la<br>Violencia Política -AVRE- (Bogotá)|Nacional|Acompañamiento psicosocial|6 textos<br>164.714_tokens_|
|Corporación Conciudadanía (Medellín)|Local|Democracia y ciudadanía|33 textos<br>546.897_tokens_|
|Corporación Jurídica Libertad (Medellín)|Regional|Defensa y promoción de derechos humanos|31 textos<br>1.580.687_tokens_|
|Corporación Región (Medellín)|Regional|Democracia y ciudadanía<br>Memoria|68 textos<br>2.410.729_tokens_|
|Corporación Vínculos (Bogotá)|Nacional|Acompañamiento social|28 textos<br>663.963_tokens_|


------------------------- PAGINA 141 --------------------------

|**Institución**|**Alcance**|**Temas**|**Volumen**|
|---|---|---|---|
|DeJusticia (Bogotá)|Nacional|Fortalecimiento del Estado de Derecho y<br>promoción de los derechos humanos|18 textos<br>1.437.823_tokens_|
|Fundación para la Reconciliación (Bogotá)|Nacional|Reconciliación y construcción de paz|4 textos<br>60.862_tokens_|
|Hacemos memoria (Medellín)|Nacional|Memoria|998 textos<br>1.398.853_tokens_|
|Humanidad<br>Vigente<br>Corporación<br>jurídica<br>(Bogotá)|Nacional|Víctimas y construcción de paz|7 textos<br>87.058_tokens_|
|Instituto de Estudios para el Desarrollo y la Paz<br>-INDEPAZ- (Bogotá)|Nacional|Paz y reconciliación|26 textos<br>535.098_tokens_|
|Instituto<br>Popular<br>de<br>Capacitación<br>-IPC-<br>(Medellín)|Local|Educación popular<br>Democracia y ciudadanía|27 textos<br>1.383.824_tokens_|
|Jurisdicción Especial para la Paz (Bogotá)|Nacional|Derechos de las víctimas a la justicia|122 textos<br>8.811.168_tokens_|
|Museo Casa de la Memoria (Medellín)|Local|Memoria|72 textos<br>664.743|


------------------------- PAGINA 142 --------------------------

|**Institución**|**Alcance**|**Temas**|**Volumen**|
|---|---|---|---|
|Movimiento Nacional de Víctimas de Crímenes<br>de Estado -MOVICE- (Bogotá)|Nacional|Crímenes de estado|67 textos<br>1.523.804_tokens_|
|Red por la Vida y los DDHH del Cauca<br>(Popayán)|Regional|Defensa de los derechos humanos|34 textos<br>363.628_tokens_|
|Reiniciar.<br>Corporación<br>para<br>la<br>Defensa<br>y<br>Promoción de los Derechos Humanos (Bogotá)|Nacional|Acompañamiento a defensores de derechos<br>humanos|4 textos<br>49.406_tokens_|
|Rodeemos el Diálogo -ReD- (Reino Unido)|Internacional|Reconciliación y construcción de paz|7 textos<br>29.258_tokens_|
|Ruta pacífica de las mujeres (Cali)|Nacional|Defensa de los derechos humanos<br>Mujeres y conflicto|55 textos<br>3.011.139_tokens_|
|Unidad de Búsqueda de Personas dadas por<br>desaparecidas (Bogotá)|Nacional|Desaparición|2 textos<br>74.567_tokens_|
|Unidad de víctimas (Bogotá)|Nacional|Defensa y memoria de las víctimas de<br>conflicto armado|110 textos<br>1.474.493_tokens_|


------------------------- PAGINA 143 --------------------------

## **Gráfico 2**

_Arquitectura general del proceso_


------------------------- PAGINA 144 --------------------------

# **8.2. Preprocesamiento de** **_dataset_**

El preprocesamiento involucra tareas de limpieza y preparación de los datos y la conversión a formatos estandarizados y compatibles para procesamiento computacional. Esta fase incluye la limpieza básica de carácteres que no se usarán, la _tokenización_ , la remoción de palabras vacías, así como la medición de frecuencia de palabras. Antes del reconocimiento de entidades nombradas es importante hacer una segmentación de oraciones, segmentación de palabras, análisis lexicográfico (lematización), etiquetado gramatical, análisis sintáctico ( _parsing_ ). En la <u>tabla 8</u> se describe detalladamente el volumen del corpus así como las tareas para la consolidación del mismo y en el gráfico <u>3 se describen las fases y tareas llevadas a cabo en el preprocesamiento.</u>

**Tabla 8**

_Tareas y datos de preprocesamiento_

|**Fase**|**Tarea**|**Descripción**|
|---|---|---|
||Conversión de PDF a texto<br>plano|Conversión a texto plano usando<br>la codificación UTF-8 mediante<br>algoritmo de Python|
|Limpieza básica|Remoción de caracteres<br>especiales|Se remueven caracteres que no<br>aportan a la interpretabilidad del<br>texto (&,!,@,+,*,etc.)|
||Remoción de salto de línea|Se eliminan los saltos de línea de<br>modo que se puedan procesar<br>párrafos completos|
|Transformación|Tokenización|Tokenizado<br>de<br>las<br>diferentes<br>oraciones dentro de las fuentes<br>textuales<br>y<br>detección<br>de<br>las<br>palabras más frecuentes dentro de<br>las mismas|
||Tamaño del corpus|3971 archivos en texto plano|
|Volumetría|Total fuentes|36 instituciones|
||Total de_tokens_|102.490.302|


------------------------- PAGINA 145 --------------------------

## **Gráfico 3**

_Fases y datos sobre el preprocesamiento_


------------------------- PAGINA 146 --------------------------

Los textos que componen el corpus atienden a una variabilidad tanto desde los géneros textuales como desde las temáticas y los propósitos comunicativos que se establecen en cada caso. Se considera información importante porque se recogen los discursos de organizaciones en torno a distintos aspectos del conflicto, por lo que se consideran textos de especialidad con una terminología particular.

En cuanto a los aspectos éticos y jurídicos del corpus, puede decirse que este corpus es recopilado para entrenar un modelo de extracción de entidades nombradas y no será difundido para otros propósitos. Las fuentes de los textos están bien especificadas y todas corresponden a recursos que se encuentran libremente para consulta desde los sitios de internet de las organizaciones. Para más datos, ver <u>anexo 2 donde se relacionan</u> los textos que integran el corpus.

A partir de estos datos, se presentan retos en al menos dos direcciones: una técnica o de procesamiento que implica definir las herramientas, técnicas y tareas para extracción, manipulación, gestión y almacenamiento de los datos. Otra de orden conceptual que implica tanto la comprensión del dominio como la definición de los mecanismos mediante los cuales integrar una conceptualización en las tareas de extracción y clasificación automática.

# **8.3. Características lingüísticas del corpus**

Los géneros discursivos tienen estructura, semántica y contexto y están delimitados según el objetivo o la intencionalidad comunicativa, el contexto, la comunidad discursiva y las formas estereotipadas o patrones característicos. También se pueden identificar niveles o planos discursivos según sean los textos para intercambio y organización, o reflejen actos de habla o acción.

Estas consideraciones son necesarias para comprender la parte discursiva de los textos, dado que:

la producción y comprensión [de conocimiento] dependen crucialmente de varias clases de conocimiento especializado de sus participantes. Esto es más obvio en el uso de la terminología técnica, pero también se extiende a


------------------------- PAGINA 147 --------------------------

muchos otros aspectos del discurso especializado, como sus temas preferidos, formatos generales o esquemas de texto, estilo, retórica (incluyendo sus metáforas típicas), patrones de argumentación, métodos de prueba y demostración, el uso de tablas, figuras y otros aspectos no verbales del discurso (Van Dijk, 2011, p. 23).

La conformación de este corpus pasa por comprender esos aspectos discursivos de los textos que se seleccionan y analizan en los cuales entender los tipos de palabras que pueden encontrarse en relación con aspectos conceptuales específicos del dominio en cuestión.

Como se dijo antes, este corpus se entiende desde dos visiones: una, relacionada con lo netamente terminológico en donde se encuentran unidades léxicas y fraseológicas prototípicas y aparecen palabras como _detención arbitraria_ , _reclamante de tierra_ o _ejecución extrajudicial_ ; y, por otro lado, se encuentran las palabras que vienen a conformar más ampliamente un discurso natural y que se encuentran inmersas en estructuras lingüísticas diversas pero cuyo valor semántico se activa en función de qué otras palabras acompañan a las primeras. En el <u>gráfico 4</u> se representan algunos ejemplos de fragmentos usados para el entrenamiento y para la identificación de entidades.

Pensar el lenguaje dentro de un dominio de conocimiento implica reconocer cuál es el valor terminológico que adquieren las palabras del lenguaje natural según los contextos en los que se encuentran y poder establecer los mecanismos mediante los cuáles hacer extracción y gestión de terminología, especialmente en ámbitos que involucren el análisis computacional del lenguaje. De acuerdo con Nazar,

la estrategia de extracción de términos consiste en asignar a una palabra o una secuencia de palabras un valor de ‘terminologicidad’ basado en su rareza. La rareza de un término está dada por una frecuencia de aparición relativamente alta en el corpus de especialidad (2011, p. 50).

El tipo de unidades léxicas y fraseológicas que aparecen en los recursos terminológicos tienen un propósito de representación de contenido y en la mayoría de los casos


------------------------- PAGINA 148 --------------------------

corresponden a conceptos claramente definidos; las entidades, por su parte, aparecen tanto como denominaciones concretas como a partir de palabras de la lengua general cuyo valor semántico es activado en función del contexto.

## **Gráfico 4**

_Ejemplos de fragmentos del corpus_

La terminologicidad de un término requiere un análisis cuantitativo de los contextos de aparición de las palabras, que puede ser un criterio para determinar el valor terminológico que adquieren las palabras del lenguaje natural según los contextos en los que estas se encuentran.

Aparecen en el corpus palabras de uso toponímico que son utilizadas para designar un poblado, un río o un área geográfica y que integran una clase concreta, la geográfica ( **GEO** ). Se encuentra información relacionada con hechos de violencia ( **VIO** ) que está compuesta tanto por el nombre de la acción o el delito propiamente dicho como por una


------------------------- PAGINA 149 --------------------------

serie de elementos que dan cuenta del tipo, dónde, cuándo, quiénes, efectos, entre otros. En la tabla 9 se presentan algunos ejemplos de estas estructuras que se encuentran en los textos.

## **Tabla 9**

_Ejemplos de entidades por clase con estructura sintáctica_

|**Clase**|**Ejemplo**|**Estructura sintáctica**<br>**prototípica**|
|---|---|---|
|GEO|Alto Ariari<br>El Espinal<br>Río Guayabero|Nombre común<br>Nombre propio|
|PER|Campesino<br>Sildano Morales<br>Excombatiente<br>Menores de edad|Nombre común<br>Nombre propio|
|AFE|Desarraigo<br>Despojo<br>Herida|Nombre común|
|VIO|Allanamiento<br>Ejecución extrajudicial<br>Secuestro|Nombre común|
|ORG|Agencia Colombiana para la<br>Reintegración<br>Ruta Pacífica de las Mujeres<br>Fenalco<br>Alianza Democrática M-19|Nombre propio|

Reflexionar sobre estas cuestiones gramaticales tiene importancia para responder a cuestiones como:

¿Cuál es la terminología –vocabulario y relaciones– que puede intervenir en la comprensión de las cuestiones o conceptos que nos ocupan? ¿Cuál es la «gramática» para relacionar esta terminología con la lógica que necesitamos para aumentar nuestra comprensión del dominio? ¿Cómo dividimos y organizamos estos conceptos? Es decir, ¿cómo categorizamos


------------------------- PAGINA 150 --------------------------

nuestro dominio? ¿Cómo combinamos estos elementos en afirmaciones y enunciados para, a continuación, comprobar su veracidad y exactitud? A través de esta gramática, en el contexto de la representación del conocimiento, ¿podemos maximizar las características estructurales de nuestro objeto de investigación útiles para los aprendices automáticos? (Bergman, 2018, p. 129).

Responder a estas cuestiones es fundamental para la conceptualización de un dominio y para definir los mecanismos mediante los cuales se puedan automatizar tareas de reconocimiento de entidades dentro de un dominio de especialidad como este.

Bergman explica algunas formas de representación del conocimiento a partir de la identificación de la gramática de ese conocimiento. Dice que las cosas relevantes son enunciadas a partir de sustantivos como _sobreviviente_ , _agresión_ , _líder_ . Luego, esas cosas entran en relación con las demás y aparecen entonces los verbos como _desplazar_ , _mutilar_ , _reparar_ ; y después, una combinación de afirmación sobre las cosas y sus relaciones, en donde se añaden otras estructuras sintácticas como los adjetivos, que darían cuenta de las propiedades de las cosas y las relaciones, en expresiones como _agresión física_ , _secuestro extorsivo_ , _atención psicológica_ .

Puede observarse así la diversidad lingüística presente en el corpus y la necesidad de analizar esas características formales que implican muchas veces de manera implícita los sentidos del lenguaje en los textos.


------------------------- PAGINA 151 --------------------------

# **Capítulo 9. Modelo para clasificación a partir del reconocimiento de entidades nombradas sobre conflicto armado**

En este capítulo se indican las técnicas, el proceso de anotación, el entrenamiento del corpus, las métricas y resultados, así como los ajustes a los parámetros que fueron requeridos en cada fase para la construcción del modelo, según distintas condiciones técnicas, lingüísticas y conceptuales, tanto del corpus como del dominio mismo.

Primero se explica el proceso de clasificación a partir de entidades en el corpus y se relacionan algunos modelos de lenguaje y el sistema de entidades definido. Posteriormente se presenta una relación entre el corpus que posee ejemplos de la lengua natural y las terminologías que sirvieron de referente para definir las clases de entidades que se identifican en el corpus. Por último, se describen los resultados de la extracción y las métricas correspondientes.

# **9.1. Generalidades para la conformación de un modelo**

Para la anotación de un corpus se deben seleccionar muestras que incluyan variedad de textos y que sean representativos del dominio, tal como se explicó en el apartado anterior. Este corpus se divide en una parte para el aprendizaje y otra como corpus de prueba, además de ejemplos sin anotar que puedan ser clasificados posteriormente por el algoritmo para validar su eficacia y precisión en el reconocimiento y asignación a una clase.

El proceso de reconocimiento de entidades nombradas implica resolver el asunto de las correferencias a partir de los siguientes pasos: primero, identificar las menciones propiamente dichas y establecer a cuáles clases pertenecen. Esta cuestión de las clases implicó una serie de decisiones y reflexiones metodológicas en todo momento.

La unidad básica de procesamiento en tareas de procesamiento de lenguaje natural es el _token_ (palabra entre espacios en blanco), sin embargo en la mayoría de los casos una entidad está constituida por dos o más _tokens_ que la representan íntegramente (sintagmas). Si entendemos las entidades como una manera de representar


------------------------- PAGINA 152 --------------------------

conceptualmente objetos de la realidad, esto se complejiza porque esa representación conlleva al uso de varios _tokens_ que corresponden a una estructura sintáctica determinada, pero que un proceso automatizado tendrá que identificar para poder validar cuándo una cadena de caracteres que conforman un conjunto de _tokens_ pueden considerarse efectivamente entidades.

Para resolver esto se entrena un modelo para la identificación de las entidades en el que se puedan juntar, por un lado, la tarea de reconocer entidades según modelos de lenguaje establecidos y, por otro, la tarea de vincular terminología propia del dominio, que parte de una conceptualización que se ha sistematizado a partir de las fuentes terminológicas y conceptuales sobre el conflicto armado.

Fueron identificadas inicialmente quince clases, de las cuales algunas corresponden a clases ya definidas en los modelos de lenguaje, como **GEO** (localización geográfica), **DATE** (fechas y tiempo), **PER** (persona), **ORG** (organización); pero se definieron como clases para este caso otras que se consideran relevantes para describir aspectos específicos del dominio, como son **VIO** (hecho de violencia), **AFE** (afectación) o **ARM** (actor armado). Se describen estas particulares para comprender cuáles son las variaciones sintácticas que se presentan en los textos y la contrastación entre las que serían denominaciones conceptuales y propiamente terminológicas y la manera como éstas aparecen en el lenguaje natural o en el corpus. Aquí se presentaron distintos desafíos de orden lingüístico y conceptual que fue necesario ir afinando a medida que se avanzaba en la optimización del algoritmo de clasificación con NER.

A partir del uso de modelos de lenguaje se incluye el reconocimiento de entidades nombradas de carácter general. Con la incorporación de otros ejemplos con clases del dominio particular, se busca una cobertura más amplia para identificar entidades propias de este ámbito. La vinculación de una terminología propia se realiza a partir de un proceso de etiquetación de ejemplos que nutran el modelo y que sirvan como entrenamiento para el aprendizaje.

La construcción de un modelo de reconocimiento de entidades nombradas debe incluir ejemplos anotados correctamente. Los modelos no aprenden todo, es un proceso de


------------------------- PAGINA 153 --------------------------

constante revisión y ajuste, por lo cual los esquemas de _labels_ o etiquetas deben ser consistentes y no demasiado específicos, pues esto tendería a atomizar tanto la información que luego los resultados serían inexactos y el modelo ineficiente.

El entrenamiento manual implica, por un lado, la conceptualización, es decir establecer qué clases y qué tipos de entidades serán reconocidas; y por otro lado la anotación que implica la segmentación dentro del conjunto de textos para distinguir los _tokens_ que son entidades y los que no lo son, y a cuáles clases pertenecen estas entidades. Luego, se usa esta estructura para anotar y para validar el funcionamiento del modelo.

Lo que se sugiere es entonces escoger entidades que estén reflejadas en el contexto local del texto, el cual es elegido a partir de criterios de segmentación usando técnicas de _parsing_ para establecer la unidad mayor de división en el texto. En este caso se trabajó a partir de oraciones completas dentro de las cuales se etiquetaron las entidades según el formato BIO ( _Beginning, Inside, Outside_ ). Cada _token_ debe ser parte de una entidad y debe indicarse a qué parte de la estructura corresponde para lo cual se usa un estándar de etiquetación mediante el cual se establece cuál es el _token_ inicial (B), el o los _tokens_ que contiene esa entidad (I) y distinguir de los que no tienen ningún valor semántico (O). En la <u>tabla 10 se muestran ejemplos de anotaciones.</u>


------------------------- PAGINA 154 --------------------------

## **Tabla 10**

_Ejemplos de anotación_

El entrenamiento también debe contemplar otros _tokens_ que no son entidades para poder distinguir una cosa de otra y aprender sobre las características que tienen las palabras cuando corresponden a entidades y cuando no. De ese modo el modelo estará preparado para reconocer nuevas entidades que no se han indicado previamente en contextos similares, lo que es justamente una de las virtudes de la utilización del aprendizaje de máquina y el uso de redes neuronales.

Definir este modelo implica responder sobre una serie de cuestiones de orden teórico y práctico: una es sobre cómo se reconoce una estructura sintáctica para hacer anotación semiautomática, cómo se pueden integrar otros corpus, lexicones y terminologías en el procesamiento dado que muchas de las entidades es posible que puedan ser identificadas y reconocidas por otros modelos o lenguajes o que incluso existan ya en otros recursos. Esto implica, entre otras cuestiones, entrenar la máquina para identificar los elementos


------------------------- PAGINA 155 --------------------------

que necesitamos que entienda y darle detallada instrucción sobre los pasos a seguir si encuentra una u otra entidad.

Todas estas cuestiones son tenidas en cuenta según la forma del corpus y los elementos que se quieren observar y cuáles son las categorías a partir de las cuales se establece la organización y representación de los datos. Por tanto, todo depende de muchos factores y requiere una revisión cuidadosa de aspectos conceptuales del dominio y lingüísticos según la naturaleza misma de los textos.

# **9.2. Clasificación de entidades a partir del corpus**

El reconocimiento de entidades nombradas en un corpus de conflictos armados implica el uso de herramientas y técnicas que permitan identificar y clasificar las menciones de personas, lugares y organizaciones que son relevantes para el contexto del conflicto. De acuerdo con Lane _et al.,_

una frase típica puede contener varias entidades con nombre de varios tipos, como entidades geográficas, organizaciones, personas, entidades políticas, tiempos (incluyendo fechas), artefactos, eventos y fenómenos naturales. Y una oración puede contener varias relaciones entre las entidades nombradas en la oración (2019, p. 340).

Goyal (2021) plantea que las entidades pueden ser organizaciones, cantidades, valores monetarios, porcentajes, nombres de personas, nombres de empresas, ubicaciones geográficas (tanto físicas como políticas), nombres de productos, fechas y horas, nombres de acontecimientos. Estas pueden reconocerse como cosas del mundo real que bien se encuentran para este dominio y para cualquier otro.

Dentro de las tareas de clasificación para el entrenamiento del modelo, se deben asignar las características y cualidades a las clases, que distinguen una de otra. Ello requiere estudiar los significados y usos posibles de las palabras por medio de _word embeddings_ , entendida como una técnica de procesamiento de lenguaje natural para representar las palabras como vectores de números, los cuales capturan la relación semántica entre las


------------------------- PAGINA 156 --------------------------

palabras. Esta técnica permite además el uso de _Word Sense Disambiguation_ para determinar el significado de una palabra específica en un contexto dado.

Un modelo de lenguaje es útil porque contiene datos que ya han sido entrenados en los cuales se identifican ya las estructuras sintácticas y gramaticales del lenguaje, que es una tarea básica para poder analizar y reconocer otros elementos relacionados con la semántica. Para este caso, se recogen muestras de textos del discurso específico y se usan modelos de lenguaje para el español. Estos datos, sin embargo, y como fue descrito en el apartado anterior, son cuidadosamente seleccionados y anotados para poder reconocer las particularidades de este discurso.

El uso de estos modelos de lenguaje es aplicable en la resolución de problemas en distintos ámbitos como la educación, la medicina, las finanzas o el servicio al cliente. Para problemas más concretos, se recurre al enfoque de ajuste fino o _fine-tuning_ , el cual se usa para entrenar un modelo con datos particulares, es decir que incorporen vocabularios específicos y muestras de texto también acotadas. _Fine-tuning_ también es utilizado para ajustar un clasificador en los datos específicos de la tarea para un tratamiento por capas. Entrenar un modelo de lenguaje en un corpus grande y luego ajustarlo en una tarea posterior más pequeña es el enfoque central utilizado en modelos basados en _transformers_ y modelos como BERT, GPT, RoBERTa y otros (Raschka, 2023).

_Fine-tuning_ es una técnica para entrenar modelos basados en redes neuronales cuando no se dispone de una gran cantidad de datos preentrenados, como sí puede ser el caso de otros trabajos de dominios de conocimiento que usan datos que ya han sido entrenados y anotados anteriormente, y cuyo volumen y validación también es significativo. _Fine-tuning_ trabaja a partir de redes neuronales que son arquitecturas que sirven para extraer y aprender directamente desde los datos que son proporcionados a partir del reconocimiento de patrones. Se requiere un conjunto de datos específicos y una muestra de datos anotados que sirvan al modelo como ejemplo de lo que debería reconocer en su análisis automático.


------------------------- PAGINA 157 --------------------------

En este caso, fueron anotados manualmente unos 90.000 _tokens_ indicando a cuál de las clases definidas pertenecían cada uno. Como se mencionó antes, la anotación se realiza usando el formato BIO, el cual es usado para etiquetar _tokens_ en la tarea de segmentación para el reconocimiento de una entidad nombrada de tal modo que se pueda indicar el _token_ de inicio y aquellos que son dependientes o hacen parte y que conforman el nombre de entidades e instancias en más de una palabra (sintagmas o frases). En la <u>tabla 11</u> se describen todas las clases y etiquetas inicialmente definidas para la anotación de los datos.

Inicialmente los nombres de las etiquetas tienen una codificación estándar de acuerdo con modelos ya establecidos. Se usaron los _labels_ **PER** (persona), **ORG** (organización), **GEO** (localización geográfica) **, DATE** (fecha) y **EVE** (evento) ya estandarizados tanto para el español como para otros idiomas desde los modelos de lenguaje. Para este caso, fueron adicionados los _labels_ **ARM** (actor armado), **AFE** (afectación), **LEY** (legislación), **VIO** (hecho de violencia), **LR** (lucha y resistencia), **MEM** (memoria), **ATE** (atención), **CON** (conceptos), **PAZ** (iniciativas de paz) y **DER** (derechos), que corresponden a elementos concretos del dominio. Estas etiquetas fueron utilizadas para la codificación inicial.

Sin embargo, dada la dispersión de los datos se optó por dejar como clases definitivas para la experimentación **ORG** (organización), **PER** (persona) y **GEO** (localización geográfica), que son comunes en modelos de lenguaje establecidos; y **VIO** (hecho de violencia), **ARM** (actor armado) y **AFE** (afectación), como clases específicas para este dominio, que sirven tanto para la clasificación de información sobre conflicto armado colombiano, pero que puede ser extrapolable a otras tareas de clasificación de información de otros conflictos.

La anotación con estas etiquetas se realiza para el conjunto de los datos que corresponden al _dataset_ , es decir, se toman ejemplos del corpus que recogen muestras del uso del lenguaje en textos propios de este dominio de conocimiento.

Para montar el modelo, se hace una selección de los datos para construir dos archivos: uno para el entrenamiento y otro para testeo. El entrenamiento está constituido por casi


------------------------- PAGINA 158 --------------------------

90.000 _tokens_ anotados en los cuales se encuentran 3.760 entidades identificadas. El testeo está conformado por más de 29.000 _tokens_ anotados en los cuales se encuentran 1.162 entidades anotadas.

Estos datos se crean a partir del método basado en reglas para generar un conjunto de datos de entrenamiento básico que sirve para definir patrones, que pueden ser cadena y _token._ Cadena cuando son _tokens_ que conforman una frase o sintagma y _token_ cuando son una sola palabra. Luego, estos datos se llevan a un formato que pueda procesarse dentro del algoritmo y se construye el sistema de clasificación a partir de los _labels_ establecidos. Después se entrena el modelo, tarea que se realiza de acuerdo a los hiperparámetros definidos y se obtienen los resultados que se explican a continuación.

**Tabla 11**

_Clases y labels para anotación_

|**Nombre**|**Label**|**Nombre**|**Label**|
|---|---|---|---|
|Sin valor<br>semántico|O|Ley|B-ley<br>I-ley|
|**Persona**|**B-per**<br>**I-per**|Fecha|B-date<br>I-date|
|**Organización**|**B-org**<br>**I-org**|Luchas y resistencias|B-luc<br>I-luc|
|**Localización**|**B-geo**<br>**I-geo**|Memoria|B-mem<br>I-mem|
|**Actor armado**|**B-arm**<br>**I-arm**|Atención|B-ate<br>I-ate|
|**Afectación**|**B-afe**<br>**I-afe**|Conceptos|B-con<br>I-con|
|**Hecho de**<br>**violencia**|**B-vio**<br>**I-vio**|Paz|B-paz<br>I-paz|
|Evento|B-eve<br>I-eve|Derechos humanos|B-der<br>I-der|


------------------------- PAGINA 159 --------------------------

# **9.3. Extracción y resultados**

La evaluación de un modelo de reconocimiento de entidades nombradas es una tarea crítica en el procesamiento de lenguaje natural puesto que implica la identificación y extracción en un texto distinguiendo las que son personas, lugares, organizaciones o fechas, que están predefinidas ya en modelos de lenguaje; pero también reconocer otras que en este ejercicio particular fueron anotadas para distinguir elementos que en el dominio son importantes como hechos de violencia, afectaciones o actores armados, por ejemplo.

La evaluación implica validar un modelo en términos de su contenido, convergencia, usuarios y conclusiones. “La validez de contenido evalúa el grado en que las unidades experimentales reflejan y representan los elementos del dominio estudiado” (Marrero _et. al._ , 2013, p. 9) y esto en función de los usuarios y sus necesidades específicas para la cual se han de determinar qué categorías deberán reconocerse.

La validez externa podría ser valorada en función del tamaño del corpus y la heterogeneidad de los textos que lo conforman. Se “evalúa hasta qué punto los resultados de un experimento pueden generalizarse a otras poblaciones y entornos experimentales” (Marrero _et al.,_ 2013, p. 10), lo cual permite extrapolar esas categorías o bien a otros dominios o bien para resolver otras necesidades de usuarios específicos que quieran representar y clasificar información sobre conflictos armados.

La validez de convergencia “evalúa en qué medida los resultados de un experimento están de acuerdo con otros resultados, teóricos o experimentales, con los que deben relacionarse” (Marrero _et al_ ., 2013, p. 10). Para ello es importante establecer un mecanismo de comparación entre anotadores, sean humanos o automáticos, para validar que se haga de una correspondencia semántica en la selección y recuperación de entidades.

Para evaluar el rendimiento de un modelo de NER es común utilizar medidas de evaluación como la precisión, el _recall_ y la puntuación _F1_ . La precisión mide la fracción de las entidades identificadas por el modelo que son correctas, mientras que el


------------------------- PAGINA 160 --------------------------

_recall_ mide la fracción de las entidades presentes en el texto que el modelo fue capaz de identificar. La puntuación _F1_ combina la precisión y el _recall_ en una sola medida que proporciona una evaluación más completa del rendimiento del modelo.

En cuanto a los datos de entrenamiento, es importante tener una muestra diversa y representativa de textos que cubran una variedad del dominio con sus respectivos contextos y que incluyan una amplia gama de entidades con nombre. Para etiquetar los datos de entrenamiento, se pueden utilizar herramientas de anotación manual o semi-automática, y se deben seguir las directrices y estándares de etiquetado establecidos para NER. En este caso y como se ha descrito reiteradamente a lo largo de la tesis, se efectúa una anotación manual y se hace una selección de textos más cuidada. De este proceso se genera una guía de anotación que puede ser útil para trabajos similares y que se puede consultar en el anexo 3.

Es importante destacar que la calidad de los datos de entrenamiento es esencial para el rendimiento de un modelo de NER. Si los datos de entrenamiento no son adecuados, el modelo puede tener dificultades para generalizar a textos nuevos y desconocidos, lo que puede resultar en una precisión y un _recall_ bajos. Por lo tanto, es importante asegurarse de que los datos de entrenamiento sean lo más representativos y de alta calidad posible.

Una de las dificultades encontrada al construir este modelo es que las métricas no eran óptimas pues se presentaba una gran dispersión de los datos, por lo que fue necesario acotar y dejar las clases que arriba se mencionaron. A continuación se presentan algunas de las consideraciones que se tuvieron para hacer los ajustes del modelo, en aspectos que van desde el proceso mismo de anotación, pasando por asuntos más conceptuales, hasta las mismas métricas y validación.

Cuando las entidades son más denominativas y representan lo que se entendería como un término propiamente dicho, el modelo puede predecir mejor; pero cuando las entidades corresponden a palabras del léxico común es más difícil identificar que estas pertenecen a una clase determinada. Esto demanda que haya una buena cantidad de ejemplos anotados que permitan distinguir y reconocer los patrones que faciliten la predicción.


------------------------- PAGINA 161 --------------------------

En el proceso de anotación se usan los ejemplos tomados del corpus, pero por otro lado se crean también unos diccionarios en donde se listan entidades ya identificadas y que se corresponden a una de las clases definidas como hechos de violencia o actores armados. Se encuentran por ejemplo, unidades como _abuso de menores_ , _abusos contra pueblos indígenas_ , que podrían considerarse conceptos y que fueron etiquetados usando los mismos _labels_ de las clases definidas. Contar con un diccionario es interesante porque permite ampliar las posibilidades del modelo a partir de recursos léxicos constituidos. Por ejemplo, puede ser que entre los ejemplos anotados no aparezca _allanamiento masivo,_ pero que en los diccionarios sí aparezca dado que se considera un término.

La anotación requiere que haya consistencia, sin embargo esto no es siempre sencillo dada la ambigüedad semántica o el significado relativo que pueden adquirir las palabras según el contexto de aparición. Por ejemplo, un _token_ solo como _desplazamiento_ , puede referirse tanto a la clase **VIO** (hecho de violencia) como **AFE** (afectación).

Algunas consideraciones particulares sobre las clases se muestran a continuación:

Las afectaciones tienen muchas maneras sintácticamente de nombrarse por lo que su identificación no es sencilla. A veces son sentimientos, daños o impactos, representados en palabras del léxico común pero en el contexto de este corpus estas unidades adquieren un valor terminológico, pues se refiere con ellas a consecuencias concretas para una población que demanda incluso el estudio de casos particulares contribuyendo así a la aparición de textos y terminologías específicas; o incluso a la creación de políticas públicas para atención de poblaciones determinadas, lo cual es un ejemplo de la generación de nuevo conocimiento y el consecuente crecimiento de terminología alrededor de esas afectaciones.

En la clase **AFE** aparecen, por ejemplo, muchos verbos, la mayoría de los cuales son parte del léxico común y dan cuenta de afectaciones relacionadas con lo físico, lo psicológico o lo político. Por ejemplo entidades como _atemorizaron_ o _estar arrinconado_ aparecen en combinación con un sustantivo, categoría frecuente en las clases **ORG** (organización), **PER** (persona) y **GEO** (localización geográfica).


------------------------- PAGINA 162 --------------------------

Se presenta una situación que tiene terminología propiamente dicha representada en términos como _cambios identitarios en medio del conflicto_ . Esto es un concepto que difícilmente se encontrará tal cual en los textos, a no ser que sea uno en donde conceptualmente se desarrolle este tema. Pero se encontrarán en el corpus otras expresiones relacionadas como _pérdida de identidad_ .

Hay también otras cuestiones con la subclasificación misma de las afectaciones. Cuando aparecen enumeradas cosas como _despojo_ , _humillación_ , _sin sentido_ ; hay afectaciones referidas a pérdidas materiales (como cuando se pierden casas, tierras o trabajos), pero también hay afectaciones de tipo psicológico.

Sobre la clase **PER** (persona) aparecen tanto nombres comunes como nombres propios e incluso los nombres comunes pueden hacer referencia a un aspecto que es particularmente relevante en el contexto de un corpus de este tipo. _Narcotraficante,_ por ejemplo, sería un _token_ de la clase **PER** que, a su vez, es también **ARM** (actor armado). Por otra parte, no se identificaron usando los modelos de lenguaje definidos tampoco _tokens_ como _narco_ para referirse a una persona y este sintagma aparece recurrentemente en algunos de los textos.

Cuando se habla de entidades en la clase **PER** , normalmente los modelos de lenguaje identifican nombres, algunos roles, como alguno de los atributos generales; pero cuando se habla de información de conflicto armado es importante también identificar si la persona afectada o el testimoniante pertenece a un grupo particular sea en razón de su género o de su etnia, edad, etc.

Sobre la clase **GEO** (localización geográfica) se considera interesante incorporar también diccionarios que detallen lugares más específicos como veredas, ríos, parajes. Por otra parte, en algunos casos el modelo asignó al nombre de un grupo armado la etiqueta **GEO** , lo cual hay que considerar y ajustar indicando la clase correcta correspondiente.

Luego, se hizo un proceso de validación del modelo para ver cómo predecía nuevas clases. Del corpus inicial, se tomaron algunas oraciones completas que no hubieran sido


------------------------- PAGINA 163 --------------------------

usadas ni para el entrenamiento ni para el testeo y se pasaba por el algoritmo para ver si reconocía las entidades y cómo las clasificaba.

En el <u>gráfico 5</u> se muestran algunos ejemplos y se compara la clasificación del modelo _vs._ la clasificación humana para comparar exactitud. En la mayoría de los casos funciona bien, pero en otros se equivoca como cuando asigna **GEO** (localización geográfica) a lo que sería en realidad un **ARM** (actor armado). Se presentan también errores aún más delicados como cuando aparece _orientación sexual_ como **AFE** (afectación) o _servidores públicos_ y _empresarios agrícolas_ como **ARM** (actores armados), sintagmas que por supuesto no fueron anotados de esta manera en el testeo ni corresponden a la verdad.

También llama la atención que clasifique en **PER** (personas) algunos nombres propios y otros no, o que devuelva la etiqueta **GEO** (localización geográfica) sin _tokens_ . Por otro lado, sorprende también que haya identificado como **AFE** (afectación) la expresión _ruptura de la armonía_ , cuando esta no se le había dado como ejemplo y en este caso sí que hay una predicción correcta.

A manera de conclusión, se encuentra que, para las entidades el criterio del modelo es relativamente bueno para encontrar entidades como **PER** (persona), **ORG** (organización), **ARM** (actor armado) y **VIO** (hecho de violencia). Sin embargo, a la hora de buscar **AFE** (afectación) esta clase no se presenta de manera tan clara como una entidad por las razones que se explicaron antes.

En la <u>tabla 12,</u> se presenta una revisión de la clasificación que hace el modelo de las entidades identificadas, separando cada _token_ para analizar en qué otros contextos se encuentra.


------------------------- PAGINA 164 --------------------------

## **Gráfico 5**

## _Ejemplos de clasificación y corrección_


------------------------- PAGINA 165 --------------------------

## **Tabla 12**

_Ejemplos de tokens y clasificación por entidades_

|**Tokens por**<br>**entidades**|**Etiqueta**|**Revisión**|
|---|---|---|
|Enfrentamiento<br>militar|VIO|***enfrentamiento**catalogado como O 1 vez en ‘_enfrentamiento entre las bandas_’<br>***militar**catalogado como O 2 veces en_‘operación militar’_,_‘confrontación militar’_|
|Toma de pueblos|VIO|***toma**no encontrado.<br>***pueblos**con otro contexto.|
|perder la vida|AFE|***pérdida**catalogado como AFE 2 veces en_‘pérdida de incidencia política’_,_‘pérdida de sus compañeros’_<br>* **vida** catalogado como O 8 veces en _‘saber de la vida de ellos_’, _‘mejorar la vida de’_, _‘cobra vida en’_, _‘la_<br>_integración, la vida y’_,_‘hablan de la vida’_,_‘es nuestra vida misma’_,_‘su trabajo y su vida’_,_‘el adulto muere en vida’_<br>***vida**catalogado como VIO 1 vez en_‘derecho a la vida’_<br>***vidas**catalogado como O 2 veces en [‘’]|
|desplazamiento<br>forzado|AFE|***desplazamiento**catalogado como PAZ 1 vez en_‘restitución y retorno de víctimas de desplazamiento’_<br>***desplazamiento**catalogado como VIO 1 vez en_‘el desplazamiento forzado’_<br>***desplazamientos**catalogado como VIO 1 vez en_‘los desplazamientos con cifras’_<br>***forzado**catalogado como VIO 2 veces en_‘desplazamiento forzado’_,_‘el abandono forzado’_<br>***forzados**catalogado como O 1 vez en_‘los trabajos agrícolasforzados’_|
|amenazas|AFE|* **amenazas** catalogado como VIO 5 veces en _‘las frecuentes amenazas de muerte’_, _‘había recibido amenazas’_,<br>_‘enfrentamos las amenazas’_,_‘han recibido amenazas directas’_,_‘o amenazas de lesionar’_|
|prejuicio|AFE|* **prejuicio**catalogado como O 1 vez en_‘porprejuicio no se dio lugar a investigación’_|


------------------------- PAGINA 166 --------------------------

|**Tokens por entidades **|**Etiqueta**|**Revisión**|
|---|---|---|
|orientación sexual|AFE?|***orientación**catalogado como O 2 veces en_‘diversidad de edad y orientación’_,_‘orientación de la secretaría’_<br>***sexual**catalogado como O 1 vez en_‘violencia sexual’_<br>***sexual**catalogado como VIO 11 vez en_‘violencia sexual’_|
|víctimas|PER|* **víctima** catalogado como O 3 veces en _‘y tampoco la víctima’_, _‘expropia a la víctima’_,_‘una mujer víctima de_<br>_violencia sexual’_<br>* **víctimas** catalogado como O 8 veces en _‘participación de las víctimas en el proceso’, ‘justicia para las_<br>_víctimas’, ‘mujeres víctimas de violencia sexual’, ‘reparaciones a las víctimas’, ‘acompañamiento a las_<br>_víctimas’, ‘salud de las víctimas’, ‘la verdad a las víctimas’, ‘acompañar a las víctimas’_<br>* **víctimas** catalogado como PER 7 vez en_‘las víctimas de violaciones’, ‘la selección de las víctimas’, ‘los foros_<br>_de víctimas’, ‘concenso entre víctimas’, ‘intentaron mostrar víctimas de ejecuciones’, ‘las víctimas del_<br>_genocidio’, ‘las víctimas que se encuentran afectadas’_<br>* **víctimas** catalogado como PAZ 2 veces en _‘Reparación de las víctimas y restitución de tierras’, ‘retorno de_<br>_víctimas’_|
|servidores públicos|ARM?|**servidores**no se encontró<br>* **públicos** catalogado como O 4 veces en _‘hicieron públicos los acuerdos’, ‘servicios públicos’, ‘comentarios_<br>_públicos’, ‘defensores públicos’_<br>***públicos**catalogado como PER 1 vez en_‘defensores públicos’_<br>***público**catalogado como O 3 veces en_‘orden público’, ‘el público se comprometa’, ‘espacio público’_|
|despojo|AFE|* **despojo** catalogado como VIO 3 veces en_‘afectadas por el despojo’, ‘el problema del despojo’, ‘despojo para_<br>_las mujeres’_|
|impunidad|AFE|***impunidad**catalogado como O 1 vez en_‘la impunidad conexa deben ser abandonadas’_<br>***impunes**catalogado como O 1 vez en_‘hechosquepermanecen impunes’_|
|reclutamiento|VIO|***reclutamiento**catalogado como VIO 1 vez en [‘reclutamiento de niños’]|


------------------------- PAGINA 167 --------------------------

En cuanto a las métricas, el mejor _score_ es de 64 %, lo cual se considera un buen desempeño. Algunos modelos, especialmente para lengua inglesa, tienen un desempeño por encima del 90 %. En modelos para español, el rendimiento puede llegar al 80 %. Sin embargo este número se considera relativo según la tarea que el modelo esté realizando. Lo ideal sería que el rendimiento de un modelo llegue mínimo a un 75 %, pero se considera aceptable si se logra más de 50 %.

Los datos consolidados del modelo estable son: 658 oraciones y 14.485 _tokens._ La distribución es de 2.037 _tokens_ distribuidos en seis categorías, así: **ORG** (organización) aparece 144 veces, **PER** (persona) aparece 216 veces, **GEO** (localización geográfica) aparece 154 veces, **VIO** (hecho de violencia) aparece 158 veces, **ARM** (actor armado) aparece 89 veces y **AFE** (afectación) aparece 49 veces.


------------------------- PAGINA 168 --------------------------

# **Capítulo 10. Ontología sobre el dominio de conflicto armado**

El desarrollo de una ontología es un proceso complejo y costoso desde el punto de vista técnico y conceptual. Su desarrollo implica la participación de muchas personas con conocimiento y experticia sobre diversos aspectos, tanto técnicos como conceptuales. Esta ontología ha sido estructurada a partir de lo que se ha denominado como la base conceptual que está constituida por los tesauros y otras terminologías del dominio que aportan tanto denominaciones como conceptos sobre el tema.

En este capítulo se describe el proceso de construcción de una ontología como base para la creación de un grafo de conocimiento. Para ello se explica en primer lugar el enfoque metodológico así como la clasificación que se hizo a partir de las terminologías que fueron recopiladas. Posteriormente se describe la estructura de la ontología, así como los conceptos y relaciones que la componen. Finalmente, se presentan algunas conclusiones y se describe el proceso de validación del modelo conceptual.

# **10.1. Metodología para la construcción de la ontología**

Para la formalización de una ontología, en esta tesis se usó OWL ( _Ontology Web Language)_ como lenguaje para describir formalmente la representación de conceptos a partir de una estructura de clases, sinónimos, definiciones, propiedades y relaciones. Hay varios aspectos que es necesario considerar que tienen que ver con la conversión de estructuras jerárquicas en un modelo de entidad-relación, pues entender o traducir de esa manera un dominio, permite que se pueda estructurar el conocimiento que sobre un ámbito se tiene y que esto pueda ser luego representado en lenguaje de máquina.

Para el desarrollo de esta ontología se incorporan metodologías ágiles que permiten trabajar con pocas reglas, generalmente fáciles de seguir. Para la construcción de esta ontología se optó por la metodología LOT ( _Linked Open Terms_ ) propuesta por el _Ontology Engineering Group_ de la Universidad Politécnica de Madrid. Esta metodología plantea como flujo de trabajo la especificación de requisitos y preguntas de competencia con casos de uso de una ontología, así como las estructuras de intercambio de datos y elicitación de conocimiento; y, posteriormente, la implementación, 167


------------------------- PAGINA 169 --------------------------

publicación y mantenimiento. La metodología LOT plantea que los roles requeridos en la construcción de la ontología son el experto en el dominio, el desarrollador, el ontólogo y el usuario de la ontología.

Como se ha mencionado antes, la construcción de esta ontología tiene dos fuentes de datos: una conceptual y otra directamente en el corpus construido. La primera se hizo a partir de la recolección de terminologías y bases conceptuales sobre el tema que tienen distintas organizaciones y archivos en el país y cuyas fuentes son ampliamente descritas en el <u>capítulo 8.</u> La segunda se hizo a partir del proceso de etiquetado y anotación para el modelo de clasificación de entidades que fue descrito en el capítulo anterior.

La ontología se construyó a partir de las dos fuentes: del corpus, con el que se han hecho las pruebas, de donde se tomaron los ejemplos para anotar; pero fundamentalmente de las terminologías. Se hizo la distribución de entidades según la clase a la que correspondía y luego se creó la ontología usando un editor de ontologías.

Una ontología es una representación de un dominio que está poblada de entidades que pueden referirse a sujetos, acontecimientos o conceptos, y de acuerdo con Bergman,

a estas cosas les asociamos relaciones internas y externas con otras cosas. Los atributos son las características intencionales de un objeto, acontecimiento, entidad, tipo (visto como instancia) o concepto. Las relaciones externas son acciones o afirmaciones entre un acontecimiento, entidad, tipo o concepto y otro particular o general (2018, p. 5).

La conceptualización de la ontología puede desarrollarse mediante diagramas en los que se identifiquen clases, propiedades y jerarquía de clases, individuos, atributos, clases y tipos de datos, jerarquía de propiedades. La ontología es útil porque permite llevar un conocimiento a un lenguaje compatible con la máquina.

La elaboración de una ontología llevaría a cabo los siguientes pasos:

1. Recopilar y preparar datos

2. Identificar términos clave

3. Crear la jerarquía de términos


------------------------- PAGINA 170 --------------------------

4. Definir las relaciones

5. Validar y refinar

Cada una de estas cuestiones demanda un trabajo más o menos manual, al menos en dominios donde no se tengan cosas tan estructuradas en forma de ontologías y conocimiento disponible anotado previamente.

De acuerdo con la metodología LOT, es importante describir los casos de uso y las preguntas de competencia de la ontología (Ver <u>tabla 13).</u> Luego se explican las clases, propiedades y atributos representados en términos generales y después los más específicos. Finalmente, se describen las limitaciones y dificultades y las líneas de trabajo futuro en la elaboración de ontologías sobre este campo.

La construcción de la ontología o base de conocimiento sobre el conflicto armado parte de la conceptualización realizada y descrita antes. De acuerdo con la metodología propuesta por Noy y Mcguinness (2001), los pasos para construir la ontología son:

1. **Considerar la reutilización de ontologías existentes.** En este punto es importante anotar que sobre este tema en concreto no se encontraron ontologías disponibles, sin embargo dado que algunos asuntos del conflicto están representados plenamente en el léxico común, es importante considerar la integración de recursos que incorporan información geográfica o de organizaciones, por ejemplo.

2. **Enumerar términos importantes en la ontología.** Este paso está siendo explicado justamente en este apartado en donde se cuenta cómo se hizo la selección de los términos, según qué fuentes y recursos y se explican las distintas versiones de clasificación de los elementos más relevantes del dominio.

3. **Definir las clases y la jerarquía de las mismas** . Aquí se describe la estructura jerárquica de las clases y las relaciones que se establecen entre ellas para indicar luego los términos e instancias que componen cada clase. Esta jerarquización está determinada según los niveles de profundidad que es posible representar en cada clase definida.


------------------------- PAGINA 171 --------------------------

## **Tabla 13**

_<mark>Especificación de requisitos y preguntas de competencia para ontología sobre conflictos armados</mark>_

|**1**<br>**Propósito**|
|---|
|La ontología sobre conflicto armado colombiano pretende servir como base de conocimiento para la extracción y clasificación<br>de entidades en textos escritos con el fin de facilitar análisis y encontrar patrones y relaciones en los textos a partir de la<br>integración con modelos de lenguaje y otras herramientas de análisis de información.|
|**2**<br>**Alcance**|
|La ontología incorpora entidades e instancias que describen eventos y hechos de violencia y los aspectos que están involucrados<br>para la comprensión del fenómeno, tales como personas, actores, acciones, información factual, así como las acciones derivadas<br>de los hechos que involucran la activación de políticas y medidas restaurativas de los derechos vulnerados, así como las acciones<br>que comunidades y personas hacen para la resistencia y la memoria.|
|**3**<br>**Lenguaje de implementación**|
|El lenguaje propuesto para la formalización de la ontología es OWL y el editor de la misma es_Protègè_.|
|**4**<br>**Usuarios finales previstos**|
|- Gestor/a de información sobre conflicto<br>- Investigador/a sobre distintos aspectos de conflicto armado<br>- Desarrollador de un sitio web con información relacionada con conflicto<br>- Analista de información sobre conflicto para toma de decisiones<br>- Gestores de memoria y defensores y promotores derechos humanos|


------------------------- PAGINA 172 --------------------------

- **6** **<mark>Requisitos de la ontología. Preguntas de competencia</mark>** - ¿Quiénes son los actores involucrados en los eventos? - ¿Qué tipos de eventos hay? - ¿Cuáles son las características de un evento para que sea tipificado como hecho de violencia, acción colectiva, estrategia de atención, acción de memoria, etcétera?

- - ¿Cuáles son las fechas en las que ocurren tanto los eventos como los hechos de violencia? - ¿Cuáles son los atributos o cualidades de las personas involucradas en cualquier tipo de evento o en un hecho de violencia? - ¿Cuáles son los tipos de personas? - ¿Cuáles son las organizaciones que aparecen y con cuáles acciones concretas están relacionadas? - ¿Qué tipos de lugares, además de los geográficos, aparecen en los textos? - ¿Cuáles son las afectaciones mencionadas en los textos y cómo se presentan? - ¿Cuáles afectaciones generan los hechos de violencia? - ¿Quiénes padecen las afectaciones? ¿Cómo enfrentan las personas las afectaciones? - ¿Cuáles son los nombres de las leyes y cuáles están relacionadas con qué tipo de actores o forma de victimización? - ¿Cuáles acciones de memoria se pueden identificar en los textos, quiénes las procuran, en dónde están? - ¿Cuáles son los actores que hacen parte de procesos de paz? - ¿Cuál es la estructura que tienen los actores armados? - ¿En dónde operan los actores? - ¿Cuál es la relación entre un hecho de violencia y un actor o actores determinados? - ¿Cuáles son las circunstancias de modo, tiempo y lugar donde ocurren los hechos de violencia? - ¿Cómo es el proceso de denuncia, quién lo instaura? - ¿Cuáles son los tipos de organización? - ¿Qué tipo de acciones se pueden relacionar con cada tipo de organización? - ¿Cuáles son las formas de lucha y resistencia que se identifican en los textos? - ¿Quiénes efectúan acciones de atención y acompañamiento y cuáles son los mecanismos? - ¿Cómo están evidenciadas las luchas por las memorias por parte de los actores?


------------------------- PAGINA 173 --------------------------

- **5** **<mark>Usos previstos</mark>** <mark>- Se pretende que la ontología sea utilizada por archivos, bibliotecas y centros de documentación que desarrollan colecciones con información relacionada con el conflicto armado.</mark>

- <mark>- También que pueda ser implementada como estructura conceptual de repositorios y páginas web de organizaciones que disponen información del conflicto.</mark>

- <mark>- Que sea usada como módulo integrado a modelos de lenguaje para el análisis de información en explotación de corpus sobre violencia.</mark>

Adaptado de (Goméz y Suárez, 2008) y (Bencharqui _et al._ , 2022)


------------------------- PAGINA 174 --------------------------

En cuanto a los datos que pueden ser reutilizables, en la <u>tabla 14</u> se encuentran las fuentes descritas que fueron identificadas como _datasets_ relacionados concretamente con la descripción y representación de conflictos armados.

La ontología sobre conflicto armado es una base de conocimiento que pretende describir semánticamente las clases relacionadas con el fenómeno con el fin de facilitar procesos de búsqueda, clasificación y extracción de información relacionada. Pretende vincular el conocimiento disponible tanto de recursos terminológicos y conceptualizaciones que se han hecho sobre el fenómeno, así como otros recursos de información que se generan sobre el dominio o relacionados con este en diferentes formatos y géneros textuales.

Esta ontología pretende ser una herramienta para facilitar el análisis de este contenido a partir de la detección automática o semiautomática de las categorías que aparecen en textos sobre conflicto armado con el fin de facilitar los procesos de investigación, estudio e incluso difusión de información sobre el conflicto. Para ello aporta la conceptualización y estructura de unas clases fundamentales en la representación del dominio.

## **Tabla 14**

_Fuentes de datos para reutilización_

|**Nombre**|**Descripción**|**Tipo de**<br>**datos**|
|---|---|---|
|_ArmedConflict_|Análisis de datos históricos de conflictos<br>armados en todo el mundo.|xlsx, csv|
|PRIOR DATS|Conjuntos de datos sobre conflictos.|xlsx, csv|
|Bases de datos ¡Basta ya!|Datos sobre categorías en el conflicto<br>entre los años 70 y 80 hasta el 2012.|xlsx, csv|
|_Empirical Studies of_<br>_Conflict Data_|Conjuntos de datos relacionados sobre<br>conflictos en el mundo.|xlsx, csv,<br>dublin core|
|_Armed Conflict Location &_<br>_Event Data Project_ (ACLED)|<sup>Datos sobre eventos.</sup>|csv|
|_Colombian conflict_|Datos vinculados en Wikidata|wikidata|


------------------------- PAGINA 175 --------------------------

# **10.2. Estructura, conceptos y relaciones**

Para la construcción de la ontología se deben considerar los aspectos terminológicos del dominio definiendo unos criterios para la selección de tesauros y otras terminologías que puedan dar validez y sustento conceptual al dominio. Ello permitirá que la identificación de conceptos se haga de manera correcta y la representación en la ontología sea lo más fiel posible a este campo de conocimiento.

Para ello se presenta una clasificación de entidades a partir de la compilación de nueve tesauros y marcos conceptuales que comprenden alrededor de 5.000 términos, categorías, conceptos y eventos de la violencia. Cada una de las clases definidas tiene cierta cantidad de términos o unidades léxicas que sirvieron de base para definir un mapa de categorías. En la <u>tabla 15</u> se muestran estas categorías, el número de términos asociados a cada una y algunos ejemplos de las palabras o términos que se encuentran.

Esta clasificación dio lugar luego a la consolidación de las entidades en donde se hizo la distinción entre instancias y términos (ver <u>gráfico 6).</u> La entidad es una palabra o conjunto de palabras que designan un objeto de la realidad, sea lugar, persona, objeto. Si bien ya hay una estructura definida para hacer la tarea de reconocimiento de entidades, para este ejercicio se hace interesante reconocer como objeto de la realidad otros asuntos como las afectaciones, las acciones de memoria o de atención, entre otros, que serían objetos de la realidad concretos de este dominio. En las instancias estarían aquellas palabras que constituyen nombres propios o comunes y que aparecen recurrentemente en los textos y relatos relacionados con el conflicto. Allí, se tienen entonces instancias como lugar o fecha. Dentro de los nombres propios están instancias como instituciones, personas, eventos, leyes.

Ahora, los términos se entienden como entidades con una significación especializada en el dominio, que a veces son propiamente términos de campos de conocimiento como _reclutamiento forzado_ o _reparación colectiva_ , o pueden ser palabras de la lengua general que dado el contexto de la oración y el texto en que se encuentran adquieren significación especializada para comprender o explicar fenómenos. Este tipo de entidades no se encuentran en un modelo de lenguaje establecido, pues son asuntos muy


------------------------- PAGINA 176 --------------------------

particulares, pero que son de gran importancia para los estudiosos de esta información y para la comunidad interesada en la comprensión también del fenómeno.

Las fuentes usadas para la construcción de la base conceptual y la definición de clases y entidades que conforman el modelo para la extracción, así como los aspectos terminológicos que son considerados para la definición de las entidades y las cualidades lingüísticas que estas tienen son aquellas terminologías (tesauros, taxonomías, marcos conceptuales) que son implementadas para describir temáticamente la información de la que disponen sitios o repositorios sobre conflicto armado, a partir de las cuales se define la estructura conceptual, así como los atributos y relaciones entre clases de modo que se definan las reglas para la identificación en los textos de las entidades.


------------------------- PAGINA 177 --------------------------

## **Tabla 15**

## _Primera clasificación de términos_

|**Clase**|**# términos**|**Ejemplos**|**Tipo unidad léxica**|
|---|---|---|---|
|Modalidades<br>de<br>victimización|301|_‘Abuso sexual’, ‘Amenaza colectiva’, ‘Retención ilegal’,_<br>_‘Secuestro extorsivo’_|Términos|
|Verbos|148|_‘incinerar’, ‘masacrar’, ‘reclutar’, ‘torturar’_|Léxico común|
|Lugares geográficos|1277|_‘Amazonía’, ‘Departamento Putumayo’, ‘Municipio Venecia -_<br>_Antioquia’, ‘Subregión Darién’_|Léxico común<br>Nombres propios|
|Lugares específicos|56|_‘Asentamiento rural’, ‘Centros de tortura’, ‘Territorios_<br>_ancestrales’, ‘Zonas de despeje’_|Léxico común|
|Actores armados|282|_‘Autodefensas de Córdoba’, ‘Bloque Capital’, ‘Ejército de_<br>_Liberación Nacional - ELN’, ‘Fuerzas Armadas_<br>_Revolucionarias de Colombia - FARC-EP’_|Nombres propios|
|Acciones militares|26|_‘Combate’, ‘Emboscada’, ‘Incursiones’, ‘Operativos_<br>_militares’_|Términos|
|Personas|178|_‘Combatientes’, ‘Jóvenes’, ‘Líderes sociales’, ‘Sindicalistas’_|Léxico común<br>Nombres propios|
|Afectaciones/Impactos/D<br>años|77|_‘Daño colectivo’, ‘Daño emocional’, ‘Impacto ambiental’,_<br>_‘Impactos en la salud’_|Léxico común<br>Términos|


------------------------- PAGINA 178 --------------------------

|**Clase**|**# términos**|**Ejemplos**|**Tipo unidad léxica**|
|---|---|---|---|
|Instituciones religiosas|11|_‘Compañía de Jesús’, ‘Iglesia Católica en Colombia’_|Nombres propios|
|Instituciones|47|_‘Centro de Estudios sobre Desarrollo Económico - CEDE’,_<br>_‘Comisión Nacional de Reparación y Reconciliación -_<br>_CNRR’, ‘Federación Nacional Sindical Agraria - FENSA’,_<br>_‘Oficina del Alto Comisionado para la Paz - OACP’_|Nombres propios|
|Instituciones<br>oficiales<br>estatales|114|_‘Cuerpo Técnico de Investigación - CTI’, ‘Defensoría del_<br>_pueblo’ ‘Dirección de Justicia Transicional’, ‘Unidad_<br>_Administrativa Especial de Gestión de Restitución de Tierras_<br>_Despojadas - UAEGRTD’_|Nombres propios|
|Instituciones<br>internacionales|48|_‘Amnistía Internacional’, ‘Humans Rights Council - HRC’,_<br>_United Nations International Children's Emergency Fund -_<br>_UNICEF’_|Nombres propios|
|Instituciones militares|178|_‘Batallón de Infantería No 32 General Pedro Justo Berrío’,_<br>_‘Escuadrones Móviles Antidisturbios - ESMAD’, ‘Fuerza_<br>_Aérea Colombiana - FAC’, ‘Unidad Policial para la_<br>_Edificación de la Paz - UNIPEP’_|Nombres propios|
|Instituciones académicas|25|_‘Instituto de Estudios Políticos y Relaciones Internacionales -_<br>_IEPRI’, ‘Instituto Pensar’ ‘Universidad de Antioquia’_<br>_‘Universidad Nacional de Colombia - UNAL’_|Nombres propios|
|Procesos y acuerdos de<br>paz|49|_‘Acuerdo sobre las víctimas’, ‘Dejación de armas’,_<br>_‘Desmovilización paramilitar’ ‘Reintegración social’_|Nombres propios<br>Términos<br>177|


------------------------- PAGINA 179 --------------------------

|**Clase**|**# términos**|**Ejemplos**|**Tipo unidad léxica**|
|---|---|---|---|
|Luchas/Resistencia|47|_‘Huelgas’, ‘Movilizaciones campesinas’, ‘Paro agrario’,_<br>_‘Resistencia’_|Léxico común<br>Términos|
|Atención a víctimas|23|_‘Acompañamiento psicosocial’, ‘Atención humanitaria’,_<br>_‘Ayuda humanitaria’, ‘Registro único de víctimas’_|Términos|
|Lugares de memoria|8|_‘Casa de Memoria La Gaitana’, ‘Casas de la memoria’,_<br>_‘Parque Monumento a las Víctimas de Trujillo’ ‘Salón del_<br>_Nunca Más’_|Nombres propios|
|Acciones de memoria|19|_‘Iniciativas de memoria’, ‘Pedagogía de la memoria’,_<br>_‘Testimonios’_|Léxico común<br>Términos|
|Instituciones de memoria|11|_‘Archivos de derechos humanos’, ‘Casas de la memoria’,_<br>_‘Museos de memoria’_|Nombres propios|
|Construcción de paz|13|_‘Cultura de paz’, ‘Educación sobre derechos humanos’,_<br>_‘Formación política’, ‘Paz territorial’_|Términos|
|Procesos de verdad|8|_‘Comisiones de la verdad’, ‘Esclarecimiento de la verdad’,_<br>_‘Verdad restaurativa’_|Nombres propios<br>Términos|
|Reparación|23|_‘Indemnización’, ‘Reparación con enfoque diferencial’,_<br>_‘Restitución de derechos’, ‘Restitución de tierras’_|Términos<br>Nombres propios|
|Términos jurídicos|411|_‘Confesión de culpabilidad’, ‘Justicia restaurativa’, ‘Medidas_<br>_de esclarecimiento’, ‘Sometimiento a la justicia’_|Términos|


------------------------- PAGINA 180 --------------------------

|**Clase**|**# términos**|**Ejemplos**|**Tipo unidad léxica**|
|---|---|---|---|
|Delitos|82|_‘Concierto para delinquir’, ‘Crimen de lesa humanidad’,_<br>_‘Explotación sexual’, ‘Tráfico de armas’_|Términos|
|Derechos|93|_‘Derecho a la libertad personal’, ‘Derechos a la verdad’,_<br>_‘Derechos colectivos de grupos étnicos’, ‘Derechos de la_<br>_víctima’_|Términos|
|Ciencia política|118|_‘Antimilitarismo’, ‘Consultas populares’, ‘Parapolítica’,_<br>_‘Plebiscito’_|Términos|
|Género|26|_‘Equidad de género’, ‘Homofobia’, ‘Población de Lesbianas,_<br>_Gays, Bisexuales, Trans e Intersexuales - LGBTI’_|Términos|

Nota: Todos los términos por clases se pueden ver en <u>anexo 6</u>


------------------------- PAGINA 181 --------------------------

## **Gráfico 6**

## _Tipologías de entidades_


------------------------- PAGINA 182 --------------------------

Como se mostró anteriormente, se puede entender un dominio de conocimiento como un área que tiene un objeto de estudio que está acompañado por teorías, métodos y preguntas que buscan la comprensión y el análisis de un fenómeno o una parte de la realidad. En este caso se entiende el conflicto armado colombiano como un campo al que han aportado otras disciplinas, pues se encuentran tanto estudios académicos en campos como la sociología, el derecho, el trabajo social, las ciencias de la información, la psicología, la memoria, etcétera; así como información que producen instituciones dedicadas a la defensa de los derechos humanos que cuentan con discursos profesionales pero también con el saber de las comunidades que se han dedicado al tema.

El conocimiento producido en este dominio puede entenderse como de especialidad, puesto que tiene una terminología propia que también es alimentada por las conceptualizaciones y denominaciones que han realizado diversas disciplinas y las mismas comunidades afectadas por el conflicto armado o que actúan por la defensa y restitución de los derechos humanos vulnerados. Estas terminologías son la base para la extracción de las clases principales que conforman la ontología o base de conocimiento del grafo.

En la <u>tabla 16</u> se describen los recursos, su alcance y propósito, el volumen, formato y lenguajes en que se encuentran, el nivel de conceptualización y la accesibilidad.

En general, estas herramientas fueron creadas con propósitos de descripción documental y para estructuración temática en los sitios web, por tanto aportan en la indización y recuperación temática a partir de las terminologías. Otras herramientas, como los marcos conceptuales del Cinep y el Museo Casa de la Memoria, actúan más como una guía que define conceptualmente aquellas cuestiones que permiten entender un fenómeno o sustentar los modos en que cada institución recopila, analiza y presenta los datos. A continuación se describen los tesauros y otras herramientas terminológicas que son la base conceptual del dominio del conflicto armado.


------------------------- PAGINA 183 --------------------------

## **Tabla 16**

## _Descripción de fuentes conceptuales_

|**Recurso**|**Alcance**|**Volumen**|**Lenguaje**|**Nivel de**<br>**conceptualización**|**Accesibilidad**|
|---|---|---|---|---|---|
|Tesauro Centro Nacional Memoria<br>Histórica|Documental|1.464 términos|HTML|Términos<br>Jerarquía|Completo en la<br>web|
|Tesauro Comisión de la Verdad|Documental|1.369 términos|SKOS<br>RDF|Términos,<br>relaciones|Completo en la<br>web|
|Tesauro Colombia Nunca Más|Documental y<br>metodológico|N/A|N/A|Conceptos y<br>relaciones|Solo estructura<br>conceptual y<br>niveles|
|Marco Conceptual Cinep|Metodológico|110 categorías|N/A|Conceptos,<br>definiciones y<br>relaciones|Texto completo|
|Categorías Sistema de Información<br>de Eventos de Violencia del<br>Conflicto Armado Colombiano del<br>Observatorio de Memoria y<br>Conflicto del CNMH|Arquitectura BD|11 categorías|N/A|Categorías y<br>definiciones sobre<br>cómo pasó, qué<br>pasó, quién es la<br>víctima, quién lo<br>hizo|Texto completo|


------------------------- PAGINA 184 --------------------------

|**Recurso**|**Alcance**|**Volumen**|**Lenguaje**|**Nivel de**<br>**conceptualización**|**Accesibilidad**|
|---|---|---|---|---|---|
|Marco conceptual del Museo Casa<br>de la Memoria|Metodológico|43 conceptos|N/A|Conceptos|Texto completo|
|Ontología basada en el sentido de<br>los verbos sobre violencia política|Descriptivo|139 verbos en<br>15 categorías|OWL|Verbos,<br>definiciones y<br>categorías|Texto completo y<br>esquema OWL|
|Tesauro Relatoría Jurisdicción<br>Especial para la Paz|Documental|1.861 términos|SKOS<br>RDF|Términos,<br>definiciones y<br>relaciones|Completo en la<br>web y descargado<br>en texto|
|Taxonomía Comisión Colombia-<br>na de Juristas|Documental|6 categorías<br>temáticas|HTML|Términos y<br>categorías|Completo en la<br>web|


------------------------- PAGINA 185 --------------------------

1. **Tesauro especializado con enfoque diferencial sobre graves violaciones a los Derechos Humanos e infracciones al Derecho Internacional Humanitario ocurridas con ocasión del conflicto armado interno** . Construido por el Archivo de los Derechos Humanos del CNMH, está dispuesto en un sitio web y ofrece una búsqueda alfabética y por palabra clave. Este vocabulario es normalizado por el Centro de Documentación y el Archivo del Centro y es utilizado para la descripción de los contenidos documentales. La búsqueda que se ofrece en la web es por términos y posee índice alfabético. Las relaciones que poseen estos términos son jerárquicas y asociativas.

2. **Tesauro Comisión para el Esclarecimiento de la Verdad.** Tiene entrada alfabética y por _Topic terms_ y posee dos grandes categorías: Núcleo y Dominio temático transversal, y también integra otros aspectos como género, lenguas, profesiones, partidos políticos, etc. Dentro de la categoría Núcleos se encuentran asuntos como Democracia y conflicto armado, Estado y sus responsabilidades en el conflicto armado, Actores armados y otros participantes en las dinámicas de la guerra, Economía y modelos de desarrollo y conflicto armado interno, etc. En cuanto al dominio temático transversal, se relacionan temas como la salud y la misión médica o los impactos. Este tesauro es fundamental en la construcción de la base de la ontología pues cada entrada de término tiene una conceptualización o descripción y algunas de ellas ofrecen descripciones de fuentes asociadas, así mismo se ofrece un glosario.

3. **Tesauro de Colombia Nunca Más.** Es un documento metodológico que sirve para la gestión de la base de datos del Proyecto Colombia Nunca Más. Este tesauro:

   - orientó la construcción de una base de datos con más de cincuenta mil registros, junto a la discusión y elaboración de una lectura del conflicto, los principios éticos políticos y otros aspectos, tanto de orden político y teórico conceptual, como metodológico (Caicedo Álvarez, 2021, p. 1).


------------------------- PAGINA 186 --------------------------

Recoge información sobre el hecho (ubicación geográfica, descripción del hecho, seguimiento al papel de los medios de comunicación, seguimiento judicial del hecho, mecanismos de impunidad, derechos de petición); datos sobre las víctimas (agresión, nombres y apellidos, vínculo con el Estado, efectos); información sobre los responsables (datos genéricos sobre las estructuras, datos sobre responsables individualizados); datos sobre las fuentes; evaluación y clasificación del hecho.

4. **Marco Conceptual de la Red Nacional de Bancos de Datos** **_._** Es una ampliación del marco conceptual propuesto por Cinep en 1995 y sirve como estructura para categorizar los hechos con ocasión de la violencia política. Está basado en marcos internacionales de derechos humanos y Derecho Internacional Humanitario y aunque no se plantea explícitamente como una herramienta terminológica, es muy importante tenerla en cuenta para la comprensión de los fenómenos y la relación que se establece con las palabras y expresiones que describen hechos victimizantes (Cinep, 2017).

5. **Categorías del Sistema de Información de Eventos de Violencia del Conflicto Armado Colombiano del Observatorio de Memoria y Conflicto del CNMH.** Recopila eventos o hechos de violencia desde 1958 registrando información sobre modo, tiempo y lugar de los hechos, responsables y víctimas del conflicto armado. Hay una información clave sobre las modalidades de violencia establecidas que corresponden a:

   - categorías conceptuales construidas a partir del estudio y el análisis del conflicto armado colombiano, y no a categorías de los derechos humanos o del Derecho Internacional Humanitario, que si bien son necesarias, resultan insuficientes para captar las particularidades de los repertorios de acción desplegados por los actores armados y las implicaciones éticas y políticas de las responsabilidades asociadas a sus acciones (Centro Nacional de Memoria Histórica. Observatorio de Memoria y Conflicto, s. f.).


------------------------- PAGINA 187 --------------------------

6. **Marco Conceptual del Museo Casa de la Memoria de Medellín.** Presentan las categorías para la conformación del museo especificando enfoques y dimensiones de la memoria que aportan material conceptual para la construcción de la base de conocimiento sobre la memoria del conflicto con impacto específico en las dinámicas urbanas de la ciudad.

7. **Ontología basada en el sentido de los verbos sobre violencia política.** Recopila verbos relativos a la violencia a partir del banco de datos del Cinep que recoge hechos de violencia y cuyo marco conceptual se refirió antes. Esta ontología está creada en lenguaje OWL y clasifica los verbos según los sentidos de cada uno y la tipología a la que corresponda (verbos que expresan estado/acción, actividad, proceso o servicio) o de acuerdo con la categoría conceptual según corresponda a violación de derechos humanos como persecución política, violación de derechos humanos como abuso de autoridad, violación de derechos humanos por intolerancia social; o violencia político-social (Tangarife _et al._ , 2014).

8. **<mark>Tesauro Relatoría</mark> JEP.** Es una herramienta para la descripción documental. Los términos incluyen relaciones jerárquicas, asociativas y de equivalencia, así como notas de alcance históricas, bibliográficas y privadas. Recoge una gran cantidad de terminología relacionada con el ámbito jurídico.

9. **<mark>Tesauro Comisión Colombiana de Juristas.</mark>** <mark>Es una taxonomía que permite describir las categorías dentro de las cuales se encuentran las publicaciones disponibles en la página. Estas categorías sirven para disponer la</mark> información de las publicaciones de la institución.

En estos tesauros y marcos conceptuales se encontraron más de 5.000 términos (ver <u>anexo 4)</u> que fueron clasificados y agrupados en distintas etapas para llegar a la definición de las clases principales que conforman la base de conocimiento. La clasificación corresponde a la distinción que se hizo en clases a partir de las terminologías. En muchos casos, por ejemplo en las clases **LEY** (legislación) o **MEM** (memoria), se está haciendo referencia a términos propiamente dichos de esta área o 186


------------------------- PAGINA 188 --------------------------

campo de los estudios sobre el conflicto, es decir se encuentran _tokens_ relacionados con una conceptualización concreta como _Sometimiento a la justicia_ o _Pedagogía de la memoria_ . En la <u>tabla 17</u> se muestra la distribución de entidades por clases de acuerdo a las terminologías.

De la clasificación descrita anteriormente, luego se afinan y definen las siguientes clases y se distinguen los términos que pertenecen a cada una, que luego fueron acotadas para efectos del experimento seleccionando solo tres específicas del dominio: **VIO** (hechos de violencia), **ARM** (actor armado) y **AFE** (afectación); y tres que son incorporadas ya en los modelos de lenguaje **ORG** (organización), **PER** (persona) y **GEO** (localización geográfica).

## **Tabla 17**

_Distribución en clases de las entidades en terminologías_

|**Clase**|**Número de**<br>**entidades**|
|---|---|
|PER|176|
|ORG|243|
|LOC|1.333|
|ARM|460|
|AFE|77|
|LAW|411|
|HV|301|
|LR|60|
|MEM|38|
|ATE|23|


------------------------- PAGINA 189 --------------------------

Las ontologías se construyen a partir de una declaración formal que describe un hecho o regla del dominio. Esta declaración sirve para definir conceptos, relaciones y propiedades. Dentro de una ontología un individuo se refiere a cualquier elemento de la realidad y está integrado por la tríada sujeto-predicado-valor. El sujeto corresponde al elemento del que se dicen cosas, el predicado sería el atributo o cualidad para describir ese elemento y el valor corresponde al dato propiamente dicho de ese elemento en relación concreta. En la <u>tabla 18</u> se muestra un ejemplo de la estructura tríadica entre sujeto, predicado y objeto.

Dentro de este dominio es importante diferenciar estos elementos por ejemplo cuando se quieren describir cualidades o cuestiones específicas de la clase **PER** (persona), que pueden ir desde objetos que describen su identificación en términos o de especificación de roles o funciones concretas. En el <u>gráfico 7</u> se ilustran algunas clases con las relaciones subordinadas que se establecen entre ellas.

## **Tabla 18**

_Ejemplos de relación sujeto, predicado y objeto_

|Estructura triada: elemento (sujeto), pr|opiedad (predicado), valor (|objeto)|
|---|---|---|
|E= Comisión para el Esclarecimiento <br>de la verdad;|P = Fecha de creación;|V = 5/5/2017|
|E= Francisco José de Roux Rengifo;|P = Fecha de nacimiento;|V = 5/7/1943|
|E= Francisco José de Roux Rengifo;|P = Ocupación;|V = Sacerdote católico|
|E= Francisco José de Roux Rengifo;|P = Ocupación;|V = Teólogo|
|E= Francisco José de Roux Rengifo;|P = Ocupación;|V = Economista|
|E= Francisco José de Roux Rengifo;|P = Ocupación;|V = Filósofo|
|E= Francisco José de Roux Rengifo;|P = Campo de trabajo;|V = Presidente CEV|


------------------------- PAGINA 190 --------------------------

## **Gráfico 7**

## _Clases en Protègè_


------------------------- PAGINA 191 --------------------------

## **Relaciones entre clases**

Aquí se describen las relaciones entre clases y se especifican qué tipos de problemas o preguntas respondería la ontología a partir de esas relaciones establecidas.

Dentro de las clases se establecen diferentes cuestiones como: la jerarquía, las anotaciones que incorporan información relacionada con la clase como etiquetas alternativas (sinónimos), definiciones (fuentes de definiciones, aclaraciones, alcance del término o la clase), comentarios.

En la ontología lo que hay son unas clases definidas y la relación entre ellas. Se presenta para algunos casos, una jerarquización según si hay elementos que pueden derivarse en otros tipos o elementos particulares. Así para la clase **AFE** (afectación) por ejemplo se especifica si esta es económica, política o sociocultural. Para otras clases, lo que hay son instancias como cuando se refiere a nombres de organizaciones, que como se dijo antes aunque no fueran estas unidades terminológicas en sentido estricto, dentro de este dominio pasan a ser una unidad que es interesante modelar en una estructura de conocimiento. En la <u>tabla 19</u> se describen propiedades de los elementos modelados en la ontología.

En algunas clases se especifican más elementos, construyendo diagramas en los que se establecen relaciones y atributos particulares de las clases. Es el caso por ejemplo, de la clase **PER** (persona) que se ilustra en el <u>gráfico 8.</u>


------------------------- PAGINA 192 --------------------------

## **Tabla 19**

_Propiedades de las clases_

|**Sujeto**|**Predicado**|**Objeto**|
|---|---|---|
|actor|participa|evento|
|actor|realiza|accion|
|actor|puede_ser|persona<br>organizacion|
|||característica|
|persona|tiene|rol_social|
|||rol_conflicto|
|rol_social|es||
|||victima|
|rol_conflicto|puede_ser|responsable|
|responsable|puede_ser|actor_armado<br>financiador|
|actor_armado|pertenece|grupo_armado|
|actor_armado|ejecuta|hecho_violencia|
|hecho_violencia|afecta|persona|
|organizacion|realiza|accion|
|||social|
|organizacion|puede_ser|estatal|
|||organizativa|
|||nombre|
|organizacion|tiene|funcion|
|||objetivo|
|hecho_violencia|genera|consecuencia|
|consecuencia|puede_ser|afectacion|
|||afectacion_psicologica<br>afectacion_fisica|
|afectacion|puede_ser|afectacion_economica|
|||afectacion_politica|


------------------------- PAGINA 193 --------------------------

|**Sujeto**|**Predicado**|**Objeto**|
|---|---|---|
|actor|participa|evento|
|||afectacion_sociocultural|
|hecho_violencia|vulnera|derecho_humano|
|derecho_humano|puede_ser|derecho_fundamental<br>derecho_soc_eco_cul|
|actor_armado|puede_ser|legal<br>ilegal|
|||hecho_violencia|
|evento|puede_ser|evento_politico|
|||evento_social|
|||nombre|
|evento|tiene|lugar|
|||fecha|
|||propósito|
|hecho_violencia|ocurre en|lugar|
|lugar|tiene|nombre<br>coordenada|
|victima|reclama|derecho|
|derecho|requiere|protección|
|organización|atiende|denuncia|
|victima|instaura|denuncia|
|||tipo_ley|
|||alcance_ley|
|ley|tiene|nombre_ley|
|||numero_ley|
|||fecha_ley|
|||nombre|
|hecho_violencia|tiene|lugar<br>fecha|
|||actor|
|~~accion~~|~~puede_ser~~|accion_violenta|


------------------------- PAGINA 194 --------------------------

|**Sujeto**|**Predicado**|**Objeto**|
|---|---|---|
|actor|participa|evento|
|||accion_colectiva|
|||accion_memoria|
|||accion_atencion|
|||lugar|
|accion_memoria|tiene|materialidad|
|||accion|
|||toponímico|
|lugar|puede_ser|genérico|
|||específico|
|||nombre|
|accion_colectiva|tiene|alcance|
|||colectivo|
|actor|participa|evento|
|víctima|requiere|atención|
|||humanitaria|
|atención|puede ser|jurídica|
|||psicosocial|
|atención|es dadapor|organización|


------------------------- PAGINA 195 --------------------------

## **Gráfico 8**

_Diagrama de la clase Persona_


------------------------- PAGINA 196 --------------------------

La ontología se piensa primero como jerarquía de clases. Por eso la ontología define unas propiedades o unas relaciones que se establecen, como se ilustra en el <u>gráfico 9.</u> Por ejemplo, se indican cuando se dice que una **organización académica** puede sufrir _amenaza_ o _allanamiento_ ; que una **afectación** es sufrida por una **persona** de tal o cual tipo. La especificidad de las relaciones que se establecen será tan rica como el dominio de conocimiento sea ampliado y descrito.

Con la ontología además es complejo porque hay varias entidades o clases que pertenecen a dominios distintos. Se encuentran términos del ámbito jurídico, de los estudios de memoria o del campo psicosocial. Se dejan entonces aquellas clases que son más fácilmente identificables como **ORG** (organización), **PER** (persona) y **GEO** (localización geográfica), que son de relativa fácil identificación usando modelos ya establecidos.

# **10.3. Validación del modelamiento conceptual**

Aquí se describen los principales resultados de esta conceptualización y se analiza el aporte de una ontología de este tipo para el estudio de los conflictos armados. También se describen cuestiones conceptuales sobre lo que se encuentra en cada una de las clases. Para empezar, es importante mencionar el aporte que otros trabajos han hecho a partir de la integración del reconocimiento de entidades nombradas y las ontologías, tanto sobre elementos teóricos y metodológicos.

En trabajos como los de Wang, K. _et al._ (2021) y Wang, X. _et al_ . (2021) se destacan problemas como la ambigüedad y la baja disponibilidad de recursos anotados previamente en campos como la química, la medicina, la farmacología. El uso de ontologías se propone principalmente para minería de datos y extracción de información en esas áreas concretas. En otro trabajo sobre el indonesio, Santoso _et al_ . (2021) proponen el reconocimiento de entidades nombradas para obtener información de textos no estructurados. Por su parte, Koho _et al_ . (2022) proponen la construcción de ontologías ligeras integrando información disponible de otros recursos de bases de datos abiertas para proporcionar opciones de búsqueda de información facetada en un recurso de información sobre testimonios de veteranos de guerra.


------------------------- PAGINA 197 --------------------------

## **Gráfico 9**

_Propiedades de los objetos_


------------------------- PAGINA 198 --------------------------

Algunas consideraciones concretas que sobre el dominio del conflicto armado se destacan en términos de la conceptualización se enuncian a continuación. Esta descripción que se presenta está relacionada con la dificultad de especificar cuándo una unidad léxica o terminológica corresponde en rigor a una clase determinada, pues según los elementos que se mencionan a continuación, en el plano del significado esto puede variar.

## **Persona (PER)**

Aparecen en esta clase tanto nombres propios como comunes, así como palabras que se refieren a roles o a situaciones o condiciones específicas de las personas que es importante destacar para reconocer tanto una atención diferenciada, la atenuación de las afectaciones o las implicaciones que tiene en un hecho de violencia concreto, por ejemplo. También vale mencionar que los roles de las personas no están indefinidamente establecidos en el tiempo y estos roles se pueden encontrar en múltiples escenarios y será importante dar cuenta de cada cuestión.

Aparecen muchas palabras de uso general para designar por ejemplo profesiones o actividades, o momentos temporales y circunstanciales de quien se habla en palabras como _acusado_ , _agente_ , _párroco_ o _niña_ , que es necesario identificar e integrar según desde qué situación se está planteando.

Sobre nombres propios, también es importante decir que se encuentra tanto nombre de pila como alias y es necesario establecer algún control de sinonimia para que cada nombre sea identificado en relación con la entidad que le corresponda y manteniendo la univocidad cuando estos nombres se refieren a un mismo sujeto en la realidad.

Aparecen también nombres genéricos para distinguir, por ejemplo, a una categoría concreta de personas, como cuando se menciona _líder indígena_ o _líder estudiantil_ para referirse individualmente, o unidades léxicas como _campesinos_ o _colectivo lesionado_ para referirse a grupos de personas específicos.


------------------------- PAGINA 199 --------------------------

## **Organización (ORG)**

Aparecen nombres propios de instituciones y organizaciones de distinto orden. Se hace necesario el tratamiento de equivalencia entre términos porque aparecen otras formas alternativas de denominación y los acrónimos de los nombres de las instituciones. También se encuentran nombres genéricos en unidades como _centros académicos internacionales_ o _centros comunitarios_ .

## **Hechos de violencia (VIO)**

Sobre esta categoría se encuentra que hay formas distintas de denominar un mismo tipo de violencia y especificaciones que correspondan a según quien las diga y cómo se clasifiquen. También aparecen palabras simples y compuestas para referir los hechos de violencia, según sea necesario ampliar o especificar ciertos elementos concretos, por ejemplo cuando se indica un tipo de agresión según a quién se ejecuta, quién la comete o con qué objetos o atenuantes específicos ocurre.

También se distinguen hechos de violencia a las personas especialmente, pero también a sitios o propiedades materiales o elementos más abstractos como el patrimonio natural o cultural o el territorio.

## **Localización geográfica (GEO)**

Sobre las categorías de lugar hay que distinguir que se tiene topónimos que corresponden a nombres propios y también unas denominaciones que se consideran nombres comunes para referirse más a tipos de lugares. Lo toponímico además hace referencia a varios niveles de localización de los lugares porque se habla tanto de departamentos o municipios como de denominaciones concretas referidas a un paraje, un río, una montaña, que pasarían por nombres comunes pero que en el contexto de un ámbito de especialidad, por ejemplo para describir un hecho de violencia o una acción de memoria concretos, se vuelven palabras relevantes que tienen una significación importante. También se presenta sinonimia en los nombres de lugares, pues en algunos


------------------------- PAGINA 200 --------------------------

casos aparecen abreviados o en la descripción misma del lugar se suelen usar distintos signos ortográficos para especificar relación o dependencia.

Es importante destacar que tanto en los relatos como en los análisis y estudios sobre fenómenos aparecen nombres propios de lugares específicos como _Palacio de Justicia_ <u>,</u> _Salón del Nunca Más_ o el nombre concreto de un resguardo indígena o de sitios de memoria.

Esta categoría tiene importancia pues aunque los sintagmas pueden entenderse como términos o instancias de la lengua general, sirven para especificar relación con elementos sobre otras categorías como **VIO** (hechos de violencia), **MEM** (memoria), o **ATE** (atención).

Algunas unidades léxicas, que si bien están compuestas por palabras de uso general, adquieren connotaciones específicas para denotar hechos de violencia o lugares donde las personas reciben atención, por ejemplo en entidades como _casas de pique,_ para referir a lo primero; o _casas de acogida,_ para lo segundo.

También es importante reconocer entidades que no hacen referencia a un lugar concreto pero sí evocan una idea de lugar o de tránsito, mostrando una relación con el espacio que sirve para ampliar o especificar cosas sobre otras categorías. Es el caso de entidades como _corredores de movilidad_ , _zonas de distensión_ o _zonas de concentración_ .

## **Actores armados (ARM)**

Aparecen palabras que pueden designar tanto a un grupo como a un individuo. La denominación tiene también variaciones sinonímicas según la variedad de nombres que se le conocen a los actores. También se presenta la cuestión de que los actores armados individuales son personas y por tanto heredan los atributos correspondientes tanto a la clase **ARM** como **PER** (persona) **,** y su significado concreto dependerá del contexto de la oración en donde se presenta la información sobre este.

En actores se encuentran tanto nombres propios de grupos o facciones concretas como comunes para referir a un tipo de actor. Por ejemplo, en la entidad _grupo armado ilegal_


------------------------- PAGINA 201 --------------------------

o _grupo paramilitar_ , que no se refiere concretamente a uno en particular sino más bien al concepto, a las dinámicas y características que tengan.

Una cuestión de importante reflexión con respecto a los actores, es establecer un límite conceptual sobre las denominaciones y los conceptos representados porque en este campo se presenta también mutabilidad de las denominaciones y definiciones. Aquí se incluyen como actores armados tanto a los grupos o facciones de grupos armados, sean legales o ilegales. Los legales son aquellos que detentan el poder armado del Estado y que corresponde a _Ejército_ , _Policía_ o _Armada_ .

Es particularmente sensible también la cualificación de actores armados como tales cuando lo que aparece son nombres propios, porque esa entidad bien puede referirse a la persona que detenta el uso de la fuerza y es actor armado, pero también se puede referir a otro momento de esa persona en el que su rol ha sido distinto.

## **Afectación (AFE)**

Esta clase se considera de gran importancia porque permite reconocer en los textos relaciones muy interesantes a nivel de las consecuencias o efectos que tienen sobre las personas los hechos de violencia. Reconocer las afectaciones permite también pensar en técnicas como el análisis de sentimientos que pueden contribuir enormemente tanto a la comprensión del fenómeno como al accionar en términos de atención y acompañamiento a las personas.

Esta clase tiene unas subdivisiones claramente identificadas que también están relacionadas con formas sintácticas concretas. Están conformadas por nombres comunes, en la mayoría de los casos verbos para referir al hecho, sustantivos para nombrar el daño y adjetivos para calificar el daño, por lo que su identificación puede llegar a no ser tan fácil y requiere de conocer sintácticamente el contexto en el cual aparecen estas palabras. Las subclases definidas para las afectaciones son: psicológicas, físicas, económicas, políticas y socioculturales.

Las afectaciones psicológicas pueden expresarse en el desencadenamiento de trastornos mentales o en la aparición de síntomas, emociones, comportamientos y sentimientos que


------------------------- PAGINA 202 --------------------------

generan sufrimiento en las víctimas. En el campo de las emociones son frecuentes las expresiones de sentimientos tales como angustia, culpa, incertidumbre, impotencia, miedo, ira y la persistencia de un duelo. Aquí aparecen entidades como _abandonó, atemorizaron, sufrimiento._

Las afectaciones físicas se relacionan con el deterioro de las condiciones de salud física que se pueden expresar en la aparición de enfermedades o el agravamiento de enfermedades pre-existentes. En esta clase se encuentran palabras para referir el daño concreto de un hecho como _amputación, degollado_ o para referir un daño posterior en entidades como _dolor, pérdida de visión._

Las afectaciones económicas se refieren al deterioro de las condiciones económicas y materiales en las cuales se sustenta la existencia, la calidad de vida y el desarrollo de los individuos, las familias y las comunidades. Se encuentra en expresiones como _abandonó su vivienda_ o _contaminación de sus aguas._ Normalmente son palabras de uso común y las entidades suelen ser expresiones complejas (frases o sintagmas).

Las afectaciones políticas son aquellas que debilitan, desestructuran o eliminan identidades políticas, expresiones de movimientos o procesos políticos que se identifican como diferentes o contrarios a los intereses del perpetrador y aparecen en términos como _confinamiento político_ o _control social._

Por último, las afectaciones socioculturales hacen referencia a los efectos de la violencia sobre el tejido social, el sistema de creencias y tradiciones de las comunidades y los elementos que se desprenden de estos como las formas de organización, la cosmovisión, los rituales y en general todo tipo de acuerdos tradicionales construidos sobre la base de la identidad cultural. Entre las afectaciones socioculturales más frecuentes en los testimonios se encuentran expresiones como _estigmatización_ , _descrédito, desestructuración de relaciones_ .


------------------------- PAGINA 203 --------------------------

# **Capítulo 11. Modelo para la construcción de un grafo de conocimiento sobre conflicto armado**

La construcción de un modelo de grafo de conocimiento que integre tanto el sistema de reconocimiento de entidades nombradas como las clases definidas en la ontología, debe incorporar información lingüística estructurada en donde estén descritos los parámetros que faciliten la vinculación con datos.

En la primera parte se plantea una reflexión sobre el uso de los grafos en la representación de información de este dominio. Luego se describe la metodología incorporada en esta tesis señalando el enfoque desde el que se aborda la construcción de un grafo. Finalmente se presenta la estructura y componentes del grafo.

Un grafo es básicamente una forma de representar conocimiento de modo que pueda recuperarse a partir de la representación conceptual de los datos. Se pueden identificar distintos tipos de grafos cuya representación y uso puede depender de la abstracción que se haga para el dominio concreto.

Para el desarrollo de este capítulo, se precisa el uso y sentido de los siguientes términos:

- Una **arista** es una relación entre dos nodos en un grafo de conocimiento. Las aristas tienen un tipo, que indica el tipo de relación, y un valor, que puede ser cualquier tipo de dato.

- Los **datos enlazados** son un conjunto de datos que están interconectados a través de enlaces RDF y que permiten representar conocimiento de forma semántica, lo que facilita su comprensión y procesamiento por máquinas.

- Un **nodo** es una representación de una entidad en un grafo de conocimiento. Puede ser una persona, un lugar, un evento, un concepto, etc. Los nodos tienen un identificador único para efectos de interoperabilidad y pueden tener atributos, que son datos adicionales sobre el nodo.

- Otro concepto que es importante, no tanto como elemento pero sí como proceso, es el **poblamiento de grafo de conocimiento** que se refiere al proceso de añadir datos a un grafo, bien sea de forma manual o automática. Hacerlo de manera manual puede ser laborioso y costoso, pero tiene la ventaja de añadir datos


------------------------- PAGINA 204 --------------------------

precisos y de alta calidad. El poblamiento automático, por su parte, es el proceso de añadir datos a un grafo utilizando herramientas y algoritmos. Este proceso puede ser más rápido y eficiente que el poblamiento manual, pero tiene la desventaja de que los datos añadidos pueden ser inexactos o de baja calidad. - Sobre estructura, también es importante explicar lo que se entiende por **tripleta RDF** , la cual se refiere a una unidad básica de información en un grafo de conocimiento compuesta por sujeto, predicado y objeto. El sujeto es un nodo, el predicado es una arista y el objeto es el valor de la arista.

Ahora bien, es importante explicar la integración del reconocimiento de entidades nombradas y la ontología con el grafo de conocimiento. Para ello se ilustra en el <u>gráfico 10</u> cómo se establece esa relación. La ontología contiene la estructura conceptual y las relaciones entre clases, y el clasificador de entidades nombradas permite encontrar léxicos en los textos que se refieren a alguna clase. Estos datos concretos contribuyen al poblamiento del grafo, el cual se entendería como la representación concreta o materialización de esa conceptualización.

# **11.1. Uso de grafos de conocimiento para representación de conocimiento sobre conflictos armados**

De acuerdo con Blumauer y Nagy (2020), el grafo es el mapeo de las relaciones entre las entidades que representan objetos del mundo, de lo cual se ha especificado antes en el modelo de NER y en la definición de las clases de la ontología. El grafo opera como una forma de establecer las conexiones que tienen los elementos que conforman un dominio y que son representados en el lenguaje.

El grafo combinaría información representada en otras estructuras como ontologías, taxonomías y redes semánticas que permiten recopilar información disponible de utilidad en este campo de conocimiento, tal como información geográfica, sobre personas, organizaciones, eventos, etc. Un grafo de conocimiento es la abstracción de un modelo de datos, el cual debe ser definido de acuerdo a los tipos de datos que sobre las clases pueda haber en el futuro. Así entonces se encuentra como tipos de grafos los siguientes:


------------------------- PAGINA 205 --------------------------

- Un **grafo multirelacional** que permite establecer claramente las relaciones entre las entidades (nodos) por medio de aristas que representan esa relación. Una ventaja de un grafo es que no importa que no se tengan todos los nodos y aristas completamente modeladas, pues se va poblando de manera incremental.

- El **grafo de propiedades** ofrece más flexibilidad para modelar relaciones más complejas y viene a complementar los grafos multirelacionales.

También se pueden distinguir tipos de grafos según el volumen de conocimiento:

- **_Graph dataset_** que se entiende como la fusión de varios grafos lo que permite actualizar o refinar datos de una fuente, así como crear _dataset_ RDF para administrar y consultar datos vinculados.

- **Grafo de conocimiento factual** que representa hechos del mundo real, por ejemplo para representar conocimiento simple como `“El presidente de Colombia es Gustavo Petro”` o más complejo como cuando se dice:

   - `Después de la masacre de sus seres queridos en las fincas Los Guáimaros y El Tapón, los días 30 y 31 de agosto de 2002, los familiares fueron testigos del olvido y el desinterés del Estado por cumplir con su obligación de garantizar justicia y verdad` .

- **Grafo de conocimiento semántico** en donde los nodos y las aristas tienen un significado definido, lo que facilita su comprensión y procesamiento por máquinas.

Como se mencionó antes, los grafos de conocimiento tienen una amplia gama de aplicaciones en dominios concretos, especialmente en tareas como:

- La **búsqueda de información** a partir de grafos de conocimiento para mejorar los resultados de búsqueda, proporcionando información adicional sobre los resultados y permitiendo realizar búsquedas más complejas.

- Los **sistemas de recomendación** se pueden utilizar para recomendar productos, servicios o información a los usuarios, basándose en sus intereses y preferencias.

- La **inteligencia artificial** usa grafos de conocimiento para entrenar modelos, proporcionando conocimiento sobre el mundo real.


------------------------- PAGINA 206 --------------------------

## **Gráfico 10**

_Relación entre categorías y componentes del modelo_


------------------------- PAGINA 207 --------------------------

Un grafo de conocimiento sobre conflictos armados puede ser muy útil para las tareas mencionadas antes, así como para proveer de herramientas semánticas a los expertos e investigadores sobre el tema que tendrán mejores herramientas para clasificación y recuperación de información a partir de ese modelado conceptual.

Con el grafo de conocimiento se busca poder encontrar y clasificar relaciones semánticas entre entidades nombradas en un texto. Un grafo de conocimiento es de gran utilidad para trabajar con datos complejos con los cuales establecer esquemas flexibles de relaciones que permitan la abstracción de los datos, es decir que permita hacer inferencias.

Entre los usos del grafo en este contexto puede destacarse la completación del grafo mismo con conocimiento más sofisticado y relevante, el reconocimiento de entidades y la extracción de relaciones.

# **11.2. Metodología para la construcción del grafo**

Blumauer y Nagy (2020) proponen unos enfoques para el desarrollo del grafo: desde el conocimiento, desde los datos y desde las entidades. Este modelo de grafo se plantea como una mezcla de estos enfoques pues por un lado se presenta de la conceptualización del dominio y se hace extracción de entidades que pueden luego ser complementadas con datos. Vale la pena distinguir entre la representación conceptual y computacional del conocimiento (gráfico <u>11),</u> pues por un lado tenemos los conceptos representados en términos y unidades de lenguaje; y por otro lado estaría la representación que de los conceptos se hace computacionalmente, convirtiendo palabras a números y vectores. En esta tesis se siguen ambos caminos y por eso el reconocimiento de la terminología es fundamental.

De acuerdo con Bergman,

las tareas críticas de cualquier instalación de un nuevo dominio son la creación del grafo de conocimiento del dominio y su poblamiento con


------------------------- PAGINA 208 --------------------------

instancias relevantes. La mayor parte del esfuerzo de implementación consiste en conceptualizar (en un grafo de conocimiento) la estructura del nuevo dominio y poblarlo con instancias (datos) (2018, p. 7).

## **Gráfico 11**

_Representación conceptual y representación computacional_

La construcción del modelo de grafo de conocimiento siguió los siguientes pasos:

1. **Definición del espacio de representación:** esto hace referencia a toda la conceptualización y contextualización del conocimiento. Aquí es donde se define la terminología del dominio que fue ampliamente explicada en los capítulos anteriores.

2. **Construcción de fuentes (** **_dataset_ ):** que se constituye tanto por el corpus en bruto para procesar como por las fuentes conceptuales para analizar la terminología. Estas fuentes conformarán luego el poblamiento para lo que se define si los recursos son estructurados o semiestructurados, qué tipos de texto se encuentran y se hace una curación del contenido para garantizar una calidad en los datos.

3. **Construcción de la ontología:** para lo cual se definen las clases, propiedades y relaciones y se crean las conexiones jerárquicas y no jerárquicas entre 207


------------------------- PAGINA 209 --------------------------

ontologías/taxonomías. En este punto se construye la estructura RDF para establecer los enlaces de relaciones, identidades, vocabulario y datos vinculados.

4. **Definición de reglas de razonamiento:** por medio de las cuales se establecen las premisas que han de tenerse en cuenta para que el modelo mantenga la coherencia entre clases y propiedades y posteriormente pueda hacer inferencias. Dentro de la definición de estas reglas se considera el desarrollo de algoritmos que pueden procesar los datos a partir de los cuales se puedan sacar conclusiones y poblar con nuevo conocimiento al grafo. También se considera en este punto, la extracción de entidades y de sus relaciones por lo cual definir unas reglas claras es fundamental. Aquí también se considera el modelo de clasificación a utilizar para modelar las relaciones. En la definiciones de estas propiedades se establecen los nodos, las etiquetas y las propiedades y se determina cuándo introducir nuevas relaciones.

5. **Modelo de pruebas e implementación:** en esta fase se presentan algunos ejemplos con las clases definidas y las instancias que fueron recopiladas de las fuentes terminológicas.

# **11.3. Estructura y componentes del grafo de conocimiento**

El grafo de conocimiento podría entenderse desde varias capas: una es la de los datos, en donde se establecen cuestiones relacionadas con el almacenamiento, la extracción y el procesamiento (limpieza y transformación para manipulación). La capa de razonamiento donde se incorpora la ontología y las reglas de inferencia que permitan deducir las relaciones entre entidades. Luego está la capa de acceso o consulta que se ocupa de definir la interfaz de acceso y visualización de los datos. La capa de infraestructura en la que se determinan los elementos de _hardware_ y _software_ que son requeridos para el funcionamiento del grafo. La capa de aplicación, que hace referencia a los usos que el grafo tendrá en vinculación con otras fuentes y recursos. Adicionalmente, habría que considerar aspectos de seguridad y ética en el tratamiento de los datos.


------------------------- PAGINA 210 --------------------------

Los elementos que componen este grafo pueden agruparse en tres grandes bloques: datos, esquema y consulta. El primero se refiere a los tipos de datos y fuentes de los mismos construidos o disponibles, el esquema hace referencia a la estructura conceptual que parte de la ontología; y el tercero, la consulta, se refiere a la manera como esta información y la relación que se establece entre ella tiene sentido para ser recuperable y usable.

## **Bloque de datos**

Los datos que se pueden añadir a un grafo de conocimiento pueden ser de diferentes tipos como:

- los **datos factuales** , aquellos que representan hechos del mundo real, como:

   - `El gobierno colombiano y las FARC firmaron un acuerdo de paz en 2016` ;

- los **datos relacionales** representan relaciones entre entidades, como:

```
Lasvíctimasdelconflictoarmadocolombianotienenderechoa
```

- `la justicia y a la reparación` ;

- y los **datos descriptivos** que sirven para especificar cualidades de las entidades, como:

`Las víctimas del conflicto armado colombiano tienen derecho a la justicia y a la reparación` .

Sobre los datos es importante anotar que para que el poblamiento de un grafo de conocimiento sea relevante, es necesario considerar la calidad de los datos, así como su coherencia y relevancia en el dominio en cuestión. Estos datos además deben contener identificadores globales/persistentes que ayuden a que sean unívocos y puedan reutilizarse en distintos esquemas conceptuales manteniendo la coherencia entre los objetos.

## **Bloque de esquema**

El esquema hace referencia a la estructura conceptual, es donde se define el significado de los términos, lo que facilita el razonamiento sobre los grafos. Esta estructura está representada en la ontología y recoge las clases, propiedades y relaciones.


------------------------- PAGINA 211 --------------------------

Este esquema a su vez está compuesto por uno semántico y uno emergente:

- El **esquema semántico** permite definir el significado de los términos de alto nivel, que son recopilados a partir del vocabulario o terminología especializada del dominio. Es un esquema predefinido que define las clases de entidades, las propiedades y las relaciones que pueden existir entre ellas. Se basa en vocabularios y ontologías existentes, como Wikidata, OWL o SKOS ( _Simple Knowledge Organization System_ ). Proporciona una estructura rígida y bien definida al grafo de conocimiento. Facilita la interoperabilidad entre diferentes grafos de conocimiento que utilizan el mismo esquema. Se construye a partir de nodos y aristas que explicitan la relación entre ellos (ver ejemplo en gráfico 12).

- El **esquema emergente** , por su parte, se desarrolla a partir de los datos que se van añadiendo al grafo de conocimiento. No se basa en vocabularios o ontologías predefinidas y, por tanto, es más flexible y adaptable a nuevos tipos de información. Se puede usar para proporcionar una descripción general comprensible, para ayudar con la definición de un esquema semántico o de validación, para optimizar la indexación y consulta del grafo, para guiar la integración de los grafos (esto para plantear fases o módulos para desarrollar varios grafos sobre conflicto). Hace referencia al poblamiento de instancias particulares que se reconocen en los textos y que deberán ser ubicadas en esa estructura conceptual.

En general, los esquemas semánticos y los esquemas emergentes son dos enfoques complementarios para la organización de la información en los grafos de conocimiento. La elección de uno u otro dependerá de las necesidades específicas del grafo y del tipo de información que se desea almacenar.

## **Bloque de consultas**

Las consultas son fundamentales en un grafo de conocimiento pues es a partir de ellas como se logra validar que el conocimiento esté bien representado y que el razonamiento que se hace sobre el mismo se corresponde con lo que es en la realidad. Para definir un sistema de consultas se deben seguir los siguientes pasos:


------------------------- PAGINA 212 --------------------------

1. **Definir el objetivo de la consulta:** se definen el tipo de preguntas como: ¿Qué información desea obtener del grafo de conocimiento?, ¿Se busca información sobre actores específicos, eventos, lugares o relaciones entre ellos?

2. **Identificar las entidades relevantes:** para ello se retoman las clases y entidades establecidas como relevantes en el grafo mediante las cuales consultar sobre personas, organizaciones, lugares, etc. Se debe utilizar el vocabulario del grafo de modo que puedan identificarse entidades correctas.

3. **Seleccionar el tipo de consulta:** se puede recuperar información referida tanto a las entidades como a las relaciones, y adicionalmente poder encontrar patrones en estos elementos.

4. **Escribir la consulta:** esta consulta está basada en el modelo de datos RDF y permite recuperar información del grafo, así como filtrar y ordenar los resultados. Esta consulta se basa en patrones de tripletas compuestas de un sujeto, predicado y objeto.

5. **Ejecutar la consulta y obtener los resultados:** validar lo que se devuelve para verificar que tanto entidades como relaciones sean correctas.

En el gráfico 13 se representa la relación entre estos bloques que componen el grafo.


------------------------- PAGINA 213 --------------------------

## **Gráfico 12**

_Ejemplo de nodos y aristas en el dominio_


------------------------- PAGINA 214 --------------------------

## **Gráfico 13**

_Relación entre bloques del grafo_

En cuanto a los componentes del grafo de conocimiento se destacan principalmente los nodos, propiedades y relaciones.

El nodo o clase es la entidad en el grafo, tiene una o más etiquetas y posee unas propiedades, tal como se ilustra en la <u>tabla 20.</u>

Los nodos representan entidades, que pueden ser cualquier objeto o concepto que pueda ser identificado. Abarcan entidades tangibles como personas, lugares u organizaciones, y entidades intangibles como colores, sentimientos o conceptos. Cada nodo tiene un identificador único y puede tener propiedades que lo describen.


------------------------- PAGINA 215 --------------------------

## **Tabla 20**

_Lista de propiedades por clase_

|**Clase**|**Propiedad**|
|---|---|
||Nombre|
||Nombre alternativo|
||Tipo|
|ORG|Dirección|
||Razón social|
||Fecha de conformación|
||Público objetivo|
||Nombre|
|PER|Rol social|
||Rol en conflicto|
||Característica sociodemográfica|
||Tipo|
||Nombre|
|ARM|Nombre alternativo|
||Fecha de conformación|
||Divisiones|
||Lugar de acción|
||Tipo de acción|
||Lugar|
|MEM|Responsable iniciativa|
||Materialidad|
||Discursos|


------------------------- PAGINA 216 --------------------------

|**Clase**|**Propiedad**|
|---|---|
||Nombre|
||Dónde (relación)|
|VIO|Cuándo (relación)|
||Derecho vulnerado|
||Responsable (presunto) (relación|
||Nombre propio|
|GEO|Nombre común|
||coordenada|
|AFE|Nombre|
||Tipo|
||Nombre|
||Número|
|LEY|Categoría normativa|
||Fecha|
||Entidad que promulga|
||Nombre|
|PAZ|Tipo de iniciativa|

## **Propiedades**

Una propiedad es una característica o atributo que describe a una entidad o a una relación entre entidades. Las propiedades permiten enriquecer la información y facilitar la comprensión y el análisis del grafo.

Las propiedades son esenciales para dar significado a las entidades y relaciones en un grafo de conocimiento. Al agregar propiedades, se puede crear una representación más completa y precisa del conflicto armado. Estas propiedades facilitan la búsqueda y 215


------------------------- PAGINA 217 --------------------------

recuperación de información y permiten analizar y describir las relaciones complejas entre los elementos. En la <u>tabla 21</u> se describen algunas propiedades por clase.

## **Relaciones**

Las relaciones o aristas conectan dos nodos y representan la relación que existe entre dos entidades. Pueden tener direcciones y etiquetas que describen la naturaleza de la relación. El conjunto de un nodo, una arista y otro nodo se denomina triple y es la unidad básica de información en un grafo de conocimiento.

Ejemplo:

- Nodo: _Fabiola Lalinde_ (entidad: **PER** ).

- Propiedad: **rol_social** : _pedagoga_ , _defensora de derechos humanos_ .

- Arista: _madre_ (relación dirigida: **PER** ).

- Nodo: _Luis Fernando Lalinde_ (entidad: **PER** ).

- Arista: _sufre_ (relación dirigida).

- Nodo: _desaparición forzada_ (entidad: **VIO** ).

- Propiedad: **fecha** : _1984._

Triple: ( _Fabiola Lalinde_ , _pedagoga y defensora de derechos humanos_ , **madre de** _Luis Fernando Lalinde_ quien **sufre** _desaparición forzada_ en _1984_ .

En la tabla 21 se presenta la relación entre los dos.


------------------------- PAGINA 218 --------------------------

## **Tabla 21**

_Relaciones entre nodos_

|**Sujeto**|**Predicado**|**Objeto**|
|---|---|---|
||participa|evento|
|**actorenconflicto**|realiza|acción|
|**__**||persona|
||puede_ser|organizacion|
|||característica|
|**persona**|tiene|rol_social|
|||rol_conflicto|
|**rol_social**|es||
|||víctima|
|**rol_conflicto**|puede_ser|responsable|
|**responsable**|puede_ser|actor_armado<br>financiador|
|**actorarmado**|pertenece|grupo_armado|
|**_**|ejecuta|hecho_violencia|
||ejecutadopor|actor_armado|
||afecta|persona|
||genera|consecuencia|
||ocurre_en|lugar|
|**hecho_violencia**||nombre|
||tiene|lugar|
|||fecha|
|||actor|
||vulnera|derecho_humano|
||realiza|accion|
||uedeser|social|
|**organizacion**|p_|estatal|
||i|nombre|
||tene|función/objetivo|


------------------------- PAGINA 219 --------------------------

|**Sujeto**|**Predicado**|**Objeto**|
|---|---|---|
|||afectacion_psicologica<br>afectacion_fisica|
|**afectacion**|puede_ser|afectacion_economica|
|||afectacion_politica|
|||afectacion_sociocultural|
|**actor_armado**|puede_ser|legal|
|||ilegal|
|||hecho_violencia|
||puede_ser|evento_politico|
|||evento_social|
|**evento**||nombre|
|||lugar|
||tiene|fecha|
|||propósito|
|||nombre|
||tiene|coordenada|
|**lugar**||toponímico|
||puede_ser|genérico|
|||específico|
||reclama|derecho|
|**víctima**|instaura|denuncia|
||requiere|atención|
|**derecho**|requiere|protección|
|**organización**|atiende|denuncia|
|||tipo_ley|
|||alcance_ley|
|**ley**|tiene|nombre_ley|
|||numero_ley|
|||fecha_ley|
|||accion_colectiva|
|**accion**|puede_ser|accion_atencion|
|||accion_memoria|


------------------------- PAGINA 220 --------------------------

|**Sujeto**|**Predicado**|**Objeto**|
|---|---|---|
|||lugar|
|**accion_memoria**|tiene|materialidad|
|||accion|
|||nombre|
|**accion_colectiva**|tiene|alcance|
|||colectivo|
|||humanitaria|
|**atención**|puede ser|jurídica|
|||psicosocial|
|**atención**|es dadapor|organización|
|**derechohumano**|uedeser|derecho_fundamental|
|**_**|p_|derecho_soc_eco_cul|

Estos componentes están relacionados en el siguiente <u>gráfico 14</u> que muestra cómo se integrarían los distintos bloques y elementos en un grafo de conocimiento.

## **Evaluación y validez de grafo**

La evaluación es un proceso importante porque permite agregar nuevas entidades y relaciones, corregir errores conceptuales, semánticos o estructurales y mejorar la estructura y organización del grafo. Este es un proceso que debe ser continuo y realizarse regularmente para garantizar actualidad y utilidad de la representación.

Los criterios propuestos por Hogan _et al._ (2021) que debe cumplir un grafo y con los cuales se deberá evaluar son: precisión (sintáctica, semántica, puntualidad con respecto a la realidad), cobertura (completitud, representatividad), coherencia (consistencia, validez), concisión (representabilidad, entendibilidad).

Para concluir, en este capítulo se hizo un recuento por los componentes de un modelo de grafo de conocimiento sobre conflictos armados, el cual permite representar y conectar información de forma flexible, facilitando la búsqueda y análisis de información.


------------------------- PAGINA 221 --------------------------

## **Gráfico 14**

_Componentes del grafo_


------------------------- PAGINA 222 --------------------------

# **Parte 3. Resultados**

# **Capítulo 12. Conclusiones**

Las conclusiones de esta tesis doctoral han sido planteadas en varios sentidos. Por un lado, una reflexión sobre la representación del conocimiento y la terminología, tanto semántica como computacionalmente, luego sobre las ontologías y grafos de conocimiento como herramientas de representación y sobre el reconocimiento de entidades nombradas como técnica para extracción de información de un corpus. También se presentan algunas conclusiones relacionadas con el proceso de entrenamiento y modelación en términos de las dificultades y retos. Por último, sobre la aplicación de técnicas de procesamiento de lenguaje natural e inteligencia artificial en dominios de conocimiento que describen o estudian fenómenos sociales, especialmente conflictos armados.

Como se explicó a lo largo de la tesis, la exploración de varias herramientas para representar conocimiento a partir del lenguaje reúne varios campos de interés. Por un lado, la terminología que aporta tanto teoría como métodos para recopilar, sistematizar y disponer conocimiento representado en forma de tesauros, glosarios y/o diccionarios especializados. Uno de los aportes de esta tesis es que se recogen esas terminologías de manera más sistemática y se plantean las bases para una estructura conceptual armonizada y consensuada, que redundará en mejores y más potentes herramientas de representación y uso de la información relacionada con el conflicto armado.

Por otro lado, se vincula también la tecnología pues la recopilación y sistematización, tanto de la terminología en el sentido más estricto como de la conceptualización en un sentido más amplio, requieren resolver asuntos como el almacenamiento, la recuperación y la consulta. A lo largo de la tesis, se ha explicado cómo la aplicación de estas técnicas tienen sentido en diferentes dominios de conocimiento, y particularmente en este pues se genera muchísima información y es un tema que requiere permanente estudio, análisis y comprensión.


------------------------- PAGINA 223 --------------------------

Tanto la conceptualización como los productos aplicados que se derivan de la tesis, permiten fortalecer el derecho de acceso a la información de formas amplias y eficaces, lo que tiene una relevancia en un escenario de transición hacia la paz y la convivencia, como el que se vive actualmente en Colombia. Si bien el propósito de dar acceso a esta información lo han llevado a cabo distintas organizaciones sociales, académicas, gubernamentales, es importante plantear un trabajo colaborativo con el concurso de más instituciones y personas en torno a herramientas más eficaces de representación.

Por otro lado, la aproximación que se ha hecho a la resolución de problemas de acceso y recuperación a la información vincula saberes propios de las ciencias de la información y de la computación. Esta tesis plantea un sistema de clases que podría ser modelado y adaptado a distintos contextos y en los cuales se propenda a fortalecer la interoperabilidad entre los datos.

Este trabajo tiene su aporte en la vinculación de varias técnicas y métodos, herramientas y conceptos que deben ser tenidas en cuenta para la conformación de una estructura de conocimiento. Por tanto, el aporte fundamental es metodológico y conceptual pues se define una estructura de conocimiento sobre el dominio y se exploran al menos tres técnicas y herramientas para efectuar la representación, que se encuentran distribuídas en varias tareas: la extracción y el reconocimiento para poder distinguir, de un conjunto de datos, aquellos que son valiosos y significativos; la formalización de conocimiento en estructuras conceptuales a partir de una ontología; y las bases para un modelo que vincule un grafo de conocimiento.

A continuación se describen las conclusiones más específicas sobre cada uno de los aspectos, tanto conceptuales como metodológicos, que se han desarrollado en la tesis.

1. En cuanto a la **representación del conocimiento y la terminología** para la construcción de esquemas como las ontologías se concluye que la multiplicidad de formas para denominar conceptos, la variabilidad textual y de niveles de abstracción, así como la naturaleza misma del significado especializado de los términos exigen un enfoque sistemático y formal de representación. La construcción de ontologías desde lo


------------------------- PAGINA 224 --------------------------

terminológico se convierte en una tarea fundamental para la extracción y representación de conocimiento, permitiendo una comunicación más precisa, eficiente y efectiva.

En las tareas de representación de conocimiento se incorporan distintas técnicas y mecanismos. En esta tesis se exploraron, por un lado, el reconocimiento de entidades que permite definir que un objeto o entidad pertenece a una clase determinada; y, por otro lado, la ontología, que se piensa primero como jerarquía de las clases, reconociendo los valores y atributos que dichas clases tienen; y el grafo de conocimiento, como la herramienta mediante la cual hacer confluir los elementos que describan un dominio y que potencien el acceso y uso del conocimiento del mismo.

2. Sobre el desarrollo de **ontologías,** se destaca que estas sirven para mejorar la precisión y la consistencia en la representación del conocimiento, facilitando la comprensión y el intercambio de información entre diferentes actores. Las ontologías permiten reducir la ambigüedad y la vaguedad en el lenguaje, evitando confusiones e interpretaciones erróneas, facilita la interoperabilidad entre sistemas de información, permitiendo la integración y el acceso eficiente a datos de diferentes fuentes, potencia el análisis y la recuperación de información posibilitando la extracción de conocimiento útil a partir de grandes cantidades de datos.

En esta tesis se buscó establecer un sistema de clases para el conflicto armado partiendo de toda la terminología y conceptualización disponible sobre el tema; sin embargo, construir una ontología con tantas clases es complejo y costoso y requiere un trabajo de equipo, entre otras cosas por la complejidad misma de la terminología que pertenece a ámbitos distintos de conocimiento. Por esa razón, si bien se definen las clases principales de la ontología, en la especificación más concreta de ellas, se incluyen sólo algunas de las clases a modo de experimentación que pueda ser extrapolable a otros contextos y ampliable para el contexto colombiano.

Otro aspecto relevante de las ontologías, que corresponde a su propósito inicial, es que estas favorecen la reutilización del conocimiento en diferentes contextos, optimizando el esfuerzo intelectual y los recursos disponibles. De esta manera se pueden aprovechar otras estructuras de conocimiento para describir dominios específicos. Es reconocer que 223


------------------------- PAGINA 225 --------------------------

existen ya estructuras y representaciones conceptuales. Sin embargo, armonizar estas estructuras es un proceso costoso en términos conceptuales y técnicos. La ontología desarrollada en esta tesis formaliza las clases principales para estructurar conocimiento relacionado con conflictos armados.

Este aspecto de conocimiento compartido requiere que se construyan y establezcan herramientas estandarizadas para el intercambio de estructuras conceptuales. Sin embargo, la reutilización de ontologías está condicionada por las particularidades propias y las necesidades concretas de los usuarios a los cuales la ontología servirá, además de las características concretas del dominio, que también varía según diversos aspectos.

El objetivo de llegar a consensos en el conocimiento demanda que cada una de las entidades y clases que se incorporan en una ontología sean correctas y correspondan a la realidad, por tanto es importante considerar el rol de profesionales de la información que, en llave con los expertos del dominio, promuevan una curaduría de la información que está directamente relacionada también con la mayor calidad de los datos contextualizados.

En cuanto al desarrollo de las ontologías se sugiere seguir un proceso que se vaya escalando pues el proceso de modelar conocimiento es complejo y costoso, por tanto ir definiendo un sistema básico de clases que luego puedan ir siendo ampliadas y ajustadas es más efectivo.

3. En cuanto al **Reconocimiento de Entidades Nombradas** , se encuentra que construir herramientas en dominios particulares demanda la existencia de buenos léxicos para la extracción de términos y estos léxicos podrían ser, bien las ontologías o bien los corpus anotados, ejemplos en dónde equipos y personas hacen el trabajo de clasificación y anotación para reconocer las entidades y que estos sean validados para garantizar que las herramientas recogen un saber consensuado.

La tarea de reconocer entidades nombradas se ve enfrentada al fenómeno de la ambigüedad semántica y, por tanto, definir criterios de desambiguación es fundamental.


------------------------- PAGINA 226 --------------------------

Incluso para ámbitos de la ciencia, en donde se pretende una univocidad y estandarización, se presentan problemas de ambigüedad descritos en áreas como las ciencias biomédicas (Wang K. _et al._ , 2021) o la química (Wang, X. _et al._ , 2021). Una de las tareas planteadas para desambiguar sentidos en el texto es identificar dónde está posicionado un concepto, lematizar con reglas y a través de _word embeddings_ reconocer cuáles de las palabras que se encuentran permitirá ayudar a predecir el sentido que esa palabra tiene y la localización en el gran mapa conceptual de su dominio.

En esta tarea se demuestra que usar modelos de lenguaje es de gran utilidad en ámbitos generales, pues ellos incorporan cierto conocimiento del mundo ya muy estandarizado como en el caso de los nombres de organizaciones, lugares o personas. Sin embargo, cuando se aplican al análisis de corpus de dominios específicos, hay una gran cantidad de conocimiento que no se encuentra aún representado. Y por tanto la inclusión de nuevas entidades de conocimientos específicos a modelos más amplios permitirán la explotación mayor de estas herramientas para favorecer ya no solo la representación sino la extracción, la clasificación y el análisis.

En la exploración de herramientas y técnicas para la clasificación a partir de NER se encontraron muchas bibliotecas, librerías y recursos, muchas de las cuales son de código abierto y adaptables a necesidades particulares, lo cual es de gran utilidad pero se reconoce también una curva de aprendizaje importante para interactuar con ellas. Otra opción que aparece en el camino es el uso de modelos de lenguaje, que también se exploraron. Se define el uso de la técnica _fine-tuning_ para construir una herramienta particular y entrenar el modelo a partir de las clases y la base conceptual definida dentro de la tesis para la modelación del dominio.

4. Sobre **grafos de conocimiento** se encuentra que si bien estos se proponen como herramientas y estructuras de conocimiento, este conocimiento no necesariamente es fijo en tanto que puede cambiar el mundo, los requerimientos, los recursos, las significaciones mismas y estos cambios afectan las inferencias que previamente haya aprendido un modelo, lo cual requeriría un rediseño. En el caso de fenómenos sociales es complejo encontrar definiciones y hasta denominaciones estandarizadas para todos


------------------------- PAGINA 227 --------------------------

los casos, pues los sentidos pueden cambiar permanentemente por una serie de matices y aspectos de la realidad que hacen difícil que la tarea de clasificar sea definitiva. Es el caso, por ejemplo, de la denominación y descripción de actores armados, que está en permanente disputa ya no solo lingüística o semántica sino política.

El uso de grafos de conocimiento busca maximizar e integrar lo que se sabe del mundo a partir de diversas fuentes y para ello se combinan técnicas de diversas áreas como las bases de datos, la lógica, el aprendizaje automático y el procesamiento del lenguaje natural, además del conocimiento específico de los dominios en los que se planteen.

Un modelo de representación de información sobre conflicto armado colombiano que contiene las entidades que son importantes para ese dominio, no solo aquellas entidades que representan a personalidades como un presidente o un comandante de un grupo paramilitar o guerrillero, sino muy especialmente a las víctimas, a los defensores de derechos humanos, que vistos técnicamente serían también una entidad pero que no necesariamente son reconocidos dentro de un modelo de lenguaje porque este no fue entrenado para ello.

Solo para ilustrar esto, por ejemplo al usar Gemini, el bot conversacional de Google basado en inteligencia artificial, se encuentra que no puede reconocer como entidad a _Fabiola Lalinde_ , reconocida líder, activista y defensora de los derechos humanos en Colombia, quien perdió a su hijo Luis Fernando en 1984, desaparecido durante años. Fabiola lideró una búsqueda por la verdad y el reconocimiento de las circunstancias de desaparición de su hijo, lo que la llevó a la investigación y documentación en un archivo que fue incluido como parte del Registro Regional del Programa Memoria del Mundo de la Unesco en 2015. Contrariamente, cuando se solicita al modelo que escriba información sobre Juan Manuel Santos, quien fue presidente de Colombia en los periodos 2010-2014 y 2014-2018 y quien firmó el Acuerdo de paz con las FARC en 2016, reconoce claramente esta entidad e incluso aporta información sobre los atributos que tiene. Y es importante, por supuesto, el reconocimiento de diversos actores, pero el de las víctimas y luchadores de derechos humanos es fundamental también, debe hacer parte del relato nacional y ser incorporados en modelos de lenguaje y herramientas de


------------------------- PAGINA 228 --------------------------

reconocimiento automático.

El esquema semántico construido sirve como base conceptual para la estructuración y poblamiento del grafo de conocimiento que representará el conflicto armado como dominio y con tantos niveles de complejidad y relacionamiento entre los elementos como sea posible entrenar.

**5. Sobre entrenamiento y modelación** es importante decir que para el proceso de anotación, que es fundamental en el entrenamiento, es necesario contar con datos válidos y de alta calidad, sin embargo es casi inevitable que haya errores o ruido en los datos. El porcentaje de datos anotados que se considera válido depende en gran medida del conjunto de datos y de las especificaciones del problema en cuestión. En general, se espera que el porcentaje de datos incorrectos o ruidosos sea lo más bajo posible.

La calidad de los datos en el proceso de entrenamiento es crucial para el rendimiento del modelo y por tanto en esta tesis se tomaron medidas para minimizar la cantidad de errores y el ruido en los datos, de modo que estos fueran lo más precisos y representativos posible. Con este propósito surge justamente la guía de anotación que, en correspondencia con la representación conceptual que del dominio se conoce y se busca en los datos, pueda servir para que equipos más amplios de expertos y anotadores permitan la validación de datos.

Las guías son fundamentales para hacer la anotación de corpus, sea cual sea el propósito. Para un buen entrenamiento, se incluyeron ejemplos distintos y variados, tanto correctos como incorrectos, de modo que el modelo pueda aprender a distinguir entre una cosa y otra y sus resultados sean mucho más eficaces.

Para modelar y entrenar se hizo un estudio minucioso de los distintos fenómenos léxicos presentes en los ejemplos, de modo que ya en la semántica computacional se consideren cuestiones como los sentidos de las palabras, las relaciones semánticas, las expresiones multipalabras, la metonimia, la metáfora, el paráfrasis, los roles semánticos, entre otros, fenómenos propios del discurso natural que es necesario entender para el


------------------------- PAGINA 229 --------------------------

establecimiento y reconocimiento posterior de patrones para el procesamiento automático.

**6. Sobre aplicación de técnicas de PLN en el estudio de fenómenos sociales** se destaca que el desarrollo de herramientas de representación y la incorporación de nuevas tecnologías para el estudio de fenómenos sociales abre muchas posibilidades. El grafo de conocimiento, por ejemplo, es útil para que los investigadores y comunidad en general puedan encontrar y extraer mejor la información relacionada con el conflicto armado. Sin embargo, hay que considerar varias cuestiones éticas y prácticas de esta labor. Entre las éticas se encuentran la protección y el tratamiento de los datos. Entre las prácticas habría que diferenciar entre técnicas y metodológicas. Las primeras hacen referencia a asuntos de procesamiento y memoria. Las metodológicas tienen que ver con la necesidad de hacer anotación sobre los datos y la dificultad operativa que eso pueda tener, además de los sesgos e imprecisiones propias de un análisis conceptual en donde se presentan distintos fenómenos.

De acuerdo a las técnicas para la construcción de grafos de conocimiento propuesto en Hogan _et. al._ (2021), un aporte interesante para este dominio de conocimiento es establecer un mapa del conocimiento disponible para cada uno de los métodos y plantear sobre cómo la recopilación y disposición de estos recursos amplían y mejoran la eficiencia de un grafo de conocimiento. Este trabajo se enmarca como aporte a otras discusiones que en el país se plantean en torno a la preservación, gestión, acceso y uso de archivos como el Legado de la Comisión de la Verdad, que dispone de un volumen grandísimo de información. Tener información adecuadamente disponible y con posibilidades de acceso contribuye a los procesos de verdad y de reconocimiento y a la visibilización y uso de los archivos y la información. Y ello contribuye a que tanto víctimas como sociedad en general puedan reconocer el daño y las afectaciones y construir una mejor convivencia y la tan anhelada y esquiva construcción de paz.


------------------------- PAGINA 230 --------------------------

# **Capítulo 13. Resultados, limitaciones y trabajo futuro**

El desarrollo de las aplicaciones de la tesis está fundamentado especialmente en lo terminológico y conceptual y en los recursos computacionales que representan esa información del dominio. Sin embargo, en el desarrollo de estas aplicaciones se presentan una serie de limitaciones a partir de las cuales pueden proyectarse algunas líneas de trabajo futuro.

# **13.1. Resultados aplicados**

En cuanto a los resultados aplicados que han sido referidos a lo largo del texto, se destacan unos conceptuales y otros más metodológicos. Los primeros se refieren a estructuras o esquemas con datos bien descritos y los metodológicos se refieren a desarrollos o herramientas en los que se fue haciendo la sistematización del modelo de clasificación NER, la ontología y el grafo. Algunos de estos recursos pueden tener alguna utilidad práctica en la extrapolación metodológica o conceptual de este trabajo en el desarrollo de otros; y están también los que corresponden a elementos ampliados en relación con el corpus y el _dataset_ construido.

## **Glosario de términos de la tesis**

El glosario de términos recoge aquellas denominaciones y descripciones de los campos de conocimiento que vincula esta tesis, los cuales refieren a conceptos, metodologías, herramientas y procedimientos que provienen del lenguaje de la computación, la lingüística, la terminología y la representación del conocimiento. La organización del glosario es alfabética y en cada entrada se indica el correspondiente en inglés o español, según el caso. Cuando el uso del término es más extendido y comprendido en su lengua original, la entrada se hace en inglés o con el nombre de la sigla que representa. También se sugieren algunas referencias a autores que explican o abordan ampliamente el tema. Este insumo es interesante para otros profesionales que se enfrenten al desarrollo de herramientas de este tipo desde distintos campos de formación, sean terminólogos, bibliotecólogos y documentalistas, ingenieros o desarrolladores. Puede consultarse en este enlace.


------------------------- PAGINA 231 --------------------------

## **Corpus sobre conflicto armado**

Para la elaboración de esta tesis se recogieron cerca de 4000 recursos a texto completo que representan una gran variabilidad del uso del lenguaje especializado en este dominio. Este conjunto de textos resulta de interés para futuros desarrollos y exploraciones de otros aspectos lingüísticos, sintácticos y semánticos. En el <u>anexo 2</u> se hace una relación de las fuentes del corpus. Para ver todos los documentos completos remitirse a la carpeta de _<u>dataset</u>_ .

## **Guía de anotación**

Esta guía define las cuestiones conceptuales y metodológicas que deben tenerse en cuenta para abordar problemas de representación de conocimiento sobre conflictos armados. Puede ser extrapolable para anotar otros recursos relacionados. Es un recurso importante para futuros desarrollos. En el <u>anexo 3</u> se detallan los criterios y consideraciones para la anotación.

## **Terminología recopilada**

La identificación y extracción de terminología proveniente de los recursos conceptuales permitió la construcción de una fuente de cerca de 5000 términos que se encuentran debidamente clasificados según las categorías que en cada caso se consideraron. Este es un gran insumo para terminólogos, documentalistas e incluso investigadores y estudiosos del tema. En el anexo 4 se presenta la lista de términos según como aparecen en las terminologías de referencia, mostrando la frecuencia de aparición de esos mismos términos en distintos recursos. Cada hoja recoge los términos de una institución particular y luego hay uno que los compila todos.

## **Algoritmos para clasificación a partir del reconocimiento de entidades nombradas**

En el proceso de experimentación de clasificación con reconocimiento de entidades se construyeron varias versiones de algoritmos. En el <u>anexo 5</u> se incluye una carpeta con tres libros de códigos y el _dataset_ que fue utilizado para el entrenamiento. Pueden evidenciarse las librerías utilizadas, las cargas de datos _train_ y _test,_ el entrenamiento y


------------------------- PAGINA 232 --------------------------

los resultados. Así mismo, estos se encuentran en _<u>Hugging Face</u>_ <u>,</u> que es un repositorio en donde se alojan versiones de código y es útil para desarrolladores.

## **Clases y entidades sobre conflicto armado**

Las clases y entidades definidas para la construcción del modelo se formalizaron en Protège, archivo que corresponde al <u>anexo 6.</u> A partir de esta estructura se construyó el _mapping_ (anexo <u>7)</u> en donde pueden visualizarse las clases y sus relaciones. Este insumo resulta de gran interés para futuros desarrollos a partir de esta conceptualización y para la ampliación con nuevas instancias.

# **13.2. Limitaciones del estudio**

1. Una de las principales dificultades para el desarrollo de modelos de lenguaje y de cualquier herramienta de representación y clasificación automática es la disponibilidad de los datos. Cuando se piensa en este tipo de trabajos que usan ontologías, se piensa en la reutilización de conocimiento ya disponible y en datos vinculados que puedan incorporarse para nuevas preguntas. Un ejemplo de esto, además de que la mayoría de conocimiento disponible se encuentra en inglés, es que en Wikidata hay más información del norte que del sur global, y eso sin contar la poca disponibilidad de conocimiento en dominios tan particulares, como se ilustró con el ejemplo anteriormente mencionado en las conclusiones sobre _Fabiola Lalinde_ . Por esta razón, trabajos en dominios concretos que puedan luego ser validados y compartidos por comunidades más amplias contribuirá a la dotación de más conocimiento disponible.

Una de las limitaciones en este sentido, fue no contar con los mecanismos adecuados para la adopción y reutilización de conocimiento ya existente, sumado a que la base conceptual viene de distintas fuentes y que la tarea de sistematización y armonización semántica y terminológica es compleja. Esta dificultad fue paliada haciendo un modelamiento escalar, en el cual se definieron primero las entidades y una vez estas estuvieron bien descritas y representadas, continuar con la extracción de las relaciones entre ellas, lo cual demanda la definición de reglas muy claras y la construcción de algoritmos que lo faciliten.


------------------------- PAGINA 233 --------------------------

La construcción de herramientas computacionales para representar conocimiento requiere de equipos humanos y técnicos altamente calificados que definan las reglas que puedan inducir a la extracción de las relaciones entre las entidades y esto, como se sabe, es un proceso altamente complejo y costoso. Por ello se plantea la necesidad de constituir estrategias para el trabajo colaborativo que vincule a instituciones y personas que puedan aportar conocimiento para la recopilación y construcción de datos anotados que permitan robustecer el entrenamiento de los modelos.

2. La ambigüedad representa una dificultad en múltiples dimensiones, tanto para el entendimiento y la comprensión entre los expertos sobre las cosas que denominan como para la pretensión de sistematizar conocimiento de manera unívoca como se espera de herramientas como una ontología, un grafo o la misma terminología de dominio. En este dominio particular de los conflictos armados se presentan muchos desafíos con relación a la ambigüedad, que deberán ser resueltos con el concurso de múltiples voces de las distintas especialidades y orillas que componen los discursos de este dominio. Desambiguar también es una tarea colectiva y, por tanto, una limitación en esta tesis es la falta suficiente y amplia de expertos que validen el conocimiento, como se da en casos de construcción de ontologías y grafos en donde intervienen equipos. Para compensarlo, es fundamental contar con un buen léxico, esencial para la extracción, tanto de entidades como de relaciones.

3. El grafo de conocimiento está compuesto tanto por los datos, la base de datos, el clasificador a partir de NER y la ontología que describe el conocimiento explícito sobre el dominio. Y ello conlleva pensar también en temas de almacenamiento, gestión, navegación y visualización, así como los algoritmos que se requieran para el funcionamiento óptimo del modelo. En este sentido, otra limitación que se plantea es técnica pues tanto el entrenamiento como el modelamiento requiere de equipos de cómputo de gran capacidad de procesamiento. Estos desarrollos requieren también el concurso de equipos amplios de profesionales que puedan encargarse del desarrollo computacional y de software para disponer de un espacio en la web en donde gestionar y disponer la información. Ello también demanda capacidad computacional tanto para el


------------------------- PAGINA 234 --------------------------

almacenamiento como para el procesamiento. La experimentación realizada en esta tesis se hizo usando los medios disponibles para la construcción del modelo.

4. La técnica de _fine-tuning_ resulta de gran utilidad para trabajar con modelos en datos no entrenados, sin embargo en el proceso se presentan errores, lo cual requiere hacer ajustes permanentemente, que demandan no solo conocimiento experto sino tareas dispendiosas o la necesidad de contar con herramientas de cómputo y de costo para anotar más fácilmente. Como se explicó antes, el entrenamiento de un modelo requiere idealmente un gran número de ejemplos anotados, lo cual como se ha explicado a lo largo del trabajo es particularmente complejo. También se requiere que haya validación cruzada, tal como se deja sugerido en la guía de anotación (ver anexo 3).

# **13.3. Líneas de trabajo futuro**

1. Para ampliar el grafo de conocimiento sobre conflicto armado, se sugiere incorporar datos vinculados para el reconocimiento de entidades. Esto bajo la misma lógica de las ontologías, aprovechando y reutilizando conocimiento sobre el mundo disponible. Sobre esto aporta un buen ejemplo el trabajo de Koho _et al._ (2022), quienes plantean la extracción de conocimiento desde Wikidata para ampliar el análisis de información sobre testimonios de veteranos finlandeses de la Segunda Guerra Mundial. Esta experiencia abre caminos de trabajo para la puesta en conversación de otro conocimiento disponible sobre el país o el conflicto en particular en relación con otra información de testimonios o memoria. Aquí se plantea la necesidad de establecer conversación con otras iniciativas de datos abiertos y de ciencia ciudadana, estrategias que permitirán ampliar la capacidad de recopilación de datos anotados y de calidad y por tanto mejorar los modelos con representaciones más certeras del dominio.

2. La adopción de una guía de anotación semántica para corpus de conflictos armados puede contribuir al desarrollo de la clasificación automática a partir de otros elementos como por ejemplo las emociones presentes en los textos y la relación con otras entidades y actores. Además, la incorporación de otros ejemplos de anotación relacionados con lenguas minorizadas, pues hay una producción significativa de


------------------------- PAGINA 235 --------------------------

información sobre comunidades indígenas, quienes han sido uno de los actores más afectados por el conflicto. Aquí se pretende una socialización y adopción de la guía por parte de organizaciones que custodian, preservan y disponen información sobre conflicto armado, tanto en el orden nacional como el Centro de Memoria Histórica y el Legado de la Comisión de la Verdad, como por distintos archivos de derechos humanos que tienen no solamente mucho que aportar en términos de conocimiento sobre el conflicto, sino también grandes dificultades para gestión, recuperación y disposición de su información.

3. La construcción de herramientas de representación de conocimiento es un proceso costoso que requiere gran calidad de corpus anotados. Una línea de trabajo interesante para alcanzar este propósito tiene que ver con la descripción colaborativa a la que podrían aportar archivistas, defensores de derechos humanos, sobrevivientes, y por supuesto expertos en el ámbito. Esto a partir de la implementación de trabajo colaborativo por medio de una plataforma de agregación y validación de las entidades y nodos establecidos que permita recoger las denominaciones y descripciones que sobre las entidades se realiza. En esta plataforma se definirían las bases para incorporar tareas como el entrenamiento de datos y la verificación humana.

4. Las personas interactúan con los grafos de conocimiento de diversas maneras, tanto explícita como implícitamente. Estas interacciones pueden ayudar a mejorar la calidad de los grafos de conocimiento, a la vez que proporcionan información valiosa sobre cómo las personas interactúan con la información. Por tanto se propone crear y enriquecer grafos de conocimiento a partir de validación cruzada y bajo métricas estandarizadas. Algunas aplicaciones que se plantean para los grafos de conocimiento tienen que ver con el aprovechamiento de información pública. En este sentido, se propone otra línea de trabajo que vincule la extracción de esta información mediante las técnicas adecuadas.

5. Algunos cuestionamientos al tratamiento de datos se dan en cuanto se evidencian herramientas informáticas cargadas de subjetividad, pues la anotación o categorización de la información muchas veces está dada por elementos subjetivos que parten de la


------------------------- PAGINA 236 --------------------------

experiencia y el conocimiento propios de los sujetos. Por tanto, el trabajo colaborativo y la validación cruzada de los datos, aportará en objetividad a la hora de entrenar herramientas de este tipo.

6. La construcción de corpus anotados con datos de calidad en dominios específicos, demanda el estudio y adopción de modelos de lenguaje ya existentes, así como el trabajo colaborativo con otros colectivos de personas que se han preocupado por la construcción y disposición de herramientas para el español. Esto demanda tanto conocimiento computacional como semántico y crítico para contrarrestar los riesgos y límites ante los que nos ponen herramientas de inteligencia artificial, que todavía presentan cosas relacionadas con sesgos, falta de empatía, limitaciones éticas.

7. La construcción de ontologías es un proceso complejo y costoso y por tanto aprovechar ya conocimiento formalizado de ese modo es de gran utilidad por tanto se sugiere la adopción de métodos para su reutilización en correspondencia con las métricas mediante las que se definen. Sin embargo, la adopción de las ontologías, que prometen ser estandarizadas para el intercambio, no siempre es tan transparente, pues el reuso se condiciona a los escenarios y contextos específicos y las particularidades propias no solo del dominio sino de las organizaciones que las adopten. En este sentido es importante definir modelos y métricas de evaluación de las ontologías a fin de establecer los modos en los cuales estas serán adoptadas. Una línea de investigación en este sentido, es definir esos criterios de reutilización de conocimiento disponible y el estudio técnico y metodológico de la interoperabilidad de los datos. Para ello, el trabajo mancomunado con profesionales de distintos campos de conocimiento es requerido.

8. Otro campo de interés viene con el desarrollo de los LLM ( _large language models_ ) que prometen grandes desarrollos a partir del uso de inteligencia artificial para el modelamiento conceptual. Sin embargo aquí es importante estudiar cómo esas nuevas entidades están siendo entendidas y cómo se puede mitigar o reducir cuestiones como los sesgos. El abordaje de este problema de investigación se plantea desde la representación de conocimiento y la exploración indaga por distintos caminos desde la programación, la terminología y la estructuración de conocimiento. Este recorrido se


------------------------- PAGINA 237 --------------------------

propone como un campo de interés para futuros investigadores, tanto para la exploración de información de otros conflictos armados como para la representación de otros dominios de conocimiento de las ciencias sociales y humanas.


------------------------- PAGINA 238 --------------------------

# **Referencias bibliográficas**

- Aguado de Cea, G., Álvarez de Mon y Rego, I. y Pareja Lora, A. (2002). Primeras aproximaciones a la anotación lingüístico-ontológica de documentos de la Web Semántica: OntoTag. _Inteligencia Artificial, Revista Iberoamericana de Inteligencia Artificial_ , (17), 37-49. <u>https://oa.upm.es/6545/1/Primeras_aproximaciones_a.pdf</u>

- Antoniou, G., Harmelen, F. (2004). Web ontology language: OWL. En: Staab, S., Studer, R. (Eds). _Handbook of ontologies_ . Springer.

- Aussenac-Gilles, N., Biebow, B., Szulman, S. (2000). Revisiting Ontology Design: A Methodology Based on Corpus Analysis. En: _Proceedings of the 12th European Workshop on Knowledge Acquisition, Modeling and Management_ . London: Springer-Verlag.

- Ayadi, A., Sameta, A., Bertrand, F., Zanni-Merk, C. (2019). Ontology population with deep learning-based NLP: a case study on the Biomolecular Network Ontology. En: _23rd International Conference on Knowledge-Based and Intelligent Information & Engineering Systems._ <u>https://doi.org/10.1016/j.rcim.2021.102281</u>

- Barrasa, J., Hodler, A., Webber, J. (2021). _Knowledge Graphs: Data in Context for Responsive Businesses_ . O’Reilly Media.

- Bencharqui, H., Haidrar, S., Anwar, A. (2022). Ontology-based Requirements Specification Process. _E3S Web of Conferences_ (351). <u>https://doi.org/10.1051/e3sconf/202235101045</u>

- Bergman, M. (2018). _A Knowledge Representation: Practionary Guidelines Based on Charles Sanders Peirce_ . Springer.

- Bernaras, A., Laresgoiti, I. (1996). Building and reusing ontologies for electrical network applications. En: Wahlster, W. (Ed.). _Proceedings 12th European Conference on Artificial Intelligence ECAI'96_ .


------------------------- PAGINA 239 --------------------------

- Blumauer, A., Nagy, H. (2020). _The knowledge graph cookbook: recipes that work_ . Monochrom.

- Brickley, D., Guha, R. (2000). _Resource Description Framework (RDF) Schema Specification 1.0. W3C._ <u>https://www.w3.org/TR/2000/CR-rdf-schema-20000327/</u>

- Buendía, M. (2010). Anotación semántica en el dominio especializado de la Meteorología. En: Caballero, R., Pinar Sanz, M. (Ed.). _Modos y formas de la comunicación humana_ (923‐934). Ediciones de la Universidad de Castilla‐La Mancha / AESLA.

- Cabré, M.T. (1993). _La terminología: teoría, metodología, aplicaciones_ . Editorial Antártida/Empúries.

- Cabré, M.T. (1999). _La terminología: representación y comunicación_ . Institut Universitari de Lingüística Aplicada.

- Caicedo-Álvarez, J.F. (2021). _Investigación en Derechos Humanos y Movimiento Social: El Proyecto Colombia Nunca Más PCNM y el Movimiento Nacional de Víctimas del Crímenes de Estado MOVICE_ .

- Centro Nacional de Memoria Histórica. Observatorio de Memoria y Conflicto. _Sistema de Información de Eventos de Violencia del Conflicto Armado Colombiano_ . <u>https://micrositios.centrodememoriahistorica.gov.co/observatorio/sievcac/</u>

- Chaudhri, V., Farquhar, A., Fikes, R., Karp, P., Rice, J. (1998). _Open Knowledge Base Connectivity 2.0.31: Proposed_ . Stanford University.

- Cinep. (2017). _Marco conceptual de la Red Nacional de bancos de datos_ . <u>https://www.nocheyniebla.org/wp-content/uploads/u1/comun/marcoteorico.pdf</u>

- Colombia. Presidencia de la República. (2017). _Decreto Ley 588 de 2017_ “Por el cual se organiza la Comisión para el Esclarecimiento de la Verdad, la Convivencia y la no Repetición”.


------------------------- PAGINA 240 --------------------------

<u>https://www.funcionpublica.gov.co/eva/gestornormativo/norma_pdf.php?i=8063 3</u>

- Comisión de la verdad. (2022). _Metodologías de análisis de entrevistas utilizando Procesamiento de Lenguaje Natural (PLN)._ <u>https://www.comisiondelaverdad.co/metodologia-procesamiento-lenguaje-natura l</u>

- Comisión de la Verdad. (2022). _Hay futuro si hay verdad: informe final. Hallazgos y recomendaciones de la Comisión de la Verdad de Colombia_ . Comisión de la verdad.

- Das, S., Katiyar, A., Passonneau, R., Zhang, R. (2021). CONTAINER: Few-Shot Named Entity Recognition via Contrastive Learning. _arXiv:2109.07589._ <u>https://doi.org/10.48550/arXiv.2109.07589</u>

- Debellis, M. (2021). _A Practical Guide to Building OWL Ontologies Using Protégé 5.5 and Plugins_ . <u>https://www.researchgate.net/publication/351037551_A_Practical_Guide_to_Bu ilding_OWL_Ontologies_Using_Protege_55_and_Plugins</u>

- Domingue, J., Motta, E., Corcho García, O. (1999). _Knowledge Modelling in WebOnto and OCML: A User Guide. There is a new OCML manual in the works_ .

- Dou, J., Qina, J., Jina, Z., Lia, Z. (2018). Knowledge graph based on domain ontology and natural language processing technology for Chinese intangible cultural heritage. _Journal of Visual Languages and Computing,_ (48), 19–28. <u>https://doi.org/10.1016/j.jvlc.2018.06.005</u>

- Eriksson, H. (2007). An Annotation Tool for Semantic Documents. En: Franconi, E., Kifer, M., May, W. (Ed). _The Semantic Web: Research and Applications. ESWC 2007. Lecture Notes in Computer Science_ (4519). Springer.


------------------------- PAGINA 241 --------------------------

- Estopà, R. (1999). _Extracció de terminologia: elements per a la construcció d’unSEACUSE(Sistema d’Extracció Automàtica de Candisats a Unitats de Significació Especialitzada)._ Universitat Pompeu Fabra.

- Fensel, D., Şimşek, U., Angele, K. Huaman, E., Kärle, E. Panasiuk, O. Toma, I. Umbrich, J., Wahler, A. (2020). _Knowledge Graphs Methodology, Tools and Selected Use Cases_ . Springer.

- Fernández, M., Gómez-Pérez, A., Juristo, N. (1997). Methontology: From Ontological Art Towards Ontological Engineering. En: _AAAI Technical Report_ .

- Fernández-López, M., Gómez-Pérez, A., Suárez-Figueroa, M. (2013). Methodological guidelines for reusing general ontologies. _Data & Knowledge Engineering_ (86), 242-275. https://doi.org/10.1016/j.datak.2013.03.006

- Fernández-Silva, S., Becerra Rojas, N. (2015). La variación terminológica en la comprensión y producción de textos académicos: Propuesta de representación en un diccionario especializado de aprendizaje de Psicología, _Ibérica_ (30), 183-208. <u>https://www.redalyc.org/pdf/2870/287042542009.pdf</u>

- Freixa, J. (2002). _La Variació terminològica: anàlisi de la variació denominativa en textos de diferent grau d'especialització de l'àrea de medi ambient_ . Universitat Pompeu Fabra.

- Freixa, J. (2005). Variación terminológica: ¿Por qué y para qué?. _Meta: journal des traducteurs / Meta: Translators' Journal_ , 50(4). <u>https://doi.org/10.7202/019917ar</u>

- Garijo, D., Poveda, M. (2020). Best Practices for Implementing FAIR Vocabularies and Ontologies on the Web. _arXiv:2003.13084._ <u>https://doi.org/10.48550/arXiv.2003.13084</u>

- Giraldo, M. (2019). _Archivos vivos: documentar los derechos humanos y la memoria en Colombia_ . Universidad Autónoma de Barcelona.


------------------------- PAGINA 242 --------------------------

- Gómez Pérez, A., Fernández López, M., Corcho, O. (2004). _Ontological engineering: with examples from the areas of knowledge management, e-Commerce and the semantic web_ . Springer.

- Gómez-Pérez, A., Suárez-Figueroa, M. (2008). _Ontology Requirements Specification_ . <u>http://neon-project.org/nw/book-chapters/Chapter-05.pdf</u>

- Goyal, C. (2021) Part 10: Step by Step Guide to Master NLP – Named Entity. _Analytics vidhya_ .

<u>https://www.analyticsvidhya.com/blog/2021/06/part-10-step-by-step-guide-to-m aster-nlp-named-entity-recognition/</u>

- Gruber, T. (1993). A Translation Approach to Portable Ontology Specifications. _Knowledge Systems Laboratory. Technical Report KSL 92-71_ . <u>https://tomgruber.org/writing/ontolingua-kaj-1993.pdf</u>

- Grüninger, M., Fox, M. (1995). Methodology for the Design and Evaluation of Ontologies. _Workshop on Basic Ontological Issues in Knowledge Sharing,_ IJCAI-95.

- Gupta, N., Singh, S., Roth, D. (2017). Entity Linking via Joint Encoding of Types, Descriptions, and Context. En: Palmer, M., Hwa, R., Riedel, S. (Ed.) _Proceedings of the 2017 Conference on Empirical Methods in Natural Language Processing_ , (pp. 2681–2690). https://aclanthology.org/D17-1284/

- He, Y., Chen, J., Antonyrajah, D., Horrocks, I. (2022). BERTMap: A BERT-based Ontology Alignment System. _arXiv:2112.02682v4._ <u>https://doi.org/10.48550/arXiv.2112.02682</u>

- Hogan, A., Blomqvist, E., Cochez, M., Amato, C., Melo, G., Gutierrez, C., Labra Gayo, J., Kirrane, S., Neumaier, S., Polleres, A., Navigli, R. Ngonga Ngomo, A., Rashid, S., Rula, A., Schmelzeisen, L., Sequeda, J., Staab, S., Zimmermann, A. (2021). Knowledge graphs. _rXiv:2003.02320v6._ <u>https://arxiv.org/abs/2003.02320</u>


------------------------- PAGINA 243 --------------------------

- Horrocks, I. (2000). _A Denotational Semantics for Standard OIL and Instance OIL. Technical report_ . University of Manchester. Department of Computer Science.

- Hu, F., Shao, Z., Ruan, T. (2014). Self-Supervised Chinese Ontology Learning from Online Encyclopedias. _The Scientific World Journal._ <u>http://dx.doi.org/10.1155/2014/848631</u>

- Ide, N., Suderman, K. (2014). The Linguistic Annotation Framework: A Standard for Annotation Interchange and Merging. _Language Resources and Evaluation,_ 48(3), 395–418. 10.1007/s10579-014-9268-1

- Ji, S., Pan, S., Cambria, E., Marttinen, P., Yu, P. (2021). A Survey on Knowledge Graphs: Representation, Acquisition and Applications. _IEEE Transactions on Neural Networks and Learning Systems_ . <u>10.1109/TNNLS.2021.3070843</u>

- <mark>Jullien, M., Valentino, M., Freitas, A. (2022). Do Transformers Encode a Foundational Ontology? Probing Abstract Classes in Natural Language.</mark> _<mark>arXiv:2201.10262.</mark>_ <u><mark>https://doi.org/10.48550/arXiv.2201.10262</mark></u>

- Jurafsky, D., Martin, J. (2019). Lexicons for sentiment, affect, and connotation. En: _Speech and language processing_ . Stanford University. <u><mark>https://web.stanford.edu/~jurafsky/slp3/old_oct19/21.pdf</mark></u>

- Jurisdicción Especial para la Paz, Comisión de la Verdad, HRDAG. (2022). _Informe metodológico del proyecto conjunto JEP-CEV-HRDAG de integración de datos y estimación estadística_ . <u>https://www.comisiondelaverdad.co/sites/default/files/descargables/2022-08/04_ Anexo_Proyecto_JEP_CEV_HRDAG_08022022.pdf</u>

- Karp, P., Chaudhri, V., Thomere, J. (2000). XOL: An XML-Based Ontology Exchange Language. <u>https://www.sri.com/wp-content/uploads/2021/12/676.pdf</u>

- Kejriwal, M., Knoblock, C., Szekely, P. (2021). _Knowledge Graphs: Fundamentals, Techniques, and Applications._ The MIT Press.


------------------------- PAGINA 244 --------------------------

- Khan, L., Luo, F. (2002). Ontology construction for information selection. _14th IEEE International Conference on Tools with Artificial Intelligence_ . <u>10.1109/TAI.2002.1180796</u>

- Kietz, J., Maedche, A., Voltz, R. (2000). Method for Semi-Automatic Ontology Acquisition from a Corporate Intranet. _Proceedings of Workshop Ontologies and Text, co-located with EKAW'2000_ .

- Kifer, M., Lausen, G., Wu, J. (1995). Logical Foundations of Object Oriented and Frame Based Languages. _Journal of the Association for Computing Machinery,_ 42(4), 741–843. https://doi.org/10.1145/210332.210335

- Kochmar, E. (2022). _Getting Started with Natural Language Processing_ . Manning.

- Koho, M., Leal, R. Ikkala, E. Tampe, M., Rantala, H., Hyvönen, E. (2022). Building Lightweight Ontologies for Faceted Search with Named Entity Recognition: Case WarMemoirSampo. _Text2KG 2022: International Workshop on Knowledge Graph Generation from Text, Co-located with the ESWC 2022_ . <u>https://ceur-ws.org/Vol-3184/TEXT2KG_Paper_2.pdf</u>

- Kulmanov, M., Zohra Smaili, F., Gao, X., Hoehndorf, R. (2021). Semantic similarity and machine learning with ontologies. _Briefings in Bioinformatics_ , 22(4), 1-18. <u>https://doi.org/10.1093/bib/bbaa199</u>

- Lamy, J.B. (2021). _Ontologies with Python: Programming OWL 2.0_ Ontologies with Python and Owlready2._ Apress.

- Lan, Z., Chen, M., Goodman, S., Gimpel, K., Sharma, P., Soricut, R. (2020). ALBERT: A Lite BERT for Self-supervised Learning of Language Representations. _arXiv:1909.11942._ <u>https://doi.org/10.48550/arXiv.1909.11942</u>

- Lane, H., Howard, C., Hapke, H. (2019). _Natural Language Processing in Action: Understanding, analyzing, and generating text with Python_ . Manning.


------------------------- PAGINA 245 --------------------------

- Lawan, A. Rakib, A. (2019). The Semantic Web Rule Language Expressiveness Extensions: A Survey. _arXiv:1903.11723._ <u>https://doi.org/10.48550/arXiv.1903.11723</u>

- Li, J., Sun, A., Han, J., Li, C. (2020). A Survey on Deep Learning for Named Entity Recognition. _arXiv:1812.09449._ <u>https://doi.org/10.48550/arXiv.1812.09449</u>

- Liang, C., Yu, Y., Jiang, H., Er, S., Wang, R., Zhao, T., Zhang, C. (2020). BOND: BERT-Assisted Open-Domain Named Entity Recognition with Distant Supervision. _arXiv:2006.15509._ <u>https://doi.org/10.48550/arXiv.2006.15509</u>

- Liu, X., Zhang, F., Hou, Z., Mian, L., Wang, Z., Zhang, J., Tang, J. (2021). Self-supervised Learning: Generative or Contrastive. _arXiv:2006.08218_ . <u>https://doi.org/10.48550/arXiv.2006.08218</u>

- Lorente, M. (2013). Terminología in vivo y variación funcional. _Ugarteburu Terminologia Jardunaldiak_ , 2-18. <u>https://www.ehu.eus/documents/2430735/2730483/LIBURUAehuei13-02.pdf</u>

- Maedche, A., Staab, S. (2000). The TEXT-TO-ONTO Ontology Learning Environment. En: _ICDM-Workshop on Integrating Data Mining and Knowledge Management_ . <u>https://www.researchgate.net/publication/2950026_The_TEXT-TO-ONTO_Onto logy_Learning_Environment</u>

- Maedche, A., Staab, S. (2004). Ontology Learning. En: Staab, S., Studer, R. (Ed.). _Handbook on Ontologies. International Handbooks on Information Systems_ . Springer. <u>https://doi.org/10.1007/978-3-540-24750-0_9</u>

- Marneffe, M.; Manning, C., Nivre, J., Zeman, D. (2021). Universal dependencies. _Computational linguistics_ , 47(2), 255-308. <u>https://doi.org/10.1162/coli_a_00402</u>

- Marrero, M., Urbano, J., Sánchez-Cuadrado, S., Morato, J., Gómez-Berbís, J. (2013).

Named Entity Recognition: Fallacies, Challenges and Opportunities. _Computer Standards & Interfaces,_ 35(5), 482-489. <u>https://doi.org/10.1016/j.csi.2012.09.004</u>


------------------------- PAGINA 246 --------------------------

- Mcguinness, D., Fikes, R. Hendler, J., Stein, L. (2002). DAML+OIL: an ontology language for the Semantic Web. _IEEE Intelligent Systems,_ 17(5), 72-80. <u>10.1109/MIS.2002.1039835</u>

- Meng, X., Ganoe, C., Sieberg, R., Cheung, Y., Hassanpour, S. (2019). Self-Supervised Contextual Language Representation of Radiology Reports to Improve the Identification of Communication Urgency. A _MIA Jt Summits Transl Sci Proc_ ., 413-421.

   - <u>https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7233055/pdf/3269396.pdf</u>

- Mizoguchi, R., Ikeda, M. (1995). Towards Ontology Engineering. En: _Technical Report AI-TR-96-1, I.S.I.R._ Osaka University.

- Molina Mejía, J. (2021). _Lingüística computacional y de corpus: teorías, métodos y aplicaciones_ . Editorial Universidad de Antioquia.

- Moreno Ortiz, A. (2008). Ontologías para la terminología: por qué, cuándo, cómo. _Revista Tradumàtica: Traducció i tecnologies de la informació y la comunicació,_ (6). https://raco.cat/index.php/Tradumatica/article/view/123681/171628

- Moreno Schneider, J., Rehma, G., Montiel-Ponsoda, E., Rodríguez-Doncel, V., Martín-Chozas, P., Navas-Loro, M., Kaltenböck, M., Revenko, A., Karampatakis, S., Sagederd, C., Gracia, J., Maganza, F., Kernerman, I., Dorielle, L., Lagzdins, A., Bosque Gil, J., Verhoeven, P., Gómez Díaz, E., Ballesteros, P. (2022). Lynx: A knowledge-based AI service platform for content processing, enrichment and analysis for the legal domain. _Information Systems,_ (106). <u>https://doi.org/10.1016/j.is.2021.101966</u>

- Musgrave, S., Schalley, A., Haugh, M. (2014). The use of ontologies as a tool for aggregating spoken corpora. En: Ruhi, Ş., Haugh, M., Schmidt, T., Wörne, K. _Best practices for spoken corpora in linguistic research_ (225-248) _._ Cambridge Scholars Publishing.


------------------------- PAGINA 247 --------------------------

Navarro Colorado, F. (2007). _Metodología, construcción y explotación de corpus anotados semántica y anafóricamente_ . Universidad de Alicante.

- Navarro-Galindo, J., Samos, J. (2013). FLERSA: Soporte a la Definición de Anotaciones y Búsquedas Semánticas en un CMS. En: _Actas de las XVI Jornadas de Ingeniería del Software y Bases de Datos_ (101). <u>https://lbd.udc.es/jornadas2011/actas/JISBD/JISBD/S1/Regulares/jisbd2011_sub mission_34.pdf</u>

- Nazar, R. (2011). Estudio diacrónico de la terminología especializada utilizando métodos cuantitativos: Ejemplos de aplicación a un corpus de artículos de lingüística aplicada. _Revista Signos_ , 44(75), 48-67. <u>http://dx.doi.org/10.4067/S0718-09342011000100005</u>

- Neches, R., Fikes, R., Finin, T., Gruber, T., Patil, R., Swartout, W. (1991). Enabling Technology for Knowledge Sharing. _AI Magazine_ (3), 36-56. <u>https://doi.org/10.1609/aimag.v12i3.902</u>

- Noy, N., Mcguinness, D. (2001). _Ontology Development 101: A Guide to Creating Your First Ontology_ . <u>https://protege.stanford.edu/publications/ontology_development/ontology101.pd f</u>

- Pérez Hernández, M. (2002). Explotación de los córpora textuales informatizados para la creación de bases de datos terminológicas basadas en el conocimiento. _Estudios de Lingüística del Español (ELiEs)_ (18). http://elies.rediris.es/elies18/

- Poveda-Villalóna, M., Fernández-Izquierdo, A., Fernández-López, M., García-Castro, R. (2022). LOT: An industrial oriented ontology engineering framework. _Engineering Applications of Artificial Intelligence_ , 111. <u>https://doi.org/10.1016/j.engappai.2022.104755</u>

- Pustejovsky, J., Lee, K., Bunt, H., Romary, L. (2010). ISO-TimeML: An International Standard for Semantic Annotation. _Proceedings of the Seventh International_


------------------------- PAGINA 248 --------------------------

_Conference on Language Resources and Evaluation_ (LREC'10). <u>http://www.lrec-conf.org/proceedings/lrec2010/pdf/55_Paper.pdf</u>

- Raschka, S. (2023). Understanding Large Language Models: A Cross-Section of the Most Relevant Literature To Get Up to Speed. _Ahead of AI._ <u>https://magazine.sebastianraschka.com/p/understanding-large-language-models</u>

- Rothman, D. (2021). _Transformers for Natural Language Processing: Build innovative deep neural network architectures for NLP with Python, PyTorch, TensorFlow, BERT, RoBERTa, and more_ . Packt.

Ruder, S. (2022). _Entity Linking: Task._ <u>http://nlpprogress.com/english/entity_linking.html</u>

- Santoso, J., Setiawana, E., Purwantob, C., Yuniarnoc, E., Hariadic, M., Purnomo, M. (2021). Named entity recognition for extracting concept in ontology building on Indonesian language using end-to-end bidirectional long short-term memory. _Expert Systems With Applications_ (176). <u>https://doi.org/10.1016/j.eswa.2021.114856</u>

- Schalley, A. (2019). Ontologies and ontological methods in linguistics. Language and _Linguistics Compass_ , 13(11), 1-19. <u>https://doi.org/10.1111/lnc3.12356</u>

- <mark>Schmidt, D., Guizzardi, G., Pease, A., Trojahn, C., Vieira, R. (2020). Foundational ontologies meet ontology matching: A survey.</mark> _<mark>Semantic Web,</mark>_ <mark>13(4), 685-704.</mark> <u>10.3233/SW-210447</u>

- Schneider, P., Schopf, T., Vladika, J., Galkin, M., Simperl, E., Matthes, F. (2022). A Decade of Knowledge Graphs in Natural Language Processing: A Survey. _arXiv:2210.00105v1_ . https://doi.org/10.48550/arXiv.2210.00105

- Schrader, B. (2020). What’s the Difference Between an Ontology and a Knowledge Graph?. _Enterprise knowledge._ <u>https://enterprise-knowledge.com/whats-the-difference-between-an-ontology-an d-a-knowledge-graph/</u>


------------------------- PAGINA 249 --------------------------

- Sierra Martínez, G. (2015). _Introducción a los corpus lingüísticos_ . Universidad Nacional Autónoma de México.

- <mark>Silva, V., Freitas, A., Handschuh, S. (2016). Word Tagging with Foundational Ontology Classes: Extending the WordNet-DOLCE Mapping to Verbs.</mark> _<mark>arXiv:1806.07699</mark>_ <mark>.</mark> <u><mark>https://doi.org/10.48550/arXiv.1806.07699</mark></u>

- Staab, S., Studer, R., Schnurr, H., Sure-Vetter, Y. (2001). Knowledge Processes and Ontologies. _Intelligent Systems, IEEE,_ 16(1), 26-34. <u><mark>10.1109/5254.912382</mark></u>

- Studer, R., Benjamins, V., Fensel, D. (1998). Knowledge engineering: principles and methods. _Data & Knowledge Engineering_ 25(1-2), 1-38. <u>https://publikationen.bibliothek.kit.edu/189497/3003</u>

- Swartout, B., Patil, R., Knight, K., Russ, T. (1997). Toward Distributed Use of Large-Scale Ontologies. _AAAI Technical Report SS-97-06_ . <u>https://cdn.aaai.org/Symposia/Spring/1997/SS-97-06/SS97-06-018.pdf</u>

- Tangarife, A.M., Urrego, G., Mejía, J.A. (2014). Advances and Challenges of an Ontology Focused on Verbs Related to Political Violence. En: Quiroz, G., Patiño, P. (Eds.). _LSP in Colombia : advances and challenges_ (67-84). Peterlang.

- Tangarife, A.M., Arenas, S., Ruiz, J.D., Baena, F., Muñoz, N., Tirado, T., Muñoz, B. (2022). Modelo y algoritmo para la identificación y la clasificación de afectaciones en un corpus de testimonios sobre desaparición forzada. _Scire: Representación y organización del Conocimiento_ , 28(2), 23–34. <u>https://doi.org/10.54886/scire.v28i2.4797</u>

- Tehseen, R. (2018). Semantic Information Retrieval: A Survey. _Journal of Information Technology & Software Engineering_ , 8(3), 1-7. 10.4172/2165-7866.1000241

- Uschold, M., King, M. (1995). Towards a Methodology for Building Ontologies. En: _Workshop on Basic Ontological Issues in Knowledge Sharing, held in conjunction with IJCAI-95._


------------------------- PAGINA 250 --------------------------

<u>https://www.aiai.ed.ac.uk/publications/documents/1995/95-ont-ijcai95-ont-meth od.pdf</u>

- Vaca Serrano, A., García Subies, G., Montoro Zamorano, H., Aldama García, N., Samy, D., Betancur Sánchez, D., Moreno Sandoval, A., Guerrero Nieto, M., Barbero Jiménez, A. (2022). RigoBERTa: A State-of-the-Art Language Model For Spanish. _arXiv:2205.10233v3_ <u>. https://arxiv.org/pdf/2205.10233.pdf</u>

- Van Dijk, T. (2011). Specialized discourse and knowledge a case study of the discourse of modern genetics. _Cadernos de Estudos Linguísticos_ , (44), 21–56. <u>10.20396/cel.v44i0.8637063</u>

- Vargas Sierra, C. (2006). El léxico especializado y las ontologías. En: Alcaraz Varó, E., Martínez, J., Yus Ramos, F. (Coord.). _Las lenguas profesionales y académicas_ (41-52). Ariel.

- Vasileiadis, I., Fragouli, E. (2020). A Methodological Framework for Evaluating Knowledge Management in the Public Sector: A Case Study. _<mark>BAM 2020 Conference Proceedings.</mark>_ <u><mark>https://eprints.kingston.ac.uk/id/eprint/52671</mark></u>

- Villazón Terrazas, B. (2011). _A Method for Reusing and Re-engineering Non-ontological Resources for Building Ontologies_ . Universidad Politécnica de Madrid.

- Viltres Sala, H., Rodríguez Leyva, P. (2019). Componente para la anotación semántica de información. _Avances_ , 21( 1), 32-44. <u>https://dialnet.unirioja.es/descarga/articulo/6789908.pdf</u>

- Vinyals, O., Blundell, C., Lillicrap, T., Kavukcuoglu, K., Wierstra, D. (2017). Matching Networks for One Shot Learning. _arXiv:1606.04080v2._ <u>https://arxiv.org/pdf/1606.04080.pdf</u>

- Wang, K., Stevens, R., Alachram, H., Li, Y., Soldatova, L., King, R., Ananiadou, S., Schoene, A., Li, M., Christopoulou, F., Ambite, J., Matthew, J., Garg, S., Hermjakob, U., Marcu, D., Sheng, E., Beißbarth, T., Wingender, E., Galstyan,


------------------------- PAGINA 251 --------------------------

   - A., Gao, X., Chambers, B., Pan, W., Khomtchouk, B., Evans, J. (2021). NERO: a biomedical named-entity (recognition) ontology with a large, annotated corpus reveals meaningful associations through text embedding. _Systems Biology and Applications,_ 7(1). 1-8. <u>https://doi.org/10.1038/s41540-021-00200-x.</u>

- Wang, X., Hu, V., Song, X., Garg, S., Xiao, J., Han, J. (2021). ChemNER: Fine-Grained Chemistry Named Entity Recognition with Ontology-Guided Distant Supervision. En: Moens, M., Huang, X., Specia, L., Wen-tau Yih, S. (Ed.). _Proceedings of the 2021 Conference on Empirical Methods in Natural Language Processing_ (5227–5240). Association for Computational Linguistics. <u>https://aclanthology.org/2021.emnlp-main.424/</u>

- Wu, Shih-Hung; Hsu, Wen-Lian. (2002). SOAT: A Semi-Automatic Domain Ontology Acquisition Tool from Chinese Corpus. _COLING 2002: The 17th International Conference on Computational Linguistics._ Disponible en: <u>https://aclanthology.org/C02-2013/</u>

- Xu, Y., Rajpathak, D., Gibbs, I., Klabjan, D. (2019). Automatic Ontology Learning from Domain-Specific Short Unstructured Text Data. _arXiv:1903.04360_ <u>https://doi.org/10.48550/arXiv.1903.04360</u>


------------------------- PAGINA 252 --------------------------

# **Índice de anexos**

Los anexos de esta tesis pueden ser consultados en el CD adjunto o siguiendo este <u>enlace.</u>

A continuación se escriben los archivos que pueden ser encontrados en el disco:

## **Anexo 1. Glosario de términos de la tesis**

Archivo de texto en donde se referencian los conceptos fundamentales de la tesis. Se presenta una definición y se indica en dónde se trabaja el tema en la tesis, así como los autores más relevantes que sobre el tema fueron citados en la tesis.

## **Anexo 2. Fuentes del corpus**

Archivo en donde se referencian los textos que fueron recopilados para la conformación del corpus. Están organizados alfabéticamente y según la institución productora o compiladora.

## **Anexo 3. Guía de anotación**

Archivo de texto Esta guía define las cuestiones conceptuales y metodológicas que deben tenerse en cuenta para abordar problemas de representación de conocimiento sobre conflictos armados. Puede ser extrapolable para anotar otros recursos relacionados. Es un recurso importante para futuros desarrollos. En el <u>anexo 3</u> se detallan los criterios y consideraciones para la anotación.

## **Anexo 4. Terminología recopilada**

Se presenta la lista de términos según como aparecen en las terminologías de referencia, mostrando la frecuencia de aparición de esos mismos términos en distintos recursos. Aquí se encuentran tanto términos propiamente dichos como otras etiquetas que corresponden a instancias. Están agrupados por clases.

## **Anexo 5. Algoritmos para clasificación a partir del reconocimiento de entidades nombradas**


------------------------- PAGINA 253 --------------------------

En el proceso de experimentación de clasificación con reconocimiento de entidades se construyeron varias versiones de algoritmos. En el <u>anexo 5</u> se incluye una carpeta con tres libros de códigos y el _dataset_ que fue utilizado para el entrenamiento. Pueden evidenciarse las librerías utilizadas, las cargas de datos _train_ y _test,_ el entrenamiento y los resultados. Así mismo, estos se encuentran en _<u>Hugging Face</u>_ <u>,</u> que es un repositorio en donde se alojan versiones de código y es útil para desarrolladores.

## **Anexo 6. Clases y entidades sobre conflicto armado (Protegè)**

Archivo para visualización de clases, entidades e instancias construidas en Protège.

## **Anexo 7. Clases y entidades sobre conflicto armado (** **_mapping_ )**

Archivo para visualización de clases en _mapping._
