"""버스 + 지하철 통학 시간 (방향 있는 그래프 + 다익스트라).

데이터: 서울시 버스노선별 정류소정보(노선·순번·정류장·좌표), TOPIS 노선별 정류장 구간 평균 운행시간(초, 시간대별),
노선별 정류장별 버스 운행횟수(시간대별). 출근 시간대(평일 7~8시) 값을 쓴다.

노드
  (역, 호선)          지하철 (SubwayGraph 그대로)
  ("S", 정류장)        정류장에 서 있는 상태
  ("R", 노선, 순번)    그 노선 버스를 타고 순번 정류장에 있는 상태
간선: 정류장 → 버스 = 기다리는 시간, 버스 → 다음 순번 = 구간 운행시간, 버스 → 정류장 = 0(하차),
      가까운 정류장끼리·정류장↔역 = 걸어서 환승 (역은 개찰구 시간 추가). 버스는 노선 방향으로만 간다.
"""
from __future__ import annotations

import heapq
from collections import defaultdict

import numpy as np
import pandas as pd

from kkc.commute.subway import WALK_M_PER_MIN, SubwayGraph, _km

LINK_M = 200  # 이 거리 안의 정류장끼리, 정류장 ↔ 역은 걸어서 갈아탄다
ACCESS_MIN = 15  # 집·목적지에서 정류장·역까지 걸을 수 있는 최대 시간
ENTER_MIN, EXIT_MIN = 3, 2  # 정류장 ↔ 역: 개찰구·계단 (이게 없으면 역 밖 정류장을 거쳐 공식 환승 시간을 건너뛴다)
DETOUR = 1.3  # 직선 거리 → 실제 걷는 거리 (골목 우회), subway.nearest_station 과 같은 값
WEEKDAY_RUSH = ["07시", "08시"]


def walk_minutes(km):
    return km * 1000 * DETOUR / WALK_M_PER_MIN


def wait_minutes(buses_per_hour: float) -> float:
    """정류장 평균 대기 = 배차 간격의 절반, 1~15분."""
    return float(np.clip(30 / buses_per_hour, 1, 15)) if buses_per_hour > 0 else 15.0


def ride_minutes(seconds: float, km: float) -> float:
    """구간 실측 운행시간(초) → 분. 종점 대기가 섞여 터무니없이 긴 구간은 시속 8km로 자른다."""
    # shortcut: 종점 대기 판단을 속도 하한(8km/h)으로만 함. 회차 정류장 정보를 쓰면 더 정확.
    return min(seconds / 60, km / 8 * 60)


class TransitGraph:
    def __init__(self, subway: SubwayGraph, coords: pd.DataFrame) -> None:
        self.adj: dict = defaultdict(list)
        for u, nbrs in subway.adj.items():
            self.adj[u].extend(nbrs)
        rows = [(n, coords.lat[n[0]], coords.lon[n[0]]) for n in list(subway.adj) if n[0] in coords.index]
        self.points = pd.DataFrame(rows, columns=["node", "lat", "lon"])  # 걸어서 타고 내릴 수 있는 곳 (역·정류장)

    def add_bus(self, stops: pd.DataFrame, ride_min: dict, wait_min: dict, default_wait: float = 8.0) -> None:
        """stops: route, seq, stop, lat, lon (노선별 정류장 순서). ride_min[(노선, 순번)] = 다음 순번까지 분 (없으면 거리로),
        wait_min[(노선, 정류장)] = 대기 분."""
        for route, g in stops.sort_values(["route", "seq"]).groupby("route", sort=False):
            prev = None
            for r in g.itertuples(index=False):
                ride, stop = ("R", route, r.seq), ("S", r.stop)
                self.adj[stop].append((ride, wait_min.get((route, r.stop), default_wait)))
                self.adj[ride].append((stop, 0.0))
                if prev is not None:
                    km = _km(prev.lat, prev.lon, r.lat, r.lon)
                    self.adj[("R", route, prev.seq)].append((ride, ride_min.get((route, prev.seq), km / 15 * 60)))
                prev = r
        new = stops.drop_duplicates("stop")
        self.points = pd.concat([self.points, pd.DataFrame(
            {"node": [("S", s) for s in new.stop], "lat": new.lat.values, "lon": new.lon.values})], ignore_index=True)

    def link_walks(self, max_m: float = LINK_M) -> None:
        """가까운 정류장끼리, 정류장 ↔ 역을 도보 간선으로 잇는다 (역끼리는 지하철 환승 데이터가 이미 있음)."""
        lat, lon = self.points.lat.to_numpy(), self.points.lon.to_numpy()
        is_bus = np.array([n[0] == "S" for n in self.points.node])
        nodes = self.points.node.tolist()
        for i in np.flatnonzero(is_bus):
            d = _km(lat, lon, lat[i], lon[i])
            for j in np.flatnonzero((d * 1000 <= max_m) & (np.arange(len(d)) != i)):
                w = walk_minutes(d[j])
                if is_bus[j]:
                    self.adj[nodes[i]].append((nodes[j], w))  # 정류장끼리 (반대 방향은 j 차례에 들어간다)
                else:
                    self.adj[nodes[i]].append((nodes[j], w + ENTER_MIN))
                    self.adj[nodes[j]].append((nodes[i], w + EXIT_MIN))

    def access(self, lat: float, lon: float, route=None, k: int = 15) -> dict:
        """(lat, lon)에서 걸어서 ACCESS_MIN 안에 닿는 역·정류장 {노드: 도보 분}. 직선으로 가까운 k곳 중에서 고른다.
        route(lat, lon, [(lat, lon), ...]) → 도보 m 를 주면 실제 걷는 길로 잰다 (산·철길 너머를 고르지 않게)."""
        d = pd.Series(_km(self.points.lat.to_numpy(), self.points.lon.to_numpy(), lat, lon), index=self.points.index)
        near = self.points.loc[d.nsmallest(k).index]
        mins = walk_minutes(d[near.index])
        if route is not None:
            xy = near[["lat", "lon"]].drop_duplicates()
            try:
                m = dict(zip(map(tuple, xy.to_numpy()), route(lat, lon, list(map(tuple, xy.to_numpy())))))
                mins = pd.Series([m[(a, b)] / WALK_M_PER_MIN for a, b in zip(near.lat, near.lon)], index=near.index)
            except (OSError, ValueError, KeyError):
                pass  # 경로를 못 받으면 직선 × 1.3
        ok = mins <= ACCESS_MIN
        pick = mins[ok] if ok.any() else mins.nsmallest(1)
        return {near.node[i]: float(pick[i]) for i in pick.index}

    def times_to(self, egress: dict) -> dict:
        """egress {노드: 목적지까지 도보 분} → 모든 노드에서 목적지까지 최소 분 (역방향 다익스트라)."""
        if not hasattr(self, "_radj"):
            self._radj = defaultdict(list)
            for u, nbrs in self.adj.items():
                for v, w in nbrs:
                    self._radj[v].append((u, w))
        dist: dict = {}
        pq = [(w, n) for n, w in egress.items()]
        heapq.heapify(pq)
        while pq:
            d, u = heapq.heappop(pq)
            if u in dist:
                continue
            dist[u] = d
            for v, w in self._radj[u]:
                if v not in dist:
                    heapq.heappush(pq, (d + w, v))
        return dist

    def time_from(self, lat: float, lon: float, to: dict, extra: dict | None = None) -> float:
        """(lat, lon)에서 출발해 목적지까지 분 = min(걸어서 닿는 역·정류장까지 도보 + 거기서 목적지까지). extra로 출발점을 더 줄 수 있다."""
        acc = {**self.access(lat, lon), **(extra or {})}
        best = min((w + to[n] for n, w in acc.items() if n in to), default=float("nan"))
        return float(best)

    def __getstate__(self):
        return {k: v for k, v in self.__dict__.items() if k != "_radj"}  # 역방향 인접 목록은 불러온 뒤 다시 만든다


def load_bus(route_xlsx, speed_csv, turn_csv, weekdays=None) -> tuple[pd.DataFrame, dict, dict]:
    """세 파일 → (stops, ride_min, wait_min). 평일 7~8시 평균. weekdays: 쓸 기준_날짜 목록 (없으면 토·일 뺀 전부)."""
    rs = pd.read_excel(route_xlsx)
    stops = pd.DataFrame({"route": rs.ROUTE_ID, "seq": rs["순번"], "stop": rs.NODE_ID, "lat": rs["Y좌표"], "lon": rs["X좌표"]})
    stops = stops.dropna().query("lat > 37 and lon > 126")  # 좌표 0 같은 깨진 행 제외

    def rush(df, prefix):
        dates = pd.to_datetime(df["기준_날짜"].astype(str), format="%Y%m%d")
        df = df[dates.dt.dayofweek < 5] if weekdays is None else df[df["기준_날짜"].isin(weekdays)]
        cols = [f"{prefix}_{h}" for h in WEEKDAY_RUSH]
        return df.assign(v=df[cols].replace(0, np.nan).mean(axis=1))

    sp = pd.read_csv(speed_csv, encoding="cp949", usecols=["기준_날짜", "노선_ID", "출발_정류장_순서", "운행시간_07시", "운행시간_08시"])
    sec = rush(sp, "운행시간").groupby(["노선_ID", "출발_정류장_순서"]).v.mean().dropna()
    xy = stops.set_index(["route", "seq"])[["lat", "lon"]]
    nxt = xy.groupby(level=0).shift(-1)  # 다음 순번 정류장 좌표
    km = pd.Series(_km(xy.lat, xy.lon, nxt.lat, nxt.lon), index=xy.index).dropna()
    sec = sec[sec.index.isin(km.index)]
    ride_min = {k: ride_minutes(s, km[k]) for k, s in sec.items()}

    hr = pd.read_csv(turn_csv, encoding="cp949", usecols=["기준_날짜", "노선_ID", "정류장_ID", "버스운행횟수_07시", "버스운행횟수_08시"])
    per_hour = rush(hr, "버스운행횟수").groupby(["노선_ID", "정류장_ID"]).v.mean().dropna()
    wait_min = {k: wait_minutes(n) for k, n in per_hour.items()}
    return stops, ride_min, wait_min
