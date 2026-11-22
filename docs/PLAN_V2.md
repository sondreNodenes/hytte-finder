# Plan v2: geografisk oppdeling, jakt og fiske, Finn-priser

Status: **utkast til godkjenning** (ingenting av dette er kodet ennå).

## A. Dele opp store kommuner geografisk (hyttefelt-klynger)

Problem: én kommuneprikk (høydebånd-tyngdepunkt) representerer hele kommunen, og Krødsherad/Norefjell dobbelttelles.

Løsning: finn hyttefelt fra data, ikke fra håndplukk.

1. **Hent hytter:** OSM `building=cabin|hut` (importert fra Matrikkelen; ca. 3 200 i Krødsherad-boksen) som sentroidepunkter, per kandidatkommune. Én Overpass-spørring per kommune, cachet, filtrert mot kommunepolygon (shapely).
2. **Klynge:** DBSCAN på haversine-avstand, `eps` = 1,5 km, `min_samples` = 25 hytter (begge i config). Hver klynge får: antall hytter, sentroide, konveks flate, median-/maks-høyde (DTM).
3. **Navn:** Kartverket Stedsnavn-API (`ws.geonorge.no/stedsnavn/v1/punkt`): nærmeste fjellområde/slette/grend. Overstyring av navn i `config/hyttefelt.yaml` (dagens seeds blir navneoverstyringer).
4. **Tilgang og kjøretid:** snap sentroiden til nærmeste vei (OSRM), kjøretid fra Holmenkollen per klynge. Klynger over 165 min filtreres som før.
5. **Variabler per klynge:** snø (5 km radius rundt klyngen), OSM-praktisk/løyper/ruter og rando-terreng beregnes per klynge, ikke per kommune.
6. **Pris:** SSB gir fortsatt bare kommunenivå. Alle klynger i en kommune deler kommunepris, og dette flagges tydelig (`price_level = kommune`). Mer realistiske priser: se punkt D.
7. **Kommuneradene fjernes** som rangerte rader. Kommunen beholdes som kontekst (pris, skatt, villrein, jakt).
8. **Ytelse:** bulk-henting per kommune (én Overpass-spørring for punkter og én for linjer) og lokal beregning per klynge. Det blir langt raskere enn dagens spørring per punkt (ca. 2 min hver).
9. **Tester:** klyngingen er deterministisk, minstestørrelse overholdes, klynger ligger innen riktig kommune, navn-fallback fungerer.

Forventet resultat: ca. 40–120 klynger. Store kommuner (Hol, Ål, Ringsaker, Trysil, Nore og Uvdal) deles i flere felt, og små kommuner får ett.

## B. Parameter: jakt

Det finnes ingen åpne data på «jaktkvalitet» per hyttefelt. Det vi kan hente ærlig:

| Variabel | Kilde | Nivå |
|---|---|---|
| `jakt_elg_felt_snitt` (3 sesonger) | SSB 03432 «Felte elg» | kommune |
| `jakt_hjort_felt_snitt` (3 sesonger) | SSB 03434 «Felte hjort» | kommune |
| `jakt_elg_tillatt_felt` | SSB 08696 «Tillatt felt elg» | kommune |
| `jakt_per_utmark` (felt per km² utmark/skog) | SSB + Kartverket arealstatistikk (hvis tilgjengelig) | kommune |
| `jaktrett_tilgang` (0–2) | **manuell** `config/jakt_fiske.csv` (fjellstyre/Statskog/Inatur/grunneierlag) | felt/kommune |
| `villrein_cabins` (kontekst, ikke score) | SSB 12761 | kommune |

Kan ikke dekkes åpent: rype og småvilt, jaktkort-tilgang og jaktkvoter per teig. Disse blir NaN eller manuelle.
Ny kategori **Jakt** i scoring (vekt i config, se spørsmål).

## C. Parameter: fiske

Det finnes ingen åpne kommunetall for innlandsfiske. Proxy fra geodata:

| Variabel | Kilde |
|---|---|
| `vann_areal_km2_10km`, `vann_antall_10km` (innsjøer ≥ 0,1 km²) | NVE Innsjødatabase (verifiseres), fallback OSM `natural=water` |
| `storste_innsjo_km2_10km`, `avstand_nærmeste_innsjo_km` | samme |
| `elv_km_10km` (OSM `waterway=river`) | OSM |
| `fiskekort_tilgang` (0–2) | **manuell** `config/jakt_fiske.csv` (Inatur/Statskog/fjellstyre/grunneierlag) |

Beskrivelse i rapporten: dette måler *tilgang til vann*, ikke fiskekvalitet eller bestand. Fiskekort-tilgang må sjekkes manuelt. Ny kategori **Fiske** i scoring.

## D. Finn-priser: scraper kan ikke bygges slik det er bedt om

`https://www.finn.no/robots.txt` sier: *«Crawling FINN.no is prohibited unless you have written permission»*, og vilkårene forbyr roboter/automatiserte tjenester uten eksplisitt samtykke. Opprinnelig oppdrag sa også «respekter robots.txt og vilkår». Jeg bygger derfor **ikke** en scraper uten skriftlig tillatelse. Alternativer:

1. **Be Finn om skriftlig tillatelse/dataavtale** (du eller NTNU kan kontakte dem). Hvis du får det, bygger jeg en høflig klient med rate limit og cache, i en egen modul.
2. **Manuell inntasting med hjelpeverktøy (anbefalt):** `make finn-template` lager `data/raw/finn_manual.csv` per hyttefelt-klynge (kolonner: klynge, pris, bra_m2, byggeår, dato, url). Du taster inn 5–10 aktuelle annonser per felt mens du leser dem. Pipeline regner median pris, m²-pris og «pris per m²» per felt og bruker dem i Verdi-kategorien i stedet for kommunesnitt der det finnes data. Oppføringer med < 5 annonser flagges «tynt».
3. **Andre kilder:** jeg kan først sjekke vilkår og API-er hos andre portaler/statistikkleverandører. Jeg bygger ingenting før vilkårene er lest.

## E. Konfig, output, dokumentasjon

- `config/weights.yaml`: kategoriene Jakt og Fiske, klyngeparametre, nye profiler.
- Rapport, dashboard, kart (klyngeomriss, hyttetetthet) og `FINDINGS.md` oppdateres.
- README og SOURCES.md oppdateres. 
- Tester for nye moduler og eksisterende scoring.

## F. Rekkefølge (commit per steg)

1. Hytteklynger + stedsnavn + tilgang (A1–A4).
2. Variabler per klynge, bulk-Overpass (A5–A8), fjerne kommuneradene.
3. Jakt-variabler (SSB) + manuell fil.
4. Fiske-variabler (vann/elv) + manuell fil.
5. Finn: valgt alternativ fra D.
6. Scoring/vekter/profiler, rapport, dashboard, kart, tester, `make all` fra rent oppsett.
