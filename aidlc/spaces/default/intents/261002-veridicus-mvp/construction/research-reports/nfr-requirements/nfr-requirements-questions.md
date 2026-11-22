# Preguntas de NFR Requirements — U12 research-reports

- **Unidad:** U12 `research-reports` (tipo `service`). Bolt B12, después de la demo (P11 = A de Delivery
  Planning).
- **Componentes:** el módulo ResearchReports de `session-api`, las rutas `/research-reports*` de ConsoleApi
  (rol `investigador`) y la pantalla M8 de AnalystConsole.
- **Situación:** primera pasada (revisión 1, 2026-11-22), sobre el Functional Design revisión 1 de U12
  (BR1.1–BR8.4, F1–F6, E1–E40, FD-U12-01 a FD-U12-12), aprobado hoy.
- **Artefactos de esta etapa para un `service`:** los seis documentos y `traceability.json`.

---

## 1. Lo que ya está decidido y no se vuelve a preguntar

| Tema | Decisión | Fuente |
|---|---|---|
| *Canary* «CANARIO-7f3a» | `422` `research.invalid_report` en un hallazgo, como nombre de campo y en los campos con patrón; el nombre del archivo no se guarda ni se registra | CD-03; FD-U12-01; P1 = A del Functional Design |
| Contraste con lo versionado | Solo se acepta un reporte del perfil, la tabla de precios y las etiquetas vigentes | P1 = A del Functional Design; BR3.1–BR3.5 |
| `runs[]` | Solo agregados y la huella de entradas, nunca un `interview_sha256` | P2 = A del Functional Design; BR5.2 |
| Origen | `origin` de C19 v2 lo escribe la CLI | P3 = A del Functional Design; NFR-U11-14 |
| Forma de los límites | `limits.exceeded` siempre `413`; C25 sin nulos; cada cifra la fija su unidad dueña; decimales solo en `ratio` y `s` | NFR-U1-01, NFR-U1-03, NFR-U1-07 |
| Topes de las subidas `multipart` | Declaran `x-veridicus-max-bytes` con su nombre de C25 y responden `413` y `415` como Problem Details | NFR10.7 de U1 |
| Tabla `history` | `veridicus_app` solo `SELECT` e `INSERT`; la retención no la toca | ADR-014; convención de auditoría de U3; U2 (tres usuarios de base) |
| Sesión web | 12 h, con cierre a los 30 min de inactividad | U3 |
| Errores de la base | `503` `system.unavailable`, sin filas | Propuesta de U3; §9 del Functional Design |
| Accesibilidad | Suite `axe` de U4, WCAG 2.1 AA, 0 violaciones `serious` o `critical` | BR8.1; D14 de U4 |
| Pila | Python 3.12, FastAPI, SQLAlchemy 2 con psycopg 3, Alembic en un `Job`, `jsonschema` Draft 2020-12, React con TypeScript estricto | `team.md`; U4 (D9, D11) |

## 2. Lo que el diseño resolverá sin preguntar

Las precisiones a artefactos aprobados van a la tabla NFR-U12-xx de `security-requirements.md`. No se edita
ningún original.

1. **Cifras de C25 que son de U12.** `research_report_max_bytes` = 8 388 608 (8 MiB),
   `research_report_max_json_depth` = 8 y una cifra nueva, `research_report_write_timeout_s` = 15. Se
   dimensionan con un reporte sintético del peor caso estimado (240 corridas × 30 llamadas, unos 3,3 MB) y
   con el estimado de la corrida sobre las 10 entrevistas del piloto (unos 0,3 MB). La profundidad natural
   de C19 v2 es 5 niveles.
2. **Volumen de la lista.** Sin paginación hasta 1 000 reportes. Si se superan, la paginación entra por PR
   de U1 sobre C1.
3. **Latencias.** p95 de la subida, del detalle, de la lista y de la comparación, medidas en nivel 1 con la
   marca `perf`.
4. **Defensas del analizador de JSON.** Profundidad comprobada antes de construir objetos, números no
   finitos (incluido `1e400`), enteros enormes y rangos que caben en la base y en el navegador.
5. **Sin disco.** El `multipart` se lee en memoria con su tope. El Ingress de la ruta de subida no puede
   devolver su propio `413` en HTML ni guardar el cuerpo en disco; eso lo fija Infrastructure Design.
6. **`415`.** Una petición que no es `multipart/form-data` da `415` con un `code` nuevo,
   `research.invalid_type`.
7. **Campos nuevos de C19 v2 (NFR-U11-14 y FD-U8-09).** `blocking` y la latencia p50 y p95 por papel se
   guardan y se muestran. `clarifications` pasa el esquema pero no se guarda.
8. **Cobertura.** 80 % de líneas, y 100 % de ramas en la validación, el contraste y el armado de rechazos
   sin eco, porque protegen NFR12.
9. **Empaquetado del catálogo de referencia** (pregunta abierta 4 del Functional Design). Queda para
   Infrastructure Design, con el requisito de solo lectura.

---

## 3. Preguntas

Sin preguntas: todo lo fijan las fuentes.

Las preguntas abiertas 1 a 4 del Functional Design se resuelven con las fuentes aprobadas (sección 2). La 5
(el costo de P1 = A en E18 y E19) no se pregunta aquí: el Functional Design la dejó para decidirla en la
aprobación, y aparece como riesgo en `reliability-requirements.md` §4.
