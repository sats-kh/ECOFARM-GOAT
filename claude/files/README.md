# 🐐 에코팜 흑염소 관리 솔루션 v1.0

> 소규모 다농장(2~5곳)을 위한 상용화 수준 축산 이력 관리 프로그램

---

## 📁 파일 구조

```
ecofarm/
├── app.py            ← 메인 Streamlit 앱 (실행 진입점)
├── db_init.py        ← DB 스키마 정의 & 초기화 & 시드 데이터
├── utils.py          ← 공통 유틸리티 함수 모음
├── requirements.txt  ← 패키지 의존성
└── eco_farm.db       ← SQLite DB (자동 생성)
```

---

## 🚀 빠른 시작

### 1. 패키지 설치
```bash
pip install -r requirements.txt
```

### 2. 앱 실행
```bash
streamlit run app.py
```

### 3. 브라우저에서 확인
```
http://localhost:8501
```

---

## 📊 DB 테이블 구조

| 테이블 | 설명 |
|--------|------|
| `farms` | 농장 정보 (멀티테넌트) |
| `users` | 사용자/담당자 |
| `group_codes` | 그룹 코드 마스터 |
| `individuals` | 개체 (핵심) |
| `health_logs` | 건강/진료 이력 |
| `birth_events` | 출산/번식 이력 |
| `movements` | 이동/입출하 이력 |
| `weight_logs` | 체중 기록 |
| `vaccine_logs` | 백신/예방접종 |
| `change_logs` | 변경 감사 로그 |

---

## 📱 주요 기능

### 대시보드
- 실시간 사육 두수 (암/수/거세)
- 누적 이벤트 현황 (출산/입하/폐사/출하)
- 이번달 이벤트 카운트
- 개체 분포 도넛 차트 4종
- 월별 출산 트렌드 차트
- 최근 활동 로그
- 전체 데이터 Excel 내보내기

### 개체 관리
- 개체 목록 (검색/필터)
- 개체 상세 조회 (체중 추이 차트 포함)
- 정보 수정 (상태/방/그룹/품종/비고)
- 건강/번식/이동/체중 이력 탭
- 신규 개체 등록 (자동 번호 생성)

### 이벤트 기록
- 건강·진료 기록 (결과에 따른 상태 자동 변경)
- 출산·번식 기록
- 이동·입출하 기록 (상태 자동 변경)
- 체중 일괄 측정
- 백신·예방접종 기록

### 이력 조회
- 분야별 전체 데이터 조회
- 날짜 범위 필터 + 키워드 검색
- CSV / Excel 개별 내보내기

---

## 🔧 커스터마이징

### 그룹 코드 추가
`db_init.py`의 `SEED_DATA_SQL`에 INSERT 추가:
```sql
INSERT OR IGNORE INTO group_codes (code, farm_id, label, gender) VALUES
    ('NEWGRP', 'FARM01', '새 그룹명', '암');
```

### 농장 추가
```sql
INSERT OR IGNORE INTO farms (id, name, owner) VALUES ('FARM03', '3호 농장', '대표자명');
```

### DB 직접 초기화 (리셋)
```bash
rm eco_farm.db
python db_init.py
```

---

## 📈 향후 개발 로드맵

- [ ] 사용자 로그인 / 권한 관리 (admin/manager/worker)
- [ ] 알림 기능 (예방접종 예정일, 다음 방문일)
- [ ] 모바일 앱 (Streamlit Cloud 배포)
- [ ] 사료 급여 / 재고 관리 모듈
- [ ] 수익/비용 분석 리포트
- [ ] 바코드/RFID 스캔 연동
- [ ] 클라우드 DB 전환 (PostgreSQL)

---

## 📞 문의
© 2026 Eco Farm Solution
