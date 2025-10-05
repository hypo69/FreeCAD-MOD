## \file AIAssistant/ai_assistant_workbench.py
# -*- coding: utf-8 -*-
#! .pyenv/bin/python3

"""
Рабочая среда AI Assistant для FreeCAD.
Интеграция с Google Gemini для анализа изображений и генерации 3D-моделей.
"""

import FreeCAD
import FreeCADGui
import os
import shutil
import zipfile
import json
import datetime
from pathlib import Path
from typing import Optional
from PySide import QtGui, QtCore
from AIAssistant.settings_dialog import SettingsDialog

# === ГЛОБАЛЬНЫЕ ПУТИ ===
AI_DATA_DIR: Path = Path(FreeCAD.getUserAppDataDir()) / "AIAssistant" / "data"
AI_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Импорт проекта
try:
    from AIAssistant.project_manager import AIProject
    project: Optional[AIProject] = AIProject()
except Exception as ex:
    FreeCAD.Console.PrintError(f"[AIAssistant] Project manager error: {ex}\n")
    project = None

# === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===
def get_image_files() -> list[str]:
    """Функция возвращает список файлов изображений в директории AI_DATA_DIR."""
    exts = {'.png', '.jpg', '.jpeg', '.bmp', '.svg', '.gif'}
    return sorted([f for f in os.listdir(AI_DATA_DIR) if Path(f).suffix.lower() in exts])

def get_text_files() -> list[str]:
    """Функция возвращает список текстовых файлов в директории AI_DATA_DIR."""
    exts = {'.txt', '.md'}
    return sorted([f for f in os.listdir(AI_DATA_DIR) if Path(f).suffix.lower() in exts])

def safe_remove(filepath: Path) -> bool:
    """Функция удаляет файл и возвращает статус операции."""
    try:
        os.remove(filepath)
        return True
    except Exception as ex:
        FreeCAD.Console.PrintError(f"[AIAssistant] Delete error: {ex}\n")
        return False

def save_ai_response_to_history(prompt: str, response: str) -> None:
    """Функция сохраняет диалог (prompt + response) в историю."""
    history_dir: Path = AI_DATA_DIR / "ai_history"
    history_dir.mkdir(parents=True, exist_ok=True)
    timestamp: str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename: str = f"ai_response_{timestamp}.json"
    filepath: Path = history_dir / filename
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": timestamp,
                "prompt": prompt,
                "response": response,
                "provider": "gemini"
            }, f, ensure_ascii=False, indent=2)
        FreeCAD.Console.PrintMessage(f"[AIAssistant] Response saved to history: {filename}\n")
    except Exception as ex:
        FreeCAD.Console.PrintError(f"[AIAssistant] Failed to save history: {ex}\n")

# === КОМАНДЫ ===
class LoadImageCommand:
    """Команда загрузки изображений в рабочую директорию AIAssistant."""

    def GetResources(self) -> dict[str, str]:
        """Функция возвращает ресурсы для отображения команды."""
        icon_path: str = os.path.join(os.path.dirname(__file__), "Resources", "icons", "load_image.svg")
        return {"MenuText": "Load Image", "ToolTip": "Load image into AI workspace", "Pixmap": icon_path}

    def Activated(self) -> None:
        """Функция отправляет связанный контент в выбранный ИИ-провайдер."""
        if project is None or not project.get_all_links():
            QtGui.QMessageBox.information(None, "No Data", "First link an image to a text using 'Link Content'.")
            return

        links = project.get_all_links()
        image_file, text_file = next(iter(links.items()))
        image_path: Path = AI_DATA_DIR / image_file
        text_path: Path = AI_DATA_DIR / text_file

        if not text_path.exists():
            QtGui.QMessageBox.critical(None, "Error", f"Text file not found: {text_path}")
            return

        try:
            with open(text_path, 'r', encoding='utf-8') as f:
                prompt: str = f.read()
        except Exception as ex:
            QtGui.QMessageBox.critical(None, "Error", f"Cannot read text file:\n{str(ex)}")
            return

        FreeCAD.Console.PrintMessage("[AIAssistant] Sending to AI...\n")
        try:
            from AIAssistant.ai_client import AIClient
            client = AIClient()
            response: str = client.ask(prompt, str(image_path))
        except Exception as ex:
            response = f"AI client error: {str(ex)}"

        save_ai_response_to_history(prompt, response)
        dialog = AIResponseDialog(prompt, response)
        dialog.exec_()

        def IsActive(self) -> bool:
            """Функция возвращает True, если команда активна."""
            return True

class LoadTextCommand:
    """Команда загрузки или создания текстового файла."""

    def GetResources(self) -> dict[str, str]:
        """Функция возвращает ресурсы для отображения команды."""
        icon_path: str = os.path.join(os.path.dirname(__file__), "Resources", "icons", "load_text.svg")
        return {"MenuText": "Load Text", "ToolTip": "Load or write text (Markdown)", "Pixmap": icon_path}

    def Activated(self) -> None:
        """Функция открывает диалог редактора текста."""
        dialog = TextEditorDialog()
        dialog.exec_()

    def IsActive(self) -> bool:
        """Функция возвращает True, если команда активна."""
        return True

class LinkContentCommand:
    """Команда связывания изображения с текстовым описанием."""

    def GetResources(self) -> dict[str, str]:
        """Функция возвращает ресурсы для отображения команды."""
        icon_path: str = os.path.join(os.path.dirname(__file__), "Resources", "icons", "link_content.svg")
        return {"MenuText": "Link Content", "ToolTip": "Link image to text description", "Pixmap": icon_path}

    def Activated(self) -> None:
        """Функция открывает диалог связывания контента."""
        if project is None:
            QtGui.QMessageBox.critical(None, "Error", "Project manager not available.")
            return
        dialog = LinkContentDialog()
        dialog.exec_()

    def IsActive(self) -> bool:
        """Функция возвращает True, если команда активна."""
        return project is not None

class ManageContentCommand:
    """Команда управления загруженным контентом."""

    def GetResources(self) -> dict[str, str]:
        """Функция возвращает ресурсы для отображения команды."""
        icon_path: str = os.path.join(os.path.dirname(__file__), "Resources", "icons", "manage_content.svg")
        return {"MenuText": "Manage Content", "ToolTip": "View and edit your files", "Pixmap": icon_path}

    def Activated(self) -> None:
        """Функция открывает диалог управления контентом."""
        dialog = ContentManagerDialog()
        dialog.exec_()

    def IsActive(self) -> bool:
        """Функция возвращает True, если команда активна."""
        return True

class AISettingsCommand:
    """Команда открытия настроек ИИ-провайдера."""

    def GetResources(self) -> dict[str, str]:
        """Функция возвращает ресурсы для отображения команды."""
        return {"MenuText": "AI Settings", "ToolTip": "Configure AI provider and API key"}

    def Activated(self) -> None:
        """Функция открывает диалог настроек."""
        from AIAssistant.settings_dialog import SettingsDialog
        dialog = SettingsDialog()
        dialog.exec_()

    def IsActive(self) -> bool:
        """Функция возвращает True, если команда активна."""
        return True

class AskAICommand:
    """Команда отправки запроса в Google Gemini."""

    def GetResources(self) -> dict[str, str]:
        """Функция возвращает ресурсы для отображения команды."""
        icon_path: str = os.path.join(os.path.dirname(__file__), "Resources", "icons", "ai_chat.svg")
        return {"MenuText": "Ask AI", "ToolTip": "Send linked image+text to Google Gemini", "Pixmap": icon_path}

    def Activated(self) -> None:
        """Функция отправляет связанный контент в Google Gemini."""
        if project is None or not project.get_all_links():
            QtGui.QMessageBox.information(None, "No Data", "First link an image to a text using 'Link Content'.")
            return

        settings = QtCore.QSettings("FreeCAD", "AIAssistant")
        api_key: str = settings.value("api_key", "")
        if not api_key:
            QtGui.QMessageBox.critical(None, "Error", "Gemini API key not set. Go to AI Settings.")
            return

        links = project.get_all_links()
        image_file, text_file = next(iter(links.items()))
        image_path: Path = AI_DATA_DIR / image_file
        text_path: Path = AI_DATA_DIR / text_file

        if not text_path.exists():
            QtGui.QMessageBox.critical(None, "Error", f"Text file not found: {text_path}")
            return

        try:
            with open(text_path, 'r', encoding='utf-8') as f:
                prompt: str = f.read()
        except Exception as ex:
            QtGui.QMessageBox.critical(None, "Error", f"Cannot read text file:\n{str(ex)}")
            return

        FreeCAD.Console.PrintMessage("[AIAssistant] Sending to Google Gemini...\n")
        response: str = "Failed to get response."

        try:
            from AIAssistant.gemini import GoogleGenerativeAi
            llm = GoogleGenerativeAi(api_key=api_key)
            response = llm.ask(q=prompt, image_path=str(image_path), attempts=5)
            if response is None:
                response = "Gemini returned empty response."
        except Exception as ex:
            response = f"Gemini error: {str(ex)}"

        save_ai_response_to_history(prompt, response)
        dialog = AIResponseDialog(prompt, response)
        dialog.exec_()

    def IsActive(self) -> bool:
        """Функция возвращает True, если команда активна."""
        return True

class Generate3DCommand:
    """Команда генерации 3D-объекта по текстовому описанию."""

    def GetResources(self) -> dict[str, str]:
        """Функция возвращает ресурсы для отображения команды."""
        return {"MenuText": "Generate 3D from AI", "ToolTip": "Create 3D object based on AI description"}

    def Activated(self) -> None:
        """Функция создаёт 3D-объект по описанию."""
        text, ok = QtGui.QInputDialog.getMultiLineText(
            None, "Generate 3D", "Enter object description:", "Box 50x30x20 mm"
        )
        if not ok or not text.strip():
            return
        try:
            doc = FreeCAD.ActiveDocument or FreeCAD.newDocument("AI_Generated")
            if "box" in text.lower() or "короб" in text.lower():
                import re
                nums = list(map(float, re.findall(r'\d+\.?\d*', text)))
                if len(nums) >= 3:
                    l, w, h = nums[0], nums[1], nums[2]
                    box = doc.addObject("Part::Box", "AI_Box")
                    box.Length = l
                    box.Width = w
                    box.Height = h
                    doc.recompute()
                    FreeCAD.Console.PrintMessage(f"[AIAssistant] Created box: {l}x{w}x{h}\n")
                else:
                    QtGui.QMessageBox.warning(None, "Parse Error", "Need 3 dimensions for box.")
            else:
                QtGui.QMessageBox.information(None, "Not Implemented", "Only 'box' supported now.")
        except Exception as ex:
            QtGui.QMessageBox.critical(None, "Error", f"3D generation failed:\n{str(ex)}")

    def IsActive(self) -> bool:
        """Функция возвращает True, если команда активна."""
        return True

class ExportProjectCommand:
    """Команда экспорта проекта в ZIP-архив."""

    def GetResources(self) -> dict[str, str]:
        """Функция возвращает ресурсы для отображения команды."""
        return {"MenuText": "Export Project", "ToolTip": "Export all data as ZIP"}

    def Activated(self) -> None:
        """Функция создаёт ZIP-архив с данными проекта."""
        zip_path, _ = QtGui.QFileDialog.getSaveFileName(None, "Save Project", "", "ZIP Files (*.zip)")
        if not zip_path:
            return
        if not zip_path.endswith(".zip"):
            zip_path += ".zip"
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                root_dir = AI_DATA_DIR.parent
                for root, dirs, files in os.walk(AI_DATA_DIR):
                    for file in files:
                        full_path = Path(root) / file
                        arc_path = full_path.relative_to(root_dir)
                        zf.write(full_path, arc_path)
            QtGui.QMessageBox.information(None, "Success", f"Project exported to:\n{zip_path}")
        except Exception as ex:
            QtGui.QMessageBox.critical(None, "Error", f"Export failed:\n{str(ex)}")

    def IsActive(self) -> bool:
        """Функция возвращает True, если команда активна."""
        return True

# === ДИАЛОГИ ===
# (TextEditorDialog, LinkContentDialog, ContentManagerDialog, AIResponseDialog — без изменений, как в предыдущих версиях)
# ... (оставлены без изменений для краткости; при необходимости могу предоставить полную версию)

# === РАБОЧАЯ СРЕДА ===
class AIAssistantWorkbench(FreeCADGui.Workbench):
    """Рабочая среда AI Assistant."""

    MenuText = "AI Assistant"
    ToolTip = "Google Gemini-powered design assistant"

    def __init__(self) -> None:
        """Функция инициализирует иконку рабочей среды."""
        self.Icon = os.path.join(os.path.dirname(__file__), "Resources", "icons", "ai_assistant.svg")

    def Initialize(self) -> None:
        """Функция регистрирует команды в интерфейсе."""
        self.list = [
            "LoadImageCommand",
            "LoadTextCommand",
            "LinkContentCommand",
            "ManageContentCommand",
            "AskAICommand",
            "Generate3DCommand",
            "AISettingsCommand",
            "ExportProjectCommand"
        ]
        self.appendToolbar("AI Tools", self.list)
        self.appendMenu("AI Assistant", self.list)

    def GetClassName(self) -> str:
        """Функция возвращает имя класса рабочей среды."""
        return "Gui::PythonWorkbench"

# === РЕГИСТРАЦИЯ ===
FreeCADGui.addCommand("LoadImageCommand", LoadImageCommand())
FreeCADGui.addCommand("LoadTextCommand", LoadTextCommand())
FreeCADGui.addCommand("LinkContentCommand", LinkContentCommand())
FreeCADGui.addCommand("ManageContentCommand", ManageContentCommand())
FreeCADGui.addCommand("AskAICommand", AskAICommand())
FreeCADGui.addCommand("Generate3DCommand", Generate3DCommand())
FreeCADGui.addCommand("AISettingsCommand", AISettingsCommand())
FreeCADGui.addCommand("ExportProjectCommand", ExportProjectCommand())