import sys
from pathlib import Path

def app_base_dir() -> Path:
    
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)

    return Path(__file__).resolve().parents[1]

def resource_path(*parts) -> str:
    return str(app_base_dir().joinpath(*parts))