# Graph Report - 내프로젝트  (2026-11-26)

## Corpus Check
- 25 files · ~11,192 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 4 file(s) not represented in the graph (top: (none) 3, .toml 1)

## Summary
- 234 nodes · 410 edges · 22 communities (11 shown, 11 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 25 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `cb4c0789`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_core.py
- AI 자취방 추천 서비스 — 제안서 초안 (팀 KKC)
- SubwayGraph
- test_pipeline.py
- pandas
- KKC · AI 자취방 추천 서비스 — Claude 작업 규칙
- unsplash_listings.py
- .claude/CLAUDE.md
- install-plugins.sh script
- streamlit_app.py
- ui.py
- read_table
- build_data.py
- KKC · AI 자취방 추천 서비스

## God Nodes (most connected - your core abstractions)
1. `read_table()` - 13 edges
2. `load_seoul_metro()` - 13 edges
3. `col()` - 10 edges
4. `SubwayGraph` - 9 edges
5. `fill_pools()` - 8 edges
6. `load_rent()` - 8 edges
7. `load_station_coords()` - 8 edges
8. `region_rents()` - 8 edges
9. `train()` - 8 edges
10. `room_thumb()` - 7 edges

## Surprising Connections (you probably didn't know these)
- `다음 할 일` --references--> `SubwayGraph`  [INFERRED]
  README.md → src/kkc/commute/subway.py
- `다음 할 일` --references--> `train()`  [INFERRED]
  README.md → src/kkc/price/model.py
- `load()` --calls--> `load_fov_model()`  [INFERRED]
  app/streamlit_app.py → src/kkc/vision/fov.py
- `rank_view()` --calls--> `converted_rent()`  [INFERRED]
  app/streamlit_app.py → src/kkc/price/model.py
- `compare_listings()` --calls--> `score_regions()`  [INFERRED]
  app/streamlit_app.py → src/kkc/ranking/rank.py

## Import Cycles
- None detected.

## Communities (22 total, 11 thin omitted)

### Community 0 - "test_core.py"
Cohesion: 0.12
Nodes (13): build_model(), crop_ratio(), exif_fov(), fov_from_focal_35mm(), load_fov_model(), predict_fov(), restore_standard_view(), _to_tensor() (+5 more)

### Community 1 - "AI 자취방 추천 서비스 — 제안서 초안 (팀 KKC)"
Cohesion: 0.11
Nodes (18): 1. 프로젝트 요약, 2. 목적 및 필요성, 3. 프로젝트 개요, 4. 기대효과 및 활용 방안, 5. 구현 계획 (초안), AI 자취방 추천 서비스 — 제안서 초안 (팀 KKC), 경쟁 서비스 비교, 기획 의도 (+10 more)

### Community 2 - "SubwayGraph"
Cohesion: 0.14
Nodes (7): _line(), load_seoul_metro(), _minutes(), region_commute(), _station(), SubwayGraph, test_dijkstra_with_transfer()

### Community 3 - "test_pipeline.py"
Cohesion: 0.26
Nodes (7): nearest_station(), _photo(), test_exif_fov(), test_load_seoul_metro(), test_station_coords_and_nearest(), test_subway_branch_and_alias(), test_train_and_predict_fov_smoke()

### Community 4 - "pandas"
Cohesion: 0.13
Nodes (15): compare_listings(), 다음 할 일, converted_rent(), load_rent(), _prep(), price_gap(), region_deal_stats(), region_rents() (+7 more)

### Community 5 - "KKC · AI 자취방 추천 서비스 — Claude 작업 규칙"
Cohesion: 0.33
Nodes (5): graphify, KKC · AI 자취방 추천 서비스 — Claude 작업 규칙, 규칙, 이 프로젝트, 적용된 플러그인 (project scope, `.claude/settings.json`)

### Community 6 - "unsplash_listings.py"
Cohesion: 0.19
Nodes (8): api_get(), build_listings(), download_file(), fill_pools(), load_manifest(), main(), RateLimited, save_manifest()

### Community 15 - "streamlit_app.py"
Cohesion: 0.08
Nodes (14): deposit_text(), esc(), geocode(), img_b64(), leaflet_map(), map_css(), map_data(), photo_src() (+6 more)

### Community 16 - "ui.py"
Cohesion: 0.28
Nodes (4): gap_label(), pick_photo(), test_gap_label_cheaper_pricier_similar(), test_pick_photo_by_room_cycles_and_falls_back()

### Community 17 - "read_table"
Cohesion: 0.11
Nodes (12): rank_view(), load_station_coords(), col(), read_table(), dong_table(), _minmax(), score_regions(), tradeoff_suggestions() (+4 more)

### Community 21 - "KKC · AI 자취방 추천 서비스"
Cohesion: 0.33
Nodes (5): Claude Code 플러그인, KKC · AI 자취방 추천 서비스, 구조, 빠른 시작, 실제 데이터 넣기

## Knowledge Gaps
- **11 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `SubwayGraph` connect `SubwayGraph` to `pandas`?**
  _High betweenness centrality (0.047) - this node is a cross-community bridge._
- **Are the 5 inferred relationships involving `load_seoul_metro()` (e.g. with `_minutes()` and `.add_segment()`) actually correct?**
  _`load_seoul_metro()` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Should `test_core.py` be split into smaller, more focused modules?**
  _Cohesion score 0.12333333333333334 - nodes in this community are weakly interconnected._
- **Why does `다음 할 일` connect `pandas` to `SubwayGraph`, `KKC · AI 자취방 추천 서비스`?**
  _High betweenness centrality (0.045) - this node is a cross-community bridge._
- **Should `AI 자취방 추천 서비스 — 제안서 초안 (팀 KKC)` be split into smaller, more focused modules?**
  _Cohesion score 0.10526315789473684 - nodes in this community are weakly interconnected._
- **Why does `load_seoul_metro()` connect `SubwayGraph` to `read_table`, `test_pipeline.py`, `pandas`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **Should `SubwayGraph` be split into smaller, more focused modules?**
  _Cohesion score 0.14285714285714285 - nodes in this community are weakly interconnected._