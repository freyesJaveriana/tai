"""`limits.load`: las cifras efectivas solo bajan (C25, BR11.1, §4.15, NFRD-U1-09; E33, E37).

`load` se prueba con un `environ` en memoria, nunca con `os.environ`.
"""

import builtins
import importlib.resources
import io
import os
import socket
from types import ModuleType
from typing import Any

import pytest
from helpers import CONTRACTS_ROOT, importar_o_fallar, load_contract


def _limits() -> ModuleType:
    return importar_o_fallar("veridicus_contracts.limits", "paso 12 (T10)")


def _rechaza(environ: dict[str, str], *fragmentos: str) -> None:
    limits = _limits()
    with pytest.raises(limits.LimitsConfigError) as caught:
        limits.load(environ)
    assert caught.value.code == "config.invalid_limit"
    for fragmento in fragmentos:
        assert fragmento in str(caught.value)


def test_sin_variables_devuelve_el_catalogo_empaquetado() -> None:
    efectivos = _limits().load({})
    catalogo = load_contract("limits.v1.yaml")["limits"]
    assert efectivos == {nombre: entrada["value"] for nombre, entrada in catalogo.items()}
    assert efectivos["turn_max_chars"] == 20000
    assert efectivos["anonymizer_masking_budget_ratio"] == 0.15
    assert efectivos["audio_base64_max_chars"] == 8_000_000


def test_el_catalogo_empaquetado_es_el_archivo_de_contracts() -> None:
    empaquetado = importlib.resources.files("veridicus_contracts") / "limits.v1.yaml"
    assert empaquetado.read_text(encoding="utf-8") == (CONTRACTS_ROOT / "limits.v1.yaml").read_text(
        encoding="utf-8"
    )


def test_e33_una_variable_que_sube_la_cifra_se_rechaza() -> None:
    _rechaza({"VERIDICUS_LIMIT_TURN_MAX_CHARS": "20001"}, "VERIDICUS_LIMIT_TURN_MAX_CHARS", "sube")


def test_bajar_o_igualar_una_cifra_se_acepta() -> None:
    limits = _limits()
    assert limits.load({"VERIDICUS_LIMIT_TURN_MAX_CHARS": "10000"})["turn_max_chars"] == 10000
    assert limits.load({"VERIDICUS_LIMIT_TURN_MAX_CHARS": "20000"})["turn_max_chars"] == 20000


def test_bajar_un_decimal_en_s_y_en_ratio() -> None:
    efectivos = _limits().load(
        {
            "VERIDICUS_LIMIT_ANONYMIZER_MASKING_BUDGET_RATIO": "0.1",
            "VERIDICUS_LIMIT_POLL_INTERVAL_S": "10.5",
            "VERIDICUS_LIMIT_POLL_INTERVAL_ACTIVE_S": "1",
        }
    )
    assert efectivos["anonymizer_masking_budget_ratio"] == 0.1
    assert efectivos["poll_interval_s"] == 10.5
    assert efectivos["poll_interval_active_s"] == 1


def test_e37_un_valor_que_no_es_un_numero_se_rechaza() -> None:
    _rechaza({"VERIDICUS_LIMIT_TURN_MAX_CHARS": "abc"}, "VERIDICUS_LIMIT_TURN_MAX_CHARS")


@pytest.mark.parametrize(
    ("variable", "valor"),
    [
        ("VERIDICUS_LIMIT_TURN_MAX_CHARS", ""),
        ("VERIDICUS_LIMIT_TURN_MAX_CHARS", "0"),
        ("VERIDICUS_LIMIT_TURN_MAX_CHARS", "-5"),
        ("VERIDICUS_LIMIT_TURN_MAX_CHARS", "1.5"),
        ("VERIDICUS_LIMIT_TURN_MAX_CHARS", "007"),
        ("VERIDICUS_LIMIT_TURN_MAX_CHARS", " 5"),
        ("VERIDICUS_LIMIT_TURN_MAX_CHARS", "9" * 5000),
        ("VERIDICUS_LIMIT_POLL_INTERVAL_S", "0"),
        ("VERIDICUS_LIMIT_POLL_INTERVAL_S", "0.0"),
        ("VERIDICUS_LIMIT_POLL_INTERVAL_S", "1e3"),
        ("VERIDICUS_LIMIT_POLL_INTERVAL_S", "-1"),
        ("VERIDICUS_LIMIT_ANONYMIZER_MASKING_BUDGET_RATIO", "0"),
        ("VERIDICUS_LIMIT_ANONYMIZER_MASKING_BUDGET_RATIO", "nan"),
    ],
)
def test_e37_un_valor_invalido_para_su_unidad_se_rechaza(variable: str, valor: str) -> None:
    _rechaza({variable: valor}, variable)


def test_e37_un_limite_que_no_existe_se_rechaza() -> None:
    _rechaza({"VERIDICUS_LIMIT_NO_EXISTE": "5"}, "VERIDICUS_LIMIT_NO_EXISTE")


def test_un_nombre_mal_escrito_no_pasa_en_silencio() -> None:
    _rechaza({"VERIDICUS_LIMIT_TURN_MAX_CHAR": "100"}, "VERIDICUS_LIMIT_TURN_MAX_CHAR")
    _rechaza({"VERIDICUS_LIMIT_": "100"})


def test_las_variables_ajenas_al_prefijo_se_ignoran() -> None:
    limits = _limits()
    ajenas = {"PATH": "x", "VERIDICUS_LIMITS_PATH": "otro.yaml", "VERIDICUS_PROFILE": "y"}
    assert limits.load(ajenas) == limits.load({})


def test_una_relacion_rota_tras_bajar_no_arranca() -> None:
    # La ventana (60) por debajo del solapamiento (20): fragment_overlap_turns < fragment_window_turns.
    _rechaza({"VERIDICUS_LIMIT_FRAGMENT_WINDOW_TURNS": "10"}, "fragment_overlap_turns")


def test_una_relacion_con_igualdad_permitida_se_acepta_y_sin_ella_se_rechaza() -> None:
    limits = _limits()
    # retention_min_days (1) <= retention_max_days (90): igualar es válido.
    efectivos = limits.load({"VERIDICUS_LIMIT_RETENTION_MAX_DAYS": "1"})
    assert efectivos["retention_max_days"] == efectivos["retention_min_days"] == 1
    # import_file_max_bytes < import_body_max_bytes: igualar no es válido.
    _rechaza(
        {"VERIDICUS_LIMIT_IMPORT_BODY_MAX_BYTES": "2097152"},
        "import_file_max_bytes",
        "import_body_max_bytes",
    )


def test_load_no_modifica_el_entorno_ni_comparte_el_resultado() -> None:
    limits = _limits()
    environ = {"VERIDICUS_LIMIT_TURN_MAX_CHARS": "10"}
    copia = dict(environ)
    primero = limits.load(environ)
    assert environ == copia
    primero["turn_max_chars"] = 1
    assert limits.load({})["turn_max_chars"] == 20000


def test_el_catalogo_se_lee_una_sola_vez(monkeypatch: pytest.MonkeyPatch) -> None:
    limits = _limits()

    def fallar(*_args: Any, **_kwargs: Any) -> None:
        raise AssertionError("limits.load no debe volver a leer el catálogo")

    monkeypatch.setattr(limits, "load_file", fallar)
    assert limits.load({})["turn_max_chars"] == 20000


@pytest.mark.parametrize("valor", ["5abc", "5.", "007.5", ".5", "5.5.5", "5,5", "1e3"])
def test_un_decimal_mal_formado_es_un_error_de_limites_y_no_un_valueerror(valor: str) -> None:
    _rechaza({"VERIDICUS_LIMIT_POLL_INTERVAL_S": valor}, "VERIDICUS_LIMIT_POLL_INTERVAL_S")


def test_un_decimal_entero_se_devuelve_como_entero() -> None:
    limits = _limits()
    efectivo = limits.load({"VERIDICUS_LIMIT_POLL_INTERVAL_ACTIVE_S": "1.0"})["poll_interval_active_s"]
    assert efectivo == 1
    assert type(efectivo) is int
    efectivo = limits.load({"VERIDICUS_LIMIT_POLL_INTERVAL_ACTIVE_S": "1.5"})["poll_interval_active_s"]
    assert efectivo == 1.5
    assert type(efectivo) is float


def _fallar(*_args: Any, **_kwargs: Any) -> None:
    raise AssertionError("limits.load no debe tocar archivos, entorno ni red (§4.15)")


class _EntornoQueFalla:
    def __getitem__(self, _clave: str) -> str:
        return _fallar()  # type: ignore[no-any-return]

    def get(self, *_args: Any) -> str:
        return _fallar()  # type: ignore[no-any-return]

    def __iter__(self) -> Any:
        return _fallar()

    def __contains__(self, _clave: object) -> bool:
        return _fallar()  # type: ignore[no-any-return]


def test_load_es_pura_sin_open_ni_entorno_ni_red(monkeypatch: pytest.MonkeyPatch) -> None:
    limits = _limits()
    esperado = limits.load({"VERIDICUS_LIMIT_TURN_MAX_CHARS": "10"})
    with monkeypatch.context() as parche:
        parche.setattr(builtins, "open", _fallar)
        parche.setattr(io, "open", _fallar)
        parche.setattr(os, "environ", _EntornoQueFalla())
        parche.setattr(os, "getenv", _fallar)
        parche.setattr(socket, "socket", _fallar)
        assert limits.load({"VERIDICUS_LIMIT_TURN_MAX_CHARS": "10"}) == esperado
        assert limits.load({})["turn_max_chars"] == 20000


def test_load_no_toca_el_entorno_del_proceso(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VERIDICUS_LIMIT_TURN_MAX_CHARS", "99999999")
    assert _limits().load({})["turn_max_chars"] == 20000
