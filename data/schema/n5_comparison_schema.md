# n5_comparison_schema.md — N5 비교쌍 xlsx 컬럼 명세

> 버전: v2.0 / 작성: de_sujin / 세션 4 / 2026-06-06
> 파일 경로: `data/n5/n5_comparison.xlsx`
> 결정 이력: E-5, E-7, E-8, E-9, E-10, E-16, 즉6, 즉7

---

## 개요

| 항목 | 내용 |
|------|------|
| 파일명 | n5_comparison.xlsx |
| 시트 수 | 2개 |
| 비교쌍 수 | 25쌍 |
| 클러스터 수 | 6개 (A~F) |

---

## Sheet 1: `comparison_pairs`

비교쌍 기본 정보 (25 rows).

| 컬럼명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| `compare_id` | string | ✓ | PK. 형식: `compare_n5_{LEFT}_{RIGHT}`. variant 포함 시 `_inf`, `_kei`, `_alt`, `_ta` 등 suffix. |
| `left_grammar_point_id` | string | ✓ | 좌측 항목 ID. FK → n5_master.xlsx: master_list 또는 variant_chunks. |
| `right_grammar_point_id` | string | ✓ | 우측 항목 ID. FK → n5_master.xlsx: master_list 또는 variant_chunks. |
| `cluster` | string | ✓ | 클러스터 구분. `A`, `B`, `C`, `D`, `E`, `F` 중 하나. |
| `star_weight` | string | ✓ | 혼동도·중요도. `1star`, `2star`, `3star` 중 하나. |
| `confusion_point` | string | ✓ | 혼동 요점 한 줄 요약. |

### 클러스터 정의

| 클러스터 | 테마 | 쌍 수 |
|---------|------|------|
| A | 조사 대조 (격·한정) | 6쌍 |
| B | 활용·표현 형태 대조 | 5쌍 |
| C | 시간·이유 접속 대조 | 4쌍 |
| D | 종조사·접속·병렬 대조 | 3쌍 |
| E | 시제·추측·설명 대조 | 4쌍 |
| F | E-12 신규 항목 관련 대조 (E-16) | 3쌍 |

### star_weight 기준

| 값 | 의미 |
|----|------|
| `3star` | N5 핵심 혼동 포인트. 학습자 오답률 높음. E-8에 의해 #4/#14 ★★★로 상향. |
| `2star` | 중요 혼동 포인트. 학습자 주의 필요. |
| `1star` | 기본 대조. 접속·격식 차이 등 경미한 혼동. |

### compare_id 패턴 특이사항

| compare_id | 설명 |
|-----------|------|
| `compare_n5_026_026inf` | 031_031i 패턴: base vs variant (E-7) |
| `compare_n5_035_035alt` | base vs variant (E-7) |
| `compare_n5_082_082kei` | base vs variant (E-7) |
| `compare_n5_031_031i` | ある vs いる — 동일 base ID의 自/他 대조 |
| `compare_n5_084_084i` | それから vs そして — 동일 base ID의 의미 대조 |
| `compare_n5_106_ta` | ほうがいい 辞書形 vs た形 — 同一 항목 内 接続形 대조 (E-16, 수진 판단) |

---

## Sheet 2: `comparison_chunks`

비교쌍 RAG 임베딩 데이터 (25 rows).

| 컬럼명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| `compare_id` | string | ✓ | PK. FK → comparison_pairs.compare_id. |
| `pair_label` | string | ✓ | 비교쌍 레이블. 형식: `{LEFT명} vs {RIGHT명}`. |
| `cluster` | string | ✓ | 클러스터 구분 (comparison_pairs와 동일). |
| `star_weight` | string | ✓ | 혼동도·중요도 (comparison_pairs와 동일). |
| `embedding_text` | string | ✓ | RAG 임베딩용 비교 요약 텍스트. 50~100자 권장. |

### embedding_text 작성 가이드

- **길이**: 50~100자 (compare chunk 기준)
- **구조**: `{LEFT} vs {RIGHT} — 핵심 차이 요약. 추가 메모.`
- **포함 필수**: 혼동 포인트 키워드, 접속 형태 차이(있는 경우)
- **E-7 variant 표기**: `E-7 variant.` 명시
- **E-16 신규 표기**: `E-16.` 명시
- **즉6 적용**: に/で 쌍 — "이동 도착점"으로 표기 (방향 아님)
- **즉7 적용**: だろう/でしょう 쌍 — "남성에서 더 자주 사용" (남성어 아님)

---

## 비교쌍 전체 목록 (25쌍)

### Cluster A — 조사 대조

| # | compare_id | 좌측 | 우측 | ★ |
|---|-----------|------|------|---|
| 1 | compare_n5_001_002 | は | が | ★★★ |
| 2 | compare_n5_004_005 | に | で | ★★★ |
| 3 | compare_n5_007_010 | と | や | ★★ |
| 4 | compare_n5_014_015 | だけ | しか〜ない | ★★★ |
| 5 | compare_n5_004_006 | に | へ | ★★ |
| 6 | compare_n5_011_012 | から | まで | ★★ |

### Cluster B — 활용·표현 형태 대조

| # | compare_id | 좌측 | 우측 | ★ |
|---|-----------|------|------|---|
| 7 | compare_n5_031_031i | ある | いる | ★★★ |
| 8 | compare_n5_032_033 | ほしい | たい | ★★★ |
| 9 | compare_n5_023_089 | ている | てある | ★★★ |
| 10 | compare_n5_026_026inf | てはいけない | ちゃいけない | ★ |
| 11 | compare_n5_035_035alt | なければならない | ないといけない | ★★ |

### Cluster C — 시간·이유 접속 대조

| # | compare_id | 좌측 | 우측 | ★ |
|---|-----------|------|------|---|
| 12 | compare_n5_043_090 | 前に | てから | ★★ |
| 13 | compare_n5_090_044 | てから | 後で | ★★ |
| 14 | compare_n5_011_088 | から | ので | ★★★ |
| 15 | compare_n5_084_084i | それから | そして | ★★ |

### Cluster D — 종조사·접속·병렬 대조

| # | compare_id | 좌측 | 우측 | ★ |
|---|-----------|------|------|---|
| 16 | compare_n5_050_051 | ね | よ | ★★ |
| 17 | compare_n5_082_082kei | けど | けれども | ★★ |
| 18 | compare_n5_008_010 | も | や | ★★ |

### Cluster E — 시제·추측·설명 대조

| # | compare_id | 좌측 | 우측 | ★ |
|---|-----------|------|------|---|
| 19 | compare_n5_095_096 | もう | まだ | ★★★ |
| 20 | compare_n5_085_047 | だろう | でしょう | ★ |
| 21 | compare_n5_086_087 | んです | のです | ★ |
| 22 | compare_n5_045_047 | と思います | でしょう | ★ |

### Cluster F — E-12 신규 항목 관련 (E-16 추가)

| # | compare_id | 좌측 | 우측 | ★ |
|---|-----------|------|------|---|
| 23 | compare_n5_107_026 | なくてもいい | てはいけない | ★★★ |
| 24 | compare_n5_108_023 | たことがある | ている | ★★ |
| 25 | compare_n5_106_ta | ほうがいい辞書形 | ほうがいい た形 | ★★ |

> **제거된 비교쌍** (E-5, E-10):
> - でも/しかし/けど 3-way 비교 → E-5에 의해 완전 제거
> - つもり/予定 비교 → E-10에 의해 완전 제거 (予定는 N4 범위)

---

## 데이터 무결성 규칙

1. `compare_id` 는 전체 고유값.
2. `left_grammar_point_id` 와 `right_grammar_point_id` 는 `n5_master.xlsx`의 `master_list` 또는 `variant_chunks` 에 존재하는 ID여야 함.
3. 동일 ID 자기 대조 쌍(`031_031i`, `084_084i`, `106_ta`)은 의미 차이 또는 接続形 차이 기반으로만 허용.
4. `embedding_text` 길이: compare chunk ≥ 50자, ≤ 120자.
5. Cluster F의 3쌍은 E-16 결정으로 추가된 신규쌍으로, E-12 신규 항목(106~108)을 포함.
6. 각 비교쌍의 `comparison_pair_ids` 는 `n5_master.xlsx` l3_assignment 시트와 양방향 동기화 필요.
