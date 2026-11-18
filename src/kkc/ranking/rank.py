"""지역·매물 추천 순위.

1단계(지금): 가중합 점수 — 데이터 없이도 바로 동작하는 베이스라인.
2단계: 사용자 선호 데이터(클릭/선택)가 모이면 LightGBM LambdaRank로 교체.
피처: 예측 월세, 통학 시간, 반경 내 편의점·마트·병원 수(소상공인시장진흥공단 상가정보).
"""
from __future__ import annotations

import pandas as pd

from kkc.data import col, read_table

DEFAULT_WEIGHTS = {"rent": 0.5, "commute": 0.35, "amenity": 0.15}
AMENITY_KEYWORDS = ("편의점", "슈퍼마켓", "의원", "병원")  # 편의점·마트·병원


def amenity_counts(store_csv) -> pd.Series:
    """소상공인시장진흥공단 상가(상권)정보 CSV → 자치구별 편의점·마트·병원 수.
    shortcut: 제안서의 '반경 내 개수' 대신 자치구 전체 개수. 매물 좌표가 생기면 위도·경도로 반경 집계."""
    df = read_table(store_csv, must="상권업종", usecols=lambda c: "소분류명" in c or "시군구명" in c)  # 300MB라 두 컬럼만
    sub = df[col(df, "소분류명")].fillna("")
    hit = df[sub.str.contains("|".join(AMENITY_KEYWORDS))]
    return hit.groupby(col(df, "시군구명")).size()


def _minmax(s: pd.Series) -> pd.Series:
    rng = s.max() - s.min()
    return (s - s.min()) / rng if rng else s * 0


def score_regions(df: pd.DataFrame, budget: float, max_commute: float,
                  weights: dict[str, float] = DEFAULT_WEIGHTS) -> pd.DataFrame:
    """df: region, pred_rent, commute_min, amenity_cnt. 예산/통학 초과 지역은 제외."""
    ok = df[(df.pred_rent <= budget) & (df.commute_min <= max_commute)].copy()
    ok["score"] = (
        weights["rent"] * (1 - _minmax(ok.pred_rent))
        + weights["commute"] * (1 - _minmax(ok.commute_min))
        + weights["amenity"] * _minmax(ok.amenity_cnt)
    )
    return ok.sort_values("score", ascending=False).reset_index(drop=True)


def tradeoff_suggestions(df: pd.DataFrame, budget: float, max_commute: float,
                         extra_minutes=(10, 20)) -> list[dict]:
    """'통학 N분만 양보하면 월 X만원 절약' 제안."""
    base = df[(df.pred_rent <= budget) & (df.commute_min <= max_commute)]
    if base.empty:
        return []
    base_rent = base.pred_rent.min()
    out = []
    for m in extra_minutes:
        alt = df[(df.pred_rent <= budget) & (df.commute_min <= max_commute + m)]
        saving = base_rent - alt.pred_rent.min()
        if saving > 0:
            best = alt.loc[alt.pred_rent.idxmin(), "region"]
            out.append({"extra_minutes": m, "monthly_saving": round(float(saving), 1), "region": best})
    return out


def train_ltr(X: pd.DataFrame, y: pd.Series, group_sizes: list[int]):
    """선호 데이터가 생기면 사용. group_sizes = 사용자(쿼리)별 후보 수."""
    import lightgbm as lgb
    model = lgb.LGBMRanker(objective="lambdarank", n_estimators=200)
    model.fit(X, y, group=group_sizes)
    return model
