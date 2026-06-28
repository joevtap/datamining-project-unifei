"""Executa um notebook de forma headless via nbclient (sem precisar de jupyter/nbconvert).

Reusa o padrão "Execução headless" do README. Roda o notebook no diretório notebooks/
(para que a resolução de caminhos relativos funcione) e grava o notebook executado de
volta no mesmo arquivo, preservando as saídas das células.

Configurável por variáveis de ambiente:
- NOTEBOOK    : caminho do notebook (padrão: notebooks/00_pipeline_completo.ipynb)
- CELL_TIMEOUT: tempo máximo por célula, em segundos (padrão: 36000 = 10 h)
- MODO_RAPIDO : herdado pelo kernel; controla a carga do DoE (ver Seção 0 do notebook)
"""
import os

import nbformat
from nbclient import NotebookClient

NOTEBOOK = os.environ.get("NOTEBOOK", "notebooks/00_pipeline_completo.ipynb")
CELL_TIMEOUT = int(os.environ.get("CELL_TIMEOUT", "36000"))


def main():
    notebook = nbformat.read(NOTEBOOK, as_version=4)
    # resources.metadata.path = notebooks/ porque o notebook resolve datasets/, outputs/
    # etc. a partir do diretório-pai do cwd (ver Seção 0). O kernel herda o ambiente do
    # processo, então MODO_RAPIDO exportado no shell chega às células.
    client = NotebookClient(
        notebook,
        timeout=CELL_TIMEOUT,
        kernel_name="python3",
        resources={"metadata": {"path": "notebooks"}},
    )
    print(f"Executando {NOTEBOOK} | MODO_RAPIDO={os.environ.get('MODO_RAPIDO', 'true')} "
          f"| timeout/célula={CELL_TIMEOUT}s", flush=True)
    client.execute()
    nbformat.write(notebook, NOTEBOOK)
    print("OK ->", NOTEBOOK)


if __name__ == "__main__":
    main()
