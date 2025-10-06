# -*- coding: utf-8 -*-
"""
Вспомогательные функции и общие константы для AIEngineer.
"""

import FreeCAD
import os
import json
import datetime
from pathlib import Path
from typing import Optional

# Единый путь к данным аддона — используется ВЕЗДЕ
AI_DATA_DIR: Path = Path(FreeCAD.getUserAppDataDir()) / "AIEngineer" / "data"
AI_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Путь к иконкам
ICON_PATH: str = str(Path(__file__).parent / "Resources" / "icons")

def get_icon(icon_name: str) -> str:
    """
    Возвращает полный путь к иконке или пустую строку, если файл не найден.
    """
    icon_file = os.path.join(ICON_PATH, icon_name)
    if os.path.exists(icon_file):
        return icon_file
    FreeCAD.Console.PrintWarning(f"[AIEngineer] Icon not found: {icon_file}\n")
    return ""

def get_image_files() -> list[str]:
    """Возвращает список изображений в AI_DATA_DIR."""
    exts = {'.png', '.jpg', '.jpeg', '.bmp', '.svg', '.gif'}
    return sorted([
        f for f in os.listdir(AI_DATA_DIR)
        if Path(f).suffix.lower() in exts
    ])

def get_text_files() -> list[str]:
    """Возвращает список текстовых файлов в AI_DATA_DIR."""
    exts = {'.txt', '.md'}
    return sorted([
        f for f in os.listdir(AI_DATA_DIR)
        if Path(f).suffix.lower() in exts
    ])

def safe_remove(filepath: Path) -> bool:
    """Безопасное удаление файла."""
    try:
        os.remove(filepath)
        return True
    except Exception as ex:
        FreeCAD.Console.PrintError(f"[AIEngineer] Delete error: {ex}\n")
        return False

def save_ai_response_to_history(prompt: str, response: str) -> None:
    """Сохраняет диалог (prompt + response) в историю."""
    history_dir = AI_DATA_DIR / "ai_history"
    history_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = history_dir / f"ai_response_{timestamp}.json"
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": timestamp,
                "prompt": prompt,
                "response": response,
                "provider": "gemini"
            }, f, ensure_ascii=False, indent=2)
        FreeCAD.Console.PrintMessage(f"[AIEngineer] Response saved to history: {filepath.name}\n")
    except Exception as ex:
        FreeCAD.Console.PrintError(f"[AIEngineer] Failed to save history: {ex}\n")