import os
import pandas as pd
import plotly.express as px
import streamlit as st
from db import fetch_data

# ==============================================================================
# 1. 환경공단 OpenAPI 충전기 타입 규격 매핑
# ==============================================================================
CHGER_TYPE_MAP = {
    "01": "DC차데모", "02": "AC완속", "03": "DC차데모+AC3상",
    "04": "DC콤보", "05": "DC차데모+DC콤보", "06": "DC차데모+AC3상+DC콤보",
    "07": "AC3상", "08": "DC콤보(완속)", "09": "NACS",
    "10": "DC콤보+NACS", "11": "DC콤보2(버스전용)"
}

# ==============================================================================
# 2. 충전소 데이터 로드 & 통합 전처리 함수 (DB / CSV Fallback)
# ==============================================================================
@st.cache_data(ttl=600)
def load_charging_data():
    """MySQL DB 또는 로컬 CSV 파일에서 충전소 데이터를 조회하고 가공합니다."""
    # 1. DB에서 먼저 데이터 조회
    query = """
        SELECT stat_name AS statNm, stat_id AS statId, chger_id AS chgerId,
               chger_type AS chgerType, output, addr, lat, lng, region AS 권역
        FROM charging_stations
    """
    df_raw = fetch_data(query)

    # 2. DB 데이터가 없으면 로컬 CSV 파일 읽기
    if df_raw.empty:
        loaded_dfs = []
        region_files = {
            "서울": "전기차충전소_서울.csv",
            "경기": "전기차충전소_경기도.csv",
            "강원": "전기차충전소_강원도.csv",
            "충청": "전기차충전소_충청도.csv",
            "전라": "전기차충전소_전라도.csv",
            "경상": "전기차충전소_경상도.csv",
            "제주": "전기차충전소_제주도.csv"
        }
        
        possible_dirs = [
            os.path.join("data", "전기차충전소"),
            "data",
            "지역별_충전소데이터",
            "."
        ]
        
        for region_name, filename in region_files.items():
            for pdir in possible_dirs:
                fpath = os.path.join(pdir, filename)
                if os.path.exists(fpath):
                    try:
                        temp = pd.read_csv(fpath, encoding="utf-8-sig", dtype=str)
                    except UnicodeDecodeError:
                        temp = pd.read_csv(fpath, encoding="cp949", dtype=str)
                    temp["권역"] = region_name
                    loaded_dfs.append(temp)
                    break

        if loaded_dfs:
            df_raw = pd.concat(loaded_dfs, ignore_index=True)
            rename_map = {
                "충전소명": "statNm", "충전소ID": "statId", "충전기ID": "chgerId",
                "충전기타입": "chgerType", "충전용량": "output", "주소": "addr",
                "위도": "lat", "경도": "lng"
            }
            df_raw = df_raw.rename(columns=rename_map)

    if df_raw.empty:
        return pd.DataFrame()

    df_raw["lat"] = pd.to_numeric(df_raw.get("lat"), errors="coerce")
    df_raw["lng"] = pd.to_numeric(df_raw.get("lng"), errors="coerce")
    df_raw["output"] = pd.to_numeric(df_raw.get("output"), errors="coerce").fillna(0)
    
    valid_raw = df_raw.dropna(subset=["lat", "lng"]).copy()
    if valid_raw.empty:
        return pd.DataFrame()

    valid_raw["충전기타입명"] = (
        valid_raw["chgerType"].astype(str).str.strip().str.zfill(2).map(CHGER_TYPE_MAP).fillna("기타")
    )

    valid_raw["_is_slow"] = valid_raw["chgerType"].isin(["02", "08"]) | ((valid_raw["output"] > 0) & (valid_raw["output"] <= 14))
    valid_raw["_is_fast"] = (valid_raw["output"] >= 50) | valid_raw["chgerType"].isin(["01", "03", "04", "05", "06", "07", "09", "10", "11"])

    group_col = "statId" if "statId" in valid_raw.columns and valid_raw["statId"].str.strip().any() else "statNm"

    df_station = valid_raw.groupby(group_col, as_index=False).agg(
        권역=("권역", "first"),
        statNm=("statNm", "first"),
        addr=("addr", "first"),
        lat=("lat", "mean"),
        lng=("lng", "mean"),
        충전기수=("chgerType", "count"),
        최대출력=("output", "max"),
        지원사양=("충전기타입명", lambda x: ", ".join(pd.Series(x).dropna().unique()[:3])),
        has_slow=("_is_slow", "any"),
        has_fast=("_is_fast", "any")
    ).rename(columns={"최대출력": "최대출력(kW)"})

    def get_type_label(row):
        if row["has_slow"] and row["has_fast"]: return "급속/완속 동시"
        elif row["has_fast"]: return "급속 전용"
        elif row["has_slow"]: return "완속 전용"
        return "기타"

    df_station["충전소구분"] = df_station.apply(get_type_label, axis=1)
    df_station = df_station.drop(columns=["has_slow", "has_fast"])

    return df_station

# ==============================================================================
# 3. 메인 렌더링 함수
# ==============================================================================
def render():
    st.title("🔌 전기차 충전소 인프라 현황")
    st.markdown("---")

    df_station = load_charging_data()

    if df_station.empty:
        st.warning("충전소 데이터를 불러올 수 없습니다. DB 및 CSV 파일 위치를 확인해 주세요.")
        return

    # ==============================================================================
    # [상단 영역] tab3_image1: 공간 지도 위치 확보 (Container)
    # ==============================================================================
    map_container = st.container()

    # ==============================================================================
    # [하단 영역] tab3_image2: 검색 및 사양 필터
    # ==============================================================================
    st.markdown("---")
    st.subheader("🔍 검색 및 사양 필터")

    available_regions = ["서울", "경기", "강원", "충청", "전라", "경상", "제주"]
    existing_regions = [r for r in available_regions if r in df_station["권역"].unique()]
    default_region = ["서울"] if "서울" in existing_regions else ([existing_regions[0]] if existing_regions else [])

    # 필터 1행 (3개 열)
    f_col1, f_col2, f_col3 = st.columns(3)
    with f_col1:
        selected_regions = st.multiselect("지역(권역) 선택", options=existing_regions, default=default_region)
    with f_col2:
        cat_options = ["완속 전용", "급속/완속 동시", "급속 전용"]
        selected_types = st.multiselect("충전소 유형 (사양)", options=cat_options, default=cat_options)
    with f_col3:
        all_connectors = sorted(list(set(CHGER_TYPE_MAP.values())))
        selected_connectors = st.multiselect(
            "지원 커넥터 규격", 
            options=all_connectors, 
            default=[], 
            help="비워두면 모든 커넥터 규격을 검색합니다."
        )

    # 필터 2행 (2개 열)
    f_col4, f_col5 = st.columns([1, 2])
    with f_col4:
        min_kw = st.slider("최소 충전용량 (kW 이상)", 0, 350, 0, step=10)
    with f_col5:
        search_kw = st.text_input("충전소명 또는 주소 검색", "", placeholder="검색할 충전소명 또는 주소를 입력하세요")

    # ==============================================================================
    # 필터 적용 데이터 계산
    # ==============================================================================
    filtered = df_station.copy()

    if selected_regions:
        filtered = filtered[filtered["권역"].isin(selected_regions)]
    if selected_types:
        filtered = filtered[filtered["충전소구분"].isin(selected_types)]
    if min_kw > 0:
        filtered = filtered[filtered["최대출력(kW)"] >= min_kw]
    if selected_connectors:
        pattern = "|".join(selected_connectors)
        filtered = filtered[filtered["지원사양"].str.contains(pattern, na=False, regex=True)]
    if search_kw.strip():
        kw = search_kw.strip()
        search_mask = (
            filtered["statNm"].astype(str).str.contains(kw, case=False, na=False) |
            filtered["addr"].astype(str).str.contains(kw, case=False, na=False)
        )
        filtered = filtered[search_mask]

    # ==============================================================================
    # [상단 렌더링] tab3_image1: 공간 지도 및 인터페이스 출력
    # ==============================================================================
    with map_container:
        region_title = " & ".join(selected_regions) if selected_regions else "전국"
        st.subheader(f"🗺️ {region_title} 전기차 및 충전소 공간 지도")
        st.caption("원 크기: 거점별 충전기 수 / 마커 색상: 충전소 구분(완속 전용, 급속 전용, 급속/완속 동시)")

        r_col, _ = st.columns([3, 1])
        with r_col:
            st.radio(
                "지도 종류",
                ["🔴 개별 충전소 위치 지도", "🟠 지역별 전기차 vs 충전기 버블 지도"],
                horizontal=True,
                label_visibility="collapsed"
            )

        st.markdown("##### 충전소 유형 및 충전기 수별 위치 분포")

        if not filtered.empty:
            center_lat = filtered["lat"].mean()
            center_lon = filtered["lng"].mean()

            color_map = {
                "완속 전용": "#0075FF",
                "급속/완속 동시": "#00E676",
                "급속 전용": "#FF1744",
                "기타": "#718096"
            }

            map_kwargs = dict(
                lat="lat",
                lon="lng",
                color="충전소구분",
                color_discrete_map=color_map,
                size="충전기수",
                size_max=18,
                opacity=0.9,
                hover_name="statNm",
                hover_data={
                    "addr": True, "권역": True, "충전기수": True,
                    "최대출력(kW)": True, "지원사양": True, "lat": False, "lng": False
                },
                zoom=10 if len(selected_regions) <= 1 else 7,
                center={"lat": center_lat, "lon": center_lon},
                height=600
            )

            if hasattr(px, "scatter_map"):
                fig = px.scatter_map(filtered, map_style="carto-positron", **map_kwargs)
            else:
                fig = px.scatter_mapbox(filtered, mapbox_style="carto-positron", **map_kwargs)

            fig.update_layout(
                margin={"r": 0, "t": 10, "l": 0, "b": 0},
                legend=dict(
                    title_text="충전소구분",
                    orientation="v", yanchor="top", y=0.98, xanchor="right", x=0.99,
                    bgcolor="rgba(255, 255, 255, 0.9)", bordercolor="#cbd5e1", borderwidth=1
                )
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("선택하신 필터 조건에 일치하는 충전소 데이터가 없습니다.")

    # ==============================================================================
    # [하단 렌더링] tab3_image2: 통계 지표(Metrics) & 상세 데이터 목록
    # ==============================================================================
    st.markdown("---")
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("조회된 충전소 수", f"{len(filtered):,} 개소")
    kpi2.metric("총 충전기 대수", f"{int(filtered['충전기수'].sum()) if not filtered.empty else 0:,} 대")
    kpi3.metric("선택된 권역 수", f"{len(selected_regions)} 개")

    with st.expander("📋 충전소 상세 데이터 목록 확인"):
        if not filtered.empty:
            show_cols = ["statNm", "권역", "충전소구분", "충전기수", "최대출력(kW)", "지원사양", "addr"]
            valid_show_cols = [c for c in show_cols if c in filtered.columns]
            renamed_df = filtered[valid_show_cols].rename(
                columns={"statNm": "충전소명", "addr": "주소"}
            )
            st.dataframe(renamed_df, use_container_width=True)
        else:
            st.write("표시할 충전소 데이터가 없습니다.")