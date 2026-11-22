"""Metadata: hver variabel med enhet, kilde, hentedato (dato settes ved kjøring) og beskrivelse."""
from __future__ import annotations

SSB = "SSB (data.ssb.no), lisens NLOD 2.0"
OSM = "OpenStreetMap via Overpass API, ODbL"
NVE_SNOW = "NVE/MET Klima i Norge utgave 2025 (thredds.met.no), NLOD 2.0"

VARIABLES = [
    # id, kategori, enhet, kilde, beskrivelse
    ("drive_min", "Kjøretid", "min", "OSRM (router.project-osrm.org), data © OSM/ODbL", "Kjøretid bil fra Holmenkollen til nærmeste vei ved området (sommer, uten trafikk)"),
    ("drive_min_winter", "Kjøretid", "min", "Avledet: drive_min × vinterfaktor (config)", "Anslag vinterkjøretid; IKKE målt"),
    ("elevation_m", "Snø", "moh", "Kartverket høydedata-API (fallback Open-Meteo/Copernicus DEM)", "Høyde over havet ved punktet"),
    ("ski_season_days", "Snø", "dager/år", NVE_SNOW, "Skisesongens lengde 1991–2020 (dager med snøvannekv. >60 mm ≈ 25 cm), snitt innen radius"),
    ("swe_max_mm", "Snø", "mm", NVE_SNOW, "Maksimal årlig snømengde (snøvannekvivalent) 1991–2020, snitt innen radius"),
    ("ski_season_change_2041_2070_rcp45", "Snø", "dager/år", NVE_SNOW, "Endring i skisesong 2041–2070 vs 1991–2020 (RCP4.5, ensemblesnitt)"),
    ("ski_season_proj_2041_2070", "Snø", "dager/år", "Avledet", "Skisesong 1991–2020 + endring (framskrivning)"),
    ("avg_price_nok", "Verdi", "NOK", SSB + " tabell 11694", "Snittpris fritidseiendom med bygning i fritt salg, kommune, sammenslått over price_years. IKKE median"),
    ("sales_pooled", "Verdi", "antall", SSB + " tabell 11694", "Antall salg i kommunen, sammenslått"),
    ("sales_last_year", "Verdi", "antall", SSB + " tabell 11694", "Antall salg siste år; <15 => usikkert"),
    ("value_price_per_snow", "Verdi", "NOK/poeng", "Avledet", "Snittpris / snøscore (0–1, gulv i config)"),
    ("value_price_per_trail", "Verdi", "NOK/km", "Avledet", "Snittpris / (løype-km 10 km + merkede ruter-km 15 km)"),
    ("tax_rate_permille", "Økonomi", "‰", SSB + " tabell 14674 (KOSTRA)", "Generell eiendomsskattesats (kommune)"),
    ("tax_exempt_cabins", "Økonomi", "1/0", SSB + " tabell 14674 (KOSTRA)", "Fritak for fritidseiendom (1=ja)"),
    ("tax_cabins_total_1000", "Økonomi", "1000 NOK", SSB + " tabell 14674 (KOSTRA)", "Innbetalt eiendomsskatt fra fritidsboliger i kommunen"),
    ("villrein_cabins", "Regler", "antall", SSB + " tabell 12761", "Fritidsbygg i nasjonalt villreinområde i kommunen (regelverk kan påvirke bruk/bygging)"),
    ("nearest_eat_km", "Praktisk", "km", OSM, "Avstand til nærmeste pub/bar/kafé/restaurant"),
    ("eat_5km", "Praktisk", "antall", OSM, "Antall pub/bar/kafé/restaurant innen 5 km"),
    ("eat_15km", "Praktisk", "antall", OSM, "… innen 15 km"),
    ("gathering_5km", "Praktisk", "antall", OSM, "Samlingssteder (pub/bar/kafé) innen 5 km"),
    ("nearest_grocery_km", "Praktisk", "km", OSM, "Avstand til nærmeste dagligvare (supermarket/convenience)"),
    ("nearest_grocery_weekend_open", "Praktisk", "bool", OSM, "Nærmeste dagligvare har helgeåpent iflg. opening_hours (NaN = ukjent)"),
    ("nearest_vinmonopol_km", "Praktisk", "km", OSM, "Avstand til nærmeste Vinmonopol"),
    ("nearest_pharmacy_km", "Praktisk", "km", OSM, "Avstand til nærmeste apotek"),
    ("nearest_doctor_km", "Praktisk", "km", OSM, "Avstand til legekontor/klinikk/sykehus"),
    ("nearest_fuel_km", "Praktisk", "km", OSM, "Avstand til nærmeste bensinstasjon"),
    ("ev_charging_15km", "Praktisk", "antall", OSM, "Ladestasjoner innen 15 km"),
    ("nearest_ev_km", "Praktisk", "km", OSM, "Avstand til nærmeste elbil-lading"),
    ("nearest_alpine_km", "Praktisk", "km", OSM, "Avstand til alpinanlegg (winter_sports/aerialway/downhill)"),
    ("nearest_main_road_km", "Praktisk", "km", OSM, "Avstand til nærmeste trunk/primary/secondary vei (typisk riks-/fylkesvei)"),
    ("nordic_km_10km", "Rando", "km", OSM, "Preparerte langrennsløyper (piste:type=nordic) innen 10 km"),
    ("nordic_direct_access", "Rando", "bool", OSM, "Løype ≤1 km fra punktet"),
    ("dnt_routes_km_15km", "Rando", "km", OSM, "DNT-merkede turruter (hiking-relasjoner) innen 15 km"),
    ("winter_routes_km_15km", "Rando", "km", OSM, "Vinterruter (route=ski/skitour, piste:type=skitour) innen 15 km"),
    ("marked_routes_km_15km", "Rando", "km", OSM, "DNT + vinterruter"),
    ("slope_25_40_share", "Rando", "andel", "Kartverket DTM (WCS) 50 m, avledet", "Andel av areal innen 10 km med helning 25–40° (50 m DTM jevner ut helning)"),
    ("relief_to_1000m_peak_m", "Rando", "m", "Kartverket DTM, avledet", "Høydeforskjell til nærmeste topp ≥1000 moh innen 15 km (0 hvis ingen)"),
    ("dist_to_1000m_peak_km", "Rando", "km", "Kartverket DTM, avledet", "Avstand til nærmeste topp ≥1000 moh"),
    ("avalanche_zone_share_of_steep", "Rando", "andel", "NVE Snøskred aktsomhetsområder (kart.nve.no), avledet", "Andel av 25–40°-terrenget i aktsomhetsområde. KONTEKST, ikke sikkerhetsvurdering"),
    ("friends_cabins", "Sosialt", "antall", "config/venner.csv (manuell)", "Antall venner med hytte i kommunen"),
    ("owner_oslo_akershus_share", "Sosialt", "andel", "SSB – ikke publisert som kommunetabell", "NaN: ingen åpen kommunetabell funnet"),
    ("nominal_snow_days_30cm_1971_2000", "Snø", "dager", "NVE – utilgjengelig (tom THREDDS-katalog)", "NaN: datasettet har ingen fungerende nedlastingslenke"),
    ("mobile_coverage", "Praktisk", "-", "Nkom – ikke hentet", "NaN: ikke åpen API-tilgang implementert"),
    ("fiber_broadband", "Praktisk", "-", "Nkom – ikke hentet", "NaN: ikke åpen API-tilgang implementert"),
]
