import os
import pandas as pd
import plotly.express as px
import streamlit as st


def draw_gender_age_chart(
    df_long: pd.DataFrame | None = None,
    *,
    file_path: str | None = None,
    years: list[str] = ["2024", "2023", "2022"],
    gender_colors: dict[str, str] | None = None,
    default_year: str = "2024",
    default_mode: str = "전체 보기",
):

    # -------------------------
    # 0) 데이터 로드
    # -------------------------
    if df_long is None:
        if file_path is None:
            raise ValueError("df_long 또는 file_path 둘 중 하나는 반드시 필요합니다.")

        # __file__ 기준 상대경로도 지원
        base_dir = os.path.dirname(os.path.abspath(__file__))
        abs_path = file_path
        if not os.path.isabs(file_path):
            abs_path = os.path.join(base_dir, file_path)

        df_long = pd.read_pickle(abs_path)

    df_long = df_long.copy()

    # -------------------------
    # 1) 비율 컬럼 준비(있으면 유지)
    # -------------------------
    if "비율(%)" not in df_long.columns:
        df_long["비율(%)"] = (
            df_long.groupby(["연도", "연령대"])["자동차등록대수"]
            .transform(lambda x: x / x.sum() * 100)
        )

    # -------------------------
    # 2) 색상 세팅
    # -------------------------
    if gender_colors is None:
        gender_colors = {"남자": "#2f7192", "여자": "#d6867f"}

    # -------------------------
    # 3) Streamlit UI
    # -------------------------
    # years가 실제 데이터와 다르면, 데이터 기반으로 보정
    available_years = sorted(df_long["연도"].astype(str).unique(), reverse=True)
    years = [y for y in years if y in available_years] or available_years

    if default_year not in years:
        default_year = years[0]

    selected_year = st.radio(
        "연도 선택",
        years,
        index=years.index(default_year),
        horizontal=True,
    )

    modes = ["전체 보기", "남여 비율 보기"]
    if default_mode not in modes:
        default_mode = modes[0]

    mode = st.selectbox("mode", modes, index=modes.index(default_mode))

    # -------------------------
    # 4) Plotly Figure 생성
    # -------------------------
    if mode == "전체 보기":
        df_plot = df_long[df_long["연도"].astype(str) == selected_year]
        title = f"{selected_year}년 연령대별 성별 자동차 등록대수"
        hovertemplate = (
            "연령대: %{x}<br>"
            "성별: %{fullData.name}<br>"
            "등록대수: %{y:,}대<extra></extra>"
        )

        fig = px.bar(
            df_plot,
            x="연령대",
            y="자동차등록대수",
            color="성별",
            barmode="group",
            color_discrete_map=gender_colors,
        )

        fig.update_traces(
            marker_line_width=0.5,
            marker_line_color="rgba(0,0,0,0.3)",
            hovertemplate=hovertemplate,
        )

    else:  # "남여 비율 보기"
        df_plot = df_long[df_long["연도"].astype(str) == selected_year]
        title = f"{selected_year}년 연령대별 성별 자동차 등록대수"

        fig = px.scatter(
            df_plot,
            x="연령대",
            y="비율(%)",                 # ✅ 비율 보기면 y는 비율(%)가 맞게 수정
            size="자동차등록대수",
            color="성별",
            color_discrete_map=gender_colors,
            size_max=60,
            hover_name="성별",
            hover_data={"연령대": True, "자동차등록대수": True, "성별": False, "비율(%)": ':.1f'},
        )

    # -------------------------
    # 5) 공통 레이아웃
    # -------------------------
    fig.update_layout(
        font=dict(family="Malgun Gothic, Arial, sans-serif", color="black"),
        title=dict(
            text=title,
            x=0.5,
            y=0.95,
            xanchor="center",
            font=dict(size=20, color="black"),
        ),
        margin=dict(t=100, b=50, l=120, r=50),
        xaxis_title="연령대",
        yaxis=dict(
            title=dict(
                text="자동차 등록대수 (대)" if mode != "남여 비율 보기" else "비율 (%)",
                standoff=40,
                font=dict(size=14),
            ),
            showgrid=True,
            gridcolor="rgba(0,0,0,0.1)",
            tickformat="," if mode != "남여 비율 보기" else ".0f",
            tickfont=dict(size=12, color="black"),
            automargin=True,
        ),
        plot_bgcolor="#ecf7f8",
        paper_bgcolor="#ecf7f8",
        legend=dict(
            title_text="",
            x=1.02,
            y=0.5,
            xanchor="left",
            yanchor="middle",
            bgcolor="rgba(255,255,255,0)",
            font=dict(size=12, color="black"),
        ),
        xaxis=dict(
            showgrid=False,
            tickfont=dict(size=12, color="black"),
            automargin=True,
            title_standoff=20,
        ),
    )

    st.plotly_chart(fig, use_container_width=True, theme=None)

    return fig, df_plot
