import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from kkc.ui import gap_label


def test_gap_label_cheaper_pricier_similar():
    assert gap_label(-3.24) == ("시세보다 3.2만 원 싸요", "good")
    assert gap_label(1.8) == ("시세보다 1.8만 원 비싸요", "bad")
    assert gap_label(0.3) == ("시세와 비슷해요", "neutral")
