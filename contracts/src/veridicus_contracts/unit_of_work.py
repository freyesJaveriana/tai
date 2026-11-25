"""`UnitOfWork`: la transacción compartida de `session-api` (C10, C11, C12, C23 y C24).

contract-summary lo nombra entre comillas en cada firma de las interfaces en proceso y no lo define
(P-T16-1). Aquí va como `Protocol` sin métodos, en un solo módulo que importan los demás: el
contrato no fija qué hace la transacción, solo que es la misma en toda la llamada. La consolidación
lee, escribe la versión del reporte y bloquea la ronda en una sola transacción (ADR-001, AC6.1.6) y
ningún módulo abre la suya propia dentro de estas llamadas. U4 aporta la implementación.
"""

from typing import Protocol


class UnitOfWork(Protocol):
    """La transacción abierta por quien llama (ConsoleApi o el trabajador); sin métodos propios."""
