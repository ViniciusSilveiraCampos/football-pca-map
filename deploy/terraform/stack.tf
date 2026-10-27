resource "portainer_stack" "site" {
  name            = "football-pca-map"
  endpoint_id     = data.portainer_environment.local.id
  deployment_type = "standalone"
  method          = "file"
  stack_file_path = "${path.module}/../docker-compose.yml"

  # a imagem é local (buildada no host), não há registry de onde puxar
  pull_image = false

  env {
    name  = "TUNNEL_TOKEN"
    value = cloudflare_zero_trust_tunnel_cloudflared.site.tunnel_token
  }

  # Muda junto com o conteúdo da imagem. Sem isso a stack não tem nenhum
  # atributo diferente quando só o site mudou: o build gera a imagem nova no
  # host, o Terraform não vê diff, não redeploya, e o container segue servindo
  # a imagem antiga. O depends_on só ordena as operações, não força atualização.
  env {
    name  = "BUILD_HASH"
    value = null_resource.docker_build.triggers.files_hash
  }

  depends_on = [
    null_resource.docker_build,
  ]
}
