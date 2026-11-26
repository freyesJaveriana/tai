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

# (protocolo, texto del doble correcto, texto que lo deja con otra firma, miembro en conflicto)
NEGATIVOS = [
    pytest.param(
        "ReviewRounds",
        "self, uow: UnitOfWork, session_id: UUID, for_update: bool = False",
        "self, uow: UnitOfWork, session_id: UUID",
        "open_round",
        id="open_round_sin_for_update",
    ),
    pytest.param(
        "ReviewCommands",
        "        reformulation: str | None,\n        actor: Actor,\n",
        "        reformulation: str | None,\n",
        "decide",
        id="decide_sin_actor",
    ),
    pytest.param(
        "Purgeable",
        ") -> Mapping[str, int]:",
        ") -> int:",
        "count_session",
        id="count_session_devuelve_int",
    ),
    pytest.param(
        "ReviewRounds",
        "self, uow: UnitOfWork, round_id: UUID, report_version_id: UUID, actor: Actor",
        "self, uow: UnitOfWork, round_id: UUID, report_version_id: UUID",
        "lock_round",
        id="lock_round_sin_actor",
    ),
    pytest.param(
        "SessionLifecycle",
        "        actor: Actor,\n        finalize_first: bool = False,\n",
        "        actor: Actor,\n",
        "mark_consolidated",
        id="mark_consolidated_sin_finalize_first",
    ),
    pytest.param(
        "AccessLog",
        "        resource_id: UUID,\n        export_sha256: str | None = None,\n",
        "        resource_id: UUID,\n",
        "record",
        id="record_sin_export_sha256",
    ),
    pytest.param(
        "Authenticator",
        "password: str) -> tuple[Principal, str]:",
        "password: str) -> Principal:",
        "login",
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


def _notas_de_conflicto(salida: str) -> str:
    """Las líneas `note:` de mypy, donde nombra los miembros que no coinciden con el `Protocol`."""
    return "\n".join(linea for linea in salida.splitlines() if ": note:" in linea)


@pytest.mark.parametrize(("protocolo", "correcto", "cambiado", "miembro"), NEGATIVOS)
def test_un_doble_con_otra_firma_no_pasa_mypy_estricto(
    tmp_path: Path,
    cache_de_mypy: Path,
    contracts_root: Path,
    protocolo: str,
    correcto: str,
    cambiado: str,
    miembro: str,
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
    assert re.search(rf"\b{miembro}\b", _notas_de_conflicto(salida)), (miembro, salida)


IMPORTACIONES_AUXILIARES = """from datetime import datetime
from uuid import UUID

from veridicus_contracts.report_ports import (
    BlockedCode,
    EffectiveState,
    FoldState,
    ModelCallRole,
    ModelCallView,
    RoundKind,
    RoundStatus,
    RoundView,
    RunMode,
    RunStatus,
    RunView,
    SessionOrigin,
    SessionSnapshot,
    SessionStatus,
    Speaker,
    SuggestionWithDecision,
    TurnView,
)
from veridicus_contracts.analyzer.v1 import Hallazgo
"""

# Un doble por tipo auxiliar, con los nombres, tipos y valores cerrados de las entidades aprobadas
# (P-T16-8). Cada uno trae el control negativo: (texto correcto, texto cambiado, miembro).
DOBLE_SNAPSHOT = """
class Doble:
    session_id: UUID
    owner_user_id: UUID
    profile_name: str
    config_sha256: str
    same_family_declared: bool
    status: SessionStatus
    origin: SessionOrigin
    finalized_at: datetime | None
    terminated_at: datetime | None
    consent_withdrawn_at: datetime | None
    blocked_code: BlockedCode | None
    turns: list[TurnView]
    runs: list[RunView]
    pending_runs: int
"""

AUXILIARES = [
    pytest.param(
        "SessionSnapshot",
        DOBLE_SNAPSHOT,
        "    status: SessionStatus\n",
        "    state: SessionStatus\n",
        "status",
        id="SessionSnapshot_status_se_llama_state",
    ),
    pytest.param(
        "SessionSnapshot",
        DOBLE_SNAPSHOT,
        "    terminated_at: datetime | None\n",
        "",
        "terminated_at",
        id="SessionSnapshot_sin_terminated_at",
    ),
    pytest.param(
        "SessionSnapshot",
        DOBLE_SNAPSHOT,
        "    origin: SessionOrigin\n",
        "    origin: str\n",
        "origin",
        id="SessionSnapshot_origin_es_str",
    ),
    pytest.param(
        "TurnView",
        """
class Doble:
    n: int
    speaker: Speaker
    page: int | None
    fold_state: FoldState
""",
        "    fold_state: FoldState\n",
        "    fold_state: str\n",
        "fold_state",
        id="TurnView_fold_state_es_str",
    ),
    pytest.param(
        "RunView",
        """
class Doble:
    run_id: UUID
    mode: RunMode
    from_turn: int
    to_turn: int
    status: RunStatus
    attempt: int
    fragmented: bool | None
    covered_by_final: bool
    model_calls: list[ModelCallView]
""",
        "    covered_by_final: bool\n",
        "",
        "covered_by_final",
        id="RunView_sin_covered_by_final",
    ),
    pytest.param(
        "ModelCallView",
        """
class Doble:
    role: ModelCallRole
    provider: str
    model: str
    version: str | None
    effort_or_quantization: str | None
    engine: str | None
    seed: int | None
    tokens_in: int
    tokens_out: int
    used_fallback: bool
    external: bool
    anonymized: bool
    at: datetime
""",
        "    role: ModelCallRole\n",
        "    role: str\n",
        "role",
        id="ModelCallView_role_es_str",
    ),
    pytest.param(
        "RoundView",
        """
class Doble:
    round_id: UUID
    session_id: UUID
    number: int
    kind: RoundKind
    status: RoundStatus
    based_on_round_id: UUID | None
""",
        "    status: RoundStatus\n",
        "    state: RoundStatus\n",
        "status",
        id="RoundView_status_se_llama_state",
    ),
    pytest.param(
        "SuggestionWithDecision",
        """
class Doble:
    suggestion_id: UUID
    hallazgo: Hallazgo
    state: EffectiveState
    note: str | None
    reformulation: str | None
    decided_by: UUID | None
    decided_at: datetime | None
""",
        "    decided_by: UUID | None\n    decided_at: datetime | None\n",
        "    actor_user_id: UUID | None\n    at: datetime | None\n",
        "decided_by",
        id="SuggestionWithDecision_usa_actor_user_id_y_at_de_la_tabla",
    ),
]


@pytest.mark.parametrize(("protocolo", "doble", "correcto", "cambiado", "miembro"), AUXILIARES)
def test_cada_tipo_auxiliar_exige_los_campos_y_valores_de_su_entidad(
    tmp_path: Path,
    cache_de_mypy: Path,
    contracts_root: Path,
    protocolo: str,
    doble: str,
    correcto: str,
    cambiado: str,
    miembro: str,
) -> None:
    """P-T16-8: el doble con los campos de la entidad pasa; con otro nombre o con `str` en lugar
    del `Literal` cerrado, no, y mypy nombra el campo."""
    clase = doble
    assert correcto in clase, "el control negativo no encuentra el texto que debe cambiar"
    encabezado = IMPORTACIONES_AUXILIARES
    fuente_buena = encabezado + clase + _uso(protocolo)
    bueno, codigo = _mypy(tmp_path, cache_de_mypy, contracts_root, fuente_buena)
    assert codigo == 0, bueno
    malo_dir = tmp_path / "malo"
    malo_dir.mkdir()
    fuente = encabezado + clase.replace(correcto, cambiado) + _uso(protocolo)
    salida, codigo = _mypy(malo_dir, cache_de_mypy, contracts_root, fuente)
    assert codigo == 1, salida
    assert f'expected "{protocolo}"' in salida
    assert "[arg-type]" in salida
    assert re.search(rf"\b{miembro}\b", _notas_de_conflicto(salida)), (miembro, salida)


def test_los_valores_cerrados_de_c11_son_los_de_las_entidades_aprobadas() -> None:
    """P-T16-8: los `Literal` repiten los `allowed` de entities.md de U4 y de U5."""
    puertos = importar_o_fallar("veridicus_contracts.report_ports", "T16")
    esperados = {
        # text-flow/functional-design/entities.md
        "SessionStatus": {
            "open",
            "paused",
            "suspended",
            "finalized",
            "terminated",
            "blocked",
            "consolidated",
        },
        "SessionOrigin": {"guiada", "corpus", "sintetico"},
        "BlockedCode": {"anonymizer.incident"},
        "Speaker": {"ENT", "TEST"},
        "FoldState": {"visible", "plegado"},
        "RunMode": {"incremental", "final"},
        "RunStatus": {"queued", "processing", "done", "error", "cancelled"},
        "ModelCallRole": {"juez", "verificador", "verificador_permutado"},
        # human-review/functional-design/entities.md
        "RoundKind": {"initial", "correction"},
        "RoundStatus": {"open", "locked", "discarded"},
        "EffectiveState": {"pending", "accepted", "edited", "dismissed"},
    }
    for nombre, valores in esperados.items():
        assert set(typing.get_args(getattr(puertos, nombre))) == valores, nombre
        assert len(typing.get_args(getattr(puertos, nombre))) == len(valores), nombre


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


def test_los_literal_de_hallazgo_son_los_enum_del_esquema_de_c6() -> None:
    """CD-05: `HallazgoTipo` y `CitaAviso` repiten, valor por valor, los enum de `salida.schema.json`
    y son los que `Hallazgo` y `Cita` usan."""
    modelo = importar_o_fallar("veridicus_contracts.analyzer.v1", "T16")
    defs = load_contract("analyzer/v1/salida.schema.json")["$defs"]
    tipos = defs["hallazgo"]["properties"]["tipo"]["enum"]
    avisos = defs["cita"]["properties"]["avisos"]["items"]["enum"]
    assert sorted(typing.get_args(modelo.HallazgoTipo)) == sorted(tipos)
    assert sorted(typing.get_args(modelo.CitaAviso)) == sorted(avisos)
    assert len(typing.get_args(modelo.HallazgoTipo)) == len(tipos)
    assert len(typing.get_args(modelo.CitaAviso)) == len(avisos)
    assert typing.get_type_hints(modelo.Hallazgo)["tipo"] == modelo.HallazgoTipo
    assert typing.get_type_hints(modelo.Cita)["avisos"] == list[modelo.CitaAviso]


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
