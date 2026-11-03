# Personas — Veridicus (analizador de incoherencias del TG)

**Revisión 2 — cambio 01 (DT27, 2026-11-02).** Fuente: PRD S3 (ICP y vetos de confianza), roles de
`requirements.md` (FR1.2), respuesta 1 de `user-stories-questions.md` y, en la segunda pasada,
`docs/iteracion2.md` §2.2 y la respuesta 9; el rol de P4 en la consola, por Refined Mockups (2026-11-03). Todas las personas son ficticias; el repositorio usa solo
datos sintéticos.

## P1 — Analista de Verdad (principal)

| Campo | Contenido |
|---|---|
| Rol en la aplicación | `analista` |
| Contexto | Integrante de una unidad de investigación de 10 a 100 personas en una entidad de justicia transicional (JEP, DAV, CNMH). En el MVP, el autor del proyecto con el conjunto sintético. |
| Objetivos | Encontrar las contradicciones dentro de un relato largo sin releerlo entero; tener cada contradicción con sus dos citas a la vista; entregar un reporte que resista auditoría; que la decisión sea humana, no de la IA. |
| Dolores | Fatiga analítica y desgaste emocional por relatos de trauma; relectura de entrevistas largas para localizar contradicciones entre pasajes distantes (S2); inconsistencias entre analistas; la fatiga lo expone a aceptar sin leer lo que propone la IA (sesgo de automatización, S12-R2). |
| Comodidad técnica | Media: usa la consola web, no la terminal (supuesto; S3 no lo fija). |
| Contexto de uso | Importa una transcripción ya hecha, o ingresa el testimonio turno a turno durante la entrevista con la atención repartida; los hallazgos llegan «silenciosos» (S5-CU3). Al crear la sesión elige el perfil de modelos y sabe si el texto saldrá seudonimizado hacia un proveedor comercial. |
| Frecuencia | En cada entrevista; varias sesiones por semana. |
| Qué no puede pasar | Que la IA califique al compareciente como mentiroso; recibir una cita que no está en el testimonio; perder una sesión a mitad de la entrevista; quedarse sin poder entregar el reporte porque el análisis completo falló (pregunta 13). |
| Cambio 01 | Deja de cargar escenarios de control; gana la elección del perfil, la importación y el modo final. |

## P2 — Administrador de plataforma (Líder SRE / CISO)

| Campo | Contenido |
|---|---|
| Rol en la aplicación | `admin` |
| Contexto | Uno de 3 a 15 ingenieros que operan clústeres del sector justicia; en el MVP, el autor en su máquina de CPU. |
| Objetivos | Desplegar todo dentro del clúster local con cambios revisables por PR; demostrar que nada sin seudonimizar sale del clúster y que la única salida es la del anonimizador; cambiar perfiles, proveedores, *prompts* y límites solo por PR; crear las claves de API en Secrets; gestionar usuarios desde la consola. |
| Dolores | Sanciones si un testimonio identificable llega a una nube pública; agentes de IA con permisos de escritura descontrolados; pods que caen por memoria (S12-R4). |
| Comodidad técnica | Alta: Kubernetes, Helm, GitHub. |
| Frecuencia | En cada despliegue y cuando hay que cambiar un perfil. |
| Veto | Si el sistema no funciona aislado en el clúster o si algo sin seudonimizar sale de él (AUTONOMIA-04). |
| Cambio 01 | El umbral pasa a perfiles, proveedores y claves por PR; el anonimizador y su salida a internet pasan a ser su responsabilidad. |

## P3 — Oficial de Cumplimiento Ético (parte interesada, sin consola)

| Campo | Contenido |
|---|---|
| Rol en la aplicación | Ninguno: no inicia sesión. Revisa reportes y evidencia de pruebas. |
| Objetivos | Que toda contradicción traiga sus dos citas verificadas; que solo un humano valide hallazgos y consolide; que nunca aparezca un juicio de veracidad, emocional ni estilométrico. |
| Dolores | Revictimización de personas con trastorno de estrés postraumático o vacíos de memoria; alucinaciones que deformen hechos. |
| Veto | Si un hallazgo llega sin sus dos citas verificadas o si hay juicio automatizado sin supervisión humana (AUTONOMIA-03, AUTONOMIA-05). |
| Cómo aparece en las historias | Como persona de las historias de integridad (citas verificadas, sin vocabulario de veracidad, *prompt* inmutable, rastro de auditoría) y como criterios de aceptación en las del analista. Su evidencia es el reporte consolidado y el historial de pruebas (R-03 de la primera revisión). |
| Cambio 01 | «CoT y cita» pasa a «dos citas verificadas». |

## P4 — Investigador del TG (nueva)

| Campo | Contenido |
|---|---|
| Rol en la aplicación | `investigador`: en la consola solo sube y consulta reportes de corridas y evaluaciones, sin leer sesiones (FR1.2, FR13.5; Refined Mockups, 2026-11-03). Todo lo demás lo hace con la biblioteca y la línea de comandos. |
| Contexto | Autor del Trabajo de Grado *Diálogos para la Memoria*, que reutiliza el mismo analizador con el mismo contrato en la app `sistema` (DT17, DT20). Trabaja en su máquina local y en el clúster ZINE (Ing. Sistemas, SLURM, solo CPU). |
| Objetivos | Correr el analizador por lotes sobre el conjunto sintético y el corpus del piloto; comparar perfiles y modelos con métricas reproducibles; medir la calidad de modelos locales grandes en ZINE; validar los modelos locales antes del diseño (respuesta 14). |
| Dolores | Corridas largas que se cortan en el clúster; resultados que no se pueden comparar porque no registran modelo, cuantización ni configuración; un repositorio público donde no puede entrar nada del piloto. |
| Comodidad técnica | Alta: Python, línea de comandos, SLURM. |
| Frecuencia | En cada cambio del analizador, del *prompt* o de un perfil, y en cada lote de evaluación. |
| Qué no puede pasar | Que un dato del piloto entre a Git; que un trabajo se lance en ZINE sin que él lo revise (AUTONOMIA-01). |

## Relación y prioridad

| Prioridad | Persona | Relación |
|---|---|---|
| 1 | Analista de Verdad | Usa el producto y es el único que valida hallazgos y consolida. |
| 2 | Investigador del TG | Usa el mismo analizador desde la línea de comandos y consulta sus reportes en la consola; sus mediciones fijan los perfiles que el analista elige. |
| 3 | Administrador de plataforma | Hace posible que el analista trabaje dentro del clúster; nunca cambia el estado de un hallazgo. |
| 4 | Oficial de Cumplimiento Ético | Audita lo que produce el analista; sus vetos limitan lo que la IA puede mostrar. |

El compareciente no es persona del MVP: no usa la interfaz, y su testimonio entra como texto que importa
o ingresa el analista (respuesta 1).
