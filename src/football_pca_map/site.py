"""Exporta os dados do site de apresentação (`site/data.js`).

Tudo segue a regra do projeto: scaler, PCA e classificadores são ajustados só no
treino; todos os jogadores passam apenas por `transform`.
"""

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.metrics import confusion_matrix, f1_score

from football_pca_map.data import FEATURES, GROUP_ORDER, RAW_PATH
from football_pca_map.model import (
    RANDOM_STATE,
    classifier_pipeline,
    fit_map,
    pca_pipeline,
    split,
)

log = logging.getLogger(__name__)

# Gravado como script (window.PCA_DATA) para o site abrir direto do disco, sem servidor.
SITE_DATA = Path("site/data.js")
TARGET = "PositionGroup"
CLASSIFIER_KS = [1, 2, 3, 5, 10, 20, None]
# Jogadores destacados no mapa e na apresentação.
HIGHLIGHTS = [
    "L. Messi",
    "Cristiano Ronaldo",
    "Neymar Jr",
    "K. De Bruyne",
    "N. Kanté",
    "V. van Dijk",
    "Sergio Ramos",
    "M. Neuer",
    "De Gea",
    "H. Kane",
    "Marcelo",
]


def _classifiers(train: pd.DataFrame, test: pd.DataFrame) -> list[dict]:
    dummy = DummyClassifier(strategy="most_frequent").fit(
        train[FEATURES], train[TARGET]
    )
    rows = [
        {
            "k": 0,
            "pca": False,
            "f1": round(
                f1_score(test[TARGET], dummy.predict(test[FEATURES]), average="macro"),
                3,
            ),
            "confusao": None,
        }
    ]
    for k in CLASSIFIER_KS:
        pipe = classifier_pipeline(k).fit(train[FEATURES], train[TARGET])
        pred = pipe.predict(test[FEATURES])
        matrix = confusion_matrix(test[TARGET], pred, labels=GROUP_ORDER)
        rows.append(
            {
                "k": k if k is not None else len(FEATURES),
                "pca": k is not None,
                "f1": round(f1_score(test[TARGET], pred, average="macro"), 3),
                "confusao": matrix.tolist(),
            }
        )
    return rows


def build(raw: pd.DataFrame, players: pd.DataFrame) -> dict:
    train, test = split(players)
    pipe = fit_map(train, FEATURES)
    scaler, pca = pipe.named_steps["scaler"], pipe.named_steps["pca"]
    coords = pipe.transform(players[FEATURES])

    full = pca_pipeline(None).fit(train[FEATURES])
    ratio = full.named_steps["pca"].explained_variance_ratio_
    eigen = full.named_steps["pca"].explained_variance_

    z_train = scaler.transform(train[FEATURES])
    corr = np.corrcoef(z_train, rowvar=False)

    names = players["Name"].tolist()
    in_train = players.index.isin(train.index)
    return {
        "random_state": RANDOM_STATE,
        "brutas": {"linhas": len(raw), "colunas": raw.shape[1]},
        "finais": len(players),
        "treino": len(train),
        "teste": len(test),
        "features": FEATURES,
        "grupos": GROUP_ORDER,
        "media": scaler.mean_.round(6).tolist(),
        "desvio": scaler.scale_.round(6).tolist(),
        "loadings": pca.components_.round(6).tolist(),
        "variancia": ratio.round(4).tolist(),
        "autovalores": eigen.round(3).tolist(),
        "correlacao": corr.round(2).tolist(),
        "classificador": _classifiers(train, test),
        "destaques": [n for n in HIGHLIGHTS if n in names],
        # Colunas paralelas (formato compacto): um item por jogador.
        "jogadores": {
            "nome": names,
            "clube": players["Club"].fillna("—").tolist(),
            "posicao": players["Position"].tolist(),
            "grupo": [GROUP_ORDER.index(g) for g in players[TARGET]],
            "overall": players["Overall"].fillna(0).astype(int).tolist(),
            "treino": in_train.astype(int).tolist(),
            "pc": coords.round(3).tolist(),
            "atributos": players[FEATURES].round(0).astype(int).to_numpy().tolist(),
        },
        "exemplo_bruto": raw.loc[raw["Name"] == "L. Messi"]
        .iloc[0][["Name", "Height", "Weight", "Position", "Value", "Wage"]]
        .astype(str)
        .to_dict(),
    }


def export(raw: pd.DataFrame, players: pd.DataFrame, path: Path = SITE_DATA) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = build(raw, players)
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    path.write_text(f"window.PCA_DATA = {body};\n")
    log.info("%s (%.1f MB) a partir de %s", path, path.stat().st_size / 1e6, RAW_PATH)
    return path
