## \file AIEngineer/gemini.py
# -*- coding: utf-8 -*-
#! .pyenv/bin/python3

"""
Модуль для взаимодействия с Google Generative AI (Gemini).
==========================================================

Предоставляет класс GoogleGenerativeAi для работы с моделями Gemini.

.. module:: AIEngineer.gemini
"""

import time
from pathlib import Path
from typing import Optional, Dict, List, Any

import google.generativeai as genai
from google.api_core.exceptions import (
    GatewayTimeout,
    ServiceUnavailable,
    ResourceExhausted,
)
from google.auth.exceptions import (
    DefaultCredentialsError,
    RefreshError,
)
import FreeCAD

from AIEngineer.utils import (
    normalize_answer,
    get_image_bytes,
    j_dumps,
    j_loads,
    pprint as print,
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
    """

    def __init__(
        self,
        api_key: str,
        model_name: str = 'gemini-2.0-flash-exp',
        generation_config: Optional[Dict] = None,
        system_instruction: Optional[str] = None,
    ):
        """
        Функция инициализирует клиент Google Generative AI.
        
        Args:
            api_key (str): API-ключ Google Gemini.
            model_name (str, optional): Имя модели. По умолчанию 'gemini-2.0-flash-exp'.
            generation_config (Optional[Dict], optional): Конфигурация генерации. По умолчанию None.
            system_instruction (Optional[str], optional): Системная инструкция. По умолчанию None.
        
        Raises:
            DefaultCredentialsError: Ошибка аутентификации API.
            RefreshError: Ошибка обновления токена.
            Exception: Неожиданная ошибка инициализации.
        """
        self.api_key: str = api_key
        self.model_name: str = model_name
        self.generation_config: Dict = generation_config if generation_config is not None else {
            'response_mime_type': 'text/plain'
        }
        self.system_instruction: Optional[str] = system_instruction

        logger.debug(f'Инициализация GoogleGenerativeAi: model_name={self.model_name}, '
                     f'generation_config={self.generation_config}')

        if not self.api_key:
            logger.error('API-ключ не предоставлен')
            raise ValueError('API key is required')

        try:
            genai.configure(api_key=self.api_key)
            logger.debug('Gemini API сконфигурирован с ключом API')

            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=self.generation_config,
                system_instruction=self.system_instruction,
            )
            logger.info(f'Модель {self.model_name} инициализирована')
        except (DefaultCredentialsError, RefreshError):
            logger.error('Ошибка аутентификации Gemini API')
            raise
        except Exception as ex:
            logger.error(f'Не удалось инициализировать модель Gemini: {ex}')
            raise

    def ask(
        self, 
        q: str, 
        image_path: Optional[str] = None,
        attempts: int = 5
    ) -> Optional[str]:
        """
        Функция отправляет запрос в Google Gemini и возвращает ответ.
        
        Args:
            q (str): Текстовый запрос.
            image_path (Optional[str], optional): Путь к изображению. По умолчанию None.
            attempts (int, optional): Количество попыток повтора. По умолчанию 5.
        
        Returns:
            Optional[str]: Ответ от модели или None при ошибке.
        
        Example:
            >>> llm = GoogleGenerativeAi(api_key='your-key')
            >>> response = llm.ask('Опиши эту деталь', image_path='drawing.png')
            >>> print(response)
        """
        content_parts: List[Any] = []
        logger.debug(f'Начало обработки запроса: "{q}" с изображением: {image_path}')

        # Добавление изображения если указано
        if image_path and Path(image_path).exists():
            try:
                uploaded_file = genai.upload_file(image_path)
                content_parts.append(uploaded_file)
                logger.info(f'Изображение {image_path} загружено')
                logger.debug(f'Uploaded file объект: {uploaded_file}')
            except Exception as ex:
                logger.error(f'Ошибка загрузки изображения: {image_path} - {ex}')

        content_parts.append(q)
        logger.debug(f'Сформирован контент для отправки: {content_parts}')

        for attempt in range(attempts):
            logger.debug(f'Попытка {attempt + 1}/{attempts} отправки запроса')
            try:
                response = self.model.generate_content(content_parts)
                if hasattr(response, 'text') and response.text:
                    normalized: str = normalize_answer(response.text)
                    logger.debug(f'Нормализованный ответ: {normalized[:100]}...')
                    return normalized
                else:
                    sleep_time: int = INITIAL_RETRY_SLEEP_SECONDS ** attempt
                    logger.debug(f'Пустой ответ. Пауза: {sleep_time} сек.')
                    time.sleep(sleep_time)
            except ResourceExhausted:
                logger.critical('Исчерпан лимит запросов (ResourceExhausted)')
                return 'ResourceExhausted'
            except (DefaultCredentialsError, RefreshError):
                logger.error('Ошибка аутентификации')
                return None
            except (GatewayTimeout, ServiceUnavailable):
                if attempt >= SERVICE_UNAVAILABLE_MAX_ATTEMPTS:
                    logger.error(f'Сервис недоступен после {SERVICE_UNAVAILABLE_MAX_ATTEMPTS} попыток')
                    break
                sleep_time: int = INITIAL_RETRY_SLEEP_SECONDS ** attempt + SERVICE_RETRY_SLEEP_SECONDS_BASE
                logger.error(f'Сервис недоступен. Попытка {attempt + 1}/{attempts}. Пауза: {sleep_time} сек.')
                time.sleep(sleep_time)
            except Exception as ex:
                logger.error(f'Неожиданная ошибка при генерации ответа: {ex}')
                return None

        logger.error(f'Не удалось получить ответ после {attempts} попыток')
        return None