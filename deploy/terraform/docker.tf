# Builda a imagem no Docker host remoto pelo proxy da Docker API do Portainer,
# no mesmo endpoint público que o provider já usa: o host não é alcançável fora
# da LAN e não há túnel SSH. O script dispara o build de forma assíncrona e
# acompanha por polling, porque o Cloudflare derruba com 524 qualquer request
# que passe de ~100s.

locals {
  repo_root = "${path.module}/../.."
}

resource "null_resource" "docker_build" {
  triggers = {
    # "**" e não "*": site/ tem subpasta (fonts) e um fileset não-recursivo
    # não veria mudança nenhuma dentro dela
    files_hash = md5(join(",", concat(
      [filemd5("${local.repo_root}/deploy/Dockerfile"), filemd5("${local.repo_root}/deploy/nginx.conf")],
      [for f in fileset("${local.repo_root}/site", "**") : filemd5("${local.repo_root}/site/${f}")],
    )))
  }

  provisioner "local-exec" {
    command = "${local.repo_root}/deploy/build-image.sh"

    environment = {
      PORTAINER_ENDPOINT = var.portainer_endpoint
      PORTAINER_USER     = var.portainer_user
      PORTAINER_PASSWORD = var.portainer_password
      ENDPOINT_ID        = tostring(data.portainer_environment.local.id)
      CONTEXT_DIR        = local.repo_root
      DOCKERFILE         = "deploy/Dockerfile"
      IMAGE_TAG          = var.image_tag
    }
  }
}
