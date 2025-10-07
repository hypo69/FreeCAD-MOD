## \file AIEngineer/dialogs/chat_dialog.py
# -*- coding: utf-8 -*-
"""
Диалог чата с Google Gemini AI.
=================================

Предоставляет интерактивный интерфейс для общения с моделью Gemini
с поддержкой истории сообщений, контекста и изображений.

.. module:: AIEngineer.dialogs.chat_dialog
"""

import asyncio
from pathlib import Path
from typing import Optional, List, Dict
from PySide import QtGui, QtCore
import FreeCAD

from ..gemini import GoogleGenerativeAi
from ..utils import get_api_key, AI_DATA_DIR, get_image_files


class ChatMessage(QtGui.QWidget):
    """Виджет для отображения одного сообщения в чате."""

    def __init__(self, text: str, is_user: bool = True, parent=None):
        """
        Функция инициализирует виджет сообщения.

        Args:
            text (str): Текст сообщения.
            is_user (bool): True если сообщение от пользователя, False если от AI.
            parent: Родительский виджет.
        """
        super().__init__(parent)
        
        layout = QtGui.QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)
        
        # Текстовое поле сообщения
        text_edit = QtGui.QTextEdit()
        text_edit.setPlainText(text)
        text_edit.setReadOnly(True)
        text_edit.setMaximumHeight(150)
        
        # Стилизация в зависимости от отправителя
        if is_user:
            text_edit.setStyleSheet(
                'QTextEdit { '
                'background-color: #E3F2FD; '
                'border: 1px solid #90CAF9; '
                'border-radius: 8px; '
                'padding: 8px; '
                '}'
            )
            layout.addStretch()
            layout.addWidget(text_edit, 7)
        else:
            text_edit.setStyleSheet(
                'QTextEdit { '
                'background-color: #F5F5F5; '
                'border: 1px solid #E0E0E0; '
                'border-radius: 8px; '
                'padding: 8px; '
                '}'
            )
            layout.addWidget(text_edit, 7)
            layout.addStretch()
        
        self.setLayout(layout)


class ChatDialog(QtGui.QDialog):
    """Диалог чата с Google Gemini AI."""

    def __init__(self, parent=None):
        """
        Функция инициализирует диалог чата.

        Args:
            parent: Родительский виджет.
        """
        super().__init__(parent)
        self.setWindowTitle('AI Engineer — Chat with Gemini')
        self.resize(800, 600)
        
        # Инициализация переменных
        self.llm: Optional[GoogleGenerativeAi] = None
        self.current_image: Optional[Path] = None
        self.current_model: str = ''
        self.chat_session_name: str = 'freecad_chat'
        
        # Создание UI
        self._create_ui()
        
        # Инициализация AI клиента
        self._initialize_ai()
        
        # Загрузка истории при открытии
        self._load_chat_history()

    def _create_ui(self) -> None:
        """Функция создает пользовательский интерфейс."""
        main_layout = QtGui.QVBoxLayout()
        
        # === ЗАГОЛОВОК ===
        header_layout = QtGui.QHBoxLayout()
        
        title_label = QtGui.QLabel('<h2>💬 Chat with Gemini AI</h2>')
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Отображение текущей модели
        self.model_label = QtGui.QLabel('Model: Loading...')
        self.model_label.setStyleSheet(
            'QLabel { '
            'color: #1976D2; '
            'font-weight: bold; '
            'padding: 5px; '
            'background-color: #E3F2FD; '
            'border-radius: 4px; '
            '}'
        )
        header_layout.addWidget(self.model_label)
        
        # Кнопка настроек
        settings_btn = QtGui.QPushButton('⚙️ Settings')
        settings_btn.clicked.connect(self._open_settings)
        settings_btn.setMaximumWidth(100)
        settings_btn.setToolTip('Open AI Settings to change model')
        header_layout.addWidget(settings_btn)
        
        # Кнопка очистки истории
        clear_btn = QtGui.QPushButton('🗑️ Clear')
        clear_btn.clicked.connect(self._clear_chat)
        clear_btn.setMaximumWidth(80)
        header_layout.addWidget(clear_btn)
        
        main_layout.addLayout(header_layout)
        
        # === ОБЛАСТЬ СООБЩЕНИЙ ===
        self.messages_scroll = QtGui.QScrollArea()
        self.messages_scroll.setWidgetResizable(True)
        self.messages_scroll.setStyleSheet(
            'QScrollArea { '
            'background-color: white; '
            'border: 1px solid #E0E0E0; '
            'border-radius: 4px; '
            '}'
        )
        
        # Контейнер для сообщений
        self.messages_container = QtGui.QWidget()
        self.messages_layout = QtGui.QVBoxLayout()
        self.messages_layout.addStretch()
        self.messages_container.setLayout(self.messages_layout)
        self.messages_scroll.setWidget(self.messages_container)
        
        main_layout.addWidget(self.messages_scroll)
        
        # === ПАНЕЛЬ КОНТЕКСТА ===
        context_layout = QtGui.QHBoxLayout()
        
        # Выбор изображения
        self.image_combo = QtGui.QComboBox()
        self.image_combo.addItem('No image')
        self._refresh_image_list()
        context_layout.addWidget(QtGui.QLabel('Attach image:'))
        context_layout.addWidget(self.image_combo, 3)
        
        # Кнопка обновления списка изображений
        refresh_btn = QtGui.QPushButton('🔄')
        refresh_btn.setMaximumWidth(40)
        refresh_btn.clicked.connect(self._refresh_image_list)
        refresh_btn.setToolTip('Refresh image list')
        context_layout.addWidget(refresh_btn)
        
        context_layout.addStretch()
        
        main_layout.addLayout(context_layout)
        
        # === ПАНЕЛЬ ВВОДА ===
        input_layout = QtGui.QVBoxLayout()
        
        # Поле ввода сообщения
        self.input_text = QtGui.QTextEdit()
        self.input_text.setMaximumHeight(100)
        self.input_text.setPlaceholderText('Type your message here...')
        self.input_text.setStyleSheet(
            'QTextEdit { '
            'border: 2px solid #90CAF9; '
            'border-radius: 4px; '
            'padding: 8px; '
            'font-size: 11pt; '
            '}'
        )
        input_layout.addWidget(self.input_text)
        
        # Кнопки отправки
        buttons_layout = QtGui.QHBoxLayout()
        
        self.send_btn = QtGui.QPushButton('📤 Send (Ctrl+Enter)')
        self.send_btn.clicked.connect(self._send_message)
        self.send_btn.setStyleSheet(
            'QPushButton { '
            'background-color: #2196F3; '
            'color: white; '
            'border: none; '
            'border-radius: 4px; '
            'padding: 10px 20px; '
            'font-size: 11pt; '
            'font-weight: bold; '
            '} '
            'QPushButton:hover { '
            'background-color: #1976D2; '
            '} '
            'QPushButton:disabled { '
            'background-color: #BDBDBD; '
            '}'
        )
        buttons_layout.addWidget(self.send_btn)
        
        close_btn = QtGui.QPushButton('Close')
        close_btn.clicked.connect(self._on_close)
        close_btn.setMaximumWidth(100)
        buttons_layout.addWidget(close_btn)
        
        input_layout.addLayout(buttons_layout)
        main_layout.addLayout(input_layout)
        
        # === ИНДИКАТОР ЗАГРУЗКИ ===
        self.loading_label = QtGui.QLabel('⏳ Processing...')
        self.loading_label.setStyleSheet(
            'QLabel { '
            'color: #1976D2; '
            'font-weight: bold; '
            'padding: 5px; '
            '}'
        )
        self.loading_label.hide()
        main_layout.addWidget(self.loading_label)
        
        self.setLayout(main_layout)
        
        # Горячая клавиша для отправки
        send_shortcut = QtGui.QShortcut(QtGui.QKeySequence('Ctrl+Return'), self)
        send_shortcut.activated.connect(self._send_message)

    def _initialize_ai(self) -> None:
        """Функция инициализирует AI клиент с настройками из QSettings."""
        api_key: str = get_api_key()
        
        if not api_key:
            QtGui.QMessageBox.critical(
                self,
                'Error',
                'Gemini API key not configured.\n\n'
                'Please configure it in AI Settings.'
            )
            self.send_btn.setEnabled(False)
            self.model_label.setText('Model: Not configured')
            return
        
        # Загрузка настроек из QSettings
        settings = QtCore.QSettings('FreeCAD', 'AIEngineer')
        model_name: str = settings.value('model_name', 'gemini-2.5-flash')
        
        try:
            self.current_model = model_name
            self.llm = GoogleGenerativeAi(
                api_key=api_key,
                model_name=model_name,
                system_instruction=(
                    'Вы - технический ассистент для инженеров, работающих с FreeCAD. '
                    'Предоставляйте точные, краткие и полезные ответы. '
                    'При анализе изображений описывайте технические детали.'
                )
            )
            # Установка имени сессии чата
            self.llm.chat_session_name = self.chat_session_name
            self.model_label.setText(f'Model: {model_name}')
            FreeCAD.Console.PrintMessage(f'[AIEngineer] Chat initialized with {model_name}\n')
            
        except Exception as ex:
            FreeCAD.Console.PrintError(f'[AIEngineer] Failed to initialize AI: {ex}\n')
            QtGui.QMessageBox.critical(
                self,
                'Initialization Error',
                f'Failed to initialize Gemini:\n{str(ex)}'
            )
            self.send_btn.setEnabled(False)
            self.model_label.setText('Model: Error')

    def _load_chat_history(self) -> None:
        """Функция загружает историю чата при открытии диалога."""
        if not self.llm:
            return
        
        try:
            # Попытка загрузить историю из файла
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.llm._load_chat_history())
            loop.close()
            
            # Восстановление сообщений в UI
            if self.llm.chat_history:
                for msg in self.llm.chat_history:
                    role = msg.get('role', '')
                    parts = msg.get('parts', [])
                    
                    if role == 'user':
                        # Извлечение текста из частей
                        text_parts = [p for p in parts if isinstance(p, str)]
                        if text_parts:
                            text = '\n'.join(text_parts)
                            self._add_message_to_ui(text, is_user=True)
                    elif role == 'model':
                        text_parts = [p for p in parts if isinstance(p, str)]
                        if text_parts:
                            text = '\n'.join(text_parts)
                            self._add_message_to_ui(text, is_user=False)
                
                FreeCAD.Console.PrintMessage(
                    f'[AIEngineer] Loaded {len(self.llm.chat_history)} messages from history\n'
                )
        except Exception as ex:
            FreeCAD.Console.PrintError(f'[AIEngineer] Failed to load chat history: {ex}\n')

    def _open_settings(self) -> None:
        """Функция открывает диалог настроек для изменения модели."""
        try:
            from ..settings_dialog import SettingsDialog
            dialog = SettingsDialog()
            result = dialog.exec_()
            
            if result == QtGui.QDialog.Accepted:
                # Перезагрузка AI клиента с новыми настройками
                settings = QtCore.QSettings('FreeCAD', 'AIEngineer')
                new_model: str = settings.value('model_name', 'gemini-2.5-flash')
                
                if new_model != self.current_model:
                    response = QtGui.QMessageBox.question(
                        self,
                        'Model Changed',
                        f'Model changed to {new_model}.\n\n'
                        'Start a new chat session with this model?',
                        QtGui.QMessageBox.Yes | QtGui.QMessageBox.No
                    )
                    
                    if response == QtGui.QMessageBox.Yes:
                        self._initialize_ai()
                        self._clear_chat()
                        
        except Exception as ex:
            FreeCAD.Console.PrintError(f'[AIEngineer] Failed to open settings: {ex}\n')
            QtGui.QMessageBox.critical(
                self,
                'Settings Error',
                f'Failed to open settings:\n{str(ex)}'
            )

    def _refresh_image_list(self) -> None:
        """Функция обновляет список доступных изображений."""
        current_text: str = self.image_combo.currentText()
        self.image_combo.clear()
        self.image_combo.addItem('No image')
        
        images: List[str] = get_image_files()
        self.image_combo.addItems(images)
        
        # Восстановление выбранного изображения
        if current_text != 'No image':
            index: int = self.image_combo.findText(current_text)
            if index >= 0:
                self.image_combo.setCurrentIndex(index)

    def _clear_chat(self) -> None:
        """Функция очищает историю чата."""
        if not self.llm or not self.llm.chat_history:
            return
        
        response = QtGui.QMessageBox.question(
            self,
            'Clear Chat',
            'Clear all messages?',
            QtGui.QMessageBox.Yes | QtGui.QMessageBox.No
        )
        
        if response == QtGui.QMessageBox.Yes:
            # Очистка UI
            while self.messages_layout.count() > 1:
                item = self.messages_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            # Очистка истории в модели
            if self.llm:
                self.llm.clear_history()
            
            FreeCAD.Console.PrintMessage('[AIEngineer] Chat history cleared\n')

    def _add_message_to_ui(self, text: str, is_user: bool = True) -> None:
        """
        Функция добавляет сообщение в UI.

        Args:
            text (str): Текст сообщения.
            is_user (bool): True если от пользователя, False если от AI.
        """
        message_widget = ChatMessage(text, is_user)
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, message_widget)
        
        # Прокрутка вниз
        QtCore.QTimer.singleShot(100, lambda: self.messages_scroll.verticalScrollBar().setValue(
            self.messages_scroll.verticalScrollBar().maximum()
        ))

    def _send_message(self) -> None:
        """Функция отправляет сообщение в AI."""
        if not self.llm:
            QtGui.QMessageBox.warning(
                self,
                'Not Initialized',
                'AI is not initialized. Please check your settings.'
            )
            return
        
        message: str = self.input_text.toPlainText().strip()
        
        if not message:
            QtGui.QMessageBox.warning(self, 'Warning', 'Please enter a message.')
            return
        
        # Отключение UI во время обработки
        self.send_btn.setEnabled(False)
        self.input_text.setEnabled(False)
        self.loading_label.show()
        
        # Добавление сообщения пользователя в UI
        self._add_message_to_ui(message, is_user=True)
        self.input_text.clear()
        
        # Проверка наличия прикрепленного изображения
        selected_image: str = self.image_combo.currentText()
        image_path: Optional[Path] = None
        
        if selected_image and selected_image != 'No image':
            image_path = AI_DATA_DIR / selected_image
            FreeCAD.Console.PrintMessage(f'[AIEngineer] Attaching image: {selected_image}\n')
        
        # Отправка запроса
        QtCore.QTimer.singleShot(10, lambda: self._process_message(message, image_path))

    def _process_message(self, message: str, image_path: Optional[Path] = None) -> None:
        """
        Функция обрабатывает сообщение и использует метод chat для сохранения истории.

        Args:
            message (str): Текст сообщения.
            image_path (Optional[Path]): Путь к изображению.
        """
        try:
            response: Optional[str] = None
            
            # Использование метода chat для сохранения истории
            if image_path and image_path.exists():
                # Для изображений используем describe_image, но добавляем в историю вручную
                mime_type: str = 'image/jpeg' if image_path.suffix.lower() in ['.jpg', '.jpeg'] else 'image/png'
                response = self.llm.describe_image(
                    image=image_path,
                    mime_type=mime_type,
                    prompt=message
                )
                
                # Добавление в историю вручную, так как describe_image не использует chat
                if response:
                    self.llm.chat_history.append({'role': 'user', 'parts': [message, str(image_path)]})
                    self.llm.chat_history.append({'role': 'model', 'parts': [response]})
                    
                    # Сохранение истории
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self.llm._save_chat_history())
                    loop.close()
            else:
                # Использование метода chat, который автоматически сохраняет историю
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                response = loop.run_until_complete(
                    self.llm.chat(message, chat_session_name=self.chat_session_name)
                )
                loop.close()
            
            # Обработка ответа
            if response:
                self._add_message_to_ui(response, is_user=False)
                FreeCAD.Console.PrintMessage('[AIEngineer] Response received and saved to history\n')
            else:
                QtGui.QMessageBox.warning(
                    self,
                    'No Response',
                    'AI did not return a response. Please try again.'
                )
            
        except Exception as ex:
            FreeCAD.Console.PrintError(f'[AIEngineer] Chat error: {ex}\n')
            QtGui.QMessageBox.critical(
                self,
                'Error',
                f'An error occurred:\n{str(ex)}'
            )
        
        finally:
            # Включение UI
            self.send_btn.setEnabled(True)
            self.input_text.setEnabled(True)
            self.loading_label.hide()
            self.input_text.setFocus()

    def _on_close(self) -> None:
        """Функция сохраняет историю при закрытии диалога."""
        if self.llm and self.llm.chat_history:
            try:
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.llm._save_chat_history())
                loop.close()
                FreeCAD.Console.PrintMessage('[AIEngineer] Chat history saved on close\n')
            except Exception as ex:
                FreeCAD.Console.PrintError(f'[AIEngineer] Failed to save history on close: {ex}\n')
        
        self.accept()