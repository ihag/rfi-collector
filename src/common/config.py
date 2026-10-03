import sys
from pathlib import Path


def _resolve_base_dir() -> Path:
    """exe(PyInstaller) 실행이면 exe가 있는 폴더, 아니면 프로젝트 루트."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    # 이 파일 위치: <root>/src/common/config.py
    return Path(__file__).resolve().parents[2]


BASE_DIR = _resolve_base_dir()
ENV_PATH = BASE_DIR / ".env"
LOG_PATH = BASE_DIR / "rfi.log"
DEFAULT_OUTPUT_DIR = BASE_DIR

# ---- API 설정 (조달청 나라장터 사전규격정보서비스) ----
_API_BASE = "https://apis.data.go.kr/1230000/ao/HrcspSsstndrdInfoService"
API_ENDPOINTS = {
    "물품": f"{_API_BASE}/getPublicPrcureThngInfoThng",
    "용역": f"{_API_BASE}/getPublicPrcureThngInfoServc",
    "공사": f"{_API_BASE}/getPublicPrcureThngInfoCnstwk",
    "외자": f"{_API_BASE}/getPublicPrcureThngInfoFrgcpt",
}
PAGE_SIZE = 999
MAX_PAGES = 100                 # 무한 루프 방지
REQUEST_TIMEOUT = (5, 30)       # (연결, 응답) 초
MAX_RETRIES = 3

# ---- 수집 / 1차 판별 기준 ----
LOOKBACK_DAYS = 30              # API 조회 시작일 = 오늘 - N일
MIN_BUDGET_EXCL_VAT = 90_909_091  # 1억 원 / 1.1 (부가세 제외 환산)
BUDGET_UNSET_MAX = 10           # 이 값 이하의 예산은 '미입력'으로 보고 제외하지 않음
