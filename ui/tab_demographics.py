import os

import streamlit as st
from PIL import Image

from api.naver_searchad_scraper import scrape_keyword_charts


def render_demographics_tab(related_keywords_df, credentials):
    """인구통계 분석 탭을 렌더링한다.

    네이버 검색광고 키워드 도구에서 직접 차트를 스크래핑하여 표시한다.
    """
    has_naver_login = all([
        credentials.get("naver_login_id"),
        credentials.get("naver_login_pw"),
    ])

    if not has_naver_login:
        st.info(
            "인구통계 분석(성별/연령대/월별 추이)을 위해 **네이버 로그인 정보**를 설정해주세요.\n\n"
            "네이버 검색광고 키워드 도구에서 직접 차트를 가져옵니다.\n\n"
            "사이드바의 **API 키 설정 > 네이버 로그인** 에서 입력해주세요."
        )
        return

    naver_id = credentials["naver_login_id"]
    naver_pw = credentials["naver_login_pw"]

    st.subheader("인구통계 차트 (네이버 키워드 도구)")

    num_keywords = st.slider(
        "캡처할 키워드 수 (조회 결과 상위 N개)",
        min_value=1,
        max_value=10,
        value=3,
        key="demo_num_keywords",
    )

    if st.button("인구통계 차트 가져오기", type="primary", key="demo_scrape_btn"):
        keyword = st.session_state.get("run_keyword", "")
        if not keyword:
            st.warning("먼저 키워드를 입력하고 분석을 시작해주세요.")
            return

        progress_bar = st.progress(0)
        status_text = st.empty()
        log_container = st.expander("진행 로그 (상세)", expanded=True)
        log_lines = []

        step_count = [0]
        total_steps = 15 + num_keywords * 3

        def on_progress(msg):
            step_count[0] += 1
            pct = min(step_count[0] / total_steps, 0.99)
            progress_bar.progress(pct)
            status_text.text(msg)
            log_lines.append(msg)
            with log_container:
                st.text("\n".join(log_lines))

        try:
            with st.spinner("네이버 검색광고에서 차트를 가져오는 중... (약 1~2분 소요)"):
                chart_results = scrape_keyword_charts(
                    keyword=keyword,
                    naver_id=naver_id,
                    naver_pw=naver_pw,
                    num_keywords=num_keywords,
                    progress_callback=on_progress,
                )

            progress_bar.progress(1.0)
            status_text.text("완료!")

            if chart_results:
                st.session_state["demo_chart_results"] = chart_results
                st.success("{}개 키워드 차트를 가져왔습니다.".format(len(chart_results)))
            else:
                st.warning(
                    "차트를 가져오지 못했습니다.\n\n"
                    "위의 **진행 로그**에서 어느 단계에서 멈췄는지 확인해주세요."
                )

        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            st.error("차트 가져오기 실패: {}".format(e))

            if log_lines:
                with st.expander("실패 시점 로그", expanded=True):
                    for line in log_lines:
                        st.text(line)

            err_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "screenshots", "error_screenshot.png",
            )
            if os.path.exists(err_path):
                st.image(err_path, caption="오류 발생 시 화면", use_container_width=True)

    # 저장된 결과 표시
    if "demo_chart_results" in st.session_state and st.session_state["demo_chart_results"]:
        st.divider()
        for item in st.session_state["demo_chart_results"]:
            kw_name = item.get("keyword", "")
            img_path = item.get("image_path", "")

            st.markdown("### {}".format(kw_name))

            if img_path and os.path.exists(img_path):
                img = Image.open(img_path)
                st.image(img, caption="{} - 인구통계 차트".format(kw_name), use_container_width=True)
            else:
                st.warning("'{}' 차트 이미지를 찾을 수 없습니다.".format(kw_name))

            st.markdown("---")

    st.caption(
        "네이버 검색광고 키워드 도구에서 직접 캡처한 차트입니다. "
        "성별/연령대/월별 추이가 네이버 공식 데이터와 동일합니다."
    )
