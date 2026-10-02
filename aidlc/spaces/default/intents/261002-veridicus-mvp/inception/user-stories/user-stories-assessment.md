# Evaluación — ¿hacen falta historias de usuario?

## Decisión

**Ejecutar.**

## Motivo

Veridicus es un producto con interfaz para personas, varios actores con permisos distintos y reglas de
negocio delicadas (AUTONOMIA-03 y AUTONOMIA-05). Los requisitos de
`inception/requirements-analysis/requirements.md` dicen qué debe hacer el sistema; las historias dicen
quién lo hace, en qué orden y cómo se comprueba que terminó, con criterios Given/When/Then que Code
Generation y Build and Test pueden convertir en pruebas.

## Factores considerados

| Factor | Situación en Veridicus |
|---|---|
| Tipo de proyecto | Greenfield, multicomponente (frontend, API de sesión, agente semántico, base de datos y cola) |
| Funciones de cara al usuario | Sí: carga de escenarios, ingreso del testimonio, revisión de alertas, consolidación y descarga |
| Personas | Al menos dos roles con permisos distintos (`analista`, `admin`) y dos vetos de confianza (SRE/CISO y cumplimiento ético) |
| Complejidad de las reglas | Alta: umbral del Silencio Fáctico, máquina de estados de la alerta, consolidación bloqueante, versiones de reporte |
| Prácticas del equipo | team-practices exige que cada tarea nombre su verificación (AUTONOMIA-02); los criterios de aceptación son el puente |

## Dónde aportan más las historias

- El flujo de **texto** de punta a punta, que es la primera unidad del plan de entrega (team-practices,
  Walking Skeleton).
- La **revisión humana** de alertas y la **consolidación**, donde viven AUTONOMIA-03 y el riesgo de
  sesgo de automatización.
- El **Silencio Fáctico**, donde AUTONOMIA-05 exige una prueba por debajo del umbral.
- Los hallazgos que la revisión de Análisis de Requisitos dejó abiertos (R-01, R-03 a R-06), que aquí se
  resuelven como criterios de aceptación.
