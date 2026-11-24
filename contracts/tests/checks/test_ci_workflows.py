"""Guardia de la CI: ningún workflow aplica cambios al clúster (security-design §4.11, AUTONOMIA-01).

`checks/ci_workflows.py` falla si un workflow de `.github/workflows/` contiene `--write`, `kubectl apply`,
`helm install`, `helm upgrade` o credenciales del clúster (`kubeconfig`, `KUBECONFIG`). La CI nunca
regenera la huella de seguridad ni despliega.
"""

from pathlib import Path
from types import ModuleType

import pytest
from helpers import CONTRACTS_ROOT, importar_o_fallar

REPO_ROOT = CONTRACTS_ROOT.parent


@pytest.fixture
def guardia() -> ModuleType:
    return importar_o_fallar("veridicus_contracts.checks.ci_workflows", "T18, paso 19")


def _workflow(raiz: Path, nombre: str, texto: str) -> Path:
    ruta = raiz / ".github" / "workflows" / nombre
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(texto, encoding="utf-8")
    return ruta


def test_los_workflows_reales_no_aplican_cambios_ni_tienen_credenciales(guardia: ModuleType) -> None:
    nombres = [ruta.name for ruta in guardia.workflows(REPO_ROOT)]
    assert "repo-level0.yml" in nombres, "la guardia no pasa en vacío"
    assert guardia.comprobar(REPO_ROOT) == []


@pytest.mark.parametrize(
    ("linea", "termino"),
    [
        ("run: kubectl apply -f deploy/", "kubectl apply"),
        ("run: kubectl   apply -f deploy/", "kubectl apply"),
        ("run: KUBECTL APPLY -f deploy/", "kubectl apply"),
        ("run: helm install veridicus charts/x", "helm install"),
        ("run: helm\tupgrade veridicus charts/x", "helm upgrade"),
        ("run: uv run python -m veridicus_contracts.tools.security_surface --write", "--write"),
        # F-01: opciones globales entre la herramienta y el verbo.
        ("run: kubectl -n veridicus apply -f x.yaml", "kubectl apply"),
        ("run: kubectl --context=minikube apply -f x.yaml", "kubectl apply"),
        ("run: kubectl --namespace veridicus apply -f x.yaml", "kubectl apply"),
        ("run: kubectl --dry-run apply -f x.yaml", "kubectl apply"),
        ("run: kubectl -n a --context=b --namespace c apply -f x.yaml", "kubectl apply"),
        ("run: helm --namespace v upgrade --install a b", "helm upgrade"),
        ("run: helm -n v install a b", "helm install"),
        ("run: helm --kube-context=m --debug install a b", "helm install"),
        ("env: {KUBECONFIG: /tmp/k}", "kubeconfig"),
        ("env: {KUBE_CONFIG: /tmp/k}", "kubeconfig"),
        ("run: echo ${{ secrets.kube_config }}", "kubeconfig"),
        ("run: echo ${{ secrets.kubeconfig }}", "kubeconfig"),
    ],
)
def test_un_workflow_con_un_comando_prohibido_es_rojo(guardia: ModuleType, tmp_path: Path, linea: str, termino: str) -> None:
    ruta = _workflow(tmp_path, "malo.yml", f"name: x\njobs:\n  j:\n    steps:\n      - {linea}\n")
    problemas = guardia.scan([ruta])
    assert problemas == [f"{ruta.as_posix()}:5: {termino} no se permite en un workflow (AUTONOMIA-01, §4.11)"]
    assert guardia.comprobar(tmp_path) == problemas


def test_un_workflow_con_kubectl_apply_en_un_comentario_tambien_es_rojo(guardia: ModuleType, tmp_path: Path) -> None:
    _workflow(tmp_path, "comentario.yaml", "# antes: kubectl apply -f x\nname: x\n")
    assert len(guardia.comprobar(tmp_path)) == 1


def test_un_workflow_limpio_y_las_lecturas_de_kubectl_pasan(guardia: ModuleType, tmp_path: Path) -> None:
    _workflow(tmp_path, "limpio.yml", "name: x\njobs:\n  j:\n    steps:\n      - run: helm template charts/x\n      - run: kubectl get pods\n")
    assert guardia.comprobar(tmp_path) == []


@pytest.mark.parametrize(
    "linea",
    [
        "run: kubectl -n veridicus get pods",
        "run: kubectl --context=minikube get pods -o yaml",
        "run: kubectl get pods applyd",
        "run: helm --namespace v template a b",
        "run: helm -n v list",
        "run: helm lint charts/x --strict",
    ],
)
def test_las_lecturas_con_opciones_globales_pasan(guardia: ModuleType, tmp_path: Path, linea: str) -> None:
    _workflow(tmp_path, "lectura.yml", f"name: x\njobs:\n  j:\n    steps:\n      - {linea}\n")
    assert guardia.comprobar(tmp_path) == []


def test_varias_apariciones_se_reportan_en_orden_de_archivo_y_linea(guardia: ModuleType, tmp_path: Path) -> None:
    _workflow(tmp_path, "b.yml", "run: helm install a\nrun: kubectl apply -f x --write\n")
    _workflow(tmp_path, "a.yml", "run: helm upgrade a\n")
    problemas = guardia.comprobar(tmp_path)
    assert [p.rsplit("/", 1)[1].split(" ", 1)[0] for p in problemas] == ["a.yml:1:", "b.yml:1:", "b.yml:2:", "b.yml:2:"]
    assert all(p.endswith("(AUTONOMIA-01, §4.11)") for p in problemas)


def test_solo_se_miran_los_workflows_yaml_de_la_carpeta(guardia: ModuleType, tmp_path: Path) -> None:
    assert guardia.comprobar(tmp_path) == []
    ruta = _workflow(tmp_path, "notas.txt", "kubectl apply\n")
    otra = tmp_path / ".github" / "dependabot.yml"
    otra.write_text("kubectl apply\n", encoding="utf-8")
    assert guardia.comprobar(tmp_path) == []
    assert [r.name for r in guardia.workflows(tmp_path)] == []
    assert ruta.exists()
