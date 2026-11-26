"""La corrida: juez, filtro, verificador y permutación (BR3.2, BR6.1 a BR6.4, BR7, BR8; F2 a F7).

`analyze` nunca lanza una excepción por un fallo del modelo o del anonimizador (AUTONOMIA-05): un error
tipado de `model_calls`, una respuesta que no valida contra su esquema, un puntero de marca alterada
que no cae en ningún candidato, el plazo agotado o un incidente de anonimización dejan una salida con
`estado: error`, su código, hallazgos y descartes vacíos y el registro de las llamadas que se
alcanzaron a hacer. Nunca sale un resultado parcial. Solo escapan:

- `InputRejected` (la tupla de `veridicus_errors`), antes de cualquier llamada (BR1);
- `CancelledError`, si `cancelled()` es verdadero antes de una llamada (BR7.2);
- un fallo del propio código (por ejemplo un `ModelCallError` sin código en BR7.1), que no se
  convierte en estado error: se propaga (CLI, código 5).

B11a corre una sola ventana con todos los turnos, sin fragmentar, porque el juez es externo (BR3.2). El
modo fragmentado, el incremental y el alterno se difieren a B11b.

Orden de la corrida (F1 a F7): validación previa, comprobación del *prompt* (K-88), juez, filtro,
verificador por sobreviviente (con la permutación después de la directa), armado de la salida y su
validación contra C6 (BR8.1).
"""

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from functools import cache
from typing import Any, NoReturn, cast

from jsonschema import Draft202012Validator
from veridicus_contracts.model_calls import (
    Destination,
    GenerateRequest,
    GenerateResult,
    ModelCall,
    ModelCallError,
)
from veridicus_errors import SystemInternalError
from veridicus_execution_profiles.loader import EffectiveConfig
from veridicus_model_gateway.port import ModelGateway

from veridicus_incoherence_analyzer.application import messages, preflight
from veridicus_incoherence_analyzer.application.contract import salida_validator
from veridicus_incoherence_analyzer.application.deadline import (
    CancelCheck,
    DeadlineExpired,
    RunClock,
)
from veridicus_incoherence_analyzer.domain import output
from veridicus_incoherence_analyzer.domain.filter import (
    Discard,
    FilterResult,
    InvalidJudgeResponse,
    Survivor,
    Window,
    filter_candidates,
)
from veridicus_incoherence_analyzer.domain.ids import positions_of
from veridicus_incoherence_analyzer.domain.run_state import (
    INCIDENT,
    Phase,
    RunState,
    error_code_for,
    is_incident,
)

Entrada = dict[str, Any]
Salida = dict[str, Any]

INVALID_OUTPUT = "salida_invalida"
DEADLINE = "tiempo_agotado"


class _Aborted(Exception):
    """Corta la corrida; el motivo ya está en el `RunState`."""


@cache
def _local_validator(role: messages.Role) -> Draft202012Validator:
    """El validador del esquema local estricto de la respuesta de un papel (BR3.4)."""
    return Draft202012Validator(messages.load_response_schema(role, "local"))


def _destination(raw: Mapping[str, Any]) -> Destination:
    """El destino de un papel tal como está en el perfil: nombres de claves, nunca sus valores."""
    return Destination(
        provider=raw["provider"],
        model=raw["model"],
        scope=raw["scope"],
        version=raw.get("version"),
        family=raw.get("family"),
        base_url=raw.get("base_url"),
        api_key_ref=raw.get("api_key_ref"),
        parameters=dict(raw.get("parameters", {})),
    )


def _destinations(config: EffectiveConfig) -> dict[str, Destination]:
    """El destino de cada papel de las llamadas; `verifier_permuted` usa el de su alias."""
    profile = config.profile
    roles = profile["roles"]
    alias = profile["role_aliases"]["verifier_permuted"]
    return {
        "judge": _destination(roles["judge"]),
        "verifier": _destination(roles["verifier"]),
        "verifier_permuted": _destination(roles[alias]),
    }


def _prompt_matches(config: EffectiveConfig) -> bool:
    """La huella de la configuración, la de los bytes leídos ahora y la referencia versionada
    coinciden (BR3.1, PD-13, K-88). Con los 64 ceros del valor por omisión, no."""
    return config.prompt_sha256 == messages.prompt_sha256() == messages.load_prompt_reference()


def _is_valid(salida: Mapping[str, Any]) -> bool:
    return salida_validator().is_valid(dict(salida))


class _Run:
    """Una corrida: el plazo, el estado, las llamadas hechas y los turnos de la entrada."""

    def __init__(
        self,
        config: EffectiveConfig,
        gateway: ModelGateway,
        clock: RunClock,
        turns: Mapping[int, Mapping[str, Any]],
    ) -> None:
        self.config = config
        self.state = RunState()
        self.calls: list[ModelCall] = []
        self._gateway = gateway
        self._clock = clock
        self._turns = turns
        self._destinations = _destinations(config)

    # --- el estado y el registro ---------------------------------------------------------------

    def _fail(self, code: str) -> None:
        self.state = self.state.fail(code)

    def _stop(self, code: str) -> NoReturn:
        self._fail(code)
        raise _Aborted

    def _account(self, destination: Destination, call: ModelCall | None) -> None:
        """Copia la llamada al registro (BR8.3) y, si salió sin anonimizar, es un incidente (BR7.6)."""
        if call is not None:
            self.calls.append(call)
        if is_incident(destination.scope, call):
            self._fail(INCIDENT)

    # --- una llamada ---------------------------------------------------------------------------

    def _generate(
        self, role: str, kind: messages.Role, payload: Mapping[str, Any]
    ) -> GenerateResult:
        """Una llamada con su plazo; devuelve el resultado con el contenido ya validado contra el
        esquema local (BR3.4).

        Cualquier fallo deja el estado en error y corta la corrida con `_Aborted`.
        """
        destination = self._destinations[role]
        try:
            timeout_s = self._clock.before_call()
        except DeadlineExpired:
            self._stop(DEADLINE)
        request = GenerateRequest(
            role=role,
            destination_slot="primary",
            profile_name=self.config.profile_name,
            profile_sha256=self.config.profile_sha256,
            destination=destination,
            messages=messages.build_messages(kind, payload),
            schema=messages.load_response_schema(kind, "wire"),
            timeout_s=timeout_s,
            seed=destination.parameters.get("seed"),
        )
        try:
            result: GenerateResult = self._gateway.generate(request)
        except ModelCallError as error:
            self._fail(error_code_for(error))
            self._account(destination, getattr(error, "call", None))
            raise _Aborted from None
        self._account(destination, result.call)
        try:
            self._clock.after_call()
        except DeadlineExpired:
            self._fail(DEADLINE)
        if self.state.failed:
            raise _Aborted
        if not _local_validator(kind).is_valid(result.content):
            self._stop(INVALID_OUTPUT)
        return result

    # --- las fases -----------------------------------------------------------------------------

    def judge(self) -> Window:
        """Una sola ventana con todos los turnos (BR3.2)."""
        ordered = [self._turns[number] for number in sorted(self._turns)]
        result = self._generate("judge", "judge", messages.judge_payload(ordered))
        return Window(
            candidates=result.content["hallazgos"], altered_markers=result.altered_markers
        )

    def screen(self, window: Window) -> FilterResult:
        """El filtro determinista, sin llamadas (BR5.2)."""
        self.state = self.state.advance(Phase.FILTERING)
        try:
            return filter_candidates([window], self._turns)
        except InvalidJudgeResponse:
            self._stop(INVALID_OUTPUT)

    def _confirms(self, role: str, survivor: Survivor, *, permuted: bool) -> bool:
        payload = messages.verifier_payload(survivor.candidate, permuted=permuted)
        return bool(self._generate(role, "verifier", payload).content["confirma"])

    def verify(self, survivors: Sequence[Survivor]) -> tuple[list[Survivor], list[Discard]]:
        """Una llamada `verifier` por sobreviviente, en el orden de BR6.1, y con la permutación
        activa una `verifier_permuted` después de la directa, aunque la directa diga que no."""
        self.state = self.state.advance(Phase.VERIFYING)
        positions = positions_of(self._turns)
        permutation: bool = self.config.profile["permutation"]
        confirmed: list[Survivor] = []
        discards: list[Discard] = []
        for survivor in sorted(survivors, key=lambda item: item.sort_key(positions)):
            direct = self._confirms("verifier", survivor, permuted=False)
            inverse = (
                self._confirms("verifier_permuted", survivor, permuted=True)
                if permutation
                else True
            )
            turn_a, turn_b = f"T{survivor.turn_a}", f"T{survivor.turn_b}"
            if not direct:
                discards.append(Discard("rechazado_verificador", turn_a, turn_b))
            elif not inverse:
                discards.append(Discard("rechazado_permutacion", turn_a, turn_b))
            else:
                confirmed.append(survivor)
        self.state = self.state.advance(Phase.FINALIZING)
        return confirmed, discards


def _failed(
    config: EffectiveConfig, interview: str, date: datetime, calls: Sequence[ModelCall], code: str
) -> Salida:
    return output.build_output(
        config,
        interview=interview,
        date=date,
        findings=[],
        discards=[],
        calls=calls,
        error_code=code,
    )


def _finish(
    run: _Run,
    interview: str,
    date: datetime,
    turns: Mapping[int, Mapping[str, Any]],
    confirmed: Sequence[Survivor],
    discards: Sequence[Discard],
) -> Salida:
    """Arma la salida y la valida contra C6 (BR8.1); si no valida, la sustituye por `salida_invalida`."""
    salida = output.build_output(
        run.config,
        interview=interview,
        date=date,
        findings=output.assemble_findings(interview, confirmed, turns),
        discards=discards,
        calls=run.calls,
    )
    if _is_valid(salida):
        return salida
    replacement = _failed(run.config, interview, date, run.calls, INVALID_OUTPUT)
    if not _is_valid(replacement):
        raise SystemInternalError("la salida en error no valida contra C6: defecto del analizador")
    return replacement


def run_analysis(
    entrada: Entrada,
    config: EffectiveConfig,
    gateway: ModelGateway,
    cancelled: CancelCheck | None = None,
) -> Salida:
    """La corrida completa de `analyze` (C17): ver el docstring del módulo."""
    preflight.check(entrada, config)
    transcription = entrada["transcripcion"]
    interview: str = transcription["entrevista"]
    turns = {turn["n"]: turn for turn in transcription["turnos"]}
    date = datetime.now(UTC)
    if not _prompt_matches(config):
        return _failed(config, interview, date, [], INVALID_OUTPUT)
    clock = RunClock(
        config.limits["model_call_timeout_s"], config.limits["run_deadline_final_s"], cancelled
    )
    run = _Run(config, gateway, clock, turns)
    try:
        window = run.judge()
        filtered = run.screen(window)
        confirmed, rejected = run.verify(filtered.survivors)
    except _Aborted:
        return _failed(config, interview, date, run.calls, cast(str, run.state.error_code))
    return _finish(run, interview, date, turns, confirmed, [*filtered.discards, *rejected])
