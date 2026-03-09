import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# --- 설정 ---
DB_FILE = "eco_farm.db"
st.set_page_config(
    page_title="에코팜 흑염소 관리",
    page_icon="🐐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- DB 연결 함수 ---
def get_connection():
    return sqlite3.connect(DB_FILE)

def run_query(query, params=None):
    conn = get_connection()
    try:
        if params:
            df = pd.read_sql(query, conn, params=params)
        else:
            df = pd.read_sql(query, conn)
        return df
    finally:
        conn.close()

def run_action(query, params):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        conn.commit()
        return True
    except Exception as e:
        st.error(f"DB 오류: {e}")
        return False
    finally:
        conn.close()

# --- 페이지: 대시보드 ---
def show_dashboard():
    st.title("📊 에코팜 현황 대시보드")
    st.markdown("---")

    # 1. 핵심 지표 (KPI)
    col1, col2, col3, col4 = st.columns(4)
    
    # 총 사육 두수
    df_total = run_query("SELECT count(*) as cnt FROM individuals WHERE status='사육'")
    total_cnt = df_total.iloc[0]['cnt']
    
    # 암컷/수컷
    df_gender = run_query("SELECT gender, count(*) as cnt FROM individuals WHERE status='사육' GROUP BY gender")
    female_cnt = df_gender[df_gender['gender'] == '암']['cnt'].sum() if not df_gender.empty else 0
    male_cnt = df_gender[df_gender['gender'] == '수']['cnt'].sum() if not df_gender.empty else 0
    
    # 이번 달 출산 예정 (교배이력 기반)
    current_month = datetime.now().strftime("%y-%m") # 예: 26-03
    df_birth_plan = run_query(f"SELECT count(*) as cnt FROM breeding_events WHERE expected_birth_month LIKE '{current_month}%'")
    birth_plan_cnt = df_birth_plan.iloc[0]['cnt']

    col1.metric("총 사육 두수", f"{total_cnt} 마리", "전체")
    col2.metric("암컷 (사육)", f"{female_cnt} 마리", f"{round(female_cnt/total_cnt*100, 1) if total_cnt else 0}%")
    col3.metric("수컷 (사육)", f"{male_cnt} 마리", f"{round(male_cnt/total_cnt*100, 1) if total_cnt else 0}%")
    col4.metric("이번 달 출산 예정", f"{birth_plan_cnt} 건", "교배 기준")

    # 2. 차트 영역
    st.subheader("📈 사육 현황 분석")
    c1, c2 = st.columns([1, 1])
    
    with c1:
        # 그룹별 두수 현황
        st.markdown("**그룹별 사육 두수**")
        df_group = run_query("""
            SELECT group_code, count(*) as cnt 
            FROM individuals 
            WHERE status='사육' 
            GROUP BY group_code 
            ORDER BY cnt DESC
        """)
        if not df_group.empty:
            fig_bar = px.bar(df_group, x='group_code', y='cnt', color='cnt', 
                             labels={'group_code': '그룹', 'cnt': '두수'}, template="plotly_white")
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("데이터가 없습니다.")

    with c2:
        # 품종 비율
        st.markdown("**품종별 비율**")
        df_breed = run_query("SELECT breed, count(*) as cnt FROM individuals WHERE status='사육' GROUP BY breed")
        if not df_breed.empty:
            fig_pie = px.pie(df_breed, values='cnt', names='breed', hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("데이터가 없습니다.")

    # 3. 최근 이슈 (건강/출산)
    st.markdown("---")
    st.subheader("🔔 최근 알림 (건강 이슈)")
    df_health = run_query("SELECT date, goat_id, symptom, diagnosis, result FROM health_logs ORDER BY date DESC LIMIT 5")
    if not df_health.empty:
        st.dataframe(df_health, use_container_width=True)
    else:
        st.success("최근 기록된 건강 이슈가 없습니다.")

# --- 페이지: 개체 관리 ---
def show_individuals():
    st.title("🐐 개체 통합 관리")
    
    # 검색 및 필터
    with st.expander("🔍 검색 및 필터", expanded=True):
        c1, c2 = st.columns([3, 1])
        with c1:
            search_term = st.text_input("개체번호 검색", placeholder="예: F0255")
        with c2:
            status_filter = st.selectbox("상태 필터", ["전체", "사육", "폐사", "출하", "거세대기"])

    # 쿼리 생성
    base_query = "SELECT * FROM individuals WHERE 1=1"
    params = []
    
    if search_term:
        base_query += " AND id LIKE ?"
        params.append(f"%{search_term}%")
    
    if status_filter != "전체":
        base_query += " AND status = ?"
        params.append(status_filter)
        
    df = run_query(base_query, params)
    
    # 메인 리스트 표시
    st.dataframe(
        df[['id', 'status', 'gender', 'breed', 'room_no', 'group_code', 'birth_date', 'mother_id']], 
        use_container_width=True,
        height=300
    )

    # 개체 상세 보기 및 수정
    if len(df) > 0:
        selected_id = st.selectbox("상세 정보를 볼 개체를 선택하세요", df['id'].tolist())
        
        if selected_id:
            st.markdown("---")
            goat_data = df[df['id'] == selected_id].iloc[0]
            
            c1, c2 = st.columns([1, 2])
            
            with c1:
                st.info(f"🏷️ **{goat_data['id']}** 상세 프로필")
                st.write(f"**상태:** {goat_data['status']}")
                st.write(f"**성별:** {goat_data['gender']}")
                st.write(f"**품종:** {goat_data['breed']}")
                st.write(f"**출생일:** {goat_data['birth_date']}")
                st.write(f"**모축:** {goat_data['mother_id']} / **종축:** {goat_data['father_id']}")
                
                # [수정 기능] 상태/방번호 변경
                with st.form("update_status_form"):
                    st.write("🔧 **정보 수정**")
                    new_status = st.selectbox("상태 변경", ["사육", "폐사", "출하", "격리", "거세대기"], index=0)
                    new_room = st.text_input("방 번호 변경", value=goat_data['room_no'])
                    new_note = st.text_area("비고 수정", value=goat_data['notes'] if goat_data['notes'] else "")
                    
                    if st.form_submit_button("저장하기"):
                        query = "UPDATE individuals SET status=?, room_no=?, notes=? WHERE id=?"
                        if run_action(query, (new_status, new_room, new_note, selected_id)):
                            st.success("정보가 업데이트되었습니다! (새로고침 시 반영)")
                            st.rerun()

            with c2:
                # 탭으로 이력 관리
                tab1, tab2, tab3 = st.tabs(["🏥 건강 이력", "👶 출산/교배 이력", "🚚 이동 이력"])
                
                with tab1:
                    hist_health = run_query("SELECT date, symptom, diagnosis, treatment FROM health_logs WHERE goat_id=?", (selected_id,))
                    if not hist_health.empty:
                        st.dataframe(hist_health)
                    else:
                        st.write("기록된 건강 이력이 없습니다.")
                
                with tab2:
                    if goat_data['gender'] == '암':
                        st.markdown("**출산 이력**")
                        hist_birth = run_query("SELECT birth_date, total_kids, live_male, live_female FROM birth_events WHERE mother_id=?", (selected_id,))
                        st.dataframe(hist_birth) if not hist_birth.empty else st.write("출산 기록 없음")
                    
                    st.markdown("**교배 정보**")
                    # 교배 정보는 수컷/암컷 모두 관련될 수 있음 (단, DB구조상 수컷ID or 그룹ID로 추적 필요)
                    # 여기선 단순화하여 그룹 정보 표시
                    st.write(f"현재 속한 그룹: **{goat_data['group_code']}**")

                with tab3:
                    hist_move = run_query("SELECT date, type, destination FROM movements WHERE goat_id=?", (selected_id,))
                    st.dataframe(hist_move) if not hist_move.empty else st.write("이동 기록 없음")

# --- 페이지: 전체 이력 조회 ---
def show_history():
    st.title("🗂️ 전체 이력 조회")
    
    tab_health, tab_birth, tab_move = st.tabs(["건강/진료", "출산/번식", "이동/입출하"])
    
    with tab_health:
        st.subheader("최근 건강 진료 기록")
        df = run_query("SELECT * FROM health_logs ORDER BY date DESC LIMIT 100")
        st.dataframe(df, use_container_width=True)
        
    with tab_birth:
        st.subheader("최근 출산 기록")
        df = run_query("SELECT * FROM birth_events ORDER BY birth_date DESC LIMIT 100")
        st.dataframe(df, use_container_width=True)
        
    with tab_move:
        st.subheader("최근 이동(입/출하) 기록")
        df = run_query("SELECT * FROM movements ORDER BY date DESC LIMIT 100")
        st.dataframe(df, use_container_width=True)

# --- 메인 실행 ---
def main():
    menu = st.sidebar.selectbox(
        "메뉴 선택", 
        ["대시보드", "개체 관리", "이력 조회"]
    )
    
    if menu == "대시보드":
        show_dashboard()
    elif menu == "개체 관리":
        show_individuals()
    elif menu == "이력 조회":
        show_history()

if __name__ == "__main__":
    main()