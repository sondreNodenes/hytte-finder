"""Snødata fra NVE/MET Klima i Norge (utgave 2025), 1x1 km NetCDF. Gjennomsnitt innen radius."""
from __future__ import annotations

import numpy as np
import pandas as pd
from pyproj import Transformer

from .common import RAW

SNOW = RAW / "snow"
URLS = {
    "skisesong_1991-2020_swe60ge.nc": "https://thredds.met.no/thredds/fileServer/KSS/Klima_i_Norge/utgave2025/ReferenceIndices/swe60ge/reference_1991-2020_disthbv_norway_1km_swe60ge.nc",
    "swemax_1991-2020.nc": "https://thredds.met.no/thredds/fileServer/KSS/Klima_i_Norge/utgave2025/ReferenceIndices/swemax/reference_1991-2020_disthbv_norway_1km_swemax.nc",
    "diff_swe60ge_rcp45.nc": "https://thredds.met.no/thredds/fileServer/KSS/Klima_i_Norge/utgave2025/ClimateStatistics/diff-swe60ge/ensemble-mean_rcp45_both-bc-estobs_disthbv_norway_1km_diff-swe60ge.nc",
}


def download_all() -> None:
    import requests
    SNOW.mkdir(parents=True, exist_ok=True)
    for name, url in URLS.items():
        f = SNOW / name
        if f.exists() and f.stat().st_size > 1000:
            continue
        with requests.get(url, stream=True, timeout=300) as r:
            r.raise_for_status()
            with open(f, "wb") as out:
                for chunk in r.iter_content(1 << 20):
                    out.write(chunk)


def radius_mean(path, var: str, lats, lons, radius_km: float, layer: int = 0) -> np.ndarray:
    """Gjennomsnitt av `var` (lag `layer`) i sirkel med radius rundt hvert punkt.
    Rutenettet er UTM33 med 1 km celler; maskerte/NaN-celler (hav, ikke-data) ignoreres."""
    import netCDF4 as nc
    d = nc.Dataset(path)
    x, y = np.asarray(d["Xc"][:], float), np.asarray(d["Yc"][:], float)
    v = d[var]
    a = v[layer] if v.ndim == 3 else v[:]
    a = np.ma.filled(np.ma.masked_invalid(a).astype(float), np.nan)
    t = Transformer.from_crs(4326, 32633, always_xy=True)
    px, py = t.transform(np.asarray(lons), np.asarray(lats))
    XX, YY = np.meshgrid(x, y)
    out = []
    for cx, cy in zip(px, py):
        m = ((XX - cx) ** 2 + (YY - cy) ** 2) <= (radius_km * 1000) ** 2
        vals = a[m]
        vals = vals[~np.isnan(vals)]
        out.append(vals.mean() if len(vals) else np.nan)
    return np.array(out)


def add_snow(df: pd.DataFrame, radius_km: float) -> pd.DataFrame:
    df = df.copy()
    lat, lon = df["lat"].values, df["lon"].values
    df["ski_season_days"] = radius_mean(SNOW / "skisesong_1991-2020_swe60ge.nc", "swe60ge_annual", lat, lon, radius_km)
    df["swe_max_mm"] = radius_mean(SNOW / "swemax_1991-2020.nc", "swemax_annual", lat, lon, radius_km)
    df["ski_season_change_2041_2070_rcp45"] = radius_mean(
        SNOW / "diff_swe60ge_rcp45.nc", "diff-swe60ge_annual", lat, lon, radius_km, layer=0)
    df["ski_season_proj_2041_2070"] = df["ski_season_days"] + df["ski_season_change_2041_2070_rcp45"]
    return df
