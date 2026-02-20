import time
from datetime import datetime

import pandas as pd
import requests

from config.settings import SEARCHAD_BASE_URL, SEARCHAD_KEYWORD_URI, REQUEST_TIMEOUT
from utils.auth import get_searchad_headers


def _parse_search_count(value) -> int:
    """검색량 값을 정수로 변환한다. '< 10' 같은 문자열은 5로 처리."""
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        stripped = value.strip().replace(",", "")
        if stripped.startswith("<"):
            return 5
        try:
            return int(stripped)
        except ValueError:
            return 0
    return 0


def fetch_related_keywords(
    keyword: str,
    api_key: str,
    secret_key: str,
    customer_id: str,
) -> pd.DataFrame:
    """네이버 검색광고 API로 연관 키워드와 월간 검색량을 조회한다.

    Returns:
        DataFrame with columns: 키워드, PC검색량, 모바일검색량, 총검색량, 경쟁도,
                                 PC검색량_원본, 모바일검색량_원본
    Raises:
        Exception: API 호출 실패 시
    """
    url = SEARCHAD_BASE_URL + SEARCHAD_KEYWORD_URI
    headers = get_searchad_headers("GET", SEARCHAD_KEYWORD_URI, api_key, secret_key, customer_id)
    params = {
        "hintKeywords": keyword,
        "showDetail": "1",
    }

    resp = requests.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)

    if resp.status_code == 401:
        raise Exception("검색광고 API 인증 실패: API 키를 확인해주세요.")
    if resp.status_code == 429:
        raise Exception("검색광고 API 호출 한도 초과: 잠시 후 다시 시도해주세요.")
    resp.raise_for_status()

    data = resp.json()
    keyword_list = data.get("keywordList", [])

    if not keyword_list:
        return pd.DataFrame(columns=["키워드", "PC검색량", "모바일검색량", "총검색량", "경쟁도",
                                      "PC검색량_원본", "모바일검색량_원본"])

    rows = []
    for item in keyword_list:
        pc_raw = item.get("monthlyPcQcCnt", 0)
        mobile_raw = item.get("monthlyMobileQcCnt", 0)
        pc = _parse_search_count(pc_raw)
        mobile = _parse_search_count(mobile_raw)
        rows.append({
            "키워드": item.get("relKeyword", ""),
            "PC검색량": pc,
            "모바일검색량": mobile,
            "총검색량": pc + mobile,
            "경쟁도": item.get("compIdx", ""),
            "PC검색량_원본": str(pc_raw),
            "모바일검색량_원본": str(mobile_raw),
        })

    df = pd.DataFrame(rows)
    df = df.sort_values("총검색량", ascending=False).reset_index(drop=True)
    return df


def fetch_current_search_volume(
    keyword: str,
    api_key: str,
    secret_key: str,
    customer_id: str,
) -> dict:
    """검색광고 API로 현재 월 PC/모바일 절대 검색량을 조회한다.

    /keywordstool은 항상 직전 완료월 기준 검색량만 반환하므로
    1회 호출로 현재 기준값을 가져온다.

    Returns:
        {"pc": 1500, "mobile": 12000}
    """
    url = SEARCHAD_BASE_URL + SEARCHAD_KEYWORD_URI
    headers = get_searchad_headers(
        "GET", SEARCHAD_KEYWORD_URI, api_key, secret_key, customer_id
    )
    params = {
        "hintKeywords": keyword,
        "showDetail": "1",
    }

    resp = requests.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)
    if resp.status_code == 429:
        time.sleep(1)
        headers = get_searchad_headers(
            "GET", SEARCHAD_KEYWORD_URI, api_key, secret_key, customer_id
        )
        resp = requests.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()

    data = resp.json()
    keyword_list = data.get("keywordList", [])

    keyword_lower = keyword.lower().replace(" ", "")
    for item in keyword_list:
        rel_kw = item.get("relKeyword", "").lower().replace(" ", "")
        if rel_kw == keyword_lower:
            return {
                "pc": _parse_search_count(item.get("monthlyPcQcCnt", 0)),
                "mobile": _parse_search_count(item.get("monthlyMobileQcCnt", 0)),
            }

    return {"pc": 0, "mobile": 0}
