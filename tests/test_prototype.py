import numpy as np
import pandas as pd
import pytest

from football_pca_map import prototype
from football_pca_map.data import FEATURES, GROUP_ORDER


@pytest.fixture(scope="module")
def models() -> prototype.Models:
    rng = np.random.default_rng(0)
    n_per_group = 40
    players = pd.DataFrame(
        rng.normal(50, 10, size=(n_per_group * 4, len(FEATURES))), columns=FEATURES
    )
    groups = np.repeat(GROUP_ORDER, n_per_group)
    # Goleiros com atributos de goleiro bem mais altos, para o PCA ter estrutura.
    gk_columns = [c for c in FEATURES if c.startswith("GK")]
    players.loc[groups == "Goleiro", gk_columns] += 40
    players["PositionGroup"] = pd.Categorical(groups, categories=GROUP_ORDER)
    players["Name"] = [f"Jogador {i}" for i in range(len(players))]
    players["Club"] = "Clube"
    players["Position"] = "CM"
    players["Overall"] = 70.0
    return prototype.build_models(players, ks=[2, None])


def test_attribute_groups_cover_every_feature_once():
    grouped = [f for features in prototype.ATTRIBUTE_GROUPS.values() for f in features]
    assert sorted(grouped) == sorted(FEATURES)


def test_project_matches_map_coordinates(models):
    index = models.players.index[0]
    attributes = prototype.player_attributes(models, index)
    assert prototype.project(models, attributes) == pytest.approx(
        tuple(models.coords.loc[index])
    )


def test_predict_returns_sorted_probabilities(models):
    attributes = prototype.player_attributes(models, models.players.index[0])
    for k in (2, None):
        proba = prototype.predict(models, attributes, k)
        assert set(proba.index) == set(GROUP_ORDER)
        assert proba.sum() == pytest.approx(1)
        assert proba.is_monotonic_decreasing


def test_nearest_excludes_the_player_itself(models):
    index = models.players.index[5]
    attributes = prototype.player_attributes(models, index)
    assert prototype.nearest(models, attributes, n=1).index[0] == index
    others = prototype.nearest(models, attributes, n=3, exclude=index)
    assert index not in others.index
    assert others["distancia"].is_monotonic_increasing


def test_cumulative_variance_reaches_one(models):
    assert models.cumulative_variance[-1] == pytest.approx(1)
