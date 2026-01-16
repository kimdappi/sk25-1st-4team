import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components

from visualization.visual import filter_data, draw_chart
from utils.faq import showgenesisfaq, showhyundaifaq, showkiafaq
from utils.store import showstore
from visualization.gen_age import draw_gender_age_chart


st.set_page_config(page_title="Car Pick", layout="wide")

###============================== 데이터 호출 ==============================##
df = pd.read_pickle("../data/자동차등록.pkl")
df_long = df

store_df=pd.read_pickle("../data/hyundai_store.pkl")
genderage_df=pd.read_pickle("../data/성별_연령별_데이터_통합.pkl")

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

        /* ✅ 화면 중앙보다 살짝 위로 */
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

    /* ✅ 버튼을 intro 안에서 예쁘게 */
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

# ---- 메뉴 버튼들 ----
if st.sidebar.button("1. 시도 별 추이", use_container_width=True):
    st.session_state.page = "sido_trend"
    set_qp({"page": "sido_trend"})
    st.rerun()

if st.sidebar.button("2. 지역 별 추이", use_container_width=True):
    st.session_state.page = "region_trend"
    set_qp({"page": "region_trend"})
    st.rerun()

if st.sidebar.button("3. 성별 연령 추이", use_container_width=True):
    st.session_state.page = "gender_age_trend"
    set_qp({"page": "gender_age_trend"})
    st.rerun()

if st.sidebar.button("4. 필터식 추천", use_container_width=True):
    st.session_state.page = "recommend"
    set_qp({"page": "recommend"})
    st.rerun()

if st.sidebar.button("5. FAQ", use_container_width=True):
    st.session_state.page = "faq"
    set_qp({"page": "faq"})
    st.rerun()


if st.sidebar.button("5. 대리점 정보", use_container_width=True):
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

if page == "sido_trend":
    st.title("시도 별 추이")
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

    dff = filter_data(df_long, sido, sigungu, car, gubun)
    fig = draw_chart(dff, sido, sigungu, car, gubun, chart_type)
    
    st.plotly_chart(
        fig,
        use_container_width=True,
        config={"scrollZoom": True, "displayModeBar": True},
        key=f"main_chart_{sido}_{sigungu}_{car}_{gubun}_{chart_type}"
    )
    
    st.divider()

elif page == "region_trend":
    st.title("2) 지역 별 추이")
    st.info("여기에 2번 화면 코드 넣으면 됨")

elif page == "gender_age_trend":
    st.set_page_config(layout="wide")
    st.title("3) 성별 연령 추이")
    draw_gender_age_chart(genderage_df)



elif page == "recommend":
    st.title("4) 필터식 추천")

    # 세션 기본값(선택 유지)
    if "rec_gender" not in st.session_state:
        st.session_state.rec_gender = "전체"
    if "rec_age" not in st.session_state:
        st.session_state.rec_age = "20대"
    if "rec_kind" not in st.session_state:
        st.session_state.rec_kind = "승용"

    # 상단 한 줄 드랍다운 바
    with st.container():
        c1, c2, c3 = st.columns(3)

        gender = c1.selectbox(
            "성별",
            ["전체", "남", "여"],
            index=["전체", "남", "여"].index(st.session_state.rec_gender),
            key="rec_gender_select",
        )

        age = c2.selectbox(
            "연령",
            ["20대", "30대", "40대", "50대", "60대", "70대", "80대"],
            index=["20대", "30대", "40대", "50대", "60대", "70대", "80대"].index(st.session_state.rec_age),
            key="rec_age_select",
        )

        kind = c3.selectbox(
            "차종",
            ["승용", "승합"],
            index=["승용", "승합"].index(st.session_state.rec_kind),
            key="rec_kind_select",
        )

    # 선택값을 세션에 반영
    st.session_state.rec_gender = gender
    st.session_state.rec_age = age
    st.session_state.rec_kind = kind

    st.divider()

    #  현재 선택값
    st.subheader("선택된 조건")
    st.write({
        "성별": st.session_state.rec_gender,
        "연령": st.session_state.rec_age,
        "차종": st.session_state.rec_kind,
    })

    # 여기서 추천 로직 연결
    # gender = st.session_state.rec_gender
    # age = st.session_state.rec_age
    # kind = st.session_state.rec_kind
    #
    # reco_df = recommend_fn(df_long, gender, age, kind)
    # st.dataframe(reco_df)


elif page == "faq":
    st.title("5) FAQ")

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




elif page == "carstore": #구현 완료
    st.title("5) 대리점 정보")

    st.set_page_config(layout="wide")

    fig = showstore(store_df)
    st.plotly_chart(fig, use_container_width=True)

elif page == "intro":
    st.title("Intro")
    st.info("처음 화면 내용")

else:
    st.title("대시보드")
    st.info("왼쪽에서 메뉴를 선택하세요")
