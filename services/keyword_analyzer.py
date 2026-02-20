import pandas as pd

from api.naver_autocomplete import fetch_autocomplete_suggestions
from api.naver_searchad import fetch_related_keywords


def analyze_keyword(keyword, credentials):
    """메인 키워드에 대해 연관키워드, 자동완성을 분석한다.

    인구통계(성별/연령대/월별 추이)는 별도의 스크래핑으로 처리된다.
    """
    result = {
        "related_keywords": None,
        "autocomplete": [],
        "errors": [],
    }

    # 1. 자동완성 (API 키 불필요)
    try:
        result["autocomplete"] = fetch_autocomplete_suggestions(keyword)
    except Exception as e:
        result["errors"].append("자동완성 조회 실패: {}".format(e))

    # 2. 연관 키워드 + 검색량 (검색광고 API)
    searchad_keys = (
        credentials.get("searchad_api_key"),
        credentials.get("searchad_secret_key"),
        credentials.get("searchad_customer_id"),
    )
    if all(searchad_keys):
        try:
            result["related_keywords"] = fetch_related_keywords(
                keyword, *searchad_keys
            )
        except Exception as e:
            result["errors"].append("연관 키워드 조회 실패: {}".format(e))
    else:
        result["errors"].append(
            "검색광고 API 키가 설정되지 않았습니다. "
            "사이드바에서 API 키를 입력하면 연관 키워드와 검색량을 확인할 수 있습니다."
        )

    return result
