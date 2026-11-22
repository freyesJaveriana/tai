# Preguntas de NFR Requirements — U7 forensic-report

**Unidad.** U7 `forensic-report`: finalizar, consolidar, guardar, verificar y descargar el reporte, y
la ronda de corrección (`functional-design/functional-spec.md`, `rules.md`).

**Sin preguntas nuevas.** Las metas de esta unidad salen de lo ya decidido: MTTV < 10 minutos (NFR7),
reporte en el volumen con SHA-256 (FR7.3), solo inserción (NFR11), los *timeouts* y la base de
`session-api` de U3 y U4, y la frontera del clúster de §1 del diseño funcional. No hay valores abiertos
que dependan del humano.

---

# Segunda pasada — cambio 01, adenda 02 y Functional Design revisión vigente (2026-11-22)

**Sin preguntas: todo lo fijan las fuentes.** Ninguna decisión de esta pasada enfrenta dos fuentes
aprobadas sin una salida que las cumpla a las dos, ni cambia el alcance, el riesgo aceptado o un dato
que sale del clúster (regla de `project.md` del 2026-11-22). Lo que se aplica sin preguntar queda en la
tabla NFR-U7-xx de `security-requirements.md` §6 y se presenta en la aprobación.

## Lo que ya está decidido

- Functional Design de U7, revisión 2 (aprobado hoy): módulo ReviewReport; P5 = A (la descarga es la
  exportación y `/download` es la lectura de la vista previa); P6 = A (página = sección H2 fija o bloque
  de N = 25); P7 = A (la importada se finaliza al consolidar y queda fuera de MTTV); P8 = A (se exporta
  cualquier versión, con rótulo de reemplazo); exportación con marca, `export_sha256` y sin guardar los
  bytes (BR9); retención por `purge_session` (BR10); el `admin` lee y exporta (FR1, VE-13).
- Adenda 02: VE-01 (aviso en cada página), VE-02 (vocabulario), VE-12 (retención por `Job`), VE-13
  (exportación) y las precisiones A-1, A-2 y A-3.
- U1: `limits.exceeded` responde siempre `413`; C25 no admite nulos y cada cifra entra cuando su unidad
  dueña la fija (NFR-U1-03, NFR-U1-07).
- U2: tres usuarios de base de datos; el `Job` de retención vive en `deploy/jobs/`, con `backoffLimit: 0`,
  y monta en escritura el volumen de reportes (NFR10.7, NFR10.16 de U2).
- U3: el registro de una lectura corre en un punto de guardado de 500 ms y «la exportación la decide U7;
  si no fija otro, usa el mismo valor» (NFR-U3-05); las métricas de `session-api` son internas y no van a
  C15 (NFR-U3-03); un error fuera de la jerarquía es `500 system.internal` y un *timeout* de base es
  `503 system.unavailable` (NFR10.17 de U3).
- U4, U5 y U6: `transcript_max_chars` = 250 000, `transcript_max_turns` = 2 000, `turn_max_chars` =
  20 000, `review_text_max_chars` = 2 000, sondeo de 2 s y 15 s.
- Infrastructure Design de U7, revisión 1 (aprobado): PVC de 2 GiB, cuota propia con dos *gauges*
  (P3 = A), `reports/` como subdirectorio `0700`, `Recreate` y 30 s de gracia (P1 = A), respaldo conjunto
  a pedido (P2 = A).

## Cómo se registra la revisión 2

- Los requisitos conservan su ID; cada fila dice si **se mantiene**, **cambia**, es **nuevo** o queda
  **Retirado** (sin renumerar). Lo nuevo toma el número siguiente de su grupo.
- Se cierran los hallazgos R-01 a R-05 de `reviews/review-01.md` en las filas que los citan.
- Las precisiones de la revisión 1 (§6 de `security-requirements.md`) que ya entraron en C1, C11 o en el
  Functional Design se dan por cerradas; las que cambian quedan en la tabla NFR-U7-xx.

## Lo que el diseño resolverá sin preguntar

Respuestas a §12 del Functional Design:

1. **Plazos de la exportación y tamaño máximo.** Plazo total de 10 s, lectura del archivo dentro del
   plazo del volumen (5 s) y `AccessLog.record` en 500 ms. Cifra nueva de C25 `report_max_bytes` =
   8 MiB; la exportación cabe en esa cifra más 64 KiB. Todo se arma en memoria dentro del `limits.memory`
   de 768 MiB de la API (NFR-U7-01, NFR8.1, NFR8.9, NFR10.17).
2. **Costo del SHA-256 en la vista previa.** Se recalcula en cada lectura, sin caché, porque una caché
   ocultaría una alteración. Con 8 MiB cuesta menos de 50 ms. La consola no vuelve a pedir la vista previa
   en el sondeo (NFR3.4, NFR3.15).
3. **Plazo del adaptador real de `AccessLog`.** 500 ms, como U3; aquí un fallo o un vencimiento revierte
   la transacción y responde `503 report.export_not_recorded` sin bytes. Tiene métrica y regla
   informativa (NFR-U7-09, NFR11.7, NFR15.5).
4. **Duración de `purge_session`.** p95 ≤ 2 s con 10 versiones y 100 exportaciones, dentro del
   `activeDeadlineSeconds` del `Job` (NFR3.14, NFR10.27).
5. **Efecto de N = 25.** Los puntos de página añaden menos del 2 % de bytes en el caso máximo y no
   cambian las metas de latencia (NFR3.3, NFR8.5).
6. **MTTV solo en guiadas.** Sí: NFR7.1 y NFR7.3 lo dicen, y el arnés mide todas las transcripciones del
   conjunto sintético cargadas como sesiones guiadas (NFR-U7-10).

Además: el fallo de escritura del volumen responde `500 system.internal`; `verify_store` corre como
comando de solo lectura dentro del contenedor de la API (cierra R-01 y se ajusta a los tres usuarios de
U2); el `Ingress` no escribe en disco las respuestas con el reporte; el paquete pasa a `review_report`
(glosario de `team.md`).
