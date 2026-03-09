import sqlite3
import pandas as pd
import os

DB_FILE = "eco_farm.db"

def inspect_db():
    if not os.path.exists(DB_FILE):
        print(f"❌ '{DB_FILE}' 파일을 찾을 수 없습니다. db.py를 먼저 실행했는지 확인하세요.")
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # 1. 생성된 테이블 목록 확인
    print("="*50)
    print("📂 [1] 생성된 테이블 목록")
    print("="*50)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    table_names = [t[0] for t in tables if t[0] != 'sqlite_sequence'] # sqlite_sequence는 내부 관리용이라 제외
    print(table_names)
    print("\n")

    # 2. 각 테이블별 데이터 조회 (상위 5건)
    print("="*50)
    print("🔍 [2] 테이블별 데이터 샘플 (상위 5건)")
    print("="*50)

    for table in table_names:
        print(f"\n📌 테이블: {table}")
        
        # 총 행 수 조회
        count = pd.read_sql(f"SELECT count(*) as cnt FROM {table}", conn).iloc[0]['cnt']
        print(f"   - 총 데이터 수: {count} 건")
        
        # 데이터 조회
        df = pd.read_sql(f"SELECT * FROM {table} LIMIT 5", conn)
        
        if not df.empty:
            print(df.to_string(index=False)) # 인덱스 없이 깔끔하게 출력
        else:
            print("   (데이터가 없습니다)")
        print("-" * 50)

    # 3. 데이터 연결 무결성 샘플 체크 (개체 <-> 출산)
    print("\n")
    print("="*50)
    print("🔗 [3] 데이터 연결 테스트 (개체마스터 + 출산이력 JOIN)")
    print("="*50)
    
    query = """
    SELECT 
        i.id as 개체번호, 
        i.breed as 품종, 
        b.birth_date as 출산일, 
        b.total_kids as 산자수 
    FROM individuals i
    JOIN birth_events b ON i.id = b.mother_id
    LIMIT 5
    """
    df_join = pd.read_sql(query, conn)
    
    if not df_join.empty:
        print(df_join.to_string(index=False))
    else:
        print("매칭되는 출산 이력 데이터가 없습니다. (데이터가 적어서 그럴 수 있습니다)")

    conn.close()

if __name__ == "__main__":
    inspect_db()