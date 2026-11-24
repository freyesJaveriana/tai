"""Guardia de la CI: ningún workflow aplica cambios al clúster (security-design §4.11, AUTONOMIA-01).

`checks/ci_workflows.py` falla si un workflow de `.github/workflows/` contiene `--write`, `kubectl apply`,
`helm install`, `helm upgrade` o credenciales del clúster (`kubeconfig`, `KUBECONFIG`). La CI nunca
regenera la huella de seguridad ni despliega.
"""

import re
import signal
import time
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


def _tarda_menos_de(segundos: float, patron: re.Pattern[str], texto: str) -> bool:
    """Busca `patron` en `texto` con un reloj de pared: si pasa del plazo, el motor se interrumpe."""

    def _vencido(*_: object) -> None:
        raise TimeoutError

    anterior = signal.signal(signal.SIGALRM, _vencido)
    signal.setitimer(signal.ITIMER_REAL, segundos)
    inicio = time.perf_counter()
    try:
        patron.search(texto)
    except TimeoutError:
        return False
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, anterior)
    return time.perf_counter() - inicio < segundos


@pytest.mark.parametrize(("opcion", "repeticiones"), [("-a", 40), ("--a", 30), ("--a-b.c", 30), ("-a=1", 30), ("--", 30)])
@pytest.mark.parametrize("herramienta", ["kubectl", "helm"])
def test_f02_muchas_opciones_seguidas_no_hacen_retroceder_al_motor(
    guardia: ModuleType, herramienta: str, opcion: str, repeticiones: int
) -> None:
    # F-02: un `-a` que sigue a una opción podía ser su valor o una opción nueva, y `--a` se podía leer como
    # `-` más `-a` o como `--` más `a` (retroceso exponencial). Cada caso lleva su tope de tiempo.
    cola = f" {opcion}" * repeticiones
    texto = herramienta + cola + " x"
    for termino, patron in guardia.PROHIBIDOS:
        assert _tarda_menos_de(1.0, patron, texto), (termino, opcion, "tarda más de 1 s")
    # Y las mismas opciones seguidas de un verbo prohibido sí se detectan, en poco tiempo.
    verbo = "apply" if herramienta == "kubectl" else "install"
    patron = next(p for t, p in guardia.PROHIBIDOS if t == f"{herramienta} {verbo}")
    assert _tarda_menos_de(1.0, patron, herramienta + cola + f" {verbo}")
    assert patron.search(herramienta + cola + f" {verbo}") is not None


def test_f02_las_formas_de_la_sonda_siguen_detectandose_y_las_lecturas_no_dan_falso_positivo(
    guardia: ModuleType, tmp_path: Path
) -> None:
    texto = (
        "a: kubectl -n x apply -f y\n"
        "b: kubectl --context=x apply -f y\n"
        "c: kubectl --namespace x apply -f y\n"
        "d: kubectl -v 9 --namespace x apply -f y\n"
        "e: kubectl -n x -- apply -f y\n"
        "f: /usr/bin/kubectl apply -f y\n"
        "g: helm --namespace v upgrade --install a b\n"
        "h: KUBE_CONFIG: x\n"
        "i: kubectl -n x describe applyset\n"
        "j: kubectl --context=m -n x get pods\n"
        "k: helm -n v list\n"
    )
    ruta = _workflow(tmp_path, "sonda.yml", texto)
    prefijo = ruta.as_posix() + ":"
    lineas = sorted({int(p.removeprefix(prefijo).split(":", 1)[0]) for p in guardia.scan([ruta])})
    assert lineas == [1, 2, 3, 4, 5, 6, 7, 8], lineas


def test_p_t18_16_un_valor_entre_comillas_con_espacios_es_una_limitacion_declarada(
    guardia: ModuleType, tmp_path: Path
) -> None:
    # F-03 de la ronda 2: el análisis es de texto y no entiende comillas; queda como límite declarado.
    _workflow(tmp_path, "comillas.yml", 'run: kubectl --namespace "a b" apply -f x\n')
    assert guardia.comprobar(tmp_path) == []
    assert any("comillas" in limitacion for limitacion in guardia.LIMITACIONES)
    assert any("variable" in limitacion for limitacion in guardia.LIMITACIONES)
