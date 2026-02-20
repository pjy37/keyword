import os
from typing import Optional, Tuple

import streamlit as st

# .env 파일 자동 로드 (python-dotenv 설치 필요: pip install python-dotenv)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def _get_credentials() -> dict:
    """환경변수 또는 기본값에서 API 인증 정보를 가져온다.

    우선순위: 환경변수(.env) > 하드코딩 기본값
    """
    return {
        "searchad_api_key": os.getenv(
            "SEARCHAD_API_KEY",
            "01000000007638696007d48dbcde1c7ccc0ebdd11cef980bb94e42063caa226416cc22c0df",
        ),
        "searchad_secret_key": os.getenv(
            "SEARCHAD_SECRET_KEY",
            "AQAAAAB2OGlgB9SNvN4cfMwOvdEcgPDln0EJRfKT/DTm76IRpg==",
        ),
        "searchad_customer_id": os.getenv(
            "SEARCHAD_CUSTOMER_ID",
            "3854788",
        ),
        "datalab_client_id": os.getenv("DATALAB_CLIENT_ID", ""),
        "datalab_client_secret": os.getenv("DATALAB_CLIENT_SECRET", ""),
    }


def render_sidebar() -> Tuple[Optional[str], dict]:
    """사이드바를 렌더링하고 키워드와 인증 정보를 반환한다.

    Returns:
        (keyword, credentials) - 분석 실행 시 keyword가 문자열, 아니면 None
    """
    credentials = _get_credentials()

    with st.sidebar:
        st.header("네이버 키워드 분석 도구")

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

        st.divider()
        st.caption("API 연결 상태")

        # 검색광고 API 상태
        if credentials["searchad_api_key"] and credentials["searchad_customer_id"]:
            st.success("검색광고 API: 연결됨", icon="✅")
        else:
            st.error("검색광고 API: 미설정", icon="❌")

        # 데이터랩 API 상태
        if credentials["datalab_client_id"]:
            st.success("데이터랩 API: 연결됨", icon="✅")
        else:
            st.info("데이터랩 API: 미설정 (선택사항)", icon="ℹ️")

        # API 키 확인용 (접힌 상태)
        with st.expander("API 키 확인"):
            st.text(f"Customer ID: {credentials['searchad_customer_id']}")
            st.text(f"API Key: ...{credentials['searchad_api_key'][-8:]}")
            st.text(f"Secret: ...{credentials['searchad_secret_key'][-8:]}")
            st.caption("키 변경은 .env 파일을 수정하세요.")

    keyword = st.session_state.get("run_keyword")
    if keyword:
        return keyword, credentials

    return None, credentials
