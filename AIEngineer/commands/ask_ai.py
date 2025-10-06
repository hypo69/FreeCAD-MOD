# -*- coding: utf-8 -*-
"""
Команда отправки связанного изображения и текстового описания в Google Gemini.
"""

import FreeCAD
from PySide import QtGui, QtCore
from ..utils import get_icon, AI_DATA_DIR, save_ai_response_to_history
from ..project_manager import AIProject

# Пытаемся получить экземпляр проекта (с обработкой ошибок)
try:
    project = AIProject()
except Exception as ex:
    FreeCAD.Console.PrintError(f"[AIEngineer] Failed to initialize project manager in ask_ai: {ex}\n")
    project = None

class AskAICommand:
    """Команда отправки запроса в Google Gemini с изображением и текстом."""

    def GetResources(self):
        return {
            "MenuText": "Ask AI",
            "ToolTip": "Send linked image+text to Google Gemini",
            "Pixmap": get_icon("ai_chat.svg")
        }

    def Activated(self):
        if project is None or not project.get_all_links():
            QtGui.QMessageBox.information(
                None, "No Data", "First link an image to a text using 'Link Content'."
            )
            return

        # Загружаем API-ключ из настроек
        settings = QtCore.QSettings("FreeCAD", "AIEngineer")
        api_key = settings.value("api_key", "")
        if not api_key:
            QtGui.QMessageBox.critical(
                None, "Error", "Gemini API key not set. Go to AI Settings."
            )
            return

        # Берём первую доступную связку (image → text)
        links = project.get_all_links()
        image_file, text_file = next(iter(links.items()))
        image_path = AI_DATA_DIR / image_file
        text_path = AI_DATA_DIR / text_file

        if not text_path.exists():
            QtGui.QMessageBox.critical(None, "Error", f"Text file not found: {text_path}")
            return

        # Читаем текстовый промпт
        try:
            with open(text_path, 'r', encoding='utf-8') as f:
                prompt = f.read()
        except Exception as ex:
            QtGui.QMessageBox.critical(None, "Error", f"Cannot read text file:\n{str(ex)}")
            return

        FreeCAD.Console.PrintMessage("[AIEngineer] Sending to Google Gemini...\n")
        response = "Failed to get response."

        # Отправляем запрос в Gemini
        try:
            from ..gemini import GoogleGenerativeAi
            # Используем стабильную модель вместо экспериментальной
            llm = GoogleGenerativeAi(api_key=api_key, model_name='gemini-1.5-flash')
            gemini_response = llm.ask(q=prompt, image_path=str(image_path), attempts=5)
            response = gemini_response if gemini_response is not None else "Gemini returned empty response."
        except Exception as ex:
            response = f"Gemini error: {str(ex)}"

        # Сохраняем в историю и показываем результат
        save_ai_response_to_history(prompt, response)

        from ..dialogs.ai_response import AIResponseDialog
        dialog = AIResponseDialog(prompt, response)
        dialog.exec_()

    def IsActive(self):
        """Команда активна, только если есть связанные данные."""
        return project is not None and bool(project.get_all_links())