## \file AIEngineer/commands/load_text.py
# -*- coding: utf-8 -*-
"""
Команда загрузки или создания нового текстового файла (промпта).
"""

from PySide import QtGui
from ..utils import get_icon

class LoadTextCommand:
    """Команда открытия текстового редактора для создания или загрузки промпта."""

    def GetResources(self):
        return {
            "MenuText": "Load Text",
            "ToolTip": "Load or write text (Markdown)",
            "Pixmap": get_icon("load_text.svg")
        }

    def Activated(self):
        try:
            from ..dialogs.text_editor import TextEditorDialog
            dialog = TextEditorDialog()
            dialog.exec_()
        except Exception as ex:
            QtGui.QMessageBox.critical(
                None, "Editor Error", f"Failed to open text editor:\n{str(ex)}"
            )

    def IsActive(self):
        return True