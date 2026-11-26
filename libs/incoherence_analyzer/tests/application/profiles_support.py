"""Archivos de perfiles sintéticos para las pruebas de `analyze` (sin tocar `config/profiles.yaml`).

Cada función escribe un archivo en el directorio temporal de la prueba y devuelve la configuración
efectiva que sale de `load_config` con la referencia del *prompt* (K-88), como la compondrá la CLI.
"""

from pathlib import Path

from veridicus_execution_profiles.loader import EffectiveConfig, load_config

from tests.support import KEY_REF, env
from veridicus_incoherence_analyzer.application.messages import load_prompt_reference

ANTHROPIC_ROLE = """\
      {role}:
        provider: anthropic
        model: claude-sonnet-5-5
        scope: external
        family: claude
        api_key_ref: {key}
{parameters}"""

LOCAL_ROLE = """\
      {role}:
        provider: local
        model: {model}
        scope: local
        family: {family}
        base_url: "http://127.0.0.1:8080"
"""


def _external(role: str, parameters: str = "") -> str:
    return ANTHROPIC_ROLE.format(role=role, key=KEY_REF, parameters=parameters)


def _local(role: str, model: str, family: str) -> str:
    return LOCAL_ROLE.format(role=role, model=model, family=family)


def anthropic_profile(
    tmp_path: Path, *, permutation: bool = True, seed: int | None = None
) -> EffectiveConfig:
    """Como `demo-anthropic`, con la permutación y la semilla que pida la prueba."""
    parameters = "" if seed is None else f"        parameters:\n          seed: {seed}\n"
    text = (
        'schema_version: "1.0.0"\n'
        "profiles:\n"
        "  demo-anthropic:\n"
        "    purpose: demonstration\n"
        "    same_family_declared: true\n"
        f"    permutation: {str(permutation).lower()}\n"
        "    role_aliases:\n"
        "      verifier_permuted: verifier\n"
        "    roles:\n" + _external("judge", parameters) + _external("verifier", parameters)
    )
    return _load(tmp_path, "demo-anthropic", text)


def local_profile(tmp_path: Path, *, fallback: bool = False) -> EffectiveConfig:
    """Un perfil sin destinos externos o, con `fallback`, con un alterno externo."""
    text = (
        'schema_version: "1.0.0"\n'
        "profiles:\n"
        "  todo-local:\n"
        "    purpose: evaluation\n"
        "    permutation: true\n"
        "    role_aliases:\n"
        "      verifier_permuted: verifier\n"
        "    roles:\n"
        + _local("judge", "modelo-juez-prueba", "familia-a")
        + _local("verifier", "modelo-verificador-prueba", "familia-b")
    )
    if fallback:
        text += "    fallback_provider:\n" + _external("x").split("\n", 1)[1]
    return _load(tmp_path, "todo-local", text)


def _load(tmp_path: Path, name: str, text: str) -> EffectiveConfig:
    path = tmp_path / f"{name}.yaml"
    path.write_text(text, encoding="utf-8")
    return load_config(name, env(), path, prompt_sha256=load_prompt_reference())
