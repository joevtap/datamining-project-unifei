# Design da Entrega 3 - Design de Experimentos

## Objetivo

Preparar o Design de Experimentos da etapa de Modelagem e Avaliacao do projeto de Mineracao de Dados, sem executar o treinamento dos modelos. O desenho deve seguir a hierarquia exigida no enunciado:

Features -> Modelo -> Hiperparametros -> Metricas de Avaliacao

## Contexto do Projeto

O projeto ja possui a base limpa e transformada da Entrega 2 em `outputs/`. Os arquivos principais para a Entrega 3 sao:

- `outputs/drug_events_train_transformed.csv`
- `outputs/drug_events_test_transformed.csv`
- `outputs/data_preparation_metadata.json`

A variavel alvo e `serious`, tratada como problema de classificacao binaria. No conjunto de treino, a distribuicao observada e moderadamente desbalanceada:

- `serious = 1`: 62,3%
- `serious = 2`: 37,7%

Por isso, o DoE deve priorizar metricas robustas a desbalanceamento moderado, como `f1_macro` e `balanced_accuracy`, mantendo tambem acuracia, precisao, revocacao e ROC-AUC quando o modelo permitir probabilidades ou funcao de decisao.

## Abordagem Escolhida

Serao criados dois artefatos:

1. Um notebook `notebooks/04_design_experimentos_entrega3.ipynb`, contendo o planejamento reprodutivel do DoE em Python, com definicao de subconjuntos de atributos, modelos, espacos de hiperparametros, validacao cruzada estratificada e estrutura de armazenamento de resultados esperados.
2. Uma secao LaTeX `secao_design_experimentos_entrega3.tex`, pronta para insercao no relatorio.

O notebook deve preparar os objetos e tabelas do experimento, mas nao deve chamar `fit`, `GridSearchCV.fit`, `RandomizedSearchCV.fit` ou qualquer rotina que treine modelos. Essa restricao sera explicitada no proprio notebook.

## Subconjuntos de Atributos

O DoE comparara tres conjuntos de atributos:

- `F1_basico_clinico`: atributos demograficos e clinicos ja tratados.
- `F2_medicamentos_estruturado`: `F1` acrescido de atributos estruturados de medicamentos.
- `F3_completo_com_texto`: `F2` acrescido de atributos textuais agregados de substancia ativa e produto medicinal.

Essa progressao permite avaliar o ganho incremental dos atributos de medicamento e texto, mantendo a hierarquia experimental exigida.

## Modelos

O DoE usara modelos de classificacao com perfis distintos:

- Regressao Logistica: baseline linear interpretavel.
- Arvore de Decisao: baseline nao linear simples.
- Random Forest: ensemble nao linear robusto.
- Gradient Boosting: ensemble sequencial para comparar com Random Forest.
- SVM: margem maxima, testando fronteiras lineares e nao lineares.

Todos os modelos serao definidos em pipelines do scikit-learn para manter consistencia entre pre-processamento, validacao cruzada e busca de hiperparametros.

## Hiperparametros

Cada modelo tera um grid ou distribuicao de parametros documentado. A busca planejada sera feita com `GridSearchCV` para espacos pequenos e `RandomizedSearchCV` para espacos maiores, conforme o custo computacional esperado.

## Avaliacao

O planejamento documentara as metricas para treino, validacao cruzada e teste:

- `accuracy`
- `balanced_accuracy`
- `precision_macro`
- `recall_macro`
- `f1_macro`
- `roc_auc`

A metrica primaria para selecao sera `f1_macro`, por equilibrar o desempenho entre as classes em um cenario de desbalanceamento moderado.

## Saidas Esperadas

A etapa entregara somente o planejamento:

- tabela de feature sets;
- tabela de modelos;
- tabela de hiperparametros;
- estrutura de execucao futura com `GridSearchCV` ou `RandomizedSearchCV`;
- modelo de tabela de resultados para treino e teste;
- texto LaTeX explicando o desenho experimental.

Nenhum modelo sera treinado nesta entrega.
