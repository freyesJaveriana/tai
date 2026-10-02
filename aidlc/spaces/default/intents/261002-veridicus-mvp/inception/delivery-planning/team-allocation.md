# Asignación de Bolts — Veridicus (MVP)

**Insumos.** Bolts de `bolt-plan.md`; unidades de `inception/units-generation/unit-of-work.md`
(unit-of-work) y su grafo `unit-of-work-dependency.md` (unit-of-work-dependency); prácticas de
`inception/practices-discovery/team-practices.md` (team-practices). Team Formation (1.5) no se ejecutó
en el scope `classic`.

## Quién ejecuta cada Bolt

Un **Bolt** es una pasada de construcción sobre una o varias unidades de trabajo que termina en algo
demostrable. Un **mob** es el grupo que trabaja junto en un Bolt; aquí el mob es siempre el mismo par:
el agente desarrollador (IA) propone y escribe, y el autor revisa y aprueba (team-practices: «el agente
propone, el humano aprueba»). No hay varios equipos, así que no hace falta un *Program Board* (el
tablero que reparte Bolts entre equipos).

| Bolt | Unidades | Ejecuta | Revisa y aprueba | Apoyo puntual |
|---|---|---|---|---|
| Tareas previas | — | Autor + agente desarrollador (tarea conjunta) | Autor | — |
| B1 Contratos | U1 | aidlc-developer-agent | Autor | — |
| B2 Acceso | U3 | aidlc-developer-agent | Autor | — |
| B3 Flujo de texto | U4 | aidlc-developer-agent | Autor | Par del curso solo si el autor lo pide |
| B4 Plataforma | U2 | aidlc-developer-agent | Autor (aplica a mano los artefactos fusionados hasta el módulo 8) | — |
| B5 Revisión humana | U5 | aidlc-developer-agent | Autor | — |
| B6 Reporte forense | U7 | aidlc-developer-agent | Autor | — |
| B7 Ciclo de vida | U6 | aidlc-developer-agent | Autor | — |
| B8 Extras del asistente | U8 | aidlc-developer-agent | Autor | — |
| B9 Voz | U9 | aidlc-developer-agent | Autor | — |
| (B10) Anonimizador | U10 | aidlc-developer-agent, si se construye | Autor | — |

## Reglas de trabajo

- **Una unidad a la vez.** El grafo admite trabajo en paralelo (por ejemplo, plataforma junto a acceso
  después de los contratos), pero con una sola persona revisando, el paralelismo solo aumenta el
  trabajo a medio revisar. Construction corre en serie y recorre **etapa por etapa** (P8): todas las
  unidades pasan por cada etapa de diseño antes de llegar a su plan de tareas.
- **La aprobación humana es la fusión.** Cada PR del Bolt lo revisa y aprueba el autor con la evidencia
  del comando de verificación; la fusión en `main` protegida es la aprobación registrada. Ningún paso
  aplica cambios al clúster sin ella (AUTONOMIA-01).
- **Sin autonomía en Construction.** Cada punto de control se revisa («Review each checkpoint»); el
  agente nunca elige ni propone continuar solo (team-practices, Forbidden).
- **Carga del autor.** El cuello de botella es la revisión del autor, no la escritura de código. Cada
  Bolt es una unidad y entra como un solo PR con squash (P9); cada PR lleva su evidencia. B3 (flujo de
  texto, XL) es el PR más grande y el que más tiempo de revisión pide; se revisa por capas, en el orden
  de su plan de tareas.
