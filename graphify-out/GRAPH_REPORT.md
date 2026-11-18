# Graph Report - 내프로젝트  (2026-11-18)

## Corpus Check
- 22 files · ~6,832 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 9 file(s) not represented in the graph (top: .csv 5, (none) 3, .toml 1)

## Summary
- 183 nodes · 306 edges · 19 communities (9 shown, 10 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 21 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- test_core.py
- AI 자취방 추천 서비스 — 제안서 초안 (팀 KKC)
- SubwayGraph
- rank.py
- model.py
- KKC · AI 자취방 추천 서비스 — Claude 작업 규칙
- KKC · AI 자취방 추천 서비스
- .claude/CLAUDE.md
- install-plugins.sh script
- streamlit_app.py
- test_pipeline.py

## God Nodes (most connected - your core abstractions)
1. `read_table()` - 13 edges
2. `load_seoul_metro()` - 13 edges
3. `col()` - 10 edges
4. `SubwayGraph` - 9 edges
5. `load_rent()` - 8 edges
6. `region_rents()` - 8 edges
7. `train()` - 8 edges
8. `load_station_coords()` - 8 edges
9. `AI 자취방 추천 서비스 — 제안서 초안 (팀 KKC)` - 7 edges
10. `price_gap()` - 6 edges

## Surprising Connections (you probably didn't know these)
- `다음 할 일` --references--> `SubwayGraph`  [INFERRED]
  README.md → src/kkc/commute/subway.py
- `다음 할 일` --references--> `train()`  [INFERRED]
  README.md → src/kkc/price/model.py
- `test_read_table_skips_notice_and_cp949()` --calls--> `read_table()`  [INFERRED]
  tests/test_pipeline.py → src/kkc/data.py
- `test_amenity_counts()` --calls--> `amenity_counts()`  [INFERRED]
  tests/test_pipeline.py → src/kkc/ranking/rank.py
- `load()` --calls--> `load_fov_model()`  [INFERRED]
  app/streamlit_app.py → src/kkc/vision/fov.py

## Import Cycles
- None detected.

## Communities (19 total, 10 thin omitted)

### Community 0 - "test_core.py"
Cohesion: 0.11
Nodes (13): build_model(), crop_ratio(), exif_fov(), fov_from_focal_35mm(), load_fov_model(), predict_fov(), restore_standard_view(), _to_tensor() (+5 more)

### Community 1 - "AI 자취방 추천 서비스 — 제안서 초안 (팀 KKC)"
Cohesion: 0.11
Nodes (18): 1. 프로젝트 요약, 2. 목적 및 필요성, 3. 프로젝트 개요, 4. 기대효과 및 활용 방안, 5. 구현 계획 (초안), AI 자취방 추천 서비스 — 제안서 초안 (팀 KKC), 경쟁 서비스 비교, 기획 의도 (+10 more)

### Community 2 - "SubwayGraph"
Cohesion: 0.19
Nodes (5): load_seoul_metro(), _minutes(), region_commute(), SubwayGraph, test_dijkstra_with_transfer()

### Community 3 - "rank.py"
Cohesion: 0.10
Nodes (12): _line(), load_station_coords(), nearest_station(), _station(), col(), read_table(), amenity_counts(), _minmax() (+4 more)

### Community 4 - "model.py"
Cohesion: 0.16
Nodes (11): 다음 할 일, converted_rent(), _prep(), price_gap(), region_deal_stats(), region_rents(), train(), _fake_rents() (+3 more)

### Community 5 - "KKC · AI 자취방 추천 서비스 — Claude 작업 규칙"
Cohesion: 0.33
Nodes (5): graphify, KKC · AI 자취방 추천 서비스 — Claude 작업 규칙, 규칙, 이 프로젝트, 적용된 플러그인 (project scope, `.claude/settings.json`)

### Community 6 - "KKC · AI 자취방 추천 서비스"
Cohesion: 0.33
Nodes (5): Claude Code 플러그인, KKC · AI 자취방 추천 서비스, 구조, 빠른 시작, 실제 데이터 넣기

### Community 15 - "streamlit_app.py"
Cohesion: 0.11
Nodes (5): deposit_text(), geocode(), load(), price_text(), won()

### Community 17 - "test_pipeline.py"
Cohesion: 0.20
Nodes (11): load_rent(), _photo(), test_amenity_counts(), test_exif_fov(), test_load_rent(), test_load_rent_seoul_format(), test_load_seoul_metro(), test_read_table_skips_notice_and_cp949() (+3 more)

## Knowledge Gaps
- **10 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `SubwayGraph` connect `SubwayGraph` to `rank.py`, `model.py`?**
  _High betweenness centrality (0.058) - this node is a cross-community bridge._
- **Are the 5 inferred relationships involving `load_seoul_metro()` (e.g. with `_minutes()` and `.add_segment()`) actually correct?**
  _`load_seoul_metro()` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Should `test_core.py` be split into smaller, more focused modules?**
  _Cohesion score 0.10837438423645321 - nodes in this community are weakly interconnected._
- **Why does `다음 할 일` connect `model.py` to `SubwayGraph`, `KKC · AI 자취방 추천 서비스`?**
  _High betweenness centrality (0.054) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `SubwayGraph` (e.g. with `다음 할 일` and `test_dijkstra_with_transfer()`) actually correct?**
  _`SubwayGraph` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Should `AI 자취방 추천 서비스 — 제안서 초안 (팀 KKC)` be split into smaller, more focused modules?**
  _Cohesion score 0.10526315789473684 - nodes in this community are weakly interconnected._
- **Why does `load_seoul_metro()` connect `SubwayGraph` to `test_pipeline.py`, `rank.py`?**
  _High betweenness centrality (0.048) - this node is a cross-community bridge._