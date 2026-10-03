# Veridicus — Diálogos para la Memoria

Proyecto de curso: un sistema de entrevista asistida por IA que contrasta, en Kubernetes
y de forma soberana, el relato de un compareciente frente a un marco de verdad
documental, para apoyar (no reemplazar) al analista humano en procesos de justicia
transicional en Colombia.

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
├── docker/               contenedor aislado tai-aidlc (Claude Code + AI-DLC), ver docker/README.md
├── docs/                 insumos del PRD
│   ├── pvb.md             copia del PVB
│   ├── overview.md        panorama del dominio (justicia transicional, PLN forense)
│   ├── mercado.md         análisis de mercado y competencia
│   ├── icp.md             perfil de cliente ideal y buyer personas
│   ├── critica.md         investigación adversarial
│   ├── limite-autonomia.md  reglas AUTONOMIA-01..05 (PRD Segmento 6) para la memoria de AI-DLC
│   └── iteracion1.md      bitácora del Paso 0 (análisis de conflictos, aprobado por el autor)
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
    └── Veridicus_PVB_PRD.pptx  resumen visual del PVB + PRD (12 diapositivas, ~10 min, con notas del orador)
```

## Avance del flujo AI-DLC

El MVP se especifica con AI-DLC (scope `classic`). Los artefactos viven en
[`aidlc/spaces/default/intents/261002-veridicus-mvp/`](./aidlc/spaces/default/intents/261002-veridicus-mvp/)
(`I/` abajo); cada etapa se cierra con aprobación humana y un commit `aidlc(<etapa>): …`.

**Etapa cerrada más reciente:** Functional Design (2026-10-02). **Siguiente:** NFR Requirements.

| Fase | Etapa | Estado | Documentos principales |
|---|---|---|---|
| Inception | Practices Discovery | Aprobada | [`team-practices.md`](./aidlc/spaces/default/intents/261002-veridicus-mvp/inception/practices-discovery/team-practices.md) |
| Inception | Requirements Analysis | Aprobada | [`requirements.md`](./aidlc/spaces/default/intents/261002-veridicus-mvp/inception/requirements-analysis/requirements.md) |
| Inception | User Stories | Aprobada | [`user-stories/`](./aidlc/spaces/default/intents/261002-veridicus-mvp/inception/user-stories/) |
| Inception | Refined Mockups | Aprobada | [`mockups.md`](./aidlc/spaces/default/intents/261002-veridicus-mvp/inception/refined-mockups/mockups.md), [`interaction-spec.md`](./aidlc/spaces/default/intents/261002-veridicus-mvp/inception/refined-mockups/interaction-spec.md) |
| Inception | Domain Design | Aprobada | [`components.md`](./aidlc/spaces/default/intents/261002-veridicus-mvp/inception/domain-design/components.md), [`decisions.md`](./aidlc/spaces/default/intents/261002-veridicus-mvp/inception/domain-design/decisions.md) |
| Inception | Units Generation | Aprobada | [`unit-of-work.md`](./aidlc/spaces/default/intents/261002-veridicus-mvp/inception/units-generation/unit-of-work.md) |
| Inception | Contract Design | Aprobada | [`contract-summary.md`](./aidlc/spaces/default/intents/261002-veridicus-mvp/inception/contract-design/contract-summary.md) |
| Inception | Delivery Planning | Aprobada | [`bolt-plan.md`](./aidlc/spaces/default/intents/261002-veridicus-mvp/inception/delivery-planning/bolt-plan.md) |
| Construction | Functional Design | Aprobada | [`construction/<unidad>/functional-design/`](./aidlc/spaces/default/intents/261002-veridicus-mvp/construction/): entidades, reglas, especificación funcional y trazabilidad de las 9 unidades (contracts, identity-access, text-flow, human-review, session-lifecycle, assistant-extras, anonymizer, forensic-report, voice), con su revisión en `reviews/` |
| Construction | NFR Requirements, NFR Design, Infrastructure Design | Pendientes | — |
| Construction | Code Generation (solo Parte 1: plan de tareas) | Pendiente | — |

Los hallazgos abiertos de las revisiones de Functional Design quedaron aceptados como riesgo
en la aprobación. Los cambios propuestos a contratos y a otras unidades están en la tabla
«Cambios entre unidades» de cada `functional-spec.md`.

### Qué es Veridicus, en una línea

> Un sistema multiagente de entrevista asistida por IA que contrasta en tiempo real el
> relato de un compareciente frente a un marco de verdad documental y señala
> incongruencias afectivo-semánticas —nunca veredictos de veracidad— para analistas de
> justicia transicional, desplegado de forma soberana en un clúster Kubernetes local.

Ver `pvb.md` (visión) y `specs/prd.md` (los 13 segmentos de requisitos, incluido el
alcance MoSCoW del MVP académico) para el detalle completo.

---

> **Nota de mantenimiento:** este README debe **revisarse y actualizarse siempre que se
> agregue documentación nueva** al repositorio (un archivo a `docs/`, una fuente a
> `research/`, un segmento nuevo a `specs/prd.md`). Un README desactualizado es, para
> efectos de coherencia del proyecto, tan problemático como una cita sin fuente.
