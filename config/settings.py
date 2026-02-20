# 네이버 검색광고 API
SEARCHAD_BASE_URL = "https://api.naver.com"
SEARCHAD_KEYWORD_URI = "/keywordstool"

# 네이버 데이터랩 API
DATALAB_URL = "https://openapi.naver.com/v1/datalab/search"

# 네이버 자동완성 (비공식)
AUTOCOMPLETE_URL = "https://ac.search.naver.com/nx/ac"

# 연령대 코드 매핑 (네이버 데이터랩)
AGE_CODE_MAP = {
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

# 자동완성 기본 파라미터
AUTOCOMPLETE_PARAMS = {
    "con": "1",
    "frm": "nv",
    "ans": "2",
    "r_format": "json",
    "r_enc": "UTF-8",
    "r_unicode": "0",
    "t_koreng": "1",
    "run": "2",
    "rev": "4",
    "q_enc": "UTF-8",
    "st": "100",
}

# API 요청 타임아웃 (초)
REQUEST_TIMEOUT = 10
