#!/usr/bin/env bash
# Builda a imagem do site no Docker host remoto, sem SSH e sem LAN.
#
# O projeto nao esta em nenhum registry, entao a imagem precisa nascer no proprio
# host onde a stack roda — e a tag local que o docker-compose.yml referencia.
#
# Caminho: proxy da Docker API do Portainer, no mesmo endpoint público que o
# provider já usa. O build NÃO roda segurando a conexão HTTP — o Cloudflare
# derruba qualquer request que passe de ~100s com erro 524, e este Dockerfile
# leva minutos. Em vez disso:
#
#   1. sobe um container `docker:cli` com o socket do Docker montado;
#   2. injeta o contexto de build dentro dele via /archive;
#   3. inicia o container (retorna na hora) e acompanha por polling.
#
# Assim toda request é curta e nada esbarra no timeout do proxy.
set -euo pipefail

: "${PORTAINER_ENDPOINT:?PORTAINER_ENDPOINT não definido}"
: "${PORTAINER_USER:?PORTAINER_USER não definido}"
: "${PORTAINER_PASSWORD:?PORTAINER_PASSWORD não definido}"
: "${ENDPOINT_ID:?ENDPOINT_ID não definido}"
: "${CONTEXT_DIR:?CONTEXT_DIR não definido}"
: "${DOCKERFILE:?DOCKERFILE não definido}"
: "${IMAGE_TAG:?IMAGE_TAG não definido}"

BUILDER_IMAGE="${BUILDER_IMAGE:-docker:cli}"
BUILD_TIMEOUT="${BUILD_TIMEOUT:-900}"
POLL_INTERVAL="${POLL_INTERVAL:-5}"

api="${PORTAINER_ENDPOINT%/}"

jwt=$(curl -sS -m 30 -X POST "$api/api/auth" \
  -H 'Content-Type: application/json' \
  -d "$(printf '{"username":"%s","password":"%s"}' "$PORTAINER_USER" "$PORTAINER_PASSWORD")" \
  | sed -n 's/.*"jwt":"\([^"]*\)".*/\1/p')

if [ -z "$jwt" ]; then
  echo "erro: falha ao autenticar em $api/api/auth" >&2
  exit 1
fi

docker_api="$api/api/endpoints/$ENDPOINT_ID/docker"
auth="Authorization: Bearer $jwt"

cid=""
cleanup() {
  [ -n "$cid" ] && curl -sS -m 60 -X DELETE -H "$auth" \
    "$docker_api/containers/$cid?force=1" >/dev/null 2>&1 || true
}
trap cleanup EXIT

# O builder é pequeno (~20s de pull) e o endpoint é idempotente.
echo "garantindo imagem do builder ($BUILDER_IMAGE)"
builder_repo="${BUILDER_IMAGE%%:*}"
builder_tag="${BUILDER_IMAGE##*:}"
curl -sS --fail-with-body -m 300 -X POST -H "$auth" \
  "$docker_api/images/create?fromImage=$builder_repo&tag=$builder_tag" >/dev/null

# O contexto é injetado em /tmp porque o /archive exige um path que já exista
# na imagem do builder.
cid=$(curl -sS --fail-with-body -m 60 -X POST -H "$auth" \
  -H 'Content-Type: application/json' \
  -d "{\"Image\":\"$BUILDER_IMAGE\",
       \"Tty\":true,
       \"Cmd\":[\"docker\",\"build\",\"-t\",\"$IMAGE_TAG\",\"-f\",\"/tmp/$DOCKERFILE\",\"/tmp\"],
       \"HostConfig\":{\"Binds\":[\"/var/run/docker.sock:/var/run/docker.sock\"]}}" \
  "$docker_api/containers/create" \
  | sed -n 's/.*"Id":"\([^"]*\)".*/\1/p')

if [ -z "$cid" ]; then
  echo "erro: não consegui criar o container de build" >&2
  exit 1
fi
echo "builder criado: $(echo "$cid" | cut -c1-12)"

echo "enviando contexto de build"
# Só o que a imagem usa: o contexto é a raiz do repo, que também tem data/,
# .venv, artigo/... e nada disso precisa subir pro host.
tar -cf - -C "$CONTEXT_DIR" deploy/Dockerfile deploy/nginx.conf site \
  | curl -sS --fail-with-body -m 300 -X PUT -H "$auth" \
      -H 'Content-Type: application/x-tar' --data-binary @- \
      "$docker_api/containers/$cid/archive?path=/tmp" >/dev/null

curl -sS --fail-with-body -m 60 -X POST -H "$auth" \
  "$docker_api/containers/$cid/start" >/dev/null
echo "build iniciado no host; acompanhando a cada ${POLL_INTERVAL}s"

elapsed=0
while :; do
  sleep "$POLL_INTERVAL"
  elapsed=$((elapsed + POLL_INTERVAL))

  # State é plano aqui (sem healthcheck no builder), então dá para recortar
  # sem depender de jq, que não existe na imagem do CI.
  state=$(curl -sS --fail-with-body -m 30 -H "$auth" \
    "$docker_api/containers/$cid/json" | grep -o '"State":{[^}]*}')
  running=$(printf '%s' "$state" | sed -n 's/.*"Running":\([a-z]*\).*/\1/p')

  if [ "$running" = "false" ]; then
    break
  fi

  echo "  ... buildando (${elapsed}s)"

  if [ "$elapsed" -ge "$BUILD_TIMEOUT" ]; then
    echo "erro: build passou de ${BUILD_TIMEOUT}s" >&2
    curl -sS -m 60 -H "$auth" "$docker_api/containers/$cid/logs?stdout=1&stderr=1&tail=40" >&2 || true
    exit 1
  fi
done

exit_code=$(printf '%s' "$state" | sed -n 's/.*"ExitCode":\([0-9-]*\).*/\1/p')

echo "--- log do build ---"
curl -sS -m 120 -H "$auth" "$docker_api/containers/$cid/logs?stdout=1&stderr=1&tail=60"
echo "--- fim do log ---"

if [ "$exit_code" != "0" ]; then
  echo "erro: build falhou no host remoto (exit $exit_code)" >&2
  exit 1
fi

echo "imagem $IMAGE_TAG construída em ${elapsed}s"
