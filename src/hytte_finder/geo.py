"""Geokoding (Nominatim), ruting (OSRM), høyde (Kartverket / Open-Meteo), kommuneinfo (Geonorge)."""
from __future__ import annotations

import math

from .common import get_json

OSRM = "https://router.project-osrm.org/route/v1/driving/{},{};{},{}"


def kommuner() -> dict[str, dict]:
    """Alle norske kommuner: navn -> {nr, navn}. Kilde: Geonorge kommuneinfo."""
    d = get_json("https://ws.geonorge.no/kommuneinfo/v1/kommuner", ns="geonorge")
    return {k["kommunenummer"]: {"nr": k["kommunenummer"], "navn": k["kommunenavnNorsk"]} for k in d}


def kommune_info(nr: str) -> dict:
    d = get_json(f"https://ws.geonorge.no/kommuneinfo/v1/kommuner/{nr}", ns="geonorge")
    lon, lat = d["punktIOmrade"]["coordinates"]
    ring = d["avgrensningsboks"]["coordinates"][0]
    lons, lats = [p[0] for p in ring], [p[1] for p in ring]
    return {"nr": nr, "navn": d["kommunenavnNorsk"], "lat": lat, "lon": lon,
            "bbox": (min(lons), min(lats), max(lons), max(lats))}


def geocode(query: str) -> tuple[float, float, str] | None:
    """Nominatim-oppslag. Foretrekker place/tourism/landuse fremfor vann."""
    res = get_json("https://nominatim.openstreetmap.org/search",
                   params={"q": query, "format": "json", "limit": 5, "countrycodes": "no"},
                   pause=1.5, ns="nominatim")
    if not res:
        return None
    pref = {"place", "tourism", "landuse", "aerialway", "boundary", "leisure", "highway"}
    res = sorted(res, key=lambda r: (r["class"] not in pref,))
    r = res[0]
    return float(r["lat"]), float(r["lon"]), f"{r['class']}/{r['type']} osm:{r['osm_type']}/{r['osm_id']}"


def in_bbox(lat, lon, bbox, margin_deg=0.05) -> bool:
    return (bbox[0] - margin_deg <= lon <= bbox[2] + margin_deg
            and bbox[1] - margin_deg <= lat <= bbox[3] + margin_deg)


def drive_minutes(lat1, lon1, lat2, lon2) -> dict | None:
    """OSRM (bil). Rutes til nærmeste vei ved målet (OSRM snapper koordinaten)."""
    try:
        d = get_json(OSRM.format(lon1, lat1, lon2, lat2), params={"overview": "false"},
                     pause=1.1, ns="osrm")
    except RuntimeError:
        return None
    if d.get("code") != "Ok":
        return None
    r = d["routes"][0]
    return {"drive_min": r["duration"] / 60, "drive_km": r["distance"] / 1000,
            "snap_m": d["waypoints"][1].get("distance")}


def elevation(lat, lon) -> tuple[float, str] | tuple[float, None]:
    """Høyde over havet. Kartverket høydedata-API, fallback Open-Meteo (Copernicus DEM)."""
    try:
        d = get_json("https://ws.geonorge.no/hoydedata/v1/punkt",
                     params={"nord": lat, "ost": lon, "koordsys": 4326}, pause=0.3, ns="hoyde")
        z = d["punkter"][0]["z"]
        if z is not None and not math.isnan(float(z)):
            return float(z), "Kartverket hoydedata"
    except Exception:  # noqa: BLE001
        pass
    try:
        d = get_json("https://api.open-meteo.com/v1/elevation",
                     params={"latitude": lat, "longitude": lon}, pause=0.3, ns="openmeteo")
        return float(d["elevation"][0]), "Open-Meteo (Copernicus DEM)"
    except Exception:  # noqa: BLE001
        return float("nan"), None


def kommune_polygon(nr: str):
    """Kommunegrense (shapely, EPSG:4326) fra Geonorge kommuneinfo."""
    from shapely.geometry import shape
    d = get_json(f"https://ws.geonorge.no/kommuneinfo/v1/kommuner/{nr}/omrade",
                 params={"utkoordsys": 4326}, ns="geonorge", timeout=180)
    return shape(d["omrade"])


def snap_to_road(lat, lon) -> tuple[float, float, float] | None:
    """OSRM nearest: (lat, lon, avstand_m) til nærmeste vei."""
    try:
        d = get_json(f"https://router.project-osrm.org/nearest/v1/driving/{lon},{lat}",
                     params={"number": 1}, pause=1.1, ns="osrm")
        w = d["waypoints"][0]
        return w["location"][1], w["location"][0], w["distance"]
    except Exception:  # noqa: BLE001
        return None
