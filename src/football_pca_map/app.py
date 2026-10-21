"""Protótipo web: Mapa dos Jogadores do FIFA 19.

Executar com:  uv run streamlit run src/football_pca_map/app.py
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from football_pca_map import prototype
from football_pca_map.data import FEATURES, GROUP_ORDER, RAW_PATH, load_raw, prepare
from football_pca_map.plots import GROUP_COLORS

TARGET = prototype.TARGET
SYMBOLS = {
    "Goleiro": "circle",
    "Defensor": "square",
    "Meio-campo": "triangle-up",
    "Atacante": "diamond",
}
INK = "#0b0b0b"
POSITIVE, NEGATIVE = "#2a78d6", "#eb6834"

# Casos em que o classificador erra (ver outputs/tables/erros_exemplos.csv) e um
# jogador inventado, para mostrar limitações na demo.
CHALLENGES = [
    ("Isco", "LW", "Ponta-esquerda com perfil de meia armador."),
    ("R. Sterling", "RW", "Ponta-direita que também cria jogadas."),
    ("I. Gueye", "RDM", "Volante marcador: desarma como um zagueiro."),
    ("A. Florenzi", "RB", "Lateral que joga como meia de lado."),
    ("José Callejón", "RM", "Meia de lado que ataca como ponta."),
]

st.set_page_config(page_title="Mapa dos Jogadores", layout="wide")


@st.cache_resource(show_spinner="Treinando o PCA e os classificadores…")
def load_models() -> prototype.Models:
    return prototype.build_models(prepare(load_raw()))


@st.cache_resource
def player_labels() -> dict[int, str]:
    """Rótulos das listas de busca, montados uma vez (são 18 mil opções)."""
    players = load_models().players
    labels = (
        players["Name"]
        + " · "
        + players["Club"].fillna("sem clube")
        + " ("
        + players["Position"]
        + ", "
        + players["Overall"].map("{:.0f}".format)
        + ")"
    )
    return labels.to_dict()


def base_map(models: prototype.Models, height: int = 560) -> go.Figure:
    fig = go.Figure()
    players, coords = models.players, models.coords
    for group in GROUP_ORDER:
        mask = players[TARGET] == group
        fig.add_trace(
            go.Scattergl(
                x=coords.loc[mask, "PC1"],
                y=coords.loc[mask, "PC2"],
                mode="markers",
                name=group,
                marker={
                    "color": GROUP_COLORS[group],
                    "symbol": SYMBOLS[group],
                    "size": 5,
                    "opacity": 0.35,
                },
                customdata=players.loc[mask, ["Name", "Club", "Position", "Overall"]],
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>%{customdata[1]}<br>"
                    "Posição: %{customdata[2]} · Overall %{customdata[3]:.0f}"
                    "<br>PC1 %{x:.2f} · PC2 %{y:.2f}<extra></extra>"
                ),
            )
        )
    variance = models.variance
    fig.update_layout(
        height=height,
        margin={"l": 10, "r": 10, "t": 30, "b": 10},
        legend={"orientation": "h", "y": 1.06, "x": 0, "itemsizing": "constant"},
        xaxis_title=f"PC1 ({variance[0]:.0%}): goleiro ←→ jogador de linha habilidoso",
        yaxis_title=f"PC2 ({variance[1]:.0%}): ataque ←→ defesa",
    )
    return fig


def mark(fig: go.Figure, points: pd.DataFrame, name: str, color: str, size: int):
    """Destaca pontos (colunas PC1, PC2, label) por cima do mapa."""
    fig.add_trace(
        go.Scatter(
            x=points["PC1"],
            y=points["PC2"],
            mode="markers+text",
            name=name,
            text=points["label"],
            textposition="top center",
            textfont={"size": 13, "color": color},
            marker={
                "color": color,
                "size": size,
                "symbol": "star" if size > 14 else "circle-open",
                "line": {"width": 2, "color": color},
            },
            hoverinfo="text",
        )
    )


def probability_chart(proba: pd.Series) -> go.Figure:
    proba = proba.reindex(GROUP_ORDER)
    fig = go.Figure(
        go.Bar(
            x=proba.to_numpy(),
            y=proba.index,
            orientation="h",
            marker_color=[GROUP_COLORS[g] for g in proba.index],
            text=[f"{p:.0%}" for p in proba],
            textposition="outside",
        )
    )
    fig.update_layout(
        height=200,
        margin={"l": 10, "r": 40, "t": 10, "b": 10},
        xaxis={"range": [0, 1.1], "tickformat": ".0%", "showgrid": False},
        yaxis={"autorange": "reversed"},
        showlegend=False,
    )
    return fig


def show_prediction(
    models: prototype.Models, attributes: dict[str, float], key: str, charts=True
):
    full = prototype.predict(models, attributes, None)
    k2 = prototype.predict(models, attributes, 2)
    col_full, col_k2 = st.columns(2)
    with col_full:
        st.metric("Com os 37 atributos", full.index[0], f"{full.iloc[0]:.0%} de chance")
        if charts:
            st.plotly_chart(probability_chart(full), key=f"{key}_full")
    with col_k2:
        st.metric("Só com PC1 e PC2", k2.index[0], f"{k2.iloc[0]:.0%} de chance")
        if charts:
            st.plotly_chart(probability_chart(k2), key=f"{key}_k2")
    st.caption(
        "A porcentagem é a confiança do modelo, não uma certeza: "
        "ela vem dos padrões dos jogadores de treino."
    )


@st.fragment
def tab_map(models: prototype.Models):
    st.subheader("Cada ponto é um jogador")
    st.write(
        "O PCA resumiu os 37 atributos de cada jogador em só **2 números**. "
        "Jogadores parecidos ficam perto. Passe o mouse para ver quem é quem."
    )
    players = models.players
    by_overall = players.sort_values("Overall", ascending=False).index
    col_search, col_n = st.columns([3, 1])
    with col_search:
        index = st.selectbox(
            "Busque um jogador",
            by_overall,
            format_func=player_labels().__getitem__,
            key="search",
        )
    with col_n:
        n = st.slider("Parecidos", 1, 10, 5)

    attributes = prototype.player_attributes(models, index)
    neighbors = prototype.nearest(models, attributes, n=n, exclude=index)
    fig = base_map(models)
    mark(fig, neighbors.assign(label=""), "Mais parecidos", INK, 12)
    chosen = models.coords.loc[[index]].assign(label=players.loc[index, "Name"])
    mark(fig, chosen, "Selecionado", INK, 18)
    st.plotly_chart(fig, key="map")

    st.markdown(f"**Os {n} mais parecidos com {players.loc[index, 'Name']}**")
    st.dataframe(
        neighbors[["Name", "Club", "Position", TARGET, "Overall", "distancia"]],
        hide_index=True,
        column_config={TARGET: "Grupo", "distancia": "Distância"},
    )
    st.caption(
        "A distância é medida nos 37 atributos, não no mapa: o mapa guarda "
        f"{models.cumulative_variance[1]:.0%} da informação, então dois pontos "
        "próximos no mapa ainda podem ser diferentes."
    )


def _load_template():
    attributes = prototype.player_attributes(
        st.session_state["models"], st.session_state["template"]
    )
    for feature, value in attributes.items():
        st.session_state[f"attr_{feature}"] = int(round(value))


@st.fragment
def tab_create(models: prototype.Models):
    st.subheader("Crie seu jogador")
    st.write(
        "Comece de um jogador real e mexa nos atributos. O modelo **não é "
        "retreinado**: o jogador novo é só projetado no mapa que já existe."
    )
    players = models.players
    by_overall = players.sort_values("Overall", ascending=False).index
    if "template" not in st.session_state:
        st.session_state["template"] = by_overall[0]
        _load_template()
    st.selectbox(
        "Começar de",
        by_overall,
        format_func=player_labels().__getitem__,
        key="template",
        on_change=_load_template,
    )

    col_result, col_sliders = st.columns([3, 2])
    # Os sliders rolam dentro da própria caixa, para o mapa continuar visível.
    with col_sliders, st.container(height=600):
        for group, features in prototype.ATTRIBUTE_GROUPS.items():
            with st.expander(group, expanded=group in ("Goleiro", "Ataque")):
                for feature in features:
                    low, high = prototype.ATTRIBUTE_RANGES.get(feature, (1, 99))
                    st.slider(feature, low, high, key=f"attr_{feature}")
    attributes = {f: float(st.session_state[f"attr_{f}"]) for f in FEATURES}

    with col_result:
        pc1, pc2 = prototype.project(models, attributes)
        show_prediction(models, attributes, "create", charts=False)
        fig = base_map(models, height=430)
        template = players.loc[st.session_state["template"]]
        original = models.coords.loc[[st.session_state["template"]]].assign(
            label=f"{template['Name']} (original)"
        )
        mark(fig, original, "Original", "#52514e", 12)
        created = pd.DataFrame({"PC1": [pc1], "PC2": [pc2], "label": ["Seu jogador"]})
        mark(fig, created, "Seu jogador", INK, 20)
        st.plotly_chart(fig, key="create_map")
        st.markdown(f"**Posição no mapa:** PC1 = {pc1:.2f} · PC2 = {pc2:.2f}")


def loadings_chart(series: pd.Series, n: int = 10) -> go.Figure:
    top = series.reindex(series.abs().nlargest(n).index)
    fig = go.Figure(
        go.Bar(
            x=top.to_numpy(),
            y=top.index,
            orientation="h",
            marker_color=[POSITIVE if v >= 0 else NEGATIVE for v in top],
        )
    )
    fig.update_layout(
        height=360,
        margin={"l": 10, "r": 10, "t": 10, "b": 10},
        yaxis={"autorange": "reversed"},
        xaxis_title="Peso no componente (azul = empurra para +, laranja = para −)",
    )
    return fig


@st.fragment
def tab_axes(models: prototype.Models):
    st.subheader("O que significa cada eixo?")
    st.write(
        "Cada eixo é uma **receita**: uma soma de todos os atributos, cada um com "
        "um peso. Os atributos com peso maior são os que mais mexem no eixo."
    )
    variance = models.variance
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            f"**PC1 · {variance[0]:.0%} da informação**  \n"
            "Direita: controle de bola, drible e passe altos. "
            "Esquerda: atributos de goleiro."
        )
        st.plotly_chart(loadings_chart(models.load["PC1"]), key="pc1")
    with col2:
        st.markdown(
            f"**PC2 · {variance[1]:.0%} da informação**  \n"
            "Em cima: desarme, marcação e força. "
            "Embaixo: finalização, agilidade e equilíbrio."
        )
        st.plotly_chart(loadings_chart(models.load["PC2"]), key="pc2")
    st.caption(
        "O sinal de um componente é arbitrário; fixamos que PC1 positivo = controle "
        "de bola alto e PC2 positivo = desarme alto, para o mapa não 'virar'."
    )


@st.fragment
def tab_information(models: prototype.Models):
    st.subheader("Quanta informação perdemos?")
    cumulative = models.cumulative_variance
    k = st.slider("Número de componentes (k)", 1, len(cumulative), 2)
    col_var, col_clf = st.columns(2)
    with col_var:
        st.metric(f"Informação guardada com k = {k}", f"{cumulative[k - 1]:.0%}")
        fig = go.Figure(
            go.Scatter(
                x=list(range(1, len(cumulative) + 1)),
                y=cumulative,
                mode="lines+markers",
                line={"color": POSITIVE, "width": 2},
            )
        )
        fig.add_trace(
            go.Scatter(
                x=[k],
                y=[cumulative[k - 1]],
                mode="markers",
                marker={"size": 14, "color": INK},
            )
        )
        fig.update_layout(
            height=320,
            showlegend=False,
            margin={"l": 10, "r": 10, "t": 10, "b": 10},
            xaxis_title="k",
            yaxis={
                "tickformat": ".0%",
                "range": [0, 1.02],
                "title": "variância acumulada",
            },
        )
        st.plotly_chart(fig, key="scree")
    with col_clf:
        st.markdown("**Acerto do classificador de posição (F1-macro, teste)**")
        rows = [
            {
                "Entrada": "37 atributos" if kk is None else f"PCA, k = {kk}",
                "F1-macro": round(f1, 3),
            }
            for kk, f1 in models.f1_by_k.items()
        ]
        st.dataframe(pd.DataFrame(rows), hide_index=True)
        st.caption(
            "Com 2 componentes o mapa é fácil de ver, mas o classificador perde "
            "acerto; com 10 ele fica quase igual ao modelo com tudo."
        )


@st.fragment
def tab_challenge(models: prototype.Models):
    st.subheader("Desafie o modelo")
    st.write("Casos em que o modelo erra, e por quê. IA não é mágica.")
    players = models.players
    options = {}
    for name, position, why in CHALLENGES:
        hit = players.index[
            (players["Name"] == name) & (players["Position"] == position)
        ]
        if len(hit):
            options[f"{name} ({position})"] = (hit[0], why)
    choice = st.radio("Escolha um caso", list(options), horizontal=True)
    index, why = options[choice]
    attributes = prototype.player_attributes(models, index)

    real = players.loc[index, TARGET]
    full = prototype.predict(models, attributes, None)
    st.markdown(
        f"**Posição real:** {real} ({players.loc[index, 'Position']}) · "
        f"**Modelo diz:** {full.index[0]}  \n{why}"
    )
    col_map, col_pred = st.columns([3, 2])
    with col_map:
        fig = base_map(models, height=460)
        mark(
            fig,
            models.coords.loc[[index]].assign(label=players.loc[index, "Name"]),
            "Caso",
            INK,
            18,
        )
        st.plotly_chart(fig, key="challenge_map")
    with col_pred:
        show_prediction(models, attributes, "challenge")


def main():
    st.title("Mapa dos Jogadores · FIFA 19 em 2 dimensões")
    st.caption(
        "PCA aplicado a 37 atributos de 18 mil jogadores · Grupo 4 · "
        "Inteligência Artificial II · FIB"
    )
    if not RAW_PATH.exists():
        st.error("Dataset não encontrado. Rode `uv run football-pca-map download`.")
        st.stop()
    models = load_models()
    st.session_state["models"] = models

    tabs = st.tabs(
        [
            "Mapa",
            "Crie seu jogador",
            "O que são os eixos?",
            "Quanta informação perdemos?",
            "Desafie o modelo",
        ]
    )
    with tabs[0]:
        tab_map(models)
    with tabs[1]:
        tab_create(models)
    with tabs[2]:
        tab_axes(models)
    with tabs[3]:
        tab_information(models)
    with tabs[4]:
        tab_challenge(models)


main()
