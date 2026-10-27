# Deploy do site

O `site/` vai ao ar em **https://football-pca-map.viniciussc.com** no mesmo esquema dos outros stacks
(`tf-parque-palmeiras`): imagem nginx buildada no host pelo Portainer, stack com sidecar `cloudflared`
e tunnel Cloudflare próprio, state no MinIO. Quem aplica é o workflow
[`.github/workflows/deploy.yml`](../.github/workflows/deploy.yml), a cada push na `main` que toque
`site/` ou `deploy/` (ou manualmente, em *Actions → Deploy → Run workflow*).

| Arquivo | O que faz |
|---|---|
| `Dockerfile`, `nginx.conf` | nginx servindo `site/`; os assets ganham `?v=<md5>` para furar o cache do Cloudflare |
| `docker-compose.yml` | site + `cloudflared`, sem porta exposta |
| `build-image.sh` | builda a imagem no host pela Docker API do Portainer |
| `terraform/` | tunnel, CNAME, build e stack no Portainer |
| `set-github-secrets.sh` | sobe os secrets para o GitHub Environment a partir do seu `terraform.tfvars` local |

## Segredos: só no GitHub Environment

Nenhuma credencial fica no repositório. O job `validate` (roda em PRs) não usa segredo nenhum; só o job
`apply` usa o environment **`production`**, que guarda:

`MINIO_ACCESS_KEY_ID`, `MINIO_SECRET_ACCESS_KEY`, `PORTAINER_ENDPOINT`, `PORTAINER_USER`,
`PORTAINER_PASSWORD`, `CLOUDFLARE_API_KEY`, `CLOUDFLARE_EMAIL`, `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_ZONE_ID`.

### Configuração (uma vez, pelo dono do repo)

1. **Settings → Environments → New environment → `production`.**
   - *Deployment branches and tags* → **Selected branches** → só `main`. Assim um workflow alterado num
     branch ou PR não recebe os segredos (PR de fork nunca recebe).
   - Opcional: *Required reviewers* → você. Todo apply fica esperando sua aprovação.
2. Secrets: pela interface ou com o script, que lê `terraform/terraform.tfvars` (no `.gitignore`):
   ```bash
   cp deploy/terraform/terraform.tfvars.example deploy/terraform/terraform.tfvars   # e preencha
   AWS_ACCESS_KEY_ID=... AWS_SECRET_ACCESS_KEY=... ./deploy/set-github-secrets.sh
   ```
3. **Settings → Branches**: proteja a `main` (PR obrigatório, com revisão do code owner). O
   [`CODEOWNERS`](../.github/CODEOWNERS) exige a sua revisão em `.github/` e `deploy/`.

## Rodar local

```bash
cd deploy/terraform
terraform init -backend-config=backend.hcl   # precisa de AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY (MinIO)
terraform plan
```

Para só testar a imagem: `docker build -f deploy/Dockerfile -t football-pca-map . && docker run --rm -p 8080:80 football-pca-map`.

Não existe `cloudflare_ruleset` aqui de propósito: a fase de cache da zona pertence ao `tf-parque-palmeiras`
(uma zona só tem um ruleset por fase).
