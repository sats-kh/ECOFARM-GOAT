import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# --- 페이지 설정 ---
st.set_page_config(
    page_title="에코팜 흑염소 관리 솔루션",
    page_icon="🐐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 디자인 커스텀 (CSS) ---
# 여기서부터 HTML/CSS를 통해 모바일 반응형 Grid를 설정합니다.
st.markdown("""
<style>
    /* 전체 배경 및 폰트 */
    .stApp {
        background-color: #f4f6f9;
    }
    h1, h2, h3, h4, h5 {
        font-family: 'Pretendard', 'Malgun Gothic', sans-serif;
        color: #2c3e50;
    }
    
    /* 사이드바 스타일 */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e1e8ed;
    }

    /* ---------------------------------------------------
       반응형 Grid 시스템 (PC 4열, 모바일 2열)
       --------------------------------------------------- */
    .grid-container-4 {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 15px;
        margin-bottom: 20px;
    }
    .grid-container-3 {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 15px;
        margin-top: 20px;
        margin-bottom: 30px;
    }
    
    /* 화면이 768px 이하(모바일/태블릿)일 때 2열로 변경 */
    @media (max-width: 768px) {
        .grid-container-4 {
            grid-template-columns: repeat(2, 1fr);
        }
        .grid-container-3 {
            grid-template-columns: repeat(1, 1fr); /* 안내 카드는 세로 1줄로 */
        }
    }

    /* --- 총괄 지표 카드 (상단 4개) --- */
    .metric-card-main {
        background-color: white;
        border-radius: 12px;
        padding: 20px 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.03);
        border: 1px solid #ecf0f1;
        text-align: center;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .metric-main-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #7f8c8d;
        margin-bottom: 5px;
    }
    .metric-main-value {
        font-size: 2.2rem;
        font-weight: 800;
        color: #2c3e50;
    }

    /* --- 서브 지표 카드 (출산, 입하 등) --- */
    .sub-metric-card {
        background-color: white;
        border: 1px solid #ecf0f1;
        border-radius: 10px;
        padding: 18px 10px;
        text-align: center;
        box-shadow: 0 2px 5px rgba(0,0,0,0.02);
        display: flex;
        flex-direction: column;
        justify-content: center;
        height: 100%;
    }
    .sub-metric-title {
        font-size: 16px;
        font-weight: 800;
        color: #34495e;
        margin-bottom: 8px;
    }
    .sub-metric-detail {
        font-size: 13px;
        color: #7f8c8d;
        font-weight: 500;
    }

    /* 커스텀 박스 (테이블 컨테이너 등) */
    .info-box {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.03);
        border: 1px solid #ecf0f1;
        margin-bottom: 20px;
        height: 100%;
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

# --- 도넛 차트 생성 헬퍼 함수 ---
def create_donut_chart(labels, values, title, hole_size=0.6):
    if sum(values) == 0:
        labels, values = ["데이터 없음"], [1]
        colors = ['#ecf0f1']
    else:
        colors = px.colors.qualitative.Pastel

    fig = go.Figure(data=[go.Pie(
        labels=labels, 
        values=values, 
        hole=hole_size,
        textinfo='label+value' if sum(values) > 0 else 'none',
        textposition='inside',
        marker=dict(colors=colors, line=dict(color='#ffffff', width=2)),
        insidetextorientation='horizontal'
    )])
    
    fig.update_layout(
        title_text=f"<b>{title}</b>",
        title_x=0.5,
        title_y=0.95,
        title_font=dict(size=15, color='#2c3e50'),
        showlegend=False,
        margin=dict(t=50, b=10, l=10, r=10),
        height=260,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig

# --- 페이지: 대시보드 ---
def show_dashboard():
    today_str = datetime.now().strftime("%Y년 %m월 %d일")
    st.markdown(f"### 📅 {today_str} 에코팜 축사 개체 현황")
    st.write("") 

    # [DB Data Fetching]
    df_totals = run_query("SELECT gender, count(*) as cnt FROM individuals WHERE status='사육' GROUP BY gender")
    total_cnt = df_totals['cnt'].sum() if not df_totals.empty else 0
    f_cnt = df_totals[df_totals['gender'] == '암']['cnt'].sum() if not df_totals.empty else 0
    m_cnt = df_totals[df_totals['gender'] == '수']['cnt'].sum() if not df_totals.empty else 0
    c_cnt = df_totals[df_totals['gender'] == '거세']['cnt'].sum() if not df_totals.empty else 0

    df_birth = run_query("SELECT IFNULL(SUM(total_kids),0) as tot, IFNULL(SUM(live_female),0) as f, IFNULL(SUM(live_male),0) as m FROM birth_events")
    birth_tot = int(df_birth.iloc[0]['tot'])
    birth_f = int(df_birth.iloc[0]['f'])
    birth_m = int(df_birth.iloc[0]['m'])
    
    inbound_cnt = run_query("SELECT count(*) as cnt FROM movements WHERE type='입하'").iloc[0]['cnt']
    outbound_cnt = run_query("SELECT count(*) as cnt FROM individuals WHERE status='출하'").iloc[0]['cnt']
    dead_cnt = run_query("SELECT count(*) as cnt FROM individuals WHERE status='폐사'").iloc[0]['cnt']

    # 1. 상단: 총괄 현황 (HTML/CSS Grid로 렌더링 - 모바일에서 2x2 반응형)
    st.markdown("##### 📊 사육 총괄 현황")
    st.markdown(f"""
    <div class="grid-container-4">
        <div class="metric-card-main">
            <div class="metric-main-title">총 사육 두수</div>
            <div class="metric-main-value">{total_cnt:,}</div>
        </div>
        <div class="metric-card-main">
            <div class="metric-main-title">암컷</div>
            <div class="metric-main-value">{f_cnt:,}</div>
        </div>
        <div class="metric-card-main">
            <div class="metric-main-title">수컷</div>
            <div class="metric-main-value">{m_cnt:,}</div>
        </div>
        <div class="metric-card-main">
            <div class="metric-main-title">거세</div>
            <div class="metric-main-value">{c_cnt:,}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2. 중단: 상세 증감 내역 (서브 지표) (HTML/CSS Grid로 렌더링)
    st.markdown(f"""
    <div class="grid-container-4">
        <div class="sub-metric-card">
            <div class="sub-metric-title">🐣 누적 출산: {birth_tot}</div>
            <div class="sub-metric-detail">암 {birth_f} &nbsp;|&nbsp; 수 {birth_m}</div>
        </div>
        <div class="sub-metric-card">
            <div class="sub-metric-title">📥 누적 입하: {inbound_cnt}</div>
            <div class="sub-metric-detail">이동 내역 기준</div>
        </div>
        <div class="sub-metric-card">
            <div class="sub-metric-title">✝️ 누적 폐사: {dead_cnt}</div>
            <div class="sub-metric-detail">상태: 폐사 기준</div>
        </div>
        <div class="sub-metric-card">
            <div class="sub-metric-title">📤 누적 출하: {outbound_cnt}</div>
            <div class="sub-metric-detail">상태: 출하 기준</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr style='margin: 30px 0; border: none; border-top: 1px solid #e1e8ed;'>", unsafe_allow_html=True)

    # [DB Data for Charts]
    df_f = run_query("SELECT breed, group_code FROM individuals WHERE status='사육' AND gender='암'")
    f_child = len(df_f[df_f['group_code'] == 'ETCF'])
    f_adult = len(df_f) - f_child
    f_breeds = df_f['breed'].value_counts()
    
    df_m = run_query("SELECT group_code FROM individuals WHERE status='사육' AND gender='수'")
    m_special = len(df_m[df_m['group_code'].isin(['SGOAT1', 'SGOAT2'])])
    m_other = len(df_m[df_m['group_code'] == 'SBOER'])
    m_child = len(df_m[df_m['group_code'] == 'ETCM'])

    df_c = run_query("SELECT group_code, status FROM individuals WHERE gender='거세' OR status='거세대기'")
    c_weedat = len(df_c[df_c['group_code'] == 'WEEDAT'])
    c_wboer_done = len(df_c[(df_c['group_code'] == 'WBOER') & (df_c['status'] == '사육')])
    c_wgoat_wait = len(df_c[(df_c['group_code'] == 'WGOAT') & (df_c['status'] == '거세대기')])
    c_wboer_wait = len(df_c[(df_c['group_code'] == 'WBOER') & (df_c['status'] == '거세대기')])

    # 3. 하단: 도넛 차트 4개 (Streamlit Columns 사용, 단, st.columns는 모바일 1열 고정이므로 이를 우회하려면 CSS가 필요.
    # 하지만 Plotly 그래프는 HTML 컨테이너 안에 넣기 까다로우므로 Streamlit의 모바일 최적화 기능을 활용하여 모바일에서는 세로로 보이되 깔끔하게 떨어지도록 유지합니다.
    # 만약 차트도 모바일 2열을 원하시면 화면이 너무 작아 차트 글씨가 깨집니다. 차트는 모바일에서 1열로 떨어지는 것이 UX상 맞습니다.)
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        fig_f1 = create_donut_chart(['성축', '자축'], [f_adult, f_child], f"암컷 연령별 ({f_cnt})")
        st.plotly_chart(fig_f1, use_container_width=True)

    with c2:
        fig_f2 = create_donut_chart(f_breeds.index.tolist(), f_breeds.values.tolist(), f"암컷 품종별 ({f_cnt})")
        st.plotly_chart(fig_f2, use_container_width=True)

    with c3:
        fig_m = create_donut_chart(['특종묘', '그외종묘', '자축'], [m_special, m_other, m_child], f"수컷 종별 ({m_cnt})")
        st.plotly_chart(fig_m, use_container_width=True)

    with c4:
        fig_c = create_donut_chart(['독거세반', '그리거세반', '특거세전', '그리거세전'], 
                                   [c_weedat, c_wboer_done, c_wgoat_wait, c_wboer_wait], f"거세 분류 ({c_cnt})")
        st.plotly_chart(fig_c, use_container_width=True)

    # 4. 차트 하단 안내 카드 3종 세트 (HTML/CSS Grid로 렌더링 - PC 3열, 모바일 1열)
    st.markdown("""
    <div class="grid-container-3">
        <div style="background-color: #fff8e1; padding: 18px; border-radius: 8px; border-left: 5px solid #ffca28; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
            <b style="color:#f39c12; font-size:15px;">💡 대시보드 집계 기준</b><br><br>
            <span style="font-size:13px; color:#555; line-height:1.6;">
            • <b>성축/자축(암):</b> ETCF 그룹을 자축으로, 그 외 성축으로 분류<br>
            • <b>상단 총괄:</b> [현재상태=사육] 인 개체만 실시간 카운트<br>
            • <b>누적 통계:</b> 과거 이력이 모두 포함된 전체 누적 합계
            </span>
        </div>
        <div style="background-color: #e3f2fd; padding: 18px; border-radius: 8px; border-left: 5px solid #64b5f6; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
            <b style="color:#2980b9; font-size:15px;">📌 수컷 분류 기준</b><br><br>
            <span style="font-size:13px; color:#555; line-height:1.6;">
            • <b>특종묘:</b> SGOAT1, SGOAT2 그룹 소속<br>
            • <b>그외종묘:</b> SBOER 그룹 소속<br>
            • <b>자축:</b> ETCM 그룹 소속
            </span>
        </div>
        <div style="background-color: #e8f5e9; padding: 18px; border-radius: 8px; border-left: 5px solid #81c784; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
            <b style="color:#27ae60; font-size:15px;">✂️ 거세 용어 기준</b><br><br>
            <span style="font-size:13px; color:#555; line-height:1.6;">
            • <b>독거세반:</b> WEEDAT 그룹<br>
            • <b>그리거세반:</b> WBOER 그룹 (사육 중)<br>
            • <b>특/그리거세전:</b> WGOAT/WBOER 중 '거세대기'
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)


# --- 페이지: 개체 관리 ---
def show_individuals():
    st.title("🐐 개체 통합 관리")
    
    with st.container():
        st.markdown('<div class="info-box" style="padding: 15px;">', unsafe_allow_html=True)
        c1, c2, c3 = st.columns([4, 2, 1])
        with c1:
            search_term = st.text_input("🔎 개체번호 검색", placeholder="예: F0255")
        with c2:
            status_filter = st.selectbox("상태 필터", ["전체", "사육", "폐사", "출하", "거세대기", "격리"])
        with c3:
            st.write("")
            st.write("")
            st.button("🔄 새로고침", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    base_query = "SELECT * FROM individuals WHERE 1=1"
    params = []
    if search_term:
        base_query += " AND id LIKE ?"
        params.append(f"%{search_term}%")
    if status_filter != "전체":
        base_query += " AND status = ?"
        params.append(status_filter)
        
    df = run_query(base_query, params)
    
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
            
            st.markdown(f"""
            <div class="info-box">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <h2 style="margin:0; color:#2c3e50; font-weight:800;">🏷️ {goat_data['id']}</h2>
                    <span style="background-color:#00b894; color:white; padding:6px 14px; border-radius:20px; font-size:14px; font-weight:bold;">{goat_data['status']}</span>
                </div>
                <hr style="margin:15px 0; border:none; border-top:1px solid #ecf0f1;">
                <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap:12px; font-size:15px; color:#34495e;">
                    <div><span style="color:#7f8c8d;">성별:</span> <b>{goat_data['gender']}</b></div>
                    <div><span style="color:#7f8c8d;">품종:</span> <b>{goat_data['breed']}</b></div>
                    <div><span style="color:#7f8c8d;">방번호:</span> <b>{goat_data['room_no']}호</b></div>
                    <div><span style="color:#7f8c8d;">그룹:</span> <b>{goat_data['group_code']}</b></div>
                    <div><span style="color:#7f8c8d;">출생일:</span> <b>{goat_data['birth_date']}</b></div>
                    <div><span style="color:#7f8c8d;">부/모:</span> <b>{goat_data['father_id']} / {goat_data['mother_id']}</b></div>
                </div>
                <div style="margin-top:15px; padding:10px; background-color:#f8f9fa; border-radius:8px; color:#7f8c8d; font-size:14px;">
                    📝 {goat_data['notes'] if goat_data['notes'] else "기록된 특이사항이 없습니다."}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            tab1, tab2, tab3, tab4 = st.tabs(["📋 정보 수정", "🏥 건강 기록", "👶 번식 기록", "🚚 이동 기록"])
            
            with tab1:
                with st.form("edit_form"):
                    c1, c2 = st.columns(2)
                    with c1:
                        status_opts = ["사육", "폐사", "출하", "격리", "거세대기"]
                        idx = status_opts.index(goat_data['status']) if goat_data['status'] in status_opts else 0
                        new_status = st.selectbox("상태 변경", status_opts, index=idx)
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
                if not hist_health.empty:
                    st.dataframe(hist_health, use_container_width=True, hide_index=True)
                else:
                    st.info("건강 이력이 없습니다.")

            with tab3:
                if goat_data['gender'] == '암':
                    hist_birth = run_query("SELECT birth_date as 출산일, total_kids as 산자수, live_male as '수(생존)', live_female as '암(생존)' FROM birth_events WHERE mother_id=? ORDER BY birth_date DESC", (selected_id_val,))
                    if not hist_birth.empty:
                        st.dataframe(hist_birth, use_container_width=True, hide_index=True)
                    else:
                        st.info("출산 기록이 없습니다.")
                else:
                    st.info("수컷/거세 개체는 출산 기록이 없습니다.")

            with tab4:
                hist_move = run_query("SELECT date as 일자, type as 유형, destination as 장소 FROM movements WHERE goat_id=? ORDER BY date DESC", (selected_id_val,))
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
        각 분야별 전체 이력을 엑셀처럼 한눈에 조회할 수 있습니다.
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["🏥 건강/진료", "👶 출산/번식", "🚚 이동/입출하"])
    
    with tab1:
        df = run_query("SELECT date as 일자, goat_id as 개체번호, symptom as 증상, diagnosis as 진단, treatment as 처방, result as 결과, manager as 담당자 FROM health_logs ORDER BY date DESC LIMIT 300")
        st.dataframe(df, use_container_width=True, height=500, hide_index=True)
    
    with tab2:
        df = run_query("SELECT birth_date as 출산일, mother_id as 모축번호, birth_order as 회차, total_kids as 산자수, live_male as 수생존, live_female as 암생존, delivery_type as 분만형태 FROM birth_events ORDER BY birth_date DESC LIMIT 300")
        st.dataframe(df, use_container_width=True, height=500, hide_index=True)
        
    with tab3:
        df = run_query("SELECT date as 일자, goat_id as 개체번호, type as 유형, destination as 목적지, notes as 비고 FROM movements ORDER BY date DESC LIMIT 300")
        st.dataframe(df, use_container_width=True, height=500, hide_index=True)

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