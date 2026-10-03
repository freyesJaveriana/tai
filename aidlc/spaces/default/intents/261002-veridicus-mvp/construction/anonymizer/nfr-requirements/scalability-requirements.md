# Requisitos de escalado — U10 anonymizer

**Insumos.** Flujos F1 y F2 de `functional-design/functional-spec.md` (functional-spec); reglas BR1.3 y
BR2.1 de `functional-design/rules.md` (rules); FR11.3, NFR8 y los supuestos de carga de
`inception/requirements-analysis/requirements.md` (requirements); C13 y C14 de
`inception/contract-design/contract-summary.md` (contract-summary); respuesta P1 = A de
`nfr-requirements-questions.md`; NFR8.7 de U4 (un turno a la vez en el juez).

## 1. Carga esperada

| Dimensión | Valor | Origen |
|---|---|---|
| Despliegue por defecto | **0 réplicas**: el proxy no se despliega (P1 = A) | Respuesta P1 |
| Llamadas `judge` simultáneas si se habilita | 1 (`semantic-agent` procesa un turno a la vez) | NFR8.7 de U4 |
| Llamadas `embed` simultáneas si se habilita | ≤ 2 (indexador de `session-api` y consultas de afirmaciones) | D11 de U4 |
| Tamaño de una llamada | ≤ 512 KiB de cuerpo; ≤ 2 000 nombres propios | NFR10.8 |

## 2. Requisitos

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR8.2 | El proxy limita sus llamadas simultáneas y rechaza el exceso sin enviar nada. | Como máximo **4** llamadas en curso (`VERIDICUS_ANONYMIZER_MAX_CONCURRENCY`, entero 1–8); la quinta recibe al instante `503` con `code` `anonymizer.busy`, **sin enmascarar ni enviar nada**, y el cliente la trata como recuperable (precisión en `security-requirements.md` §6). Prueba de nivel 1 con un destino *fake* bloqueado: 4 llamadas en curso, la 5.ª recibe 503 y el destino registra 4 peticiones. | Nivel 1 |
| NFR8.3 | El proxy no guarda estado entre llamadas. | Cada `MaskTable` vive solo dentro de su llamada (NFR10.2); el proceso no tiene base de datos, Redis ni volumen persistente. Dos llamadas con los mismos nombres en orden distinto producen marcadores numerados de forma independiente (`[PERSONA_1]` en ambas). El MVP corre como máximo 1 réplica; más réplicas no exigen cambios. | Nivel 0 |
| NFR8.4 | Habilitar el proxy no baja el éxito del *pipeline*. | En el PR de habilitación, la corrida de carga de NFR8 de U4 (`evaluation/load/run_batches.py`, 50 sesiones en tandas de 3) con el proxy en el camino cumple **≥ 98 %** (NFR8.5 de U4) y 0 `OOMKilled` del proxy. | Corrida de carga a demanda, en el PR de habilitación |

## 3. Señal para escalar

No hay autoescalado. La concurrencia la limita el juez (uno a la vez) y la cola de U4, no el proxy. Si
`veridicus_anonymizer_requests_total{result="busy"}` crece de forma sostenida (`observability-requirements.md`),
se sube `VERIDICUS_ANONYMIZER_MAX_CONCURRENCY` por PR con la medición de NFR8.1; el tope de 8 protege la
memoria del pod.
