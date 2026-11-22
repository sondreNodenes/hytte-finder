"""Genererer output/rapport.md (norsk) fra ranking, profiler og sensitivitet."""
from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from .common import OUTPUT, PROCESSED
from .scoring import CATS


def _f(v, nd=0, suf="") -> str:
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "–"
    return f"{v:,.{nd}f}".replace(",", " ") + suf


def _md(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    out = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for _, r in df.iterrows():
        out.append("| " + " | ".join(str(x) for x in r.values) + " |")
    return "\n".join(out)


def _why(r: pd.Series) -> str:
    cats = {c: r[c] for c in CATS if pd.notna(r.get(c))}
    best = sorted(cats, key=cats.get, reverse=True)[:2]
    worst = min(cats, key=cats.get)
    bits = [f"sterkest på {best[0]} ({cats[best[0]]:.2f}) og {best[1]} ({cats[best[1]]:.2f}); svakest på {worst} ({cats[worst]:.2f})"]
    facts = [f"{_f(r.get('drive_min', np.nan))} min kjøring (vinter ca. {_f(r.get('drive_min_winter', np.nan))})",
             f"{_f(r.get('elevation_m', np.nan))} moh", f"skisesong {_f(r.get('ski_season_days', np.nan))} dager (modellert 1991–2020)",
             f"snittpris i kommunen {_f(r.get('avg_price_nok', np.nan)/1e6, 2)} mill ({_f(r.get('sales_pooled', np.nan))} salg samlet, {_f(r.get('sales_last_year', np.nan))} siste år)"]
    if pd.notna(r.get("nordic_km_10km")):
        facts.append(f"{_f(r['nordic_km_10km'])} km preparerte løyper innen 10 km")
    if pd.notna(r.get("nearest_grocery_km")):
        facts.append(f"dagligvare {_f(r['nearest_grocery_km'],1)} km unna")
    s = f"{'; '.join(bits)}. " + "; ".join(facts) + "."
    if r.get("usikker"):
        s += " **Usikker pris:** færre enn 15 salg siste år."
    return s


def build(cfg: dict) -> None:
    rk = pd.read_csv(OUTPUT / "ranking.csv", dtype={"kommunenr": str})
    pr = pd.read_csv(OUTPUT / "ranking_profiler.csv")
    se = pd.read_csv(OUTPUT / "sensitivity.csv")
    fo = pd.read_csv(PROCESSED / "filtered_out.csv", dtype={"kommunenr": str})
    meta = pd.read_csv(PROCESSED / "variables.csv")
    f, p, w = cfg["filters"], cfg["params"], cfg["weights"]["default"]
    top = rk.head(10)

    L = []
    L.append(f"# Hytte-finder: rapport ({date.today().isoformat()})\n")
    L.append(f"*Beslutningsstøtte, ikke finansiell rådgivning.* Rangering av {len(rk)} fjellområder "
             f"(kommuner og hyttefelt) innen {f['max_drive_min']} min kjøring fra {cfg['home']['navn']} "
             f"for budsjett {f['price_min_nok']/1e6:.1f}–{f['price_max_nok']/1e6:.1f} mill. kr.\n")
    L.append("## Sammendrag: topp 10 (standardvekter)\n")
    L.append("Vekter: " + ", ".join(f"{k} {v:.0%}" for k, v in w.items()) + ".\n")
    t = pd.DataFrame({
        "#": top["rank"], "Område": top["navn"], "Type": top["type"], "Kommune": top["kommune"],
        "Score": top["score"].map(lambda v: _f(v, 1)), "Kjøretid (min)": top["drive_min"].map(_f),
        "Snittpris (mill)": (top["avg_price_nok"] / 1e6).map(lambda v: _f(v, 2)),
        "Skisesong (d)": top.get("ski_season_days", pd.Series(np.nan, index=top.index)).map(_f), "Moh": top["elevation_m"].map(_f),
        "Usikker pris": top["usikker"].map(lambda b: "ja" if b else "")})
    L.append(_md(t) + "\n")
    L.append("### Begrunnelse\n")
    for _, r in top.iterrows():
        L.append(f"{int(r['rank'])}. **{r['navn']}** ({r['type']}, {r['kommune']}) – {_why(r)}")
    L.append("")

    L.append("## Profiler (alternative vektsett)\n")
    for name, g in pr.groupby("profil", sort=False):
        wts = cfg["profiles"][name]
        L.append(f"### {name}\nVekter: " + ", ".join(f"{k} {v:.0%}" for k, v in wts.items()) + "\n")
        g = g.sort_values("rank").head(10)
        L.append(_md(pd.DataFrame({"#": g["rank"], "Område": g["navn"], "Type": g["type"],
                                   "Kommune": g["kommune"], "Score": g["score"].map(lambda v: _f(v, 1))})) + "\n")

    L.append("## Sensitivitetsanalyse\n")
    L.append(f"{p['sensitivity_runs']} tilfeldige vektsett (Dirichlet, konsentrasjon {p['sensitivity_alpha']}, "
             f"rundt standardvektene). Tabellen viser hvor ofte området havner i topp 5 / topp 10.\n")
    s = se.head(15)
    L.append(_md(pd.DataFrame({"Område": s["navn"], "Type": s["type"], "Std.rang": s["rank"],
                               "Topp 5": s["topp5_andel"].map(lambda v: f"{v:.0%}"),
                               "Topp 10": s["topp10_andel"].map(lambda v: f"{v:.0%}"),
                               "Snittrang": s["snittrang"].map(lambda v: _f(v, 1)),
                               "Rangspenn": s.apply(lambda r: f"{int(r['beste_rang'])}–{int(r['dårligste_rang'])}", axis=1)})) + "\n")
    stable = se[se["topp5_andel"] >= 0.5]["navn"].tolist()
    L.append("Områder som er i topp 5 i minst halvparten av kjøringene: " + (", ".join(stable) or "ingen") + ". "
             "Områder som bare er topp 5 i få kjøringer bør leses som «avhengig av vektene».\n")

    L.append("## Hva dataene faktisk viser\n")
    L.append(f"- {len(fo)} av {len(rk) + len(fo)} kandidater falt ut på harde filtre "
             f"(kjøretid > {f['max_drive_min']} min eller snittpris > {f['price_max_nok']*f['price_tolerance']/1e6:.2f} mill / manglende pris).")
    L.append(f"- {int(rk['usikker'].sum())} av {len(rk)} rangerte områder har færre enn {f['min_sales_certain']} salg siste år (priser er usikre).")
    miss = rk[[c for c in meta["variabel"] if c in rk.columns]].isna().mean().sort_values(ascending=False)
    miss = miss[miss > 0.3]
    if len(miss):
        L.append("- Variabler med mer enn 30 % manglende verdi blant rangerte områder: " + ", ".join(f"`{k}` ({v:.0%})" for k, v in miss.items()) + ".")
    L.append("- Variabler som ikke finnes som åpne data (NaN i hele datasettet): "
             + ", ".join(f"`{r.variabel}`" for r in meta.itertuples() if r.kilde.startswith(("NVE – utilg", "Nkom", "SSB – ikke"))) + ".\n")

    L.append("## Forbehold\n")
    L += [
        "- **Snitt, ikke median:** SSB publiserer kun snitt og antall salg per kommune (tabell 11694). Snitt trekkes opp av enkeltdyre salg. Skille mellom nye og brukte hytter finnes ikke. Prisen er kommuneprisen, ikke prisen i det enkelte hyttefelt.",
        "- **Små salgsvolum:** Kommuner med få salg har svært ustabile snitt (markert «usikker»).",
        "- **Modellert snø:** Skisesong og snømengde er modellerte 1x1 km-data (1991–2020) midlet over radius, ikke målinger. Datasettet for snødybde >30 cm (1971–2000) var ikke tilgjengelig; framskrivning gjelder 2041–2070 (RCP4.5), ikke 2031–2060.",
        "- **Kjøretid:** OSRM (åpen demo-server) uten trafikk/føre. Vinterkjøretid er kun sommer × " + str(f["winter_factor"]) + ". Kommuner plasseres i tyngdepunktet av arealet i høydebåndet 600–1100 moh (snappet til vei), ikke der hyttene faktisk ligger.",
        "- **OSM-dekning:** Antall og avstand til tilbud avhenger av hva som er kartlagt. Åpningstider mangler ofte. Ruter og løyper er telt som lengde innen radius.",
        "- **Terreng:** 50 m DTM jevner ut helning og undervurderer bratt terreng. Skredaktsomhet er kontekst, **ikke sikkerhetsvurdering**. Vurder alltid skredfare (Varsom.no) lokalt.",
        "- **Mobildekning/bredbånd, eierbosted (venneproxy), snødybde fra stasjoner (Frost) og Finn-priser** er ikke med (se README/SOURCES). Fyll gjerne `config/venner.csv`.",
        "- **Pris og kjøretid må verifiseres mot aktuelle annonser før kjøp.**\n",
    ]
    L.append("## Fem neste steg\n")
    hf = rk[rk["type"] == "hyttefelt"].head(3)["navn"].tolist()
    L += [
        f"1. Søk på Finn.no etter hytter i {', '.join(hf) if hf else 'toppområdene'} og noter faktiske priser, m² og kjøretid (legg gjerne m²-pris i `data/raw/finn_manual.csv`, kolonner: kommune, pris_per_m2_nok).",
        "2. Fyll ut `config/venner.csv` og kjør `make score report` på nytt – Sosialt-kategorien teller da med.",
        "3. Test vektfølsomhet i `config/weights.yaml` (f.eks. Snø 40 % / Verdi 15 %) og se om topp 5 er stabil.",
        "4. På visning: vinterbrøyting og vei (brøyteavtale, veilag, avgift), vann/avløp (privat brønn/slamavskiller eller kommunalt), strøm og oppvarming, mobildekning/fiber, bunnlinje for vedlikehold (tak, kledning, fukt/råte, fellesutgifter, eiendomsskatt).",
        "5. Besøk 2–3 toppområder i februar–mars: sjekk snøforhold, løypetilgang, støy/trafikk og avstand til dagligvare og apotek, og sjekk reguleringsplan (utbyggingsplaner, villrein-/byggerestriksjoner) hos kommunen.\n",
    ]
    (OUTPUT / "rapport.md").write_text("\n".join(L), encoding="utf-8")
