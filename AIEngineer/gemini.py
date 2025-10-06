## \file AIEngineer/gemini.py
# -*- coding: utf-8 -*-
#! .pyenv/bin/python3

"""
Модуль для взаимодействия с Google Generative AI (Gemini).
==========================================================

Предоставляет класс GoogleGenerativeAi для работы с моделями Gemini.

.. module:: AIEngineer.gemini
"""

import asyncio
import time
from pathlib import Path
from typing import Optional, Dict, List, Any, Union
from types import SimpleNamespace

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
        FreeCAD.Console.PrintMessage(f"[Gemini] INFO: {msg}\n")
    
    def error(self, msg: str, *args, **kwargs) -> None:
        FreeCAD.Console.PrintError(f"[Gemini] ERROR: {msg}\n")
    
    def warning(self, msg: str, *args, **kwargs) -> None:
        FreeCAD.Console.PrintMessage(f"[Gemini] WARN: {msg}\n")
    
    def debug(self, msg: str, *args, **kwargs) -> None:
        FreeCAD.Console.PrintMessage(f"[Gemini] DEBUG: {msg}\n")
    
    def critical(self, msg: str, *args, **kwargs) -> None:
        FreeCAD.Console.PrintError(f"[Gemini] CRITICAL: {msg}\n")

logger = MockLogger()

# === КОНСТАНТЫ ===
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
    """

    def __init__(
        self,
        api_key: str,
        model_name: str = 'gemini-2.0-flash-exp',
        generation_config: Optional[Dict] = None,
        system_instruction: Optional[str] = None,
    ):
        self.api_key = api_key
        self.model_name = model_name
        self.generation_config = generation_config if generation_config is not None else {
            'response_mime_type': 'text/plain'
        }
        self.system_instruction = system_instruction

        logger.debug(f"Инициализация GoogleGenerativeAi: model_name={self.model_name}, "
                     f"generation_config={self.generation_config}")

        try:
            genai.configure(api_key=self.api_key)
            logger.debug("Gemini API сконфигурирован с ключом API")

            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=self.generation_config,
                system_instruction=self.system_instruction,
            )
            logger.info(f"Модель {self.model_name} инициализирована")
        except (DefaultCredentialsError, RefreshError):
            logger.error('Ошибка аутентификации Gemini API')
            raise
        except Exception as ex:
            logger.error('Не удалось инициализировать модель Gemini')
            raise

    def ask(
        self, 
        q: str, 
        image_path: Optional[str] = None,
        attempts: int = 5
    ) -> Optional[str]:
        content_parts: List[Any] = []
        logger.debug(f"Начало обработки запроса: '{q}' с изображением: {image_path}")

        # Добавление изображения если указано
        if image_path and Path(image_path).exists():
            try:
                uploaded_file = genai.upload_file(image_path)
                content_parts.append(uploaded_file)
                logger.info(f"Изображение {image_path} загружено")
                logger.debug(f"Uploaded file объект: {uploaded_file}")
            except Exception:
                logger.error(f"Ошибка загрузки изображения: {image_path}")

        content_parts.append(q)
        logger.debug(f"Сформирован контент для отправки: {content_parts}")

        for attempt in range(attempts):
            logger.debug(f"Попытка {attempt + 1}/{attempts} отправки запроса")
            try:
                response = self.model.generate_content(content_parts)
                if hasattr(response, 'text') and response.text:
                    normalized = normalize_answer(response.text)
                    logger.debug(f"Нормализованный ответ: {normalized}")
                    return normalized
                else:
                    sleep_time = INITIAL_RETRY_SLEEP_SECONDS ** attempt
                    logger.debug(f"Пустой ответ. Пауза: {sleep_time} сек.")
                    time.sleep(sleep_time)
            except ResourceExhausted:
                logger.critical("Исчерпан лимит запросов (ResourceExhausted)")
                return "ResourceExhausted"
            except (DefaultCredentialsError, RefreshError):
                logger.error("Ошибка аутентификации")
                return None
            except (GatewayTimeout, ServiceUnavailable):
                if attempt >= SERVICE_UNAVAILABLE_MAX_ATTEMPTS:
                    logger.error(f"Сервис недоступен после {SERVICE_UNAVAILABLE_MAX_ATTEMPTS} попыток")
                    break
                sleep_time = INITIAL_RETRY_SLEEP_SECONDS ** attempt + SERVICE_RETRY_SLEEP_SECONDS_BASE
                logger.error(f"Сервис недоступен. Попытка {attempt + 1}/{attempts}. Пауза: {sleep_time} сек.")
                time.sleep(sleep_time)
            except Exception:
                logger.error("Неожиданная ошибка при генерации ответа")
                return None

        logger.error(f"Не удалось получить ответ после {attempts} попыток")
        return None
