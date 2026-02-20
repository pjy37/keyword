import streamlit as st


def render_autocomplete_tab(suggestions: list[str]):
    """자동완성 연관검색어 탭을 렌더링한다."""
    if not suggestions:
        st.warning("자동완성 결과가 없습니다.")
        return

    st.subheader(f"자동완성 연관검색어 ({len(suggestions)}개)")

    for i, keyword in enumerate(suggestions, 1):
        st.markdown(f"**{i}.** {keyword}")

    st.caption("네이버 검색창 자동완성 기반 (비공식) | API 키 없이 사용 가능")
