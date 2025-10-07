## \file /src/utils/jjson.py
# -*- coding: utf-8 -*-
#! .pyenv/bin/python3

"""
Модуль JSON утилит для работы с JSON данными.
==================================================
Предоставляет функции для загрузки, сохранения, обработки и поиска данных в JSON объектах и файлах.

Основные функции:
- `j_dumps(data, file_path, ensure_ascii, mode, exc_info)`: Сохраняет Python объекты (словари, списки, SimpleNamespace, строки JSON) 
                                                             в JSON файл или возвращает их как Python объект (`dict`, `list`) после обработки.
                                                             Поддерживает различные режимы записи (перезапись, добавление в начало/конец).
  Пример: `j_dumps({'key': 'value'}, Path('output.json'))` возвращает `True` в случае успеха.
          `processed_obj = j_dumps({'key': 'value'})` возвращает обработанный словарь `{'key': 'value'}`.
- `j_loads(jjson, ordered)`: Загружает JSON данные из файла, строки, словаря, списка или SimpleNamespace.
                             Может обрабатывать директории с JSON файлами. Возвращает `dict` или `list`.
                             При ошибке возвращает `{}`.
  Пример: `data = j_loads(Path('input.json'))`
- `j_loads_ns(jjson, ordered)`: Аналогично `j_loads`, но конвертирует результат в `SimpleNamespace` или список `SimpleNamespace`.
                                При ошибке или если `j_loads` вернул пустой результат, возвращает `{}`.
  Пример: `ns_data = j_loads_ns(Path('input.json'))`
- `sanitize_json_files(path)`: Проверяет и "санитизирует" JSON файлы в указанной директории или отдельный JSON файл.
                               Невалидные файлы переименовываются (добавляется суффикс `.sanitized`). Возвращает `bool`.
  Пример: `sanitize_json_files(Path('./data_dir/'))`
- `find_keys(obj, keys_to_find, found)`: Рекурсивно ищет значения по заданным ключам во вложенной структуре данных 
                                        (словарь или список). Возвращает словарь, где ключи - это искомые ключи,
                                        а значения - списки найденных значений.
  Пример: `found_values = find_keys(my_data, ['id', 'name'])`

Внутренние вспомогательные функции:
- `_convert_to_dict(value)`: Рекурсивно конвертирует объекты SimpleNamespace и вложенные структуры в словари.
- `_read_existing_data(path, exc_info)`: Читает и парсит JSON данные из указанного файла. Возвращает `dict` или `list`, либо `{}` при ошибке.
- `_merge_data(data, existing_data, mode)`: Объединяет новые данные (`data`) с существующими (`existing_data`) 
                                          в соответствии с указанным режимом (`mode`). Возвращает объединенный `dict` или `list`, либо `{}` при ошибке.
- `_decode_strings(data)`: Рекурсивно декодирует строки (unicode_escape) в структуре данных.
- `_string_to_dict(json_string)`: Удаляет Markdown обёртки (```json ... ```) из строки и парсит её как JSON. Возвращает `dict` или `list`, либо `{}` при ошибке.

Класс конфигурации:
- `Config`: Содержит константы для режимов записи файлов (`MODE_WRITE`, `MODE_APPEND_START`, `MODE_APPEND_END`).

 ```rst
 .. module:: src.utils.jjson
 ```
"""
import json
import codecs
import re # Используется в _string_to_dict
from pathlib import Path
from tkinter.filedialog import LoadFileDialog
from typing import Any, List as TypingList, Dict as TypingDict # TypingList/Dict for find_keys as per original.
from collections.abc import Mapping, Sequence
from types import SimpleNamespace
from dataclasses import dataclass
from json_repair import repair_json
#import json_repair


from src.logger.logger import logger
from .convertors.dict import dict2ns
from .convertors.list import list2dict


@dataclass
class Config:
    """
    Конфигурационный класс для хранения констант режимов записи.
    
    Attributes:
        MODE_WRITE (str): Режим перезаписи файла.
        MODE_APPEND_START (str): Режим добавления данных в начало файла (логическое добавление).
        MODE_APPEND_END (str): Режим добавления данных в конец файла (логическое добавление).
    """
    MODE_WRITE:str = 'w'
    MODE_APPEND_START:str = 'a+'
    MODE_APPEND_END:str = '+a'

def _convert_to_dict(value: Any) -> Any:
    """
    Функция рекурсивно конвертирует объекты SimpleNamespace и вложенные структуры в словари.

    Args:
        value (Any): Значение для конвертации. Может быть SimpleNamespace, словарем, списком или другим типом.

    Returns:
        Any: Конвертированное значение. SimpleNamespace и словари преобразуются в `dict`,
             списки обрабатываются рекурсивно. Другие типы возвращаются как есть.
    
    Example:
        >>> class MyNS(SimpleNamespace): pass
        >>> ns = MyNS(a=1, b=MyNS(c=2))
        >>> _convert_to_dict(ns)
        {'a': 1, 'b': {'c': 2}}
        >>> _convert_to_dict([MyNS(x=10), 20])
        [{'x': 10}, 20]
    """
    # Рекурсивная конвертация SimpleNamespace в dict
    if isinstance(value, SimpleNamespace):
        return {key: _convert_to_dict(val) for key, val in vars(value).items()}
    # Рекурсивная конвертация словарей (для обработки вложенных SimpleNamespace)
    if isinstance(value, dict):
        return {key: _convert_to_dict(val) for key, val in value.items()}
    # Рекурсивная конвертация списков
    if isinstance(value, list):
        return list2dict(value)
    # Возврат значения без изменений, если это не SimpleNamespace, dict или list
    return value

def _read_existing_data(path: Path, exc_info: bool = True) -> dict[Any, Any] | list[Any]:
    """
    Функция читает и парсит JSON данные из указанного файла.

    Args:
        path (Path): Путь к JSON файлу.
        exc_info (bool, optional): Логировать ли информацию об исключении. По умолчанию `True`.

    Returns:
        dict[Any, Any] | list[Any]: Словарь или список с данными из JSON файла. 
                                     Возвращает пустой словарь, если файл не найден, поврежден или возникает другая ошибка чтения.
    
    Example:
        >>> # Предположим, 'data.json' содержит {"key": "value"}
        >>> # _read_existing_data(Path('data.json')) 
        >>> # {'key': 'value'}
        >>> # _read_existing_data(Path('non_existent.json'))
        >>> # {} 
        # Примеры закомментированы, так как требуют наличия файлов
    """
    try:
        # Чтение и парсинг JSON из файла
        return json.loads(path.read_text(encoding='utf-8'))
    except json.JSONDecodeError as ex:
        logger.error(f'Error decoding existing JSON in {path}: {ex}', ex, exc_info=exc_info)
        return {}
    except FileNotFoundError: # Обработка случая, если файл не найден
        logger.error(f'File not found for reading existing data: {path}', None, exc_info=exc_info)
        return {}
    except Exception as ex:
        logger.error(f'Error reading {path=}: {ex}', ex, exc_info=exc_info)
        return {}

def _merge_data(
    data: dict[Any, Any] | list[Any], 
    existing_data: dict[Any, Any] | list[Any], 
    mode: str
) -> dict[Any, Any] | list[Any]:
    """
    Функция объединяет новые данные (`data`) с существующими (`existing_data`) 
    в соответствии с указанным режимом (`mode`).

    Args:
        data (dict[Any, Any] | list[Any]): Новые данные (словарь или список).
        existing_data (dict[Any, Any] | list[Any]): Существующие данные (словарь или список).
        mode (str): Режим объединения. Поддерживаются `Config.MODE_APPEND_START` и `Config.MODE_APPEND_END`.

    Returns:
        dict[Any, Any] | list[Any]: Объединенные данные. Если типы несовместимы или режим не предполагает слияния,
                                     может вернуть `data` или `existing_data` на основе логики режима.
                                     Возвращает `data` по умолчанию, если режим не `a+` или `+a`.
                                     В случае ошибки возвращает пустой словарь.
    
    Example:
        >>> _merge_data({'c': 3}, {'a': 1, 'b': 2}, Config.MODE_APPEND_START)
        {'a': 1, 'b': 2, 'c': 3}
        >>> _merge_data([3], [1, 2], Config.MODE_APPEND_START)
        [3, 1, 2]
        >>> _merge_data({'c': 3}, {'a': 1, 'b': 2}, Config.MODE_APPEND_END)
        {'a': 1, 'b': 2, 'c': 3}
        >>> _merge_data([3], [1, 2], Config.MODE_APPEND_END)
        [1, 2, 3]
    """
    # Объединение данных в зависимости от режима
    try:
        if mode == Config.MODE_APPEND_START:
            # Добавление новых данных в начало (для списков) или обновление существующего словаря (для словарей)
            if isinstance(data, list) and isinstance(existing_data, list):
               return data + existing_data
            if isinstance(data, dict) and isinstance(existing_data, dict):
                 merged_dict: dict[Any, Any] = existing_data.copy()
                 merged_dict.update(data) # Ключи из 'data' перезапишут ключи в 'existing_data'
                 return merged_dict
            logger.warning(f"Cannot merge data for MODE_APPEND_START due to type mismatch or unsupported types. Returning existing_data. Data type: {type(data)}, Existing data type: {type(existing_data)}")
            return existing_data # Приоритет существующим данным
        elif mode == Config.MODE_APPEND_END:
            # Добавление новых данных в конец (для списков) или обновление нового словаря существующими данными (для словарей)
            if isinstance(data, list) and isinstance(existing_data, list):
                return existing_data + data
            if isinstance(data, dict) and isinstance(existing_data, dict):
                 merged_dict = data.copy()
                 merged_dict.update(existing_data) # Ключи из 'existing_data' перезапишут ключи в 'data'
                 return merged_dict
            logger.warning(f"Cannot merge data for MODE_APPEND_END due to type mismatch or unsupported types. Returning data. Data type: {type(data)}, Existing data type: {type(existing_data)}")
            return data # Приоритет новым данным
        # Если режим не предполагает слияния (например, 'w'), возвращаются новые данные
        return data
    except Exception as ex:
        logger.error(f'Error merging data: {ex}', ex, exc_info=True)
        return {} # Возврат пустого словаря в случае непредвиденной ошибки


def j_dumps(
    data: dict[Any, Any] | SimpleNamespace | list[Any] | str,
    file_path: Path | str | None = None,
    indent:int = 4,
    ensure_ascii: bool = False,
    mode: str = Config.MODE_WRITE,
    exc_info: bool = True,
) -> bool | dict[Any, Any] | list[Any] | None:
    """
    Сериализует Python объект в JSON строку или сохраняет его в файл.

    Если `file_path` указан, функция пытается записать данные в файл.
    Возвращает `True` при успешной записи, `False` в случае ошибки.

    Если `file_path` не указан (`None`), функция обрабатывает `data` 
    (например, конвертирует из `SimpleNamespace` или JSON-строки) и возвращает 
    получившийся Python объект (`dict` или `list`). Возвращает `None` при ошибке обработки.

    Args:
        data (dict | SimpleNamespace | list | str): Данные для сериализации. Могут быть словарем,
            `SimpleNamespace`, списком или JSON-строкой (которая будет предварительно обработана).
        file_path (Path | str | None, optional): Путь к файлу для сохранения.
            Если `None`, данные не сохраняются, а возвращаются после обработки. По умолчанию `None`.
        ensure_ascii (bool, optional): Если `False`, символы не-ASCII будут сохранены как есть.
            Если `True`, они будут экранированы. По умолчанию `False`.
        mode (str, optional): Режим записи файла, если `file_path` указан.
            Поддерживаются `Config.MODE_WRITE` (перезапись), `Config.MODE_APPEND_START` (добавление "в начало"),
            `Config.MODE_APPEND_END` (добавление "в конец"). По умолчанию `Config.MODE_WRITE`.
            Режимы добавления логически объединяют данные перед записью.
        exc_info (bool, optional): Логировать ли полную информацию об исключении. По умолчанию `True`.

    Returns:
        bool | dict | list | None:
            - `True`: если `file_path` указан и запись в файл прошла успешно.
            - `False`: если `file_path` указан и произошла ошибка записи.
            - `dict | list`: если `file_path` не указан, возвращается обработанный Python объект.
            - `None`: если `file_path` не указан и произошла ошибка обработки данных.
    
    Example:
        >>> data_dict = {'key': 'value', 'num': 123}
        >>> # j_dumps(data_dict, 'output.json')  # Записывает в файл, вернет True/False (требует файл)
        >>> class MyNS(SimpleNamespace): pass
        >>> ns_data = MyNS(name='test')
        >>> processed_data = j_dumps(ns_data) 
        >>> isinstance(processed_data, dict)
        True
        >>> processed_data['name']
        'test'
        >>> invalid_json_string = "{'key': 'value'}" 
        >>> result = j_dumps(invalid_json_string) 
        >>> result is None 
        True
    """
    processed_data: dict[Any, Any] | list[Any] | None
    path: Path | None = None

    # Начальная обработка входных данных
    if isinstance(data, str):
        data_as_obj: dict[Any, Any] | list[Any] = _string_to_dict(data)
        # Если _string_to_dict вернул пусто, но строка была непустой и не являлась "{}" или "[]"
        if not data_as_obj and data.strip() and data.strip() not in ('{}', '[]'):
            try:
                repaired_json_str: str = repair_json(data, return_objects=True)
                processed_data = json.loads(repaired_json_str)
            except Exception as ex_repair:
                logger.error(f'Error repairing/parsing JSON string (first 100 chars): "{data[:100]}..."', ex_repair, exc_info=exc_info)
                return False if file_path else None
        else:
            processed_data = data_as_obj

    if isinstance(processed_data, (SimpleNamespace, dict, list)):
        processed_data = _convert_to_dict(processed_data)
    else:
        logger.error(f'Unsupported data type for j_dumps: {type(processed_data)}', None, exc_info=exc_info)
        return False if file_path else None

    if processed_data is None : # Не должно случиться, если _convert_to_dict/_string_to_dict работают как ожидается
        logger.error(f'Data became None after initial processing. Original type: {type(processed_data)}', None, exc_info=exc_info)
        return False if file_path else None

    if file_path:
        path = Path(file_path)

    if mode not in {Config.MODE_WRITE, Config.MODE_APPEND_START, Config.MODE_APPEND_END}:
        logger.warning(f"Unsupported mode '{mode}'. Defaulting to '{Config.MODE_WRITE}'.")
        mode = Config.MODE_WRITE

    if path:
        final_data_to_write: dict[Any, Any] | list[Any] = processed_data
        
        if mode in {Config.MODE_APPEND_START, Config.MODE_APPEND_END}:
            if path.exists() and path.is_file(): # Провера, что это файл
                existing_data: dict[Any, Any] | list[Any] = _read_existing_data(path, exc_info)
                # Проверка типов перед слиянием
                if isinstance(processed_data, (dict, list)) and isinstance(existing_data, (dict, list)):
                    final_data_to_write = _merge_data(processed_data, existing_data, mode)
                    if not final_data_to_write and (processed_data or existing_data):
                         logger.warning(f"Data merging resulted in empty data for {path}. Check merge logic and data types.")
                elif not isinstance(existing_data, (dict, list)): # existing_data не удалось прочитать корректно
                    logger.warning(f"Could not properly read or parse existing data from {path} for merge. Read data type: {type(existing_data)}. Writing new data only.")
                    # final_data_to_write остается processed_data
            elif not path.exists() : # Файл не существует, режим добавления работает как обычная запись
                logger.info(f"File {path} does not exist for append mode. Will create a new file.")

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open(Config.MODE_WRITE, encoding='utf-8') as f: # Слияние выполнено, пишем всегда в 'w'
                json.dump(final_data_to_write, f, ensure_ascii=ensure_ascii, indent = indent)
            return True
        except Exception as ex:
            logger.error(f'Failed to write data to {path}:', ex, exc_info=exc_info)
            return False
    else: # file_path is None
        return processed_data


def _decode_strings(data: Any) -> Any:
    """
    Функция рекурсивно декодирует строки в структуре данных из формата 'unicode_escape'.

    Это полезно для строк, которые могли быть экранированы, например, при передаче через JSON
    и содержат последовательности вида `\\uXXXX`.

    Args:
        data (Any): Структура данных (строка, список, словарь) для декодирования.

    Returns:
        Any: Структура данных с рекурсивно декодированными строками.
             Если элемент не является строкой, списком или словарем, он возвращается без изменений.
    
    Example:
        >>> _decode_strings("hello\\u0020world")
        'hello world'
        >>> _decode_strings({"key": "value\\u0020test"})
        {'key': 'value test'}
        >>> _decode_strings(["item1", "item\\u0032"])
        ['item1', 'item2']
    """
    if isinstance(data, str):
        try:
           return codecs.decode(data, 'unicode_escape')
        except Exception:
            return data # Возврат исходной строки, если декодирование не удалось
    if isinstance(data, list):
        return [_decode_strings(item) for item in data]
    if isinstance(data, dict):
        return {
            _decode_strings(key): _decode_strings(value) for key, value in data.items()
        }
    return data

def _string_to_dict(json_string: str, return_objects:bool = False) -> dict[Any, Any] | list[Any]:
    """
    Функция удаляет Markdown-обёртки (например, ```json ... ```) из строки
    и затем парсит её как JSON, возвращая словарь или список.

    Args:
        json_string (str): Строка, потенциально содержащая JSON и Markdown-обёртки.

    Returns:
        dict[Any, Any] | list[Any]: Словарь или список, полученный после парсинга JSON.
                                     Возвращает пустой словарь, если строка пуста, является невалидным JSON
                                     или происходит ошибка парсинга.
    
    Example:
        >>> _string_to_dict('```json\\n{"key": "value"}\\n```')
        {'key': 'value'}
        >>> _string_to_dict('{"name": "test", "items": [1, 2]}')
        {'name': 'test', 'items': [1, 2]}
        >>> _string_to_dict('invalid json')
        {}
    """
    result: dict[Any, Any] | list[Any] = {}
    if not isinstance(json_string, str):
        logger.warning(f'_string_to_dict expects a string, got {type(json_string)}. Returning empty dict.')
        return {}

    cleaned_string: str = json_string.strip()
    
    # Улучшенный regex для удаления ```json ... ``` и просто ``` ... ```
    if cleaned_string.startswith('```'):
        cleaned_string = re.sub(r'^```(?:json)?\s*', '', cleaned_string, count=1)
        cleaned_string = re.sub(r'\s*```$', '', cleaned_string, count=1)
        cleaned_string = cleaned_string.strip()
        
    if not cleaned_string:
        return {}

    try:
        result:dict = json.loads(cleaned_string)
    except json.JSONDecodeError as ex:
        logger.error(f'JSON parsing error for string (first 100 chars): "{cleaned_string[:100]}..."', ex, False)
        logger.debug(f'Trying repair_json')
        try:
            repaired_result:dict|bool = repair_json(cleaned_string)
            result:dict = json.loads(repaired_result)
        except Exception as ex:
            logger.error(f'Error in repair_json', ex)
            return {}
    except Exception as ex:
        logger.error(f'Unexpected error parsing string (first 100 chars): "{cleaned_string[:100]}..."', ex, False)
        return {}
        
    return result


def j_loads(
    jjson: dict[Any, Any] | SimpleNamespace | str | Path | list[Any], ordered: bool = True # ordered not used
) -> dict[Any, Any] | list[Any]:
    """
    Загружает JSON-совместимые данные из различных источников.

    Поддерживает загрузку из:
    - `dict`, `list`, `SimpleNamespace`: возвращаются после некоторой обработки (например, декодирование строк).
    - `str`: строка парсится как JSON (с предварительной очисткой от Markdown и попыткой "ремонта").
    - `Path`: если путь указывает на файл, он читается как JSON. Если на директорию,
              рекурсивно загружаются все `.json` файлы из нее, и результат возвращается как список.
    
    Параметр `ordered` в текущей реализации не используется для сохранения порядка элементов.

    Args:
        jjson (dict | SimpleNamespace | str | Path | list): Источник данных.
        ordered (bool, optional): Параметр для будущего использования. В текущей версии не влияет. По умолчанию `True`.

    Returns:
        dict[Any, Any] | list[Any]: Обработанные данные (словарь или список).
                                     В случае ошибки возвращает пустой словарь `{}`.
    
    Example:
        >>> # Предположим, 'data.json' содержит {"id": 1, "value": "test\\u0020data"}
        >>> # data_from_file = j_loads(Path('data.json')) 
        >>> # isinstance(data_from_file, dict) and data_from_file.get('value') == 'test data'
        >>> # True (требует файл)
        >>> data_from_string = j_loads('{"name": "example"}')
        >>> data_from_string.get('name')
        'example'
        >>> data_from_list = j_loads([{"item": "A"}, "item\\u0020B"])
        >>> isinstance(data_from_list, list) and data_from_list[1] == 'item B'
        True
        >>> # j_loads(Path('non_existent_dir/'))
        >>> # {} (требует файловую систему)
    """
    jjson_internal: Any = jjson
    if isinstance(jjson, SimpleNamespace):
        jjson_internal = vars(jjson) # Конвертация SimpleNamespace в dict для дальнейшей обработки

    try:
        if isinstance(jjson_internal, Path):
            path_obj: Path = jjson_internal
            if path_obj.is_dir():
                files: TypingList[Path] = list(path_obj.glob('*.json'))
                return [j_loads(file, ordered=ordered) for file in files] # j_loads вернет {} для невалидных файлов
            elif path_obj.is_file():
                # json.loads корректно обрабатывает \uXXXX из файла. _decode_strings здесь не нужен.
                try:
                    return json.loads(path_obj.read_text(encoding='utf-8'))
                except Exception as ex:
                    logger.error(f'Ошибка чтения словаря',ex, False)
                    try:
                        with path_obj.open('r', encoding='utf-8') as f:
                            file_content: str = f.read()
                            if not file_content:
                                logger.error(f'В файле {path_obj} Нет данных!', None, False)
                                return {}

                        repaired_json: dict| None = _string_to_dict(file_content, return_objects=True)
                        ...
                        return repaired_json 
                    except Exception as ex:
                        logger.error(f'Error reading file {path_obj}: {ex}', ex, False)
                        ...
                        return {}
                    ...
            else:
                logger.error(f'Path does not exist or is not a file/directory: {path_obj}', None, False)
                return {}
        
        if isinstance(jjson_internal, str):
            parsed_obj: dict[Any, Any] | list[Any] = _string_to_dict(jjson_internal) # _string_to_dict возвращает {} при ошибке
            return _decode_strings(parsed_obj) # Декодирование строк в полученном объекте

        if isinstance(jjson_internal, list):
            return _decode_strings(jjson_internal) # Декодирование строк в списке
        
        if isinstance(jjson_internal, dict):
            return _decode_strings(jjson_internal) # Декодирование строк в словаре
            
    except FileNotFoundError: # Эта ветка может быть не достигнута из-за проверок is_file/is_dir
        logger.error(f'File not found: {str(jjson_internal)}', None, False)
        return {}
    except json.JSONDecodeError as ex:
        log_input_repr: str = str(jjson_internal) if isinstance(jjson_internal, Path) else repr(jjson_internal)[:200]
        logger.error(f'JSON parsing error for input ({type(jjson_internal)}): {log_input_repr}...', ex, False)
        return {}
    except Exception as ex:
        log_input_repr = str(jjson_internal) if isinstance(jjson_internal, Path) else repr(jjson_internal)[:200]
        logger.error(f'Error loading data for input ({type(jjson_internal)}): {log_input_repr}...', ex, False)
        return {}
    
    logger.warning(f'j_loads received unhandled data type: {type(jjson_internal)}. Returning empty dict.')
    return {}


def j_loads_ns(
    jjson: Path | SimpleNamespace | dict[Any, Any] | str | list[Any], # Добавлен list[Any] для полноты
    ordered: bool = True # ordered not used
) -> SimpleNamespace | TypingList[SimpleNamespace | Any] | dict[Any, Any]: # dict if j_loads returns empty {}
    """
    Загружает JSON-совместимые данные и конвертирует результат в `SimpleNamespace`.

    Функция является обёрткой над `j_loads`. Если `j_loads` возвращает словарь,
    он конвертируется в `SimpleNamespace`. Если `j_loads` возвращает список,
    каждый элемент-словарь в списке конвертируется в `SimpleNamespace`.

    Args:
        jjson (Path | SimpleNamespace | dict | str | list): Источник данных, как в `j_loads`.
        ordered (bool, optional): Параметр для `j_loads`. В текущей версии не используется. По умолчанию `True`.

    Returns:
        SimpleNamespace | list[SimpleNamespace | Any] | dict:
            - `SimpleNamespace`: если загруженные данные являются словарем.
            - `list[SimpleNamespace | Any]`: если загруженные данные являются списком (элементы-словари конвертируются).
            - `dict`: пустой словарь `{}`, если `j_loads` вернул пустой результат или произошла ошибка.
    
    Example:
        >>> # Предположим, 'user.json' содержит {"name": "Alice", "age": 30}
        >>> # user_ns = j_loads_ns(Path('user.json'))
        >>> # isinstance(user_ns, SimpleNamespace) and user_ns.name == 'Alice'
        >>> # True (требует файл)
        >>> # Предположим, 'users.json' содержит [{"name": "Bob"}, {"name": "Charlie"}]
        >>> # users_list_ns = j_loads_ns(Path('users.json'))
        >>> # isinstance(users_list_ns, list) and isinstance(users_list_ns[0], SimpleNamespace)
        >>> # True (требует файл)
        >>> j_loads_ns("invalid json")
        {}
    """
    data: dict[Any, Any] | list[Any] = j_loads(jjson, ordered=ordered)
    
    if not data and isinstance(data, dict): # j_loads вернул {}, что означает ошибку или пустой JSON
        return {} 
    
    if isinstance(data, list):
        return [dict2ns(item) if isinstance(item, dict) else item for item in data]
    if isinstance(data, dict): # Включая непустые словари
        return dict2ns(data)
    
    # Если data не dict и не list (например, j_loads вернул что-то неожиданное, хотя не должен)
    # или data это пустой список (j_loads([]) -> []), то dict2ns не применим напрямую.
    # Если data пустой список, вернем его же.
    if isinstance(data, list): # Covers empty list case specifically
        return []

    return {} # Общий fallback, если data имеет неожиданный тип или j_loads вернул что-то странное

def sanitize_json_files(path: Path) -> bool:
    """
    Проверяет валидность JSON файлов в указанной директории или одного JSON файла.

    Если файл невалиден, он переименовывается путем добавления суффикса '.sanitized' к его имени.
    Если файл валиден, он остается без изменений.
    Если указанный путь не существует или не является файлом/директорией, логируется ошибка,
    и функция возвращает `False`.

    Args:
        path (Path): Путь к JSON файлу или директории, содержащей JSON файлы.

    Returns:
        bool: `True`, если все обработанные файлы валидны или были успешно "санитизированы" (переименованы).
              `False`, если путь невалиден, или если хотя бы один файл не удалось обработать.
    
    Example:
        >>> # Примеры требуют создания временных файлов и директорий.
        >>> # from pathlib import Path
        >>> # import json
        >>> # temp_dir = Path('./temp_sanitize_test')
        >>> # temp_dir.mkdir(exist_ok=True)
        >>> # (temp_dir / 'valid.json').write_text(json.dumps({"key": "value"}))
        >>> # (temp_dir / 'invalid.json').write_text("{'bad': 'json'")
        >>> # sanitize_json_files(temp_dir) # Ожидаемый результат: True
        >>> # (temp_dir / 'invalid.json.sanitized').exists() # Ожидаемый результат: True
        >>> # # ... очистка ...
    """
    all_successful: bool = True

    def process_file(file_path: Path) -> bool:
        logger.info(f'Start sanitize file: {file_path}')

        def write_sanitzed_suffix(file_path) -> bool:
            try:
                sanitized_path: Path = file_path.with_name(file_path.name + '.sanitized')
                file_path.rename(sanitized_path)
                logger.info(f'File renamed to: {sanitized_path}')
                return True
            except Exception as rename_ex:
                logger.error(f'Failed to rename file: {file_path} to {sanitized_path}', rename_ex)
                return False


        if not file_path.is_file() or file_path.suffix.lower() != '.json':
            logger.error(f'Path is not a JSON file: {file_path}')
            return False
        
        try:
            with file_path.open('r', encoding='utf-8') as f:
                json.load(f)
            logger.info(f'File is valid: {file_path}')
            return True

        except Exception as ex:
            logger.error(f'Error reading or parsing JSON in file: {file_path}\nStart repair', ex)
            try:
                with file_path.open('r', encoding='utf-8') as f:
                    text_data:str = f
            except Exception as ex:
                logger.error("Не удается открыть файл. Возват из функции")
                write_sanitzed_suffix(file_path)
                return False

            repaired_data = _string_to_dict(text_data, return_objects=True)
            if not repaired_data:
                logger.error(f'Failed to repair JSON in file: {file_path}')
                write_sanitzed_suffix(file_path)
                return False
                

            if j_dumps(repaired_data, file_path.open('w', encoding='utf-8'), ensure_ascii=False, indent=4):
                logger.success(f'File repaired and saved: {file_path}')
                return True

        return True # Файл валиден или успешно переименован

    if not path.exists():
        logger.error(f'Path not found: {path}')
        return False

    if path.is_file():
        if not process_file(path):
            all_successful = False
    elif path.is_dir():
        for json_file in path.rglob('*.json'):
            # Пропуск файлы, которые уже были переименованы с суффиксом .sanitized,
            # чтобы избежать их повторной обработки или ошибок.
            if '.sanitized' in json_file.suffixes: # Check if '.sanitized' is one of the suffixes
                continue
            if not process_file(json_file):
                all_successful = False
    else:
        logger.error(f'Path is not a file or directory: {path}')
        return False

    return all_successful


def find_keys(
    obj: Any,
    keys_to_find_input: TypingList[str] | str,
    found: TypingDict[str, TypingList[Any]] | None = None,
) -> TypingDict[str, TypingList[Any]]:
    """
    Рекурсивно находит все значения, связанные с указанными ключами, во вложенной структуре данных.

    Args:
        obj (Any): Входной Python объект (словарь, список или любая JSON-подобная структура).
        keys_to_find_input (TypingList[str] | str): Список строковых ключей для поиска или один ключ-строка.
        found (dict[str, list[Any]] | None, optional): Аккумулятор для найденных ключей и их значений.
            Обычно используется внутренне для рекурсии. По умолчанию `None`.

    Returns:
        dict[str, list[Any]]: Словарь, где каждый искомый ключ сопоставлен со списком всех найденных для него значений.
    
    Example:
        >>> data = {
        ...     "id": 1, "name": "Parent", 
        ...     "child": {"id": 2, "name": "Child1"}, 
        ...     "items": [{"id": 3, "value": "A"}, {"name": "Child2", "id": 4}]
        ... }
        >>> result = find_keys(data, ["id", "name"])
        >>> sorted(result['id']) # Сортировка для предсказуемого порядка в тесте
        [1, 2, 3, 4]
        >>> sorted(result['name'])
        ['Child1', 'Child2', 'Parent']
        >>> # Test with a single key string
        >>> result_single = find_keys(data, "id")
        >>> sorted(result_single['id'])
        [1, 2, 3, 4]
        >>> find_keys(data, ["non_existent_key"]) # Test with non-existent key
        {'non_existent_key': []}
    """
    
    # Эта переменная будет содержать фактический список строковых ключей для поиска.
    actual_keys_list_to_search: TypingList[str]
    # Эта переменная будет содержать словарь-аккумулятор.
    current_accumulator_dict: TypingDict[str, TypingList[Any]]

    # Блок выполняется только при первоначальном (не рекурсивном) вызове.
    if found is None:
        # Обработка keys_to_find_input для гарантии, что это список строк.
        if isinstance(keys_to_find_input, str):
            actual_keys_list_to_search = [keys_to_find_input]
        elif isinstance(keys_to_find_input, list) and all(isinstance(k, str) for k in keys_to_find_input):
            actual_keys_list_to_search = keys_to_find_input
        else:
            # Логирование ошибки, если тип входных данных не соответствует ожидаемому.
            logger.error(f"Параметр 'keys_to_find_input' должен быть строкой или списком строк. Получено: {type(keys_to_find_input)}")
            # Возврат пустого словаря или частично сформированного, если возможно.
            if hasattr(keys_to_find_input, '__iter__') and not isinstance(keys_to_find_input, (str, bytes)):
                 return {str(k): [] for k in keys_to_find_input if isinstance(k, str)}
            return {}

        # Инициализация словаря-аккумулятора.
        current_accumulator_dict = {key_item: [] for key_item in actual_keys_list_to_search}
    # Блок выполняется при рекурсивных вызовах.
    else:
        current_accumulator_dict = found
        # В рекурсивных вызовах `keys_to_find_input` фактически является `actual_keys_list_to_search` из родительского вызова.
        # Таким образом, это уже обработанный список строк.
        if not (isinstance(keys_to_find_input, list) and all(isinstance(k, str) for k in keys_to_find_input)):
            # Это не должно произойти, если рекурсия вызывается корректно. Логирование ошибки, если это произошло.
            logger.error("Внутренняя ошибка: `keys_to_find_input` в рекурсивном вызове не является списком строк.")
            return current_accumulator_dict # Или выбросить исключение

        actual_keys_list_to_search = keys_to_find_input


    try:
        # Если объект является словарем или подобным отображением.
        if isinstance(obj, Mapping):
            for key, value in obj.items():
                # Приведение ключа из obj к строке для поиска.
                key_as_str: str = str(key)
                if key_as_str in actual_keys_list_to_search:
                    # Если ключ совпадает с одним из искомых, добавление его значения.
                    # Код пользователя содержал `if value:`, что пропускало бы ложные значения (например, None, 0, False).
                    # Эта проверка удалена, чтобы включать все значения для найденных ключей.
                    if value:
                        # Проверка, является ли значение списком или кортежем.
                        if isinstance(value, (list, tuple)):
                            # Приведение к списку для хранения в аккумуляторе.
                            current_accumulator_dict[key_as_str].extend(list(value))
                        else:
                            # Добавление значения в аккумулятор.
                            current_accumulator_dict[key_as_str].append(value)
                
                # Рекурсивный вызов find_keys для значения.
                # Передача `actual_keys_list_to_search` (обработанный список) и `current_accumulator_dict`.
                find_keys(value, actual_keys_list_to_search, current_accumulator_dict)
        # Если объект является списком или кортежем (но не строкой/байтами).
        elif isinstance(obj, Sequence) and not isinstance(obj, (str, bytes)):
            for item in obj:
                # Рекурсивный вызов find_keys для каждого элемента в последовательности.
                find_keys(item, actual_keys_list_to_search, current_accumulator_dict)
    
    except Exception as ex:
        logger.error('Ошибка при поиске ключей в объекте', ex, exc_info=True)
        # Функция вернет 'current_accumulator_dict' в его состоянии на момент ошибки.

    return current_accumulator_dict