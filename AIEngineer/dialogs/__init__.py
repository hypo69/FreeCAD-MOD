## \file AIEngineer/dialogs/__init__.py
# -*- coding: utf-8 -*-
"""
Импорт всех диалогов AI Engineer.
===================================

Модуль экспортирует все диалоговые окна для использования
в командах рабочей среды.

.. module:: AIEngineer.dialogs
"""

from .ai_response import AIResponseDialog
from .chat_dialog import ChatDialog
from .content_manager import ContentManagerDialog
from .link_content_dialog import LinkContentDialog
from .text_editor import TextEditorDialog

__all__ = [
    'AIResponseDialog',
    'ChatDialog',
    'ContentManagerDialog',
    'LinkContentDialo',
    'TextEditorDialog',
]