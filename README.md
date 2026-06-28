# Mineração de Dados — Eventos Adversos a Medicamentos (OpenFDA)

Projeto da disciplina de Mineração de Dados (UNIFEI), seguindo o processo **CRISP-DM**.
A partir de relatórios de eventos adversos a medicamentos da **OpenFDA / FAERS** (FDA
Adverse Event Reporting System), o objetivo é **prever a gravidade** de um relatório —
o atributo `serious` (`1` = grave, `2` = não-grave), um problema de **classificação
binária** com classes **desbalanceadas** (~62% / 38% no treino).

Todo o fluxo está consolidado em um único notebook — **`notebooks/00_pipeline_completo.ipynb`** —
que vai do JSON bruto até a avaliação em dados nunca vistos.

## Resultado principal

DoE com **6 experimentos** (3 modelos × 2 conjuntos de atributos), seleção por `f1_macro`:

| Melhor modelo | Teste (30%) | Validação (nunca vista) |
|---------------|-------------|--------------------------|
| **EXP-05 — Random Forest · Completo (17 atributos)** | F1-macro **0,825** · ROC AUC **0,909** | F1-macro **0,783** · ROC AUC **0,866** |

- O conjunto **Completo** (com engenharia de atributos) supera o **Baseline** nos três modelos.
- **Gradient Boosting · Completo (EXP-06)** fica praticamente empatado com o melhor.
- A **Regressão Logística** é competitiva e a que **melhor generaliza** (menor diferença
  treino→teste). Tabelas completas em `outputs/` e na apresentação.

## Pré-requisitos

- [`uv`](https://docs.astral.sh/uv/) (gerenciador de pacotes/ambiente)
- Python ≥ 3.14 (o `uv` resolve/instala automaticamente)

## Setup

```bash
uv sync                                              # instala dependências (+ grupo dev)
uv run python -m ipykernel install --user --name python3   # registra o kernel Jupyter
```

No **VS Code** ou **Jupyter**, abra os notebooks e selecione o kernel do `.venv`.

## Estrutura do repositório

```
notebooks/00_pipeline_completo.ipynb  # pipeline CRISP-DM completo (PRINCIPAL)
notebooks/inferencia_modelos.ipynb    # aplicar modelos salvos a dados nunca vistos (autocontido)
scripts/                              # execução remota (EC2) e geração de gráficos
apresentacao/                         # apresentação (HTML), roteiro e imagens
outputs/                              # resultados (CSVs); models/ é regenerável
datasets/ , validation/               # dados brutos OpenFDA (NÃO versionados)
```

## Dados (não versionados)

São grandes (~2,8 GB) e estão no `.gitignore`; coloque-os manualmente:

| Pasta | Conteúdo | Versionado? |
|-------|----------|-------------|
| `datasets/` | JSON brutos da OpenFDA para treino/teste (~1,6 GB) | não |
| `validation/` | JSON brutos (mesmo formato) para validação final (~1,2 GB) | não |
| `outputs/` | Artefatos gerados (CSVs) | sim (exceto `models/`, parquet e `_progress.log`) |
| `outputs/models/` | Modelos treinados `*.joblib` — **regeneráveis** rodando o `00_pipeline_completo` | não |

> Os arquivos têm nomes no padrão OpenFDA (`drug-event-0001-of-0028.json`, etc.).

## Notebook principal — `notebooks/00_pipeline_completo.ipynb`

Executa todo o CRISP-DM de ponta a ponta:

1. **Ingestão** dos JSON em *streaming* (`ijson`) → Parquet.
2. **Transformação** em Polars *lazy* (limpeza, faixa etária, *feature engineering*).
3. **Imputação KNN** da faixa etária faltante (ajustada só no treino).
4. **Split** estratificado 70/30 em `serious`.
5. **Balanceamento por SMOTE** + **DoE** (Regressão Logística, Random Forest, Gradient
   Boosting × Baseline/Completo = EXP-01…EXP-06).
6. **Avaliação** no teste e **validação** contra `validation/*.json` (sem vazamento).

Variáveis de ambiente (lidas pelo notebook):

| Variável | Padrão | Efeito |
|----------|--------|--------|
| `MODO_RAPIDO` | `true` | `true`: grades reduzidas + `cv=3` (demonstração). `false`: grades completas + `cv=5` (run oficial, mais custoso). |
| `REUSE_TRAINED` | `true` | Se já houver modelo treinado em `outputs/models/`, **reaproveita** (pula a busca de hiperparâmetros) e refaz só a avaliação. |

Acompanhamento ao vivo: o notebook grava `outputs/_progress.log` (use `tail -f`), pois a
execução headless só descarrega a saída das células ao final.

### Como rodar

```bash
# Interface: abra notebooks/00_pipeline_completo.ipynb e rode todas as células.
# Headless (linha de comando), modo rápido:
MODO_RAPIDO=true uv run python scripts/run_notebook.py
# Run completo (custoso — prefira uma máquina potente / EC2):
MODO_RAPIDO=false uv run python scripts/run_notebook.py
```

## Métodos utilizados

- **Carregamento preguiçoso (lazy) — Polars + streaming.** Os JSON são lidos registro a
  registro com `ijson` (memória O(1), independente do tamanho) e a transformação inteira
  é **uma única *query* Polars** materializada de uma vez em *streaming* — sem DataFrames
  intermediários. Escala para datasets grandes. A modelagem usa um pipeline
  sklearn/imblearn que só executa no `.fit()`.
- **Balanceamento por SMOTE.** O alvo é desbalanceado. Em vez de `class_weight`, usa-se
  **SMOTE** (oversampling sintético baseado em KNN) **dentro** do `imblearn.Pipeline`
  (`ColumnTransformer → SMOTE → modelo`). Ele atua **somente nos *folds* de treino** da
  validação cruzada (nunca no teste/validação) e, com `sampling_strategy="auto"`, equilibra
  qualquer proporção (*dataset-agnóstico*).
- **Imputação KNN da faixa etária.** A faixa etária faltante é prevista por um
  `KNeighborsClassifier` a partir de país, sexo e medicamentos — ajustado **só no treino**
  (registros com faixa conhecida) e aplicado a treino/teste/validação **sem vazamento**.
- **Engenharia de atributos.** 5 *features* derivadas (nº de substâncias/tipos, flags de
  produto/múltiplos medicamentos/EUA) → conjunto **Completo (17)** vs. **Baseline (11)**.
- **DoE e seleção.** `GridSearchCV` (Regressão Logística) e `RandomizedSearchCV` (árvores),
  `StratifiedKFold` `cv=5`, `refit="f1_macro"`, `random_state=42`. Métricas de **rótulo**
  (`predict`) para acurácia/precisão/recall/F1 e de **probabilidade** (`predict_proba`)
  para ROC AUC.

## Reproduzir os resultados

```bash
uv sync
# coloque os dados em datasets/ e validation/ (ver tabela acima)

# (a) validar o pipeline rapidamente
MODO_RAPIDO=true uv run python scripts/run_notebook.py

# (b) resultados oficiais (custoso — recomenda-se EC2, ver abaixo)
MODO_RAPIDO=false uv run python scripts/run_notebook.py
```

Saídas em `outputs/`: `resumo_experimentos_arvores.csv` (6 experimentos),
`metricas_validacao.csv`, `comparacao_teste_validacao.csv`, `cv_results_EXP-0X.csv` e
`models/*.joblib`. Gráficos da apresentação:
`uv run python scripts/make_presentation_charts.py`.

## Usar os modelos em dados de validação (nunca vistos)

Há dois caminhos para aplicar os modelos **já treinados** a dados que eles nunca viram:

1. **Notebook dedicado — `notebooks/inferencia_modelos.ipynb` (recomendado).**
   Autocontido: carrega um modelo de `outputs/models/`, reaplica a mesma transformação do
   pipeline e o **imputador KNN ajustado só no treino**, e pontua os JSON de uma
   pasta (padrão `validation/`). Reporta as métricas quando há gabarito (`serious`) e salva
   `outputs/predicoes_inferencia.csv`. Use `MAX_RECORDS` para um teste rápido. As colunas
   de entrada são lidas do próprio pipeline (`feature_names_in_`), então o conjunto certo
   (Baseline/Completo) é escolhido automaticamente.

2. **Reaproveitando o `00_pipeline_completo`.** Com os modelos presentes e `REUSE_TRAINED=true`
   (padrão), rodar o `00_pipeline_completo` **não retreina** — ele carrega os modelos, pula a busca e
   reavalia, inclusive na validação, regravando `metricas_validacao.csv`.

> Pontuar dados brutos exige reingerir/transformar os JSON-alvo (a validação tem ~1,2 GB);
> para tudo de uma vez, prefira uma máquina potente / EC2.

## Execução na nuvem (AWS EC2)

O run completo (`MODO_RAPIDO=false`) é **CPU/RAM-bound** (parse JSON, KNN, SMOTE,
`RandomizedSearchCV`): o que importa é **muitos vCPUs**, não GPU. Este projeto foi
executado em uma instância **`c7i.4xlarge`** (16 vCPU / 32 GB RAM, ~50 GB de disco,
Ubuntu) — suficiente para o DoE completo em poucas dezenas de minutos. Instâncias *spot*
reduzem o custo.

Os scripts em `scripts/` usam a **chave `.pem`** via variável `SSH_KEY` e fazem o
*bootstrap* completo — uma EC2 nova pode vir **sem uv, sem python e até sem rsync**; os
scripts instalam o que falta (o `uv` traz o próprio Python 3.14).

| Script | Onde roda | Papel |
|--------|-----------|-------|
| `deploy_code.sh user@host` | local | Envia o código via rsync (dispensa git na EC2) |
| `upload_data.sh user@host` | local | Envia `datasets/` + `validation/` (~2,8 GB), resumível |
| `run_cloud.sh` | EC2 | Instala uv, `uv sync`, registra o kernel e executa o notebook |
| `run_notebook.py` | EC2/local | Executor headless (nbclient) |
| `fetch_outputs.sh user@host` | local | Traz `outputs/` e o notebook executado de volta |

> Usuário SSH padrão do EC2: **`ubuntu`** (Ubuntu) ou **`ec2-user`** (Amazon Linux).

**Passo a passo:**

```bash
# Defina a chave e o destino (ajuste o caminho da .pem e o host).
export SSH_KEY=~/Downloads/minha-chave.pem
export HOST=ubuntu@SEU-IP-OU-DNS
export SSH_OPTS="-o StrictHostKeyChecking=accept-new"   # evita prompt de host key

# 1. Lance uma c7i.4xlarge (Ubuntu, ~50 GB EBS) e libere a porta 22 (SSH) para o seu IP.

# 2. Da SUA máquina: envie o código e os dados (~2,8 GB)
bash scripts/deploy_code.sh "$HOST"
bash scripts/upload_data.sh "$HOST"

# 3. Na EC2: rode em tmux (o run completo é longo e sobrevive a quedas de SSH)
ssh -i "$SSH_KEY" "$HOST"
cd ~/datamining-project-unifei
tmux new -s run
MODO_RAPIDO=false bash scripts/run_cloud.sh
#   (validar o setup antes? MODO_RAPIDO=true bash scripts/run_cloud.sh)
#   Ctrl-b d destaca o tmux; tail -f outputs/_progress.log acompanha o progresso

# 4. Da SUA máquina: traga os resultados de volta
bash scripts/fetch_outputs.sh "$HOST"

# 5. Lembre-se de ENCERRAR a instância EC2 depois (evita custo).
```

> **Dica de tuning:** com muitos núcleos, `RandomizedSearchCV(n_jobs=-1)` aninhado a
> `RandomForest(n_jobs=-1)` pode causar *oversubscription*; se notar contenção, limite o
> `n_jobs` de um dos níveis.

## Apresentação

`apresentacao/apresentacao.html` — deck HTML autocontido (11 slides,
16:9; setas/espaço/swipe para navegar). Roteiro do apresentador em
`roteiro_apresentador.md`; gráficos em `img/` (gerados por
`scripts/make_presentation_charts.py`).

> Histórico: o fluxo original era dividido em notebooks por entrega (preparação,
> transformação, DoE de árvores, validação). O **`00_pipeline_completo`** consolidou e
> modernizou tudo (lazy + SMOTE + DoE completo com Regressão Logística); a evolução
> anterior permanece no histórico de commits do git.

## Execução headless (genérica)

```bash
NOTEBOOK=notebooks/00_pipeline_completo.ipynb MODO_RAPIDO=false uv run python scripts/run_notebook.py
```
