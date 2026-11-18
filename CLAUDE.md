# KKC · AI 자취방 추천 서비스 — Claude 작업 규칙

## 이 프로젝트
서울 자취방 추천 웹서비스 (인공지능프로그래밍 팀 프로젝트, 팀 KKC: 김태욱·김상혁·최한별).
전체 기획은 `docs/proposal.md` 참고.

| 모듈 | 담당 | 기술 |
|---|---|---|
| `src/kkc/price` | 김태욱 | Gradient Boosting 회귀 (전월세 실거래가 → 환산 월세 예측) |
| `src/kkc/ranking`, `app/` | 김상혁 | 가중합 베이스라인 → LightGBM LambdaRank, Streamlit |
| `src/kkc/vision` | 최한별 | EfficientNet-B0 전이학습 (화각 회귀) + 1x 시야 복원 |
| `src/kkc/commute` | 공통 | 지하철 그래프 다익스트라 (1~8호선, 환승역 145곳) |

## 적용된 플러그인 (project scope, `.claude/settings.json`)
- **superpowers** — 브레인스토밍 → 계획 → TDD → 리뷰 순서로 작업.
- **andrej-karpathy-skills** — 코딩 전에 생각, 단순하게, 필요한 곳만 고치기, 목표 중심.
- **i-have-adhd** — 답은 행동 먼저, 번호 매긴 단계, 곁가지 없이.
- **ponytail** — 필요한 최소 코드만. YAGNI, 표준 라이브러리 먼저.

## 규칙
1. 새 기능은 `tests/`에 테스트 먼저. `pytest -q`가 통과해야 완료.
2. 데이터 파일(`data/raw`, `data/processed`)은 커밋하지 않는다.
3. 화각 결과는 "허위 매물" 판정이 아니라 **참고 정보**로만 표시한다.
4. 숫자(시세·통계)는 출처와 기준 시점을 같이 적는다.
5. 답변은 한국어로.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- When graphify-out/graph.json exists, run `graphify query "<question>"` before your first grep, search or source-file read for a codebase question, and put this rule in every subagent prompt that explores code. Read raw files only for lines the graph or an earlier read already located. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. When the answer is under a Markdown heading, `graphify section "<heading>"` prints that section's text, so the .md need not be opened. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
- A committed graphify-out/graph.json is rewritten whole on every build, so a large diff to it in a pull request is expected. Do not flag it as churn or suggest skipping the graph rebuild or its hooks.
