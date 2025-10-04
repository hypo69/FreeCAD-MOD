import FreeCAD, FreeCADGui
import os
import shutil
from pathlib import Path
from PySide import QtGui, QtCore

# Папка для изображений (внутри пользовательской директории FreeCAD)
IMAGE_FOLDER = os.path.join(FreeCAD.getUserAppDataDir(), "MyImages")

# Создаём папку при первом запуске
os.makedirs(IMAGE_FOLDER, exist_ok=True)

class ImportImageCommand:
    def GetResources(self):
        icon_path = os.path.join(os.path.dirname(__file__), "Resources", "icons", "import_image.svg")
        return {
            "MenuText": "Import Image",
            "ToolTip": "Copy image files to your personal library",
            "Pixmap": icon_path
        }

    def Activated(self):
        dialog = ImageImportDialog()
        dialog.exec_()

    def IsActive(self):
        return True


class ImageLibraryWorkbench(FreeCADGui.Workbench):
    MenuText = "Image Library"
    ToolTip = "Manage your image library"

    def __init__(self):
        self.Icon = os.path.join(os.path.dirname(__file__), "Resources", "icons", "image_library.svg")

    def Initialize(self):
        self.list = ["ImportImageCommand"]
        self.appendToolbar("Image Tools", self.list)
        self.appendMenu("Image Library", self.list)

    def GetClassName(self):
        return "Gui::PythonWorkbench"


class ImageImportDialog(QtGui.QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Import Images to Library")
        self.resize(500, 400)

        # Список уже загруженных изображений
        self.list_widget = QtGui.QListWidget()
        self.refresh_list()

        # Кнопки
        self.add_button = QtGui.QPushButton("Add Images...")
        self.remove_button = QtGui.QPushButton("Remove Selected")
        self.insert_button = QtGui.QPushButton("Insert as Plane (3D)")
        self.close_button = QtGui.QPushButton("Close")

        self.add_button.clicked.connect(self.add_images)
        self.remove_button.clicked.connect(self.remove_selected)
        self.insert_button.clicked.connect(self.insert_as_plane)
        self.close_button.clicked.connect(self.accept)

        # Раскладка
        button_layout = QtGui.QHBoxLayout()
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.remove_button)
        button_layout.addWidget(self.insert_button)
        button_layout.addStretch()
        button_layout.addWidget(self.close_button)

        main_layout = QtGui.QVBoxLayout()
        main_layout.addWidget(QtGui.QLabel(f"Library folder: {IMAGE_FOLDER}"))
        main_layout.addWidget(self.list_widget)
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

    def refresh_list(self):
        self.list_widget.clear()
        for file in sorted(os.listdir(IMAGE_FOLDER)):
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.svg', '.gif')):
                self.list_widget.addItem(file)

    def add_images(self):
        files, _ = QtGui.QFileDialog.getOpenFileNames(
            self,
            "Select Image Files",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.svg *.gif)"
        )
        if not files:
            return

        for src in files:
            filename = os.path.basename(src)
            dst = os.path.join(IMAGE_FOLDER, filename)
            
            # Если файл с таким именем уже есть — добавляем суффикс
            if os.path.exists(dst):
                name, ext = os.path.splitext(filename)
                counter = 1
                while os.path.exists(os.path.join(IMAGE_FOLDER, f"{name}_{counter}{ext}")):
                    counter += 1
                dst = os.path.join(IMAGE_FOLDER, f"{name}_{counter}{ext}")
            
            try:
                shutil.copy2(src, dst)
            except Exception as e:
                QtGui.QMessageBox.warning(self, "Copy Error", f"Failed to copy {filename}:\n{str(e)}")
                continue

        self.refresh_list()

    def remove_selected(self):
        items = self.list_widget.selectedItems()
        if not items:
            return

        for item in items:
            filename = item.text()
            filepath = os.path.join(IMAGE_FOLDER, filename)
            try:
                os.remove(filepath)
            except Exception as e:
                QtGui.QMessageBox.warning(self, "Delete Error", f"Failed to delete {filename}:\n{str(e)}")
                continue

        self.refresh_list()

    def insert_as_plane(self):
        items = self.list_widget.selectedItems()
        if not items:
            QtGui.QMessageBox.information(self, "Info", "Select an image to insert.")
            return

        filename = items[0].text()
        filepath = os.path.join(IMAGE_FOLDER, filename)

        doc = FreeCAD.ActiveDocument
        if not doc:
            doc = FreeCAD.newDocument("ImagePlane")

        try:
            # Создаём плоскость с изображением
            img = doc.addObject("Image::ImagePlane", "ImagePlane")
            img.ImageFile = filepath
            img.XSize = 100.0  # мм
            img.YSize = 100.0
            doc.recompute()
            FreeCADGui.ActiveDocument.ActiveView.fitAll()
        except Exception as e:
            QtGui.QMessageBox.critical(self, "Insert Error", f"Cannot insert image:\n{str(e)}")


FreeCADGui.addCommand("ImportImageCommand", ImportImageCommand())