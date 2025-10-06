# -*- coding: utf-8 -*-
"""
Команда экспорта всего проекта AI Engineer в ZIP-архив.
"""

import os
import zipfile
from pathlib import Path
from PySide import QtGui
from ..utils import get_icon, AI_DATA_DIR
import FreeCAD

class ExportProjectCommand:
    """Команда экспорта всех данных проекта (изображения, тексты, ссылки) в ZIP."""

    def GetResources(self):
        return {
            "MenuText": "Export Project",
            "ToolTip": "Export all data as ZIP",
            "Pixmap": get_icon("export_project.svg")  # рекомендуется добавить иконку
        }

    def Activated(self):
        zip_path, _ = QtGui.QFileDialog.getSaveFileName(
            None, "Save Project", "", "ZIP Files (*.zip)"
        )
        if not zip_path:
            return
        if not zip_path.endswith(".zip"):
            zip_path += ".zip"

        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                # Архивируем всю папку AI_DATA_DIR (включая подпапки вроде ai_history)
                root_dir = AI_DATA_DIR.parent  # .../AIEngineer/
                for root, dirs, files in os.walk(AI_DATA_DIR):
                    for file in files:
                        full_path = Path(root) / file
                        # Сохраняем структуру относительно AIEngineer/
                        arc_path = full_path.relative_to(root_dir)
                        zf.write(full_path, arc_path)
            QtGui.QMessageBox.information(
                None, "Success", f"Project exported to:\n{zip_path}"
            )
            FreeCAD.Console.PrintMessage(f"[AIEngineer] Project exported: {zip_path}\n")
        except Exception as ex:
            QtGui.QMessageBox.critical(
                None, "Error", f"Export failed:\n{str(ex)}"
            )
            FreeCAD.Console.PrintError(f"[AIEngineer] Export error: {ex}\n")

    def IsActive(self):
        return True