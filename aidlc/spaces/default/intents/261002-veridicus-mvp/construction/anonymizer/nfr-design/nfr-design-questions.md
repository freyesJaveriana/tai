# Preguntas de NFR Design — U10 anonymizer

**Unidad.** U10 `anonymizer` (`anonymizer-proxy`, COULD): adaptador de ModelGateway que enmascara
nombres, lugares y números de expediente antes de llamar a un modelo externo (`judge` y `embed`),
restaura la respuesta dentro del clúster y falla cerrado. Todo el módulo es guardia de AUTONOMIA-04
(nunca sale del clúster audio crudo, transcripción sin anonimizar, nombres de víctimas ni
identificadores reales del proceso).

**Lo que ya está decidido y no se vuelve a preguntar.** Requisitos y decisiones D1–D9 de
`nfr-requirements/`: proxy apagado por defecto y habilitado solo por un PR con ADR del proveedor y la
`NetworkPolicy` de ese único destino (P1 = A); detección con `google-re2` sobre una copia sin
mayúsculas ni tildes y prioridad EXPEDIENTE > PERSONA > LUGAR; lista de nombres propios enviada por el
cliente en `veridicus_masking` (el proxy no tiene credencial de base de datos); un solo intento hacia
el destino, sin reintentos; tabla de equivalencias solo en memoria y borrada en `finally`; límites de
entrada, códigos de error, logs con lista blanca y métricas `veridicus_anonymizer_*`. Los hallazgos de
la revisión de NFR Requirements que un experto puede cerrar se integran en el diseño sin preguntar:
huecos de la política de salida (regla sin `to`, `hostNetwork`, pod sin denegación por defecto),
plazo total por llamada con `anyio.fail_after`, lista permitida de cabeceras salientes y alcance de la
puerta de 100 % de ramas sobre `libs/model_gateway`. Quedan dos decisiones de criterio.

---

## P1 — Cómo se numeran los marcadores cuando se usan *embeddings* externos

Hoy cada llamada numera sus marcadores desde 1 (NFR8.3: «Ana Pérez» puede ser `[PERSONA_1]` en un
lote de pasajes y «Juan Gómez» ser `[PERSONA_1]` en la consulta de una afirmación). Los pasajes se
vectorizan en lotes de 32 y cada afirmación en otra llamada, así que el mismo marcador puede nombrar a
personas distintas y la similitud por `pgvector` pierde sentido; el umbral de AUTONOMIA-05 (no hay
alerta ni pregunta por debajo de la similitud configurada) dependería de vectores que confunden
personas. La revisión de NFR Requirements lo marcó como hallazgo mayor.

A. Numeración estable por versión de escenario: un nombre de la lista del escenario recibe siempre el
   número de su posición en esa lista (`[PERSONA_12]` es la misma persona en todas las llamadas de esa
   versión), calculado en cada llamada a partir de la lista que envía el cliente, sin guardar estado;
   lo que solo detectan las reglas se numera por llamada a partir del tamaño de la lista. Se añade una
   prueba de nivel 1 que compara, sobre el Golden Dataset, la similitud enmascarada con la no
   enmascarada. Precisa NFR8.3 en la tabla de precisiones. El destino puede enlazar menciones del mismo
   seudónimo entre llamadas, riesgo ya aceptado en el ADR como «estructura del testimonio».
   (Recomendada)
B. Marcador por categoría sin número para `embed` (`[PERSONA]`, `[LUGAR]`, `[EXPEDIENTE]`): estable
   entre llamadas y sin enlace entre seudónimos, pero dos personas distintas se vuelven iguales para la
   similitud. `judge` sigue numerando por llamada.
C. Se mantiene la numeración por llamada y se añade solo la prueba de nivel 1 de similitud; si no
   cumple, los *embeddings* externos quedan fuera de alcance y solo se admite `judge` externo.
X. Other (please specify)

[Answer]: A **Mode:** guided
## P2 — Sobre qué representación del texto se enmascara y se restaura

El bloque de datos del juez va como JSON dentro de `messages[].content` (decisión de NFR Requirements
de U4). Si el proxy busca nombres sobre ese texto serializado, un escape JSON lo deja pasar: «Peña»
escrito como `Peña` o «Ana Pérez» partido por un salto de línea (`Ana\nPérez`) no coincide con
ninguna regla y sale del clúster en claro, violando AUTONOMIA-04. En el regreso, restaurar en crudo un
nombre con comillas o barra invertida dentro de la respuesta JSON del juez (C6, esquema del resultado
del juez) puede romperla y contar como error de formato, cuyo umbral es 0 %.

A. Enmascarado y restauración sobre los valores ya decodificados: el proxy interpreta como JSON el
   contenido que lo es y enmascara cada cadena decodificada (las demás, como texto), y vuelve a
   serializar con `ensure_ascii=False`; la respuesta se restaura sobre sus cadenas decodificadas y se
   serializa de nuevo, así un nombre con comillas no rompe C6. Además, una comprobación final sobre el
   cuerpo exacto que se va a enviar (decodificado) busca los nombres de la lista y secuencias de 6 o más
   dígitos; si encuentra alguno, `failed_closed` sin enviar. Pruebas de propiedad de nivel 0 con
   escapes, saltos de línea y nombres con caracteres especiales. (Recomendada)
B. Enmascarado sobre el texto serializado tal cual, pero `failed_closed` si contiene cualquier
   secuencia `\u` o un salto de línea escapado entre palabras con mayúscula; restauración con escape
   JSON del valor cuando el marcador está dentro de una cadena. Sin comprobación final.
C. Enmascarado y restauración sobre el texto serializado tal cual, como dicen hoy los requisitos, sin
   tratamiento especial de escapes.
X. Other (please specify)

[Answer]: A **Mode:** guided