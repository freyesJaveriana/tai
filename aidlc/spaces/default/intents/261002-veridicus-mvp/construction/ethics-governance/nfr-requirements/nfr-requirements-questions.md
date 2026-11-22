# Preguntas de NFR Requirements — U13 ethics-governance

- **Unidad:** U13 `ethics-governance` (tipo `service`, demostración, ADR-016). Bolt B13.
- **Componentes:** el módulo EthicsGovernance de `session-api` (reconocimiento, adaptador real de
  `AccessLog`, reporte de problemas, plazo de retención), el `Job` de retención, el comando de consulta y
  lo que agrega a AnalystConsole (diálogo, franja, panel, plazo y avisos de bienestar).
- **Situación:** primera pasada (revisión 1, 2026-11-22), sobre el Functional Design revisión 1 de U13
  (BR1.1–BR9.2, F1–F10, E1–E54, FD-U13-01 a FD-U13-13), aprobado hoy.
- **Artefactos de esta etapa para un `service`:** los seis documentos y `traceability.json`.

---

## 1. Lo que ya está decidido y no se vuelve a preguntar

| Tema | Decisión | Fuente |
|---|---|---|
| Demostración sin compuertas | Nada de U13 impide abrir ni crear sesiones | ADR-016; DD-01 a DD-05; BR1.6 |
| Respuestas P1–P7 del Functional Design | «Más tarde» con franja; plazo por defecto igual al máximo; desde la creación; reducen el dueño y el `admin`; reloj real y `--as-of` solo con `--dry-run`; reportes sin sesión por antigüedad; consulta por comando | `functional-design-questions.md` |
| Cifras ya fijadas por la adenda | `retention_max_days` = 90, `retention_min_days` = 1, `acknowledgement_validity_days` = 90, `testimony_warning_words` = 8 | VE-04; VE-12; AC15.3.3; FD-U13-03 |
| Forma de los límites | `limits.exceeded` siempre `413`; C25 sin nulos; decimales solo en `ratio` y `s`; unidades `days`, `chars`, `words`, `bytes`, `s` | NFR-U1-01, NFR-U1-03, NFR-U1-07; NFR10.14 de U1 |
| Plazo de `AccessLog` | 500 ms (`VERIDICUS_ACCESS_LOG_TIMEOUT_MS`): en las lecturas, en un punto de guardado que no revierte la respuesta; en la exportación, revierte y responde `503 report.export_not_recorded` | NFR-U3-05; NFR10.21 de U3; NFR-U7-09 |
| `Job` de retención | En `deploy/jobs/`, fuera de Argo CD, `backoffLimit: 0`, con `activeDeadlineSeconds`; monta en escritura los volúmenes de reportes y audio; sale solo a PostgreSQL y Redis; nunca un `CronJob` | NFR10.16 y NFR-U2-09 de U2 |
| Usuarios de base de datos | Tres: `veridicus_app`, `veridicus_retention` y el de migraciones; la prueba común de auditoría recorre las tablas de U13 | U2; NFR11.3 de U3 |
| Comandos de operación | Los ejecuta el humano con `kubectl exec` en el contenedor de `session-api`, en una transacción `READ ONLY` (como `verify_store`) | NFR-U7-05; NFR10.20 de U7 |
| Plazos comunes | `statement_timeout` 2 s y Redis ≤ 0,5 s | NFR10.11 de U3 |
| Volumen | Un solo analista en la sustentación; ≤ 500 sesiones en la base; `transcript_max_turns` = 2 000 y `transcript_max_chars` = 250 000 | requirements §5; U6; U4 |
| Pila | Python 3.12, FastAPI, SQLAlchemy 2 con psycopg 3, Alembic en un `Job`, React con TypeScript estricto | `team.md`; U3, U4 |

## 2. Lo que el diseño resolverá sin preguntar

Las precisiones a artefactos aprobados van a la tabla NFR-U13-xx de `security-requirements.md` (§7). No
se edita ningún original.

1. **Cifras de C25 que son de U13** (pregunta abierta 1 del Functional Design).
   - `problem_report_note_max_chars` = 2 000, el mismo tope que las notas de la revisión humana (U5). Con
     ese tope, la nota aporta como mucho unas 1 000 secuencias de 8 palabras a la comparación, y el costo lo
     manda el tamaño de la sesión, no la nota.
   - `wellness_reminder_interval_s` = 2 700 (45 minutos). El repositorio no trae una cifra del protocolo
     del TG. Es una propuesta de esta etapa, que se presenta en la aprobación. Para la demostración, el
     entorno puede bajarla (`VERIDICUS_LIMIT_WELLNESS_REMINDER_INTERVAL_S`), nunca subirla.
   - Una cifra nueva, `ethics_body_max_bytes` = 32 768, para el cuerpo JSON de las tres rutas que
     escriben en U13, igual que hizo U5 con `review_body_max_bytes`.
2. **`413` en vez de `422`** para la nota sobre el tope (NFR-U1-03).
3. **Latencia de la comparación de testimonio** (pregunta 2). p95 en el servidor y en la consola, con una
   sesión sintética de 2 000 turnos y 250 000 caracteres.
4. **`AccessLog`** (pregunta 3). Toma los 500 ms de U3 y U7, sin reintento. Su latencia propia la mide U13,
   como pidió U3.
5. **`Job` de retención** (pregunta 4). Aquí solo se nombran como requisitos para Infrastructure Design el
   `activeDeadlineSeconds`, los recursos, el montaje de los volúmenes con el mismo UID de `session-api` y el
   Secret de `veridicus_retention`. Se suma una sola ejecución a la vez y el fallo cerrado ante Redis caído.
6. **Comando de consulta** (pregunta 5). Corre con `kubectl exec`, como `verify_store` de U7, sin `Job` ni
   rol propio. Devuelve 1 000 filas por defecto y 10 000 como máximo, y avisa si trunca.
7. **Riesgos de la pregunta 6** (no bloquean). Van a `reliability-requirements.md` §4 para decidirlos en la
   aprobación.

---

## 3. Preguntas

Sin preguntas: todo lo fijan las fuentes.

Las preguntas abiertas 1 a 5 del Functional Design se resuelven con las fuentes aprobadas (sección 2). La
cifra del recordatorio de bienestar no tiene fuente en el repositorio, pero no cambia el alcance, el riesgo
ni lo que sale del clúster: es un aviso que no bloquea (DD-05). Por eso va como propuesta a la tabla
NFR-U13 y no como pregunta.
