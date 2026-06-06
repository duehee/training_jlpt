# n5_master_schema.md — N5 마스터 xlsx 컬럼 명세

> 버전: v2.0 / 작성: de_sujin / 세션 4 / 2026-06-06
> 파일 경로: `data/n5/n5_master.xlsx`
> 결정 이력: E-1, E-2, E-5, E-7, E-8, E-9, E-12, E-13, 즉3~즉10

---

## 개요

| 항목 | 내용 |
|------|------|
| 파일명 | n5_master.xlsx |
| 시트 수 | 5개 |
| base 항목 수 | 109개 (IDs 001~110, 061 gap) |
| variant 항목 수 | 3개 |
| BORDER 항목 수 | 25개 (21 기존 + E-12 4건: 106/107/108/110 확정) |

---

## Sheet 1: `master_list`

기본 문법 포인트 메타데이터 (109 base items).

| 컬럼명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| `grammar_point_id` | string | ✓ | PK. 형식: `grammar_n5_{NNN}`. 061 gap 존재 (E-1 제거). |
| `chunk_type` | string | ✓ | 항상 `point`. (variant는 Sheet 5에 별도 관리) |
| `japanese_name` | string | ✓ | 문법 항목의 일본어 표기. |
| `korean_meaning` | string | ✓ | 한국어 의미·기능 요약 (30자 이내 권장). |
| `level` | string | ✓ | 항상 `N5`. |
| `l1` | string | ✓ | L1 분류명. 9개 카테고리 중 하나. |
| `l2` | string | ✓ | L2 세부 분류명. L1 하위 소분류. |
| `source_pool` | string | ✓ | 출처 소스 목록. 형식: `SRC-01,SRC-02,...`. |
| `frequency` | integer | ✓ | 출처 등장 빈도 (1~6). |
| `note` | string | | 변경 사유·특이사항. E-12 신규, E-2 이관 등 표기. |

### L1 분류 enum (9개)

| L1 | 항목 수 | 대표 ID |
|----|---------|---------|
| 조사 | 15 | 001~015 |
| 활용 | 15 | 016~029, 089 |
| 문형·표현 | 27 | 030~048, 085~087, 091, 106~109 |
| 종조사 | 5 | 049~053 |
| 지시·연체 | 7 | 054~060 |
| 의문 표현 | 10 | 062~071 (061 gap) |
| 시간·수량 | 8 | 072~078, 110 |
| 접속·연결 | 6 | 081~084, 088, 090 |
| 부사류 | 16 | 079~080, 092~105 |

---

## Sheet 2: `taxonomy_def`

L1/L2 분류 체계 정의.

| 컬럼명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| `l1_name` | string | ✓ | L1 분류명 (9개). |
| `l2_name` | string | ✓ | L2 소분류명. |
| `definition` | string | ✓ | 소분류 정의·설명. |
| `item_count` | integer | ✓ | 해당 L2에 속하는 base 항목 수. |
| `id_range_examples` | string | ✓ | 대표 ID 범위 또는 예시. |

---

## Sheet 3: `l3_assignment`

문법 항목별 L3 메타데이터 태그 배정 (109 base items).

| 컬럼명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| `grammar_point_id` | string | ✓ | FK → master_list.grammar_point_id |
| `border_candidate` | boolean | ✓ | N5/N4 경계 후보 여부. 유효 21개. `True`=BORDER, `False`=해당 없음. |
| `border_reason` | string | | BORDER 이유 요약. border_candidate=False이면 빈 문자열. |
| `connection_type` | string | | 접속 형태. 값 목록: `verb_dict`, `verb_te`, `verb_nai`, `verb_ta`, `verb_stem`, `noun`, `plain`, `iadj`, `nadj`, `iadj_stem`, `null`. 조사/부사류는 `null`. |
| `tense` | string | ✓ | 시제. `non_past`, `past`, `any` 중 하나. |
| `polarity` | string | ✓ | 극성. `positive`, `negative`, `both` 중 하나. |
| `formality` | string | ✓ | 격식. `polite`, `plain`, `both` 중 하나. |
| `comparison_pair_ids` | string (JSON) | ✓ | 비교 쌍 ID 목록 (JSON array 문자열). E-9 대량 정리 적용. 형식: `["grammar_n5_XXX", ...]` 또는 `[]`. |
| `embedding_text` | string | ✓ | RAG 임베딩용 텍스트. point chunk: 150~270자 (Q6 품질 기준). |

### connection_type 값 설명

| 값 | 의미 |
|----|------|
| `verb_dict` | 動詞 辞書形 접속 |
| `verb_te` | 動詞 て形 접속 |
| `verb_nai` | 動詞 ない形 접속 |
| `verb_ta` | 動詞 た形 접속 |
| `verb_stem` | 動詞 語幹(ます形) 접속 |
| `noun` | 명사 접속 |
| `plain` | 普通形 접속 |
| `iadj` | い형용사 어간 접속 |
| `nadj` | な형용사 어간 접속 |
| `iadj_stem` | い형용사 語幹 접속 |
| `null` | 조사·부사류 등 형태 변화 없는 독립 요소 |

---

## Sheet 4: `border_meta`

N5/N4 경계 항목 상세 정보 (25 items = 21 기존 + E-12 4건: 106/107/108/110).

| 컬럼명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| `grammar_point_id` | string | ✓ | FK → master_list.grammar_point_id. BORDER=True인 25개 (E-12 4건 포함). |
| `border_reason` | string | ✓ | 경계 후보로 선정된 이유 (1~2문장). |
| `n5_scope` | string | ✓ | N5 범위에서 학습해야 할 핵심 용법. |
| `n4_advanced` | string | ✓ | N4 이상에서 심화해야 할 고급 용법. |

### BORDER 유효 25개 ID 목록

**기존 21개**: `002, 004, 005, 007, 011, 013, 023, 026, 028, 032, 035, 043, 047, 048, 085, 086, 087, 088, 089, 090, 091`

**E-12 신규 4건 (츠쿠야 §7 확정)**: `106, 107, 108, 110`

> 변경 이력:
> - 001 제거: 즉8 (は는 N5 핵심, BORDER 승격 불필요)
> - 040 제거: 즉3 (より〜のほうが는 N5 비교 기본 표현, BORDER 불필요)
> - 035 duplicate 제거: 즉4 (중복 row 제거)
> - 079, 080: E-2에 의해 L1-9 이관 후 재검토에서 BORDER 미해당으로 확정

---

## Sheet 5: `variant_chunks`

문법 항목의 이형태(variant) 청크 (3 items).

| 컬럼명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| `grammar_point_id` | string | ✓ | PK. 형식: `grammar_n5_{NNN}_{suffix}`. |
| `chunk_type` | string | ✓ | 항상 `variant`. |
| `base_id` | string | ✓ | 원본 ID. FK → master_list.grammar_point_id. |
| `japanese_name` | string | ✓ | 이형태의 일본어 표기. |
| `korean_meaning` | string | ✓ | 이형태의 한국어 의미 및 특징 설명. |
| `level` | string | ✓ | 항상 `N5`. |
| `l1` | string | ✓ | base_id의 L1과 동일. |
| `l2` | string | ✓ | base_id의 L2와 동일. |
| `variant_label` | string | ✓ | 이형태 분류 레이블. 예: `구어 이형태`, `형식체 이형태`. |
| `border_candidate` | boolean | | BORDER 여부. `True` 또는 `False`. 레지스터 변이 variant는 base가 N5/N4 경계 관리 → 전부 False. |
| `embedding_text` | string | ✓ | RAG 임베딩용 텍스트. variant: ~120~150자. |
| `note` | string | | 특이사항·재검수 대기 상태 등. |

### Variant 3건 ID 목록

| grammar_point_id | base_id | 설명 |
|-----------------|---------|------|
| `grammar_n5_026_informal` | `grammar_n5_026` | ちゃいけない (구어 이형태) |
| `grammar_n5_082_keisiki` | `grammar_n5_082` | けれども (형식체 이형태) |
| `grammar_n5_035_alt` | `grammar_n5_035` | ないといけない (구어 이형태) |

---

## 데이터 무결성 규칙

1. `grammar_point_id` 는 전체 고유값. `grammar_n5_061` 은 E-1에 의해 영구 제거.
2. `border_candidate=True` 항목은 반드시 `border_meta` 시트에 대응 row 존재.
3. `comparison_pair_ids` 가 비어있지 않으면 해당 ID가 `n5_comparison.xlsx`의 `comparison_pairs` 또는 `variant_chunks` 에 존재해야 함.
4. `embedding_text` 길이: point ≥ 150자, variant ≥ 100자.
5. E-12 신규 항목 BORDER: 106/107/108/110 = TRUE, 109 = FALSE (츠쿠야 §7 확정 2026-06-06).
