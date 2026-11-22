"""CLI: python -m hytte_finder.cli {data|score|report|all} [--limit N]"""
from __future__ import annotations

import argparse
import logging

import pandas as pd

from . import candidates, ssb
from .common import PROCESSED, load_config


def cmd_data(cfg: dict, limit: int | None) -> None:
    df = candidates.build(cfg, limit)
    prices = ssb.price_summary(cfg["filters"]["price_years"])
    df = df.merge(prices, on="kommunenr", how="left")
    df.to_csv(PROCESSED / "areas.csv", index=False)
    logging.info("Skrev %d rader til areas.csv", len(df))


def cmd_score(cfg: dict) -> None:
    from . import scoring
    from .common import OUTPUT
    df = pd.read_csv(PROCESSED / "areas.csv", dtype={"kommunenr": str})
    df = scoring.apply_filters(df, cfg)
    ok = df[df["passes"]].reset_index(drop=True)
    ok = scoring.category_scores(ok, cfg)
    ranked = scoring.rank_table(ok, cfg["weights"]["default"])
    OUTPUT.mkdir(exist_ok=True)
    ranked.to_csv(OUTPUT / "ranking.csv", index=False)
    df[~df["passes"]].to_csv(PROCESSED / "filtered_out.csv", index=False)
    print(ranked[["rank", "navn", "type", "drive_min", "avg_price_nok", "score"]].head(15).to_string())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["data", "score", "report", "all"])
    ap.add_argument("--limit", type=int, default=None, help="begrens antall kandidater (testkjøring)")
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    cfg = load_config()
    if a.stage in ("data", "all"):
        cmd_data(cfg, a.limit)
    if a.stage in ("score", "all"):
        cmd_score(cfg)


if __name__ == "__main__":
    main()
