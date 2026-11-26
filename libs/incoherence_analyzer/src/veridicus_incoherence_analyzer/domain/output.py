"""Armado de la salida C6 (BR8).

Funciones puras que arman los diccionarios de C6; la validación contra el esquema (BR8.1) y la
sustitución por `salida_invalida` son de `analyze`, que es quien conoce el registro de contratos.

Costura de las pruebas (BR8.1): `assemble_findings` arma cada hallazgo llamando a
`build_finding(...)` por el nombre global de este módulo, para que una prueba lo sustituya con
`monkeypatch` por un armador que deje fuera `observaciones` («un hallazgo armado a propósito sin
observaciones») y compruebe que la salida sustituta es `salida_invalida`, conserva
`registro.llamadas` (BR7.1) y valida contra C6.
"""

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any, Final

from veridicus_contracts.model_calls import ModelCall
from veridicus_execution_profiles.loader import EffectiveConfig

from veridicus_incoherence_analyzer.domain.filter import Discard, Survivor
from veridicus_incoherence_analyzer.domain.ids import format_id, positions_of

# La tabla fija de BR9.6 (`model_calls/role-translation.v1.yaml`): del papel de una llamada al papel
# de `registro.llamadas`. Una prueba la compara con el archivo que publica U1.
ROLE_NAMES: Final[Mapping[str, str]] = {
    "judge": "juez",
    "verifier": "verificador",
    "verifier_permuted": "verificador_permutado",
}
CONTRACT_VERSION: Final = "1.0.0"
ANALYZER_NAME: Final = "incoherencias"


def _timestamp(moment: datetime) -> str:
    """Fecha en UTC con la forma `AAAA-MM-DDThh:mm:ssZ` que usan C6 y C13."""
    return moment.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _quote(quote: Mapping[str, Any], turns: Mapping[int, Mapping[str, Any]]) -> dict[str, Any]:
    """La cita con la página y los avisos que pone el núcleo a partir del turno (BR5.7)."""
    number = int(str(quote["turno"])[1:])
    turn = turns[number]
    built: dict[str, Any] = {"cita": quote["cita"], "turno": f"T{number}"}
    if "pagina" in turn:
        built["pagina"] = turn["pagina"]
    notices = []
    if turn.get("hablante") == "ENT":
        notices.append("turno_entrevistador")
    if turn.get("estado") == "plegado":
        notices.append("turno_plegado")
    if notices:
        built["avisos"] = notices
    return built


def build_finding(
    finding_id: str, candidate: Mapping[str, Any], turns: Mapping[int, Mapping[str, Any]]
) -> dict[str, Any]:
    """El `hallazgo` de C6 de un candidato que sobrevivió: `id`, los campos del juez y, en cada
    cita, `pagina` y `avisos` tomados de su turno (BR5.7). `turns` va por número `n`."""
    return {
        "id": finding_id,
        "hecho": candidate["hecho"],
        "tipo": candidate["tipo"],
        "cita_a": _quote(candidate["cita_a"], turns),
        "cita_b": _quote(candidate["cita_b"], turns),
        "observaciones": candidate["observaciones"],
    }


def assemble_findings(
    interview: str, survivors: Sequence[Survivor], turns: Mapping[int, Mapping[str, Any]]
) -> list[dict[str, Any]]:
    """Ordena los sobrevivientes con la clave de BR8.2 y arma cada hallazgo con su `id`."""
    positions = positions_of(turns)
    ordered = sorted(survivors, key=lambda survivor: survivor.sort_key(positions))
    return [
        build_finding(format_id(interview, ordinal), survivor.candidate, turns)
        for ordinal, survivor in enumerate(ordered, start=1)
    ]


def build_call(call: ModelCall) -> dict[str, Any]:
    """Una fila de `registro.llamadas`; omite los opcionales que valen `None` (C6 es cerrado)."""
    record: dict[str, Any] = {
        "papel": ROLE_NAMES[call.role],
        "proveedor": call.provider,
        "modelo": call.model,
    }
    optional = (
        ("version", call.version),
        ("esfuerzo_o_cuantizacion", call.effort_or_quantization),
        ("motor", call.engine),
        ("semilla", call.seed),
    )
    record.update({name: value for name, value in optional if value is not None})
    record.update(
        {
            "tokens_entrada": call.input_tokens,
            "tokens_salida": call.output_tokens,
            "proveedor_alterno": call.fallback_provider,
            "anonimizado": call.anonymized,
            "fecha": _timestamp(call.at),
        }
    )
    return record


def _discard(discard: Discard) -> dict[str, str]:
    record: dict[str, str] = {"motivo": discard.reason}
    if discard.turno_a is not None:
        record["turno_a"] = discard.turno_a
    if discard.turno_b is not None:
        record["turno_b"] = discard.turno_b
    return record


def build_output(
    config: EffectiveConfig,
    *,
    interview: str,
    date: datetime,
    findings: Sequence[Mapping[str, Any]],
    discards: Sequence[Discard],
    calls: Sequence[ModelCall],
    error_code: str | None = None,
) -> dict[str, Any]:
    """La salida C6. Con `error_code` es una salida en error: `hallazgos` y `descartes` vacíos, sin
    `observaciones_conductor` y con el registro de las llamadas que se alcanzaron a hacer (BR7.1).

    `version`, `perfil` y `config_sha256` salen de la configuración, y solo `fecha` y las fechas de
    las llamadas vienen del reloj (BR8.7). `prompt_sha256` es la huella de los bytes del *prompt*
    leídos en la corrida (BR3.1): `analyze` la sobrescribe con ella, y aquí sale de la configuración
    solo hasta entonces. B11a declara `fragmentado: false` (BR8.5) y no estima costo (BR8.4 se
    difiere).
    """
    failed = error_code is not None
    output: dict[str, Any] = {
        "contrato": CONTRACT_VERSION,
        "analizador": ANALYZER_NAME,
        "version": config.analyzer_version,
        "entrevista": interview,
        "prompt_sha256": config.prompt_sha256,
        "perfil": config.profile_name,
        "config_sha256": config.config_sha256,
        "fecha": _timestamp(date),
        "estado": "error" if failed else "ok",
        "hallazgos": [] if failed else [dict(finding) for finding in findings],
        "registro": {
            "llamadas": [build_call(call) for call in calls],
            "descartes": [] if failed else [_discard(discard) for discard in discards],
            "fragmentado": {"activo": False},
            "tokens_entrada": sum(call.input_tokens for call in calls),
            "tokens_salida": sum(call.output_tokens for call in calls),
        },
    }
    if failed:
        output["error"] = {"codigo": error_code}
    return output
