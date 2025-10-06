# Changelog - Интеграция Gemini v0.2.0

## 📅 2025-01-07

### ✨ Новые функции

#### 1. Полнофункциональный класс GoogleGenerativeAi
- **Файл:** `AIEngineer/gemini.py` (ПОЛНОСТЬЮ ПЕРЕПИСАН)
- Интегрирован класс из проекта hypotez
- Поддержка RAG (Retrieval-Augmented Generation)
- История чатов с автосохранением
- Асинхронные методы: `chat()`, `ask_async()`, `upload_file()`
- Системные инструкции для настройки поведения модели
- Улучшенная обработка ошибок с автоматическими ретраями

#### 2. Хранение API-ключа в .env
- **Файл:** `AIEngineer/utils.py` (ОБНОВЛЁН)
- Добавлены функции: `load_env()`, `save_to_env()`, `get_api_key()`
- Приоритет: `.env` → `QSettings` → параметр конструктора
- Автоматическая миграция из QSettings

#### 3. Обновлённый диалог настроек
- **Файл:** `AIEngineer/settings_dialog.py` (ОБНОВЛЁН)
- Автоматическое сохранение в .env
- Индикатор источника ключа (`.env` / `QSettings`)
- Дублирование в QSettings для обратной совместимости

#### 4. Улучшенная команда Ask AI
- **Файл:** `AIEngineer/commands/ask_ai.py` (ОБНОВЛЁН)
- Использует `describe_image()` вместо базового `ask()`
- Поддержка системных инструкций
- Обработка ошибок конфигурации с подсказками пользователю

#### 5. Расширенная инициализация
- **Файл:** `AIEngineer/InitGui.py` (ОБНОВЛЁН)
- Проверка наличия `.env` файла при загрузке
- Проверка настройки API-ключа
- Понятные инструкции в консоли при проблемах

---

## 📝 Изменённые файлы

### Критические изменения (требуют замены):

```
AIEngineer/gemini.py              ← ПОЛНОСТЬЮ ПЕРЕПИСАН
```

### Важные обновления (требуют замены):

```
AIEngineer/utils.py               ← Добавлены функции .env
AIEngineer/settings_dialog.py     ← Поддержка .env
AIEngineer/commands/ask_ai.py     ← Использует describe_image()
AIEngineer/InitGui.py             ← Проверка конфигурации
```

### Новые файлы:

```
AIEngineer/.env.example           ← Шаблон конфигурации
MIGRATION.md                      ← Руководство по миграции
INTEGRATION_GUIDE.md              ← Полная документация
QUICKSTART.md                     ← Быстрый старт
CHANGELOG.md                      ← Этот файл
```

---

## 🔄 Миграция с v0.1.0

### Автоматическая миграция (рекомендуется):

1. Замените файлы из списка выше
2. Откройте FreeCAD
3. Выберите рабочую среду **AI Engineer**
4. Откройте **AI Settings** (⚙️)
5. Нажмите **OK** (ключ автоматически мигрирует в .env)

### Ручная миграция:

1. Найдите текущий ключ в QSettings:
   - Windows: `HKEY_CURRENT_USER\Software\FreeCAD\AIEngineer`
   - Linux/macOS: `~/.config/FreeCAD/AIEngineer.conf`

2. Создайте `.env` файл:
   ```bash
   # Windows
   cd %APPDATA%\FreeCAD\AIEngineer
   echo GEMINI_API_KEY=ваш-ключ > .env
   
   # Linux/macOS
   cd ~/.FreeCAD/AIEngineer
   echo "GEMINI_API_KEY=ваш-ключ" > .env
   chmod 600 .env
   ```

---

## 🆕 Новые методы API

### GoogleGenerativeAi

#### `chat(q, chat_session_name, context)`
```python
response = await llm.chat('Привет!', chat_session_name='my_chat')
```

#### `ask_async(q, attempts, save_dialogue, clean_response, context)`
```python
response = await llm.ask_async('Вопрос', context=['Контекст'])
```

#### `describe_image(image, mime_type, prompt)`
```python
description = llm.describe_image(Path('image.jpg'), prompt='Опиши')
```

#### `start_new_chat_session(new_system_instruction, initial_history)`
```python
llm.start_new_chat_session(new_system_instruction='Ты - эксперт')
```

#### `clear_history()`
```python
llm.clear_history()
```

#### `upload_file(file, file_name)`
```python
uploaded = await llm.upload_file('document.pdf')
```

---

## 🔧 Изменения в существующих методах

### `ask()` - теперь с RAG

**Было:**
```python
response = llm.ask(q='Вопрос', image_path='/path/to/image.jpg')
```

**Стало:**
```python
# Для текста с контекстом
response = llm.ask('Вопрос', context=['Контекст1', 'Контекст2'])

# Для изображений используйте describe_image()
response = llm.describe_image(Path('image.jpg'), prompt='Вопрос')
```

### `__init__()` - новые параметры

**Было:**
```python
llm = GoogleGenerativeAi(
    api_key='key',
    model_name='gemini-1.5-flash'
)
```

**Стало:**
```python
llm = GoogleGenerativeAi(
    api_key='key',  # Опционально - загрузится из .env
    model_name='gemini-1.5-flash',
    generation_config={'response_mime_type': 'text/plain'},
    system_instruction='Опциональная инструкция'
)
```

---

## 🐛 Исправленные ошибки

### v0.1.0 → v0.2.0

1. **API-ключ терялся при перезапуске FreeCAD**
   - Решение: Хранение в `.env` файле

2. **Нет обработки превышения лимита токенов**
   - Решение: Автоматический перезапуск чата при `InvalidArgument`

3. **Невозможно передать контекст для RAG**
   - Решение: Параметр `context` во всех методах запросов

4. **Отсутствие истории диалогов**
   - Решение: Метод `chat()` с автосохранением

5. **Плохая обработка сетевых ошибок**
   - Решение: Умные ретраи с экспоненциальной задержкой

6. **Нет поддержки больших изображений**
   - Решение: Использование File API через `describe_image()`

---

## ⚠️ Устаревшие функции

### Deprecated (но работают):

#### `ask(q, image_path=...)`
```python
# DEPRECATED
response = llm.ask(q='Вопрос', image_path='/path/image.jpg')

# ИСПОЛЬЗУЙТЕ
response = llm.describe_image(Path('image.jpg'), prompt='Вопрос')
```

---

## 📊 Статистика изменений

```
Файлов изменено: 5
Файлов создано: 5
Строк добавлено: ~1500
Строк удалено: ~200
Новых методов: 6
Deprecated методов: 0 (старые работают)
```

---

## 🔮 Планируемые изменения

### v0.3.0 (Q2 2025):
- [ ] GUI для просмотра истории чатов
- [ ] Поддержка Claude API
- [ ] Векторный поиск для RAG
- [ ] Экспорт диалогов в PDF

### v0.4.0 (Q3 2025):
- [ ] Мультимодальный анализ
- [ ] Генерация G-code
- [ ] Интеграция с CAM
- [ ] Облачная синхронизация

---

## 📚 Документация

- **QUICKSTART.md** - быстрый старт (5 минут)
- **MIGRATION.md** - руководство по миграции на .env
- **INTEGRATION_GUIDE.md** - полная документация API

---

## 🙏 Благодарности

- Проект **hypotez** - за базовый класс GoogleGenerativeAi
- Сообщество **FreeCAD** - за фидбек и тестирование
- **Google** - за бесплатный tier Gemini API

---

**Версия:** 0.2.0  
**Дата:** 2025-01-07  
**Авторы:** hypo69

---

## 📞 Поддержка

**GitHub:** [github.com/hypo69/AIEngineer](https://github.com/hypo69/AIEngineer)  
**Issues:** [github.com/hypo69/AIEngineer/issues](https://github.com/hypo69/AIEngineer/issues)  
**Telegram:** @aiengineer_freecad