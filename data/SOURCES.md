# Datakilder

Hentedato: se `data/processed/variables.csv` (kolonnen `hentedato`) – dato for siste `make data`. Råfiler ligger i `data/raw/`, API-svar caches i `data/cache/` (ikke i git).

| Kilde | URL | Brukt til | Lisens |
|---|---|---|---|
| SSB 11694 – omsetning og kjøpesum fritidseiendom (K) | https://data.ssb.no/api/v0/no/table/11694 | antall salg, snittpris per kommune 2023–2025 | NLOD 2.0 |
| SSB 12511 – fritidsbygg etter høyde over havet (K) | https://data.ssb.no/api/v0/no/table/12511 | definerer fjellhyttekommuner (≥ 600 moh) | NLOD 2.0 |
| SSB 14674 – KOSTRA eiendomsskatt (K) | https://data.ssb.no/api/v0/no/table/14674 | sats, fritak, skatt fra fritidsboliger | NLOD 2.0 |
| SSB 12761 – fritidsbygg i villreinområder (K) | https://data.ssb.no/api/v0/no/table/12761 | regelverkskontekst (villrein) | NLOD 2.0 |
| Geonorge kommuneinfo | https://ws.geonorge.no/kommuneinfo/v1/ | kommunenavn/-nummer, grenser, bbox | NLOD / CC BY 4.0 |
| Kartverket høydedata (DTM, WCS) | https://wcs.geonorge.no/skwms1/wcs.hoyde-dtm_somlos | terreng (50/500 m) | CC BY 4.0 |
| Kartverket høydedata-API (punkt) | https://ws.geonorge.no/hoydedata/v1/punkt | høyde over havet | CC BY 4.0 |
| NVE/MET Klima i Norge 2025: skisesong 1991–2020 | https://thredds.met.no/thredds/fileServer/KSS/Klima_i_Norge/utgave2025/ReferenceIndices/swe60ge/reference_1991-2020_disthbv_norway_1km_swe60ge.nc | skisesongens lengde | åpne data (NLOD; se Geonorge-metadata) |
| NVE/MET: maks snømengde 1991–2020 | …/ReferenceIndices/swemax/reference_1991-2020_disthbv_norway_1km_swemax.nc | snøvannekvivalent maks | som over |
| NVE/MET: endring skisesong 2041–2070 RCP4.5 | …/ClimateStatistics/diff-swe60ge/ensemble-mean_rcp45_both-bc-estobs_disthbv_norway_1km_diff-swe60ge.nc | framskrivning | som over |
| NVE snøskred aktsomhetsområder | https://kart.nve.no/enterprise/rest/services/SnoskredAktsomhet/MapServer | aktsomhetsandel av turterreng | NLOD |
| OpenStreetMap via Overpass | https://overpass-api.de (speil: maps.mail.ru, kumi.systems) | tilbud, alpin, løyper, ruter | ODbL © OSM-bidragsytere |
| OSM Nominatim | https://nominatim.openstreetmap.org | koordinater for hyttefelt | ODbL |
| OSRM demo-server | https://router.project-osrm.org | kjøretid, snap til vei | data ODbL; demoserver uten garantier |
| Open-Meteo elevation (fallback) | https://api.open-meteo.com/v1/elevation | høyde hvis Kartverket feiler | CC BY 4.0 |

## Forsøkt, men utilgjengelig (NaN)
- **Snødybde > 30 cm 1971–2000 og framskrivning 2031–2060** (data.norge.no / Geonorge uuid 42329031-049b-4817-bc43-ba3e8d1c4809): ingen nedlastingslenke i Geonorge-posten, THREDDS-katalogen `KSS/Klima_i_Norge_2100/utgave2015` er tom (forsøkt 2 ganger).
- **Mobildekning/fiber (Nkom):** ikke implementert (ingen åpen API verifisert).
- **Eierbosted for hytter (SSB):** ingen åpen kommunetabell funnet (søk 2 ganger).
- **Finn.no:** https://www.finn.no/robots.txt forbyr automatisert tilgang uten skriftlig samtykke → ikke hentet. Manuell CSV støttes.
- **MET Frost:** valgfri, krever klient-ID; ikke implementert.
