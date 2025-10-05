# ai_assistant_workbench.py
import FreeCAD, FreeCADGui
import os
import shutil
from pathlib import Path
from PySide import QtGui, QtCore

# Папка для всех данных AIAssistant
AI_DATA_DIR = os.path.join(FreeCAD.getUserAppDataDir(), "AIAssistant", "data")
os.makedirs(AI_DATA_DIR, exist_ok=True)

# === КОМАНДА: ЗАГРУЗКА ИЗОБРАЖЕНИЯ (из Части 1) ===
class LoadImageCommand:
    def GetResources(self):
        icon_path = os.path.join(os.path.dirname(__file__), "Resources", "icons", "load_image.svg")
        return {
            "MenuText": "Load Image",
            "ToolTip": "Load image (PNG, JPG, SVG) into AI workspace",
            "Pixmap": icon_path
        }

    def Activated(self):
        files, _ = QtGui.QFileDialog.getOpenFileNames(
            None,
            "Select Image Files",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.svg *.gif)"
        )
        if not files:
            return

        for src in files:
            self._copy_file_safe(src)

    def _copy_file_safe(self, src):
        filename = os.path.basename(src)
        dst = os.path.join(AI_DATA_DIR, filename)
        if os.path.exists(dst):
            name, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(os.path.join(AI_DATA_DIR, f"{name}_{counter}{ext}")):
                counter += 1
            dst = os.path.join(AI_DATA_DIR, f"{name}_{counter}{ext}")
        try:
            shutil.copy2(src, dst)
            FreeCAD.Console.PrintMessage(f"[AIAssistant] Saved: {dst}\n")
        except Exception as e:
            FreeCAD.Console.PrintError(f"[AIAssistant] Copy error: {str(e)}\n")
            QtGui.QMessageBox.critical(None, "Error", f"Failed to copy:\n{str(e)}")

    def IsActive(self):
        return True


# === КОМАНДА: ЗАГРУЗКА ТЕКСТА ===
class LoadTextCommand:
    def GetResources(self):
        icon_path = os.path.join(os.path.dirname(__file__), "Resources", "icons", "load_text.svg")
        return {
            "MenuText": "Load Text",
            "ToolTip": "Load or write text (Markdown, plain text)",
            "Pixmap": icon_path
        }

    def Activated(self):
        dialog = TextEditorDialog()
        dialog.exec_()

    def IsActive(self):
        return True


# === ДИАЛОГ: РЕДАКТОР ТЕКСТА ===
class TextEditorDialog(QtGui.QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Assistant — Text Editor")
        self.resize(600, 500)

        # Текстовое поле с поддержкой Markdown (визуально — обычный текст)
        self.text_edit = QtGui.QTextEdit()
        self.text_edit.setAcceptRichText(False)  # Только plain text (Markdown — это текст!)
        self.text_edit.setFont(QtGui.QFont("Courier", 10))

        # Кнопки
        self.load_file_btn = QtGui.QPushButton("Load File (.txt, .md)")
        self.save_btn = QtGui.QPushButton("Save as Markdown")
        self.cancel_btn = QtGui.QPushButton("Cancel")

        self.load_file_btn.clicked.connect(self.load_file)
        self.save_btn.clicked.connect(self.save_text)
        self.cancel_btn.clicked.connect(self.reject)

        # Раскладка
        btn_layout = QtGui.QHBoxLayout()
        btn_layout.addWidget(self.load_file_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(QtGui.QLabel("Enter or load your prompt, notes, or instructions (Markdown supported):"))
        layout.addWidget(self.text_edit)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def load_file(self):
        file_path, _ = QtGui.QFileDialog.getOpenFileName(
            self,
            "Open Text File",
            "",
            "Text Files (*.txt *.md);;All Files (*)"
        )
        if not file_path:
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.text_edit.setPlainText(content)
            FreeCAD.Console.PrintMessage(f"[AIAssistant] Loaded: {file_path}\n")
        except Exception as e:
            QtGui.QMessageBox.critical(self, "Load Error", f"Cannot read file:\n{str(e)}")

    def save_text(self):
        text = self.text_edit.toPlainText().strip()
        if not text:
            QtGui.QMessageBox.warning(self, "Warning", "Text is empty!")
            return

        # Генерируем имя файла: ai_prompt_1.md, ai_prompt_2.md...
        base_name = "ai_prompt"
        ext = ".md"
        counter = 1
        while os.path.exists(os.path.join(AI_DATA_DIR, f"{base_name}_{counter}{ext}")):
            counter += 1
        filename = f"{base_name}_{counter}{ext}"
        filepath = os.path.join(AI_DATA_DIR, filename)

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(text)
            FreeCAD.Console.PrintMessage(f"[AIAssistant] Text saved: {filepath}\n")
            QtGui.QMessageBox.information(self, "Saved", f"Text saved as:\n{filename}")
            self.accept()
        except Exception as e:
            QtGui.QMessageBox.critical(self, "Save Error", f"Cannot save file:\n{str(e)}")


# === РАБОЧАЯ СРЕДА ===
class AIAssistantWorkbench(FreeCADGui.Workbench):
    MenuText = "AI Assistant"
    ToolTip = "AI design assistant: images + text"

    def __init__(self):
        self.Icon = os.path.join(os.path.dirname(__file__), "Resources", "icons", "ai_assistant.svg")

    def Initialize(self):
        self.list = ["LoadImageCommand", "LoadTextCommand"]
        self.appendToolbar("AI Tools", self.list)
        self.appendMenu("AI Assistant", self.list)

    def GetClassName(self):
        return "Gui::PythonWorkbench"


# === РЕГИСТРАЦИЯ КОМАНД ===
FreeCADGui.addCommand("LoadImageCommand", LoadImageCommand())
FreeCADGui.addCommand("LoadTextCommand", LoadTextCommand())