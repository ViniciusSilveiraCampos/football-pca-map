variable "portainer_endpoint" {
  description = "URL da API do Portainer"
  type        = string
}

variable "portainer_user" {
  description = "Usuário admin do Portainer"
  type        = string
}

variable "portainer_password" {
  description = "Senha do admin do Portainer"
  type        = string
  sensitive   = true
}

variable "cloudflare_api_key" {
  description = "Global API Key da Cloudflare"
  type        = string
  sensitive   = true
}

variable "cloudflare_email" {
  description = "E-mail da conta Cloudflare"
  type        = string
}

variable "cloudflare_account_id" {
  description = "ID da conta Cloudflare"
  type        = string
}

variable "cloudflare_zone_id" {
  description = "ID da zona DNS"
  type        = string
}

variable "cloudflare_domain" {
  description = "Domínio base"
  type        = string
  default     = "viniciussc.com"
}

variable "cloudflare_subdomain" {
  description = "Subdomínio do site"
  type        = string
  default     = "football-pca-map"
}

variable "image_tag" {
  description = "Tag local da imagem, buildada no próprio host (não há registry)"
  type        = string
  default     = "football-pca-map:latest"
}
