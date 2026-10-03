from datetime import datetime

from src.common.utils import get_target_dates


def test_weekday_targets_only_yesterday():
    # 2025-03-11 (화) -> 전일 월요일만
    _, _, dates = get_target_dates(today=datetime(2025, 3, 11, 9, 0))
    assert dates == ["2025-03-10"]


def test_monday_includes_weekend_and_friday():
    # 2025-03-10 (월) -> 일, 토, 직전 금요일
    _, _, dates = get_target_dates(today=datetime(2025, 3, 10, 9, 0))
    assert dates == ["2025-03-09", "2025-03-08", "2025-03-07"]


def test_holiday_across_year_boundary():
    # 2025-01-02 (목): 1/1 신정 -> 12/31(화)까지 거슬러 올라감
    _, _, dates = get_target_dates(today=datetime(2025, 1, 2, 9, 0))
    assert dates == ["2025-01-01", "2024-12-31"]


def test_date_range_strings():
    today = datetime(2025, 3, 11, 14, 30)
    start, end, _ = get_target_dates(days_ago=30, end_mode="yesterday", today=today)
    assert start == "202502090000"
    assert end == "202503102359"
    _, end_now, _ = get_target_dates(days_ago=30, end_mode="now", today=today)
    assert end_now == "202503111430"
