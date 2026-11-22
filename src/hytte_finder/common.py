"""Felles hjelpefunksjoner: stier, config, cachet HTTP med retry/backoff."""
from __future__ import annotations

import hashlib
import json
import math
import os
import time
from pathlib import Path

import requests
import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
CACHE = ROOT / "data" / "cache"
OUTPUT = ROOT / "output"
CONFIG = ROOT / "config"

load_dotenv(ROOT / ".env")


def user_agent() -> str:
    mail = os.getenv("CONTACT_EMAIL", "").strip()
    base = "hytte-finder/0.1 (student project)"
    return f"{base} {mail}" if mail else base


def load_config(path: Path | None = None) -> dict:
    with open(path or CONFIG / "weights.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def haversine_km(lat1, lon1, lat2, lon2) -> float:
    r = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


_last_call: dict[str, float] = {}


def _key(method: str, url: str, params, data) -> str:
    blob = json.dumps([method, url, params, data], sort_keys=True, default=str)
    return hashlib.sha256(blob.encode()).hexdigest()[:40]


def cached_request(method: str, url: str, *, params=None, data=None, json_body=None,
                   pause: float = 1.0, retries: int = 4, timeout: int = 90,
                   binary: bool = False, ns: str = "http"):
    """HTTP med disk-cache, pause mellom kall per vert og eksponentiell backoff.

    Returnerer parsed JSON (eller bytes hvis binary=True). Kaster RuntimeError
    etter `retries` mislykkede forsøk.
    """
    CACHE.mkdir(parents=True, exist_ok=True)
    d = CACHE / ns
    d.mkdir(exist_ok=True)
    k = _key(method, url, params, data if data is not None else json_body)
    f = d / (k + (".bin" if binary else ".json"))
    if f.exists():
        return f.read_bytes() if binary else json.loads(f.read_text(encoding="utf-8"))
    host = url.split("/")[2]
    last_err = None
    for attempt in range(retries):
        wait = pause - (time.time() - _last_call.get(host, 0))
        if wait > 0:
            time.sleep(wait)
        try:
            r = requests.request(method, url, params=params, data=data, json=json_body,
                                 headers={"User-Agent": user_agent()}, timeout=timeout)
            _last_call[host] = time.time()
            if r.status_code in (429, 502, 503, 504):
                raise RuntimeError(f"HTTP {r.status_code}")
            if 400 <= r.status_code < 500:  # klientfeil: ikke prøv på nytt
                raise ValueError(f"HTTP {r.status_code}: {r.text[:200]}")
            r.raise_for_status()
            if binary:
                f.write_bytes(r.content)
                return r.content
            out = r.json()
            f.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
            return out
        except ValueError as e:
            raise RuntimeError(f"{url}: {e}") from e
        except Exception as e:  # noqa: BLE001
            last_err = e
            time.sleep(min(60, 2 ** attempt * 3))
    raise RuntimeError(f"Mislyktes etter {retries} forsøk: {url} ({last_err})")


def get_json(url, **kw):
    return cached_request("GET", url, **kw)


def post_json(url, **kw):
    return cached_request("POST", url, **kw)
