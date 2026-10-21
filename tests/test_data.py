import numpy as np
import pandas as pd
import pytest

from football_pca_map.data import (
    FEATURES,
    GROUP_ORDER,
    POSITION_TO_GROUP,
    height_to_cm,
    prepare,
    weight_to_kg,
)

# Os 27 códigos de posição presentes no FIFA 19.
FIFA_POSITIONS = (
    "GK CB LCB RCB LB RB LWB RWB CDM LDM RDM CM LCM RCM CAM LAM RAM LM RM "
    "ST LS RS CF LF RF LW RW"
).split()


def make_raw(positions: list[str | None]) -> pd.DataFrame:
    rng = np.random.default_rng(0)
    n = len(positions)
    raw = pd.DataFrame(
        rng.integers(1, 99, size=(n, len(FEATURES))).astype(float), columns=FEATURES
    )
    raw = raw.drop(columns=["HeightCm", "WeightKg"])
    raw["Height"] = "5'11"
    raw["Weight"] = "170lbs"
    raw["Position"] = positions
    raw["Name"] = [f"Jogador {i}" for i in range(n)]
    return raw


def test_height_to_cm():
    assert height_to_cm(pd.Series(["6'0", "5'7"])).tolist() == pytest.approx(
        [182.88, 170.18]
    )


def test_weight_to_kg():
    assert weight_to_kg(pd.Series(["159lbs"])).iloc[0] == pytest.approx(72.12, abs=0.01)


def test_all_fifa_positions_have_a_group():
    assert set(FIFA_POSITIONS) == set(POSITION_TO_GROUP)
    assert set(POSITION_TO_GROUP.values()) == set(GROUP_ORDER)


def test_prepare_drops_missing_and_maps_groups():
    raw = make_raw(["GK", "CB", None, "CM", "ST"])
    raw.loc[3, "Finishing"] = np.nan

    players = prepare(raw)

    assert players.index.tolist() == [0, 1, 4]
    assert players["PositionGroup"].tolist() == ["Goleiro", "Defensor", "Atacante"]
    assert players["HeightCm"].iloc[0] == pytest.approx(180.34)
    assert not players[FEATURES].isna().any().any()


def test_prepare_rejects_unknown_position():
    with pytest.raises(ValueError, match="XX"):
        prepare(make_raw(["GK", "XX"]))
