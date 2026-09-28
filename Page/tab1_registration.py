import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from db import fetch_data

ICE = "#3D7AB3"
EV = "#62B900"
HYBRID = "#F39A16"
OTHER = "#E95676"
PANEL = "#FFFFFF"
TEXT = "#15212B"
GRID = "#E7EDF2"
BORDER = "#DEE5EB"

def get_national_data(year, month):
    """지정된 연도/월의 전국 지역별 집계 데이터를 DB에서 가져옵니다."""
    query = """
        SELECT 
            TRIM(sido) AS sido, 
            TRIM(region) AS region, 
            SUM(ice_count) AS ice_count, 
            SUM(ev_count) AS ev_count,
            SUM(hybrid_count) AS hybrid_count, 
            SUM(etc_count) AS etc_count, 
            SUM(total_count) AS total_count
        FROM car_registrations
        WHERE year = :year AND month = :month
        GROUP BY TRIM(sido), TRIM(region)
    """
    df = fetch_data(query, {"year": year, "month": month})
    if df.empty:
        return pd.DataFrame()
    
    rows = []
    
    # 1. 경기도 (시/군 합산)
    gy = df[df['sido'] == '경기']
    if not gy.empty:
        vals = {
            'ice_count': gy['ice_count'].sum(),
            'ev_count': gy['ev_count'].sum(),
            'hybrid_count': gy['hybrid_count'].sum(),
            'etc_count': gy['etc_count'].sum()
        }
        rows.append({'지역': '경기도', **vals, 'total_count': sum(vals.values())})

    # 2. 서울특별시 (25개 자치구 합산)
    se = df[df['sido'] == '서울']
    if not se.empty:
        vals = {
            'ice_count': se['ice_count'].sum(),
            'ev_count': se['ev_count'].sum(),
            'hybrid_count': se['hybrid_count'].sum(),
            'etc_count': se['etc_count'].sum()
        }
        rows.append({'지역': '서울', **vals, 'total_count': sum(vals.values())})

    # 3. 광역 권역 집계
    for r_name in ["경상도", "전라도", "충청도", "강원도", "제주도"]:
        one = df[df['region'] == r_name]
        if not one.empty:
            r = one.iloc[0]
            rows.append({
                '지역': r_name, 
                'ice_count': r['ice_count'], 
                'ev_count': r['ev_count'], 
                'hybrid_count': r['hybrid_count'], 
                'etc_count': r['etc_count'],
                'total_count': r['ice_count'] + r['ev_count'] + r['hybrid_count'] + r['etc_count']
            })
            
    return pd.DataFrame(rows)

def get_trend_data():
    """각 연도별 기말(최신 월) 스냅샷 기준 연도별 자동차 등록 추이를 가져옵니다."""
    query = """
        WITH max_months AS (
            SELECT year, MAX(month) AS max_m
            FROM car_registrations
            GROUP BY year
        )
        SELECT 
            c.year AS year, 
            SUM(c.total_count) AS 등록대수, 
            SUM(c.ev_count) AS 전기차, 
            SUM(c.hybrid_count) AS 하이브리드, 
            SUM(c.ice_count) AS 내연기관
        FROM car_registrations c
        JOIN max_months m ON c.year = m.year AND c.month = m.max_m
        GROUP BY c.year
        ORDER BY c.year ASC
    """
    df = fetch_data(query)
    if not df.empty:
        df['year_str'] = df['year'].astype(str) + "년"
    return df


def fmt_delta(current, previous):
    """전월 대비 증감대수 및 증감률 계산"""
    if previous == 0 or pd.isna(previous):
        return "변동 없음", "off"
    change = current - previous
    rate = (change / previous) * 100
    if change > 0:
        return f"▲ {change:,.0f}대 (+{rate:.1f}%)", "normal"
    elif change < 0:
        return f"▼ {abs(change):,.0f}대 ({rate:.1f}%)", "inverse"
    else:
        return "변동 없음", "off"


def render():
    st.title("📊 전국 자동차 등록현황 대시보드")
    # st.caption("전국 자동차 및 전기차(EV) 보급 현황과 시점별/지역별 데이터 추이를 분석합니다.")
    st.markdown("---")

    # =========================================================
    # [1] 최신 기준 현황 요약 (Hero & Top KPI)
    # =========================================================
    LATEST_YEAR = 2026
    LATEST_MONTH = 8

    current_summary = get_national_data(LATEST_YEAR, LATEST_MONTH)

    if not current_summary.empty:
        tot = current_summary['total_count'].sum()
        ev = current_summary['ev_count'].sum()
        ice = current_summary['ice_count'].sum()
        hybrid = current_summary['hybrid_count'].sum()
        other = current_summary['etc_count'].sum()

        st.subheader(f"⚡ 최신 자동차 등록 현황 요약 ({LATEST_YEAR}년 {LATEST_MONTH:02d}월 기준)")

        # 최신 KPI 카드 5개
        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("🚘 총 등록대수", f"{tot:,.0f} 대")
        k2.metric("⚡ 전기차", f"{ev:,.0f} 대", f"전체의 {(ev/tot*100):.1f}%")
        k3.metric("⛽ 내연기관", f"{ice:,.0f} 대", f"전체의 {(ice/tot*100):.1f}%")
        k4.metric("🍃 하이브리드", f"{hybrid:,.0f} 대", f"전체의 {(hybrid/tot*100):.1f}%")
        k5.metric("🌱 기타 차량", f"{other:,.0f} 대", f"전체의 {(other/tot*100):.1f}%")

        st.markdown("<br>", unsafe_allow_html=True)

        # 상단 핵심 그래프 (지역별 Stacked Bar + 연료별 Donut)
        col_chart_left, col_chart_right = st.columns([1.4, 1])

        with col_chart_left:
            st.subheader("📊 지역별 등록 분포")
            chart_df = current_summary.sort_values("total_count", ascending=False)
            fig_bar = go.Figure()
            fig_bar.add_bar(
                x=chart_df['지역'], 
                y=chart_df['total_count'] - chart_df['ev_count'], 
                name="비전기차", 
                marker_color=ICE
            )
            fig_bar.add_bar(
                x=chart_df['지역'], 
                y=chart_df['ev_count'], 
                name="전기차", 
                marker_color=EV
            )
            fig_bar.update_layout(
                barmode="stack", 
                height=360, 
                margin=dict(l=10, r=10, t=20, b=10),
                legend=dict(orientation="h", y=1.1, x=1, xanchor="right")
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        with col_chart_right:
            st.subheader("🔋 연료별 비중")
            fig_pie = go.Figure(go.Pie(
                labels=["내연기관", "하이브리드", "전기차", "기타"],
                values=[ice, hybrid, ev, other],
                hole=0.6,
                marker=dict(colors=[ICE, HYBRID, EV, OTHER])
            ))
            fig_pie.update_layout(
                height=360, 
                margin=dict(l=10, r=10, t=20, b=10),
                legend=dict(orientation="h", y=-0.1, x=0.5, xanchor="center")
            )
            st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("---")

    # =========================================================
    # [2] 기간별 / 지역별 데이터 세부 조회 & 전월 대비 증감 분석
    # =========================================================
    st.subheader("🔎 기간별 · 지역별 상세 데이터 조망")
    # st.caption("원하는 연도, 월, 지역을 직접 선택하여 시점별 등록 수량 및 전월 대비 변동폭을 확인하세요.")

    # 컨트롤 필터 (연도, 월, 지역)
    ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([1, 1, 1.5])
    
    years_list = [2026, 2025, 2024, 2023]
    with ctrl_col1:
        sel_year = st.selectbox("📅 연도 선택", years_list, index=0, key="detail_year")

    max_m = 8 if sel_year == 2026 else 12
    with ctrl_col2:
        sel_month = st.selectbox("📆 월 선택", list(range(1, max_m + 1)), index=min(7, max_m - 1), key="detail_month")

    selected_period_df = get_national_data(sel_year, sel_month)

    if selected_period_df.empty:
        st.warning("선택하신 기간의 데이터가 DB에 존재하지 않습니다.")
        return

    available_regions = selected_period_df['지역'].unique().tolist()
    with ctrl_col3:
        sel_region = st.selectbox("📍 상세 분석 지역 선택", available_regions, index=0, key="detail_region")

    # 선택한 지역의 현재 달 데이터
    region_data = selected_period_df[selected_period_df['지역'] == sel_region].iloc[0]

    # 전월(Previous Month) 계산 및 데이터 조회
    prev_year = sel_year
    prev_month = sel_month - 1
    if prev_month == 0:
        prev_year -= 1
        prev_month = 12

    prev_period_df = get_national_data(prev_year, prev_month)
    prev_region_data = None
    if not prev_period_df.empty and sel_region in prev_period_df['지역'].values:
        prev_region_data = prev_period_df[prev_period_df['지역'] == sel_region].iloc[0]

    st.markdown("<br>", unsafe_allow_html=True)

    # 선택 지역 도넛 차트 (좌) & 전월 대비 증감 KPI 카드 (우)
    detail_left, detail_right = st.columns([1, 1.2])

    with detail_left:
        st.markdown(f"##### ⛽ **{sel_region}** ({sel_year}년 {sel_month}월) 연료 비율")
        donut_fig = go.Figure(go.Pie(
            labels=["내연기관", "전기차", "하이브리드", "기타"],
            values=[
                region_data['ice_count'], 
                region_data['ev_count'], 
                region_data['hybrid_count'], 
                region_data['etc_count']
            ],
            hole=0.6,
            marker=dict(colors=[ICE, EV, HYBRID, OTHER])
        ))
        donut_fig.update_layout(height=320, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(donut_fig, use_container_width=True)

    with detail_right:
        st.markdown(f"##### 📌 **{sel_region}** 전월({prev_year}.{prev_month:02d}) 대비 등록 증감")
        
        m_c1, m_c2 = st.columns(2)
        
        # 내연기관
        prev_ice = prev_region_data['ice_count'] if prev_region_data is not None else 0
        delta_ice, delta_ice_color = fmt_delta(region_data['ice_count'], prev_ice)
        m_c1.metric("⛽ 내연기관", f"{region_data['ice_count']:,.0f} 대", delta_ice, delta_color=delta_ice_color)

        # 전기차
        prev_ev = prev_region_data['ev_count'] if prev_region_data is not None else 0
        delta_ev, delta_ev_color = fmt_delta(region_data['ev_count'], prev_ev)
        m_c2.metric("⚡ 전기차", f"{region_data['ev_count']:,.0f} 대", delta_ev, delta_color=delta_ev_color)

        m_c3, m_c4 = st.columns(2)

        # 하이브리드
        prev_hybrid = prev_region_data['hybrid_count'] if prev_region_data is not None else 0
        delta_hybrid, delta_hybrid_color = fmt_delta(region_data['hybrid_count'], prev_hybrid)
        m_c3.metric("🍃 하이브리드", f"{region_data['hybrid_count']:,.0f} 대", delta_hybrid, delta_color=delta_hybrid_color)

        # 기타
        prev_etc = prev_region_data['etc_count'] if prev_region_data is not None else 0
        delta_etc, delta_etc_color = fmt_delta(region_data['etc_count'], prev_etc)
        m_c4.metric("🌱 기타", f"{region_data['etc_count']:,.0f} 대", delta_etc, delta_color=delta_etc_color)

    st.markdown("---")

    # =========================================================
    # [3] 연도별 전국 자동차 등록 추이 (Line Chart)
    # =========================================================
    st.subheader("📈 전국 연도별 자동차 등록 추이 (2023 ~ 2026)")
    # st.caption("각 연도별 기말 스냅샷(12월 기준, 2026년은 8월 기준) 누적 등록대수 추이입니다.")
    trend_df = get_trend_data()

    if not trend_df.empty:
        fig_line = px.line(
            trend_df, 
            x='year_str', 
            y=['등록대수', '전기차', '하이브리드', '내연기관'],
            markers=True,
            color_discrete_map={
                '등록대수': '#1F77B4',
                '전기차': EV,
                '하이브리드': HYBRID,
                '내연기관': ICE
            }
        )
        fig_line.update_layout(
            height=400,
            xaxis_title="연도",
            yaxis_title="등록대수 (대)",
            legend_title="구분",
            margin=dict(l=10, r=10, t=20, b=10)
        )
        st.plotly_chart(fig_line, use_container_width=True)