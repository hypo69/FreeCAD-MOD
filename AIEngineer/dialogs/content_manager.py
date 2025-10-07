## \file AIEngineer/dialogs/content_manager.py
# -*- coding: utf-8 -*-
"""
Полнофункциональный менеджер контента: вкладки Images и Texts.
===============================================================

Предоставляет интерфейс для управления загруженными изображениями
и текстовыми файлами.

.. module:: AIEngineer.dialogs.content_manager
"""

import os
from pathlib import Path
from PySide import QtGui
from ..utils import get_image_files, get_text_files, AI_DATA_DIR, safe_remove
from ..project_manager import AIProject
import FreeCAD

project = AIProject()


class ContentManagerDialog(QtGui.QDialog):
    """Основной диалог управления контентом."""

    def __init__(self):
        """Функция инициализирует менеджер контента."""
        super().__init__()
        self.setWindowTitle('AI Engineer — Content Manager')
        self.resize(700, 500)

        self.tabs = QtGui.QTabWidget()
        self.image_tab = self.create_image_tab()
        self.text_tab = self.create_text_tab()
        self.tabs.addTab(self.image_tab, 'Images')
        self.tabs.addTab(self.text_tab, 'Texts')

        close_btn = QtGui.QPushButton('Close')
        close_btn.clicked.connect(self.accept)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.tabs)
        layout.addWidget(close_btn)
        self.setLayout(layout)

    def create_image_tab(self) -> QtGui.QWidget:
        """Функция создает вкладку для управления изображениями."""
        widget = QtGui.QWidget()
        layout = QtGui.QVBoxLayout()

        self.image_list = QtGui.QListWidget()
        self.image_list.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.refresh_image_list()

        self.link_btn = QtGui.QPushButton('Link to Text')
        self.unlink_btn = QtGui.QPushButton('Unlink')
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
        """Функция создает вкладку для управления текстовыми файлами."""
        widget = QtGui.QWidget()
        layout = QtGui.QVBoxLayout()

        self.text_list = QtGui.QListWidget()
        self.text_list.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.refresh_text_list()

        edit_btn = QtGui.QPushButton('Edit')
        delete_btn = QtGui.QPushButton('Delete')
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
                item.setForeground(QtGui.QColor('green'))
            self.image_list.addItem(item)

    def refresh_text_list(self) -> None:
        """Функция обновляет список текстовых файлов."""
        self.text_list.clear()
        for f in get_text_files():
            self.text_list.addItem(f)

    def link_image(self) -> None:
        """Функция связывает выбранное изображение с текстом."""
        items = self.image_list.selectedItems()
        if not items or project is None:
            return
        image_file = items[0].text()
        text_files = get_text_files()
        if not text_files:
            QtGui.QMessageBox.information(self, 'No Texts', 'No text files available.')
            return
        text_file, ok = QtGui.QInputDialog.getItem(
            self, 'Link Text', 'Select text file:', text_files, 0, False
        )
        if ok and text_file:
            project.link_text_to_image(image_file, text_file)
            FreeCAD.Console.PrintMessage(f'[AIEngineer] Linked: {image_file} ↔ {text_file}\n')
            self.refresh_image_list()

    def unlink_image(self) -> None:
        """Функция отвязывает выбранное изображение от текста."""
        items = self.image_list.selectedItems()
        if not items or project is None:
            return
        image_file = items[0].text()
        if project.is_image_linked(image_file):
            project.unlink_image(image_file)
            FreeCAD.Console.PrintMessage(f'[AIEngineer] Unlinked: {image_file}\n')
            self.refresh_image_list()

    def edit_selected_text(self) -> None:
        """Функция открывает редактор для выбранного текста."""
        items = self.text_list.selectedItems()
        if not items:
            return
        filename = items[0].text()
        filepath = AI_DATA_DIR / filename
        from .text_editor import TextEditorDialog
        dialog = TextEditorDialog(filepath)
        dialog.exec_()
        self.refresh_text_list()

    def delete_selected_text(self) -> None:
        """Функция удаляет выбранный текстовый файл."""
        items = self.text_list.selectedItems()
        if not items:
            return
        filename = items[0].text()
        if QtGui.QMessageBox.question(
            self, 'Confirm', f'Delete "{filename}"?',
            QtGui.QMessageBox.Yes | QtGui.QMessageBox.No
        ) != QtGui.QMessageBox.Yes:
            return

        # Отвязывание от изображений
        if project:
            project.unlink_text(filename)

        filepath = AI_DATA_DIR / filename
        if safe_remove(filepath):
            FreeCAD.Console.PrintMessage(f'[AIEngineer] Deleted: {filename}\n')
            self.refresh_text_list()