# Mapa de historias por unidad — Veridicus

**Revisión 2 (2026-11-07), segunda pasada por el cambio 01 (DT27) y la adenda 02.** Sustituye a la
revisión 1. Las historias retiradas conservan su fila sin unidad.

**Insumos.** Historias de `inception/user-stories/stories.md` y `stories-adenda-02.md` (stories, revisión
2); unidades de `unit-of-work.md`; requisitos de `inception/requirements-analysis/requirements.md`
(requirements); componentes de `inception/domain-design/components.md` (components).

## Historia → unidad

| Historia | Título corto | Prioridad | Unit ID | Directory |
|---|---|---|---|---|
| US1.1 | Cargar e indexar un escenario | Retirada | — | — |
| US1.2 | Corregir un escenario con versión nueva | Retirada | — | — |
| US1.3 | Elegir escenario del catálogo | Retirada | — | — |
| US2.1 | Crear una sesión con su entrevista y su perfil | MUST | U4 | u4-text-flow |
| US2.2 | Enviar el testimonio turno a turno | MUST | U4 | u4-text-flow |
| US2.3 | Pegar un bloque de turnos | MUST | U6 | u6-session-lifecycle |
| US2.4 | Finalizar la sesión | MUST | U7 | u7-forensic-report |
| US2.5 | Ver la lista de sesiones | MUST | U6 | u6-session-lifecycle |
| US2.6 | Importar una transcripción con turnos y páginas | MUST | U6 | u6-session-lifecycle |
| US2.7 | Lanzar el modo final | MUST | U6 | u6-session-lifecycle |
| US3.1 | Revisar una contradicción con sus dos citas | MUST | U4 | u4-text-flow |
| US3.2 | Nunca recibir un resultado parcial | MUST | U11 | u11-incoherence-analyzer |
| US3.3 | Que el testimonio no cambie las reglas | MUST | U11 | u11-incoherence-analyzer |
| US3.4 | Ningún hallazgo sin dos citas verificadas | MUST | U11 | u11-incoherence-analyzer |
| US3.5 | Que el verificador confirme cada hallazgo | MUST | U11 | u11-incoherence-analyzer |
| US3.6 | Solo contradicciones con turnos nuevos | MUST | U11 | u11-incoherence-analyzer |
| US3.7 | Ver la limitación del modo fragmentado | MUST | U11 | u11-incoherence-analyzer |
| US4.1 | Calificar «no documentada» por umbral | Retirada | — | — |
| US4.2 | Recibir el Paquete de Contexto de Traspaso | Retirada | — | — |
| US4.3 | Impedir que el agente arranque sin umbral | Retirada | — | — |
| US5.1 | Aceptar tras leer las observaciones | MUST | U5 | u5-human-review |
| US5.2 | Editar con reformulación propia | MUST | U5 | u5-human-review |
| US5.3 | Descartar con una nota | MUST | U5 | u5-human-review |
| US5.4 | Solo el dueño cambia sus hallazgos | MUST | U5 | u5-human-review |
| US5.5 | Ningún juicio de veracidad | MUST | U4 | u4-text-flow |
| US5.6 | Teclado y lector de pantalla | SHOULD | U4 | u4-text-flow |
| US6.1 | Consolidar la sesión | MUST | U7 | u7-forensic-report |
| US6.2 | Descargar y comprobar la integridad | MUST | U7 | u7-forensic-report |
| US6.3 | Corregir con una versión nueva | MUST | U7 | u7-forensic-report |
| US7.1 | Reanudar una sesión interrumpida | MUST | U6 | u6-session-lifecycle |
| US8.1 | Iniciar sesión en la consola | MUST | U3 | u3-identity-access |
| US8.2 | Gestionar usuarios | MUST | U3 | u3-identity-access |
| US8.3 | Perfiles, proveedores, prompts y límites solo por PR | MUST | U3 | u3-identity-access |
| US8.4 | Rastro de auditoría que no se reescribe | MUST | U3 | u3-identity-access |
| US9.1 | Negar la salida salvo al anonimizador | MUST | U2 | u2-platform |
| US9.2 | Saber que cada servicio está listo | MUST | U2 | u2-platform |
| US9.3 | Recursos y credenciales de cada pod | MUST | U2 | u2-platform |
| US9.4 | Base de datos y cola dentro del clúster | MUST | U2 | u2-platform |
| US9.5 | Ningún workflow aplica cambios ni envía a ZINE | MUST | U2 | u2-platform |
| US10.1 | Ver el progreso del análisis | SHOULD | U6 | u6-session-lifecycle |
| US10.2 | Grabar un turno por voz | SHOULD | U9 | u9-voice |
| US10.3 | Recibir aclaraciones neutras | SHOULD | U8 | u8-assistant-extras |
| US10.4 | Escuchar la pregunta | SHOULD | U9 | u9-voice |
| US10.5 | Confirmar cada hallazgo en ambos órdenes | SHOULD | U8 | u8-assistant-extras |
| US10.6 | Propuesta de umbral cuando hay ruido | Retirada | — | — |
| US10.7 | Sincronizar el clúster con GitOps | SHOULD | U2 | u2-platform |
| US10.8 | Razón de descartes como señal | SHOULD | U2 | u2-platform |
| US11.1 | Ver indicios afectivos | Retirada | — | — |
| US11.2 | Volver desde el historial lateral | COULD | U6 | u6-session-lifecycle |
| US11.3 | Seudonimizar antes de un proveedor externo | MUST | U10 | u10-anonymizer |
| US11.4 | Escalar los trabajadores según la cola | COULD | U2 | u2-platform |
| US11.5 | Anonimizador solo hacia proveedores configurados | MUST | U10 | u10-anonymizer |
| US11.6 | Anonimizador como única salida del clúster | MUST | U2 | u2-platform |
| US12.1 | Ejecutar el analizador por lotes desde la CLI | MUST | U11 | u11-incoherence-analyzer |
| US12.2 | Usar la biblioteca sin infraestructura | MUST | U11 | u11-incoherence-analyzer |
| US12.3 | Evaluar sobre el conjunto sintético | MUST | U11 | u11-incoherence-analyzer |
| US12.4 | Correr el corpus del piloto fuera de Git | MUST | U11 | u11-incoherence-analyzer |
| US12.5 | Ver el registro de modelos de una corrida | MUST | U11 | u11-incoherence-analyzer |
| US12.6 | Subir y consultar un reporte | MUST | U12 | u12-research-reports |
| US12.7 | Comparar dos reportes | SHOULD | U12 | u12-research-reports |
| US13.1 | Elegir el perfil de modelos de la sesión | MUST | U4 | u4-text-flow |
| US13.2 | Cada corrida guarda su configuración efectiva | MUST | U11 | u11-incoherence-analyzer |
| US13.3 | No arrancar con un perfil inválido | MUST | U11 | u11-incoherence-analyzer |
| US13.4 | Juez y verificador de familias distintas | MUST | U11 | u11-incoherence-analyzer |
| US13.5 | Proveedor alterno ante un bloqueo | MUST | U11 | u11-incoherence-analyzer |
| US13.6 | Primera rebanada con un comercial y uno local | MUST | U11 | u11-incoherence-analyzer |
| US13.7 | Comparar los demás proveedores comerciales | MUST | U11 | u11-incoherence-analyzer |
| US14.1 | Validar los modelos locales antes del diseño | MUST | — | Cumplida antes del diseño (`docs/validacion-zine/`) |
| US14.2 | Preparar el paquete de entrada para ZINE | MUST | U11 | u11-incoherence-analyzer |
| US14.3 | Registrar modelo y cuantización en ZINE | MUST | U11 | u11-incoherence-analyzer |
| US15.1 | Reconocer las reglas de uso | Demostración | U13 | u13-ethics-governance |
| US15.2 | Pausar o terminar el análisis | MUST | U6 | u6-session-lifecycle |
| US15.3 | Reportar un problema sin copiar el testimonio | Demostración | U13 | u13-ethics-governance |
| US15.4 | Registrar el consentimiento antes de capturar | MUST | U4 | u4-text-flow |
| US15.5 | Ver el aviso de propósito limitado | MUST | U4 | u4-text-flow |
| US15.6 | Saber quién vio cada sesión | Demostración | U13 | u13-ethics-governance |
| US15.7 | Borrado al vencer la retención | Demostración | U13 | u13-ethics-governance |
| US15.8 | Exportar el reporte con marca de agua | MUST | U7 | u7-forensic-report |
| US15.9 | Trabajar con avisos de bienestar | Demostración | U13 | u13-ethics-governance |
| US15.10 | Medir sesgo por tipo de relato | MUST | U11 | u11-incoherence-analyzer |

## Historias que cumplen varias unidades

| Historia | Unidad dueña | Otras unidades que la cumplen | Cómo |
|---|---|---|---|
| US5.6 Accesibilidad | U4 (base y suite `axe`) | U3, U5, U6, U7, U8, U9, U12, U13 | Cada pantalla nueva entra en la suite `axe` de U4 (P5). |
| US8.4 Auditoría | U3 (convención y prueba común) | U4, U5, U6, U7, U13 | Cada historial de solo inserción cumple la convención de ADR-003 (P5); el Job de retención de U13 es la única excepción (A-2). |
| US5.5 Vocabulario prohibido | U4 (escaneo de salida e interfaz) | U11 (escáner), U7 (reporte), U8 (aclaraciones) | Toda salida nueva pasa por el escáner de U11. |
| US3.2 Sin resultado parcial | U11 (`estado: error` con hallazgos vacíos) | U4 | AnalysisWorker no publica ni guarda hallazgos de una corrida con error. |
| US3.6 Modo incremental | U11 (solo lo que toca turnos nuevos) | U4 | La sesión deduplica por par de citas (AC3.6.3). |
| US3.7 Modo fragmentado | U11 (ventanas y registro) | U4, U7 | La consola y el reporte muestran la limitación. |
| US12.5 Registro de modelos | U11 (registro y costo) | U4 | La consola muestra el registro de la corrida en solo lectura (AC12.5.3). |
| US13.3 Perfil inválido | U11 (validación) | U4, U10 | Ningún proceso arranca con un perfil inválido ni con un destino externo sin anonimizador. |
| US13.6 Primera rebanada | U11 | U10 | El proveedor comercial va por el módulo del anonimizador. |
| US8.3 Solo por PR | U3 (ninguna ruta que escriba) | U11 | Los perfiles, *prompts* y precios son archivos versionados que lee U11. |
| US9.1 y US11.6 Salida denegada | U2 | U9, U10 | Todos los pods entran en la política; solo `anonymizer-proxy` tiene salida. |
| US10.5 Ambos órdenes | U8 | U11 | La permutación vive en el código de la biblioteca, detrás de la opción del perfil. |
| US5.4 Solo el dueño | U5 | U7, U6 | Consolidar, corregir, pausar y terminar también exigen ser el dueño. |
| US15.2 Pausar o terminar | U6 | U4 | Tras la retirada del consentimiento, U4 no encola ni analiza ninguna corrida (VE-10 (a)). |
| US15.5 Aviso | U4 | U7, U11 | El reporte y la salida de la CLI llevan el mismo aviso (VE-01). |
| US15.8 Exportación | U7 (marca de agua y *hash*) | U13 | La exportación se registra por el puerto de ConsoleApi que implementa U13 (AC15.8.2, UG-09). |
| US15.7 Retención | U13 | U4, U5, U7 | Cada unidad borra lo suyo cuando U13 se lo pide, en el orden inverso de las referencias. |

## Orden de historias dentro de cada unidad

El orden sigue las dependencias de datos de stories:

- **U1 contracts:** contrato común v1.0.0 → mensajes de corrida y resultado → esquema del perfil y
  precios → catálogo de límites → vocabulario y aviso → esquema del reporte de la CLI → OpenAPI → métricas
  y formato de fecha.
- **U2 platform:** US9.4 → US9.3 → US9.1 → US11.6 → US9.5 → US9.2 → US10.7 → US10.8 → US11.4.
- **U3 identity-access:** US8.1 → US8.2 → US8.4 → US8.3.
- **U4 text-flow:** US13.1 → US15.4 → US2.1 → US2.2 → US3.1 → US12.5 (consola) → US15.5 → US5.5 →
  US5.6.
- **U5 human-review:** US5.1 → US5.3 → US5.2 → US5.4.
- **U6 session-lifecycle:** US2.3 → US2.6 → US2.7 → US2.5 → US7.1 → US15.2 → US10.1 → US11.2.
- **U7 forensic-report:** US2.4 → US6.1 → US6.2 → US15.8 → US6.3.
- **U8 assistant-extras:** US10.3 → US10.5.
- **U9 voice:** US10.2 → US10.4.
- **U10 anonymizer:** US11.3 → US11.5.
- **U11 incoherence-analyzer:** US12.2 → US13.3 → US13.2 → US3.3 → US3.4 → US3.5 → US3.2 → US3.6 →
  US3.7 → US13.4 → US13.5 → US12.1 → US12.5 → US13.6 → US12.3 → US15.10 → US12.4 → US13.7 → US14.2 →
  US14.3.
- **U12 research-reports:** US12.6 → US12.7.
- **U13 ethics-governance:** US15.1 → US15.6 → US15.3 → US15.9 → US15.7.

## Verificación de cobertura

- Stories tiene 80 historias: 71 tienen exactamente una unidad dueña, 8 están «Retirada» (US1.1–US1.3,
  US4.1–US4.3, US10.6, US11.1) y US14.1 se cumplió antes del diseño.
- Cada unidad salvo U1 tiene al menos una historia; U1 es de tipo `spec` y respalda criterios de US3.6,
  US8.3, US12.6, US13.3 y US15.4.
- Las MUST quedan en U2–U7, U10, U11 y U12; ninguna unidad MUST depende de U8, U9 ni U13. El único
  criterio MUST que necesita a U13 es AC15.8.2, que entra por un puerto y se verifica con U13 (UG-09).
