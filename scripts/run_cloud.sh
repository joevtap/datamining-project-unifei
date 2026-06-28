#!/usr/bin/env bash
# Prepara o ambiente e executa o notebook final na VM, em modo COMPLETO por padrão.
#
# Roda NA VM (não na sua máquina). Faz o bootstrap completo: instala o uv se faltar, e o
# uv resolve/instala o Python 3.14 — ou seja, a instância pode vir sem uv nem python.
#
# Pensado para rodar dentro de um tmux/nohup (o run completo é longo e deve sobreviver a
# uma queda de SSH). Pré-requisitos: código do projeto presente e dados já enviados para
# datasets/ e validation/ (use scripts/deploy_code.sh e scripts/upload_data.sh).
#
# Variáveis de ambiente (com padrões):
#   MODO_RAPIDO=false   -> run completo (grades cheias + cv=5). Use true para validar.
#   CELL_TIMEOUT=36000  -> tempo máximo por célula (segundos).
#
# Uso (na VM):
#   bash scripts/run_cloud.sh
#   MODO_RAPIDO=true bash scripts/run_cloud.sh      # validação rápida do setup
set -euo pipefail

# Executa a partir da raiz do projeto, independentemente de onde o script foi chamado.
cd "$(dirname "$0")/.."

export MODO_RAPIDO="${MODO_RAPIDO:-false}"
export CELL_TIMEOUT="${CELL_TIMEOUT:-36000}"

# Garante que o uv esteja no PATH (instalações novas o colocam em ~/.local/bin).
export PATH="$HOME/.local/bin:$PATH"

# Instala o uv se ausente. O uv traz um Python autônomo, então a instância pode não ter
# python/uv pré-instalados. Usa curl ou wget, o que estiver disponível.
if ! command -v uv >/dev/null 2>&1; then
    echo ">> uv não encontrado; instalando..."
    if command -v curl >/dev/null 2>&1; then
        curl -LsSf https://astral.sh/uv/install.sh | sh
    elif command -v wget >/dev/null 2>&1; then
        wget -qO- https://astral.sh/uv/install.sh | sh
    else
        echo "!! Nem curl nem wget disponíveis para instalar o uv." >&2
        echo "   Instale um deles (ex.: sudo dnf install -y curl) e rode de novo." >&2
        exit 1
    fi
    export PATH="$HOME/.local/bin:$PATH"
fi
command -v uv >/dev/null 2>&1 || { echo "!! uv ainda indisponível no PATH." >&2; exit 1; }

echo ">> Sincronizando ambiente (Python 3.14 + dependências + grupo dev)..."
uv sync

# Registra o kernel para que o nbclient o encontre durante a execução headless.
echo ">> Registrando kernel Jupyter..."
uv run python -m ipykernel install --user --name python3 >/dev/null

echo ">> Executando o notebook (MODO_RAPIDO=$MODO_RAPIDO)..."
uv run python scripts/run_notebook.py

echo ">> Concluído. Artefatos em outputs/ (use scripts/fetch_outputs.sh para trazer de volta)."
