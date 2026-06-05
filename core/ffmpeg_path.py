import platform
from pathlib import Path

def get_ffmpeg_path():
    addon_root = Path(__file__).parent.parent

    if platform.system() == "Windows":
        return addon_root / "bin" / "windows"