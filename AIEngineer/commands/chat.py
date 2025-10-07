## \file AIEngineer/commands/chat.py
# -*- coding: utf-8 -*-
"""
Команда открытия интерактивного чата с Google Gemini AI.
=========================================================

Предоставляет пользователю возможность вести диалог с моделью
в удобном интерфейсе с поддержкой истории и изображений.

.. module:: AIEngineer.commands.chat
"""

import FreeCAD
from PySide import QtGui
from ..utils import get_icon


class ChatCommand:
    """Команда открытия окна чата с AI."""

    def GetResources(self):
        """
        Функция возвращает ресурсы команды (иконка, текст меню, подсказка).
        
        Returns:
            dict: Словарь с ресурсами команды.
        """
        return {
            'MenuText': 'AI Chat',
            'ToolTip': 'Open interactive chat with Gemini AI',
            'Pixmap': get_icon('ai_chat.svg')
        }

    def Activated(self):
        """
        Функция выполняет открытие диалога чата при активации команды.
        
        Returns:
            None
        """
        try:
            from ..dialogs.chat_dialog import ChatDialog
            dialog = ChatDialog()
            dialog.exec_()
        except Exception as ex:
            FreeCAD.Console.PrintError(f'[AIEngineer] Failed to open chat dialog: {ex}\n')
            QtGui.QMessageBox.critical(
                None,
                'Chat Error',
                f'Failed to open chat dialog:\n{str(ex)}'
            )

    def IsActive(self):
        """
        Функция проверяет, активна ли команда (всегда доступна).
        
        Returns:
            bool: True (команда всегда активна).
        """
        return True