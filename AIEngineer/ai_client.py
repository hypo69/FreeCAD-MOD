## \file AIAssistant/ai_client.py
# -*- coding: utf-8 -*-
#! .pyenv/bin/python3

"""
Универсальный клиент для взаимодействия с ИИ-провайдерами: Ollama, OpenAI, Google Gemini.
Поддерживает отправку текста и изображений.
"""

import os
import json
import base64
import requests
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
import FreeCAD
from AIEngineer.settings_dialog import SettingsDialog
from AIEngineer.gemini import GoogleGenerativeAi

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

        url: str = "https://api.openai.com/v1/chat/completions"
        headers: Dict[str, str] = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        messages = [{"role": "user", "content": [{"type": "text", "text": prompt}]}]
        if image_path and Path(image_path).suffix.lower() in {'.png', '.jpg', '.jpeg'}:
            b64_img = self.encode_image(image_path)
            messages[0]["content"].append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}
            })

        payload: Dict[str, Any] = {"model": self.model, "messages": messages, "max_tokens": 1000}
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as ex:
            return f"OpenAI error: {str(ex)}"


class GeminiClient:
    """Клиент для Google Gemini API (адаптированный из gemini.py)."""

    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash-latest"):
        """Функция инициализирует клиент Google Generative AI."""
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(model_name=model_name)
            log_info(f"Gemini model '{model_name}' initialized")
        except Exception as ex:
            log_error(f"Failed to initialize Gemini: {str(ex)}")
            raise

    def ask(self, prompt: str, image_path: Optional[str] = None) -> Optional[str]:
        """Функция отправляет запрос в Gemini и возвращает ответ."""
        import google.generativeai as genai
        content = []
        if image_path and Path(image_path).exists():
            try:
                uploaded_file = genai.upload_file(image_path)
                content = [uploaded_file, prompt]
                log_info(f"Image {image_path} uploaded to Gemini")
            except Exception as ex:
                log_error(f"Image upload failed: {str(ex)}")
                content = [prompt]
        else:
            content = [prompt]

        try:
            response = self.model.generate_content(content)
            if hasattr(response, 'text') and response.text:
                return response.text.strip()
            else:
                log_error("Empty response from Gemini")
                return None
        except Exception as ex:
            return f"Gemini error: {str(ex)}"


# === УНИВЕРСАЛЬНЫЙ КЛИЕНТ ===
class AIClient:
    """Универсальный клиент для выбора ИИ-провайдера."""

    def __init__(self):
        """Функция инициализирует настройки из QSettings."""
        from PySide import QtCore
        settings = QtCore.QSettings("FreeCAD", "AIAssistant")
        self.provider = settings.value("provider", "gemini")
        self.model = settings.value("model", "gemini-1.5-flash-latest")
        self.api_key = settings.value("api_key", "")
        self.base_url = settings.value("base_url", "http://localhost:11434")

    def ask(self, prompt: str, image_path: Optional[str] = None) -> str:
        """Функция отправляет запрос выбранному ИИ-провайдеру."""
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
                return response if response is not None else "Gemini returned empty response."
            except Exception as ex:
                return f"Gemini error: {str(ex)}"
        else:
            return f"Provider '{self.provider}' is not supported."