# data/n5/ — N5 운영 데이터

> 세션 4 수진 v2 plan 승인 후 생성·갱신 예정.

## 예정 파일 (decision_log 2026-06-06 E-13)

### `n5_master.xlsx` (5 시트)
| 시트 | 내용 |
|---|---|
| `master_list` | 110 base 항목 (수진 v1 105 + E-12 5건 추가) |
| `taxonomy_def` | L1 9그룹 + L2 소분류 정의 |
| `l3_assignment` | 항목별 L3 메타 태그 매트릭스 |
| `border_meta` | BORDER 21항목 상세 (이유 + N5 범위 + N4 심화) |
| `variant_chunks` | E-11 variant 3건 (`_informal` / `_keisiki` / `_alt`) |

### `n5_comparison.xlsx` (2 시트)
| 시트 | 내용 |
|---|---|
| `comparison_pairs` | 22쌍 (E-5 -1, E-6 -1 적용) + ★ + 클러스터 |
| `comparison_chunks` | 각 쌍 본문 + 예문 + embedding_text |

## 작성자
- 수진 (`de_sujin`) — 세션 4 v2 plan 정빈님 승인 후
- 헤더 명세는 `docs/planning/session_3/jp_tsukuya/07_pre_v2_check.md` §2-⑤ 참조 + `data/schema/n5_*_schema.md` 신설

## 변경 정책
- 데이터 수정 = xlsx 직접 편집 (운영자 = 정빈님)
- 데이터 추가 = 수진 (도메인 책임자)
- 검수 = 츠쿠야 (`jp_tsukuya`) — 세션 4 재검수 단계
