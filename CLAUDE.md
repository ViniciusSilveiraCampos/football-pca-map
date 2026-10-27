# football-pca-map

Análise de componentes principais (PCA) aplicada a dados de futebol em campo, gerando mapas.
Python 3.12, gerenciado com **uv**.

> Instruções de revisão de PR estão em `REVIEW.md`.

## Estrutura

- `src/football_pca_map/` — pacote principal (layout `src/`).
- `tests/` — pytest; `pythonpath = ["src"]` já configurado.
- `data/raw/` e `outputs/` — dados brutos e figuras geradas, fora do git.

## Comandos

```bash
uv sync                 # cria .venv e instala tudo (inclui grupo dev)
uv run task format      # ruff --fix + black
uv run task lint        # ruff check + black --check (o mesmo que o CI)
uv run task test        # pytest com cobertura
uv add <pacote>         # dependência de runtime
uv add --dev <pacote>   # dependência de desenvolvimento
```

## Convenções

- **black** formata, **ruff** só faz lint (E501 desligado no ruff). Não use `ruff format`.
- Etapas aleatórias sempre com `random_state` fixo.
- `fit` do scaler/PCA só em dados de treino; o resto usa `transform`.

## CI

- `.github/workflows/ci.yml` — jobs `black`, `ruff` e `test` em push para `main`/`develop` e em PRs.
- `.github/workflows/claude-code-review.yml` — revisão automática de PR pelo Claude Code
  (precisa do secret `CLAUDE_CODE_OAUTH_TOKEN`).
- `.github/workflows/artigo.yml` — a cada push na `main`, compila `artigo/main.tex` (resumo da XXI Jornada
  Científica, modelo da FIB em abnTeX2: Arial 10, máx. 2 páginas, logo em `artigo/figuras/`) e
  envia o PDF para um canal do Discord (secret `DISCORD_WEBHOOK_URL`).
  Para compilar localmente: `cd artigo && latexmk -pdf main.tex`.
- `.github/workflows/artigo-release.yml` — compila o resumo em PRs que tocam `artigo/` (PDF como
  artefato; falha se passar de 2 páginas) e, em tags `artigo-v*`, anexa o PDF a um release do GitHub.
  Trechos grifados com `\completar{...}` no `main.tex` ainda precisam ser preenchidos. Não precisa de secret
  (usa o `GITHUB_TOKEN`). Para publicar: `git tag artigo-v1.0 && git push origin artigo-v1.0`.
- `.github/workflows/deploy.yml` — a cada push na `main` que toque `site/` ou `deploy/`, faz `terraform apply`
  em `deploy/terraform/` (tunnel Cloudflare + stack no Portainer, mesmo padrão do `tf-parque-palmeiras`).
  Os segredos ficam só no GitHub Environment `production` (restrito à `main`); em PRs roda só
  `fmt`/`validate`, sem segredo. Detalhes e setup em `deploy/README.md`.

## Tracing no LangSmith (compartilhado)

Todo o time manda as conversas para **um único** LangSmith: o workspace compartilhado do projeto,
no projeto `football-pca-map`. O `.claude/settings.json` já habilita o plugin `langsmith-tracing`
(o Claude Code oferece instalar o marketplace ao abrir o projeto), define o projeto e liga o
tracing (`TRACE_TO_LANGSMITH=true`). Só falta a chave, que **nunca** vai para o git:

```bash
cp .claude/settings.local.example.json .claude/settings.local.json
# edite e coloque uma chave gerada DENTRO do workspace compartilhado
# (smith.langchain.com → troque para o workspace do projeto → Settings → API Keys)
```

Para ter acesso ao workspace, peça um convite ao dono do projeto. O `settings.local.json` está no
`.gitignore`. Sem chave nada é enviado; para não rastrear, ponha `"TRACE_TO_LANGSMITH": "false"` no
seu `settings.local.json`.
