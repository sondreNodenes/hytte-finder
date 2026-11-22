"""Enkelt, selvstendig dashboard (output/dashboard.html): sorterbar rangering, kategoriscorer,
sensitivitet. Ingen eksterne avhengigheter; data bygges inn som JSON."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from .common import OUTPUT, PROCESSED
from .scoring import CATS

TEMPLATE = """<!doctype html><html lang="no"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Hytte-finder dashboard</title>
<style>
:root{--bg:#fafaf7;--fg:#1d2420;--mut:#66706a;--card:#fff;--line:#e2e5df;--acc:#2f7d57;--bar:#cfe5d8}
@media(prefers-color-scheme:dark){:root{--bg:#141a16;--fg:#e6ebe7;--mut:#94a09a;--card:#1c241f;--line:#2c3631;--acc:#58c08a;--bar:#2b4a3a}}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.45 system-ui,sans-serif}
main{max-width:1100px;margin:0 auto;padding:24px 16px}
h1{margin:0 0 4px;font-size:26px}h2{margin:32px 0 10px;font-size:18px}
.sub{color:var(--mut);margin-bottom:18px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px}
.card b{display:block;font-size:24px}.card span{color:var(--mut);font-size:13px}
.wrap{overflow-x:auto;background:var(--card);border:1px solid var(--line);border-radius:10px}
table{border-collapse:collapse;width:100%;font-size:14px}
th,td{padding:7px 10px;text-align:left;border-bottom:1px solid var(--line);white-space:nowrap}
th{cursor:pointer;color:var(--mut);font-weight:600;position:sticky;top:0;background:var(--card)}
td.n{text-align:right;font-variant-numeric:tabular-nums}
.bar{display:inline-block;height:8px;background:var(--acc);border-radius:4px;vertical-align:middle;margin-right:6px}
.cat{display:inline-block;width:46px;text-align:center;border-radius:4px;font-size:12px;padding:1px 0;margin-right:2px}
.tag{font-size:11px;border:1px solid var(--line);border-radius:10px;padding:0 6px;color:var(--mut)}
.warn{color:#b8860b}a{color:var(--acc)}.note{color:var(--mut);font-size:13px;margin-top:8px}
</style></head><body><main>
<h1>Hytte-finder</h1>
<div class="sub">Rangering av fjellområder innen __MAXDRIVE__ min fra __HOME__ · budsjett __BUDGET__ mill. kr · generert fra <code>output/ranking.csv</code></div>
<div class="cards" id="cards"></div>
<h2>Rangering (klikk på kolonne for å sortere)</h2>
<div class="wrap"><table id="t"></table></div>
<div class="note">Kategoriscorer 0–1 (rangpersentil blant rangerte områder). ⚠ = kommunesnitt fra SSB (ingen Finn-annonser nok for feltet); uten ⚠ = median fra Finn/manuell. kr/m² vises bare når nok annonser finnes.</div>
<h2>Sensitivitet: andel av 1000 tilfeldige vektsett i topp 5</h2>
<div class="wrap"><table id="s"></table></div>
<h2>Mer</h2>
<p><a href="map.html">Kart (Leaflet)</a> · <a href="rapport.md">Rapport</a> · <a href="ranking.csv">ranking.csv</a> · <a href="../docs/FINDINGS.md">Funn og nøkler</a></p>
<p class="note">Beslutningsstøtte, ikke finansiell rådgivning. Verifiser pris og kjøretid mot aktuelle annonser.</p>
</main><script>
const D=__DATA__, S=__SENS__, CATS=__CATS__;
const f=(v,n=0)=>v==null?'–':Number(v).toLocaleString('nb-NO',{maximumFractionDigits:n});
const col=v=>v==null?'transparent':`hsl(${Math.round(v*120)},45%,${matchMedia('(prefers-color-scheme:dark)').matches?28:80}%)`;
document.getElementById('cards').innerHTML=[[D.length,'rangerte områder'],[__OUT__,'filtrert bort'],
 [D[0].navn,'høyest score ('+f(D[0].score,1)+')'],[f(Math.min(...D.map(d=>d.drive_min))),'korteste kjøretid (min)']]
 .map(([a,b])=>`<div class="card"><b>${a}</b><span>${b}</span></div>`).join('');
let sortKey='rank',asc=true;
const COLS=[['rank','#'],['navn','Hyttefelt'],['kommune','Kommune'],['n_cabins','Hytter'],['score','Score'],...CATS.map(c=>[c,c]),
 ['drive_min','Kjøretid'],['price_used_nok','Pris'],['price_per_m2_used','kr/m²'],['ski_season_days','Skisesong'],['elevation_m','Moh'],['nordic_km_10km','Løype km']];
function draw(){
 const rows=[...D].sort((a,b)=>{const x=a[sortKey],y=b[sortKey];if(x==null)return 1;if(y==null)return -1;
  return (typeof x==='string'?x.localeCompare(y):x-y)*(asc?1:-1)});
 document.getElementById('t').innerHTML='<tr>'+COLS.map(([k,l])=>`<th data-k="${k}">${l}</th>`).join('')+'</tr>'+
 rows.map(r=>'<tr>'+COLS.map(([k])=>{const v=r[k];
  if(k==='score')return `<td class="n"><span class="bar" style="width:${v*0.6}px"></span>${f(v,1)}</td>`;
  if(CATS.includes(k))return `<td><span class="cat" style="background:${col(v)}">${v==null?'–':f(v,2)}</span></td>`;
  if(k==='price_used_nok')return `<td class="n ${r.price_source&&r.price_source.startsWith('SSB')?'warn':''}" title="${r.price_source||''}">${f(v/1e6,2)} mill${r.price_source&&r.price_source.startsWith('SSB')?' ⚠':''}</td>`;
  if(k==='price_per_m2_used')return `<td class="n">${v==null?'–':f(v)}</td>`;
  if(k==='drive_min')return `<td class="n">${f(v)} min</td>`;
  if(k==='type')return `<td><span class="tag">${v}</span></td>`;
  return typeof v==='number'?`<td class="n">${f(v,k==='rank'?0:0)}</td>`:`<td>${v??'–'}</td>`}).join('')+'</tr>').join('');
 document.querySelectorAll('#t th').forEach(th=>th.onclick=()=>{const k=th.dataset.k;asc=k===sortKey?!asc:(k==='navn'||k==='type'||k==='rank'||k==='drive_min'||k==='avg_price_nok');sortKey=k;draw()});
}
draw();
document.getElementById('s').innerHTML='<tr><th>Område</th><th>Std.rang</th><th>Topp 5</th><th>Topp 10</th><th>Rangspenn</th></tr>'+
 S.slice(0,15).map(s=>`<tr><td>${s.navn}</td><td class="n">${s.rank}</td><td><span class="bar" style="width:${s.topp5_andel*120}px"></span>${f(s.topp5_andel*100)}%</td><td class="n">${f(s.topp10_andel*100)}%</td><td class="n">${s.beste_rang}–${s['dårligste_rang']}</td></tr>`).join('');
</script></body></html>"""


def _clean(df: pd.DataFrame) -> list[dict]:
    return json.loads(df.replace({np.nan: None}).to_json(orient="records"))


def build(cfg: dict) -> None:
    rk = pd.read_csv(OUTPUT / "ranking.csv", dtype={"kommunenr": str})
    se = pd.read_csv(OUTPUT / "sensitivity.csv")
    fo = pd.read_csv(PROCESSED / "filtered_out.csv")
    keep = ["rank", "navn", "kommune", "n_cabins", "score", *CATS, "drive_min", "price_used_nok",
            "price_per_m2_used", "price_source", "usikker", "ski_season_days", "elevation_m", "nordic_km_10km"]
    f = cfg["filters"]
    html = (TEMPLATE.replace("__DATA__", json.dumps(_clean(rk[keep])))
            .replace("__SENS__", json.dumps(_clean(se)))
            .replace("__CATS__", json.dumps([c for c in CATS if rk[c].notna().any()], ensure_ascii=False))
            .replace("__OUT__", str(len(fo))).replace("__MAXDRIVE__", str(f["max_drive_min"]))
            .replace("__HOME__", cfg["home"]["navn"])
            .replace("__BUDGET__", f"{f['price_min_nok']/1e6:.1f}–{f['price_max_nok']/1e6:.1f}"))
    (OUTPUT / "dashboard.html").write_text(html, encoding="utf-8")
