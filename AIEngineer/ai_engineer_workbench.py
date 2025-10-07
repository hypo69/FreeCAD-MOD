## \file AIEngineer/ai_engineer_workbench.py
# -*- coding: utf-8 -*-
"""
Рабочая среда AI Engineer для FreeCAD.
========================================

Интеграция с Google Gemini для анализа изображений и генерации 3D-моделей.

.. module:: AIEngineer.ai_engineer_workbench
"""

import FreeCAD
import FreeCADGui
from .utils import get_icon

class AIEngineerWorkbench(FreeCADGui.Workbench):
    """Рабочая среда AI Engineer."""

    MenuText = "AI Engineer"
    ToolTip = "Google Gemini-powered design assistant for engineers"

    def __init__(self) -> None:
        """Инициализирует иконку рабочей среды."""
        self.Icon = get_icon("ai_engineer.svg")

    def Initialize(self) -> None:
        """
        Регистрирует команды в интерфейсе FreeCAD.
        
        Импорт команд выполняется локально — это безопасно и эффективно.
        Добавлена обработка исключений, чтобы ошибка в одной команде
        не привела к полному сбою загрузки рабочей среды.
        """
        command_classes = []
        command_names = []

        try:
            # Импорт команд выполняется локально — это безопасно и эффективно
            from .commands import (
                LoadImageCommand,
                LoadTextCommand,
                LinkContentCommand,
                ManageContentCommand,
                AskAICommand,
                Generate3DCommand,
                AISettingsCommand,
                ExportProjectCommand,
            )

            command_classes = [
                LoadImageCommand,
                LoadTextCommand,
                LinkContentCommand,
                ManageContentCommand,
                AskAICommand,
                Generate3DCommand,
                AISettingsCommand,
                ExportProjectCommand,
            ]

        except Exception as ex:
            FreeCAD.Console.PrintError(
                f"[AIEngineer] Failed to import commands in workbench: {ex}\n"
            )
            # Даже при ошибке — регистрируем хотя бы настройки, чтобы пользователь мог исправить проблему
            try:
                from .commands import AISettingsCommand
                command_classes = [AISettingsCommand]
            except Exception:
                FreeCAD.Console.PrintError("[AIEngineer] Even settings command failed to load.\n")
                return

        # Регистрация команд
        for cls in command_classes:
            try:
                name = cls.__name__
                FreeCADGui.addCommand(name, cls())
                command_names.append(name)
            except Exception as ex:
                FreeCAD.Console.PrintError(
                    f"[AIEngineer] Failed to register command {cls.__name__}: {ex}\n"
                )
                continue

        if command_names:
            # Добавляем команды на панель инструментов и в меню
            self.appendToolbar("AI Tools", command_names)
            self.appendMenu("AI Engineer", command_names)
        else:
            FreeCAD.Console.PrintWarning("[AIEngineer] No commands were registered.\n")

    def GetClassName(self) -> str:
        """Возвращает имя класса рабочей среды для FreeCAD."""
        return "Gui::PythonWorkbench"