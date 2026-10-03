import logging
import sys
import threading
import time

from src.common.errors import RfiError

logger = logging.getLogger(__name__)
BAR_LENGTH = 20


def _render(percent: int, suffix: str = ""):
    filled = BAR_LENGTH * percent // 100
    bar = "█" * filled + "░" * (BAR_LENGTH - filled)
    sys.stdout.write(f"\r▶ 진행률: [{bar}] {percent}%{suffix}")
    sys.stdout.flush()


def _wait_for_exit():
    try:
        input("엔터 키를 누르면 종료됩니다")
    except EOFError:  # 표준 입력이 없는 환경
        pass


def show_progress_bar(task_function, title="작업", pause=True):
    """task_function(callback=...)을 별도 스레드에서 실행하며 진행률을 표시한다.

    task_function은 문자열(완료 메시지) 또는 None(결과 없음)을 반환하고,
    실패 시 RfiError를 발생시킨다.
    """
    print("=" * 50)
    print(f"   {title} 시작")
    print("=" * 50)

    state = {"percent": 0, "result": None, "error": None}

    def report(percent):
        state["percent"] = max(0, min(100, int(percent)))

    def worker():
        try:
            state["result"] = task_function(callback=report)
        except RfiError as exc:
            logger.error("작업 실패: %s", exc)
            state["error"] = str(exc)
        except Exception as exc:  # 예상하지 못한 오류도 화면에 안내하고 로그에 남김
            logger.exception("예기치 못한 오류")
            state["error"] = f"예기치 못한 오류: {exc} (자세한 내용은 rfi.log 참고)"

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()

    last = -1
    while thread.is_alive():
        if state["percent"] != last:
            last = state["percent"]
            _render(last)
        time.sleep(0.05)
    thread.join()

    if state["error"]:
        _render(state["percent"], " 중단")
        message = f"[오류] {state['error']}"
    else:
        _render(100, " 완료")
        message = state["result"] or "수집 대상 기간에 새로 등록된 사업이 없습니다."
    print()

    print("\n" + "=" * 50)
    print(f"   {message}")
    print("=" * 50 + "\n")

    if pause:
        _wait_for_exit()
