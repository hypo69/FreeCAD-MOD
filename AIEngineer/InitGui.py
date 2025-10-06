import sys
import os
import site
import FreeCAD
import FreeCADGui

# Путь к рабочему venv
VENV_PATH = r"C:\Users\user\Documents\repos\hypotez\venv"
SITE_PACKAGES = os.path.join(VENV_PATH, "Lib", "site-packages")

if os.path.isdir(SITE_PACKAGES):
    site.addsitedir(SITE_PACKAGES)

# Функция безопасной проверки импорта
def safe_import(package_name: str):
    try:
        __import__(package_name)
        return True
    except ImportError:
        FreeCAD.Console.PrintMessage(
            f"[AIEngineer] Warning: {package_name} not found. "
            "Some AI features will be disabled.\n"
        )
        return False
    except Exception as ex:
        FreeCAD.Console.PrintMessage(
            f"[AIEngineer] Warning: {package_name} failed to load ({ex}). "
            "Some AI features may be unstable.\n"
        )
        return False

# Проверяем основные AI-пакеты
safe_import("google.generativeai")
safe_import("grpc")
safe_import("protobuf")

# Подключаем рабочую панель AIEngineer
from AIEngineer.ai_engineer_workbench import AIEngineerWorkbench
FreeCADGui.addWorkbench(AIEngineerWorkbench())
