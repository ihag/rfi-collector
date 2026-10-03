import logging
from datetime import datetime
from pathlib import Path

from src.common.config import LOOKBACK_DAYS
from src.common.errors import ApiError, OutputError
from src.common.utils import get_api_key, get_target_dates
from src.rfi.api_client import fetch_all_items
from src.rfi.processor import build_rfi_table, summarize

logger = logging.getLogger(__name__)


def run_fetch_rfi(output_dir: Path, callback=None):
    """수집 -> 가공/1차 판별 -> 엑셀 저장. 완료 메시지 또는 None(대상 없음)을 반환."""
    report = callback or (lambda _percent: None)
    report(5)

    api_key = get_api_key()
    bgn_dt, end_dt, target_dates = get_target_dates(days_ago=LOOKBACK_DAYS, end_mode="yesterday")
    logger.info("조회 기간 %s ~ %s / 대상 등록일 %s", bgn_dt, end_dt, target_dates)

    items, failed = fetch_all_items(api_key, bgn_dt, end_dt, report)
    report(75)

    df = build_rfi_table(items, target_dates)
    if df is None:
        report(100)
        if failed:
            raise ApiError(f"수집된 데이터가 없고 일부 분야({', '.join(failed)})가 실패했습니다. 다시 실행해 주세요.")
        return None
    report(85)

    output_dir = Path(output_dir)
    save_path = output_dir / f"사전규격_{datetime.now():%y%m%d}.xlsx"
    report(95)
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        df.to_excel(save_path, index=False)
    except PermissionError:
        raise OutputError(f"파일이 열려 있어 저장할 수 없습니다. 닫고 다시 실행해 주세요. ({save_path.name})")
    except OSError as exc:
        raise OutputError(f"파일을 저장할 수 없습니다: {exc}")
    report(100)

    total, excluded, remaining = summarize(df)
    message = f"{total}건 수집 완료 (1차 비대상 {excluded}건 / 직접 판별 필요 {remaining}건)"
    if failed:
        message += f"\n   ⚠ 일부 분야 수집 실패: {', '.join(failed)} - 다시 실행해 주세요"
    logger.info(message)
    return message
