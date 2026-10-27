output "service_url" {
  value = "https://${var.cloudflare_subdomain}.${var.cloudflare_domain}"
}

output "tunnel_id" {
  value = cloudflare_zero_trust_tunnel_cloudflared.site.id
}

output "stack_name" {
  value = portainer_stack.site.name
}
