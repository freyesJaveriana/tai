"""C12 v2.0.0: IdentityAccess hacia ConsoleApi (en proceso).

Se mantiene la forma; cambia el conjunto de roles: entra `investigador` (FR1.2). Revisión 4:
`UserChange` lleva `[user_id, change, old_value, new_value, actor_kind, actor_user_id, actor_system,
at]` y el alta del primer admin lleva `actor_kind: system` y `actor_system: create-admin`
(FD-U3-06). Importaciones: `veridicus_contracts.identity` (FD-U1-04). Solo firmas: la
implementación es de U3.
"""

from typing import Literal, Protocol
from uuid import UUID

from veridicus_contracts.unit_of_work import UnitOfWork

# Igual al enum `Role` de `api/console.v2.yaml` (C1); una prueba lo comprueba.
Role = Literal["analista", "admin", "investigador"]


class Principal(Protocol):
    @property
    def user_id(self) -> UUID: ...

    @property
    def username(self) -> str: ...

    @property
    def role(self) -> Role: ...


class Authenticator(Protocol):
    def login(self, uow: UnitOfWork, username: str, password: str) -> tuple[Principal, str]:
        """Devuelve el principal y el identificador de sesión para la cookie.

        Mismo error (auth.invalid_credentials) para usuario inexistente y contraseña errónea.
        """
        ...

    def resolve(self, uow: UnitOfWork, session_token: str) -> Principal:
        """auth.unauthenticated si la sesión no existe, venció o el usuario está desactivado."""
        ...

    def csrf_token(self, session_token: str) -> str: ...

    def logout(self, uow: UnitOfWork, session_token: str) -> None: ...


class UserAdmin(Protocol):
    def create(
        self, uow: UnitOfWork, username: str, password: str, role: Role, actor: Principal
    ) -> UUID: ...

    def update(
        self,
        uow: UnitOfWork,
        user_id: UUID,
        active: bool | None,
        role: Role | None,
        actor: Principal,
    ) -> None:
        """Desactivar revoca todas las sesiones del usuario. Deja fila en UserChange."""
        ...
