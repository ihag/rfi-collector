"""RFI Collector 진입점.

실행:  python main.py
빌드:  pyinstaller --onefile --name RFI main.py
"""
import multiprocessing
from functools import partial

from src.common.config import DEFAULT_OUTPUT_DIR
from src.common.folder_dialog import choose_output_dir
from src.common.progress_ui import show_progress_bar
from src.common.utils import setup_logging
from src.rfi.get_rfilist import run_fetch_rfi


def main():
    setup_logging()
    output_dir = choose_output_dir(DEFAULT_OUTPUT_DIR)
    print(f"\n저장 폴더: {output_dir}\n")
    show_progress_bar(partial(run_fetch_rfi, output_dir), title="RFI 수집")


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
