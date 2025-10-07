## \file AIEngineer/commands/load_image.py
# -*- coding: utf-8 -*-
"""
Команда загрузки изображений в рабочую директорию AIEngineer.
"""

import os
import shutil
from pathlib import Path
import FreeCAD
from PySide import QtGui
from ..utils import get_icon, AI_DATA_DIR

class LoadImageCommand:
    """Команда загрузки одного или нескольких изображений в рабочую папку AIEngineer."""

    def GetResources(self):
        return {
            "MenuText": "Load Image",
            "ToolTip": "Load image into AI workspace",
            "Pixmap": get_icon("load_image.svg")
        }

    def Activated(self):
        files, _ = QtGui.QFileDialog.getOpenFileNames(
            None,
            "Select Images",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.svg *.gif)"
        )
        if not files:
            return

        for src in files:
            filename = os.path.basename(src)
            dst = AI_DATA_DIR / filename

            # Избегаем перезаписи: добавляем суффикс _1, _2, ...
            if dst.exists():
                name, ext = os.path.splitext(filename)
                counter = 1
                while (AI_DATA_DIR / f"{name}_{counter}{ext}").exists():
                    counter += 1
                dst = AI_DATA_DIR / f"{name}_{counter}{ext}"

            try:
                shutil.copy2(src, dst)
                FreeCAD.Console.PrintMessage(f"[AIEngineer] Saved: {dst}\n")
            except Exception as ex:
                QtGui.QMessageBox.critical(
                    None, "Copy Error", f"Failed to copy:\n{str(ex)}"
                )

    def IsActive(self):
        return True