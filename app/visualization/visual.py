import plotly.express as px
import pandas as pd
import folium
import requests

GEO_URL_PROVINCES = "https://raw.githubusercontent.com/southkorea/southkorea-maps/master/kostat/2018/json/skorea-provinces-2018-geo.json"
GEO_URL = "https://raw.githubusercontent.com/southkorea/southkorea-maps/master/kostat/2018/json/skorea-municipalities-2018-geo.json"
geo_data = requests.get(GEO_URL).json()



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



def draw_gugun_folium_map(pkl_path: str, year: int, vehicle_type: str):
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



def draw_sido_folium_map(sido_df, year: int, kind: str = "car"):
    """
    sido_df: 컬럼에 '시도명' + f"{year}.12 월" 존재해야 함
    year: 2022, 2023, 2024 ...
    kind: "car" 또는 "van" (승용/승합)
    return: folium.Map
    """

    # 1) kind별 설정
    if kind == "car":
        title = f"{year}년 자동차 등록 현황"
        custom_bins = [0, 100000, 200000, 300000, 500000, 600000, 700000, 800000,
                       1000000, 1100000, 1500000, 2000000, 3000000, 4000000, 5600000]
        legend_html = f"""
        <div style="
            position: fixed;
            top: 20px; right: 20px; width: 200px; height: auto;
            background-color: white; border:2px solid grey; z-index:9999; font-size:12px;
            padding: 10px; border-radius: 10px; opacity: 0.9;">
            <b style="font-size:13px;">{title}</b><br>
            <div style="margin-top:8px;">
                <i style="background:#800026; width:14px; height:14px; float:left; margin-right:8px; border:1px solid #999;"></i> 4M ~ 5.6M<br>
                <i style="background:#BD0026; width:14px; height:14px; float:left; margin-right:8px; border:1px solid #999;"></i> 3M ~ 4M<br>
                <i style="background:#E31A1C; width:14px; height:14px; float:left; margin-right:8px; border:1px solid #999;"></i> 2M ~ 3M<br>
                <i style="background:#FC4E2A; width:14px; height:14px; float:left; margin-right:8px; border:1px solid #999;"></i> 1.5M ~ 2M<br>
                <i style="background:#FD8D3C; width:14px; height:14px; float:left; margin-right:8px; border:1px solid #999;"></i> 1.1M ~ 1.5M<br>
                <i style="background:#FEB24C; width:14px; height:14px; float:left; margin-right:8px; border:1px solid #999;"></i> 1M ~ 1.1M<br>
                <i style="background:#FED976; width:14px; height:14px; float:left; margin-right:8px; border:1px solid #999;"></i> 800K ~ 1M<br>
                <i style="background:#FFEDA0; width:14px; height:14px; float:left; margin-right:8px; border:1px solid #999;"></i> 700K ~ 800K<br>
                <i style="background:#FFFFCC; width:14px; height:14px; float:left; margin-right:8px; border:1px solid #999;"></i> 600K ~ 700K<br>
                <i style="background:#FFFFE5; width:14px; height:14px; float:left; margin-right:8px; border:1px solid #999;"></i> 500K ~ 600K<br>
                <i style="background:#FFF7BC; width:14px; height:14px; float:left; margin-right:8px; border:1px solid #999;"></i> 300K ~ 500K<br>
                <i style="background:#FEE391; width:14px; height:14px; float:left; margin-right:8px; border:1px solid #999;"></i> 200K ~ 300K<br>
                <i style="background:#FEC44F; width:14px; height:14px; float:left; margin-right:8px; border:1px solid #999;"></i> 100K ~ 200K<br>
                <i style="background:#FFFFF7; width:14px; height:14px; float:left; margin-right:8px; border:1px solid #999;"></i> 100K 미만<br>
            </div>
            <p style="font-size:10px; margin-top:5px; color:gray; line-height:1.2;">
                * K=천 단위, M=백만 단위
            </p>
        </div>
        """
    else:
        title = f"{year}년 승합차 등록 현황"
        custom_bins = [0, 10000, 15000, 20000, 25000, 30000, 40000, 45000, 50000,
                       90000, 100000, 150000, 180000, 200000]
        legend_html = f"""
        <div style="
            position: fixed;
            top: 20px; right: 20px; width: 180px; height: auto;
            background-color: white; border:2px solid grey; z-index:9999; font-size:12px;
            padding: 10px; border-radius: 10px; opacity: 0.9;">
            <b style="font-size:13px;">{title}</b><br>
            <div style="margin-top:8px; line-height: 1.5;">
                <i style="background:#800026; width:13px; height:13px; float:left; margin-right:8px; border:1px solid #999;"></i> 180K ~ 200K<br>
                <i style="background:#BD0026; width:13px; height:13px; float:left; margin-right:8px; border:1px solid #999;"></i> 150K ~ 180K<br>
                <i style="background:#E31A1C; width:13px; height:13px; float:left; margin-right:8px; border:1px solid #999;"></i> 100K ~ 150K<br>
                <i style="background:#FC4E2A; width:13px; height:13px; float:left; margin-right:8px; border:1px solid #999;"></i> 90K ~ 100K<br>
                <i style="background:#FD8D3C; width:13px; height:13px; float:left; margin-right:8px; border:1px solid #999;"></i> 50K ~ 90K<br>
                <i style="background:#FEB24C; width:13px; height:13px; float:left; margin-right:8px; border:1px solid #999;"></i> 45K ~ 50K<br>
                <i style="background:#FED976; width:13px; height:13px; float:left; margin-right:8px; border:1px solid #999;"></i> 40K ~ 45K<br>
                <i style="background:#FFEDA0; width:13px; height:13px; float:left; margin-right:8px; border:1px solid #999;"></i> 30K ~ 40K<br>
                <i style="background:#FFFFCC; width:13px; height:13px; float:left; margin-right:8px; border:1px solid #999;"></i> 25K ~ 30K<br>
                <i style="background:#FFFFE5; width:13px; height:13px; float:left; margin-right:8px; border:1px solid #999;"></i> 20K ~ 25K<br>
                <i style="background:#FFF7BC; width:13px; height:13px; float:left; margin-right:8px; border:1px solid #999;"></i> 15K ~ 20K<br>
                <i style="background:#FEE391; width:13px; height:13px; float:left; margin-right:8px; border:1px solid #999;"></i> 10K ~ 15K<br>
                <i style="background:#FFFFF7; width:13px; height:13px; float:left; margin-right:8px; border:1px solid #999;"></i> 10K 미만<br>
            </div>
            <p style="font-size:10px; margin-top:5px; color:gray;">* K = 천 단위 (10K = 1만 대)</p>
        </div>
        """

    # 2) 기본 지도
    m = folium.Map(location=[36.5, 127.8], zoom_start=7)
    value_col = f"{year}.12 월"

    # 3) Choropleth
    cp = folium.Choropleth(
        geo_data=GEO_URL_PROVINCES,
        data=sido_df,
        columns=["시도명", value_col],
        key_on="feature.properties.name",
        fill_color="YlOrRd",
        fill_opacity=0.7,
        line_opacity=0.3,
        bins=custom_bins,
        legend_name=""
    ).add_to(m)

    # folium 기본 colorbar 제거
    for child in list(cp._children):
        if child.startswith("color_map"):
            del cp._children[child]

    # 4) Tooltip용 GeoJson
    value_dict = sido_df.set_index("시도명")[value_col].to_dict()
    geo_data = requests.get(GEO_URL_PROVINCES).json()

    for f in geo_data["features"]:
        f["properties"]["차량대수"] = value_dict.get(f["properties"]["name"], 0)

    folium.GeoJson(
        geo_data,
        style_function=lambda x: {"fillOpacity": 0, "color": "black", "weight": 0.3},
        highlight_function=lambda x: {"fillOpacity": 0.3, "weight": 2},
        tooltip=folium.GeoJsonTooltip(
            fields=["name", "차량대수"],
            aliases=["시도명:", "차량 대수(대):"],
            localize=True
        )
    ).add_to(m)

    # 5) 커스텀 레전드 추가
    m.get_root().html.add_child(folium.Element(legend_html))

    return m


def build_sido_maps(dfs_by_year: dict, kind: str):
    """
    dfs_by_year: {2022: df, 2023: df, 2024: df}
    kind: "car" or "van"
    return: {2022: folium.Map, ...}
    """
    return {year: draw_sido_folium_map(df, year, kind=kind) for year, df in dfs_by_year.items()}
