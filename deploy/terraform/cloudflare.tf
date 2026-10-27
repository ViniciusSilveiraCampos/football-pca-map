# Cada stack da casa tem o seu próprio tunnel e o seu próprio sidecar
# cloudflared no compose — não existe tunnel compartilhado.

resource "random_id" "tunnel_secret" {
  byte_length = 35
}

resource "cloudflare_zero_trust_tunnel_cloudflared" "site" {
  account_id = var.cloudflare_account_id
  name       = "football-pca-map"
  secret     = random_id.tunnel_secret.b64_std
}

resource "cloudflare_zero_trust_tunnel_cloudflared_config" "site" {
  account_id = var.cloudflare_account_id
  tunnel_id  = cloudflare_zero_trust_tunnel_cloudflared.site.id

  config {
    ingress_rule {
      hostname = "${var.cloudflare_subdomain}.${var.cloudflare_domain}"
      # o nome do serviço no compose; o cloudflared resolve por DNS do Docker
      service = "http://football-pca-map:80"
    }

    # a regra catch-all é obrigatória e tem que ser a última
    ingress_rule {
      service = "http_status:404"
    }
  }
}

resource "cloudflare_record" "site" {
  zone_id         = var.cloudflare_zone_id
  name            = var.cloudflare_subdomain
  content         = "${cloudflare_zero_trust_tunnel_cloudflared.site.id}.cfargotunnel.com"
  type            = "CNAME"
  proxied         = true
  allow_overwrite = true
  comment         = "Football PCA Map - managed by Terraform"
}

# Sem cloudflare_ruleset aqui: a fase http_request_cache_settings da zona
# pertence ao tf-parque-palmeiras (uma zona só tem UM ruleset por fase). Os
# assets ganham ?v=<md5> no build da imagem (ver deploy/Dockerfile) e o HTML não
# é cacheado pelo Cloudflare por padrão, então não precisa de regra.
