import streamlit as st
import pandas as pd
from db import fetch_data

# =========================================================
# 1. 데이터 로딩 및 이미지 URL 보정 함수
# =========================================================
@st.cache_data(ttl=300)
def get_ev_data(sido, sigungu):
    query = """
        SELECT sido, sigungu, img_url, model_name, trim_name,
               price_after_tax, price_before_tax,
               subsidy_total, subsidy_gov, subsidy_local,
               conversion_total, conversion_gov, conversion_local,
               final_price
        FROM ev_subsidies
        WHERE sido = :sido
    """
    params = {"sido": sido}
    if sigungu and sigungu != "전체":
        query += " AND sigungu = :sigungu"
        params["sigungu"] = sigungu
    return fetch_data(query, params)

@st.cache_data(ttl=300)
def get_ice_data():
    query = """
        SELECT category, model_name, trim_name, price, price_text, img_url
        FROM ice_vehicles
    """
    return fetch_data(query)

def fix_image_url(url):
    """이미지 URL 상대경로 자동 보정"""
    if pd.isna(url) or not str(url).strip():
        return "https://via.placeholder.com/200x120?text=No+Image"
    url = str(url).strip()
    if url.startswith("//"):
        return "https:" + url
    elif url.startswith("/"):
        return "https://www.hyundai.com" + url
    return url

# =========================================================
# 2. 메인 렌더링 함수
# =========================================================
def render():
    st.markdown("""
        <style>
        /* 3단계 최종가 박스 (빨간색) */
        .final-price-box {
            background-color: #FFF5F5;
            border: 2px solid #FEB2B2;
            border-radius: 10px;
            padding: 16px;
            text-align: center;
            font-size: 22px;
            font-weight: 800;
            color: #E53E3E;
            margin-top: 10px;
            margin-bottom: 10px;
        }
        /* 4단계 절약 금액 박스 (초록색) */
        .savings-box {
            background-color: #F0FFF4;
            border: 2px solid #68D391;
            border-radius: 12px;
            padding: 24px;
            text-align: center;
            color: #22543D;
            margin-top: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        }
        .savings-title {
            font-size: 20px;
            font-weight: 700;
            color: #2F855A;
            margin-bottom: 8px;
        }
        .savings-amount {
            font-size: 32px;
            font-weight: 900;
            color: #276749;
        }
        .price-row-bold {
            display: flex;
            justify-content: space-between;
            padding: 5px 0;
            font-size: 15px;
            font-weight: 700;
        }
        .price-sub-row {
            display: flex;
            justify-content: space-between;
            padding: 2px 0 2px 15px;
            font-size: 13px;
            color: #718096;
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("⚖️ 내연기관 vs 전기차 비교")
    st.markdown("---")

    # =========================================================
    # [필터] 상단 조회 필터
    # =========================================================
    st.subheader("⚙️ 비교 조회 필터")
    
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        sido_list = ["서울", "경기"]
        selected_sido = st.selectbox("시/도", sido_list, index=0, key="t2_sido")

    ev_raw = get_ev_data(selected_sido, "전체")
    sigungu_opts = ["전체"]
    if not ev_raw.empty and "sigungu" in ev_raw.columns:
        sigungu_opts += sorted(ev_raw["sigungu"].dropna().unique().tolist())

    with col_f2:
        selected_sigungu = st.selectbox("시/군/구", sigungu_opts, index=0, key="t2_sigungu")

    with col_f3:
        budget_opts = [
            "전체 예산",
            "2000만원 이상 3000만원 미만",
            "3000만원 이상 4000만원 미만",
            "4000만원 이상 5000만원 미만",
            "5000만원 이상 6000만원 미만",
            "6000만원 이상"
        ]
        selected_budget = st.selectbox("예산금액", budget_opts, index=1, key="t2_budget")

    # 예산 범위 설정
    min_b, max_b = 0, 999999999
    if "2000만원 이상 3000만원 미만" in selected_budget: min_b, max_b = 20000000, 30000000
    elif "3000만원 이상 4000만원 미만" in selected_budget: min_b, max_b = 30000000, 40000000
    elif "4000만원 이상 5000만원 미만" in selected_budget: min_b, max_b = 40000000, 50000000
    elif "5000만원 이상 6000만원 미만" in selected_budget: min_b, max_b = 50000000, 60000000
    elif "6000만원 이상" in selected_budget: min_b, max_b = 60000000, 999999999

    st.markdown("---")

    # 데이터 로드
    ice_df = get_ice_data()
    ev_df = get_ev_data(selected_sido, selected_sigungu)

    ice_filtered = ice_df[(ice_df["price"] >= min_b) & (ice_df["price"] < max_b)] if not ice_df.empty else pd.DataFrame()
    ev_filtered = ev_df[(ev_df["final_price"] >= min_b) & (ev_df["final_price"] < max_b)] if not ev_df.empty else pd.DataFrame()

    # 페이지네이션 세션 상태
    if "ice_page" not in st.session_state: st.session_state["ice_page"] = 1
    if "ev_page" not in st.session_state: st.session_state["ev_page"] = 1

    # =========================================================
    # [1단계] 모델 선택 (콜백 함수 기반 단일 선택 및 model_name 연동)
    # =========================================================
    step1_col_left, step1_col_right = st.columns(2)

    def on_ice_select(chosen_model, all_models):
        st.session_state["selected_ice_model"] = chosen_model
        for m in all_models:
            st.session_state[f"chk_ice_{m}"] = (m == chosen_model)

    def on_ev_select(chosen_model, all_models):
        st.session_state["selected_ev_model"] = chosen_model
        for m in all_models:
            st.session_state[f"chk_ev_{m}"] = (m == chosen_model)

    # 1. 내연기관 모델 선택
    with step1_col_left:
        st.markdown("## ⛽ 내연기관")
        st.markdown("### 1. 모델 선택")
        if ice_filtered.empty:
            st.info("조건에 맞는 내연기관 차량이 없습니다.")
        else:
            ice_models = ice_filtered[["model_name", "img_url"]].drop_duplicates("model_name").reset_index(drop=True)
            all_ice_names = ice_models["model_name"].tolist()

            if "selected_ice_model" not in st.session_state or st.session_state["selected_ice_model"] not in all_ice_names:
                st.session_state["selected_ice_model"] = all_ice_names[0]

            for m in all_ice_names:
                key = f"chk_ice_{m}"
                if key not in st.session_state:
                    st.session_state[key] = (m == st.session_state["selected_ice_model"])

            total_ice = len(ice_models)
            per_page = 3
            total_ice_pages = max(1, (total_ice + per_page - 1) // per_page)
            
            curr_page = min(st.session_state["ice_page"], total_ice_pages)
            start_idx = (curr_page - 1) * per_page
            page_models_ice = ice_models.iloc[start_idx : start_idx + per_page]

            cols_m = st.columns(per_page)
            for idx, (_, row) in enumerate(page_models_ice.iterrows()):
                with cols_m[idx % per_page]:
                    m_name = row["model_name"]
                    
                    st.checkbox(
                        "", 
                        key=f"chk_ice_{m_name}", 
                        on_change=on_ice_select, 
                        args=(m_name, all_ice_names),
                        label_visibility="collapsed"
                    )
                    st.image(fix_image_url(row["img_url"]), use_container_width=True)
                    # model_name 컬럼 값 출력 (중앙 정렬 굵은 글씨)
                    st.markdown(f"<p style='text-align: center; font-weight: bold; margin-top: 5px;'>{m_name}</p>", unsafe_allow_html=True)

            p_col1, p_col2, p_col3 = st.columns([1, 2, 1])
            with p_col1:
                if st.button("◀", key="prev_ice") and curr_page > 1:
                    st.session_state["ice_page"] -= 1
                    st.rerun()
            with p_col2:
                st.markdown(f"<p style='text-align: center;'><b>{curr_page} / {total_ice_pages} 페이지</b><br><small>총 {total_ice}개</small></p>", unsafe_allow_html=True)
            with p_col3:
                if st.button("▶", key="next_ice") and curr_page < total_ice_pages:
                    st.session_state["ice_page"] += 1
                    st.rerun()

    # 1. 전기차 모델 선택
    with step1_col_right:
        st.markdown("## ⚡ 전기차")
        st.markdown("### 1. 모델 선택")
        if ev_filtered.empty:
            st.info("조건에 맞는 전기차 차량이 없습니다.")
        else:
            ev_models = ev_filtered[["model_name", "img_url"]].drop_duplicates("model_name").reset_index(drop=True)
            all_ev_names = ev_models["model_name"].tolist()

            if "selected_ev_model" not in st.session_state or st.session_state["selected_ev_model"] not in all_ev_names:
                st.session_state["selected_ev_model"] = all_ev_names[0]

            for m in all_ev_names:
                key = f"chk_ev_{m}"
                if key not in st.session_state:
                    st.session_state[key] = (m == st.session_state["selected_ev_model"])

            total_ev = len(ev_models)
            per_page = 3
            total_ev_pages = max(1, (total_ev + per_page - 1) // per_page)

            curr_page = min(st.session_state["ev_page"], total_ev_pages)
            start_idx = (curr_page - 1) * per_page
            page_models_ev = ev_models.iloc[start_idx : start_idx + per_page]

            cols_m_ev = st.columns(per_page)
            for idx, (_, row) in enumerate(page_models_ev.iterrows()):
                with cols_m_ev[idx % per_page]:
                    m_name = row["model_name"]
                    
                    st.checkbox(
                        "", 
                        key=f"chk_ev_{m_name}", 
                        on_change=on_ev_select, 
                        args=(m_name, all_ev_names),
                        label_visibility="collapsed"
                    )
                    st.image(fix_image_url(row["img_url"]), use_container_width=True)
                    # model_name 컬럼 값 출력 (중앙 정렬 굵은 글씨)
                    st.markdown(f"<p style='text-align: center; font-weight: bold; margin-top: 5px;'>{m_name}</p>", unsafe_allow_html=True)

            p_col1, p_col2, p_col3 = st.columns([1, 2, 1])
            with p_col1:
                if st.button("◀", key="prev_ev") and curr_page > 1:
                    st.session_state["ev_page"] -= 1
                    st.rerun()
            with p_col2:
                st.markdown(f"<p style='text-align: center;'><b>{curr_page} / {total_ev_pages} 페이지</b><br><small>총 {total_ev}개</small></p>", unsafe_allow_html=True)
            with p_col3:
                if st.button("▶", key="next_ev") and curr_page < total_ev_pages:
                    st.session_state["ev_page"] += 1
                    st.rerun()

    # 1단계 수평 구분선
    st.markdown("---")

    # =========================================================
    # [2단계] 트림 선택
    # =========================================================
    step2_col_left, step2_col_right = st.columns(2)

    selected_ice_model = st.session_state.get("selected_ice_model")
    selected_ev_model = st.session_state.get("selected_ev_model")

    selected_ice_info = None
    selected_ev_info = None

    # 2. 내연기관 트림 선택
    with step2_col_left:
        if selected_ice_model:
            st.markdown(f"### 2. [{selected_ice_model}] 트림 선택")
            ice_trims = ice_filtered[ice_filtered["model_name"] == selected_ice_model]
            if not ice_trims.empty:
                with st.container(border=True):
                    trim_names = ice_trims["trim_name"].tolist()
                    selected_ice_trim = st.radio("내연기관 트림 목록", trim_names, key="radio_ice_trim", label_visibility="collapsed")
                    selected_ice_info = ice_trims[ice_trims["trim_name"] == selected_ice_trim].iloc[0]

    # 2. 전기차 트림 선택
    with step2_col_right:
        if selected_ev_model:
            st.markdown(f"### 2. [{selected_ev_model}] 트림 선택")
            ev_trims = ev_filtered[ev_filtered["model_name"] == selected_ev_model]
            if not ev_trims.empty:
                with st.container(border=True):
                    trim_names = ev_trims["trim_name"].tolist()
                    selected_ev_trim = st.radio("전기차 트림 목록", trim_names, key="radio_ev_trim", label_visibility="collapsed")
                    selected_ev_info = ev_trims[ev_trims["trim_name"] == selected_ev_trim].iloc[0]

    # 2단계 수평 구분선
    st.markdown("---")

    # =========================================================
    # [3단계] 상세 금액
    # =========================================================
    step3_col_left, step3_col_right = st.columns(2)

    # 3. 내연기관 상세 금액
    with step3_col_left:
        st.markdown("### 3. 상세 금액")
        if selected_ice_info is not None:
            ice_final_price = selected_ice_info["price"]
            with st.container(border=True):
                st.markdown(
                    f"<div class='final-price-box'>최종가: {ice_final_price:,.0f} 원</div>",
                    unsafe_allow_html=True
                )

    # 3. 전기차 상세 금액
    with step3_col_right:
        st.markdown("### 3. 상세 금액")
        if selected_ev_info is not None:
            with st.container(border=True):
                st.markdown(f"""
                    <div class='price-row-bold'><span>세제 혜택 후</span><span>{selected_ev_info['price_after_tax']:,.0f}원</span></div>
                    <div class='price-row-bold'><span>세제 혜택 전</span><span>{selected_ev_info['price_before_tax']:,.0f}원</span></div>
                    <div class='price-row-bold'><span>보조금</span><span>-{selected_ev_info['subsidy_total']:,.0f}원</span></div>
                    <div class='price-sub-row'><span>국가 보조금</span><span>-{selected_ev_info['subsidy_gov']:,.0f}원</span></div>
                    <div class='price-sub-row'><span>지자체 보조금</span><span>-{selected_ev_info['subsidy_local']:,.0f}원</span></div>
                    <div class='price-row-bold'><span>전환지원금</span><span>-{selected_ev_info['conversion_total']:,.0f}원</span></div>
                    <div class='price-sub-row'><span>국가 전환지원금</span><span>-{selected_ev_info['conversion_gov']:,.0f}원</span></div>
                    <div class='price-sub-row'><span>지자체 전환지원금</span><span>-{selected_ev_info['conversion_local']:,.0f}원</span></div>
                """, unsafe_allow_html=True)

                st.markdown(
                    f"<div class='final-price-box'>최종가: {selected_ev_info['final_price']:,.0f}원</div>",
                    unsafe_allow_html=True
                )

    # 3단계 수평 구분선
    st.markdown("---")

    # =========================================================
    # [4단계] 최종 가격 비교 및 절약 금액 (초록색 하이라이트)
    # =========================================================
    st.markdown("## 4. 💡 최종 가격 비교 및 절약 금액")

    if selected_ice_info is not None and selected_ev_info is not None:
        ice_p = selected_ice_info["price"]
        ev_p = selected_ev_info["final_price"]
        diff = abs(ice_p - ev_p)
        diff_man = round(diff / 10000)

        if ev_p < ice_p:
            cheaper_msg = f"⚡ <b>[{selected_ev_info['model_name']}] </b> 구매 시 ⛽ <b>[{selected_ice_info['model_name']}] </b>보다"
            saving_text = f"약 <span class='savings-amount'>{diff_man:,}만 원</span> 더 절약할 수 있습니다! 🎉"
        elif ice_p < ev_p:
            cheaper_msg = f"⛽ <b>[{selected_ice_info['model_name']}] </b> 구매 시 ⚡ <b>[{selected_ev_info['model_name']}] </b>보다"
            saving_text = f"약 <span class='savings-amount'>{diff_man:,}만 원</span> 더 절약할 수 있습니다! 🎉"
        else:
            cheaper_msg = f"두 차량의 최종 실구매가가 동일합니다!"
            saving_text = "0원 차이"

        st.markdown(f"""
            <div class='savings-box'>
                <div class='savings-title'>{cheaper_msg}</div>
                <div>{saving_text}</div>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.info("비교할 내연기관과 전기차 모델을 모두 선택해 주시면 최종 절약 금액이 계산됩니다.")