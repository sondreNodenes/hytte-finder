"""Randoforhold: helningsandel 25–40° (Kartverket DTM), 1000-m-topp, NVE snøskred-aktsomhet."""
from __future__ import annotations

import io
import logging

import numpy as np
import pandas as pd
from pyproj import Transformer

from . import terrain
from .common import get_json, cached_request

log = logging.getLogger("rando")
NVE = "https://kart.nve.no/enterprise/rest/services/SnoskredAktsomhet/MapServer/export"
PEAK_SEARCH_KM = 15


def avalanche_mask(x0, y0, x1, y1, nx, ny) -> np.ndarray | None:
    """NVE aktsomhetsområder for snøskred (lag 0 PotensieltSkredfareOmr) som boolsk raster
    på samme grid som DEM (1:1 piksler). None hvis tjenesten feiler."""
    from PIL import Image
    params = {"bbox": f"{x0},{y0},{x1},{y1}", "bboxSR": 25833, "imageSR": 25833,
              "size": f"{nx},{ny}", "format": "png32", "transparent": "true",
              "layers": "show:0", "f": "image"}
    try:
        b = cached_request("GET", NVE, params=params, binary=True, pause=1.0, ns="nve", timeout=120)
        im = np.array(Image.open(io.BytesIO(b)).convert("RGBA"))
        return im[..., 3] > 0
    except Exception as e:  # noqa: BLE001
        log.warning("NVE aktsomhet feilet: %s", str(e)[:100])
        return None


def analyse(lat, lon, cfg_params: dict) -> dict:
    res = cfg_params["terrain_resolution_m"]
    r_km, lo, hi = cfg_params["terrain_radius_km"], cfg_params["slope_min_deg"], cfg_params["slope_max_deg"]
    pk = cfg_params["peak_min_masl"]
    win = PEAK_SEARCH_KM * 1000
    cx, cy = Transformer.from_crs(4326, 25833, always_xy=True).transform(lon, lat)
    out = {k: np.nan for k in ("slope_25_40_share", "relief_to_1000m_peak_m", "dist_to_1000m_peak_km",
                                "avalanche_zone_share_of_steep", "terrain_elev_p90_m")}
    try:
        a, t = terrain.fetch_dem(cx - win, cy - win, cx + win, cy + win, res)
    except RuntimeError as e:
        log.warning("DEM feilet (%s,%s): %s", lat, lon, str(e)[:100])
        return out
    ny, nx = a.shape
    rows, cols = np.indices(a.shape)
    xs, ys = t * (cols + 0.5, rows + 0.5)
    dist = np.hypot(xs - cx, ys - cy)
    sl = terrain.slope_deg(a, res)
    inner = (dist <= r_km * 1000) & ~np.isnan(a)
    steep = inner & (sl >= lo) & (sl <= hi)
    out["slope_25_40_share"] = float(steep.sum() / inner.sum()) if inner.any() else np.nan
    out["terrain_elev_p90_m"] = float(np.nanpercentile(a[inner], 90)) if inner.any() else np.nan
    # Høyeste topp >= peak_min (lokalt maksimum i 11x11-vindu) innen søkeradius
    from scipy.ndimage import maximum_filter
    af = np.where(np.isnan(a), -9999, a)
    peaks = (af == maximum_filter(af, size=11)) & (af >= pk) & (dist <= win)
    z0 = a[int(ny / 2), int(nx / 2)]
    if peaks.any():
        d = np.where(peaks, dist, np.inf)
        i = np.unravel_index(np.argmin(d), d.shape)
        out["dist_to_1000m_peak_km"] = float(d[i] / 1000)
        out["relief_to_1000m_peak_m"] = float(max(0.0, a[i] - z0))
    else:  # ingen 1000-m-topp innen søkeradius: ingen høydeforskjell opp til slik topp
        out["relief_to_1000m_peak_m"] = 0.0
    # Skredaktsomhet (kontekst, ikke sikkerhetsvurdering)
    x0, y0 = t * (0, ny)
    x1, y1 = t * (nx, 0)
    m = avalanche_mask(x0, y0, x1, y1, nx, ny)
    if m is not None and steep.any():
        out["avalanche_zone_share_of_steep"] = float((m & steep).sum() / steep.sum())
    return out


def add_rando(df: pd.DataFrame, cfg_params: dict) -> pd.DataFrame:
    rows = []
    for _, r in df.iterrows():
        log.info("Rando %s (%d/%d)", r["navn"], len(rows) + 1, len(df))
        rows.append(analyse(r["lat"], r["lon"], cfg_params))
    return pd.concat([df.reset_index(drop=True), pd.DataFrame(rows)], axis=1)
