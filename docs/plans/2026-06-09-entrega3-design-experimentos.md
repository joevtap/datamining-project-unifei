# Entrega 3 Design de Experimentos Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Criar os artefatos da Entrega 3 com o planejamento do Design de Experimentos, sem executar treinamento de modelos.

**Architecture:** A entrega sera documentada em um notebook reprodutivel e em uma secao LaTeX para relatorio. O notebook define feature sets, modelos, hiperparametros, metricas e estrutura futura de execucao com `GridSearchCV` e `RandomizedSearchCV`, mas nao chama nenhum metodo de treino.

**Tech Stack:** Python 3.14, pandas, scikit-learn, Jupyter Notebook, LaTeX.

---

### Task 1: Notebook do Design de Experimentos

**Files:**
- Create: `notebooks/04_design_experimentos_entrega3.ipynb`

**Step 1: Criar notebook com contexto da etapa**

Adicionar celulas Markdown explicando que a Entrega 3 prepara o DoE das fases CRISP-DM de Modelagem e Avaliacao, seguindo a hierarquia:

```text
Features -> Modelo -> Hiperparametros -> Metricas de Avaliacao
```

**Step 2: Carregar metadados basicos sem treinar modelos**

Adicionar celulas Python para importar bibliotecas, localizar `outputs/`, carregar amostras/colunas dos CSVs transformados e calcular distribuicao da variavel alvo.

**Step 3: Definir feature sets**

Criar dicionario `feature_sets` com:

- `F1_basico_clinico`
- `F2_medicamentos_estruturado`
- `F3_completo_com_texto`

**Step 4: Definir modelos candidatos**

Criar dicionario `model_specs` com Regressao Logistica, Arvore de Decisao, Random Forest, Gradient Boosting e SVM.

**Step 5: Definir metricas e validacao cruzada**

Configurar `StratifiedKFold` e dicionario `scoring` com `accuracy`, `balanced_accuracy`, `precision_macro`, `recall_macro`, `f1_macro` e `roc_auc`.

**Step 6: Definir blueprint de busca**

Criar uma lista `experiment_blueprint` que combine cada feature set com cada modelo e documente o tipo de busca planejado (`GridSearchCV` ou `RandomizedSearchCV`), sem executar `.fit()`.

**Step 7: Criar tabela modelo de resultados**

Gerar `results_template` com colunas para feature set, modelo, busca, melhores hiperparametros, metricas de treino, validacao cruzada e teste.

**Step 8: Validar que o notebook abre como JSON**

Run:

```bash
python -m json.tool notebooks/04_design_experimentos_entrega3.ipynb
```

Expected: o comando termina sem erro de JSON.

### Task 2: Secao LaTeX

**Files:**
- Create: `secao_design_experimentos_entrega3.tex`

**Step 1: Escrever secao de planejamento experimental**

Adicionar uma secao em portugues descrevendo objetivo, hierarquia experimental, feature sets, modelos, hiperparametros, metricas e criterio de selecao.

**Step 2: Incluir tabelas sinteticas**

Adicionar tabelas LaTeX para:

- subconjuntos de atributos;
- modelos e hiperparametros;
- metricas planejadas.

**Step 3: Reforcar que a etapa nao executa modelos**

Adicionar paragrafo final informando que a execucao sera feita em etapa posterior, mantendo a Entrega 3 restrita ao planejamento do DoE.

### Task 3: Validacao Final

**Files:**
- Read: `notebooks/04_design_experimentos_entrega3.ipynb`
- Read: `secao_design_experimentos_entrega3.tex`
- Read: `docs/plans/2026-06-09-entrega3-design-experimentos-design.md`

**Step 1: Confirmar arquivos criados**

Run:

```bash
git status --short
```

Expected: os novos arquivos aparecem como untracked ou modified.

**Step 2: Verificar ausencia de execucao de treino**

Run:

```bash
rg "\.fit\(|GridSearchCV\(.*\.fit|RandomizedSearchCV\(.*\.fit" notebooks/04_design_experimentos_entrega3.ipynb
```

Expected: nenhuma chamada real de treino; se houver texto explicativo, deve estar claramente como exemplo nao executado.

**Step 3: Revisar consistencia dos nomes**

Garantir que os nomes dos arquivos `outputs/drug_events_train_transformed.csv` e `outputs/drug_events_test_transformed.csv` estejam iguais aos artefatos existentes.
