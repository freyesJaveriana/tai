# Veridicus — Diálogos para la Memoria

Proyecto de curso: un sistema de entrevista asistida por IA que detecta, en Kubernetes,
contradicciones dentro del relato de un compareciente sobre hechos centrales, cada una con
dos citas literales verificadas, para apoyar (no reemplazar) al analista humano en procesos
de justicia transicional en Colombia. Desde el cambio 01 (DT27, 2026-10-27) es además el
analizador de incoherencias del Trabajo de Grado *Diálogos para la Memoria*
([`docs/iteracion2.md`](./docs/iteracion2.md)).

---

## Datos del curso

| Campo | Valor |
|---|---|
| Curso | Tópicos Especiales en Informática |
| Semestre | 2026-3 |
| Profesor | Luis Felipe Ariza Vesga |
| Universidad | Pontificia Universidad Javeriana |
| Ciudad | Bogotá, Colombia |
| Repositorio del curso | [`lfarizav/topicos-especiales`](https://github.com/lfarizav/topicos-especiales) |

## Autor

| Campo | Valor |
|---|---|
| Nombre | Felipe Reyes Palacio |
| Correo | freyes@javeriana.edu.co |
| Programa | Maestría en Ingeniería de Sistemas y Maestría en Inteligencia Artificial |

> **Nota de contexto:** `docs/pvb.md` señala que Veridicus está alineado con el Trabajo
> de Grado de Maestría del autor, *"Diálogos para la Memoria"*, dirigido por el
> **Dr. Luis Gabriel Moreno**. Ese director de tesis es una persona distinta del profesor
> de este curso, **Luis Felipe Ariza Vesga** — no confundir los dos roles al leer los
> documentos de `docs/` y `research/06-documentacion-propia/`.

---

## Entregables y de dónde salen sus reglas

El curso especifica, en su propio repositorio, exactamente qué se entrega y cómo se
evalúa. Esta tabla conecta cada entregable de este repo con la página del curso que lo
exige:

| Entregable | Archivo en este repo | Especificado en (repo del curso) |
|---|---|---|
| Product Vision Board (PVB) | [`pvb.md`](./pvb.md) (copia en [`docs/pvb.md`](./docs/pvb.md)) | [`modulo2/README.md`](https://github.com/lfarizav/topicos-especiales/blob/main/modulo2/README.md) · [`modulo2/INSTRUCCIONES-ENTREGA.md`](https://github.com/lfarizav/topicos-especiales/blob/main/modulo2/INSTRUCCIONES-ENTREGA.md) |
| Product Requirements Document (PRD) | [`specs/prd.md`](./specs/prd.md) | [`modulo3/README.md`](https://github.com/lfarizav/topicos-especiales/blob/main/modulo3/README.md) · [`modulo3/prompts-para-especificacion.md`](https://github.com/lfarizav/topicos-especiales/blob/main/modulo3/prompts-para-especificacion.md) (Prompt 1) |
| Investigación de validación | [`docs/overview.md`](./docs/overview.md), [`docs/mercado.md`](./docs/mercado.md), [`docs/icp.md`](./docs/icp.md) | [`modulo2/INSTRUCCIONES-ENTREGA.md`](https://github.com/lfarizav/topicos-especiales/blob/main/modulo2/INSTRUCCIONES-ENTREGA.md) (Paso 2) |
| Investigación de crítica (adversarial) | [`docs/critica.md`](./docs/critica.md) | ídem (Paso 2) |
| Regla de evidencia y caso de alucinación de IA a estudiar | Anexo de auditoría en [`docs/pvb.md`](./docs/pvb.md) | [`modulo3/research/README.md`](https://github.com/lfarizav/topicos-especiales/blob/main/modulo3/research/README.md) del repo del curso — **no confundir con [`research/README.md`](./research/README.md) de este repo**, que es el índice de nuestro propio corpus documental, no el caso de estudio del curso |
| Análisis de conflictos (Paso 0) entre PVB e insumos | [`docs/iteracion1.md`](./docs/iteracion1.md) | [`modulo3/prompts-para-especificacion.md`](https://github.com/lfarizav/topicos-especiales/blob/main/modulo3/prompts-para-especificacion.md) (sección "PASO 0") |
| Cronograma y fecha de cada entregable | — | [`README.md`](https://github.com/lfarizav/topicos-especiales/blob/main/README.md) del repo del curso ("Cronograma — 16 sesiones"), fuente de verdad de fechas |

Reglas del curso que gobiernan todo lo anterior (ver `INSTRUCCIONES-ENTREGA.md` y el
README raíz del curso): toda cifra lleva fuente con enlace y fecha; las proyecciones
propias se marcan `[INTERNO]` y lo no verificado `[VERIFICAR]`; y **el agente propone,
el humano aprueba** — ninguna decisión de alcance o de PVB/PRD se delega a la IA sin
revisión explícita.

---

## Estructura del repositorio

```
tai/
├── pvb.md              ← Entregable 1 (Product Vision Board)
├── plan-aidlc.md         plan propio para AI-DLC v2.10.0: de PVB/PRD a unidades y tareas
├── docker/               contenedor aislado (tai-aidlc; tg-veridicus desde el cambio 01), ver docker/README.md
├── docs/                 insumos del PRD
│   ├── pvb.md             copia del PVB
│   ├── overview.md        panorama del dominio (justicia transicional, PLN forense)
│   ├── mercado.md         análisis de mercado y competencia
│   ├── icp.md             perfil de cliente ideal y buyer personas
│   ├── critica.md         investigación adversarial
│   ├── limite-autonomia.md  reglas AUTONOMIA-01..05 (PRD Segmento 6) para la memoria de AI-DLC
│   ├── iteracion1.md      bitácora del Paso 0 (análisis de conflictos, aprobado por el autor)
│   └── iteracion2.md      análisis de impacto del cambio 01 (analizador de incoherencias del TG), aprobado
├── specs/
│   └── prd.md           ← Entregable 2 (Product Requirements Document, 13 segmentos)
├── research/             corpus documental citado por docs/ y specs/
│   ├── README.md          índice del corpus: qué cita cada documento y por qué
│   ├── 01-marco-legal-colombiano/       Ley 1448/2011, Ley 2421/2024, Ley 1581/2012
│   ├── 02-memoria-historica-y-conflicto/  CEV, CNMH, Patiño, minería de texto JEP Caso 03
│   ├── 03-llm-as-a-judge/                 MT-Bench, Themis, JudgeBlender, Preference Leakage
│   ├── 04-analisis-forense-del-testimonio/ LieXBerta, codificación de preguntas forenses
│   ├── 05-etica-sesgos-y-riesgos/          Stochastic Parrots, UNESCO, NLP en trauma
│   └── 06-documentacion-propia/            propuesta y hoja de ruta del TG del autor
└── presentations/        material de apoyo para mostrar el avance en clase
    ├── Veridicus_PVB_PRD.pptx  resumen visual del PVB + PRD (12 diapositivas, ~10 min, con notas del orador)
    └── Veridicus_AIDLC_avance.pptx  avance con AI-DLC v2: etapas, interfaz, arquitectura, unidades e infraestructura, con el plan de U1 en Code Generation (8 diapositivas, con notas del orador)
```

## Avance del flujo AI-DLC

El MVP se especifica con AI-DLC (scope `classic`). Los artefactos viven en
[`aidlc/spaces/default/intents/261002-veridicus-mvp/`](./aidlc/spaces/default/intents/261002-veridicus-mvp/)
(`I/` abajo); cada etapa se cierra con aprobación humana y un commit `aidlc(<etapa>): …`.

**Cambio 01 (2026-10-30):** Veridicus pasa a ser el analizador de incoherencias del TG (DT27). El
análisis de impacto y sus decisiones están en [`docs/iteracion2.md`](./docs/iteracion2.md); PVB, PRD
(iteración 6), reglas AUTONOMIA y `plan-aidlc.md` ya están corregidos. El flujo volvió a
**Requirements Analysis (2.3)** para revisar en este intent las etapas 2.3 a 3.5; la tabla de abajo
muestra lo aprobado **antes** del cambio, que cada etapa revisada actualizará (Requirements Analysis, User Stories y Refined Mockups ya están revisadas; **antes de Domain Design** se validan los modelos locales en el clúster Ing. Sistemas, FR16.3). El plan de U1 nunca se
aprobó y se regenerará con el contrato común; desde entonces, el autor elige `Approve Plan` y se
construye por Bolts.

| Fase | Etapa | Estado | Documentos principales |
|---|---|---|---|
| Inception | Practices Discovery | Aprobada | [`team-practices.md`](./aidlc/spaces/default/intents/261002-veridicus-mvp/inception/practices-discovery/team-practices.md) |
| Inception | Requirements Analysis | Aprobada (revisión 2, cambio 01) | [`requirements.md`](./aidlc/spaces/default/intents/261002-veridicus-mvp/inception/requirements-analysis/requirements.md): revisión 2 con el contrato común v0.1 del analizador (FR4.1–FR4.9: 7 tipos, dos citas verificadas, `error` ⇒ hallazgos vacíos), anonimizador obligatorio (FR11.3–FR11.4), biblioteca y CLI (FR13), perfiles por papel (FR14), `ModelGateway` (FR15) y lotes en ZINE (FR16); retirados FR2, FR5, FR11.1 y NFR9. Revisión en [`reviews/review-02.md`](./aidlc/spaces/default/intents/261002-veridicus-mvp/inception/requirements-analysis/reviews/review-02.md) (READY; R-01 a R-06 aceptados como riesgo) |
| Inception | User Stories | Aprobada (revisión 2, cambio 01) | [`stories.md`](./aidlc/spaces/default/intents/261002-veridicus-mvp/inception/user-stories/stories.md): 62 historias activas en 14 épicas (US12.6 y US12.7 entran por Refined Mockups), con las retiradas marcadas sin renumerar; épicas nuevas 12 (biblioteca y CLI), 13 (perfiles y modelos) y 14 (ZINE, con US14.1 MUST: validación de modelos locales antes de Domain Design). [`personas.md`](./aidlc/spaces/default/intents/261002-veridicus-mvp/inception/user-stories/personas.md) suma P4, Investigador del TG. Revisión en [`reviews/review-03.md`](./aidlc/spaces/default/intents/261002-veridicus-mvp/inception/user-stories/reviews/review-03.md) (READY; R-01 a R-05 resueltos) |
| Inception | Refined Mockups | Aprobada (revisión 2, cambio 01) | [`mockups.md`](./aidlc/spaces/default/intents/261002-veridicus-mvp/inception/refined-mockups/mockups.md): M0–M8 (M2 retirada); nuevas M7 importar transcripción y M8 reportes del investigador (rol `investigador`, FR1.2 y FR13.5). Sesión con perfil, citas A/B con contexto, franja del modo final y registro de modelos por corrida. [`interaction-spec.md`](./aidlc/spaces/default/intents/261002-veridicus-mvp/inception/refined-mockups/interaction-spec.md), [`design-system-mapping.md`](./aidlc/spaces/default/intents/261002-veridicus-mvp/inception/refined-mockups/design-system-mapping.md), [`accessibility-checklist.md`](./aidlc/spaces/default/intents/261002-veridicus-mvp/inception/refined-mockups/accessibility-checklist.md). Lienzo visual: <https://claude.ai/artifact/5D2otJRp5fh6YsccE6m8iw>. Revisión en [`reviews/review-04.md`](./aidlc/spaces/default/intents/261002-veridicus-mvp/inception/refined-mockups/reviews/review-04.md) (READY) |
| Inception | Domain Design | Aprobada | [`components.md`](./aidlc/spaces/default/intents/261002-veridicus-mvp/inception/domain-design/components.md), [`decisions.md`](./aidlc/spaces/default/intents/261002-veridicus-mvp/inception/domain-design/decisions.md) |
| Inception | Units Generation | Aprobada | [`unit-of-work.md`](./aidlc/spaces/default/intents/261002-veridicus-mvp/inception/units-generation/unit-of-work.md) |
| Inception | Contract Design | Aprobada | [`contract-summary.md`](./aidlc/spaces/default/intents/261002-veridicus-mvp/inception/contract-design/contract-summary.md) |
| Inception | Delivery Planning | Aprobada | [`bolt-plan.md`](./aidlc/spaces/default/intents/261002-veridicus-mvp/inception/delivery-planning/bolt-plan.md) |
| Construction | Functional Design | Aprobada | [`construction/<unidad>/functional-design/`](./aidlc/spaces/default/intents/261002-veridicus-mvp/construction/): entidades, reglas, especificación funcional y trazabilidad de las 9 unidades (contracts, identity-access, text-flow, human-review, session-lifecycle, assistant-extras, anonymizer, forensic-report, voice), con su revisión en `reviews/` |
| Construction | NFR Requirements | Aprobada | [`construction/<unidad>/nfr-requirements/`](./aidlc/spaces/default/intents/261002-veridicus-mvp/construction/): requisitos de rendimiento, seguridad, escalado, fiabilidad y observabilidad, decisiones de pila y trazabilidad de las 10 unidades (incluida platform). Claves: juez Qwen2.5-7B Q4 y `multilingual-e5-base` en CPU, umbral inicial 0,80 calibrado en nivel 2, p95 ≤ 60 s por turno de texto, humo en 120 s, plazo proporcional a la cola (tope 3 600 s); revisiones en `reviews/` |
| Construction | NFR Design | Aprobada | [`construction/<unidad>/nfr-design/`](./aidlc/spaces/default/intents/261002-veridicus-mvp/construction/): diseño de rendimiento, seguridad, escalado, fiabilidad, observabilidad y componentes lógicos, más trazabilidad, de las 10 unidades (U1 y platform solo seguridad). Claves: catálogo único de límites `contracts/limits.v1.yaml`, huella de seguridad versionada, cursor `change_seq` por sesión con orden de bloqueo sesión → ronda, reintento acotado del juez, TLS local con mkcert, subida de audio en memoria y reescritura del AOF de Redis, seudónimos estables del anonimizador; revisiones en `reviews/` |
| Construction | Infrastructure Design | Aprobada | [`construction/<unidad>/infrastructure-design/`](./aidlc/spaces/default/intents/261002-veridicus-mvp/construction/): especificación de infraestructura, monitoreo, pipeline de CI/CD y trazabilidad de las 9 unidades con despliegue. Claves: Minikube + Calico en un namespace `veridicus` (20 GiB/10 CPU en desarrollo, 28 GiB en demostración), red negada por defecto, CloudNativePG con roles separados, Redis 7.2 `noeviction`, límites con ≥ 20 % sobre picos, sonda de `session-api` sin Redis, `Recreate` en la API, respaldo conjunto con `backup-db.sh`, extras solo en la demostración, voz en las dos máquinas, CoreDNS con lista blanca; la CI nunca despliega; revisiones en `reviews/` |
| Construction | Code Generation (solo Parte 1: plan de tareas) | En curso (U1 lista) | [`code-generation-plan.md`](./aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/code-generation-plan.md), [`unit-test-instructions.md`](./aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/unit-test-instructions.md) de U1 contracts: 19 pasos, cada uno con su `Verificación:` (AUTONOMIA-02), para producir los contratos versionados C1–C16 de `contracts/`, el paquete `veridicus_contracts` con la suite de nivel 0, sus generadores (tipos y constantes TypeScript, huella de seguridad) y el *job* de CI. Claves: decisiones PD-1 a PD-5 (la versión 1.0.0 de cada contrato integra las precisiones aprobadas de U1–U10; el escáner en ejecución queda en U4; NFR10.6 por análisis estático de patrones), pruebas de contratos y guardias AUTONOMIA-03/04/05 escritas primero en rojo, suite sin red en ≤ 60 s con ≥ 80 % de líneas y 100 % de ramas en `checks/`. El trabajo se detiene en el plan: la Parte 2 (código) queda fuera de este flujo. Pendientes: los planes de U2–U10 |

Los hallazgos abiertos de las revisiones de Functional Design, NFR Requirements, NFR Design e Infrastructure Design quedaron
aceptados como riesgo en la aprobación; están en `reviews/` de cada unidad. Las precisiones a artefactos aprobados
están en §6 de cada `security-requirements.md` y en las tablas «Precisiones a artefactos ya aprobados» de cada diseño de NFR. Los cambios propuestos a contratos y a otras unidades están en la tabla
«Cambios entre unidades» de cada `functional-spec.md`.

### Qué es Veridicus, en una línea

> Un sistema multiagente de entrevista asistida por IA que detecta contradicciones
> dentro del relato de un compareciente sobre hechos centrales, con dos citas literales
> verificadas —nunca veredictos de veracidad—, para analistas de justicia transicional,
> desplegado en un clúster Kubernetes local del que ningún dato sin seudonimizar sale.

Ver `pvb.md` (visión) y `specs/prd.md` (los 13 segmentos de requisitos, incluido el
alcance MoSCoW del MVP académico) para el detalle completo.

---

> **Nota de mantenimiento:** este README debe **revisarse y actualizarse siempre que se
> agregue documentación nueva** al repositorio (un archivo a `docs/`, una fuente a
> `research/`, un segmento nuevo a `specs/prd.md`). Un README desactualizado es, para
> efectos de coherencia del proyecto, tan problemático como una cita sin fuente.
