# Preguntas de Functional Design — U7 forensic-report

**Unidad.** U7 `forensic-report` (tipo `service`): finalizar la sesión e iniciar MTTV (US2.4),
consolidar con sus precondiciones, escaneo y SHA-256 (US6.1), descargar con verificación de integridad
(US6.2) y corregir con una versión nueva (US6.3). Usa las rondas y decisiones de U5; no las define.

**Lo que ya está decidido y no se vuelve a preguntar.** Solo el dueño finaliza, consolida y corrige
(`403` para otro analista, `admin` o identidad de servicio; ADR-009, AC6.1.7, AC6.3.5). Consolidar exige
sesión finalizada, 0 turnos en cola o procesando y 0 sugerencias pendientes en la ronda abierta; los turnos
en «Error» no bloquean y se rotulan «turno no evaluado» con su `code` (AC6.1.1, AC6.1.3). La consolidación
lee, escribe la versión y bloquea la ronda en una sola transacción y de dos simultáneas gana una
(`409 report.conflict`; C11, AC6.1.6). El reporte se escanea con el vocabulario prohibido excluyendo citas
literales y texto del analista; si hay coincidencia, `409 report.forbidden_vocabulary` y no hay reporte
(AC5.5.1, ErrorCode de C1). La descarga recalcula el SHA-256 y responde `409 report.integrity_mismatch`
si no coincide (C1). Una corrección abre o retoma la única ronda de corrección, que parte de la versión
vigente; consolidarla crea una versión nueva que referencia a la anterior (FR7.5, C11). MTTV va de
`finalized_at` a la primera consolidación (NFR7). Quedan cuatro huecos.

---

## P1 — Cómo se descarta una copia de trabajo de corrección

El criterio de «Descartar copia» (AC6.3.2) pide eliminar la copia sin crear versión. Pero la copia es una
ronda de revisión de U5, que solo tiene los estados `open` y `locked`, cuyas decisiones son de solo
inserción (AC8.4.2), y el contrato en proceso entre ForensicReport y HumanReview (C11) no trae una
operación de descarte. Sin una decisión, la ronda abierta nunca se podría cerrar sin consolidar.

A. Agregar a la ronda el estado `discarded` (desde `open`, con quién y cuándo, sin volver a `open`) y la
   operación `discard_correction_round` a C11, subiendo el contrato a v1.1.0 en su propio PR. Las
   decisiones de esa ronda se conservan como rastro, pero ya no cuentan para ninguna versión. Como el
   diseño de U5 ya está escrito, el cambio se anota en una tabla de este artefacto y tú decides en la
   aprobación si se actualiza el original. (Recomendada)
B. No permitir descartar: la copia queda abierta hasta que se consolide, y «Descartar copia» desaparece
   de la interfaz (exige cambiar el criterio AC6.3.2 en `stories.md`).
X. Other (please specify)

[Answer]: A **Mode:** guided

## P2 — Orden entre guardar el archivo del reporte y confirmar la transacción

El archivo vive en el volumen persistente y la fila de la versión en PostgreSQL; no hay una transacción
que abarque los dos. Si uno se escribe y el otro falla, puede quedar una versión sin archivo (la descarga
fallaría para siempre) o un archivo sin versión.

A. Primero el archivo, luego la fila: se genera el identificador de la versión, se escribe el archivo con
   ese nombre en un archivo temporal, se fuerza a disco y se renombra; solo entonces se confirma la
   transacción que crea la fila y bloquea la ronda. Si la transacción falla (incluido perder la carrera
   de AC6.1.6), se borra el archivo; un barrido al arrancar elimina archivos sin fila. Nunca existe una
   versión sin archivo. (Recomendada)
B. Primero la fila, luego el archivo: se confirma la transacción y después se escribe el archivo; si la
   escritura falla, la versión queda marcada como dañada y se reintenta. Puede haber una versión
   registrada sin archivo durante un tiempo.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P3 — Cómo aparece en el reporte una sugerencia «editada»

Al editar, el analista escribe su propia reformulación y el fragmento, la cita, el documento y la CoT de la
IA no cambian (US5.2). El reporte debe permitir distinguir qué dijo la IA y qué decidió la persona.

A. Se muestran las dos cosas, rotuladas: «Sugerencia de la IA» (con su CoT intacta) y «Reformulación del
   analista» (con quién y cuándo). La reformulación queda fuera del escaneo de vocabulario por ser texto
   del analista. (Recomendada)
B. Solo la reformulación del analista, con una nota «editada por el analista»; la CoT original se omite.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P4 — Quién puede leer y descargar un reporte

El contrato marca como «solo dueño» finalizar, consolidar y corregir, pero no limita quién lista y
descarga las versiones. AC5.4.2 dice que otro analista abre la sesión en solo lectura y puede leer el
reporte. El reporte contiene el testimonio completo de una víctima.

A. El dueño y los demás analistas pueden listar y descargar (solo lectura); un usuario `admin` o una
   identidad de servicio recibe `403`, porque administra usuarios y no casos. (Recomendada)
B. El dueño, los demás analistas y los `admin` pueden listar y descargar.
C. Solo el dueño puede descargar; los demás analistas ven la lista de versiones sin descargar.
X. Other (please specify)

[Answer]: A **Mode:** guided
