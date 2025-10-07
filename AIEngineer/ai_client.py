## \file AIAssistant/ai_client.py
# -*- coding: utf-8 -*-

"""
Универсальный клиент для взаимодействия с ИИ-провайдерами: Ollama, OpenAI, Google Gemini.
Поддерживает отправку текста и изображений.

Этот модуль предоставляет единый интерфейс для работы с разными ИИ-провайдерами,
абстрагируя различия в их API. Поддерживается как текстовый ввод, так и мультимодальный
ввод с изображениями (где это поддерживается провайдером).

Важно: для Google Gemini используется библиотека google-generativeai версии 0.6.0 и выше.
В этих версиях изменился способ работы с изображениями и конфигурацией генерации.
"""

import os
import json
import base64
import requests
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
import FreeCAD

# === ЛОГГЕР ДЛЯ FREECAD ===
def log_info(msg: str) -> None:
    """Функция записывает информационное сообщение в консоль FreeCAD."""
    FreeCAD.Console.PrintMessage(f"[AIAssistant] {msg}\n")

def log_error(msg: str) -> None:
    """Функция записывает ошибку в консоль FreeCAD."""
    FreeCAD.Console.PrintError(f"[AIAssistant] ERROR: {msg}\n")


# === КЛИЕНТЫ ПРОВАЙДЕРОВ ===
class OllamaClient:
    """Клиент для локальных моделей через Ollama API."""

    def __init__(self, model: str = "llava:latest", base_url: str = "http://localhost:11434"):
        """Функция инициализирует параметры подключения к Ollama."""
        self.model = model
        self.base_url = base_url

    def encode_image(self, image_path: str) -> str:
        """Функция кодирует изображение в base64."""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def ask(self, prompt: str, image_path: Optional[str] = None) -> str:
        """Функция отправляет запрос в Ollama и возвращает ответ."""
        url: str = f"{self.base_url}/api/generate"
        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        if image_path and Path(image_path).suffix.lower() in {'.png', '.jpg', '.jpeg'}:
            payload["images"] = [self.encode_image(image_path)]

        try:
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            return response.json().get("response", "No response")
        except Exception as ex:
            return f"Ollama error: {str(ex)}"


class OpenAIClient:
    """Клиент для OpenAI API."""

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        """Функция инициализирует параметры подключения к OpenAI."""
        self.api_key = api_key
        self.model = model

    def encode_image(self, image_path: str) -> str:
        """Функция кодирует изображение в base64."""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def ask(self, prompt: str, image_path: Optional[str] = None) -> str:
        """Функция отправляет запрос в OpenAI и возвращает ответ."""
        if not self.api_key:
            return "OpenAI error: API key not set."

        # Исправлено: удалены лишние пробелы в конце URL, которые вызывали ошибку 404
        url: str = "https://api.openai.com/v1/chat/completions"
        headers: Dict[str, str] = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        messages = [{"role": "user", "content": [{"type": "text", "text": prompt}]}]
        if image_path and Path(image_path).suffix.lower() in {'.png', '.jpg', '.jpeg'}:
            b64_img = self.encode_image(image_path)
            # Определяем MIME-тип на основе расширения файла для корректной обработки OpenAI
            mime_type = "image/jpeg" if Path(image_path).suffix.lower() in ['.jpg', '.jpeg'] else "image/png"
            messages[0]["content"].append({
                "type": "image_url",
                "image_url": {"url": f"data:{mime_type};base64,{b64_img}"}
            })

        payload: Dict[str, Any] = {"model": self.model, "messages": messages, "max_tokens": 1000}
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as ex:
            return f"OpenAI error: {str(ex)}"


class GeminiClient:
    """
    Клиент для Google Gemini API.

    Важно: начиная с версии google-generativeai >= 0.6.0 (2024–2025 гг.),
    изменились следующие аспекты:
    
    1. Глобальная функция `genai.upload_file()` больше не существует.
       Вместо этого изображения передаются напрямую в `generate_content`
       как строка пути (str) или байты (bytes).
    
    2. Параметр `response_mime_type: 'text/plain'` в `GenerationConfig`
       больше не поддерживается и вызывает ошибку:
       "Unknown field for GenerationConfig: response_mime_type".
       Текстовый ответ является поведением по умолчанию, поэтому
       дополнительная конфигурация не требуется.
    
    3. Модели семейства Gemini 2.5 (например, gemini-2.5-flash,
       gemini-2.5-pro, gemini-2.5-flash-lite) доступны через API
       и могут использоваться напрямую по имени.
    
    Данный клиент учитывает все эти изменения и работает корректно
    с актуальными версиями библиотеки.
    """

    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        """
        Функция инициализирует клиент Google Generative AI.
        
        Аргументы:
            api_key (str): Ключ API для доступа к Google Generative AI.
            model_name (str): Имя модели Gemini. По умолчанию используется
                              "gemini-2.5-flash", но поддерживаются также
                              "gemini-2.5-pro", "gemini-2.5-flash-lite",
                              "gemini-1.5-flash", "gemini-1.5-pro".
        """
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            
            # Убираем generation_config с response_mime_type — он больше не поддерживается.
            # В новых версиях библиотеки (>=0.6.0) указание 'text/plain' вызывает ошибку:
            # "Unknown field for GenerationConfig: response_mime_type".
            # Поскольку текстовый ответ является поведением по умолчанию,
            # мы не передаём никакую generation_config, если она не требуется для специальных задач (например, JSON).
            self.model = genai.GenerativeModel(model_name=model_name)
            log_info(f"Gemini model '{model_name}' initialized")
        except Exception as ex:
            log_error(f"Failed to initialize Gemini: {str(ex)}")
            raise

    def ask(self, prompt: str, image_path: Optional[str] = None) -> Optional[str]:
        """
        Функция отправляет запрос в Gemini и возвращает ответ.
        
        Поддерживается мультимодальный ввод: текст + изображение.
        Изображение передаётся как строка пути к файлу — это требование
        современной версии google-generativeai.
        
        Аргументы:
            prompt (str): Текстовый запрос к модели.
            image_path (Optional[str]): Путь к изображению (опционально).
        
        Возвращает:
            Optional[str]: Текстовый ответ модели или None в случае пустого ответа.
        """
        content = []
        if prompt:
            content.append(prompt)

        # Передаём изображение как строку пути (str), а не как объект Path.
        # Библиотека google-generativeai >= 0.6.0 ожидает именно строку или байты.
        # Передача объекта pathlib.Path вызывает ошибку:
        # "Could not create `Blob`, expected `Blob`, `dict` or an `Image` type..."
        if image_path and Path(image_path).exists():
            content.append(str(image_path))  # ← КЛЮЧЕВОЕ ИЗМЕНЕНИЕ: преобразуем Path в str
            log_info(f"Image path added to Gemini request: {image_path}")
        elif image_path:
            log_error(f"Image file not found: {image_path}")

        try:
            response = self.model.generate_content(content)
            if hasattr(response, 'text') and response.text:
                return response.text.strip()
            else:
                log_error("Empty response from Gemini")
                return None
        except Exception as ex:
            log_error(f"Gemini request failed: {str(ex)}")
            return f"Gemini error: {str(ex)}"


# === УНИВЕРСАЛЬНЫЙ КЛИЕНТ ===
class AIClient:
    """
    Универсальный клиент для выбора ИИ-провайдера.
    
    Загружает настройки из QSettings FreeCAD и автоматически создаёт
    экземпляр нужного клиента (Ollama, OpenAI или Gemini).
    """

    def __init__(self):
        """Функция инициализирует настройки из QSettings."""
        from PySide import QtCore
        settings = QtCore.QSettings("FreeCAD", "AIAssistant")
        self.provider = settings.value("provider", "gemini")
        self.model = settings.value("model", "gemini-2.5-flash")
        self.api_key = settings.value("api_key", "")
        self.base_url = settings.value("base_url", "http://localhost:11434")

    def ask(self, prompt: str, image_path: Optional[str] = None) -> str:
        """
        Функция отправляет запрос выбранному ИИ-провайдеру.
        
        Аргументы:
            prompt (str): Текстовый запрос.
            image_path (Optional[str]): Путь к изображению (если поддерживается провайдером).
        
        Возвращает:
            str: Ответ от ИИ-провайдера или сообщение об ошибке.
        """
        if self.provider == "ollama":
            client = OllamaClient(model=self.model, base_url=self.base_url)
            return client.ask(prompt, image_path)
        elif self.provider == "openai":
            client = OpenAIClient(api_key=self.api_key, model=self.model)
            return client.ask(prompt, image_path)
        elif self.provider == "gemini":
            try:
                client = GeminiClient(api_key=self.api_key, model_name=self.model)
                response = client.ask(prompt, image_path)