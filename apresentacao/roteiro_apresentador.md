# Roteiro do apresentador

Apresentação: `apresentacao.html` (9 slides, 16:9). Navegação: setas / espaço / swipe.
Tempo-alvo: ~8–10 min. Estrutura: contexto → pergunta → pipeline → DoE → resultados →
fechamento crítico.

---

## Slide 1 — Capa (~20s)
- Abrir com a ideia central: prever a **gravidade** de eventos adversos a medicamentos para
  **acelerar a triagem** em emergências, usando dados públicos do FDA (OpenFDA / FAERS).

## Slide 2 — Contexto do problema (~1min)
- Reações adversas e interações entre medicamentos são comuns e podem ser graves.
- São relatadas ao sistema do FDA (FAERS) e publicadas abertamente no OpenFDA.
- Na emergência, decidir rápido o que é grave (triagem) é crítico e custoso.
- Números: ~36 mil relatórios; alvo `serious` (grave/não-grave); classes desbalanceadas (~62/38).

## Slide 3 — Pergunta de negócio (~45s)
- A pergunta que guia o trabalho: **dá para prever a gravidade de um novo caso a partir de
  relatórios passados de outros pacientes?**
- Se sim, o modelo prioriza automaticamente os casos mais prováveis de graves → triagem mais rápida.

## Slide 4 — Pipeline dos dados (~1min30)
- Fluxo: coleta (OpenFDA, JSON) → limpeza e uma linha por relatório → faixa etária estimada
  por KNN → engenharia de atributos → balanceamento por SMOTE → dataset final.
- Explicar em uma frase cada método (sem entrar em código):
  - **KNN** completa a idade faltante a partir de casos parecidos (aprendido só no treino).
  - **Engenharia de atributos**: cria sinais úteis (nº de medicamentos/substâncias, indicadores).
  - **SMOTE**: gera exemplos sintéticos da classe minoritária para o treino ver as duas
    classes de forma equilibrada.
- Dataset final: alvo `serious`; dois conjuntos — Baseline (originais) e Completo (+ engenharia).

## Slide 5 — Design de Experimentos (~1min)
- 3 modelos (Regressão Logística, Random Forest, Gradient Boosting) × 2 conjuntos = 6 experimentos.
- Seleção por **F1-macro** (justa com desbalanceamento), via validação cruzada.
- Avaliação final no teste (30%) e em dados nunca vistos. Mesmo procedimento para todos.

## Slide 6 — Resultados: desempenho (~1min)
- Gráfico: o conjunto **Completo** supera o **Baseline** nos três modelos.
- Árvores no topo; Regressão Logística competitiva.
- **Modelo escolhido: Random Forest · Completo** — F1-macro 0,825 e ROC AUC 0,909 no teste.

## Slide 7 — Resultados: generalização (~1min)
- Gráfico teste × validação: quedas pequenas e uniformes (~0,03–0,04).
- O ranking entre modelos se mantém; funciona mesmo com a validação tendo distribuição
  diferente (55,8/44,2). Conclusão: **generaliza bem**, sem sobreajuste evidente.

## Slide 8 — Fechamento crítico: dá para implantar? (~1min30)
- Veredito honesto: **ainda não** como decisão autônoma. Serve como **apoio à triagem** —
  prioriza, mas a decisão final é do profissional (humano no circuito).
- Limitações:
  - **Recall da classe grave**: ~32% dos casos graves passam despercebidos na validação. Em
    triagem, o falso negativo é o erro mais caro.
  - **Viés da fonte**: OpenFDA é feito de relatos voluntários (subnotificação, sem causalidade
    comprovada) — pode não refletir toda a população clínica.

## Slide 9 — Caminho para produção (~1min)
- Implantar é um **ciclo** (CRISP-DM, fase de Implantação), não um evento único:
  servir o modelo → monitorar (desempenho + drift) → re-treino offline periódico →
  CI/CD de dados e modelo → revalidação contínua → realimenta o ciclo.
- Mensagem final: com esse ciclo mínimo, o modelo pode entrar com segurança como ferramenta
  de apoio; sem ele, não.

---

### Perguntas prováveis
- **Por que o recall da classe grave é mais baixo?** Desbalanceamento; o SMOTE ajuda mas não
  elimina. Melhorias: ajustar o limiar de decisão, custo assimétrico, mais atributos.
- **Por que F1-macro e não acurácia?** Acurácia engana com classes desbalanceadas; F1-macro
  pesa as duas classes igualmente.
- **Por que Random Forest e não Gradient Boosting?** Empate técnico; o Random Forest leva
  ligeira vantagem no teste e é robusto e simples de manter.
- **Como evitar vazamento de dados?** Tudo que aprende (imputação, balanceamento, escala) é
  ajustado só no treino; a validação usa dados nunca vistos.
