"""Interaktivt kart (folium/Leaflet): farge etter score, popup med alle variabler."""
from __future__ import annotations

import html

import folium
import pandas as pd
from branca.colormap import LinearColormap

from .common import OUTPUT, PROCESSED

HIDE = {"passes", "filter_reason"}


def _popup(row: pd.Series, meta: dict) -> str:
    rows = []
    for k, v in row.items():
        if k in HIDE or pd.isna(v) or v == "":
            continue
        if isinstance(v, float):
            v = f"{v:,.2f}".rstrip("0").rstrip(".") if abs(v) < 1000 else f"{v:,.0f}"
        unit = meta.get(k, "")
        rows.append(f"<tr><td><b>{html.escape(str(k))}</b></td><td>{html.escape(str(v))} {html.escape(unit)}</td></tr>")
    return ("<div style='max-height:320px;overflow:auto;font-size:12px'><table>" + "".join(rows) + "</table></div>")


def build(cfg: dict) -> None:
    ranked = pd.read_csv(OUTPUT / "ranking.csv", dtype={"kommunenr": str})
    out = pd.read_csv(PROCESSED / "filtered_out.csv", dtype={"kommunenr": str})
    meta = pd.read_csv(PROCESSED / "variables.csv")
    units = dict(zip(meta["variabel"], meta["enhet"]))
    h = cfg["home"]
    m = folium.Map(location=[60.8, 9.8], zoom_start=7, tiles="OpenStreetMap")
    folium.Marker([h["lat"], h["lon"]], tooltip=h["navn"], icon=folium.Icon(color="blue", icon="home")).add_to(m)
    cm = LinearColormap(["#d73027", "#fee08b", "#1a9850"], vmin=ranked["score"].min(), vmax=ranked["score"].max(),
                        caption="Totalscore (0–100, standardvekter)")
    for _, r in ranked.iterrows():
        shape = dict(radius=5 + min(14.0, float(r.get("n_cabins", 25)) ** 0.5 / 3))
        folium.CircleMarker([r["lat"], r["lon"]], color="black", weight=1, fill=True, fill_opacity=0.9,
                            fill_color=cm(r["score"]), tooltip=f"#{int(r['rank'])} {r['navn']} ({r['kommune']}, {int(r['n_cabins'])} hytter) – {r['score']:.0f}",
                            popup=folium.Popup(_popup(r, units), max_width=420), **shape).add_to(m)
    g = folium.FeatureGroup(name="Filtrert bort (grå)", show=False)
    for _, r in out.iterrows():
        folium.CircleMarker([r["lat"], r["lon"]], radius=4, color="#888", fill=True, fill_opacity=0.6,
                            tooltip=f"{r['navn']}: {r['filter_reason']}").add_to(g)
    g.add_to(m)
    cm.add_to(m)
    folium.LayerControl().add_to(m)
    OUTPUT.mkdir(exist_ok=True)
    m.save(str(OUTPUT / "map.html"))
