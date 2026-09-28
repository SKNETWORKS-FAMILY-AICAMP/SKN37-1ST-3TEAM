
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path


# =========================================================
# 1. PAGE
# =========================================================

st.set_page_config(
    page_title="자동차 등록 현황",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "전국자동차등록현황.csv"

YEARS = [2023, 2024, 2025, 2026]
CURRENT_YEAR = 2026
CURRENT_MONTH = 8

PROJECT_REGIONS = [
    "경기도",
    "경상도",
    "서울",
    "전라도",
    "충청도",
    "인천",
    "부산",
    "대구",
    "강원도",
    "울산",
]


# =========================================================
# 2. COLOR SYSTEM
# EV = HERO COLOR
# =========================================================

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

if st.session_state.dark_mode:
    BG = "#0B1118"
    PANEL = "#111B26"
    PANEL_2 = "#152331"
    TEXT = "#F4F7FA"
    SUBTEXT = "#9AA8B5"
    BORDER = "#263645"
    GRID = "#253442"
    ICE = "#8997A5"
    EV = "#B7FF3C"
    EV_DARK = "#78C91D"
    HYBRID = "#FFB23E"
    OTHER = "#FF6B8B"
    INPUT = "#111B26"
    SIDEBAR = "#0A1016"
else:
    BG = "#F4F6F8"
    PANEL = "#FFFFFF"
    PANEL_2 = "#F8FAFC"
    TEXT = "#15212B"
    SUBTEXT = "#667482"
    BORDER = "#DEE5EB"
    GRID = "#E7EDF2"
    ICE = "#6F7C88"
    EV = "#62B900"
    EV_DARK = "#3E8200"
    HYBRID = "#F39A16"
    OTHER = "#E95676"
    INPUT = "#FFFFFF"
    SIDEBAR = "#EDF2F5"


# =========================================================
# 3. GLOBAL CSS
# =========================================================

st.markdown(
    f"""
    <style>
    .stApp {{
        background:
            radial-gradient(circle at 95% 5%, rgba(98,185,0,.08), transparent 28%),
            {BG};
        color: {TEXT};
    }}

    [data-testid="stSidebar"] {{
        background: {SIDEBAR};
        border-right: 1px solid {BORDER};
    }}

    [data-testid="stSidebar"] * {{
        color: {TEXT} !important;
    }}

    .block-container {{
        max-width: 1480px;
        padding: 1.6rem 2.2rem 2.8rem 2.2rem;
    }}

    h1, h2, h3, h4, p, label {{
        color: {TEXT};
    }}

    .hero {{
        background:
            linear-gradient(120deg, {PANEL} 0%, {PANEL_2} 68%, rgba(98,185,0,.09) 100%);
        border: 1px solid {BORDER};
        border-radius: 24px;
        padding: 22px 26px 20px 26px;
        margin-bottom: 18px;
        box-shadow: 0 12px 36px rgba(0,0,0,.05);
        position: relative;
        overflow: hidden;
    }}

    .hero::after {{
        content: "";
        position: absolute;
        width: 210px;
        height: 210px;
        right: -90px;
        top: -80px;
        border-radius: 50%;
        background: rgba(98,185,0,.12);
        filter: blur(2px);
    }}

    .hero-kicker {{
        display: inline-flex;
        align-items: center;
        gap: 6px;
        border-radius: 999px;
        padding: 6px 11px;
        border: 1px solid rgba(98,185,0,.35);
        background: rgba(98,185,0,.10);
        color: {EV_DARK};
        font-size: .74rem;
        font-weight: 800;
        letter-spacing: .06em;
        margin-bottom: 10px;
    }}

    .hero-title {{
        font-size: clamp(2rem, 3vw, 3rem);
        font-weight: 900;
        letter-spacing: -.045em;
        line-height: 1;
        margin-bottom: 9px;
    }}

    .hero-title .ev {{
        color: {EV};
    }}

    .hero-desc {{
        color: {SUBTEXT};
        font-size: .92rem;
        margin-bottom: 0;
    }}

    .hero-meta {{
        color: {SUBTEXT};
        font-size: .75rem;
        margin-top: 9px;
    }}

    .section-head {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin: 18px 0 10px 0;
    }}

    .section-title {{
        font-size: 1.10rem;
        font-weight: 850;
        letter-spacing: -.02em;
    }}

    .section-note {{
        color: {SUBTEXT};
        font-size: .73rem;
    }}

    .metric-card {{
        background: {PANEL};
        border: 1px solid {BORDER};
        border-radius: 20px;
        padding: 17px 18px 15px 18px;
        min-height: 142px;
        box-shadow: 0 10px 26px rgba(0,0,0,.04);
    }}

    .metric-card.ev {{
        border: 1px solid rgba(98,185,0,.70);
        background:
            linear-gradient(145deg, {PANEL} 0%, rgba(98,185,0,.10) 100%);
        box-shadow:
            0 0 0 1px rgba(98,185,0,.06),
            0 12px 34px rgba(98,185,0,.13);
    }}

    .metric-label {{
        color: {SUBTEXT};
        font-size: .76rem;
        font-weight: 700;
        margin-bottom: 8px;
    }}

    .metric-icon {{
        float: right;
        width: 32px;
        height: 32px;
        display: grid;
        place-items: center;
        border-radius: 10px;
        font-size: 17px;
        background: {PANEL_2};
        border: 1px solid {BORDER};
    }}

    .metric-card.ev .metric-icon {{
        background: rgba(98,185,0,.15);
        border-color: rgba(98,185,0,.28);
    }}

    .metric-value {{
        font-size: clamp(1.50rem, 2.25vw, 2.15rem);
        font-weight: 900;
        letter-spacing: -.055em;
        line-height: 1.05;
        white-space: nowrap;
        margin-bottom: 8px;
    }}

    .metric-card.ev .metric-value {{
        color: {EV};
    }}

    .metric-ratio {{
        display: inline-flex;
        align-items: center;
        border-radius: 999px;
        padding: 4px 8px;
        font-size: .69rem;
        font-weight: 800;
        color: {EV_DARK};
        background: rgba(98,185,0,.12);
    }}

    .metric-ratio.neutral {{
        color: {SUBTEXT};
        background: {PANEL_2};
        border: 1px solid {BORDER};
    }}

    .mini-card {{
        background: {PANEL};
        border: 1px solid {BORDER};
        border-radius: 17px;
        padding: 10px 13px;
        min-height: 66px;
        margin-bottom: 9px;
    }}

    .mini-card.hybrid {{
        border-left: 4px solid {HYBRID};
    }}

    .mini-card.other {{
        border-left: 4px solid {OTHER};
    }}

    .mini-label {{
        color: {SUBTEXT};
        font-size: .68rem;
        font-weight: 700;
    }}

    .mini-value {{
        color: {TEXT};
        font-size: 1.03rem;
        font-weight: 850;
        line-height: 1.1;
        margin-top: 3px;
    }}

    .mini-ratio {{
        color: {SUBTEXT};
        font-size: .65rem;
        margin-top: 2px;
    }}

    .chart-card {{
        background: {PANEL};
        border: 1px solid {BORDER};
        border-radius: 20px;
        padding: 12px 14px 6px 14px;
        box-shadow: 0 10px 28px rgba(0,0,0,.035);
    }}

    .control-card {{
        background: {PANEL};
        border: 1px solid {BORDER};
        border-radius: 18px;
        padding: 13px 14px 3px 14px;
        margin-bottom: 12px;
    }}

    .detail-card {{
        background: {PANEL};
        border: 1px solid {BORDER};
        border-radius: 20px;
        padding: 17px;
        box-shadow: 0 10px 28px rgba(0,0,0,.035);
    }}

    .detail-title {{
        font-size: 1.02rem;
        font-weight: 850;
        margin-bottom: 12px;
    }}

    .detail-metric {{
        border: 1px solid {BORDER};
        border-radius: 16px;
        padding: 13px;
        background: {PANEL_2};
        min-height: 102px;
        margin-bottom: 10px;
    }}

    .detail-metric.ev {{
        border-color: rgba(98,185,0,.50);
        background: rgba(98,185,0,.07);
    }}

    .detail-metric.hybrid {{
        border-color: rgba(243,154,22,.42);
        background: rgba(243,154,22,.06);
    }}

    .detail-metric.other {{
        border-color: rgba(233,86,118,.36);
        background: rgba(233,86,118,.05);
    }}

    .detail-metric .label {{
        color: {SUBTEXT};
        font-size: .72rem;
        font-weight: 750;
    }}

    .detail-metric .number {{
        color: {TEXT};
        font-size: 1.34rem;
        font-weight: 900;
        letter-spacing: -.04em;
        margin: 6px 0 7px 0;
    }}

    .detail-metric.ev .number {{
        color: {EV};
    }}

    .delta {{
        display: inline-block;
        border-radius: 999px;
        padding: 4px 8px;
        font-size: .66rem;
        font-weight: 800;
    }}

    .delta.up {{
        color: #157347;
        background: #E8F8EF;
    }}

    .delta.down {{
        color: #B42318;
        background: #FDECEC;
    }}

    .delta.flat {{
        color: {SUBTEXT};
        background: {PANEL_2};
        border: 1px solid {BORDER};
    }}

    .footer-bar {{
        margin-top: 20px;
        padding: 13px 16px;
        border-radius: 16px;
        background: linear-gradient(90deg, rgba(98,185,0,.15), rgba(98,185,0,.04));
        border: 1px solid rgba(98,185,0,.22);
        color: {TEXT};
        font-size: .77rem;
        font-weight: 700;
        text-align: center;
    }}

    div[data-baseweb="select"] > div {{
        background: {INPUT};
        border-color: {BORDER};
        border-radius: 12px;
    }}

    div[data-baseweb="select"] span {{
        color: {TEXT} !important;
    }}

    [data-testid="stSidebar"] .stRadio > label {{
        font-weight: 800;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 4. DATA
# =========================================================

@st.cache_data
def load_data():
    path = DATA_FILE

    if not path.exists():
        candidates = list(BASE_DIR.glob("전국자동차등록현황*.csv"))
        if not candidates:
            raise FileNotFoundError(
                "같은 폴더에 전국자동차등록현황 CSV가 없습니다."
            )
        path = max(candidates, key=lambda p: p.stat().st_mtime)

    data = pd.read_csv(path, encoding="utf-8-sig")

    required = [
        "연도", "월", "시도", "지역",
        "등록대수", "내연기관", "전기차", "하이브리드", "기타",
    ]
    missing = [c for c in required if c not in data.columns]
    if missing:
        raise ValueError(
            "CSV에 필요한 컬럼이 없습니다: " + ", ".join(missing)
        )

    numeric_cols = [
        "연도", "월", "등록대수",
        "내연기관", "전기차", "하이브리드", "기타",
    ]

    for col in numeric_cols:
        data[col] = pd.to_numeric(data[col], errors="coerce")

    data = data.dropna(subset=["연도", "월"]).copy()

    for col in [
        "등록대수", "내연기관", "전기차", "하이브리드", "기타"
    ]:
        data[col] = data[col].fillna(0)

    data["연도"] = data["연도"].astype(int)
    data["월"] = data["월"].astype(int)
    data["시도"] = data["시도"].fillna("").astype(str).str.strip()
    data["지역"] = data["지역"].fillna("").astype(str).str.strip()

    return data


try:
    df = load_data()
except Exception as e:
    st.error(str(e))
    st.stop()


# =========================================================
# 5. CALCULATIONS
# =========================================================

def national_period(data, year, month):
    period = data[
        (data["연도"] == year) &
        (data["월"] == month)
    ].copy()

    rows = []

    # 경기: 시/군 합산, 비정상적으로 작은 부천시 행 제외
    gyeonggi = period[period["시도"] == "경기"].copy()
    gyeonggi = gyeonggi[
        ~(
            (gyeonggi["지역"] == "부천시") &
            (gyeonggi["등록대수"] < 1000)
        )
    ]

    if len(gyeonggi) >= 30:
        vals = {
            "내연기관": gyeonggi["내연기관"].sum(),
            "전기차": gyeonggi["전기차"].sum(),
            "하이브리드": gyeonggi["하이브리드"].sum(),
            "기타": gyeonggi["기타"].sum(),
        }

        rows.append({
            "지역": "경기도",
            **vals,
            "등록대수": sum(vals.values()),
        })

    # 서울: 25개 자치구 합산
    seoul = period[period["시도"] == "서울"].copy()

    if len(seoul) >= 25:
        vals = {
            "내연기관": seoul["내연기관"].sum(),
            "전기차": seoul["전기차"].sum(),
            "하이브리드": seoul["하이브리드"].sum(),
            "기타": seoul["기타"].sum(),
        }

        rows.append({
            "지역": "서울",
            **vals,
            "등록대수": sum(vals.values()),
        })

    # 이미 집계된 지역
    for region_name in [
        "경상도", "전라도", "충청도", "강원도"
    ]:
        one = period[period["지역"] == region_name]

        if not one.empty:
            r = one.iloc[0]

            rows.append({
                "지역": region_name,
                "내연기관": r["내연기관"],
                "전기차": r["전기차"],
                "하이브리드": r["하이브리드"],
                "기타": r["기타"],
                "등록대수": (
                    r["내연기관"]
                    + r["전기차"]
                    + r["하이브리드"]
                    + r["기타"]
                ),
            })

    return pd.DataFrame(rows)


def detail_period(data, year, month, region):
    period = data[
        (data["연도"] == year) &
        (data["월"] == month)
    ].copy()

    if region == "서울":
        return period[
            period["시도"] == "서울"
        ].copy()

    if region == "경기도":
        result = period[
            period["시도"] == "경기"
        ].copy()

        return result[
            ~(
                (result["지역"] == "부천시") &
                (result["등록대수"] < 1000)
            )
        ].copy()

    return period[
        period["지역"] == region
    ].copy()


def fuel_totals(data):
    return {
        "내연기관": float(data["내연기관"].sum()),
        "전기차": float(data["전기차"].sum()),
        "하이브리드": float(data["하이브리드"].sum()),
        "기타": float(data["기타"].sum()),
    }


def pct(value, total):
    return (value / total * 100) if total else 0


def fmt_delta(current, previous):
    if previous == 0:
        return "변동 없음", "flat"

    change = current - previous
    rate = change / previous * 100

    if change > 0:
        return f"▲ {change:,.0f}대  (+{rate:.1f}%)", "up"

    if change < 0:
        return f"▼ {abs(change):,.0f}대  ({rate:.1f}%)", "down"

    return "변동 없음", "flat"


def plot_theme(fig):
    fig.update_layout(
        paper_bgcolor=PANEL,
        plot_bgcolor=PANEL,
        font=dict(
            family="Arial, sans-serif",
            color=TEXT,
        ),
        margin=dict(l=20, r=20, t=25, b=20),
        hoverlabel=dict(
            bgcolor=PANEL,
            font_color=TEXT,
        ),
    )

    fig.update_xaxes(
        gridcolor=GRID,
        linecolor=BORDER,
        zerolinecolor=GRID,
    )

    fig.update_yaxes(
        gridcolor=GRID,
        linecolor=BORDER,
        zerolinecolor=GRID,
    )

    return fig


# =========================================================
# 6. SIDEBAR
# =========================================================

st.sidebar.markdown("## ⚡ EV DATA LAB")
st.sidebar.caption("자동차 등록 데이터를 한눈에")
st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "페이지",
    [
        "전국단위 자동차 현황 데이터",
        "서울&경기 내연기관 vs 전기자동차",
        "전기차 충전소 설치 현황",
        "전기차 보조금",
        "FAQ",
    ],
)

st.sidebar.markdown("---")

st.session_state.dark_mode = st.sidebar.toggle(
    "다크모드",
    value=st.session_state.dark_mode,
)

st.sidebar.markdown(
    '<div style="margin-top:18px; font-size:.72rem; color:#8090A0;">'
    "데이터 기준 · 2023.01 — 2026.08"
    "</div>",
    unsafe_allow_html=True,
)


# =========================================================
# 7. MAIN
# =========================================================

if menu == "전국단위 자동차 현황 데이터":

    current = national_period(
        df,
        CURRENT_YEAR,
        CURRENT_MONTH,
    )

    total = current["등록대수"].sum()
    ev = current["전기차"].sum()
    ice = current["내연기관"].sum()
    hybrid = current["하이브리드"].sum()
    other = current["기타"].sum()

    ev_pct = pct(ev, total)
    ice_pct = pct(ice, total)
    hybrid_pct = pct(hybrid, total)
    other_pct = pct(other, total)

    # -----------------------------------------------------
    # HERO
    # -----------------------------------------------------

    st.markdown(
        """
        <div class="hero">
            <div class="hero-kicker">⚡ ELECTRIC VEHICLE FOCUS</div>
            <div class="hero-title">
                자동차 등록 현황 <span class="ev">대시보드</span>
            </div>
            <div class="hero-desc">
                자동차 등록 데이터를 기반으로 보는 친환경차 전환 흐름
            </div>
            <div class="hero-meta">
                현재 기준 · 2026년 08월  ·  2023.01 — 2026.08
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # -----------------------------------------------------
    # TOP KPI
    # -----------------------------------------------------

    c1, c2, c3, c4 = st.columns(
        [1.35, 1.35, 1.35, 0.85],
        gap="medium",
    )

    with c1:
        st.markdown(
            f"""
            <div class="metric-card">
                <span class="metric-icon">🚘</span>
                <div class="metric-label">총 등록대수</div>
                <div class="metric-value">{total:,.0f}대</div>
                <span class="metric-ratio neutral">전체 기준</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            f"""
            <div class="metric-card ev">
                <span class="metric-icon">⚡</span>
                <div class="metric-label">전기차 등록수</div>
                <div class="metric-value">{ev:,.0f}대</div>
                <span class="metric-ratio">전체의 {ev_pct:.1f}%</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c3:
        st.markdown(
            f"""
            <div class="metric-card">
                <span class="metric-icon">⛽</span>
                <div class="metric-label">내연기관 등록수</div>
                <div class="metric-value">{ice:,.0f}대</div>
                <span class="metric-ratio neutral">전체의 {ice_pct:.1f}%</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c4:
        st.markdown(
            f"""
            <div class="mini-card hybrid">
                <div class="mini-label">하이브리드</div>
                <div class="mini-value">{hybrid:,.0f}대</div>
                <div class="mini-ratio">전체의 {hybrid_pct:.1f}%</div>
            </div>
            <div class="mini-card other">
                <div class="mini-label">기타</div>
                <div class="mini-value">{other:,.0f}대</div>
                <div class="mini-ratio">전체의 {other_pct:.1f}%</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # -----------------------------------------------------
    # CHARTS
    # -----------------------------------------------------

    st.markdown(
        """
        <div class="section-head">
            <div class="section-title">📊 지역별 등록 현황</div>
            <div class="section-note">회색 · 전체 등록대수  /  초록 · 전기차</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns(
        [1.42, 1],
        gap="medium",
    )

    with left:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)

        chart_df = current[
            ["지역", "등록대수", "전기차"]
        ].sort_values(
            "등록대수",
            ascending=False,
        ).reset_index(drop=True)

        chart_df["비전기차"] = (
            chart_df["등록대수"] -
            chart_df["전기차"]
        )

        fig = go.Figure()

        fig.add_bar(
            x=chart_df["지역"],
            y=chart_df["비전기차"],
            name="비전기차",
            marker_color=ICE,
            hovertemplate="%{x}<br>비전기차 %{y:,.0f}대<extra></extra>",
        )

        fig.add_bar(
            x=chart_df["지역"],
            y=chart_df["전기차"],
            name="전기차",
            marker_color=EV,
            hovertemplate="%{x}<br>전기차 %{y:,.0f}대<extra></extra>",
        )

        fig.update_layout(
            barmode="stack",
            height=390,
            showlegend=False,
            yaxis_title="등록대수",
            xaxis_title="",
        )

        plot_theme(fig)

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)

        ft = {
            "내연기관": ice,
            "하이브리드": hybrid,
            "전기차": ev,
            "기타": other,
        }

        fuel_df = pd.DataFrame({
            "연료": list(ft.keys()),
            "등록대수": list(ft.values()),
        })

        fig = go.Figure(
            go.Pie(
                labels=fuel_df["연료"],
                values=fuel_df["등록대수"],
                hole=0.66,
                sort=False,
                marker=dict(
                    colors=[ICE, HYBRID, EV, OTHER],
                    line=dict(
                        color=PANEL,
                        width=2,
                    ),
                ),
                textinfo="percent",
                hovertemplate="%{label}<br>%{value:,.0f}대<extra></extra>",
            )
        )

        fig.update_layout(
            height=390,
            showlegend=True,
            legend=dict(
                orientation="h",
                y=-0.02,
                x=0.5,
                xanchor="center",
            ),
        )

        plot_theme(fig)

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

        st.markdown("</div>", unsafe_allow_html=True)

    # -----------------------------------------------------
    # ANALYSIS
    # -----------------------------------------------------

    st.markdown(
        """
        <div class="section-head" style="margin-top:22px;">
            <div class="section-title">🔎 기간별 지역 분석</div>
            <div class="section-note">원하는 시점과 지역을 선택해 비교</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="control-card">', unsafe_allow_html=True)

    a, b, c = st.columns(
        [1, 1, 2],
        gap="small",
    )

    with a:
        year = st.selectbox(
            "연도",
            YEARS,
            index=YEARS.index(2026),
        )

    max_month = 8 if year == 2026 else 12

    with b:
        month = st.selectbox(
            "월",
            list(range(1, max_month + 1)),
            index=min(7, max_month - 1),
        )

    available = national_period(
        df,
        year,
        month,
    )

    if available.empty:
        st.warning("선택한 기간의 집계 가능한 데이터가 없습니다.")
        st.stop()

    with c:
        region = st.selectbox(
            "지역",
            available["지역"].tolist(),
        )

    st.markdown("</div>", unsafe_allow_html=True)

    prev_year = year
    prev_month = month - 1

    if prev_month == 0:
        prev_year -= 1
        prev_month = 12

    detail = detail_period(
        df,
        year,
        month,
        region,
    )

    previous_detail = detail_period(
        df,
        prev_year,
        prev_month,
        region,
    )

    cur = fuel_totals(detail)
    prev = fuel_totals(previous_detail)

    l2, r2 = st.columns(
        [1.05, 1.15],
        gap="medium",
    )

    # Donut
    with l2:
        st.markdown(
            f"""
            <div class="detail-card">
                <div class="detail-title">⛽ {region} 연료 비율</div>
            """,
            unsafe_allow_html=True,
        )

        donut_df = pd.DataFrame({
            "연료": list(cur.keys()),
            "등록대수": list(cur.values()),
        })

        fig = go.Figure(
            go.Pie(
                labels=donut_df["연료"],
                values=donut_df["등록대수"],
                hole=0.66,
                sort=False,
                marker=dict(
                    colors=[ICE, EV, HYBRID, OTHER],
                    line=dict(color=PANEL, width=2),
                ),
                textinfo="percent",
                hovertemplate="%{label}<br>%{value:,.0f}대<extra></extra>",
            )
        )

        fig.update_layout(
            height=390,
            showlegend=True,
            legend=dict(
                orientation="h",
                y=-0.02,
                x=0.5,
                xanchor="center",
            ),
        )

        plot_theme(fig)

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

        st.markdown("</div>", unsafe_allow_html=True)

    # 2x2 detail cards
    with r2:
        st.markdown(
            f"""
            <div class="detail-card">
                <div class="detail-title">📌 {region} 상세</div>
            """,
            unsafe_allow_html=True,
        )

        d1, d2 = st.columns(2)

        label_pairs = [
            ("내연기관", "내연기관", ""),
            ("전기차 등록수", "전기차", "ev"),
            ("하이브리드", "하이브리드", "hybrid"),
            ("기타", "기타", "other"),
        ]

        def card_html(label, key, css_class):
            text_delta, delta_class = fmt_delta(
                cur[key],
                prev[key],
            )

            return f"""
            <div class="detail-metric {css_class}">
                <div class="label">{label}</div>
                <div class="number">{cur[key]:,.0f}대</div>
                <span class="delta {delta_class}">{text_delta}</span>
            </div>
            """

        with d1:
            st.markdown(
                card_html(
                    "내연기관",
                    "내연기관",
                    "",
                ),
                unsafe_allow_html=True,
            )

            st.markdown(
                card_html(
                    "하이브리드",
                    "하이브리드",
                    "hybrid",
                ),
                unsafe_allow_html=True,
            )

        with d2:
            st.markdown(
                card_html(
                    "전기차 등록수",
                    "전기차",
                    "ev",
                ),
                unsafe_allow_html=True,
            )

            st.markdown(
                card_html(
                    "기타",
                    "기타",
                    "other",
                ),
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        """
        <div class="footer-bar">
            ⚡ 자동차 등록 데이터를 통해 보는 친환경차 전환의 흐름
        </div>
        """,
        unsafe_allow_html=True,
    )


elif menu == "서울&경기 내연기관 vs 전기자동차":

    st.markdown(
        """
        <div class="hero">
            <div class="hero-kicker">⚡ EV COMPARISON</div>
            <div class="hero-title">서울 · 경기 <span class="ev">내연기관 vs 전기자동차</span></div>
            <div class="hero-desc">서울 자치구와 경기 시·군의 내연기관 및 전기차 등록 현황 비교</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    y = st.selectbox(
        "연도",
        YEARS,
        index=YEARS.index(2026),
        key="sg_y",
    )

    max_month = 8 if y == 2026 else 12

    m = st.selectbox(
        "월",
        list(range(1, max_month + 1)),
        index=min(7, max_month - 1),
        key="sg_m",
    )

    region = st.radio(
        "지역",
        ["서울", "경기도"],
        horizontal=True,
    )

    detail = detail_period(
        df,
        y,
        m,
        region,
    )

    if detail.empty:
        st.warning("선택한 기간의 데이터가 없습니다.")
        st.stop()

    chart = detail[
        ["지역", "내연기관", "전기차"]
    ].copy()

    fig = go.Figure()

    fig.add_bar(
        x=chart["지역"],
        y=chart["내연기관"],
        name="내연기관",
        marker_color=ICE,
    )

    fig.add_bar(
        x=chart["지역"],
        y=chart["전기차"],
        name="전기차",
        marker_color=EV,
    )

    fig.update_layout(
        barmode="group",
        height=500,
    )

    plot_theme(fig)

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    x1, x2, x3 = st.columns(3)

    with x1:
        st.metric(
            "등록대수",
            f"{detail['등록대수'].sum():,.0f}대",
        )

    with x2:
        st.metric(
            "내연기관",
            f"{detail['내연기관'].sum():,.0f}대",
        )

    with x3:
        st.metric(
            "전기차",
            f"{detail['전기차'].sum():,.0f}대",
        )


elif menu == "전기차 충전소 설치 현황":

    st.markdown(
        """
        <div class="hero">
            <div class="hero-kicker">⚡ CHARGING INFRA</div>
            <div class="hero-title">전기차 <span class="ev">충전소 설치 현황</span></div>
            <div class="hero-desc">충전 인프라 데이터 연결 영역</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.info("충전소 데이터를 연결하면 이 화면에 구현할 수 있습니다.")


elif menu == "전기차 보조금":

    st.markdown(
        """
        <div class="hero">
            <div class="hero-kicker">⚡ EV SUBSIDY</div>
            <div class="hero-title">전기차 <span class="ev">보조금</span></div>
            <div class="hero-desc">지역 및 차량별 보조금 데이터 연결 영역</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.info("보조금 데이터를 연결하면 이 화면에 구현할 수 있습니다.")


elif menu == "FAQ":

    st.markdown(
        """
        <div class="hero">
            <div class="hero-kicker">⚡ PROJECT FAQ</div>
            <div class="hero-title">프로젝트 <span class="ev">FAQ</span></div>
            <div class="hero-desc">자동차 등록 데이터와 대시보드 이용 방법</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.info("프로젝트 FAQ 내용을 여기에 연결하면 됩니다.")
