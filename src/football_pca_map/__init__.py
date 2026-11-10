"""Mapas de PCA para jogadores do FIFA 19."""

import argparse
import logging

from football_pca_map import analysis, animations, data, site


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="football-pca-map",
        description="PCA nos atributos dos jogadores do FIFA 19.",
    )
    parser.add_argument(
        "command",
        choices=["download", "analyze", "gifs", "site", "all"],
        help="download: baixa data/raw/data.csv · analyze: EDA + mapa + E1–E4 · "
        "gifs: animações dos gráficos em docs/img/ · site: dados do site em site/ · "
        "all: tudo",
    )
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    if args.command in ("download", "all"):
        data.download_raw()
    if args.command in ("analyze", "all"):
        raw = data.load_raw()
        analysis.run_all(raw, data.prepare(raw))
        logging.info("Resultados em %s/", analysis.OUTPUTS)
    if args.command in ("gifs", "all"):
        animations.make_all(data.prepare(data.load_raw()))
    if args.command in ("site", "all"):
        raw = data.load_raw()
        site.export(raw, data.prepare(raw))
