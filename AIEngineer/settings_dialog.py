## \file AIAssistant/settings_dialog.py
# -*- coding: utf-8 -*-
#! .pyenv/bin/python3

"""
Диалог настройки ИИ-провайдера: выбор модели, ввод API-ключа.
"""

from PySide import QtGui, QtCore

class SettingsDialog(QtGui.QDialog):
    """Диалог настройки параметров ИИ."""

    def __init__(self):
        """Функция инициализирует интерфейс настроек."""
        super().__init__()
        self.setWindowTitle("AI Assistant Settings")
        self.resize(500, 350)

        settings = QtCore.QSettings("FreeCAD", "AIAssistant")
        self.provider = settings.value("provider", "gemini")
        self.model = settings.value("model", "gemini-1.5-flash-latest")
        self.api_key = settings.value("api_key", "")
        self.base_url = settings.value("base_url", "http://localhost:11434")

        self.provider_combo = QtGui.QComboBox()
        self.provider_combo.addItems(["gemini", "ollama", "openai"])
        self.provider_combo.setCurrentText(self.provider)
        self.provider_combo.currentTextChanged.connect(self.on_provider_changed)

        self.model_input = QtGui.QLineEdit(self.model)
        self.api_key_input = QtGui.QLineEdit(self.api_key)
        self.api_key_input.setEchoMode(QtGui.QLineEdit.Password)
        self.base_url_input = QtGui.QLineEdit(self.base_url)

        self.on_provider_changed(self.provider)

        layout = QtGui.QFormLayout()
        layout.addRow("AI Provider:", self.provider_combo)
        layout.addRow("Model:", self.model_input)
        layout.addRow("API Key:", self.api_key_input)
        layout.addRow("Base URL (Ollama):", self.base_url_input)

        btn_layout = QtGui.QHBoxLayout()
        save_btn = QtGui.QPushButton("Save")
        cancel_btn = QtGui.QPushButton("Cancel")
        save_btn.clicked.connect(self.save_settings)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)

        main_layout = QtGui.QVBoxLayout()
        main_layout.addLayout(layout)
        main_layout.addLayout(btn_layout)
        self.setLayout(main_layout)

    def on_provider_changed(self, provider: str) -> None:
        """Функция обновляет доступность полей в зависимости от провайдера."""
        if provider == "gemini":
            self.base_url_input.setEnabled(False)
            self.api_key_input.setEnabled(True)
            self.model_input.setText("gemini-1.5-flash-latest")
        elif provider == "openai":
            self.base_url_input.setEnabled(False)
            self.api_key_input.setEnabled(True)
        else:  # ollama
            self.base_url_input.setEnabled(True)
            self.api_key_input.setEnabled(False)

    def save_settings(self) -> None:
        """Функция сохраняет настройки в QSettings."""
        settings = QtCore.QSettings("FreeCAD", "AIAssistant")
        settings.setValue("provider", self.provider_combo.currentText())
        settings.setValue("model", self.model_input.text())
        settings.setValue("api_key", self.api_key_input.text())
        settings.setValue("base_url", self.base_url_input.text())
        QtGui.QMessageBox.information(self, "Saved", "Settings saved successfully!")
        self.accept()