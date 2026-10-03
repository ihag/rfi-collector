import logging
import time
from urllib.parse import quote

import requests

from src.common.config import (
    API_ENDPOINTS,
    MAX_PAGES,
    MAX_RETRIES,
    PAGE_SIZE,
    REQUEST_TIMEOUT,
)
from src.common.errors import ApiError

logger = logging.getLogger(__name__)

_OK_CODES = {"00", "03"}  # 00: 정상, 03: 데이터 없음


def _mask(text: str, api_key: str) -> str:
    """오류 메시지/로그에 인증키가 노출되지 않도록 가린다."""
    for secret in {api_key, quote(api_key, safe="")}:
        text = text.replace(secret, "***")
    return text


def _validate(payload) -> None:
    if not isinstance(payload, dict) or "response" not in payload:
        raise ApiError(f"예상하지 못한 응답 형식입니다: {str(payload)[:200]}")
    header = payload["response"].get("header", {})
    code = str(header.get("resultCode", "00"))
    if code not in _OK_CODES:
        raise ApiError(f"API 오류 [{code}] {header.get('resultMsg', '')}")


def _request_json(session, url, params, api_key):
    last_error = ""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            res = session.get(url, params=params, timeout=REQUEST_TIMEOUT)
            res.raise_for_status()
            payload = res.json()
            _validate(payload)
            return payload
        except ApiError as exc:
            # 인증키 오류 등은 재시도해도 소용없으므로 즉시 중단 (키는 마스킹)
            raise ApiError(_mask(str(exc), api_key)) from None
        except (requests.RequestException, ValueError) as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            if isinstance(exc, ValueError):
                last_error += " (응답이 JSON이 아닙니다. 인증키/활용신청 상태를 확인하세요)"
            last_error = _mask(last_error, api_key)
            logger.warning("API 호출 실패 (%d/%d): %s", attempt, MAX_RETRIES, last_error)
            if attempt < MAX_RETRIES:
                time.sleep(attempt)
    raise ApiError(f"API 호출 실패 ({MAX_RETRIES}회 재시도): {last_error}")


def _extract_items(payload) -> list:
    items = payload["response"].get("body", {}).get("items") or []
    if isinstance(items, dict):  # 단건일 때 dict로 내려오는 경우 대비
        items = items.get("item", items)
        if isinstance(items, dict):
            items = [items]
    return list(items)


def _fetch_endpoint(session, url, api_key, bgn_dt, end_dt) -> list:
    collected = []
    for page_no in range(1, MAX_PAGES + 1):
        params = {
            "ServiceKey": api_key,
            "inqryDiv": "1",
            "inqryBgnDt": bgn_dt,
            "inqryEndDt": end_dt,
            "pageNo": str(page_no),
            "numOfRows": str(PAGE_SIZE),
            "type": "json",
        }
        items = _extract_items(_request_json(session, url, params, api_key))
        collected.extend(items)
        if len(items) < PAGE_SIZE:
            break
    return collected


def fetch_all_items(api_key, bgn_dt, end_dt, callback=None):
    """4개 분야(물품/용역/공사/외자)의 사전규격을 모두 조회한다.

    Returns:
        (items, failed_labels)  일부 분야만 실패하면 실패한 분야명을 함께 돌려준다.
    Raises:
        ApiError: 모든 분야가 실패한 경우
    """
    report = callback or (lambda _percent: None)
    all_items, failed, last_error = [], [], None

    with requests.Session() as session:
        for idx, (label, url) in enumerate(API_ENDPOINTS.items()):
            report(10 + idx * 15)
            try:
                items = _fetch_endpoint(session, url, api_key, bgn_dt, end_dt)
            except ApiError as exc:
                logger.error("[%s] 수집 실패: %s", label, exc)
                failed.append(label)
                last_error = exc
                continue
            logger.info("[%s] %d건 수집", label, len(items))
            all_items.extend(items)

    if len(failed) == len(API_ENDPOINTS):
        raise ApiError(f"모든 분야 수집에 실패했습니다. ({last_error})")
    return all_items, failed
