"""
db_init.py - 에코팜 흑염소 관리 솔루션 DB 초기화 모듈
다농장(멀티테넌트) 지원, 완전한 이력 관리 스키마
"""
import sqlite3
import os
from datetime import datetime

DB_FILE = "eco_farm.db"

SCHEMA_SQL = """
-- ================================================================
-- 1. 농장 정보 (멀티테넌트 지원)
-- ================================================================
CREATE TABLE IF NOT EXISTS farms (
    id          TEXT PRIMARY KEY,          -- 농장 코드 (예: FARM01)
    name        TEXT NOT NULL,             -- 농장명
    owner       TEXT,                      -- 대표자
    address     TEXT,                      -- 주소
    phone       TEXT,                      -- 연락처
    created_at  TEXT DEFAULT (datetime('now', 'localtime'))
);

-- ================================================================
-- 2. 사용자 / 담당자
-- ================================================================
CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    farm_id     TEXT NOT NULL REFERENCES farms(id),
    username    TEXT NOT NULL UNIQUE,
    role        TEXT DEFAULT 'worker',     -- admin / manager / worker
    name        TEXT,
    phone       TEXT,
    created_at  TEXT DEFAULT (datetime('now', 'localtime'))
);

-- ================================================================
-- 3. 그룹 코드 정의 (축사 그룹 마스터)
-- ================================================================
CREATE TABLE IF NOT EXISTS group_codes (
    code        TEXT PRIMARY KEY,
    farm_id     TEXT REFERENCES farms(id),
    label       TEXT NOT NULL,             -- 한글 표시명
    gender      TEXT,                      -- 암/수/거세/혼합
    description TEXT
);

-- ================================================================
-- 4. 개체 (핵심 테이블)
-- ================================================================
CREATE TABLE IF NOT EXISTS individuals (
    id              TEXT PRIMARY KEY,       -- 개체번호 (예: F0001)
    farm_id         TEXT REFERENCES farms(id),
    gender          TEXT NOT NULL,          -- 암/수/거세
    breed           TEXT DEFAULT '흑염소',   -- 품종
    birth_date      TEXT,                   -- 출생일 (YYYY-MM-DD)
    birth_type      TEXT DEFAULT '자가출생', -- 자가출생/구입
    status          TEXT DEFAULT '사육',    -- 사육/폐사/출하/격리/거세대기
    room_no         TEXT,                   -- 방/축사 번호
    group_code      TEXT REFERENCES group_codes(code),
    father_id       TEXT,                   -- 부축 ID
    mother_id       TEXT,                   -- 모축 ID
    purchase_date   TEXT,                   -- 구입일 (구입 개체)
    purchase_price  INTEGER,               -- 구입 단가
    weight_initial  REAL,                  -- 초기 체중 (kg)
    ear_tag         TEXT,                   -- 귀표 번호
    rfid            TEXT,                   -- RFID 태그
    notes           TEXT,                   -- 비고
    created_at      TEXT DEFAULT (datetime('now', 'localtime')),
    updated_at      TEXT DEFAULT (datetime('now', 'localtime'))
);

-- ================================================================
-- 5. 건강/진료 기록
-- ================================================================
CREATE TABLE IF NOT EXISTS health_logs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    goat_id     TEXT NOT NULL REFERENCES individuals(id),
    farm_id     TEXT REFERENCES farms(id),
    date        TEXT NOT NULL,             -- 진료일
    symptom     TEXT,                      -- 증상
    diagnosis   TEXT,                      -- 진단
    treatment   TEXT,                      -- 처방/처치
    medicine    TEXT,                      -- 사용 약품
    dose        TEXT,                      -- 용량
    cost        INTEGER DEFAULT 0,         -- 진료비
    result      TEXT DEFAULT '진행중',      -- 완치/진행중/폐사
    vet_name    TEXT,                      -- 수의사/담당자
    manager     TEXT,                      -- 기록 담당자
    next_visit  TEXT,                      -- 다음 방문 예정일
    notes       TEXT,
    created_at  TEXT DEFAULT (datetime('now', 'localtime'))
);

-- ================================================================
-- 6. 출산/번식 기록
-- ================================================================
CREATE TABLE IF NOT EXISTS birth_events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    farm_id         TEXT REFERENCES farms(id),
    mother_id       TEXT NOT NULL REFERENCES individuals(id),
    father_id       TEXT REFERENCES individuals(id),
    birth_date      TEXT NOT NULL,          -- 출산일
    birth_order     INTEGER DEFAULT 1,      -- 산차 (몇 번째 출산)
    total_kids      INTEGER DEFAULT 0,      -- 총 산자수
    live_male       INTEGER DEFAULT 0,      -- 수컷 생존
    live_female     INTEGER DEFAULT 0,      -- 암컷 생존
    stillborn       INTEGER DEFAULT 0,      -- 사산
    delivery_type   TEXT DEFAULT '자연분만', -- 자연분만/제왕절개/난산
    birth_weight_avg REAL,                 -- 평균 출생 체중
    notes           TEXT,
    manager         TEXT,
    created_at      TEXT DEFAULT (datetime('now', 'localtime'))
);

-- ================================================================
-- 7. 이동/입출하 기록
-- ================================================================
CREATE TABLE IF NOT EXISTS movements (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    farm_id     TEXT REFERENCES farms(id),
    goat_id     TEXT NOT NULL REFERENCES individuals(id),
    date        TEXT NOT NULL,
    type        TEXT NOT NULL,              -- 입하/출하/이동/격리/복귀
    destination TEXT,                       -- 목적지/출발지
    reason      TEXT,                       -- 이동 사유
    price       INTEGER DEFAULT 0,          -- 거래 금액 (입출하 시)
    weight      REAL,                       -- 이동 시 체중
    manager     TEXT,
    notes       TEXT,
    created_at  TEXT DEFAULT (datetime('now', 'localtime'))
);

-- ================================================================
-- 8. 체중 기록
-- ================================================================
CREATE TABLE IF NOT EXISTS weight_logs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    goat_id     TEXT NOT NULL REFERENCES individuals(id),
    farm_id     TEXT REFERENCES farms(id),
    date        TEXT NOT NULL,
    weight      REAL NOT NULL,             -- 체중 (kg)
    manager     TEXT,
    notes       TEXT,
    created_at  TEXT DEFAULT (datetime('now', 'localtime'))
);

-- ================================================================
-- 9. 백신/예방접종 기록
-- ================================================================
CREATE TABLE IF NOT EXISTS vaccine_logs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    goat_id     TEXT NOT NULL REFERENCES individuals(id),
    farm_id     TEXT REFERENCES farms(id),
    date        TEXT NOT NULL,
    vaccine_name TEXT NOT NULL,            -- 백신명
    dose        TEXT,                      -- 용량
    next_date   TEXT,                      -- 다음 접종일
    manager     TEXT,
    notes       TEXT,
    created_at  TEXT DEFAULT (datetime('now', 'localtime'))
);

-- ================================================================
-- 10. 변경 이력 로그 (감사 추적)
-- ================================================================
CREATE TABLE IF NOT EXISTS change_logs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    farm_id     TEXT,
    table_name  TEXT NOT NULL,
    record_id   TEXT NOT NULL,
    action      TEXT NOT NULL,             -- INSERT/UPDATE/DELETE
    field_name  TEXT,
    old_value   TEXT,
    new_value   TEXT,
    manager     TEXT,
    created_at  TEXT DEFAULT (datetime('now', 'localtime'))
);

-- ================================================================
-- 인덱스
-- ================================================================
CREATE INDEX IF NOT EXISTS idx_ind_farm     ON individuals(farm_id);
CREATE INDEX IF NOT EXISTS idx_ind_status   ON individuals(status);
CREATE INDEX IF NOT EXISTS idx_ind_gender   ON individuals(gender);
CREATE INDEX IF NOT EXISTS idx_health_goat  ON health_logs(goat_id);
CREATE INDEX IF NOT EXISTS idx_health_date  ON health_logs(date);
CREATE INDEX IF NOT EXISTS idx_birth_mother ON birth_events(mother_id);
CREATE INDEX IF NOT EXISTS idx_birth_date   ON birth_events(birth_date);
CREATE INDEX IF NOT EXISTS idx_move_goat    ON movements(goat_id);
CREATE INDEX IF NOT EXISTS idx_weight_goat  ON weight_logs(goat_id);
"""

SEED_DATA_SQL = """
-- 기본 농장 데이터
INSERT OR IGNORE INTO farms (id, name, owner, address, phone) VALUES
    ('FARM01', '에코팜 1호 농장', '홍길동', '경기도 양평군', '010-1234-5678'),
    ('FARM02', '에코팜 2호 농장', '김철수', '강원도 횡성군', '010-9876-5432');

-- 그룹 코드 마스터
INSERT OR IGNORE INTO group_codes (code, farm_id, label, gender, description) VALUES
    ('SGOAT1', 'FARM01', '특종묘1반', '수', '우량 씨수염소 1그룹'),
    ('SGOAT2', 'FARM01', '특종묘2반', '수', '우량 씨수염소 2그룹'),
    ('SBOER',  'FARM01', '그외종묘반', '수', '보어 계열 종묘'),
    ('ETCM',   'FARM01', '수자축반', '수', '수컷 자축'),
    ('ETCF',   'FARM01', '암자축반', '암', '암컷 자축'),
    ('FGOAT1', 'FARM01', '암성축1반', '암', '암컷 성축 1그룹'),
    ('FGOAT2', 'FARM01', '암성축2반', '암', '암컷 성축 2그룹'),
    ('WEEDAT', 'FARM01', '독거세반', '거세', '독립 거세 완료'),
    ('WBOER',  'FARM01', '그리거세반', '거세', '보어 계열 거세'),
    ('WGOAT',  'FARM01', '특거세반', '거세', '특종 거세');

-- 샘플 개체 (데모용)
INSERT OR IGNORE INTO individuals (id, farm_id, gender, breed, birth_date, status, room_no, group_code, notes) VALUES
    ('F0001', 'FARM01', '암', '흑염소', '2022-03-15', '사육', '1', 'FGOAT1', '우량 번식 모체'),
    ('F0002', 'FARM01', '암', '흑염소', '2022-05-20', '사육', '1', 'FGOAT1', NULL),
    ('F0003', 'FARM01', '암', '흑염소', '2023-01-10', '사육', '2', 'FGOAT2', NULL),
    ('F0004', 'FARM01', '암', '흑염소 x 보어', '2023-06-05', '사육', '2', 'ETCF', '자축'),
    ('M0001', 'FARM01', '수', '흑염소', '2021-08-12', '사육', '3', 'SGOAT1', '씨수염소 A'),
    ('M0002', 'FARM01', '수', '보어', '2022-11-01', '사육', '3', 'SBOER', NULL),
    ('M0003', 'FARM01', '수', '흑염소', '2023-09-20', '거세대기', '4', 'WGOAT', NULL),
    ('C0001', 'FARM01', '거세', '흑염소', '2022-07-18', '사육', '5', 'WEEDAT', '거세 완료'),
    ('C0002', 'FARM01', '거세', '보어', '2022-09-30', '사육', '5', 'WBOER', NULL),
    ('F0005', 'FARM01', '암', '흑염소', '2020-04-10', '폐사', '0', 'FGOAT1', '질병으로 폐사');

-- 샘플 출산 기록
INSERT OR IGNORE INTO birth_events (farm_id, mother_id, father_id, birth_date, birth_order, total_kids, live_male, live_female, delivery_type) VALUES
    ('FARM01', 'F0001', 'M0001', '2023-03-10', 1, 2, 1, 1, '자연분만'),
    ('FARM01', 'F0001', 'M0001', '2024-02-20', 2, 3, 1, 2, '자연분만'),
    ('FARM01', 'F0002', 'M0001', '2023-08-15', 1, 1, 0, 1, '자연분만'),
    ('FARM01', 'F0003', 'M0002', '2024-05-01', 1, 2, 2, 0, '자연분만');

-- 샘플 건강 기록
INSERT OR IGNORE INTO health_logs (goat_id, farm_id, date, symptom, diagnosis, treatment, result, manager) VALUES
    ('F0001', 'FARM01', '2024-01-15', '식욕 부진', '소화불량', '소화제 투여', '완치', '홍길동'),
    ('F0003', 'FARM01', '2024-03-20', '기침, 콧물', '호흡기 감염', '항생제 투여 5일', '완치', '홍길동'),
    ('F0005', 'FARM01', '2024-06-10', '급격한 체중 감소, 기력저하', '원인불명 내부 감염', '집중 치료', '폐사', '홍길동');

-- 샘플 이동 기록
INSERT OR IGNORE INTO movements (farm_id, goat_id, date, type, destination, price, manager) VALUES
    ('FARM01', 'F0001', '2022-04-01', '입하', '경기도 양평 농장', 250000, '홍길동'),
    ('FARM01', 'M0001', '2021-09-01', '입하', '강원도 횡성 농장', 500000, '홍길동'),
    ('FARM01', 'F0005', '2024-06-10', '출하', '-', 0, '홍길동');

-- 샘플 체중 기록
INSERT OR IGNORE INTO weight_logs (goat_id, farm_id, date, weight, manager) VALUES
    ('F0001', 'FARM01', '2024-01-01', 42.5, '홍길동'),
    ('F0001', 'FARM01', '2024-04-01', 44.2, '홍길동'),
    ('F0001', 'FARM01', '2024-07-01', 45.8, '홍길동'),
    ('M0001', 'FARM01', '2024-01-01', 68.0, '홍길동'),
    ('M0001', 'FARM01', '2024-07-01', 71.5, '홍길동');
"""


def init_db(db_file: str = DB_FILE) -> bool:
    """DB 스키마 및 시드 데이터 초기화"""
    try:
        conn = sqlite3.connect(db_file)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        cursor = conn.cursor()
        
        # 스키마 생성
        cursor.executescript(SCHEMA_SQL)
        
        # 시드 데이터 (최초 실행 시에만)
        cursor.executescript(SEED_DATA_SQL)
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"DB 초기화 오류: {e}")
        return False


def get_connection(db_file: str = DB_FILE) -> sqlite3.Connection:
    """DB 연결 반환 (WAL 모드, 외래키 활성화)"""
    conn = sqlite3.connect(db_file)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.row_factory = sqlite3.Row
    return conn


if __name__ == "__main__":
    if init_db():
        print(f"✅ DB 초기화 완료: {DB_FILE}")
    else:
        print("❌ DB 초기화 실패")
