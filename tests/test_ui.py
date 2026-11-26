import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from kkc.ui import gap_label


def test_gap_label_cheaper_pricier_similar():
    assert gap_label(-3.24) == ("시세보다 3.2만 원 싸요", "good")
    assert gap_label(1.8) == ("시세보다 1.8만 원 비싸요", "bad")
    assert gap_label(0.3) == ("시세와 비슷해요", "neutral")


def test_pick_photo_by_room_cycles_and_falls_back():
    from kkc.ui import pick_photo
    m = {"main": [{"id": "a"}, {"id": "b"}], "living": [{"id": "c"}]}
    assert pick_photo(m, "원룸", 0)["id"] == "a"
    assert pick_photo(m, "원룸", 3)["id"] == "b"  # 사진보다 매물이 많으면 돌려 쓴다
    assert pick_photo(m, "투룸", 1)["id"] == "c"
    assert pick_photo({}, "원룸", 0) is None  # 사진을 안 받았으면 일러스트로
