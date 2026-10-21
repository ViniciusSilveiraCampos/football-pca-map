"""EDA, mapa PCA e experimentos E1–E4. Tudo é gravado em `outputs/`."""

import json
import logging
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
from sklearn.pipeline import Pipeline

from football_pca_map import plots
from football_pca_map.data import FEATURES, GROUP_ORDER, SKILL_ATTRIBUTES
from football_pca_map.model import (
    RANDOM_STATE,
    classifier_pipeline,
    fit_map,
    loadings,
    pca_pipeline,
    split,
)

log = logging.getLogger(__name__)

OUTPUTS = Path("outputs")
FIGURES = OUTPUTS / "figures"
TABLES = OUTPUTS / "tables"
TARGET = "PositionGroup"
E3_COMPONENTS = [2, 3, 5, 10, 20]


def _top(series: pd.Series, n: int = 3) -> list[str]:
    """Atributos de maior |peso|, com o sinal, ex.: ["+BallControl", "-GKDiving"]."""
    top = series.reindex(series.abs().nlargest(n).index)
    return [f"{'+' if v >= 0 else '-'}{name}" for name, v in top.items()]


def eda(raw: pd.DataFrame, players: pd.DataFrame) -> dict:
    """Descobertas da EDA: amostra, classes, correlações e casos estranhos."""
    counts = players[TARGET].value_counts().reindex(GROUP_ORDER)
    plots.class_distribution(counts, FIGURES / "eda_posicoes.png")

    corr = players[FEATURES].corr()
    plots.correlation_heatmap(corr, FIGURES / "eda_correlacao.png")
    upper = np.triu_indices(len(corr), k=1)
    pairs = pd.Series(
        corr.to_numpy()[upper],
        index=pd.MultiIndex.from_arrays(
            [corr.index[upper[0]], corr.columns[upper[1]]], names=["a", "b"]
        ),
    )
    strong = pairs[pairs.abs() >= 0.8]

    plots.two_features_map(
        players,
        "BallControl",
        "StandingTackle",
        FIGURES / "baseline_2_atributos.png",
        "Baseline visual: só 2 dos 37 atributos",
    )

    gk = players[TARGET] == "Goleiro"
    gk_skills = [c for c in SKILL_ATTRIBUTES if c.startswith("GK")]
    other_skills = [c for c in SKILL_ATTRIBUTES if not c.startswith("GK")]

    findings = {
        "linhas_brutas": len(raw),
        "linhas_finais": len(players),
        "linhas_descartadas": len(raw) - len(players),
        "sem_posicao": int(raw["Position"].isna().sum()),
        "posicao_sem_idade_ou_overall": raw.loc[
            raw["Position"].notna() & raw[["Age", "Overall"]].isna().any(axis=1),
            "Name",
        ].tolist(),
        "jogadores_por_grupo": counts.to_dict(),
        "proporcao_maior_classe": round(counts.max() / counts.sum(), 3),
        "pares_correlacao_acima_0_8": len(strong),
        "pares_correlacao_total": len(pairs),
        "media_atributos_gk": {
            "goleiros": round(players.loc[gk, gk_skills].mean().mean(), 1),
            "linha": round(players.loc[~gk, gk_skills].mean().mean(), 1),
        },
        "media_atributos_linha": {
            "goleiros": round(players.loc[gk, other_skills].mean().mean(), 1),
            "linha": round(players.loc[~gk, other_skills].mean().mean(), 1),
        },
    }
    strong.rename("correlacao").to_csv(TABLES / "eda_correlacoes_fortes.csv")
    return findings


def pca_map(train: pd.DataFrame, players: pd.DataFrame) -> dict:
    """Mapa 2D: ajusta no treino, projeta todos os jogadores com `transform`."""
    pipe = fit_map(train, FEATURES)
    pca = pipe.named_steps["pca"]
    coords = pd.DataFrame(
        pipe.transform(players[FEATURES]), index=players.index, columns=["PC1", "PC2"]
    )
    plots.pca_map(
        coords,
        players,
        pca.explained_variance_ratio_,
        FIGURES / "mapa_pca.png",
        f"{len(players):,} jogadores do FIFA 19: {len(FEATURES)} atributos "
        "reduzidos a 2 números (PCA)".replace(",", "."),
    )
    load = loadings(pipe, FEATURES)
    load.to_csv(TABLES / "loadings_pc1_pc2.csv")
    plots.top_loadings(load, "PC1", FIGURES / "loadings_pc1.png")
    plots.top_loadings(load, "PC2", FIGURES / "loadings_pc2.png")

    out = players[["Name", "Club", "Position", TARGET, "Overall"]].join(coords)
    out.to_csv(TABLES / "mapa_coordenadas.csv")
    model_dir = OUTPUTS / "model"
    model_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipe, model_dir / "map_pipeline.joblib")

    return {
        "variancia_pc1": round(float(pca.explained_variance_ratio_[0]), 3),
        "variancia_pc2": round(float(pca.explained_variance_ratio_[1]), 3),
        "pc1_top": _top(load["PC1"], 5),
        "pc2_top": _top(load["PC2"], 5),
    }


def experiment_1(train: pd.DataFrame, test: pd.DataFrame) -> pd.DataFrame:
    """E1: com × sem padronização, só habilidades (0–100) × com altura/peso/reputação."""
    rows = []
    for feature_set, features in [
        ("34 habilidades", SKILL_ATTRIBUTES),
        ("37 atributos", FEATURES),
    ]:
        for scale in (True, False):
            pipe = pca_pipeline(2, scale=scale).fit(train[features])
            ratio = pipe.named_steps["pca"].explained_variance_ratio_
            load = loadings(pipe, features)
            clf = Pipeline(
                [
                    *pca_pipeline(2, scale=scale).steps,
                    ("clf", LogisticRegression(max_iter=2000)),
                ]
            )
            clf.fit(train[features], train[TARGET])
            pred = clf.predict(test[features])
            rows.append(
                {
                    "atributos": feature_set,
                    "padronizado": scale,
                    "var_pc1": round(ratio[0], 3),
                    "var_pc2": round(ratio[1], 3),
                    "pc1_top3": ", ".join(_top(load["PC1"])),
                    "f1_macro_k2": round(
                        f1_score(test[TARGET], pred, average="macro"), 3
                    ),
                }
            )
    return pd.DataFrame(rows)


def experiment_2(train: pd.DataFrame) -> pd.DataFrame:
    """E2: variância explicada por número de componentes."""
    pipe = pca_pipeline(None).fit(train[FEATURES])
    ratio = pipe.named_steps["pca"].explained_variance_ratio_
    plots.scree(ratio, FIGURES / "e2_variancia_explicada.png")
    return pd.DataFrame(
        {
            "k": np.arange(1, len(ratio) + 1),
            "variancia": ratio.round(4),
            "acumulada": np.cumsum(ratio).round(4),
        }
    )


def experiment_3(train: pd.DataFrame, test: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """E3: classificador de posição com 37 atributos × k componentes × Dummy."""
    models = {
        "Dummy (classe mais frequente)": DummyClassifier(strategy="most_frequent")
    }
    models["Regressão logística, 37 atributos"] = classifier_pipeline(None)
    for k in E3_COMPONENTS:
        models[f"Regressão logística, PCA k={k}"] = classifier_pipeline(k)

    rows, predictions = [], {}
    for name, model in models.items():
        start = time.perf_counter()
        model.fit(train[FEATURES], train[TARGET])
        elapsed = time.perf_counter() - start
        pred = model.predict(test[FEATURES])
        predictions[name] = pred
        rows.append(
            {
                "modelo": name,
                "f1_macro": round(f1_score(test[TARGET], pred, average="macro"), 3),
                "acuracia": round(accuracy_score(test[TARGET], pred), 3),
                "tempo_fit_s": round(elapsed, 3),
            }
        )

    for name, filename in [
        ("Regressão logística, 37 atributos", "e3_confusao_37.png"),
        ("Regressão logística, PCA k=2", "e3_confusao_k2.png"),
    ]:
        matrix = pd.DataFrame(
            confusion_matrix(test[TARGET], predictions[name], labels=GROUP_ORDER),
            index=GROUP_ORDER,
            columns=GROUP_ORDER,
        )
        plots.confusion(matrix, FIGURES / filename, name)
    return pd.DataFrame(rows), predictions


def experiment_4(train: pd.DataFrame) -> dict:
    """E4: PCA só com jogadores de linha (sem goleiros)."""
    outfield = train[train[TARGET] != "Goleiro"]
    pipe = fit_map(outfield, FEATURES)
    ratio = pipe.named_steps["pca"].explained_variance_ratio_
    load = loadings(pipe, FEATURES)
    load.to_csv(TABLES / "e4_loadings_sem_goleiros.csv")
    return {
        "var_pc1": round(float(ratio[0]), 3),
        "var_pc2": round(float(ratio[1]), 3),
        "pc1_top": _top(load["PC1"], 5),
        "pc2_top": _top(load["PC2"], 5),
    }


def error_analysis(test: pd.DataFrame, pred: np.ndarray) -> pd.DataFrame:
    """Taxa de erro por posição detalhada (código original do FIFA)."""
    wrong = test[TARGET].to_numpy() != pred
    results = pd.DataFrame(
        {
            "Position": test["Position"],
            "grupo": test[TARGET].astype(str),
            "erro": wrong,
            "previsto": pred,
        },
        index=test.index,
    )
    by_position = results.groupby("Position").agg(
        grupo=("grupo", "first"), jogadores=("erro", "size"), taxa_erro=("erro", "mean")
    )
    by_position["previsto_quando_erra"] = (
        results[results["erro"]]
        .groupby("Position")["previsto"]
        .agg(lambda p: p.mode().iloc[0])
    )
    by_position = by_position.fillna({"previsto_quando_erra": "-"}).sort_values(
        "taxa_erro", ascending=False
    )
    by_position["taxa_erro"] = by_position["taxa_erro"].round(3)
    examples = (
        test.loc[wrong, ["Name", "Position", TARGET, "Overall"]]
        .assign(previsto=pred[wrong])
        .sort_values("Overall", ascending=False)
    )
    examples.head(30).to_csv(TABLES / "erros_exemplos.csv")
    return by_position


def run_all(raw: pd.DataFrame, players: pd.DataFrame) -> dict:
    FIGURES.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)
    train, test = split(players)
    log.info("Treino: %d · Teste: %d", len(train), len(test))

    results = {"random_state": RANDOM_STATE, "treino": len(train), "teste": len(test)}
    results["eda"] = eda(raw, players)
    results["mapa"] = pca_map(train, players)

    e1 = experiment_1(train, test)
    e1.to_csv(TABLES / "e1_padronizacao.csv", index=False)
    e2 = experiment_2(train)
    e2.to_csv(TABLES / "e2_variancia.csv", index=False)
    e3, predictions = experiment_3(train, test)
    e3.to_csv(TABLES / "e3_classificador.csv", index=False)
    results["e4"] = experiment_4(train)

    errors = error_analysis(test, predictions["Regressão logística, 37 atributos"])
    errors.to_csv(TABLES / "erros_por_posicao.csv")

    results["e1"] = e1.to_dict(orient="records")
    results["e2"] = {
        f"k_{int(level * 100)}": int(np.searchsorted(e2["acumulada"], level) + 1)
        for level in (0.8, 0.9)
    }
    results["e3"] = e3.to_dict(orient="records")
    (OUTPUTS / "results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2, default=str)
    )
    return results
