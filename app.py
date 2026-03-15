import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime

# --- 페이지 설정 ---
st.set_page_config(
    page_title="에코팜 흑염소 관리 솔루션",
    page_icon="🐐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 디자인 커스텀 (CSS) ---
st.markdown("""
<style>
    /* 전체 배경 및 폰트 */
    .stApp {
        background-color: #f8f9fa;
    }
    h1, h2, h3 {
        font-family: 'Pretendard', sans-serif;
        color: #2d3436;
    }
    
    /* KPI 카드 스타일 */
    div.css-1r6slb0 {
        background-color: white;
        border: 1px solid #dfe6e9;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        border-radius: 10px;
        padding: 15px;
    }
    
    /* 사이드바 스타일 */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #f1f2f6;
    }
    
    /* 탭 스타일 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        white-space: pre-wrap;
        background-color: #ffffff;
        border-radius: 8px;
        color: #636e72;
        font-weight: 600;
        border: 1px solid #dfe6e9;
        padding: 0 20px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #00b894 !important;
        color: white !important;
        border: none;
    }
    
    /* 커스텀 박스 클래스 */
    .info-box {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.04);
        border: 1px solid #f1f2f6;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# --- DB 설정 ---
DB_FILE = "eco_farm.db"

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

# --- 컴포넌트: KPI 카드 ---
def metric_card(title, value, sub_value, icon, color="blue"):
    st.markdown(f"""
    <div style="background-color: white; padding: 20px; border-radius: 10px; border-left: 5px solid {color}; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="font-size: 14px; color: #636e72; font-weight: 600;">{title}</span>
            <span style="font-size: 20px;">{icon}</span>
        </div>
        <div style="font-size: 28px; font-weight: 700; color: #2d3436; margin: 10px 0;">{value}</div>
        <div style="font-size: 13px; color: {color};">
            {sub_value}
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- 페이지: 대시보드 ---
def show_dashboard():
    st.title("📊 에코팜 대시보드")
    st.caption(f"마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    st.write("") 

    # 1. KPI 영역
    col1, col2, col3, col4 = st.columns(4)
    
    df_total = run_query("SELECT count(*) as cnt FROM individuals WHERE status='사육'")
    total_cnt = df_total.iloc[0]['cnt']
    
    df_gender = run_query("SELECT gender, count(*) as cnt FROM individuals WHERE status='사육' GROUP BY gender")
    female_cnt = df_gender[df_gender['gender'] == '암']['cnt'].sum() if not df_gender.empty else 0
    male_cnt = df_gender[df_gender['gender'] == '수']['cnt'].sum() if not df_gender.empty else 0
    
    current_month = datetime.now().strftime("%y-%m")
    df_birth = run_query(f"SELECT count(*) as cnt FROM breeding_events WHERE expected_birth_month LIKE '{current_month}%'")
    birth_cnt = df_birth.iloc[0]['cnt']

    with col1:
        metric_card("총 사육 두수", f"{total_cnt}두", "전체 사육 개체", "🐐", "#00b894")
    with col2:
        metric_card("암컷 (모축/육성)", f"{female_cnt}두", f"점유율 {round(female_cnt/total_cnt*100) if total_cnt else 0}%", "🚺", "#fd79a8")
    with col3:
        metric_card("수컷 (종모/비육)", f"{male_cnt}두", f"점유율 {round(male_cnt/total_cnt*100) if total_cnt else 0}%", "🚹", "#0984e3")
    with col4:
        metric_card("이번 달 출산 예정", f"{birth_cnt}건", "교배 이력 기준", "📅", "#fdcb6e")

    st.write("")
    st.write("")

    # 2. 분석 차트 영역
    c1, c2 = st.columns([2, 1])
    
    with c1:
        st.markdown("##### 🏘️ 그룹별 사육 현황")
        df_group = run_query("""
            SELECT group_code, count(*) as cnt 
            FROM individuals 
            WHERE status='사육' 
            GROUP BY group_code 
            ORDER BY cnt DESC
        """)
        if not df_group.empty:
            fig = px.bar(df_group, x='group_code', y='cnt', text='cnt',
                         color='cnt', color_continuous_scale='Mint',
                         labels={'group_code': '그룹', 'cnt': '마리 수'})
            fig.update_layout(plot_bgcolor='white', showlegend=False, height=350)
            fig.update_traces(textposition='outside', marker_color='#00b894')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("데이터가 없습니다.")

    with c2:
        st.markdown("##### 🧬 품종 비율")
        df_breed = run_query("SELECT breed, count(*) as cnt FROM individuals WHERE status='사육' GROUP BY breed")
        if not df_breed.empty:
            fig = px.pie(df_breed, values='cnt', names='breed', hole=0.6,
                         color_discrete_sequence=px.colors.qualitative.Pastel)
            fig.update_layout(height=350, showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("데이터가 없습니다.")

    # 3. 알림 영역
    st.markdown("##### 🔔 최근 건강 이슈 (최근 5건)")
    df_health = run_query("SELECT date as '일자', goat_id as '개체번호', symptom as '증상', diagnosis as '진단', result as '결과' FROM health_logs ORDER BY date DESC LIMIT 5")
    
    if not df_health.empty:
        st.dataframe(
            df_health, 
            use_container_width=True,
            hide_index=True,
            column_config={
                "결과": st.column_config.TextColumn(
                    "결과",
                    help="치료 결과",
                    validate="^(회복|치료중)$"
                )
            }
        )
    else:
        st.info("최근 기록된 건강 이슈가 없습니다.")

# --- 페이지: 개체 관리 ---
def show_individuals():
    st.title("🐐 개체 통합 관리")
    
    # 상단 검색 바
    with st.container():
        st.markdown('<div class="info-box">', unsafe_allow_html=True)
        c1, c2, c3 = st.columns([4, 2, 1])
        with c1:
            search_term = st.text_input("🔎 개체번호 검색", placeholder="개체번호를 입력하세요 (예: F0255)")
        with c2:
            status_filter = st.selectbox("상태 필터", ["전체", "사육", "폐사", "출하", "거세대기", "격리"])
        with c3:
            st.write("")
            st.write("")
            st.button("새로고침", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # 쿼리 실행
    base_query = "SELECT * FROM individuals WHERE 1=1"
    params = []
    if search_term:
        base_query += " AND id LIKE ?"
        params.append(f"%{search_term}%")
    if status_filter != "전체":
        base_query += " AND status = ?"
        params.append(status_filter)
        
    df = run_query(base_query, params)
    
    # 레이아웃 분할
    col_list, col_detail = st.columns([1, 2])
    
    with col_list:
        st.markdown(f"**검색 결과** ({len(df)}건)")
        
        if not df.empty:
            st.dataframe(
                df[['id', 'gender', 'room_no']], 
                use_container_width=True, 
                height=600,
                hide_index=True
            )
            selected_id_val = st.selectbox("👉 상세 조회할 개체 선택", df['id'].tolist())
        else:
            st.warning("검색 결과가 없습니다.")
            selected_id_val = None

    with col_detail:
        if selected_id_val:
            goat_data = df[df['id'] == selected_id_val].iloc[0]
            
            # 프로필 카드 디자인
            st.markdown(f"""
            <div class="info-box">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <h2 style="margin:0; color:#2d3436;">🏷️ {goat_data['id']}</h2>
                    <span style="background-color:#00b894; color:white; padding:5px 10px; border-radius:15px; font-size:14px;">{goat_data['status']}</span>
                </div>
                <hr style="margin:15px 0; border:none; border-top:1px solid #dfe6e9;">
                <div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px;">
                    <div><b>성별:</b> {goat_data['gender']}</div>
                    <div><b>품종:</b> {goat_data['breed']}</div>
                    <div><b>방번호:</b> {goat_data['room_no']}호</div>
                    <div><b>그룹:</b> {goat_data['group_code']}</div>
                    <div><b>출생일:</b> {goat_data['birth_date']}</div>
                    <div><b>부/모:</b> {goat_data['father_id']} / {goat_data['mother_id']}</div>
                </div>
                <div style="margin-top:15px; color:#636e72; font-size:14px;">
                    📝 {goat_data['notes'] if goat_data['notes'] else "특이사항 없음"}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # 탭 인터페이스
            tab1, tab2, tab3, tab4 = st.tabs(["📋 정보 수정", "🏥 건강 기록", "👶 번식 기록", "🚚 이동 기록"])
            
            with tab1:
                with st.form("edit_form"):
                    c1, c2 = st.columns(2)
                    with c1:
                        new_status = st.selectbox("상태 변경", ["사육", "폐사", "출하", "격리", "거세대기"], index=["사육", "폐사", "출하", "격리", "거세대기"].index(goat_data['status']) if goat_data['status'] in ["사육", "폐사", "출하", "격리", "거세대기"] else 0)
                    with c2:
                        new_room = st.text_input("방 번호", value=goat_data['room_no'])
                    new_note = st.text_area("비고 (특이사항)", value=goat_data['notes'] if goat_data['notes'] else "")
                    
                    if st.form_submit_button("💾 변경사항 저장", use_container_width=True):
                        query = "UPDATE individuals SET status=?, room_no=?, notes=? WHERE id=?"
                        if run_action(query, (new_status, new_room, new_note, selected_id_val)):
                            st.success("저장되었습니다.")
                            st.rerun()

            with tab2:
                hist_health = run_query("SELECT date as 일자, symptom as 증상, diagnosis as 진단, treatment as 처방 FROM health_logs WHERE goat_id=? ORDER BY date DESC", (selected_id_val,))
                # ✅ 수정됨: 명시적인 if-else 블록 사용
                if not hist_health.empty:
                    st.dataframe(hist_health, use_container_width=True, hide_index=True)
                else:
                    st.info("기록이 없습니다.")

            with tab3:
                if goat_data['gender'] == '암':
                    hist_birth = run_query("SELECT birth_date as 출산일, total_kids as 산자수, live_male as '수(생존)', live_female as '암(생존)' FROM birth_events WHERE mother_id=? ORDER BY birth_date DESC", (selected_id_val,))
                    # ✅ 수정됨
                    if not hist_birth.empty:
                        st.dataframe(hist_birth, use_container_width=True, hide_index=True)
                    else:
                        st.info("출산 기록이 없습니다.")
                else:
                    st.info("수컷 개체입니다.")

            with tab4:
                hist_move = run_query("SELECT date as 일자, type as 유형, destination as 장소 FROM movements WHERE goat_id=? ORDER BY date DESC", (selected_id_val,))
                # ✅ 수정됨
                if not hist_move.empty:
                    st.dataframe(hist_move, use_container_width=True, hide_index=True)
                else:
                    st.info("이동 기록이 없습니다.")
        else:
            st.info("👈 왼쪽 목록에서 개체를 선택해주세요.")

# --- 페이지: 이력 조회 ---
def show_history():
    st.title("🗂️ 전체 데이터 조회")
    
    st.markdown("""
    <div class="info-box">
        각 분야별 전체 이력을 엑셀처럼 조회할 수 있습니다.
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["🏥 건강/진료", "👶 출산/번식", "🚚 이동/입출하"])
    
    with tab1:
        df = run_query("SELECT date, goat_id, symptom, diagnosis, treatment, result, manager FROM health_logs ORDER BY date DESC LIMIT 300")
        st.dataframe(df, use_container_width=True, height=500)
    
    with tab2:
        df = run_query("SELECT birth_date, mother_id, birth_order, total_kids, live_male, live_female, delivery_type FROM birth_events ORDER BY birth_date DESC LIMIT 300")
        st.dataframe(df, use_container_width=True, height=500)
        
    with tab3:
        df = run_query("SELECT date, goat_id, type, destination, notes FROM movements ORDER BY date DESC LIMIT 300")
        st.dataframe(df, use_container_width=True, height=500)

# --- 메인 실행 ---
def main():
    with st.sidebar:
        st.title("🐐 ECO FARM")
        st.markdown("---")
        menu = st.radio("MENU", ["대시보드", "개체 관리", "이력 조회"], index=0)
        st.markdown("---")
        st.caption("© 2026 Eco Farm Solution")

    if menu == "대시보드":
        show_dashboard()
    elif menu == "개체 관리":
        show_individuals()
    elif menu == "이력 조회":
        show_history()

if __name__ == "__main__":
    main()