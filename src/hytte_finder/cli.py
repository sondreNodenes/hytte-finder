"""CLI: python -m hytte_finder.cli {data|finn|score|report|all} [--limit N]"""
from __future__ import annotations

import argparse
import logging
from datetime import date

import pandas as pd

from . import candidates, ssb
from .common import CONFIG, OUTPUT, PROCESSED, RAW, load_config
from .variables import VARIABLES


def _manual_scores(df: pd.DataFrame) -> pd.DataFrame:
    """config/jakt_fiske.csv (nokkel = id | navn | kommune): jaktrett_tilgang, fiskekort_tilgang (0–2)."""
    df = df.copy()
    f = CONFIG / "jakt_fiske.csv"
    m = pd.read_csv(f) if f.exists() else pd.DataFrame(columns=["nokkel"])
    for col in ("jaktrett_tilgang", "fiskekort_tilgang"):
        df[col] = float("nan")
        if col in m.columns and not m.empty:
            for key_col in ("kommune", "navn", "id"):          # mest spesifikke vinner (sist)
                mp = dict(zip(m["nokkel"].astype(str), m[col]))
                hit = df[key_col].astype(str).map(mp)
                df[col] = hit.combine_first(df[col])
    return df


def _venner(df: pd.DataFrame) -> pd.DataFrame:
    """Manuell vennefil. Tom fil => NaN (inngår ikke). Fylt fil => 0 for kommuner uten oppføring."""
    f = CONFIG / "venner.csv"
    df = df.copy()
    v = pd.read_csv(f) if f.exists() else pd.DataFrame(columns=["kommune", "antall_venner_med_hytte"])
    if v.empty:
        df["friends_cabins"] = float("nan")
    else:
        df["friends_cabins"] = df["kommune"].map(dict(zip(v["kommune"], v["antall_venner_med_hytte"]))).fillna(0)
    return df


def cmd_data(cfg: dict, limit: int | None) -> None:
    from . import fiske, osm, rando, snow
    from .scoring import apply_filters
    PROCESSED.mkdir(parents=True, exist_ok=True)
    meta = pd.DataFrame(VARIABLES, columns=["variabel", "kategori", "enhet", "kilde", "beskrivelse"])
    meta["hentedato"] = date.today().isoformat()
    meta.to_csv(PROCESSED / "variables.csv", index=False)
    f, p = cfg["filters"], cfg["params"]
    df = candidates.build(cfg, limit)
    df = df.merge(ssb.price_summary(f["price_years"]), on="kommunenr", how="left")
    df = df.merge(ssb.property_tax(str(max(f["price_years"]))), on="kommunenr", how="left")
    df = df.merge(ssb.villrein_cabins(str(max(f["price_years"]))), on="kommunenr", how="left")
    df["villrein_cabins"] = df["villrein_cabins"].fillna(0)
    h = ssb.hunting(p["hunting_seasons"])
    df = df.merge(h, on="kommunenr", how="left")
    df["jakt_elg_per_100km2"] = df["elg_felt_snitt"] / df["kommune_area_km2"] * 100
    df["jakt_hjort_per_100km2"] = df["hjort_felt_snitt"] / df["kommune_area_km2"] * 100
    df = _venner(_manual_scores(df))
    df["owner_oslo_akershus_share"] = float("nan")
    df = apply_filters(df, cfg)
    keep = df["passes"]
    logging.info("%d av %d klynger består harde filtre; resten får ikke dyre variabler", keep.sum(), len(df))
    ok = df[keep].reset_index(drop=True)
    snow.download_all()
    ok = snow.add_snow(ok, p["snow_radius_km"])
    ok = fiske.add_fiske(ok, p)
    ok = osm.add_osm(ok)
    ok = rando.add_rando(ok, p)
    out = pd.concat([ok, df[~keep]], ignore_index=True)
    out.to_csv(PROCESSED / "areas.csv", index=False)
    logging.info("Skrev %d rader til areas.csv", len(out))


def cmd_finn(cfg: dict, max_clusters: int) -> None:
    """Valgfritt engangs-uttrekk av Finn-annonser (ikke del av `all`). Se finn.py for forsiktighetsregler."""
    from . import finn
    from .scoring import apply_filters
    df = pd.read_csv(PROCESSED / "areas.csv", dtype={"kommunenr": str})
    df = apply_filters(df.drop(columns=["passes", "filter_reason", "usikker"], errors="ignore"), cfg)
    rk = OUTPUT / "ranking.csv"
    if rk.exists():          # søk først for de best rangerte feltene (kjør `score` før `finn`)
        top = pd.read_csv(rk)["id"].head(max_clusters)
        df = df[df["id"].isin(top)]
        logging.info("Finn: bruker topp %d fra ranking.csv", len(top))
    finn.run(df, max_clusters)


def _add_prices(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """Slå på Finn-/manuelle medianer. price_used = Finn-median hvis nok annonser, ellers kommunesnitt."""
    from . import finn
    min_ads = cfg["params"]["finn_min_ads"]
    min_k = cfg["params"].get("finn_min_ads_kommune", min_ads)
    df = df.drop(columns=[c for c in df.columns if c.startswith("finn_median") or c == "finn_n_ads"], errors="ignore")
    agg = finn.aggregate(df, min_ads, min_k)
    df = df.merge(agg, on="id", how="left")
    need = df["finn_level"].map({"felt": min_ads, "kommune": min_k}).fillna(10 ** 9)
    enough = df["finn_n_ads"].fillna(0) >= need
    df["price_source"] = [("finn " + str(l) + "-median") if e else "SSB kommunesnitt"
                          for e, l in zip(enough, df["finn_level"])]
    df["price_used_nok"] = df["finn_median_price_nok"].where(enough, df["avg_price_nok"])
    df["price_per_m2_used"] = df["finn_median_price_per_m2"].where(enough)
    df["finn_tynt"] = df["finn_n_ads"].notna() & ~enough
    df["over_budsjett"] = df["price_used_nok"] > cfg["filters"]["price_max_nok"]
    return df


def cmd_score(cfg: dict) -> None:
    from . import scoring
    df = pd.read_csv(PROCESSED / "areas.csv", dtype={"kommunenr": str})
    df = scoring.apply_filters(df.drop(columns=["passes", "filter_reason", "usikker"], errors="ignore"), cfg)
    df = _add_prices(df, cfg)
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
    print(ranked[["rank", "navn", "kommune", "drive_min", "price_used_nok", "score"]].head(15).to_string())


def cmd_report(cfg: dict) -> None:
    from . import dashboard, findings, mapview, report
    mapview.build(cfg)
    dashboard.build(cfg)
    findings.build(cfg)
    report.build(cfg)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["data", "finn", "score", "report", "all"])
    ap.add_argument("--limit", type=int, default=None, help="begrens antall kommuner (testkjøring)")
    ap.add_argument("--max-clusters", type=int, default=30, help="finn: maks antall søk")
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    cfg = load_config()
    if a.stage in ("data", "all"):
        cmd_data(cfg, a.limit)
    if a.stage == "finn":
        cmd_finn(cfg, a.max_clusters)
    if a.stage in ("score", "all"):
        cmd_score(cfg)
    if a.stage in ("report", "all"):
        cmd_report(cfg)


if __name__ == "__main__":
    main()
