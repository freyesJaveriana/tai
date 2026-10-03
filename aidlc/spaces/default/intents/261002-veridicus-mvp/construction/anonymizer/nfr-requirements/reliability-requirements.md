# Requisitos de fiabilidad — U10 anonymizer

**Insumos.** Flujos F1–F3, la máquina de estados de una llamada y §8 «Errores y bordes» de
`functional-design/functional-spec.md` (functional-spec); reglas BR1.3, BR2.1, BR2.2 y BR3.2 de
`functional-design/rules.md` (rules); FR11.3, NFR4, NFR6 y NFR10 de
`inception/requirements-analysis/requirements.md` (requirements); C13, C14 y C16 de
`inception/contract-design/contract-summary.md` (contract-summary); respuesta P1 = A de
`nfr-requirements-questions.md`; NFR10.14–NFR10.16 de U4.

## 1. Objetivos

U10 es COULD y se entrega apagado: no tiene objetivo de disponibilidad, y ninguna función MUST depende
de él. Lo que sí es obligatorio, esté o no desplegado, es que **falle cerrado**: ante cualquier duda no
sale nada. Si se habilita y se cae, los turnos terminan en error y el analista los reintenta a mano;
el sistema puede volver al juez interno con un PR que apague el proxy.

## 2. Falla cerrada, *timeout* y arranque

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR10.1 | Falla cerrada en **cada rama** (BR2.1). | Ramas que terminan en `failed_closed` con `500` `anonymizer.masking_failed` (o el código de NFR10.8) y **0 peticiones al destino**: reglas no cargadas o con SHA-256 distinto; lista de nombres ausente, inválida o fuera de límites; error del detector; enmascarado que pasa de 2 s (NFR3.4); texto de entrada con forma de marcador; tabla incoherente (un mismo valor normalizado con dos marcadores); cuerpo inválido o demasiado grande; cualquier excepción no prevista dentro de `masking`. El destino *fake* cuenta las peticiones: 0 en cada rama. El módulo entero (`domain/` y `application/` del proxy) tiene **100 % de ramas** (NFR13.2). | Nivel 0 |
| NFR10.4 | *Timeout* explícito hacia el destino y **sin reintentos**. | Un solo intento por llamada: conexión 5 s; lectura `judge` 170 s y `embed` 25 s (menores que los *timeouts* de 180 s y 30 s del cliente de U4, para que el error del proxy llegue antes); el *values* no puede subirlos por encima de esos topes (el proxy no arranca). *Timeout* → `504` `anonymizer.upstream_timeout`; 4xx, 5xx, 3xx, conexión rechazada o respuesta ilegible → `502` `anonymizer.upstream_error`; en ambos casos la tabla se borra y no hay segundo intento. Pruebas de nivel 0 con un *fake* lento, uno que devuelve 500, uno con 429 y uno que corta la conexión: el *fake* registra **exactamente 1** petición en cada caso. Con la precisión a NFR10.16 de U4 (`security-requirements.md` §6), tampoco hay reenvío por la cola. | Nivel 0 |
| NFR10.7 | El proxy no arranca mal configurado y `/readyz` no sale del clúster (BR2.2, C16). | Al arrancar se validan: reglas (SHA-256 y `schema_version`), `VERIDICUS_ANONYMIZER_UPSTREAM_URL` (NFR10.5), `VERIDICUS_ANONYMIZER_API_KEY` presente, modelo declarado y *timeouts* dentro de sus topes. Si algo falta o es inválido, el proceso termina con código ≠ 0 y un log que nombra el ajuste (nunca su valor). `/healthz` responde 200 si el proceso vive; `/readyz` responde 200 solo con todo lo anterior válido y **no** hace ninguna petición al destino externo. Prueba de nivel 0 por ajuste ausente o inválido; prueba de nivel 1 de que `/readyz` no abre conexiones salientes. | Nivel 0 y nivel 1 |

## 3. Restauración y calidad de la IA con un juez externo

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR6.1 | La CoT restaurada se lee con los nombres reales. | Toda aparición en la respuesta de un marcador de la tabla de la llamada se restaura a su valor original (BR1.3, E5): **0 marcadores conocidos** quedan en la respuesta devuelta; los desconocidos se dejan tal cual y se cuentan (`unknown_markers` en el log). Prueba de propiedad de nivel 0 con Hypothesis: enmascarar y restaurar un texto sin marcadores previos devuelve el mismo texto. La validación de C6 y el escaneo de C8 siguen en U4, después de restaurar. | Nivel 0 |
| NFR4.1 | Habilitar el proxy no empeora la calidad de la IA. | El PR de habilitación adjunta el reporte de nivel 2 con el proxy en el camino y cumple todos los umbrales de NFR4 de requirements (≥ 5 de 6 discrepancias, ≤ 1 alerta en las alineadas, 100 % de trazabilidad factual, 0 % de error de formato JSON, consistencia > 65 % al invertir el orden, y Hecho No Documentado con 0 alertas, 0 preguntas y 1 paquete). Si se cambian también los *embeddings*, el PR reindexa los escenarios y recalibra el umbral con el barrido de NFR4.1 de U4. | Nivel 2, en el PR de habilitación |
| NFR4.2 | La evaluación con juez externo es repetible. | El ADR declara que el proveedor acepta `temperature = 0` y `seed`; dos corridas de nivel 2 seguidas dan las mismas calificaciones, `passage_ids` y alertas (NFR4.2 de U4). Si el proveedor no lo garantiza y las corridas difieren, el proxy no se habilita. | Nivel 2, en el PR de habilitación |

## 4. Fallas y recuperación

| Falla | Qué se pierde | Cómo se recupera |
|---|---|---|
| Error en el enmascarado | Nada sale; el turno queda en `error` con `turn.error.system` | El analista usa «Reintentar evaluación»; si se repite, es un hallazgo de las reglas |
| *Timeout* o error del destino | El turno queda en `error` (`turn.error.timeout` o `turn.error.system`) | Reintento manual; sin reintento automático hacia fuera (NFR10.4) |
| Proxy saturado (`anonymizer.busy`) | Nada; no se envió nada | El mensaje vuelve por la cola de U4 (recuperable) |
| Caída o reinicio del proxy | La llamada en curso; la tabla en memoria desaparece con el proceso | El cliente recibe error de conexión hacia el proxy (dentro del clúster) y lo trata como U4 trata un servidor de modelo caído |
| Proveedor que incumple el ADR | — | PR que pone `anonymizer.enabled: false` y devuelve las URL al juez interno; la verificación de NFR1.7 confirma que ya no hay salida |

## 5. Degradación

Con el proxy apagado (por defecto) no hay degradación posible: el sistema usa el juez interno. Con el
proxy habilitado y el destino caído, la consola sigue respondiendo (NFR3.9 de U4), los turnos terminan
en error con su `code` y nada se reenvía; el `/readyz` de los clientes muestra la dependencia caída
según NFR10.19 de U4.
