import plotly.express as px
import pandas as pd
import folium
import requests

GEO_URL_PROVINCES = "https://raw.githubusercontent.com/southkorea/southkorea-maps/master/kostat/2018/json/skorea-provinces-2018-geo.json"
GEO_URL_MUNI = "https://raw.githubusercontent.com/southkorea/southkorea-maps/master/kostat/2018/json/skorea-municipalities-2018-geo.json"

geo_muni = requests.get(GEO_URL_MUNI).json()
geo_prov = requests.get(GEO_URL_PROVINCES).json()

MUNI_NAMES = [f["properties"]["name"] for f in geo_muni["features"]]
PROV_NAMES = [f["properties"]["name"] for f in geo_prov["features"]]

# -------------------------
# 시간 흐름별 추이 구현 함수
# -------------------------

def filter_car_regis_data(df, sido, sigungu, car, gubun):
    """
    필터링 함수
    """
    dff = df[
        (df["시도명"] == sido) &
        (df["시군구"] == sigungu) &
        (df["차종"] == car) &
        (df["구분"] == gubun)
    ].sort_values("date")

    return dff


def draw_car_regis_chart(dff, sido, sigungu, car, gubun, chart_type):
    """
    차트 생성 함수
    """
    title = f"{sido} {sigungu} | {car} - {gubun} (월별)"

    if chart_type == "Line":
        fig = px.line(
            dff,
            x="date",
            y="대수",
            markers=True,
            title=title
        )
    else:
        fig = px.bar(
            dff,
            x="date",
            y="대수",
            title=title
        )

    fig.update_layout(
        hovermode="x unified",
        xaxis_title="월",
        yaxis_title="등록 대수"
    )

    return fig

# -------------------------
# 지역 별 추이(군구) 구현 함수
# -------------------------

def draw_gugun_folium_map(full_df: pd.DataFrame, year: int, vehicle_type: str):
    category = "승용차" if vehicle_type == "car" else "승합차"

    df = full_df[
        (full_df["reg_year"] == year) &
        (full_df["vehicle_type"] == vehicle_type)
    ]

    df_sum = df.groupby("sigungu_name", as_index=False)["car_count"].sum()

    # GeoJSON의 name 기준 테이블 만들고 merge (O(N))
    base = pd.DataFrame({"name": MUNI_NAMES})
    df_final = base.merge(df_sum, left_on="name", right_on="sigungu_name", how="left")
    df_final["car_count"] = df_final["car_count"].fillna(0).astype(int)

    # 보정값 반영
    if vehicle_type == "car":
        df_final.loc[df_final["name"] == "계룡시", "car_count"] = 18600
        df_final.loc[df_final["name"] == "계양구", "car_count"] = 110000
    else:
        df_final.loc[df_final["name"] == "계룡시", "car_count"] = 750
        df_final.loc[df_final["name"] == "계양구", "car_count"] = 4500

    df_final["display_val"] = df_final["car_count"] / 1000

    # bins: quantile은 나쁘지 않지만, 매번 계산 싫으면 고정 bins 추천
    series = df_final["display_val"]
    bins = series.quantile([0, 0.1, 0.3, 0.5, 0.7, 0.85, 0.95, 1]).unique().tolist()
    if len(bins) < 3:
        bins = 6

    m = folium.Map(location=[36.5, 127.5], zoom_start=7)

    ch = folium.Choropleth(
        geo_data=geo_muni,  # requests 재호출 없음
        data=df_final,
        columns=["name", "display_val"],
        key_on="feature.properties.name",
        fill_color="YlOrRd",
        fill_opacity=0.6,
        line_color="black",
        line_weight=0.3,
        line_opacity=1,
        bins=bins,
        legend_name=f"{year}년 {category} 등록수 (천 대)"
    ).add_to(m)

    # tooltip도 dict 한번만 만들기
    value_map = df_final.set_index("name")["car_count"].to_dict()
    for feat in ch.geojson.data["features"]:
        nm = feat["properties"]["name"]
        feat["properties"]["tooltip_text"] = f"{nm}: {value_map.get(nm, 0):,} 대"

    ch.geojson.add_child(
        folium.GeoJsonTooltip(fields=["tooltip_text"], aliases=["🚗 현황:"], labels=False)
    )

    return m


# -------------------------
# 지역 별 추이(시도) 구현 함수
# -------------------------
def draw_sido_folium_map(sido_df, year: int, kind: str = "car"):
    m = folium.Map(location=[36.5, 127.8], zoom_start=7)
    value_col = f"{year}.12 월"

    # (기존 custom_bins/legend_html 로직은 그대로 두되) geo_prov 재사용
    # Choropleth
    cp = folium.Choropleth(
        geo_data=geo_prov,   
        data=sido_df,
        columns=["시도명", value_col],
        key_on="feature.properties.name",
        fill_color="YlOrRd",
        fill_opacity=0.7,
        line_opacity=0.3,
        bins=( [0, 100000, 200000, 300000, 500000, 600000, 700000, 800000,
                1000000, 1100000, 1500000, 2000000, 3000000, 4000000, 5600000]
              if kind=="car"
              else [0, 10000, 15000, 20000, 25000, 30000, 40000, 45000, 50000,
                    90000, 100000, 150000, 180000, 200000] ),
        legend_name=""
    ).add_to(m)

    # folium 기본 colorbar 제거
    for child in list(cp._children):
        if child.startswith("color_map"):
            del cp._children[child]

    # Tooltip: dict로 한번에
    value_dict = sido_df.set_index("시도명")[value_col].to_dict()

    # geo_prov를 직접 수정하면 다음 호출에 누적될 수 있으니, 얕은 복사(딥카피는 무거움)
    prov = {"type": geo_prov["type"], "features": []}
    for f in geo_prov["features"]:
        props = dict(f["properties"])
        nm = props["name"]
        props["차량대수"] = int(value_dict.get(nm, 0))
        prov["features"].append({"type": f["type"], "geometry": f["geometry"], "properties": props})

    folium.GeoJson(
        prov,
        style_function=lambda x: {"fillOpacity": 0, "color": "black", "weight": 0.3},
        highlight_function=lambda x: {"fillOpacity": 0.3, "weight": 2},
        tooltip=folium.GeoJsonTooltip(
            fields=["name", "차량대수"],
            aliases=["시도명:", "차량 대수(대):"],
            localize=True
        )
    ).add_to(m)

    return m


def build_sido_maps(dfs_by_year: dict, kind: str):
    """
    dfs_by_year: {2022: df, 2023: df, 2024: df}
    kind: "car" or "van"
    return: {2022: folium.Map, ...}
    """
    return {year: draw_sido_folium_map(df, year, kind=kind) for year, df in dfs_by_year.items()}
