"""Figuras do projeto (matplotlib, salvas em PNG)."""

from pathlib import Path

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from football_pca_map.data import GROUP_ORDER  # noqa: E402

# Paleta categórica validada (todas as combinações de pares, modo claro). A separação
# para daltonismo deutan fica entre 6 e 8, então cada posição também tem marcador
# próprio e rótulo direto no centro do grupo.
GROUP_COLORS = {
    "Goleiro": "#6250d6",
    "Defensor": "#1baf7a",
    "Meio-campo": "#eda100",
    "Atacante": "#e34948",
}
GROUP_MARKERS = {"Goleiro": "o", "Defensor": "s", "Meio-campo": "^", "Atacante": "D"}
INK = "#0b0b0b"
INK_MUTED = "#52514e"
GRID = "#e4e3df"
SURFACE = "#fcfcfb"

# Jogador destacado → deslocamento do nome em pontos (evita sobreposição).
HIGHLIGHT_PLAYERS = {
    "L. Messi": (6, -10),
    "Cristiano Ronaldo": (6, 4),
    "Neymar Jr": (-6, 6),
    "K. De Bruyne": (6, 4),
    "V. van Dijk": (6, 4),
    "N. Kanté": (6, 4),
    "Marcelo": (6, 4),
    "Alisson": (6, 4),
    "De Gea": (6, -10),
}
# Onde fica o rótulo de cada grupo, em quantis (PC1, PC2) dos pontos do grupo:
# acima dos goleiros e defensores, abaixo dos atacantes, à direita dos meias.
GROUP_LABEL_QUANTILES = {
    "Goleiro": (0.5, 0.995),
    "Defensor": (0.3, 0.995),
    "Meio-campo": (0.995, 0.5),
    "Atacante": (0.5, 0.005),
}


def style_axes(ax: plt.Axes) -> None:
    ax.set_facecolor(SURFACE)
    ax.grid(color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(INK_MUTED)
    ax.tick_params(colors=INK_MUTED)


def _save(fig: plt.Figure, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)
    return path


def pca_map(
    coords: pd.DataFrame,
    players: pd.DataFrame,
    variance: np.ndarray,
    path: Path,
    title: str,
) -> Path:
    """Mapa PC1 × PC2 colorido por posição, com jogadores conhecidos destacados.

    `players` precisa das colunas `PositionGroup` e `Name`.
    """
    groups, names = players["PositionGroup"], players["Name"]
    fig, ax = plt.subplots(figsize=(10, 7))
    fig.patch.set_facecolor(SURFACE)
    style_axes(ax)
    for group in GROUP_ORDER:
        mask = groups == group
        ax.scatter(
            coords.loc[mask, "PC1"],
            coords.loc[mask, "PC2"],
            s=7,
            alpha=0.3,
            color=GROUP_COLORS[group],
            marker=GROUP_MARKERS[group],
            linewidths=0,
            label=f"{group} ({mask.sum():,})".replace(",", "."),
        )
        qx, qy = GROUP_LABEL_QUANTILES[group]
        anchor = (
            coords.loc[mask, "PC1"].quantile(qx),
            coords.loc[mask, "PC2"].quantile(qy),
        )
        ax.annotate(
            group,
            anchor,
            fontsize=11,
            fontweight="bold",
            color=INK,
            ha="center",
            va="bottom" if qy > 0.9 else "top" if qy < 0.1 else "center",
            bbox={
                "boxstyle": "round,pad=0.25",
                "fc": SURFACE,
                "ec": "none",
                "alpha": 0.8,
            },
        )

    for name, offset in HIGHLIGHT_PLAYERS.items():
        hit = names == name
        if not hit.any():
            continue
        x, y = coords.loc[hit, ["PC1", "PC2"]].iloc[0]
        ax.scatter(x, y, s=40, color=INK, edgecolors=SURFACE, linewidths=1.5, zorder=3)
        ax.annotate(
            name,
            (x, y),
            xytext=offset,
            textcoords="offset points",
            ha="right" if offset[0] < 0 else "left",
            fontsize=9,
            color=INK,
            zorder=4,
        )

    ax.set_xlabel(
        f'PC1 ({variance[0]:.0%} da variância): "goleiro"  ←→  '
        '"jogador de linha habilidoso"',
        color=INK,
    )
    ax.set_ylabel(f'PC2 ({variance[1]:.0%}): "ataque"  ←→  "defesa"', color=INK)
    ax.set_title(title, color=INK, loc="left")
    legend = ax.legend(loc="upper left", markerscale=3, frameon=True)
    for handle in legend.legend_handles:
        handle.set_alpha(1)
    return _save(fig, path)


def two_features_map(
    players: pd.DataFrame, x: str, y: str, path: Path, title: str
) -> Path:
    """Baseline visual: dispersão de dois atributos originais."""
    coords = players[[x, y]].rename(columns={x: "PC1", y: "PC2"})
    fig, ax = plt.subplots(figsize=(10, 7))
    fig.patch.set_facecolor(SURFACE)
    style_axes(ax)
    for group in GROUP_ORDER:
        mask = players["PositionGroup"] == group
        ax.scatter(
            coords.loc[mask, "PC1"],
            coords.loc[mask, "PC2"],
            s=7,
            alpha=0.3,
            color=GROUP_COLORS[group],
            marker=GROUP_MARKERS[group],
            linewidths=0,
            label=group,
        )
    ax.set_xlabel(x, color=INK)
    ax.set_ylabel(y, color=INK)
    ax.set_title(title, color=INK, loc="left")
    legend = ax.legend(loc="upper left", markerscale=3)
    for handle in legend.legend_handles:
        handle.set_alpha(1)
    return _save(fig, path)


def class_distribution(counts: pd.Series, path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(7, 4))
    fig.patch.set_facecolor(SURFACE)
    style_axes(ax)
    ax.grid(axis="y", visible=False)
    bars = ax.barh(
        counts.index[::-1],
        counts.to_numpy()[::-1],
        color=[GROUP_COLORS[g] for g in counts.index[::-1]],
        height=0.6,
    )
    ax.bar_label(
        bars,
        labels=[f"{v:,}".replace(",", ".") for v in counts.to_numpy()[::-1]],
        padding=4,
        color=INK,
    )
    ax.set_xlabel("Jogadores", color=INK)
    ax.set_title("Jogadores por grupo de posição", color=INK, loc="left")
    return _save(fig, path)


def correlation_heatmap(corr: pd.DataFrame, path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(11, 9.5))
    fig.patch.set_facecolor(SURFACE)
    image = ax.imshow(corr.to_numpy(), cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xticks(range(len(corr)), corr.columns, rotation=90, fontsize=7)
    ax.set_yticks(range(len(corr)), corr.index, fontsize=7)
    ax.set_title("Correlação de Pearson entre os atributos", color=INK, loc="left")
    fig.colorbar(image, ax=ax, fraction=0.04, label="correlação")
    return _save(fig, path)


def scree(variance_ratio: np.ndarray, path: Path) -> Path:
    cumulative = np.cumsum(variance_ratio)
    ks = np.arange(1, len(variance_ratio) + 1)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    fig.patch.set_facecolor(SURFACE)
    style_axes(ax)
    ax.bar(ks, variance_ratio, color="#2a78d6", width=0.7, label="por componente")
    ax.plot(
        ks,
        cumulative,
        color=INK,
        linewidth=2,
        marker="o",
        markersize=4,
        label="acumulada",
    )
    for level in (0.8, 0.9):
        k = int(np.searchsorted(cumulative, level) + 1)
        ax.axhline(level, color=INK_MUTED, linewidth=0.8, linestyle="--")
        ax.annotate(
            f"{level:.0%} com k = {k}",
            (len(ks), level),
            xytext=(0, 4),
            textcoords="offset points",
            ha="right",
            color=INK_MUTED,
        )
    ax.set_xlabel("Número de componentes (k)", color=INK)
    ax.set_ylabel("Variância explicada", color=INK)
    ax.yaxis.set_major_formatter(mpl.ticker.PercentFormatter(1))
    ax.set_title("Quanta informação cada componente guarda", color=INK, loc="left")
    ax.legend(loc="center right")
    return _save(fig, path)


def top_loadings(load: pd.DataFrame, component: str, path: Path, n: int = 10) -> Path:
    """Os n atributos de maior |peso| no componente, com o sinal preservado."""
    top = load[component].reindex(load[component].abs().nlargest(n).index)[::-1]
    fig, ax = plt.subplots(figsize=(7, 4.5))
    fig.patch.set_facecolor(SURFACE)
    style_axes(ax)
    ax.grid(axis="y", visible=False)
    colors = ["#2a78d6" if v >= 0 else "#eb6834" for v in top]
    ax.barh(top.index, top.to_numpy(), color=colors, height=0.6)
    ax.axvline(0, color=INK_MUTED, linewidth=0.8)
    ax.set_xlabel(
        f"Peso no {component} (azul = positivo, laranja = negativo)", color=INK
    )
    ax.set_title(f"O que forma o {component}", color=INK, loc="left")
    return _save(fig, path)


def confusion(matrix: pd.DataFrame, path: Path, title: str) -> Path:
    share = matrix.div(matrix.sum(axis=1), axis=0)
    fig, ax = plt.subplots(figsize=(6, 5))
    fig.patch.set_facecolor(SURFACE)
    ax.imshow(share.to_numpy(), cmap="Blues", vmin=0, vmax=1)
    ax.set_xticks(range(len(matrix)), matrix.columns, rotation=30)
    ax.set_yticks(range(len(matrix)), matrix.index)
    for i in range(len(matrix)):
        for j in range(len(matrix)):
            value = share.iloc[i, j]
            ax.text(
                j,
                i,
                f"{matrix.iloc[i, j]}\n{value:.0%}",
                ha="center",
                va="center",
                fontsize=9,
                color=SURFACE if value > 0.5 else INK,
            )
    ax.set_xlabel("Previsto", color=INK)
    ax.set_ylabel("Real", color=INK)
    ax.set_title(title, color=INK, loc="left")
    return _save(fig, path)
