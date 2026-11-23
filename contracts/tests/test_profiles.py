"""`profiles.validate` (F8, BR9.2-BR9.5, BR9.8, §4.15): módulo guardia con 100 % de ramas.

Escenarios E21 a E26, E38 y E39 de functional-spec §5. Todo con datos sintéticos; el
*canary* de `api_key_ref` demuestra que ningún mensaje repite el valor de un ajuste.
"""

import copy
import os
import socket
from collections.abc import Mapping
from typing import Any

import pytest
from helpers import cargar_fixture, importar_o_fallar

pytestmark = pytest.mark.c18

PREFIJO = "VERIDICUS_"
CANARY = "CANARY_ZXQ_7731"
DIRECTORIO = "profiles/fixtures"


def _perfiles() -> Any:
    return importar_o_fallar("veridicus_contracts.profiles", "paso 11, T09")


def _destino(modelo: str, **extra: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "provider": "local",
        "model": modelo,
        "scope": "local",
        "base_url": "http://veridicus-llm:8080",
    }
    base.update(extra)
    return base


def _analizador() -> dict[str, Any]:
    """Un archivo válido del analizador con un perfil sintético."""
    return {
        "schema_version": "1.0.0",
        "profiles": {
            "todo-local": {
                "purpose": "demonstration",
                "roles": {
                    "judge": _destino("modelo-juez-prueba", family="familia-a"),
                    "verifier": _destino("modelo-verificador-prueba", family="familia-b"),
                },
                "role_aliases": {"verifier_permuted": "verifier"},
                "permutation": True,
            }
        },
    }


def _base() -> dict[str, Any]:
    """Un archivo válido del perfil genérico (E21)."""
    return cargar_fixture(f"{DIRECTORIO}/profile-base.valid.yaml", "C18.profile-base")["payload"]  # type: ignore[no-any-return]


def _perfil(datos: dict[str, Any], nombre: str = "todo-local") -> dict[str, Any]:
    return datos["profiles"][nombre]  # type: ignore[no-any-return]


def _rechaza(datos: Any, *, kind: str = "analyzer", prefijo: str = PREFIJO) -> Any:
    modulo = _perfiles()
    with pytest.raises(modulo.ProfileValidationError) as info:
        modulo.validate(datos, key_prefix=prefijo, kind=kind)
    return info.value


# --- Aceptación ---------------------------------------------------------------------


def test_e21_el_perfil_generico_con_papeles_de_prueba_se_acepta() -> None:
    perfiles = _perfiles().validate(_base(), key_prefix=PREFIJO, kind="base")
    assert set(perfiles["prueba-generica"]["roles"]) == {"prueba_a", "prueba_b"}


def test_el_perfil_del_analizador_de_la_configuracion_efectiva_se_acepta() -> None:
    efectiva = cargar_fixture(f"{DIRECTORIO}/effective-config.valid.json", "C18.effective-config")
    datos = {"schema_version": "1.0.0", "profiles": {"comercial-piloto": efectiva["payload"]["profile"]}}
    perfiles = _perfiles().validate(datos, key_prefix=PREFIJO, kind="analyzer")
    assert "comercial-piloto" in perfiles


def test_un_perfil_del_analizador_tambien_cumple_la_base() -> None:
    _perfiles().validate(_analizador(), key_prefix=PREFIJO, kind="base")


def test_el_resultado_es_inmutable() -> None:
    perfiles = _perfiles().validate(_analizador(), key_prefix=PREFIJO, kind="analyzer")
    assert isinstance(perfiles, Mapping)
    with pytest.raises(TypeError):
        perfiles["otro"] = {}
    perfil = perfiles["todo-local"]
    with pytest.raises(TypeError):
        perfil["purpose"] = "production"
    assert isinstance(perfil["roles"], Mapping)
    with pytest.raises(TypeError):
        perfil["roles"]["judge"]["model"] = "otro"


def test_el_resultado_congela_las_listas_y_no_comparte_la_entrada() -> None:
    datos = _base()
    _perfil(datos, "prueba-generica")["etiquetas"] = ["a", "b"]
    perfiles = _perfiles().validate(datos, key_prefix=PREFIJO, kind="base")
    assert perfiles["prueba-generica"]["etiquetas"] == ("a", "b")
    _perfil(datos, "prueba-generica")["etiquetas"].append("c")
    assert perfiles["prueba-generica"]["etiquetas"] == ("a", "b")


def test_e38_un_campo_extra_es_valido_en_la_base_y_rechazado_en_el_analizador() -> None:
    datos = _analizador()
    _perfil(datos)["prueba_extra"] = True
    _perfiles().validate(datos, key_prefix=PREFIJO, kind="base")
    error = _rechaza(datos)
    assert "todo-local" in str(error)
    assert "prueba_extra" in str(error)


# --- E22 y la forma del analizador --------------------------------------------------


def test_e22_el_perfil_del_analizador_con_un_papel_extra_se_rechaza() -> None:
    fixture = cargar_fixture(f"{DIRECTORIO}/analyzer-profile.extra-role.yaml", "C18.profiles")
    error = _rechaza(fixture["payload"])
    assert "perfil todo-local" in str(error)
    assert "prueba_a" in str(error)


def test_el_analizador_exige_judge_y_verifier() -> None:
    datos = _analizador()
    del _perfil(datos)["roles"]["verifier"]
    error = _rechaza(datos)
    assert "verifier" in str(error)
    assert "todo-local" in str(error)


@pytest.mark.parametrize("alias", [{}, {"verifier_permuted": "judge"}, {"otro": "verifier"}])
def test_el_analizador_exige_exactamente_el_alias_verifier_permuted(alias: dict[str, str]) -> None:
    datos = _analizador()
    _perfil(datos)["role_aliases"] = alias
    _rechaza(datos)


def test_el_analizador_exige_sus_ajustes_obligatorios() -> None:
    for ajuste in ("role_aliases", "permutation"):
        datos = _analizador()
        del _perfil(datos)[ajuste]
        assert ajuste in str(_rechaza(datos))


def test_el_proposito_del_analizador_es_un_enum() -> None:
    datos = _analizador()
    _perfil(datos)["purpose"] = "otro-proposito"
    assert "purpose" in str(_rechaza(datos))
    _perfil(datos)["purpose"] = "evaluation"
    _perfiles().validate(datos, key_prefix=PREFIJO, kind="analyzer")


def test_el_proposito_de_la_base_es_texto_con_patron() -> None:
    datos = _base()
    _perfil(datos, "prueba-generica")["purpose"] = "Otro Proposito"
    assert "purpose" in str(_rechaza(datos, kind="base"))
    _perfil(datos, "prueba-generica")["purpose"] = "otro-proposito"
    _perfiles().validate(datos, key_prefix=PREFIJO, kind="base")


# --- Sobre del archivo --------------------------------------------------------------


@pytest.mark.parametrize("kind", ["base", "analyzer"])
def test_el_sobre_exige_la_version_y_los_nombres_de_perfil(kind: str) -> None:
    datos = _base() if kind == "base" else _analizador()
    perfil = next(iter(datos["profiles"].values()))

    malo = copy.deepcopy(datos)
    malo["schema_version"] = "2.0.0"
    assert "schema_version" in str(_rechaza(malo, kind=kind))

    sin_version = copy.deepcopy(datos)
    del sin_version["schema_version"]
    assert "schema_version" in str(_rechaza(sin_version, kind=kind))

    for nombre in ("Mayuscula", "x" * 49, "con espacio"):
        malo = copy.deepcopy(datos)
        malo["profiles"] = {nombre: perfil}
        error = _rechaza(malo, kind=kind)
        assert "profiles" in str(error)

    vacio = copy.deepcopy(datos)
    vacio["profiles"] = {}
    assert "profiles" in str(_rechaza(vacio, kind=kind))

    sin_perfiles = copy.deepcopy(datos)
    del sin_perfiles["profiles"]
    assert "profiles" in str(_rechaza(sin_perfiles, kind=kind))


@pytest.mark.parametrize("datos", [None, [], "texto", 7])
def test_un_documento_que_no_es_un_objeto_se_rechaza(datos: Any) -> None:
    _rechaza(datos)
    _rechaza(datos, kind="base")


def test_un_perfil_sin_papeles_o_sin_proposito_se_rechaza() -> None:
    datos = _base()
    _perfil(datos, "prueba-generica")["roles"] = {}
    assert "roles" in str(_rechaza(datos, kind="base"))
    datos = _base()
    del _perfil(datos, "prueba-generica")["purpose"]
    assert "purpose" in str(_rechaza(datos, kind="base"))


def test_el_nombre_de_un_papel_tiene_la_forma_de_role_name() -> None:
    datos = _base()
    roles = _perfil(datos, "prueba-generica")["roles"]
    roles["Prueba A"] = roles.pop("prueba_a")
    error = _rechaza(datos, kind="base")
    assert "roles" in str(error)
    # El nombre no válido no se repite en el mensaje.
    assert "Prueba A" not in str(error)


# --- E23: referencias cruzadas de los alias (BR9.2) ----------------------------------


def test_e23_un_alias_a_un_papel_que_no_existe_se_rechaza() -> None:
    datos = _base()
    _perfil(datos, "prueba-generica")["role_aliases"] = {"prueba_b_permutada": "verificador_x"}
    error = _rechaza(datos, kind="base")
    assert "prueba_b_permutada" in str(error)
    assert "no existe" in str(error)
    assert "verificador_x" not in str(error)


def test_e23_un_alias_que_apunta_a_otro_alias_se_rechaza() -> None:
    datos = _base()
    _perfil(datos, "prueba-generica")["role_aliases"] = {
        "prueba_b_permutada": "prueba_b",
        "segundo_alias": "prueba_b_permutada",
    }
    error = _rechaza(datos, kind="base")
    assert "segundo_alias" in str(error)
    assert "otro alias" in str(error)


def test_e23_un_alias_con_el_nombre_de_un_papel_se_rechaza() -> None:
    datos = _base()
    _perfil(datos, "prueba-generica")["role_aliases"] = {"prueba_a": "prueba_b"}
    error = _rechaza(datos, kind="base")
    assert "nombre de un papel" in str(error)


def test_un_perfil_generico_sin_alias_es_valido() -> None:
    datos = _base()
    del _perfil(datos, "prueba-generica")["role_aliases"]
    _perfiles().validate(datos, key_prefix=PREFIJO, kind="base")


# --- E24 y E25: prefijo de las claves (BR9.4) ----------------------------------------


def _con_clave(referencia: str) -> dict[str, Any]:
    datos = _analizador()
    _perfil(datos)["roles"]["judge"]["api_key_ref"] = referencia
    return datos


def test_e24_otro_clave_se_rechaza_con_un_prefijo_y_se_acepta_con_otro() -> None:
    datos = _con_clave("OTRO_CLAVE")
    error = _rechaza(datos, prefijo="VERIDICUS_")
    assert "judge" in str(error)
    assert "api_key_ref" in str(error)
    assert "todo-local" in str(error)
    _perfiles().validate(datos, key_prefix="OTRO_", kind="analyzer")


def test_la_clave_con_el_prefijo_correcto_se_acepta() -> None:
    _perfiles().validate(_con_clave("VERIDICUS_CLAVE_JUEZ"), key_prefix=PREFIJO, kind="analyzer")


@pytest.mark.parametrize("referencia", ["veridicus_clave", "AB", "A" * 65, "1CLAVE", "CLAVE-X"])
def test_api_key_ref_exige_la_forma_generica(referencia: str) -> None:
    error = _rechaza(_con_clave(referencia), prefijo="A")
    assert "ajuste api_key_ref: no cumple la forma exigida" in str(error)


def test_el_prefijo_de_la_clave_tambien_se_exige_al_proveedor_alterno() -> None:
    datos = _analizador()
    _perfil(datos)["fallback_provider"] = _destino("modelo-alterno", api_key_ref="OTRO_ALTERNO")
    error = _rechaza(datos)
    assert "fallback_provider" in str(error)
    assert "api_key_ref" in str(error)
    _perfil(datos)["fallback_provider"]["api_key_ref"] = "VERIDICUS_ALTERNO"
    _perfiles().validate(datos, key_prefix=PREFIJO, kind="analyzer")


def test_el_prefijo_es_un_texto_con_la_forma_de_una_clave() -> None:
    modulo = _perfiles()
    for prefijo in ("", "veridicus_", "VERI DICUS_", 7, None):
        with pytest.raises(modulo.ProfileValidationError) as info:
            modulo.validate(_analizador(), key_prefix=prefijo, kind="analyzer")
        assert "key_prefix" in str(info.value)


def test_el_tipo_de_perfil_es_base_o_analyzer() -> None:
    modulo = _perfiles()
    with pytest.raises(modulo.ProfileValidationError) as info:
        modulo.validate(_analizador(), key_prefix=PREFIJO, kind="otro")
    assert "kind" in str(info.value)


# --- E26: un solo proveedor alterno (BR9.5) -------------------------------------------


def test_e26_un_papel_con_su_propio_fallback_se_rechaza() -> None:
    datos = _analizador()
    _perfil(datos)["roles"]["judge"]["fallback"] = _destino("modelo-alterno")
    error = _rechaza(datos)
    assert "judge" in str(error)
    assert "fallback" in str(error)
    _perfil(datos)["roles"]["judge"].pop("fallback")
    _perfil(datos)["fallback_provider"] = _destino("modelo-alterno")
    _perfiles().validate(datos, key_prefix=PREFIJO, kind="analyzer")


def test_un_papel_con_fallback_provider_propio_se_rechaza_en_la_base() -> None:
    datos = _base()
    _perfil(datos, "prueba-generica")["roles"]["prueba_a"]["fallback_provider"] = _destino("m")
    error = _rechaza(datos, kind="base")
    assert "prueba_a" in str(error)


def test_un_error_del_proveedor_alterno_lo_nombra_como_papel() -> None:
    datos = _analizador()
    _perfil(datos)["fallback_provider"] = _destino("modelo-alterno", sobra=1)
    error = _rechaza(datos)
    assert (
        "perfil todo-local, papel fallback_provider, ajuste sobra: ajuste no permitido"
        in error.problems
    )


# --- E39: el prefijo es obligatorio ---------------------------------------------------


def test_e39_validate_sin_key_prefix_es_un_error_de_tipo() -> None:
    with pytest.raises(TypeError):
        _perfiles().validate(_base(), kind="base")


def test_validate_exige_kind_y_solo_acepta_argumentos_con_nombre() -> None:
    modulo = _perfiles()
    with pytest.raises(TypeError):
        modulo.validate(_base(), key_prefix=PREFIJO)
    with pytest.raises(TypeError):
        modulo.validate(_base(), PREFIJO, "base")


# --- El error: código estable y nunca un valor -----------------------------------------


def test_el_error_lleva_el_codigo_estable_y_los_problemas() -> None:
    error = _rechaza(_con_clave("OTRO_CLAVE"))
    assert error.code == "config.invalid_profile"
    assert isinstance(error, ValueError)
    assert error.problems
    assert all(isinstance(problema, str) for problema in error.problems)
    assert str(error).startswith("perfil no válido")


def test_los_problemas_nombran_perfil_papel_y_ajuste() -> None:
    error = _rechaza(_con_clave("OTRO_CLAVE"))
    assert error.problems == ("perfil todo-local, papel judge, ajuste api_key_ref: no cumple el prefijo exigido",)


def test_los_problemas_salen_en_un_orden_estable() -> None:
    datos = _analizador()
    _perfil(datos)["purpose"] = "otro-proposito"
    _perfil(datos)["permutation"] = "si"
    primero = _rechaza(datos).problems
    segundo = _rechaza(copy.deepcopy(datos)).problems
    assert primero == segundo
    assert len(primero) == 2


def test_un_nombre_de_forma_inusual_no_llega_al_mensaje() -> None:
    datos = _analizador()
    _perfil(datos)["roles"]["judge"]["x" * 70] = 1
    _perfil(datos)["roles"]["judge"]["con espacio"] = 1
    error = _rechaza(datos)
    assert "x" * 70 not in str(error)
    assert "con espacio" not in str(error)
    assert "?" in str(error)


def test_el_canary_de_api_key_ref_no_aparece_en_ningun_mensaje() -> None:
    modulo = _perfiles()
    casos: list[tuple[dict[str, Any], str, str]] = []
    # Forma inválida, prefijo incorrecto y valor en un ajuste que sobra.
    datos = _con_clave(CANARY.lower())
    casos.append((datos, PREFIJO, "analyzer"))
    casos.append((_con_clave(CANARY), PREFIJO, "analyzer"))
    casos.append((_con_clave(CANARY), PREFIJO, "base"))
    extra = _analizador()
    _perfil(extra)["roles"]["judge"]["api_key_ref"] = "VERIDICUS_CLAVE"
    _perfil(extra)["roles"]["judge"]["otra_clave"] = CANARY
    casos.append((extra, PREFIJO, "analyzer"))
    alterno = _analizador()
    _perfil(alterno)["fallback_provider"] = _destino("modelo-alterno", api_key_ref=CANARY)
    casos.append((alterno, PREFIJO, "analyzer"))
    tipo = _analizador()
    _perfil(tipo)["roles"]["judge"]["api_key_ref"] = [CANARY]
    casos.append((tipo, PREFIJO, "analyzer"))
    for datos_del_caso, prefijo, kind in casos:
        with pytest.raises(modulo.ProfileValidationError) as info:
            modulo.validate(datos_del_caso, key_prefix=prefijo, kind=kind)
        error = info.value
        textos = [str(error), repr(error), *map(str, error.args), *error.problems]
        assert all(CANARY not in texto and CANARY.lower() not in texto for texto in textos)
        assert error.__cause__ is None
        assert error.__context__ is None


# --- Pureza (§4.15) --------------------------------------------------------------------


def test_validate_no_hace_entrada_salida_ni_lee_el_entorno(monkeypatch: pytest.MonkeyPatch) -> None:
    modulo = _perfiles()
    valido = _analizador()
    invalido = _con_clave("OTRO_CLAVE")

    def prohibido(*_args: Any, **_kwargs: Any) -> Any:
        raise AssertionError("validate no debe hacer E/S ni leer el entorno")

    class EntornoProhibido:
        def __getattr__(self, nombre: str) -> Any:
            raise AssertionError(f"validate leyó os.environ.{nombre}")

        def __getitem__(self, _clave: str) -> Any:
            raise AssertionError("validate leyó os.environ")

        def __contains__(self, _clave: object) -> bool:
            raise AssertionError("validate leyó os.environ")

        def __iter__(self) -> Any:
            raise AssertionError("validate leyó os.environ")

    # El parche vive solo dentro del bloque: pytest también lee el entorno al informar.
    with monkeypatch.context() as parche:
        parche.setattr("builtins.open", prohibido)
        parche.setattr(os, "environ", EntornoProhibido())
        parche.setattr(socket, "socket", prohibido)
        parche.setattr(os, "getenv", prohibido)
        resultado = modulo.validate(valido, key_prefix=PREFIJO, kind="analyzer")
        try:
            modulo.validate(invalido, key_prefix=PREFIJO, kind="analyzer")
        except modulo.ProfileValidationError as error:
            fallo = error
        else:
            fallo = None
    assert "todo-local" in resultado
    assert fallo is not None
