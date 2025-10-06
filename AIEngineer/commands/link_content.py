# -*- coding: utf-8 -*-
"""
Команда связывания изображения с текстовым описанием.
"""

import FreeCAD
from PySide import QtGui
from ..utils import get_icon
from ..project_manager import AIProject

# Инициализация менеджера проекта
try:
    project = AIProject()
except Exception as ex:
    FreeCAD.Console.PrintError(f"[AIEngineer] Project manager init failed in link_content: {ex}\n")
    project = None

class LinkContentCommand:
    """Команда открытия диалога для связывания изображения и текстового файла."""

    def GetResources(self):
        return {
            "MenuText": "Link Content",
            "ToolTip": "Link image to text description",
            "Pixmap": get_icon("link_content.svg")
        }

    def Activated(self):
        if project is None:
            QtGui.QMessageBox.critical(
                None, "Error", "Project manager not available."
            )
            return

        try:
            from ..dialogs.link_content_dialog import LinkContentDialog
            dialog = LinkContentDialog()
            dialog.exec_()
        except Exception as ex:
            QtGui.QMessageBox.critical(
                None, "Dialog Error", f"Failed to open link dialog:\n{str(ex)}"
            )

    def IsActive(self):
        """Команда активна, только если менеджер проектов доступен."""
        return project is not None