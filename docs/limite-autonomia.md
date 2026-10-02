# Límite de autonomía del agente — Veridicus

> Origen: extensión de AI-DLC v1 del módulo 5 (`.aidlc-rule-details/extensions/autonomia/`),
> portada a v2.10.0. En v2 estas reglas viven en `aidlc/spaces/default/memory/team.md`
> (ver `plan-aidlc.md`, Paso 0); este archivo es la fuente versionada de donde se copian.

## Overview
Estas reglas son restricciones bloqueantes en todas las fases de AI-DLC (v2.x). No son
recomendaciones. Cada etapa DEBE verificarlas antes de presentar su mensaje de
finalización. Derivan del Segmento 6 de `specs/prd.md` (Principios de diseño no
negociables) y de la regla del curso «el agente propone, el humano aprueba».

### Default Enforcement
Todas las reglas de este documento son **bloqueantes**. Si no se cumple un criterio de
verificación, es un hallazgo bloqueante: la etapa solo puede ofrecer «Request Changes».
Cada verificación se cita por su ID en la bitácora de auditoría del intent.

---

## Rule AUTONOMIA-01: Ninguna tarea aplica cambios a infraestructura sin aprobación

**Rule**: Ninguna unidad de trabajo puede contener una tarea que aplique cambios al clúster
de Kubernetes, a la base de datos gestionada por CloudNativePG, a la nube o a cualquier
entorno compartido sin una aprobación humana registrada. El destino de la cadena del agente
es un pull request con evidencia adjunta, nunca un `kubectl apply` autónomo.

**Verification**:
- Ningún plan de tareas contiene un paso que ejecute `kubectl apply`, `helm install`,
  `helm upgrade`, `terraform apply`, una migración de esquema sobre la base del clúster o
  equivalente sin un paso previo de aprobación humana
- Toda tarea que toque un entorno compartido produce un artefacto revisable (manifiesto,
  chart, script de migración, PR), no un cambio directo

---

## Rule AUTONOMIA-02: Todo criterio de aceptación se verifica con un comando

**Rule**: Cada tarea de cada unidad DEBE tener un criterio de aceptación comprobable
ejecutando un comando. Las formulaciones de opinión no son criterios de aceptación.

**Verification**:
- Ningún criterio de aceptación usa formulaciones como «funciona correctamente»,
  «es usable» o «tiene buen rendimiento» sin un comando o umbral medible
- Cada tarea nombra el comando, la prueba o la comprobación que demuestra que terminó

---

## Rule AUTONOMIA-03: La IA nunca emite veredictos de veracidad ni consolida sin el analista

**Rule**: (PRD Segmento 6, Principio 1) El sistema actúa solo como consultor del analista.
Ninguna historia, componente o tarea puede producir una etiqueta automática de veracidad
sobre el compareciente («mentiroso», «falso», «miente», puntaje binario de verdad) ni
consolidar el reporte forense final sin la validación explícita de un analista humano.

**Verification**:
- Todo hallazgo generado por la IA se modela como «sugerencia de revisión» con estado
  editable (pendiente / aceptada / editada / descartada) y el actor que lo cambia es humano
- El paso de consolidación del reporte exige una acción explícita del analista y queda
  registrado quién la hizo y cuándo
- Existe al menos una prueba automatizada que falla si la salida de la IA o la interfaz
  contiene una etiqueta de veracidad binaria

---

## Rule AUTONOMIA-04: Ningún dato sensible sale del clúster

**Rule**: (PRD Segmento 6, Principio 3) Ningún componente puede enviar audio crudo,
transcripciones sin anonimizar, nombres de víctimas o identificadores reales del proceso
fuera del clúster local. Cualquier llamada opcional a un LLM externo pasa por el servicio de
anonimización y solo transporta texto depurado.

**Verification**:
- El diseño de aplicación declara, para cada componente, si corre dentro o fuera del clúster
  y qué datos cruza esa frontera
- Toda tarea que integre un servicio externo incluye una prueba que verifica que el payload
  saliente pasó por el anonimizador (sin nombres ni ubicaciones del conjunto de prueba)
- Existe una tarea que produce la `NetworkPolicy` que niega salida a internet a los pods que
  manejan datos sin anonimizar (como artefacto revisable, ver AUTONOMIA-01)

---

## Rule AUTONOMIA-05: Sin evidencia documental, la IA escala al humano en lugar de inferir

**Rule**: (PRD Segmento 6, Principio 4, y Segmento 7, Journey 4) Toda alerta de
incongruencia debe mostrar su Cadena de Pensamiento enlazando el fragmento de la
transcripción con la cita literal y el identificador del documento del marco de verdad.
Cuando la similitud recuperada está por debajo del umbral configurado, el sistema NO genera
alerta ni pregunta automática: marca el turno como «Hecho No Documentado» y entrega el
Paquete de Contexto de Traspaso al analista.

**Verification**:
- El modelo de datos de una alerta incluye como campos obligatorios: fragmento de
  transcripción, cita del documento, ID del documento y traza CoT; una alerta sin ellos es
  rechazada por validación
- El umbral de similitud es un parámetro configurable y existe una prueba que, con una
  entrada por debajo del umbral, verifica que no se emite alerta ni pregunta y sí se emite el
  paquete de traspaso
