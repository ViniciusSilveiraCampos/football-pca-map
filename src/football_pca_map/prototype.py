"""Lógica do protótipo web, separada da interface Streamlit para poder ser testada.

Tudo é ajustado no treino; jogadores existentes e criados na demo passam só por
`transform`/`predict`.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score
from sklearn.pipeline import Pipeline

from football_pca_map.data import FEATURES
from football_pca_map.model import (
    classifier_pipeline,
    fit_map,
    loadings,
    pca_pipeline,
    split,
)

TARGET = "PositionGroup"
# k avaliados na aba "Quanta informação perdemos?" (None = 37 atributos, sem PCA).
CLASSIFIER_KS = [1, 2, 3, 5, 10, 20, None]

# Grupos de sliders da aba "Crie seu jogador".
ATTRIBUTE_GROUPS = {
    "Ataque": [
        "Finishing",
        "Positioning",
        "ShotPower",
        "LongShots",
        "Volleys",
        "Penalties",
        "HeadingAccuracy",
    ],
    "Técnica e passe": [
        "BallControl",
        "Dribbling",
        "ShortPassing",
        "LongPassing",
        "Crossing",
        "Curve",
        "FKAccuracy",
        "Vision",
        "Composure",
    ],
    "Físico": [
        "Acceleration",
        "SprintSpeed",
        "Agility",
        "Balance",
        "Reactions",
        "Jumping",
        "Stamina",
        "Strength",
    ],
    "Defesa": [
        "Marking",
        "StandingTackle",
        "SlidingTackle",
        "Interceptions",
        "Aggression",
    ],
    "Goleiro": ["GKDiving", "GKHandling", "GKKicking", "GKPositioning", "GKReflexes"],
    "Corpo e fama": ["HeightCm", "WeightKg", "International Reputation"],
}
ATTRIBUTE_RANGES = {
    "HeightCm": (150, 210),
    "WeightKg": (50, 115),
    "International Reputation": (1, 5),
}


@dataclass
class Models:
    players: pd.DataFrame
    coords: pd.DataFrame
    map_pipe: Pipeline
    full_pca: Pipeline
    classifiers: dict[int | None, Pipeline]
    f1_by_k: dict[int | None, float]
    load: pd.DataFrame

    @property
    def variance(self) -> np.ndarray:
        return self.map_pipe.named_steps["pca"].explained_variance_ratio_

    @property
    def cumulative_variance(self) -> np.ndarray:
        return np.cumsum(self.full_pca.named_steps["pca"].explained_variance_ratio_)


def build_models(players: pd.DataFrame, ks=CLASSIFIER_KS) -> Models:
    train, test = split(players)
    map_pipe = fit_map(train, FEATURES)
    coords = pd.DataFrame(
        map_pipe.transform(players[FEATURES]),
        index=players.index,
        columns=["PC1", "PC2"],
    )
    classifiers, f1_by_k = {}, {}
    for k in ks:
        clf = classifier_pipeline(k).fit(train[FEATURES], train[TARGET])
        classifiers[k] = clf
        pred = clf.predict(test[FEATURES])
        f1_by_k[k] = float(f1_score(test[TARGET], pred, average="macro"))
    return Models(
        players=players,
        coords=coords,
        map_pipe=map_pipe,
        full_pca=pca_pipeline(None).fit(train[FEATURES]),
        classifiers=classifiers,
        f1_by_k=f1_by_k,
        load=loadings(map_pipe, FEATURES),
    )


def as_frame(attributes: dict[str, float]) -> pd.DataFrame:
    """Um jogador (dict atributo → valor) como DataFrame de uma linha."""
    return pd.DataFrame([attributes])[FEATURES]


def project(models: Models, attributes: dict[str, float]) -> tuple[float, float]:
    pc1, pc2 = models.map_pipe.transform(as_frame(attributes))[0]
    return float(pc1), float(pc2)


def predict(models: Models, attributes: dict[str, float], k: int | None) -> pd.Series:
    """Probabilidade de cada posição, da maior para a menor."""
    clf = models.classifiers[k]
    proba = clf.predict_proba(as_frame(attributes))[0]
    return pd.Series(proba, index=clf.classes_).sort_values(ascending=False)


def nearest(
    models: Models, attributes: dict[str, float], n: int = 5, exclude: int | None = None
) -> pd.DataFrame:
    """Os n jogadores mais parecidos nos 37 atributos padronizados.

    A distância é medida no espaço completo, não no mapa 2D: dois pontos próximos
    no mapa podem ser diferentes em atributos que o PCA comprimiu.
    """
    scaler = models.map_pipe.named_steps["scaler"]
    everyone = scaler.transform(models.players[FEATURES])
    target = scaler.transform(as_frame(attributes))[0]
    distance = np.linalg.norm(everyone - target, axis=1)
    if exclude is not None:
        distance[models.players.index.get_loc(exclude)] = np.inf
    order = np.argsort(distance)[:n]
    rows = models.players.iloc[order][["Name", "Club", "Position", TARGET, "Overall"]]
    return rows.assign(distancia=distance[order].round(2)).join(models.coords)


def player_attributes(models: Models, index: int) -> dict[str, float]:
    row = models.players.loc[index, FEATURES]
    return {feature: float(value) for feature, value in row.items()}
