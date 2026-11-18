"""화각 모델 학습. 사진 폴더(0.5x·1x로 찍은 실내 jpg, EXIF 유지)를 넣으면 models/fov.pt 저장.

    python scripts/train_fov.py data/raw/photos --epochs 10
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from kkc.vision.fov import train_fov  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("photos")
ap.add_argument("--epochs", type=int, default=10)
args = ap.parse_args()

_, mae = train_fov(args.photos, epochs=args.epochs, out=ROOT / "models/fov.pt")
print(f"화각 검증 MAE {mae:.1f}°  → models/fov.pt")
