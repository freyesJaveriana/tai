"""C10 v2.0.0: HumanReview hacia InterviewSession y ConsoleApi (en proceso).

Cambia el candidato (el hallazgo de C6 en lugar de la alerta) y el despliegue de la CoT pasa a
«observaciones desplegadas». Revisión 4: `decide` suma `suggestion.not_found` y `limits.exceeded`
(FD-U5-01). Importaciones: `veridicus_contracts.human_review` y `veridicus_contracts.analyzer.v1`
(FD-U1-04). Solo firmas: las implementaciones son de U5 y U4.
"""

from datetime import datetime
from typing import Literal, Protocol
from uuid import UUID

from veridicus_contracts.analyzer.v1 import Hallazgo
from veridicus_contracts.unit_of_work import UnitOfWork

DecisionState = Literal["accepted", "edited", "dismissed"]


class Actor(Protocol):
    """Quién y cuándo. Solo lectura: una implementación congelada también lo cumple (P-T16-2)."""

    @property
    def user_id(self) -> UUID | None:
        """`None` es el sistema (al proponer)."""
        ...

    @property
    def at(self) -> datetime: ...


class SuggestionProposer(Protocol):
    """Puerto que convierte los hallazgos de una corrida en sugerencias de revisión."""

    def propose(
        self, uow: UnitOfWork, session_id: UUID, run_id: UUID, hallazgos: list[Hallazgo]
    ) -> list[UUID]:
        """Guarda cada hallazgo como sugerencia pendiente (C7).

        Une sin duplicar por el par no ordenado de (turno, cita normalizada en espacios) (FR4.9):
        un hallazgo ya decidido conserva su estado y su historial.
        Si la sesión no tiene ronda, abre la ronda 1 en la misma transacción (ADR-007).
        Rechaza un hallazgo sin sus campos obligatorios (AUTONOMIA-05).
        Con todas las rondas bloqueadas rechaza con review.round_locked.
        """
        ...


class ReviewCommands(Protocol):
    """Puerto de las acciones del analista sobre una sugerencia de revisión."""

    def record_observations_view(
        self, uow: UnitOfWork, suggestion_id: UUID, actor: Actor
    ) -> None: ...

    def decide(
        self,
        uow: UnitOfWork,
        suggestion_id: UUID,
        state: DecisionState,
        note: str | None,
        reformulation: str | None,
        actor: Actor,
    ) -> UUID:
        """El actor ya viene autorizado como dueño (ADR-009).

        Errores: review.observations_not_viewed, review.note_required,
        review.invalid_transition, review.round_locked, suggestion.not_found y
        limits.exceeded (revisión 4, FD-U5-01).
        """
        ...
