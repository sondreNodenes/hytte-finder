import numpy as np
import pandas as pd
import pytest

from hytte_finder import scoring
from hytte_finder.common import haversine_km, load_config


def test_percentile_normalization_range_and_order():
    s = pd.Series([10, 20, 30, 40])
    n = scoring.normalize(s, "percentile")
    assert n.min() == 0 and n.max() == 1
    assert n.is_monotonic_increasing


def test_minmax_and_invert():
    s = pd.Series([0.0, 5.0, 10.0])
    assert scoring.normalize(s, "minmax").tolist() == [0, 0.5, 1]
    assert scoring.normalize(s, "minmax", invert=True).tolist() == [1, 0.5, 0]


def test_nan_preserved_and_constant_is_neutral():
    n = scoring.normalize(pd.Series([1.0, np.nan, 3.0]), "minmax")
    assert np.isnan(n[1])
    c = scoring.normalize(pd.Series([7.0, 7.0, np.nan]), "percentile")
    assert c[0] == 0.5 and np.isnan(c[2])


def test_weighted_mean_renormalizes_over_missing():
    f = pd.DataFrame({"a": [1.0, 1.0], "b": [0.0, np.nan]})
    r = scoring.weighted_mean_rowwise(f, {"a": 0.5, "b": 0.5})
    assert r[0] == pytest.approx(0.5) and r[1] == pytest.approx(1.0)
    all_nan = pd.DataFrame({"a": [np.nan]})
    assert np.isnan(scoring.weighted_mean_rowwise(all_nan, {"a": 1})[0])


def test_total_score_bounds():
    df = pd.DataFrame({c: [0.0, 1.0] for c in scoring.CATS})
    s = scoring.total_score(df, load_config()["weights"]["default"])
    assert s.tolist() == [0, 100]


def test_default_weights_sum_to_one():
    cfg = load_config()
    assert sum(cfg["weights"]["default"].values()) == pytest.approx(1.0)
    for p in cfg["profiles"].values():
        assert sum(p.values()) == pytest.approx(1.0)


def _base(**kw):
    d = {"drive_min": 100.0, "avg_price_nok": 3e6, "sales_last_year": 50, "elevation_m": 800.0}
    d.update(kw)
    return d


def test_drive_time_filter_boundary():
    cfg = load_config()
    df = pd.DataFrame([_base(drive_min=165.0), _base(drive_min=165.1), _base(drive_min=np.nan)])
    out = scoring.apply_filters(df, cfg)
    assert out["passes"].tolist() == [True, False, False]
    assert "kjøretid" in out["filter_reason"][1]


def test_price_filter_and_uncertain_flag():
    cfg = load_config()
    limit = cfg["filters"]["price_max_nok"] * cfg["filters"]["price_tolerance"]
    df = pd.DataFrame([_base(avg_price_nok=limit), _base(avg_price_nok=limit + 1),
                       _base(avg_price_nok=np.nan), _base(sales_last_year=14)])
    out = scoring.apply_filters(df, cfg)
    assert out["passes"].tolist() == [True, False, False, True]
    assert out["usikker"].tolist() == [False, False, False, True]


def test_value_indices_use_floor_and_trail_offer():
    df = pd.DataFrame({"avg_price_nok": [3e6, 3e6], "nordic_km_10km": [100.0, 0.0],
                       "marked_routes_km_15km": [0.0, 0.0]})
    out = scoring.value_indices(df, pd.Series([0.5, 0.0]), floor=0.05)
    assert out["value_price_per_snow"][0] == pytest.approx(6e6)
    assert out["value_price_per_snow"][1] == pytest.approx(6e7)
    assert out["value_price_per_trail"][0] == pytest.approx(3e4)
    assert out["value_price_per_trail"][1] == pytest.approx(3e6)  # gulv 1 km


def test_sensitivity_deterministic_and_dominant_area():
    cfg = load_config()
    df = pd.DataFrame({"id": ["a", "b", "c"], **{c: [0.9, 0.5, 0.1] for c in scoring.CATS}})
    s1 = scoring.sensitivity(df, cfg["weights"]["default"], 200, 50, 1)
    s2 = scoring.sensitivity(df, cfg["weights"]["default"], 200, 50, 1)
    assert s1.equals(s2)
    assert s1.iloc[0]["id"] == "a" and s1.iloc[0]["topp5_andel"] == 1.0


def test_rank_table_orders_descending():
    df = pd.DataFrame({"id": ["a", "b"], **{c: [0.2, 0.8] for c in scoring.CATS}})
    r = scoring.rank_table(df, load_config()["weights"]["default"])
    assert r["id"].tolist() == ["b", "a"] and r["rank"].tolist() == [1, 2]


def test_haversine_oslo_lillehammer():
    d = haversine_km(59.964, 10.667, 61.115, 10.466)
    assert 125 < d < 135


def test_elevation_filter_excludes_lowland():
    cfg = load_config()
    df = pd.DataFrame([_base(elevation_m=cfg["filters"]["min_elevation_m"]),
                       _base(elevation_m=cfg["filters"]["min_elevation_m"] - 1), _base(elevation_m=np.nan)])
    out = scoring.apply_filters(df, cfg)
    assert out["passes"].tolist() == [True, False, False]


def test_new_categories_in_config_and_scored():
    cfg = load_config()
    assert {"Jakt", "Fiske"} <= set(cfg["weights"]["default"]) <= set(scoring.CATS)
    df = pd.DataFrame({"id": ["a", "b"], "avg_price_nok": [3e6, 3e6], "ski_season_days": [100.0, 200.0],
                       "elevation_m": [700.0, 900.0], "drive_min": [100.0, 120.0],
                       "jakt_elg_per_100km2": [1.0, 5.0], "lake_area_km2_10km": [9.0, 1.0]})
    out = scoring.category_scores(df, cfg)
    assert out["Jakt"][1] > out["Jakt"][0] and out["Fiske"][0] > out["Fiske"][1]
    assert out["Sosialt"].isna().all()
