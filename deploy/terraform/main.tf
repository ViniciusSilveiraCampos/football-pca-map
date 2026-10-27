terraform {
  required_version = ">= 1.0.0"

  required_providers {
    portainer  = { source = "portainer/portainer", version = "~> 1.22" }
    cloudflare = { source = "cloudflare/cloudflare", version = "~> 4.0" }
    random     = { source = "hashicorp/random", version = "~> 3.5" }
    null       = { source = "hashicorp/null", version = "~> 3.0" }
  }

  backend "s3" {
    bucket = "terraform-state"

    endpoints = { s3 = "https://storage.viniciussc.com" }

    region                      = "us-east-1"
    skip_credentials_validation = true
    skip_metadata_api_check     = true
    skip_requesting_account_id  = true
    use_path_style              = true
    # Credenciais por env: AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY
  }
}

provider "portainer" {
  endpoint        = var.portainer_endpoint
  api_user        = var.portainer_user
  api_password    = var.portainer_password
  skip_ssl_verify = true
}

provider "cloudflare" {
  api_key = var.cloudflare_api_key
  email   = var.cloudflare_email
}

data "portainer_environment" "local" {
  name = "local"
}
