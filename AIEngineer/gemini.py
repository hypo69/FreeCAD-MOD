## \file AIEngineer/gemini.py
# -*- coding: utf-8 -*-
#! .pyenv/bin/python3

"""
Модуль для взаимодействия с Google Generative AI (Gemini).
==========================================================

Предоставляет класс GoogleGenerativeAi для работы с моделями Gemini
с поддержкой чата, RAG, истории диалогов и обработки изображений.

.. module:: AIEngineer.gemini
"""

import asyncio
import time
import json
from io import IOBase
from pathlib import Path
from typing import Optional, Dict, List, Any, Union
from types import SimpleNamespace
import datetime

import google.generativeai as genai
import grpc

from grpc import RpcError
from google.api_core.exceptions import (
    GatewayTimeout,
    RetryError,
    ServiceUnavailable,
    ResourceExhausted,
    InvalidArgument,
)
from google.auth.exceptions import (
    DefaultCredentialsError,
    RefreshError,
)

import FreeCAD

from AIEngineer.utils import (
    get_api_key,
    AI_DATA_DIR,
    j_dumps,
    j_loads,
    get_image_bytes,
    normalize_answer,
)

# === ЛОГГЕР ДЛЯ FREECAD ===
class MockLogger:
    """Класс логгера для вывода сообщений в консоль FreeCAD."""
    
    def info(self, msg: str, *args, **kwargs) -> None:
        """Функция выводит информационное сообщение."""
        FreeCAD.Console.PrintMessage(f'[Gemini] INFO: {msg}\n')
    
    def error(self, msg: str, *args, **kwargs) -> None:
        """Функция выводит сообщение об ошибке."""
        FreeCAD.Console.PrintError(f'[Gemini] ERROR: {msg}\n')
    
    def warning(self, msg: str, *args, **kwargs) -> None:
        """Функция выводит предупреждение."""
        FreeCAD.Console.PrintMessage(f'[Gemini] WARN: {msg}\n')
    
    def debug(self, msg: str, *args, **kwargs) -> None:
        """Функция выводит отладочное сообщение."""
        FreeCAD.Console.PrintMessage(f'[Gemini] DEBUG: {msg}\n')
    
    def critical(self, msg: str, *args, **kwargs) -> None:
        """Функция выводит критическое сообщение."""
        FreeCAD.Console.PrintError(f'[Gemini] CRITICAL: {msg}\n')

logger = MockLogger()

# === КОНСТАНТЫ ===
NETWORK_ERROR_MAX_ATTEMPTS: int = 5
SERVICE_UNAVAILABLE_MAX_ATTEMPTS: int = 3
INVALID_INPUT_MAX_ATTEMPTS: int = 3
INITIAL_RETRY_SLEEP_SECONDS: int = 2
NETWORK_RETRY_SLEEP_SECONDS: int = 120
SERVICE_RETRY_SLEEP_SECONDS_BASE: int = 10
QUOTA_EXHAUSTED_SLEEP_SECONDS: int = 14400


class GoogleGenerativeAi:
    """
    Класс для взаимодействия с моделями Google GenerativeAi.

    Атрибуты:
        api_key (str): Ключ API для доступа к Google Generative AI.
        model_name (str): Имя используемой модели Gemini.
        generation_config (Dict): Конфигурация для генерации ответов.
        system_instruction (Optional[str]): Системная инструкция для модели.
        model (genai.GenerativeModel): Инициализированный клиент модели.
        _chat (genai.ChatSession): Активный сеанс чата с моделью.
        chat_history (List[Dict]): История текущего диалога в памяти.
        chat_session_name (str): Имя текущего чата для сохранения истории.
        history_dir (Path): Директория для сохранения истории чатов.
        history_json_file (Path): Путь к JSON файлу с историей текущего чата.
    """

    api_key: str
    system_instruction: Optional[str]
    model_name: str
    model: genai.GenerativeModel
    timestamp: str
    _chat: genai.ChatSession
    chat_history: List[Dict]
    chat_session_name: str
    history_dir: Path
    history_json_file: Path

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = 'gemini-1.5-flash',
        generation_config: Optional[Dict] = None,
        system_instruction: Optional[str] = None,
    ):
        """
        Функция инициализирует экземпляр класса GoogleGenerativeAi.

        Args:
            api_key (Optional[str]): Ключ API для Google Generative AI.
                                     Если None, загружается из .env через get_api_key().
            model_name (str): Имя модели Gemini. По умолчанию 'gemini-1.5-flash'.
            generation_config (Optional[Dict]): Конфигурация генерации.
                                                По умолчанию {'response_mime_type': 'text/plain'}.
            system_instruction (Optional[str]): Системная инструкция для модели.

        Raises:
            ValueError: Если API-ключ не найден.
            DefaultCredentialsError: Ошибка аутентификации API.
            RefreshError: Ошибка обновления токена.
        """
        # Загрузка API-ключа из .env если не передан
        self.api_key = api_key if api_key else get_api_key()
        
        if not self.api_key:
            logger.error('API-ключ не найден. Настройте его в AI Settings.')
            raise ValueError('API key is required. Configure it in AI Settings.')

        self.model_name = model_name
        self.generation_config = generation_config if generation_config is not None else {
            'response_mime_type': 'text/plain'
        }
        self.system_instruction = system_instruction

        # Инициализация директории для истории чатов
        self.history_dir = AI_DATA_DIR / 'chats'
        self.history_dir.mkdir(parents=True, exist_ok=True)
        self.timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        self.chat_history = []
        self.chat_session_name = f'chat_{self.timestamp}'
        self.history_json_file = Path()

        logger.debug(f'Инициализация GoogleGenerativeAi: model_name={self.model_name}, '
                     f'generation_config={self.generation_config}')

        try:
            genai.configure(api_key=self.api_key)
            logger.debug('Gemini API сконфигурирован с ключом API')

            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=self.generation_config,
                system_instruction=self.system_instruction,
            )
            
            # Инициализация чата с системной инструкцией
            self._chat = self._start_chat(initial_system_instruction=self.system_instruction)
            
            logger.info(f'Модель {self.model_name} инициализирована')
            
        except (DefaultCredentialsError, RefreshError):
            logger.error('Ошибка аутентификации Gemini API')
            raise
        except Exception as ex:
            logger.error(f'Не удалось инициализировать модель Gemini: {ex}')
            raise

    def _start_chat(
        self,
        initial_history: Optional[List[Dict]] = None,
        initial_system_instruction: Optional[str] = None
    ) -> genai.ChatSession:
        """
        Функция запускает новый сеанс чата с моделью.

        Args:
            initial_history (Optional[List[Dict]]): История для загрузки в чат.
            initial_system_instruction (Optional[str]): Системная инструкция для сессии.

        Returns:
            genai.ChatSession: Объект сеанса чата.
        """
        history_to_load: List[Dict] = initial_history if initial_history is not None else []
        
        # Добавление системной инструкции в начало истории
        if initial_system_instruction:
            if not history_to_load or (
                history_to_load[0].get('role') == 'user' and 
                initial_system_instruction not in history_to_load[0].get('parts', [])
            ):
                history_to_load.insert(0, {
                    'role': 'user',
                    'parts': [initial_system_instruction]
                })
                logger.debug(f'Системная инструкция добавлена в историю чата')

        return self.model.start_chat(history=history_to_load)

    def start_new_chat_session(
        self,
        new_system_instruction: Optional[str] = None,
        initial_history: Optional[List[Dict]] = None
    ) -> None:
        """
        Функция начинает новый сеанс чата с опциональной новой системной инструкцией.

        Args:
            new_system_instruction (Optional[str]): Новая системная инструкция.
            initial_history (Optional[List[Dict]]): Начальная история для нового чата.

        Returns:
            None
        """
        if new_system_instruction is not None:
            self.system_instruction = new_system_instruction

        self.chat_history = []
        self._chat = self._start_chat(
            initial_history=initial_history,
            initial_system_instruction=self.system_instruction
        )
        logger.info('Новый сеанс чата успешно начат')

    async def _save_chat_history(self) -> bool:
        """
        Функция асинхронно сохраняет текущую историю чата в JSON файл.

        Returns:
            bool: True в случае успешного сохранения, False при ошибке.
        """
        json_file_name: str = f'{self.chat_session_name}-{self.timestamp}.json'
        self.history_json_file = self.history_dir / json_file_name

        if not j_dumps(self.chat_history, self.history_json_file):
            logger.error(f'Ошибка сохранения истории чата в файл {self.history_json_file}')
            return False
        
        logger.info(f'История чата сохранена в файл {self.history_json_file}')
        return True

    async def _load_chat_history(self, chat_data_folder: Optional[str | Path] = None) -> None:
        """
        Функция асинхронно загружает историю чата из JSON файла.

        Args:
            chat_data_folder (Optional[str | Path]): Путь к папке с файлом 'history.json'.

        Returns:
            None
        """
        history_to_load: Optional[List[Dict]] = None
        target_file: Path = self.history_json_file

        try:
            if chat_data_folder:
                target_file = Path(chat_data_folder) / 'history.json'

            if not target_file.exists():
                logger.info(f'Файл истории {target_file} не найден. Новая история будет создана')
                self.chat_history = []
                self._chat = self._start_chat(initial_system_instruction=self.system_instruction)
                return

            history_to_load = j_loads(target_file)
            
            if not history_to_load:
                logger.error(f'Файл истории {target_file} пуст или содержит некорректные данные')
                self.chat_history = []
                self._chat = self._start_chat(initial_system_instruction=self.system_instruction)
                return

            # Удаление системной инструкции из загруженной истории
            if (self.system_instruction and history_to_load and 
                history_to_load[0].get('role') == 'user' and 
                self.system_instruction in history_to_load[0].get('parts', [])):
                history_to_load = history_to_load[1:]
                logger.debug('Системная инструкция удалена из загруженной истории')

            self.chat_history = history_to_load
            self._chat = self._start_chat(
                initial_history=self.chat_history,
                initial_system_instruction=self.system_instruction
            )

            logger.info(f'История чата ({len(self.chat_history)} сообщений) загружена из {target_file}')

        except Exception as ex:
            logger.error(f'Ошибка загрузки истории чата из файла {target_file}: {ex}')
            self.chat_history = []
            self._chat = self._start_chat(initial_system_instruction=self.system_instruction)

    def clear_history(self) -> None:
        """
        Функция очищает историю чата в памяти и удаляет связанный JSON файл.

        Returns:
            None
        """
        try:
            self.chat_history = []
            if self.history_json_file.exists():
                self.history_json_file.unlink()
                logger.info(f'Файл истории {self.history_json_file} удалён')
            
            self._chat = self._start_chat(initial_system_instruction=self.system_instruction)
            logger.info('История чата очищена и сеанс перезапущен')
        except Exception as ex:
            logger.error(f'Ошибка при очистке истории чата: {ex}')

    async def chat(
        self,
        q: str,
        chat_session_name: Optional[str] = '',
        context: Optional[Union[str, List[str]]] = None
    ) -> Optional[str]:
        """
        Функция обрабатывает чат-запрос пользователя с поддержкой RAG.

        Args:
            q (str): Вопрос пользователя.
            chat_session_name (str): Имя чата для сохранения/загрузки истории.
            context (Optional[Union[str, List[str]]]): Дополнительный контекст для RAG.

        Returns:
            Optional[str]: Текстовый ответ модели или None в случае ошибки.
        """
        self.chat_session_name = chat_session_name if chat_session_name else self.chat_session_name
        response_text: Optional[str] = None

        # Формирование содержимого запроса с учетом контекста
        parts_to_send: List[Any] = []
        if context:
            context_str: str = '\n'.join(context) if isinstance(context, list) else context
            parts_to_send.append(f'Контекст:\n{context_str}\n\n')
            logger.debug(f'Контекст RAG добавлен в запрос (длина: {len(context_str)} символов)')

        parts_to_send.append(q)

        try:
            try:
                response = await self._chat.send_message_async(parts_to_send)

            except ResourceExhausted:
                logger.error('Исчерпан ресурс (Resource exhausted). Возможно, превышена квота')
                logger.info(f'Пауза перед перезапуском чата: {QUOTA_EXHAUSTED_SLEEP_SECONDS} секунд')
                await asyncio.sleep(QUOTA_EXHAUSTED_SLEEP_SECONDS)
                self.start_new_chat_session(new_system_instruction=self.system_instruction)
                return None

            except InvalidArgument as ex:
                logger.error(f'Недопустимый аргумент (InvalidArgument): {ex}')
                if hasattr(ex, 'message') and 'maximum number of tokens allowed' in ex.message:
                    logger.warning('Превышен лимит токенов. Перезапуск чата и повторная попытка')
                    self.start_new_chat_session(new_system_instruction=self.system_instruction)
                    return await self.chat(q, chat_session_name, context)
                return None

            except RpcError as ex:
                logger.error(f'Ошибка RPC: {ex.code()} - {ex.details()}')
                if ex.code() == grpc.StatusCode.DEADLINE_EXCEEDED:
                    timeout: int = 300
                    logger.debug(f'Таймаут RPC. Пауза {timeout} секунд, затем перезапуск чата')
                    await asyncio.sleep(timeout)
                    self.start_new_chat_session(new_system_instruction=self.system_instruction)
                    return await self.chat(q, chat_session_name, context)
                return None

            except Exception as ex:
                logger.error(f'Общая ошибка при отправке сообщения в чат: {ex}')
                return None

            # Обработка ответа
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                logger.info(f'Токены в ответе: {response.usage_metadata.candidates_token_count}')
                logger.info(f'Токены в запросе: {response.usage_metadata.prompt_token_count}')
                logger.info(f'Общее количество токенов: {response.usage_metadata.total_token_count}')

            if hasattr(response, 'text') and response.text:
                response_text = response.text
                self.chat_history.append({'role': 'user', 'parts': parts_to_send})
                self.chat_history.append({'role': 'model', 'parts': [response_text]})
                await self._save_chat_history()
                return response_text
            else:
                logger.error(f'Пустой ответ от модели. Ответ: {response}')
                if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
                    logger.warning(f'Обратная связь по промпту: {response.prompt_feedback}')
                return None

        except Exception as ex:
            logger.error(f'Критическая ошибка в методе chat: {ex}')
            return None

    def ask(
        self,
        q: str,
        attempts: int = 15,
        save_dialogue: bool = False,
        clean_response: bool = True,
        context: Optional[Union[str, List[str]]] = None
    ) -> Optional[str]:
        """
        Функция синхронно отправляет текстовый запрос модели с поддержкой RAG.

        Args:
            q (str): Текстовый запрос к модели.
            attempts (int): Количество попыток отправки запроса. По умолчанию 15.
            save_dialogue (bool): Флаг сохранения диалога в файл.
            clean_response (bool): Флаг очистки ответа от разметки. По умолчанию True.
            context (Optional[Union[str, List[str]]]): Дополнительный контекст для RAG.

        Returns:
            Optional[str]: Текстовый ответ модели или None в случае неудачи.
        """
        response_text: Optional[str] = None

        # Формирование содержимого запроса с учетом контекста
        content_to_send: List[Any] = []
        if context:
            context_str: str = '\n'.join(context) if isinstance(context, list) else context
            content_to_send.append(f'Контекст:\n{context_str}\n\n')
            logger.debug(f'Контекст RAG добавлен в запрос (длина: {len(context_str)} символов)')

        content_to_send.append(q)

        for attempt in range(attempts):
            try:
                response = self.model.generate_content(content_to_send)

                if hasattr(response, 'text') and response.text:
                    response_text = response.text
                    return normalize_answer(response_text) if clean_response else response_text
                else:
                    sleep_time: int = INITIAL_RETRY_SLEEP_SECONDS ** attempt
                    logger.debug(
                        f'От модели не получен ответ. Попытка: {attempt + 1}/{attempts}. '
                        f'Пауза: {sleep_time} сек.'
                    )
                    time.sleep(sleep_time)
                    continue

            except (GatewayTimeout, ServiceUnavailable):
                if attempt >= SERVICE_UNAVAILABLE_MAX_ATTEMPTS:
                    logger.error(f'Сервис недоступен после {SERVICE_UNAVAILABLE_MAX_ATTEMPTS} попыток')
                    break
                sleep_time: int = INITIAL_RETRY_SLEEP_SECONDS ** attempt + SERVICE_RETRY_SLEEP_SECONDS_BASE
                logger.error(
                    f'Сервис недоступен. Попытка: {attempt + 1}/{attempts}. '
                    f'Пауза: {sleep_time} сек.'
                )
                time.sleep(sleep_time)
                continue

            except ResourceExhausted:
                logger.critical('Исчерпан лимит. В ответе будет передан `ResourceExhausted` строкой')
                return 'ResourceExhausted'

            except (DefaultCredentialsError, RefreshError):
                logger.error('Ошибка аутентификации')
                return None
            except (InvalidArgument, RpcError):
                logger.error('Ошибка API')
                return None
            except RetryError:
                logger.error('Модель перегружена (RetryError). Попробуйте позже')
                return None
            except Exception as ex:
                logger.error(f'Ошибка при отправке запроса модели: {ex}')
                return None
            finally:
                processing_time: float = time.time() - start_time
                logger.info(f'Время обработки изображения: {processing_time:.2f} сек.')

            if hasattr(response, 'text') and response.text:
                return response.text
            else:
                logger.info(f'Модель вернула ответ без текста: {response}')
                if hasattr(response, 'prompt_feedback'):
                    logger.warning(f'Обратная связь по промпту: {response.prompt_feedback}')
                return None

        except Exception as ex:
            logger.error(f'Произошла ошибка при обработке изображения: {ex}')
            return None

    async def upload_file(
        self,
        file: str | Path | IOBase,
        file_name: Optional[str] = None
    ) -> Optional[Any]:
        """
        Функция асинхронно загружает файл в Google AI File API.

        Args:
            file (str | Path | IOBase): Путь к файлу или файловый объект.
            file_name (Optional[str]): Имя файла для отображения в API.

        Returns:
            Optional[Any]: Объект File от API в случае успеха, иначе None.
        """
        resolved_file_path: Optional[Path | IOBase] = None
        resolved_file_name: Optional[str] = file_name

        try:
            if isinstance(file, Path):
                resolved_file_path = file
                if not resolved_file_name:
                    resolved_file_name = file.name
            elif isinstance(file, str):
                resolved_file_path = Path(file)
                if not resolved_file_name:
                    resolved_file_name = resolved_file_path.name
            elif isinstance(file, IOBase):
                if not resolved_file_name:
                    logger.warning('Для IOBase рекомендуется указывать file_name')
                    if hasattr(file, 'name'):
                        resolved_file_name = Path(file.name).name
                    else:
                        resolved_file_name = 'uploaded_file'
                resolved_file_path = file
            else:
                logger.error(f'Неподдерживаемый тип для file: {type(file)}')
                return None

            logger.debug(f'Начало загрузки файла: {resolved_file_name or resolved_file_path}')
            
            response = await genai.upload_file_async(
                path=resolved_file_path,
                mime_type=None,
                name=resolved_file_name,
                display_name=resolved_file_name,
                resumable=True,
            )
            
            logger.debug(f'Файл "{response.display_name}" (URI: {response.uri}) успешно загружен')
            return response

        except Exception as ex:
            logger.error(f'Ошибка загрузки файла "{resolved_file_name or file}": {ex}')
            return None

            except (ValueError, TypeError):
                if attempt >= INVALID_INPUT_MAX_ATTEMPTS:
                    logger.error(f'Ошибка входных данных после {INVALID_INPUT_MAX_ATTEMPTS} попыток')
                    break
                logger.error(f'Некорректные входные данные. Попытка: {attempt + 1}/{attempts}')
                time.sleep(5)
                continue

            except (InvalidArgument, RpcError):
                logger.error('Ошибка API')
                return None

            except Exception as ex:
                logger.error(f'Неожиданная ошибка: {ex}')
                return None

        logger.error(f'Не удалось получить ответ от модели после {attempts} попыток')
        return None

    async def ask_async(
        self,
        q: str,
        attempts: int = 15,
        save_dialogue: bool = False,
        clean_response: bool = True,
        context: Optional[Union[str, List[str]]] = None
    ) -> Optional[str]:
        """
        Функция асинхронно отправляет текстовый запрос модели с поддержкой RAG.

        Args:
            q (str): Текстовый запрос к модели.
            attempts (int): Количество попыток отправки запроса. По умолчанию 15.
            save_dialogue (bool): Флаг сохранения диалога в файл.
            clean_response (bool): Флаг очистки ответа от разметки. По умолчанию True.
            context (Optional[Union[str, List[str]]]): Дополнительный контекст для RAG.

        Returns:
            Optional[str]: Текстовый ответ модели или None в случае неудачи.
        """
        response_text: Optional[str] = None

        # Формирование содержимого запроса с учетом контекста
        content_to_send: List[Any] = []
        if context:
            context_str: str = '\n'.join(context) if isinstance(context, list) else context
            content_to_send.append(f'Контекст:\n{context_str}\n\n')
            logger.debug(f'Контекст RAG добавлен в запрос (длина: {len(context_str)} символов)')

        content_to_send.append(q)

        for attempt in range(attempts):
            try:
                response = await self.model.generate_content_async(content_to_send)
                logger.info(f'Модель {self.model_name} обработала запрос')

                if hasattr(response, 'text') and response.text:
                    response_text = response.text
                    return normalize_answer(response_text) if clean_response else response_text
                else:
                    sleep_time: int = INITIAL_RETRY_SLEEP_SECONDS ** attempt
                    logger.debug(
                        f'От модели не получен ответ. Попытка: {attempt + 1}/{attempts}. '
                        f'Асинхронная пауза: {sleep_time} сек.'
                    )
                    await asyncio.sleep(sleep_time)
                    continue

            except (GatewayTimeout, ServiceUnavailable):
                if attempt >= SERVICE_UNAVAILABLE_MAX_ATTEMPTS:
                    logger.error(f'Сервис недоступен после {SERVICE_UNAVAILABLE_MAX_ATTEMPTS} попыток')
                    break
                sleep_time: int = INITIAL_RETRY_SLEEP_SECONDS ** attempt + SERVICE_RETRY_SLEEP_SECONDS_BASE
                logger.error(
                    f'Сервис недоступен. Попытка: {attempt + 1}/{attempts}. '
                    f'Асинхронная пауза: {sleep_time} сек.'
                )
                await asyncio.sleep(sleep_time)
                continue

            except ResourceExhausted:
                logger.critical('Исчерпана квота')
                timeout_quota: int = QUOTA_EXHAUSTED_SLEEP_SECONDS
                logger.debug(
                    f'Исчерпана квота. Попытка: {attempt + 1}/{attempts}. '
                    f'Асинхронная пауза: {timeout_quota/3600} час(ов)'
                )
                await asyncio.sleep(timeout_quota)
                continue

            except (DefaultCredentialsError, RefreshError):
                logger.error('Ошибка аутентификации')
                return None

            except (ValueError, TypeError):
                if attempt >= INVALID_INPUT_MAX_ATTEMPTS:
                    logger.error(f'Ошибка входных данных после {INVALID_INPUT_MAX_ATTEMPTS} попыток')
                    break
                logger.error(f'Некорректные входные данные. Попытка: {attempt + 1}/{attempts}')
                await asyncio.sleep(5)
                continue

            except (InvalidArgument, RpcError):
                logger.error('Ошибка API')
                return None

            except Exception as ex:
                logger.error(f'Неожиданная ошибка: {ex}')
                return None

        logger.error(f'Не удалось получить ответ от модели после {attempts} попыток')
        return None

    def describe_image(
        self,
        image: Path | bytes,
        mime_type: Optional[str] = 'image/jpeg',
        prompt: Optional[str] = ''
    ) -> Optional[str]:
        """
        Функция отправляет изображение в модель Gemini и возвращает его описание.

        Args:
            image (Path | bytes): Путь к файлу изображения или байты изображения.
            mime_type (Optional[str]): MIME-тип изображения. По умолчанию 'image/jpeg'.
            prompt (Optional[str]): Текстовый промпт для модели вместе с изображением.

        Returns:
            Optional[str]: Текстовое описание изображения или None при ошибке.
        """
        image_data: bytes
        start_time: float = time.time()

        try:
            if isinstance(image, Path):
                img_bytes = get_image_bytes(str(image))
                if not img_bytes:
                    logger.error(f'Не удалось прочитать байты изображения из файла: {image}')
                    return None
                image_data = img_bytes
            elif isinstance(image, bytes):
                image_data = image
            else:
                logger.error(f'Некорректный тип для image. Ожидается Path или bytes, получено: {type(image)}')
                return None

            content_parts: List[Any] = []
            if prompt:
                content_parts.append({'text': prompt})

            # Загрузка изображения через API
            uploaded_file = genai.upload_file(path=image_data, mime_type=mime_type)
            content_parts.append(uploaded_file)

            try:
                response = self.model.generate_content(content_parts)

            except (DefaultCredentialsError, RefreshError):
                logger.error('Ошибка аутентификации')
                return None