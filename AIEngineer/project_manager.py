# -*- coding: utf-8 -*-
"""
Менеджер проекта AI Engineer: хранит связи между изображениями и текстовыми файлами.
"""

import json
import FreeCAD
from pathlib import Path

# Единый путь к данным — должен совпадать с AI_DATA_DIR из utils.py
AI_DATA_DIR = Path(FreeCAD.getUserAppDataDir()) / "AIEngineer" / "data"
PROJECT_FILE = AI_DATA_DIR / "project.json"

# Создаём директорию при импорте
AI_DATA_DIR.mkdir(parents=True, exist_ok=True)

class AIProject:
    """Управляет связями: изображение ↔ текстовый промпт."""

    def __init__(self):
        self.data = self._load()

    def _load(self):
        """Загружает проект из JSON-файла или создаёт новый."""
        if PROJECT_FILE.exists():
            try:
                with open(PROJECT_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as ex:
                FreeCAD.Console.PrintError(f"[AIEngineer] Failed to load project.json: {ex}\n")
        return {"links": {}}  # {"image.png": "prompt_1.md"}

    def save(self):
        """Сохраняет текущее состояние проекта в файл."""
        try:
            with open(PROJECT_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception as ex:
            FreeCAD.Console.PrintError(f"[AIEngineer] Failed to save project.json: {ex}\n")

    def link_text_to_image(self, image_file: str, text_file: str) -> None:
        """Связывает изображение с текстовым файлом."""
        self.data["links"][image_file] = text_file
        self.save()

    def unlink_image(self, image_file: str) -> None:
        """Отвязывает изображение от текста."""
        if image_file in self.data["links"]:
            del self.data["links"][image_file]
            self.save()

    def unlink_text(self, text_file: str) -> None:
        """Отвязывает ВСЕ изображения, ссылающиеся на данный текстовый файл."""
        images_to_unlink = [
            img for img, txt in self.data["links"].items() if txt == text_file
        ]
        for img in images_to_unlink:
            del self.data["links"][img]
        if images_to_unlink:
            self.save()

    def get_linked_text(self, image_file: str) -> str | None:
        """Возвращает имя текстового файла, связанного с изображением."""
        return self.data["links"].get(image_file)

    def get_all_links(self) -> dict[str, str]:
        """Возвращает копию всех связей."""
        return self.data["links"].copy()

    def is_image_linked(self, image_file: str) -> bool:
        """Проверяет, связано ли изображение с каким-либо текстом."""
        return image_file in self.data["links"]