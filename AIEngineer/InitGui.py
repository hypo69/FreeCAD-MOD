# AIEngineer/InitGui.py
import FreeCADGui
from .ai_engineer_workbench import AIEngineerWorkbench

FreeCADGui.addWorkbench(AIEngineerWorkbench())