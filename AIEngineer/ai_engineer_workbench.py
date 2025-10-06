# -*- coding: utf-8 -*-
"""
Рабочая среда AI Engineer для FreeCAD.
========================================

Интеграция с Google Gemini для анализа изображений и генерации 3D-моделей.

.. module:: AIEngineer.ai_engineer_workbench
"""

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
        """Регистрирует команды в интерфейсе FreeCAD."""
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

        # Создаём экземпляры команд и регистрируем их
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

        command_names = []
        for cls in command_classes:
            name = cls.__name__
            FreeCADGui.addCommand(name, cls())
            command_names.append(name)

        # Добавляем команды на панель инструментов и в меню
        self.appendToolbar("AI Tools", command_names)
        self.appendMenu("AI Engineer", command_names)

    def GetClassName(self) -> str:
        """Возвращает имя класса рабочей среды для FreeCAD."""
        return "Gui::PythonWorkbench"