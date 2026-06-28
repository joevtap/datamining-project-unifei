#!/usr/bin/env bash
# Envia os dados não versionados (datasets/ + validation/, ~2,8 GB) para a VM via rsync.
#
# rsync sobre SSH com --partial/-P permite RETOMAR uploads interrompidos — útil para os
# arquivos grandes.
#
# Uso:
#   SSH_KEY=caminho/chave.pem bash scripts/upload_data.sh user@host [caminho_remoto]
# Exemplos (AWS EC2):
#   SSH_KEY=~/Downloads/minha-chave.pem bash scripts/upload_data.sh ec2-user@1.2.3.4
#   SSH_KEY=~/Downloads/minha-chave.pem bash scripts/upload_data.sh ubuntu@ec2-...amazonaws.com
#
# Usuário padrão do EC2: ec2-user (Amazon Linux) ou ubuntu (Ubuntu).
# Alternativa sem rsync: 'aws s3 cp --recursive datasets/ s3://bucket/datasets/'.
set -euo pipefail

ORIG_PWD="$PWD"
cd "$(dirname "$0")/.."
# shellcheck source=scripts/_ssh_common.sh
source "$(dirname "$0")/_ssh_common.sh"

HOST="${1:?uso: [SSH_KEY=chave.pem] upload_data.sh user@host [caminho_remoto]}"
REMOTE="${2:-~/datamining-project-unifei}"

echo ">> Garantindo rsync no host remoto..."
ensure_remote_rsync "$HOST"

for dir in datasets validation; do
    if [ ! -d "$dir" ]; then
        echo "!! Diretório local '$dir' não existe — nada a enviar." >&2
        continue
    fi
    echo ">> Enviando $dir/ -> $HOST:$REMOTE/$dir/"
    $SSH_CMD "$HOST" "mkdir -p \"$REMOTE/$dir\""
    rsync -avhP --partial -e "$RSYNC_RSH" "$dir/" "$HOST:$REMOTE/$dir/"
done

echo ">> Upload concluído."
