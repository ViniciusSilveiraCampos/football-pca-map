import numpy as np
import pandas as pd
import pytest

from football_pca_map.model import (
    classifier_pipeline,
    fit_map,
    fix_component_signs,
    loadings,
    pca_pipeline,
    split,
)

FEATURES = ["BallControl", "StandingTackle", "GKDiving", "Strength"]


@pytest.fixture
def players() -> pd.DataFrame:
    rng = np.random.default_rng(0)
    frame = pd.DataFrame(
        rng.normal(50, 15, size=(192, len(FEATURES))), columns=FEATURES
    )
    frame["PositionGroup"] = np.repeat(
        ["Goleiro", "Defensor", "Meio-campo", "Atacante"], 48
    )
    return frame


def test_split_is_stratified_and_reproducible(players):
    train_a, test_a = split(players)
    train_b, _ = split(players)
    assert train_a.index.equals(train_b.index)
    assert set(test_a["PositionGroup"].value_counts()) == {12}


def test_fit_map_uses_only_train(players):
    train, _ = split(players)
    pipe = fit_map(train, FEATURES)
    np.testing.assert_allclose(pipe.named_steps["scaler"].mean_, train[FEATURES].mean())
    assert not np.allclose(pipe.named_steps["scaler"].mean_, players[FEATURES].mean())


def test_signs_follow_anchors(players):
    pipe = fit_map(players, FEATURES)
    load = loadings(pipe, FEATURES)
    assert load.loc["BallControl", "PC1"] > 0
    assert load.loc["StandingTackle", "PC2"] > 0


def test_sign_flip_is_consistent_with_transform(players):
    """Inverter components_ inverte as coordenadas, e corrigir duas vezes não muda nada."""
    pipe = pca_pipeline(2).fit(players[FEATURES])
    pca = pipe.named_steps["pca"]
    before = pipe.transform(players[FEATURES])
    pca.components_ = -pca.components_
    np.testing.assert_allclose(pipe.transform(players[FEATURES]), -before)

    fix_component_signs(pca, FEATURES)
    fixed = pca.components_.copy()
    fix_component_signs(pca, FEATURES)
    np.testing.assert_array_equal(pca.components_, fixed)


def test_classifier_pipeline_optional_pca():
    assert "pca" not in classifier_pipeline(None).named_steps
    assert classifier_pipeline(3).named_steps["pca"].n_components == 3
