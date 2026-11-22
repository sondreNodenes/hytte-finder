"""Filtre, normalisering, kategoriscorer, totalscore, profiler og sensitivitetsanalyse."""
from __future__ import annotations

import numpy as np
import pandas as pd

CATS = ["Snø", "Verdi", "Rando", "Praktisk", "Kjøretid", "Jakt", "Fiske", "Sosialt"]


# ---------------------------------------------------------------- filtre
def apply_filters(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """Setter `passes` og `filter_reason`. Kjøretid og pris er harde filtre."""
    f = cfg["filters"]
    df = df.copy()
    reasons = []
    for _, r in df.iterrows():
        why = []
        if pd.isna(r.get("drive_min")):
            why.append("kjøretid mangler")
        elif r["drive_min"] > f["max_drive_min"]:
            why.append(f"kjøretid {r['drive_min']:.0f} min > {f['max_drive_min']}")
        z = r.get("elevation_m")
        if "min_elevation_m" in f and f["min_elevation_m"] and (pd.isna(z) or z < f["min_elevation_m"]):
            why.append("høyde mangler" if pd.isna(z) else f"høyde {z:.0f} moh < {f['min_elevation_m']} (ikke fjell)")
        p = r.get("avg_price_nok")
        if pd.isna(p):
            why.append("pris mangler (ingen salg i SSB)")
        elif p > f["price_max_nok"] * f["price_tolerance"]:
            why.append(f"snittpris {p/1e6:.1f} mill > {f['price_max_nok']*f['price_tolerance']/1e6:.2f} mill")
        reasons.append("; ".join(why))
    df["filter_reason"] = reasons
    df["passes"] = df["filter_reason"] == ""
    df["usikker"] = df["sales_last_year"].fillna(0) < f["min_sales_certain"]
    return df


# ---------------------------------------------------------------- normalisering
def normalize(s: pd.Series, method: str = "percentile", invert: bool = False) -> pd.Series:
    """0–1. percentile: rangpersentil (robust mot uteliggere); minmax: lineær.
    NaN forblir NaN. Konstant serie gir 0.5. invert=True: lav verdi = høy score."""
    s = pd.to_numeric(s, errors="coerce")
    valid = s.dropna()
    if valid.empty:
        return s
    if valid.nunique() == 1:
        out = pd.Series(0.5, index=s.index).where(s.notna())
    elif method == "percentile":
        out = (s.rank(method="average") - 1) / (valid.rank(method="average").max() - 1)
    elif method == "minmax":
        out = (s - valid.min()) / (valid.max() - valid.min())
    else:
        raise ValueError(f"ukjent normalisering: {method}")
    return 1 - out if invert else out


def weighted_mean_rowwise(frame: pd.DataFrame, weights: dict[str, float]) -> pd.Series:
    """Vektet snitt over kolonner, renormalisert over ikke-NaN per rad. Alle NaN -> NaN."""
    cols = [c for c in weights if c in frame.columns]
    if not cols:
        return pd.Series(np.nan, index=frame.index)
    w = np.array([weights[c] for c in cols], dtype=float)
    x = frame[cols].to_numpy(dtype=float)
    mask = ~np.isnan(x)
    num = np.where(mask, x, 0.0) @ w
    den = mask @ w
    with np.errstate(invalid="ignore", divide="ignore"):
        res = np.where(den > 0, num / den, np.nan)
    return pd.Series(res, index=frame.index)


# ---------------------------------------------------------------- kategorier
def value_indices(df: pd.DataFrame, snow_score: pd.Series, floor: float) -> pd.DataFrame:
    """Verdi-indeks: pris per snøsikkerhetspoeng og pris per tur-/skitilbud (km)."""
    df = df.copy()
    price = df["price_used_nok"] if "price_used_nok" in df.columns else df["avg_price_nok"]
    df["value_price_per_snow"] = price / snow_score.clip(lower=floor)
    offer = df.get("nordic_km_10km", pd.Series(np.nan, index=df.index)).fillna(0) \
        + df.get("marked_routes_km_15km", pd.Series(np.nan, index=df.index)).fillna(0)
    have = df.get("nordic_km_10km", pd.Series(np.nan, index=df.index)).notna() | \
        df.get("marked_routes_km_15km", pd.Series(np.nan, index=df.index)).notna()
    df["trail_offer_km"] = offer.where(have)
    df["value_price_per_trail"] = price / df["trail_offer_km"].clip(lower=1.0)
    return df


def category_scores(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """Beregner normaliserte variabler og seks kategoriscorer (kolonner = kategorinavn)."""
    method = cfg["params"]["normalization"]
    df = df.copy()
    norm = {}
    for cat in CATS:
        for v in cfg["categories"].get(cat, []):
            if v["col"] in df.columns and v["col"] not in norm and cat != "Verdi":
                norm[v["col"]] = normalize(df[v["col"]], method, v.get("invert", False))
        if cat == "Snø":
            snow_frame = pd.DataFrame(norm)
            df["Snø"] = weighted_mean_rowwise(
                snow_frame, {v["col"]: v["w"] for v in cfg["categories"]["Snø"]})
            df = value_indices(df, df["Snø"], cfg["params"]["value_snow_floor"])
            for v in cfg["categories"]["Verdi"]:
                if v["col"] in df.columns:
                    norm[v["col"]] = normalize(df[v["col"]], method, v.get("invert", False))
    nf = pd.DataFrame(norm)
    for cat in CATS:
        if cat == "Snø":
            continue
        df[cat] = weighted_mean_rowwise(nf, {v["col"]: v["w"] for v in cfg["categories"].get(cat, [])})
    return df


def total_score(df: pd.DataFrame, weights: dict[str, float]) -> pd.Series:
    """Totalscore 0–100 = vektet sum av kategoriscorer, renormalisert over tilgjengelige kategorier."""
    return 100 * weighted_mean_rowwise(df[CATS], weights)


def rank_table(df: pd.DataFrame, weights: dict[str, float]) -> pd.DataFrame:
    out = df.copy()
    out["score"] = total_score(out, weights)
    out = out.sort_values("score", ascending=False).reset_index(drop=True)
    out["rank"] = np.arange(1, len(out) + 1)
    return out


# ---------------------------------------------------------------- sensitivitet
def sensitivity(df: pd.DataFrame, base: dict[str, float], runs: int, alpha: float,
                seed: int, top: int = 5) -> pd.DataFrame:
    """Dirichlet rundt standardvekter. Returnerer andel av kjøringer i topp N og snittrang."""
    rng = np.random.default_rng(seed)
    cats = [c for c in CATS if base.get(c, 0) > 0]
    w0 = np.array([base[c] for c in cats], dtype=float)
    w0 = w0 / w0.sum()
    W = rng.dirichlet(alpha * w0, size=runs)
    x = df[cats].to_numpy(dtype=float)
    mask = ~np.isnan(x)
    num = np.where(mask, x, 0.0) @ W.T            # (n_areas, runs)
    den = mask.astype(float) @ W.T
    with np.errstate(invalid="ignore", divide="ignore"):
        S = np.where(den > 0, num / den, -np.inf)
    ranks = (-S).argsort(axis=0).argsort(axis=0) + 1   # 1 = best
    res = pd.DataFrame({"id": df["id"].values,
                        f"topp{top}_andel": (ranks <= top).mean(axis=1),
                        "topp10_andel": (ranks <= 10).mean(axis=1),
                        "snittrang": ranks.mean(axis=1),
                        "beste_rang": ranks.min(axis=1), "dårligste_rang": ranks.max(axis=1)})
    return res.sort_values(f"topp{top}_andel", ascending=False).reset_index(drop=True)
