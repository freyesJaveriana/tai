# Resumen del código: U1 `contracts` (Bolt B1)

Bolt B1 fusionado en `main` con *squash* en eb9d851 (PR #42). Se construyó con el loop de agentes del cambio 04 (DT30): 33 tareas del plan y 12 correctivas en los PR #5 a #41. Cada tarea pasó una revisión adversarial VERDE. Las tareas, bitácoras e informes están en `docs/loop/`; las decisiones del humano, en `decisiones-humano.md` (E-1 a E-45 y precisiones P-*).

## Archivos creados y modificados

La lista completa está en `source-manifest.json`, junto a este archivo. Comparado con la base 20a8cc4, B1 deja esto:
- **`contracts/`**, el paquete de contratos. Sus partes:
  - esquemas versionados: `analyzer/v1` (copia de C6 con F7), `api/` (C1 v2, C21 y la ruta interna de voz), `queues/` (C2, C3 y C5 v2), `integrity/` (C7 v2, C8 v2, el aviso, los casos de escaneo y la aclaración neutral), `profiles/` (C18), `model_calls/` (C13), `cli/` (C19 v2), `errors/`, `health/` (C16), `metrics/` (C15), `format/`, `ui/` y `limits.v1.yaml` (C25);
  - `src/veridicus_contracts/`, con la carga, el registro, la huella JCS, la validación, las interfaces C10–C12, C23 y C24, `checks/` (24 guardias) y `tools/` (herramientas deterministas);
  - `tests/`, con contratos, guardias AUTONOMIA, `checks`, `tools` y `typing`;
  - `ts/`, la mitad TypeScript con los mismos veredictos;
  - `vendor/`, con los meta-esquemas y su `SHA256SUMS`.
- **`libs/errors/`**: la jerarquía única de excepciones del catálogo v2.
- **CI y ganchos**:
  - `.github/workflows/contracts-level0.yml`, con los *jobs* `contracts-level0` y `errors-level0`;
  - `.github/workflows/repo-level0.yml`;
  - `.pre-commit-config.yaml`, `.yamllint.yaml` y la plantilla de PR.
- **Guardias del repositorio público**: `scripts/check-no-insumos.sh`, `check-no-cluster-ids.sh` y `check-no-datos-personales.sh`.
- **Repositorio público, sin datos del clúster ni datos personales del autor**: `docs/validacion-zine/`, `docs/devlog.md`, `plan-aidlc.md`, la propuesta del TG en `research/06-documentacion-propia/` y `stories.md`, este último solo en los nombres que autorizó E-45.
- **Loop**: `.claude/agents/codificador.md`, `.claude/agents/revisor.md` y `docs/loop/`.

## Decisiones clave de implementación

- **E-1:** los módulos van en `contracts/src/veridicus_contracts/` en lugar del mapa `python/`, porque la instalación editable, el sdist y mypy no veían el mapa. De ahí sale la nota K-59 (ver Desviaciones).
- **E-5:** el esquema de C18 se escribe junto con C2, que lo referencia.
- **E-7 y E-8:** C8 v2 suma ya los términos de VE-02 y sus formas verbales comunes.
- **E-10 a E-18:** las guardias de T15 encontraron defectos reales en contratos ya fusionados. Los corrigieron las correctivas T15b y T15c; la más grave fue el tope del texto de los turnos en C2.
- **E-28 a E-31:** versión semántica `x-veridicus-version` en la raíz de cada contrato (T18c).
- **E-32:** el repositorio es público. No se usan nombres del clúster ni datos del piloto, y las guardias de insumos, identificadores y datos personales corren en la CI.
- **E-33:** la suite se aceleró hasta caber en los 60 s de NFR2.1 sin quitar ninguna prueba (T18d).
- **E-44 y E-45:** `contracts-level0` y `errors-level0` se piden como comprobaciones obligatorias de `main`. La guardia de identificadores revisa todo el repositorio, sin exenciones por carpeta.
- **P-T30-1 a P-T30-3:** los correos del autor se comparan por SHA-256, sin escribirlos. `.gitleaks.toml` no cambia, porque `gitleaks git` revisa la historia, que conserva los datos.

## Cobertura de pruebas

- La suite Python (`timeout 60 uv run --frozen --offline --directory contracts pytest`) tiene unas 2900 pruebas y corre en unos 30 s. Cumple el 80 % de líneas por paquete y el **100 % de ramas** en los módulos guardia (V-GUARD, paso 5 del informe de cobertura).
- `libs/errors` y la mitad TypeScript (Vitest, sin red) tienen sus propias suites.
- En CI bloquean `contracts-level0` (los 12 pasos de §4.13), `errors-level0` y `repo-level0`.
- Trazabilidad: `traceability.json` cubre 116 IDs, todos los AC, NFR y BR de U1.
  - 109 están en `OK`, cada uno con una prueba o un módulo existente.
  - 6 son `N/A`, porque se miden en ejecución en otras unidades.
  - 1 está en `Deferred`: AC12.6.1, que pasa a U12.
  - El sensor de trazabilidad pasa sin hallazgos.

## Desviaciones del plan

- **Correctivas fuera del plan original**, todas con su archivo de tarea y su revisión:
  - T02b: id relativo y URI repetida;
  - T15b y T15c: contratos que encontraron las guardias de T15;
  - T17b: patrón único de fecha;
  - T18b: patrones acotados;
  - T18c: versión semántica;
  - T18d: suite en 60 s;
  - T22b: la guardia de *workflows* exige SHA y permisos de lectura;
  - T27: servidor desde `ZINE_SERVIDOR`;
  - T28: `ruff format` y `yamllint`;
  - T29: identificadores en todo el repositorio;
  - T30: datos personales del autor.
- **Cambio 05** (E-32): etiqueta `contracts-v<versión>` igual a la versión del `pyproject.toml`, README con instalación por Git, huellas aprobadas de C6 fijadas y repositorio público. Sus tareas son T23 a T26.
- **K-59.** `contract-summary.md` y `bolt-plan.md` todavía citan las rutas antiguas `contracts/python/`. Por la regla de no editar artefactos aprobados no se cambian: E-1 manda, y la ruta vigente es `contracts/src/veridicus_contracts/`.
- **Pendientes que no bloquean** (K-76, para B10):
  - formas que la guardia de identificadores no detecta: una asignación con ámbito, un nodo en el nombre de un archivo, `.psd1`, una URL `file:` y un host concatenado;
  - un exento seguido de punto y cifras en la guardia de datos personales;
  - `ruff format` sin correr en `libs/errors` en la CI.
- **Paso 5 de Code Generation fuera de orden.** Se hizo después de fusionar el PR del Bolt (#42), no antes como pedía el cambio 06 §2. Entra a `main` por su propio PR desde `aidlc/b1-cierre`.
