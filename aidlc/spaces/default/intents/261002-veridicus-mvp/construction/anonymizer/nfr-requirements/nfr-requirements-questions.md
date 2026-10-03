# Preguntas de NFR Requirements — U10 anonymizer

**Unidad.** U10 `anonymizer` (COULD): proxy que enmascara nombres, lugares y expedientes antes de llamar
a un modelo externo y falla cerrado (`functional-design/functional-spec.md`, `rules.md`).

**Lo que ya está decidido y no se vuelve a preguntar.** Marcadores consistentes con restauración dentro
del clúster (P1), lista de nombres propios del escenario (P2), sin reintentos hacia el destino, solo el
proxy con salida, y que el juez por defecto del MVP es el interno. Los tiempos y la cobertura del módulo
guardia salen de team-practices y no necesitan pregunta.

---

## P1 — Condiciones para usar un proveedor externo

Aunque solo salgan marcadores, el destino externo recibe la estructura del testimonio. FR11.3 no fija
qué proveedor es aceptable ni cómo se habilita el proxy.

A. El proxy se entrega apagado. Habilitarlo exige un PR con un ADR del proveedor: compromiso escrito de
   no usar los datos para entrenar, retención ≤ 30 días, región declarada y TLS 1.2 o superior; el
   PR también cambia la `NetworkPolicy` para ese único destino. (Recomendada)
B. Cualquier proveedor compatible con OpenAI por HTTPS, sin más condiciones, porque los datos salen
   enmascarados.
C. No construir U10 en el MVP: se documentan sus requisitos y la unidad queda diferida.
X. Other (please specify)

[Answer]: A **Mode:** guided
