"""Bygger kandidatliste: fjellhyttekommuner (SSB) + hyttefelt (OSM) med kjøretid og høyde."""
from __future__ import annotations

import logging

import pandas as pd
import yaml

from . import geo, ssb, terrain
from .common import CONFIG, PROCESSED, haversine_km

log = logging.getLogger("candidates")


def mountain_point(nr: str, band: tuple[float, float], info: dict) -> tuple[float, float, str] | None:
    """Punkt i kommunen: celle i høydebåndet nærmest tyngdepunktet av båndarealet (DTM 500 m)."""
    import numpy as np
    from pyproj import Transformer
    from shapely.geometry import Point
    from shapely.prepared import prep
    poly = geo.kommune_polygon(nr)
    to25833 = Transformer.from_crs(4326, 25833, always_xy=True)
    to4326 = Transformer.from_crs(25833, 4326, always_xy=True)
    minx, miny, maxx, maxy = poly.bounds
    x0, y0 = to25833.transform(minx, miny)
    x1, y1 = to25833.transform(maxx, maxy)
    try:
        a, t = terrain.fetch_dem(min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1), 500)
    except RuntimeError as e:
        log.warning("DEM feilet for %s: %s", nr, e)
        return None
    rows, cols = np.where((a >= band[0]) & (a <= band[1]))
    if len(rows) == 0:
        return None
    xs, ys = t * (cols + 0.5, rows + 0.5)
    lons, lats = to4326.transform(xs, ys)
    pp = prep(poly)
    inside = np.array([pp.contains(Point(lo, la)) for lo, la in zip(lons, lats)])
    if not inside.any():
        return None
    lons, lats, xs, ys = lons[inside], lats[inside], np.array(xs)[inside], np.array(ys)[inside]
    i = np.argmin((xs - xs.mean()) ** 2 + (ys - ys.mean()) ** 2)
    return float(lats[i]), float(lons[i]), f"DTM-høydebånd {band[0]}–{band[1]} moh, {inside.sum()} celler"


def build(cfg: dict, limit: int | None = None) -> pd.DataFrame:
    f, home = cfg["filters"], cfg["home"]
    names = geo.kommuner()
    name2nr = {v["navn"]: k for k, v in names.items()}

    # --- Fjellhyttekommuner fra SSB 12511 (fritidsbygg >= mountain_min_masl) ---
    mc = ssb.mountain_cabins(f["mountain_min_masl"])
    mc = mc[mc["kommunenr"].isin(names) & (mc["mountain_cabins"] >= f["min_mountain_cabins"])]
    rows = []
    for _, r in mc.iterrows():
        info = geo.kommune_info(r["kommunenr"])
        dist = haversine_km(home["lat"], home["lon"], info["lat"], info["lon"])
        if dist > f["candidate_radius_km"]:
            continue
        mp = mountain_point(info["nr"], tuple(f["kommune_band_masl"]), info)
        if mp is None:
            log.warning("Fant ikke fjellpunkt i %s – droppet", info["navn"])
            continue
        lat, lon, src = mp
        snap = geo.snap_to_road(lat, lon)
        if snap:
            lat, lon, sm = snap
            src += f"; snappet til vei ({sm:.0f} m)"
        rows.append({"id": f"k{info['nr']}", "navn": info["navn"], "type": "kommune",
                     "kommunenr": info["nr"], "kommune": info["navn"], "lat": lat,
                     "lon": lon, "loc_source": src,
                     "air_km": dist, "mountain_cabins": r["mountain_cabins"]})
    log.info("%d fjellhyttekommuner innen %s km", len(rows), f["candidate_radius_km"])

    # --- Hyttefelt (seeds) ---
    seeds = yaml.safe_load(open(CONFIG / "hyttefelt.yaml", encoding="utf-8"))["hyttefelt"]
    mcd = dict(zip(mc["kommunenr"], mc["mountain_cabins"]))
    for s in seeds:
        nr = name2nr.get(s["kommune"])
        if nr is None:
            log.warning("Ukjent kommune %s for %s", s["kommune"], s["navn"])
            continue
        g = None
        for q in s.get("queries", [s.get("query", s["navn"])]):
            g = geo.geocode(q)
            if g is not None:
                break
        if g is None:
            log.warning("Geokoding feilet: %s", s["navn"])
            continue
        lat, lon, src = g
        bbox = geo.kommune_info(nr)["bbox"]
        if not geo.in_bbox(lat, lon, bbox):
            log.warning("%s ligger utenfor %s sin boks (%s) – droppet", s["navn"], s["kommune"], src)
            continue
        rows.append({"id": "h-" + s["navn"].lower().replace(" ", "-"), "navn": s["navn"],
                     "type": "hyttefelt", "kommunenr": nr, "kommune": s["kommune"], "lat": lat,
                     "lon": lon, "loc_source": f"OSM Nominatim {src}",
                     "air_km": haversine_km(home["lat"], home["lon"], lat, lon),
                     "mountain_cabins": mcd.get(nr, float("nan"))})
    df = pd.DataFrame(rows).drop_duplicates("id")
    if limit:
        df = pd.concat([df[df.type == "hyttefelt"].head(limit - limit // 2),
                        df[df.type == "kommune"].head(limit // 2)])

    # --- Kjøretid og høyde ---
    out = []
    for _, r in df.iterrows():
        d = geo.drive_minutes(home["lat"], home["lon"], r["lat"], r["lon"]) or {}
        z, zsrc = geo.elevation(r["lat"], r["lon"])
        out.append({**d, "elevation_m": z, "elevation_source": zsrc})
    df = pd.concat([df.reset_index(drop=True), pd.DataFrame(out)], axis=1)
    df["drive_min_winter"] = df["drive_min"] * f["winter_factor"]
    PROCESSED.mkdir(parents=True, exist_ok=True)
    return df
