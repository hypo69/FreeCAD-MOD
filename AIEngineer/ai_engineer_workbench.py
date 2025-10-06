## \file AIEngineer/ai_engineer_workbench.py
# -*- coding: utf-8 -*-
#! .pyenv/bin/python3

"""
Рабочая среда AI Engineer для FreeCAD.
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
from AIEngineer.gemini import GoogleGenerativeAi

# === ГЛОБАЛЬНЫЕ ПУТИ ===
AI_DATA_DIR: Path = Path(FreeCAD.getUserAppDataDir()) / "AIEngineer" / "data"
AI_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Импорт проекта
try:
    from AIEngineer.project_manager import AIProject
    project: Optional[AIProject] = AIProject()
except Exception as ex:
    FreeCAD.Console.PrintError(f"[AIEngineer] Project manager error: {ex}\n")
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
        FreeCAD.Console.PrintError(f"[AIEngineer] Delete error: {ex}\n")
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
        FreeCAD.Console.PrintMessage(f"[AIEngineer] Response saved to history: {filename}\n")
    except Exception as ex:
        FreeCAD.Console.PrintError(f"[AIEngineer] Failed to save history: {ex}\n")

# === КОМАНДЫ ===
class LoadImageCommand:
    """Команда загрузки изображений в рабочую директорию AIEngineer."""

    def GetResources(self) -> dict[str, str]:
        """Функция возвращает ресурсы для отображения команды."""
        return {"MenuText": "Load Image", "ToolTip": "Load image into AI workspace", "Pixmap": "load_image.svg"}

    def Activated(self) -> None:
        """Функция выполняет загрузку выбранных изображений."""
        files, _ = QtGui.QFileDialog.getOpenFileNames(None, "Select Images", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.svg *.gif)")
        if not files:
            return
        for src in files:
            filename: str = os.path.basename(src)
            dst: Path = AI_DATA_DIR / filename
            if dst.exists():
                name, ext = os.path.splitext(filename)
                counter: int = 1
                while (AI_DATA_DIR / f"{name}_{counter}{ext}").exists():
                    counter += 1
                dst = AI_DATA_DIR / f"{name}_{counter}{ext}"
            try:
                shutil.copy2(src, dst)
                FreeCAD.Console.PrintMessage(f"[AIEngineer] Saved: {dst}\n")
            except Exception as ex:
                QtGui.QMessageBox.critical(None, "Error", f"Failed to copy:\n{str(ex)}")

    def IsActive(self) -> bool:
        """Функция возвращает True, если команда активна."""
        return True

class LoadTextCommand:
    """Команда загрузки или создания текстового файла."""

    def GetResources(self) -> dict[str, str]:
        """Функция возвращает ресурсы для отображения команды."""
        return {"MenuText": "Load Text", "ToolTip": "Load or write text (Markdown)", "Pixmap": "load_text.svg"}

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
        return {"MenuText": "Link Content", "ToolTip": "Link image to text description", "Pixmap": "link_content.svg"}

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
        return {"MenuText": "Manage Content", "ToolTip": "View and edit your files", "Pixmap": "manage_content.svg"}

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
        from AIEngineer.settings_dialog import SettingsDialog
        dialog = SettingsDialog()
        dialog.exec_()

    def IsActive(self) -> bool:
        """Функция возвращает True, если команда активна."""
        return True

class AskAICommand:
    """Команда отправки запроса в Google Gemini."""

    def GetResources(self) -> dict[str, str]:
        """Функция возвращает ресурсы для отображения команды."""
        return {"MenuText": "Ask AI", "ToolTip": "Send linked image+text to Google Gemini", "Pixmap": "ai_chat.svg"}

    def Activated(self) -> None:
        """Функция отправляет связанный контент в Google Gemini."""
        if project is None or not project.get_all_links():
            QtGui.QMessageBox.information(None, "No Data", "First link an image to a text using 'Link Content'.")
            return

        settings = QtCore.QSettings("FreeCAD", "AIEngineer")
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

        FreeCAD.Console.PrintMessage("[AIEngineer] Sending to Google Gemini...\n")
        response: str = "Failed to get response."

        try:
            from AIEngineer.ai_client import GoogleGenerativeAi
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
                    FreeCAD.Console.PrintMessage(f"[AIEngineer] Created box: {l}x{w}x{h}\n")
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
class TextEditorDialog(QtGui.QDialog):
    """Диалог редактирования текста."""

    def __init__(self, filepath: Optional[Path] = None):
        super().__init__()
        self.filepath = filepath
        self.setWindowTitle("Edit Text" if filepath else "New Text")
        self.resize(600, 500)
        self.text_edit = QtGui.QTextEdit()
        self.text_edit.setAcceptRichText(False)
        self.text_edit.setFont(QtGui.QFont("Courier", 10))
        if filepath and filepath.exists():
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    self.text_edit.setPlainText(f.read())
            except Exception as ex:
                QtGui.QMessageBox.critical(self, "Load Error", str(ex))
                return
        save_btn = QtGui.QPushButton("Save")
        cancel_btn = QtGui.QPushButton("Cancel")
        save_btn.clicked.connect(self.save_text)
        cancel_btn.clicked.connect(self.reject)
        btn_layout = QtGui.QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout = QtGui.QVBoxLayout()
        layout.addWidget(QtGui.QLabel("Enter your prompt (Markdown supported):"))
        layout.addWidget(self.text_edit)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def save_text(self) -> None:
        """Функция сохраняет текст в файл."""
        text = self.text_edit.toPlainText().strip()
        if not text:
            QtGui.QMessageBox.warning(self, "Warning", "Text is empty!")
            return
        if self.filepath:
            filepath = self.filepath
        else:
            base_name = "ai_prompt"
            ext = ".md"
            counter = 1
            while (AI_DATA_DIR / f"{base_name}_{counter}{ext}").exists():
                counter += 1
            filepath = AI_DATA_DIR / f"{base_name}_{counter}{ext}"
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(text)
            FreeCAD.Console.PrintMessage(f"[AIEngineer] Saved: {filepath}\n")
            QtGui.QMessageBox.information(self, "Saved", "Text saved successfully!")
            self.accept()
        except Exception as ex:
            QtGui.QMessageBox.critical(self, "Save Error", str(ex))

class LinkContentDialog(QtGui.QDialog):
    """Диалог связывания изображения и текста."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Link Image and Text")
        self.resize(600, 400)
        self.image_list = QtGui.QListWidget()
        self.text_list = QtGui.QListWidget()
        self.refresh_lists()
        self.link_btn = QtGui.QPushButton("→ Link Selected")
        self.link_btn.clicked.connect(self.link_selected)
        layout = QtGui.QHBoxLayout()
        layout.addWidget(QtGui.QLabel("Images:"))
        layout.addWidget(self.image_list)
        layout.addWidget(self.link_btn)
        layout.addWidget(QtGui.QLabel("Texts:"))
        layout.addWidget(self.text_list)
        close_btn = QtGui.QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        main_layout = QtGui.QVBoxLayout()
        main_layout.addLayout(layout)
        main_layout.addWidget(close_btn)
        self.setLayout(main_layout)

    def refresh_lists(self) -> None:
        """Функция обновляет списки изображений и текстов."""
        self.image_list.clear()
        self.text_list.clear()
        for f in get_image_files():
            item = QtGui.QListWidgetItem(f)
            if project and project.is_image_linked(f):
                item.setForeground(QtGui.QColor("green"))
            self.image_list.addItem(item)
        for f in get_text_files():
            self.text_list.addItem(f)

    def link_selected(self) -> None:
        """Функция связывает выбранные изображение и текст."""
        img_items = self.image_list.selectedItems()
        txt_items = self.text_list.selectedItems()
        if not img_items or not txt_items:
            QtGui.QMessageBox.warning(self, "Selection", "Select one image and one text file.")
            return
        image_file = img_items[0].text()
        text_file = txt_items[0].text()
        project.link_text_to_image(image_file, text_file)
        FreeCAD.Console.PrintMessage(f"[AIEngineer] Linked: {image_file} ↔ {text_file}\n")
        self.refresh_lists()

class ContentManagerDialog(QtGui.QDialog):
    """Диалог управления контентом."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Engineer — Content Manager")
        self.resize(700, 500)
        self.tabs = QtGui.QTabWidget()
        self.image_tab = self.create_image_tab()
        self.text_tab = self.create_text_tab()
        self.tabs.addTab(self.image_tab, "Images")
        self.tabs.addTab(self.text_tab, "Texts")
        close_btn = QtGui.QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.tabs)
        layout.addWidget(close_btn)
        self.setLayout(layout)

    def create_image_tab(self) -> QtGui.QWidget:
        """Функция создаёт вкладку для изображений."""
        widget = QtGui.QWidget()
        layout = QtGui.QVBoxLayout()
        self.image_list = QtGui.QListWidget()
        self.image_list.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.refresh_image_list()
        self.link_btn = QtGui.QPushButton("Link to Text")
        self.unlink_btn = QtGui.QPushButton("Unlink")
        self.link_btn.clicked.connect(self.link_image)
        self.unlink_btn.clicked.connect(self.unlink_image)
        btn_layout = QtGui.QHBoxLayout()
        btn_layout.addWidget(self.link_btn)
        btn_layout.addWidget(self.unlink_btn)
        btn_layout.addStretch()
        layout.addWidget(self.image_list)
        layout.addLayout(btn_layout)
        widget.setLayout(layout)
        return widget

    def create_text_tab(self) -> QtGui.QWidget:
        """Функция создаёт вкладку для текстов."""
        widget = QtGui.QWidget()
        layout = QtGui.QVBoxLayout()
        self.text_list = QtGui.QListWidget()
        self.text_list.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.refresh_text_list()
        edit_btn = QtGui.QPushButton("Edit")
        delete_btn = QtGui.QPushButton("Delete")
        edit_btn.clicked.connect(self.edit_selected_text)
        delete_btn.clicked.connect(self.delete_selected_text)
        btn_layout = QtGui.QHBoxLayout()
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(delete_btn)
        btn_layout.addStretch()
        layout.addWidget(self.text_list)
        layout.addLayout(btn_layout)
        widget.setLayout(layout)
        return widget

    def refresh_image_list(self) -> None:
        """Функция обновляет список изображений."""
        self.image_list.clear()
        for f in get_image_files():
            item = QtGui.QListWidgetItem(f)
            if project and project.is_image_linked(f):
                item.setForeground(QtGui.QColor("green"))
            self.image_list.addItem(item)

    def refresh_text_list(self) -> None:
        """Функция обновляет список текстов."""
        self.text_list.clear()
        for f in get_text_files():
            self.text_list.addItem(f)

    def link_image(self) -> None:
        """Функция связывает изображение с текстом."""
        items = self.image_list.selectedItems()
        if not items or project is None:
            return
        image_file = items[0].text()
        text_files = get_text_files()
        if not text_files:
            QtGui.QMessageBox.information(self, "No Texts", "No text files available.")
            return
        text_file, ok = QtGui.QInputDialog.getItem(self, "Link Text", "Select text file:", text_files, 0, False)
        if ok and text_file:
            project.link_text_to_image(image_file, text_file)
            FreeCAD.Console.PrintMessage(f"[AIEngineer] Linked: {image_file} ↔ {text_file}\n")
            self.refresh_image_list()

    def unlink_image(self) -> None:
        """Функция отвязывает изображение от текста."""
        items = self.image_list.selectedItems()
        if not items or project is None:
            return
        image_file = items[0].text()
        if project.is_image_linked(image_file):
            project.unlink_image(image_file)
            FreeCAD.Console.PrintMessage(f"[AIEngineer] Unlinked: {image_file}\n")
            self.refresh_image_list()

    def edit_selected_text(self) -> None:
        """Функция редактирует выбранный текст."""
        items = self.text_list.selectedItems()
        if not items:
            return
        filename = items[0].text()
        filepath = AI_DATA_DIR / filename
        dialog = TextEditorDialog(filepath)
        dialog.exec_()
        self.refresh_text_list()

    def delete_selected_text(self) -> None:
        """Функция удаляет выбранный текст."""
        items = self.text_list.selectedItems()
        if not items:
            return
        filename = items[0].text()
        if QtGui.QMessageBox.question(self, "Confirm", f"Delete '{filename}'?", QtGui.QMessageBox.Yes | QtGui.QMessageBox.No) != QtGui.QMessageBox.Yes:
            return
        filepath = AI_DATA_DIR / filename
        if safe_remove(filepath):
            FreeCAD.Console.PrintMessage(f"[AIEngineer] Deleted: {filename}\n")
            self.refresh_text_list()

class AIResponseDialog(QtGui.QDialog):
    """Диалог отображения ответа от ИИ."""

    def __init__(self, prompt: str, response: str):
        super().__init__()
        self.setWindowTitle("AI Engineer — Response from Gemini")
        self.resize(700, 500)
        layout = QtGui.QVBoxLayout()
        layout.addWidget(QtGui.QLabel("<b>Your prompt:</b>"))
        prompt_edit = QtGui.QTextEdit()
        prompt_edit.setPlainText(prompt)
        prompt_edit.setReadOnly(True)
        layout.addWidget(prompt_edit)
        layout.addWidget(QtGui.QLabel("<b>Gemini Response:</b>"))
        response_edit = QtGui.QTextEdit()
        response_edit.setPlainText(str(response))
        response_edit.setReadOnly(True)
        layout.addWidget(response_edit)
        copy_btn = QtGui.QPushButton("Copy Response")
        close_btn = QtGui.QPushButton("Close")
        copy_btn.clicked.connect(lambda: QtGui.QApplication.clipboard().setText(str(response)))
        close_btn.clicked.connect(self.accept)
        btn_layout = QtGui.QHBoxLayout()
        btn_layout.addWidget(copy_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

# === РАБОЧАЯ СРЕДА ===
class AIEngineerWorkbench(FreeCADGui.Workbench):
    """Рабочая среда AI Engineer."""

    MenuText = "AI Engineer"
    ToolTip = "Google Gemini-powered design assistant for engineers"

    def __init__(self) -> None:
        """Функция инициализирует иконку рабочей среды."""
        self.Icon = "ai_engineer.svg"

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
        self.appendMenu("AI Engineer", self.list)

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