"""웹 데모 (Streamlit). 실행: streamlit run app/streamlit_app.py

직장·학교 입력 → 가장 가까운 역 → 자치구별 통학 시간 + 원룸 보증금·월세 → 추천 순위와 서울 지도.
scripts/build_data.py 가 만든 파일을 쓰고, 없으면 예시 데이터로 동작한다.
  data/processed/regions.csv, data/processed/stations.csv
  models/price.joblib, models/subway.pkl, models/fov.pt (scripts/train_fov.py)
"""
import json
import pickle
import sys
import urllib.parse
import urllib.request
from pathlib import Path

import joblib
import pandas as pd
import pydeck as pdk
import streamlit as st
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from kkc.commute.subway import nearest_station, region_commute  # noqa: E402
from kkc.price.model import BTYPES, ROOMS, converted_rent, price_gap  # noqa: E402
from kkc.ranking.rank import score_regions, tradeoff_suggestions  # noqa: E402
from kkc.vision.fov import load_fov_model, predict_fov, restore_standard_view, wide_angle_flag  # noqa: E402

REGIONS, STATIONS, DEALS, PRICE, SUBWAY, FOV = (ROOT / p for p in (
    "data/processed/regions.csv", "data/processed/stations.csv", "data/processed/deals.csv", "models/price.joblib",
    "models/subway.pkl", "models/fov.pt"))
SAMPLE = pd.DataFrame({
    "region": ["관악구", "동작구", "광진구", "마포구", "성북구", "강남구"],
    "pred_rent": [55, 60, 62, 68, 52, 102],
    "commute_min": [35, 28, 40, 30, 45, 20],
    "amenity_cnt": [120, 95, 110, 140, 80, 200],
    "deposit_med": [500, 1000, 1000, 1000, 500, 1000], "rent_med": [45, 50, 52, 58, 43, 70],
})  # 예시 값 — 실제 데이터로 교체
SEOUL_BOX = "126.76,37.70,127.19,37.42"  # 위치 검색을 서울 안으로 한정 (서,북,동,남)

st.set_page_config(page_title="KKC 자취방 추천", page_icon="🏠", layout="wide")


@st.cache_resource
def load():
    price = joblib.load(PRICE) if PRICE.exists() else None
    subway = pickle.load(open(SUBWAY, "rb")) if SUBWAY.exists() else None
    fov = load_fov_model(FOV) if FOV.exists() else None
    return price, subway, fov


@st.cache_data(show_spinner="위치 찾는 중…")
def geocode(query: str):
    """장소 이름 → (위도, 경도, 주소). OpenStreetMap Nominatim(키 불필요). 못 찾거나 오프라인이면 None."""
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(
        {"q": query, "format": "json", "limit": 1, "countrycodes": "kr", "viewbox": SEOUL_BOX, "bounded": 1})
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "kkc-room-finder-demo"})
        hit = json.load(urllib.request.urlopen(req, timeout=8))
    except (OSError, ValueError):
        return None
    return (float(hit[0]["lat"]), float(hit[0]["lon"]), hit[0]["display_name"]) if hit else None


def won(v: float) -> str:
    """만원 단위 → '1,000만' / '2.5억'. 1000만 이상은 100만 단위로 반올림(실제 계약값 6,793만 → 6,800만)."""
    if v >= 10000:
        return f"{v / 10000:.1f}억".replace(".0억", "억")
    return f"{round(v, -2) if v >= 1000 else v:,.0f}만"


def deposit_text(r) -> str:
    """보증금은 1000만에 몰려 있어 한 값보다 '보통 범위(가운데 50%)'가 구별 차이를 보여준다."""
    if "deposit_lo" not in r or r.deposit_lo == r.deposit_hi:
        return won(r.deposit_med)
    return f"{won(r.deposit_lo)}~{won(r.deposit_hi)}"


def price_text(r) -> str:
    return f"전세 {deposit_text(r)}" if r.rent_med == 0 else f"보증금 {deposit_text(r)} / 월세 {r.rent_med:,.0f}만"


price, subway, fov_model = load()
ready = REGIONS.exists() and STATIONS.exists() and DEALS.exists() and subway

st.title("🏠 직장·학교 근처 자취방 찾기")
st.caption("직장이나 학교를 입력하면 지하철로 다니기 좋은 지역과 원룸 보증금·월세를 알려드려요.")

with st.sidebar:
    st.header("조건")
    room = st.radio("방", list(ROOMS), horizontal=True, format_func=lambda k: f"{k} ({ROOMS[k]})")
    kind = st.radio("계약", ["월세", "전세"], horizontal=True)
    if kind == "월세":
        max_deposit = st.slider("보증금 최대(만원)", 100, 10000, 2000, step=100)
        max_rent = st.slider("월세 최대(만원)", 20, 200, 60 if room == "원룸" else 90, step=5)
    else:
        max_deposit = st.slider("전세금 최대(만원)", 5000, 80000, 25000 if room == "원룸" else 35000, step=1000,
                                help="10000만원 = 1억")
        max_rent = float("inf")
    max_commute = st.slider("통학·통근 최대(분)", 10, 90, 45, step=5)
    w = st.slider("무엇이 더 중요해요?", 0, 100, 65, format="%d%%", help="0% = 월세가 싼 곳, 100% = 가까운 곳")
    st.caption("← 월세 싼 곳 · 가까운 곳 →")
weights = {"rent": (1 - w / 100) * 0.85, "commute": w / 100 * 0.85, "amenity": 0.15}

place = st.text_input("직장·학교", value="경희대학교", placeholder="예: 경희대학교, 삼성전자 서초사옥, 강남역")

dest = None
if ready:
    regions, coords = pd.read_csv(REGIONS), pd.read_csv(STATIONS, index_col=0)
    hit = geocode(place.strip()) if place.strip() else None
    if hit:
        lat, lon, addr = hit
        station, walk = nearest_station(lat, lon, coords)
    elif place.strip().removesuffix("역") in coords.index:  # 검색 실패(오프라인 등) 시 역 이름으로라도
        station, walk = place.strip().removesuffix("역"), 0.0
        lat, lon, addr = coords.lat[station], coords.lon[station], f"{station}역"
    else:
        st.warning("장소를 찾지 못했어요. 다른 이름이나 가까운 지하철역 이름으로 입력해 보세요.")
        st.stop()
    dest = {"lat": lat, "lon": lon, "label": "📍 " + place.strip(), "info": "직장·학교"}
    st.markdown(f"📍 **{addr.split(', 대한민국')[0]}**  \n가장 가까운 역: **{station}역** (도보 약 {walk:.0f}분)")
    if walk > 25:
        st.caption("⚠️ 가까운 1~8호선 역이 멀어요. 코레일·9호선 등은 아직 데이터에 없어서 실제보다 길게 나올 수 있어요.")
    regions["commute_min"] = (regions.region.map(region_commute(subway, station)) + walk).round()
    deals = pd.read_csv(DEALS).query("room == @room and kind == @kind").drop(columns=["room", "kind"])
    regions = regions.dropna(subset=["commute_min"]).merge(deals.rename(columns={"gu": "region"}), on="region")
else:
    regions = SAMPLE
    st.caption("⚠️ 예시 데이터로 표시 중 — scripts/build_data.py 를 실행하면 실제 데이터로 바뀝니다")

# 순위의 '가격' = 고른 방·계약의 실제 중앙값을 환산월세로 (전세는 월세 0이라 보증금 이자만). AI 예측값은 표에 따로.
regions = regions.assign(model_rent=regions.pred_rent, pred_rent=converted_rent(regions.deposit_med, regions.rent_med))
ok = regions[(regions.deposit_med <= max_deposit) & (regions.rent_med <= max_rent)]
ranked = score_regions(ok, budget=float("inf"), max_commute=max_commute, weights=weights)

# 1·2. 추천 지역 — 상위 3곳 카드 + 지도 + 전체 표
st.subheader("추천 지역")
if ranked.empty:
    st.info("조건에 맞는 지역이 없어요. 왼쪽에서 보증금·월세·통학 시간을 조금 늘려 보세요.")
for col, (i, r) in zip(st.columns(3), ranked.head(3).iterrows()):
    with col.container(border=True):
        st.markdown(f"#### {i + 1}위 · {r.region}")
        if "station" in r:
            st.caption(f"{r.station}역 근처")
        st.markdown(f"**{price_text(r)}**")
        st.markdown(f"🚇 {r.commute_min:.0f}분")

if dest:
    m = regions.copy()
    m["rank"] = m.region.map({g: i for i, g in enumerate(ranked.region)})
    m["label"] = [f"{int(k) + 1}. {g}" if pd.notna(k) else g for k, g in zip(m["rank"], m.region)]
    m["color"] = [[37, 99, 235, 230] if k < 3 else [96, 165, 250, 200] if pd.notna(k) else [156, 163, 175, 140]
                  for k in m["rank"]]
    m["size"] = [900 if k < 3 else 650 if pd.notna(k) else 450 for k in m["rank"]]
    m["info"] = [f"{room} {price_text(r)}<br/>🚇 {r.commute_min:.0f}분 ({r.station}역)"
                 for _, r in m.iterrows()]
    d = pd.DataFrame([{**dest, "color": [220, 38, 38, 255], "size": 700}])
    pts = pd.concat([m, d])[["lat", "lon", "label", "info", "color", "size"]]
    layers = [
        pdk.Layer("ScatterplotLayer", pts, get_position="[lon, lat]", get_fill_color="color", get_radius="size",
                  pickable=True, stroked=True, get_line_color=[255, 255, 255], line_width_min_pixels=1),
        pdk.Layer("TextLayer", pts, get_position="[lon, lat]", get_text="label", get_size=13,
                  get_color=[17, 24, 39], get_pixel_offset=[0, -18], character_set="auto",
                  font_family="'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif", font_weight=600),
    ]
    st.pydeck_chart(pdk.Deck(layers=layers, map_provider="carto", map_style=pdk.map_styles.CARTO_LIGHT,
                             initial_view_state=pdk.ViewState(latitude=37.56, longitude=126.99, zoom=10.3),
                             tooltip={"html": "<b>{label}</b><br/>{info}"}), height=520)
    st.caption("진한 파랑: 상위 3곳 · 파랑: 조건에 맞는 지역 · 회색: 조건 밖 · 빨강: 직장·학교. "
               "점에 마우스를 올리면 보증금·월세·통학 시간이 보여요.")

st.dataframe(
    ranked.assign(순위=ranked.index + 1, deposit=[deposit_text(r) for _, r in ranked.iterrows()])[
        ["순위", "region"] + (["station"] if "station" in ranked else [])
        + ["commute_min", "deposit"] + (["rent_med"] if kind == "월세" else [])
        + [c for c in ["deals", "model_rent"] if c in ranked] + ["amenity_cnt"]],
    hide_index=True, width="stretch",
    column_config={"region": "지역", "station": "대표역", "commute_min": st.column_config.NumberColumn("통학(분)"),
                   "deposit": "보증금(보통 범위)" if kind == "월세" else "전세금(보통 범위)",
                   "rent_med": st.column_config.NumberColumn("월세(만원)", format="%d"),
                   "deals": st.column_config.NumberColumn("거래 수", help="최근 12개월, 이 방·계약 종류"),
                   "model_rent": st.column_config.NumberColumn("AI 예측 시세(20㎡ 환산월세)", format="%.1f"),
                   "amenity_cnt": st.column_config.NumberColumn("편의점·마트·병원 수")})
if price:
    st.caption(f"보증금·월세: 서울특별시 전월세가 정보(서울 열린데이터광장, 아파트 제외) 최근 12개월(~{price['latest_ym']}) "
               f"실제 계약 — 방은 면적으로 구분(원룸 ~33㎡, 투룸 33~66㎡), 보증금은 가운데 50% 범위(25~75%), "
               f"월세는 중앙값. AI 예측 시세: 같은 자료(계약 {price['period']}) "
               f"20㎡ 기준 Gradient Boosting 예측 (최근 계약 20% 검증 MAE {price['mae']:.1f}만원). "
               "통학: 대표역까지 서울교통공사 역간 소요시간(2024-08) + 환승 + 목적지 도보. "
               "편의시설: 소상공인시장진흥공단 상가정보(2026-09). 위치 검색: OpenStreetMap.")

# 5. 양보 제안
with st.expander("💡 이것만 양보하면"):
    tips = tradeoff_suggestions(ok, float("inf"), max_commute)
    for s in tips:
        st.write(f"통학 {s['extra_minutes']}분만 양보하면 {s['region']}에서 월 약 {s['monthly_saving']}만원 절약")
    if not tips:
        st.write("지금 조건에서 더 싸게 갈 곳은 없어요.")

# 3·6. 매물 가격 비교 + 종합 추천
st.divider()
st.subheader("내 후보 매물 비교")
listings = st.data_editor(pd.DataFrame({
    "name": ["매물 A"], "gu": [regions.region.iloc[0]], "dong": [""], "area_m2": [20.0],
    "floor": [3], "build_year": [2015], "btype": ["단독다가구"], "deposit": [1000], "rent": [50],
}), num_rows="dynamic", column_config={"gu": st.column_config.SelectboxColumn(options=list(regions.region)),
                                      "btype": st.column_config.SelectboxColumn(options=BTYPES)})
listings = listings.dropna(subset=["gu", "deposit", "rent"])
if not listings.empty:
    by_gu = regions.set_index("region")
    cand = pd.DataFrame({
        "region": listings.name, "pred_rent": converted_rent(listings.deposit, listings.rent).round(1),
        "commute_min": listings.gu.map(by_gu.commute_min), "amenity_cnt": listings.gu.map(by_gu.amenity_cnt),
    })
    if price:
        cand["시세 대비(만원)"] = price_gap(price["model"], listings.assign(contract_ym=price["latest_ym"])).round(1).values
    budget = converted_rent(max_deposit, max_rent)
    picked = score_regions(cand, budget, max_commute).rename(columns={"region": "매물", "pred_rent": "환산월세"})
    st.dataframe(picked)
    if len(picked) < len(cand):
        st.caption(f"예산·통학 조건을 넘는 매물 {len(cand) - len(picked)}개는 제외됨 (예산 = 보증금·월세 최대를 환산월세로)")
    st.caption("시세 대비: 음수면 같은 조건 예측 시세보다 싸다." if price else "가격 모델이 없어 시세 비교는 생략")

# 4. 사진 화각
st.subheader("매물 사진 화각 분석")
up = st.file_uploader("매물 사진", type=["jpg", "jpeg", "png"])
if up:
    img = Image.open(up).convert("RGB")
    if fov_model:
        est = predict_fov(fov_model, img)
        st.write(f"추정 화각 {est:.0f}°")
    else:
        est = st.number_input("추정 화각(°) — 모델 학습 전 임시 입력", 40.0, 130.0, 108.0)
    st.info(f"{wide_angle_flag(est)} (참고 정보이며 허위 매물 판정이 아닙니다)")
    c1, c2 = st.columns(2)
    c1.image(img, caption="원본")
    c2.image(restore_standard_view(img, est), caption="표준 렌즈(1x) 시야")
