"""Kandidater v2: hyttefelt-klynger (OSM-hytter, DBSCAN) i fjellhyttekommuner, med kjøretid og høyde."""
from __future__ import annotations

import logging

import pandas as pd
import yaml

from . import clusters, geo, ssb
from .common import CONFIG, haversine_km

log = logging.getLogger("candidates")


def mountain_kommuner(cfg: dict) -> pd.DataFrame:
    """Fjellhyttekommuner: >= min_mountain_cabins fritidsbygg over mountain_min_masl (SSB 12511),
    kommunepunkt innen candidate_radius_km fra hjem."""
    f, home = cfg["filters"], cfg["home"]
    names = geo.kommuner()
    mc = ssb.mountain_cabins(f["mountain_min_masl"])
    mc = mc[mc["kommunenr"].isin(names) & (mc["mountain_cabins"] >= f["min_mountain_cabins"])]
    rows = []
    for _, r in mc.iterrows():
        info = geo.kommune_info(r["kommunenr"])
        d = haversine_km(home["lat"], home["lon"], info["lat"], info["lon"])
        if d <= f["candidate_radius_km"]:
            rows.append({"kommunenr": r["kommunenr"], "kommune": info["navn"], "air_km_kommune": d,
                         "mountain_cabins": r["mountain_cabins"]})
    return pd.DataFrame(rows).sort_values("kommunenr").reset_index(drop=True)


def build(cfg: dict, limit: int | None = None) -> pd.DataFrame:
    f, home, p = cfg["filters"], cfg["home"], cfg["params"]
    km = mountain_kommuner(cfg)
    if limit:
        km = km.head(limit)
    log.info("%d fjellhyttekommuner innen %s km", len(km), f["candidate_radius_km"])
    rows = []
    for _, k in km.iterrows():
        poly = geo.kommune_polygon(k["kommunenr"])
        area = geo.kommune_area_km2(poly)
        cl = clusters.cluster_kommune(poly, p)
        cl.sort(key=lambda c: -c["n_cabins"])
        log.info("%s: %d hyttefelt-klynger (%d hytter i klynger)", k["kommune"], len(cl),
                 sum(c["n_cabins"] for c in cl))
        for i, c in enumerate(cl, 1):
            rows.append({"id": f"c{k['kommunenr']}-{i}", "type": "hyttefelt", "kommunenr": k["kommunenr"],
                         "kommune": k["kommune"], "kommune_area_km2": area, "lat": c["lat"], "lon": c["lon"],
                         "n_cabins": c["n_cabins"], "cluster_radius_km": c["radius_km"],
                         "mountain_cabins": k["mountain_cabins"],
                         "air_km": haversine_km(home["lat"], home["lon"], c["lat"], c["lon"])})
    df = pd.DataFrame(rows)
    if df.empty:
        raise RuntimeError("Ingen klynger funnet – sjekk Overpass-tilgang")
    seeds = yaml.safe_load(open(CONFIG / "hyttefelt.yaml", encoding="utf-8"))["hyttefelt"]
    df = clusters.name_clusters(df, seeds)
    d = geo.drive_table(home["lat"], home["lon"], list(zip(df["lat"], df["lon"])))
    df = pd.concat([df, pd.DataFrame(d)], axis=1)
    df["drive_min_winter"] = df["drive_min"] * f["winter_factor"]
    z = [geo.elevation(la, lo) for la, lo in zip(df["lat"], df["lon"])]
    df["elevation_m"] = [a for a, _ in z]
    df["elevation_source"] = [b for _, b in z]
    df["loc_source"] = "medoid av OSM-hytter i klynge (DBSCAN)"
    return df
