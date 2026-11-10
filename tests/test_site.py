import numpy as np
import pandas as pd
import pytest

from football_pca_map import site
from football_pca_map.data import FEATURES, GROUP_ORDER
from football_pca_map.model import classifier_pipeline


@pytest.fixture(scope="module")
def players() -> pd.DataFrame:
    rng = np.random.default_rng(0)
    n_per_group = 40
    frame = pd.DataFrame(
        rng.normal(50, 10, size=(n_per_group * 4, len(FEATURES))), columns=FEATURES
    )
    groups = np.repeat(GROUP_ORDER, n_per_group)
    gk_columns = [c for c in FEATURES if c.startswith("GK")]
    frame.loc[groups == "Goleiro", gk_columns] += 40
    frame["PositionGroup"] = pd.Categorical(groups, categories=GROUP_ORDER)
    return frame


def _proba_from_export(model: dict, x: np.ndarray) -> np.ndarray:
    """A mesma conta que o site faz no navegador (site/app.js)."""
    h = (x - np.array(model["media"])) / np.array(model["desvio"])
    if model["pca"] is not None:
        h = (h - np.array(model["pca_media"])) @ np.array(model["pca"]).T
    logits = h @ np.array(model["coef"]).T + np.array(model["intercepto"])
    exp = np.exp(logits - logits.max(axis=1, keepdims=True))
    return exp / exp.sum(axis=1, keepdims=True)


@pytest.mark.parametrize("k", [None, 2, 10])
def test_exported_model_reproduces_predict_proba(players, k):
    pipe = classifier_pipeline(k).fit(players[FEATURES], players["PositionGroup"])
    model = site.position_model(pipe)
    x = players[FEATURES].to_numpy()[:25]

    expected = pipe.predict_proba(players[FEATURES].iloc[:25])
    assert np.allclose(_proba_from_export(model, x), expected, atol=1e-4)
    assert model["k"] == (k or len(FEATURES))
    assert sorted(model["classes"]) == list(range(len(GROUP_ORDER)))
