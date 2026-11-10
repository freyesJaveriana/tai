# Evaluación — ¿hacen falta historias de usuario?

**Revisión 2 — cambio 01 (DT27, 2026-11-02).**

**Revisión 3 — revalidación (2026-11-09).** La decisión no cambia: se ratifican en bloque las precisiones de
Domain Design y Contract Design (preguntas 17–19 de `user-stories-questions.md`).

## Decisión

**Ejecutar.**

## Motivo

Veridicus es un producto con interfaz para personas, una biblioteca y una línea de comandos que usa otra
persona, varios actores con permisos distintos y reglas delicadas (AUTONOMIA-03, AUTONOMIA-04 y
AUTONOMIA-05). Los requisitos de `inception/requirements-analysis/requirements.md` dicen qué debe hacer
el sistema; las historias dicen quién lo hace, en qué orden y cómo se comprueba que terminó, con criterios
Given/When/Then que Code Generation y Build and Test pueden convertir en pruebas.

## Factores considerados

| Factor | Situación en Veridicus |
|---|---|
| Tipo de proyecto | Greenfield, multicomponente: biblioteca del analizador con CLI, frontend, API de sesión, trabajador del analizador, anonimizador, base de datos y cola |
| Funciones de cara al usuario | Sí: crear la sesión con su perfil, importar o ingresar la transcripción, lanzar el modo final, revisar hallazgos, consolidar y descargar; y, para el investigador, la CLI y la evaluación |
| Personas | Dos roles en la consola (`analista`, `admin`), un usuario de la CLI (Investigador del TG) y dos vetos de confianza (SRE/CISO y cumplimiento ético) |
| Complejidad de las reglas | Alta: verificación determinista de las dos citas, máquina de estados del hallazgo, fallo cerrado del anonimizador, modo incremental frente a final, consolidación bloqueante, versiones de reporte |
| Prácticas del equipo | team-practices exige que cada tarea nombre su verificación (AUTONOMIA-02); los criterios de aceptación son el puente |

## Dónde aportan más las historias

- La **primera rebanada**: biblioteca y CLI con el anonimizador y un proveedor comercial sobre
  transcripciones sintéticas (pregunta 10).
- La **verificación de las dos citas** y el **fallo cerrado**, donde viven AUTONOMIA-04 y AUTONOMIA-05.
- La **revisión humana** y la **consolidación**, donde viven AUTONOMIA-03 y el riesgo de sesgo de
  automatización.
- La **validación de modelos locales en ZINE**, que la pregunta 14 pone antes de Domain Design.
- Los hallazgos que la revisión de requisitos dejó abiertos (R-01 a R-03), que aquí se resuelven como
  criterios de aceptación (preguntas 10 a 12).
