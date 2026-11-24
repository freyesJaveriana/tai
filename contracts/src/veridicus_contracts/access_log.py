"""C23 v1.0.0: puerto `AccessLog` (en proceso).

La interfaz la define U7 y el adaptador real lo aporta U13; ConsoleApi la cablea y la llama
(UG-09, ADR-016). EthicsGovernance no importa nada de ConsoleApi. Importaciones:
`veridicus_contracts.access_log` (FD-U1-04). El adaptador por defecto (no registra, avisa solo con
IDs y `/readyz` informa `access_log: not_configured`) es de U7, no de este módulo.
"""

from typing import Literal, Protocol
from uuid import UUID

from veridicus_contracts.unit_of_work import UnitOfWork

ResourceType = Literal["session", "suggestion", "report_version", "report_export"]


class AccessLog(Protocol):
    def record(
        self,
        uow: UnitOfWork,
        user_id: UUID,
        resource_type: ResourceType,
        resource_id: UUID,
        export_sha256: str | None = None,
    ) -> None:
        """Solo inserción y sin texto (VE-11). export_sha256 solo para report_export (A-3).

        Revisión 4 (FD-U13-11): el adaptador real lanza una excepción ante un fallo o un timeout,
        sin reintentos. En la exportación tiene 500 ms: si falla o vence, la exportación
        revierte la transacción y responde 503 report.export_not_recorded (NFR-U7-09). En las
        lecturas marcadas con x-veridicus-access-log la respuesta sale igual (FD-U3-05).
        """
        ...
