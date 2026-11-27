"""El guardián de shell `scripts/check-no-cluster-apply.sh` y su excepción para `scripts/humano/` (F-07).

Solo se ejecuta el guardián (que lee archivos) sobre árboles pequeños armados en `tmp_path`; ningún
script de `scripts/humano/` se ejecuta. Las operaciones del clúster se arman con fragmentos.
"""

import shutil
import subprocess
from pathlib import Path

import pytest
from support import DEPLOY

ROOT = DEPLOY.parent
GUARDIAN = ROOT / "scripts" / "check-no-cluster-apply.sh"
K = "kube" + "ctl"
LINE = f"{K} apply -f y\n"


def _tree(root: Path, rel: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(LINE, encoding="utf-8")


def _run(root: Path) -> int:
    bash = shutil.which("bash")
    assert bash is not None
    done = subprocess.run(  # noqa: S603 (bash y rutas propias, sin shell)
        [bash, str(GUARDIAN), str(root)], capture_output=True, text=True, check=False
    )
    return done.returncode


def test_the_exact_human_folder_is_not_read(tmp_path: Path) -> None:
    _tree(tmp_path, "scripts/humano/aplicar.sh")
    assert _run(tmp_path) == 0


@pytest.mark.parametrize(
    "rel",
    [
        "scripts/otro/humano/aplicar.sh",
        "scripts/humano2/aplicar.sh",
        "scripts/aplicar.sh",
        ".github/humano/aplicar.sh",
        ".github/workflows/humano/aplicar.sh",
    ],
)
def test_f07_any_other_folder_named_humano_is_read(tmp_path: Path, rel: str) -> None:
    _tree(tmp_path, rel)
    assert _run(tmp_path) == 1


def test_a_tree_with_only_the_human_folder_and_a_clean_script_passes(tmp_path: Path) -> None:
    _tree(tmp_path, "scripts/humano/aplicar.sh")
    (tmp_path / "scripts" / "limpio.sh").write_text("echo hola\n", encoding="utf-8")
    assert _run(tmp_path) == 0


def test_a_tree_without_github_or_scripts_has_nothing_to_read(tmp_path: Path) -> None:
    assert _run(tmp_path) == 0


def test_the_real_repository_passes() -> None:
    assert _run(ROOT) == 0
