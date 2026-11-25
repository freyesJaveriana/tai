"""C24 v1.1.0: puertos de borrado para la retención (en proceso).

El Job de retención de U13 (demostración, lo lanza el humano) borra una sesión vencida en el orden
inverso de las referencias. Cada unidad borra solo lo suyo y solo el usuario de base de datos del
Job tiene `DELETE` (A-2). Importaciones: `veridicus_contracts.retention` (FD-U1-04). Solo firmas:
las implementaciones son de U4, U5, U7 y U13.

Orden del Job:
  (1) EthicsGovernance.ProblemReport de la sesión (incluidos los ligados por sugerencia, UG-01);
  (2) ReviewReport: ReportExport y ReportVersion de la más nueva a la más antigua, con sus archivos;
  (3) HumanReview: ObservationsView, ReviewDecision, ReviewSuggestion, ReviewRound;
  (4) InterviewSession: todo lo de la sesión y por último InterviewSessionRecord.

`AnonymizationIncident` no se borra: sobrevive sin clave foránea, solo con IDs (FD-U4-12). El acta
(RetentionAct) y el registro de acceso sobreviven sin clave foránea.
"""

from collections.abc import Mapping, Sequence
from typing import Protocol
from uuid import UUID

from veridicus_contracts.unit_of_work import UnitOfWork


class PurgedVersion(Protocol):
    """Una versión de reporte borrada; el recibo no lleva texto (FD-U7-12)."""

    @property
    def report_version_id(self) -> UUID: ...

    @property
    def sha256(self) -> str: ...

    @property
    def file_missing(self) -> bool:
        """El archivo ya no estaba al borrar la versión."""
        ...


class PurgeReceipt(Protocol):
    """El recibo de un borrado: IDs y SHA-256, nunca texto (P-T16-3)."""

    @property
    def session_id(self) -> UUID: ...

    @property
    def deleted_ids(self) -> Mapping[str, Sequence[UUID]]:
        """Los IDs borrados por tipo de registro."""
        ...

    @property
    def versions(self) -> Sequence[PurgedVersion]:
        """Solo en ReviewReport; vacía en los demás módulos."""
        ...


class Purgeable(Protocol):
    """Puerto de borrado por sesión que implementa cada módulo que guarda datos de la sesión."""

    def purge_session(self, uow: UnitOfWork, session_id: UUID) -> PurgeReceipt:
        """Borra lo de la sesión que pertenece a este módulo y devuelve los IDs borrados y, en
        ReviewReport, los SHA-256 de los reportes. Nunca devuelve texto.

        InterviewSession borra TranscriptPaste antes que Turn (FD-U6-22) y los archivos de
        TurnAudio antes que su fila; el acta lleva audio_id y sha256 (FD-U9-09).
        """
        ...

    def count_session(self, uow: UnitOfWork, session_id: UUID) -> Mapping[str, int]:
        """Cuenta, por tipo de registro, lo que `purge_session` borraría, sin borrar nada
        (NFRD-U13-08).
        """
        ...
