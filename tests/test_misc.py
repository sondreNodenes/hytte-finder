import numpy as np

from hytte_finder import osm, ssb, terrain


def test_slope_of_plane():
    # 1 m stigning per 1 m horisontalt = 45 grader
    a = np.tile(np.arange(10, dtype=float), (10, 1))
    s = terrain.slope_deg(a, 1.0)
    assert np.allclose(s, 45)


def test_jsonstat_parser():
    js = {"id": ["Region", "Tid"], "size": [2, 1],
          "dimension": {"Region": {"category": {"index": {"0301": 0, "3303": 1},
                                                "label": {"0301": "Oslo", "3303": "Kongsberg"}}},
                        "Tid": {"category": {"index": {"2025": 0}}}},
          "value": [1.5, None]}
    df = ssb.jsonstat_to_df(js)
    assert df["Region_label"].tolist() == ["Oslo", "Kongsberg"]
    assert df["value"][0] == 1.5 and np.isnan(df["value"][1])


def test_seg_length_only_inside_radius():
    geom = [{"lat": 61.0, "lon": 10.0}, {"lat": 61.0, "lon": 10.05}, {"lat": 62.0, "lon": 10.05}]
    inside = osm._seg_len_in_radius(geom, 61.0, 10.0, 5)
    assert 2.5 < inside < 3.0  # kun første segment (~2.7 km)


def test_bbox_contains_center():
    s, w, n, e = [float(x) for x in osm.bbox(61.0, 10.0, 15).strip("()").split(",")]
    assert s < 61 < n and w < 10 < e
