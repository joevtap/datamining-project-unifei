"""Gera os gráficos da apresentação a partir dos resultados já salvos em outputs/.

Script one-off: NÃO treina nem reexecuta o pipeline — apenas lê os CSVs de resultado
(`outputs/resumo_experimentos_arvores.csv`, `metricas_validacao.csv`,
`comparacao_teste_validacao.csv`) e extrai a figura de matrizes de confusão já embutida
no notebook executado (`notebooks/00_pipeline_completo.ipynb`). As imagens são gravadas em
`apresentacao/img/` (mesmo tema visual da apresentação).

Uso: uv run python scripts/make_presentation_charts.py
"""
import base64
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # backend sem display (headless)
import matplotlib.pyplot as plt
import pandas as pd

PROJ = Path(__file__).resolve().parent.parent
OUTPUTS = PROJ / "outputs"
IMG = PROJ / "apresentacao" / "img"
IMG.mkdir(parents=True, exist_ok=True)

# Paleta consistente por modelo (legível sobre fundo branco do slide).
COR_BASELINE = "#94a3b8"   # cinza-azulado
COR_COMPLETO = "#0d9488"   # teal (combina com o accent mint do tema)
ORDEM_MODELOS = ["Regressão Logística", "Random Forest", "Gradient Boosting"]

plt.rcParams.update({
    "font.size": 13,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.25,
    "figure.dpi": 150,
})


def _ordena_por_modelo(df):
    """Ordena um DataFrame pela ordem canônica dos modelos (LR, RF, GB)."""
    df = df.copy()
    df["_ord"] = df["modelo"].map({m: i for i, m in enumerate(ORDEM_MODELOS)})
    return df.sort_values("_ord")


def grafico_baseline_vs_completo(resumo):
    """Barras agrupadas: ganho do conjunto Completo sobre o Baseline, por modelo.

    Dois painéis (F1-macro e ROC AUC no teste) evidenciam o efeito da engenharia de
    atributos de forma consistente entre os três modelos.
    """
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    for ax, (metrica, titulo, lim) in zip(
        axes,
        [("teste_f1_macro", "F1-macro (teste)", (0.75, 0.85)),
         ("teste_roc_auc", "ROC AUC (teste)", (0.85, 0.92))],
    ):
        piv = resumo.pivot_table(index="modelo", columns="conjunto", values=metrica)
        piv = piv.reindex(ORDEM_MODELOS)
        x = range(len(piv))
        w = 0.38
        ax.bar([i - w / 2 for i in x], piv["Baseline (11)"], w,
               label="Baseline (11)", color=COR_BASELINE)
        ax.bar([i + w / 2 for i in x], piv["Completo (17)"], w,
               label="Completo (17)", color=COR_COMPLETO)
        for i in x:
            ax.text(i - w / 2, piv["Baseline (11)"].iloc[i] + 0.002,
                    f"{piv['Baseline (11)'].iloc[i]:.3f}", ha="center", fontsize=10)
            ax.text(i + w / 2, piv["Completo (17)"].iloc[i] + 0.002,
                    f"{piv['Completo (17)'].iloc[i]:.3f}", ha="center", fontsize=10)
        ax.set_title(titulo)
        ax.set_xticks(list(x))
        ax.set_xticklabels([m.replace(" ", "\n") for m in piv.index])
        ax.set_ylim(*lim)
        ax.legend(loc="lower right", fontsize=11)
    fig.suptitle("Engenharia de atributos: Baseline × Completo", fontsize=15, y=1.02)
    fig.tight_layout()
    dest = IMG / "baseline_vs_completo.png"
    fig.savefig(dest, bbox_inches="tight")
    plt.close(fig)
    print("ok:", dest.name)


def grafico_teste_vs_validacao(comp):
    """Barras agrupadas por experimento: F1-macro no teste vs. na validação.

    Mostra a generalização (queda pequena e uniforme) para os 6 experimentos.
    """
    comp = comp.sort_values("exp_id")
    fig, ax = plt.subplots(figsize=(13, 5.2))
    x = range(len(comp))
    w = 0.38
    ax.bar([i - w / 2 for i in x], comp["teste_f1_macro"], w,
           label="Teste (30%)", color=COR_COMPLETO)
    ax.bar([i + w / 2 for i in x], comp["validacao_f1_macro"], w,
           label="Validação (nunca vista)", color=COR_BASELINE)
    for i in x:
        ax.text(i - w / 2, comp["teste_f1_macro"].iloc[i] + 0.002,
                f"{comp['teste_f1_macro'].iloc[i]:.3f}", ha="center", fontsize=9)
        ax.text(i + w / 2, comp["validacao_f1_macro"].iloc[i] + 0.002,
                f"{comp['validacao_f1_macro'].iloc[i]:.3f}", ha="center", fontsize=9)
    rotulos = [f"{r.exp_id}\n{r.modelo.split()[0]}·{r.conjunto.split()[0]}"
               for r in comp.itertuples()]
    ax.set_xticks(list(x))
    ax.set_xticklabels(rotulos, fontsize=10)
    ax.set_ylabel("F1-macro")
    ax.set_ylim(0.74, 0.84)
    ax.set_title("Generalização: teste × validação (dados nunca vistos)", fontsize=15)
    ax.legend(loc="lower right", fontsize=11)
    fig.tight_layout()
    dest = IMG / "teste_vs_validacao.png"
    fig.savefig(dest, bbox_inches="tight")
    plt.close(fig)
    print("ok:", dest.name)


def extrai_matrizes_confusao(notebook_path, dest):
    """Extrai a figura PNG das matrizes de confusão já embutida no notebook executado.

    Reaproveita a figura real do run (6 experimentos) em vez de recomputá-la — assim não
    é preciso reexecutar o pipeline. Grava o primeiro PNG encontrado nas saídas.
    """
    nb = json.loads(Path(notebook_path).read_text(encoding="utf-8"))
    for cell in nb["cells"]:
        if cell.get("cell_type") != "code":
            continue
        for out in cell.get("outputs", []):
            data = out.get("data", {})
            if "image/png" in data:
                png = data["image/png"]
                png = "".join(png) if isinstance(png, list) else png
                Path(dest).write_bytes(base64.b64decode(png))
                print("ok:", Path(dest).name, "(extraída do notebook)")
                return True
    print("AVISO: nenhuma figura PNG encontrada no notebook.")
    return False


def main():
    resumo = _ordena_por_modelo(pd.read_csv(OUTPUTS / "resumo_experimentos_arvores.csv"))
    comp = pd.read_csv(OUTPUTS / "comparacao_teste_validacao.csv")
    grafico_baseline_vs_completo(resumo)
    grafico_teste_vs_validacao(comp)
    extrai_matrizes_confusao(PROJ / "notebooks" / "00_pipeline_completo.ipynb", IMG / "cm_teste.png")


if __name__ == "__main__":
    main()
