# AIEngineer для FreeCAD

**AIEngineer** — это рабочая среда (Workbench) для FreeCAD, которая интегрирует возможности Google Gemini AI для анализа изображений, генерации технических описаний и создания 3D-моделей на основе текстовых промптов.

## 🎯 Основные возможности

- **Загрузка изображений** — импорт технических чертежей, фотографий деталей и эскизов
- **Создание текстовых промптов** — описание требований к модели в формате Markdown
- **Связывание контента** — привязка изображений к текстовым описаниям
- **AI-анализ** — отправка связанных данных в Google Gemini для получения технических рекомендаций
- **Генерация 3D** — создание простых геометрических объектов (параллелепипеды) на основе текстовых описаний
- **Управление проектом** — просмотр, редактирование и удаление загруженных файлов
- **Экспорт проекта** — сохранение всех данных в ZIP-архив

## 📋 Требования

### Обязательные зависимости
- **FreeCAD** 0.21 или выше
- **Python** 3.10+
- **Google Gemini API ключ** (бесплатно: [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey))

### Python-библиотеки
Установите через консоль FreeCAD Python:

```python
import subprocess
import sys
subprocess.run([sys.executable, '-m', 'pip', 'install', 
                'grpcio', 'protobuf', 'google-generativeai'])
```

## 🚀 Установка

### Способ 1: Через FreeCAD Addon Manager (рекомендуется)

1. Откройте FreeCAD
2. Перейдите в меню **Tools → Addon Manager**
3. Нажмите **Install from URL**
4. Введите: `https://github.com/hypo69/AIEngineer`
5. Нажмите **OK** и дождитесь завершения установки
6. Перезапустите FreeCAD

### Способ 2: Ручная установка

**Windows:**
```bash
git clone https://github.com/hypo69/AIEngineer.git
xcopy /E /I AIEngineer "%APPDATA%\FreeCAD\Mod\AIEngineer"
```

**Linux/macOS:**
```bash
git clone https://github.com/hypo69/AIEngineer.git
cp -r AIEngineer ~/.FreeCAD/Mod/
```

После установки перезапустите FreeCAD.

## ⚙️ Настройка

1. Запустите FreeCAD
2. Выберите рабочую среду **AI Engineer** в выпадающем меню
3. Нажмите на иконку **AI Settings** (шестерёнка)
4. Введите ваш API-ключ Google Gemini
5. Нажмите **OK**

## 📚 Быстрый старт

### Пример: Анализ чертежа детали

1. **Загрузите изображение:**
   - Нажмите **Load Image**
   - Выберите файл чертежа (PNG/JPG)

2. **Создайте текстовое описание:**
   - Нажмите **Load Text**
   - Введите промпт, например:
     ```
     Проанализируй чертёж и определи:
     - Тип детали
     - Основные размеры
     - Материал (если указан)
     - Рекомендации по изготовлению
     ```
   - Нажмите **Save**

3. **Свяжите данные:**
   - Нажмите **Link Content**
   - Выберите изображение слева и текст справа
   - Нажмите **→ Link Selected**

4. **Получите ответ от AI:**
   - Нажмите **Ask AI**
   - Дождитесь ответа от Gemini
   - Скопируйте результат при необходимости

### Пример: Создание 3D-модели по описанию

1. Нажмите **Generate 3D from AI**
2. Введите описание, например: `Параллелепипед 100x50x30 мм`
3. Нажмите **OK**
4. Модель будет создана в активном документе

## 🛠️ Структура проекта

```
AIEngineer/
├── InitGui.py              # Инициализация рабочей среды
├── ai_engineer_workbench.py # Основной класс Workbench
├── gemini.py               # Клиент Google Gemini API
├── project_manager.py      # Управление связями файлов
├── settings_dialog.py      # Диалог настроек
├── utils.py                # Вспомогательные функции
├── commands/               # Команды панели инструментов
│   ├── load_image.py
│   ├── load_text.py
│   ├── link_content.py
│   ├── ask_ai.py
│   ├── generate_3d.py
│   └── ...
├── dialogs/                # Диалоговые окна
│   ├── text_editor.py
│   ├── content_manager.py
│   └── ...
└── Resources/
    └── icons/              # SVG-иконки команд
```

## 🔧 Хранение данных

Все файлы проекта хранятся в:
- **Windows:** `%APPDATA%\FreeCAD\AIEngineer\data\`
- **Linux/macOS:** `~/.FreeCAD/AIEngineer/data/`

Структура:
```
data/
├── project.json         # Связи изображений и текстов
├── *.png, *.jpg        # Загруженные изображения
├── *.md, *.txt         # Текстовые промпты
└── ai_history/         # История запросов к AI
    └── ai_response_*.json
```

## 🐛 Устранение неполадок

### Ошибка: "gRPC not found"
```python
import subprocess, sys
subprocess.run([sys.executable, '-m', 'pip', 'install', 'grpcio'])
```

### Ошибка: "API key not set"
- Откройте **AI Settings**
- Убедитесь, что ключ введён корректно
- Проверьте валидность ключа на [aistudio.google.com](https://aistudio.google.com/app/apikey)

### Ошибка: "Gemini returned empty response"
- Проверьте интернет-соединение
- Убедитесь, что не превышен лимит запросов API (бесплатный план: 60 запросов/минуту)
- Попробуйте упростить промпт

### Модель не создаётся из текста
В текущей версии поддерживаются только параллелепипеды. Пример правильного формата:
```
Box 100 50 30
Параллелепипед 100x50x30
Короб 100 50 30 мм
```

## 📝 Лицензия

MIT License — см. файл [LICENSE](LICENSE)

## 👤 Автор

**hypo69**  
GitHub: [github.com/hypo69](https://github.com/hypo69)

## 🤝 Вклад в проект

Пул-реквесты приветствуются! Для крупных изменений сначала откройте Issue для обсуждения.

## 🔗 Полезные ссылки

- [Google Gemini API Documentation](https://ai.google.dev/docs)
- [FreeCAD Python API](https://wiki.freecad.org/Python)
- [FreeCAD Addon Development](https://wiki.freecad.org/Workbench_creation)

---

**Версия:** 0.1.0  
**Дата:** 2025-10-05