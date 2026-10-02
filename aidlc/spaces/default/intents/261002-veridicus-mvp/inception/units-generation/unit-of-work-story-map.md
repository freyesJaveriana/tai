# Mapa de historias por unidad — Veridicus

**Insumos.** Historias de `inception/user-stories/stories.md` (stories); unidades de `unit-of-work.md`;
requisitos de `inception/requirements-analysis/requirements.md` (requirements); componentes de
`inception/domain-design/components.md` (components).

## Historia → unidad

| Historia | Título corto | Prioridad | Unit ID | Directory |
|---|---|---|---|---|
| US1.1 | Cargar e indexar un escenario | MUST | U4 | u4-text-flow |
| US1.2 | Corregir un escenario con versión nueva | MUST | U6 | u6-session-lifecycle |
| US1.3 | Elegir escenario del catálogo | MUST | U4 | u4-text-flow |
| US2.1 | Crear una sesión ligada a un escenario | MUST | U4 | u4-text-flow |
| US2.2 | Enviar el testimonio turno a turno | MUST | U4 | u4-text-flow |
| US2.3 | Pegar una transcripción completa | MUST | U6 | u6-session-lifecycle |
| US2.4 | Finalizar la sesión | MUST | U7 | u7-forensic-report |
| US2.5 | Ver la lista de sesiones | MUST | U6 | u6-session-lifecycle |
| US3.1 | Ver una alerta con su justificación | MUST | U4 | u4-text-flow |
| US3.2 | Nunca recibir una alerta parcial | MUST | U4 | u4-text-flow |
| US3.3 | Que el testimonio no cambie las reglas del juez | MUST | U4 | u4-text-flow |
| US4.1 | Calificar «no documentada» por umbral | MUST | U4 | u4-text-flow |
| US4.2 | Recibir el Paquete de Contexto de Traspaso | MUST | U4 | u4-text-flow |
| US4.3 | Impedir que el agente arranque sin umbral | MUST | U4 | u4-text-flow |
| US5.1 | Aceptar una alerta tras leer su CoT | MUST | U5 | u5-human-review |
| US5.2 | Editar una alerta con reformulación propia | MUST | U5 | u5-human-review |
| US5.3 | Descartar una alerta con nota | MUST | U5 | u5-human-review |
| US5.4 | Solo el dueño cambia sus alertas | MUST | U5 | u5-human-review |
| US5.5 | Ningún juicio de veracidad | MUST | U4 | u4-text-flow |
| US5.6 | Teclado y lector de pantalla | SHOULD | U4 | u4-text-flow |
| US6.1 | Consolidar cuando todo está revisado | MUST | U7 | u7-forensic-report |
| US6.2 | Descargar y comprobar integridad | MUST | U7 | u7-forensic-report |
| US6.3 | Corregir un reporte con versión nueva | MUST | U7 | u7-forensic-report |
| US7.1 | Reanudar una sesión interrumpida | MUST | U6 | u6-session-lifecycle |
| US8.1 | Iniciar sesión | MUST | U3 | u3-identity-access |
| US8.2 | Gestionar usuarios | MUST | U3 | u3-identity-access |
| US8.3 | Cambiar el umbral con un PR | MUST | U3 | u3-identity-access |
| US8.4 | Rastro de auditoría no reescribible | MUST | U3 | u3-identity-access |
| US9.1 | Aislar de internet los pods sensibles | MUST | U2 | u2-platform |
| US9.2 | Salud de cada servicio | MUST | U2 | u2-platform |
| US9.3 | Recursos y credenciales de cada pod | MUST | U2 | u2-platform |
| US9.4 | Base de datos y cola en el clúster | MUST | U2 | u2-platform |
| US9.5 | Ningún workflow aplica cambios | MUST | U2 | u2-platform |
| US10.1 | Ver el progreso | SHOULD | U6 | u6-session-lifecycle |
| US10.2 | Grabar un turno por voz | SHOULD | U9 | u9-voice |
| US10.3 | Sugerencia de pregunta | SHOULD | U8 | u8-assistant-extras |
| US10.4 | Escuchar la pregunta | SHOULD | U9 | u9-voice |
| US10.5 | Confirmar en ambos órdenes | SHOULD | U8 | u8-assistant-extras |
| US10.6 | Propuesta de umbral por AIR | SHOULD | U2 | u2-platform |
| US10.7 | GitOps con Argo CD | SHOULD | U2 | u2-platform |
| US11.1 | Indicios afectivos en el paquete | COULD | U8 | u8-assistant-extras |
| US11.2 | Historial lateral | COULD | U6 | u6-session-lifecycle |
| US11.3 | Anonimizar antes de llamadas externas | COULD | U10 | u10-anonymizer |
| US11.4 | Escalar trabajadores con KEDA | COULD | U2 | u2-platform |

U1 (`contracts`) no implementa historias por sí misma: entrega los contratos de los que dependen los
criterios de US2.2 (AC2.2.3), US3.2, US5.5 (AC5.5.3, AC5.5.4) y US8.3 (AC8.3.1).

## Historias que cruzan unidades

| Historia | Unidad dueña | Otras unidades que la cumplen | Cómo |
|---|---|---|---|
| US5.6 Accesibilidad | U4 (base y suite `axe`) | U3, U5, U6, U7, U8, U9 | Cada pantalla nueva entra en la suite `axe` de U4 (P5). |
| US8.4 Auditoría | U3 (convención y prueba común) | U4, U5, U6, U7 | Cada historial de solo inserción cumple la convención de ADR-003 (P5). |
| US5.5 Vocabulario prohibido | U4 (escaneo de salida e interfaz) | U7 (reporte), U8 (pregunta, indicio afectivo) | Toda salida nueva pasa por IntegrityPolicy. |
| US9.1 NetworkPolicy | U2 | U9, U10 | El audio-worker entra en la política de salida denegada; solo el anonimizador tendría salida. |
| US5.4 Solo el dueño | U5 | U7 | Consolidar y corregir también exigen ser el dueño (AC6.1.7, AC6.3.5). |

## Orden de historias dentro de cada unidad

El orden sigue las dependencias de datos de `stories.md` (sección Dependencias):

- **U1 contracts:** mensajes de cola → esquemas del juez y de la alerta → vocabulario prohibido →
  OpenAPI → métricas y formato de fecha.
- **U2 platform:** US9.4 → US9.3 → US9.1 → US9.5 → US9.2 → US10.7 → US10.6 → US11.4.
- **U3 identity-access:** US8.1 → US8.2 → US8.4 → US8.3.
- **U4 text-flow:** US1.1 → US1.3 → US2.1 → US2.2 → US4.3 → US3.3 → US4.1 → US3.1 → US3.2 → US4.2 →
  US5.5 → US5.6.
- **U5 human-review:** US5.1 → US5.3 → US5.2 → US5.4.
- **U6 session-lifecycle:** US1.2 → US2.3 → US2.5 → US7.1 → US10.1 → US11.2.
- **U7 forensic-report:** US2.4 → US6.1 → US6.2 → US6.3.
- **U8 assistant-extras:** US10.3 → US10.5 → US11.1.
- **U9 voice:** US10.2 → US10.4.
- **U10 anonymizer:** US11.3.

## Verificación de cobertura

- Las 44 historias de `stories.md` tienen exactamente una unidad dueña.
- Cada unidad salvo U1 tiene al menos una historia; U1 es de tipo `spec` y respalda criterios de
  US2.2, US3.2, US5.5 y US8.3.
- Las MUST quedan en U2–U7; ninguna MUST depende de U8, U9 ni U10.
