# data/ — 운영 데이터 디렉터리

> 운영 진실 = xlsx 형식 (DB in/out 편의)
> 검수·메모는 `docs/planning/session_N/`에 보관, 본 디렉터리는 **확정 운영 데이터만**.

## 구조

```
data/
├── n5/                    ← N5 마스터·비교쌍 xlsx (세션 4 수진 v2부터)
├── schema/                ← xlsx 스키마 명세 (헤더·타입·필수 여부)
├── n4/                    ← 추후 N4 작업 시 신설
└── n3/                    ← 추후 N3 작업 시 신설
```

## 정책 (decision_log 2026-06-06 E-13)
- xlsx = 운영 진실 공급원
- MD = 검수·협업 친화 형식 (인간 가독성, `docs/planning/session_N/de_sujin/`에 별도 유지)
- DB 적재 = xlsx → 적재 파이프라인 (Stage 1 또는 트랙 3에서 lead/재현 설계)
- 스키마 변경 금지 — 신규 컬럼 추가만 허용, 기존 컬럼 rename 금지 (적재 호환성)

## 신규 파일 추가 절차
- v2 plan 정빈님 승인 후 수진이 작성·갱신
- 스키마 변경은 `data/schema/` 업데이트 필요 (수진 + 재현 협업)
