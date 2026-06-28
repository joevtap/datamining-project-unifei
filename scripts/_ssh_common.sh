#!/usr/bin/env bash
# Helpers comuns de SSH/rsync para os scripts de nuvem. NÃO executar direto — é "sourced".
#
# Configuração por ambiente:
#   SSH_KEY  : caminho da chave .pem (recomendado no AWS EC2). Vazio = usa ~/.ssh/config
#              ou o ssh-agent. Caminhos relativos são resolvidos a partir da pasta de onde
#              o script foi chamado (ORIG_PWD), não da raiz do projeto.
#   SSH_OPTS : opções extras de ssh (ex.: "-o StrictHostKeyChecking=accept-new").
#
# Após "source", use: "$SSH_CMD" host '...' e rsync -e "$RSYNC_RSH" ...

SSH_KEY="${SSH_KEY:-}"
SSH_OPTS="${SSH_OPTS:-}"

# Resolve a chave relativa em relação à pasta de invocação (os scripts dão cd para a raiz).
case "$SSH_KEY" in
    "" | /*) : ;;
    *) SSH_KEY="${ORIG_PWD:-$PWD}/$SSH_KEY" ;;
esac

if [ -n "$SSH_KEY" ]; then
    if [ ! -f "$SSH_KEY" ]; then
        echo "!! Chave SSH '$SSH_KEY' não encontrada." >&2
        exit 1
    fi
    # O EC2 recusa a chave se ela estiver com permissões abertas.
    chmod 600 "$SSH_KEY" 2>/dev/null || true
    SSH_OPTS="-i $SSH_KEY $SSH_OPTS"
fi

SSH_CMD="ssh $SSH_OPTS"
RSYNC_RSH="ssh $SSH_OPTS"

# Garante que o rsync exista no host remoto (instâncias novas podem não ter).
# Cobre Amazon Linux (dnf/yum) e Ubuntu/Debian (apt-get).
ensure_remote_rsync() {
    local host="$1"
    $SSH_CMD "$host" 'command -v rsync >/dev/null 2>&1 || (
        sudo dnf install -y rsync 2>/dev/null ||
        sudo yum install -y rsync 2>/dev/null ||
        (sudo apt-get update -qq && sudo apt-get install -y rsync)
    )' || {
        echo "!! Não consegui garantir o rsync em $host." >&2
        return 1
    }
}
