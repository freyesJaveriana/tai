"""C11 v2.0.0: lo que ReviewReport usa de los demás módulos (en proceso).

Sale `ScenarioReader` (TruthFrame); cambia la instantánea de la sesión y se renombra el consumidor
(ReviewReport, antes ForensicReport). Revisión 4: `for_update`, `pending_counts`,
`discard_correction_round`, `SessionLifecycle` y `PendingSessions`. Importaciones:
`veridicus_contracts.report_ports` (FD-U1-04). Solo firmas: las implementaciones son de U4, U5 y U7.

Los tipos auxiliares que contract-summary nombra entre comillas van como `Protocol` de solo lectura
(P-T16-2), con los campos que nombran las docstrings y la revisión 4 (P-T16-3).
"""

from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any, Literal, Protocol
from uuid import UUID

from veridicus_contracts.analyzer.v1 import Hallazgo
from veridicus_contracts.human_review import Actor
from veridicus_contracts.unit_of_work import UnitOfWork

RoundState = Literal["open", "locked", "discarded"]
SuggestionState = Literal["pending", "accepted", "edited", "dismissed"]


class TurnView(Protocol):
    """Un turno de la instantánea: su número `T<n>`, hablante, página (si la hay) y estado."""

    @property
    def turn(self) -> str: ...

    @property
    def speaker(self) -> str: ...

    @property
    def page(self) -> int | None: ...

    @property
    def state(self) -> str: ...


class RunView(Protocol):
    """Una corrida de la instantánea con su registro de modelos y su modo fragmentado."""

    @property
    def run_id(self) -> UUID: ...

    @property
    def state(self) -> str: ...

    @property
    def fragmented(self) -> bool: ...

    @property
    def model_registry(self) -> Mapping[str, Any]:
        """El `registro` de C6 de la corrida (llamadas, descartes, tokens); sin texto."""
        ...


class SessionSnapshot(Protocol):
    """La instantánea de una sesión (FD-U6-21, FD-U7-03). Nunca lleva datos del consentimiento."""

    @property
    def session_id(self) -> UUID: ...

    @property
    def state(self) -> str: ...

    @property
    def owner_user_id(self) -> UUID: ...

    @property
    def origin(self) -> str: ...

    @property
    def profile(self) -> str: ...

    @property
    def profile_same_family(self) -> bool:
        """La marca de misma familia entre juez y verificador del perfil."""
        ...

    @property
    def config_sha256(self) -> str: ...

    @property
    def finalized_at(self) -> datetime | None: ...

    @property
    def terminated_at(self) -> datetime | None: ...

    @property
    def consent_withdrawn_at(self) -> datetime | None:
        """Solo la hora de la retirada, sin datos del consentimiento (FD-U6-21)."""
        ...

    @property
    def blocked_code(self) -> str | None: ...

    @property
    def last_final_mode_state(self) -> str | None: ...

    @property
    def turns(self) -> Sequence[TurnView]: ...

    @property
    def runs(self) -> Sequence[RunView]: ...

    @property
    def pending_runs(self) -> int:
        """Cuántas corridas siguen en `queued` o `processing`."""
        ...


class RoundView(Protocol):
    """Una ronda de revisión; `discarded` no vuelve nunca a `open` (FD-U5-04)."""

    @property
    def round_id(self) -> UUID: ...

    @property
    def session_id(self) -> UUID: ...

    @property
    def number(self) -> int: ...

    @property
    def state(self) -> RoundState: ...

    @property
    def is_correction(self) -> bool: ...


class SuggestionWithDecision(Protocol):
    """Una sugerencia con su estado vigente (FD-U5-05)."""

    @property
    def suggestion_id(self) -> UUID: ...

    @property
    def hallazgo(self) -> Hallazgo: ...

    @property
    def state(self) -> SuggestionState: ...

    @property
    def note(self) -> str | None: ...

    @property
    def reformulation(self) -> str | None: ...

    @property
    def decided_by(self) -> UUID | None: ...

    @property
    def decided_at(self) -> datetime | None: ...


class SessionReader(Protocol):
    """Dueño: InterviewSession (U4, U6)."""

    def snapshot(self, uow: UnitOfWork, session_id: UUID) -> SessionSnapshot:
        """Estado, dueño, perfil y config_sha256, finalized_at, turnos con hablante, página y estado,
        corridas con su registro de modelos y su modo fragmentado, y cuántas corridas siguen
        queued o processing. Sin consentimiento con datos personales (no los hay, P11).

        Revisión 4: suma `consent_withdrawn_at` y conserva `terminated` (FD-U6-21), y declara
        origen, `blocked_code`, terminación y retirada con su hora, estado del último modo final
        y perfil con la marca de misma familia (FD-U7-03).
        """
        ...


class ReviewRounds(Protocol):
    """Dueño: HumanReview (U5)."""

    def open_round(
        self, uow: UnitOfWork, session_id: UUID, for_update: bool = False
    ) -> RoundView | None:
        """Con for_update=True bloquea la fila de la ronda; el orden de bloqueo es sesión → ronda
        (regla de project.md). Si la sesión no tiene ronda, con for_update=True abre la 1 y la
        devuelve (revisión 4, FD-U5-03).
        """
        ...

    def pending_count(self, uow: UnitOfWork, round_id: UUID) -> int:
        """Vale también para `pending_suggestions` de la vista (FD-U6-20)."""
        ...

    def pending_counts(self, uow: UnitOfWork, session_ids: list[UUID]) -> dict[UUID, int]:
        """Pendientes por sesión, para la lista de sesiones (NFR-U6-04)."""
        ...

    def decisions(self, uow: UnitOfWork, round_id: UUID) -> list[SuggestionWithDecision]:
        """Devuelve el estado vigente de cada sugerencia con su propia nota, y la reformulación
        solo si el estado es `edited` (revisión 4, FD-U5-05).
        """
        ...

    def lock_round(
        self, uow: UnitOfWork, round_id: UUID, report_version_id: UUID, actor: Actor
    ) -> None:
        """Falla con report.conflict si la ronda ya está bloqueada (una sola consolidación gana).

        Siempre con un actor: ninguna firma consolida sin un humano (AUTONOMIA-03).
        """
        ...

    def open_correction_round(self, uow: UnitOfWork, session_id: UUID, actor: Actor) -> UUID:
        """Abre o retoma la única ronda de corrección de la sesión. No guarda la versión de la que
        parte: ReviewReport la deduce de la ronda bloqueada anterior (R-01 de Domain Design).
        """
        ...

    def discard_correction_round(self, uow: UnitOfWork, session_id: UUID, actor: Actor) -> None:
        """Descarta la ronda de corrección abierta (estado `discarded`, revisión 4, FD-U5-04).

        Solo sobre una ronda de corrección abierta; guarda quién y cuándo y nunca vuelve a
        `open`. Sin copia abierta, falla con report.conflict.
        """
        ...


class SessionLifecycle(Protocol):
    """Dueño: InterviewSession (FD-U7-02)."""

    def finalize(self, uow: UnitOfWork, session_id: UUID, actor: Actor) -> None: ...

    def mark_consolidated(
        self,
        uow: UnitOfWork,
        session_id: UUID,
        report_version_id: UUID,
        actor: Actor,
        finalize_first: bool = False,
    ) -> None:
        """Marca la sesión consolidada por un humano (AUTONOMIA-03). Con finalize_first=True
        finaliza antes, en la misma transacción.
        """
        ...


class PendingSessions(Protocol):
    """Lo que ConsoleApi usa al cambiar un rol (FD-U3-04)."""

    def count_pending(self, uow: UnitOfWork, owner_user_id: UUID) -> int:
        """Sesiones pendientes del usuario. El adaptador por defecto devuelve 0 hasta que U4 cree
        la tabla de sesiones.
        """
        ...
