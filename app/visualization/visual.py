import plotly.express as px
import pandas as pd
import folium
import requests

def filter_data(df, sido, sigungu, car, gubun):
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


def draw_chart(dff, sido, sigungu, car, gubun, chart_type):
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



# ✅ GeoJSON은 전역에서 1번만 로드 (Streamlit 재실행에도 캐시 가능)
GEO_URL = "https://raw.githubusercontent.com/southkorea/southkorea-maps/master/kostat/2018/json/skorea-municipalities-2018-geo.json"
geo_data = requests.get(GEO_URL).json()

def draw_folium_map(pkl_path: str, year: int, vehicle_type: str):
    """
    vehicle_type: 'car' or 'van'
    return: folium.Map
    """
    category = "승용차" if vehicle_type == "car" else "승합차"

    full_df = pd.read_pickle(pkl_path)

    df = full_df[
        (full_df["reg_year"].astype(str) == str(year)) &
        (full_df["vehicle_type"] == vehicle_type)
    ]

    df_sum = df.groupby("sigungu_name")["car_count"].sum().reset_index()

    final_mapping = {}
    for feature in geo_data["features"]:
        g_name = feature["properties"]["name"]
        matched = df_sum[df_sum["sigungu_name"].str.contains(g_name, na=False)]
        val = matched["car_count"].sum() if not matched.empty else 0

        # (원본 코드의 보정 로직 유지)
        if g_name == "계룡시":
            val = 18600 if vehicle_type == "car" else 750
        elif g_name == "계양구":
            val = 110000 if vehicle_type == "car" else 4500

        final_mapping[g_name] = int(val)

    df_final = pd.DataFrame(list(final_mapping.items()), columns=["name", "value"])
    df_final["display_val"] = df_final["value"] / 1000

    # Bins (분포가 이상할 때 대비)
    series = df_final["display_val"]
    quantiles = [0, 0.1, 0.3, 0.5, 0.7, 0.85, 0.95, 1]
    bins = series.quantile(quantiles).unique().tolist()
    if len(bins) < 3:
        bins = 6  # folium이 내부에서 균등 분할

    m = folium.Map(location=[36.5, 127.5], zoom_start=7)

    choropleth = folium.Choropleth(
        geo_data=geo_data,
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

    # tooltip text 주입
    for feature in choropleth.geojson.data["features"]:
        name = feature["properties"]["name"]
        real_val = final_mapping.get(name, 0)
        feature["properties"]["tooltip_text"] = f"{name}: {real_val:,} 대"

    choropleth.geojson.add_child(
        folium.GeoJsonTooltip(fields=["tooltip_text"], aliases=["🚗 현황:"], labels=False)
    )

    return m
