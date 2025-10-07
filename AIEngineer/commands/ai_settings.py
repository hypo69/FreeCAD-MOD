## \file AIEngineer/project_manager.py
# -*- coding: utf-8 -*-
"""
Команда открытия настроек ИИ-провайдера (Google Gemini).
"""

from PySide import QtGui
from ..utils import get_icon

class AISettingsCommand:
    """Команда открытия диалога настроек API-ключа и параметров ИИ."""

    def GetResources(self):
        return {
            "MenuText": "AI Settings",
            "ToolTip": "Configure AI provider and API key",
            "Pixmap": get_icon("ai_settings.svg")
        }

    def Activated(self):
        try:
            from ..settings_dialog import SettingsDialog
            dialog = SettingsDialog()
            dialog.exec_()
        except Exception as ex:
            QtGui.QMessageBox.critical(
                None,
                "Settings Error",
                f"Failed to open settings dialog:\n{str(ex)}"
            )

    def IsActive(self):
        return True