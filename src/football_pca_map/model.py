"""Pipelines de PCA e de classificação de posição.

Regra do projeto: o scaler e o PCA são ajustados (`fit`) só no treino; teste e
jogadores novos passam apenas por `transform`.
"""

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

RANDOM_STATE = 42
TEST_SIZE = 0.25

# O sinal de um autovetor é arbitrário. Para os eixos do mapa terem sempre o mesmo
# significado, cada componente é orientado para que o atributo-âncora tenha peso
# positivo: PC1 positivo = jogador de linha habilidoso, PC2 positivo = defesa.
SIGN_ANCHORS = {0: "BallControl", 1: "StandingTackle"}


def split(players: pd.DataFrame, target: str = "PositionGroup"):
    """Divisão treino/teste estratificada pela posição."""
    return train_test_split(
        players,
        test_size=TEST_SIZE,
        stratify=players[target],
        random_state=RANDOM_STATE,
    )


def pca_pipeline(n_components: int | None = 2, *, scale: bool = True) -> Pipeline:
    steps = [("scaler", StandardScaler())] if scale else []
    steps.append(("pca", PCA(n_components=n_components, random_state=RANDOM_STATE)))
    return Pipeline(steps)


def classifier_pipeline(n_components: int | None = None) -> Pipeline:
    """Regressão logística sobre os atributos padronizados, com PCA opcional."""
    steps = [("scaler", StandardScaler())]
    if n_components is not None:
        steps.append(("pca", PCA(n_components=n_components, random_state=RANDOM_STATE)))
    steps.append(("clf", LogisticRegression(max_iter=2000)))
    return Pipeline(steps)


def fix_component_signs(pca: PCA, feature_names: list[str]) -> PCA:
    """Orienta cada componente de forma determinística (altera o PCA no lugar).

    Componentes com âncora em `SIGN_ANCHORS` ficam com peso positivo no atributo
    âncora; os demais, com peso positivo no atributo de maior |peso|.
    """
    names = list(feature_names)
    for i, component in enumerate(pca.components_):
        anchor = SIGN_ANCHORS.get(i)
        ref = names.index(anchor) if anchor in names else np.argmax(np.abs(component))
        if component[ref] < 0:
            pca.components_[i] = -component
    return pca


def fit_map(train: pd.DataFrame, features: list[str], n_components: int = 2):
    """Ajusta scaler + PCA no treino e orienta os eixos."""
    pipe = pca_pipeline(n_components).fit(train[features])
    fix_component_signs(pipe.named_steps["pca"], features)
    return pipe


def loadings(pipe: Pipeline, features: list[str]) -> pd.DataFrame:
    pca = pipe.named_steps["pca"]
    columns = [f"PC{i + 1}" for i in range(pca.n_components_)]
    return pd.DataFrame(pca.components_.T, index=features, columns=columns)
