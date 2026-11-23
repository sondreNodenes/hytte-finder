# Funn og nøkler (2026-11-23)

Automatisk generert av `make report` fra `output/ranking.csv`. Tall er fra siste kjøring; se `output/rapport.md` for utfyllende rapport og forbehold.

## Funn

- **Topp 3:** 1. Djupsjølia (68.2), 2. Miljoseter (64.7), 3. Kvernomsætra (64.4).
- **Robusthet:** 3 områder er topp 5 i ≥ 50 % av 1000 tilfeldige vektsett: Djupsjølia, Kvernomsætra, Svarthaugen.
- **Filtre:** 551 av 656 kandidater falt ut. 455 på kjøretid (> 165 min), 52 på pris.
- **Mest snø:** **Kuåsen** (181 dager); høyest beliggenhet: **Djupedal** (945 moh).
- **Billigst (brukt pris):** **Kvernomsætra** (1 174 180 kr); dyrest: **Sjusjøen** (5 600 000 kr).
- **Kvadratpris (Finn/manuell median):** lavest **Busufjellet** (23 148 kr/m²); høyest **Sjusjøen** (62 963 kr/m²). 1 felt har egne feltannonser, 64 bruker kommune-median (grovere, delt av alle felt i kommunen).
- **Mest innsjøvann (fiske-proxy):** **Myggbukta** (391.1 km² innen 10 km).
- **Mest elgfelling per areal:** **Budor** (34.0 elg/100 km²) (kommunenivå).
- **Beste verdi (lavest pris per snøpoeng):** **Svartsætra** (2 022 555 kr/poeng).
- **Mest løyper:** **Huken** (433 km innen 10 km).
- **Bratteste turterreng (25–40°):** **Folalii** (0.125 av arealet) – 50 m DTM undervurderer helning.
- **Kjøretid:** **Kjerringknatten** (73 min) er nærmest; **Slokoseter** (165 min) lengst blant rangerte.
- **Praktisk:** 76 av 105 områder har > 5 km til dagligvare (Miljoseter, Kvernomsætra, Busufjellet, Høgkorset, Dyrbeintjernshøgda, Rugland seter…); median avstand til Vinmonopol er 15 km.
- **DNT-ruter:** 104 av 105 områder har DNT-merkede ruter innen 15 km i OSM.
- **Antall felt:** 105 rangerte hyttefelt i 23 kommuner; største: Svarthaugen (1938 hytter), Sjusjøen (1588 hytter), Djupsjølia (1169 hytter).
- **Usikre priser:** 0 av 105 har < 15 salg siste år.
- **Helt tomme nøkler:** `jaktrett_tilgang`, `fiskekort_tilgang`, `friends_cabins`, `owner_oslo_akershus_share`, `Sosialt` (se data/SOURCES.md for hvorfor).

## Nøkler (alle kolonner i `output/ranking.csv`)

`Dekning` = andel rangerte områder med verdi. Kilder/lisenser: `data/SOURCES.md`.

| Nøkkel | Kategori | Enhet | Beskrivelse | Kilde | Dekning |
|---|---|---|---|---|---|
| `id` | Identitet | - | Unik id (k<kommunenr> eller h-<navn>) | avledet/pipeline | 100% |
| `type` | Identitet | - | alltid hyttefelt (klynge) | avledet/pipeline | 100% |
| `kommunenr` | Identitet | - | SSB/Geonorge kommunenummer (2024-inndeling) | avledet/pipeline | 100% |
| `kommune` | Identitet | - | Kommunenavn | avledet/pipeline | 100% |
| `kommune_area_km2` | Identitet | km² | Kommunens areal | Geonorge kommuneinfo, avledet | 100% |
| `lat` | Posisjon | grader | Breddegrad (kommune: snappet til vei) | avledet/pipeline | 100% |
| `lon` | Posisjon | grader | Lengdegrad | avledet/pipeline | 100% |
| `n_cabins` | Identitet | antall | Antall hytter i klyngen (DBSCAN) | OpenStreetMap via Overpass API, ODbL (building=cabin|hut) | 100% |
| `cluster_radius_km` | Identitet | km | Største avstand fra klyngens sentrum til en hytte | Avledet | 100% |
| `mountain_cabins` | Identitet | antall | Fritidsbygg over 600 moh i kommunen (SSB 12511) | avledet/pipeline | 100% |
| `air_km` | Kjøretid | km | Luftlinje fra Holmenkollen til kommunepunkt/hyttefelt | avledet/pipeline | 100% |
| `navn` | Identitet | - | Områdenavn | avledet/pipeline | 100% |
| `navn_kilde` | Identitet | - | Hvor navnet kommer fra: seed, stedsnavn eller fallback | avledet/pipeline | 100% |
| `drive_min` | Kjøretid | min | Kjøretid bil fra Holmenkollen til nærmeste vei ved området (sommer, uten trafikk) | OSRM (router.project-osrm.org), data © OSM/ODbL | 100% |
| `drive_km` | Kjøretid | km | Kjørelengde (OSRM) | avledet/pipeline | 100% |
| `snap_m` | Kjøretid | m | Avstand fra punktet til nærmeste vei (OSRM-snap) | avledet/pipeline | 100% |
| `drive_min_winter` | Kjøretid | min | Anslag vinterkjøretid; IKKE målt | Avledet: drive_min × vinterfaktor (config) | 100% |
| `elevation_m` | Snø | moh | Høyde over havet ved punktet | Kartverket høydedata-API (fallback Open-Meteo/Copernicus DEM) | 100% |
| `elevation_source` | Snø | - | Kilde for høyde (Kartverket eller fallback) | avledet/pipeline | 100% |
| `loc_source` | Posisjon | - | Hvordan posisjonen ble funnet | avledet/pipeline | 100% |
| `sales_pooled` | Verdi | antall | Antall salg i kommunen, sammenslått | SSB (data.ssb.no), lisens NLOD 2.0 tabell 11694 | 100% |
| `sales_last_year` | Verdi | antall | Antall salg siste år; <15 => usikkert | SSB (data.ssb.no), lisens NLOD 2.0 tabell 11694 | 100% |
| `avg_price_nok` | Verdi | NOK | Snittpris fritidseiendom med bygning i fritt salg, kommune, sammenslått over price_years. IKKE median | SSB (data.ssb.no), lisens NLOD 2.0 tabell 11694 | 100% |
| `tax_cabins_total_1000` | Økonomi | 1000 NOK | Innbetalt eiendomsskatt fra fritidsboliger i kommunen | SSB (data.ssb.no), lisens NLOD 2.0 tabell 14674 (KOSTRA) | 100% |
| `tax_exempt_cabins` | Økonomi | 1/0 | Fritak for fritidseiendom (1=ja) | SSB (data.ssb.no), lisens NLOD 2.0 tabell 14674 (KOSTRA) | 100% |
| `tax_has` | Økonomi | 1/0 | Kommunen har eiendomsskatt | avledet/pipeline | 100% |
| `tax_rate_permille` | Økonomi | ‰ | Generell eiendomsskattesats (kommune) | SSB (data.ssb.no), lisens NLOD 2.0 tabell 14674 (KOSTRA) | 100% |
| `tax_rate_residential_permille` | Økonomi | ‰ | Differensiert sats bolig/fritid | avledet/pipeline | 78% |
| `villrein_cabins` | Regler | antall | Fritidsbygg i nasjonalt villreinområde i kommunen (regelverk kan påvirke bruk/bygging) | SSB (data.ssb.no), lisens NLOD 2.0 tabell 12761 | 100% |
| `villrein_areas` | Regler | - | Nasjonale villreinområder med fritidsbygg i kommunen | avledet/pipeline | 22% |
| `elg_felt_snitt` | Jakt | dyr/år | Felte elg i kommunen, snitt over config.hunting_seasons | SSB (data.ssb.no), lisens NLOD 2.0 tabell 03432 | 100% |
| `hjort_felt_snitt` | Jakt | dyr/år | Felte hjort i kommunen, snitt over sesongene | SSB (data.ssb.no), lisens NLOD 2.0 tabell 03434 | 100% |
| `jakt_elg_per_100km2` | Jakt | dyr/100 km² | Felt elg per 100 km² kommuneareal (inkl. ikke-jaktbart areal) | Avledet | 100% |
| `jakt_hjort_per_100km2` | Jakt | dyr/100 km² | Felt hjort per 100 km² kommuneareal | Avledet | 100% |
| `jaktrett_tilgang` | Jakt | 0–2 | Tilgang til jaktrett/jaktkort (0 ingen, 1 mulig, 2 god). NaN hvis ikke fylt | config/jakt_fiske.csv (manuell) | 0% |
| `fiskekort_tilgang` | Fiske | 0–2 | Tilgang til fiskekort/fiskerett. NaN hvis ikke fylt. Proxy-en måler tilgang til vann, ikke fiskekvalitet | config/jakt_fiske.csv (manuell) | 0% |
| `friends_cabins` | Sosialt | antall | Antall venner med hytte i kommunen | config/venner.csv (manuell) | 0% |
| `owner_oslo_akershus_share` | Sosialt | andel | NaN: ingen åpen kommunetabell funnet | SSB – ikke publisert som kommunetabell | 0% |
| `ski_season_days` | Snø | dager/år | Skisesongens lengde 1991–2020 (dager med snøvannekv. >60 mm ≈ 25 cm), snitt innen radius | NVE/MET Klima i Norge utgave 2025 (thredds.met.no), NLOD 2.0 | 100% |
| `swe_max_mm` | Snø | mm | Maksimal årlig snømengde (snøvannekvivalent) 1991–2020, snitt innen radius | NVE/MET Klima i Norge utgave 2025 (thredds.met.no), NLOD 2.0 | 100% |
| `ski_season_change_2041_2070_rcp45` | Snø | dager/år | Endring i skisesong 2041–2070 vs 1991–2020 (RCP4.5, ensemblesnitt) | NVE/MET Klima i Norge utgave 2025 (thredds.met.no), NLOD 2.0 | 100% |
| `ski_season_proj_2041_2070` | Snø | dager/år | Skisesong 1991–2020 + endring (framskrivning) | Avledet | 100% |
| `lake_count_10km` | Fiske | antall | Innsjøer ≥ lake_min_km2 med kant innen 10 km | NVE Innsjødatabase | 100% |
| `lake_area_km2_10km` | Fiske | km² | Samlet areal av disse innsjøene (hele innsjøens areal) | NVE Innsjødatabase | 100% |
| `nearest_lake_km` | Fiske | km | Avstand til nærmeste innsjø (til forenklet kantpunkt) | NVE Innsjødatabase | 100% |
| `largest_lake_name` | Fiske | - | Største innsjø innen 10 km | NVE Innsjødatabase | 100% |
| `largest_lake_km2` | Annet | - | (se kode) | avledet/pipeline | 100% |
| `osm_ok` | Kvalitet | bool | Overpass-punktspørring lyktes | avledet/pipeline | 100% |
| `eat_5km` | Praktisk | antall | Antall pub/bar/kafé/restaurant innen 5 km | OpenStreetMap via Overpass API, ODbL | 100% |
| `eat_15km` | Praktisk | antall | … innen 15 km | OpenStreetMap via Overpass API, ODbL | 100% |
| `gathering_5km` | Praktisk | antall | Samlingssteder (pub/bar/kafé) innen 5 km | OpenStreetMap via Overpass API, ODbL | 100% |
| `gathering_15km` | Praktisk | antall | Samlingssteder (pub/bar/kafé) innen 15 km | avledet/pipeline | 100% |
| `ev_5km` | Praktisk | antall | Ladestasjoner innen 5 km | avledet/pipeline | 100% |
| `ev_15km` | Annet | - | (se kode) | avledet/pipeline | 100% |
| `nearest_eat_km` | Praktisk | km | Avstand til nærmeste pub/bar/kafé/restaurant | OpenStreetMap via Overpass API, ODbL | 100% |
| `nearest_gathering_km` | Praktisk | km | Avstand til nærmeste pub/bar/kafé | avledet/pipeline | 100% |
| `nearest_grocery_km` | Praktisk | km | Avstand til nærmeste dagligvare (supermarket/convenience) | OpenStreetMap via Overpass API, ODbL | 100% |
| `nearest_vinmonopol_km` | Praktisk | km | Avstand til nærmeste Vinmonopol | OpenStreetMap via Overpass API, ODbL | 100% |
| `nearest_pharmacy_km` | Praktisk | km | Avstand til nærmeste apotek | OpenStreetMap via Overpass API, ODbL | 100% |
| `nearest_doctor_km` | Praktisk | km | Avstand til legekontor/klinikk/sykehus | OpenStreetMap via Overpass API, ODbL | 100% |
| `nearest_fuel_km` | Praktisk | km | Avstand til nærmeste bensinstasjon | OpenStreetMap via Overpass API, ODbL | 100% |
| `nearest_ev_km` | Praktisk | km | Avstand til nærmeste elbil-lading | OpenStreetMap via Overpass API, ODbL | 100% |
| `nearest_alpine_km` | Praktisk | km | Avstand til alpinanlegg (winter_sports/aerialway/downhill) | OpenStreetMap via Overpass API, ODbL | 100% |
| `nearest_main_road_km` | Praktisk | km | Avstand til nærmeste trunk/primary/secondary vei (typisk riks-/fylkesvei) | OpenStreetMap via Overpass API, ODbL | 100% |
| `grocery_5km` | Praktisk | antall | Dagligvarebutikker innen 5 km | avledet/pipeline | 100% |
| `ev_charging_15km` | Praktisk | antall | Ladestasjoner innen 15 km | OpenStreetMap via Overpass API, ODbL | 100% |
| `nearest_grocery_name` | Praktisk | - | Navn på nærmeste dagligvare | avledet/pipeline | 93% |
| `nearest_grocery_weekend_open` | Praktisk | bool | Nærmeste dagligvare har helgeåpent iflg. opening_hours (NaN = ukjent) | OpenStreetMap via Overpass API, ODbL | 78% |
| `eat_names` | Praktisk | - | Navn på spisesteder innen 5 km | avledet/pipeline | 54% |
| `osm_lines_ok` | Kvalitet | bool | Overpass løype-/rutespørring lyktes | avledet/pipeline | 100% |
| `nordic_km_10km` | Rando | km | Preparerte langrennsløyper (piste:type=nordic) innen 10 km | OpenStreetMap via Overpass API, ODbL | 100% |
| `nordic_nearest_km` | Rando | km | Avstand til nærmeste preparerte langrennsløype | avledet/pipeline | 100% |
| `nordic_direct_access` | Rando | bool | Løype ≤1 km fra punktet | OpenStreetMap via Overpass API, ODbL | 100% |
| `dnt_routes_km_15km` | Rando | km | DNT-merkede turruter (hiking-relasjoner) innen 15 km | OpenStreetMap via Overpass API, ODbL | 100% |
| `dnt_routes_n` | Rando | antall | Antall DNT-ruter (relasjoner) innen 15 km | avledet/pipeline | 100% |
| `winter_routes_km_15km` | Rando | km | Vinterruter (route=ski/skitour, piste:type=skitour) innen 15 km | OpenStreetMap via Overpass API, ODbL | 100% |
| `marked_routes_km_15km` | Rando | km | DNT + vinterruter | OpenStreetMap via Overpass API, ODbL | 100% |
| `slope_25_40_share` | Rando | andel | Andel av areal innen 10 km med helning 25–40° (50 m DTM jevner ut helning) | Kartverket DTM (WCS) 50 m, avledet | 100% |
| `relief_to_1000m_peak_m` | Rando | m | Høydeforskjell til nærmeste topp ≥1000 moh innen 15 km (0 hvis ingen) | Kartverket DTM, avledet | 100% |
| `dist_to_1000m_peak_km` | Rando | km | Avstand til nærmeste topp ≥1000 moh | Kartverket DTM, avledet | 67% |
| `avalanche_zone_share_of_steep` | Rando | andel | Andel av 25–40°-terrenget i aktsomhetsområde. KONTEKST, ikke sikkerhetsvurdering | NVE Snøskred aktsomhetsområder (kart.nve.no), avledet | 100% |
| `terrain_elev_p90_m` | Rando | moh | 90-persentil av høyde innen 10 km | avledet/pipeline | 100% |
| `filter_reason` | Filter | - | Hvorfor området falt ut (tom for rangerte) | avledet/pipeline | 0% |
| `passes` | Filter | bool | Besto harde filtre | avledet/pipeline | 100% |
| `usikker` | Filter | bool | Færre enn 15 salg i kommunen siste år | avledet/pipeline | 100% |
| `finn_n_ads` | Verdi | antall | Antall annonser brukt (kun hytter hvis sted inneholder feltnavn; side 1 av søket) | Finn.no (engangsuttrekk) + data/raw/finn_manual.csv | 62% |
| `finn_median_price_nok` | Verdi | NOK | Median prisantydning | Finn.no / manuell | 62% |
| `finn_median_price_per_m2` | Verdi | NOK/m² | Median prisantydning per m² BRA/areal oppgitt i annonse | Finn.no / manuell | 62% |
| `finn_median_area_m2` | Verdi | m² | Median areal | Finn.no / manuell | 62% |
| `finn_level` | Annet | - | (se kode) | avledet/pipeline | 62% |
| `price_source` | Verdi | - | Hvilken pris som brukes | Avledet | 100% |
| `price_used_nok` | Verdi | NOK | Finn-median hvis ≥ finn_min_ads annonser, ellers SSB kommunesnitt | Avledet | 100% |
| `price_per_m2_used` | Verdi | NOK/m² | Finn-median kr/m² (kun når nok annonser) | Avledet | 62% |
| `finn_tynt` | Verdi | bool | 1–(min−1) annonser: Finn-pris brukes ikke | Avledet | 100% |
| `over_budsjett` | Annet | - | (se kode) | avledet/pipeline | 100% |
| `Snø` | Score | 0–1 | Kategoriscore Snø (rangpersentil, vektet snitt av variabler) | avledet/pipeline | 100% |
| `value_price_per_snow` | Verdi | NOK/poeng | Snittpris / snøscore (0–1, gulv i config) | Avledet | 100% |
| `trail_offer_km` | Verdi | km | Løype-km (10 km) + merkede ruter-km (15 km) | avledet/pipeline | 100% |
| `value_price_per_trail` | Verdi | NOK/km | Snittpris / (løype-km 10 km + merkede ruter-km 15 km) | Avledet | 100% |
| `Verdi` | Score | 0–1 | Kategoriscore Verdi (rangpersentil, vektet snitt av variabler) | avledet/pipeline | 100% |
| `Rando` | Score | 0–1 | Kategoriscore Rando (rangpersentil, vektet snitt av variabler) | avledet/pipeline | 100% |
| `Praktisk` | Score | 0–1 | Kategoriscore Praktisk (rangpersentil, vektet snitt av variabler) | avledet/pipeline | 100% |
| `Kjøretid` | Score | 0–1 | Kategoriscore Kjøretid (rangpersentil, vektet snitt av variabler) | avledet/pipeline | 100% |
| `Jakt` | Score | 0–1 | Kategoriscore Jakt (rangpersentil, vektet snitt av variabler) | avledet/pipeline | 100% |
| `Fiske` | Score | 0–1 | Kategoriscore Fiske (rangpersentil, vektet snitt av variabler) | avledet/pipeline | 100% |
| `Sosialt` | Score | 0–1 | Kategoriscore Sosialt (rangpersentil, vektet snitt av variabler) | avledet/pipeline | 0% |
| `score` | Score | 0–100 | Totalscore, standardvekter | avledet/pipeline | 100% |
| `rank` | Score | # | Rang etter totalscore | avledet/pipeline | 100% |
| `nominal_snow_days_30cm_1971_2000` | Snø | dager | NaN: datasettet har ingen fungerende nedlastingslenke | NVE – utilgjengelig (tom THREDDS-katalog) | 0 % (ikke i data) |
| `mobile_coverage` | Praktisk | - | NaN: ikke åpen API-tilgang implementert | Nkom – ikke hentet | 0 % (ikke i data) |
| `fiber_broadband` | Praktisk | - | NaN: ikke åpen API-tilgang implementert | Nkom – ikke hentet | 0 % (ikke i data) |
