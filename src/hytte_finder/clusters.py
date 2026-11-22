"""Hyttefelt-klynger: OSM building=cabin|hut -> DBSCAN (+ oppdeling av store klynger) -> navn."""
from __future__ import annotations

import logging
import math

import numpy as np
import pandas as pd
from pyproj import Transformer
from scipy.cluster.vq import kmeans2
from scipy.spatial import cKDTree
from shapely import contains_xy

from . import geo, osm
from .common import CONFIG, haversine_km

log = logging.getLogger("clusters")
TO_UTM = Transformer.from_crs(4326, 25833, always_xy=True)
FROM_UTM = Transformer.from_crs(25833, 4326, always_xy=True)


def dbscan(xy: np.ndarray, eps: float, min_samples: int) -> np.ndarray:
    """Enkel, deterministisk DBSCAN (meter). Støy = -1. Punkter sorteres først, slik at
    resultatet ikke avhenger av innlesingsrekkefølge."""
    n = len(xy)
    labels = -np.ones(n, dtype=int)
    if n == 0:
        return labels
    tree = cKDTree(xy)
    nbrs = tree.query_ball_point(xy, eps)
    core = np.array([len(x) >= min_samples for x in nbrs])
    cid = 0
    for i in range(n):
        if labels[i] != -1 or not core[i]:
            continue
        labels[i] = cid
        stack = [i]
        while stack:
            j = stack.pop()
            if not core[j]:
                continue
            for k in nbrs[j]:
                if labels[k] == -1:
                    labels[k] = cid
                    stack.append(k)
        cid += 1
    return labels


def split_large(xy: np.ndarray, labels: np.ndarray, max_radius_m: float, seed: int = 42) -> np.ndarray:
    """Del klynger med radius > max_radius_m i delklynger (k-means, fast seed). Gjentas til alle er
    innen radius (maks 4 runder) siden k-means-deler kan være skjeve."""
    out = labels.copy()
    for _ in range(4):
        new = _split_once(xy, out, max_radius_m, seed)
        if (new == out).all():
            break
        out = new
    return out


def _split_once(xy: np.ndarray, labels: np.ndarray, max_radius_m: float, seed: int) -> np.ndarray:
    out = labels.copy()
    nxt = labels.max() + 1 if len(labels) else 0
    for c in sorted(set(labels) - {-1}):
        idx = np.where(labels == c)[0]
        pts = xy[idx]
        radius = np.sqrt(((pts - pts.mean(0)) ** 2).sum(1)).max()
        if radius <= max_radius_m:
            continue
        k = max(2, int(math.ceil(radius / max_radius_m)))
        _, lab = kmeans2(pts, k, minit="++", seed=seed)
        for sub in range(1, k):
            out[idx[lab == sub]] = nxt
            nxt += 1
    return out


def fetch_cabins(poly) -> np.ndarray:
    """Hytter (lat, lon) innen kommunepolygonen. Overpass bbox-spørring (cachet)."""
    minx, miny, maxx, maxy = poly.bounds
    q = ('[out:json][timeout:120];nwr["building"~"^(cabin|hut)$"]'
         f"({miny:.5f},{minx:.5f},{maxy:.5f},{maxx:.5f});out center;")
    js = osm._run(q)
    if js is None:
        return np.empty((0, 2))
    pts = []
    for e in js["elements"]:
        la, lo = osm._center(e)
        if la is not None:
            pts.append((la, lo))
    if not pts:
        return np.empty((0, 2))
    a = np.array(sorted(pts))
    keep = contains_xy(poly, a[:, 1], a[:, 0])
    return a[keep]


def cluster_kommune(poly, p: dict) -> list[dict]:
    pts = fetch_cabins(poly)
    if len(pts) < p["cluster_min_cabins"]:
        return []
    x, y = TO_UTM.transform(pts[:, 1], pts[:, 0])
    xy = np.column_stack([x, y])
    lab = dbscan(xy, p["cluster_eps_km"] * 1000, p["cluster_min_cabins"])
    lab = split_large(xy, lab, p["cluster_max_radius_km"] * 1000, p["random_seed"])
    res = []
    for c in sorted(set(lab) - {-1}):
        m = lab == c
        cxy = xy[m]
        cen = cxy.mean(0)
        i = np.argmin(((cxy - cen) ** 2).sum(1))      # medoid = faktisk hytte nærmest sentrum
        lon, lat = FROM_UTM.transform(*cxy[i])
        res.append({"n_cabins": int(m.sum()), "lat": lat, "lon": lon,
                    "radius_km": float(np.sqrt(((cxy - cen) ** 2).sum(1)).max() / 1000),
                    "cabin_xy": cxy})
    return res


def name_clusters(df: pd.DataFrame, seeds: list[dict]) -> pd.DataFrame:
    """Navn: seed (config/hyttefelt.yaml) innen 2,5 km hvis finnes, ellers Kartverket stedsnavn,
    ellers '<kommune> hyttefelt N'. Duplikater får suffiks."""
    df = df.copy()
    seed_pts = []
    for s in seeds:
        for q in s.get("queries", [s["navn"]]):
            g = geo.geocode(q)
            if g:
                seed_pts.append((s["navn"], g[0], g[1]))
                break
    names, src = [], []
    for _, r in df.iterrows():
        best = None
        for nm, la, lo in seed_pts:
            d = haversine_km(r["lat"], r["lon"], la, lo)
            if d <= 2.5 and (best is None or d < best[0]):
                best = (d, nm)
        if best:
            names.append(best[1]); src.append("seed")
            continue
        nm = geo.place_name(r["lat"], r["lon"])
        names.append(nm or f"{r['kommune']} hyttefelt"); src.append("stedsnavn" if nm else "fallback")
    df["navn"], df["navn_kilde"] = names, src
    seen: dict[str, int] = {}
    final = []
    for nm, kn in zip(df["navn"], df["kommune"]):
        seen[nm] = seen.get(nm, 0) + 1
        final.append(nm if seen[nm] == 1 else f"{nm} {seen[nm]}")
    df["navn"] = final
    return df
