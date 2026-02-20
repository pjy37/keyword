from typing import Optional

import streamlit as st
import plotly.express as px
import pandas as pd


def render_keywords_tab(df: Optional[pd.DataFrame]):
    """연관 키워드 + 검색량 탭을 렌더링한다."""
    if df is None:
        st.info(
            "검색광고 API 키를 설정하면 연관 키워드와 월간 검색량을 확인할 수 있습니다.\n\n"
            "사이드바의 **API 키 설정**에서 검색광고 API 키를 입력해주세요."
        )
        return

    if df.empty:
        st.warning("연관 키워드가 없습니다.")
        return

    st.subheader(f"총 {len(df)}개의 연관 키워드")

    # 표시용 DataFrame (원본 검색량 문자열 사용)
    display_df = df[["키워드", "PC검색량_원본", "모바일검색량_원본", "총검색량", "경쟁도"]].copy()
    display_df.columns = ["키워드", "PC 검색량", "모바일 검색량", "총 검색량", "경쟁도"]

    st.dataframe(
        display_df,
        width="stretch",
        hide_index=True,
        column_config={
            "총 검색량": st.column_config.NumberColumn(format="%d"),
        },
    )

    # 상위 20개 바 차트
    top_n = min(20, len(df))
    chart_df = df.head(top_n).copy()

    fig = px.bar(
        chart_df,
        x="총검색량",
        y="키워드",
        orientation="h",
        title=f"검색량 상위 {top_n}개 키워드",
        color="총검색량",
        color_continuous_scale="Blues",
    )
    fig.update_layout(
        yaxis={"categoryorder": "total ascending"},
        height=max(400, top_n * 30),
        showlegend=False,
    )
    st.plotly_chart(fig, width="stretch")

    # CSV 다운로드
    csv = df[["키워드", "PC검색량_원본", "모바일검색량_원본", "총검색량", "경쟁도"]].to_csv(
        index=False, encoding="utf-8-sig"
    )
    st.download_button(
        label="CSV 다운로드",
        data=csv,
        file_name="related_keywords.csv",
        mime="text/csv",
    )
