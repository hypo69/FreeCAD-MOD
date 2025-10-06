# utils.py
import json
import re
from pathlib import Path
from typing import Any, Optional, Union

# === string/ai_string_utils.py ===
def normalize_answer(text: str) -> str:
    text = text.strip()
    if text.startswith("```") and text.endswith("```"):
        lines = text.split("\n")
        if len(lines) >= 2:
            return "\n".join(lines[1:-1])
    if text.startswith("text\n"):
        text = text[5:]
    return text.strip()

# === file.py ===
def read_text_file(file_path: Path) -> Optional[str]:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception:
        return None

def save_text_file(data: str, file_path: Path) -> bool:
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(data)
        return True
    except Exception:
        return False

# === jjson.py ===
def j_dumps(data: Any, file_path: Path, mode: str = 'w') -> bool:
    try:
        with open(file_path, mode, encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False

def j_loads(file_path: Path) -> Optional[Any]:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None

# === image.py ===
def get_image_bytes(image_path: Path) -> Optional[bytes]:
    try:
        with open(image_path, "rb") as f:
            return f.read()
    except Exception:
        return None

# === printer.py (упрощённый) ===
def pprint(*args, **kwargs):
    import FreeCAD
    msg = " ".join(str(a) for a in args)
    FreeCAD.Console.PrintMessage(f"[PPRINT] {msg}\n")