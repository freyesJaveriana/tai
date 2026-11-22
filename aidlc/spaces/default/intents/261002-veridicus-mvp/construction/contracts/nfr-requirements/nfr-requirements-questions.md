# Preguntas de NFR Requirements — U1 contracts

**Unidad.** U1 `contracts` (tipo `spec`): contratos versionados en `contracts/` y la suite de
validación de nivel 0 con *fixtures* positivos y negativos; ningún comportamiento en ejecución
(`functional-design/functional-spec.md`, `rules.md`). Por ser `spec`, esta unidad solo produce
requisitos de seguridad, decisiones de pila y trazabilidad: no tiene rendimiento, escalado,
fiabilidad ni observabilidad propios.

**Lo que ya está decidido y no se vuelve a preguntar.** Python 3.12, `pytest` + `pytest-cov`,
Hypothesis, mypy estricto, Ruff y `uv` con un lockfile por paquete; CI en GitHub Actions con
`gitleaks`, `pip-audit` y Semgrep; datos solo sintéticos; formas de C1–C16; reglas BR1.1–BR8.2;
escáner de vocabulario en `libs/integrity_policy` a cargo de U4 (team.md, project.md,
`contract-summary.md`). Solo quedan los huecos de abajo.

---

## P1 — Dónde vive y cómo corre la suite de validación de U1

La suite F1 valida todos los contratos y sus *fixtures* en cada PR. Hay que fijar si `contracts/` es
un paquete con su propio entorno o si la suite vive dentro de otro paquete.

A. `contracts/` es un paquete Python 3.12 autocontenido (su `pyproject.toml`, su lockfile de `uv` y
   su carpeta `tests/`), igual que un servicio; la suite corre con `pytest`, en CPU y sin red.
   (Recomendada)
B. La suite vive en `libs/`, junto al escáner de U4, y `contracts/` solo guarda archivos de datos.
C. La suite vive en el frontend (Node + TypeScript), porque la consola también importa contratos.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P2 — Herramientas para validar los documentos OpenAPI, AsyncAPI y JSON Schema

La suite tiene que comprobar que C1, C14 y C16 son OpenAPI 3.1 válidos, que C2–C5 son AsyncAPI 3.0
válidos y que los *fixtures* cumplen los esquemas. Los validadores oficiales de AsyncAPI están en
Node, mientras que el resto de la suite es Python.

A. Todo en Python y sin red: `jsonschema` (draft 2020-12, con verificación de formatos) para C6, C7 y
   las cargas de los mensajes; `openapi-spec-validator` para C1, C14 y C16; los meta-esquemas
   oficiales de OpenAPI 3.1 y AsyncAPI 3.0 copiados en `contracts/` y fijados por SHA-256 para
   validar C2–C5. (Recomendada)
B. Python para los esquemas JSON y la CLI oficial de AsyncAPI (`@asyncapi/cli`, Node, versión
   fijada) en un *job* aparte de la CI.
C. Spectral (Node) con reglas propias para OpenAPI y AsyncAPI, y Python solo para los esquemas JSON.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P3 — Cómo usa el frontend (TypeScript) los contratos

La consola importa de U1 el OpenAPI de C1, el catálogo de `code`, el catálogo de rótulos
(`ui/result-labels.v1.yaml`) y la lista de vocabulario prohibido C8. Si cada lado escribe sus tipos
a mano, el frontend y el servidor pueden divergir sin que nada falle.

A. Tipos TypeScript generados en el *build* a partir del OpenAPI de C1 y de los catálogos, con una
   comprobación en CI que falla si los tipos generados no coinciden con los contratos. (Recomendada)
B. El frontend importa el YAML o JSON de `contracts/` en el *build* y escribe sus tipos a mano,
   protegidos por una prueba de contrato.
C. No se decide aquí: lo fija U4 cuando construya la consola.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P4 — Cómo prueba la suite que ningún *fixture* tiene datos reales (regla BR1.6)

BR1.6 pide que la suite falle si un *fixture* contiene un nombre, testimonio o expediente que no esté
marcado como sintético, pero no fija cómo se comprueba. Detectar «un nombre real» de forma automática
no es exacto, así que hay que elegir qué se verifica y qué queda a la revisión del PR.

A. Cada *fixture* declara `synthetic: true` y la lista de personas y lugares que menciona; todos deben
   salir de un catálogo cerrado de nombres ficticios (`contracts/fixtures/synthetic-names.yaml`), y la
   suite además rechaza patrones de identificadores reales (cédula de 6 a 10 dígitos, número de
   radicado judicial de 23 dígitos). `gitleaks` cubre los secretos. (Recomendada)
B. Solo la marca `synthetic: true` y la revisión del autor en el PR.
C. *Fixtures* sin nombres propios: solo marcadores como `PERSONA_1`, `LUGAR_1` y `EXP_0001`, y la suite
   rechaza cualquier secuencia con forma de nombre propio fuera de una lista de palabras permitidas.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P5 — Meta de cobertura del código de la suite de U1

Las prácticas fijan 80 % de líneas por servicio Python y 100 % de ramas en los módulos guardia. U1 no
es un servicio, pero sus comprobaciones de reglas protegen AUTONOMIA-03 y AUTONOMIA-05: ningún campo
de veracidad en los esquemas (BR3.3), ninguna ruta que escriba el umbral (BR7.1), los cuatro campos de
la alerta (BR4.1), los tres rótulos (BR6.1) y que cada *fixture* negativo falle por la regla que
declara.

A. Los módulos de comprobación de reglas de la suite son módulos guardia: 100 % de ramas; el resto de
   `contracts/`, 80 % de líneas. (Recomendada)
B. 80 % de líneas para todo `contracts/`, sin módulos guardia.
C. Sin meta de cobertura: los *fixtures* negativos son el control.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P6 — Tiempo máximo de la suite de U1

La suite corre en cada PR (nivel 0) y su salida es la evidencia que exige AUTONOMIA-02; un tiempo
máximo medible evita que crezca sin control.

A. Como máximo 60 s en la máquina de desarrollo (CPU) y en la CI, sin red ni base de datos.
   (Recomendada)
B. Como máximo 3 minutos.
C. Sin límite propio; basta con el tiempo total de la CI.
X. Other (please specify)

[Answer]: A **Mode:** guided

---

# Segunda pasada — cambio 01, adenda 02 y Functional Design revisión 2 (2026-11-22)

**Por qué hay segunda pasada.** La revisión 1 (2026-10-03) se escribió sobre C1–C16 y BR1.1–BR8.2. El
Functional Design vigente de U1 trae C1–C25 (C4 y C9 «Retirado»), BR1.1–BR12.3, tres funciones puras
(FD-U1-10) y el paquete `veridicus-contracts`. Los Functional Design de las demás unidades, aprobados hoy,
piden a U1 contratos, códigos, archivos y cifras nuevos en C25.

**Regla para preguntar** (`project.md`, decisión del humano del 2026-11-22). Solo pregunto cuando dos
fuentes aprobadas se contradicen o cuando la decisión cambia alcance, riesgo o un dato que sale del
clúster. Lo demás lo aplico siguiendo las fuentes y lo anoto en la tabla de precisiones NFR-U1-xx, que
revisas en la aprobación. Quedan **dos preguntas**, P7 y P8: las dos son contradicciones entre fuentes
aprobadas, y P8 además cambia el alcance de B1.

## Lo que ya está decidido

| Tema | Qué queda fijo | Fuente |
|---|---|---|
| Forma y pila de la suite | Las respuestas P1–P6 de la revisión 1 siguen: paquete autocontenido; `jsonschema`, `openapi-spec-validator` y meta-esquemas copiados, todo sin red; tipos TypeScript generados; datos sintéticos con catálogo cerrado; 100 % de ramas en `checks/`; suite en ≤ 60 s | Revisión 1, P1–P6 |
| Inventario | C1–C25 con C4 y C9 «Retirado»; la copia de C6 sin editar, con `SHA256SUMS`; `limits.v1.yaml` (C25); la distribución `veridicus-contracts` con su tabla de rutas | functional-spec §1, BR1.7, BR12.1 |
| Funciones puras | `profiles.validate`, `limits.load` y `registry`, sin E/S | FD-U1-10, BR9.8, BR11.1, BR12.3 |
| Validación también en TypeScript | Validador estricto (ajv `strict`), huella JCS recalculada y registro de esquemas, también en TypeScript y en nivel 0 | contract-summary regla 1; BR1.9, BR9.7, BR12.3 |
| NFR de Inception | NFR1–NFR15. NFR9 está «Retirado» (cambio 01) | requirements §3 |
| Cifras de C25 | U1 nombra cada cifra y valida la forma del catálogo; el valor lo fija la unidad dueña en su NFR Requirements | contract-summary C25; brief de la etapa |
| Vocabulario y aviso | C8 v2 con los términos de VE-02, el aviso de VE-01 con su frase base y los casos de escaneo que ejecuta U11 | BR5.1–BR5.8; adenda 02 |
| Riesgo de FD-U1-14 | Sigue pendiente de tu decisión en la aprobación de Functional Design; aquí no se vuelve a preguntar | functional-spec §9 |

## Cómo se registra la revisión 2

- `security-requirements.md`, `tech-stack-decisions.md` y `traceability.json` pasan a la revisión 2 en
  el mismo archivo, con una nota de cabecera que dice qué cambia y por qué.
- Los requisitos conservan su ID. Lo que sale queda «Retirado» sin renumerar, y lo nuevo toma el número
  siguiente de su grupo (NFR1.2, NFR10.13 en adelante, NFR11.4 y siguientes). Las decisiones D1–D12 de la
  pila conservan su número, y las nuevas empiezan en D13.
- `traceability.json` declara NFR9 como `N/A` («Retirado», cambio 01) y apunta cada NFR a sus `NFRx.y`
  de la revisión 2.
- Las precisiones a artefactos aprobados (contract-summary, Functional Design de U1 y de otras unidades) van
  en la tabla NFR-U1-xx de `security-requirements.md`. Ningún original se edita.

## Lo que el diseño resolverá sin preguntar

Cada punto sale de una fuente aprobada. Entra a los artefactos con su NFR-U1-xx.

1. **Cifras nuevas de C25, solo con su nombre.** Las pidieron las unidades dueñas: `anonymizer_request_max_bytes` y
   `anonymizer_masking_budget_ratio` (FD-U10-13); `review_text_max_chars` y `review_body_max_bytes`
   (FD-U5-02); `research_report_max_json_depth` (FD-U12-12); `retention_max_days`, `retention_min_days`,
   `acknowledgement_validity_days`, `wellness_reminder_interval_s` y `problem_report_note_max_chars`
   (FD-U13-03). Las claves y plazos de U9 (FD-U9-06) y el tamaño del reporte de U7 entran cuando sus NFR
   les den nombre. La suite exige un nombre único por cifra y una unidad de una lista cerrada, que suma
   `ratio`, `days` y `levels`. `limits.load` acepta decimales en `ratio` y en `s`: lo pide FD-U10-13, y
   precisa el «entero» de BR11.1.
2. **Valor declarado igual al catálogo.** Todo `maxLength`, `maxItems` o tamaño de un cuerpo de C1, C2, C5,
   C19 o C21 lleva `x-veridicus-limit: <nombre de C25>`, y la suite comprueba que la cifra coincide con la
   del catálogo. Cierra R-05 de la revisión 1. Las subidas `multipart/form-data` (importación, audio,
   reporte de la CLI) declaran su nombre de C25 y sus respuestas `413` y `415` (R-01 de la revisión 1).
3. **Rutas públicas de C1.** Una lista explícita, cada una con su motivo: `POST /auth/login` y, si apruebas
   FD-U4-08, `GET /notice`. La suite falla ante cualquier otro `security: []`.
4. **Extensiones de C1.** `x-veridicus-access-log` (FD-U3-05) y `x-veridicus-owner-only-for-role`
   (FD-U13-05) se validan contra valores cerrados, igual que `x-veridicus-roles`.
5. **Códigos nuevos.** Entran al catálogo con su clase de excepción (BR7.4), por la regla 6 de
   contract-summary:
   - U3: `user.*`, `auth.too_many_attempts`, `system.internal`, `system.unavailable`;
   - U4: `session.consolidated`, `session.suspended`;
   - U5: `suggestion.not_found`;
   - U6: `session.not_paused`, `session.not_finalized`;
   - U7: `report.final_mode_not_launched`, `report.not_found`, `report.export_not_recorded`;
   - U9: `speech.unavailable`, `speech.text_rejected`;
   - U12: `research.not_found`, `research.not_comparable_kind`;
   - U13: `retention.*`, `ethics.text_version_outdated`, `problem_report.ids_mismatch`.
6. **Archivos nuevos en `contracts/`.** `transcript/speaker-markers.v1.yaml` (FD-U6-08),
   `integrity/clarification-speech.v1.yaml` (FD-U9-05) e `integrity/usage-rules.v1.yaml` (FD-U13-02).
   Llevan versión semántica y ejemplos sintéticos (BR1.6), y los textos de reglas y aviso quedan excluidos
   del escaneo, como el aviso de VE-01.
7. **Cambios de versión.** C19 v2 es un cambio mayor (FD-U11-09, FD-U12-05, FD-U12-07) y sigue cerrado:
   toda cadena es `enum` o tiene `pattern` sin espacios (BR10.1). C3 2.1.0 (FD-U4-02) y C5 1.2.0 (FD-U9-01)
   son cambios menores, con su prueba de compatibilidad de *fixtures* anteriores (BR1.3).
8. **Huella JCS publicada por U1.** Es la función pura que pide FD-U10-12, junto a `profiles.validate`,
   comprobada contra el *fixture* de C18. Así U10 y U11 no tienen dos implementaciones que puedan dar `409`
   en todas las llamadas.
9. **`ModelCall` en los errores tipados** (FD-U10-04). Lo llevan `ContentBlocked`, `Timeout`,
   `ProviderError` e `InvalidOutput`; `AnonymizerUnavailable`, nunca. La suite lo comprueba con mypy
   estricto.
10. **Frontera del clúster (NFR1.1).** El nombre corto de servicio de C21
    (`http://veridicus-anonymizer-proxy:8080`) se admite junto a `.svc.cluster.local` y a las rutas
    relativas. C22 no se copia a `contracts/`, así que ningún contrato declara un dominio de internet.
11. **Paso del paquete (F9).** La construcción e instalación del paquete en un entorno limpio necesita red
    para instalar dependencias. Va en un paso aparte del *job*, fuera del `timeout 60` y de
    `--disable-socket`, con su propio plazo. Lo mismo `pip-audit` (R-04 b de la revisión 1).
12. **Pruebas de tiempo estables.** Los patrones se prueban con un límite de pasos de retroceso y no con
    tiempo de pared (R-04 a). Además, una prueba AST rechaza `YAML(typ='unsafe')` y cualquier cargador
    fuera de `loaders.py` (R-03).

Ningún punto cambia qué datos salen del clúster.

## P7 — Estado HTTP de `limits.exceeded`

Dos grupos de fuentes aprobadas se contradicen. **U4** (E6: turno de `turn_max_chars` + 1 caracteres),
**U6** (E6 y E30: bloque o archivo sobre el límite) y **U12** (E12: reporte sobre
`research_report_max_bytes`) responden `413`. **U5** (E21: nota de `review_text_max_chars` + 1
caracteres) y **U13** (§9: nota sobre el tope) responden `422`. U1 es dueño del catálogo, y BR7.4 da una
clase de excepción por `code`, que un solo manejador traduce a Problem Details. Con un solo `code` y dos
estados, el manejador no puede responder bien a los dos grupos.

A. Un solo estado, `413`, para todo `limits.exceeded`: toda cifra de C25 es un tamaño o un conteo máximo.
   U5 y U13 cambian su `422` en su segunda pasada de NFR, como precisión de su Functional Design.
   **(Recomendada:** la siguen tres de cinco unidades, y el manejador queda con una clase y un estado).
B. Un solo estado, `422`, para todo `limits.exceeded`; cambian U4, U6 y U12.
C. Dos códigos: `limits.exceeded` (`413`) para cuerpos, archivos y conteos de turnos, y un `code` nuevo,
   `limits.field_too_long` (`422`), para la longitud de un campo de texto; el turno de U4 pasa a `422`.
D. El mismo `code` con el estado elegido por cada ruta: el catálogo admite `[413, 422]` y la clase no fija
   el estado. Esto precisa BR7.4 y el manejador único de U3.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P8 — Dónde corre la mitad TypeScript de la suite de U1

Hay una contradicción entre fuentes aprobadas. La revisión 1 de este NFR (P2 = A, D1–D4) dejó la suite
**solo en Python y sin Node**, y anotó como riesgo que el frontend no existe cuando se construye U1. Pero
la regla 1 de contract-summary y las reglas BR1.9, BR9.7 y BR12.3 piden en nivel 0 lo mismo en
TypeScript:
- cargar cada esquema con ajv `strict`;
- recalcular la huella JCS del *fixture* de C18;
- resolver las referencias con `addSchema`.

La consola valida C7 al mostrar una sugerencia (F4). Decidirlo cambia el alcance de B1.

A. U1 suma `contracts/ts/`, un subpaquete con su versión de Node LTS y sus dependencias fijadas en
   lockfile: ajv en modo `strict`, Vitest y una biblioteca de JCS. Corre en el mismo *job*
   `contracts-level0`, sin red tras instalar, y con `npm audit` (`HIGH`+ con corrección). La consola lo
   importa. B1 crece un poco, pero las tres reglas quedan probadas desde el primer Bolt.
   **(Recomendada:** es lo que piden la regla 1 y las tres BR).
B. U1 entrega solo los *fixtures* y las huellas esperadas. La mitad TypeScript la añade la primera unidad
   que crea `frontend/` (U3), como prueba de contrato del consumidor. Hasta entonces BR1.9, BR9.7 y BR12.3
   se prueban solo en Python, y la precisión queda en la tabla NFR-U1-xx.
C. Se retira la mitad TypeScript: la consola solo usa los tipos generados y no valida esquemas en tiempo
   de ejecución. Precisa BR1.9, BR9.7, BR12.3 y F4.
X. Other (please specify)

[Answer]: A **Mode:** guided
