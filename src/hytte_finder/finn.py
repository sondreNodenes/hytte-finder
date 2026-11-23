"""Finn.no: lite, ENGANGS-uttrekk av annonsepriser for å anslå kr/m² per hyttefelt.

Forsiktighetsregler (Finns robots.txt/vilkår krever skriftlig tillatelse til automatisert bruk;
bruken her er brukerens eget valg og ansvar):
 * leser robots.txt maskinelt og henter kun tillatte URL-er
 * ett kall hver `FINN_PAUSE_S` sekunder, kun side 1 per søk, maks `max_clusters` søk
 * identifiserbar User-Agent, alle svar caches (aldri samme URL to ganger)
 * stopper ved alt annet enn HTTP 200 eller tegn på bot-sperre (omgår ALDRI blokkering)
 * kjøres kun manuelt (`make finn`), er ikke del av `make all`
 * rå annonsedata (adresser/lenker) lagres i data/raw/finn_listings.csv som er .gitignore-t;
   bare medianer går videre til datasettet.
"""
from __future__ import annotations

import hashlib
import html as htmllib
import logging
import re
import time
import urllib.robotparser as robotparser
from datetime import date
from urllib.parse import quote

import numpy as np
import pandas as pd
import requests

from .common import CACHE, RAW, user_agent

log = logging.getLogger("finn")
BASE = "https://www.finn.no/realestate/leisuresale/search.html"
FINN_PAUSE_S = 6.0
LISTINGS = RAW / "finn_listings.csv"
MANUAL = RAW / "finn_manual.csv"


class Blocked(RuntimeError):
    pass


def _norm(s: str) -> str:
    return re.sub(r"[^a-zæøå0-9]+", " ", s.lower()).strip()


def _num(s: str) -> float:
    return float(re.sub(r"[^\d]", "", s))


def parse_search(page: str) -> list[dict]:
    """Trekk ut annonser fra søkeresultatsiden (article.sf-search-ad). Rene tekstfelter."""
    ads, seen = [], set()
    for art in re.findall(r"<article.*?</article>", page, re.S):
        code = re.search(r"finnkode=(\d+)", art)
        if not code or code.group(1) in seen:
            continue
        txt = re.sub(r"<(script|style).*?</\1>", "", art, flags=re.S)
        txt = re.sub(r"<img[^>]*>", "", txt)
        parts = [htmllib.unescape(p).strip() for p in re.split(r"<[^>]+>", txt) if p.strip()]
        area = next((p for p in parts if re.fullmatch(r"\d[\d\s]*\sm²", p)), None)
        price = next((p for p in parts if re.fullmatch(r"\d[\d\s]*\skr", p)), None)
        total = next((p for p in parts if p.startswith("Totalpris")), None)
        kind = next((p for p in parts if "∙" in p and p != "∙"), "")
        i = parts.index(area) if area else -1
        loc = parts[i - 1] if i > 0 else ""
        if not (area and price):
            continue
        seen.add(code.group(1))
        ads.append({"finnkode": code.group(1), "location": loc, "area_m2": _num(area),
                    "price_nok": _num(price),
                    "total_price_nok": _num(total) if total and re.search(r"\d", total) else np.nan,
                    "type": next((t.strip() for t in kind.split("∙") if t.strip() in
                                  ("Hytte", "Leilighet", "Enebolig", "Tomannsbolig", "Tomt", "Rekkehus")), ""),
                    "ownership": kind.split("∙")[0].strip()})
    return ads


def _robots() -> robotparser.RobotFileParser:
    rb = requests.get("https://www.finn.no/robots.txt", headers={"User-Agent": user_agent()}, timeout=30)
    rb.raise_for_status()
    rp = robotparser.RobotFileParser()
    rp.parse(rb.text.splitlines())
    return rp


_last = 0.0


def fetch(q: str, rp: robotparser.RobotFileParser) -> str:
    global _last
    url = f"{BASE}?q={quote(q)}"
    if not rp.can_fetch(user_agent(), url):
        raise Blocked(f"robots.txt forbyr {url}")
    d = CACHE / "finn"
    d.mkdir(parents=True, exist_ok=True)
    f = d / (hashlib.sha256(url.encode()).hexdigest()[:24] + ".html")
    if f.exists():
        return f.read_text(encoding="utf-8")
    wait = FINN_PAUSE_S - (time.time() - _last)
    if wait > 0:
        time.sleep(wait)
    try:
        r = requests.get(url, headers={"User-Agent": user_agent(), "Accept-Language": "nb-NO"}, timeout=45)
    except requests.RequestException as e:   # timeout/nettverk: stopp rolig, ikke prøv hardere
        _last = time.time()
        raise Blocked(f"Finn svarte ikke ({type(e).__name__}) – stopper") from e
    _last = time.time()
    if r.status_code != 200:
        raise Blocked(f"HTTP {r.status_code} fra Finn – stopper (omgår ikke blokkering)")
    if re.search(r"captcha|access denied|are you a robot", r.text[:8000], re.I):
        raise Blocked("Bot-sperre oppdaget – stopper")
    f.write_text(r.text, encoding="utf-8")
    return r.text


def match_cluster(ads: list[dict], navn: str, kommune: str) -> list[dict]:
    """Behold hytter hvis stedsangivelse inneholder feltnavnet (søket er fritekst og kan gi treff andre steder)."""
    key = _norm(navn)
    return [a for a in ads if a["type"] == "Hytte" and key and key in _norm(a["location"])]


def run(areas: pd.DataFrame, max_clusters: int = 30) -> pd.DataFrame:
    """Hent annonser for inntil max_clusters felt (de som består filtrene; best rangerte hvis ranking finnes):
    ett søk på feltnavn per felt (nivå «felt») og ett søk per kommune (nivå «kommune», fallback)."""
    ok = areas[areas["passes"]]
    ok = ok.sort_values("drive_min").head(max_clusters) if len(ok) > max_clusters else ok
    rp = _robots()
    rows, n = [], 0
    try:
        for _, r in ok.iterrows():
            n += 1
            log.info("Finn: felt '%s' (%d/%d)", r["navn"], n, len(ok))
            for a in match_cluster(parse_search(fetch(r["navn"], rp)), r["navn"], r["kommune"]):
                rows.append({**a, "cluster_id": r["id"], "cluster": r["navn"], "nivaa": "felt", "kilde": "finn",
                             "dato": date.today().isoformat()})
        for nr, k in ok.drop_duplicates("kommunenr").set_index("kommunenr")["kommune"].items():
            log.info("Finn: kommune '%s'", k)
            for a in parse_search(fetch(k, rp)):
                if a["type"] == "Hytte":
                    rows.append({**a, "cluster_id": f"kommune:{nr}", "cluster": k, "nivaa": "kommune",
                                 "kilde": "finn", "dato": date.today().isoformat()})
    except Blocked as e:
        log.error("%s – avbrutt, lagrer det som er hentet", e)
    df = pd.DataFrame(rows)
    RAW.mkdir(parents=True, exist_ok=True)
    df.to_csv(LISTINGS, index=False)
    log.info("Lagret %d annonser i %s (ikke i git)", len(df), LISTINGS.name)
    return df


def _med(a: pd.DataFrame) -> pd.DataFrame:
    a = a[(a["area_m2"] > 0) & (a["price_nok"] > 0)].copy()
    a["ppm2"] = a["price_nok"] / a["area_m2"]
    return a.groupby("cluster_id").agg(finn_n_ads=("price_nok", "size"), finn_median_price_nok=("price_nok", "median"),
                                       finn_median_price_per_m2=("ppm2", "median"),
                                       finn_median_area_m2=("area_m2", "median")).reset_index()


def aggregate(areas: pd.DataFrame, min_ads: int, min_ads_kommune: int | None = None) -> pd.DataFrame:
    """Medianer per felt. Felt-nivå (annonser der stedet inneholder feltnavnet, + manuell CSV
    `nokkel,pris_nok,bra_m2`) brukes hvis ≥ min_ads annonser; ellers kommune-nivå (søk på kommunenavn) hvis
    ≥ min_ads; ellers den tynne felt-verdien. Kolonne finn_level = felt|kommune."""
    min_k = min_ads if min_ads_kommune is None else min_ads_kommune
    cols = ["id", "finn_n_ads", "finn_median_price_nok", "finn_median_price_per_m2", "finn_median_area_m2", "finn_level"]
    frames = []
    if LISTINGS.exists() and LISTINGS.stat().st_size > 5:
        frames.append(pd.read_csv(LISTINGS)[["cluster_id", "price_nok", "area_m2"]])
    if MANUAL.exists() and MANUAL.stat().st_size > 5:
        m = pd.read_csv(MANUAL)
        if {"nokkel", "pris_nok", "bra_m2"} <= set(m.columns):
            key = {}
            for _, r in areas.iterrows():
                for k in (r["id"], r["navn"], r["kommune"]):
                    key.setdefault(str(k), r["id"])
            m["cluster_id"] = m["nokkel"].astype(str).map(key)
            frames.append(m.dropna(subset=["cluster_id"]).rename(
                columns={"pris_nok": "price_nok", "bra_m2": "area_m2"})[["cluster_id", "price_nok", "area_m2"]])
    if not frames:
        return pd.DataFrame(columns=cols)
    g = _med(pd.concat(frames)).set_index("cluster_id")
    out = []
    for _, r in areas.iterrows():
        felt = g.loc[r["id"]] if r["id"] in g.index else None
        kom = g.loc[f"kommune:{r['kommunenr']}"] if f"kommune:{r['kommunenr']}" in g.index else None
        if felt is not None and felt["finn_n_ads"] >= min_ads:
            pick, lvl = felt, "felt"
        elif kom is not None and kom["finn_n_ads"] >= min_k:
            pick, lvl = kom, "kommune"
        elif felt is not None:
            pick, lvl = felt, "felt"
        else:
            continue
        out.append({"id": r["id"], **pick.to_dict(), "finn_level": lvl})
    return pd.DataFrame(out, columns=cols)
