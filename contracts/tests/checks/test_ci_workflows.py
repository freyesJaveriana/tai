"""Guardia de la CI: ningún workflow aplica cambios al clúster (security-design §4.11 y §4.13, AUTONOMIA-01).

`checks/ci_workflows.py` falla si un workflow de `.github/workflows/` contiene `--write`, `kubectl apply`,
`helm install`, `helm upgrade` o credenciales del clúster (`kubeconfig`, `KUBECONFIG`), si una acción no va
fijada por SHA de 40 caracteres (o `docker://` por digest) o si el workflow no declara `permissions:
contents: read` en la raíz o usa `contents: write` o `write-all` en cualquier nivel (U01-T22b, K-70).
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


PERMISOS_OK = "permissions:\n  contents: read\n"
SHA = "3d3c42e5aac5ba805825da76410c181273ba90b1"
DIGEST = "a" * 64


def _wf(pasos: str, cabecera: str = PERMISOS_OK, job_extra: str = "") -> str:
    """Un workflow mínimo y válido; los pasos empiezan en la línea 8 (con cabecera) y el nombre en la 1."""
    return f"name: x\n{cabecera}jobs:\n  j:\n    runs-on: ubuntu-24.04\n{job_extra}    steps:\n{pasos}"


def test_los_workflows_reales_no_aplican_cambios_ni_tienen_credenciales(guardia: ModuleType) -> None:
    nombres = [ruta.name for ruta in guardia.workflows(REPO_ROOT)]
    assert "repo-level0.yml" in nombres, "la guardia no pasa en vacío"
    assert "contracts-level0.yml" in nombres, "la guardia no pasa en vacío"
    assert guardia.comprobar(REPO_ROOT) == []


def test_la_regla_cita_team_md_deployment(guardia: ModuleType) -> None:
    assert "team.md, Deployment" in guardia.REGLA


@pytest.mark.parametrize(
    "uses",
    [
        "actions/checkout@v4",
        "actions/checkout@main",
        f"actions/checkout@{SHA[:39]}",
        f"actions/checkout@{SHA.upper()}",
        "actions/checkout",
        f"actions/checkout@{SHA}0",
        "docker://alpine:3.20",
        f"docker://alpine@sha256:{DIGEST[:63]}",
    ],
)
def test_una_accion_sin_fijar_por_sha_es_roja(guardia: ModuleType, tmp_path: Path, uses: str) -> None:
    ruta = _workflow(tmp_path, "malo.yml", _wf(f"      - uses: {uses}\n"))
    esperado = f"{ruta.as_posix()}:8: acción sin fijar por SHA: {uses} {guardia.REGLA}"
    assert guardia.comprobar(tmp_path) == [esperado]


def test_una_accion_entre_comillas_o_en_un_comentario(guardia: ModuleType, tmp_path: Path) -> None:
    pasos = '      - uses: "actions/checkout@v4"\n      # uses: actions/checkout@v4\n'
    ruta = _workflow(tmp_path, "comillas.yml", _wf(pasos))
    assert guardia.comprobar(tmp_path) == [f"{ruta.as_posix()}:8: acción sin fijar por SHA: actions/checkout@v4 {guardia.REGLA}"]


@pytest.mark.parametrize(
    ("paso", "linea"),
    [
        ("      - uses:\n          actions/checkout@v4\n", 9),
        ('      - "uses": actions/checkout@v4\n', 8),
        ("      - uses : actions/checkout@v4\n", 8),
        ("      - {uses: actions/checkout@v4}\n", 8),
        ("      - uses: >-\n          actions/checkout@v4\n", 9),
        ("      - 'uses': 'actions/checkout@v4'\n", 8),
    ],
)
def test_f01_toda_forma_de_escribir_uses_se_lee_del_yaml_cargado(
    guardia: ModuleType, tmp_path: Path, paso: str, linea: int
) -> None:
    # F-01 de la ronda 1: el valor en otra línea, la clave entre comillas, el espacio antes de los dos puntos
    # y el flujo son YAML válido y fijaban la acción por etiqueta sin que la guardia lo viera.
    ruta = _workflow(tmp_path, "forma.yml", _wf(paso))
    assert guardia.comprobar(tmp_path) == [
        f"{ruta.as_posix()}:{linea}: acción sin fijar por SHA: actions/checkout@v4 {guardia.REGLA}"
    ]


def test_f01_una_accion_cuyo_texto_no_aparece_en_el_archivo_se_reporta_sin_linea(
    guardia: ModuleType, tmp_path: Path
) -> None:
    # El escape YAML `\x40` construye `@`: el valor cargado no está escrito tal cual en ninguna línea.
    ruta = _workflow(tmp_path, "escape.yml", _wf('      - uses: "actions/checkout\\x40v4"\n'))
    assert guardia.comprobar(tmp_path) == [
        f"{ruta.as_posix()}: acción sin fijar por SHA: actions/checkout@v4 {guardia.REGLA}"
    ]


def test_f01_varias_acciones_se_reportan_en_el_orden_del_archivo_con_su_linea(
    guardia: ModuleType, tmp_path: Path
) -> None:
    pasos = f"      - uses: actions/checkout@{SHA}\n      - uses: a/b@v1\n      - uses: a/b@v1\n"
    ruta = _workflow(tmp_path, "varias.yml", _wf(pasos))
    assert guardia.comprobar(tmp_path) == [
        f"{ruta.as_posix()}:9: acción sin fijar por SHA: a/b@v1 {guardia.REGLA}",
        f"{ruta.as_posix()}:10: acción sin fijar por SHA: a/b@v1 {guardia.REGLA}",
    ]


@pytest.mark.parametrize(
    ("cabecera", "alcances"),
    [
        ("permissions:\n  contents: read\n  packages: write\n", "packages"),
        ("permissions:\n  contents: read\n  id-token: write\n  packages: write\n", "id-token, packages"),
    ],
)
def test_p_t22b_2_la_raiz_con_escritura_de_otro_alcance_es_roja(
    guardia: ModuleType, tmp_path: Path, cabecera: str, alcances: str
) -> None:
    ruta = _workflow(tmp_path, "raiz.yml", _wf("      - run: echo hola\n", cabecera=cabecera))
    assert guardia.comprobar(tmp_path) == [
        f"{ruta.as_posix()}: la raíz declara escritura ({alcances}); solo un job puede tenerla {guardia.REGLA}"
    ]


def test_f05_el_sha_no_se_contrasta_con_el_comentario_es_una_limitacion_declarada(
    guardia: ModuleType, tmp_path: Path
) -> None:
    # Un SHA bien formado pasa aunque el comentario diga otra versión: comprobarlo necesita red (K-70).
    _workflow(tmp_path, "comentario.yml", _wf(f"      - uses: actions/checkout@{SHA} # v1.0.0, no es esa\n"))
    assert guardia.comprobar(tmp_path) == []
    assert any("versión del comentario" in limitacion for limitacion in guardia.LIMITACIONES)
    assert len(guardia.LIMITACIONES) == 3


@pytest.mark.parametrize(
    "uses",
    [
        "./",
        "./.github/actions/local",
        f"docker://alpine@sha256:{DIGEST}",
        f"actions/checkout@{SHA}",
        f"dueno/repo/ruta/interna@{SHA}",
    ],
)
def test_una_accion_fijada_o_local_pasa(guardia: ModuleType, tmp_path: Path, uses: str) -> None:
    _workflow(tmp_path, "bueno.yml", _wf(f"      - uses: {uses} # v1\n"))
    assert guardia.comprobar(tmp_path) == []


@pytest.mark.parametrize(
    ("cabecera", "texto"),
    [
        ("", "falta `permissions: contents: read` en la raíz"),
        ("permissions:\n  contents: write\n", "la raíz declara permisos distintos de `contents: read`"),
        ("permissions: write-all\n", "la raíz declara permisos distintos de `contents: read`"),
        ("permissions: read-all\n", "la raíz declara permisos distintos de `contents: read`"),
        ("permissions:\n  packages: read\n", "la raíz declara permisos distintos de `contents: read`"),
    ],
)
def test_la_raiz_sin_contents_read_es_roja(guardia: ModuleType, tmp_path: Path, cabecera: str, texto: str) -> None:
    ruta = _workflow(tmp_path, "permisos.yml", _wf("      - run: echo hola\n", cabecera=cabecera))
    assert guardia.comprobar(tmp_path) == [f"{ruta.as_posix()}: {texto} {guardia.REGLA}"]


@pytest.mark.parametrize(
    "job_extra",
    [
        "    permissions:\n      contents: write\n",
        "    permissions: write-all\n",
    ],
)
def test_un_job_con_contents_write_o_write_all_es_rojo(guardia: ModuleType, tmp_path: Path, job_extra: str) -> None:
    ruta = _workflow(tmp_path, "job.yml", _wf("      - run: echo hola\n", job_extra=job_extra))
    assert guardia.comprobar(tmp_path) == [
        f"{ruta.as_posix()}: `contents: write` o `write-all` no se permite en ningún nivel {guardia.REGLA}"
    ]


def test_un_job_con_packages_write_y_raiz_de_lectura_pasa(guardia: ModuleType, tmp_path: Path) -> None:
    job_extra = "    permissions:\n      packages: write\n      contents: read\n"
    _workflow(tmp_path, "build.yml", _wf("      - run: echo hola\n", job_extra=job_extra))
    assert guardia.comprobar(tmp_path) == []


@pytest.mark.parametrize("texto", ["jobs: [\n", "a: 1\na: 2\n"])
def test_un_yaml_que_no_carga_es_un_problema_y_no_un_salto(guardia: ModuleType, tmp_path: Path, texto: str) -> None:
    ruta = _workflow(tmp_path, "roto.yml", texto)
    problemas = guardia.comprobar(tmp_path)
    assert len(problemas) == 1
    assert problemas[0].startswith(f"{ruta.as_posix()}: no se puede cargar: ")
    assert problemas[0].endswith(guardia.REGLA)


@pytest.mark.parametrize("texto", ["", "solo texto\n"])
def test_un_workflow_que_no_es_un_mapa_no_declara_permisos(guardia: ModuleType, tmp_path: Path, texto: str) -> None:
    ruta = _workflow(tmp_path, "vacio.yml", texto)
    assert guardia.comprobar(tmp_path) == [
        f"{ruta.as_posix()}: falta `permissions: contents: read` en la raíz {guardia.REGLA}"
    ]


@pytest.mark.parametrize(
    ("linea", "termino"),
    [
        ("run: kubectl apply -f deploy/", "kubectl apply"),
        ("run: kubectl   apply -f deploy/", "kubectl apply"),
        ("run: KUBECTL APPLY -f deploy/", "kubectl apply"),
        ("run: helm install veridicus charts/x", "helm install"),
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
    ruta = _workflow(tmp_path, "malo.yml", f"name: x\njobs:\n  j:\n    steps:\n      - {linea}\n{PERMISOS_OK}")
    problemas = guardia.scan([ruta])
    assert problemas == [f"{ruta.as_posix()}:5: {termino} no se permite en un workflow {guardia.REGLA}"]
    assert guardia.comprobar(tmp_path) == problemas


def test_un_tabulador_entre_helm_y_upgrade_se_detecta_aunque_el_yaml_no_cargue(
    guardia: ModuleType, tmp_path: Path
) -> None:
    # El escáner de comandos es de texto; el YAML con tabulador no carga y eso es otro problema, no un salto.
    ruta = _workflow(tmp_path, "tab.yml", f"name: x\njobs:\n  j:\n    steps:\n      - run: helm\tupgrade a\n{PERMISOS_OK}")
    assert guardia.scan([ruta]) == [f"{ruta.as_posix()}:5: helm upgrade no se permite en un workflow {guardia.REGLA}"]


def test_un_workflow_con_kubectl_apply_en_un_comentario_tambien_es_rojo(guardia: ModuleType, tmp_path: Path) -> None:
    _workflow(tmp_path, "comentario.yaml", f"# antes: kubectl apply -f x\nname: x\n{PERMISOS_OK}")
    assert len(guardia.comprobar(tmp_path)) == 1


def test_un_workflow_limpio_y_las_lecturas_de_kubectl_pasan(guardia: ModuleType, tmp_path: Path) -> None:
    pasos = "      - run: helm template charts/x\n      - run: kubectl get pods\n"
    _workflow(tmp_path, "limpio.yml", _wf(pasos))
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
    _workflow(tmp_path, "lectura.yml", f"name: x\njobs:\n  j:\n    steps:\n      - {linea}\n{PERMISOS_OK}")
    assert guardia.comprobar(tmp_path) == []


def test_varias_apariciones_se_reportan_en_orden_de_archivo_y_linea(guardia: ModuleType, tmp_path: Path) -> None:
    _workflow(tmp_path, "b.yml", f"x: helm install a\ny: kubectl apply -f x --write\n{PERMISOS_OK}")
    _workflow(tmp_path, "a.yml", f"x: helm upgrade a\n{PERMISOS_OK}")
    problemas = guardia.comprobar(tmp_path)
    assert [p.rsplit("/", 1)[1].split(" ", 1)[0] for p in problemas] == ["a.yml:1:", "b.yml:1:", "b.yml:2:", "b.yml:2:"]
    assert all(p.endswith(guardia.REGLA) for p in problemas)


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
    _workflow(tmp_path, "comillas.yml", f'run: kubectl --namespace "a b" apply -f x\n{PERMISOS_OK}')
    assert guardia.comprobar(tmp_path) == []
    assert any("comillas" in limitacion for limitacion in guardia.LIMITACIONES)
    assert any("variable" in limitacion for limitacion in guardia.LIMITACIONES)
