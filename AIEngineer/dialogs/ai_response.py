# -*- coding: utf-8 -*-
"""
Диалог отображения ответа от Google Gemini.
"""

from PySide import QtGui

class AIResponseDialog(QtGui.QDialog):
    """Окно для просмотра и копирования ответа ИИ."""

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