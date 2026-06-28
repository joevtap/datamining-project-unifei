# Roteiro do apresentador — Trabalho final (CRISP-DM · Eventos adversos a medicamentos)

Apresentação: `apresentacao_entrega3.html` (11 slides, 16:9). Navegação: setas / espaço /
swipe. Tempo-alvo total: ~10–12 min. Os números vêm do **run completo**
(`MODO_RAPIDO=False`) e estão em `outputs/` — os mesmos exibidos nos slides.

**Lembretes de vocabulário (valem para o deck todo):**
- **Alvo `serious`** (classificação binária): `serious = 1` → evento **grave** (classe
  positiva, ~62% do treino); `serious = 2` → **não-grave**.
- **F1-macro**: média do F1 entre as duas classes — é a **métrica de seleção** por ser
  justa sob desbalanceamento. **ROC AUC** usa a probabilidade (`predict_proba`).

---

## Slide 1 — Capa (~30s)
- Apresentar o tema: prever a **gravidade** (`serious`) de relatórios de eventos adversos
  a medicamentos do FDA (OpenFDA / FAERS).
- Frase-âncora: "um pipeline consolidado, com carregamento preguiçoso, balanceamento por
  SMOTE e um Design de Experimentos de 6 configurações, validado em dados nunca vistos".

## Slide 2 — O problema e os dados (~1min)
- Cada registro = um relatório com paciente + lista de medicamentos.
- Alvo `serious`: **1 = grave**, **2 = não-grave**; **desbalanceado** (~62/38 no treino).
- ~36 mil relatórios; conjunto Completo tem 17 atributos (originais + 5 de engenharia).
- Gancho: "o desbalanceamento motiva o SMOTE; o volume motiva o carregamento preguiçoso".

## Slide 3 — Pipeline CRISP-DM (~1min)
- Percorrer o fluxo: ingestão streaming → transformação lazy → imputação KNN da faixa
  etária → split 70/30 → SMOTE (só no treino) → DoE → validação.
- **Mensagem-chave:** tudo que aprende (KNN, SMOTE, scaler, TF-IDF, modelos) é ajustado
  **só no treino** → **zero vazamento**.

## Slide 4 — Método: carregamento preguiçoso (Polars) (~1min30)
- `ijson` lê registro a registro (memória O(1)); a transformação é **uma única query**
  Polars, materializada uma vez em streaming.
- Benefício: escala para datasets grandes (~2,8 GB) sem materializar etapas intermediárias.
- A modelagem é um pipeline sklearn/imblearn que **só executa no `.fit()`**.

## Slide 5 — Método: SMOTE (~1min30)
- Por que SMOTE e não `class_weight`: sintetiza exemplos da minoria (via KNN) em vez de só
  reponderar a perda.
- Posição no pipeline: `ColumnTransformer → SMOTE → modelo`; com `imblearn.Pipeline` atua
  **só nos folds de treino** (sem vazamento).
- `sampling_strategy="auto"` → dataset-agnóstico. Resultado: treino vai de 14.089/8.527
  para 14.089/14.089.

## Slide 6 — DoE: 6 experimentos (~1min)
- 3 modelos (Regressão Logística, Random Forest, Gradient Boosting) × 2 conjuntos
  (Baseline 11, Completo 17) = EXP-01 a EXP-06.
- LR por `GridSearchCV`; árvores por `RandomizedSearchCV`. Seleção por **f1_macro**,
  `StratifiedKFold` cv=5, `random_state=42`.

## Slide 7 — Resultados no teste (~1min30)
- Ler a linha vencedora: **EXP-05 (RF · Completo)** — F1-macro **0,825**, ROC AUC **0,909**.
- EXP-06 (GB · Completo) praticamente empatado.
- Notar que a precisão da classe 1 é alta (~0,92) e o recall é o ponto mais fraco — efeito
  do desbalanceamento mesmo após SMOTE.

## Slide 8 — Visualização no teste (~1min)
- Gráfico esquerdo: **Completo > Baseline** nos três modelos (F1-macro e ROC AUC).
- Matrizes de confusão: a diagonal domina; os erros se concentram em prever "2" quando é
  "1" (falsos não-graves) — relevante no domínio clínico.

## Slide 9 — Validação em dados nunca vistos (~1min)
- Mesmas métricas e hiperparâmetros, aplicados a 21.899 registros de **outros** arquivos.
- Distribuição diferente (55,8/44,2) e ainda assim métricas estáveis (~0,78 F1-macro).
- Reforçar: pipeline reaplicado **sem vazamento** (parâmetros do treino).

## Slide 10 — Teste × validação (~1min)
- Quedas **pequenas e uniformes** (~0,03–0,04) em F1-macro e ROC AUC → boa generalização.
- O **ranking** entre modelos se mantém do teste para a validação.

## Slide 11 — Conclusões (~1min)
1. Engenharia de atributos agrega ganho consistente (Completo > Baseline nos 3 modelos).
2. Melhor: EXP-05 (RF · Completo); EXP-06 (GB) empatado.
3. Regressão Logística é competitiva e a mais barata, e **generaliza melhor** (gap
   treino–teste ~0,006 vs ~0,05–0,06 das árvores).
4. Boa generalização em dados nunca vistos; ranking preservado.
5. Robustez mesmo com distribuição de classes diferente na validação.

---

### Perguntas prováveis (preparar)
- **Por que o recall da classe grave é mais baixo?** Desbalanceamento; SMOTE ajuda mas não
  elimina. Melhorias: ajustar o limiar de decisão, custo assimétrico, mais features.
- **SMOTE não causa vazamento?** Não: aplicado só nos folds de treino, dentro da CV.
- **Por que árvores sobreajustam mais?** Maior capacidade; o gap treino–teste evidencia
  isso frente à Regressão Logística.
- **Reprodutibilidade?** `random_state=42` em todas as etapas; instruções no README.
