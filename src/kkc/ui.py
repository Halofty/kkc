"""화면 문구 도우미 (Streamlit 없이 테스트 가능하게 분리)."""


def gap_label(gap: float, tol: float = 0.5) -> tuple[str, str]:
    """매물 환산월세 - 예측 시세(만원) → (배지 문구, 톤 good/bad/neutral). ±tol 안은 비슷하다고 본다."""
    if gap < -tol:
        return f"시세보다 {-gap:.1f}만 원 싸요", "good"
    if gap > tol:
        return f"시세보다 {gap:.1f}만 원 비싸요", "bad"
    return "시세와 비슷해요", "neutral"


def tradeoff_lines(suggestions: list[dict]) -> list[str]:
    """tradeoff_suggestions 결과 → 화면 문구. 더 양보해도 같은 동네면 중복이라 뺀다."""
    out, seen = [], set()
    for s in suggestions:
        if s["region"] in seen:
            continue
        seen.add(s["region"])
        out.append(f"통학 {s['extra_minutes']}분만 양보하면 {s['region']}에서 월 {s['monthly_saving']:.1f}만 원 아낄 수 있어요")
    return out


# 정렬 항목 → (컬럼, 오름차순 이름, 내림차순 이름). 거리 = 통학 시간. 전세금은 전세일 때 보증금 칸.
SORTS = {"월세": ("rent_med", "낮은순", "높은순"), "보증금": ("deposit_med", "낮은순", "높은순"),
         "전세금": ("deposit_med", "낮은순", "높은순"), "거리": ("commute_min", "가까운순", "먼순"),
         "추천": ("rank", "높은순", "낮은순")}


def sort_regions(df, key: str, desc: bool = False):
    """정렬된 df와 '월세 낮은순' 같은 기준 문구. 같은 값이면 추천 순위로."""
    col, up, down = SORTS[key]
    by = [col] if col == "rank" else [col, "rank"]
    return df.sort_values(by, ascending=[not desc] + [True] * (len(by) - 1)), f"{key} {down if desc else up}"
