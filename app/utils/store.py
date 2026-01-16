### 구현 완료
import pandas as pd
import plotly.graph_objects as go


def showstore(store_df: pd.DataFrame) -> go.Figure:
    """
    현대차 대리점/전시장 지도 Plotly Figure 생성 함수
    - 시도 드롭다운 필터
    - 유형별 색상 분리
    - hover 정보 카드형
    """

    # =========================
    # 1) 설정값 / 매핑
    # =========================
    SIDO_MAP = {
        "01": "서울특별시",
        "06": "인천광역시",
        "07": "경기도",
        "02": "강원특별자치도",
        "05": "충청남도",
        "03": "대전광역시",
        "04": "충청북도",
        "15": "대구광역시",
        "16": "경상북도",
        "11": "부산광역시",
        "13": "경상남도",
        "12": "울산광역시",
        "18": "전북특별자치도",
        "10": "전라남도",
        "08": "광주광역시",
        "14": "제주특별자치도",
    }

    TYPE_COLOR = {
        "지점/전시장": "#e63946",
        "대리점": "#457b9d",
    }

    HOVER_TEMPLATE = (
        "<b>%{text}</b><br>"
        "유형: %{customdata[0]}<br>"
        "거리: %{customdata[1]:.1f} km<br>"
        "전시장 차량: %{customdata[2]}대<br>"
        "보유 차량: %{customdata[3]}대<br>"
        "<br>"
        "주소: %{customdata[4]}<br>"
        "전화: %{customdata[5]}"
        "<extra></extra>"
    )

    # =========================
    # 2) 데이터 전처리
    # =========================
    dff = store_df.copy()

    dff["lat"] = pd.to_numeric(dff["lat"], errors="coerce")
    dff["lon"] = pd.to_numeric(dff["lon"], errors="coerce")
    dff["distance_km"] = pd.to_numeric(dff["distance_km"], errors="coerce")

    dff = dff.dropna(subset=["lat", "lon"])
    dff["sido_name"] = dff["sido_code"].map(SIDO_MAP).fillna(dff["sido_code"])

    SIDO_COL = "sido_name"
    SIDO_LIST = sorted(dff[SIDO_COL].unique())

    # =========================
    # 3) trace 추가 함수
    # =========================
    def add_type_traces(fig, data, name_prefix, visible):
        for agency_type, color in TYPE_COLOR.items():
            sub = data[data["agencyType"] == agency_type]
            fig.add_trace(
                go.Scattermapbox(
                    lat=sub["lat"],
                    lon=sub["lon"],
                    mode="markers",
                    marker=dict(size=9, color=color, opacity=0.85),
                    text=sub["agencyName"],
                    customdata=sub[
                        [
                            "agencyType",
                            "distance_km",
                            "displayCarCount",
                            "carMasterCount",
                            "agencyAddress",
                            "agencyTel",
                        ]
                    ].values,
                    hovertemplate=HOVER_TEMPLATE,
                    name=f"{name_prefix}{agency_type}",
                    visible=visible,
                )
            )

    # =========================
    # 4) Figure 구성
    # =========================
    fig = go.Figure()

    # 전체
    add_type_traces(fig, dff, name_prefix="전체 - ", visible=True)

    # 시도별
    start_idx = len(fig.data)
    for s in SIDO_LIST:
        sub_s = dff[dff[SIDO_COL] == s]
        add_type_traces(fig, sub_s, name_prefix=f"{s} - ", visible=False)

    # =========================
    # 5) 드롭다운 버튼
    # =========================
    buttons = []

    # 전체 버튼
    vis_all = [False] * len(fig.data)
    vis_all[0] = True
    vis_all[1] = True
    buttons.append(dict(label="전체", method="update", args=[{"visible": vis_all}]))

    # 시도 버튼
    for i, s in enumerate(SIDO_LIST):
        vis = [False] * len(fig.data)
        base = start_idx + i * 2
        vis[base] = True
        vis[base + 1] = True
        buttons.append(dict(label=s, method="update", args=[{"visible": vis}]))

    # =========================
    # 6) 레이아웃
    # =========================
    fig.update_layout(
        title="현대차 대리점/전시장 지도",
        width=1600,
        height=550,
        margin=dict(l=10, r=10, t=60, b=10),
        mapbox=dict(
            style="open-street-map",
            zoom=7,
            center=dict(
                lat=float(dff["lat"].mean()),
                lon=float(dff["lon"].mean()),
            ),
        ),
        updatemenus=[dict(
            type="dropdown",
            x=0.01, y=0.99,
            xanchor="left", yanchor="top",
            buttons=buttons
        )],
        legend=dict(
            orientation="h",
            y=1.02,
            x=1,
            xanchor="right",
            yanchor="bottom"
        ),
        hoverlabel=dict(
            bgcolor="white",
            bordercolor="#D0D0D0",
            font=dict(
                family="Pretendard, Apple SD Gothic Neo, Malgun Gothic",
                size=14,
                color="black",
            ),
            align="left",
        ),
    )

    return fig
