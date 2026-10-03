# Componentes lógicos — U10 anonymizer

**Insumos.** `nfr-requirements/performance-requirements.md` (performance-requirements),
`nfr-requirements/security-requirements.md` (security-requirements),
`nfr-requirements/scalability-requirements.md` (scalability-requirements),
`nfr-requirements/reliability-requirements.md` (reliability-requirements),
`nfr-requirements/observability-requirements.md` (observability-requirements) y
`nfr-requirements/tech-stack-decisions.md` (tech-stack-decisions) de esta unidad;
`functional-design/functional-spec.md` (functional-spec); C13–C16 de
`inception/contract-design/contract-summary.md` (contract-summary); respuestas P1 = A y P2 = A de
`nfr-design-questions.md`; los demás documentos de diseño de esta carpeta.

## 1. Inventario

| Componente lógico | Proceso y capa | Dentro o fuera del clúster | Responsabilidad | Patrones de NFR |
|---|---|---|---|---|
| `ProxyApi` | `anonymizer-proxy`, `api/` | Dentro | Rutas C14 permitidas, `404` para el resto, límites de cuerpo | Admisión con semáforo; Problem Details |
| `MaskedCall` | `application/` | Dentro | Orquesta validar, enmascarar, comprobar, enviar y restaurar | Falla cerrada; plazos con `fail_after`; tabla borrada en `finally` |
| `PayloadWalker` | `domain/` | Dentro | Decodificar y reserializar cadenas hoja (P2 = A) | Representación decodificada |
| `Masker` y `NumberingPlan` | `domain/` | Dentro | Detección `re2` y marcadores estables (P1 = A) | Tiempo lineal; sin estado |
| `OutboundCheck` | `domain/` | Dentro | Segunda barrera sobre el cuerpo exacto | Defensa en profundidad |
| `Restorer` | `domain/` | Dentro | Restaurar cadenas hoja de la respuesta | JSON válido tras restaurar |
| `UpstreamClient` | `adapters/` | Dentro; único con salida | HTTPS al destino del ADR | TLS ≥ 1.2, sin redirecciones, un intento, 4 cabeceras |
| `RulesLoader` y `Settings` | `adapters/` | Dentro | Reglas montadas `readOnly` y ajustes | No arranca mal configurado |
| `AnonymizerGateway` | `libs/model_gateway`, en `semantic-agent` y `session-api` | Dentro | Adaptador C13 que llama al proxy con la lista ordenada | Traduce `502` y `504` a finales |
| `anonymizer_route` | `libs/model_gateway` | Dentro | URL del proxy solo en juez y *embeddings* | 100 % de ramas |
| Destino externo | — | **Fuera** | Juez o *embeddings* del proveedor | Solo recibe marcadores |

Las capas `api/` → `application/` → `domain/` con `adapters/` se hacen cumplir con import-linter;
`domain/` no importa `httpx` ni nada de red (contrato de import-linter con control negativo).

## 2. Dominios de falla y radio de impacto

| Falla | Qué deja de funcionar | Qué sigue | Radio |
|---|---|---|---|
| Proxy apagado (por defecto) | Nada | Todo, con el juez interno | Ninguno |
| Caída del proxy habilitado | Juez y, si se usan, *embeddings* externos | Consola, revisión de alertas ya emitidas, afirmaciones bajo el umbral | Turnos en curso (error o reclamo) |
| Destino externo caído | Igual | Igual; nada se reenvía | Turnos en curso terminan en `error` |
| Reglas defectuosas | Toda llamada termina cerrada | Igual | Ninguna fuga: el radio es de disponibilidad, no de datos |

El diseño elige siempre que una falla del proxy cueste disponibilidad y nunca confidencialidad.

## 3. Recursos compartidos

| Recurso | Compartido con | Aislamiento |
|---|---|---|
| `libs/model_gateway` | U4, U8, U9 | El adaptador y la regla de ruta son módulos propios de U10 |
| Formateador de logs de `libs/` | Todas las unidades | Perfil de campos de U10 en la lista blanca |
| Catálogo `contracts/limits.v1.yaml` | Todas | Entradas `anonymizer.*` con U10 como dueña |
| Base de datos y Redis | — | El proxy no tiene credencial de ninguno |

## 4. Entrega a Infrastructure Design

- `Deployment`, `Service` y `NetworkPolicy` del proxy solo con `anonymizer.enabled: true`; 1 réplica;
  CPU `requests` 100m y `limits` 1; `limits.memory` = pico medido + ≥ 20 %.
- `ConfigMap` de reglas montado `readOnly`, `emptyDir` en memoria de ≤ 16 MiB para `/tmp`, Secret
  `veridicus-anonymizer-credential` por `secretKeyRef`, `automountServiceAccountToken: false`.
- Riesgos transferidos: desactivar los volcados de memoria (*core dumps*) en el nodo; limitar la
  resolución DNS externa a lo necesario si el CNI lo permite (T15); CNI con políticas por FQDN si el
  proveedor no tiene CIDR estables, o el proxy no se habilita.
- Tabla de fronteras de AUTONOMIA-04: el proxy aparece fuera de la frontera solo con el *payload*
  enmascarado (BR3.4).

## 5. Calidad, pruebas y textos (NFR2.1, NFR2.2, NFR12.1, NFR13.1, NFR13.2, NFR14.1)

- **Sin red y en CPU (NFR2.1).** Nivel 0 con `httpx.MockTransport`; nivel 1 con un servidor HTTPS local
  y certificado de `trustme`; `pytest-socket` falla ante cualquier conexión fuera de `localhost`.
  Ninguna prueba llama a un proveedor real ni descarga un modelo.
- **Sin GPU (NFR2.2).** Prueba de nivel 0 sobre el render de `values-cpu.yaml` y `values-gpu.yaml` con
  el proxy habilitado en un *values* de prueba: 0 `nvidia.com/gpu` en el proxy.
- **Datos sintéticos (NFR12.1).** *Fixtures* del catálogo de U1 con `synthetic: true`; la comprobación
  de U1 sobre `services/anonymizer-proxy/tests/` da 0 hallazgos.
- **Cobertura (NFR13.1, NFR13.2).** ≥ 80 % de líneas en `services/anonymizer-proxy`; 100 % de ramas en
  `domain/` y `application/` del proxy y en `libs/model_gateway/anonymizer_route.py` y el adaptador
  `AnonymizerGateway`, con `.coveragerc-guards`.
- **Textos (NFR14.1).** `detail` de los errores desde el catálogo en español; identificadores del
  glosario (`masking_request`, `mask_table`, `mask_category`, `detection_rule_set`,
  `outbound_destination`, `marker`, `proper_nouns`, y los nuevos `numbering_plan` y `outbound_check`);
  marcadores con categorías en español porque son valores del contrato.
