# gemini.py
import asyncio
import time
from pathlib import Path
from typing import Optional, Dict, List, Any, Union
from io import IOBase
import google.generativeai as genai
from google.api_core.exceptions import (
    GatewayTimeout,
    ServiceUnavailable,
    ResourceExhausted,
    InvalidArgument,
)
from google.auth.exceptions import (
    DefaultCredentialsError,
    RefreshError,
)
import FreeCAD
from .utils import (
    normalize_answer,
    get_image_bytes,
    j_dumps,
    j_loads,
    pprint as print,
)

# === ЗАМЕНА header, gs ===
class MockGS:
    @property
    def now(self):
        return time.strftime("%Y%m%d_%H%M%S")

gs = MockGS()

# === ЛОГГЕР ДЛЯ FREECAD ===
class MockLogger:
    def info(self, msg, *args, **kwargs):
        FreeCAD.Console.PrintMessage(f"[Gemini] INFO: {msg}\n")
    def error(self, msg, *args, **kwargs):
        FreeCAD.Console.PrintError(f"[Gemini] ERROR: {msg}\n")
    def warning(self, msg, *args, **kwargs):
        FreeCAD.Console.PrintMessage(f"[Gemini] WARN: {msg}\n")
    def debug(self, msg, *args, **kwargs):
        FreeCAD.Console.PrintMessage(f"[Gemini] DEBUG: {msg}\n")
    def critical(self, msg, *args, **kwargs):
        FreeCAD.Console.PrintError(f"[Gemini] CRITICAL: {msg}\n")

logger = MockLogger()

NETWORK_ERROR_MAX_ATTEMPTS = 5
SERVICE_UNAVAILABLE_MAX_ATTEMPTS = 3
INVALID_INPUT_MAX_ATTEMPTS = 3
INITIAL_RETRY_SLEEP_SECONDS = 2
NETWORK_RETRY_SLEEP_SECONDS = 120
SERVICE_RETRY_SLEEP_SECONDS_BASE = 10
QUOTA_EXHAUSTED_SLEEP_SECONDS = 14400

class GoogleGenerativeAi:
    """
    Класс для взаимодействия с моделями Google GenerativeAi.

    Атрибуты:
        api_key (str): Ключ API для доступа к Google Generative AI.
        generation_config (Dict): Конфигурация для генерации ответов моделью.
                                  По умолчанию `{'response_mime_type': 'text/plain'}`.
                                  Допустимые mime-типы: `text/plain`, `application/json`,
                                  `application/xml`, `application/yaml`, `text/x.enum`.
        system_instruction (Optional[str]): Системная инструкция для модели. По умолчанию `None`.
        model_name (str): Имя Используетсяой модели Gemini.
        config (SimpleNamespace): Загруженная конфигурация из файла 'gemini.json'.
        history_dir (Path): Директория для сохранения истории чатов.
        timestamp (str): Текущая временная метка для именования файлов истории.
        model (Any): Инициализированный клиент модели `genai.GenerativeModel`.
        _chat (Any): Активный сеанс чата с моделью.
        chat_history (List[Dict]): История текущего диалога в памяти.
        chat_session_name (str): Имя текущего чата для сохранения истории.
        history_json_file (Path): Путь к JSON файлу с историей текущего чата.
    """
    ENDPOINT:Path = __root__/ 'src'/ 'llm'/ 'gemini'
    config: SimpleNamespace = j_loads_ns(ENDPOINT/ 'gemini.json')
    api_key: str
    system_instruction: Optional[str]
    model_name: str = config.model_name
    model: genai.GenerativeModel # Уточненный тип

    timestamp: str
    _chat: genai.ChatSession # Уточненный тип
    chat_history: List[Dict] = []
    chat_session_name: str = gs.now
    history_dir: Path = Path()
    history_json_file: Path = Path()
    dialogue_txt_path: Path = Path()
    history_txt_file: Path = Path()


    def __init__(
        self,
        api_key: str,
        model_name: str = 'gemini-2.5-flash',
        generation_config: Optional[Dict] = None, # По умолчанию используется {'response_mime_type': 'text/plain'}
        system_instruction: Optional[str] = None,
    ):
        """
        Инициализирует экземпляр класса GoogleGenerativeAi.

        Args:
            api_key (str): Ключ API для Google Generative AI.
            model_name (str): Имя модели Gemini для использования (например, 'gemini-pro').
            generation_config (Dict, optional): Конфигурация генерации.
                                                По умолчанию `{'response_mime_type': 'text/plain'}`.
            system_instruction (Optional[str], optional): Системная инструкция для модели.
                                                         По умолчанию `None`.
        """

        self.api_key = api_key
        self.model_name = model_name
        # Используем предложенный generation_config, если он задан,
        # иначе используем стандартный для plain text
        self.generation_config = generation_config if generation_config is not None else {'response_mime_type': 'text/plain'}
        self.system_instruction = system_instruction

        self.history_dir = Path(__root__, gs.path.external_storage, 'chats')
        self.timestamp = gs.now

        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=self.generation_config,
                # System instruction передается при старте чата, а не при инициализации модели,
                # если вы хотите, чтобы она применялась к истории.
                # genai 0.6.0+ поддерживает system_instruction в GenerativeModel,
                # но для чата лучше передавать его в history.
                # Если вы используете genai >= 0.6.0 и хотите system_instruction,
                # который применяется ко всей модели независимо от истории чата,
                # то оставьте его здесь. Для гибкости сброса, я его уберу отсюда.
                # system_instruction=self.system_instruction, # Убираем отсюда
                system_instruction = self.system_instruction,
            )
            # При первом старте чата _start_chat будет использовать self.system_instruction
            self._chat = self._start_chat(initial_system_instruction=self.system_instruction)

            logger.info(f"Модель {self.model.model_name} инициализирована", None, False)
        except (DefaultCredentialsError, RefreshError) as ex:
             logger.error('Ошибка аутентификации Gemini API', exc_info=True)
             raise # Повторный вызыв исключения, чтобы прервать инициализацию
        except Exception as ex:
            logger.error('Не удалось инициализировать модель Gemini', exc_info=True)
            raise # Повторный вызыв исключения, чтобы прервать инициализацию


    def _start_chat(self, initial_history: Optional[List[Dict]] = None,
                    initial_system_instruction: Optional[str] = None) -> genai.ChatSession:
        """
        Функция запускает новый сеанс чата с моделью.

        Учитывает наличие `system_instruction` при инициализации чата.

        Args:
            initial_history (Optional[List[Dict]]): История для загрузки в чат.
            initial_system_instruction (Optional[str]): Системная инструкция для этой сессии чата.

        Returns:
            genai.ChatSession: Объект сеанса чата.
        """
        history_to_load = initial_history if initial_history is not None else []
        
        # Если есть системная инструкция, добавляем её в начало истории как сообщение пользователя
        # Это распространенный паттерн для Gemini, когда system_instruction передается как первый user-сообщение.
        # В genai 0.6.0+, system_instruction можно передать в GenerativeModel, но для reset-able чатов
        # включение его в history при старте чата может быть более гибким.
        if initial_system_instruction:
            # Проверяем, не является ли первое сообщение уже системной инструкцией
            if not history_to_load or (history_to_load[0].get('role') == 'user' and initial_system_instruction not in history_to_load[0].get('parts', [])):
                history_to_load.insert(0, {'role': 'user', 'parts': [initial_system_instruction]})
                logger.debug(f"Системная инструкция '{initial_system_instruction[:50]}...' добавлена в историю чата.")

        return self.model.start_chat(history=history_to_load)

    # Добавление метода для перезапуска чата с новой системной инструкцией или историей
    def start_new_chat_session(self, new_system_instruction: Optional[str] = None,
                               initial_history: Optional[List[Dict]] = None) -> None:
        """
        Начинает новый сеанс чата, опционально с новой системной инструкцией и/или историей.

        Args:
            new_system_instruction (Optional[str]): Новая системная инструкция для этого чата.
                                                    Если None, используется текущая `self.system_instruction`.
            initial_history (Optional[List[Dict]]): Начальная история для нового чата.
        """
        if new_system_instruction is not None:
            self.system_instruction = new_system_instruction # Обновляем системную инструкцию экземпляра

        self.chat_history = [] # Очищаем историю в памяти
        self._chat = self._start_chat(initial_history=initial_history,
                                      initial_system_instruction=self.system_instruction)
        logger.info("Новый сеанс чата успешно начат.")


    async def _save_chat_history(self) -> bool:
        """
        Функция асинхронно сохраняет текущую историю чата в JSON файл.

        Имя файла формируется из `chat_session_name` и `timestamp`.

        Returns:
            bool: `True` в случае успешного сохранения, `False` при ошибке.
        """
        json_file_name: str = f'{self.chat_session_name}-{self.timestamp}.json'
        self.history_json_file = Path(self.history_dir, json_file_name)

        # Создание директории, если она не существует
        try:
            self.history_dir.mkdir(parents=True, exist_ok=True)
        except Exception as ex:
            logger.error(f'Не удалось создать директорию для истории чата: {self.history_dir}', exc_info=True)
            return False

        if not j_dumps(data=self.chat_history, file_path=self.history_json_file, mode='w'):
            logger.error(f"Ошибка сохранения истории чата в файл {self.history_json_file=}", None, False)
            return False
        logger.info(f"История чата сохранена в файл {self.history_json_file=}", None, False)
        return True

    async def _load_chat_history(self, chat_data_folder: Optional[str | Path]) -> None:
        """
        Функция асинхронно загружает историю чата из JSON файла.

        Опционально принимает путь к папке с данными чата. Если указан,
        использует 'history.json' из этой папки. Иначе использует
        текущий `self.history_json_file`.

        Args:
            chat_data_folder (Optional[str | Path]): Путь к папке с файлом 'history.json'.

        Returns:
            None
        """
        history_to_load: Optional[List[Dict]] = None
        target_file: Path = self.history_json_file # По умолчанию Используется текущий файл

        try:
            if chat_data_folder:
                # Если указана папка, формируем путь к history.json в ней
                target_file = Path(chat_data_folder, 'history.json')

            if target_file.exists():
                history_to_load = j_loads(target_file)
                if history_to_load is not None:
                    # Очищаем историю от системной инструкции, если она была добавлена
                    # как первое сообщение, чтобы не дублировать её при перезапуске чата.
                    if self.system_instruction and history_to_load and \
                       history_to_load[0].get('role') == 'user' and \
                       self.system_instruction in history_to_load[0].get('parts', []):
                       # Удаляем системную инструкцию из истории, которую Передача в _start_chat,
                       # так как _start_chat её добавит
                       history_to_load = history_to_load[1:]
                       logger.debug("Системная инструкция удалена из загруженной истории для корректного старта чата.")


                    self.chat_history = history_to_load
                    # Перезапускаем чат с загруженной историей и системной инструкцией
                    self._chat = self._start_chat(initial_history=self.chat_history,
                                                  initial_system_instruction=self.system_instruction)

                    logger.info(f"История чата ({len(self.chat_history)} сообщений) загружена из файла. \n{target_file=}", None, False)
                else:
                     logger.error(f"Файл истории {target_file=} пуст или содержит некорректные данные.", None, False)
            else:
                logger.info(f"Файл истории {target_file=} не найден. Новая история будет создана.", None, False)
                self.chat_history = [] # Проверка, что история пуста, если файл не найден
                self._chat = self._start_chat(initial_system_instruction=self.system_instruction) # Начинаем новый чат

        except Exception as ex:
            logger.error(f"Ошибка загрузки истории чата из файла {target_file=}", exc_info=True)
            self.chat_history = [] # Сброс истории при ошибке загрузки
            self._chat = self._start_chat(initial_system_instruction=self.system_instruction) # Начинаем новый чат при ошибке

    def clear_history(self) -> None:
        """
        Функция очищает историю чата в памяти и удаляет связанный JSON файл истории.
        Перезапускает текущий чат-сеанс.

        Returns:
            None
        """
        try:
            self.chat_history = []  # Очистка истории в памяти
            if hasattr(self, 'history_json_file') and self.history_json_file.exists():
                self.history_json_file.unlink()  # Удаление файла истории
                logger.info(f"Файл истории {self.history_json_file} удалён.")
            # Перезапускаем чат, чтобы он начал с чистого листа
            self._chat = self._start_chat(initial_system_instruction=self.system_instruction)
            logger.info("История чата очищена и сеанс перезапущен.")
        except Exception as ex:
            logger.error('Ошибка при очистке истории чата.', exc_info=True)

    async def chat(self, q: str, chat_session_name: Optional[str] = '',
                   context: Optional[Union[str, List[str]]] = None) -> Optional[str]:
        """
        Функция обрабатывает чат-запрос пользователя, управляет историей и возвращает ответ модели.
        Добавлена возможность передачи контекста для RAG.

        Args:
            q (str): Вопрос пользователя.
            chat_session_name (str): Имя чата для сохранения/загрузки истории.
            context (Optional[Union[str, List[str]]]): Дополнительный контекст для модели (для RAG).
                                                       Может быть строкой или списком строк.

        Returns:
            Optional[str]: Текстовый ответ модели или `None` в случае ошибки.
        """
        self.chat_session_name = chat_session_name if chat_session_name else self.chat_session_name
        response: Any = None
        response_text: Optional[str] = None

        # Формирование содержимого запроса с учетом контекста
        parts_to_send: List[Any] = []
        if context:
            if isinstance(context, list):
                context_str = "\n".join(context)
            else:
                context_str = context
            parts_to_send.append(f"Контекст:\n{context_str}\n\n")
            logger.debug(f"Контекст RAG добавлен в запрос (длина: {len(context_str)} символов).")

        parts_to_send.append(q) # Добавляем основной запрос пользователя

        try:
            # Отправка запроса модели
            try:
                # Асинхронная отправка сообщения с учетом дополнительных частей
                response = await self._chat.send_message_async(parts_to_send)

            except ResourceExhausted as ex:
                logger.error("Исчерпан ресурс (Resource exhausted). Возможно, превышена квота.", exc_info=True)
                logger.info(f"Пауза перед перезапуском чата: {QUOTA_EXHAUSTED_SLEEP_SECONDS} секунд.")
                await asyncio.sleep(QUOTA_EXHAUSTED_SLEEP_SECONDS) # Длительная пауза при исчерпании квоты
                self.start_new_chat_session(new_system_instruction=self.system_instruction) # Перезапуск чата
                return None

            except InvalidArgument as ex:
                 logger.error("Недопустимый аргумент (InvalidArgument)", exc_info=True)
                 # Проверка на превышение лимита токенов
                 if hasattr(ex, 'message') and 'maximum number of tokens allowed' in ex.message:
                    logger.warning("Превышен лимит токенов. Перезапуск чата и повторная попытка...")
                    # Очищаем историю и пробуем снова (может помочь, если проблема в длинной истории)
                    self.start_new_chat_session(new_system_instruction=self.system_instruction)
                    return await self.chat(q, chat_session_name, context) # Повторная попытка
                 return None

            except RpcError as ex:
                # Обработка ошибок gRPC, включая таймауты
                logger.error(f"Ошибка RPC: {ex.code()} - {ex.details()}", exc_info=True)
                if ex.code() == grpc.StatusCode.DEADLINE_EXCEEDED:
                     timeout: int = 300 # Уменьшенное время ожидания
                     logger.debug(f'Таймаут RPC. Пауза {timeout} секунд, затем перезапуск чата.')
                     await asyncio.sleep(timeout)
                     self.start_new_chat_session(new_system_instruction=self.system_instruction)
                     return await self.chat(q, chat_session_name, context) # Повторная попытка
                return None

            except Exception as ex:
                 logger.error("Общая ошибка при отправке сообщения в чат", exc_info=True)
                 return None

            # Обработка ответа и метаданных
            try:
                if hasattr(response, 'usage_metadata') and response.usage_metadata:
                    response_token_count = response.usage_metadata.candidates_token_count
                    total_token_count = response.usage_metadata.total_token_count
                    prompt_token_count = response.usage_metadata.prompt_token_count

                    logger.info(f"Токены в ответе: {response_token_count}")
                    logger.info(f"Токены в запросе: {prompt_token_count}")
                    logger.info(f"Общее количество токенов: {total_token_count}")
                else:
                    logger.warning("Метаданные об использовании токенов отсутствуют в ответе (usage_metadata is None or empty).")

            except AttributeError:
                logger.warning("Атрибут 'usage_metadata' отсутствует в объекте ответа.")
            except Exception as meta_ex:
                 logger.error("Ошибка при извлечении метаданных токенов", exc_info=True)

            # Проверка и извлечение текста ответа
            if hasattr(response, 'text') and response.text:
                response_text = response.text
                # Добавление запроса (возможно, с контекстом) и ответа в историю
                self.chat_history.append({"role": "user", "parts": parts_to_send}) # Сохраняем как отправили
                self.chat_history.append({"role": "model", "parts": [response_text]})
                await self._save_chat_history()
                return response_text
            else:
                logger.error(f"Пустой ответ от модели. Ответ: {response}", None, False)
                if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
                    logger.warning(f"Обратная связь по промпту: {response.prompt_feedback}", None, False)
                return None

        except Exception as ex:
            logger.error(f"Критическая ошибка в методе chat. Ответ: {response}", exc_info=True)
            return None

    def ask(self, q: str, attempts: int = 15, save_dialogue: bool = False,
            clean_response: bool = True, context: Optional[Union[str, List[str]]] = None) -> Optional[str]:
        """
        Метод синхронно отправляет текстовый запрос модели и возвращает ответ.
        Использует `generate_content` (не для чата). Повторяет запрос при ошибках.
        Добавлена возможность передачи контекста для RAG.

        Args:
            q (str): Текстовый запрос к модели.
            attempts (int): Количество попыток отправки запроса. По умолчанию 15.
            save_dialogue (bool): Флаг сохранения диалога (вопрос/ответ) в файл.
            clean_response (bool): Флаг очистки ответа от разметки кода. По умолчанию True.
            context (Optional[Union[str, List[str]]]): Дополнительный контекст для модели (для RAG).

        Returns:
            Optional[str]: Текстовый ответ модели или `None` в случае неудачи после всех попыток.
        """
        response: Any = None
        response_text: Optional[str] = None

        # Формирование содержимого запроса с учетом контекста
        content_to_send: List[Any] = []
        if context:
            if isinstance(context, list):
                context_str = "\n".join(context)
            else:
                context_str = context
            content_to_send.append(f"Контекст:\n{context_str}\n\n")
            logger.debug(f"Контекст RAG добавлен в запрос (длина: {len(context_str)} символов).")

        content_to_send.append(q)

        for attempt in range(attempts):
            try:
                response = self.model.generate_content(content_to_send)

                if hasattr(response, 'text') and response.text:
                    response_text = response.text
                    if save_dialogue:
                        # TODO: Реализовать _save_dialogue
                        logger.warning("Функция _save_dialogue не реализована, история не сохранена.")

                    return normalize_answer(response_text) if clean_response else response_text
                else:
                    sleep_time = INITIAL_RETRY_SLEEP_SECONDS ** attempt
                    logger.debug(
                        f"От модели не получен ответ. Попытка: {attempt + 1}/{attempts}. Пауза: {sleep_time} сек.",
                        None,
                        False
                    )
                    time.sleep(sleep_time)
                    continue

            except requests.exceptions.RequestException as ex:
                if attempt >= NETWORK_ERROR_MAX_ATTEMPTS:
                    logger.error(f"Сетевая ошибка после {NETWORK_ERROR_MAX_ATTEMPTS} попыток.", exc_info=True)
                    break
                sleep_time_network = NETWORK_RETRY_SLEEP_SECONDS
                logger.debug(
                    f"Сетевая ошибка. Попытка: {attempt + 1}/{attempts}. Пауза: {sleep_time_network/60} мин. Время: {gs.now}",
                    exc_info=True,
                    # False, # Убрал exc_info=False, так как exc_info=True логирует трейсбек
                )
                time.sleep(sleep_time_network)
                continue

            except (GatewayTimeout, ServiceUnavailable) as ex:
                if attempt >= SERVICE_UNAVAILABLE_MAX_ATTEMPTS:
                     logger.error(f"Сервис недоступен после {SERVICE_UNAVAILABLE_MAX_ATTEMPTS} попыток.", exc_info=True)
                     break
                sleep_time_service = INITIAL_RETRY_SLEEP_SECONDS**attempt + SERVICE_RETRY_SLEEP_SECONDS_BASE
                logger.error(f"Сервис недоступен. Попытка: {attempt + 1}/{attempts}. Пауза: {sleep_time_service} сек.", exc_info=True)
                time.sleep(sleep_time_service)
                continue

            except ResourceExhausted as ex:
                logger.critical(f"""
                ------------------------------------------------------------------------

                Исчерпан лимит. В ответе будет передан `ResourceExhausted` строкой.

                -------------------------------------------------------------------------
                """, None, False)
                return "ResourceExhausted"

            except (DefaultCredentialsError, RefreshError) as ex:
                logger.error("Ошибка аутентификации.", exc_info=True)
                return None

            except (ValueError, TypeError) as ex:
                if attempt >= INVALID_INPUT_MAX_ATTEMPTS:
                    logger.error(f"Ошибка входных данных после {INVALID_INPUT_MAX_ATTEMPTS} попыток.", exc_info=True)
                    break
                timeout_input = 5
                logger.error(
                    f"Некорректные входные данные. Попытка: {attempt + 1}/{attempts}. Пауза: {timeout_input} сек. Время: {gs.now}",
                    exc_info=True,
                )
                time.sleep(timeout_input)
                continue

            except (InvalidArgument, RpcError) as ex:
                logger.error("Ошибка API.", exc_info=True)
                return None

            except Exception as ex:
                logger.error("Неожиданная ошибка.", exc_info=True)
                return None

        logger.error(f"Не удалось получить ответ от модели после {attempts} попыток.")
        return None

    async def ask_async(self, q: str, attempts: int = 15, save_dialogue: bool = False,
                        clean_response: bool = True, context: Optional[Union[str, List[str]]] = None) -> Optional[str]:
        """
        Метод асинхронно отправляет текстовый запрос модели и возвращает ответ.
        Использует `generate_content` (не для чата) в отдельном потоке. Повторяет запрос при ошибках.
        Добавлена возможность передачи контекста для RAG.

        Args:
            q (str): Текстовый запрос к модели.
            attempts (int): Количество попыток отправки запроса. По умолчанию 15.
            save_dialogue (bool): Флаг сохранения диалога (вопрос/ответ) в файл.
            clean_response (bool): Флаг очистки ответа от разметки кода. По умолчанию True.
            context (Optional[Union[str, List[str]]]): Дополнительный контекст для модели (для RAG).

        Returns:
            Optional[str]: Текстовый ответ модели или `None` в случае неудачи после всех попыток.
        """
        response: Any = None
        response_text: Optional[str] = None

        # Формирование содержимого запроса с учетом контекста
        content_to_send: List[Any] = []
        if context:
            if isinstance(context, list):
                context_str = "\n".join(context)
            else:
                context_str = context
            content_to_send.append(f"Контекст:\n{context_str}\n\n")
            logger.debug(f"Контекст RAG добавлен в запрос (длина: {len(context_str)} символов).")

        content_to_send.append(q)

        for attempt in range(attempts):
            try:
                response = await self.model.generate_content_async(content_to_send)
                logger.info(f'Модель {self.model.model_name} Обработала запрос',None, False)

                if hasattr(response, 'text') and response.text:
                    response_text = response.text
                    if save_dialogue:
                        # TODO: Реализовать _save_dialogue
                        logger.warning("Функция _save_dialogue не реализована, история не сохранена.")

                    return normalize_answer(response_text) if clean_response else response_text

                else:
                    sleep_time = INITIAL_RETRY_SLEEP_SECONDS ** attempt
                    logger.debug(
                        f"От модели не получен ответ. Попытка: {attempt + 1}/{attempts}. Асинхронная пауза: {sleep_time} сек.",
                        None,
                        False
                    )
                    await asyncio.sleep(sleep_time)
                    continue


            except requests.exceptions.RequestException as ex:
                if attempt >= NETWORK_ERROR_MAX_ATTEMPTS:
                    logger.error(f"Сетевая ошибка после {NETWORK_ERROR_MAX_ATTEMPTS} попыток.", exc_info=True)
                    break
                sleep_time_network: int = NETWORK_RETRY_SLEEP_SECONDS
                logger.debug(
                    f"Сетевая ошибка. Попытка: {attempt + 1}/{attempts}. Асинхронная пауза: {sleep_time_network/60} мин. Время: {gs.now}",
                    exc_info=True,
                )
                await asyncio.sleep(sleep_time_network)
                continue

            except (GatewayTimeout, ServiceUnavailable) as ex:
                if attempt >= SERVICE_UNAVAILABLE_MAX_ATTEMPTS:
                     logger.error(f"Сервис недоступен после {SERVICE_UNAVAILABLE_MAX_ATTEMPTS} попыток.", exc_info=True)
                     break
                sleep_time_service = INITIAL_RETRY_SLEEP_SECONDS**attempt + SERVICE_RETRY_SLEEP_SECONDS_BASE
                logger.error(f"Сервис недоступен. Попытка: {attempt + 1}/{attempts}. Асинхронная пауза: {sleep_time_service} сек.", exc_info=True)
                await asyncio.sleep(sleep_time_service)
                continue

            except ResourceExhausted as ex:
                 # Длительная асинхронная пауза при исчерпании квоты
                logger.critical(f"""
                ------------------------------------------------------------------------

                Исчерпана квота.

                -------------------------------------------------------------------------
                """, None, False)
                timeout_quota: int = QUOTA_EXHAUSTED_SLEEP_SECONDS
                logger.debug(
                    f"Исчерпана квота. Попытка: {attempt + 1}/{attempts}. Асинхронная пауза: {timeout_quota/3600} час(ов). Время: {gs.now}",
                    exc_info=True,
                )
                await asyncio.sleep(timeout_quota)
                continue

            except (DefaultCredentialsError, RefreshError) as ex:
                logger.error("Ошибка аутентификации.", exc_info=True)
                return None

            except (ValueError, TypeError) as ex:
                if attempt >= INVALID_INPUT_MAX_ATTEMPTS:
                    logger.error(f"Ошибка входных данных после {INVALID_INPUT_MAX_ATTEMPTS} попыток.", exc_info=True)
                    break
                timeout_input = 5
                logger.error(
                    f"Некорректные входные данные. Попытка: {attempt + 1}/{attempts}. Асинхронная пауза: {timeout_input} сек. Время: {gs.now}",
                    exc_info=True,
                )
                await asyncio.sleep(timeout_input)
                continue

            except (InvalidArgument, RpcError) as ex:
                logger.error("Ошибка API.", exc_info=True)
                return None

            except Exception as ex:
                logger.error("Неожиданная ошибка.", exc_info=True)
                return None

        logger.error(f"Не удалось получить ответ от модели после {attempts} попыток.")
        return None


    def describe_image(
        self, image: Path | bytes, mime_type: Optional[str] = 'image/jpeg', prompt: Optional[str] = ''
    ) -> Optional[str]:
        """
        Функция отправляет изображение (и опциональный промпт) в модель Gemini Pro Vision
        и возвращает его текстовое описание.

        Args:
            image (Path | bytes): Путь к файлу изображения или байты изображения.
            mime_type (Optional[str]): MIME-тип изображения. По умолчанию 'image/jpeg'.
            prompt (Optional[str]): Текстовый промпт для модели вместе с изображением. По умолчанию ''.

        Returns:
            Optional[str]: Текстовое описание изображения от модели или `None` при ошибке.
        """

        image_data: bytes
        content: List[Any]
        response: Any = None
        response_text: Optional[str] = None
        start_time: float = time.time()

        try:
            if isinstance(image, Path):
                img_bytes = get_image_bytes(image)
                if img_bytes is None:
                     logger.error(f"Не удалось прочитать байты изображения из файла: {image}")
                     return None
                image_data = img_bytes
            elif isinstance(image, bytes):
                image_data = image
            else:
                logger.error(f"Некорректный тип для 'image'. Ожидается Path или bytes, получено: {type(image)}")
                return None

            content_parts: List[Any] = []
            if prompt:
                content_parts.append({"text": prompt}) # Явно указываем тип content

            content_parts.append(genai.upload_file_async(path=image_data, mime_type=mime_type)) # Использование API для загрузки файла

            # Отправка запроса
            try:
                # generate_content теперь принимает список Content (текст и File)
                response = self.model.generate_content(content_parts)

            except DefaultCredentialsError as ex:
                logger.error("Ошибка аутентификации:", exc_info=True)
                return None
            except (InvalidArgument, RpcError) as ex:
                logger.error("Ошибка API:", exc_info=True)
                return None
            except RetryError as ex:
                logger.error("Модель перегружена (RetryError). Попробуйте позже:", exc_info=True)
                return None
            except Exception as ex:
                logger.error("Ошибка при отправке запроса модели:", exc_info=True)
                return None
            finally:
                 processing_time = time.time() - start_time
                 logger.info(f'\nВремя обработки изображения: {processing_time:.2f} сек.\n', text_color='yellow', bg_color='red')

            if hasattr(response, 'text') and response.text:
                 response_text = response.text
                 return response_text
            else:
                 logger.info(f"{{Модель вернула ответ без текста: {response}}}", text_color='cyan')
                 if hasattr(response, 'prompt_feedback'):
                     logger.warning(f"Обратная связь по промпту: {response.prompt_feedback}")
                 return None

        except Exception as ex:
            logger.error("Произошла ошибка при обработке изображения:", exc_info=True)
            return None

    async def upload_file(
        self, file: str | Path | IOBase, file_name: Optional[str] = None
    ) -> Optional[Any]: # Возвращает объект File или None
        """
        Асинхронно загружает файл в Google AI File API.

        https://github.com/google-gemini/generative-ai-python/blob/main/docs/api/google/generativeai/upload_file.md

        Args:
            file (str | Path | IOBase): Путь к файлу или файловый объект.
            file_name (Optional[str]): Имя файла для отображения в API. Если None,
                                       используется имя из пути файла.

        Returns:
            Optional[Any]: Объект `File` от API в случае успеха, иначе `None`.
                           (Тип Any, т.к. `file_types.File` не экспортируется явно).
        """

        response: Any = None
        resolved_file_path: Optional[Path] = None
        resolved_file_name: Optional[str] = file_name

        try:
            if isinstance(file, Path):
                resolved_file_path = file
                if resolved_file_name is None:
                    resolved_file_name = file.name
            elif isinstance(file, str):
                 resolved_file_path = Path(file)
                 if resolved_file_name is None:
                    resolved_file_name = resolved_file_path.name
            elif isinstance(file, IOBase):
                 if resolved_file_name is None:
                     logger.warning("Для IOBase рекомендуется указывать file_name.")
                     if hasattr(file, 'name'):
                         resolved_file_name = Path(file.name).name
                     else:
                         resolved_file_name = 'uploaded_file'
                 resolved_file_path = file # type: ignore
            else:
                 logger.error(f"Неподдерживаемый тип для 'file': {type(file)}")
                 return None

            logger.debug(f"Начало загрузки файла: {resolved_file_name or resolved_file_path}")
            response = await genai.upload_file_async(
                path=resolved_file_path, # type: ignore
                mime_type=None,
                name=resolved_file_name,
                display_name=resolved_file_name,
                resumable=True,
            )
            logger.debug(f"Файл '{response.display_name}' (URI: {response.uri}) успешно загружен.", None, False)
            return response

        except Exception as ex:
            logger.error(f"Ошибка загрузки файла '{resolved_file_name or file}'", exc_info=True)
            return None


async def main():
    """Основная асинхронная функция для демонстрации работы класса."""
    onela:str = gs.credentials.gemini.onela.api_key
    kazarinov:str = gs.credentials.gemini.kazarinov.api_key
    system_instruction = 'Ты — полезный ассистент, который всегда отвечает очень кратко и по существу, используя не более двух предложений.'
    # model_name = 'gemini-2.5-flash-preview-04-17' # Убедитесь, что это актуальное имя для Flash
    model_name = 'gemini-1.5-flash-latest' # Рекомендуется использовать latest

    if not onela and not kazarinov:
        logger.error("Ключ API Gemini не найден в gs.credentials.gemini.api_key.")
        return

    try:
        llm = GoogleGenerativeAi(
            api_key = kazarinov,
            model_name = model_name,
            system_instruction = system_instruction,
            # Можно явно указать response_mime_type здесь, если хотите,
            # например, для получения JSON ответов по умолчанию.
            # generation_config={'response_mime_type': 'application/json'}
        )
    except Exception as ex:
        logger.error(f"Не удалось инициализировать GoogleGenerativeAi:", exc_info=True)
        return

    logger.info("\nНачало сеанса чата. Введите 'exit' для выхода.")
    chat_session_name = f'chat_session_{gs.now}'

    # --- Пример использования нового метода для начала новой сессии (с новой системной инструкцией) ---
    # llm.start_new_chat_session(new_system_instruction='Ты — поэт, который отвечает на все вопросы в форме хайку.')
    # llm_message = await llm.chat('Привет, поэт! Как твои дела?', chat_session_name)
    # if llm_message:
    #      logger.info(f"Gemini (поэт): {llm_message}")


    # --- Пример использования chat с контекстом (RAG) ---
    print("\n--- Пример чата с контекстом (RAG) ---")
    rag_context = [
        "Петров Иван Васильевич (id: 12345) - менеджер по продажам. Его телефон: +79123456789, email: ivan.petrov@example.com.",
        "Сидорова Анна Петровна (id: 67890) - руководитель отдела маркетинга. Её телефон: +79876543210, email: anna.sidorova@example.com.",
        "Компания 'Альфа' является нашим ключевым партнером.",
        "Основной продукт компании - 'Виртуальный помощник 2.0'."
    ]

    llm_message = await llm.chat('Какой телефон у Петрова Ивана Васильевича?',
                                 chat_session_name=chat_session_name,
                                 context=rag_context)
    if llm_message:
        logger.info(f"Gemini (с RAG): {llm_message}")
    else:
        logger.warning("Gemini (с RAG): Не удалось получить ответ.")

    llm_message = await llm.chat('Кто руководитель отдела маркетинга?',
                                 chat_session_name=chat_session_name,
                                 context=rag_context)
    if llm_message:
        logger.info(f"Gemini (с RAG): {llm_message}")
    else:
        logger.warning("Gemini (с RAG): Не удалось получить ответ.")

    # --- Пример использования ask_async с контекстом (RAG, stateless) ---
    print("\n--- Пример stateless запроса с контекстом (RAG) ---")
    query_stateless = "Каков основной продукт компании 'Альфа'?"
    llm_message_stateless = await llm.ask_async(query_stateless, context=rag_context)
    if llm_message_stateless:
        logger.info(f"Gemini (ask_async с RAG): {llm_message_stateless}")
    else:
        logger.warning("Gemini (ask_async с RAG): Не удалось получить ответ.")


    # --- Продолжение обычного чата (без контекста, если не передать) ---
    print("\n--- Продолжение обычного чата (без контекста) ---")
    llm_message = await llm.chat('Привет! Как дела?', chat_session_name)
    if llm_message:
         logger.info(f"Gemini: {llm_message}")

    while True:
        try:
            user_message = input("You: ")
        except EOFError:
             logger.info("\nЗавершение чата по EOF.")
             break
        if user_message.lower() == 'exit':
            logger.info("Завершение чата по команде пользователя.")
            break

        llm_message = await llm.chat(user_message, chat_session_name=chat_session_name)
        if llm_message:
            logger.info(f"Gemini: {llm_message}")
        else:
            logger.warning("Gemini: Не удалось получить ответ.")


# if __name__ == "__main__":
#     asyncio.run(main())