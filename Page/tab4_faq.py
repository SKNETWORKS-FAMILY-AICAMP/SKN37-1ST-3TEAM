import streamlit as st
import pandas as pd
from db import fetch_data

@st.cache_data(ttl=300)
def load_faq_data():
    """MySQL DB 또는 CSV에서 전체 FAQ 데이터를 로드하고 카테고리를 정제합니다."""
    query = """
        SELECT vehicle_type, category, source, question, answer
        FROM faqs
    """
    df = fetch_data(query)
    
    # DB 조회 결과가 없을 경우 CSV 파이프라인 Fallback 로딩
    if df.empty:
        import os
        faq_configs = [
            ('FAQ_내연기관_기아.csv', '내연기관', '기아 (내연기관)'),
            ('FAQ_전기차_기아.csv', '전기차', '기아 (전기차)'),
            ('FAQ_전기차_epit.csv', '전기차', 'E-pit 충전'),
            ('FAQ_전기차_차지비.csv', '전기차', '차지비 충전'),
            ('FAQ_전기차_무공해차.csv', '전기차', '무공해차 보조금')
        ]
        dfs = []
        for fname, vtype, src in faq_configs:
            path = os.path.join("data", "FAQ", fname)
            if not os.path.exists(path):
                path = fname
            if os.path.exists(path):
                try:
                    d = pd.read_csv(path)
                    d_cols = [c.lower() for c in d.columns]
                    q_col = d.columns[d_cols.index('question')] if 'question' in d_cols else '질문'
                    a_col = d.columns[d_cols.index('answer')] if 'answer' in d_cols else '답변'
                    c_col = 'category' if 'category' in d.columns else ('세부카테고리' if '세부카테고리' in d.columns else None)
                    
                    sub_df = pd.DataFrame({
                        'vehicle_type': vtype,
                        'category': d[c_col] if c_col and c_col in d.columns else '일반',
                        'source': src,
                        'question': d[q_col],
                        'answer': d[a_col]
                    })
                    dfs.append(sub_df)
                except Exception:
                    pass
        if dfs:
            df = pd.concat(dfs, ignore_index=True)

    # 카테고리 태그 명칭 정제 ('충전', '충전소 이용', '충전소 기본 이용' -> '충전'으로 자동 통합)
    if not df.empty and 'category' in df.columns:
        df['category'] = df['category'].fillna('일반').astype(str).str.strip()
        df['category'] = df['category'].replace({
            '충전': '충전',
            '충전소 이용': '충전',
            '충전소 기본 이용': '충전'
        })
        
    return df

def render():
    st.title("❓ 통합 FAQ")
    st.caption("대괄호 [카테고리] 태그 또는 검색어를 기준으로 FAQ를 직관적으로 검색하세요.")
    st.markdown("---")

    st.markdown("""
        <style>
        /* 인기 태그 버튼 열 스타일: 사이드바 선택 라디오 버튼 포인트 컬러와 통일 */
        div[data-testid="stColumn"] button {
            background-color: var(--primary-color, #FF4B4B) !important;
            color: #FFFFFF !important;
            border-radius: 20px !important;
            border: 1px solid var(--primary-color, #FF4B4B) !important;
            font-weight: 600 !important;
            font-size: 15px !important;
            transition: all 0.2s ease-in-out !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
        }
        div[data-testid="stColumn"] button:hover {
            background-color: #E03131 !important;
            border-color: #E03131 !important;
            color: #FFFFFF !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 8px rgba(0,0,0,0.15) !important;
        }
        div[data-testid="stColumn"] button:active {
            transform: translateY(0px) !important;
        }
        </style>
    """, unsafe_allow_html=True)

    df_faq = load_faq_data()

    if df_faq.empty:
        st.warning("등록된 FAQ 데이터가 없습니다. DB 또는 CSV 파일 위치를 확인해 주세요.")
        return

    # 검색창 key 세션 상태 초기화
    if "global_faq_search_input" not in st.session_state:
        st.session_state["global_faq_search_input"] = ""

    # 버튼 클릭 시 입력창(session_state)에 자동으로 키워드를 주입하는 콜백 함수
    def set_search_keyword(keyword):
        st.session_state["global_faq_search_input"] = keyword

    # =========================================================
    # [1] 상위 3개 카테고리 태그 자동 추출 & Quick Tag 버튼
    # =========================================================
    st.subheader("🔍 FAQ 카테고리 / 키워드 검색")

    # DB/CSV 데이터에서 '일반', '그외'를 제외한 최다 빈도 카테고리 상위 3개 자동 추출
    top_categories = [
        cat for cat in df_faq['category'].value_counts().index 
        if cat not in ['일반', '그외']
    ][:3]

    st.markdown("##### 🏷️ 인기 카테고리 태그 (클릭 시 자동 입력 및 검색)")
    
    # 버튼 4개 (전체보기 + 상위 3개 카테고리)
    tag_cols = st.columns(len(top_categories) + 1)
    
    # 0번 버튼: 검색어 초기화
    with tag_cols[0]:
        st.button("🔄 전체보기", on_click=set_search_keyword, args=("",), use_container_width=True)

    # 1~3번 버튼: 최다 빈도 3개 카테고리 태그
    for idx, tag in enumerate(top_categories):
        with tag_cols[idx + 1]:
            st.button(f"#{tag}", on_click=set_search_keyword, args=(tag,), use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # =========================================================
    # [2] 통합 검색 입력창 (st.session_state 연동)
    # =========================================================
    search_query = st.text_input(
        "검색어 입력", 
        key="global_faq_search_input", 
        placeholder="[카테고리] 태그명 또는 키워드를 입력하세요 (예: 충전, 배터리, 결제, 네비게이션)",
        label_visibility="collapsed"
    ).strip()

    # 입력된 검색어 매칭 로직
    if search_query:
        # 1. [카테고리] 태그 직접 매칭 (1순위)
        cat_mask = df_faq['category'].astype(str).str.contains(search_query, case=False, na=False)
        
        # 2. 질문 및 답변 본문 매칭 (2순위)
        content_mask = (
            df_faq['question'].astype(str).str.contains(search_query, case=False, na=False) |
            df_faq['answer'].astype(str).str.contains(search_query, case=False, na=False)
        )
        
        filtered_df = df_faq[cat_mask | content_mask].copy()
        
        # 카테고리 일치 항목을 결과 상단에 정렬
        filtered_df['is_cat_match'] = cat_mask
        filtered_df = filtered_df.sort_values(by=['is_cat_match'], ascending=False).drop(columns=['is_cat_match'])
        
        st.success(f"🔍 **'[{search_query}]'** 관련 FAQ 검색 결과: 총 **{len(filtered_df)}**건의 질문이 있습니다.")
    else:
        filtered_df = df_faq.copy()

    st.markdown("<br>", unsafe_allow_html=True)

    # =========================================================
    # [3] 카테고리 탭 (전체 / 전기차 & 충전소 / 내연기관 / 그외)
    # =========================================================
    tab_all, tab_ev, tab_ice, tab_etc = st.tabs([
        "📋 전체 FAQ", 
        "⚡ 전기차 & 충전소 FAQ", 
        "🚗 내연기관 FAQ", 
        "💡 그외 FAQ"
    ])

    with tab_all:
        st.subheader("📋 전체 FAQ 목록")
        if filtered_df.empty:
            st.info("검색어에 일치하는 질문이 없습니다.")
        else:
            for _, row in filtered_df.iterrows():
                with st.expander(f"[{row['category']}] {row['question']}"):
                    st.write(row['answer'])

    with tab_ev:
        st.subheader("⚡ 전기차 및 충전 인프라 FAQ")
        ev_df = filtered_df[
            (filtered_df['vehicle_type'] == '전기차') & 
            (~filtered_df['category'].isin(['그외', '완속충전기 설치지원 사업']))
        ]
        if ev_df.empty:
            st.info("해당하는 전기차/충전소 FAQ 질문이 없습니다.")
        else:
            st.caption(f"총 {len(ev_df)}개의 질문이 있습니다.")
            for _, row in ev_df.iterrows():
                with st.expander(f"[{row['category']}] {row['question']}"):
                    st.write(row['answer'])

    with tab_ice:
        st.subheader("🚗 내연기관 차량 FAQ")
        ice_df = filtered_df[
            (filtered_df['vehicle_type'] == '내연기관') & 
            (~filtered_df['category'].isin(['그외']))
        ]
        if ice_df.empty:
            st.info("해당하는 내연기관 FAQ 질문이 없습니다.")
        else:
            st.caption(f"총 {len(ice_df)}개의 질문이 있습니다.")
            for _, row in ice_df.iterrows():
                with st.expander(f"[{row['category']}] {row['question']}"):
                    st.write(row['answer'])

    with tab_etc:
        st.subheader("💡 그외 FAQ")
        etc_df = filtered_df[
            filtered_df['category'].isin(['그외', '완속충전기 설치지원 사업']) |
            filtered_df['category'].str.contains('그외|기타|설치지원', na=False)
        ]
        if etc_df.empty:
            st.info("해당하는 그외 FAQ 질문이 없습니다.")
        else:
            st.caption(f"총 {len(etc_df)}개의 질문이 있습니다.")
            for _, row in etc_df.iterrows():
                with st.expander(f"[{row['category']}] {row['question']}"):
                    st.write(row['answer'])