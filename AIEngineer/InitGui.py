# -*- coding: utf-8 -*-
"""
Модуль инициализации рабочей среды AIEngineer для FreeCAD.
=============================================================

Выполняет:
- Проверку наличия необходимых AI-библиотек
- Регистрацию рабочей среды AIEngineer в FreeCAD

.. module:: AIEngineer
"""

import FreeCAD
import FreeCADGui

# === ПРОВЕРКА ЗАВИСИМОСТЕЙ ===
FreeCAD.Console.PrintMessage("\n" + "=" * 60 + "\n")
FreeCAD.Console.PrintMessage("[AIEngineer] Checking dependencies...\n")
FreeCAD.Console.PrintMessage("=" * 60 + "\n")

# Проверка gRPC
try:
    import grpc
    try:
        from grpc._cython import cygrpc
        FreeCAD.Console.PrintMessage(f"[AIEngineer] ✓ gRPC v{grpc.__version__}\n")
        has_grpc = True
    except ImportError:
        FreeCAD.Console.PrintWarning(
            "[AIEngineer] ✗ gRPC cygrpc module not found\n"
            "[AIEngineer]   Trying to continue anyway...\n"
        )
        has_grpc = False
except ImportError:
    FreeCAD.Console.PrintWarning("[AIEngineer] ✗ gRPC not found\n")
    has_grpc = False
except Exception as ex:
    FreeCAD.Console.PrintError(f"[AIEngineer] ✗ gRPC error: {ex}\n")
    has_grpc = False

# Проверка Protobuf
try:
    import google.protobuf
    FreeCAD.Console.PrintMessage("[AIEngineer] ✓ Protocol Buffers\n")
    has_protobuf = True
except ImportError:
    FreeCAD.Console.PrintWarning("[AIEngineer] ✗ Protocol Buffers not found\n")
    has_protobuf = False
except Exception as ex:
    FreeCAD.Console.PrintError(f"[AIEngineer] ✗ Protobuf error: {ex}\n")
    has_protobuf = False

# Проверка Google Generative AI
try:
    import google.generativeai
    FreeCAD.Console.PrintMessage("[AIEngineer] ✓ Google Generative AI\n")
    has_genai = True
except ImportError:
    FreeCAD.Console.PrintWarning("[AIEngineer] ✗ Google Generative AI not found\n")
    has_genai = False
except Exception as ex:
    FreeCAD.Console.PrintError(f"[AIEngineer] ✗ Generative AI error: {ex}\n")
    has_genai = False

# === РЕГИСТРАЦИЯ РАБОЧЕЙ СРЕДЫ ===
try:
    # ИСПРАВЛЕНО: абсолютный импорт вместо относительного
    from AIEngineer.ai_engineer_workbench import AIEngineerWorkbench
    FreeCADGui.addWorkbench(AIEngineerWorkbench())
    FreeCAD.Console.PrintMessage("[AIEngineer] ✓ Workbench registered successfully\n")
    workbench_ok = True
except ImportError as ex:
    FreeCAD.Console.PrintError(
        f"[AIEngineer] ✗ Failed to import workbench: {ex}\n"
        "[AIEngineer]   Check that ai_engineer_workbench.py exists\n"
    )
    workbench_ok = False
except Exception as ex:
    FreeCAD.Console.PrintError(
        f"[AIEngineer] ✗ Workbench initialization failed: {ex}\n"
    )
    workbench_ok = False

# === ИТОГОВОЕ СООБЩЕНИЕ ===
FreeCAD.Console.PrintMessage("=" * 60 + "\n")

all_deps_ok = has_grpc and has_protobuf and has_genai

if all_deps_ok and workbench_ok:
    FreeCAD.Console.PrintMessage(
        "[AIEngineer] ✓ Initialization complete - All systems ready!\n"
        "=" * 60 + "\n"
    )
elif workbench_ok:
    missing = []
    if not has_grpc:
        missing.append("grpc")
    if not has_protobuf:
        missing.append("protobuf")
    if not has_genai:
        missing.append("genai")
    
    FreeCAD.Console.PrintWarning(
        f"[AIEngineer] ⚠ Missing: {', '.join(missing)}\n"
        "[AIEngineer] ⚠ Workbench loaded with limited functionality\n"
        "=" * 60 + "\n"
        "\n"
        "To install missing packages, run in FreeCAD Python Console:\n"
        "\n"
        "  import subprocess\n"
        "  import sys\n"
        "  subprocess.run([sys.executable, '-m', 'pip', 'install',\n"
        "                  'grpcio', 'protobuf', 'google-generativeai'])\n"
        "\n"
        "Then restart FreeCAD.\n"
        "=" * 60 + "\n"
    )
else:
    FreeCAD.Console.PrintError(
        "[AIEngineer] ✗ Initialization failed\n"
        "=" * 60 + "\n"
    )