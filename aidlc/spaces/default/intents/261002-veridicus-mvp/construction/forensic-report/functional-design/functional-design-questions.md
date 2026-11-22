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

---

# Segunda pasada — cambio 01, adenda 02 y revisiones 3 (2026-11-22)

**Unidad.** U7 `forensic-report` (tipo `service`, MUST, tamaño L; componente **ReviewReport**, antes
ForensicReport). Conserva el directorio y el slug (UG-08), pero sus artefactos hablan de «reporte de
revisión» (`review_report`, VE-03). Según la revisión 3 de `unit-of-work.md` entrega: finalizar la sesión
(US2.4), consolidar con sus precondiciones, escaneo y SHA-256 (US6.1), descargar con verificación de
integridad (US6.2), corregir con una versión nueva (US6.3) y **exportar con marca de agua, roles y *hash*
por exportación** (US15.8, VE-13, A-3). El reporte cita los dos fragmentos de cada hallazgo y lleva el
aviso de VE-01. **Sale** todo lo que venía del marco de verdad: escenario y su SHA-256
(`ScenarioReader`), umbral de similitud, Hechos No Documentados con su Paquete de Contexto de Traspaso y
CoT (cambio 01, DD-10).

## Lo que ya está decidido y no se vuelve a preguntar

| Tema | Qué está decidido | Fuente |
|---|---|---|
| Contenido del reporte | Transcripción por turnos con hablante y página; todas las sugerencias con estado final y nota; por cada una, hecho, tipo, las dos citas con turno y página, avisos y observaciones; perfil, `config_sha256`, `prompt_sha256`, versión del analizador y registro de modelos de cada corrida; modo fragmentado y su ventana; «Tramo no evaluado» y «Modo final no completado. Revisión manual requerida» con su código; quién consolidó y cuándo; «Sin sugerencias de revisión» si no hay | FR7.2; AC6.1.3, AC6.1.8 (revisión 3) |
| Sugerencia editada | Se muestran la de la IA (hecho, citas y observaciones intactas) y la reformulación del analista, rotuladas; la reformulación no se escanea | P3 = A (primera pasada); AC5.5.2 (d) |
| Aviso de VE-01 | Texto versionado, en la cabecera y al final de cada sección de página del reporte; el escáner excluye solo esa cadena, leída del mismo archivo | VE-01; AC15.5.2; A-1 |
| Vocabulario | La lista de C8 suma los términos de VE-02 («prueba», «probatorio», «pliego», «inculpa», «miente», «engaño», «falso») en una versión nueva por PR; el reporte generado se escanea `[N1]` | VE-02; AC5.5.1; FD de U11 (`scan(text, literal_sources)`) |
| Precondiciones | Bloquean, en este orden: sesión sin finalizar, modo final sin lanzar, análisis en cola o procesando, sugerencias pendientes; se listan todos. Un modo final o tramo en `error` no bloquea: lo avisa el diálogo, con el foco inicial en «Cancelar». Un hallazgo que llega con el diálogo abierto da `409` al confirmar | FR7.1; AC6.1.1, AC6.1.2, AC6.1.9; mockups §6.9 |
| Sesiones sin modo final posible | Una sesión bloqueada por incidente, terminada o con la retirada del consentimiento se consolida sin exigir un modo final terminado; el reporte declara el incidente, la terminación o la retirada con su hora y los tramos sin evaluar | FD-U4-19; FD-U6-11 |
| Transiciones | Finalizar es ruta de U7 desde `open`, `paused`, `suspended` y `blocked`; consolidar, desde `finalized` y `terminated`; `consolidated` es el único estado final | FD-U6-12, FD-U6-18; FD de U6 §3 |
| Roles | Leer sesiones y reportes: todos los analistas y el `admin`. Exportar: el analista dueño y el `admin`; el `investigador` y el analista que no es dueño reciben `403`. Consolidar y corregir: solo el dueño. **Sustituye a P4 = A** de la primera pasada, que daba `403` al `admin` | FR1 (tabla de roles); VE-13; AC15.8.1; AC6.1.7, AC6.3.5; C1 `/exports` (`x-veridicus-owner-only-for-role: analista`) |
| Exportación | Cada exportación es un artefacto propio: marca visible con usuario y hora en la cabecera y en cada página, SHA-256 de la versión en la cabecera, `export_sha256` que coincide con `sha256sum`; entidad ReportExport de solo inserción | VE-13; A-3; FR7.3, FR7.4; components (ReviewReport, ReportExport); C1 `/reports/{id}/exports` |
| Registro de acceso | U7 define el puerto `AccessLog` (C23). La ruta de exportación lo llama ella misma con usuario, versión y `export_sha256`, y no entrega si el registro real falla. Con el adaptador por defecto (sin U13), exporta igual, avisa en el log solo con IDs y `/readyz` informa `access_log: not_configured` con `200` | UG-09; C23; FD de U3 F11 y FD-U3-05; ADR-016 |
| Aclaraciones neutras | No entran en el reporte; el escaneo de contenido del reporte lo comprueba sobre un *fixture* | FD de U8 P6 = A |
| Retención | ReviewReport implementa su parte de `Purgeable.purge_session`: borra ReportExport y luego ReportVersion de la más nueva a la más antigua, con sus archivos, y devuelve IDs y SHA-256, nunca texto | C24; VE-12; components (EthicsGovernance) |
| Concurrencia y archivo | `open_round(for_update=True)`, orden sesión → ronda con `change_cursor.bump`, archivo antes que fila, 1 réplica con `Recreate`, barrido con margen y limpieza inmediata | NFR Design de U7 (revisión 1); FD-U5-03; project.md § Corrections |
| Turnos colgados | Los vence el supervisor de corridas de U4 (pasan a `error` con `analysis.system` al vencer su plazo), así que nunca bloquean para siempre | FD de U4 (supervisor de corridas); C25 |
| Descartar la copia | Estado `discarded` y `discard_correction_round` en C11 | FD-U5-04 (recoge X1 de la primera pasada) |
| Cifras | Plazos de E/S, tamaño máximo del reporte, latencia de consolidación y de exportación | NFR Requirements de U7; `contracts/limits.v1.yaml` |
| Preguntas P1–P3 de la primera pasada | **Siguen.** P1 (descarte, ahora FD-U5-04), P2 (archivo antes que fila) y P3 (IA y analista) | Respuestas de la primera pasada |

## Cómo se registra la revisión 2

- Los cuatro artefactos (`entities.md`, `rules.md`, `functional-spec.md`, `traceability.json`) llevan una
  cabecera «Revisión 2 (2026-11-22), segunda pasada por el cambio 01 y la adenda 02» que sustituye a la
  revisión 1 del 2026-10-03, nombra qué sigue, qué sale y qué entra, y llama al módulo ReviewReport.
- **IDs estables** (regla de project.md): ningún ID se renumera. Lo que sale queda «Retirado» con su motivo:
  - Entidades y atributos: `scenario_version_id`, `scenario_sha256` y `similarity_threshold` de
    ReportVersion; `undocumented_facts` de ReportContent; las referencias a ScenarioVersion y
    HandoffPackage.
  - Reglas: las partes de BR3.1 sobre fragmento, ID de documento, CoT y Hechos No Documentados se
    reescriben con el contenido de FR7.2 (sigue el ID); BR5.3 se reescribe con los roles de la tabla de
    FR1 (sale el `403` al `admin`).
  - Flujos: F2 paso 4 pierde `ScenarioReader.version_info`.
- **Entra** lo nuevo con números nuevos: entidad ReportExport y la interfaz del puerto `AccessLog`; reglas
  desde **BR9.1** (exportación, marca y *hash*), **BR10.1** (retención) y **BR11.1** (aviso de VE-01,
  avisos de la sesión y vocabulario de VE-02); flujos desde **F8** (exportar) y **F9** (borrar por
  retención); escenarios desde **E11** (la primera pasada tenía 10 sin número; se numeran E1–E10 en su
  orden actual).
- `traceability.json`: entran AC15.8.1, AC15.8.2, AC15.5.2 y AC6.1.8–AC6.1.9, con los AC de US6.1 de la
  revisión 3; los AC retirados salen de `upstream_ids` y las reglas o atributos retirados van en
  `reverse` como `N/A` con «Retirado (cambio 01)».
- Las precisiones a artefactos aprobados (contract-summary, components, `stories.md`, FD de U4, U5, U6 y
  U3) van a una tabla **FD-U7-01…** en `functional-spec.md`, sin editar los originales; decides en la
  aprobación. La tabla X1–X6 de la primera pasada se revisa fila por fila: X1 la recoge FD-U5-04; X4 ya
  está en C1; X5 la sustituye la tabla de roles de FR1; X2, X3 y X6 siguen o se reescriben como FD-U7.
- Los hallazgos de `reviews/review-01.md`: R-02 y R-03 quedaron cerrados en NFR Design de U7 (1 réplica,
  margen del barrido, `open_round(for_update=True)`); R-04 lo cierra el supervisor de corridas de U4;
  R-01 y R-05 se cierran con los puntos 1 y 9 de la lista siguiente.

## Lo que el diseño resolverá sin preguntar

1. **Escaneo del reporte (cierra R-01).** Se llama a `scan(text, literal_sources)` de U11 con
   `literal_sources` = los textos de todos los turnos, como hace el analizador (FD de U11). Así la
   transcripción y las dos citas no se escanean; tampoco la reformulación, las notas ni el aviso (A-1).
   Sin eso, con «prueba» en la lista de VE-02, casi ningún testimonio se podría consolidar. Va como
   precisión a AC5.5.1 y lleva control negativo: «miente» en un texto del sistema del reporte lo hace
   fallar; dentro de un turno, no.
2. **Contenido nuevo del reporte.** BR3.1 y la plantilla de `format_version` siguen FR7.2. Las secciones
   de avisos de la sesión: modo fragmentado, misma familia (AC13.1.2), incidente de anonimización
   (`blocked_code`), terminación y retirada del consentimiento con su hora (FD-U6-11, FD-U6-21). Todo se
   lee de `SessionReader.snapshot` (BR19.4 de U4); `format_version` sube, y las versiones viejas no se
   tocan.
3. **Reporte sin rastros del marco de verdad.** Sale `ScenarioReader` de las dependencias de ReviewReport
   (precisión a C11 si aún lo declara). El archivo dorado de AC6.1.3 se regenera.
4. **Precondiciones nuevas.** «Modo final sin lanzar» entra en la guardia después de «sin finalizar»,
   con el code `report.final_mode_not_launched` (va a C1 como precisión si no existe). Las sesiones de
   FD-U4-19 y FD-U6-11 quedan exentas. Los tramos en `error` se rotulan «Tramo no evaluado» con su code.
5. **Exportación, en este orden:** autorización por rol y dueño (mecanismo de F2 de U3); versión
   existente (`404`); recálculo del SHA-256 del archivo de la versión (`409 report.integrity_mismatch` si
   no coincide); armado de los bytes con la marca (usuario, hora de Colombia y UTC, SHA-256 de la
   versión) y el aviso; escaneo de las cadenas fijas de la marca; cálculo de `export_sha256`; en una
   transacción, inserción de ReportExport y `AccessLog.record`; *commit*; envío con
   `X-Veridicus-Export-SHA256`. Si el registro real falla, se revierte y no sale ningún byte (code
   nuevo para la tabla de precisiones). **El archivo exportado no se guarda**: solo su *hash*, para no
   multiplicar copias del testimonio (VE-12). Es módulo guardia con 100 % de ramas.
6. **Botón para quien no puede exportar.** «Descargar reporte» queda deshabilitado y enfocable con el
   motivo «Solo el dueño de la sesión o un administrador pueden exportar el reporte», como AC5.6.4, en
   vez de dejar que falle con `403`; el `403` de la API sigue y tiene su prueba (mockups §11, US15.8).
7. **El `admin` en M5.** Abre M5 en solo lectura, con el banner de AC5.4.2, ve la lista de versiones y
   exporta; no ve «Corregir reporte» ni «Descartar copia».
8. **Retención (C24).** El borrado usa el usuario de base `veridicus_retention` (el de la aplicación no
   puede borrar, BR4.4) y borra el archivo antes de la fila, para no dejar archivos sin dueño. Devuelve
   los IDs y el SHA-256 de cada versión borrada para el acta. Si un archivo ya no está, se registra y
   sigue. Prueba de nivel 1 con reloj simulado (parte de U7 de AC15.7.2).
9. **Compatibilidad de los cambios (cierra R-05).** Cada precisión a C1 y C11 indica la versión menor que
   la recibe y el orden de los PR (contratos de U1 primero, después el código de U7). El estado
   `discarded` amplía un enum: se declara como cambio menor con la nota de que todo `match` sobre el
   estado de la ronda debe tener rama por defecto, y la prueba de contrato lo comprueba.
10. **Accesibilidad y auditoría.** M5 y los diálogos nuevos entran en la suite `axe` de U4 (US5.6);
    ReportExport sigue la convención de auditoría de U3 (US8.4).

---

## P5 — Qué hace la ruta `/download` ahora que existe la exportación

C1 tiene dos rutas: `/download`, que entrega el Markdown exacto de la versión a **cualquier** analista y
al `admin` (sin marca), y `/exports`, que entrega el archivo con marca solo al dueño y al `admin`. Pero
AC15.8.1 dice que el analista que no es dueño, al pedir «la descarga», recibe `403`, y VE-13 pide que
cada archivo que sale de la consola lleve la marca. Si `/download` sigue igual, un analista no dueño saca
el reporte sin marca y sin registro de exportación. M5 también necesita algo para su «Vista previa del
reporte», que leen todos los analistas y el `admin` (AC5.4.2).

A. **Un solo camino para sacar un archivo.** «Descargar reporte» llama siempre a `/exports`.
   `/download` deja de ofrecer un archivo y pasa a ser la **lectura de la versión** para la vista previa
   de M5 (todos los lectores, se muestra en la página y se registra como `report_version` en
   `AccessLog`, FD-U3-05), con el mismo recálculo del SHA-256. AC6.2.1 se cumple con la exportación:
   «coincide con el registrado **para esa exportación**» (FR7.3). Va como precisión a C1 y a AC6.2.1.
   (Recomendada)
B. **Dos archivos.** `/download` sigue entregando los bytes exactos de la versión, pero solo al dueño y
   al `admin` (los mismos roles que exportar), para comprobar el SHA-256 de la versión con `sha256sum`; la
   exportación con marca es aparte. Sale un archivo sin marca, y hay que decir en VE-13 que no cuenta
   como exportación.
C. **Como está en C1.** `/download` sin marca para todos los analistas y el `admin`. Exige cambiar
   AC15.8.1, porque contradice su `403`.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P6 — Qué es una «página» en un reporte Markdown

AC15.5.2 pone el aviso de VE-01 «en la cabecera y al final de cada sección de página», y AC15.8.2 pone la
marca de agua «en la cabecera y en cada página». Un Markdown no tiene páginas: cómo se parta decide si una
hoja impresa o un fragmento copiado se queda sin aviso ni marca.

A. **Por secciones y bloques fijos.** El reporte tiene secciones H2 fijas (datos de la corrida,
   transcripción, sugerencias de revisión, avisos, consolidación). El aviso, y en la exportación también
   la marca, cierra cada sección H2, y dentro de la transcripción y de las sugerencias se repite cada
   bloque de N turnos o N sugerencias. La cifra N la propone el diseño en la tabla de precisiones. Sigue
   siendo Markdown, determinista y sin dependencias nuevas. (Recomendada)
B. **Un PDF con páginas reales.** La exportación se genera en PDF con aviso y marca en el encabezado y el
   pie de cada página. Cumple al pie de la letra, pero suma un motor de PDF a `session-api`, fuentes y
   pruebas de bytes deterministas, y cambia el `text/markdown` de C1.
C. **Saltos de página marcados en el Markdown** (un separador cada N líneas que un conversor convierte en
   salto). Las «páginas» solo existen si el lector usa ese conversor.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P7 — Cómo se finaliza y se consolida una sesión importada

Una sesión importada nace `open` y cerrada a turnos nuevos, y mockups §6.2 le quita «Finalizar sesión».
Pero la guardia exige una sesión finalizada para consolidar, y la máquina de U6 solo consolida desde
`finalized` o `terminated`. Además, MTTV empieza en `finalized_at` (NFR7): en una importada no hay un
momento en que el analista «finaliza».

A. **Finalizar implícito al consolidar.** En una importada, la transacción de consolidar registra
   `open → finalized → consolidated` (dos filas de historial, actor el dueño) y la guardia no muestra
   «Finaliza la sesión para consolidar». Las importadas quedan fuera de MTTV, que se mide en sesiones
   guiadas (el conjunto sintético de NFR7). Precisión a FD de U6 (tabla de transiciones) y a AC6.1.1.
   (Recomendada)
B. **Mostrar «Finalizar sesión» también en las importadas**, con un diálogo sin la frase de los turnos;
   MTTV empieza al pulsarlo. Es un paso más para el analista, y es una precisión a mockups §6.2 y a
   AC2.4.1.
C. **Una transición nueva `open → consolidated`** solo para importadas, sin pasar por `finalized` y fuera
   de MTTV. Es más simple, pero el historial de la sesión no tiene finalización.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P8 — Si se puede exportar una versión que ya no es la vigente

Una corrección deja la versión anterior intacta y en la lista (FR7.5, AC6.3.4). `/exports` recibe un
`report_version_id`, así que nada impide exportar la versión 1 cuando ya existe la 2. Eso conserva el
rastro completo, pero puede hacer circular un reporte que el propio analista corrigió.

A. **Se exporta cualquier versión**, y la cabecera de una no vigente dice «Reemplazada por la versión N
   el <fecha>», junto a la marca. Así queda el rastro, y quien la lee sabe que hay una más nueva.
   (Recomendada)
B. **Solo la vigente.** Las anteriores se ven en la lista con su SHA-256, pero exportarlas responde
   `409` con un code nuevo (`report.version_superseded`).
C. **Cualquier versión, sin rótulo.** La exportación es igual para todas las versiones.
X. Other (please specify)

[Answer]: A **Mode:** guided
