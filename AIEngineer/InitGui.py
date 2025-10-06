# -*- coding: utf-8 -*-
"""
Модуль инициализации рабочей среды AIEngineer для FreeCAD.
=============================================================

Выполняет:
- Проверку наличия необходимых AI-библиотек
- Проверку конфигурации .env файла
- Регистрацию рабочей среды AIEngineer в FreeCAD

.. module:: AIEngineer
"""

import FreeCAD
import FreeCADGui

# === ПРОВЕРКА ЗАВИСИМОСТЕЙ ===
FreeCAD.Console.PrintMessage('\n' + '=' * 60 + '\n')
FreeCAD.Console.PrintMessage('[AIEngineer] Checking dependencies...\n')
FreeCAD.Console.PrintMessage('=' * 60 + '\n')

# Проверка gRPC
has_grpc: bool = False
try:
    import grpc
    try:
        from grpc._cython import cygrpc
        FreeCAD.Console.PrintMessage(f'[AIEngineer] ✓ gRPC v{grpc.__version__}\n')
        has_grpc = True
    except ImportError:
        FreeCAD.Console.PrintWarning(
            '[AIEngineer] ✗ gRPC cygrpc module not found\n'
            '[AIEngineer]   Trying to continue anyway...\n'
        )
        has_grpc = False
except ImportError:
    FreeCAD.Console.PrintWarning('[AIEngineer] ✗ gRPC not found\n')
    has_grpc = False
except Exception as ex:
    FreeCAD.Console.PrintError(f'[AIEngineer] ✗ gRPC error: {ex}\n')
    has_grpc = False

# Проверка Protobuf
has_protobuf: bool = False
try:
    import google.protobuf
    FreeCAD.Console.PrintMessage('[AIEngineer] ✓ Protocol Buffers\n')
    has_protobuf = True
except ImportError:
    FreeCAD.Console.PrintWarning('[AIEngineer] ✗ Protocol Buffers not found\n')
    has_protobuf = False
except Exception as ex:
    FreeCAD.Console.PrintError(f'[AIEngineer] ✗ Protobuf error: {ex}\n')
    has_protobuf = False

# Проверка Google Generative AI
has_genai: bool = False
try:
    import google.generativeai
    FreeCAD.Console.PrintMessage('[AIEngineer] ✓ Google Generative AI\n')
    has_genai = True
except ImportError:
    FreeCAD.Console.PrintWarning('[AIEngineer] ✗ Google Generative AI not found\n')
    has_genai = False
except Exception as ex:
    FreeCAD.Console.PrintError(f'[AIEngineer] ✗ Generative AI error: {ex}\n')
    has_genai = False

# === ПРОВЕРКА КОНФИГУРАЦИИ .ENV ===
env_ok: bool = False
api_key_found: bool = False

try:
    from AIEngineer.utils import load_env, get_api_key, ENV_FILE
    
    env_vars = load_env()
    api_key: str = get_api_key()
    
    if ENV_FILE.exists():
        FreeCAD.Console.PrintMessage(f'[AIEngineer] ✓ .env file found: {ENV_FILE}\n')
        env_ok = True
    else:
        FreeCAD.Console.PrintWarning(
            f'[AIEngineer] ⚠ .env file not found: {ENV_FILE}\n'
            '[AIEngineer]   Create it via AI Settings dialog\n'
        )
    
    if api_key:
        FreeCAD.Console.PrintMessage('[AIEngineer] ✓ API key configured\n')
        api_key_found = True
    else:
        FreeCAD.Console.PrintWarning(
            '[AIEngineer] ⚠ API key not found\n'
            '[AIEngineer]   Configure it via AI Settings (⚙️ icon)\n'
        )
        
except Exception as ex:
    FreeCAD.Console.PrintError(f'[AIEngineer] ✗ Configuration check failed: {ex}\n')

# === РЕГИСТРАЦИЯ РАБОЧЕЙ СРЕДЫ ===
workbench_ok: bool = False
try:
    from AIEngineer.ai_engineer_workbench import AIEngineerWorkbench
    FreeCADGui.addWorkbench(AIEngineerWorkbench())
    FreeCAD.Console.PrintMessage('[AIEngineer] ✓ Workbench registered successfully\n')
    workbench_ok = True
except ImportError as ex:
    FreeCAD.Console.PrintError(
        f'[AIEngineer] ✗ Failed to import workbench: {ex}\n'
        '[AIEngineer]   Check that ai_engineer_workbench.py exists\n'
    )
    workbench_ok = False
except Exception as ex:
    FreeCAD.Console.PrintError(
        f'[AIEngineer] ✗ Workbench initialization failed: {ex}\n'
    )
    workbench_ok = False

# === ИТОГОВОЕ СООБЩЕНИЕ ===
FreeCAD.Console.PrintMessage('=' * 60 + '\n')

all_deps_ok: bool = has_grpc and has_protobuf and has_genai

if all_deps_ok and workbench_ok and api_key_found:
    FreeCAD.Console.PrintMessage(
        '[AIEngineer] ✓ Initialization complete - All systems ready!\n'
        '=' * 60 + '\n'
    )
elif workbench_ok:
    missing: list = []
    warnings: list = []
    
    # Проверка зависимостей
    if not has_grpc:
        missing.append('grpc')
    if not has_protobuf:
        missing.append('protobuf')
    if not has_genai:
        missing.append('genai')
    
    # Проверка конфигурации
    if not api_key_found:
        warnings.append('API key not configured')
    if not env_ok:
        warnings.append('.env file missing')
    
    if missing:
        FreeCAD.Console.PrintWarning(
            f'[AIEngineer] ⚠ Missing dependencies: {", ".join(missing)}\n'
        )
    
    if warnings:
        FreeCAD.Console.PrintWarning(
            f'[AIEngineer] ⚠ Configuration issues: {", ".join(warnings)}\n'
        )
    
    FreeCAD.Console.PrintWarning(
        '[AIEngineer] ⚠ Workbench loaded with limited functionality\n'
        '=' * 60 + '\n'
    )
    
    if missing:
        FreeCAD.Console.PrintMessage(
            '\nTo install missing packages, run in FreeCAD Python Console:\n'
            '\n'
            '  import subprocess\n'
            '  import sys\n'
            '  subprocess.run([sys.executable, "-m", "pip", "install",\n'
            '                  "grpcio", "protobuf", "google-generativeai"])\n'
            '\n'
            'Then restart FreeCAD.\n'
        )
    
    if not api_key_found:
        FreeCAD.Console.PrintMessage(
            '\nTo configure API key:\n'
            '1. Switch to AI Engineer workbench\n'
            '2. Click AI Settings (⚙️ icon)\n'
            '3. Enter your Google Gemini API key\n'
            '4. Get free key at: https://aistudio.google.com/app/apikey\n'
        )
    
    FreeCAD.Console.PrintMessage('=' * 60 + '\n')
else:
    FreeCAD.Console.PrintError(
        '[AIEngineer] ✗ Initialization failed\n'
        '=' * 60 + '\n'
    )