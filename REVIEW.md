# Instruções de revisão

Escreva **todos** os comentários e o resumo em português do Brasil.

Este repositório aplica PCA a dados de futebol em campo (posições, eventos, métricas por jogador
ou por time) para gerar mapas. O que importa é o que invalida a análise ou distorce o mapa — não
o que quebra o estilo.

## O que é 🔴 Importante aqui

Reserve Importante para o que corrompe o resultado ou a reprodutibilidade:

- Vazamento de dados: `StandardScaler`/`PCA` ajustado (`fit`) em dados que incluem o conjunto de
  teste/avaliação, ou `fit` refeito onde deveria ser só `transform`.
- Features em escalas diferentes entrando no PCA sem padronização (ex.: metros misturados com
  contagens ou porcentagens) — o primeiro componente vira "a feature de maior variância".
- Sistema de coordenadas do campo errado: origem trocada, eixo Y invertido, unidades do provider
  (0–100, 0–120×80, metros) misturadas sem conversão, ou lados não espelhados entre o 1º e o 2º
  tempo / entre mandante e visitante.
- Interpretação de componente que depende do sinal ou da ordem dos autovetores sem fixá-los
  (o sinal de um componente do PCA é arbitrário).
- NaN/inf entrando no `fit` ou linhas descartadas silenciosamente (`dropna`) alterando a amostra
  sem registro.
- `random_state` ausente em qualquer etapa aleatória (amostragem, `PCA(svd_solver="randomized")`,
  clusterização) — o resultado deixa de ser reprodutível.
- Agregação errada: média de jogadores com minutagens muito diferentes sem normalizar por
  90 minutos, ou join entre tabelas que duplica linhas.

## O que é 🟡 Nit no máximo

Nomes, docstrings, organização de imports, sugestões de refactor, type hints faltando, escolhas
estéticas de cor/legenda nos plots.

## Não reportar

- Formatação e lint: o workflow `ci.yml` já roda `black --check` e `ruff check`.
- Arquivos gerados ou de dados: `uv.lock`, `data/raw/`, `outputs/`, imagens (`*.png`, `*.svg`),
  notebooks executados, `.coverage`, `htmlcov/`.
- Cobertura de teste ausente, exceto no caso listado em "Sempre checar".
- `.venv/` e qualquer `__pycache__/`.

## Sempre checar

- Se o PR altera a conversão de coordenadas ou as dimensões do campo, confirme que existe teste
  em `tests/` cobrindo pelo menos os cantos e o centro do campo. Sem teste é 🔴 Importante.
- Se o PR muda o número de componentes, a lista de features ou o pré-processamento do PCA sem
  mencionar no corpo do PR, aponte como 🟡 Nit: mapas anteriores deixam de ser comparáveis.

## Volume e formato

- No máximo 5 nits por review. Se achou mais, cite "mais N itens semelhantes" no resumo.
- Abra o resumo com uma linha de contagem, por exemplo `2 importantes, 3 nits`.
- Se não houver nada importante, comece o resumo com "Nenhum problema bloqueante."
- Afirmação sobre comportamento precisa de citação `arquivo:linha`, não de inferência pelo nome.
