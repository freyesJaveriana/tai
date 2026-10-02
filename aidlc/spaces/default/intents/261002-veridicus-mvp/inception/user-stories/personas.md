# Personas — Veridicus (MVP académico)

Fuente: PRD S3 (ICP y vetos de confianza), roles de `requirements.md` (FR1.2) y respuesta 1 de
`user-stories-questions.md`. Todas las personas son ficticias; el MVP usa solo datos sintéticos.

## P1 — Analista de Verdad (principal)

| Campo | Contenido |
|---|---|
| Rol en la aplicación | `analista` |
| Contexto | Integrante de una unidad de investigación de 10 a 100 personas en una entidad de justicia transicional (JEP, DAV, CNMH). En el MVP, el autor del proyecto con el Golden Dataset. |
| Objetivos | Contrastar un testimonio contra el marco de verdad en minutos y no en días; entregar un reporte que resista auditoría; que la decisión sea humana, no de la IA. |
| Dolores | Fatiga analítica y desgaste emocional por relatos de trauma; retraso por el cotejo manual y fragmentado de cada entrevista frente a expedientes extensos (S3); inconsistencias entre analistas; la fatiga lo expone a aceptar sin leer lo que propone la IA (sesgo de automatización, S12-R2). |
| Comodidad técnica | Media: usa la consola web, no la terminal (supuesto; S3 no lo fija). |
| Contexto de uso | Trabaja con la consola durante la entrevista o justo después, con la atención repartida: las alertas llegan «silenciosas» (S5-CU3) y puede tener que intervenir «en caliente» (S7-J4). Necesita avisos que no interrumpan y un estado que se lea de un vistazo. |
| Frecuencia | En cada entrevista; varias sesiones por semana. |
| Qué no puede pasar | Que la IA califique al compareciente como mentiroso; perder una sesión a mitad de la entrevista. |

## P2 — Administrador de plataforma (Líder SRE / CISO)

| Campo | Contenido |
|---|---|
| Rol en la aplicación | `admin` |
| Contexto | Uno de 3 a 15 ingenieros que operan clústeres del sector justicia; en el MVP, el autor en su máquina de CPU. |
| Objetivos | Desplegar todo dentro del clúster local con cambios revisables por PR; demostrar que ningún dato sin anonimizar sale del clúster; gestionar usuarios desde la consola; cambiar el umbral solo mediante un PR revisable, sin que el sistema se recalibre solo (respuesta 5). |
| Dolores | Sanciones si un testimonio llega a una nube pública; agentes de IA con permisos de escritura descontrolados; pods que caen por memoria (S12-R4). |
| Comodidad técnica | Alta: Kubernetes, Helm, GitHub. |
| Frecuencia | En cada despliegue y cuando hay que ajustar el umbral. |
| Veto | Si el sistema no funciona aislado en el clúster o si algo sin anonimizar sale de él (AUTONOMIA-04). |

## P3 — Oficial de Cumplimiento Ético (parte interesada, sin consola)

| Campo | Contenido |
|---|---|
| Rol en la aplicación | Ninguno: no inicia sesión. Revisa reportes y evidencia de pruebas. |
| Objetivos | Que toda alerta tenga su justificación (CoT) y su cita; que solo un humano valide hallazgos y consolide; que nunca aparezca un juicio de veracidad. |
| Dolores | Revictimización de personas con trastorno de estrés postraumático o vacíos de memoria; alucinaciones que deformen hechos. |
| Veto | Si falta explicabilidad o si hay juicio automatizado sin supervisión humana (AUTONOMIA-03). |
| Cómo aparece en las historias | Como persona de las historias de integridad (sin vocabulario de veracidad, prompt inmutable) y como criterios de aceptación en las del analista. |

## Relación y prioridad

| Prioridad | Persona | Relación |
|---|---|---|
| 1 | Analista de Verdad | Usa el sistema y es el único que valida hallazgos y consolida. |
| 2 | Administrador de plataforma | Hace posible que el analista trabaje dentro del clúster; nunca cambia el estado de una alerta. |
| 3 | Oficial de Cumplimiento Ético | Audita lo que produce el analista; sus vetos limitan lo que la IA puede mostrar. |

El compareciente no es persona del MVP: no usa la interfaz, y su testimonio entra como texto que carga
el analista (respuesta 1).
