"""OpenStreetMap via Overpass: praktiske tilbud, alpin, løyper og ruter rundt et punkt.
Data © OpenStreetMap-bidragsytere, ODbL. Alt caches; to speil prøves før NaN."""
from __future__ import annotations

import logging
import math
import re
from functools import lru_cache

import numpy as np
import pandas as pd

from .common import haversine_km, post_json

log = logging.getLogger("osm")
MIRRORS = ["https://overpass-api.de/api/interpreter",
           "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
           "https://overpass.kumi.systems/api/interpreter"]
FAR_KM = 30      # søkeradius for «nærmeste»-variabler
NEAR_KM = 15     # radius for telling og ruter


@lru_cache(maxsize=6)
def _run(query: str) -> dict | None:
    for url in MIRRORS:
        try:
            return post_json(url, data={"data": query}, pause=3.0, retries=4, timeout=100, ns="overpass")
        except RuntimeError as e:
            log.warning("Overpass %s feilet: %s", url.split('/')[2], str(e)[:120])
    return None


def bbox(lat, lon, km) -> str:
    """Overpass-bbox (s,w,n,e) rundt punkt; bbox-spørringer er mye raskere enn around."""
    dlat = km / 111.32
    dlon = km / (111.32 * math.cos(math.radians(lat)))
    return f"({lat-dlat:.5f},{lon-dlon:.5f},{lat+dlat:.5f},{lon+dlon:.5f})"


TILE_LAT, TILE_LON = 0.25, 0.5   # flis-størrelse (grader); klynger i samme flis deler Overpass-spørringer


def tile_bbox(lat, lon, margin_km) -> str:
    """Overpass-bbox for flisen som inneholder punktet, utvidet med margin. Alle punkter i samme flis
    får identisk bbox -> én cachet spørring deles av mange områder."""
    s0 = math.floor(lat / TILE_LAT) * TILE_LAT
    w0 = math.floor(lon / TILE_LON) * TILE_LON
    dlat = margin_km / 111.32
    dlon = margin_km / (111.32 * math.cos(math.radians(s0 + TILE_LAT / 2)))
    return f"({s0-dlat:.4f},{w0-dlon:.4f},{s0+TILE_LAT+dlat:.4f},{w0+TILE_LON+dlon:.4f})"


def query_points(lat, lon) -> str:
    a = tile_bbox(lat, lon, FAR_KM)
    n = tile_bbox(lat, lon, NEAR_KM)
    return f"""[out:json][timeout:90];
(
 nwr["amenity"~"^(pub|bar|cafe|restaurant|pharmacy|doctors|clinic|hospital|fuel|charging_station)$"]{a};
 nwr["shop"~"^(supermarket|convenience|alcohol)$"]{a};
 nwr["landuse"="winter_sports"]{a};
 nwr["aerialway"~"^(chair_lift|gondola|drag_lift|t-bar|j-bar|platter|magic_carpet|cable_car|rope_tow|mixed_lift)$"]{a};
 way["piste:type"="downhill"]{a};
 way["highway"~"^(trunk|primary|secondary)$"]{n};
);
out center tags;"""


def query_lines(lat, lon) -> str:
    n = tile_bbox(lat, lon, NEAR_KM)
    return f"""[out:json][timeout:90];
(
 way["piste:type"~"^(nordic|skitour)$"]{n};
 rel["route"~"^(hiking|foot|ski|skitour)$"]{n};
 way["route"="ski"]{n};
);
out geom{n};"""


def _seg_len_in_radius(geom, lat0, lon0, radius_km) -> float:
    """Lengde (km) av polylinje der segmentets midtpunkt ligger innen radius."""
    tot = 0.0
    for p, q in zip(geom, geom[1:]):
        if p is None or q is None:  # punkt utenfor bbox (out geom(bbox))
            continue
        mlat, mlon = (p["lat"] + q["lat"]) / 2, (p["lon"] + q["lon"]) / 2
        if haversine_km(lat0, lon0, mlat, mlon) <= radius_km:
            tot += haversine_km(p["lat"], p["lon"], q["lat"], q["lon"])
    return tot


def _min_dist(geom, lat0, lon0) -> float:
    return min((haversine_km(lat0, lon0, p["lat"], p["lon"]) for p in geom if p), default=math.inf)


def _center(e):
    if "lat" in e:
        return e["lat"], e["lon"]
    c = e.get("center")
    return (c["lat"], c["lon"]) if c else (None, None)


WEEKEND = re.compile(r"(Sa|Su)\b|24/7", re.I)


def _nearest(items, lat0, lon0):
    ds = [haversine_km(lat0, lon0, la, lo) for la, lo, _ in items if la is not None]
    return min(ds) if ds else math.nan


def analyse(lat, lon, opts: dict | None = None) -> dict:
    """Returnerer dict med OSM-variabler. Mangler data (Overpass feilet) -> kun NaN."""
    p = _run(query_points(lat, lon))
    out: dict = {}
    if p is None:
        out["osm_ok"] = False
    else:
        out["osm_ok"] = True
        els = []
        for e in p["elements"]:
            la, lo = _center(e)
            els.append((la, lo, e.get("tags", {})))
        def sel(pred):
            return [(la, lo, t) for la, lo, t in els if la is not None and pred(t)]
        eat = sel(lambda t: t.get("amenity") in ("pub", "bar", "cafe", "restaurant"))
        gather = sel(lambda t: t.get("amenity") in ("pub", "cafe", "bar"))
        groc = sel(lambda t: t.get("shop") in ("supermarket", "convenience"))
        vin = sel(lambda t: t.get("shop") == "alcohol" and "vinmonopol" in
                  (t.get("name", "") + t.get("brand", "")).lower())
        pharm = sel(lambda t: t.get("amenity") == "pharmacy")
        doc = sel(lambda t: t.get("amenity") in ("doctors", "clinic", "hospital"))
        fuel = sel(lambda t: t.get("amenity") == "fuel")
        ev = sel(lambda t: t.get("amenity") == "charging_station")
        alp = sel(lambda t: t.get("landuse") == "winter_sports" or "aerialway" in t
                  or t.get("piste:type") == "downhill")
        roads = sel(lambda t: t.get("highway") in ("trunk", "primary", "secondary"))
        for name, items in [("eat", eat), ("gathering", gather), ("ev", ev)]:
            for r in (5, 15):
                out[f"{name}_{r}km"] = sum(haversine_km(lat, lon, la, lo) <= r for la, lo, _ in items)
        out["nearest_eat_km"] = _nearest(eat, lat, lon)
        out["nearest_gathering_km"] = _nearest(gather, lat, lon)
        out["nearest_grocery_km"] = _nearest(groc, lat, lon)
        out["nearest_vinmonopol_km"] = _nearest(vin, lat, lon)
        out["nearest_pharmacy_km"] = _nearest(pharm, lat, lon)
        out["nearest_doctor_km"] = _nearest(doc, lat, lon)
        out["nearest_fuel_km"] = _nearest(fuel, lat, lon)
        out["nearest_ev_km"] = _nearest(ev, lat, lon)
        out["nearest_alpine_km"] = _nearest(alp, lat, lon)
        out["nearest_main_road_km"] = _nearest(roads, lat, lon)
        out["grocery_5km"] = sum(haversine_km(lat, lon, la, lo) <= 5 for la, lo, _ in groc)
        out["ev_charging_15km"] = out["ev_15km"]
        # Dagligvare nærmeste: åpningstider (ofte mangler i OSM)
        if groc:
            la, lo, t = min(groc, key=lambda x: haversine_km(lat, lon, x[0], x[1]))
            oh = t.get("opening_hours")
            out["nearest_grocery_name"] = t.get("name")
            out["nearest_grocery_weekend_open"] = (bool(WEEKEND.search(oh)) if oh else math.nan)
        # Helårs-/samlingssted som beskriver tilbudet
        out["eat_names"] = "; ".join(sorted({t.get("name", "") for la, lo, t in eat
                                             if t.get("name") and haversine_km(lat, lon, la, lo) <= 5}))[:300]

    l = _run(query_lines(lat, lon))
    if l is None:
        out["osm_lines_ok"] = False
        return out
    out["osm_lines_ok"] = True
    nordic = dnt = winter = 0.0
    dnt_n = 0
    nordic_min = math.inf
    for e in l["elements"]:
        t = e.get("tags", {})
        geoms = []
        if e["type"] == "way" and "geometry" in e:
            geoms = [e["geometry"]]
        elif e["type"] == "relation":
            geoms = [m["geometry"] for m in e.get("members", []) if m.get("type") == "way" and "geometry" in m]
        if not geoms:
            continue
        length = sum(_seg_len_in_radius(g, lat, lon, NEAR_KM) for g in geoms)
        if e["type"] == "way" and t.get("piste:type") == "nordic":
            nordic += _seg_len_in_radius(e["geometry"], lat, lon, 10)
            nordic_min = min(nordic_min, _min_dist(e["geometry"], lat, lon))
        elif e["type"] == "way" and (t.get("piste:type") == "skitour" or t.get("route") == "ski"):
            winter += length
        elif e["type"] == "relation":
            r = t.get("route")
            op = (t.get("operator", "") + t.get("network:name", "") + t.get("name", "")).lower()
            if r in ("ski", "skitour"):
                winter += length
            elif r in ("hiking", "foot") and ("dnt" in op or "turistforening" in op or "trekking" in op):
                dnt += length
                dnt_n += 1 if length > 0 else 0
    out["nordic_km_10km"] = round(nordic, 2)
    out["nordic_nearest_km"] = nordic_min if math.isfinite(nordic_min) else math.nan
    out["nordic_direct_access"] = bool(nordic_min <= 1.0)
    out["dnt_routes_km_15km"] = round(dnt, 2)
    out["dnt_routes_n"] = dnt_n
    out["winter_routes_km_15km"] = round(winter, 2)
    out["marked_routes_km_15km"] = round(dnt + winter, 2)
    return out


def add_osm(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for i, r in df.iterrows():
        log.info("OSM %s (%d/%d)", r["navn"], len(rows) + 1, len(df))
        rows.append(analyse(r["lat"], r["lon"]))
    return pd.concat([df.reset_index(drop=True), pd.DataFrame(rows)], axis=1)
