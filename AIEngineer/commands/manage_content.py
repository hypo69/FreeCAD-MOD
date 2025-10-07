## \file AIEngineer/commands/manage_content.py
# -*- coding: utf-8 -*-
"""
Команда открытия менеджера контента (просмотр, редактирование, удаление файлов).
"""

from PySide import QtGui
from ..utils import get_icon

class ManageContentCommand:
    """Команда управления загруженными изображениями и текстовыми файлами."""

    def GetResources(self):
        return {
            "MenuText": "Manage Content",
            "ToolTip": "View and edit your files",
            "Pixmap": get_icon("manage_content.svg")
        }

    def Activated(self):
        try:
            from ..dialogs.content_manager import ContentManagerDialog
            dialog = ContentManagerDialog()
            dialog.exec_()
        except Exception as ex:
            QtGui.QMessageBox.critical(
                None, "Manager Error", f"Failed to open content manager:\n{str(ex)}"
            )

    def IsActive(self):
        return True