import logging
import os
from datetime import date, datetime, timedelta

import holidays
from dotenv import load_dotenv

from src.common.config import ENV_PATH, LOG_PATH
from src.common.errors import ConfigError

MAX_HOLIDAY_STREAK = 15  # 연휴가 아무리 길어도 이 이상 거슬러 올라가지 않음


def setup_logging():
    """로그를 파일(rfi.log)에만 기록한다. (콘솔 진행률 바를 방해하지 않기 위함)"""
    try:
        handlers = [logging.FileHandler(LOG_PATH, encoding="utf-8")]
    except OSError:  # 쓰기 권한이 없는 폴더 등
        handlers = [logging.NullHandler()]
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=handlers,
        force=True,
    )


def get_api_key() -> str:
    load_dotenv(ENV_PATH)
    api_key = (os.getenv("API_KEY") or "").strip()
    if not api_key:
        raise ConfigError(f".env 파일에 API_KEY가 없습니다. ({ENV_PATH})")
    return api_key


def is_holiday_or_weekend(dt, kr_holidays=None) -> bool:
    d = dt.date() if isinstance(dt, datetime) else dt
    if kr_holidays is None:
        kr_holidays = holidays.KR(years=d.year)
    return d.weekday() >= 5 or d in kr_holidays


def get_target_dates(days_ago=1, end_mode="now", today=None):
    """조회 기간 문자열과, 수집 대상 등록일 목록을 반환한다.

    전일이 주말/공휴일이면 직전 영업일까지 거슬러 올라가며
    그 사이의 모든 날짜를 대상에 포함한다.
    (예: 월요일 실행 -> 일, 토, 직전 금요일)
    """
    today = today or datetime.now()
    # 연말연초에 걸친 연휴를 위해 전년도 공휴일도 함께 로드
    kr_holidays = holidays.KR(years=range(today.year - 1, today.year + 1))

    target = today - timedelta(days=1)
    captured = []
    while is_holiday_or_weekend(target, kr_holidays) and len(captured) < MAX_HOLIDAY_STREAK:
        captured.append(target.strftime("%Y-%m-%d"))
        target -= timedelta(days=1)
    captured.append(target.strftime("%Y-%m-%d"))

    str_start = (today - timedelta(days=days_ago)).strftime("%Y%m%d0000")
    if end_mode == "yesterday":
        str_end = (today - timedelta(days=1)).strftime("%Y%m%d2359")
    else:
        str_end = today.strftime("%Y%m%d%H%M")

    return str_start, str_end, captured
