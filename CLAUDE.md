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
- `.github/workflows/artigo.yml` — a cada push na `main`, compila `artigo/main.tex` (abnTeX2) e
  envia o PDF para um canal do Discord (secret `DISCORD_WEBHOOK_URL`).
  Para compilar localmente: `cd artigo && latexmk -pdf main.tex`.

## Tracing no LangSmith (opcional, por pessoa)

O `.claude/settings.json` já habilita o plugin `langsmith-tracing`; o Claude Code oferece instalar
o marketplace ao abrir o projeto. Cada pessoa manda as conversas para o **próprio** LangSmith:

```bash
cp .claude/settings.local.example.json .claude/settings.local.json
# edite e coloque sua chave pessoal (smith.langchain.com → Settings → API Keys)
```

O `settings.local.json` está no `.gitignore`. Sem ele (ou com `TRACE_TO_LANGSMITH` diferente de
`"true"`), nada é enviado. O projeto no LangSmith padrão é `football-pca-map`.
