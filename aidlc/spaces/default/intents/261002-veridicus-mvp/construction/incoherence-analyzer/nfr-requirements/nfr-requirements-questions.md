# Preguntas de NFR Requirements — U11 incoherence-analyzer

- **Unidad:** U11 `incoherence-analyzer` (tipo `library`), directorio `u11-incoherence-analyzer`. Prioridad MUST,
  tamaño XL. Bolt B11, la primera rebanada de valor (B1 contratos → B10 anonimizador → B11 analizador).
- **Componentes:** IncoherenceAnalyzer, AnalyzerCli, ModelGateway (puerto, adaptador local de C14, adaptador
  `anonymizer` y cliente HTTP de C21), ExecutionProfiles, IntegrityPolicy (escáner y aviso), `evaluation/`
  y `evaluation/zine/`.
- **Situación:** primera pasada (revisión 1, 2026-11-22), sobre el Functional Design revisión 1 de U11
  (BR1.1–BR14.5, F1–F12, E1–E66, FD-U11-01 a FD-U11-28).
- **Artefactos de esta etapa para un `library`:** `security-requirements.md`, `tech-stack-decisions.md` y
  `traceability.json` (los demás son de `service` y `ui` según el archivo de etapa). Por el peso de NFR3,
  NFR8 y NFR10 en esta unidad, el diseño añadirá también `performance-requirements.md` y
  `reliability-requirements.md`.

Contesta debajo de cada `[Answer]:` con la letra o con tu texto. Son **3 preguntas**. Solo pregunto lo que
cambia qué datos salen del clúster, el alcance de B10/B11 o el riesgo de la compuerta de nivel 2; todo lo
demás lo aplica el diseño (sección 2) y queda en la tabla NFR-U11-xx para que lo corrijas en la aprobación.

---

## 1. Lo que ya está decidido y no se vuelve a preguntar

| Tema | Decisión | Fuente |
|---|---|---|
| Proveedor comercial de la primera rebanada | **Anthropic** es el juez de `comercial-piloto`; su adaptador y su ADR van primero en B10 | P2 = A de U10 (NFR-U10-07) |
| Familia del generador del conjunto sintético | De **Google u OpenAI**, distinta de la del juez y de la del verificador de todo perfil de evaluación | NFR5 B; NFR-U10-07; BR12.1; BR13.5 |
| Juez y verificador | De familias distintas en todo perfil de evaluación; un perfil de demostración puede repetir familia solo si lo declara, con aviso | FR14.4; `project.md`; BR2.4, BR2.5 |
| ADR por proveedor | Cada modelo de `ProviderCapabilityTable` exige el ADR de su proveedor (no entrenamiento, retención ≤ 30 días, región, TLS, dominio) | NFR1.2 de U10 |
| Plazo por llamada mínimo | `model_call_timeout_s` ≥ 200 s para 186 000 caracteres; si U11 fija menos, falla su PR | NFR-U10-04 |
| Formas de C25 y de los errores | `limits.exceeded` siempre `413`; catálogo sin nulos; `limits.load` acepta decimales en `ratio` y `s` | NFR-U1-01, NFR-U1-03, NFR-U1-07 |
| Cifras que fija U11 en C25 | Las de la configuración efectiva que «cambian el resultado del análisis»: `model_call_timeout_s`, `run_deadline_incremental_s`, `run_deadline_final_s`, `fragment_window_turns` y `fragment_overlap_turns` | C18 (esquemas que decide U11); U1 §4 de su NFR |
| Umbrales absolutos del nivel 2 | 100 % de citas verificadas, 0 % de error de formato JSON, permutación en el 100 % de las consultas *offline*, consistencia **> 65 %** al invertir el orden, 0 fugas del anonimizador | `team.md` (nivel 2); NFR4; BR12.3 |
| Escenario A | Se mide con una salida reconocible y frente al desacuerdo entre 3 corridas | `project.md`; BR12.6 |
| Verificación de citas | Regla del piloto: solo se normalizan espacios, « […] » une fragmentos en orden, ENT y plegado con aviso | `project.md`; BR5.5–BR5.7 |
| Modo fragmentado | Con modelos locales, ventanas con solapamiento; lo más distante es una limitación declarada y medida por distancia | `project.md`; P14 = A de iteracion2; BR2.7, BR12.5 |
| Modelos locales medidos en ZINE | Juez Qwen3.6-35B-A3B Q8_0 (SHA-256 `d1a39580…`) y verificador gpt-oss-20b Q8_0 (SHA-256 `bcd455d4…`, familia gpt-oss, apache-2.0); en CPU el modo local es por lotes; JSON forzado con `json_schema` y razonamiento apagado (20/20) | `docs/validacion-zine/reporte.md` (revisión del 2026-11-06, «Diseñar con limitaciones registradas») |
| CPU primero | Niveles 0 y 1 sin GPU ni red; la etapa GPU va aparte, a demanda | NFR2; `team.md`; `project.md` |
| Datos | Nunca datos reales en el repositorio ni en la CI; el corpus solo fuera de Git; los `.sbatch` los lanza el humano | `project.md` y `team.md` (Forbidden); BR11.5, BR14.4 |
| Campo `origin` de C19 v2 | La CLI lo escribe (`local` o `zine`) | P3 = A de U12; NFR12.3 de U1 |
| Permutación en producción | La decide U8 (US10.5) sin cambiar la lógica de la biblioteca | FD-U11-06 |

## 2. Lo que el diseño resolverá sin preguntar

Las precisiones a artefactos aprobados irán a la tabla NFR-U11-xx de `security-requirements.md`. No se
edita ningún original.

1. **Cifras de C25 que fija U11** (propuesta; cada una entra al catálogo por PR de U1 antes del código de
   B11). El catálogo guarda el **máximo** que necesita cualquier sitio (ZINE, por lotes en CPU) y cada
   despliegue lo baja con `VERIDICUS_LIMIT_<NOMBRE>` (`project.md`):
   - `model_call_timeout_s = 3600` (una ventana del juez local en CPU puede tardar ~35 min con la generación
     medida de 1,36–6,77 *tokens*/s; cumple NFR-U10-04 con margen);
   - `run_deadline_final_s = 43200` (12 h: modo final por ventanas de la entrevista más larga en ZINE) y
     `run_deadline_incremental_s = 900`;
   - `fragment_window_turns = 60` y `fragment_overlap_turns = 20` como topes; el perfil local del clúster
     usa `window: 40`, `overlap: 10` (E23), y la comprobación de nivel 1 exige que ventana + *prompt* +
     reserva de salida quepan en el contexto del servidor.
   - En el clúster, U4 y U2 pueden bajar estas cifras por entorno; U11 declara los mínimos que no se pueden
     cruzar (como NFR-U10-04).
2. **Latencias de NFR3 y *N* de la prueba de humo.** Se calculan con la respuesta a P1 y con los datos de
   U10 (`masking_ms`, `upstream_ms`). Presupuesto de la biblioteca (sin cola) para una transcripción
   sintética de ≤ 60 turnos con `comercial-piloto`: p95 de `analyze` incremental ≤ 120 s y *N* = 240 s
   para `smoke.spec.ts`; la parte de cola y consola la suma U4.
3. **Costo de `verifier_permuted` frente a NFR3 y NFR8.** La permutación es obligatoria solo en perfiles
   de evaluación (BR2.9); `comercial-piloto` y `todo-local` quedan con `permutation: false` hasta que U8
   decida US10.5, así que NFR8 (50 sesiones, 3 concurrentes) no paga la segunda llamada. En evaluación el
   costo se declara en el reporte (*tokens* y costo por papel).
4. **Perfiles de evaluación espejo.** `evaluate` exige `purpose: evaluation` (BR12.1), así que cada perfil
   de producto tiene su espejo de evaluación con los mismos modelos y la permutación activa (p. ej.,
   `evaluacion-comercial` y `evaluacion-local-zine`, este con `batch_only: true`).
5. **Tramos de distancia de la sensibilidad (BR12.5):** se confirman los del diseño (hasta *O*, de *O*+1 a
   *W*, más de *W*), con *W* y *O* del perfil o los topes de C25 si el perfil no fragmenta, para que dos
   perfiles sean comparables.
6. **Modelo local del clúster.** `todo-local` en Minikube usa un juez Qwen cuantizado que quepa en la
   memoria que fija Infrastructure Design (válido solo para demostración, BR12.7) y el verificador
   gpt-oss-20b; el archivo exacto y su SHA-256 los fija Infrastructure Design de U2.
7. **Seguridad de la CLI y la biblioteca.** Claves solo por `api_key_ref` desde el entorno de la máquina,
   nunca en logs (*canary*); `gitleaks` sobre `evaluation/` y el paquete de ZINE; `pip-audit` y Trivy;
   import-linter (BR10.5); escritura atómica; Problem Details solo en el trabajador. Cada uno con su
   comando y su umbral (AUTONOMIA-02).
8. **Cobertura.** 80 % de líneas en los cuatro paquetes de `libs/` de U11 y 100 % de ramas en los módulos
   guardia de §10 del Functional Design, con las exclusiones declaradas (arnés de evaluación).

---

## 3. Preguntas

### P1. Verificador de `comercial-piloto` y familia del generador

**Contexto.** El juez es de Anthropic (P2 = A de U10). Falta el verificador, que debe ser de otra familia
en evaluación, y eso fija el generador del conjunto (Google u OpenAI, distinto del verificador). La
decisión cambia **qué proveedores reciben texto seudonimizado** y el alcance de B10: hoy B10 solo exige el
adaptador y el ADR de Anthropic para la primera rebanada, y `team.md` habla de «un proveedor comercial».
El verificador local medido en ZINE es gpt-oss-20b, de la línea de OpenAI: si se trata como familia de
OpenAI, el generador debe ser de **Google** en cualquier caso, porque el perfil de evaluación de ZINE usa
ese verificador. Los identificadores exactos de los modelos comerciales entrarían con el PR de
`config/profiles.yaml` y el ADR del proveedor; si quieres fijarlos ya, escríbelos en tu respuesta.

- A. **(Recomendada)** Verificador **local gpt-oss-20b** también en `comercial-piloto` y en su espejo de
  evaluación; sin alterno en la primera rebanada; generador de **Google**. Solo Anthropic recibe datos
  seudonimizados y B10 no crece. Costo: el verificador corre en CPU (lectura medida de 7,8 *tokens*/s; con
  caché del *prompt*, unos 20–60 s por llamada), la evaluación de nivel 2 en la anfitriona necesita el
  servidor local con ~12 GB de RAM, y BR2.7 se precisa para exigir el modo fragmentado solo cuando el
  **juez** es local (hoy lo exige si el verificador lo es).
- B. Verificador comercial de **OpenAI**; sin alterno; generador de **Google**. Es rápido, pero un segundo
  proveedor recibe las citas seudonimizadas, y el adaptador y el ADR de OpenAI pasan a la primera parte de
  B10 (R14 crece).
- C. Verificador comercial de **Google**; generador de **OpenAI**. Choca con el perfil de evaluación de
  ZINE: su verificador gpt-oss sería de la misma línea que el generador, y BR12.1 lo rechazaría salvo que
  se declare gpt-oss como familia aparte.
- D. Como B, más un alterno de **Google** (tercera familia, BR2.6) en el perfil de evaluación. Tres
  proveedores reciben datos y el alterno coincide con la familia del generador.
- X. Other (please specify)

[Answer]: A **Mode:** guided

### P2. Umbrales de las métricas estadísticas del nivel 2

**Contexto.** NFR4 deja a esta etapa los umbrales de precisión, sensibilidad y acuerdo entre 3 corridas
(BR12.3 los compara por su media; el acuerdo es el Jaccard medio por muestra). Con unas 25–40
contradicciones esperadas, el margen de error de una proporción es de ±0,15 aproximadamente. Un umbral
alto puede bloquear los PR de IA antes de la demo; uno bajo debilita lo que el TG puede afirmar. Los
umbrales nunca se bajan después (`team.md`).

- A. **(Recomendada)** Precisión **≥ 0,70**, sensibilidad **≥ 0,60** y acuerdo entre 3 corridas
  **≥ 0,60**. Bloquean solo con el perfil de evaluación de la primera rebanada (PR de IA y entregas
  etiquetadas); con los demás perfiles (ZINE, local) el reporte dice `passes` pero no bloquea. El acuerdo
  de tipo y la sensibilidad por distancia se reportan sin umbral.
- B. Más estrictos: 0,80 / 0,70 / 0,70, con la misma regla de bloqueo.
- C. Más laxos: 0,60 / 0,50 / 0,50, con la misma regla de bloqueo.
- D. Sin umbral estadístico en B11: la primera corrida fija la línea base y los umbrales entran por PR
  después (solo pueden subir). Hasta entonces solo bloquean los absolutos.
- X. Other (please specify)

[Answer]: A **Mode:** guided

### P3. Composición mínima del conjunto sintético

**Contexto.** BR13.2 exige los 7 tipos, relatos coherentes y los 4 casos trampa, y deja la composición
mínima a esta etapa. El conjunto se construye y se revisa a mano dentro de B11 (P12 = A de Delivery
Planning, riesgo R8), con la demo en 8 días. Más muestras dan métricas más estables y cuestan más
generación, revisión y llamadas (3 corridas por muestra).

- A. **(Recomendada)** **40 muestras:** 21 con contradicción (3 por tipo), 11 coherentes y 8 trampa (2 por
  caso). Al menos 6 largas (más de 120 turnos) y al menos 3 contradicciones esperadas en cada tramo de
  distancia; cada valor de `tipo_hecho` y de `perfil_persona` en al menos 2 muestras.
- B. **24 muestras:** 14 con contradicción (2 por tipo), 6 coherentes y 4 trampa; al menos 3 largas. Más
  rápido de revisar, métricas menos estables (±0,2).
- C. **70 muestras:** 35 con contradicción (5 por tipo), 20 coherentes y 15 trampa; al menos 10 largas.
  Más estable, pero pone en riesgo B11 antes de la demo.
- D. 24 muestras en B11 y crecer a 40 en una versión 1.1.0 del conjunto antes de la sustentación, por PR.
- X. Other (please specify)

[Answer]: A **Mode:** guided
