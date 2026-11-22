"""CLI: python -m hytte_finder.cli {data|score|report|all} [--limit N]"""
from __future__ import annotations

import argparse
import logging

import pandas as pd

from . import candidates, ssb
from datetime import date

from .variables import VARIABLES
from .common import CONFIG, PROCESSED, RAW, load_config


def _venner(df: pd.DataFrame) -> pd.DataFrame:
    """Manuell vennefil. Tom fil => NaN (inngår ikke). Fylt fil => 0 for kommuner uten oppføring."""
    f = CONFIG / "venner.csv"
    df = df.copy()
    v = pd.read_csv(f) if f.exists() else pd.DataFrame(columns=["kommune", "antall_venner_med_hytte"])
    if v.empty:
        df["friends_cabins"] = float("nan")
    else:
        m = dict(zip(v["kommune"], v["antall_venner_med_hytte"]))
        df["friends_cabins"] = df["kommune"].map(m).fillna(0)
    return df


def _finn_manual(df: pd.DataFrame) -> pd.DataFrame:
    """Valgfri manuell Finn-statistikk: data/raw/finn_manual.csv (kommune, pris_per_m2_nok, dato)."""
    f = RAW / "finn_manual.csv"
    df = df.copy()
    if f.exists():
        m = pd.read_csv(f)
        df["finn_price_per_m2_nok"] = df["kommune"].map(dict(zip(m["kommune"], m["pris_per_m2_nok"])))
    else:
        df["finn_price_per_m2_nok"] = float("nan")
    return df


def cmd_data(cfg: dict, limit: int | None) -> None:
    from . import osm, rando, snow
    PROCESSED.mkdir(parents=True, exist_ok=True)
    meta = pd.DataFrame(VARIABLES, columns=["variabel", "kategori", "enhet", "kilde", "beskrivelse"])
    meta["hentedato"] = date.today().isoformat()
    meta.to_csv(PROCESSED / "variables.csv", index=False)
    df = candidates.build(cfg, limit)
    f = cfg["filters"]
    df = df.merge(ssb.price_summary(f["price_years"]), on="kommunenr", how="left")
    df = df.merge(ssb.property_tax(str(max(f["price_years"]))), on="kommunenr", how="left")
    vr = ssb.villrein_cabins(str(max(f["price_years"])))
    df = df.merge(vr, on="kommunenr", how="left")
    df["villrein_cabins"] = df["villrein_cabins"].fillna(0)
    df = _venner(_finn_manual(df))
    df["owner_oslo_akershus_share"] = float("nan")
    # Dyre steg kun for områder som består kjøretids- og prisfilter
    from .scoring import apply_filters
    df = apply_filters(df, cfg)
    keep = df["passes"]
    logging.info("%d av %d områder består harde filtre; resten får ikke OSM/terreng", keep.sum(), len(df))
    ok = df[keep].reset_index(drop=True)
    snow.download_all()
    ok = snow.add_snow(ok, cfg["params"]["snow_radius_km"])
    ok = osm.add_osm(ok)
    ok = rando.add_rando(ok, cfg["params"])
    out = pd.concat([ok, df[~keep]], ignore_index=True)
    out.to_csv(PROCESSED / "areas.csv", index=False)
    logging.info("Skrev %d rader til areas.csv", len(out))


def cmd_score(cfg: dict) -> None:
    from . import scoring
    from .common import OUTPUT
    df = pd.read_csv(PROCESSED / "areas.csv", dtype={"kommunenr": str})
    df = scoring.apply_filters(df.drop(columns=["passes", "filter_reason", "usikker"], errors="ignore"), cfg)
    ok = df[df["passes"]].reset_index(drop=True)
    ok = scoring.category_scores(ok, cfg)
    OUTPUT.mkdir(exist_ok=True)
    ranked = scoring.rank_table(ok, cfg["weights"]["default"])
    ranked.to_csv(OUTPUT / "ranking.csv", index=False)
    profs = []
    for name, w in cfg["profiles"].items():
        r = scoring.rank_table(ok, w)
        r["profil"] = name
        profs.append(r[["profil", "rank", "id", "navn", "type", "kommune", "score"]])
    pd.concat(profs).to_csv(OUTPUT / "ranking_profiler.csv", index=False)
    p = cfg["params"]
    sens = scoring.sensitivity(ranked, cfg["weights"]["default"], p["sensitivity_runs"],
                               p["sensitivity_alpha"], p["random_seed"])
    sens = sens.merge(ranked[["id", "navn", "type", "kommune", "rank"]], on="id")
    sens.to_csv(OUTPUT / "sensitivity.csv", index=False)
    df[~df["passes"]].to_csv(PROCESSED / "filtered_out.csv", index=False)
    print(ranked[["rank", "navn", "type", "drive_min", "avg_price_nok", "score"]].head(15).to_string())


def cmd_report(cfg: dict) -> None:
    from . import mapview, report
    mapview.build(cfg)
    report.build(cfg)


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
    if a.stage in ("report", "all"):
        cmd_report(cfg)


if __name__ == "__main__":
    main()
