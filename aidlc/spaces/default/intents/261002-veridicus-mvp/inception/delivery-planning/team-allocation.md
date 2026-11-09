# Asignación de Bolts — Veridicus (MVP)

**Revisión 2 (2026-11-09), segunda pasada por el cambio 01 (DT27) y la adenda 02.** Sustituye a la
revisión 1: B10 pasa a MUST y entran B11–B13; el orden es el de `bolt-plan.md` (P10, P11).

**Insumos.** Bolts de `bolt-plan.md`; unidades de `inception/units-generation/unit-of-work.md`
(unit-of-work) y su grafo `unit-of-work-dependency.md` (unit-of-work-dependency); prácticas de
`inception/practices-discovery/team-practices.md` y `team.md` (team-practices). Team Formation (1.5) no
se ejecutó en el scope `classic`.

## Quién ejecuta cada Bolt

Un **Bolt** es una pasada de construcción sobre una unidad de trabajo que termina en algo que corre y se
puede demostrar. Un **mob** es el grupo que trabaja junto en un Bolt; aquí es siempre el mismo par: el
agente desarrollador (IA) propone y escribe, y el autor revisa y aprueba (team-practices: «el agente
propone, el humano aprueba»). No hay varios equipos, así que no hace falta un *Program Board* (el
tablero que reparte Bolts entre equipos).

| Orden | Bolt | Unidad | Ejecuta | Revisa y aprueba | Lo que solo hace el humano |
|---|---|---|---|---|---|
| 0 | P0.1 Configuración de GitHub | — | Autor + agente desarrollador (tarea conjunta) | Autor | Cambiar la protección de `main` y los permisos en GitHub |
| 1 | B1 Contratos | U1 | aidlc-developer-agent | Autor | — |
| 2 | B10 Anonimizador | U10 | aidlc-developer-agent | Autor | Crear la clave de API del proveedor comercial en su `.env` no versionado |
| 3 | B11 Analizador | U11 | aidlc-developer-agent | Autor | Revisar a mano el conjunto sintético; lanzar los `sbatch` en ZINE; correr la CLI sobre el piloto fuera de Git |
| 4 | B2 Acceso | U3 | aidlc-developer-agent | Autor | — |
| 5 | B3 Flujo de texto | U4 | aidlc-developer-agent | Autor | — |
| 6 | B4 Plataforma | U2 | aidlc-developer-agent | Autor | Aplicar a mano los artefactos fusionados (hasta el módulo 8); crear los Secrets; verificar la `NetworkPolicy` en el clúster |
| 7 | B5 Revisión humana | U5 | aidlc-developer-agent | Autor | — |
| 8 | B6 Reporte de revisión | U7 | aidlc-developer-agent | Autor | — |
| 9 | B12 Reportes del investigador | U12 | aidlc-developer-agent | Autor | — |
| 10 | B7 Ciclo de vida | U6 | aidlc-developer-agent | Autor | Correr la prueba de carga de NFR8 en la máquina CPU |
| 11 | B13 Ética | U13 | aidlc-developer-agent | Autor | Lanzar el Job de retención |
| 12 | B8 Extras del asistente | U8 | aidlc-developer-agent | Autor | — |
| 13 | B9 Voz | U9 | aidlc-developer-agent | Autor | — |

Un par del curso solo participa si el autor lo pide (team-practices), y además en la calificación Likert
de las observaciones (NFR6), antes de la sustentación.

## Reglas de trabajo

- **Una unidad a la vez.** El grafo admite trabajo en paralelo (por ejemplo, acceso junto a anonimizador
  después de los contratos), pero con una sola persona revisando, el paralelismo solo aumenta el trabajo
  a medio revisar. Construction corre en serie y recorre **etapa por etapa** (P8): todas las unidades
  pasan por cada etapa de diseño antes de llegar a su plan de tareas.
- **`Approve Plan` es del humano.** El agente genera el plan de tareas de cada unidad; el autor lo revisa
  y solo él elige `Approve Plan` (`team.md`, Mandated).
- **La aprobación humana es la fusión.** Cada PR del Bolt lo revisa y aprueba el autor con la evidencia
  del comando de verificación; la fusión en `main` protegida es la aprobación registrada. Ningún paso
  aplica cambios al clúster ni envía trabajos a ZINE sin el humano (AUTONOMIA-01).
- **Sin autonomía en Construction.** Cada punto de control se revisa («Review each checkpoint»); el
  agente nunca elige ni propone continuar solo (`team.md`, Forbidden).
- **Carga del autor.** El cuello de botella es la revisión del autor, no la escritura de código. Cada
  Bolt es una unidad y entra como un solo PR con squash (P9). B11 (analizador, XL) es ahora el PR más
  grande y el que más revisión pide, seguido de B3; ambos se revisan por capas, en el orden de su plan de
  tareas.
