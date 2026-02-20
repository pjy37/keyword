from typing import Optional, Tuple

import streamlit as st


def render_sidebar() -> Tuple[Optional[str], dict]:
    """사이드바를 렌더링하고 키워드와 인증 정보를 반환한다.

    Returns:
        (keyword, credentials) - 분석 실행 시 keyword가 문자열, 아니면 None
    """
    with st.sidebar:
        st.header("네이버 키워드 분석 도구")

        # API 키 설정
        with st.expander("API 키 설정", expanded=False):
            st.subheader("검색광고 API")
            st.text_input(
                "API License", type="password", key="searchad_api_key"
            )
            st.text_input(
                "Secret Key", type="password", key="searchad_secret_key"
            )
            st.text_input(
                "Customer ID", key="searchad_customer_id"
            )

        # API 키 발급 안내
        with st.expander("API 키 발급 안내", expanded=False):
            st.markdown("""
**검색광고 API 키 발급**
1. [네이버 검색광고](https://searchad.naver.com) 접속 및 로그인
2. 상단 메뉴 **도구 > API 사용 관리**
3. API License, Secret Key, Customer ID 확인
            """)

        st.divider()

        # 키워드 입력
        st.text_input(
            "분석할 키워드",
            placeholder="예: 캠핑, 다이어트, 맛집",
            key="keyword_input",
        )

        analyze_clicked = st.button(
            "분석 시작",
            type="primary",
            use_container_width=True,
        )

        # 분석 버튼 클릭 시 session_state에 저장
        if analyze_clicked and st.session_state.get("keyword_input", "").strip():
            st.session_state["run_keyword"] = st.session_state["keyword_input"].strip()

        # API 키 보유 상태 표시
        st.divider()
        st.caption("API 연결 상태")

        has_searchad = all([
            st.session_state.get("searchad_api_key"),
            st.session_state.get("searchad_secret_key"),
            st.session_state.get("searchad_customer_id"),
        ])

        if has_searchad:
            st.success("검색광고 API: 설정됨", icon="✅")
        else:
            st.info("검색광고 API: 미설정", icon="ℹ️")

    # session_state에서 직접 읽기
    credentials = {
        "searchad_api_key": st.session_state.get("searchad_api_key", ""),
        "searchad_secret_key": st.session_state.get("searchad_secret_key", ""),
        "searchad_customer_id": st.session_state.get("searchad_customer_id", ""),
    }

    keyword = st.session_state.get("run_keyword")
    if keyword:
        return keyword, credentials

    return None, credentials
