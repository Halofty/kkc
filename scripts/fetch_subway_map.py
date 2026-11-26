#!/usr/bin/env python3
"""지도에 그릴 서울 지하철 1~9호선 실제 선로 모양 + 역 이름을 OpenStreetMap(Overpass API)에서 받는다.

사용법: python scripts/fetch_subway_map.py   (키 필요 없음, 1~2분)
결과: data/processed/subway_map.json — 앱이 있으면 지도에 호선을 그린다. 데이터 출처 © OpenStreetMap 기여자 (ODbL).
"""
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from kkc.commute.subway import osm_subway_map  # noqa: E402

OUT = ROOT / "data/processed/subway_map.json"
QUERY = """[out:json][timeout:250];
area["ISO3166-2"="KR-11"]->.a;
rel(area.a)["route"="subway"]["ref"~"^[1-9]$"]->.r;
.r out geom;
node(r.r)["railway"="stop"];
out;"""


SERVERS = ["https://overpass-api.de/api/interpreter",  # 공용 서버가 자주 바빠서(502·504) 미러를 차례로 시도
           "https://overpass.kumi.systems/api/interpreter",
           "https://maps.mail.ru/osm/tools/overpass/api/interpreter"]


def fetch():
    for url in SERVERS:
        req = urllib.request.Request(url, data=urllib.parse.urlencode({"data": QUERY}).encode(),
                                     headers={"User-Agent": "kkc-subway-map/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                return json.load(r)["elements"]
        except (urllib.error.URLError, TimeoutError) as e:
            print(f"  {url.split('/')[2]} 실패 ({e}), 다음 서버로...")
    sys.exit("❌ Overpass 서버가 모두 응답하지 않습니다. 잠시 뒤 다시 실행하세요.")


def main():
    print("OpenStreetMap에서 1~9호선 선로를 받는 중... (1~2분)")
    m = osm_subway_map(fetch())
    if not m["lines"]:
        sys.exit("❌ 선로를 하나도 못 받았습니다. 잠시 뒤 다시 실행하세요 (Overpass 서버가 바쁠 수 있음).")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(m, ensure_ascii=False), encoding="utf-8")
    print(f"✅ 호선 {len(m['lines'])}개, 역 {len(m['stations'])}곳 → {OUT}")


if __name__ == "__main__":
    main()
