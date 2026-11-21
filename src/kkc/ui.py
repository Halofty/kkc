"""화면 문구 도우미 (Streamlit 없이 테스트 가능하게 분리)."""


def gap_label(gap: float, tol: float = 0.5) -> tuple[str, str]:
    """매물 환산월세 - 예측 시세(만원) → (배지 문구, 톤 good/bad/neutral). ±tol 안은 비슷하다고 본다."""
    if gap < -tol:
        return f"시세보다 {-gap:.1f}만 원 싸요", "good"
    if gap > tol:
        return f"시세보다 {gap:.1f}만 원 비싸요", "bad"
    return "시세와 비슷해요", "neutral"
