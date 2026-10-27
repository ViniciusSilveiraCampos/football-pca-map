#!/usr/bin/env bash
# Envia os secrets do deploy pro GitHub Environment "production".
# Uso: ./deploy/set-github-secrets.sh
# Requer: gh autenticado (gh auth login) com permissão de admin no repo.
#
# NENHUM segredo está escrito neste arquivo: tudo é lido de
# deploy/terraform/terraform.tfvars, que está no .gitignore. As credenciais do
# MinIO (backend do state) vêm do ambiente, como no set-gitlab-vars.sh dos
# outros stacks.

set -euo pipefail

RAIZ="$(cd "$(dirname "$0")" && pwd)"
TFVARS="$RAIZ/terraform/terraform.tfvars"
ENV_NAME="${ENV_NAME:-production}"
: "${AWS_ACCESS_KEY_ID:?exporte AWS_ACCESS_KEY_ID (MinIO) antes de rodar}"
: "${AWS_SECRET_ACCESS_KEY:?exporte AWS_SECRET_ACCESS_KEY (MinIO) antes de rodar}"

if [ ! -f "$TFVARS" ]; then
  echo "ERRO: $TFVARS não existe. Copie terraform.tfvars.example e preencha." >&2
  exit 1
fi

# lê uma variável do tfvars, sem as aspas
tfvar() {
  local v
  v=$(sed -nE "s/^[[:space:]]*$1[[:space:]]*=[[:space:]]*\"(.*)\"[[:space:]]*$/\1/p" "$TFVARS")
  [ -n "$v" ] || { echo "ERRO: '$1' não encontrada em $TFVARS" >&2; exit 1; }
  printf '%s' "$v"
}

set_secret() {
  # pelo stdin, pra o valor não aparecer na lista de processos
  printf '%s' "$2" | gh secret set "$1" --env "$ENV_NAME"
  echo "✓ $1"
}

echo "==> Configurando secrets do environment '$ENV_NAME'..."

# --- Backend S3 (MinIO) ---
set_secret "MINIO_ACCESS_KEY_ID"     "$AWS_ACCESS_KEY_ID"
set_secret "MINIO_SECRET_ACCESS_KEY" "$AWS_SECRET_ACCESS_KEY"

# --- Portainer ---
set_secret "PORTAINER_ENDPOINT" "$(tfvar portainer_endpoint)"
set_secret "PORTAINER_USER"     "$(tfvar portainer_user)"
set_secret "PORTAINER_PASSWORD" "$(tfvar portainer_password)"

# --- Cloudflare ---
set_secret "CLOUDFLARE_API_KEY"    "$(tfvar cloudflare_api_key)"
set_secret "CLOUDFLARE_EMAIL"      "$(tfvar cloudflare_email)"
set_secret "CLOUDFLARE_ACCOUNT_ID" "$(tfvar cloudflare_account_id)"
set_secret "CLOUDFLARE_ZONE_ID"    "$(tfvar cloudflare_zone_id)"

echo ""
echo "==> Todos os secrets configurados."
