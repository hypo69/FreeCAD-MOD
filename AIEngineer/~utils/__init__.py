# # -*- coding: utf-8 -*-
# #! .pyenv/bin/python3



# """ 
# Коллекция небольших утилит, предназначенных для упрощения часто выполняемых задач программирования.
# Включает инструменты для конвертации данных, работы с файлами и форматированного вывода.
# """

# Импорты утилит в алфавитном порядке
from .convertors import (
    TextToImageGenerator,
    base64_to_tmpfile,
    base64encode,
    csv2dict,
    csv2ns,
    decode_unicode_escape,
    dict2csv,
    dict2html,
    dict2ns,
    dict2xls,
    dict2xml,
    dot2png,
    escape2html,
    html2dict,
    html2escape,
    html2ns,
    html2text,
    html2text_file,
    json2csv,
    json2ns,
    json2xls,
    json2xml,
    md2dict,
    ns2csv,
    ns2dict,
    ns2xls,
    ns2xml,
    replace_key_in_dict,
    speech_recognizer,
    text2speech,
    webp2png,
    xls2dict
)

from .csv import (
    read_csv_as_dict,
    read_csv_as_ns,
    read_csv_file,
    save_csv_file
)

from .date_time import (
    TimeoutCheck
)

from .file import (
    get_directory_names,
    get_filenames,
    read_text_file,
    recursively_get_file_path,
    recursively_read_text_files,
    recursively_yield_file_path,  
    remove_bom,
    save_text_file
)

from .image import (
    save_image,
    save_image_from_url,
      random_image,
)

from .jjson import (
    j_dumps,
    j_loads,
    j_loads_ns
)

from .pdf import (
    PDFUtils
)

from .printer import (
    pprint
)

from .string import (
    ProductFieldsValidator,
    StringFormatter,
    normalize_string,
    normalize_int,
    normalize_float,
    normalize_boolean
)

from .url import (
    extract_url_params, 
    is_url
)

from .video import (
    save_video_from_url
)

from .path import get_relative_path



# -*- coding: utf-8 -*-
"""
Вспомогательные функции и общие константы для AIEngineer.
"""

import FreeCAD
import os
import json
import datetime
from pathlib import Path
from typing import Optional

# Единый путь к данным аддона — используется ВЕЗДЕ
AI_DATA_DIR: Path = Path(FreeCAD.getUserAppDataDir()) / 'AIEngineer' / 'data'
AI_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Путь к файлу .env
ENV_FILE: Path = AI_DATA_DIR.parent / '.env'

# Путь к иконкам
ICON_PATH: str = str(Path(__file__).parent / 'Resources' / 'icons')


def get_icon(icon_name: str) -> str:
    """
    Функция возвращает полный путь к иконке или пустую строку, если файл не найден.
    
    Args:
        icon_name (str): Имя файла иконки.
    
    Returns:
        str: Полный путь к иконке или пустая строка.
    """
    icon_file: str = os.path.join(ICON_PATH, icon_name)
    if not os.path.exists(icon_file):
        FreeCAD.Console.PrintWarning(f'[AIEngineer] Icon not found: {icon_file}\n')
        return ''
    return icon_file


def get_image_files() -> list[str]:
    """
    Функция возвращает список изображений в AI_DATA_DIR.
    
    Returns:
        list[str]: Отсортированный список имен файлов изображений.
    """
    exts: set = {'.png', '.jpg', '.jpeg', '.bmp', '.svg', '.gif'}
    return sorted([
        f for f in os.listdir(AI_DATA_DIR)
        if Path(f).suffix.lower() in exts
    ])


def get_text_files() -> list[str]:
    """
    Функция возвращает список текстовых файлов в AI_DATA_DIR.
    
    Returns:
        list[str]: Отсортированный список имен текстовых файлов.
    """
    exts: set = {'.txt', '.md'}
    return sorted([
        f for f in os.listdir(AI_DATA_DIR)
        if Path(f).suffix.lower() in exts
    ])


def safe_remove(filepath: Path) -> bool:
    """
    Функция выполняет безопасное удаление файла.
    
    Args:
        filepath (Path): Путь к файлу для удаления.
    
    Returns:
        bool: True если удаление успешно, False в случае ошибки.
    """
    try:
        os.remove(filepath)
        return True
    except Exception as ex:
        FreeCAD.Console.PrintError(f'[AIEngineer] Delete error: {ex}\n')
        return False


def save_ai_response_to_history(prompt: str, response: str) -> None:
    """
    Функция сохраняет диалог (prompt + response) в историю.
    
    Args:
        prompt (str): Текст промпта пользователя.
        response (str): Ответ от AI.
    
    Returns:
        None
    """
    history_dir: Path = AI_DATA_DIR / 'ai_history'
    history_dir.mkdir(parents=True, exist_ok=True)
    timestamp: str = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    filepath: Path = history_dir / f'ai_response_{timestamp}.json'
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': timestamp,
                'prompt': prompt,
                'response': response,
                'provider': 'gemini'
            }, f, ensure_ascii=False, indent=2)
        FreeCAD.Console.PrintMessage(f'[AIEngineer] Response saved to history: {filepath.name}\n')
    except Exception as ex:
        FreeCAD.Console.PrintError(f'[AIEngineer] Failed to save history: {ex}\n')


def load_env() -> dict[str, str]:
    """
    Функция загружает переменные окружения из файла .env.
    
    Returns:
        dict[str, str]: Словарь с переменными окружения.
    
    Example:
        >>> env_vars = load_env()
        >>> api_key = env_vars.get('GEMINI_API_KEY')
    """
    env_vars: dict[str, str] = {}
    
    if not ENV_FILE.exists():
        FreeCAD.Console.PrintMessage(f'[AIEngineer] .env file not found: {ENV_FILE}\n')
        return env_vars
    
    try:
        with open(ENV_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Пропуск пустых строк и комментариев
                if not line or line.startswith('#'):
                    continue
                
                # Парсинг строки KEY=VALUE
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Удаление кавычек, если есть
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    
                    env_vars[key] = value
        
        FreeCAD.Console.PrintMessage(f'[AIEngineer] Loaded {len(env_vars)} variables from .env\n')
        return env_vars
        
    except Exception as ex:
        FreeCAD.Console.PrintError(f'[AIEngineer] Failed to load .env: {ex}\n')
        return env_vars


def save_to_env(key: str, value: str) -> bool:
    """
    Функция сохраняет или обновляет переменную в файле .env.
    
    Args:
        key (str): Имя переменной окружения.
        value (str): Значение переменной.
    
    Returns:
        bool: True если сохранение успешно, False в случае ошибки.
    
    Example:
        >>> save_to_env('GEMINI_API_KEY', 'your-api-key-here')
        True
    """
    existing_vars: dict[str, str] = load_env()
    existing_vars[key] = value
    
    try:
        with open(ENV_FILE, 'w', encoding='utf-8') as f:
            f.write('# AIEngineer Configuration\n')
            f.write(f'# Generated: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n\n')
            
            for k, v in existing_vars.items():
                # Экранирование значений с пробелами
                if ' ' in v or '"' in v:
                    v = f'"{v}"'
                f.write(f'{k}={v}\n')
        
        FreeCAD.Console.PrintMessage(f'[AIEngineer] Saved {key} to .env\n')
        return True
        
    except Exception as ex:
        FreeCAD.Console.PrintError(f'[AIEngineer] Failed to save to .env: {ex}\n')
        return False


def get_api_key() -> str:
    """
    Функция получает API-ключ из .env файла или QSettings.
    Приоритет: .env > QSettings.
    
    Returns:
        str: API-ключ или пустая строка, если не найден.
    """
    # Попытка загрузки из .env
    env_vars: dict[str, str] = load_env()
    api_key: str = env_vars.get('GEMINI_API_KEY', '')
    
    if api_key:
        FreeCAD.Console.PrintMessage('[AIEngineer] API key loaded from .env\n')
        return api_key
    
    # Fallback на QSettings
    from PySide import QtCore
    settings = QtCore.QSettings('FreeCAD', 'AIEngineer')
    api_key = settings.value('api_key', '')
    
    if api_key:
        FreeCAD.Console.PrintMessage('[AIEngineer] API key loaded from QSettings\n')
    else:
        FreeCAD.Console.PrintWarning('[AIEngineer] API key not found\n')
    
    return api_key


def get_image_bytes(image_path: str) -> Optional[bytes]:
    """
    Функция считывает изображение как байты.
    
    Args:
        image_path (str): Путь к файлу изображения.
    
    Returns:
        Optional[bytes]: Байты изображения или None при ошибке.
    """
    try:
        with open(image_path, 'rb') as f:
            return f.read()
    except Exception as ex:
        FreeCAD.Console.PrintError(f'[AIEngineer] Failed to read image: {ex}\n')
        return None


def normalize_answer(answer: str) -> str:
    """
    Функция нормализует ответ от AI, удаляя markdown разметку кода и лишние пробелы.
    
    Args:
        answer (str): Исходный ответ.
    
    Returns:
        str: Нормализованный ответ.
    """
    if not answer:
        return ''
    
    # Удаление markdown блоков кода
    import re
    answer = re.sub(r'```[a-zA-Z]*\n', '', answer)
    answer = re.sub(r'```', '', answer)
    
    # Удаление лишних пробелов и переносов строк
    answer = answer.strip()
    
    return answer


# def j_dumps(data: dict | list, filepath: Path) -> bool:
#     """
#     Функция сохраняет данные в JSON-файл.
    
#     Args:
#         data (dict | list): Данные для сохранения.
#         filepath (Path): Путь к файлу.
    
#     Returns:
#         bool: True если сохранение успешно, False в случае ошибки.
#     """
#     try:
#         filepath.parent.mkdir(parents=True, exist_ok=True)
#         with open(filepath, 'w', encoding='utf-8') as f:
#             json.dump(data, f, ensure_ascii=False, indent=2)
#         return True
#     except Exception as ex:
#         FreeCAD.Console.PrintError(f'[AIEngineer] j_dumps error: {ex}\n')
#         return False


# def j_loads(filepath: Path) -> dict | list | None:
#     """
#     Функция загружает данные из JSON-файла.
    
#     Args:
#         filepath (Path): Путь к файлу.
    
#     Returns:
#         dict | list | None: Загруженные данные или None при ошибке.
#     """
#     if not filepath.exists():
#         FreeCAD.Console.PrintWarning(f'[AIEngineer] File not found: {filepath}\n')
#         return None
    
#     try:
#         with open(filepath, 'r', encoding='utf-8') as f:
#             return json.load(f)
#     except Exception as ex:
#         FreeCAD.Console.PrintError(f'[AIEngineer] j_loads error: {ex}\n')
#         return None


# def pprint(data: str, *args, **kwargs) -> None:
#     """
#     Функция выводит данные в консоль FreeCAD.
    
#     Args:
#         data (str): Данные для вывода.
#     """
#     FreeCAD.Console.PrintMessage(f'{data}\n')