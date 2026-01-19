import pandas as pd
import plotly.graph_objects as go
import os
import pickle

# =========================
# 데이터 로드
# =========================
def load_store_data():
    file_path = "../data/hyundai_kia_genesis_agency.pkl"
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            df = pickle.load(f)
        return df if isinstance(df, pd.DataFrame) else pd.DataFrame(df)
    return pd.DataFrame()


# =========================
# 공통 지도 생성 함수
# =========================
def showstore_all(store_df: pd.DataFrame, type_color: dict, title: str) -> go.Figure:

    if store_df.empty:
        fig = go.Figure()
        fig.update_layout(title="표시할 데이터가 없습니다.")
        return fig

    # =========================
    # 1. 시도 정규화 맵
    # =========================
    SIDO_MAP = {
        "서울": ["서울특별시", "서울시", "서울"],
        "경기": ["경기도", "경기"],
        "인천": ["인천광역시"],
        "부산": ["부산광역시"],
        "대구": ["대구광역시"],
        "광주": ["광주광역시"],
        "대전": ["대전광역시", "대전시"],
        "울산": ["울산광역시"],
        "세종": ["세종특별자치시"],

        "강원": ["강원특별자치도", "강원도"],
        "충북": ["충청북도"],
        "충남": ["충청남도"],
        "전북": ["전북특별자치도", "전라북도", "전라북도특별자치도"],
        "전남": ["전라남도"],
        "경북": ["경상북도"],
        "경남": ["경상남도"],
        "제주": ["제주특별자치도", "제주시"],
    }

    REVERSE_SIDO_MAP = {
        v: k
        for k, values in SIDO_MAP.items()
        for v in values
    }

    # =========================
    # 2. 데이터 전처리
    # =========================
    dff = store_df.copy()

    dff["lat"] = pd.to_numeric(dff["latitude"], errors="coerce")
    dff["lon"] = pd.to_numeric(dff["longitude"], errors="coerce")
    dff = dff.dropna(subset=["lat", "lon"])

    dff["showroom_label"] = dff["is_showroom"].map({
        True: "있음",
        False: "없음"
    })

    dff["sido_raw"] = dff["agency_address"].apply(
        lambda x: x.split()[0] if isinstance(x, str) else None
    )
    dff["sido_name"] = dff["sido_raw"].map(REVERSE_SIDO_MAP).fillna("기타")

    sido_list = sorted(dff["sido_name"].unique())

    # =========================
    # 3. Hover 템플릿
    # =========================
    hover_template = (
        "<b>%{text}</b><br>"
        "유형 : %{customdata[1]}<br>"
        "전시 여부 : %{customdata[2]}<br><br>"
        "주소 : %{customdata[3]}<br>"
        "전화 : %{customdata[4]}"
        "<extra></extra>"
    )

    fig = go.Figure()

    # =========================
    # 4. 범례 고정용 더미 트레이스 (추가)
    # =========================
    # 지역 선택과 상관없이 범례 버튼이 항상 떠 있게 합니다.
    for a_type, color in type_color.items():
        fig.add_trace(go.Scattermapbox(
            lat=[None], lon=[None],
            mode="markers",
            marker=dict(size=11, color=color),
            name=a_type,
            legendgroup=a_type,
            showlegend=True,
            visible=True  # 항상 켜져 있음
        ))

    # =========================
    # 5. 데이터 포인트 추가 함수
    # =========================
    def add_traces(target_df, name_prefix="", is_visible=True):
        for a_type, color in type_color.items():
            sub = target_df[target_df["agency_type"] == a_type]
            if sub.empty:
                continue

            fig.add_trace(go.Scattermapbox(
                lat=sub["lat"],
                lon=sub["lon"],
                mode="markers",
                marker=dict(size=11, color=color, opacity=0.8),
                text=sub["agency_name"],
                customdata=sub[
                    ["agency_name", "agency_type", "showroom_label",
                     "agency_address", "agency_tel"]
                ].values,
                hovertemplate=hover_template,
                name=a_type,
                legendgroup=a_type,
                showlegend=False,
                visible=is_visible
            ))

    # =========================
    # 6. 전체 데이터 및 시도별 데이터
    # =========================
    dummy_count = len(type_color)
    
    add_traces(dff, is_visible=True) # 전체

    start_idx = len(fig.data)
    for sido in sido_list:
        sub_sido = dff[dff["sido_name"] == sido]
        add_traces(sub_sido, name_prefix=sido, is_visible=False)

    # =========================
    # 7. 드롭다운 버튼
    # =========================
    buttons = []

    # 전체
    vis_all = [True] * dummy_count + [False] * (len(fig.data) - dummy_count)
    for i in range(dummy_count, dummy_count + len(type_color)):
        if i < len(vis_all):
            vis_all[i] = True
            
    buttons.append(dict(
        label="전체 지역",
        method="update",
        args=[{"visible": vis_all}]
    ))

    # 시도별
    for i, sido in enumerate(sido_list):
        vis = [True] * dummy_count + [False] * (len(fig.data) - dummy_count)
        base = start_idx + (i * len(type_color))
        for j in range(len(type_color)):
            if base + j < len(vis):
                vis[base + j] = True

        buttons.append(dict(
            label=sido,
            method="update",
            args=[{"visible": vis}]
        ))

    # =========================
    # 8. 레이아웃
    # =========================
    fig.update_layout(
        title=dict(text=f"<b>{title}</b>", font=dict(size=24, color="#1E293B")),
        mapbox=dict(
            style="open-street-map", zoom=6.5,
            center=dict(lat=dff["lat"].mean(), lon=dff["lon"].mean())
        ),
        updatemenus=[dict(
            buttons=buttons, direction="down", showactive=True,
            x=0.01, y=0.98, xanchor="left", yanchor="top",
            bgcolor="white", bordercolor="#CBD5E1", borderwidth=1
        )],
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="right", x=1,
            font=dict(size=15, color="#334155"),
        ),
        margin=dict(l=0, r=0, t=90, b=0),
        height=750
    )

    return fig


# 브랜드별 호출 함수
def showhyundai_store():
    df = load_store_data()
    target = df[df["company_name"] == "hyundai"]
    colors = {"지점/전시장": "#e63946", "대리점": "#457b9d"}
    return showstore_all(target, colors, "현대자동차 매장 분포")

def showkia_store():
    df = load_store_data()
    target = df[df["company_name"] == "kia"]
    colors = {"지점": "#e63946", "대리점": "#457b9d", "플래그십 스토어": "#2ecc71", "Kia360": "#f1c40f"}
    return showstore_all(target, colors, "기아 매장 분포")

def showgenesis_store():
    df = load_store_data()
    target = df[df["company_name"] == "genesis"]
    colors = {"지점": "#e63946", "대리점": "#457b9d"}
    return showstore_all(target, colors, "제네시스 매장 분포")