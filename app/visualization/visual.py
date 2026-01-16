import plotly.express as px

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
