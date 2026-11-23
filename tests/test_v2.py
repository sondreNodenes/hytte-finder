import numpy as np
import pandas as pd

from hytte_finder import clusters, finn, osm

ART = """<article class="sf-search-ad"><a href="/realestate/leisuresale/ad.html?finnkode=111"></a>
<div>Megler AS</div><div>Fin hytte</div><div>Gutubakken 18, Sjusjøen</div><div>70 m²</div>
<div>4&nbsp;650&nbsp;000&nbsp;kr</div><div>Totalpris: 4&nbsp;767&nbsp;340&nbsp;kr</div><div>Selveier ∙ Hytte ∙ 2 soverom</div></article>
<article class="sf-search-ad"><a href="/realestate/leisuresale/ad.html?finnkode=222"></a>
<div>Leilighet</div><div>Veien 1, Sjusjøen</div><div>50 m²</div><div>3&nbsp;000&nbsp;000&nbsp;kr</div><div>Selveier ∙ Leilighet ∙ 1 soverom</div></article>
<article class="sf-search-ad"><a href="/realestate/leisuresale/ad.html?finnkode=333"></a>
<div>Annet sted</div><div>Veien 2, Hemsedal</div><div>100 m²</div><div>5&nbsp;000&nbsp;000&nbsp;kr</div><div>Selveier ∙ Hytte ∙ 3 soverom</div></article>
<article><a href="/realestate/leisuresale/ad.html?finnkode=444"></a><div>Uten pris</div></article>"""


def test_finn_parse_and_match():
    ads = finn.parse_search(ART)
    assert [a["finnkode"] for a in ads] == ["111", "222", "333"]
    assert ads[0]["area_m2"] == 70 and ads[0]["price_nok"] == 4_650_000 and ads[0]["type"] == "Hytte"
    m = finn.match_cluster(ads, "Sjusjøen", "Ringsaker")
    assert [a["finnkode"] for a in m] == ["111"]      # kun hytte med feltnavn i stedsangivelsen


def test_finn_aggregate_median(tmp_path, monkeypatch):
    f = tmp_path / "l.csv"
    pd.DataFrame({"cluster_id": ["a"] * 3 + ["b"], "price_nok": [3e6, 4e6, 5e6, 2e6],
                  "area_m2": [50, 50, 100, 40]}).to_csv(f, index=False)
    monkeypatch.setattr(finn, "LISTINGS", f)
    monkeypatch.setattr(finn, "MANUAL", tmp_path / "none.csv")
    areas = pd.DataFrame({"id": ["a", "b"], "navn": ["A", "B"], "kommune": ["K", "K"], "kommunenr": ["1", "1"]})
    g = finn.aggregate(areas, 3).set_index("id")
    assert g.loc["a", "finn_n_ads"] == 3 and g.loc["a", "finn_level"] == "felt"
    assert g.loc["a", "finn_median_price_per_m2"] == 60000     # median(60000, 80000, 50000)
    assert g.loc["a", "finn_median_price_nok"] == 4e6


def test_dbscan_finds_dense_groups_and_noise():
    rng = np.random.default_rng(0)
    xy = np.vstack([rng.normal([0, 0], 500, (50, 2)), rng.normal([30000, 0], 500, (50, 2)),
                    [[-90000, 90000]]])
    lab = clusters.dbscan(xy, 1500, 25)
    assert len(set(lab) - {-1}) == 2 and lab[-1] == -1
    assert (clusters.dbscan(xy, 1500, 25) == lab).all()   # deterministisk


def test_split_large_respects_radius():
    rng = np.random.default_rng(1)
    xy = np.column_stack([np.linspace(0, 12000, 400), rng.normal(0, 100, 400)])
    lab = clusters.dbscan(xy, 1500, 25)
    assert len(set(lab) - {-1}) == 1
    lab2 = clusters.split_large(xy, lab, 3000)
    assert len(set(lab2) - {-1}) > 1


def test_tile_bbox_shared_within_tile():
    a = osm.tile_bbox(61.05, 10.10, 30)
    assert a == osm.tile_bbox(61.20, 10.40, 30)
    assert a != osm.tile_bbox(61.30, 10.40, 30)


def test_finn_falls_back_to_kommune_level(tmp_path, monkeypatch):
    f = tmp_path / "l.csv"
    pd.DataFrame({"cluster_id": ["a", "kommune:1", "kommune:1", "kommune:1"], "price_nok": [3e6, 4e6, 5e6, 6e6],
                  "area_m2": [50, 50, 50, 50]}).to_csv(f, index=False)
    monkeypatch.setattr(finn, "LISTINGS", f)
    monkeypatch.setattr(finn, "MANUAL", tmp_path / "none.csv")
    areas = pd.DataFrame({"id": ["a"], "navn": ["A"], "kommune": ["K"], "kommunenr": ["1"]})
    g = finn.aggregate(areas, 3, 3).set_index("id")
    assert g.loc["a", "finn_level"] == "kommune" and g.loc["a", "finn_median_price_per_m2"] == 100000


def test_kommune_level_needs_more_ads(tmp_path, monkeypatch):
    f = tmp_path / "l.csv"
    pd.DataFrame({"cluster_id": ["kommune:1"] * 4, "price_nok": [1e6] * 4, "area_m2": [50] * 4}).to_csv(f, index=False)
    monkeypatch.setattr(finn, "LISTINGS", f)
    monkeypatch.setattr(finn, "MANUAL", tmp_path / "none.csv")
    areas = pd.DataFrame({"id": ["a"], "navn": ["A"], "kommune": ["K"], "kommunenr": ["1"]})
    assert finn.aggregate(areas, 3, 10).empty       # 4 annonser < 10 på kommune-nivå
