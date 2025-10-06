# -*- coding: utf-8 -*-
"""
Команда генерации 3D-объекта на основе текстового описания (в будущем — через ИИ).
"""

import FreeCAD
from PySide import QtGui
from ..utils import get_icon

class Generate3DCommand:
    """Команда создания 3D-объекта по текстовому описанию."""

    def GetResources(self):
        return {
            "MenuText": "Generate 3D from AI",
            "ToolTip": "Create 3D object based on AI description",
            "Pixmap": get_icon("generate_3d.svg")  # рекомендуется добавить иконку
        }

    def Activated(self):
        text, ok = QtGui.QInputDialog.getMultiLineText(
            None, "Generate 3D", "Enter object description:", "Box 50x30x20 mm"
        )
        if not ok or not text.strip():
            return

        try:
            doc = FreeCAD.ActiveDocument or FreeCAD.newDocument("AI_Generated")
            description = text.lower()

            # Простой парсинг для "box"
            if "box" in description or "короб" in description or "параллелепипед" in description:
                import re
                # Ищем все числа (целые и с плавающей точкой)
                nums = list(map(float, re.findall(r'\d+\.?\d*', text)))
                if len(nums) >= 3:
                    l, w, h = nums[0], nums[1], nums[2]
                    box = doc.addObject("Part::Box", "AI_Box")
                    box.Length = l
                    box.Width = w
                    box.Height = h
                    doc.recompute()
                    FreeCAD.Console.PrintMessage(f"[AIEngineer] Created box: {l}x{w}x{h}\n")
                else:
                    QtGui.QMessageBox.warning(
                        None, "Parse Error", "Need at least 3 dimensions for a box (e.g. 'Box 50 30 20')."
                    )
            else:
                QtGui.QMessageBox.information(
                    None, "Not Implemented",
                    "Only 'box' is supported for now.\n"
                    "Future versions will support cylinders, sketches, and full AI-generated models."
                )

        except ValueError as ex:
            QtGui.QMessageBox.critical(
                None, "Input Error", f"Invalid number format:\n{str(ex)}"
            )
        except Exception as ex:
            QtGui.QMessageBox.critical(
                None, "Error", f"3D generation failed:\n{str(ex)}"
            )
            FreeCAD.Console.PrintError(f"[AIEngineer] 3D generation error: {ex}\n")

    def IsActive(self):
        return True