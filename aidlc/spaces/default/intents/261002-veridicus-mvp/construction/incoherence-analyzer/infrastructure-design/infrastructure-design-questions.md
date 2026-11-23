# Preguntas de Infrastructure Design — U11 incoherence-analyzer

**Unidad.** U11 `incoherence-analyzer` (tipo `library`, MUST, XL): la biblioteca `libs/incoherence_analyzer/`
con su línea de comandos `veridicus`, `libs/model_gateway/`, `libs/execution_profiles/`,
`libs/integrity_policy/`, el arnés y el conjunto sintético de `evaluation/` y los `.sbatch` de
`evaluation/zine/`. No despliega nada propio: corre dentro de la CLI (máquina del humano o nodo de ZINE) y
dentro de `semantic-agent` (U4). Primera pasada de esta etapa para U11 (revisión 1, 2026-11-23).

# Segunda pasada — cambio 01, adenda 02 y NFR Design revisión vigente (2026-11-23)

> El título sigue la convención de esta etapa para todas las unidades. Para U11 es la primera pasada:
> la unidad nació con el cambio 01 y no tiene revisión anterior de Infrastructure Design.

## Lo que ya está decidido

- **Tipo `library`.** El archivo de etapa (`produces_kinds`) le pide a una `library` solo `cicd-pipeline.md`
  y `traceability.json`. La máquina donde corre la CLI, ZINE y la frontera de datos van como secciones de
  `cicd-pipeline.md` (IDS-U11-01).
- **Sin métricas ni puertos propios** (NFR15.2, `performance-design.md` §7): no hay `monitoring-design.md`;
  lo que se mide queda en el reporte C19 v2.
- **Niveles y compuertas** (`team.md`, `## Testing Posture`): niveles 0 y 1 en cada PR, en CPU y sin red
  (`pytest-socket`); 80 % de líneas por paquete y 100 % de ramas en los siete módulos guardia
  (`reliability-design.md` §6); nivel 2 fuera de la CI, con el reporte adjunto al PR, bloqueante para los PR
  que tocan la IA y para toda entrega etiquetada; solo con `evaluacion-comercial` bloquea (NFR-U11-14).
- **Empaquetado** (D1, D2, `security-design.md` §11): cuatro paquetes con su `pyproject.toml` y `uv.lock` con
  *hashes*; `libs-anonymizer` solo en el *extra* `cli`; la wheelhouse de ZINE sale de `uv export --frozen`;
  ZINE solo usa perfiles locales (BR14.2) y la instalación es sin internet (BR14.5, AC14.2.5, M5 con Python
  3.12.16).
- **Frontera** (IDS-U10-09, `security-design.md` §1): en la CLI el módulo de U10 corre en el mismo proceso y
  la única barrera en la máquina del humano es la del proceso; en ZINE no interviene el anonimizador.
- **Supuesto de máquina** (brief del 2026-11-22; IDS-U2-01 ya decidido): un solo equipo de 64 GB, solo CPU,
  sin máquina GPU; WSL2 con 56 GB y Minikube de 50 GiB. Durante una evaluación de nivel 2 el humano apaga el
  juez de `todo-local` (IDS-U2-11) y el verificador corre en la anfitriona con ≤ 14 GB (NFR2.2).
- **AUTONOMIA-01**: ningún *workflow* ni *script* toca el clúster ni envía trabajos a ZINE.

## Cómo se registra la revisión

Revisión 1 de `cicd-pipeline.md` y `traceability.json` en esta carpeta. Las precisiones a artefactos ya
aprobados y las peticiones a otras unidades son IDS-U11-01 en adelante, en §11 de `cicd-pipeline.md`.

## Lo que el diseño resolverá sin preguntar

- El mecanismo concreto de «reporte adjunto al PR» y su comprobación en la CI (IDS-U11-04).
- Cómo corre el verificador local en la anfitriona durante el nivel 2: la misma imagen de `llama-server` que
  U2 fija por digest, solo en *loopback* y con el archivo del volumen de modelos de U2 (IDS-U11-05).
- Cómo se arma y se prueba la wheelhouse sin el *extra* `cli` (IDS-U11-02, IDS-U11-03).
- La forma de los *workflows* para que sus comprobaciones puedan ser obligatorias aunque filtren por rutas
  (IDS-U11-07) y la sustitución de los *workflows* de la revisión 1 de U4 (IDS-U11-08).

Sin preguntas: todo lo fijan las fuentes.
