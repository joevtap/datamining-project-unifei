# Roteiro do apresentador — Entrega 3 (Execução do DoE de árvores + Validação)

Guia de apoio para a apresentação `apresentacao_entrega3.html` (7 slides, sem capa).
Para cada slide: **Falar** (o que dizer) e **Como interpretar** (como ler o que está na
tela). Navegação: setas/espaço para avançar; o contador no canto inferior direito
(`01 / 07`) indica a posição.

> **Contexto em uma frase (abertura, opcional):** "Esta etapa executa o Design de
> Experimentos da Entrega 3 sobre os dados já preparados — foco nos modelos de árvore —
> e valida os modelos em dados que eles nunca viram."

**Lembretes de vocabulário (valem para o deck todo):**
- **Alvo `serious`** (classificação binária): `serious = 1` → evento **grave** (classe
  positiva, ~62% do treino); `serious = 2` → **não-grave**.
- **F1-macro**: média do F1 entre as duas classes — é a **métrica de seleção** porque
  trata as classes de forma justa sob o desbalanceamento moderado.
- **ROC AUC**: usa a **probabilidade contínua** prevista; mede a separação entre classes
  independpente do limiar.
- **Conjunto Baseline (11)**: atributos originais. **Completo (17)**: Baseline + 5
  features de engenharia + flag de imputação.

---

## Slide 1 — "O que o DoE previa"

**Falar:**
- "O experimento planejado cruzava **2 conjuntos de atributos** (Baseline e Completo) com
  **3 modelos** (Regressão Logística, Random Forest, Gradient Boosting), dando **6
  experimentos**, EXP-01 a EXP-06."
- "A seleção de hiperparâmetros usa **f1_macro** como critério, com validação cruzada
  estratificada e `random_state=42` para reprodutibilidade."

**Como interpretar:**
- A tabela é o **plano completo**. As duas linhas em cinza (EXP-01 e EXP-04, Regressão
  Logística) já antecipam visualmente o que **ainda não foi executado** — isso conecta
  com o próximo slide.
- Random Forest e Gradient Boosting usam **RandomizedSearchCV**; a Logística usaria
  **GridSearchCV**.

---

## Slide 2 — "O que rodou, sob limitação de hardware"

**Falar:**
- "Nesta execução rodamos os **4 experimentos de árvore** — EXP-02, 03, 05 e 06."
- "A **Regressão Logística (EXP-01 e EXP-04) ficou adiada** para uma etapa posterior."
- "Importante ser transparente: rodamos em **MODO_RAPIDO** — grades de hiperparâmetros
  reduzidas e validação cruzada com 3 folds — por limitação de hardware. Então os
  hiperparâmetros escolhidos vêm de um **espaço de busca reduzido**, não da tabela
  completa do enunciado."

**Como interpretar:**
- Coluna esquerda (mint) = **feito**; coluna direita (cinza) = **adiado**.
- A ressalva do MODO_RAPIDO é uma **nota de honestidade metodológica**: os números são
  válidos e comparáveis entre si, mas são de demonstração — não os "oficiais" da Tabela 1.

---

## Slide 3 — "Métricas por modelo" (teste)

**Falar:**
- "Estas são as métricas no **conjunto de teste** (os 30% separados, estratificados)."
- "Lendo pela métrica de seleção, **F1-macro**: o melhor é o **EXP-05 — Random Forest
  com o conjunto Completo, 0,826**, também com a maior **ROC AUC, 0,909** (em destaque)."
- "Em ambos os modelos, o **conjunto Completo supera o Baseline** — ou seja, a engenharia
  de atributos ajudou."
- "Os hiperparâmetros selecionados estão na faixa inferior: o Random Forest convergiu
  para 200 árvores, profundidade livre e `class_weight=balanced`; o Gradient Boosting
  para 100 estimadores, profundidade 3 e learning rate 0,2."

**Como interpretar:**
- `Prec. (1)` / `Rec. (1)` / `F1 (1)` são da **classe positiva (grave)**. Note o padrão
  do Random Forest: **precisão alta (~0,91–0,92) e recall menor (~0,79)** — ele é
  conservador ao marcar "grave", erra pouco quando marca, mas deixa passar mais casos.
- O Gradient Boosting tem **recall um pouco maior** da classe grave (~0,82) — equilíbrio
  ligeiramente diferente.
- `Bal. acc.` (acurácia balanceada) confirma que o desempenho não está inflado pela
  classe majoritária.

---

## Slide 4 — Visualização (teste)

**Falar:**
- "À esquerda, **Baseline × Completo** nas duas métricas-chave: as barras do Completo
  ficam **consistentemente acima** — é a evidência visual do ganho da engenharia de
  atributos."
- "À direita, as **matrizes de confusão** dos quatro modelos no teste: a diagonal
  concentra os acertos."

**Como interpretar:**
- Nas barras, o ganho do Completo é **pequeno mas consistente** — não é um salto, é uma
  melhora estável nos dois modelos.
- Nas matrizes, os eixos estão rotulados como **1 (grave)** e **2 (não-grave)**,
  consistentes com a validação (slide 6). Linhas = classe real, colunas = classe
  prevista; a **diagonal** concentra os acertos e o que está fora dela são os erros.

---

## Slide 5 — "Mesmas métricas, mesmos hiperparâmetros" (validação)

**Falar:**
- "Agora o teste de fogo: aplicamos os **mesmos modelos já treinados** a um conjunto de
  **dados nunca vistos** — outros arquivos JSON no mesmo formato."
- "Reaplicamos exatamente o mesmo pipeline (imputação, scaler) com **parâmetros do
  treino, sem nenhum reajuste** — portanto **sem vazamento**. As métricas e os
  hiperparâmetros são os mesmos do slide anterior."
- "São quase **22 mil registros** de validação, e repare que a **distribuição de classes
  é diferente** do treino (55,8/44,2 contra 62,3/37,7)."

**Como interpretar:**
- A leitura é a mesma do slide 3, mas em dado novo. O **ranking se mantém**: Completo
  ainda lidera, EXP-05 continua o melhor por F1-macro (0,783) e ROC AUC (0,868).
- O fato de a **distribuição ser diferente** e as métricas continuarem coerentes é um
  primeiro sinal de **robustez** (fecha no slide de conclusões).

---

## Slide 6 — "Teste → Validação"

**Falar:**
- "Aqui medimos **quanto o desempenho cai** ao sair do teste para os dados nunca vistos."
- "As quedas são **pequenas e uniformes** — da ordem de **0,03 a 0,04** tanto em F1-macro
  quanto em ROC AUC, nos quatro modelos."
- "À esquerda, as matrizes de confusão na validação confirmam que a diagonal continua
  dominante."

**Como interpretar:**
- A coluna **Δ** mostra a diferença (validação − teste); todos negativos e próximos —
  **nenhum modelo desaba**, o que indica **boa generalização** e ausência de
  sobreajuste severo ao split treino/teste.
- Se algum Δ fosse muito maior que os outros, indicaria um modelo frágil — não é o caso.

---

## Slide 7 — "O que os números mostram" (conclusões)

**Falar (passar pelos 5 pontos, sem inventar além do que está medido):**
1. "A **engenharia de atributos agrega ganho consistente** — Completo > Baseline em teste
   e validação."
2. "O **melhor modelo é o EXP-05**, Random Forest com o conjunto Completo."
3. "O **Random Forest sobreajusta mais** que o Gradient Boosting: o gap treino–teste de
   F1-macro é ~0,05 no RF contra ~0,015 no GB. Ou seja, o RF entrega o melhor resultado,
   mas o GB é mais 'honesto' entre treino e teste."
4. "Houve **boa generalização** em dados nunca vistos — quedas pequenas e uniformes."
5. "E **robustez**: a validação tinha distribuição de classes diferente e as métricas se
   mantiveram estáveis."

**Como interpretar / fechamento:**
- A mensagem central: **resultados consistentes e que generalizam**, com o conjunto
  Completo e o Random Forest na frente — dentro da limitação assumida do MODO_RAPIDO.
- Encerramento honesto: "Os próximos passos naturais são rodar no **modo completo** (grade
  oficial) e executar a **Regressão Logística** (EXP-01/04) para fechar a comparação."

---

## Perguntas prováveis (Q&A)

- **"Por que F1-macro e não acurácia?"** Porque há desbalanceamento moderado (~62/38); a
  acurácia favoreceria a classe majoritária. F1-macro pondera as duas classes igualmente.
- **"Por que a Regressão Logística não entrou?"** Decisão de escopo + custo; ela ficou
  documentada e preparada para a etapa seguinte.
- **"Os hiperparâmetros são os melhores possíveis?"** Não necessariamente — saíram de um
  espaço de busca reduzido (MODO_RAPIDO). São os melhores **dentro** dessa busca.
- **"Como garantem que não houve vazamento na validação?"** Nada foi ajustado na
  validação: scaler, imputador KNN e modelos vêm todos do treino; `serious` da validação
  serviu apenas como gabarito.
- **"Random Forest é melhor que Gradient Boosting?"** Por F1-macro/ROC AUC, sim, por
  pequena margem; mas o GB tem menor gap treino–teste. A escolha final pode pesar
  estabilidade vs. pico de desempenho.

---

### Apêndice — números de referência (caso perguntem)

| Exp. | Modelo · Conjunto | F1-macro teste | ROC AUC teste | F1-macro valid. | ROC AUC valid. |
|------|-------------------|:--:|:--:|:--:|:--:|
| EXP-02 | RF · Baseline | 0,817 | 0,904 | 0,778 | 0,863 |
| EXP-03 | GB · Baseline | 0,806 | 0,899 | 0,779 | 0,856 |
| EXP-05 | RF · Completo | **0,826** | **0,909** | **0,783** | **0,868** |
| EXP-06 | GB · Completo | 0,818 | 0,903 | 0,782 | 0,864 |

- **Hiperparâmetros — Random Forest:** `n_estimators=200, max_depth=None,
  min_samples_split=5, min_samples_leaf=2, class_weight=balanced`.
- **Hiperparâmetros — Gradient Boosting:** `n_estimators=100, max_depth=3,
  learning_rate=0.2`.
- **Validação:** 21.899 registros; distribuição `serious` 55,8% / 44,2%.
- **Fonte dos números:** `outputs/resumo_experimentos_arvores.csv`,
  `outputs/metricas_validacao.csv`, `outputs/comparacao_teste_validacao.csv`.
