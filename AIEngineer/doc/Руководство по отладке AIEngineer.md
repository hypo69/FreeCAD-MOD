# Руководство по отладке AIEngineer

## 📋 Оглавление

1. [Включение логирования](#включение-логирования)
2. [Типы логов](#типы-логов)
3. [Отладка по компонентам](#отладка-по-компонентам)
4. [Типичные проблемы](#типичные-проблемы)
5. [Примеры логов](#примеры-логов)

---

## Включение логирования

### Где смотреть логи

**FreeCAD Report View:**
```
View → Panels → Report view
```

Все сообщения AIEngineer имеют префикс `[AIEngineer]`.

### Уровни логирования

| Уровень | Префикс | Цвет | Назначение |
|---------|---------|------|------------|
| INFO | `[AIEngineer] INFO:` | Обычный | Важные события |
| DEBUG | `[AIEngineer] DEBUG:` | Обычный | Детальная отладка |
| ERROR | `[AIEngineer] ERROR:` | Красный | Ошибки |

---

## Типы логов

### 1. Инициализация компонентов

**AIClient:**
```
[AIEngineer] DEBUG: AIClient initializing
[AIEngineer] DEBUG: AIClient settings loaded:
[AIEngineer] DEBUG:   provider: gemini
[AIEngineer] DEBUG:   model: gemini-2.5-flash
[AIEngineer] DEBUG:   api_key_length: 39
[AIEngineer] DEBUG:   base_url: http://localhost:11434
```

**OllamaClient:**
```
[AIEngineer] DEBUG: OllamaClient initialized: model=llava:latest, base_url=http://localhost:11434
```

**OpenAIClient:**
```
[AIEngineer] DEBUG: OpenAIClient initialized: model=gpt-4o, api_key_length=51
```

**GeminiClient:**
```
[AIEngineer] DEBUG: GeminiClient initializing: model_name=gemini-2.5-flash, api_key_length=39
[AIEngineer] DEBUG: GeminiClient: google.generativeai imported successfully
[AIEngineer] DEBUG: GeminiClient: API key configured
[AIEngineer] INFO: Gemini model 'gemini-2.5-flash' initialized
[AIEngineer] DEBUG: GeminiClient initialization complete
```

### 2. Обработка запросов

**Вызов ask():**
```
[AIEngineer] DEBUG: AIClient.ask called: provider=gemini, prompt_length=25, image_path=None
[AIEngineer] DEBUG: AIClient: creating GeminiClient
```

**С изображением:**
```
[AIEngineer] DEBUG: GeminiClient.ask called: prompt_length=50, image_path=/path/to/image.jpg
[AIEngineer] DEBUG: GeminiClient: prompt added to content
[AIEngineer] DEBUG: GeminiClient: checking image path existence: /path/to/image.jpg
[AIEngineer] DEBUG: GeminiClient: image file exists, size: 1048576 bytes
[AIEngineer] INFO: Image path added to Gemini request: /path/to/image.jpg
[AIEngineer] DEBUG: GeminiClient: content list prepared, items count: 2
```

### 3. Кодирование изображений

**Ollama/OpenAI:**
```
[AIEngineer] DEBUG: OllamaClient encoding image: /path/to/image.jpg
[AIEngineer] DEBUG: OllamaClient image encoded successfully, size: 1398101 chars
```

### 4. HTTP-запросы

**Ollama:**
```
[AIEngineer] DEBUG: OllamaClient sending POST request to http://localhost:11434/api/generate
[AIEngineer] DEBUG: OllamaClient received response: 250 chars
```

**OpenAI:**
```
[AIEngineer] DEBUG: OpenAIClient adding image to messages: /path/to/image.jpg
[AIEngineer] DEBUG: OpenAIClient image mime_type: image/jpeg
[AIEngineer] DEBUG: OpenAIClient sending POST request to https://api.openai.com/v1/chat/completions
[AIEngineer] DEBUG: OpenAIClient received response: 350 chars
```

**Gemini:**
```
[AIEngineer] DEBUG: GeminiClient: calling model.generate_content()
[AIEngineer] DEBUG: GeminiClient: response received from model
[AIEngineer] DEBUG: GeminiClient: response text extracted, length: 150 chars
```

### 5. Ошибки

**Файл не найден:**
```
[AIEngineer] ERROR: Image file not found: /path/to/missing.jpg
```

**Ошибка API:**
```
[AIEngineer] ERROR: OpenAI API key not set
[AIEngineer] ERROR: OllamaClient request failed: Connection refused
[AIEngineer] ERROR: Gemini request failed: 429 Resource has been exhausted
[AIEngineer] DEBUG: GeminiClient: exception type: ResourceExhausted
```

**Пустой ответ:**
```
[AIEngineer] ERROR: Empty response from Gemini
[AIEngineer] DEBUG: GeminiClient: response object: <google.generativeai.types.GenerateContentResponse>
```

---

## Отладка по компонентам

### AIClient

**Проблема:** Неправильный провайдер

**Что проверить в логах:**
```
[AIEngineer] DEBUG: AIClient settings loaded:
[AIEngineer] DEBUG:   provider: gemini  ← Проверьте это значение
```

**Решение:**
```python
from PySide import QtCore
settings = QtCore.QSettings('FreeCAD', 'AIEngineer')
settings.setValue('provider', 'ollama')  # или 'openai', 'gemini'
```

### OllamaClient

**Проблема:** Сервер не доступен

**Лог ошибки:**
```
[AIEngineer] DEBUG: OllamaClient sending POST request to http://localhost:11434/api/generate
[AIEngineer] ERROR: OllamaClient request failed: Connection refused
```

**Решение:**
```bash
# Запустите сервер Ollama
ollama serve

# Проверьте доступность
curl http://localhost:11434/api/tags
```

**Проблема:** Модель не найдена

**Лог ошибки:**
```
[AIEngineer] ERROR: OllamaClient request failed: model 'llava:latest' not found
```

**Решение:**
```bash
# Загрузите модель
ollama pull llava:latest

# Список установленных моделей
ollama list
```

### OpenAIClient

**Проблема:** Неправильный API-ключ

**Лог ошибки:**
```
[AIEngineer] DEBUG: OpenAIClient initialized: model=gpt-4o, api_key_length=0
[AIEngineer] ERROR: OpenAI API key not set
```

**Решение:**
```python
from PySide import QtCore
settings = QtCore.QSettings('FreeCAD', 'AIEngineer')
settings.setValue('api_key', 'sk-...')
```

**Проблема:** Ошибка 401 Unauthorized

**Лог ошибки:**
```
[AIEngineer] ERROR: OpenAIClient request failed: 401 Unauthorized
```

**Решение:**
- Проверьте правильность API-ключа
- Убедитесь, что ключ активен на [platform.openai.com](https://platform.openai.com/api-keys)

### GeminiClient

**Проблема:** Библиотека не установлена

**Лог ошибки:**
```
[AIEngineer] ERROR: Failed to initialize Gemini: No module named 'google.generativeai'
```

**Решение:**
```python
import subprocess, sys
subprocess.run([sys.executable, '-m', 'pip', 'install', 'google-generativeai'])
```

**Проблема:** Изображение не найдено

**Лог:**
```
[AIEngineer] DEBUG: GeminiClient: checking image path existence: /path/to/image.jpg
[AIEngineer] ERROR: Image file not found: /path/to/image.jpg
```

**Решение:**
- Проверьте путь к файлу
- Убедитесь, что файл существует

**Проблема:** Превышен лимит токенов

**Лог ошибки:**
```
[AIEngineer] DEBUG: GeminiClient: calling model.generate_content()
[AIEngineer] ERROR: Gemini request failed: 400 Request contains an invalid argument
```

**Решение:**
- Сократите промпт
- Уменьшите размер изображения
- Разбейте запрос на части

**Проблема:** Превышена квота

**Лог ошибки:**
```
[AIEngineer] ERROR: Gemini request failed: 429 Resource has been exhausted
[AIEngineer] DEBUG: GeminiClient: exception type: ResourceExhausted
```

**Решение:**
- Подождите 1 минуту (бесплатный лимит: 60 запросов/минуту)
- Обновите тарифный план на [aistudio.google.com](https://aistudio.google.com)

---

## Типичные проблемы

### Проблема 1: "Permission denied: '.'"

**Полный лог:**
```
[AIEngineer] DEBUG: GeminiClient.ask called: prompt_length=25, image_path=None
[AIEngineer] ERROR: j_loads error: [Errno 13] Permission denied: '.'
[Gemini] ERROR: Файл истории . пуст или содержит некорректные данные
```

**Причина:**
- Попытка чтения текущей директории вместо файла
- Неправильное формирование пути к файлу истории

**Решение:**
Проверьте код формирования пути:
```python
# ❌ Неправильно
history_path = Path('.')

# ✅ Правильно
history_path = Path.home() / '.FreeCAD' / 'AIEngineer' / 'data' / 'chats'
history_path.mkdir(parents=True, exist_ok=True)
```

### Проблема 2: Пустая директория data

**Лог:**
```
[AIEngineer] DEBUG: AIClient initializing
[AIEngineer] INFO: Data directory is empty
```

**Причина:**
- Директория не создаётся автоматически
- Нет прав на создание директории

**Решение:**
```python
from pathlib import Path

data_dir = Path.home() / '.FreeCAD' / 'AIEngineer' / 'data'

# Проверка существования
if not data_dir.exists():
    print(f"Creating data directory: {data_dir}")
    data_dir.mkdir(parents=True, exist_ok=True)
else:
    print(f"Data directory exists: {data_dir}")
    print(f"Files: {list(data_dir.glob('*'))}")
```

### Проблема 3: API-ключ не сохраняется

**Лог:**
```
[AIEngineer] DEBUG: AIClient settings loaded:
[AIEngineer] DEBUG:   api_key_length: 0
```

**Причина:**
- Ключ не был сохранён в QSettings
- Неправильное имя организации/приложения

**Решение:**
```python
from PySide import QtCore

# Проверка текущих настроек
settings = QtCore.QSettings('FreeCAD', 'AIEngineer')
print(f"Provider: {settings.value('provider')}")
print(f"API key length: {len(settings.value('api_key', ''))}")

# Сохранение ключа
settings.setValue('api_key', 'your-api-key-here')
settings.sync()

# Проверка после сохранения
print(f"Saved API key length: {len(settings.value('api_key', ''))}")
```

### Проблема 4: Изображение не кодируется

**Лог:**
```
[AIEngineer] DEBUG: OllamaClient encoding image: /path/to/image.jpg
[AIEngineer] ERROR: OllamaClient failed to encode image: [Errno 2] No such file or directory
```

**Причина:**
- Файл не существует
- Неправильный путь (относительный vs абсолютный)

**Решение:**
```python
from pathlib import Path

# Проверка файла
image_path = Path('/path/to/image.jpg')
print(f"Exists: {image_path.exists()}")
print(f"Is file: {image_path.is_file()}")
print(f"Size: {image_path.stat().st_size if image_path.exists() else 'N/A'}")
print(f"Absolute path: {image_path.absolute()}")
```

---

## Примеры логов

### Успешный запрос (только текст)

```
[AIEngineer] DEBUG: AIClient initializing
[AIEngineer] DEBUG: AIClient settings loaded:
[AIEngineer] DEBUG:   provider: gemini
[AIEngineer] DEBUG:   model: gemini-2.5-flash
[AIEngineer] DEBUG:   api_key_length: 39
[AIEngineer] DEBUG:   base_url: http://localhost:11434
[AIEngineer] DEBUG: AIClient.ask called: provider=gemini, prompt_length=25, image_path=None
[AIEngineer] DEBUG: AIClient: creating GeminiClient
[AIEngineer] DEBUG: GeminiClient initializing: model_name=gemini-2.5-flash, api_key_length=39
[AIEngineer] DEBUG: GeminiClient: google.generativeai imported successfully
[AIEngineer] DEBUG: GeminiClient: API key configured
[AIEngineer] INFO: Gemini model 'gemini-2.5-flash' initialized
[AIEngineer] DEBUG: GeminiClient initialization complete
[AIEngineer] DEBUG: GeminiClient.ask called: prompt_length=25, image_path=None
[AIEngineer] DEBUG: GeminiClient: prompt added to content
[AIEngineer] DEBUG: GeminiClient: content list prepared, items count: 1
[AIEngineer] DEBUG: GeminiClient: calling model.generate_content()
[AIEngineer] DEBUG: GeminiClient: response received from model
[AIEngineer] DEBUG: GeminiClient: response text extracted, length: 150 chars
[AIEngineer] DEBUG: AIClient: received response from Gemini, length: 150 chars
```

### Успешный запрос (текст + изображение)

```
[AIEngineer] DEBUG: AIClient.ask called: provider=gemini, prompt_length=50, image_path=/home/user/drawing.jpg
[AIEngineer] DEBUG: AIClient: creating GeminiClient
[AIEngineer] DEBUG: GeminiClient initializing: model_name=gemini-2.5-flash, api_key_length=39
[AIEngineer] DEBUG: GeminiClient: google.generativeai imported successfully
[AIEngineer] DEBUG: GeminiClient: API key configured
[AIEngineer] INFO: Gemini model 'gemini-2.5-flash' initialized
[AIEngineer] DEBUG: GeminiClient initialization complete
[AIEngineer] DEBUG: GeminiClient.ask called: prompt_length=50, image_path=/home/user/drawing.jpg
[AIEngineer] DEBUG: GeminiClient: prompt added to content
[AIEngineer] DEBUG: GeminiClient: checking image path existence: /home/user/drawing.jpg
[AIEngineer] DEBUG: GeminiClient: image file exists, size: 2097152 bytes
[AIEngineer] INFO: Image path added to Gemini request: /home/user/drawing.jpg
[AIEngineer] DEBUG: GeminiClient: content list prepared, items count: 2
[AIEngineer] DEBUG: GeminiClient: calling model.generate_content()
[AIEngineer] DEBUG: GeminiClient: response received from model
[AIEngineer] DEBUG: GeminiClient: response text extracted, length: 350 chars
[AIEngineer] DEBUG: AIClient: received response from Gemini, length: 350 chars
```

### Ошибка: файл не найден

```
[AIEngineer] DEBUG: GeminiClient.ask called: prompt_length=30, image_path=/missing/file.jpg
[AIEngineer] DEBUG: GeminiClient: prompt added to content
[AIEngineer] DEBUG: GeminiClient: checking image path existence: /missing/file.jpg
[AIEngineer] ERROR: Image file not found: /missing/file.jpg
[AIEngineer] DEBUG: GeminiClient: content list prepared, items count: 1
[AIEngineer] DEBUG: GeminiClient: calling model.generate_content()
[AIEngineer] DEBUG: GeminiClient: response received from model
[AIEngineer] DEBUG: GeminiClient: response text extracted, length: 100 chars
```

### Ошибка: API-ключ не задан

```
[AIEngineer] DEBUG: AIClient.ask called: provider=openai, prompt_length=20, image_path=None
[AIEngineer] DEBUG: AIClient: creating OpenAIClient
[AIEngineer] DEBUG: OpenAIClient initialized: model=gpt-4o, api_key_length=0
[AIEngineer] DEBUG: OpenAIClient.ask called: prompt_length=20, image_path=None
[AIEngineer] ERROR: OpenAI API key not set
```

### Ошибка: сервер недоступен

```
[AIEngineer] DEBUG: AIClient.ask called: provider=ollama, prompt_length=15, image_path=None
[AIEngineer] DEBUG: AIClient: creating OllamaClient
[AIEngineer] DEBUG: OllamaClient initialized: model=llava:latest, base_url=http://localhost:11434
[AIEngineer] DEBUG: OllamaClient.ask called: prompt_length=15, image_path=None
[AIEngineer] DEBUG: OllamaClient sending POST request to http://localhost:11434/api/generate
[AIEngineer] ERROR: OllamaClient request failed: ('Connection aborted.', ConnectionRefusedError(111, 'Connection refused'))
```

---

## Сохранение логов в файл

Для анализа логов можно перенаправить вывод в файл:

### Через Python Console FreeCAD

```python
import sys
from pathlib import Path

# Создание файла лога
log_file = Path.home() / 'AIEngineer_debug.log'

class LogTee:
    def __init__(self, *files):
        self.files = files
    
    def write(self, data):
        for f in self.files:
            f.write(data)
    
    def flush(self):
        for f in self.files:
            f.flush()

# Перенаправление stdout
log_handle = open(log_file, 'a', encoding='utf-8')
sys.stdout = LogTee(sys.__stdout__, log_handle)

print(f"Logging to: {log_file}")

# Теперь все логи будут дублироваться в файл
# Для остановки:
# sys.stdout = sys.__stdout__
# log_handle.close()
```

---

## Фильтрация логов

### Только AIEngineer логи

```python
# Открыть файл лога и найти все строки с [AIEngineer]
from pathlib import Path

log_file = Path.home() / 'AIEngineer_debug.log'

if log_file.exists():
    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            if '[AIEngineer]' in line:
                print(line.strip())
```

### Только ошибки

```python
if log_file.exists():
    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            if 'ERROR' in line:
                print(line.strip())
```

### Только DEBUG для GeminiClient

```python
if log_file.exists():
    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            if 'GeminiClient' in line and 'DEBUG' in line:
                print(line.strip())
```

---

## Поддержка

**GitHub Issues:** [github.com/hypo69/AIEngineer/issues](https://github.com/hypo69/AIEngineer/issues)

При создании issue приложите:
1. Полный лог из Report View
2. Версию FreeCAD
3. Версию Python
4. Версии библиотек:
   ```python
   import google.generativeai
   print(f"google-generativeai: {google.generativeai.__version__}")
   ```

---

**Версия документа:** 1.0  
**Дата:** 2025-01-07  
**Применимо к:** AIEngineer v0.2.0+