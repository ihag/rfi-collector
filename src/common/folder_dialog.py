import logging
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

_PS_SCRIPT = (
    "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8;"
    "Add-Type -AssemblyName System.Windows.Forms;"
    "$dlg = New-Object System.Windows.Forms.FolderBrowserDialog;"
    "$dlg.Description = '창을 닫거나 취소하면 기본 폴더에 자동 저장됩니다';"
    "$dlg.ShowNewFolderButton = $true;"
    "if ($dlg.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { Write-Host $dlg.SelectedPath }"
)


def choose_output_dir(default: Path) -> Path:
    """저장 폴더 선택 창을 띄운다. 취소/실패/비Windows 환경이면 default를 반환."""
    if sys.platform != "win32":
        return default
    try:
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-Command", _PS_SCRIPT],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        selected = proc.stdout.strip()
    except OSError as exc:
        logger.warning("폴더 선택 창을 열 수 없습니다: %s", exc)
        return default
    return Path(selected).resolve() if selected else default
