# -*- coding: utf-8 -*-
"""
Диалог настройки API-ключа Google Gemini.
"""

from PySide import QtGui, QtCore

class SettingsDialog(QtGui.QDialog):
    """Окно для ввода и сохранения API-ключа Google Generative AI."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Settings — Google Gemini")
        self.resize(500, 200)

        # Загружаем текущий ключ
        self.settings = QtCore.QSettings("FreeCAD", "AIEngineer")
        current_key = self.settings.value("api_key", "")

        layout = QtGui.QVBoxLayout()

        layout.addWidget(QtGui.QLabel(
            "Enter your Google Gemini API key:\n"
            "Get it at https://aistudio.google.com/app/apikey"
        ))

        self.key_input = QtGui.QLineEdit()
        self.key_input.setText(current_key)
        self.key_input.setEchoMode(QtGui.QLineEdit.Password)
        layout.addWidget(self.key_input)

        # Кнопка показа/скрытия ключа
        self.toggle_visibility = QtGui.QPushButton("👁️ Show Key")
        self.toggle_visibility.setCheckable(True)
        self.toggle_visibility.clicked.connect(self.toggle_key_visibility)
        layout.addWidget(self.toggle_visibility)

        # Кнопки OK / Cancel
        btn_layout = QtGui.QHBoxLayout()
        ok_btn = QtGui.QPushButton("OK")
        cancel_btn = QtGui.QPushButton("Cancel")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def toggle_key_visibility(self):
        if self.toggle_visibility.isChecked():
            self.key_input.setEchoMode(QtGui.QLineEdit.Normal)
            self.toggle_visibility.setText("👁️ Hide Key")
        else:
            self.key_input.setEchoMode(QtGui.QLineEdit.Password)
            self.toggle_visibility.setText("👁️ Show Key")

    def accept(self):
        api_key = self.key_input.text().strip()
        if api_key:
            self.settings.setValue("api_key", api_key)
        else:
            self.settings.remove("api_key")
        super().accept()