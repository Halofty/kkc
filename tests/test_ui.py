import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from kkc.ui import gap_label


def test_gap_label_cheaper_pricier_similar():
    assert gap_label(-3.24) == ("시세보다 3.2만 원 싸요", "good")
    assert gap_label(1.8) == ("시세보다 1.8만 원 비싸요", "bad")
    assert gap_label(0.3) == ("시세와 비슷해요", "neutral")


def test_tradeoff_lines_skip_same_region():
    from kkc.ui import tradeoff_lines
    s = [{"extra_minutes": 10, "monthly_saving": 10.0, "region": "C"},
         {"extra_minutes": 20, "monthly_saving": 10.0, "region": "C"},
         {"extra_minutes": 30, "monthly_saving": 14.5, "region": "D"}]
    assert tradeoff_lines(s) == ["통학 10분만 양보하면 C에서 월 10.0만 원 아낄 수 있어요",
                                 "통학 30분만 양보하면 D에서 월 14.5만 원 아낄 수 있어요"]
    assert tradeoff_lines([]) == []


def test_sort_regions_both_directions_and_label():
    import pandas as pd
    from kkc.ui import sort_regions
    df = pd.DataFrame({"region": ["A", "B", "C"], "rent_med": [50, 40, 60], "deposit_med": [500, 1000, 300],
                       "commute_min": [30, 20, 40], "rank": [1, 2, 3]})
    out, label = sort_regions(df, "월세")
    assert list(out.region) == ["B", "A", "C"] and label == "월세 낮은순"
    out, label = sort_regions(df, "월세", desc=True)
    assert list(out.region) == ["C", "A", "B"] and label == "월세 높은순"
    out, label = sort_regions(df, "거리", desc=True)
    assert list(out.region) == ["C", "A", "B"] and label == "거리 먼순"
    out, label = sort_regions(df, "보증금")
    assert list(out.region) == ["C", "A", "B"] and label == "보증금 낮은순"
    out, label = sort_regions(df, "추천")
    assert list(out.region) == ["A", "B", "C"] and label == "추천 높은순"
