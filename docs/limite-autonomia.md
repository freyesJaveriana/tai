# Límite de autonomía del agente — Veridicus

> Origen: extensión de AI-DLC v1 del módulo 5 (`.aidlc-rule-details/extensions/autonomia/`),
> portada a v2.10.0. En v2 estas reglas viven en `aidlc/spaces/default/memory/team.md`
> ver `plan-aidlc.md`, Paso 0); este archivo es la fuente versionada de donde se copian.
>
> **Cambio 01 (2026-10-30, DT27, `docs/iteracion2.md`):** AUTONOMIA-04 y AUTONOMIA-05 se
> reescriben porque Veridicus pasa a ser el analizador de incoherencias del Trabajo de Grado:
> modelos comerciales solo tras el anonimizador y hallazgos con dos citas verificadas.
> AUTONOMIA-01, 02 y 03 no cambian de regla; ganan una viñeta de verificación cada una (01 y 03).

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
- Ningún plan de tareas envía trabajos al clúster ZINE ni a otro clúster de cómputo: los
  scripts `sbatch` y su paquete de entrada son artefactos revisables que el humano lanza (DT26)

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
consolidar el reporte de revisión final sin la validación explícita de un analista humano.

**Verification**:
- Todo hallazgo generado por la IA se modela como «sugerencia de revisión» con estado
  editable (pendiente / aceptada / editada / descartada) y el actor que lo cambia es humano
- El escaneo de etiquetas de veracidad cubre las observaciones del hallazgo y las
  observaciones al conductor; solo excluye las dos citas literales del testimonio
- El paso de consolidación del reporte exige una acción explícita del analista y queda
  registrado quién la hizo y cuándo
- Existe al menos una prueba automatizada que falla si la salida de la IA o la interfaz
  contiene una etiqueta de veracidad binaria

---

## Rule AUTONOMIA-04: Ningún dato sin seudonimizar sale del clúster

**Rule**: (PRD Segmento 6, Principio 3; DT18, DT21) Ningún componente puede enviar fuera del
clúster local audio crudo, transcripciones sin seudonimizar, nombres de víctimas ni
identificadores reales del proceso. Un proveedor comercial solo recibe texto que pasó por el
anonimizador. Si el anonimizador falla, la llamada no sale (falla cerrado). El anonimizador corre
siempre dentro del clúster y solo es obligatorio delante de destinos externos.

**Verification**:
- El diseño de aplicación declara, para cada componente, si corre dentro o fuera del clúster
  y qué datos cruzan esa frontera
- Un destino externo en la configuración de modelos exige el adaptador anonimizador delante;
  si no lo tiene, el servicio no arranca (prueba de arranque con un control negativo)
- Toda tarea que integre un proveedor externo incluye una prueba de que el payload saliente
  pasó por el anonimizador (sin nombres ni ubicaciones del conjunto de prueba) y otra de que,
  si el anonimizador falla, no sale ninguna llamada
- Existe una tarea que produce la `NetworkPolicy` que niega la salida a internet a todos los
  pods salvo al anonimizador, y a este solo hacia los proveedores configurados (artefacto
  revisable, ver AUTONOMIA-01)
- Las claves de API viven en un `Secret` que crea el humano; nunca en el repositorio ni en el
  archivo de configuración

---

## Rule AUTONOMIA-05: Sin dos citas verificadas no hay hallazgo

**Rule**: (PRD Segmento 6, Principio 4; DT04, DT09, DT15) Todo hallazgo de contradicción
presenta dos citas literales de la misma transcripción, cada una con su turno y su página (si el
turno la tiene), más el hecho, el tipo y las observaciones. Antes de que el hallazgo salga del
analizador, una verificación determinista comprueba que cada cita existe en su turno; si el texto
pasó por el anonimizador, la cita se restaura primero y se verifica después. Una cita que no
aparece invalida el hallazgo. Un error del analizador nunca deja un resultado parcial. Las
vaguedades, las emociones, los detalles periféricos y las versiones de terceros no son
contradicciones.

**Verification**:
- El esquema de un hallazgo tiene como campos obligatorios `hecho`, `tipo` (uno de `fecha`,
  `numero`, `lugar`, `persona`, `negacion`, `secuencia`, `otro`), `cita_a`, `cita_b` y
  `observaciones`; un hallazgo sin cualquiera de ellos se rechaza por validación
- Existe una prueba con una cita alterada (y otra con una cita en un turno equivocado) que
  verifica que el hallazgo no sale del analizador
- Existe una prueba que verifica que `estado: error` implica una lista de hallazgos vacía
- Existe una prueba de que la cita seudonimizada se restaura antes de verificarse
