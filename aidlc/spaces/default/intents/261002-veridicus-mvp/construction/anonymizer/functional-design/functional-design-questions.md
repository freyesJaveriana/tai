# Preguntas de Functional Design — U10 anonymizer

**Unidad.** U10 `anonymizer` (tipo `service`, COULD): adaptador anonimizador de ModelGateway que
enmascara nombres, ubicaciones y números de expediente antes de cualquier llamada externa y falla
cerrado, con la prueba del *payload* saliente y la `NetworkPolicy` que solo le da salida a él
(US11.3). Solo se construye si se decide usar un modelo externo.

**Lo que ya está decidido y no se vuelve a preguntar.** Expresiones regulares en español (FR11.3);
falla cerrada (AC11.3.1); misma forma que ModelGateway (C13); 100 % de ramas; solo el proxy tiene salida
(AC11.3.2). Quedan dos huecos.

---

## P1 — Cómo se enmascara

El juez externo debe poder razonar sobre «quién estuvo dónde», así que importa si dos menciones del
mismo nombre se reconocen como la misma persona, y si la respuesta vuelve con los nombres reales.

A. Marcadores consistentes por llamada (`[PERSONA_1]`, `[LUGAR_2]`, `[EXPEDIENTE_1]`): el mismo valor
   recibe el mismo marcador; la tabla de equivalencias vive solo en memoria del proxy durante la llamada
   y se usa para restaurar la respuesta dentro del clúster. (Recomendada)
B. Marcadores genéricos sin numerar (`[PERSONA]`, `[LUGAR]`) y sin restaurar la respuesta.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P2 — Qué reconoce como nombre o lugar

Un nombre propio en español no siempre se distingue con una expresión regular («San José» puede ser
persona o lugar), y un nombre que se escape sale del clúster.

A. Expresiones regulares (tratamientos como «señor», «doña», secuencias de palabras con mayúscula
   inicial, prefijos de lugar como «vereda», «municipio de», formatos de expediente) más la lista de
   nombres propios extraída de los documentos del escenario; ante la duda, se enmascara. (Recomendada)
B. Solo expresiones regulares.
X. Other (please specify)

[Answer]: A **Mode:** guided
