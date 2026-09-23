import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path


st.set_page_config(
    page_title="자동차 등록 현황",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "전국자동차등록현황.csv"

PROJECT_REGIONS = [
    "경기도", "경상도", "서울", "전라도", "충청도",
    "인천", "부산", "대구", "강원도", "울산",
]

YEARS = [2023, 2024, 2025, 2026]
CURRENT_YEAR = 2026
CURRENT_MONTH = 8

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

if st.session_state.dark_mode:
    bg, card, text, subtext, border, sidebar = (
        "#2B2F33", "#3A3F44", "#F1F3F5", "#C7CCD1", "#555B61", "#24282C"
    )
else:
    bg, card, text, subtext, border, sidebar = (
        "#F8FAFC", "#FFFFFF", "#1F2937", "#64748B", "#E2E8F0", "#E0F2FE"
    )

st.markdown(
    f"""
    <style>
    .stApp {{ background:{bg}; color:{text}; }}
    [data-testid="stSidebar"] {{ background:{sidebar}; }}
    [data-testid="stSidebar"] * {{ color:{text} !important; }}
    .block-container {{ max-width:1450px; padding-top:1.35rem; padding-bottom:2rem; }}
    h1,h2,h3,h4,p,label {{ color:{text}; }}
    .subtitle {{ color:{subtext}; font-size:.92rem; margin-top:-10px; margin-bottom:18px; }}
    .big-metric [data-testid="stMetric"] {{
        min-height:128px; padding:18px; border:1px solid {border};
        border-radius:16px; background:{card}; overflow:visible;
    }}
    .big-metric [data-testid="stMetricValue"] {{
        font-size:clamp(1.55rem,2.2vw,2.2rem); white-space:nowrap; overflow:visible;
    }}
    .small-metric {{
        background:{card}; border:1px solid {border}; border-radius:14px;
        padding:10px 14px; min-height:58px; margin-bottom:10px; overflow:visible;
    }}
    .small-metric .label {{ color:{subtext}; font-size:.72rem; margin-bottom:2px; }}
    .small-metric .value {{ color:{text}; font-size:1.12rem; font-weight:700; line-height:1.25; white-space:nowrap; }}
    .warning-box {{
        background:{card}; border:1px solid {border}; border-left:4px solid #F59E0B;
        border-radius:12px; padding:12px 14px; margin:8px 0 16px 0; color:{text};
    }}
    div[data-baseweb="select"] > div {{ background-color:{card}; border-color:{border}; }}
    div[data-baseweb="select"] span {{ color:{text} !important; }}
    </style>
    """,
    unsafe_allow_html=True,
)


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
        raise ValueError("CSV에 필요한 컬럼이 없습니다: " + ", ".join(missing))

    for col in ["연도", "월", "등록대수", "내연기관", "전기차", "하이브리드", "기타"]:
        data[col] = pd.to_numeric(data[col], errors="coerce")

    data = data.dropna(subset=["연도", "월"]).copy()

    for col in ["등록대수", "내연기관", "전기차", "하이브리드", "기타"]:
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


def national_period(data, year, month):
    period = data[(data["연도"] == year) & (data["월"] == month)].copy()
    rows = []

    # 경기: 시/군 합계. 비정상적으로 작은 부천시는 제외.
    gyeonggi = period[period["시도"] == "경기"].copy()
    gyeonggi = gyeonggi[
        ~((gyeonggi["지역"] == "부천시") & (gyeonggi["등록대수"] < 1000))
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

    # 서울: 25개 구 합계
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

    # 이미 집계되어 있는 지역
    for region in ["경상도", "전라도", "충청도", "강원도"]:
        one = period[period["지역"] == region]
        if not one.empty:
            r = one.iloc[0]
            rows.append({
                "지역": region,
                "내연기관": r["내연기관"],
                "전기차": r["전기차"],
                "하이브리드": r["하이브리드"],
                "기타": r["기타"],
                "등록대수": r["내연기관"] + r["전기차"] + r["하이브리드"] + r["기타"],
            })

    return pd.DataFrame(rows)


def detail_period(data, year, month, region):
    period = data[(data["연도"] == year) & (data["월"] == month)].copy()

    if region == "서울":
        return period[period["시도"] == "서울"].copy()

    if region == "경기도":
        result = period[period["시도"] == "경기"].copy()
        return result[
            ~((result["지역"] == "부천시") & (result["등록대수"] < 1000))
        ].copy()

    return period[period["지역"] == region].copy()


def fuel_totals(data):
    return {
        "내연기관": data["내연기관"].sum(),
        "전기차": data["전기차"].sum(),
        "하이브리드": data["하이브리드"].sum(),
        "기타": data["기타"].sum(),
    }


def delta_text(current, previous):
    if previous == 0:
        return None
    change = current - previous
    pct = change / previous * 100
    return f"{change:+,.0f}대 ({pct:+.1f}%)"


def theme(fig):
    fig.update_layout(
        paper_bgcolor=card,
        plot_bgcolor=card,
        font=dict(color=text),
        legend=dict(font=dict(color=text)),
        margin=dict(l=20, r=20, t=20, b=20),
    )
    fig.update_xaxes(gridcolor=border, zerolinecolor=border, linecolor=border)
    fig.update_yaxes(gridcolor=border, zerolinecolor=border, linecolor=border)
    return fig


st.sidebar.markdown("## 🚗 자동차 등록 현황")
st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "메뉴",
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
    "🌙 다크모드",
    value=st.session_state.dark_mode,
)
st.sidebar.caption("데이터 기준: 2023년 01월 ~ 2026년 08월")


if menu == "전국단위 자동차 현황 데이터":

    st.title("🚗 자동차 등록 현황 대시보드")
    st.markdown(
        '<div class="subtitle">자동차등록현황_2023_2026 원본 기준</div>',
        unsafe_allow_html=True,
    )

    current = national_period(df, CURRENT_YEAR, CURRENT_MONTH)

    total = current["등록대수"].sum()
    ev = current["전기차"].sum()
    ice = current["내연기관"].sum()
    hybrid = current["하이브리드"].sum()
    other = current["기타"].sum()

    c1, c2, c3, c4 = st.columns([2.15, 2.15, 2.15, 2.15], gap="small")

    with c1:
        st.markdown('<div class="big-metric">', unsafe_allow_html=True)
        st.metric("총 등록대수", f"{total:,.0f}대")
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="big-metric">', unsafe_allow_html=True)
        st.metric("전기차 등록수", f"{ev:,.0f}대")
        st.markdown("</div>", unsafe_allow_html=True)

    with c3:
        st.markdown('<div class="big-metric">', unsafe_allow_html=True)
        st.metric("내연기관 등록수", f"{ice:,.0f}대")
        st.markdown("</div>", unsafe_allow_html=True)

    with c4:
        st.markdown(
            f"""
            <div class="small-metric">
                <div class="label">하이브리드 등록수</div>
                <div class="value">{hybrid:,.0f}대</div>
            </div>
            <div class="small-metric">
                <div class="label">기타 등록수</div>
                <div class="value">{other:,.0f}대</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    left, right = st.columns([1.35, 1], gap="medium")

    with left:
        st.subheader("📊 지역별 등록 현황")
        if current.empty:
            st.info("현재 시점의 집계 가능한 지역 데이터가 없습니다.")
        else:
            chart_df = current[["지역", "등록대수"]].sort_values("등록대수", ascending=False)
            fig = px.bar(chart_df, x="지역", y="등록대수", text="등록대수")
            fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
            fig.update_layout(showlegend=False, height=360)
            theme(fig)
            st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("⛽ 연료 타입별 비율")
        ft = fuel_totals(current)
        fuel_df = pd.DataFrame({"연료": list(ft), "등록대수": list(ft.values())})
        fig = px.pie(fuel_df, names="연료", values="등록대수", hole=0.58)
        fig.update_traces(textinfo="percent+label")
        fig.update_layout(height=360)
        theme(fig)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("🔎 기간별 지역 분석")

    a, b, c = st.columns([1, 1, 2], gap="small")

    with a:
        year = st.selectbox("연도", YEARS, index=YEARS.index(2026))

    max_month = 8 if year == 2026 else 12

    with b:
        month = st.selectbox("월", list(range(1, max_month + 1)), index=min(7, max_month - 1))

    available = national_period(df, year, month)

    if available.empty:
        st.warning("선택한 기간의 집계 가능한 데이터가 없습니다.")
        st.stop()

    with c:
        region = st.selectbox("지역", available["지역"].tolist())

    prev_year = year
    prev_month = month - 1
    if prev_month == 0:
        prev_year -= 1
        prev_month = 12

    detail = detail_period(df, year, month, region)
    previous_detail = detail_period(df, prev_year, prev_month, region)

    cur_f = fuel_totals(detail)
    prev_f = fuel_totals(previous_detail)

    l2, r2 = st.columns([1.1, 1], gap="medium")

    with l2:
        st.markdown(f"### ⛽ {region} 연료 비율")
        ddf = pd.DataFrame({"연료": list(cur_f), "등록대수": list(cur_f.values())})
        fig = px.pie(ddf, names="연료", values="등록대수", hole=0.60)
        fig.update_traces(textinfo="percent+label")
        fig.update_layout(height=390)
        theme(fig)
        st.plotly_chart(fig, use_container_width=True)

    with r2:
        st.markdown(f"### 📌 {region} 상세")

        m1, m2 = st.columns(2)
        with m1:
            st.metric("내연기관", f"{cur_f['내연기관']:,.0f}대",
                      delta=delta_text(cur_f["내연기관"], prev_f["내연기관"]))
        with m2:
            st.metric("전기차 등록수", f"{cur_f['전기차']:,.0f}대",
                      delta=delta_text(cur_f["전기차"], prev_f["전기차"]))

        m3, m4 = st.columns(2)
        with m3:
            st.metric("하이브리드", f"{cur_f['하이브리드']:,.0f}대",
                      delta=delta_text(cur_f["하이브리드"], prev_f["하이브리드"]))
        with m4:
            st.metric("기타", f"{cur_f['기타']:,.0f}대",
                      delta=delta_text(cur_f["기타"], prev_f["기타"]))


elif menu == "서울&경기 내연기관 vs 전기자동차":

    st.title("🏙️ 서울 & 경기 내연기관 vs 전기자동차")
    st.markdown(
        '<div class="subtitle">서울 자치구 / 경기 시·군 상세 데이터</div>',
        unsafe_allow_html=True,
    )

    y = st.selectbox("연도", YEARS, index=YEARS.index(2026), key="sg_y")
    max_month = 8 if y == 2026 else 12
    m = st.selectbox("월", list(range(1, max_month + 1)), index=min(7, max_month - 1), key="sg_m")
    region = st.radio("지역", ["서울", "경기도"], horizontal=True)

    detail = detail_period(df, y, m, region)

    if detail.empty:
        st.warning("선택한 기간의 데이터가 없습니다.")
        st.stop()

    chart = detail[["지역", "내연기관", "전기차"]].copy()
    fig = px.bar(chart, x="지역", y=["내연기관", "전기차"], barmode="group")
    fig.update_layout(height=480)
    theme(fig)
    st.plotly_chart(fig, use_container_width=True)

    x1, x2, x3 = st.columns(3)
    with x1:
        st.metric("등록대수", f"{detail['등록대수'].sum():,.0f}대")
    with x2:
        st.metric("내연기관", f"{detail['내연기관'].sum():,.0f}대")
    with x3:
        st.metric("전기차", f"{detail['전기차'].sum():,.0f}대")


elif menu == "전기차 충전소 설치 현황":
    st.title("🔌 전기차 충전소 설치 현황")
    st.info("충전소 데이터를 연결하면 이 화면에 구현할 수 있습니다.")


elif menu == "전기차 보조금":
    st.title("💰 전기차 보조금")
    st.info("보조금 데이터를 연결하면 이 화면에 구현할 수 있습니다.")


elif menu == "FAQ":
    st.title("❓ FAQ")
    st.info("프로젝트 FAQ 내용을 여기에 연결하면 됩니다.")
