# Документация AIClient

## Обзор

Модуль `ai_client.py` предоставляет универсальный интерфейс для работы с различными AI-провайдерами:
- **Ollama** - локальные модели (например, llava:latest)
- **OpenAI** - GPT-4o, GPT-4-vision
- **Google Gemini** - gemini-2.5-flash, gemini-2.5-pro

## Архитектура

```
AIClient (универсальный интерфейс)
    ├── OllamaClient
    ├── OpenAIClient
    └── GeminiClient
```

---

## Класс AIClient

### Описание

Универсальный клиент, который автоматически выбирает провайдера на основе настроек QSettings FreeCAD.

### Инициализация

```python
from AIEngineer.ai_client import AIClient

client = AIClient()
# Автоматически загружает настройки из QSettings:
# - provider: "ollama" | "openai" | "gemini"
# - model: название модели
# - api_key: API-ключ (для OpenAI и Gemini)
# - base_url: URL сервера (для Ollama)
```

### Конфигурация QSettings

Настройки хранятся в:
```
Организация: "FreeCAD"
Приложение: "AIAssistant"
```

Ключи:
- `provider` (str): "ollama" | "openai" | "gemini"
- `model` (str): название модели
- `api_key` (str): API-ключ
- `base_url` (str): URL для Ollama (по умолчанию: "http://localhost:11434")

### Метод ask()

```python
def ask(prompt: str, image_path: Optional[str] = None) -> str
```

**Параметры:**
- `prompt` (str): Текстовый запрос к AI
- `image_path` (Optional[str]): Путь к изображению (опционально)

**Возвращает:**
- `str`: Ответ от выбранного AI-провайдера или сообщение об ошибке

**Пример:**

```python
# Текстовый запрос
response = client.ask("Объясни принцип работы редуктора")
print(response)

# Запрос с изображением
response = client.ask(
    "Опиши эту деталь",
    image_path="C:/drawings/part.jpg"
)
print(response)
```

---

## Класс OllamaClient

### Описание

Клиент для локальных моделей через Ollama API.

### Инициализация

```python
from AIEngineer.ai_client import OllamaClient

client = OllamaClient(
    model="llava:latest",
    base_url="http://localhost:11434"
)
```

**Параметры:**
- `model` (str): Название модели Ollama (по умолчанию: "llava:latest")
- `base_url` (str): URL сервера Ollama (по умолчанию: "http://localhost:11434")

### Метод ask()

```python
def ask(prompt: str, image_path: Optional[str] = None) -> str
```

**Параметры:**
- `prompt` (str): Текстовый запрос
- `image_path` (Optional[str]): Путь к изображению (.png, .jpg, .jpeg)

**Возвращает:**
- `str`: Ответ модели или сообщение об ошибке

**Особенности:**
- Изображение кодируется в base64 автоматически
- Таймаут запроса: 120 секунд
- Поддерживаемые форматы изображений: PNG, JPG, JPEG

**Пример:**

```python
client = OllamaClient(model="llava:latest")

# Без изображения
response = client.ask("Что такое CAD?")

# С изображением
response = client.ask(
    "Опиши этот чертеж",
    image_path="drawing.png"
)
```

### Метод encode_image()

```python
def encode_image(image_path: str) -> str
```

Функция кодирует изображение в base64 для передачи в API.

**Параметры:**
- `image_path` (str): Путь к файлу изображения

**Возвращает:**
- `str`: Base64-строка

---

## Класс OpenAIClient

### Описание

Клиент для OpenAI API (GPT-4o, GPT-4-vision).

### Инициализация

```python
from AIEngineer.ai_client import OpenAIClient

client = OpenAIClient(
    api_key="sk-...",
    model="gpt-4o"
)
```

**Параметры:**
- `api_key` (str): API-ключ OpenAI
- `model` (str): Название модели (по умолчанию: "gpt-4o")

### Метод ask()

```python
def ask(prompt: str, image_path: Optional[str] = None) -> str
```

**Параметры:**
- `prompt` (str): Текстовый запрос
- `image_path` (Optional[str]): Путь к изображению (.png, .jpg, .jpeg)

**Возвращает:**
- `str`: Ответ модели или сообщение об ошибке

**Особенности:**
- Автоматическое определение MIME-типа изображения
- Изображение кодируется в base64 и встраивается в запрос как data URL
- Максимум токенов в ответе: 1000
- Таймаут: 60 секунд

**Пример:**

```python
client = OpenAIClient(api_key="sk-...")

# Текстовый запрос
response = client.ask("Создай описание болта M8x30")

# С изображением
response = client.ask(
    "Определи размеры детали по чертежу",
    image_path="technical_drawing.jpg"
)
```

### Исправление ошибки 404

В коде исправлена ошибка с лишними пробелами в URL:

```python
# ❌ Старая версия (вызывала 404)
url: str = "https://api.openai.com/v1/chat/completions "

# ✅ Исправленная версия
url: str = "https://api.openai.com/v1/chat/completions"
```

---

## Класс GeminiClient

### Описание

Клиент для Google Gemini API с поддержкой современных версий библиотеки `google-generativeai >= 0.6.0`.

### Важные изменения в API

Начиная с версии 0.6.0 библиотеки `google-generativeai`:

1. **Удален `genai.upload_file()`**
   - Изображения передаются напрямую как строка пути (str) или байты (bytes)

2. **Удален `response_mime_type` из GenerationConfig**
   - Параметр больше не поддерживается и вызывает ошибку
   - Текстовый ответ - поведение по умолчанию

3. **Поддержка моделей Gemini 2.5**
   - gemini-2.5-flash (рекомендуется)
   - gemini-2.5-pro
   - gemini-2.5-flash-lite
   - gemini-1.5-flash
   - gemini-1.5-pro

### Инициализация

```python
from AIEngineer.ai_client import GeminiClient

client = GeminiClient(
    api_key="AIza...",
    model_name="gemini-2.5-flash"
)
```

**Параметры:**
- `api_key` (str): API-ключ Google Gemini
- `model_name` (str): Название модели (по умолчанию: "gemini-2.5-flash")

**Raises:**
- `Exception`: При ошибке инициализации (логируется в FreeCAD Console)

### Метод ask()

```python
def ask(prompt: str, image_path: Optional[str] = None) -> Optional[str]
```

**Параметры:**
- `prompt` (str): Текстовый запрос
- `image_path` (Optional[str]): Путь к изображению

**Возвращает:**
- `Optional[str]`: Текстовый ответ модели или None при ошибке

**Ключевые особенности:**

1. **Передача изображения как строки пути:**
```python
# ❌ Неправильно (вызывает ошибку)
content.append(Path(image_path))

# ✅ Правильно
content.append(str(image_path))
```

2. **Проверка существования файла:**
```python
if image_path and Path(image_path).exists():
    content.append(str(image_path))
    log_info(f"Image path added to Gemini request: {image_path}")
elif image_path:
    log_error(f"Image file not found: {image_path}")
```

3. **Обработка пустых ответов:**
```python
if hasattr(response, 'text') and response.text:
    return response.text.strip()
else:
    log_error("Empty response from Gemini")
    return None
```

**Пример:**

```python
client = GeminiClient(api_key="AIza...")

# Только текст
response = client.ask("Что такое ISO-допуск?")
print(response)

# С изображением
response = client.ask(
    "Определи тип резьбы на этом чертеже",
    image_path="C:/images/thread.png"
)
print(response)
```

---

## Логирование

Все классы используют специальные функции логирования для FreeCAD Console:

### log_info()

```python
def log_info(msg: str) -> None
```

Функция записывает информационное сообщение в консоль FreeCAD.

**Пример:**
```python
log_info("Gemini model 'gemini-2.5-flash' initialized")
```

Вывод:
```
[AIAssistant] Gemini model 'gemini-2.5-flash' initialized
```

### log_error()

```python
def log_error(msg: str) -> None
```

Функция записывает ошибку в консоль FreeCAD.

**Пример:**
```python
log_error("Image file not found: /path/to/image.jpg")
```

Вывод (красным цветом):
```
[AIAssistant] ERROR: Image file not found: /path/to/image.jpg
```

---

## Сравнение провайдеров

| Функция | Ollama | OpenAI | Gemini |
|---------|--------|--------|--------|
| Текстовые запросы | ✅ | ✅ | ✅ |
| Изображения | ✅ | ✅ | ✅ |
| Локальная работа | ✅ | ❌ | ❌ |
| Бесплатный tier | ✅ | ❌ | ✅ (лимит) |
| Максимальный размер изображения | ~5 МБ | ~20 МБ | ~20 МБ |
| Таймаут | 120 сек | 60 сек | ~30 сек |
| Стоимость | Бесплатно | $$ | Бесплатно (лимит) |

---

## Примеры использования

### Пример 1: Автоматический выбор провайдера

```python
from AIEngineer.ai_client import AIClient

# Инициализация с автоматическим выбором провайдера
client = AIClient()

# Провайдер выбирается из QSettings
response = client.ask(
    "Опиши эту деталь детально",
    image_path="part.jpg"
)

print(f"Ответ: {response}")
```

### Пример 2: Явный выбор провайдера

```python
from AIEngineer.ai_client import OllamaClient, OpenAIClient, GeminiClient

# Локальная модель
ollama = OllamaClient(model="llava:13b")
response1 = ollama.ask("Что такое фреза?")

# OpenAI
openai = OpenAIClient(api_key="sk-...")
response2 = openai.ask("Создай список стандартных допусков")

# Gemini
gemini = GeminiClient(api_key="AIza...")
response3 = gemini.ask(
    "Опиши технологию изготовления",
    image_path="drawing.png"
)
```

### Пример 3: Обработка ошибок

```python
from AIEngineer.ai_client import AIClient

client = AIClient()

response = client.ask("Тестовый запрос")

# Проверка на ошибки
if "error" in response.lower():
    print(f"Произошла ошибка: {response}")
elif response.startswith("Ollama error:"):
    print("Проверьте запущен ли сервер Ollama")
elif response.startswith("OpenAI error:"):
    print("Проверьте API-ключ OpenAI")
elif response.startswith("Gemini error:"):
    print("Проверьте API-ключ Gemini")
else:
    print(f"Успешный ответ: {response}")
```

### Пример 4: Пакетная обработка изображений

```python
from pathlib import Path
from AIEngineer.ai_client import GeminiClient

client = GeminiClient(api_key="AIza...")
images_dir = Path("C:/drawings")

results = {}

for image_file in images_dir.glob("*.jpg"):
    response = client.ask(
        "Определи тип детали и основные размеры",
        image_path=str(image_file)
    )
    
    results[image_file.name] = response
    print(f"Обработано: {image_file.name}")

# Сохранение результатов
import json
with open("analysis_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
```

---

## Устранение неполадок

### Ollama

**Ошибка: "Connection refused"**

Решение:
```bash
# Запустите сервер Ollama
ollama serve

# Проверьте доступность
curl http://localhost:11434/api/tags
```

**Ошибка: "Model not found"**

Решение:
```bash
# Загрузите модель
ollama pull llava:latest

# Список доступных моделей
ollama list
```

### OpenAI

**Ошибка: "API key not set"**

Решение:
- Проверьте, что API-ключ корректно сохранен в QSettings
- Откройте AI Settings и введите ключ заново

**Ошибка: 404 Not Found**

Решение:
- Убедитесь, что используете исправленную версию `ai_client.py`
- URL должен быть без пробелов: `https://api.openai.com/v1/chat/completions`

### Gemini

**Ошибка: "Unknown field for GenerationConfig: response_mime_type"**

Решение:
- Обновите библиотеку: `pip install --upgrade google-generativeai`
- Используйте версию >= 0.6.0

**Ошибка: "Could not create Blob, expected Blob, dict or an Image type"**

Решение:
- Передавайте путь к изображению как строку: `str(image_path)`
- НЕ передавайте объект `Path` напрямую

**Ошибка: "Empty response from Gemini"**

Возможные причины:
- Модель заблокировала ответ (safety filters)
- Изображение повреждено или недоступно
- Превышен лимит токенов

Решение:
- Проверьте логи FreeCAD Console
- Попробуйте упростить запрос
- Проверьте файл изображения

---

## Интеграция с AIEngineer

### Использование в командах

Пример из `ask_ai.py`:

```python
from AIEngineer.ai_client import AIClient

# В методе Activated():
client = AIClient()

response = client.ask(
    prompt=user_prompt,
    image_path=str(image_path)
)

# Отображение результата
from AIEngineer.dialogs.ai_response import AIResponseDialog
dialog = AIResponseDialog(user_prompt, response)
dialog.exec_()
```

### Настройка провайдера через QSettings

```python
from PySide import QtCore

settings = QtCore.QSettings("FreeCAD", "AIAssistant")

# Установка провайдера
settings.setValue("provider", "gemini")  # или "ollama", "openai"
settings.setValue("model", "gemini-2.5-flash")
settings.setValue("api_key", "AIza...")

# Для Ollama дополнительно:
settings.setValue("base_url", "http://localhost:11434")
```

---

## API Reference

### AIClient

```python
class AIClient:
    def __init__(self) -> None
    def ask(self, prompt: str, image_path: Optional[str] = None) -> str
```

### OllamaClient

```python
class OllamaClient:
    def __init__(self, model: str = "llava:latest", 
                 base_url: str = "http://localhost:11434") -> None
    def encode_image(self, image_path: str) -> str
    def ask(self, prompt: str, image_path: Optional[str] = None) -> str
```

### OpenAIClient

```python
class OpenAIClient:
    def __init__(self, api_key: str, model: str = "gpt-4o") -> None
    def encode_image(self, image_path: str) -> str
    def ask(self, prompt: str, image_path: Optional[str] = None) -> str
```

### GeminiClient

```python
class GeminiClient:
    def __init__(self, api_key: str, 
                 model_name: str = "gemini-2.5-flash") -> None
    def ask(self, prompt: str, image_path: Optional[str] = None) -> Optional[str]
```

---

## Лицензия

MIT License - см. файл LICENSE

## Автор

hypo69  
GitHub: [github.com/hypo69](https://github.com/hypo69)

---

**Версия документа:** 1.0  
**Дата:** 2025-01-07  
**Применимо к:** AIEngineer v0.2.0+