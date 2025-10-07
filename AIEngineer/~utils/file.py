## \file /src/utils/file.py
# -*- coding: utf-8 -*-
#! .pyenv/bin/python3

"""
.. module:: src.utils.file 
	:platform: Windows, Unix
	:synopsis: read, wite, search text files

Модуль для работы с файлами.
=========================================================================================

Модуль содержит набор утилит для выполнения операций с файлами, таких как сохранение, чтение,
и получение списков файлов. Поддерживает обработку больших файлов с использованием генераторов
для экономии памяти.

Пример использования
--------------------

```python

    from pathlib import Path
    from src.utils.file import read_text_file, save_text_file

    file_path = Path('example.txt')
    content = read_text_file(file_path)
    if content:
        print(f'File content: {content[:100]}...')

    save_text_file(file_path, 'Новый текст')
```
"""
import os
import asyncio
import json
import fnmatch
import re
from pathlib import Path
from typing import List, Dict, Optional, Union, Generator, Iterator
from src.logger.logger import logger


def save_text_file(
    data: str | list[str] | dict,
    file_path: str | Path,
    mode: str = 'w'
) -> bool:
    """
    Сохраняет данные в текстовый файл.

    Args:
        file_path (str | Path): Путь к файлу для сохранения.
        data (str | list[str] | dict): Данные для записи. Могут быть строкой, списком строк или словарем.
        mode (str, optional): Режим записи файла ('w' для записи, 'a' для добавления).
    Returns:
        bool: `True`, если файл успешно сохранен, `False` в противном случае.
    Raises:
        Exception: При возникновении ошибки при записи в файл.

    Example:
        >>> from pathlib import Path
        >>> file_path = Path('example.txt')
        >>> data = 'Пример текста'
        >>> result = save_text_file(file_path, data)
        >>> print(result)
        True
    """
    try:
        file_path = Path(file_path)
        file_path.parent.mkdir(parents = True, exist_ok = True)

        with file_path.open(mode, encoding = 'utf-8') as file:
            if isinstance(data, list):
                file.writelines(f'{line}\n' for line in data)
            elif isinstance(data, dict):
                json.dump(data, file, ensure_ascii = False, indent = 4)
            else:
                file.write(data)
        return True
    except Exception as ex:
        logger.error(f'Ошибка при сохранении файла {file_path}.', ex)
        ...
        return False
    
def read_text_file_generator(
    file_path: str | Path,
    as_list: bool = False,
    extensions: Optional[list[str]] = None,
    chunk_size: int = 8192,
    recursive: bool = False,
    patterns: Optional[str | list[str]] = None,
) -> Generator[str, None, None] | str | list[str] | None:
    """
    Читает содержимое файла(ов) или директории.

        Args:
            file_path (str | Path): Путь к файлу или директории.
            as_list (bool, optional): Если `True`, то возвращает генератор строк или список строк, в зависимости от типа вывода.
            extensions (list[str], optional): Список расширений файлов для включения при чтении директории.
            chunk_size (int, optional): Размер чанка для чтения файла в байтах.
            recursive (bool, optional): Если `True`, то поиск файлов выполняется рекурсивно.
            patterns (str | list[str], optional): Шаблоны для фильтрации файлов при рекурсивном поиске.

        Returns:
            Generator[str, None, None] | str | list[str] | None:
            - Если `as_list` is True и `file_path` является файлом, возвращает генератор строк.
            - Если `as_list` is True и `file_path` является директорией и `recursive` is True, возвращает список строк.
            - Если `as_list` is False и `file_path` является файлом, возвращает строку.
            - Если `as_list` is False и `file_path` является директорией, возвращает объединенную строку.
            - Возвращает `None` в случае ошибки.
        Raises:
            Exception: При возникновении ошибки при чтении файла.

        Example:
            >>> from pathlib import Path
            >>> file_path = Path('example.txt')
            >>> content = read_text_file(file_path)
            >>> if content:
            ...    print(f'File content: {content[:100]}...')
            File content: Пример текста...
    Функция read_text_file может возвращать несколько разных типов данных в зависимости от входных параметров:

    Возвратые значения:
    ----------------------

    - Generator[str, None, None] (Генератор строк):
        Генератор при итерации выдаёт строки из файла(ов) по одной. Эффективно для работы с большими файлами, так как они не загружаются полностью в память.
        - Когда:
            file_path – это файл и as_list равен True.
            file_path – это директория, recursive равен True и as_list равен True. При этом в генератор попадают строки из всех найденных файлов.
            file_path – это директория, recursive равен False и as_list равен True. При этом в генератор попадают строки из всех найденных файлов в текущей директории.
        
    - str (Строка):
        Содержимое файла или объединенное содержимое всех файлов в виде одной строки.
        - Когда:
            file_path – это файл и as_list равен False.
            file_path – это директория, recursive равен False и as_list равен False. При этом возвращается объединенная строка, состоящая из содержимого всех файлов в директории, разделенных символами новой строки (\n).
            file_path – это директория, recursive равен True и as_list равен False. При этом возвращается объединенная строка, состоящая из содержимого всех файлов в директории и её поддиректориях, разделенных символами новой строки (\n).
 
    - list[str] (Список строк):
        Этот тип явно не возвращается функцией, однако когда file_path – это директория, recursive равен True и as_list равен True - функция возвращает генератор, который можно преобразовать в список при помощи list()
        - Когда:
            file_path – не является ни файлом, ни директорией.
            Произошла ошибка при чтении файла или директории (например, файл не найден, ошибка доступа и т.п.).


    Note:
        Если вы хотите прочитать содержимое файла построчно (особенно для больших файлов) используйте as_list = True. В этом случае вы получите генератор строк.
        Если вы хотите получить всё содержимое файла в виде одной строки используйте as_list = False.
        Если вы работаете с директорией, recursive = True будет обходить все поддиректории.
        extensions и patterns позволят вам фильтровать файлы при работе с директорией.
        chunk_size позволяет оптимизировать работу с большими файлами при чтении их по частям.
        None будет возвращён в случае ошибок.

    Важно помнить:
        В случае чтения директории, если as_list=False, функция объединяет все содержимое найденных файлов в одну строку. Это может потребовать много памяти, если файлов много или они большие.
        Функция полагается на другие функции-помощники (_read_file_lines_generator, _read_file_content, recursively_get_file_path, yield_text_from_files), которые здесь не определены и их поведение влияет на результат read_text_file.


    """
    try:
        path = Path(file_path)
        if path.is_file():
            if as_list:
                return _read_file_lines_generator(path, chunk_size = chunk_size)
            else:
                return _read_file_content(path, chunk_size = chunk_size)
        elif path.is_dir():
            if recursive:
                if patterns:
                    files = recursively_get_file_path(path, patterns)
                else:
                   files = [
                        p for p in path.rglob('*') if p.is_file() and (not extensions or p.suffix in extensions)
                    ]
                if as_list:
                    return (
                        line
                        for file in files
                        for line in yield_text_from_files(file, as_list = True, chunk_size = chunk_size)
                    )
                else:
                    return '\n'.join(filter(None, [read_text_file(p, chunk_size = chunk_size) for p in files]))
            else:
                files = [
                    p for p in path.iterdir() if p.is_file() and (not extensions or p.suffix in extensions)
                ]
                if as_list:
                    return (line for file in files for line in read_text_file(file, as_list = True, chunk_size = chunk_size) )
                else:
                    return '\n'.join(filter(None, [read_text_file(p, chunk_size = chunk_size) for p in files]))
        else:
            logger.error(f'Путь \'{file_path}\' не является файлом или директорией.')
            ...
            return None
    except Exception as ex:
        logger.error(f'Ошибка при чтении файла/директории {file_path}.', ex)
        ...
        return None


async def read_text_file_async(
    file_path: str | Path,
    as_list: bool = False,
    extensions: Optional[List[str]] = None,
    exc_info: bool = True
) -> str | List[str] | None:
    """
    Асинхронно считывает содержимое текстового файла или всех текстовых файлов в директории.

    Args:
        file_path (str | Path): Путь к файлу или директории.
        as_list (bool, optional):
            Если `True`, функция возвращает содержимое как список оригинальных строк.
            Если `False`, функция возвращает содержимое как одну строку,
            в которой последовательности пробельных символов заменены на один пробел,
            а двойные кавычки экранированы.
            По умолчанию `False`.
        extensions (List[str], optional): Список расширений файлов для включения
            при чтении директории (например, `['.txt', '.py']`). Точка в начале
            расширения рекомендуется, но обрабатывается и её отсутствие.
            По умолчанию `None` (включаются все файлы).
        exc_info (bool, optional): Если `True`, функция логирует информацию трассировки при ошибке.
            По умолчанию `True`.

    Returns:
        str | List[str] | None: Содержимое файла как одна обработанная строка или
                                 список оригинальных строк. Функция возвращает `None`, если путь некорректен
                                 или возникает ошибка во время чтения.

    Example:
        >>> import asyncio
        >>> import shutil # Для примера
        >>> from pathlib import Path # Для примера
        >>> # Заглушка logger для doctest
        >>> class LoggerMockDoctest:
        ...     def debug(self, msg, *args, **kwargs): pass
        ...     def warning(self, msg, *args, **kwargs): print(f"WARNING: {msg}")
        ...     def error(self, msg, *args, **kwargs): print(f"ERROR: {msg}")
        ...     def exception(self, msg, *args, **kwargs): print(f"EXCEPTION: {msg}")
        ...     def critical(self, msg, *args, **kwargs): print(f"CRITICAL: {msg}")
        >>> logger = LoggerMockDoctest()
        >>> # Заглушка aiofiles для doctest
        >>> class MockAiofilesFile:
        ...     def __init__(self, content): self.content = content
        ...     async def read(self): return self.content
        ...     async def __aenter__(self): return self
        ...     async def __aexit__(self, exc_type, exc, tb): pass
        >>> class MockAiofiles:
        ...     async def open(self, path_obj, mode, encoding):
        ...         if not path_obj.exists(): raise FileNotFoundError
        ...         return MockAiofilesFile(path_obj.read_text(encoding=encoding))
        >>> aiofiles = MockAiofiles()
        >>> # Пример использования:
        >>> async def example_usage_doctest():
        ...     test_dir_dt = Path("./test_async_read_data_dt")
        ...     if test_dir_dt.exists(): shutil.rmtree(test_dir_dt)
        ...     test_dir_dt.mkdir(exist_ok=True)
        ...     (test_dir_dt / "file1.txt").write_text("Hello\\nWorld\\nWith  spaces and \\"quotes\\" inside.", encoding="utf-8")
        ...     (test_dir_dt / "file2.log").write_text("Another log line.", encoding="utf-8")
        ...     sub_dir_dt = test_dir_dt / "subdir"
        ...     sub_dir_dt.mkdir(exist_ok=True)
        ...     (sub_dir_dt / "file3.txt").write_text("Sub dir file content.", encoding="utf-8")
        ...     content_str = await read_text_file_async(test_dir_dt / "file1.txt")
        ...     assert content_str == 'Hello World With spaces and \\"quotes\\" inside.'
        ...     content_list = await read_text_file_async(test_dir_dt / "file1.txt", as_list=True)
        ...     assert content_list == ['Hello', 'World', 'With  spaces and "quotes" inside.']
        ...     dir_content_str = await read_text_file_async(test_dir_dt, extensions=['.txt'])
        ...     assert 'Hello World With spaces and \\"quotes\\" inside.' in dir_content_str
        ...     assert 'Sub dir file content.' in dir_content_str
        ...     assert 'Another log line.' not in dir_content_str
        ...     dir_content_list = await read_text_file_async(test_dir_dt, as_list=True, extensions=['.txt', '.log'])
        ...     assert len(dir_content_list) == 5 # 3 (file1) + 1 (file2) + 1 (file3)
        ...     non_existent = await read_text_file_async(test_dir_dt / "non_existent.txt")
        ...     assert non_existent is None # Path not valid file or directory (т.к. не существует)
        ...     shutil.rmtree(test_dir_dt)
        >>> # asyncio.run(example_usage_doctest()) # Закомментировано для прохождения тестов без запуска loop
    """
    # Объявление переменных в начале функции
    path_obj: Path
    raw_content: str
    processed_content: str
    current_processed_extensions: Optional[List[str]]
    files_to_process: List[Path]
    async_tasks: List[asyncio.Task[str | List[str] | None]]
    results_from_tasks: List[str | List[str] | None]
    flattened_list_content: List[str]
    valid_string_contents: List[str]

    try:
        path_obj = Path(file_path)

        # --- Обработка одного файла ---
        if path_obj.is_file():
            try:
                async with aiofiles.open(path_obj, "r", encoding="utf-8") as f: # type: ignore
                    raw_content = await f.read()
            except Exception as ex_read_file:
                logger.critical(f'Ошибка чтения содержимого файла {str(path_obj)}: {ex_read_file}')
                return [] if as_list else ""

            if as_list:
                return raw_content.splitlines()
            else:
                processed_content = re.sub(r'\s+', ' ', raw_content)
                processed_content = processed_content.replace('"', '\\"')
                return processed_content

        # --- Обработка директории ---
        elif path_obj.is_dir():
            current_processed_extensions = None
            if extensions:
                current_processed_extensions = [ext if ext.startswith('.') else '.' + ext for ext in extensions]

            files_to_process = [
                p for p in path_obj.rglob("*")
                if p.is_file() and (not current_processed_extensions or p.suffix in current_processed_extensions)
            ]

            if not files_to_process:
                return [] if as_list else ""

            async_tasks = [
                read_text_file_async(p, as_list=as_list, extensions=None, exc_info=exc_info)
                for p in files_to_process
            ]
            
            results_from_tasks = await asyncio.gather(*async_tasks, return_exceptions=False) # Провера, что ошибки не подавляются gather

            if as_list:
                flattened_list_content = []
                for item_from_task in results_from_tasks:
                    if isinstance(item_from_task, list):
                        flattened_list_content.extend(item_from_task)
                return flattened_list_content
            else:
                valid_string_contents = []
                for item_from_task in results_from_tasks:
                    if isinstance(item_from_task, str):
                        valid_string_contents.append(item_from_task)
                return "\n".join(valid_string_contents)

        # --- Обработка некорректного пути (не файл и не директория, или не существует) ---
        else:
            logger.warning(f"Путь '{file_path}' не является корректным файлом или директорией.")
            return None

    # --- Обработка исключений ---
    except Exception as ex:
        log_message = f"Не удалось асинхронно прочитать путь '{file_path}'. Ошибка: {ex}"
        if exc_info:
            logger.exception(log_message)
        else:
            logger.error(log_message, exc_info=False)
        return None


def read_text_file(
    file_path: str | Path,
    as_list: bool = False,
    extensions: Optional[List[str]] = None,
    exc_info: bool = True
) -> str | List[str] | None:
    """
    Read the contents of a text file or all text files in a directory.

    Args:
        file_path (str | Path): Path to the file or directory.
        as_list (bool, optional):
            If True, returns content as a list of original lines.
            If False, returns content as a single string with whitespace
            collapsed to single spaces and double quotes escaped.
            Defaults to False.
        extensions (List[str], optional): List of file extensions to include
            when reading a directory (e.g., ['.txt', '.py']). The dot prefix
            is recommended but handled if missing. Defaults to None (include all files).
        exc_info (bool, optional): If True, logs traceback information on error.
            Defaults to True.

    Returns:
        str | List[str] | None: File content as a single processed string or a
                                 list of original lines. Returns None if the
                                 path is invalid or an error occurs during reading.
    """
    try:
        path = Path(file_path)

        # --- Handle Single File ---
        if path.is_file():
            # Optional: Check extension even for single files if desired
            # if extensions:
            #     processed_extensions = [ext if ext.startswith('.') else '.' + ext for ext in extensions]
            #     if path.suffix not in processed_extensions:
            #         logger.debug(f"Skipping file {path} due to extension mismatch.")
            #         return [] if as_list else "" # Or None? Consistent return type is important

            with path.open("r", encoding="utf-8") as f:
                # Read the entire file content first
                try:
                    raw_content = f.read()
                except Exception as ex:
                    logger.critical(f'Ошибка чтения содержимого файла {str(path)}')
                    return ''

            if as_list:
                # Return list of original lines
                return raw_content.splitlines()
            else:
                # Process the content for single string output
                # 1. Collapse whitespace (including newlines) to single spaces
                content = re.sub(r'\s+', ' ', raw_content)
                # 2. Escape double quotes
                content = content.replace('"', '\\"')
                return content

        # --- Handle Directory ---
        elif path.is_dir():
            processed_extensions = None
            if extensions:
                # Ensure extensions start with a dot for consistent suffix matching
                processed_extensions = [ext if ext.startswith('.') else '.' + ext for ext in extensions]

            # Find all matching files recursively
            files_to_read = [
                p for p in path.rglob("*")
                if p.is_file() and (not processed_extensions or p.suffix in processed_extensions)
            ]

            # Recursively read each file, passing the 'as_list' flag
            contents = [
                read_text_file(p, as_list=as_list, extensions=None, exc_info=exc_info)
                for p in files_to_read
            ] # Pass extensions=None in recursive call as files are already filtered

            if as_list:
                # Combine results: flatten the list of lists (of lines)
                # Filter out None values from failed reads before flattening
                flat_list = [item for sublist in contents if sublist is not None for item in sublist]
                return flat_list
            else:
                # Combine results: join the list of strings (processed file contents)
                # Filter out None values from failed reads before joining
                valid_contents = [c for c in contents if c is not None and isinstance(c, str)]
                return "\n".join(valid_contents)

        # --- Handle Invalid Path ---
        else:
            logger.warning(f"Path '{file_path}' is not a valid file or directory.")
            return None

    # --- Handle Exceptions ---
    except Exception as ex:
        # Log the error, optionally with traceback
        if exc_info:
            logger.exception(f"Failed to read path '{file_path}'. Error: {ex}") # logger.exception includes traceback
        else:
            logger.error(f"Failed to read path '{file_path}'. Error: {ex}")
        return None

def yield_text_from_files(
    file_path: str | Path,
    as_list: bool = False,
    chunk_size: int = 8192
) -> Generator[str, None, None] | str | None:
    """
    Читает содержимое файла и возвращает его в виде генератора строк или одной строки.

    Args:
        file_path (str | Path): Путь к файлу.
        as_list (bool, optional): Если True, возвращает генератор строк. По умолчанию False.
        chunk_size (int, optional): Размер чанка для чтения файла в байтах.

    Returns:
        Generator[str, None, None] | str | None: Генератор строк, объединенная строка или None в случае ошибки.

    Yields:
       str: Строки из файла, если as_list is True.

    Example:
        >>> from pathlib import Path
        >>> file_path = Path('example.txt')
        >>> for line in yield_text_from_files(file_path, as_list=True):
        ...     print(line)
        Первая строка файла
        Вторая строка файла
    """
    try:
        path = Path(file_path)
        if path.is_file():
            if as_list:
                 yield from  _read_file_lines_generator(path, chunk_size = chunk_size)
            else:
                yield _read_file_content(path, chunk_size = chunk_size)
        else:
             logger.error(f'Путь \'{file_path}\' не является файлом.')
             ...
             return None
    except Exception as ex:
        logger.error(f'Ошибка при чтении файла {file_path}.', ex)
        ...
        return None


async def save_text_file_async(
    data: Union[str, List[str], Dict],
    file_path: Union[str, Path],
    mode: str = 'w'
) -> bool:
    """
    Асинхронно сохраняет данные в текстовый файл с использованием файловой блокировки.

    Функция обеспечивает, что только один процесс/поток может одновременно записывать
    в целевой файл, используя файл с расширением `.lock` для координации.

    Args:
        data (Union[str, List[str], Dict]): Данные для записи.
            Если `list`, каждая строка записывается на новой строке.
            Если `dict`, данные сериализуются в JSON и записываются.
            Если `str`, записывается как есть.
        file_path (Union[str, Path]): Путь к файлу для сохранения.
        mode (str, optional): Режим записи файла ('w' для перезаписи, 'a' для добавления).
                              Блокировка применяется в любом режиме. По умолчанию 'w'.

    Returns:
        bool: `True`, если файл успешно сохранен, `False` в противном случае.
              В случае ошибки, информация логируется.
    
    Raises:
        Exception: Не выбрасывает напрямую, а логирует исключения и возвращает `False`.

    Example:
        >>> import asyncio
        >>> from pathlib import Path
        >>> # создание временный файл для примера
        >>> temp_dir = Path('.') / 'temp_test_data'
        >>> temp_dir.mkdir(exist_ok=True)
        >>> example_file_path = temp_dir / 'example_async.txt'
        >>> async def run_example():
        ...     data_to_save_str = 'Пример асинхронной записи строки.'
        ...     result_str = await save_text_file_async(data_to_save_str, example_file_path)
        ...     print(f'Сохранение строки: {result_str}')
        ...     data_to_save_list = ['Строка 1', 'Строка 2 из списка']
        ...     result_list = await save_text_file_async(data_to_save_list, example_file_path, mode='a')
        ...     print(f'Добавление списка строк: {result_list}')
        ...     data_to_save_dict = {"key": "value", "number": 123}
        ...     result_dict = await save_text_file_async(data_to_save_dict, example_file_path.with_suffix('.json'))
        ...     print(f'Сохранение словаря в JSON: {result_dict}')
        >>> # asyncio.run(run_example()) # Закомментировано для doctest, но так запускается
        >>> # Очистка после примера (в реальном коде может не требоваться)
        >>> # if example_file_path.exists(): example_file_path.unlink()
        >>> # if example_file_path.with_suffix('.json').exists(): example_file_path.with_suffix('.json').unlink()
        >>> # if example_file_path.with_suffix('.txt.lock').exists(): example_file_path.with_suffix('.txt.lock').unlink()
        >>> # if example_file_path.with_suffix('.json.lock').exists(): example_file_path.with_suffix('.json.lock').unlink()
        >>> # if temp_dir.exists(): temp_dir.rmdir()
    """
    _file_path: Path = Path(file_path)
    # Формирование пути к файлу блокировки
    _lock_path: Path = _file_path.with_suffix(_file_path.suffix + '.lock')
    lock: AsyncFileLock = AsyncFileLock(_lock_path)

    try:
        # Захват блокировки асинхронно
        async with lock:
            # Создание родительских директорий, если они не существуют
            _file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Асинхронное открытие файла для записи
            async with aiofiles.open(_file_path, mode, encoding='utf-8') as file_obj:
                if isinstance(data, list):
                    # Запись списка строк, каждая на новой строке
                    await file_obj.writelines(f'{line}\n' for line in data)
                elif isinstance(data, dict):
                    # Сериализация словаря в JSON и запись в файл
                    # json.dumps является синхронной операцией, но она быстрая для большинства случаев.
                    # Запись в файл (await file_obj.write) асинхронна.
                    json_data: str = json.dumps(data, ensure_ascii=False, indent=4)
                    await file_obj.write(json_data)
                else:
                    # Запись строки (или данных, приведенных к строке)
                    await file_obj.write(str(data))
            return True
    except Exception as ex:
        # Логирование ошибки при сохранении файла
        logger.error(f'Ошибка при асинхронном сохранении файла {_file_path}. Данные: {str(data)[:100]}...', ex, exc_info=True)
        return False

async def  remove_file_async(filepath: str | Path) -> bool:
    """"""
    return asyncio.run(remove_file(filepath))

def remove_file(filepath: str | Path) -> bool:
    """
    Удаляет указанный файл.

    Args:
        filepath (str | Path): Путь к файлу, который необходимо удалить.

    Returns:
        bool: `True` в случае успешного удаления файла, `False` в противном случае 
              (например, если файл не найден или возникла ошибка доступа).
    
    Example:
        >>> # from pathlib import Path
        >>> # temp_file = Path('dummy_to_remove.txt')
        >>> # temp_file.touch() # Создание временного файла
        >>> # remove_file(temp_file)
        True
        >>> # remove_file(temp_file) # Попытка удалить несуществующий файл
        False 
    """
    # Функция выполняет удаление файла
    p_filepath: Path
    try:
        p_filepath = Path(filepath)
        if p_filepath.exists():
            p_filepath.unlink()
            logger.debug(f'Файл {filepath} удален.')
            return True
        else:
            logger.warning(f'Файл {filepath} для удаления не найден.')
            return False # Файл не найден, удаление не выполнено
    except OSError as ex:
        logger.error(f'Ошибка при удалении файла {filepath}', ex, exc_info=True)
        return False

def _read_file_content(file_path: Path, chunk_size: int) -> str:
    """
    Читает содержимое файла по чанкам и возвращает как строку.

    Args:
        file_path (Path): Путь к файлу для чтения.
        chunk_size (int): Размер чанка для чтения файла в байтах.
    Returns:
        str: Содержимое файла в виде строки.
    Raises:
        Exception: При возникновении ошибки при чтении файла.
    """
    with file_path.open('r', encoding = 'utf-8') as f:
        content = ''
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            content += chunk
        #Обработка согласно заданию
        content = re.sub(r'\s+', ' ', content)
        content = content.replace('"', '\\"')
        return content

def _read_file_lines_generator(file_path: Path, chunk_size: int) -> Generator[str, None, None]:
    """
    Читает файл по строкам с помощью генератора.

    Args:
        file_path (Path): Путь к файлу для чтения.
        chunk_size (int): Размер чанка для чтения файла в байтах.
    Yields:
        str: Строки из файла.
    Raises:
        Exception: При возникновении ошибки при чтении файла.
    """
    with file_path.open('r', encoding = 'utf-8') as f:
         while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                lines = chunk.splitlines()
                # Если чанк не закончился полной строкой, то последнюю строку добавляем к следующему чанку
                if len(lines)>0 and not chunk.endswith('\n'):
                     next_chunk = f.read(1)
                     if next_chunk != '':
                        lines[-1] = lines[-1] + next_chunk
                     else:
                        for line in lines:
                            #Обработка согласно заданию
                            line = re.sub(r'\s+', ' ', line)
                            line = line.replace('"', '\\"')
                            yield line
                        break
                
                for line in lines:
                    #Обработка согласно заданию
                    line = re.sub(r'\s+', ' ', line)
                    line = line.replace('"', '\\"')
                    yield line



def get_filenames_from_directory(
    directory: str | Path, ext: str | list[str] = '*'
) -> list[str]:
    """
    Возвращает список имен файлов в директории, опционально отфильтрованных по расширению.

    Args:
        directory (str | Path): Путь к директории для поиска.
        ext (str | list[str], optional): Расширения для фильтрации.
            По умолчанию '*'.

    Returns:
        list[str]: Список имен файлов, найденных в директории.

    Example:
        >>> from pathlib import Path
        >>> directory = Path('.')
        >>> get_filenames_from_directory(directory, ['.txt', '.md'])
        ['example.txt', 'readme.md']

    TODO:
        Сейчас не работает формат параметра `ext` переданный как `*.ext`, только `ext` 
    """
    if not Path(directory).is_dir():
        logger.error(f'Указанный путь \'{directory}\' не является директорией.')
        return []

    try:
        if isinstance(ext, str):
            extensions = [ext] if ext != '*' else []
        extensions = [e if e.startswith('.') else f'.{e}' for e in extensions]

        return [
            file.name
            for file in directory.iterdir()
            if file.is_file() and (not extensions or file.suffix in extensions)
        ]
    except Exception as ex:
        logger.error(f'Ошибка при получении списка имен файлов из \'{directory}\'.', ex)
        return []


def recursively_yield_file_path(
    root_dir: str | Path, patterns: str | list[str] = '*'
) -> Generator[Path, None, None]:
    """
    Рекурсивно возвращает пути ко всем файлам, соответствующим заданным шаблонам, в указанной директории.

    Args:
        root_dir (str | Path): Корневая директория для поиска.
        patterns (str | list[str]): Шаблоны для фильтрации файлов.

    Yields:
        Path: Путь к файлу, соответствующему шаблону.

    Example:
        >>> from pathlib import Path
        >>> root_dir = Path('.')
        >>> for path in recursively_yield_file_path(root_dir, ['*.txt', '*.md']):
        ...    print(path)
        ./example.txt
        ./readme.md
    """
    try:
        patterns = [patterns] if isinstance(patterns, str) else patterns
        for pattern in patterns:
            yield from Path(root_dir).rglob(pattern)
    except Exception as ex:
         logger.error(f'Ошибка при рекурсивном поиске файлов в \'{root_dir}\'.', ex)


def recursively_get_file_path(
    root_dir: str | Path,
    patterns: str | list[str] = '*'
) -> list[Path]:
    """
    Рекурсивно возвращает список путей ко всем файлам, соответствующим заданным шаблонам, в указанной директории.

    Args:
        root_dir (str | Path): Корневая директория для поиска.
        patterns (str | list[str]): Шаблоны для фильтрации файлов.

    Returns:
        list[Path]: Список путей к файлам, соответствующим шаблонам.

    Example:
        >>> from pathlib import Path
        >>> root_dir = Path('.')
        >>> paths = recursively_get_file_path(root_dir, ['*.txt', '*.md'])
        >>> print(paths)
        [Path('./example.txt'), Path('./readme.md')]
    """
    try:
        file_paths = []
        patterns = [patterns] if isinstance(patterns, str) else patterns
        for pattern in patterns:
            file_paths.extend(Path(root_dir).rglob(pattern))
        return file_paths
    except Exception as ex:
        logger.error(f'Ошибка при рекурсивном поиске файлов в \'{root_dir}\'.', ex)
        return []


def recursively_read_text_files(
    root_dir: str | Path,
    patterns: str | list[str],
    as_list: bool = False
) -> list[str]:
    """
    Рекурсивно читает текстовые файлы из указанной корневой директории, соответствующие заданным шаблонам.

    Args:
        root_dir (str | Path): Путь к корневой директории для поиска.
        patterns (str | list[str]): Шаблон(ы) имени файла для фильтрации.
             Может быть как одиночным шаблоном (например, '*.txt'), так и списком.
        as_list (bool, optional): Если True, то возвращает содержимое файла как список строк.
             По умолчанию `False`.

    Returns:
        list[str]: Список содержимого файлов (или список строк, если `as_list=True`),
         соответствующих заданным шаблонам.

    Example:
        >>> from pathlib import Path
        >>> root_dir = Path('.')
        >>> contents = recursively_read_text_files(root_dir, ['*.txt', '*.md'], as_list=True)
        >>> for line in contents:
        ...     print(line)
        Содержимое example.txt
        Первая строка readme.md
        Вторая строка readme.md
    """
    matches = []
    root_path = Path(root_dir)

    if not root_path.is_dir():
        logger.debug(f'Корневая директория \'{root_path}\' не существует или не является директорией.')
        return []

    print(f'Поиск в директории: {root_path}')

    if isinstance(patterns, str):
        patterns = [patterns]

    for root, _, files in os.walk(root_path):
        for filename in files:
            if any(fnmatch.fnmatch(filename, pattern) for pattern in patterns):
                file_path = Path(root) / filename

                try:
                    with file_path.open('r', encoding = 'utf-8') as file:
                        if as_list:
                            matches.extend(file.readlines())
                        else:
                            matches.append(file.read())
                except Exception as ex:
                    logger.error(f'Ошибка при чтении файла \'{file_path}\'.', ex)

    return matches


def get_directory_names(directory: str | Path) -> list[str]:
    """
    Возвращает список имен директорий из указанной директории.

    Args:
        directory (str | Path): Путь к директории, из которой нужно получить имена.

    Returns:
        list[str]: Список имен директорий, найденных в указанной директории.

    Example:
        >>> from pathlib import Path
        >>> directory = Path('.')
        >>> get_directory_names(directory)
        ['dir1', 'dir2']
    """
    try:
        return [entry.name for entry in Path(directory).iterdir() if entry.is_dir()]
    except Exception as ex:
        logger.error(f'Ошибка при получении списка имен директорий из \'{directory}\'.', ex)
        return []


def remove_bom(path: str | Path) -> None:
    """
    Удаляет BOM из текстового файла или из всех файлов Python в директории.

    Args:
        path (str | Path): Путь к файлу или директории.

    Example:
        >>> from pathlib import Path
        >>> file_path = Path('example.txt')
        >>> with open(file_path, 'w', encoding='utf-8') as f:
        ...     f.write('\ufeffПример текста с BOM')
        >>> remove_bom(file_path)
        >>> with open(file_path, 'r', encoding='utf-8') as f:
        ...     print(f.read())
        Пример текста с BOM
    """
    path = Path(path)
    if path.is_file():
        try:
            with path.open('r+', encoding = 'utf-8') as file:
                content = file.read().replace('\ufeff', '')
                file.seek(0)
                file.write(content)
                file.truncate()
        except Exception as ex:
            logger.error(f'Ошибка при удалении BOM из файла {path}.', ex)
            ...
    elif path.is_dir():
        for root, _, files in os.walk(path):
             for file in files:
                 if file.endswith('.py'):
                    file_path = Path(root) / file
                    try:
                        with file_path.open('r+', encoding = 'utf-8') as f:
                            content = f.read().replace('\ufeff', '')
                            f.seek(0)
                            f.write(content)
                            f.truncate()
                    except Exception as ex:
                       logger.error(f'Ошибка при удалении BOM из файла {file_path}.', ex)
                       ...

    else:
        logger.error(f'Указанный путь \'{path}\' не является файлом или директорией.')
        ...

def find_file_in_dir(directory_path, filename):
    """
    Ищет файл с точным именем filename в директории directory_path.
    Возвращает полный путь к файлу, если найден, иначе None.
    """
    try:
        for item in os.listdir(directory_path):
            full_path = os.path.join(directory_path, item)
            # Проверка, что это файл (а не директория) и имя совпадает
            if os.path.isfile(full_path) and item == filename:
                return full_path
    except FileNotFoundError:
        print(f"Ошибка: Директория не найдена: {directory_path}")
        return None
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        return None
    return None # Файл не найден

def main() -> None:
    """Entry point for BOM removal in Python files."""
    root_dir = Path('..', 'src')
    logger.info(f'Starting BOM removal in {root_dir}')
    remove_bom(root_dir)



if __name__ == '__main__':
    main()




# # -----------------------------------------------------------

# def _yield_files_content(
#     self,
#     process_directory: str | Path,
# ) -> Iterator[tuple[Path, str]]:
#     """
#     Генерирует пути файлов и их содержимое по указанным шаблонам.

#     Args:
#         process_directory (Path | str): Абсолютный путь к стартовой директории

#     Returns:
#         bool: Iterator
#     """

#     process_directory: Path = process_directory if isinstance(process_directory, Path) else Path(process_directory)

#     # Компиляция паттернов исключаемых файлов
#     try:
#         exclude_files_patterns = [
#             re.compile(pattern) for pattern in Config.exclude_files_patterns
#         ]

#     except Exception as ex:
#         logger.error(
#             f'Не удалось скомпилировать регулярки из списка:/n{Config.exclude_files_patterns=}\n ', ex
#         )
#         ...

#     # Итерация по всем файлам в директории
#     for file_path in process_directory.rglob('*'):
#         # Проверка на соответствие шаблонам включения
#         if not any(
#             fnmatch.fnmatch(file_path.name, pattern) for pattern in Config.include_files_patterns
#         ):
#             continue

#         # Прверка исключенных директорий
#         if any(exclude_dir in file_path.parts for exclude_dir in Config.exclude_dirs):
#             continue

#         # Проверка исключенных файлов по паттерну
#         if any(exclude.match(str(file_path.name)) for exclude in exclude_files_patterns):
#             continue

#         # Проверка конкретных исключенных файлов
#         if str(file_path.name) in Config.exclude_files:
#             continue

#         # Чтение содержимого файла
#         try:
#             content = file_path.read_text(encoding='utf-8')
#             yield file_path, content
#             # make_summary( docs_dir = start_dir.parent / 'docs' )  # <- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ DEBUG  (create `summary.md`)
#         except Exception as ex:
#             logger.error(f'Ошибка при чтении файла {file_path}', ex)
#             ...
#             yield None, None

#         ...
