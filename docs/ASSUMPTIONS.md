# Antakelser og valg (autonom kjøring)

Valg som er tatt uten å spørre. Alle kan endres i `config/weights.yaml` eller koden.

## Kandidater
- **Fjellhyttekommuner** = kommuner innen 200 km luftlinje fra Holmenkollen med ≥ 300 fritidsbygg over 600 moh (SSB 12511, 2025). Dette er en datadrevet avgrensning; den kan ta med randkommuner (Hamar, Gjøvik, Gran …) som scores lavt på snø.
- **Kommunerad-plassering:** Kommunepunktet fra Geonorge ligger ofte i tettstedet. Derfor plasseres hver kommune i tyngdepunktet av arealet i høydebåndet 600–1100 moh (Kartverket DTM 500 m), snappet til nærmeste vei (OSRM). Snap-avstand står i `loc_source`.
- **Hyttefelt** (`config/hyttefelt.yaml`): koordinater fra Nominatim/OSM, sanity-sjekket mot kommunens avgrensningsboks. Seeds som feiler droppes (logges). Lifjell ble droppet fordi OSM-treffet lå utenfor kommunen.
- Gausdal er egen kommune fra 2024 (skilt ut fra Lillehammer); Skeikampen er knyttet til Gausdal.

## Filtre
- **Kjøretid:** OSRM demo-server (bil, ingen trafikk) fra Holmenkollen til nærmeste vei ved området. Vinter = sommer × 1,15 (anslag).
- **Pris:** SSB har *ikke* median eller skille ny/brukt på kommunenivå – kun antall og total kjøpesum (tabell 11694). Vi bruker snittpris slått sammen over 2023–2025 (flere salg → stabilere). Fordi snitt > median, tillates snitt opp til 3,9 mill × 1,30 = 5,07 mill. Ingen nedre grense (billigere er bra).
- **«Usikker»** = færre enn 15 salg *siste år* (2025). Områder uten SSB-salg faller ut («pris mangler»).
- Kommunepris brukes for alle områder i kommunen, også hyttefelt (det finnes ikke feltpriser åpent).

## Variabler
- **Skisesong:** NVE/MET «skisesongens lengde» 1991–2020 (snøvannekvivalent > 60 mm ≈ 25 cm). Radiusgjennomsnitt 5 km, 1x1 km-celler.
- **Snødybde > 30 cm (1971–2000) og framskrivning 2031–2060:** datasettet er registrert hos data.norge.no/Geonorge, men THREDDS-katalogen (`Klima_i_Norge_2100`) er tom og Geonorge-posten har ingen nedlastingslenke (to forsøk). Variabelen er derfor **NaN**. Som erstatning brukes maks snømengde 1991–2020 og endring i skisesong 2041–2070 (RCP4.5, ensemblesnitt) fra utgave 2025.
- **Frost (stasjonsdata):** valgfritt og ikke implementert (krever klient-ID). `FROST_CLIENT_ID` i `.env.example` er reservert.
- **Finn.no:** robots.txt/vilkår forbyr automatisert tilgang uten samtykke → ingen scraping. Støtte for manuell `data/raw/finn_manual.csv` (kolonner `kommune,pris_per_m2_nok`); vises i datatabellen, men inngår ikke i score.
- **Mobildekning/fiber (Nkom):** ingen åpen API-tilgang implementert → NaN.
- **Eierbosted (Oslo/Akershus-andel):** ingen åpen SSB-kommunetabell funnet → NaN. `config/venner.csv` støttes; tom fil = Sosialt-kategorien utelates (vekt omfordeles).
- **Terreng:** 50 m DTM (Kartverket WCS `wcs.hoyde-dtm_somlos`), radius 10 km for helning, 15 km for toppsøk. Helning 25–40° regnes med numpy-gradient. 50 m jevner ut terreng og undervurderer bratthet.
- **«Relief til topp ≥ 1000 moh»:** 0 m hvis ingen topp ≥ 1000 moh innen 15 km (en målt, ikke gjettet, verdi).
- **NVE aktsomhet:** export av lag «PotensieltSkredfareOmr» fra `kart.nve.no/.../SnoskredAktsomhet`; andel av 25–40°-cellene som ligger i aktsomhetsområde. Kun kontekst.
- **OSM-ruter:** DNT = hiking-relasjoner med operatør/nettverk som inneholder «turistforening»/DNT. Vinterruter = `route=ski|skitour` og `piste:type=skitour`. Lengder telles der segmentmidtpunkt ligger innen radius.
- **Eiendomsskatt:** SSB/KOSTRA 14674 (sats, fritak, innbetalt skatt fra fritidsboliger). Ikke med i score (informasjon i tabell/kart). Villrein: SSB 12761 (antall fritidsbygg i villreinområde) som regelverks-kontekst.

## Scoring
- **Normalisering:** rangpersentil (0–1) innen de områdene som passerte filtrene; robust mot uteliggere. Alternativ `minmax` i config.
- Kategori = vektet snitt av tilgjengelige variabler (vekter renormaliseres per område når variabler mangler). Totalscore = vektet sum av kategorier på samme måte; manglende kategori (f.eks. Sosialt) utelates og vektene omfordeles.
- **Verdi:** pris/snøscore (gulv 0,05) og pris/(løype-km + ruter-km, gulv 1 km); begge inverteres.
- **Sensitivitet:** 1000 Dirichlet-trekk med konsentrasjon 50 rundt standardvektene, seed 42.
