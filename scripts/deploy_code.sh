#!/usr/bin/env bash
# Envia o CÓDIGO do projeto para a VM via rsync (sem depender de git na instância).
#
# Útil porque uma EC2 nova pode não ter git. Sincroniza tudo, exceto dados grandes,
# ambiente virtual, .git e artefatos regeneráveis. Os dados vão pelo upload_data.sh.
#
# Uso:
#   SSH_KEY=caminho/chave.pem bash scripts/deploy_code.sh user@host [caminho_remoto]
# Exemplo (AWS EC2):
#   SSH_KEY=~/Downloads/minha-chave.pem bash scripts/deploy_code.sh ec2-user@1.2.3.4
set -euo pipefail

ORIG_PWD="$PWD"
cd "$(dirname "$0")/.."
# shellcheck source=scripts/_ssh_common.sh
source "$(dirname "$0")/_ssh_common.sh"

HOST="${1:?uso: [SSH_KEY=chave.pem] deploy_code.sh user@host [caminho_remoto]}"
REMOTE="${2:-~/datamining-project-unifei}"

echo ">> Garantindo rsync no host remoto..."
ensure_remote_rsync "$HOST"

echo ">> Enviando código -> $HOST:$REMOTE/"
$SSH_CMD "$HOST" "mkdir -p \"$REMOTE\""
rsync -avhP --partial -e "$RSYNC_RSH" \
    --exclude '.git/' \
    --exclude '.venv/' \
    --exclude 'datasets/' \
    --exclude 'validation/' \
    --exclude 'outputs/' \
    --exclude '__pycache__/' \
    ./ "$HOST:$REMOTE/"

echo ">> Código enviado. Próximos passos na VM: bash scripts/run_cloud.sh"
