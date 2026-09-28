import streamlit as st
from Page import tab1_registration, tab2_comparison, tab3_infrastructure, tab4_faq

st.set_page_config(
    page_title="전기차(EV) 맞춤형 종합 플랫폼",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.sidebar.title("⚡ EV DATA LAB")
st.sidebar.caption("전기차 관심 고객을 위한 데이터 가이드")
st.sidebar.markdown("---")

selected_tab = st.sidebar.radio(
    "📌 메뉴 선택",
    [
        "📊 전국 자동차 등록현황",
        "⚖️ 내연기관 vs 전기차",
        "🔌 전기차 충전소 인프라 현황",
        "❓ 통합 FAQ"
    ]
)

st.sidebar.markdown("---")
st.sidebar.caption("데이터 기준 · 2023.01 — 2026.08")

if selected_tab == "📊 전국 자동차 등록현황":
    tab1_registration.render()
elif selected_tab == "⚖️ 내연기관 vs 전기차":
    tab2_comparison.render()
elif selected_tab == "🔌 전기차 충전소 인프라 현황":
    tab3_infrastructure.render()
elif selected_tab == "❓ 통합 FAQ":
    tab4_faq.render()