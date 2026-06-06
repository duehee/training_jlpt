# data/schema/ — xlsx 스키마 명세

> 운영 데이터(`data/{level}/*.xlsx`)의 헤더·타입·필수 여부 정의.
> 세션 4 수진 v2 plan 작성 시 신설 예정.

## 예정 파일

| 파일 | 대상 xlsx |
|---|---|
| `n5_master_schema.md` | `data/n5/n5_master.xlsx` 5 시트 컬럼 명세 |
| `n5_comparison_schema.md` | `data/n5/n5_comparison.xlsx` 2 시트 컬럼 명세 |
| (추후) `n4_*_schema.md` | N4 작업 진입 시 동일 패턴 |

## 작성 가이드
- 헤더·타입·필수·enum·예시값 명시
- `data/n5/README.md` 시트별 컬럼 표를 정식 명세로 확장
- 변경 시 적재 파이프라인 영향 점검 (재현/lead)

## 양식 안정성 7 가이드 (07_pre_v2_check §2-⑤ 5-3)
1. 헤더 변경 금지 — 신규 컬럼 추가만 허용
2. NULL 표기 통일 — 명시적 `null` 또는 빈 문자열
3. enum lowercase + underscore (`non_past`, `polite` 등)
4. 배열 컬럼 = JSON 표기 (`["grammar_n5_002"]`)
5. 시트명 snake_case
6. 첫 행 = 헤더, 두 번째 행부터 데이터
7. bool TRUE/FALSE 대문자 통일

## 변경 책임
- 스키마 신설·변경 → 수진 + 재현 협업, 정빈님 승인 게이트
