"""공공데이터 CSV 공통 읽기. 파일마다 인코딩(cp949/utf-8)과 위쪽 안내문 줄 수가 달라서 한 곳에서 처리한다."""
from __future__ import annotations

import io
from pathlib import Path

import pandas as pd


def read_table(path, must: str = "", **read_csv_kw) -> pd.DataFrame:
    """`must`가 처음 들어간 줄을 헤더로 읽는다(국토부 파일은 위에 안내문이 있음). 천 단위 쉼표는 숫자로."""
    raw = Path(path).read_bytes()
    for enc in ("utf-8-sig", "cp949"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError(f"{path}: utf-8/cp949 둘 다 아님")
    lines = text.splitlines()
    start = next((i for i, line in enumerate(lines) if must in line), 0)
    return pd.read_csv(io.StringIO("\n".join(lines[start:])), thousands=",", **read_csv_kw)


def col(df: pd.DataFrame, key: str) -> str:
    """이름에 key가 들어간 첫 컬럼. 공공데이터는 버전마다 '(만원)', '(㎡)' 같은 꼬리가 달라서."""
    for c in df.columns:
        if key in c:
            return c
    raise KeyError(f"'{key}' 들어간 컬럼 없음: {list(df.columns)}")
