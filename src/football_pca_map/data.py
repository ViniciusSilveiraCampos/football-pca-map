"""Download, leitura e limpeza do FIFA 19 Complete Player Dataset."""

import hashlib
import logging
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

log = logging.getLogger(__name__)

KAGGLE_URL = (
    "https://www.kaggle.com/api/v1/datasets/download/"
    "javagarm/fifa-19-complete-player-dataset"
)
# O zip do Kaggle traz um único arquivo chamado kl.csv; salvamos como data.csv.
RAW_PATH = Path("data/raw/data.csv")
RAW_SHA256 = "ea6f8516b3b6f2f80d90a4e29760917ddfb8e9a5b76a13548c7f4e9d4ae8279b"
# O CSV foi gravado em Windows-1252 (o "€" dos valores é o byte 0x80).
RAW_ENCODING = "cp1252"

SKILL_ATTRIBUTES = [
    "Crossing",
    "Finishing",
    "HeadingAccuracy",
    "ShortPassing",
    "Volleys",
    "Dribbling",
    "Curve",
    "FKAccuracy",
    "LongPassing",
    "BallControl",
    "Acceleration",
    "SprintSpeed",
    "Agility",
    "Reactions",
    "Balance",
    "ShotPower",
    "Jumping",
    "Stamina",
    "Strength",
    "LongShots",
    "Aggression",
    "Interceptions",
    "Positioning",
    "Vision",
    "Penalties",
    "Composure",
    "Marking",
    "StandingTackle",
    "SlidingTackle",
    "GKDiving",
    "GKHandling",
    "GKKicking",
    "GKPositioning",
    "GKReflexes",
]
# Os 34 atributos de habilidade (escala 0–100) + 3 em outras escalas. Essa combinação
# reproduz a figura de referência do grupo (PC1 52%, PC2 14%, 18.147 jogadores).
EXTRA_ATTRIBUTES = ["HeightCm", "WeightKg", "International Reputation"]
FEATURES = SKILL_ATTRIBUTES + EXTRA_ATTRIBUTES

POSITION_GROUPS = {
    "Goleiro": ["GK"],
    "Defensor": ["CB", "LCB", "RCB", "LB", "RB", "LWB", "RWB"],
    "Meio-campo": [
        "CDM",
        "LDM",
        "RDM",
        "CM",
        "LCM",
        "RCM",
        "CAM",
        "LAM",
        "RAM",
        "LM",
        "RM",
    ],
    "Atacante": ["ST", "LS", "RS", "CF", "LF", "RF", "LW", "RW"],
}
POSITION_TO_GROUP = {
    code: group for group, codes in POSITION_GROUPS.items() for code in codes
}
GROUP_ORDER = list(POSITION_GROUPS)


def download_raw(path: Path = RAW_PATH) -> Path:
    """Baixa o dataset do Kaggle (endpoint público, sem login) e confere o hash."""
    path.parent.mkdir(parents=True, exist_ok=True)
    zip_path = path.with_suffix(".zip")
    log.info("Baixando %s", KAGGLE_URL)
    urllib.request.urlretrieve(KAGGLE_URL, zip_path)  # noqa: S310 (URL fixa)
    with zipfile.ZipFile(zip_path) as zf:
        (member,) = zf.namelist()
        path.write_bytes(zf.read(member))
    zip_path.unlink()

    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != RAW_SHA256:
        log.warning("SHA-256 diferente do esperado: %s", digest)
    return path


def load_raw(path: Path = RAW_PATH) -> pd.DataFrame:
    return pd.read_csv(path, encoding=RAW_ENCODING, index_col=0)


def height_to_cm(height: pd.Series) -> pd.Series:
    """Converte "5'7" (pés'polegadas) para centímetros."""
    parts = height.str.split("'", expand=True).astype(float)
    return parts[0] * 30.48 + parts[1] * 2.54


def weight_to_kg(weight: pd.Series) -> pd.Series:
    """Converte "159lbs" para quilogramas."""
    return weight.str.removesuffix("lbs").astype(float) * 0.45359237


def prepare(raw: pd.DataFrame) -> pd.DataFrame:
    """Limpa o dataset bruto: converte unidades, agrupa posições e remove ausentes.

    Toda linha descartada é registrada no log, com a contagem e o motivo.
    """
    players = raw.copy()
    players["HeightCm"] = height_to_cm(players["Height"])
    players["WeightKg"] = weight_to_kg(players["Weight"])
    players["PositionGroup"] = players["Position"].map(POSITION_TO_GROUP)

    unknown = players["Position"].notna() & players["PositionGroup"].isna()
    if unknown.any():
        codes = sorted(players.loc[unknown, "Position"].unique())
        raise ValueError(f"Posições sem grupo definido: {codes}")

    missing = players[FEATURES + ["PositionGroup"]].isna().any(axis=1)
    log.info(
        "Descartando %d de %d jogadores sem posição ou com atributos ausentes",
        missing.sum(),
        len(players),
    )
    players = players.loc[~missing].copy()
    players["PositionGroup"] = pd.Categorical(
        players["PositionGroup"], categories=GROUP_ORDER
    )
    return players
