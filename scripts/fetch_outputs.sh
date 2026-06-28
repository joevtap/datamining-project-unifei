#!/usr/bin/env bash
# Traz os resultados da VM de volta para a máquina local (outputs/ e o notebook executado).
#
# Use depois que scripts/run_cloud.sh terminar na VM. rsync resumível (-P).
#
# Uso:
#   SSH_KEY=caminho/chave.pem bash scripts/fetch_outputs.sh user@host [caminho_remoto]
# Exemplo (AWS EC2):
#   SSH_KEY=~/Downloads/minha-chave.pem bash scripts/fetch_outputs.sh ec2-user@1.2.3.4
set -euo pipefail

ORIG_PWD="$PWD"
cd "$(dirname "$0")/.."
# shellcheck source=scripts/_ssh_common.sh
source "$(dirname "$0")/_ssh_common.sh"

HOST="${1:?uso: [SSH_KEY=chave.pem] fetch_outputs.sh user@host [caminho_remoto]}"
REMOTE="${2:-~/datamining-project-unifei}"

echo ">> Garantindo rsync no host remoto..."
ensure_remote_rsync "$HOST"

echo ">> Trazendo outputs/ de $HOST:$REMOTE/outputs/"
mkdir -p outputs
# Exclui o parquet intermediário (regenerável) para economizar transferência.
rsync -avhP --partial --exclude '_raw_reports_*.parquet' -e "$RSYNC_RSH" \
    "$HOST:$REMOTE/outputs/" outputs/

echo ">> Trazendo o notebook executado"
rsync -avhP --partial -e "$RSYNC_RSH" \
    "$HOST:$REMOTE/notebooks/00_pipeline_completo.ipynb" notebooks/00_pipeline_completo.ipynb

echo ">> Download concluído. Veja outputs/resumo_experimentos_arvores.csv"
