"""Genererer docs/FINDINGS.md: funn (beregnet fra data) + forklaring av alle nøkler/kolonner."""
from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from .common import OUTPUT, PROCESSED, ROOT
from .scoring import CATS

STRUCT = {
    "id": ("Identitet", "-", "Unik id (k<kommunenr> eller h-<navn>)"),
    "navn": ("Identitet", "-", "Områdenavn"),
    "type": ("Identitet", "-", "kommune eller hyttefelt"),
    "kommunenr": ("Identitet", "-", "SSB/Geonorge kommunenummer (2024-inndeling)"),
    "kommune": ("Identitet", "-", "Kommunenavn"),
    "lat": ("Posisjon", "grader", "Breddegrad (kommune: snappet til vei)"),
    "lon": ("Posisjon", "grader", "Lengdegrad"),
    "loc_source": ("Posisjon", "-", "Hvordan posisjonen ble funnet"),
    "air_km": ("Kjøretid", "km", "Luftlinje fra Holmenkollen til kommunepunkt/hyttefelt"),
    "mountain_cabins": ("Identitet", "antall", "Fritidsbygg over 600 moh i kommunen (SSB 12511)"),
    "drive_km": ("Kjøretid", "km", "Kjørelengde (OSRM)"),
    "snap_m": ("Kjøretid", "m", "Avstand fra punktet til nærmeste vei (OSRM-snap)"),
    "elevation_source": ("Snø", "-", "Kilde for høyde (Kartverket eller fallback)"),
    "osm_ok": ("Kvalitet", "bool", "Overpass-punktspørring lyktes"),
    "osm_lines_ok": ("Kvalitet", "bool", "Overpass løype-/rutespørring lyktes"),
    "gathering_15km": ("Praktisk", "antall", "Samlingssteder (pub/bar/kafé) innen 15 km"),
    "ev_5km": ("Praktisk", "antall", "Ladestasjoner innen 5 km"),
    "grocery_5km": ("Praktisk", "antall", "Dagligvarebutikker innen 5 km"),
    "nearest_gathering_km": ("Praktisk", "km", "Avstand til nærmeste pub/bar/kafé"),
    "nearest_grocery_name": ("Praktisk", "-", "Navn på nærmeste dagligvare"),
    "eat_names": ("Praktisk", "-", "Navn på spisesteder innen 5 km"),
    "nordic_nearest_km": ("Rando", "km", "Avstand til nærmeste preparerte langrennsløype"),
    "dnt_routes_n": ("Rando", "antall", "Antall DNT-ruter (relasjoner) innen 15 km"),
    "terrain_elev_p90_m": ("Rando", "moh", "90-persentil av høyde innen 10 km"),
    "tax_rate_residential_permille": ("Økonomi", "‰", "Differensiert sats bolig/fritid"),
    "tax_has": ("Økonomi", "1/0", "Kommunen har eiendomsskatt"),
    "villrein_areas": ("Regler", "-", "Nasjonale villreinområder med fritidsbygg i kommunen"),
    "finn_price_per_m2_nok": ("Verdi", "NOK/m²", "Manuell Finn-statistikk (data/raw/finn_manual.csv), tom hvis ikke fylt"),
    "filter_reason": ("Filter", "-", "Hvorfor området falt ut (tom for rangerte)"),
    "passes": ("Filter", "bool", "Besto harde filtre"),
    "usikker": ("Filter", "bool", "Færre enn 15 salg siste år"),
    "trail_offer_km": ("Verdi", "km", "Løype-km (10 km) + merkede ruter-km (15 km)"),
    "score": ("Score", "0–100", "Totalscore, standardvekter"),
    "rank": ("Score", "#", "Rang etter totalscore"),
    **{c: ("Score", "0–1", f"Kategoriscore {c} (rangpersentil, vektet snitt av variabler)") for c in CATS},
}


def _f(v, nd=0):
    return "–" if v is None or (isinstance(v, float) and np.isnan(v)) else f"{v:,.{nd}f}".replace(",", " ")


def _row(r, c, nd=0, suf=""):
    return f"**{r['navn']}** ({_f(r[c], nd)}{suf})"


def build(cfg: dict) -> None:
    rk = pd.read_csv(OUTPUT / "ranking.csv", dtype={"kommunenr": str})
    fo = pd.read_csv(PROCESSED / "filtered_out.csv")
    se = pd.read_csv(OUTPUT / "sensitivity.csv")
    meta = pd.read_csv(PROCESSED / "variables.csv").set_index("variabel")
    f = cfg["filters"]
    L = [f"# Funn og nøkler ({date.today().isoformat()})\n",
         "Automatisk generert av `make report` fra `output/ranking.csv`. Tall er fra siste kjøring; se `output/rapport.md` for utfyllende rapport og forbehold.\n",
         "## Funn\n"]
    t = rk.head(3)
    L.append(f"- **Topp 3:** " + ", ".join(f"{r['rank']:.0f}. {r['navn']} ({r['score']:.1f})" for _, r in t.iterrows()) + ".")
    stable = se[se["topp5_andel"] >= 0.5]["navn"].tolist()
    L.append(f"- **Robusthet:** {len(stable)} områder er topp 5 i ≥ 50 % av {cfg['params']['sensitivity_runs']} tilfeldige vektsett: {', '.join(stable)}.")
    L.append(f"- **Filtre:** {len(fo)} av {len(rk) + len(fo)} kandidater falt ut. "
             f"{fo['filter_reason'].str.contains('kjøretid').sum()} på kjøretid (> {f['max_drive_min']} min), "
             f"{fo['filter_reason'].str.contains('snittpris|pris mangler').sum()} på pris.")
    L.append(f"- **Mest snø:** {_row(rk.loc[rk['ski_season_days'].idxmax()], 'ski_season_days', 0, ' dager')}; "
             f"høyest beliggenhet: {_row(rk.loc[rk['elevation_m'].idxmax()], 'elevation_m', 0, ' moh')}.")
    L.append(f"- **Billigst (snittpris kommune):** {_row(rk.loc[rk['avg_price_nok'].idxmin()], 'avg_price_nok', 0, ' kr')}; "
             f"dyrest: {_row(rk.loc[rk['avg_price_nok'].idxmax()], 'avg_price_nok', 0, ' kr')}.")
    L.append(f"- **Beste verdi (lavest pris per snøpoeng):** {_row(rk.loc[rk['value_price_per_snow'].idxmin()], 'value_price_per_snow', 0, ' kr/poeng')}.")
    L.append(f"- **Mest løyper:** {_row(rk.loc[rk['nordic_km_10km'].idxmax()], 'nordic_km_10km', 0, ' km innen 10 km')}.")
    L.append(f"- **Bratteste turterreng (25–40°):** {_row(rk.loc[rk['slope_25_40_share'].idxmax()], 'slope_25_40_share', 3, ' av arealet')} – 50 m DTM undervurderer helning.")
    L.append(f"- **Kjøretid:** {_row(rk.loc[rk['drive_min'].idxmin()], 'drive_min', 0, ' min')} er nærmest; "
             f"{_row(rk.loc[rk['drive_min'].idxmax()], 'drive_min', 0, ' min')} lengst blant rangerte.")
    far = rk[rk['nearest_grocery_km'] > 5]
    L.append(f"- **Praktisk:** {len(far)} av {len(rk)} områder har > 5 km til dagligvare ({', '.join(far['navn'].head(6))}"
             f"{'…' if len(far) > 6 else ''}); median avstand til Vinmonopol er {rk['nearest_vinmonopol_km'].median():.0f} km.")
    L.append(f"- **DNT-ruter:** {int((rk['dnt_routes_km_15km'] > 0).sum())} av {len(rk)} områder har DNT-merkede ruter innen 15 km i OSM.")
    hf = rk[rk["type"] == "hyttefelt"]
    L.append(f"- **Hyttefelt vs kommune:** rangerte hyttefelt: " + ", ".join(f"{r['navn']} (#{r['rank']:.0f})" for _, r in hf.iterrows()) + ".")
    L.append(f"- **Usikre priser:** {int(rk['usikker'].sum())} av {len(rk)} har < {f['min_sales_certain']} salg siste år.")
    empty = [c for c in rk.columns if rk[c].isna().all() and c != "filter_reason"]
    L.append("- **Helt tomme nøkler:** " + (", ".join(f"`{c}`" for c in empty) or "ingen") + " (se data/SOURCES.md for hvorfor).")
    L.append("\n## Nøkler (alle kolonner i `output/ranking.csv`)\n")
    L.append("`Dekning` = andel rangerte områder med verdi. Kilder/lisenser: `data/SOURCES.md`.\n")
    L.append("| Nøkkel | Kategori | Enhet | Beskrivelse | Kilde | Dekning |")
    L.append("|---|---|---|---|---|---|")
    for c in rk.columns:
        cov = f"{rk[c].notna().mean():.0%}"
        if c in meta.index:
            m = meta.loc[c]
            L.append(f"| `{c}` | {m['kategori']} | {m['enhet']} | {m['beskrivelse']} | {m['kilde']} | {cov} |")
        else:
            k, u, d = STRUCT.get(c, ("Annet", "-", "(se kode)"))
            L.append(f"| `{c}` | {k} | {u} | {d} | avledet/pipeline | {cov} |")
    for c in meta.index:
        if c not in rk.columns:
            m = meta.loc[c]
            L.append(f"| `{c}` | {m['kategori']} | {m['enhet']} | {m['beskrivelse']} | {m['kilde']} | 0 % (ikke i data) |")
    (ROOT / "docs" / "FINDINGS.md").write_text("\n".join(L) + "\n", encoding="utf-8")
