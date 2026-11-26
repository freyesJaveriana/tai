"""La API de la biblioteca (C17, CG-U11-03, R-15): `analyze` e `IncoherenceAnalyzer`."""

from typing import Protocol

import pytest
from veridicus_errors import CancelledError, ImportInvalidTranscriptError
from veridicus_execution_profiles.loader import EffectiveConfig
from veridicus_model_gateway.port import ModelGateway

from tests.support import ScriptedGateway, finding, make_config, make_entrada
from veridicus_incoherence_analyzer import api
from veridicus_incoherence_analyzer.api import (
    CancelCheck,
    Entrada,
    IncoherenceAnalyzer,
    Salida,
    analyze,
)


class AnalyzerProtocol(Protocol):
    """El `Protocol` de C17 (`contract-summary.md`), copiado tal cual para que mypy compruebe que
    `IncoherenceAnalyzer` lo cumple."""

    def analyze(
        self,
        entrada: Entrada,
        config: EffectiveConfig,
        gateway: ModelGateway,
        cancelled: CancelCheck | None = None,
    ) -> Salida: ...


def test_the_class_meets_the_protocol_and_delegates_in_the_function() -> None:
    analyzer: AnalyzerProtocol = IncoherenceAnalyzer()
    config = make_config()

    by_class = analyzer.analyze(make_entrada(), config, ScriptedGateway(findings=[finding()]))
    by_function = analyze(make_entrada(), config, ScriptedGateway(findings=[finding()]))

    assert by_class["estado"] == "ok"
    assert len(by_class["hallazgos"]) == 1
    for salida in (by_class, by_function):
        salida.pop("fecha")
        for llamada in salida["registro"]["llamadas"]:
            llamada.pop("fecha")
    assert by_class == by_function


def test_the_class_passes_the_cancel_check_and_the_rejections_through() -> None:
    analyzer = IncoherenceAnalyzer()
    config = make_config()

    with pytest.raises(CancelledError):
        analyzer.analyze(make_entrada(), config, ScriptedGateway(), cancelled=lambda: True)
    with pytest.raises(ImportInvalidTranscriptError):
        analyzer.analyze({}, config, ScriptedGateway())


def test_the_public_names_of_the_module() -> None:
    assert set(api.__all__) == {
        "CancelCheck",
        "Entrada",
        "IncoherenceAnalyzer",
        "Salida",
        "analyze",
    }
