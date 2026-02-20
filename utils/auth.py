import base64
import hashlib
import hmac
import time


def generate_signature(timestamp: str, method: str, uri: str, secret_key: str) -> str:
    """네이버 검색광고 API용 HMAC-SHA256 서명 생성."""
    message = f"{timestamp}.{method}.{uri}"
    signature = hmac.new(
        secret_key.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return base64.b64encode(signature).decode("utf-8")


def get_searchad_headers(
    method: str,
    uri: str,
    api_key: str,
    secret_key: str,
    customer_id: str,
) -> dict:
    """검색광고 API 인증 헤더 생성."""
    timestamp = str(int(time.time() * 1000))
    signature = generate_signature(timestamp, method, uri, secret_key)
    return {
        "Content-Type": "application/json; charset=UTF-8",
        "X-Timestamp": timestamp,
        "X-API-KEY": api_key,
        "X-Customer": customer_id,
        "X-Signature": signature,
    }
