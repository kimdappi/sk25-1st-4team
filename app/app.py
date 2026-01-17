import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components
from streamlit_folium import st_folium


from visualization.gen_age import draw_gender_age_chart
from visualization.visual import filter_car_regis_data,draw_car_regis_chart
from visualization.visual import draw_gugun_folium_map, draw_sido_folium_map 

from utils.faq import showgenesisfaq, showhyundaifaq, showkiafaq
from utils.store import showhyundai_store, showkia_store, showgenesis_store


st.set_page_config(page_title="Car Pick", layout="wide")

###============================== 데이터 호출 ==============================##
df = pd.read_pickle("../data/자동차등록.pkl")
df_long = df

store_df=pd.read_pickle("../data/hyundai_store.pkl")
genderage_df=pd.read_pickle("../data/성별_연령별_데이터_통합.pkl")
GUGUN_PKL_PATH="../data/군_승합_승용.pkl"
recommend_df=pd.read_pickle("../data/final_filter_data.pkl")

sidocar_2022 = pd.read_pickle('../data/sido_category/sidocar_2022.pkl')
sidocar_2023 = pd.read_pickle('../data/sido_category/sidocar_2023.pkl')
sidocar_2024 = pd.read_pickle('../data/sido_category/sidocar_2024.pkl')
sidovan_2022 = pd.read_pickle('../data/sido_category/sidovan_2022.pkl')
sidovan_2023 = pd.read_pickle('../data/sido_category/sidovan_2023.pkl')
sidovan_2024 = pd.read_pickle('../data/sido_category/sidovan_2024.pkl')

##============================== 지도 캐시 처리 ==============================##

@st.cache_data(show_spinner=False)
def cached_read_pickle(path: str) -> pd.DataFrame:
    return pd.read_pickle(path)

@st.cache_data(show_spinner=False)
def cached_draw_gugun_map(pkl_path: str, year: int, vehicle_type: str):
    """
    외부 함수 draw_gugun_folium_map 호출
    """
    # draw_gugun_folium_map 내부에서 pd.read_pickle을 다시 하니까
    # 캐시 이득을 더 보려면 외부 함수도 full_df를 인자로 받게 리팩토링이 베스트지만,
    # "외부 함수 그대로" 조건이라 여기서는 호출 캐시만 적용
    return draw_gugun_folium_map(pkl_path=pkl_path, year=year, vehicle_type=vehicle_type)

@st.cache_data(show_spinner=False)
def cached_draw_sido_map(year: int, kind: str, sido_df: pd.DataFrame):
    """
    외부 함수 draw_sido_folium_map 호출
    """
    return draw_sido_folium_map(sido_df=sido_df, year=year, kind=kind)


##============================== URL query param으로 페이지 전환 ==============================##
# Streamlit 버전에 따라 query_params API가 다를 수 있어서 둘 다 대응
def get_qp(name: str):
    try:
        return st.query_params.get(name, None)  # 최신 streamlit
    except Exception:
        return st.experimental_get_query_params().get(name, [None])[0]  # 구버전

def set_qp(params: dict):
    try:
        # 최신 streamlit
        st.query_params.update(params)
    except Exception:
        # 구버전
        st.experimental_set_query_params(**params)

# query param이 dashboard면 intro를 건너뛰고 바로 이동
qp_page = get_qp("page")
if qp_page == "dashboard":
    st.session_state.page = "dashboard"

###============================== 페이지 상태 ==============================##
if "page" not in st.session_state:
    st.session_state.page = "intro"

###============================== 공통 CSS (상단바/푸터) ==============================##
st.markdown("""
<style>
/* 상단 컬러바 */
body::before{
    content:"";
    position:fixed;
    top:0;
    left:0;
    width:100%;
    height:50px;
    background:#2E86C1;
    z-index:999999;
}

/* 하단 footer */
.footer{
    position:fixed;
    left:0;
    bottom:0;
    width:100%;
    background-color:#F2F2F2;
    color:#666;
    text-align:center;
    padding:12px 0;
    font-size:12px;
    border-top:1px solid #ddd;
    z-index:999999;
}

/* footer에 본문이 가리지 않게 여백 */
section.main{
    padding-bottom:60px;
}
</style>
""", unsafe_allow_html=True)

###============================== INTRO 화면 ==============================##
if st.session_state.page == "intro":
    st.markdown("""
    <style>
    .intro-wrap{
        height:40vh;
        display:flex;
        flex-direction:column;
        justify-content:flex-start;
        align-items:center;
        text-align:center;

        /* 화면 중앙보다 살짝 위로 */
        padding-top: 160px;        /* ← 여기 숫자만 조절하면 됨 */
    }

    .intro-title{
        font-size:42px;
        font-weight:800;
        margin-bottom:16px;
    }
    .intro-desc{
        font-size:16px;
        color:#666;
        margin-bottom:22px;
        line-height:1.6;
    }

    /* 버튼을 intro 안에서 예쁘게 */
    .start-btn-wrap{
        width: 70px;
        margin-top: -200px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="intro-wrap">
        <div class="intro-title">🚗 Car Pick 🚗</div>
        <div class="intro-desc">
            당신의 자동차 구매를 돕습니다.
        </div>
    </div>
    """, unsafe_allow_html=True)


    st.markdown("<div class='start-btn-wrap'>", unsafe_allow_html=True)
    if st.button("대시보드 시작하기 ▶", key="start_top", use_container_width=True):
        st.session_state.page = "dashboard"
        set_qp({"page": "dashboard"})
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("""
    <div class="footer">
        © SK Networks Family Artificial Intelligence Camp 25
    </div>
    """, unsafe_allow_html=True)

    st.stop()


###============================== DASHBOARD 화면 ==============================##


# page 기본값
if "page" not in st.session_state:
    st.session_state.page = "dashboard"

st.sidebar.title("옵션 선택")

# ---- 메뉴 버튼들 ----c 
if st.sidebar.button("시간 흐름 별 추이", use_container_width=True):
    st.session_state.page = "sido_trend"
    set_qp({"page": "sido_trend"})
    st.rerun()

if st.sidebar.button("지역 별 추이", use_container_width=True):
    st.session_state.page = "region_trend"
    set_qp({"page": "region_trend"})
    st.rerun()

if st.sidebar.button("성별 연령 추이", use_container_width=True):
    st.session_state.page = "gender_age_trend"
    set_qp({"page": "gender_age_trend"})
    st.rerun()

if st.sidebar.button("필터식 추천", use_container_width=True):
    st.session_state.page = "recommend"
    set_qp({"page": "recommend"})
    st.rerun()

if st.sidebar.button("FAQ", use_container_width=True):
    st.session_state.page = "faq"
    set_qp({"page": "faq"})
    st.rerun()


if st.sidebar.button("지점 정보", use_container_width=True):
    st.session_state.page = "carstore"
    set_qp({"page": "carstore"})
    st.rerun()
st.sidebar.divider()

# intro로 돌아가기
if st.sidebar.button("◀ 처음 화면으로", use_container_width=True):
    st.session_state.page = "intro"
    set_qp({"page": "intro"})
    st.rerun()



# ============================== 페이지별 렌더링 ==============================

page = st.session_state.page
###==============================[ 사이드 바 ] 시간 별 추이 출력  ==============================##

if page == "sido_trend":
    st.title("시간 흐름 별 추이")
    col1, col2, col3, col4, col5 = st.columns([1.2, 1.2, 1, 1, 1])

    sido = col1.selectbox("시도명", sorted(df_long["시도명"].unique()), key="sido")
    sigungu = col2.selectbox(
        "시군구",
        sorted(df_long.loc[df_long["시도명"] == sido, "시군구"].unique()),
        key="sigungu",
    )
    car = col3.selectbox("차종", sorted(df_long["차종"].unique()), key="car")
    gubun = col4.selectbox("구분", sorted(df_long["구분"].unique()), key="gubun")
    chart_type = col5.selectbox("차트", ["Line", "Bar"], key="chart_type")

    dff = filter_car_regis_data(df_long, sido, sigungu, car, gubun)
    fig = draw_car_regis_chart(dff, sido, sigungu, car, gubun, chart_type)
    
    st.plotly_chart(
        fig,
        use_container_width=True,
        config={"scrollZoom": True, "displayModeBar": True},
        key=f"main_chart_{sido}_{sigungu}_{car}_{gubun}_{chart_type}"
    )
    st.divider()


###==============================[ 사이드 바 ] 지역 별 추이 출력  ==============================##

elif page == "region_trend":
    st.title("지역 별 추이")

    years = [2022, 2023, 2024]
    kind_labels = {"car": "승용(car)", "van": "승합(van)"}

    # ✅ 너 app_2.py에 있는 변수명 그대로 매핑
    car_dfs_by_year = {2022: sidocar_2022, 2023: sidocar_2023, 2024: sidocar_2024}
    van_dfs_by_year = {2022: sidovan_2022, 2023: sidovan_2023, 2024: sidovan_2024}

    tab1, tab2 = st.tabs(["시도별 지도", "구 단위 지도"])

    # -------------------------
    # 1) 시도별 지도 (draw_sido_folium_map)
    # -------------------------
    with tab1:
        c1, c2 = st.columns([1, 1])
        year = c1.selectbox("연도", years, index=len(years)-1, key="sido_year")
        kind = c2.selectbox("차종", ["car", "van"], format_func=lambda x: kind_labels[x], key="sido_kind")

        sido_df = car_dfs_by_year[year] if kind == "car" else van_dfs_by_year[year]

        m = draw_sido_folium_map(sido_df=sido_df, year=year, kind=kind)
        st_folium(m, width="100%", height=650)

    # -------------------------
    # 2) 구 단위 지도 (draw_gugun_folium_map)
    # -------------------------
    with tab2:
        c1, c2 = st.columns([1, 1])
        year = c1.selectbox("연도", years, index=len(years)-1, key="gugun_year")
        vehicle_type = c2.selectbox("차종", ["car", "van"], format_func=lambda x: kind_labels[x], key="gugun_kind")

        m = draw_gugun_folium_map(pkl_path=GUGUN_PKL_PATH, year=year, vehicle_type=vehicle_type)
        st_folium(m, width="100%", height=750)


###==============================[ 사이드 바 ] 성별 연령 추이 출력  ==============================##

elif page == "gender_age_trend":
    st.set_page_config(layout="wide")
    st.title("성별 연령 추이")
    draw_gender_age_chart(genderage_df)

###==============================[ 사이드 바 ]  필더식 추천 출력  ==============================##


elif page == "recommend":
    st.title("필터식 추천")
    c1, c2, c3 = st.columns(3)
    with c1:
        gender = st.selectbox("성별", ["전체", "남성", "여성"])
    with c2:
        age_range = st.selectbox("연령", ["20대", "30대", "40대", "50대", "60대", "70대", "80대"])
    with c3:
        car_type = st.selectbox("차종", ["승용", "승합"])

    # 💡 "선택된 조건" JSON 부분 삭제함
    st.markdown("---")

    # 3. 결과 출력 (가로 3개 배치)
    mask = (recommend_df['연령대'] == age_range) & (recommend_df['차종'] == car_type)
    results = recommend_df[mask].sort_values('순위')

    if not results.empty:
        st.subheader(f"✨ {age_range} {car_type} 추천 리스트")
        cols = st.columns(3)
        for i, (_, row) in enumerate(results.iterrows()):
            with cols[i]:
                # 깔끔한 카드 스타일
                st.success(f"### {row['순위']}위")
                st.write(f"**{row['제조사']} {row['모델명']}**")
                st.metric("가격", f"약 {row['가격']}만원")
                st.info(f"선호 점유율: {row['점유율']}")
    else:
        st.warning("추천 데이터를 구성 중입니다.")

###==============================[ 사이드 바 ]  FAQ 출력  ==============================##

elif page == "faq":
    st.title("FAQ")

    # 0) 기본 선택값
    if "faq_brand" not in st.session_state:
        st.session_state.faq_brand = "hyundai"  # hyundai / kia / genesis

    st.subheader("브랜드 선택")

    # 1) 브랜드 선택 버튼 (메인 화면)
    c1, c2, c3 = st.columns(3)

    def brand_button(col, key, label):
        is_selected = (st.session_state.faq_brand == key)
        btn_label = f"{'▶ ' if is_selected else ''}{label}"

        with col:
            if st.button(btn_label, use_container_width=True, key=f"faq_{key}"):
                st.session_state.faq_brand = key
                st.rerun()

    brand_button(c1, "hyundai", "현대")
    brand_button(c2, "kia", "기아")
    brand_button(c3, "genesis", "제네시스")

    st.divider()

    # 2) 선택된 브랜드에 맞게 FAQ 출력
    if st.session_state.faq_brand == "hyundai":
        st.subheader("현대 FAQ")
        showhyundaifaq()

    elif st.session_state.faq_brand == "kia":
        st.subheader("기아 FAQ")
        showkiafaq()

    elif st.session_state.faq_brand == "genesis":
        st.subheader("제네시스 FAQ")
        showgenesisfaq()


###==============================[ 사이드 바 ]  지점 정보 출력  ==============================##
elif page == "carstore": 
    st.title("지점 정보")


    # ----------------------------
    # 0) 브랜드 전용 세션 변수
    # ----------------------------
    if "store_brand" not in st.session_state:
        st.session_state.store_brand = "hyundai"

    st.subheader("브랜드 선택")
    c1, c2, c3 = st.columns(3)

    # ----------------------------
    # 선택된 브랜드 앞에 ▶ 표시를 붙여 시각적 효과 부여하는 함수
    # ----------------------------
    def brand_button(col, key, label):
        is_selected = (st.session_state.store_brand == key)
        btn_label = f"{'▶ ' if is_selected else ''}{label}"
        with col:
            if st.button(btn_label, use_container_width=True, key=f"store_btn_{key}"):
                st.session_state.store_brand = key
                st.rerun()

    brand_button(c1, "hyundai", "현대")
    brand_button(c2, "kia", "기아")
    brand_button(c3, "genesis", "제네시스")

    st.divider()


    # ----------------------------
    # 1) 선택 브랜드에 따른 지도 생성 및 출력
    # ----------------------------
    brand = st.session_state.store_brand

    # utils/store.py에 정의된 브랜드별 전용 함수를 호출합니다.
    # 이 함수들은 내부에서 데이터를 필터링하고 색상을 입혀 Figure를 반환합니다.
    with st.spinner(f"{brand.upper()} 대리점 정보를 불러오는 중..."):
        if brand == "hyundai":
            fig = showhyundai_store()
        elif brand == "kia":
            fig = showkia_store()
        elif brand == "genesis":
            fig = showgenesis_store()

        # 생성된 Plotly 객체 출력
        st.plotly_chart(fig, use_container_width=True)


###============================== 특정 대시보드 외 페이지 처리 ==============================##
elif page == "intro":
    st.title("Intro")
    st.info("처음 화면 내용")

else:
    st.title("대시보드")
    st.info("왼쪽에서 메뉴를 선택하세요")
