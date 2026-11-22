# hytte-finder

Datadrevet rangering av norske fjellområder (kommuner og hyttefelt) for hyttekjøp: snøsikkerhet, pris mot hva man får og praktiske forhold. Utgangspunkt: Holmenkollen, maks 2 t 45 min kjøring, budsjett 3,0–3,9 mill. kr.

> Beslutningsstøtte, ikke finansiell rådgivning. Pris og kjøretid må verifiseres mot aktuelle annonser.

## Kjøring

Krever Python ≥ 3.11 og [`uv`](https://docs.astral.sh/uv/) (alternativt `pip install -r requirements.txt`).

```bash
make setup     # lager .venv og installerer avhengigheter
cp .env.example .env   # fyll inn CONTACT_EMAIL (brukes i User-Agent)
make data      # henter og renser alle data  -> data/processed/areas.csv   (første kjøring tar ~1 time pga. Overpass)
make score     # filtre + score + sensitivitet -> output/ranking.csv m.fl.
make report    # output/map.html og output/rapport.md
make all       # data + score + report
make test      # pytest
```
API-svar caches i `data/cache/`, så reruns er raske. Slett cachen for å hente på nytt.

## Justere uten å røre kode
- `config/weights.yaml`: harde filtre, vekter, tre profiler, variabler per kategori, normalisering, sensitivitetsparametre.
- `config/hyttefelt.yaml`: hyttefelt/knutepunkt som egne rader.
- `config/venner.csv`: `kommune,antall_venner_med_hytte` – inngår i kategorien Sosialt når fylt ut.
- `data/raw/finn_manual.csv` (valgfri): `kommune,pris_per_m2_nok` – kun vist i datatabellen.

## Resultater
- `output/rapport.md` – topp 10, begrunnelse, profiler, sensitivitet, forbehold, neste steg
- `output/ranking.csv`, `output/ranking_profiler.csv`, `output/sensitivity.csv`
- `output/map.html` – Leaflet-kart (farge = score, popup = alle variabler, grå = filtrert bort)
- `data/processed/areas.csv` – én rad per område med alle variabler; `variables.csv` – enhet, kilde og dato per variabel

## Struktur
```
src/hytte_finder/  candidates · ssb · geo · snow · osm · rando · terrain · scoring · mapview · report · cli
tests/             normalisering, scoring, filtre, sensitivitet, hjelpefunksjoner
docs/              PLAN.md, ASSUMPTIONS.md
data/SOURCES.md    kilder, lisenser, hentedato, utilgjengelige kilder
```

## Datakilder og lisenser
SSB (NLOD 2.0), Kartverket (CC BY 4.0), NVE/MET Klima i Norge (åpne data), NVE skredkart, OpenStreetMap (ODbL), OSRM-demoserver. Detaljer i `data/SOURCES.md`. Kartdata © OpenStreetMap-bidragsytere.

## Kjente svakheter
- SSB gir kun **snittpris** (ikke median) og ingen ny/brukt-splitt; priser er kommunenivå og kan være svært usikre ved få salg.
- Snødata er modellert (1 km); snødybde >30 cm og framskrivning 2031–2060 var utilgjengelig (framskrivning 2041–2070 brukes).
- OSRM demo-server: kjøretid uten trafikk/føre; vinter er kun et påslag.
- OSM-dekning varierer; åpningstider mangler ofte. 50 m DTM undervurderer helning. Skredaktsomhet er kontekst, ikke sikkerhetsvurdering.
- Mobildekning/fiber, eierbosted, Frost-stasjonsdata og Finn-priser er ikke med.
- Kommune-rader plasseres i høydebånd-tyngdepunkt, ikke i faktiske hyttefelt.
