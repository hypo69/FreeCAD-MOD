# -*- coding: utf-8 -*-
"""
Диалог для связывания одного изображения с одним текстовым файлом.
"""

from PySide import QtGui
from ..utils import get_image_files, get_text_files
from ..project_manager import AIProject

project = AIProject()  # предполагается, что инициализация безопасна

class LinkContentDialog(QtGui.QDialog):
    """Простой диалог: слева изображения, справа тексты, кнопка → посередине."""

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
        img_items = self.image_list.selectedItems()
        txt_items = self.text_list.selectedItems()
        if not img_items or not txt_items:
            QtGui.QMessageBox.warning(self, "Selection", "Select one image and one text file.")
            return

        image_file = img_items[0].text()
        text_file = txt_items[0].text()
        project.link_text_to_image(image_file, text_file)

        from FreeCAD import Console
        Console.PrintMessage(f"[AIEngineer] Linked: {image_file} ↔ {text_file}\n")
        self.refresh_lists()