# hytte-finder

![Python](https://img.shields.io/badge/python-3.11%2B-blue?logo=python&logoColor=white)
![Tester](https://img.shields.io/badge/pytest-17%20passed-brightgreen?logo=pytest&logoColor=white)
![Lisens](https://img.shields.io/badge/kode-MIT-yellow)
![Data](https://img.shields.io/badge/data-SSB%20%C2%B7%20Kartverket%20%C2%B7%20NVE%2FMET%20%C2%B7%20OSM-informational)
![Region](https://img.shields.io/badge/region-Norge-red)
![Status](https://img.shields.io/badge/status-beslutningsst%C3%B8tte-orange)
![Kart](https://img.shields.io/badge/kart-Leaflet%2Ffolium-green)

Datadrevet rangering av norske **hyttefelt** for hyttekjøp: snøsikkerhet, pris (inkl. kr/m² fra annonser) mot hva man får, rando, jakt og fiske og praktiske forhold. Hyttefeltene er funnet automatisk ved å klynge OSM-hytter, så store kommuner deles geografisk. Utgangspunkt, maks kjøretid, budsjett og vekter er konfigurerbare i `config/weights.yaml`.

> Beslutningsstøtte, ikke finansiell rådgivning. Pris og kjøretid må verifiseres mot aktuelle annonser.

## Kjøring

Krever Python ≥ 3.11 og [`uv`](https://docs.astral.sh/uv/) (alternativt `pip install -r requirements.txt`).

```bash
make setup     # lager .venv og installerer avhengigheter
cp .env.example .env   # fyll inn CONTACT_EMAIL (brukes i User-Agent)
make data      # henter og renser alle data  -> data/processed/areas.csv   (første kjøring tar ~1 time pga. Overpass)
make score     # filtre + score + sensitivitet -> output/ranking.csv m.fl.
make report    # output/map.html og output/rapport.md
make finn      # VALGFRITT engangs-uttrekk av Finn-annonser for kr/m² (se under)
make all       # data + score + report  (Finn er ikke med)
make test      # pytest
```
API-svar caches i `data/cache/`, så reruns er raske. Slett cachen for å hente på nytt.

## Justere uten å røre kode
- `config/weights.yaml`: harde filtre, vekter, tre profiler, variabler per kategori, normalisering, sensitivitetsparametre.
- `config/hyttefelt.yaml`: hyttefelt/knutepunkt som egne rader.
- `config/venner.csv`: `kommune,antall_venner_med_hytte` – inngår i kategorien Sosialt når fylt ut.
- `config/jakt_fiske.csv`: `nokkel,jaktrett_tilgang,fiskekort_tilgang,merknad` (nokkel = felt-id, feltnavn eller kommune; 0–2) – manuell vurdering som inngår i Jakt/Fiske.
- `data/raw/finn_manual.csv` (valgfri): `nokkel,pris_nok,bra_m2` – egne annonser som legges til Finn-medianen.

## Finn-priser (valgfritt, engangs)
`make finn` henter side 1 av Finns hytteannonser for inntil 30 hyttefelt (rolig tempo, cachet, robots.txt leses maskinelt, stopper ved enhver blokkering). Rå annonsedata ligger i `data/raw/finn_listings.csv` (ikke i git); bare medianer (kr, kr/m²) brukes videre. **Finn.no krever skriftlig tillatelse til automatisert bruk i sine vilkår;** dette er brukerens eget valg og ansvar, bruk det sparsomt og ikke publiser rådata. Annonsepriser er prisantydning, ikke solgt pris.

## Resultater
- `output/rapport.md` – topp 10, begrunnelse, profiler, sensitivitet, forbehold, neste steg
- `output/ranking.csv`, `output/ranking_profiler.csv`, `output/sensitivity.csv`
- `output/dashboard.html` – enkelt dashboard: sorterbar rangering, kategoriscorer, sensitivitet (åpnes direkte i nettleser)
- `docs/FINDINGS.md` – funn og forklaring av alle nøkler/kolonner
- `output/map.html` – Leaflet-kart (farge = score, popup = alle variabler, grå = filtrert bort)
- `data/processed/areas.csv` – én rad per område med alle variabler; `variables.csv` – enhet, kilde og dato per variabel

## Struktur
```
src/hytte_finder/  candidates · clusters · ssb · geo · snow · osm · rando · fiske · finn · terrain · scoring · mapview · dashboard · findings · report · cli
tests/             normalisering, scoring, filtre, sensitivitet, hjelpefunksjoner
docs/              PLAN.md, ASSUMPTIONS.md
data/SOURCES.md    kilder, lisenser, hentedato, utilgjengelige kilder
```

## Datakilder og lisenser
Koden er MIT-lisensiert (LICENSE). Dataene har egne lisenser.
SSB (NLOD 2.0), Kartverket (CC BY 4.0), NVE/MET Klima i Norge (åpne data), NVE skredkart, OpenStreetMap (ODbL), OSRM-demoserver. Detaljer i `data/SOURCES.md`. Kartdata © OpenStreetMap-bidragsytere.

## Kjente svakheter
- SSB gir kun **snittpris** (ikke median) på kommunenivå. Finn-medianer (kr/m²) bygger på ett uttrekk av side 1 og prisantydning.
- Jakt = felt elg/hjort per kommune (SSB); fiske = innsjøareal (NVE). Ingen data på rype/småvilt, jaktkort, fiskekort eller fiskekvalitet.
- Snødata er modellert (1 km); snødybde >30 cm og framskrivning 2031–2060 var utilgjengelig (framskrivning 2041–2070 brukes).
- OSRM demo-server: kjøretid uten trafikk/føre; vinter er kun et påslag.
- OSM-dekning varierer; åpningstider mangler ofte. 50 m DTM undervurderer helning. Skredaktsomhet er kontekst, ikke sikkerhetsvurdering.
- Mobildekning/fiber, eierbosted, Frost-stasjonsdata og Finn-priser er ikke med.
- Hyttefelt er DBSCAN-klynger av OSM-hytter (`building=cabin|hut`); resultat avhenger av OSM-dekning og klyngeparametere i config.
