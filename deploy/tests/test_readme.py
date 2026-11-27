"""La guía de la demo (paso 10): se lee como texto y nunca se ejecuta nada de lo que cita.

Cada regla lleva su control negativo: un archivo de `deploy/tests/fixtures/readme/` (o una variante
armada en memoria a partir de `ok.md`) con ese único defecto. La clave del caso del secreto pegado
se arma con fragmentos para que ningún archivo del repositorio lleve algo con forma de clave.
"""

import re
from pathlib import Path

import pytest
from readme_checks import REQUIRED_SCRIPTS, REQUIRED_SECTIONS, violations
from support import DEPLOY

ROOT = DEPLOY.parent
README = DEPLOY / "demo-analyzer" / "README.md"
FIXTURES = DEPLOY / "tests" / "fixtures" / "readme"
OK = (FIXTURES / "ok.md").read_text(encoding="utf-8")

NEGATIVES = {
    "ruta-rota.md": "cita una ruta del repositorio que no existe",
    "script-inexistente.md": "nombra un script que no está en scripts/humano",
    "sin-pull-secret.md": "falta alguno de los tres scripts del humano",
    "sin-frontera.md": "falta la sección «frontera de datos»",
    "sin-calico.md": "el comando minikube start no lleva --cni=calico",
    "menciona-kubeconfig.md": "menciona un kubeconfig",
    "etiqueta-latest.md": "usa latest como etiqueta de imagen",
}


def _fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_the_real_readme_exists() -> None:
    assert README.is_file()


def test_the_real_readme_passes_all_the_rules() -> None:
    assert violations(README.read_text(encoding="utf-8"), ROOT) == []


def test_the_real_readme_fits_in_two_pages() -> None:
    # Dos páginas impresas son unas 120 líneas de texto corrido; se deja un margen para los bloques.
    assert len(README.read_text(encoding="utf-8").splitlines()) <= 140


def test_the_fixture_that_meets_every_rule_passes() -> None:
    assert violations(OK, ROOT) == []


@pytest.mark.parametrize("name", NEGATIVES)
def test_negative_a_readme_with_one_defect_fails_its_rule(name: str) -> None:
    assert violations(_fixture(name), ROOT) == [NEGATIVES[name]]


def test_negative_probe_1_a_path_that_does_not_exist_fails() -> None:
    assert "scripts/humano/no-existe.sh" in _fixture("ruta-rota.md")
    assert violations(_fixture("ruta-rota.md"), ROOT) != []


def test_negative_probe_2_a_forgotten_script_fails() -> None:
    text = _fixture("sin-pull-secret.md")
    assert "crear-pull-secret-ghcr.sh" not in text
    assert violations(text, ROOT) != []


def test_negative_probe_3_minikube_without_calico_fails() -> None:
    text = _fixture("sin-calico.md")
    assert "minikube start --memory=8g --cpus=4" in text
    assert violations(text, ROOT) != []


def test_negative_probe_4_a_pasted_key_fails_and_is_not_echoed() -> None:
    key = "sk-" + "ant-" + "SINTETICA0123456789"
    found = violations(OK + f"\nVERIDICUS_ANTHROPIC_API_KEY={key}\n", ROOT)
    assert found == ["lleva algo con forma de clave o token"]
    assert all(key not in message for message in found)


def test_negative_probe_5_no_data_boundary_section_fails() -> None:
    assert violations(_fixture("sin-frontera.md"), ROOT) != []


@pytest.mark.parametrize("keyword", REQUIRED_SECTIONS)
def test_negative_each_required_section_is_required(keyword: str) -> None:
    lines = [
        line.replace("#", "-", 1) if line.startswith("#") and keyword in line.lower() else line
        for line in OK.splitlines()
    ]
    assert violations("\n".join(lines), ROOT) == [f"falta la sección «{keyword}»"]


@pytest.mark.parametrize("name", REQUIRED_SCRIPTS)
def test_negative_each_human_script_is_required(name: str) -> None:
    text = "\n".join(line for line in OK.splitlines() if name not in line)
    assert violations(text, ROOT) == ["falta alguno de los tres scripts del humano"]


@pytest.mark.parametrize(
    "shape",
    ["ghp_" + "A1b2C3d4E5f6G7", "github_pat_" + "A1b2C3d4E5f6G7", "sk-" + "A1b2C3d4E5f6G7h8I9j0K1"],
)
def test_negative_other_token_shapes_fail(shape: str) -> None:
    assert violations(OK + f"\n{shape}\n", ROOT) == ["lleva algo con forma de clave o token"]


def test_negative_a_second_minikube_start_without_calico_fails() -> None:
    text = OK + "\n`minikube start --memory=8g`\n"
    assert violations(text, ROOT) == ["el comando minikube start no lleva --cni=calico"]


def test_negative_no_minikube_start_at_all_fails() -> None:
    text = re.sub(r"minikube start", "minikube status", OK)
    assert violations(text, ROOT) == ["el comando minikube start no lleva --cni=calico"]


def test_negative_the_user_form_must_not_admit_an_underscore() -> None:
    assert violations(_fixture("usuario-guion-bajo.md"), ROOT) == [
        "dice que el usuario admite guion bajo"
    ]


def test_the_user_form_may_say_it_has_no_underscore() -> None:
    text = OK + "\nEl usuario: letras, cifras y guion, sin guion bajo.\n"
    assert violations(text, ROOT) == []


@pytest.mark.parametrize(
    "path",
    [
        "scripts/otra/nada.sh",
        ".github/workflows/no-existe.yml",
        "redeploy/demo-analyzer/job.yaml",
        "libs/no-existe/modulo.py",
        "contracts/no-existe.json",
    ],
)
def test_negative_f03_a_cited_path_outside_scripts_humano_is_checked(path: str) -> None:
    assert violations(OK + f"\nVea `{path}`.\n", ROOT) == [
        "cita una ruta del repositorio que no existe"
    ]


@pytest.mark.parametrize(
    "path", [".github/workflows/analyzer-image.yml", "libs/errors", "libs/anonymizer"]
)
def test_f03_a_cited_path_that_exists_passes(path: str) -> None:
    assert violations(OK + f"\nVea `{path}`.\n", ROOT) == []


@pytest.mark.parametrize("prefix", ["ghs_", "gho_", "ghu_", "ghr_", "ghp_"])
def test_negative_f03_every_github_token_prefix_fails(prefix: str) -> None:
    assert violations(OK + f"\n{prefix}A1b2C3d4E5f6G7h8\n", ROOT) == [
        "lleva algo con forma de clave o token"
    ]


def test_f03_a_minikube_start_continued_over_two_lines_passes() -> None:
    text = OK.replace(
        "`minikube start --cni=calico --memory=8g --cpus=4`",
        "`minikube start \\\n  --cni=calico --memory=8g --cpus=4`",
    )
    assert text != OK
    assert violations(text, ROOT) == []


def test_negative_f03_a_continued_minikube_start_without_calico_fails() -> None:
    text = OK + "\n`minikube start \\\n  --memory=8g`\n"
    assert violations(text, ROOT) == ["el comando minikube start no lleva --cni=calico"]


def test_negative_f03_one_heading_cannot_cover_every_section() -> None:
    body = [line for line in OK.splitlines() if not line.startswith("#")]
    heading = "## " + " ".join(REQUIRED_SECTIONS)
    text = "\n".join([heading, *body])
    assert violations(text, ROOT) == ["un encabezado cubre varias secciones obligatorias"]


def _real() -> str:
    return README.read_text(encoding="utf-8")


def test_f01_the_real_readme_gives_the_literal_ghcr_filler_and_the_order() -> None:
    text = _real()
    assert "VERIDICUS_GHCR_USER=relleno" in text
    assert "VERIDICUS_GHCR_TOKEN=relleno" in text
    assert "antes de `demo-analyzer.sh`" in text


def test_f02_the_real_readme_states_what_each_control_does() -> None:
    text = _real()
    assert "del namespace `veridicus-demo`" in text
    assert "kube-dns" in text
    assert "IP públicas" in text
    assert "dentro del proceso" in text
    assert "Kyverno" in text


def test_f04_the_real_readme_names_the_token_kind_and_removes_the_local_image() -> None:
    text = _real()
    assert "PAT clásico" in text
    assert "read:packages" in text
    assert "minikube image rm" in text
    assert "antes del script 3" in text


def test_every_script_in_the_folder_is_named_by_the_required_list() -> None:
    # visor-pod.sh no es de la demo del Job sino del visor; lo documenta deploy/demo-visor/README.md.
    names = sorted(path.name for path in (ROOT / "scripts" / "humano").glob("*.sh"))
    assert names == sorted([*REQUIRED_SCRIPTS, "visor-pod.sh", "argocd-instalar.sh"])
    visor = (ROOT / "deploy" / "demo-visor" / "README.md").read_text(encoding="utf-8")
    assert "scripts/humano/visor-pod.sh" in visor
    assert "scripts/humano/argocd-instalar.sh" in visor


def test_the_fixtures_folder_holds_only_synthetic_markdown() -> None:
    assert {path.suffix for path in Path(FIXTURES).iterdir()} == {".md"}
