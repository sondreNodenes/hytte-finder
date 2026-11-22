"""SSB PxWeb (json-stat2) klient + uttrekk for hytteomsetning, fritidsbygg og eiendomsskatt."""
from __future__ import annotations

import re

import pandas as pd

from .common import post_json

API = "https://data.ssb.no/api/v0/no/table/{}"


def query_table(table: str, selections: dict[str, list[str] | None]) -> pd.DataFrame:
    """Hent en SSB-tabell som lang DataFrame. selections: {dim: [verdier] | None (=alle)}.
    Dimensjoner som ikke nevnes hentes ikke (SSB krever alle -> bruk None for alle)."""
    q = []
    for code, vals in selections.items():
        sel = ({"filter": "all", "values": ["*"]} if vals is None
               else {"filter": "item", "values": vals})
        q.append({"code": code, "selection": sel})
    body = {"query": q, "response": {"format": "json-stat2"}}
    js = post_json(API.format(table), json_body=body, pause=1.0, ns="ssb")
    return jsonstat_to_df(js)


def jsonstat_to_df(js: dict) -> pd.DataFrame:
    ids, sizes = js["id"], js["size"]
    cats = []
    for d in ids:
        c = js["dimension"][d]["category"]
        idx = c["index"]
        order = sorted(idx, key=idx.get) if isinstance(idx, dict) else list(idx)
        cats.append([(k, c.get("label", {}).get(k, k)) for k in order])
    import itertools
    rows = []
    vals = js["value"]
    for i, combo in enumerate(itertools.product(*[range(s) for s in sizes])):
        row = {}
        for d, ci, cat in zip(ids, combo, cats):
            row[d] = cat[ci][0]
            row[d + "_label"] = cat[ci][1]
        row["value"] = vals[i] if not isinstance(vals, dict) else vals.get(str(i))
        rows.append(row)
    return pd.DataFrame(rows)


def mountain_cabins(min_masl: int, year: str = "2025") -> pd.DataFrame:
    """Fritidsbygg >= min_masl per kommune (SSB 12511)."""
    df = query_table("12511", {"Region": None, "HoydeOvHavet": None, "StorrOmrade": None,
                               "ContentsCode": ["Bygg"], "Tid": [year]})

    def lo(label: str) -> float:
        m = re.match(r"\s*(\d+)", label)
        return float(m.group(1)) if m else float("nan")

    df["lo"] = df["HoydeOvHavet_label"].map(lo)
    df = df[df["lo"] >= min_masl]
    out = df.groupby(["Region", "Region_label"], as_index=False)["value"].sum()
    return out.rename(columns={"Region": "kommunenr", "Region_label": "kommune",
                               "value": "mountain_cabins"})


def cabin_sales(years: list[int]) -> pd.DataFrame:
    """SSB 11694: omsetninger og kjøpesum (1000 kr) per kommune og år."""
    df = query_table("11694", {"Region": None, "ContentsCode": ["Omsetninger", "Kjopesum"],
                               "Tid": [str(y) for y in years]})
    p = df.pivot_table(index=["Region", "Tid"], columns="ContentsCode", values="value",
                       aggfunc="first").reset_index()
    p["Tid"] = p["Tid"].astype(int)
    p = p.rename(columns={"Region": "kommunenr", "Omsetninger": "n", "Kjopesum": "sum_1000"})
    return p


def price_summary(years: list[int]) -> pd.DataFrame:
    """Per kommune: snittpris sammenslått over years, antall salg samlet og siste år."""
    p = cabin_sales(years)
    last = p[p["Tid"] == max(years)][["kommunenr", "n"]].rename(columns={"n": "sales_last_year"})
    g = p.groupby("kommunenr").agg(sales_pooled=("n", "sum"), sum_pooled=("sum_1000", "sum"))
    g = g.reset_index().merge(last, on="kommunenr", how="left")
    g["avg_price_nok"] = g["sum_pooled"] * 1000 / g["sales_pooled"].where(g["sales_pooled"] > 0)
    return g.drop(columns="sum_pooled")


def property_tax(year: str = "2025") -> pd.DataFrame:
    """SSB 14674 (KOSTRA): eiendomsskatt. Returnerer fritidseiendom-relevante felt per kommune."""
    want = {
        "Har kommunen innført eiendomsskatt? (ja=1, nei=0)": "tax_has",
        "Generell eiendomsskattesats (per 1000)": "tax_rate_permille",
        "Differensiert skattesats for bolig- og fritidseiendommer (per 1000)": "tax_rate_residential_permille",
        "Gir kommunen eiendomsskattefritak for fritidseiendommer? (ja=1, nei=0)": "tax_exempt_cabins",
        "Herav eiendomsskatt fra fritidsboliger (1000 kr)": "tax_cabins_total_1000",
    }
    df = query_table("14674", {"KOKkommuneregion0000": None, "ContentsCode": None, "Tid": [year]})
    df = df[df["ContentsCode_label"].isin(want)]
    df["var"] = df["ContentsCode_label"].map(want)
    p = df.pivot_table(index="KOKkommuneregion0000", columns="var", values="value",
                       aggfunc="first").reset_index()
    return p.rename(columns={"KOKkommuneregion0000": "kommunenr"})


def villrein_cabins(year: str = "2025") -> pd.DataFrame:
    """SSB 12761: fritidsbygg i nasjonale villreinområder per kommune (kontekst for regelverk)."""
    df = query_table("12761", {"Region": None, "VillreinOmrReg": None, "StorrOmrade": None,
                               "ContentsCode": ["Bygg"], "Tid": [year]})
    df = df[df["value"].fillna(0) > 0]
    g = df.groupby("Region").agg(
        villrein_cabins=("value", "sum"),
        villrein_areas=("VillreinOmrReg_label", lambda s: ", ".join(sorted(set(s)))))
    return g.reset_index().rename(columns={"Region": "kommunenr"})
