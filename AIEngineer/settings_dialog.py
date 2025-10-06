# -*- coding: utf-8 -*-
"""
Диалог настройки API-ключа Google Gemini.
"""

from PySide import QtGui, QtCore
from .utils import get_api_key, save_to_env


class SettingsDialog(QtGui.QDialog):
    """Окно для ввода и сохранения API-ключа Google Generative AI."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('AI Settings — Google Gemini')
        self.resize(500, 250)

        # Загрузка текущего ключа (приоритет: .env > QSettings)
        self.settings = QtCore.QSettings('FreeCAD', 'AIEngineer')
        current_key: str = get_api_key()

        layout = QtGui.QVBoxLayout()

        # Информационный текст
        info_label = QtGui.QLabel(
            'Enter your Google Gemini API key:\n'
            'Get it at https://aistudio.google.com/app/apikey\n\n'
            'The key will be saved in .env file for security.'
        )
        layout.addWidget(info_label)

        # Поле ввода ключа
        self.key_input = QtGui.QLineEdit()
        self.key_input.setText(current_key)
        self.key_input.setEchoMode(QtGui.QLineEdit.Password)
        layout.addWidget(self.key_input)

        # Кнопка показа/скрытия ключа
        self.toggle_visibility = QtGui.QPushButton('👁️ Show Key')
        self.toggle_visibility.setCheckable(True)
        self.toggle_visibility.clicked.connect(self.toggle_key_visibility)
        layout.addWidget(self.toggle_visibility)

        # Отображение источника ключа
        from .utils import load_env
        env_vars: dict = load_env()
        source_text: str = ''
        if env_vars.get('GEMINI_API_KEY'):
            source_text = '✓ Key loaded from .env file'
        elif current_key:
            source_text = '⚠ Key loaded from QSettings (will be migrated to .env)'
        else:
            source_text = '✗ No API key found'
        
        self.source_label = QtGui.QLabel(source_text)
        self.source_label.setStyleSheet('color: gray; font-size: 10pt;')
        layout.addWidget(self.source_label)

        # Кнопки OK / Cancel
        btn_layout = QtGui.QHBoxLayout()
        ok_btn = QtGui.QPushButton('OK')
        cancel_btn = QtGui.QPushButton('Cancel')
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def toggle_key_visibility(self) -> None:
        """Функция переключает видимость API-ключа в поле ввода."""
        if self.toggle_visibility.isChecked():
            self.key_input.setEchoMode(QtGui.QLineEdit.Normal)
            self.toggle_visibility.setText('👁️ Hide Key')
        else:
            self.key_input.setEchoMode(QtGui.QLineEdit.Password)
            self.toggle_visibility.setText('👁️ Show Key')

    def accept(self) -> None:
        """Функция сохраняет API-ключ в .env и QSettings при подтверждении."""
        api_key: str = self.key_input.text().strip()
        
        if not api_key:
            self.settings.remove('api_key')
            super().accept()
            return
        
        # Сохранение в .env (основное хранилище)
        save_success: bool = save_to_env('GEMINI_API_KEY', api_key)
        
        # Дублирование в QSettings для обратной совместимости
        self.settings.setValue('api_key', api_key)
        
        if save_success:
            QtGui.QMessageBox.information(
                self,
                'Success',
                'API key saved successfully to .env file!'
            )
        else:
            QtGui.QMessageBox.warning(
                self,
                'Warning',
                'API key saved to QSettings, but failed to save to .env file.\n'
                'Check console for details.'
            )
        
        super().accept()