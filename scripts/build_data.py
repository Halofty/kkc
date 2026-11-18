"""공공데이터 → 앱이 쓰는 파일 만들기.

    python scripts/build_data.py --rent data/raw/rent_*.csv --dist data/raw/역간거리.csv \
        --transfer data/raw/환승.csv --coords data/raw/역좌표.csv --stores data/raw/상가_서울.csv

만드는 것:
  models/price.joblib          월세 GBR 모델 + 검증 MAE + 학습 데이터 기준월
  models/subway.pkl            지하철 그래프 (앱에서 통학역 바꾸면 즉시 다익스트라)
  data/processed/stations.csv  역명, 위도, 경도 (지도·목적지 근처 역 찾기)
  data/processed/regions.csv   region, pred_rent, amenity_cnt, 대표역 좌표
  data/processed/deals.csv     구 × 원룸/투룸 × 월세/전세 보증금·월세 통계(최근 12개월)
"""
import argparse
import pickle
import sys
from pathlib import Path

import joblib
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from kkc.commute.subway import GU_STATION, load_seoul_metro, load_station_coords  # noqa: E402
from kkc.price.model import load_rent, region_deal_stats, region_rents, train  # noqa: E402
from kkc.ranking.rank import amenity_counts  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--rent", nargs="+", required=True, help="국토부 전월세 실거래가 CSV (여러 개 가능)")
ap.add_argument("--dist", required=True, help="서울교통공사 역간거리 및 소요시간 CSV")
ap.add_argument("--transfer", required=True, help="서울교통공사 환승역거리 소요시간 정보 CSV")
ap.add_argument("--coords", required=True, help="서울교통공사 1_8호선 역사 좌표(위경도) CSV")
ap.add_argument("--stores", required=True, help="소상공인시장진흥공단 상가(상권)정보 서울 CSV")
args = ap.parse_args()

(ROOT / "models").mkdir(exist_ok=True)
(ROOT / "data/processed").mkdir(parents=True, exist_ok=True)

deals = pd.concat([load_rent(p) for p in args.rent], ignore_index=True)
model, mae = train(deals)
period = f"{deals.contract_ym.min()}~{deals.contract_ym.max()}"
joblib.dump({"model": model, "mae": mae, "period": period, "latest_ym": int(deals.contract_ym.max())},ROOT / "models/price.joblib")
print(f"월세 모델: 거래 {len(deals):,}건 ({period}), 검증 MAE {mae:.1f}만원")

graph = load_seoul_metro(args.dist, args.transfer)
with open(ROOT / "models/subway.pkl", "wb") as f:
    pickle.dump(graph, f)
coords = load_station_coords(args.coords)
coords.to_csv(ROOT / "data/processed/stations.csv")
no_xy = sorted({n for n, _ in graph.adj} - set(coords.index))
print(f"역 좌표: {len(coords)}곳" + (f", 그래프 역 중 좌표 없음 {no_xy}" if no_xy else ""))
missing = [s for s in GU_STATION.values() if not graph.nodes_of(s)]
print(f"지하철: 역 {len({n for n, _ in graph.adj}):,}곳" + (f", 대표역 이름 불일치 {missing}" if missing else ""))

regions = pd.DataFrame({"pred_rent": region_rents(model, deals), "amenity_cnt": amenity_counts(args.stores)})
stats = region_deal_stats(deals).reset_index()
stats.to_csv(ROOT / "data/processed/deals.csv", index=False)
print(f"deals.csv: 구×방×계약 {len(stats)}칸 (최근 12개월 ~{deals.contract_ym.max()})")
regions["station"] = regions.index.map(GU_STATION)
regions = regions.join(coords, on="station").rename_axis("region").reset_index().dropna()
regions.to_csv(ROOT / "data/processed/regions.csv", index=False)
print(f"regions.csv: {len(regions)}개 구")
