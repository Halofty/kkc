"""지하철 그래프 + 다익스트라로 통학 시간 계산.

데이터: 서울교통공사 역간거리·운행시간(1~8호선), 환승역거리 소요시간(환승역 145곳).
노드 = (역명, 호선). 같은 역의 다른 호선끼리는 환승 시간으로 연결한다.
"""
from __future__ import annotations

import heapq
from collections import defaultdict

import pandas as pd

from kkc.data import col, read_table

Node = tuple[str, str]  # (역명, 호선)

# 자치구 → 대표역(구청·중심 상권 근처, 서울교통공사 1~8호선 구간). 지역 통학 시간 = 대표역까지 시간.
# 지선 첫 역 → 실제로 갈라지는 역. 역간 파일은 지선을 본선 끝에 이어 적어서 그대로 이으면 틀린다.
BRANCH_FROM = {("2", "용답"): "성수", ("2", "도림천"): "신도림", ("5", "둔촌동"): "강동"}
# 같은 역인데 파일·호선마다 이름이 다른 곳 (4호선 총신대입구 = 7호선 이수, 좌표 파일의 옛 역명 뚝섬유원지 = 자양).
ALIAS = {"이수": "총신대입구", "신내역": "신내", "뚝섬유원지": "자양"}
# shortcut: 구 안의 역이 여러 개여도 한 역만 봄. 구별 역 목록 데이터가 생기면 구 안 역들의 최솟값으로.
GU_STATION = {
    "종로구": "종로3가", "중구": "시청", "용산구": "삼각지", "성동구": "왕십리", "광진구": "건대입구",
    "동대문구": "청량리", "중랑구": "상봉", "성북구": "성신여대입구", "강북구": "미아사거리", "도봉구": "창동",
    "노원구": "노원", "은평구": "연신내", "서대문구": "신촌", "마포구": "합정", "양천구": "오목교",
    "강서구": "발산", "구로구": "신도림", "금천구": "가산디지털단지", "영등포구": "영등포구청", "동작구": "총신대입구",
    "관악구": "서울대입구", "서초구": "교대", "강남구": "강남", "송파구": "잠실", "강동구": "천호",
}


def _minutes(v) -> float:
    """'2:30'(분:초) 또는 2.5 → 분."""
    s = str(v).strip()
    if ":" in s:
        m, sec = s.split(":")[-2:]
        return int(m) + int(sec) / 60
    return float(s)


def _line(s: pd.Series) -> pd.Series:
    return s.astype(str).str.extract(r"(\d+)")[0]  # "2호선" / "2" → "2"


def _station(s: pd.Series) -> pd.Series:
    return s.astype(str).str.replace(r"\(.*\)", "", regex=True).str.strip().replace(ALIAS)  # "사당(대림)" → "사당"


def load_seoul_metro(dist_csv, transfer_csv) -> "SubwayGraph":
    """서울교통공사 '역간거리 및 소요시간' + '환승역거리 소요시간 정보' CSV → 그래프.
    역간 파일은 호선별로 역이 순서대로 나열되고, 각 행의 시간 = 앞 역에서 이 역까지."""
    g = SubwayGraph()
    d = read_table(dist_csv, must="역명")
    line, name = _line(d[col(d, "호선")]), _station(d[col(d, "역명")])
    t = d[col(d, "시간")].map(_minutes)
    for i in range(1, len(d)):
        if line.iat[i] == line.iat[i - 1]:
            prev = BRANCH_FROM.get((line.iat[i], name.iat[i]), name.iat[i - 1])
            g.add_segment(line.iat[i], prev, name.iat[i], t.iat[i])
    tr = read_table(transfer_csv, must="환승")
    a, b = _line(tr[col(tr, "호선")]), _line(tr[col(tr, "노선")])
    st, tt = _station(tr[col(tr, "역명")]), tr[col(tr, "시간")].map(_minutes)
    for i in range(len(tr)):
        if pd.isna(a.iat[i]) or pd.isna(b.iat[i]):  # 공항철도·경의중앙선 등 1~8호선 밖 노선은 그래프에 없음
            continue
        g.add_transfer(st.iat[i], a.iat[i], b.iat[i], tt.iat[i])
    return g


def load_station_coords(csv) -> pd.DataFrame:
    """서울교통공사 '1_8호선 역사 좌표(위경도)' CSV → 역명 index, lat/lon 컬럼. 환승역은 호선마다 적혀 있어 평균."""
    d = read_table(csv, must="위도")
    name = _station(d[col(d, "역명")]).replace({"서울": "서울역"})  # 좌표 파일은 '서울', 역간 파일은 '서울역'
    return pd.DataFrame({"station": name, "lat": d[col(d, "위도")], "lon": d[col(d, "경도")]}).groupby("station").mean()


WALK_M_PER_MIN = 67  # 시속 4km


def nearest_station(lat: float, lon: float, coords: pd.DataFrame) -> tuple[str, float]:
    """가장 가까운 역과 도보 분. 거리 = 직선 × 1.3(골목 우회). 서울 위도에서 위도 1° ≈ 111km, 경도 1° ≈ 88km."""
    m = (((coords.lat - lat) * 111_000) ** 2 + ((coords.lon - lon) * 88_000) ** 2) ** 0.5
    return m.idxmin(), float(m.min() * 1.3 / WALK_M_PER_MIN)


def region_commute(g: "SubwayGraph", dest_station: str) -> dict[str, float]:
    """자치구별 목적지(통학역)까지 분. 대표역이 그래프에 없으면 NaN."""
    t = g.times_from(dest_station)
    return {gu: t.get(s, float("nan")) for gu, s in GU_STATION.items()}


class SubwayGraph:
    def __init__(self) -> None:
        self.adj: dict[Node, list[tuple[Node, float]]] = defaultdict(list)

    def add_segment(self, line: str, a: str, b: str, minutes: float) -> None:
        """같은 호선의 인접 역 (양방향)."""
        u, v = (a, line), (b, line)
        self.adj[u].append((v, minutes))
        self.adj[v].append((u, minutes))

    def add_transfer(self, station: str, line_a: str, line_b: str, minutes: float) -> None:
        u, v = (station, line_a), (station, line_b)
        self.adj[u].append((v, minutes))
        self.adj[v].append((u, minutes))

    def nodes_of(self, station: str) -> list[Node]:
        return [n for n in self.adj if n[0] == station]

    def times_from(self, station: str) -> dict[str, float]:
        """출발역(모든 호선)에서 각 역까지 최소 소요시간(분)."""
        dist: dict[Node, float] = {}
        pq = [(0.0, n) for n in self.nodes_of(station)]
        heapq.heapify(pq)
        while pq:
            d, u = heapq.heappop(pq)
            if u in dist:
                continue
            dist[u] = d
            for v, w in self.adj[u]:
                if v not in dist:
                    heapq.heappush(pq, (d + w, v))
        best: dict[str, float] = {}
        for (name, _), d in dist.items():
            best[name] = min(d, best.get(name, float("inf")))
        return best
