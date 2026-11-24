"""Interfaces en proceso C10, C11, C12, C23 y C24 frente a mypy estricto (paso 17, T16).

Los dobles se escriben en `tmp_path` y se pasan por `mypy.api.run` con `--strict`, igual que en
`test_anonymizing_provider.py`. Nunca se escribe en `src/`. Un doble mínimo de cada interfaz pasa;
uno con la firma cambiada (sin `for_update`, sin `actor`, `count_session` que devuelve `int`...)
no pasa. Los controles negativos parten del mismo texto del doble correcto, para que el único
cambio sea el de la firma.
"""

import ast
import importlib.resources
import re
import typing
from pathlib import Path

import pytest
from helpers import importar_o_fallar, load_contract
from mypy import api as mypy_api

IMPORTACIONES = """from collections.abc import Mapping
from datetime import datetime
from uuid import UUID

from veridicus_contracts.access_log import AccessLog, ResourceType
from veridicus_contracts.analyzer.v1 import Hallazgo
from veridicus_contracts.human_review import (
    Actor,
    DecisionState,
    ReviewCommands,
    SuggestionProposer,
)
from veridicus_contracts.identity import Authenticator, Principal, Role, UserAdmin
from veridicus_contracts.report_ports import (
    PendingSessions,
    ReviewRounds,
    RoundView,
    SessionLifecycle,
    SessionReader,
    SessionSnapshot,
    SuggestionWithDecision,
)
from veridicus_contracts.retention import Purgeable, PurgeReceipt
from veridicus_contracts.unit_of_work import UnitOfWork
"""

# Un doble mínimo por interfaz: nombre del protocolo -> texto de la clase `Doble`.
DOBLES: dict[str, str] = {
    "SuggestionProposer": """
class Doble:
    def propose(
        self, uow: UnitOfWork, session_id: UUID, run_id: UUID, hallazgos: list[Hallazgo]
    ) -> list[UUID]:
        raise NotImplementedError
""",
    "ReviewCommands": """
class Doble:
    def record_observations_view(
        self, uow: UnitOfWork, suggestion_id: UUID, actor: Actor
    ) -> None:
        raise NotImplementedError

    def decide(
        self,
        uow: UnitOfWork,
        suggestion_id: UUID,
        state: DecisionState,
        note: str | None,
        reformulation: str | None,
        actor: Actor,
    ) -> UUID:
        raise NotImplementedError
""",
    "SessionReader": """
class Doble:
    def snapshot(self, uow: UnitOfWork, session_id: UUID) -> SessionSnapshot:
        raise NotImplementedError
""",
    "ReviewRounds": """
class Doble:
    def open_round(
        self, uow: UnitOfWork, session_id: UUID, for_update: bool = False
    ) -> RoundView | None:
        raise NotImplementedError

    def pending_count(self, uow: UnitOfWork, round_id: UUID) -> int:
        raise NotImplementedError

    def pending_counts(self, uow: UnitOfWork, session_ids: list[UUID]) -> dict[UUID, int]:
        raise NotImplementedError

    def decisions(self, uow: UnitOfWork, round_id: UUID) -> list[SuggestionWithDecision]:
        raise NotImplementedError

    def lock_round(
        self, uow: UnitOfWork, round_id: UUID, report_version_id: UUID, actor: Actor
    ) -> None:
        raise NotImplementedError

    def open_correction_round(self, uow: UnitOfWork, session_id: UUID, actor: Actor) -> UUID:
        raise NotImplementedError

    def discard_correction_round(self, uow: UnitOfWork, session_id: UUID, actor: Actor) -> None:
        raise NotImplementedError
""",
    "SessionLifecycle": """
class Doble:
    def finalize(self, uow: UnitOfWork, session_id: UUID, actor: Actor) -> None:
        raise NotImplementedError

    def mark_consolidated(
        self,
        uow: UnitOfWork,
        session_id: UUID,
        report_version_id: UUID,
        actor: Actor,
        finalize_first: bool = False,
    ) -> None:
        raise NotImplementedError
""",
    "PendingSessions": """
class Doble:
    def count_pending(self, uow: UnitOfWork, owner_user_id: UUID) -> int:
        raise NotImplementedError
""",
    "Authenticator": """
class Doble:
    def login(self, uow: UnitOfWork, username: str, password: str) -> tuple[Principal, str]:
        raise NotImplementedError

    def resolve(self, uow: UnitOfWork, session_token: str) -> Principal:
        raise NotImplementedError

    def csrf_token(self, session_token: str) -> str:
        raise NotImplementedError

    def logout(self, uow: UnitOfWork, session_token: str) -> None:
        raise NotImplementedError
""",
    "UserAdmin": """
class Doble:
    def create(
        self, uow: UnitOfWork, username: str, password: str, role: Role, actor: Principal
    ) -> UUID:
        raise NotImplementedError

    def update(
        self,
        uow: UnitOfWork,
        user_id: UUID,
        active: bool | None,
        role: Role | None,
        actor: Principal,
    ) -> None:
        raise NotImplementedError
""",
    "AccessLog": """
class Doble:
    def record(
        self,
        uow: UnitOfWork,
        user_id: UUID,
        resource_type: ResourceType,
        resource_id: UUID,
        export_sha256: str | None = None,
    ) -> None:
        raise NotImplementedError
""",
    "Purgeable": """
class Doble:
    def purge_session(self, uow: UnitOfWork, session_id: UUID) -> PurgeReceipt:
        raise NotImplementedError

    def count_session(self, uow: UnitOfWork, session_id: UUID) -> Mapping[str, int]:
        raise NotImplementedError
""",
}

# (id, protocolo, texto del doble correcto, texto que lo deja con otra firma)
NEGATIVOS = [
    pytest.param(
        "ReviewRounds",
        "self, uow: UnitOfWork, session_id: UUID, for_update: bool = False",
        "self, uow: UnitOfWork, session_id: UUID",
        id="open_round_sin_for_update",
    ),
    pytest.param(
        "ReviewCommands",
        "        reformulation: str | None,\n        actor: Actor,\n",
        "        reformulation: str | None,\n",
        id="decide_sin_actor",
    ),
    pytest.param(
        "Purgeable",
        ") -> Mapping[str, int]:",
        ") -> int:",
        id="count_session_devuelve_int",
    ),
    pytest.param(
        "ReviewRounds",
        "self, uow: UnitOfWork, round_id: UUID, report_version_id: UUID, actor: Actor",
        "self, uow: UnitOfWork, round_id: UUID, report_version_id: UUID",
        id="lock_round_sin_actor",
    ),
    pytest.param(
        "SessionLifecycle",
        "        actor: Actor,\n        finalize_first: bool = False,\n",
        "        actor: Actor,\n",
        id="mark_consolidated_sin_finalize_first",
    ),
    pytest.param(
        "AccessLog",
        "        resource_id: UUID,\n        export_sha256: str | None = None,\n",
        "        resource_id: UUID,\n",
        id="record_sin_export_sha256",
    ),
    pytest.param(
        "Authenticator",
        "password: str) -> tuple[Principal, str]:",
        "password: str) -> Principal:",
        id="login_solo_devuelve_el_principal",
    ),
]

MODULOS = {
    "human_review": ("C10", "2.0.0"),
    "report_ports": ("C11", "2.0.0"),
    "identity": ("C12", "2.0.0"),
    "access_log": ("C23", "1.0.0"),
    "retention": ("C24", "1.1.0"),
}


@pytest.fixture(scope="module")
def cache_de_mypy(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return tmp_path_factory.mktemp("cache-mypy")


def _mypy(tmp_path: Path, cache: Path, contracts_root: Path, fuente: str) -> tuple[str, int]:
    """Pasa `fuente` por mypy estricto con `src/` en la ruta de módulos; devuelve (salida, código)."""
    for nombre in (*MODULOS, "unit_of_work"):
        importar_o_fallar(f"veridicus_contracts.{nombre}", "T16")
    configuracion = tmp_path / "mypy.ini"
    configuracion.write_text(
        f"[mypy]\nmypy_path = {contracts_root / 'src'}\nexplicit_package_bases = true\n",
        encoding="utf-8",
    )
    doble = tmp_path / "doble.py"
    doble.write_text(fuente, encoding="utf-8")
    salida, errores, codigo = mypy_api.run(
        ["--strict", "--config-file", str(configuracion), "--cache-dir", str(cache), str(doble)]
    )
    return salida + errores, codigo


def _uso(protocolo: str) -> str:
    return (
        f"\n\ndef usar_{protocolo.lower()}(valor: {protocolo}) -> None:\n    del valor\n\n\n"
        f"usar_{protocolo.lower()}(Doble())\n"
    )


def test_un_doble_minimo_de_cada_interfaz_pasa_mypy_estricto(
    tmp_path: Path, cache_de_mypy: Path, contracts_root: Path
) -> None:
    """Paso 17: cada doble cumple su `Protocol` sin heredar de él, con la firma de contract-summary."""
    fuente = IMPORTACIONES
    for indice, (protocolo, clase) in enumerate(DOBLES.items()):
        renombrada = clase.replace("class Doble:", f"class Doble{indice}:")
        fuente += renombrada + _uso(protocolo).replace("Doble()", f"Doble{indice}()")
    salida, codigo = _mypy(tmp_path, cache_de_mypy, contracts_root, fuente)
    assert codigo == 0, salida
    assert "Success: no issues found" in salida


@pytest.mark.parametrize(("protocolo", "correcto", "cambiado"), NEGATIVOS)
def test_un_doble_con_otra_firma_no_pasa_mypy_estricto(
    tmp_path: Path,
    cache_de_mypy: Path,
    contracts_root: Path,
    protocolo: str,
    correcto: str,
    cambiado: str,
) -> None:
    """Control negativo: el mismo doble con una sola firma distinta deja de ser el `Protocol`."""
    clase = DOBLES[protocolo]
    assert correcto in clase, "el control negativo no encuentra el texto que debe cambiar"
    fuente = IMPORTACIONES + clase.replace(correcto, cambiado) + _uso(protocolo)
    salida, codigo = _mypy(tmp_path, cache_de_mypy, contracts_root, fuente)
    assert codigo == 1, salida
    assert '"Doble"' in salida
    assert f'expected "{protocolo}"' in salida
    assert "[arg-type]" in salida


def test_el_rol_de_identity_es_el_enum_de_c1() -> None:
    """C12: `Role` repite el enum `Role` de `api/console.v2.yaml`, valor por valor."""
    identidad = importar_o_fallar("veridicus_contracts.identity", "T16")
    c1 = load_contract("api/console.v2.yaml")["components"]["schemas"]["Role"]["enum"]
    assert set(c1) == {"analista", "admin", "investigador"}
    assert sorted(typing.get_args(identidad.Role)) == sorted(c1)
    assert len(typing.get_args(identidad.Role)) == len(c1)


@pytest.mark.parametrize("modulo", sorted(MODULOS))
def test_la_version_del_encabezado_es_la_del_contrato(modulo: str) -> None:
    """Cada módulo declara en su encabezado el contrato y su versión (C10 v2.0.0 ... C24 v1.1.0)."""
    importado = importar_o_fallar(f"veridicus_contracts.{modulo}", "T16")
    contrato, version = MODULOS[modulo]
    docstring = ast.get_docstring(ast.parse(Path(str(importado.__file__)).read_text("utf-8")))
    assert docstring is not None, f"{modulo}: sin docstring de módulo"
    encabezado = docstring.splitlines()[0]
    assert re.search(rf"\b{contrato} v{re.escape(version)}\b", encabezado), encabezado


def test_hallazgo_tiene_las_claves_del_esquema_de_c6() -> None:
    """FD-U1-04, CD-05: `Hallazgo` y `Cita` repiten, con sus nombres en español, el esquema de C6."""
    modelo = importar_o_fallar("veridicus_contracts.analyzer.v1", "T16")
    defs = load_contract("analyzer/v1/salida.schema.json")["$defs"]
    for nombre, definicion in (("Hallazgo", defs["hallazgo"]), ("Cita", defs["cita"])):
        clase = getattr(modelo, nombre)
        assert set(clase.__annotations__) == set(definicion["properties"]), nombre
        assert set(clase.__required_keys__) == set(definicion["required"]), nombre
        assert set(clase.__optional_keys__) == set(definicion["properties"]) - set(
            definicion["required"]
        ), nombre


def test_el_modulo_analyzer_v1_convive_con_los_datos_de_analyzer_v1() -> None:
    """K-12: `analyzer/v1.py` y el directorio de datos `analyzer/v1/` no se tapan entre sí."""
    modelo = importar_o_fallar("veridicus_contracts.analyzer.v1", "T16")
    assert str(modelo.__file__).endswith("v1.py")
    datos = importlib.resources.files("veridicus_contracts") / "analyzer" / "v1"
    assert (datos / "salida.schema.json").is_file()


def test_las_docstrings_conservan_las_revisiones_y_las_guardias() -> None:
    """Las docstrings de la revisión 4 y de AUTONOMIA-03/05 viajan con el contrato."""
    revision = importar_o_fallar("veridicus_contracts.human_review", "T16")
    puertos = importar_o_fallar("veridicus_contracts.report_ports", "T16")
    bitacora = importar_o_fallar("veridicus_contracts.access_log", "T16")
    propuesta = revision.SuggestionProposer.propose.__doc__
    assert "campos obligatorios (AUTONOMIA-05)" in propuesta
    assert "review.round_locked" in propuesta
    decidir = revision.ReviewCommands.decide.__doc__
    for codigo in ("suggestion.not_found", "limits.exceeded", "review.observations_not_viewed"):
        assert codigo in decidir, codigo
    assert "FD-U5-03" in puertos.ReviewRounds.open_round.__doc__
    assert "FD-U5-04" in puertos.ReviewRounds.discard_correction_round.__doc__
    assert "FD-U5-05" in puertos.ReviewRounds.decisions.__doc__
    assert "sin reintentos" in bitacora.AccessLog.record.__doc__
