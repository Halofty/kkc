"""화면 문구 도우미 (Streamlit 없이 테스트 가능하게 분리)."""


def gap_label(gap: float, tol: float = 0.5) -> tuple[str, str]:
    """매물 환산월세 - 예측 시세(만원) → (배지 문구, 톤 good/bad/neutral). ±tol 안은 비슷하다고 본다."""
    if gap < -tol:
        return f"시세보다 {-gap:.1f}만 원 싸요", "good"
    if gap > tol:
        return f"시세보다 {gap:.1f}만 원 비싸요", "bad"
    return "시세와 비슷해요", "neutral"


def pick_photo(manifest: dict, room: str, i: int) -> dict | None:
    """i번째 매물 썸네일용 Unsplash 사진 (원룸=main, 투룸=거실 living). 없으면 None."""
    photos = manifest.get("main" if room == "원룸" else "living") or []
    return photos[i % len(photos)] if photos else None
