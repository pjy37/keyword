import streamlit as st

from ui.sidebar import render_sidebar
from ui.tab_keywords import render_keywords_tab
from ui.tab_autocomplete import render_autocomplete_tab
from services.keyword_analyzer import analyze_keyword

st.set_page_config(
    page_title="네이버 키워드 분석 도구",
    page_icon="🔍",
    layout="wide",
)

st.title("네이버 키워드 분석 도구")
st.caption("메인 키워드를 입력하면 연관 키워드와 자동완성을 한 번에 분석합니다.")

# 사이드바 렌더링
keyword, credentials = render_sidebar()

if keyword:
    with st.spinner("분석 중..."):
        result = analyze_keyword(keyword, credentials)

    # 부분 에러 표시
    for err in result.get("errors", []):
        st.warning(err)

    # 2개 탭으로 결과 표시
    tab1, tab2 = st.tabs([
        "연관 키워드 + 검색량",
        "자동완성 연관검색어",
    ])

    with tab1:
        render_keywords_tab(result.get("related_keywords"))
    with tab2:
        render_autocomplete_tab(result.get("autocomplete", []))
else:
    st.info("사이드바에서 키워드를 입력하고 **분석 시작** 버튼을 눌러주세요.")
