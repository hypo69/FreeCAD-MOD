## \file AIEngineer/dialogs/text_editor.py
# -*- coding: utf-8 -*-
"""
Диалог редактирования текстового промпта (Markdown).
"""

import os
from pathlib import Path
from PySide import QtGui
from ..utils import AI_DATA_DIR

class TextEditorDialog(QtGui.QDialog):
    """Редактор текста для создания или изменения промптов."""

    def __init__(self, filepath: Path = None):
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
            filepath = AI_DATA_DIR / f"{base_name}_{counter}{ext}

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(text)
            from FreeCAD import Console
            Console.PrintMessage(f"[AIEngineer] Saved: {filepath}\n")
            QtGui.QMessageBox.information(self, "Saved", "Text saved successfully!")
            self.accept()
        except Exception as ex:
            QtGui.QMessageBox.critical(self, "Save Error", str(ex))