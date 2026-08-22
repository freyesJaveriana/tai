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
├── docs/                 insumos del PRD
│   ├── pvb.md             copia del PVB
│   ├── overview.md        panorama del dominio (justicia transicional, PLN forense)
│   ├── mercado.md         análisis de mercado y competencia
│   ├── icp.md             perfil de cliente ideal y buyer personas
│   ├── critica.md         investigación adversarial
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
