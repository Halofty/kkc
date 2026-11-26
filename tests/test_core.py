import sys
from pathlib import Path

import pandas as pd
import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from kkc.commute.subway import SubwayGraph
from kkc.ranking.rank import score_regions, tradeoff_suggestions
from kkc.vision.fov import crop_ratio, fov_from_focal_35mm, restore_standard_view


def test_dijkstra_with_transfer():
    g = SubwayGraph()
    g.add_segment("2", "신림", "서울대입구", 2)
    g.add_segment("2", "서울대입구", "사당", 4)
    g.add_segment("4", "사당", "총신대입구", 2)
    g.add_transfer("사당", "2", "4", 3)
    t = g.times_from("신림")
    assert t["사당"] == 6
    assert t["총신대입구"] == 6 + 3 + 2


def test_fov_math():
    assert fov_from_focal_35mm(26) == pytest.approx(69.4, abs=0.1)
    assert fov_from_focal_35mm(13) == pytest.approx(108.3, abs=0.2)
    assert crop_ratio(69.4) == 1.0
    assert crop_ratio(108.3) == pytest.approx(0.5, abs=0.01)  # 0.5x → 절반 크롭


def test_restore_keeps_size():
    img = Image.new("RGB", (400, 300))
    assert restore_standard_view(img, 108).size == (400, 300)


def test_ranking_and_tradeoff():
    df = pd.DataFrame({"region": ["A", "B", "C"], "pred_rent": [70, 60, 50],
                       "commute_min": [20, 28, 38], "amenity_cnt": [10, 10, 10]})
    r = score_regions(df, budget=80, max_commute=30)
    assert list(r.region) == ["B", "A"]  # C는 통학 초과
    s = tradeoff_suggestions(df, budget=80, max_commute=30)
    assert s[0] == {"extra_minutes": 10, "monthly_saving": 10.0, "region": "C"}



def test_osm_subway_map_dedups_ways_clips_and_merges_stops():
    from kkc.commute.subway import osm_subway_map
    way = {"type": "way", "ref": 1, "role": "", "geometry": [{"lat": 37.5, "lon": 127.0}, {"lat": 37.51, "lon": 127.01}]}
    far = {"type": "way", "ref": 2, "role": "", "geometry": [{"lat": 36.8, "lon": 127.1}, {"lat": 36.81, "lon": 127.1}]}
    stop = {"type": "node", "ref": 9, "role": "stop"}
    els = [{"type": "relation", "tags": {"ref": "2"}, "members": [way, far, stop]},
           {"type": "relation", "tags": {"ref": "2"}, "members": [way]},  # 반대 방향 노선이 같은 선로를 또 적는다
           {"type": "node", "lat": 37.50, "lon": 127.0, "tags": {"name": "가"}},
           {"type": "node", "lat": 37.52, "lon": 127.0, "tags": {"name": "가"}},  # 방향별 정차 위치 → 평균
           {"type": "node", "lat": 36.80, "lon": 127.1, "tags": {"name": "천안"}}]  # 서울 밖
    m = osm_subway_map(els)
    assert m["lines"] == {"2": [[[37.5, 127.0], [37.51, 127.01]]]}
    assert m["stations"] == [{"name": "가", "lat": 37.51, "lon": 127.0}]
