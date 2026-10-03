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
