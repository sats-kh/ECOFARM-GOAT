"""
app.py - 에코팜 흑염소 관리 솔루션 메인 애플리케이션
상용화 버전 v1.0
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import os

# --- DB 및 유틸 초기화 ---
from db_init import init_db, DB_FILE
from utils import (
    run_query, run_action, get_dashboard_stats,
    paginate_data, sort_data, build_search_query,
    export_to_excel, export_to_csv, get_full_export,
    validate_goat_id, check_duplicate_goat_id, log_change,
    get_farm_list, get_group_codes, get_individual_summary,
    get_next_id, ensure_db, validate_date
)

# DB 초기화 (최초 실행 시)
ensure_db()

# ================================================================
# 페이지 설정
# ================================================================
st.set_page_config(
    page_title="에코팜 흑염소 관리 솔루션",
    page_icon="🐐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================================================================
# CSS 커스텀 스타일
# ================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700;900&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Noto Sans KR', 'Malgun Gothic', sans-serif;
    }
    .stApp { background-color: #f0f2f6; }
    
    /* 사이드바 */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a2a1a 0%, #2d4a2d 100%);
    }
    section[data-testid="stSidebar"] * { color: #e8f5e9 !important; }
    section[data-testid="stSidebar"] .stRadio label { 
        font-size: 15px; font-weight: 500; padding: 6px 0;
    }
    section[data-testid="stSidebar"] hr { border-color: #4a7a4a !important; }
    
    /* 메트릭 카드 그리드 */
    .grid-4 { display: grid; grid-template-columns: repeat(4,1fr); gap: 14px; margin-bottom: 18px; }
    .grid-3 { display: grid; grid-template-columns: repeat(3,1fr); gap: 14px; margin-bottom: 18px; }
    .grid-2 { display: grid; grid-template-columns: repeat(2,1fr); gap: 14px; margin-bottom: 18px; }
    @media(max-width:768px) {
        .grid-4 { grid-template-columns: repeat(2,1fr); }
        .grid-3 { grid-template-columns: 1fr; }
        .grid-2 { grid-template-columns: 1fr; }
    }
    
    /* 카드 스타일 */
    .card-main {
        background: white; border-radius: 14px; padding: 22px 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06); border: 1px solid #e8ecf0;
        text-align: center;
    }
    .card-main .label { font-size: 13px; font-weight: 600; color: #8a9bb0; margin-bottom: 6px; }
    .card-main .value { font-size: 2.4rem; font-weight: 900; color: #1a3a1a; line-height: 1; }
    .card-main .sub   { font-size: 12px; color: #a0adb8; margin-top: 4px; }
    
    .card-event {
        background: white; border-radius: 12px; padding: 18px 14px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.04); border: 1px solid #e8ecf0;
        text-align: center;
    }
    .card-event .etitle { font-size: 14px; font-weight: 800; color: #2d4a2d; margin-bottom: 6px; }
    .card-event .evalue { font-size: 1.6rem; font-weight: 900; color: #2d7a2d; }
    .card-event .esub   { font-size: 12px; color: #8a9bb0; }
    
    /* 섹션 헤더 */
    .section-header {
        font-size: 16px; font-weight: 800; color: #1a3a1a;
        border-left: 4px solid #2d7a2d; padding-left: 10px;
        margin: 20px 0 12px 0;
    }
    
    /* 상태 뱃지 */
    .badge {
        display: inline-block; padding: 3px 12px; border-radius: 20px;
        font-size: 12px; font-weight: 700;
    }
    .badge-사육 { background: #e8f5e9; color: #2d7a2d; }
    .badge-폐사 { background: #fce4ec; color: #c62828; }
    .badge-출하 { background: #e3f2fd; color: #1565c0; }
    .badge-격리 { background: #fff8e1; color: #f57f17; }
    .badge-거세대기 { background: #f3e5f5; color: #6a1b9a; }
    
    /* 정보 박스 */
    .info-box {
        background: white; padding: 20px; border-radius: 14px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05); border: 1px solid #e8ecf0;
        margin-bottom: 16px;
    }
    
    /* 버튼 스타일 오버라이드 */
    .stButton > button {
        border-radius: 8px; font-weight: 600;
        transition: all 0.2s;
    }
    
    /* 알림 카드 */
    .alert-card {
        padding: 14px 18px; border-radius: 10px; margin-bottom: 10px;
        border-left: 5px solid;
    }
    .alert-info   { background: #e3f2fd; border-color: #1976d2; }
    .alert-warn   { background: #fff8e1; border-color: #f9a825; }
    .alert-success{ background: #e8f5e9; border-color: #388e3c; }
    .alert-danger { background: #fce4ec; border-color: #d32f2f; }
    
    /* 탭 스타일 */
    .stTabs [data-baseweb="tab"] { font-weight: 600; font-size: 14px; }
    
    /* 다운로드 버튼 강조 */
    .download-section {
        background: linear-gradient(135deg, #e8f5e9, #f1f8e9);
        border: 1px solid #a5d6a7; border-radius: 12px; padding: 16px;
    }
    
    /* 페이지 타이틀 */
    .page-title {
        font-size: 1.8rem; font-weight: 900; color: #1a3a1a;
        margin-bottom: 4px;
    }
    .page-subtitle { font-size: 14px; color: #8a9bb0; margin-bottom: 20px; }
    
    /* 개체 상세 카드 */
    .goat-detail-card {
        background: linear-gradient(135deg, #f8fffe, #f0faf0);
        border: 1px solid #a5d6a7; border-radius: 16px; padding: 24px;
        margin-bottom: 16px;
    }
</style>
""", unsafe_allow_html=True)


# ================================================================
# 세션 상태 초기화
# ================================================================
if 'farm_id' not in st.session_state:
    st.session_state.farm_id = 'FARM01'
if 'menu' not in st.session_state:
    st.session_state.menu = '대시보드'


# ================================================================
# 헬퍼: 도넛 차트
# ================================================================
def make_donut(labels, values, title, height=250):
    total = sum(values)
    if total == 0:
        labels, values = ["데이터 없음"], [1]
        colors = ['#ecf0f1']
    else:
        colors = ['#2d7a2d', '#66bb6a', '#a5d6a7', '#c8e6c9', '#81c784', '#4caf50']

    fig = go.Figure(data=[go.Pie(
        labels=labels, values=values, hole=0.62,
        textinfo='label+value' if total > 0 else 'none',
        textposition='inside',
        marker=dict(colors=colors[:len(labels)], line=dict(color='#fff', width=2)),
        insidetextorientation='horizontal',
    )])
    fig.update_layout(
        title_text=f"<b>{title}</b>", title_x=0.5, title_y=0.97,
        title_font=dict(size=13, color='#2c3e50'),
        showlegend=False,
        margin=dict(t=45, b=5, l=5, r=5),
        height=height,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig


# ================================================================
# 헬퍼: 상태 뱃지
# ================================================================
def status_badge(status: str) -> str:
    cls = f"badge-{status}" if status in ['사육','폐사','출하','격리','거세대기'] else "badge"
    color_map = {'사육':'#2d7a2d','폐사':'#c62828','출하':'#1565c0','격리':'#f57f17','거세대기':'#6a1b9a'}
    bg_map = {'사육':'#e8f5e9','폐사':'#fce4ec','출하':'#e3f2fd','격리':'#fff8e1','거세대기':'#f3e5f5'}
    c = color_map.get(status, '#555')
    b = bg_map.get(status, '#eee')
    return f'<span style="background:{b};color:{c};padding:3px 12px;border-radius:20px;font-size:12px;font-weight:700;">{status}</span>'


# ================================================================
# 페이지 1: 대시보드
# ================================================================
def show_dashboard():
    farm_id = st.session_state.farm_id
    today_str = datetime.now().strftime("%Y년 %m월 %d일 (%a)")

    st.markdown(f'<div class="page-title">📊 축사 현황 대시보드</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="page-subtitle">📅 {today_str} · {st.session_state.get("farm_name","에코팜")}</div>', unsafe_allow_html=True)

    # 데이터 조회
    s = get_dashboard_stats(farm_id)

    # 상단 총괄 (4 카드)
    st.markdown('<div class="section-header">사육 총괄</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="grid-4">
        <div class="card-main"><div class="label">총 사육 두수</div><div class="value">{s['total']:,}</div><div class="sub">현재 사육 중</div></div>
        <div class="card-main"><div class="label">암컷 🐐</div><div class="value">{s['암']:,}</div><div class="sub">Female</div></div>
        <div class="card-main"><div class="label">수컷 🐏</div><div class="value">{s['수']:,}</div><div class="sub">Male</div></div>
        <div class="card-main"><div class="label">거세 ✂️</div><div class="value">{s['거세']:,}</div><div class="sub">Castrated</div></div>
    </div>
    """, unsafe_allow_html=True)

    # 이벤트 통계 (4 카드)
    st.markdown('<div class="section-header">누적 이벤트 현황</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="grid-4">
        <div class="card-event"><div class="etitle">🐣 누적 출산</div><div class="evalue">{s['birth_total']}</div><div class="esub">암 {s['birth_female']} | 수 {s['birth_male']}</div></div>
        <div class="card-event"><div class="etitle">📥 누적 입하</div><div class="evalue">{s['inbound']}</div><div class="esub">이동 내역 기준</div></div>
        <div class="card-event"><div class="etitle">✝️ 누적 폐사</div><div class="evalue">{s['dead']}</div><div class="esub">상태: 폐사 기준</div></div>
        <div class="card-event"><div class="etitle">📤 누적 출하</div><div class="evalue">{s['outbound']}</div><div class="esub">상태: 출하 기준</div></div>
    </div>
    """, unsafe_allow_html=True)

    # 이번달 이벤트
    this_m = datetime.now().strftime('%Y년 %m월')
    st.markdown(f"""
    <div class="grid-2">
        <div class="card-event" style="background:linear-gradient(135deg,#e8f5e9,#f1f8e9);">
            <div class="etitle">📅 {this_m} 출산</div>
            <div class="evalue" style="color:#1b5e20;">{s['births_this_month']}</div>
            <div class="esub">이번달 신규 출산 건수</div>
        </div>
        <div class="card-event" style="background:linear-gradient(135deg,#e3f2fd,#e8eaf6);">
            <div class="etitle">📅 {this_m} 진료</div>
            <div class="evalue" style="color:#0d47a1;">{s['health_this_month']}</div>
            <div class="esub">이번달 건강 기록 건수</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr style='margin:24px 0;border:none;border-top:1px solid #dee2e6;'>", unsafe_allow_html=True)

    # 도넛 차트
    st.markdown('<div class="section-header">개체 분포 분석</div>', unsafe_allow_html=True)

    df_f = run_query("SELECT breed, group_code FROM individuals WHERE status='사육' AND gender='암' AND farm_id=?", (farm_id,))
    df_m = run_query("SELECT group_code FROM individuals WHERE status='사육' AND gender='수' AND farm_id=?", (farm_id,))
    df_c = run_query("SELECT group_code, status FROM individuals WHERE (gender='거세' OR status='거세대기') AND farm_id=?", (farm_id,))
    df_status = run_query("SELECT status, COUNT(*) as cnt FROM individuals WHERE farm_id=? GROUP BY status", (farm_id,))

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        f_child = len(df_f[df_f['group_code'] == 'ETCF']) if not df_f.empty else 0
        f_adult = (len(df_f) - f_child) if not df_f.empty else 0
        st.plotly_chart(make_donut(['성축','자축'], [f_adult, f_child], f"암컷 성/자축 ({s['암']})"), use_container_width=True)
    with c2:
        breeds = df_f['breed'].value_counts() if not df_f.empty else pd.Series()
        lbls = breeds.index.tolist() if not breeds.empty else ['없음']
        vals = breeds.values.tolist() if not breeds.empty else [0]
        st.plotly_chart(make_donut(lbls, vals, f"암컷 품종별"), use_container_width=True)
    with c3:
        if not df_m.empty:
            m_sp = len(df_m[df_m['group_code'].isin(['SGOAT1','SGOAT2'])])
            m_bo = len(df_m[df_m['group_code'] == 'SBOER'])
            m_ch = len(df_m[df_m['group_code'] == 'ETCM'])
        else:
            m_sp = m_bo = m_ch = 0
        st.plotly_chart(make_donut(['특종묘','그외종묘','자축'], [m_sp, m_bo, m_ch], f"수컷 종별 ({s['수']})"), use_container_width=True)
    with c4:
        if not df_status.empty:
            sl = df_status['status'].tolist()
            sv = df_status['cnt'].tolist()
        else:
            sl, sv = ['없음'], [0]
        st.plotly_chart(make_donut(sl, sv, "전체 상태 분포"), use_container_width=True)

    # 월별 출산 트렌드
    st.markdown('<div class="section-header">월별 출산 추이 (최근 12개월)</div>', unsafe_allow_html=True)
    df_trend = run_query("""
        SELECT strftime('%Y-%m', birth_date) as month, 
               SUM(total_kids) as total, SUM(live_female) as female, SUM(live_male) as male
        FROM birth_events WHERE farm_id=?
        AND birth_date >= date('now', '-12 months')
        GROUP BY month ORDER BY month
    """, (farm_id,))

    if not df_trend.empty:
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Bar(x=df_trend['month'], y=df_trend['female'], name='암', marker_color='#ef9a9a'))
        fig_trend.add_trace(go.Bar(x=df_trend['month'], y=df_trend['male'], name='수', marker_color='#90caf9'))
        fig_trend.update_layout(
            barmode='stack', height=240,
            margin=dict(t=20, b=30, l=30, r=10),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(tickfont=dict(size=11)),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            yaxis=dict(gridcolor='#f0f0f0')
        )
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("출산 데이터가 없습니다.")

    # 최근 이벤트 요약
    st.markdown('<div class="section-header">최근 활동 로그</div>', unsafe_allow_html=True)
    rc1, rc2 = st.columns(2)
    with rc1:
        st.markdown("**최근 건강/진료 (5건)**")
        df_rh = run_query("""
            SELECT h.date as 일자, h.goat_id as 개체, h.symptom as 증상, h.result as 결과
            FROM health_logs h WHERE h.farm_id=? ORDER BY h.date DESC LIMIT 5
        """, (farm_id,))
        if not df_rh.empty:
            st.dataframe(df_rh, use_container_width=True, hide_index=True)
        else:
            st.info("최근 진료 기록 없음")
    with rc2:
        st.markdown("**최근 출산 기록 (5건)**")
        df_rb = run_query("""
            SELECT birth_date as 출산일, mother_id as 모축, total_kids as 산자수,
                   live_female as 암, live_male as 수
            FROM birth_events WHERE farm_id=? ORDER BY birth_date DESC LIMIT 5
        """, (farm_id,))
        if not df_rb.empty:
            st.dataframe(df_rb, use_container_width=True, hide_index=True)
        else:
            st.info("최근 출산 기록 없음")

    # 데이터 내보내기
    st.markdown("<hr style='margin:24px 0;border:none;border-top:1px solid #dee2e6;'>", unsafe_allow_html=True)
    st.markdown('<div class="section-header">📥 전체 데이터 내보내기</div>', unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="download-section">', unsafe_allow_html=True)
        dc1, dc2 = st.columns([3, 1])
        with dc1:
            st.markdown("전체 개체, 건강, 출산, 이동, 체중 데이터를 엑셀 파일로 내보냅니다.")
        with dc2:
            excel_data = get_full_export(farm_id)
            fname = f"에코팜_{datetime.now().strftime('%Y%m%d')}.xlsx"
            st.download_button("📊 Excel 전체 내보내기", excel_data, fname,
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                               use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)


# ================================================================
# 페이지 2: 개체 관리
# ================================================================
def show_individuals():
    farm_id = st.session_state.farm_id
    st.markdown('<div class="page-title">🐐 개체 통합 관리</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">개체 등록, 상세 조회, 정보 수정</div>', unsafe_allow_html=True)

    tab_list, tab_reg = st.tabs(["📋 개체 목록 · 상세", "➕ 신규 개체 등록"])

    # ── 탭1: 목록 + 상세 ──────────────────────────────────────────
    with tab_list:
        # 검색 필터
        with st.container():
            st.markdown('<div class="info-box" style="padding:14px;">', unsafe_allow_html=True)
            fc1, fc2, fc3, fc4 = st.columns([3, 2, 2, 1])
            with fc1:
                search_term = st.text_input("🔎 개체번호 검색", placeholder="예: F0001", label_visibility="collapsed")
            with fc2:
                status_filter = st.selectbox("상태", ["전체","사육","폐사","출하","거세대기","격리"], label_visibility="collapsed")
            with fc3:
                gender_filter = st.selectbox("성별", ["전체","암","수","거세"], label_visibility="collapsed")
            with fc4:
                st.button("🔄", use_container_width=True, help="새로고침")
            st.markdown('</div>', unsafe_allow_html=True)

        # 쿼리 빌드
        query = "SELECT * FROM individuals WHERE farm_id=?"
        params = [farm_id]
        if search_term:
            query += " AND id LIKE ?"
            params.append(f"%{search_term}%")
        if status_filter != "전체":
            query += " AND status=?"
            params.append(status_filter)
        if gender_filter != "전체":
            query += " AND gender=?"
            params.append(gender_filter)
        query += " ORDER BY id"

        df = run_query(query, params)

        col_list, col_detail = st.columns([1, 2])

        with col_list:
            st.markdown(f"**검색 결과** ({len(df)}건)")
            if not df.empty:
                display_cols = ['id','gender','status','room_no']
                rename_map = {'id':'개체번호','gender':'성별','status':'상태','room_no':'방'}
                df_show = df[display_cols].rename(columns=rename_map)
                st.dataframe(df_show, use_container_width=True, height=560, hide_index=True)
                selected_id = st.selectbox("👉 상세 조회", df['id'].tolist(), label_visibility="collapsed")
            else:
                st.warning("검색 결과가 없습니다.")
                selected_id = None

            # CSV 내보내기
            if not df.empty:
                st.download_button("📄 CSV 내보내기", export_to_csv(df),
                                   f"개체목록_{datetime.now().strftime('%Y%m%d')}.csv",
                                   mime="text/csv", use_container_width=True)

        with col_detail:
            if selected_id:
                goat = df[df['id'] == selected_id].iloc[0]
                summary = get_individual_summary(selected_id)

                st.markdown(f"""
                <div class="goat-detail-card">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
                        <span style="font-size:1.8rem;font-weight:900;color:#1a3a1a;">🏷️ {goat['id']}</span>
                        {status_badge(goat['status'])}
                    </div>
                    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:12px;font-size:14px;color:#34495e;">
                        <div><span style="color:#8a9bb0;font-size:12px;">성별</span><br><b>{goat['gender']}</b></div>
                        <div><span style="color:#8a9bb0;font-size:12px;">품종</span><br><b>{goat['breed']}</b></div>
                        <div><span style="color:#8a9bb0;font-size:12px;">방번호</span><br><b>{goat['room_no']}호</b></div>
                        <div><span style="color:#8a9bb0;font-size:12px;">그룹</span><br><b>{goat['group_code'] or '-'}</b></div>
                        <div><span style="color:#8a9bb0;font-size:12px;">출생일</span><br><b>{goat['birth_date'] or '-'}</b></div>
                        <div><span style="color:#8a9bb0;font-size:12px;">최근 체중</span><br><b>{summary.get('last_weight', '-')}</b></div>
                        <div><span style="color:#8a9bb0;font-size:12px;">부축</span><br><b>{goat['father_id'] or '-'}</b></div>
                        <div><span style="color:#8a9bb0;font-size:12px;">모축</span><br><b>{goat['mother_id'] or '-'}</b></div>
                    </div>
                    <div style="margin-top:14px;padding:10px;background:#f8faf8;border-radius:8px;color:#7a8b7a;font-size:13px;">
                        📝 {goat['notes'] if goat['notes'] else "특이사항 없음"}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                t1, t2, t3, t4, t5 = st.tabs(["✏️ 정보 수정", "🏥 건강 이력", "👶 번식 이력", "⚖️ 체중 추이", "🚚 이동 이력"])

                with t1:
                    with st.form("edit_goat"):
                        ec1, ec2 = st.columns(2)
                        with ec1:
                            s_opts = ["사육","폐사","출하","격리","거세대기"]
                            idx = s_opts.index(goat['status']) if goat['status'] in s_opts else 0
                            new_status = st.selectbox("상태", s_opts, index=idx)
                            new_room = st.text_input("방 번호", value=goat['room_no'] or '')
                        with ec2:
                            gc_df = get_group_codes(farm_id)
                            gc_opts = gc_df['code'].tolist() if not gc_df.empty else []
                            gc_idx = gc_opts.index(goat['group_code']) if goat['group_code'] in gc_opts else 0
                            new_group = st.selectbox("그룹", gc_opts, index=gc_idx)
                            new_breed = st.text_input("품종", value=goat['breed'] or '흑염소')
                        new_note = st.text_area("비고", value=goat['notes'] or '', height=80)

                        if st.form_submit_button("💾 저장", use_container_width=True, type="primary"):
                            ok = run_action(
                                "UPDATE individuals SET status=?,room_no=?,group_code=?,breed=?,notes=?,updated_at=datetime('now','localtime') WHERE id=?",
                                (new_status, new_room, new_group, new_breed, new_note, selected_id)
                            )
                            if ok:
                                log_change('individuals', selected_id, 'UPDATE', manager='담당자')
                                st.success("✅ 저장되었습니다.")
                                st.rerun()

                with t2:
                    df_h = run_query("""
                        SELECT date as 일자, symptom as 증상, diagnosis as 진단, 
                               treatment as 처방, result as 결과, manager as 담당자
                        FROM health_logs WHERE goat_id=? ORDER BY date DESC
                    """, (selected_id,))
                    if not df_h.empty:
                        st.dataframe(df_h, use_container_width=True, hide_index=True, height=300)
                    else:
                        st.info("건강 이력이 없습니다.")

                with t3:
                    if goat['gender'] == '암':
                        df_b = run_query("""
                            SELECT birth_date as 출산일, birth_order as 산차, total_kids as 산자수,
                                   live_female as '암(생존)', live_male as '수(생존)', delivery_type as 분만형태
                            FROM birth_events WHERE mother_id=? ORDER BY birth_date DESC
                        """, (selected_id,))
                        if not df_b.empty:
                            st.dataframe(df_b, use_container_width=True, hide_index=True)
                        else:
                            st.info("출산 기록이 없습니다.")
                    else:
                        # 부축으로 등록된 자손
                        df_off = run_query("""
                            SELECT b.birth_date as 출산일, b.mother_id as 모축, b.total_kids as 산자수
                            FROM birth_events b WHERE b.father_id=? ORDER BY b.birth_date DESC
                        """, (selected_id,))
                        if not df_off.empty:
                            st.markdown("**부축으로 등록된 출산 기록**")
                            st.dataframe(df_off, use_container_width=True, hide_index=True)
                        else:
                            st.info("등록된 자손 기록이 없습니다.")

                with t4:
                    df_w = run_query("""
                        SELECT date as 일자, weight as '체중(kg)', manager as 담당자
                        FROM weight_logs WHERE goat_id=? ORDER BY date
                    """, (selected_id,))
                    if not df_w.empty:
                        fig_w = px.line(df_w, x='일자', y='체중(kg)', markers=True,
                                        color_discrete_sequence=['#2d7a2d'])
                        fig_w.update_layout(height=220, margin=dict(t=10,b=30,l=30,r=10),
                                            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                            yaxis=dict(gridcolor='#f0f0f0'))
                        st.plotly_chart(fig_w, use_container_width=True)
                        st.dataframe(df_w, use_container_width=True, hide_index=True)
                    else:
                        st.info("체중 기록이 없습니다.")
                    # 체중 추가 입력
                    with st.expander("➕ 체중 기록 추가"):
                        with st.form("add_weight"):
                            wc1, wc2 = st.columns(2)
                            with wc1:
                                w_date = st.date_input("측정일", value=date.today())
                            with wc2:
                                w_val = st.number_input("체중 (kg)", min_value=0.1, max_value=200.0, step=0.1)
                            w_note = st.text_input("비고")
                            if st.form_submit_button("추가"):
                                run_action(
                                    "INSERT INTO weight_logs (goat_id, farm_id, date, weight, notes) VALUES (?,?,?,?,?)",
                                    (selected_id, farm_id, str(w_date), w_val, w_note)
                                )
                                st.success("체중 기록 추가됨")
                                st.rerun()

                with t5:
                    df_mv = run_query("""
                        SELECT date as 일자, type as 유형, destination as 목적지,
                               price as 금액, notes as 비고
                        FROM movements WHERE goat_id=? ORDER BY date DESC
                    """, (selected_id,))
                    if not df_mv.empty:
                        st.dataframe(df_mv, use_container_width=True, hide_index=True)
                    else:
                        st.info("이동 기록이 없습니다.")
            else:
                st.markdown("""
                <div class="info-box" style="text-align:center;padding:60px 20px;color:#8a9bb0;">
                    <div style="font-size:3rem;">🐐</div>
                    <div style="font-size:16px;font-weight:600;margin-top:12px;">왼쪽 목록에서 개체를 선택하세요</div>
                    <div style="font-size:13px;margin-top:6px;">개체 번호를 검색하거나 목록에서 클릭 후 드롭다운에서 선택하세요</div>
                </div>
                """, unsafe_allow_html=True)

    # ── 탭2: 신규 등록 ─────────────────────────────────────────────
    with tab_reg:
        st.markdown('<div class="section-header">신규 개체 등록</div>', unsafe_allow_html=True)

        with st.form("register_goat", clear_on_submit=True):
            rc1, rc2, rc3 = st.columns(3)
            with rc1:
                gender_new = st.selectbox("성별 *", ["암","수","거세"])
                prefix_map = {"암":"F","수":"M","거세":"C"}
                auto_id = get_next_id(prefix_map[gender_new], farm_id)
                goat_id = st.text_input("개체번호 *", value=auto_id, help="자동 생성됩니다. 직접 수정 가능")
                breed_new = st.selectbox("품종", ["흑염소","보어","흑염소 x 보어","기타"])
            with rc2:
                birth_date_new = st.date_input("출생일", value=date.today())
                birth_type_new = st.selectbox("입축 구분", ["자가출생","구입"])
                room_new = st.text_input("방 번호 *", placeholder="예: 1")
            with rc3:
                gc_df2 = get_group_codes(farm_id)
                gc_opts2 = gc_df2['code'].tolist() if not gc_df2.empty else ['FGOAT1']
                group_new = st.selectbox("그룹 코드", gc_opts2)
                father_new = st.text_input("부축 번호", placeholder="선택사항")
                mother_new = st.text_input("모축 번호", placeholder="선택사항")

            rr1, rr2 = st.columns(2)
            with rr1:
                weight_init = st.number_input("초기 체중 (kg)", min_value=0.0, step=0.1)
                purchase_price = st.number_input("구입가 (원)", min_value=0, step=1000) if birth_type_new == "구입" else 0
            with rr2:
                ear_tag = st.text_input("귀표 번호", placeholder="선택사항")
                notes_new = st.text_area("비고", height=68)

            submitted = st.form_submit_button("✅ 등록", use_container_width=True, type="primary")
            if submitted:
                # 검증
                valid, msg = validate_goat_id(goat_id)
                if not valid:
                    st.error(msg)
                elif check_duplicate_goat_id(goat_id):
                    st.error(f"개체번호 '{goat_id}'는 이미 존재합니다.")
                elif not room_new:
                    st.error("방 번호를 입력하세요.")
                else:
                    ok = run_action(
                        """INSERT INTO individuals 
                           (id, farm_id, gender, breed, birth_date, birth_type, status, 
                            room_no, group_code, father_id, mother_id, weight_initial,
                            purchase_price, ear_tag, notes)
                           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (goat_id.upper(), farm_id, gender_new, breed_new,
                         str(birth_date_new), birth_type_new, '사육',
                         room_new, group_new,
                         father_new or None, mother_new or None,
                         weight_init or None, purchase_price or None,
                         ear_tag or None, notes_new or None)
                    )
                    if ok:
                        if weight_init > 0:
                            run_action(
                                "INSERT INTO weight_logs (goat_id, farm_id, date, weight, notes) VALUES (?,?,?,?,?)",
                                (goat_id.upper(), farm_id, str(birth_date_new), weight_init, "초기 등록 체중")
                            )
                        log_change('individuals', goat_id.upper(), 'INSERT')
                        st.success(f"✅ 개체 **{goat_id.upper()}** 등록 완료!")
                        st.balloons()


# ================================================================
# 페이지 3: 이벤트 기록 (건강/출산/이동 입력)
# ================================================================
def show_records():
    farm_id = st.session_state.farm_id
    st.markdown('<div class="page-title">📝 이벤트 기록 입력</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">건강 진료, 출산, 이동/입출하 이벤트를 기록합니다.</div>', unsafe_allow_html=True)

    # 개체 목록 (사육 중)
    df_active = run_query("SELECT id FROM individuals WHERE status='사육' AND farm_id=? ORDER BY id", (farm_id,))
    id_list = df_active['id'].tolist() if not df_active.empty else []
    all_ids = run_query("SELECT id FROM individuals WHERE farm_id=? ORDER BY id", (farm_id,))['id'].tolist()

    tab_h, tab_b, tab_m, tab_w, tab_v = st.tabs([
        "🏥 건강·진료", "🐣 출산·번식", "🚚 이동·입출하", "⚖️ 체중 측정", "💉 백신 접종"
    ])

    # ── 건강 기록 ──────────────────────────────────────────────────
    with tab_h:
        c_form, c_hist = st.columns([1, 1])
        with c_form:
            st.markdown("**새 진료 기록 추가**")
            with st.form("health_form", clear_on_submit=True):
                h_id = st.selectbox("개체 선택 *", all_ids)
                hc1, hc2 = st.columns(2)
                with hc1:
                    h_date = st.date_input("진료일 *", value=date.today())
                    h_symptom = st.text_input("증상 *", placeholder="예: 식욕 부진, 기침")
                    h_diagnosis = st.text_input("진단", placeholder="예: 소화불량")
                with hc2:
                    h_treatment = st.text_area("처방·처치", placeholder="예: 소화제 3일 투여", height=80)
                    h_medicine = st.text_input("약품명")
                    h_cost = st.number_input("진료비 (원)", min_value=0, step=1000)
                hc3, hc4 = st.columns(2)
                with hc3:
                    h_result = st.selectbox("결과", ["진행중","완치","폐사","관찰중"])
                with hc4:
                    h_manager = st.text_input("담당자", value="담당자")
                h_next = st.date_input("다음 방문 예정", value=None)
                h_notes = st.text_area("비고", height=60)

                if st.form_submit_button("💾 저장", use_container_width=True, type="primary"):
                    if not h_id or not h_symptom:
                        st.error("개체와 증상은 필수입니다.")
                    else:
                        ok = run_action(
                            """INSERT INTO health_logs 
                               (goat_id, farm_id, date, symptom, diagnosis, treatment,
                                medicine, cost, result, manager, next_visit, notes)
                               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                            (h_id, farm_id, str(h_date), h_symptom, h_diagnosis,
                             h_treatment, h_medicine, h_cost, h_result, h_manager,
                             str(h_next) if h_next else None, h_notes)
                        )
                        if h_result == '폐사':
                            run_action("UPDATE individuals SET status='폐사' WHERE id=?", (h_id,))
                        if ok:
                            st.success("✅ 건강 기록 저장 완료")

        with c_hist:
            st.markdown("**최근 진료 기록 (30건)**")
            df_rh = run_query("""
                SELECT date as 일자, goat_id as 개체, symptom as 증상, 
                       diagnosis as 진단, result as 결과
                FROM health_logs WHERE farm_id=? ORDER BY date DESC LIMIT 30
            """, (farm_id,))
            st.dataframe(df_rh, use_container_width=True, height=500, hide_index=True)

    # ── 출산 기록 ──────────────────────────────────────────────────
    with tab_b:
        df_female = run_query("SELECT id FROM individuals WHERE gender='암' AND status='사육' AND farm_id=? ORDER BY id", (farm_id,))
        female_ids = df_female['id'].tolist() if not df_female.empty else []
        df_male = run_query("SELECT id FROM individuals WHERE gender='수' AND status='사육' AND farm_id=? ORDER BY id", (farm_id,))
        male_ids = df_male['id'].tolist() if not df_male.empty else []

        c_bf, c_bh = st.columns([1, 1])
        with c_bf:
            st.markdown("**출산 이벤트 등록**")
            with st.form("birth_form", clear_on_submit=True):
                b_mother = st.selectbox("모축 선택 *", female_ids if female_ids else ['없음'])
                b_father = st.selectbox("부축 선택 (선택)", ['미상'] + male_ids)
                bc1, bc2 = st.columns(2)
                with bc1:
                    b_date = st.date_input("출산일 *", value=date.today())
                    b_order = st.number_input("산차 (몇 번째 출산)", min_value=1, max_value=20, value=1)
                    b_total = st.number_input("총 산자수 *", min_value=0, max_value=10, value=1)
                with bc2:
                    b_live_f = st.number_input("암컷 생존", min_value=0, max_value=10, value=0)
                    b_live_m = st.number_input("수컷 생존", min_value=0, max_value=10, value=0)
                    b_still = st.number_input("사산 수", min_value=0, max_value=10, value=0)
                b_delivery = st.selectbox("분만 형태", ["자연분만","난산","제왕절개"])
                b_avg_w = st.number_input("평균 출생 체중 (kg)", min_value=0.0, step=0.1)
                b_manager = st.text_input("담당자", value="담당자")
                b_notes = st.text_area("비고", height=60)

                if st.form_submit_button("💾 저장", use_container_width=True, type="primary"):
                    if not female_ids:
                        st.error("등록된 암컷 개체가 없습니다.")
                    elif b_live_f + b_live_m > b_total:
                        st.error("생존 수가 총 산자수를 초과할 수 없습니다.")
                    else:
                        ok = run_action(
                            """INSERT INTO birth_events 
                               (farm_id, mother_id, father_id, birth_date, birth_order,
                                total_kids, live_female, live_male, stillborn,
                                delivery_type, birth_weight_avg, manager, notes)
                               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                            (farm_id, b_mother,
                             None if b_father == '미상' else b_father,
                             str(b_date), b_order, b_total, b_live_f, b_live_m,
                             b_still, b_delivery, b_avg_w or None, b_manager, b_notes)
                        )
                        if ok:
                            st.success("✅ 출산 기록 저장 완료")

        with c_bh:
            st.markdown("**최근 출산 기록 (30건)**")
            df_rb = run_query("""
                SELECT birth_date as 출산일, mother_id as 모축, father_id as 부축,
                       birth_order as 산차, total_kids as 산자수, 
                       live_female as 암생존, live_male as 수생존, delivery_type as 분만형태
                FROM birth_events WHERE farm_id=? ORDER BY birth_date DESC LIMIT 30
            """, (farm_id,))
            st.dataframe(df_rb, use_container_width=True, height=500, hide_index=True)

    # ── 이동 기록 ──────────────────────────────────────────────────
    with tab_m:
        c_mf, c_mh = st.columns([1, 1])
        with c_mf:
            st.markdown("**이동/입출하 기록 추가**")
            with st.form("move_form", clear_on_submit=True):
                mv_id = st.selectbox("개체 *", all_ids)
                mc1, mc2 = st.columns(2)
                with mc1:
                    mv_date = st.date_input("날짜 *", value=date.today())
                    mv_type = st.selectbox("유형 *", ["입하","출하","이동","격리","복귀","거세"])
                with mc2:
                    mv_dest = st.text_input("목적지/출발지", placeholder="예: 3번 축사, 시장")
                    mv_price = st.number_input("거래 금액 (원)", min_value=0, step=10000)
                mv_weight = st.number_input("이동 시 체중 (kg)", min_value=0.0, step=0.1)
                mv_manager = st.text_input("담당자", value="담당자")
                mv_reason = st.text_input("이동 사유")
                mv_notes = st.text_area("비고", height=60)

                if st.form_submit_button("💾 저장", use_container_width=True, type="primary"):
                    ok = run_action(
                        """INSERT INTO movements 
                           (farm_id, goat_id, date, type, destination, reason,
                            price, weight, manager, notes)
                           VALUES (?,?,?,?,?,?,?,?,?,?)""",
                        (farm_id, mv_id, str(mv_date), mv_type, mv_dest,
                         mv_reason, mv_price, mv_weight or None, mv_manager, mv_notes)
                    )
                    # 상태 자동 업데이트
                    status_update_map = {
                        '출하': '출하', '격리': '격리', '거세': '거세대기', '복귀': '사육'
                    }
                    if mv_type in status_update_map:
                        run_action("UPDATE individuals SET status=? WHERE id=?",
                                   (status_update_map[mv_type], mv_id))
                    if ok:
                        st.success(f"✅ {mv_type} 기록 저장 완료 (상태 자동 변경됨)")

        with c_mh:
            st.markdown("**최근 이동 기록 (30건)**")
            df_rm = run_query("""
                SELECT date as 일자, goat_id as 개체, type as 유형,
                       destination as 목적지, price as 금액
                FROM movements WHERE farm_id=? ORDER BY date DESC LIMIT 30
            """, (farm_id,))
            st.dataframe(df_rm, use_container_width=True, height=500, hide_index=True)

    # ── 체중 일괄 기록 ─────────────────────────────────────────────
    with tab_w:
        st.markdown("**체중 일괄 측정 기록**")
        wc1, wc2 = st.columns([1, 1])
        with wc1:
            with st.form("weight_batch", clear_on_submit=True):
                wb_date = st.date_input("측정일", value=date.today())
                wb_id = st.selectbox("개체", id_list if id_list else ['없음'])
                wb_val = st.number_input("체중 (kg)", min_value=0.1, max_value=300.0, step=0.1)
                wb_manager = st.text_input("담당자", value="담당자")
                wb_notes = st.text_input("비고")
                if st.form_submit_button("💾 저장", use_container_width=True, type="primary"):
                    run_action(
                        "INSERT INTO weight_logs (goat_id, farm_id, date, weight, manager, notes) VALUES (?,?,?,?,?,?)",
                        (wb_id, farm_id, str(wb_date), wb_val, wb_manager, wb_notes)
                    )
                    st.success("✅ 체중 기록 저장")
        with wc2:
            st.markdown("**최근 체중 기록 (30건)**")
            df_rw = run_query("""
                SELECT date as 일자, goat_id as 개체, weight as '체중(kg)', manager as 담당자
                FROM weight_logs WHERE farm_id=? ORDER BY date DESC LIMIT 30
            """, (farm_id,))
            st.dataframe(df_rw, use_container_width=True, height=440, hide_index=True)

    # ── 백신 기록 ──────────────────────────────────────────────────
    with tab_v:
        vc1, vc2 = st.columns([1, 1])
        with vc1:
            st.markdown("**백신/예방접종 기록 추가**")
            with st.form("vaccine_form", clear_on_submit=True):
                vf_id = st.selectbox("개체 *", all_ids)
                vf1, vf2 = st.columns(2)
                with vf1:
                    vf_date = st.date_input("접종일 *", value=date.today())
                    vf_name = st.text_input("백신명 *", placeholder="예: 구제역 백신")
                with vf2:
                    vf_dose = st.text_input("용량", placeholder="예: 2ml")
                    vf_next = st.date_input("다음 접종일", value=None)
                vf_manager = st.text_input("담당자", value="담당자")
                vf_notes = st.text_area("비고", height=60)
                if st.form_submit_button("💾 저장", use_container_width=True, type="primary"):
                    if not vf_name:
                        st.error("백신명은 필수입니다.")
                    else:
                        run_action(
                            "INSERT INTO vaccine_logs (goat_id, farm_id, date, vaccine_name, dose, next_date, manager, notes) VALUES (?,?,?,?,?,?,?,?)",
                            (vf_id, farm_id, str(vf_date), vf_name, vf_dose,
                             str(vf_next) if vf_next else None, vf_manager, vf_notes)
                        )
                        st.success("✅ 백신 기록 저장 완료")
        with vc2:
            st.markdown("**최근 백신 기록**")
            df_rv = run_query("""
                SELECT date as 일자, goat_id as 개체, vaccine_name as 백신명,
                       next_date as 다음접종, manager as 담당자
                FROM vaccine_logs WHERE farm_id=? ORDER BY date DESC LIMIT 30
            """, (farm_id,))
            st.dataframe(df_rv, use_container_width=True, height=440, hide_index=True)


# ================================================================
# 페이지 4: 전체 이력 조회 & 내보내기
# ================================================================
def show_history():
    farm_id = st.session_state.farm_id
    st.markdown('<div class="page-title">🗂️ 전체 이력 조회</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">분야별 전체 데이터를 조회하고 내보낼 수 있습니다.</div>', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🐐 개체 전체", "🏥 건강·진료", "🐣 출산·번식", "🚚 이동·입출하", "⚖️ 체중"])

    def show_table_with_download(df, label, fname):
        st.markdown(f"**{label}** ({len(df)}건)")
        # 날짜 필터
        fc1, fc2, fc3 = st.columns([2, 2, 3])
        with fc1:
            d_from = st.date_input("시작일", value=date(2020, 1, 1), key=f"df_{fname}")
        with fc2:
            d_to = st.date_input("종료일", value=date.today(), key=f"dt_{fname}")
        with fc3:
            keyword = st.text_input("키워드 검색", key=f"kw_{fname}", placeholder="아무 컬럼이나 검색")

        # 날짜 컬럼 자동 감지 필터
        date_cols = [c for c in df.columns if any(k in c for k in ['일자','날짜','출산일','접종일','일','date'])]
        if date_cols:
            dcol = date_cols[0]
            try:
                df[dcol] = pd.to_datetime(df[dcol], errors='coerce')
                df = df[(df[dcol] >= pd.Timestamp(d_from)) & (df[dcol] <= pd.Timestamp(d_to))]
            except:
                pass

        if keyword:
            mask = df.apply(lambda row: row.astype(str).str.contains(keyword, case=False, na=False).any(), axis=1)
            df = df[mask]

        st.dataframe(df, use_container_width=True, height=450, hide_index=True)

        dc1, dc2 = st.columns(2)
        with dc1:
            st.download_button(
                f"📄 CSV", export_to_csv(df),
                f"{fname}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv", use_container_width=True, key=f"csv_{fname}"
            )
        with dc2:
            st.download_button(
                f"📊 Excel", export_to_excel({label: df}),
                f"{fname}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True, key=f"xl_{fname}"
            )

    with tab1:
        df = run_query("SELECT * FROM individuals WHERE farm_id=? ORDER BY id", (farm_id,))
        show_table_with_download(df, "개체 전체 현황", "개체현황")
    with tab2:
        df = run_query("""
            SELECT date as 일자, goat_id as 개체번호, symptom as 증상, diagnosis as 진단,
                   treatment as 처방, medicine as 약품, cost as 진료비, result as 결과, manager as 담당자
            FROM health_logs WHERE farm_id=? ORDER BY date DESC
        """, (farm_id,))
        show_table_with_download(df, "건강·진료 이력", "건강진료")
    with tab3:
        df = run_query("""
            SELECT birth_date as 출산일, mother_id as 모축, father_id as 부축,
                   birth_order as 산차, total_kids as 산자수, live_female as 암생존,
                   live_male as 수생존, stillborn as 사산, delivery_type as 분만형태
            FROM birth_events WHERE farm_id=? ORDER BY birth_date DESC
        """, (farm_id,))
        show_table_with_download(df, "출산·번식 이력", "출산번식")
    with tab4:
        df = run_query("""
            SELECT date as 일자, goat_id as 개체번호, type as 유형, destination as 목적지,
                   price as 금액, weight as 체중, manager as 담당자
            FROM movements WHERE farm_id=? ORDER BY date DESC
        """, (farm_id,))
        show_table_with_download(df, "이동·입출하 이력", "이동이력")
    with tab5:
        df = run_query("""
            SELECT date as 일자, goat_id as 개체번호, weight as '체중(kg)', manager as 담당자
            FROM weight_logs WHERE farm_id=? ORDER BY date DESC
        """, (farm_id,))
        show_table_with_download(df, "체중 기록", "체중기록")


# ================================================================
# 메인 실행
# ================================================================
def main():
    with st.sidebar:
        st.markdown("""
        <div style="text-align:center;padding:20px 0 10px;">
            <div style="font-size:2.5rem;">🐐</div>
            <div style="font-size:1.2rem;font-weight:900;color:#a5d6a7;">ECO FARM</div>
            <div style="font-size:11px;color:#81c784;margin-top:2px;">흑염소 관리 솔루션 v1.0</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # 농장 선택 (멀티팜)
        farms = get_farm_list()
        farm_labels = [f"{n}" for _, n in farms]
        farm_ids = [i for i, _ in farms]
        selected_farm_idx = st.selectbox("🏡 농장 선택", range(len(farm_labels)),
                                         format_func=lambda i: farm_labels[i])
        st.session_state.farm_id = farm_ids[selected_farm_idx]
        st.session_state.farm_name = farm_labels[selected_farm_idx]

        st.markdown("---")

        menu = st.radio("📌 MENU", ["대시보드", "개체 관리", "이벤트 기록", "이력 조회"])

        st.markdown("---")

        # 빠른 통계 (사이드바)
        s = get_dashboard_stats(st.session_state.farm_id)
        st.markdown(f"""
        <div style="background:rgba(255,255,255,0.08);border-radius:10px;padding:14px;font-size:13px;">
            <div style="font-weight:700;margin-bottom:8px;color:#c8e6c9;">📊 빠른 현황</div>
            <div style="color:#a5d6a7;">총 사육: <b style="color:white;">{s['total']}두</b></div>
            <div style="color:#a5d6a7;">암/수/거세: <b style="color:white;">{s['암']}/{s['수']}/{s['거세']}</b></div>
            <div style="color:#a5d6a7;margin-top:4px;">이번달 출산: <b style="color:#ffcc80;">{s['births_this_month']}건</b></div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.caption("© 2026 Eco Farm Solution")
        st.caption("문의: ecofarm@example.com")

    if menu == "대시보드":
        show_dashboard()
    elif menu == "개체 관리":
        show_individuals()
    elif menu == "이벤트 기록":
        show_records()
    elif menu == "이력 조회":
        show_history()


if __name__ == "__main__":
    main()
