# Preguntas de NFR Design — U12 research-reports

- **Unidad:** U12 `research-reports` (tipo `service`). Bolt B12, después de la demo (P11 = A de Delivery
  Planning).
- **Componentes:** el módulo ResearchReports de `session-api`, las rutas `/research-reports*` de ConsoleApi
  (rol `investigador`), el `ReferenceCatalog` que arma ConsoleApi al arrancar y la pantalla M8 de
  AnalystConsole.
- **Situación:** primera pasada (revisión 1, 2026-11-22), sobre el Functional Design revisión 1
  (BR1.1–BR8.4, F1–F6, E1–E40, FD-U12-01 a FD-U12-12) y el NFR Requirements revisión 1 (NFR-U12-01 a
  NFR-U12-07), los dos aprobados.
- **Artefactos para un `service`:** los seis documentos de diseño y `traceability.json`.

## Lo que ya está decidido

| Tema | Decisión | Fuente |
|---|---|---|
| Cifras de C25 de U12 | `research_report_max_bytes` = 8 388 608, `research_report_max_json_depth` = 8, `research_report_write_timeout_s` = 15; ya están en el catálogo C25 v1 del NFR Design de U1 | NFR-U12-01; NFR Design de U1 §5 |
| `415` y `413` | `research.invalid_type` (`415`) y `limits.exceeded` siempre `413` | NFR-U12-02; NFRD-U1 (catálogo de errores) |
| Ingress | Grupo `veridicus-research-reports` con 8 454 144 bytes y las tres anotaciones sin disco (`proxy-request-buffering: "off"`) | NFR-U12-05; NFRD-U2-06 |
| Rangos de C19 v2 | Enteros de 0 a 2^53 − 1 (`seed` también negativo) y `estimated_cost` ≤ 10^9 | NFR-U12-03; NFRD-U1-06 |
| Campos nuevos de C19 v2 | Se guardan `blocking` y la latencia p50 y p95 por papel; `clarifications` pasa el esquema y no se guarda | NFR-U12-04 |
| `GuardedRoute` | Autentica, comprueba el CSRF y el rol antes de leer el cuerpo; en `multipart` delega la lectura en la unidad dueña, que la analiza en memoria | NFRD-U3-08; D2 de U12 |
| Plazo común de las consultas | `statement_timeout` de 2 s por conexión y `lock_timeout` de 2 s | NFR10.11 de U3; NFR10.15 de U5 |
| Respaldo | El RPO es el último volcado manual de U2 y el RTO el de una restauración manual | NFRD-U2-13 |
| Costo de P1 = A (E18, E19) | Aceptado; se mitiga subiendo los reportes antes de fusionar un cambio de perfil o de precios | Pregunta abierta 5 del Functional Design; `reliability-requirements.md` §4 |

## Lo que el diseño resolverá sin preguntar

Cada punto sale de las fuentes aprobadas o es un hallazgo que un experto cierra. Lo que precisa un artefacto
aprobado va a la tabla NFRD-U12-xx de `security-design.md`; ningún original se edita.

1. **Sin conexión de base retenida durante la lectura y la validación.** `GuardedRoute` corre toda la
   petición en una transacción. En la subida, eso dejaría la conexión inactiva dentro de la transacción
   mientras llega el cuerpo por trozos (el Ingress ya no lo almacena) y mientras se valida un archivo de
   hasta 8 MiB (hasta unos 12 s). El plazo de inactividad de la base es de 5 s o de 15 s según el
   artefacto (U6 frente a U7), y con cualquiera de los dos una subida legítima podría cortarse. La subida
   se parte en tres transacciones cortas, con el mismo criterio que el inicio de sesión de U3
   (NFRD-U3-12).
2. **Plazo de lectura del cuerpo.** Toda E/S lleva un plazo explícito (`team.md`). Entra una cifra de C25,
   `research_report_read_timeout_s` = 30.
3. **Bulkhead de subidas.** Dos subidas a la vez como máximo (NFR3.8 mide dos). La tercera espera hasta 5 s
   y, si no hay hueco, recibe `503` `system.unavailable` sin leer el cuerpo, como el semáforo de Argon2id
   de U3.
4. **Plazo de las lecturas** (NFR10.14 lo dejaba a esta etapa). Las lecturas usan el `statement_timeout`
   común de 2 s.
5. **Campos de la línea de log** (NFR10.17) dentro de la lista blanca del formateador único de U3.
6. **Tablas hijas con la convención de auditoría de U3** (marca, `actor_kind` y columnas de actor).
7. **«Cancelar» durante la subida** (NFR3.7): el diálogo aborta la petición y se cierra.
8. **Validación fuera del bucle de eventos**, en un hilo, para que la consola no se bloquee, y con un
   plan B medido si NFR3.10 no se cumple.

Ningún punto cambia el alcance, el riesgo aceptado ni lo que sale del clúster. U12 sigue sin abrir ningún
camino hacia fuera.

## Preguntas

Sin preguntas: todo lo fijan las fuentes.
