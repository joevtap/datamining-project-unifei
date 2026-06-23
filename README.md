# Mineração de Dados — Eventos Adversos a Medicamentos (OpenFDA)

Projeto da disciplina de Mineração de Dados (UNIFEI), seguindo o processo **CRISP-DM**.
A partir de relatórios de eventos adversos a medicamentos da **OpenFDA** (FAERS), o
objetivo é prever se um evento é **grave** (`serious`), passando por preparação dos
dados, transformação/engenharia de atributos e um **Design de Experimentos (DoE)** com
modelos de árvore na Entrega 3.

## Pré-requisitos

- [`uv`](https://docs.astral.sh/uv/) (gerenciador de pacotes/ambiente)
- Python ≥ 3.14 (o `uv` resolve/instala automaticamente)

## Setup

```bash
# Instala as dependências (inclui o grupo dev: ijson, nbclient, ipykernel)
uv sync

# Registra o kernel Jupyter dentro do próprio .venv
uv run python -m ipykernel install --prefix .venv --name python3
```

No **VS Code** ou **Jupyter**, basta abrir os notebooks e selecionar o interpretador/kernel
do `.venv` (exibido como *"Python (datamining .venv)"*).

## Dados (não versionados)

Os arquivos de dados são grandes e estão no `.gitignore` — coloque-os manualmente:

| Pasta | Conteúdo | Versionado? |
|-------|----------|-------------|
| `datasets/` | JSON brutos da OpenFDA usados em treino/teste | não |
| `validation/` | JSON brutos (mesmo formato) para validação final | não |
| `outputs/` | Artefatos gerados (CSVs, metadados, PDF) | sim (exceto `models/`) |
| `outputs/models/` | Modelos treinados `*.joblib` — **regeneráveis** rodando o nb05 | não |

## Ordem de execução dos notebooks (`notebooks/`)

Execute na ordem; cada notebook consome saídas do anterior (todas em `outputs/`).

| # | Notebook | Papel | Principais saídas |
|---|----------|-------|-------------------|
| 01 | `01_data_preparation.ipynb` | Limpeza, normalização e agregação por `safetyreportid` | `drug_events_cleaned.csv` |
| 02 | `02_entrega2_transformacao.ipynb` | Split 70/30 estratificado, imputação KNN da faixa etária, *feature engineering*, padronização (fit só no treino) | `drug_events_{train,test}_transformed.csv`, `data_preparation_metadata.json` |
| 03 | `03_visualizacao_outputs_entrega2.ipynb` | Visualizações da Entrega 2 | — |
| 04 | `04_design_experimentos_entrega3.ipynb` | Planejamento do DoE (não treina modelos) | — |
| 05 | `05_execucao_doe_arvores_entrega3.ipynb` | Executa EXP-02/03/05/06 (Random Forest e Gradient Boosting) | `cv_results_EXP-0X.csv`, `resumo_experimentos_arvores.csv`, `models/*.joblib` |
| 06 | `06_validacao_entrega3.ipynb` | Valida os modelos treinados contra `validation/*.json` (sem vazamento) | `drug_events_validation_*.csv`, `metricas_validacao.csv`, `comparacao_teste_validacao.csv` |

## Notas importantes

- **`MODO_RAPIDO`** (célula de configuração do nb05): `True` usa grades de hiperparâmetros
  reduzidas e `cv=3`, para uma execução rápida de demonstração. Para os resultados
  **oficiais** (Tabela 1 do PDF, `cv=5`), use `MODO_RAPIDO = False` — execução bem mais
  custosa.
- A **Regressão Logística** (EXP-01/EXP-04) está **adiada** para uma etapa posterior —
  apenas documentada no nb05.
- O **nb06 depende dos modelos `.joblib` gerados pelo nb05** (que não são versionados).
  Em um clone novo, **rode o nb05 antes** do nb06.
- O nb06 lê os JSON de validação em **streaming** (`ijson`) para não estourar a memória,
  e reaplica os parâmetros do treino (imputador KNN re-ajustado só no treino, scaler de
  `data_preparation_metadata.json`) — **sem vazamento**.

## Execução headless (opcional)

Para executar um notebook fora da interface, via `nbclient`:

```bash
uv run python - <<'PY'
import nbformat
from nbclient import NotebookClient
nb_path = "notebooks/05_execucao_doe_arvores_entrega3.ipynb"
nb = nbformat.read(nb_path, as_version=4)
NotebookClient(nb, timeout=2400, kernel_name="python3",
               resources={"metadata": {"path": "notebooks"}}).execute()
nbformat.write(nb, nb_path)
print("OK ->", nb_path)
PY
```
