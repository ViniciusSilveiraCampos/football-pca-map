"""GIFs animados dos gráficos da análise (matplotlib + Pillow), salvos em docs/img/."""

import logging
from pathlib import Path

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.animation import FuncAnimation, PillowWriter  # noqa: E402
from sklearn.metrics import confusion_matrix, f1_score  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402

from football_pca_map.data import FEATURES, GROUP_ORDER  # noqa: E402
from football_pca_map.model import (  # noqa: E402
    RANDOM_STATE,
    classifier_pipeline,
    fit_map,
    pca_pipeline,
    split,
)
from football_pca_map.plots import (  # noqa: E402
    GROUP_COLORS,
    GROUP_MARKERS,
    INK,
    INK_MUTED,
    SURFACE,
    style_axes,
)

log = logging.getLogger(__name__)

GIF_DIR = Path("docs/img")
TARGET = "PositionGroup"
ACCENT = "#2a78d6"
# Amostra fixa de jogadores nas animações de dispersão: deixa o GIF leve e legível.
SAMPLE_SIZE = 5000
FPS = 15


def _ease(t: np.ndarray | float) -> np.ndarray | float:
    """Suaviza o início e o fim da transição (ease-in-out cúbico)."""
    return np.where(t < 0.5, 4 * t**3, 1 - (-2 * t + 2) ** 3 / 2)


def _timeline(hold_start: int, move: int, hold_end: int) -> np.ndarray:
    """Progresso 0→1 de cada quadro: pausa, transição suavizada, pausa."""
    ramp = _ease(np.linspace(0, 1, move))
    return np.concatenate([np.zeros(hold_start), ramp, np.ones(hold_end)])


def _figure(width: float = 9, height: float = 6.2):
    fig, ax = plt.subplots(figsize=(width, height))
    fig.patch.set_facecolor(SURFACE)
    style_axes(ax)
    return fig, ax


def _save(anim: FuncAnimation, fig: plt.Figure, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    anim.save(
        path,
        writer=PillowWriter(fps=FPS),
        dpi=90,
        savefig_kwargs={"facecolor": SURFACE},
    )
    plt.close(fig)
    log.info("%s (%.1f MB)", path, path.stat().st_size / 1e6)
    return path


def morph_to_pca(players: pd.DataFrame, train: pd.DataFrame, path: Path) -> Path:
    """Os jogadores saindo de 2 atributos brutos e chegando ao mapa PCA."""
    sample = players.sample(SAMPLE_SIZE, random_state=RANDOM_STATE)
    raw = StandardScaler().fit(train[["BallControl", "StandingTackle"]])
    start = raw.transform(sample[["BallControl", "StandingTackle"]]) * 3
    end = fit_map(train, FEATURES).transform(sample[FEATURES])
    progress = _timeline(18, 45, 30)

    lo = np.minimum(start.min(axis=0), end.min(axis=0)) - 0.8
    hi = np.maximum(start.max(axis=0), end.max(axis=0)) + 0.8
    fig, ax = _figure()
    ax.set_xlim(lo[0], hi[0])
    ax.set_ylim(lo[1], hi[1])
    ax.set_xticklabels([])
    ax.set_yticklabels([])
    groups = sample[TARGET].to_numpy()
    scatters = {
        g: ax.scatter(
            [],
            [],
            s=9,
            alpha=0.45,
            color=GROUP_COLORS[g],
            marker=GROUP_MARKERS[g],
            linewidths=0,
            label=g,
        )
        for g in GROUP_ORDER
    }
    legend = ax.legend(loc="upper left", markerscale=2.5, frameon=True)
    for handle in legend.legend_handles:
        handle.set_alpha(1)
    title = ax.set_title("", loc="left", color=INK, fontsize=13)
    xlabel = ax.set_xlabel("", color=INK)
    ylabel = ax.set_ylabel("", color=INK)

    def draw(i):
        t = progress[i]
        coords = (1 - t) * start + t * end
        for g, scatter in scatters.items():
            scatter.set_offsets(coords[groups == g])
        if t < 0.5:
            title.set_text("Antes: só 2 dos 37 atributos")
            xlabel.set_text("BallControl (controle de bola)")
            ylabel.set_text("StandingTackle (desarme)")
        else:
            title.set_text("Depois: os 37 atributos resumidos pelo PCA")
            xlabel.set_text("PC1 (52%): goleiro ←→ jogador de linha habilidoso")
            ylabel.set_text("PC2 (14%): ataque ←→ defesa")
        return [*scatters.values(), title]

    anim = FuncAnimation(fig, draw, frames=len(progress), blit=False)
    return _save(anim, fig, path)


def rotating_axis(players: pd.DataFrame, path: Path) -> Path:
    """Intuição: o PCA gira uma reta até achar a direção de maior variância."""
    outfield = players[players[TARGET] != "Goleiro"]
    sample = outfield.sample(1200, random_state=RANDOM_STATE)
    points = StandardScaler().fit_transform(sample[["Finishing", "StandingTackle"]])
    angles = np.linspace(0, np.pi, 90, endpoint=False)
    directions = np.column_stack([np.cos(angles), np.sin(angles)])
    variances = (points @ directions.T).var(axis=0)
    best = int(np.argmax(variances))

    fig, (ax, ax_var) = plt.subplots(
        1, 2, figsize=(11, 5.2), gridspec_kw={"width_ratios": [1.15, 1]}
    )
    fig.patch.set_facecolor(SURFACE)
    for a in (ax, ax_var):
        style_axes(a)
    ax.scatter(
        points[:, 0], points[:, 1], s=8, alpha=0.25, color=INK_MUTED, linewidths=0
    )
    ax.set_xlim(-3.5, 3.5)
    ax.set_ylim(-3.5, 3.5)
    ax.set_aspect("equal")
    ax.set_xlabel("Finishing (padronizado)", color=INK)
    ax.set_ylabel("StandingTackle (padronizado)", color=INK)
    ax.set_title("Uma reta girando sobre os jogadores de linha", loc="left", color=INK)
    (line,) = ax.plot([], [], color=ACCENT, linewidth=2.5)
    projected = ax.scatter([], [], s=6, color=ACCENT, alpha=0.5, linewidths=0)
    best_line = ax.plot([], [], color=INK, linewidth=2, linestyle="--")[0]

    degrees = np.degrees(angles)
    ax_var.set_xlim(0, 180)
    ax_var.set_ylim(0, variances.max() * 1.15)
    ax_var.set_xlabel("Ângulo da reta (graus)", color=INK)
    ax_var.set_ylabel("Variância dos pontos projetados", color=INK)
    ax_var.set_title("Quanto os jogadores se espalham na reta", loc="left", color=INK)
    (curve,) = ax_var.plot([], [], color=ACCENT, linewidth=2)
    (dot,) = ax_var.plot([], [], "o", color=ACCENT, markersize=8)
    best_vline = ax_var.axvline(
        degrees[best], color=INK, linestyle="--", linewidth=1, visible=False
    )
    best_text = ax_var.text(
        0.03,
        0.95,
        "",
        transform=ax_var.transAxes,
        color=INK,
        va="top",
        fontsize=11,
        fontweight="bold",
    )
    n = len(angles)
    # Depois da volta completa, a reta para na direção de maior variância.
    frames = list(range(n + 25))

    def draw(frame):
        i = min(frame, n - 1)
        d = directions[best if frame >= n else i]
        line.set_data([-4 * d[0], 4 * d[0]], [-4 * d[1], 4 * d[1]])
        projected.set_offsets(np.outer(points @ d, d))
        curve.set_data(degrees[: i + 1], variances[: i + 1])
        j = best if frame >= n else i
        dot.set_data([degrees[j]], [variances[j]])
        if i >= best:
            b = directions[best]
            best_line.set_data([-4 * b[0], 4 * b[0]], [-4 * b[1], 4 * b[1]])
            best_vline.set_visible(True)
            best_text.set_text(
                f"Máximo em {degrees[best]:.0f}°: essa direção\n"
                "é o PC1 destes 2 atributos"
            )
        return [line, projected, curve, dot]

    fig.tight_layout()
    anim = FuncAnimation(fig, draw, frames=frames, blit=False)
    return _save(anim, fig, path)


def scree_build(train: pd.DataFrame, path: Path) -> Path:
    """As barras de variância explicada aparecendo uma a uma."""
    ratio = pca_pipeline(None).fit(train[FEATURES]).named_steps["pca"]
    ratio = ratio.explained_variance_ratio_
    cumulative = np.cumsum(ratio)
    ks = np.arange(1, len(ratio) + 1)
    fig, ax = _figure(9, 5)
    bars = ax.bar(
        ks, np.zeros_like(ratio), color=ACCENT, width=0.7, label="por componente"
    )
    (line,) = ax.plot(
        [], [], color=INK, linewidth=2, marker="o", markersize=4, label="acumulada"
    )
    ax.set_xlim(0, len(ks) + 1)
    ax.set_ylim(0, 1.05)
    ax.yaxis.set_major_formatter(mpl.ticker.PercentFormatter(1))
    ax.set_xlabel("Número de componentes (k)", color=INK)
    ax.set_ylabel("Variância explicada", color=INK)
    ax.legend(loc="center right")
    title = ax.set_title("", loc="left", color=INK, fontsize=13)
    marks = {level: int(np.searchsorted(cumulative, level)) for level in (0.8, 0.9)}
    drawn = set()
    frames = [k for k in range(len(ks)) for _ in range(3 if k < 12 else 1)]
    frames += [len(ks) - 1] * 30

    def draw(k):
        for i, bar in enumerate(bars):
            bar.set_height(ratio[i] if i <= k else 0)
        line.set_data(ks[: k + 1], cumulative[: k + 1])
        title.set_text(
            f"k = {k + 1}: {cumulative[k]:.0%} da informação dos 37 atributos"
        )
        for level, at in marks.items():
            if k >= at and level not in drawn:
                drawn.add(level)
                ax.axhline(level, color=INK_MUTED, linewidth=0.8, linestyle="--")
                ax.annotate(
                    f"{level:.0%} com k = {at + 1}",
                    (len(ks), level),
                    xytext=(0, 4),
                    textcoords="offset points",
                    ha="right",
                    color=INK_MUTED,
                )
        return [*bars, line, title]

    anim = FuncAnimation(fig, draw, frames=frames, blit=False)
    return _save(anim, fig, path)


def classifier_by_k(train: pd.DataFrame, test: pd.DataFrame, path: Path) -> Path:
    """Matriz de confusão e F1 do classificador conforme k cresce."""
    ks = [1, 2, 3, 4, 5, 6, 8, 10, 15, 20, None]
    results = []
    for k in ks:
        pred = (
            classifier_pipeline(k)
            .fit(train[FEATURES], train[TARGET])
            .predict(test[FEATURES])
        )
        matrix = confusion_matrix(test[TARGET], pred, labels=GROUP_ORDER)
        results.append(
            (
                k,
                f1_score(test[TARGET], pred, average="macro"),
                matrix / matrix.sum(axis=1, keepdims=True),
            )
        )

    fig, (ax_f1, ax_cm) = plt.subplots(
        1, 2, figsize=(11, 5), gridspec_kw={"width_ratios": [1, 1]}
    )
    fig.patch.set_facecolor(SURFACE)
    style_axes(ax_f1)
    labels = [str(k) if k else "37\n(todos)" for k in ks]
    xs = np.arange(len(ks))
    ax_f1.set_xticks(xs, labels)
    ax_f1.set_xlim(-0.5, len(ks) - 0.5)
    ax_f1.set_ylim(0, 1)
    ax_f1.yaxis.set_major_formatter(mpl.ticker.PercentFormatter(1))
    ax_f1.set_xlabel("Componentes usados pelo classificador (k)", color=INK)
    ax_f1.set_ylabel("F1-macro no teste", color=INK)
    ax_f1.set_title("Acerto do classificador de posição", loc="left", color=INK)
    (line,) = ax_f1.plot([], [], color=ACCENT, linewidth=2, marker="o")
    value = ax_f1.text(0, 0, "", color=INK, fontsize=11, fontweight="bold", ha="center")

    image = ax_cm.imshow(np.zeros((4, 4)), cmap="Blues", vmin=0, vmax=1)
    ax_cm.set_xticks(range(4), GROUP_ORDER, rotation=25)
    ax_cm.set_yticks(range(4), GROUP_ORDER)
    ax_cm.set_xlabel("Previsto", color=INK)
    ax_cm.set_ylabel("Real", color=INK)
    cm_title = ax_cm.set_title("", loc="left", color=INK)
    cells = [
        [ax_cm.text(j, i, "", ha="center", va="center", fontsize=11) for j in range(4)]
        for i in range(4)
    ]
    frames = [i for i in range(len(ks)) for _ in range(9)] + [len(ks) - 1] * 20

    def draw(i):
        k, f1, share = results[i]
        line.set_data(xs[: i + 1], [r[1] for r in results[: i + 1]])
        value.set_position((xs[i], f1 + 0.05))
        value.set_text(f"{f1:.2f}")
        image.set_data(share)
        cm_title.set_text(
            "Matriz de confusão · " + (f"k = {k}" if k else "37 atributos, sem PCA")
        )
        for r in range(4):
            for c in range(4):
                cells[r][c].set_text(f"{share[r, c]:.0%}")
                cells[r][c].set_color(SURFACE if share[r, c] > 0.5 else INK)
        return [line, value, image]

    fig.tight_layout()
    anim = FuncAnimation(fig, draw, frames=frames, blit=False)
    return _save(anim, fig, path)


def make_all(players: pd.DataFrame, out_dir: Path = GIF_DIR) -> list[Path]:
    train, test = split(players)
    return [
        morph_to_pca(players, train, out_dir / "anim_antes_depois.gif"),
        rotating_axis(players, out_dir / "anim_intuicao_pc1.gif"),
        scree_build(train, out_dir / "anim_variancia.gif"),
        classifier_by_k(train, test, out_dir / "anim_classificador.gif"),
    ]
