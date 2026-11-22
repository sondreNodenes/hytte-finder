# Plan: hytte-finder

Mål: datadrevet rangering av norske fjellområder (≤165 min fra Holmenkollen) for hyttekjøp 3,0–3,9 mill.

## Faser (hver fase avsluttes med commit)
0. **Oppsett** – repo, Makefile, pyproject, config, .gitignore, ASSUMPTIONS/SOURCES-skjelett.
1. **Minimal ende-til-ende** – 5 kommuner × 3 variabler (kjøretid via OSRM, høyde, SSB-pris) → scoring → ranking.csv.
2. **Kandidater** – kommuneliste (SSB/Kartverket) + hyttefelt-knutepunkt (OSM/Nominatim), ruting, høyde, filtre.
3. **SSB** – hytteomsetning (median, snitt, antall, ny/brukt), KOSTRA eiendomsskatt, eierbosted (proxy sosialt).
4. **OSM/Overpass** – praktisk (mat, dagligvare, Vinmonopol, apotek, lege, bensin, lading), alpin, løyper, ruter. 5 og 15 km.
5. **Snø** – NVE/MET skisesong, snødybde-dager (hvis nedlastbart), Frost (valgfri).
6. **Rando** – DTM (grov oppløsning) → helning 25–40 %-andel, topp >1000 moh; NVE aktsomhet for skred.
7. **Scoring** – normalisering (percentil), kategoriscorer, vekter, 3 profiler, Dirichlet-sensitivitet (1000).
8. **Output** – ranking.csv, map.html (folium), rapport.md (norsk), README.
9. **Kvalitet** – pytest, `make all` fra rent oppsett, SOURCES.md, ASSUMPTIONS.md.

## Prinsipper
- Ingen oppdiktede tall: manglende = NaN, dokumentert i SOURCES.md.
- Alle API-kall caches (data/cache), pauser, retry/backoff, User-Agent fra .env.
- Hver kilde som feiler to ganger dokumenteres og hoppes over.
