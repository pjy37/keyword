from datetime import datetime, timedelta
import time

import requests

from config.settings import DATALAB_URL, REQUEST_TIMEOUT


# 연령대를 5단계로 통합 (네이버 데이터랩 기준)
AGE_GROUPS = {
    "10대": ["2"],               # 13~18세
    "20대": ["3", "4"],          # 19~24세, 25~29세
    "30대": ["5", "6"],          # 30~34세, 35~39세
    "40대": ["7", "8"],          # 40~44세, 45~49세
    "50대+": ["9", "10", "11"],  # 50~54세, 55~59세, 60세 이상
}

# 연령대를 11단계 개별 코드 (세밀한 비교용)
AGE_CODES_ALL = {
    "1": "0~12세",
    "2": "13~18세",
    "3": "19~24세",
    "4": "25~29세",
    "5": "30~34세",
    "6": "35~39세",
    "7": "40~44세",
    "8": "45~49세",
    "9": "50~54세",
    "10": "55~59세",
    "11": "60세 이상",
}

GENDERS = {"m": "남성", "f": "여성"}

# 키워드 도구 기준 7단계 연령대 (PC/모바일 분리용)
AGE_GROUPS_V2 = {
    "0~12": ["1"],
    "13~19": ["2"],
    "20~24": ["3"],
    "25~29": ["4"],
    "30~39": ["5", "6"],
    "40~49": ["7", "8"],
    "50~": ["9", "10", "11"],
}

DEVICES = {"pc": "PC", "mo": "모바일"}


def _call_datalab_api(body, client_id, client_secret):
    """네이버 데이터랩 API 공통 호출 함수."""
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret,
        "Content-Type": "application/json",
    }
    resp = requests.post(DATALAB_URL, json=body, headers=headers, timeout=REQUEST_TIMEOUT)

    if resp.status_code == 401:
        raise Exception("데이터랩 API 인증 실패: Client ID/Secret을 확인해주세요.")
    if resp.status_code == 429:
        raise Exception("데이터랩 API 호출 한도 초과: 잠시 후 다시 시도해주세요.")
    resp.raise_for_status()
    return resp.json()


def _get_date_range_monthly():
    """최근 1개월의 시작/종료 날짜를 반환한다."""
    end = datetime.now() - timedelta(days=1)
    start = end - timedelta(days=31)
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")


def _get_date_range_yearly():
    """최근 1년의 시작/종료 날짜를 반환한다."""
    end = datetime.now() - timedelta(days=1)
    start = end - timedelta(days=365)
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")


def _extract_ratio_sum(api_response):
    """API 응답에서 전체 기간 ratio 합계를 추출한다."""
    try:
        results = api_response.get("results", [])
        if not results:
            return 0.0
        data = results[0].get("data", [])
        if not data:
            return 0.0
        return sum(float(d.get("ratio", 0.0)) for d in data)
    except (IndexError, TypeError, ValueError):
        return 0.0


def _extract_ratios_by_group(api_response):
    """API 응답에서 여러 keywordGroup의 ratio 합계를 각각 추출한다.

    Returns:
        {groupName: ratio_sum, ...}
    """
    result = {}
    try:
        results = api_response.get("results", [])
        for r in results:
            name = r.get("title", "")
            data = r.get("data", [])
            total = sum(float(d.get("ratio", 0.0)) for d in data)
            result[name] = total
    except (IndexError, TypeError, ValueError):
        pass
    return result


def fetch_demographics(keyword, client_id, client_secret):
    """앵커 정규화 방식으로 정확한 성별/연령대 비중을 구한다.

    네이버 데이터랩 API는 호출마다 독립적으로 정규화(max=100)하므로
    단순 비교가 불가능하다. 이를 해결하기 위해:

    1. 전체(필터 없음) 기준선 호출
    2. 성별 필터 호출 (남성/여성 각각)
       - 같은 호출 내에서 기준 키워드와 대상 키워드를 함께 넣어 비교
    3. 연령대 필터 호출 (11개 개별 연령대)
       - 같은 방식으로 기준 키워드 대비 비교

    핵심: 같은 API 호출 내의 여러 keywordGroup은 동일한 정규화 스케일을
    공유하지만, gender/ages 필터는 호출 전체에 적용되므로
    다른 방식이 필요 → 각 세그먼트별 호출의 ratio 합 비교

    최종적으로는 각 세그먼트 호출의 ratio_sum을 직접 비교한다.
    timeUnit="date"로 충분한 데이터 포인트를 확보하여 정밀도를 높인다.

    Returns:
        (gender_data, age_data)
        gender_data: {"남성": float, "여성": float} - 비율(%)
        age_data: {"10대": float, ...} - 비율(%)
    """
    start_date, end_date = _get_date_range_monthly()

    # ── 성별 비중 산출 ──
    # 남성/여성 각각 호출, timeUnit="date"로 일별 데이터 확보 (약 30개 포인트)
    gender_sums = {}
    for gender_code, gender_label in GENDERS.items():
        body = {
            "startDate": start_date,
            "endDate": end_date,
            "timeUnit": "date",
            "keywordGroups": [
                {"groupName": keyword, "keywords": [keyword]}
            ],
            "gender": gender_code,
        }
        try:
            resp = _call_datalab_api(body, client_id, client_secret)
            gender_sums[gender_label] = _extract_ratio_sum(resp)
        except Exception:
            gender_sums[gender_label] = 0.0
        time.sleep(0.05)

    gender_total = sum(gender_sums.values())
    if gender_total > 0:
        gender_data = {k: round(v / gender_total * 100, 1) for k, v in gender_sums.items()}
    else:
        gender_data = {k: 0.0 for k in gender_sums}

    # ── 연령대 비중 산출 ──
    # 11개 개별 연령 코드로 각각 호출하여 세밀하게 비교 후 5단계로 합산
    age_code_sums = {}
    for age_code in AGE_CODES_ALL:
        body = {
            "startDate": start_date,
            "endDate": end_date,
            "timeUnit": "date",
            "keywordGroups": [
                {"groupName": keyword, "keywords": [keyword]}
            ],
            "ages": [age_code],
        }
        try:
            resp = _call_datalab_api(body, client_id, client_secret)
            age_code_sums[age_code] = _extract_ratio_sum(resp)
        except Exception:
            age_code_sums[age_code] = 0.0
        time.sleep(0.05)

    # 5단계로 합산
    age_group_sums = {}
    for group_label, codes in AGE_GROUPS.items():
        age_group_sums[group_label] = sum(age_code_sums.get(c, 0.0) for c in codes)

    age_total = sum(age_group_sums.values())
    if age_total > 0:
        age_data = {k: round(v / age_total * 100, 1) for k, v in age_group_sums.items()}
    else:
        age_data = {k: 0.0 for k in age_group_sums}

    return gender_data, age_data


def fetch_monthly_trend(keyword, client_id, client_secret):
    """최근 1년간 월별 검색량 추이를 조회한다.

    Returns:
        [{"period": "2025-02", "ratio": 85.3}, ...]
    """
    start_date, end_date = _get_date_range_yearly()
    body = {
        "startDate": start_date,
        "endDate": end_date,
        "timeUnit": "month",
        "keywordGroups": [
            {"groupName": keyword, "keywords": [keyword]}
        ],
    }

    try:
        resp = _call_datalab_api(body, client_id, client_secret)
        results = resp.get("results", [])
        if not results:
            return []
        data = results[0].get("data", [])
        return [{"period": d.get("period", ""), "ratio": float(d.get("ratio", 0))} for d in data]
    except Exception:
        return []


def fetch_demographics_by_device(keyword, client_id, client_secret):
    """디바이스별(PC/모바일) 성별/연령대 비중을 구한다.

    비율 계산 기준:
    - 성별: PC내 남성+여성=100%, 모바일내 남성+여성=100%
    - 연령대: PC내 전연령합=100%, 모바일내 전연령합=100%

    Returns:
        (gender_data, age_data)
        gender_data: {"남성": {"PC": float, "모바일": float}, "여성": {...}}
        age_data: {"0~12": {"PC": float, "모바일": float}, ...}
    """
    start_date, end_date = _get_date_range_monthly()

    # ── 성별 × 디바이스 (4회 호출) ──
    gender_device_sums = {}
    for gender_code, gender_label in GENDERS.items():
        gender_device_sums[gender_label] = {}
        for device_code, device_label in DEVICES.items():
            body = {
                "startDate": start_date,
                "endDate": end_date,
                "timeUnit": "date",
                "keywordGroups": [
                    {"groupName": keyword, "keywords": [keyword]}
                ],
                "gender": gender_code,
                "device": device_code,
            }
            try:
                resp = _call_datalab_api(body, client_id, client_secret)
                gender_device_sums[gender_label][device_label] = _extract_ratio_sum(resp)
            except Exception:
                gender_device_sums[gender_label][device_label] = 0.0
            time.sleep(0.05)

    # 성별 비율: 디바이스별로 각각 100%가 되도록 정규화
    # PC내: 남성% + 여성% = 100%
    # 모바일내: 남성% + 여성% = 100%
    gender_data = {}
    for _, device_label in DEVICES.items():
        device_total = sum(
            gender_device_sums[g_label].get(device_label, 0.0)
            for g_label in gender_device_sums
        )
        for g_label in gender_device_sums:
            if g_label not in gender_data:
                gender_data[g_label] = {}
            if device_total > 0:
                gender_data[g_label][device_label] = round(
                    gender_device_sums[g_label][device_label] / device_total * 100, 1
                )
            else:
                gender_data[g_label][device_label] = 0.0

    # ── 연령대 × 디바이스 (7그룹 × 2디바이스 = 14회 호출) ──
    age_device_sums = {}
    for group_label, codes in AGE_GROUPS_V2.items():
        age_device_sums[group_label] = {}
        for device_code, device_label in DEVICES.items():
            body = {
                "startDate": start_date,
                "endDate": end_date,
                "timeUnit": "date",
                "keywordGroups": [
                    {"groupName": keyword, "keywords": [keyword]}
                ],
                "ages": codes,
                "device": device_code,
            }
            try:
                resp = _call_datalab_api(body, client_id, client_secret)
                age_device_sums[group_label][device_label] = _extract_ratio_sum(resp)
            except Exception:
                age_device_sums[group_label][device_label] = 0.0
            time.sleep(0.05)

    # 연령대 비율: 디바이스별로 각각 100%가 되도록 정규화
    # PC내: 전연령합 = 100%
    # 모바일내: 전연령합 = 100%
    age_data = {}
    for _, device_label in DEVICES.items():
        device_total = sum(
            age_device_sums[a_label].get(device_label, 0.0)
            for a_label in age_device_sums
        )
        for a_label in age_device_sums:
            if a_label not in age_data:
                age_data[a_label] = {}
            if device_total > 0:
                age_data[a_label][device_label] = round(
                    age_device_sums[a_label][device_label] / device_total * 100, 1
                )
            else:
                age_data[a_label][device_label] = 0.0

    return gender_data, age_data


def fetch_monthly_trend_by_device(keyword, client_id, client_secret):
    """최근 1년간 디바이스별 월별 검색 추이(상대값)를 조회한다.

    Returns:
        {"PC": [{"period": "2025-02", "ratio": 85.3}, ...],
         "모바일": [...]}
    """
    start_date, end_date = _get_date_range_yearly()
    result = {}

    for device_code, device_label in DEVICES.items():
        body = {
            "startDate": start_date,
            "endDate": end_date,
            "timeUnit": "month",
            "keywordGroups": [
                {"groupName": keyword, "keywords": [keyword]}
            ],
            "device": device_code,
        }
        try:
            resp = _call_datalab_api(body, client_id, client_secret)
            results = resp.get("results", [])
            if results:
                data = results[0].get("data", [])
                result[device_label] = [
                    {"period": d.get("period", ""), "ratio": float(d.get("ratio", 0))}
                    for d in data
                ]
            else:
                result[device_label] = []
        except Exception:
            result[device_label] = []
        time.sleep(0.05)

    return result


def estimate_absolute_volume(trend_by_device, pc_monthly, mobile_monthly):
    """데이터랩 ratio + 검색광고 API 절대값으로 월별 절대 검색량을 추정한다.

    하이브리드 방식:
    - 검색광고 API에서 직전 완료월의 절대 검색량(PC/모바일)을 가져옴
    - 데이터랩 추이에서 해당 월의 ratio를 기준점으로 사용
    - 다른 월의 ratio를 기준점 대비 비율로 스케일링

    주의: PC와 모바일은 데이터랩에서 각각 독립적으로 정규화되므로
    별도로 스케일링해야 한다.

    Args:
        trend_by_device: fetch_monthly_trend_by_device() 반환값
        pc_monthly: 검색광고 API PC 월간 검색량 (int)
        mobile_monthly: 검색광고 API 모바일 월간 검색량 (int)

    Returns:
        [{"period": "2025-02", "pc": 1500, "mobile": 12000}, ...]
    """
    pc_trend = trend_by_device.get("PC", [])
    mobile_trend = trend_by_device.get("모바일", [])

    # 두 추이의 period를 기준으로 합치기
    pc_map = {t["period"]: t["ratio"] for t in pc_trend}
    mobile_map = {t["period"]: t["ratio"] for t in mobile_trend}

    # 모든 period 수집 (정렬)
    all_periods = sorted(set(list(pc_map.keys()) + list(mobile_map.keys())))
    if not all_periods:
        return []

    # 기준월 찾기: 끝에서 두 번째 (마지막은 현재 진행 중인 불완전한 월일 수 있음)
    def _find_ref_ratio(ratio_map, periods):
        """기준 ratio 찾기 — 끝에서 두 번째 또는 0이 아닌 가장 최근 값."""
        ref_idx = -2 if len(periods) >= 2 else -1
        ref_period = periods[ref_idx]
        ref_ratio = ratio_map.get(ref_period, 0)
        if ref_ratio > 0:
            return ref_ratio
        for p in reversed(periods):
            r = ratio_map.get(p, 0)
            if r > 0:
                return r
        return 0

    pc_ref_ratio = _find_ref_ratio(pc_map, all_periods)
    mobile_ref_ratio = _find_ref_ratio(mobile_map, all_periods)

    pc_scale = (pc_monthly / pc_ref_ratio) if pc_ref_ratio > 0 else 0
    mobile_scale = (mobile_monthly / mobile_ref_ratio) if mobile_ref_ratio > 0 else 0

    result = []
    for period in all_periods:
        pc_ratio = pc_map.get(period, 0)
        mobile_ratio = mobile_map.get(period, 0)
        result.append({
            "period": period,
            "pc": max(0, round(pc_ratio * pc_scale)),
            "mobile": max(0, round(mobile_ratio * mobile_scale)),
        })

    return result
