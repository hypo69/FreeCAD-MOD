# -*- coding: utf-8 -*-
"""
Диалог настроек AI Engine для FreeCAD.
========================================

Позволяет настроить API ключ и модель Gemini.
"""

from PySide import QtGui, QtCore
import google.generativeai as genai
import FreeCAD

from AIEngineer.utils import get_api_key


class SettingsDialog(QtGui.QDialog):
    """Диалог настроек AI Engine."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI Settings — Google Gemini")
        self.setModal(True)
        self.resize(600, 400)

        # Создаём layout
        layout = QtGui.QVBoxLayout()

        # Заголовок
        label_header = QtGui.QLabel(
            "Enter your Google Gemini API key:\n"
            "Get it at https://aistudio.google.com/app/apikey\n\n"
            "The key will be saved in .env file for security."
        )
        layout.addWidget(label_header)

        # Поле ввода API ключа
        self.api_key_input = QtGui.QLineEdit()
        self.api_key_input.setEchoMode(QtGui.QLineEdit.Password)
        layout.addWidget(self.api_key_input)

        # Кнопка показать/скрыть ключ
        self.show_key_checkbox = QtGui.QCheckBox("Show Key")
        self.show_key_checkbox.stateChanged.connect(self.toggle_show_key)
        layout.addWidget(self.show_key_checkbox)

        # Разделитель
        layout.addWidget(QtGui.QLabel(""))  # пустая строка

        # Метка состояния
        self.status_label = QtGui.QLabel("")
        layout.addWidget(self.status_label)

        # Выбор модели
        layout.addWidget(QtGui.QLabel("Select Model:"))
        self.model_combo = QtGui.QComboBox()
        self.model_combo.currentIndexChanged.connect(self.on_model_changed)
        layout.addWidget(self.model_combo)

        # Кнопки OK / Cancel
        button_layout = QtGui.QHBoxLayout()
        ok_button = QtGui.QPushButton("OK")
        cancel_button = QtGui.QPushButton("Cancel")
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        # Загружаем настройки
        self.load_settings()

        # Инициализируем список моделей
        self.load_available_models()

    def toggle_show_key(self, state):
        """Переключает режим отображения ключа."""
        if state == QtCore.Qt.Checked:
            self.api_key_input.setEchoMode(QtGui.QLineEdit.Normal)
        else:
            self.api_key_input.setEchoMode(QtGui.QLineEdit.Password)

    def load_settings(self):
        """Загружает текущие настройки из QSettings."""
        settings = QtCore.QSettings("FreeCAD", "AIEngineer")
        api_key = settings.value("api_key", "")
        model_name = settings.value("model_name", "gemini-2.5-flash")

        self.api_key_input.setText(api_key)

        # Попытка установить текущую модель в комбобокс
        index = self.model_combo.findText(model_name)
        if index >= 0:
            self.model_combo.setCurrentIndex(index)
        else:
            # Если модель не найдена в списке — добавляем как первый элемент
            self.model_combo.insertItem(0, model_name)
            self.model_combo.setCurrentIndex(0)

    def save_settings(self):
        """Сохраняет настройки в QSettings."""
        settings = QtCore.QSettings("FreeCAD", "AIEngineer")
        settings.setValue("api_key", self.api_key_input.text().strip())
        settings.setValue("model_name", self.model_combo.currentText())

    def accept(self):
        """Обработка нажатия OK."""
        self.save_settings()
        super().accept()

    def load_available_models(self):
        """Загружает доступные модели из Google Gemini API."""
        api_key = self.api_key_input.text().strip()
        if not api_key:
            self.status_label.setText("⚠️ API key is empty. Cannot fetch models.")
            return

        try:
            genai.configure(api_key=api_key)
            models = genai.list_models()

            # Очищаем список
            self.model_combo.clear()

            # Фильтруем модели, поддерживающие generateContent
            available_models = []
            for m in models:
                if 'generateContent' in m.supported_generation_methods:
                    model_name = m.name.replace('models/', '')  # убираем префикс
                    available_models.append(model_name)

            # Сортируем по алфавиту
            available_models.sort()

            # Добавляем в комбобокс
            self.model_combo.addItems(available_models)

            # Устанавливаем текущую модель, если она есть в списке
            current_model = self.model_combo.currentText()
            if current_model and current_model in available_models:
                index = self.model_combo.findText(current_model)
                if index >= 0:
                    self.model_combo.setCurrentIndex(index)

            self.status_label.setText(f"✅ {len(available_models)} models loaded.")

        except Exception as ex:
            self.status_label.setText(f"❌ Error fetching models: {str(ex)}")
            FreeCAD.Console.PrintError(f"[AIEngineer] Failed to list models: {ex}\n")

    def on_model_changed(self, index):
        """Обработчик изменения выбранной модели."""
        selected_model = self.model_combo.currentText()
        FreeCAD.Console.PrintMessage(f"[AIEngineer] Selected model: {selected_model}\n")