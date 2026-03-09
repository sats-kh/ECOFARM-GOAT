import sqlite3
import pandas as pd
import os
import unicodedata

# DB 파일 설정
DB_FILE = "eco_farm.db"

def init_db():
    """데이터베이스 테이블 스키마 생성"""
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE) # 기존 DB 삭제 후 새로 생성 (개발용)
        
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # 1. 개체 마스터 (핵심 테이블)
    c.execute('''
        CREATE TABLE IF NOT EXISTS individuals (
            id TEXT PRIMARY KEY,       -- 개체번호
            status TEXT,               -- 현재상태
            breed TEXT,                -- 품종
            gender TEXT,               -- 성별
            room_no TEXT,              -- 방번호
            group_code TEXT,           -- 그룹번호
            birth_date TEXT,           -- 출생일
            mother_id TEXT,            -- 모축번호
            father_id TEXT,            -- 종축번호
            entry_date TEXT,           -- 입식일
            notes TEXT                 -- 비고
        )
    ''')

    # 2. 그룹 정보 (코드 매핑용)
    c.execute('''
        CREATE TABLE IF NOT EXISTS groups (
            group_code TEXT PRIMARY KEY,
            category TEXT,
            target_gender TEXT,
            description TEXT
        )
    ''')

    # 3. 교배 이력
    c.execute('''
        CREATE TABLE IF NOT EXISTS breeding_events (
            breeding_id TEXT PRIMARY KEY,
            group_code TEXT,
            room_no TEXT,
            male_id TEXT,
            start_date TEXT,
            end_date TEXT,
            expected_birth_month TEXT,
            result TEXT,
            notes TEXT
        )
    ''')

    # 4. 출산 이력
    c.execute('''
        CREATE TABLE IF NOT EXISTS birth_events (
            birth_id TEXT PRIMARY KEY,
            mother_id TEXT,
            birth_date TEXT,
            birth_order INTEGER,
            live_female INTEGER,
            live_male INTEGER,
            dead_female INTEGER,
            dead_male INTEGER,
            total_kids INTEGER,
            delivery_type TEXT,
            nursing_status TEXT,
            kids_ids TEXT,             -- 자축번호 목록 (쉼표로 구분된 문자열)
            notes TEXT
        )
    ''')

    # 5. 건강/진료 이력
    c.execute('''
        CREATE TABLE IF NOT EXISTS health_logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            goat_id TEXT,
            symptom TEXT,
            diagnosis TEXT,
            treatment TEXT,
            result TEXT,
            notes TEXT,
            treatment_id TEXT,         -- 처방ID
            manager TEXT
        )
    ''')

    # 6. 이동 이력 (상세 이동 경로)
    c.execute('''
        CREATE TABLE IF NOT EXISTS movements (
            move_id INTEGER PRIMARY KEY AUTOINCREMENT,
            movement_code TEXT,        -- 이동ID
            date TEXT,
            goat_id TEXT,
            type TEXT,                 -- 이동 유형 (입하/출하 등)
            destination TEXT,          -- 상대처
            notes TEXT
        )
    ''')

    conn.commit()
    conn.close()
    print("✅ 데이터베이스 스키마가 생성되었습니다.")
def clean_cols(df):
    """컬럼명에서 줄바꿈 및 공백 제거"""
    df.columns = [str(c).replace('\n', ' ').replace('\r', '').strip() for c in df.columns]
    return df

def find_filename(keyword):
    """키워드가 포함된 파일명을 찾습니다 (Mac 한글 자소분리 대응)."""
    files = os.listdir()
    for f in files:
        # 파일명과 키워드를 모두 NFC(표준 통합형)로 변환하여 비교
        norm_f = unicodedata.normalize('NFC', f)
        norm_k = unicodedata.normalize('NFC', keyword)
        if norm_k in norm_f and f.endswith('.csv'):
            return f
    return None

def load_data():
    """CSV 데이터를 정제하여 DB에 적재"""
    print(f"📂 현재 작업 경로: {os.getcwd()}")
    
    # DB 연결
    conn = sqlite3.connect(DB_FILE)
    
    # 1. 파일 찾기
    file_keywords = {
        'individuals': '개체마스터',
        'groups': '그룹 구분', # 띄어쓰기 주의
        'breeding': '교배이력',
        'birth': '출산이력',
        'health': '건강이력',
        'movements': '이동상세' 
    }
    
    files = {}
    missing_files = []
    
    for key, keyword in file_keywords.items():
        found = find_filename(keyword)
        if found:
            files[key] = found
            print(f"✅ 확인됨: [{key}] -> {found}")
        else:
            missing_files.append(keyword)
    
    if missing_files:
        print(f"\n❌ 다음 키워드가 포함된 CSV 파일을 찾을 수 없습니다: {missing_files}")
        print(f"   현재 폴더의 파일 목록: {os.listdir()}")
        print("   파일이 해당 폴더에 있는지, 이름이 맞는지 확인해주세요.")
        return # 파일이 없으면 중단

    # --- 이하 데이터 로드 로직은 기존과 동일하지만 files[key]로 접근 ---

    # 1. Individuals (개체마스터)
    try:
        df = pd.read_csv(files['individuals'])
        df = clean_cols(df)
        
        col_map = {
            '개체번호': 'id', '현재상태': 'status', '품종/종류': 'breed', 
            '성별': 'gender', '방번호': 'room_no', '그룹번호': 'group_code', 
            '출생일': 'birth_date', '모축번호': 'mother_id', '종축번호': 'father_id', 
            '비고': 'notes', '입식일': 'entry_date'
        }
        
        rename_dict = {}
        for col in df.columns:
            for key, val in col_map.items():
                if key in col: rename_dict[col] = val
        
        df = df.rename(columns=rename_dict)
        df = df.dropna(subset=['id'])
        df = df.drop_duplicates(subset=['id'], keep='first')
        
        valid_cols = [c for c in df.columns if c in col_map.values()]
        df[valid_cols].to_sql('individuals', conn, if_exists='append', index=False)
        print(f"🐐 개체마스터 {len(df)}건 로드 완료")
    except Exception as e:
        print(f"❌ 개체마스터 로드 실패: {e}")

    # 2. Groups (그룹 구분)
    try:
        # 그룹 파일만 skiprows=1, header=None 적용
        df = pd.read_csv(files['groups'], skiprows=1, header=None)
        df = df.iloc[:, 0:4]
        df.columns = ['category', 'group_code', 'target_gender', 'description']
        
        df = df.dropna(subset=['group_code'])
        df.to_sql('groups', conn, if_exists='append', index=False)
        print(f"🏷️ 그룹정보 {len(df)}건 로드 완료")
    except Exception as e:
        print(f"❌ 그룹정보 로드 실패: {e}")

    # 3. Breeding (교배 이력)
    try:
        df = pd.read_csv(files['breeding'])
        df = clean_cols(df)
        
        col_map = {'교배ID': 'breeding_id', '그룹번호': 'group_code', '방번호': 'room_no', 
                   '종부수컷번호': 'male_id', '종부투입일': 'start_date', '종부퇴실일': 'end_date', 
                   '출산예정월': 'expected_birth_month', '결과': 'result', '비고': 'notes'}
        
        rename_dict = {c: val for c in df.columns for key, val in col_map.items() if key in c}
        df = df.rename(columns=rename_dict)
        
        df = df.dropna(subset=['breeding_id'])
        df = df[~df['breeding_id'].astype(str).str.contains('--')]
        
        valid_cols = [c for c in df.columns if c in col_map.values()]
        df[valid_cols].to_sql('breeding_events', conn, if_exists='append', index=False)
        print(f"❤️ 교배이력 {len(df)}건 로드 완료")
    except Exception as e:
        print(f"❌ 교배이력 로드 실패: {e}")

    # 4. Births (출산 이력)
    try:
        df = pd.read_csv(files['birth'])
        df = clean_cols(df)
        
        col_map = {'출산ID': 'birth_id', '모축번호': 'mother_id', '출산일': 'birth_date', 
                   '출산회차': 'birth_order', '생존암컷': 'live_female', '생존수컷': 'live_male', 
                   '사산암컷': 'dead_female', '사산수컷': 'dead_male', '총산자수': 'total_kids', 
                   '분만형태': 'delivery_type', '포유상태': 'nursing_status', '자축번호목록': 'kids_ids', '비고': 'notes'}
        
        rename_dict = {c: val for c in df.columns for key, val in col_map.items() if key in c}
        df = df.rename(columns=rename_dict)
        
        df = df.dropna(subset=['birth_id'])
        df = df[~df['birth_id'].astype(str).str.contains('--')]
        
        valid_cols = [c for c in df.columns if c in col_map.values()]
        df[valid_cols].to_sql('birth_events', conn, if_exists='append', index=False)
        print(f"👶 출산이력 {len(df)}건 로드 완료")
    except Exception as e:
        print(f"❌ 출산이력 로드 실패: {e}")

    # 5. Health (건강 이력)
    try:
        df = pd.read_csv(files['health'])
        df = clean_cols(df)
        
        col_map = {'일자': 'date', '개체번호': 'goat_id', '증상': 'symptom', '진단': 'diagnosis', 
                   '처방약': 'treatment', '결과': 'result', '비고': 'notes', '치료ID': 'treatment_id', '담당': 'manager'}
        
        rename_dict = {c: val for c in df.columns for key, val in col_map.items() if key in c}
        df = df.rename(columns=rename_dict)
        
        df = df.dropna(subset=['diagnosis', 'treatment'], how='all')
        
        valid_cols = [c for c in df.columns if c in col_map.values()]
        df[valid_cols].to_sql('health_logs', conn, if_exists='append', index=False)
        print(f"🏥 건강이력 {len(df)}건 로드 완료")
    except Exception as e:
        print(f"❌ 건강이력 로드 실패: {e}")

    # 6. Movements (이동 상세)
    try:
        df = pd.read_csv(files['movements'])
        df = clean_cols(df)
        
        col_map = {'이동ID': 'movement_code', '개체번호': 'goat_id', '일자': 'date', 
                   '유형': 'type', '상대처': 'destination'}
        
        rename_dict = {c: val for c in df.columns for key, val in col_map.items() if key in c}
        df = df.rename(columns=rename_dict)
        
        df = df.dropna(subset=['goat_id'])
        
        valid_cols = [c for c in df.columns if c in col_map.values()]
        df[valid_cols].to_sql('movements', conn, if_exists='append', index=False)
        print(f"🚚 이동이력 {len(df)}건 로드 완료")
    except Exception as e:
        print(f"❌ 이동이력 로드 실패: {e}")

    conn.commit()
    conn.close()
    print("\n🎉 모든 데이터 구축이 완료되었습니다! 'eco_farm.db' 파일이 생성되었습니다.")

if __name__ == "__main__":
    init_db()
    load_data()