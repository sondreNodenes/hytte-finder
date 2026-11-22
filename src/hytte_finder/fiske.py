"""Fiske-proxy: innsjøer (NVE Innsjødatabase) innen radius. Måler TILGANG TIL VANN, ikke fiskekvalitet."""
from __future__ import annotations

import logging
import math

import numpy as np
import pandas as pd

from .common import get_json, haversine_km

log = logging.getLogger("fiske")
URL = "https://kart.nve.no/enterprise/rest/services/Innsjodatabase2/MapServer/5/query"


def lakes_near(lat, lon, radius_km: float, min_km2: float) -> dict:
    """Innsjøer ≥ min_km2 hvis kant ligger innen radius. Avstand = til nærmeste (forenklede) kantpunkt;
    areal = hele innsjøens areal (kan overdrive for innsjøer som bare delvis er innen radius)."""
    out = {"lake_count_10km": np.nan, "lake_area_km2_10km": np.nan, "nearest_lake_km": np.nan,
           "largest_lake_name": None, "largest_lake_km2": np.nan}
    dlat = radius_km / 111.32
    dlon = radius_km / (111.32 * math.cos(math.radians(lat)))
    env = f"{lon-dlon:.5f},{lat-dlat:.5f},{lon+dlon:.5f},{lat+dlat:.5f}"
    feats, offset = [], 0
    try:
        while True:
            d = get_json(URL, params={
                "geometry": env, "geometryType": "esriGeometryEnvelope", "inSR": 4326, "outSR": 4326,
                "spatialRel": "esriSpatialRelIntersects", "where": f"areal_km2>={min_km2}",
                "returnGeometry": "true", "maxAllowableOffset": 0.003, "outFields": "navn,areal_km2",
                "resultOffset": offset, "resultRecordCount": 1000, "f": "json"}, pause=0.6, ns="nve_lakes")
            if "features" not in d:
                return out
            feats += d["features"]
            if not d.get("exceededTransferLimit"):
                break
            offset += len(d["features"])
    except RuntimeError as e:
        log.warning("NVE innsjø feilet: %s", str(e)[:100])
        return out
    lakes = []
    for f in feats:
        pts = [p for ring in f.get("geometry", {}).get("rings", []) for p in ring]
        if not pts:
            continue
        dist = min(haversine_km(lat, lon, p[1], p[0]) for p in pts)
        if dist <= radius_km:
            lakes.append((dist, f["attributes"]["areal_km2"] or 0.0, f["attributes"].get("navn")))
    out["lake_count_10km"] = len(lakes)
    out["lake_area_km2_10km"] = round(sum(l[1] for l in lakes), 3)
    if lakes:
        out["nearest_lake_km"] = min(l[0] for l in lakes)
        big = max(lakes, key=lambda l: l[1])
        out["largest_lake_name"], out["largest_lake_km2"] = big[2], big[1]
    return out


def add_fiske(df: pd.DataFrame, p: dict) -> pd.DataFrame:
    rows = []
    for _, r in df.iterrows():
        log.info("Fiske %s (%d/%d)", r["navn"], len(rows) + 1, len(df))
        rows.append(lakes_near(r["lat"], r["lon"], p["lake_radius_km"], p["lake_min_km2"]))
    return pd.concat([df.reset_index(drop=True), pd.DataFrame(rows)], axis=1)
