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

---

# Segunda pasada — cambio 01, adenda 02 y NFR Requirements revisión vigente (2026-11-22)

**Por qué hay segunda pasada.** La revisión 1 (2026-10-03) diseñó un proxy COULD y apagado, delante del
juez y de `embed`, con la lista de nombres del escenario. El cambio 01 hace MUST a U10, retira `embed` y
la lista de nombres, y pone el módulo en el camino de toda llamada comercial, en la CLI y en el clúster.
El Functional Design revisión 2 (F1–F9, FD-U10-01 a FD-U10-17) y el NFR Requirements revisión 2 (tabla
NFR-U10-01 a NFR-U10-12) ya están aprobados.

## Lo que ya está decidido

| Tema | Qué queda fijo | Fuente |
|---|---|---|
| P1 y P2 de la revisión 1 | P1 = A pierde su objeto (sale `embed` y la lista del escenario; la numeración es por primera aparición dentro de la llamada, FD-U10-01). P2 = A sigue: se seudonimiza y se restaura sobre los valores de cadena decodificados (BR1.1, BR1.3, NFR10.14) | Revisión 1; cambio 01 |
| Requisitos | NFR1.2–NFR1.14, NFR2.1–NFR2.2, NFR3.1–NFR3.6, NFR4.1–NFR4.3, NFR5.1–NFR5.2, NFR6.1–NFR6.2, NFR8.1–NFR8.5, NFR10.1–NFR10.16, NFR11.1, NFR12.1, NFR13.1–NFR13.2, NFR14.1, NFR15.1–NFR15.4; decisiones D1–D13 | `nfr-requirements/`, revisión 2 |
| Proveedor de la primera rebanada | Anthropic, con su adaptador y su ADR primero en B10; verificador local | P2 = A de NFR Requirements; NFR-U11-01 |
| Tamaños | Transcripción de hasta 250 000 caracteres; las comprobaciones de U10 se repiten con esa cifra; `model_call_timeout_s` ≥ 270 s con perfil comercial | NFR-U4-02 (P6 = A) |
| Cifras de C25 | `anonymizer_request_max_bytes`, `anonymizer_response_max_bytes` y `anonymizer_masking_budget_ratio`, ya en C25 v1 | NFRD-U1-02 |
| Métricas | En `contracts/metrics/anonymizer.v1.yaml`, con la lista cerrada de etiquetas de U1 | NFRD-U1-05 |
| Límites por entorno | El catálogo empaquetado es el techo; `VERIDICUS_LIMIT_<NOMBRE>` solo baja | NFRD-U1-09 |
| Red, Secret y montajes | `NetworkPolicy`, CoreDNS, Secret `veridicus-provider-keys` y `ConfigMap` `veridicus-profiles` son de U2 | NFR1.4, NFR1.5, NFR10.12, NFR10.15 de U2 |

## Cómo se registra la revisión

- Los seis documentos y `traceability.json` pasan a la revisión 2 en el mismo archivo, con una nota de
  cabecera que dice qué cambia y por qué. La revisión 1 queda en el historial de Git.
- Las secciones y las decisiones conservan su número cuando siguen; las que salen quedan «Retirado» sin
  renumerar y lo nuevo toma números nuevos.
- Las precisiones a artefactos aprobados van en la tabla NFRD-U10-xx de `security-design.md`. Ningún
  original se edita.

## Lo que el diseño resolverá sin preguntar

1. **Hallazgos de la revisión 1 de esta etapa que siguen vivos.** R-02 (normalización con NFKC y sin
   caracteres de formato, y una verificación final del cuerpo con su propia lógica), R-03 (errores de
   transporte después del envío y reentrega de la cola de U4), R-05 (el cupo del semáforo se mantiene
   hasta que termina el hilo del NER) y R-08 (el formateador de logs solo admite campos con tipo). R-01,
   R-04, R-06 y R-07 desaparecen con el cambio 01 o pasan a U2.
2. **Esquema hacia Anthropic.** La salida estructurada del proveedor no admite `minimum`, `maxLength`,
   `if`/`then` ni `oneOf`, que el esquema de C6 usa. El adaptador envía una proyección determinista del
   esquema, solo quitando palabras clave, y valida la respuesta contra el esquema completo (D11). Lo saliente
   es un subconjunto del esquema, que no trae testimonio.
3. **Caché de *prompts* (FR15.1).** El punto de caché va solo en el bloque `system`, que no trae
   testimonio (F5). Así el proveedor no guarda en caché nada del relato.
4. **Etiqueta de métricas.** `code` pasa a `error_code`, el nombre de la lista cerrada de U1.
5. **Prometheus y el panel.** U2 hoy no deja a Prometheus raspar el proxy; se le pide la regla de entrada
   al puerto de métricas y que empaquete el panel con su copia verificada.
6. **Tamaños de 250 000 caracteres** en las pruebas de rendimiento, de memoria y de cifras atadas.

Ningún punto cambia el alcance ni deja salir del clúster algo que hoy no sale; los puntos 2 y 3 reducen lo
que sale.

Queda una pregunta, porque dos fuentes aprobadas hoy se contradicen.

## P3 — Qué responde el proxy cuando el cuerpo de C21 pasa de `anonymizer_request_max_bytes`

Las dos fuentes son de hoy:
- **U10** (NFR10.8 y BR6.1) dice que el exceso responde `422` `anonymizer.destination_rejected`.
- **U1** (NFR Design revisión 2, §4.3 y §4.17) dice otra cosa. El cuerpo de C21 declara
  `x-veridicus-max-bytes: anonymizer_request_max_bytes`, y «toda operación con `x-veridicus-max-bytes`
  declara `413` con `limits.exceeded`». `checks/limits_match.py` lo comprueba.

C21 no declara `413`, así que la suite de U1 pondría C21 en rojo. En los dos casos no sale ninguna llamada
y el cliente de U11 termina en `AnonymizerUnavailable`. Solo cambia el código HTTP y el `code`.

A. El proxy responde `413` `limits.exceeded` ante un cuerpo demasiado grande, como el resto del sistema.
   `422` `anonymizer.destination_rejected` queda para el cuerpo que no valida, el perfil o el papel
   inexistente y el destino local. Se anotan precisiones a NFR10.8, BR6.1, F8 paso 1 y C21, y el cliente de
   C21 de U11 traduce `413` a `AnonymizerUnavailable`. (Recomendada: sigue la regla única de
   `limits.exceeded` y la comprobación de U1 que ya está aprobada).
B. Se mantiene `422` `anonymizer.destination_rejected`, y se pide a U1 una excepción en
   `checks/limits_match.py` para C21, que es un contrato interno entre servicios y no de C1.
C. Se mantiene `422` y C21 deja de declarar `x-veridicus-max-bytes`: el tope queda solo en el código del
   proxy. Esto choca con NFR10.7 de U1, que exige ese tope con nombre en C21.
X. Other (please specify)

[Answer]: A **Mode:** guided