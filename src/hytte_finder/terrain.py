"""Kartverket DTM via WCS: henting (cachet), helning, tyngdepunkt i høydebånd."""
from __future__ import annotations

import hashlib
import io

import numpy as np
import rasterio
from rasterio.io import MemoryFile

from .common import CACHE, user_agent

WCS = "https://wcs.geonorge.no/skwms1/wcs.hoyde-dtm_somlos"
MAX_CELLS = 4000  # sikkerhetsgrense per kant


def fetch_dem(xmin, ymin, xmax, ymax, res: int):
    """Hent DTM (EPSG:25833) for bbox med gitt oppløsning (m). Returnerer (array, transform).
    Cachet på disk. Kaster RuntimeError hvis tjenesten feiler to ganger."""
    import requests
    xmin, ymin = np.floor(xmin / res) * res, np.floor(ymin / res) * res
    xmax, ymax = np.ceil(xmax / res) * res, np.ceil(ymax / res) * res
    nx, ny = int((xmax - xmin) / res), int((ymax - ymin) / res)
    if nx > MAX_CELLS or ny > MAX_CELLS:
        raise RuntimeError(f"DEM-forespørsel for stor ({nx}x{ny})")
    d = CACHE / "dem"
    d.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256(f"{xmin},{ymin},{xmax},{ymax},{res}".encode()).hexdigest()[:24]
    f = d / f"{key}.tif"
    if not f.exists():
        params = {"SERVICE": "WCS", "VERSION": "1.0.0", "REQUEST": "GetCoverage",
                  "COVERAGE": "las_dtm", "CRS": "EPSG:25833", "FORMAT": "GeoTIFF",
                  "BBOX": f"{xmin},{ymin},{xmax},{ymax}", "WIDTH": nx, "HEIGHT": ny}
        err = None
        for _ in range(2):
            try:
                r = requests.get(WCS, params=params, headers={"User-Agent": user_agent()}, timeout=180)
                if r.status_code == 200 and r.content[:4] in (b"II*\x00", b"MM\x00*"):
                    f.write_bytes(r.content)
                    break
                err = f"HTTP {r.status_code} {r.content[:120]!r}"
            except Exception as e:  # noqa: BLE001
                err = e
        else:
            raise RuntimeError(f"DTM-henting feilet: {err}")
    with rasterio.open(f) as src:
        a = src.read(1).astype("float64")
        if src.nodata is not None:
            a[a == src.nodata] = np.nan
        a[a < -100] = np.nan
        return a, src.transform


def slope_deg(a: np.ndarray, res: float) -> np.ndarray:
    gy, gx = np.gradient(a, res)
    return np.degrees(np.arctan(np.hypot(gx, gy)))
