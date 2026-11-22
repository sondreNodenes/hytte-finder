# Prompt v2 (til godkjenning – rediger før du sender)

Fortsett på `hytte-finder` (repoet `~/hytte-finder`). Jobb autonomt, ikke still spørsmål, ta rimelige valg og skriv dem i `docs/ASSUMPTIONS.md`. Commit ofte. Følg `docs/PLAN_V2.md`.

## Mål
1. **Del opp store kommuner geografisk**: erstatt kommune-radene med hyttefelt-klynger fra OSM `building=cabin|hut` (DBSCAN, `eps` = [1,5] km, `min_samples` = [25], begge i config). Navngi via Kartverket Stedsnavn, overstyring i `config/hyttefelt.yaml`. Kjøretid, snø, OSM-praktisk, løyper og rando beregnes per klynge. Kommune beholdes som kontekst (pris, skatt, villrein). Bulk-hent Overpass per kommune og regn lokalt per klynge.
2. **Ny kategori Jakt**: SSB 03432 (elg), 03434 (hjort), 08696 (tillatt felt elg), snitt siste 3 sesonger, kommunenivå. Manuell kolonne `jaktrett_tilgang` (0–2) i `config/jakt_fiske.csv`. Aldri gjett: manglende = NaN. Rype/småvilt dokumenteres som utilgjengelig.
3. **Ny kategori Fiske**: innsjøareal og antall innen 10 km (NVE Innsjødatabase, fallback OSM), nærmeste innsjø, elv-km (OSM), manuell `fiskekort_tilgang` (0–2). Rapporter tydelig at dette er tilgang til vann, ikke fiskekvalitet.
4. **Finn-priser**: [VELG ÉN]
   - [ ] A: bygg IKKE scraper. Lag `make finn-template` og import av manuell `data/raw/finn_manual.csv` (klynge, pris, bra_m2, byggeår, dato, url). Bruk median pris og m²-pris per felt i Verdi når ≥ 5 annonser, ellers kommunesnitt og flagg «tynt».
   - [ ] B: jeg har skriftlig tillatelse fra Finn (legg ved referanse) → bygg en høflig klient i egen modul med rate limit, cache og robots-respekt.
   - [ ] C: sjekk først vilkår hos andre kilder og rapporter, bygg ingenting.
5. **Vekter** (summerer til 1, justerbare i `config/weights.yaml`): Snø [0,25], Verdi [0,20], Rando [0,15], Praktisk [0,13], Kjøretid [0,10], Jakt [0,07], Fiske [0,07], Sosialt [0,03]. Oppdater de tre profilene (legg Jakt/Fiske tungt i en ny profil «jakt_fiske»).
6. Oppdater sensitivitetsanalysen (1000 Dirichlet-trekk), rapport, dashboard, kart (vis klyngeomriss), `docs/FINDINGS.md`, README, `data/SOURCES.md` og tester. Kjør `make all` fra rent oppsett.

## Kvalitetskrav
Som i forrige oppdrag: ingen oppdiktede tall, alle API-kall caches og er snille mot gratis tjenester, kilde og dato per variabel, ærlige forbehold. Ingen automatisert tilgang til tjenester hvis robots.txt/vilkår forbyr det.
