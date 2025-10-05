# ai_assistant_workbench.py
import FreeCAD, FreeCADGui
import os
import shutil
import zipfile
from pathlib import Path
from PySide import QtGui, QtCore

# Импорт менеджера проекта (должен быть в той же папке)
try:
    from AIAssistant.project_manager import AIProject
    project = AIProject()
except Exception as e:
    FreeCAD.Console.PrintError(f"[AIAssistant] Failed to load project manager: {str(e)}\n")
    project = None

# Папка данных
AI_DATA_DIR = os.path.join(FreeCAD.getUserAppDataDir(), "AIAssistant", "data")
os.makedirs(AI_DATA_DIR, exist_ok=True)

# === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===
def get_image_files():
    exts = {'.png', '.jpg', '.jpeg', '.bmp', '.svg', '.gif'}
    return sorted([f for f in os.listdir(AI_DATA_DIR) if Path(f).suffix.lower() in exts])

def get_text_files():
    exts = {'.txt', '.md'}
    return sorted([f for f in os.listdir(AI_DATA_DIR) if Path(f).suffix.lower() in exts])

def safe_remove(filepath):
    try:
        os.remove(filepath)
        return True
    except Exception as e:
        FreeCAD.Console.PrintError(f"[AIAssistant] Delete error: {str(e)}\n")
        return False


# === КОМАНДА: ЗАГРУЗКА ИЗОБРАЖЕНИЯ ===
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
    def __init__(self, filepath=None):
        super().__init__()
        self.filepath = filepath
        self.setWindowTitle("Edit Text" if filepath else "New Text")
        self.resize(600, 500)

        self.text_edit = QtGui.QTextEdit()
        self.text_edit.setAcceptRichText(False)
        self.text_edit.setFont(QtGui.QFont("Courier", 10))

        if filepath:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    self.text_edit.setPlainText(f.read())
            except Exception as e:
                QtGui.QMessageBox.critical(self, "Load Error", str(e))
                return

        self.save_btn = QtGui.QPushButton("Save")
        self.cancel_btn = QtGui.QPushButton("Cancel")
        self.save_btn.clicked.connect(self.save_text)
        self.cancel_btn.clicked.connect(self.reject)

        btn_layout = QtGui.QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(QtGui.QLabel("Enter your prompt or notes (Markdown supported):"))
        layout.addWidget(self.text_edit)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def save_text(self):
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
            while os.path.exists(os.path.join(AI_DATA_DIR, f"{base_name}_{counter}{ext}")):
                counter += 1
            filepath = os.path.join(AI_DATA_DIR, f"{base_name}_{counter}{ext}")

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(text)
            FreeCAD.Console.PrintMessage(f"[AIAssistant] Saved: {filepath}\n")
            QtGui.QMessageBox.information(self, "Saved", "Text saved successfully!")
            self.accept()
        except Exception as e:
            QtGui.QMessageBox.critical(self, "Save Error", str(e))


# === КОМАНДА: СВЯЗЫВАНИЕ КОНТЕНТА ===
class LinkContentCommand:
    def GetResources(self):
        icon_path = os.path.join(os.path.dirname(__file__), "Resources", "icons", "link_content.svg")
        return {
            "MenuText": "Link Content",
            "ToolTip": "Link a text description to an image",
            "Pixmap": icon_path
        }

    def Activated(self):
        if project is None:
            QtGui.QMessageBox.critical(None, "Error", "Project manager not available.")
            return
        dialog = LinkContentDialog()
        dialog.exec_()

    def IsActive(self):
        return project is not None


# === ДИАЛОГ: СВЯЗЫВАНИЕ ===
class LinkContentDialog(QtGui.QDialog):
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

    def refresh_lists(self):
        self.image_list.clear()
        self.text_list.clear()
        for f in get_image_files():
            item = QtGui.QListWidgetItem(f)
            if project and project.is_image_linked(f):
                item.setForeground(QtGui.QColor("green"))
            self.image_list.addItem(item)
        for f in get_text_files():
            self.text_list.addItem(f)

    def link_selected(self):
        img_items = self.image_list.selectedItems()
        txt_items = self.text_list.selectedItems()
        if not img_items or not txt_items:
            QtGui.QMessageBox.warning(self, "Selection", "Select one image and one text file.")
            return
        image_file = img_items[0].text()
        text_file = txt_items[0].text()
        project.link_text_to_image(image_file, text_file)
        FreeCAD.Console.PrintMessage(f"[AIAssistant] Linked: {image_file} ↔ {text_file}\n")
        self.refresh_lists()


# === КОМАНДА: УПРАВЛЕНИЕ КОНТЕНТОМ ===
class ManageContentCommand:
    def GetResources(self):
        icon_path = os.path.join(os.path.dirname(__file__), "Resources", "icons", "manage_content.svg")
        return {
            "MenuText": "Manage Content",
            "ToolTip": "View, edit and delete your AI inputs",
            "Pixmap": icon_path
        }

    def Activated(self):
        dialog = ContentManagerDialog()
        dialog.exec_()

    def IsActive(self):
        return True


# === ДИАЛОГ: УПРАВЛЕНИЕ КОНТЕНТОМ ===
class ContentManagerDialog(QtGui.QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Assistant — Content Manager")
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

    def create_image_tab(self):
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

    def create_text_tab(self):
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

    def refresh_image_list(self):
        self.image_list.clear()
        for f in get_image_files():
            item = QtGui.QListWidgetItem(f)
            if project and project.is_image_linked(f):
                item.setForeground(QtGui.QColor("green"))
            self.image_list.addItem(item)

    def refresh_text_list(self):
        self.text_list.clear()
        for f in get_text_files():
            self.text_list.addItem(f)

    def link_image(self):
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
            FreeCAD.Console.PrintMessage(f"[AIAssistant] Linked: {image_file} ↔ {text_file}\n")
            self.refresh_image_list()

    def unlink_image(self):
        items = self.image_list.selectedItems()
        if not items or project is None:
            return
        image_file = items[0].text()
        if project.is_image_linked(image_file):
            project.unlink_image(image_file)
            FreeCAD.Console.PrintMessage(f"[AIAssistant] Unlinked: {image_file}\n")
            self.refresh_image_list()

    def edit_selected_text(self):
        items = self.text_list.selectedItems()
        if not items:
            return
        filename = items[0].text()
        filepath = os.path.join(AI_DATA_DIR, filename)
        dialog = TextEditorDialog(filepath)
        dialog.exec_()
        self.refresh_text_list()

    def delete_selected_text(self):
        items = self.text_list.selectedItems()
        if not items:
            return
        filename = items[0].text()
        if QtGui.QMessageBox.question(self, "Confirm", f"Delete '{filename}'?", 
                                      QtGui.QMessageBox.Yes | QtGui.QMessageBox.No) != QtGui.QMessageBox.Yes:
            return
        filepath = os.path.join(AI_DATA_DIR, filename)
        if safe_remove(filepath):
            FreeCAD.Console.PrintMessage(f"[AIAssistant] Deleted: {filename}\n")
            self.refresh_text_list()


# === КОМАНДА: ЭКСПОРТ ПРОЕКТА ===
class ExportProjectCommand:
    def GetResources(self):
        return {
            "MenuText": "Export Project",
            "ToolTip": "Export all data (images, texts, links) as ZIP archive"
        }

    def Activated(self):
        zip_path, _ = QtGui.QFileDialog.getSaveFileName(
            None,
            "Save AI Assistant Project",
            "",
            "ZIP Files (*.zip)"
        )
        if not zip_path:
            return
        if not zip_path.endswith(".zip"):
            zip_path += ".zip"
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                root_dir = os.path.dirname(AI_DATA_DIR)
                for root, dirs, files in os.walk(AI_DATA_DIR):
                    for file in files:
                        full_path = os.path.join(root, file)
                        arc_path = os.path.relpath(full_path, root_dir)
                        zf.write(full_path, arc_path)
            QtGui.QMessageBox.information(None, "Success", f"Project exported to:\n{zip_path}")
        except Exception as e:
            QtGui.QMessageBox.critical(None, "Export Error", f"Failed to create ZIP:\n{str(e)}")

    def IsActive(self):
        return True


# === РАБОЧАЯ СРЕДА ===
class AIAssistantWorkbench(FreeCADGui.Workbench):
    MenuText = "AI Assistant"
    ToolTip = "AI-powered design assistant (images + text + linking)"

    def __init__(self):
        self.Icon = os.path.join(os.path.dirname(__file__), "Resources", "icons", "ai_assistant.svg")

    def Initialize(self):
        self.list = [
            "LoadImageCommand",
            "LoadTextCommand",
            "LinkContentCommand",
            "ManageContentCommand",
            "ExportProjectCommand"
        ]
        self.appendToolbar("AI Tools", self.list)
        self.appendMenu("AI Assistant", self.list)

    def GetClassName(self):
        return "Gui::PythonWorkbench"


# === РЕГИСТРАЦИЯ КОМАНД ===
FreeCADGui.addCommand("LoadImageCommand", LoadImageCommand())
FreeCADGui.addCommand("LoadTextCommand", LoadTextCommand())
FreeCADGui.addCommand("LinkContentCommand", LinkContentCommand())
FreeCADGui.addCommand("ManageContentCommand", ManageContentCommand())
FreeCADGui.addCommand("ExportProjectCommand", ExportProjectCommand())