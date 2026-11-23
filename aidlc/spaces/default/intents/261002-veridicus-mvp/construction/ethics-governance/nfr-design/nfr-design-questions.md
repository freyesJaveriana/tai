# Preguntas de NFR Design — U13 ethics-governance

- **Unidad:** U13 `ethics-governance` (tipo `service`). Bolt B13.
- **Componentes:** el módulo EthicsGovernance de `session-api` (fachada, adaptador real de `AccessLog`,
  `Job` de retención y comando de consulta), las rutas `/acknowledgements`, `/problem-reports` y
  `PATCH /sessions/{id}/retention` de ConsoleApi, la validación de `retention_days` al crear o importar, y
  el diálogo, la franja, el panel, el plazo y los avisos de bienestar de AnalystConsole.
- **Situación:** primera pasada (revisión 1, 2026-11-22), sobre el Functional Design revisión 1
  (BR1.1–BR9.2, F1–F10, E1–E54, FD-U13-01 a FD-U13-13) y el NFR Requirements revisión 1 (NFR-U13-01 a
  NFR-U13-12), los dos aprobados.
- **Artefactos para un `service`:** los seis documentos de diseño y `traceability.json`.

## Lo que ya está decidido

| Tema | Decisión | Fuente |
|---|---|---|
| Cifras de C25 de U13 | `retention_max_days` = 90, `retention_min_days` = 1, `acknowledgement_validity_days` = 90, `testimony_warning_words` = 8, `problem_report_note_max_chars` = 2 000, `wellness_reminder_interval_s` = 2 700 (propuesta) y `ethics_body_max_bytes` = 32 768; ya están en el catálogo C25 v1 del NFR Design de U1 | NFR-U13-01; NFR Design de U1 §5 |
| `413` | `limits.exceeded` responde siempre `413`, también en la nota y en el cuerpo | NFR-U13-02; NFRD-U1 (catálogo de errores) |
| Tope del cuerpo | Lo aplica `GuardedRoute` porque las tres rutas declaran `x-veridicus-max-bytes: ethics_body_max_bytes` | NFR-U13-03; NFRD-U1-04; NFRD-U5-04 |
| `AccessLog` | Punto de guardado de 500 ms en las lecturas (`record_access`); la exportación usa `record_access_strict` y falla cerrada con `503 report.export_not_recorded` | NFR-U3-05; NFR-U7-09; §2.4 de U3; §10 de U7 |
| Redis caído en el `Job` | La sesión no se borra: queda `failed` con `system.unavailable` | NFR-U13-05 |
| Fuera de Argo CD | Los `Job` de retención y `create-admin` viven en `deploy/jobs/` y los aplica el humano | §7.4 del NFR Design de U2 |
| `Job` en el clúster | Mismo UID y GID que `session-api`, los dos PVC en escritura, `backoffLimit: 0`, `activeDeadlineSeconds` 3 600 (propuesta), `requests` 250m/256 MiB, `limits` 1 CPU/512 MiB, salida solo a PostgreSQL, Redis y DNS | NFR-U13-07; §7.3 y §13 de U2 |
| Comando de consulta | `kubectl exec` en el contenedor `session-api`, en la lista cerrada de solo lectura de U2 | NFR-U13-08, NFR-U13-09; §9 de U2 |
| Índices de `EthicsSessionPort` | `interview_session (retention_until)` y `(created_at) WHERE retention_until IS NULL`; `turn_texts` como iterador con `yield_per` | NFRD-U4-11, NFRD-U4-12 |
| Parámetros de log de PostgreSQL | `log_parameter_max_length` y `log_parameter_max_length_on_error` a 0 | NFR-U13-12; NFRD-U2-10 |
| Plazo de inactividad del `Job` | `SET LOCAL idle_in_transaction_session_timeout` ≥ 15 s o ninguno en la transacción por sesión, porque la purga borra archivos | NFRD-U7-06 |
| `lock_timeout` y `hide_parameters` | En `session_api/shared/db.py` para todos los procesos, también los `Job` | NFRD-U5-10 |

## Lo que el diseño resolverá sin preguntar

Cada punto sale de las fuentes aprobadas o es un hallazgo que un experto cierra. Lo que precisa un artefacto
aprobado va a la tabla NFRD-U13-xx de `security-design.md`; ningún original se edita.

1. **Orden de los controles.** NFR10.1 dice «autenticación, rol, CSRF, tope, esquema y propiedad», pero
   `GuardedRoute` de U3 compara el CSRF antes que el rol y resuelve el dueño de ruta antes de leer el
   cuerpo. Se sigue a `GuardedRoute`, que es la única entrada de `/api/v1`. El resultado de seguridad es
   el mismo: `401` o `403`, 0 filas y el cuerpo sin leer.
2. **`FOR UPDATE` sin permiso `UPDATE`.** PostgreSQL exige el permiso `UPDATE` sobre al menos una columna
   para `SELECT … FOR UPDATE`, y `veridicus_retention` nunca tiene `UPDATE` (§9.3 de U3). El `Job`
   bloquea la sesión con una función `SECURITY DEFINER` que solo bloquea. Se pide lo mismo a U7 para su
   `FOR UPDATE` sobre `report_version`.
3. **Conteos de `--dry-run`.** BR5.3 pide conteos por tabla sin borrar, y C24 solo trae `purge_session`,
   que borra archivos. Se pide una operación de solo lectura `count_session` en C24, que implementan U4,
   U5 y U7.
4. **`ProblemReport` como `history` purgable.** `entities.md` lo marca `mutable` con permisos `SELECT` e
   `INSERT`, pero la función de permisos de U3 da `UPDATE` a toda tabla `mutable`. La marca pasa a
   `history`, `purgeable: true`, con `reported_by` y `reported_at` como columnas de actor.
5. **`INSERT` de `veridicus_retention` en `RetentionAct`.** Se declara como excepción explícita en la marca,
   igual que el `DELETE` de `web_session` (NFRD-U3-07).
6. **El `DETAIL` de una violación de `CHECK` en el log de PostgreSQL.** «Failing row contains (…)» copiaría
   la nota. Se pide `log_error_verbosity = terse` a U2.
7. **`retention_max_days` igual en la API y en el `Job`.** Una variable de entorno que solo bajara la cifra
   en uno de los dos procesos cambiaría el momento del borrado. Se pide una comprobación estática a U2.
8. **Índices del comando de consulta.** Se añaden los índices por hora que faltan en NFR3.10.
9. **Espacios en blanco iguales en la consola y en el servidor.** El archivo de casos compartidos declara la
   lista de puntos de código de espacio.

Ningún punto cambia el alcance, el riesgo aceptado ni lo que sale del clúster. U13 sigue sin abrir ningún
camino hacia fuera.

## Preguntas

Sin preguntas: todo lo fijan las fuentes.
