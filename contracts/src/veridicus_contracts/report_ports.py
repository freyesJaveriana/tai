"""C11 v2.0.0: lo que ReviewReport usa de los demás módulos (en proceso).

Sale `ScenarioReader` (TruthFrame); cambia la instantánea de la sesión y se renombra el consumidor
(ReviewReport, antes ForensicReport). Revisión 4: `for_update`, `pending_counts`,
`discard_correction_round`, `SessionLifecycle` y `PendingSessions`. Importaciones:
`veridicus_contracts.report_ports` (FD-U1-04). Solo firmas: las implementaciones son de U4, U5 y U7.

Los tipos auxiliares que contract-summary nombra entre comillas van como `Protocol` de solo lectura
(P-T16-2). Sus campos toman el nombre, el tipo y los valores cerrados de las entidades aprobadas de
la unidad dueña (P-T16-8): U4 (`text-flow/functional-design/entities.md`, BR17.2) para la sesión,
los turnos y las corridas, y U5 (`human-review/functional-design/entities.md`) para la ronda y la
decisión. Los valores fijos son `Literal`. Un campo que ninguna entidad nombra no está aquí: el
texto del turno (K-41) y la hora de la terminación quedan como candidatas.
"""

from collections.abc import Sequence
from datetime import datetime
from typing import Literal, Protocol
from uuid import UUID

from veridicus_contracts.analyzer.v1 import Hallazgo
from veridicus_contracts.human_review import Actor
from veridicus_contracts.unit_of_work import UnitOfWork

# U4: InterviewSessionRecord.status, .origin, .blocked_code; Turn.speaker y .fold_state;
# AnalysisRun.mode; RunStatusChange.to_status; ModelCall.role.
SessionStatus = Literal[
    "open", "paused", "suspended", "finalized", "terminated", "blocked", "consolidated"
]
SessionOrigin = Literal["guiada", "corpus", "sintetico"]
BlockedCode = Literal["anonymizer.incident"]
Speaker = Literal["ENT", "TEST"]
FoldState = Literal["visible", "plegado"]
RunMode = Literal["incremental", "final"]
RunStatus = Literal["queued", "processing", "done", "error", "cancelled"]
ModelCallRole = Literal["juez", "verificador", "verificador_permutado"]
# U5: ReviewRound.kind y .status; EffectiveState (ReviewDecision.previous_state más `pending`).
RoundKind = Literal["initial", "correction"]
RoundStatus = Literal["open", "locked", "discarded"]
EffectiveState = Literal["pending", "accepted", "edited", "dismissed"]


class TurnView(Protocol):
    """Un turno de la instantánea (entidad `Turn`): sin su texto (K-41)."""

    @property
    def n(self) -> int: ...

    @property
    def speaker(self) -> Speaker: ...

    @property
    def page(self) -> int | None: ...

    @property
    def fold_state(self) -> FoldState: ...


class ModelCallView(Protocol):
    """Una fila del registro de modelos de la corrida (entidad `ModelCall`); sin texto."""

    @property
    def role(self) -> ModelCallRole: ...

    @property
    def provider(self) -> str: ...

    @property
    def model(self) -> str: ...

    @property
    def version(self) -> str | None: ...

    @property
    def effort_or_quantization(self) -> str | None: ...

    @property
    def engine(self) -> str | None: ...

    @property
    def seed(self) -> int | None: ...

    @property
    def tokens_in(self) -> int: ...

    @property
    def tokens_out(self) -> int: ...

    @property
    def used_fallback(self) -> bool: ...

    @property
    def external(self) -> bool: ...

    @property
    def anonymized(self) -> bool: ...

    @property
    def at(self) -> datetime: ...


class RunView(Protocol):
    """Una corrida de la instantánea (entidades `AnalysisRun`, `RunStatusChange`, `RunAttempt`)."""

    @property
    def run_id(self) -> UUID: ...

    @property
    def mode(self) -> RunMode: ...

    @property
    def from_turn(self) -> int: ...

    @property
    def to_turn(self) -> int: ...

    @property
    def status(self) -> RunStatus:
        """El estado vigente: el de la última fila de `RunStatusChange`."""
        ...

    @property
    def attempt(self) -> int:
        """El intento vigente."""
        ...

    @property
    def fragmented(self) -> bool | None:
        """`RunAttempt.fragmented`: nulo si la corrida aún no tiene resultado."""
        ...

    @property
    def covered_by_final(self) -> bool:
        """Una corrida incremental en error que cubre el último modo final terminado (BR17.2)."""
        ...

    @property
    def model_calls(self) -> Sequence[ModelCallView]: ...


class SessionSnapshot(Protocol):
    """La instantánea de una sesión (FD-U6-21, FD-U7-03). Nunca lleva datos del consentimiento."""

    @property
    def session_id(self) -> UUID: ...

    @property
    def owner_user_id(self) -> UUID: ...

    @property
    def profile_name(self) -> str: ...

    @property
    def config_sha256(self) -> str: ...

    @property
    def same_family_declared(self) -> bool:
        """La marca de misma familia del perfil (`profile.same_family_declared` de C18)."""
        ...

    @property
    def status(self) -> SessionStatus: ...

    @property
    def origin(self) -> SessionOrigin: ...

    @property
    def finalized_at(self) -> datetime | None: ...

    @property
    def terminated_at(self) -> datetime | None:
        """La hora de la terminación: `SessionStatusChange.at` con `to_status: terminated`
        (P-T16-10); nulo si la sesión no terminó.
        """
        ...

    @property
    def consent_withdrawn_at(self) -> datetime | None:
        """Solo la hora de la retirada, sin datos del consentimiento (FD-U6-21)."""
        ...

    @property
    def blocked_code(self) -> BlockedCode | None: ...

    @property
    def turns(self) -> Sequence[TurnView]: ...

    @property
    def runs(self) -> Sequence[RunView]: ...

    @property
    def pending_runs(self) -> int:
        """Cuántas corridas siguen en `queued` o `processing`."""
        ...


class RoundView(Protocol):
    """Una ronda de revisión (entidad `ReviewRound`); `discarded` no vuelve nunca a `open`."""

    @property
    def round_id(self) -> UUID: ...

    @property
    def session_id(self) -> UUID: ...

    @property
    def number(self) -> int: ...

    @property
    def kind(self) -> RoundKind: ...

    @property
    def status(self) -> RoundStatus: ...

    @property
    def based_on_round_id(self) -> UUID | None:
        """Obligatoria si `kind` es `correction`: la última ronda `locked` de la sesión."""
        ...


class SuggestionWithDecision(Protocol):
    """Una sugerencia con su estado vigente (FD-U5-05)."""

    @property
    def suggestion_id(self) -> UUID: ...

    @property
    def hallazgo(self) -> Hallazgo: ...

    @property
    def state(self) -> EffectiveState: ...

    @property
    def note(self) -> str | None: ...

    @property
    def reformulation(self) -> str | None: ...

    @property
    def decided_by(self) -> UUID | None:
        """Quién decidió (`EffectiveState.decided_by`, como C7 v2); nulo si sigue `pending`
        (P-T16-9).
        """
        ...

    @property
    def decided_at(self) -> datetime | None:
        """Cuándo decidió (`EffectiveState.decided_at`, como C7 v2); nulo si sigue `pending`."""
        ...


class SessionReader(Protocol):
    """Dueño: InterviewSession (U4, U6)."""

    def snapshot(self, uow: UnitOfWork, session_id: UUID) -> SessionSnapshot:
        """Estado, dueño, perfil y config_sha256, finalized_at, turnos con hablante, página y estado,
        corridas con su registro de modelos y su modo fragmentado, y cuántas corridas siguen
        queued o processing. Sin consentimiento con datos personales (no los hay, P11).

        Revisión 4: suma `consent_withdrawn_at` y conserva `terminated` (FD-U6-21), y declara
        origen, `blocked_code`, terminación y retirada con su hora, estado del último modo final
        y perfil con la marca de misma familia (FD-U7-03).

        La hora de la terminación es `terminated_at`, derivada del historial de estados de la
        sesión (P-T16-10), y el estado del último modo final sale de `runs` (`mode == "final"`).
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
