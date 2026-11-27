# KKC · AI 자취방 추천 서비스

예산·통학지를 넣으면 서울 주거지역과 매물을 추천하고, 매물 사진의 화각을 추정해 표준 렌즈(1x) 시야로 복원해 보여주는 웹서비스.

## 빠른 시작
```bash
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
pytest -q                       # 16개 통과 확인
streamlit run app/streamlit_app.py
```

## 실제 데이터 넣기
데이터 없이도 앱은 예시 값으로 돈다. 아래 파일을 `data/raw/`에 받아 두고 스크립트를 돌리면 실제 값으로 바뀐다.

| 파일 | 출처 |
|---|---|
| 전월세 CSV (여러 개 가능) | 서울 열린데이터광장 "서울특별시 부동산 전월세가 정보"(아파트는 자동 제외) 또는 국토교통부 rt.molit.go.kr |
| 역간거리 및 소요시간 CSV | 서울 열린데이터광장 OA-12034 (서울교통공사) |
| 환승역거리 소요시간 정보 CSV | 서울 열린데이터광장 OA-13290 (서울교통공사) |
| 1_8호선 역사 좌표(위경도) CSV | 서울교통공사 (공공데이터포털) |
| 상가(상권)정보 서울 CSV | 공공데이터포털 (소상공인시장진흥공단) |
| 버스노선별 정류소정보 xlsx | 서울 열린데이터광장 OA-1095 |
| 노선별 정류장 구간 평균 운행시간 · 버스 운행횟수 CSV (`--bus-*`는 선택, 없으면 통학은 지하철만) | 서울 열린데이터광장 OA-21217 · OA-21220 (TOPIS) |

`seoul_data/`에 있는 파일로 바로 빌드 (약 1분). 먼저 노선 데이터를 받는다 — 지도 호선·역 이름 + 서울교통공사 파일에 없는 1호선 코레일 구간(회기·용산 등)·9호선을 통학 계산에 넣는다 (역간 시간은 거리로 추정):
```bash
python scripts/fetch_subway_map.py   # OpenStreetMap → data/processed/subway_map.json
python scripts/build_data.py --rent "seoul_data/서울특별시_전월세가_2025.csv"     --dist "seoul_data/서울교통공사 역간거리 및 소요시간_240810.csv"     --transfer "seoul_data/서울교통공사_환승역거리 소요시간 정보_20260831.csv"     --coords "seoul_data/서울교통공사_1_8호선 역사 좌표(위경도) 정보_20250814.csv"     --stores "seoul_data/소상공인시장진흥공단_상가(상권)정보_서울_202609.csv"     --bus-routes "seoul_data/서울시버스노선별정류소정보(20261102).xlsx"     --bus-speed "seoul_data/tpss_route_section_speedh_2026.11.09-11.15.csv"     --bus-turn "seoul_data/tpss_sta_route_hturn_2026.11.09-11.15.csv"
```
결과(2026-11-18 빌드): 거래 639,959건(계약 2023-09~2026-02), 월세 모델 MAE 15.2만원(최근 계약 20% 검증, 기존 설정 15.9), 지하철 240역, 25개 구. (2026-11-26 OSM 노선 보강 후 403역)

다른 파일로 빌드할 때:
```bash
python scripts/build_data.py --rent data/raw/rent_*.csv --dist data/raw/역간거리.csv \
    --transfer data/raw/환승.csv --coords data/raw/역좌표.csv --stores data/raw/상가_서울.csv
python scripts/train_fov.py data/raw/photos --epochs 10   # 0.5x·1x 실내 사진 (EXIF 유지)
```
결과는 `models/`, `data/processed/`(구: regions·deals, 동: dongs·deals_dong, 역: stations)에 생기고 커밋하지 않는다.

## Claude Code 플러그인
`.claude/settings.json`에 Superpowers · Karpathy skills · I have ADHD · Ponytail이 project scope로 등록돼 있음.
graphify 훅도 같이 등록돼 있어서 **`pip install -r requirements.txt`로 `graphify` CLI를 꼭 설치**해야 한다 (없으면 훅 오류).
코드를 고친 뒤에는 `graphify update .`으로 `graphify-out/` 그래프를 갱신한다.
이 폴더에서 `claude`를 실행하면 마켓플레이스 신뢰/설치 안내가 뜬다. 수동 설치는:
```powershell
.\scripts\install-plugins.ps1    # Windows
bash scripts/install-plugins.sh  # macOS/Linux
```

## 구조
```
src/kkc/price/model.py     월세 예측 (GBR) + 시세 대비 가격 차이
src/kkc/commute/subway.py  지하철 다익스트라 통학 시간
src/kkc/ranking/rank.py    지역 추천 점수 + "이것만 양보하면"
src/kkc/vision/fov.py      화각 추정 모델 + 1x 시야 복원
app/streamlit_app.py       웹 데모
docs/proposal.md           제안서 / 개발 계획
```

## 다음 할 일
- [x] (김태욱) 서울시 전월세가 → `price.model.train` (건물용도 피처 + 모델 확대, 최근 계약 20% 검증 MAE 15.9 → 15.2만원)
- [x] (공통) 서울교통공사 역간 운행시간·환승 데이터 → `SubwayGraph` 적재 (2·5호선 지선, 이수=총신대입구 보정)
- [x] (김상혁) 상가정보로 자치구별 편의시설 수 → `regions.csv` 생성 (반경 집계는 매물 좌표가 생기면)
- [ ] 1~8호선 밖 역(회기 등 코레일·9호선)은 통학지로 못 고름 — 해당 노선 데이터 추가 필요
- [ ] (최한별) 0.5x/1x 실내 사진 쌍 촬영 → EfficientNet-B0 학습
