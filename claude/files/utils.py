"""
utils.py - 에코팜 흑염소 관리 솔루션 유틸리티 모듈
DB 쿼리, 데이터 처리, 검증, 내보내기, 로깅 등 공통 함수
"""
import sqlite3
import pandas as pd
import io
import re
import streamlit as st
from datetime import datetime
from typing import Optional, List, Tuple, Any
from db_init import get_connection, init_db, DB_FILE

# ================================================================
# 1. 핵심 DB 함수
# ================================================================

def run_query(query: str, params=None) -> pd.DataFrame:
    """SELECT 쿼리 실행 → DataFrame 반환"""
    conn = get_connection()
    try:
        if params:
            df = pd.read_sql(query, conn, params=params)
        else:
            df = pd.read_sql(query, conn)
        return df
    except Exception as e:
        st.error(f"쿼리 오류: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


def run_action(query: str, params: tuple) -> bool:
    """INSERT/UPDATE/DELETE 실행 → 성공 여부 반환"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        conn.commit()
        return True
    except sqlite3.IntegrityError as e:
        st.error(f"중복 또는 제약 조건 오류: {e}")
        return False
    except Exception as e:
        st.error(f"DB 실행 오류: {e}")
        return False
    finally:
        conn.close()


def run_many(query: str, params_list: List[tuple]) -> bool:
    """다건 INSERT/UPDATE 실행"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.executemany(query, params_list)
        conn.commit()
        return True
    except Exception as e:
        st.error(f"다건 실행 오류: {e}")
        return False
    finally:
        conn.close()


# ================================================================
# 2. 대시보드 집계 통계
# ================================================================

def get_dashboard_stats(farm_id: str = "FARM01") -> dict:
    """대시보드용 주요 지표 한 번에 조회"""
    stats = {}

    # 성별별 사육 두수
    df_gender = run_query(
        "SELECT gender, COUNT(*) as cnt FROM individuals WHERE status='사육' AND farm_id=? GROUP BY gender",
        (farm_id,)
    )
    stats['total'] = int(df_gender['cnt'].sum()) if not df_gender.empty else 0
    for g in ['암', '수', '거세']:
        row = df_gender[df_gender['gender'] == g]
        stats[g] = int(row['cnt'].iloc[0]) if not row.empty else 0

    # 누적 출산
    df_birth = run_query(
        "SELECT IFNULL(SUM(total_kids),0) as tot, IFNULL(SUM(live_female),0) as f, IFNULL(SUM(live_male),0) as m FROM birth_events WHERE farm_id=?",
        (farm_id,)
    )
    stats['birth_total'] = int(df_birth.iloc[0]['tot']) if not df_birth.empty else 0
    stats['birth_female'] = int(df_birth.iloc[0]['f']) if not df_birth.empty else 0
    stats['birth_male'] = int(df_birth.iloc[0]['m']) if not df_birth.empty else 0

    # 입하/출하/폐사
    stats['inbound'] = int(run_query(
        "SELECT COUNT(*) as cnt FROM movements WHERE type='입하' AND farm_id=?", (farm_id,)
    ).iloc[0]['cnt'])
    stats['outbound'] = int(run_query(
        "SELECT COUNT(*) as cnt FROM individuals WHERE status='출하' AND farm_id=?", (farm_id,)
    ).iloc[0]['cnt'])
    stats['dead'] = int(run_query(
        "SELECT COUNT(*) as cnt FROM individuals WHERE status='폐사' AND farm_id=?", (farm_id,)
    ).iloc[0]['cnt'])

    # 이번달 이벤트
    this_month = datetime.now().strftime('%Y-%m')
    stats['births_this_month'] = int(run_query(
        "SELECT COUNT(*) as cnt FROM birth_events WHERE birth_date LIKE ? AND farm_id=?",
        (f"{this_month}%", farm_id)
    ).iloc[0]['cnt'])
    stats['health_this_month'] = int(run_query(
        "SELECT COUNT(*) as cnt FROM health_logs WHERE date LIKE ? AND farm_id=?",
        (f"{this_month}%", farm_id)
    ).iloc[0]['cnt'])

    return stats


# ================================================================
# 3. 데이터 처리 유틸
# ================================================================

def paginate_data(df: pd.DataFrame, page: int = 1, page_size: int = 20) -> Tuple[pd.DataFrame, int]:
    """데이터프레임 페이지네이션"""
    total_pages = max(1, (len(df) + page_size - 1) // page_size)
    page = max(1, min(page, total_pages))
    start = (page - 1) * page_size
    end = start + page_size
    return df.iloc[start:end], total_pages


def sort_data(df: pd.DataFrame, col: str, ascending: bool = True) -> pd.DataFrame:
    """데이터프레임 정렬"""
    if col in df.columns:
        return df.sort_values(col, ascending=ascending)
    return df


def build_search_query(base: str, filters: dict) -> Tuple[str, list]:
    """
    동적 검색 쿼리 빌더
    filters = {'column': ('op', value)} op: LIKE / = / >= / <=
    """
    query = base + " WHERE 1=1"
    params = []
    for col, (op, val) in filters.items():
        if val and val != "전체":
            if op == 'LIKE':
                query += f" AND {col} LIKE ?"
                params.append(f"%{val}%")
            else:
                query += f" AND {col} {op} ?"
                params.append(val)
    return query, params


# ================================================================
# 4. 검증 함수
# ================================================================

def validate_goat_id(goat_id: str) -> Tuple[bool, str]:
    """
    개체번호 유효성 검사
    규칙: 영문(F/M/C) + 4자리 숫자, 예: F0001
    """
    if not goat_id:
        return False, "개체번호를 입력하세요."
    pattern = r'^[FMCfmc]\d{4}$'
    if not re.match(pattern, goat_id.strip()):
        return False, "개체번호 형식 오류 (예: F0001, M0023, C0100)"
    return True, ""


def check_duplicate_goat_id(goat_id: str) -> bool:
    """개체번호 중복 확인 → True: 중복 있음"""
    df = run_query("SELECT id FROM individuals WHERE id=?", (goat_id.strip().upper(),))
    return not df.empty


def validate_date(date_str: str) -> Tuple[bool, str]:
    """날짜 형식 검증 (YYYY-MM-DD)"""
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True, ""
    except ValueError:
        return False, "날짜 형식이 올바르지 않습니다 (YYYY-MM-DD)"


def get_next_id(prefix: str, farm_id: str = "FARM01") -> str:
    """다음 개체번호 자동 생성 (예: F0001 → F0002)"""
    df = run_query(
        "SELECT id FROM individuals WHERE id LIKE ? AND farm_id=? ORDER BY id DESC LIMIT 1",
        (f"{prefix.upper()}%", farm_id)
    )
    if df.empty:
        return f"{prefix.upper()}0001"
    last_id = df.iloc[0]['id']
    try:
        num = int(last_id[1:]) + 1
        return f"{prefix.upper()}{num:04d}"
    except:
        return f"{prefix.upper()}0001"


# ================================================================
# 5. 데이터 내보내기
# ================================================================

def export_to_excel(dfs: dict, filename: str = "ecofarm_export.xlsx") -> bytes:
    """
    여러 DataFrame을 시트별로 Excel 파일로 내보내기
    dfs = {'시트명': dataframe, ...}
    반환: bytes (st.download_button에 사용)
    """
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for sheet_name, df in dfs.items():
            df.to_excel(writer, sheet_name=sheet_name[:31], index=False)
    return output.getvalue()


def export_to_csv(df: pd.DataFrame) -> bytes:
    """DataFrame → CSV bytes (UTF-8 BOM, 엑셀 호환)"""
    return df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')


def get_full_export(farm_id: str = "FARM01") -> bytes:
    """전체 데이터 Excel 내보내기 (다중 시트)"""
    dfs = {
        '개체현황': run_query("SELECT * FROM individuals WHERE farm_id=?", (farm_id,)),
        '건강진료': run_query("SELECT * FROM health_logs WHERE farm_id=?", (farm_id,)),
        '출산번식': run_query("SELECT * FROM birth_events WHERE farm_id=?", (farm_id,)),
        '이동이력': run_query("SELECT * FROM movements WHERE farm_id=?", (farm_id,)),
        '체중기록': run_query("SELECT * FROM weight_logs WHERE farm_id=?", (farm_id,)),
        '백신기록': run_query("SELECT * FROM vaccine_logs WHERE farm_id=?", (farm_id,)),
    }
    return export_to_excel(dfs, f"ecofarm_{farm_id}_{datetime.now().strftime('%Y%m%d')}.xlsx")


# ================================================================
# 6. 변경 이력 로깅
# ================================================================

def log_change(
    table_name: str,
    record_id: str,
    action: str,
    field_name: str = None,
    old_value: str = None,
    new_value: str = None,
    manager: str = "system",
    farm_id: str = "FARM01"
) -> None:
    """변경 이력 자동 기록 (감사 추적)"""
    run_action(
        """INSERT INTO change_logs 
           (farm_id, table_name, record_id, action, field_name, old_value, new_value, manager)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (farm_id, table_name, record_id, action, field_name, old_value, new_value, manager)
    )


# ================================================================
# 7. 편의 조회 함수
# ================================================================

def get_farm_list() -> List[Tuple[str, str]]:
    """농장 목록 반환 [(id, name), ...]"""
    df = run_query("SELECT id, name FROM farms ORDER BY id")
    if df.empty:
        return [("FARM01", "에코팜 1호")]
    return list(zip(df['id'], df['name']))


def get_group_codes(farm_id: str = "FARM01", gender: str = None) -> pd.DataFrame:
    """그룹 코드 목록 조회"""
    if gender:
        return run_query(
            "SELECT code, label FROM group_codes WHERE farm_id=? AND gender=? ORDER BY code",
            (farm_id, gender)
        )
    return run_query(
        "SELECT code, label, gender FROM group_codes WHERE farm_id=? ORDER BY code",
        (farm_id,)
    )


def get_individual_summary(goat_id: str) -> dict:
    """특정 개체 요약 정보"""
    df = run_query("SELECT * FROM individuals WHERE id=?", (goat_id,))
    if df.empty:
        return {}
    row = df.iloc[0].to_dict()

    # 마지막 체중
    w = run_query(
        "SELECT weight, date FROM weight_logs WHERE goat_id=? ORDER BY date DESC LIMIT 1",
        (goat_id,)
    )
    row['last_weight'] = f"{w.iloc[0]['weight']}kg ({w.iloc[0]['date']})" if not w.empty else "-"

    # 출산 횟수 (암컷)
    if row.get('gender') == '암':
        b = run_query("SELECT COUNT(*) as cnt FROM birth_events WHERE mother_id=?", (goat_id,))
        row['birth_count'] = int(b.iloc[0]['cnt']) if not b.empty else 0

    return row


def ensure_db():
    """앱 시작 시 DB 존재 여부 확인 및 초기화"""
    import os
    if not os.path.exists(DB_FILE):
        init_db()
