from typing import List

import requests

from config.settings import AUTOCOMPLETE_URL, AUTOCOMPLETE_PARAMS, REQUEST_TIMEOUT


def fetch_autocomplete_suggestions(keyword: str) -> List[str]:
    """네이버 검색창 자동완성 키워드를 가져온다.

    비공식 엔드포인트를 사용하므로 API 키가 필요 없다.
    실패 시 빈 리스트를 반환한다.
    """
    params = {**AUTOCOMPLETE_PARAMS, "q": keyword}
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Referer": "https://www.naver.com",
    }

    try:
        resp = requests.get(
            AUTOCOMPLETE_URL,
            params=params,
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()

        suggestions = []
        for item_group in data.get("items", []):
            for item in item_group:
                if isinstance(item, list) and len(item) >= 1:
                    keyword_text = item[0]
                    if isinstance(keyword_text, str) and keyword_text.strip():
                        suggestions.append(keyword_text.strip())
        return suggestions

    except Exception:
        return []
