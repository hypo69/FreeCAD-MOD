# Миграция на хранение API-ключа в .env

## 📋 Обзор изменений

Начиная с версии **0.2.0**, AIEngineer использует файл `.env` для хранения API-ключа Google Gemini вместо системного хранилища QSettings.

### Преимущества новой системы:

✅ **Безопасность**: Ключ хранится в отдельном файле, который можно исключить из системы контроля версий  
✅ **Переносимость**: Легко переносить настройки между машинами  
✅ **Стандартность**: Следует общепринятым практикам хранения секретов  
✅ **Прозрачность**: Ключ можно редактировать вручную в текстовом редакторе

---

## 🔄 Автоматическая миграция

При первом открытии **AI Settings** после обновления:

1. Ваш существующий ключ из QSettings будет **автоматически обнаружен**
2. В диалоге появится сообщение: *"⚠ Key loaded from QSettings (will be migrated to .env)"*
3. Нажмите **OK** — ключ сохранится в `.env` файл
4. При следующем открытии вы увидите: *"✓ Key loaded from .env file"*

**Никаких действий от вас не требуется!**

---

## 📁 Расположение файла .env

**Windows:**
```
%APPDATA%\FreeCAD\AIEngineer\.env
```
Полный путь:
```
C:\Users\<YourName>\AppData\Roaming\FreeCAD\AIEngineer\.env
```

**Linux:**
```
~/.FreeCAD/AIEngineer/.env
```

**macOS:**
```
~/.FreeCAD/AIEngineer/.env
```

---

## 📄 Формат файла .env

Файл автоматически создаётся с таким содержимым:

```env
# AIEngineer Configuration
# Generated: 2025-01-06 14:30:22

GEMINI_API_KEY=your-api-key-here
```

### Редактирование вручную

Вы можете открыть файл любым текстовым редактором и изменить ключ:

```env
# Однострочные значения
GEMINI_API_KEY=AIzaSyC...

# Значения с пробелами (используйте кавычки)
GEMINI_API_KEY="AIza SyC..."

# Комментарии начинаются с #
# MODEL_NAME=gemini-1.5-flash
```

**После редактирования перезапустите FreeCAD!**

---

## 🔍 Проверка работы

### Способ 1: Через интерфейс

1. Откройте **AI Settings** (⚙️)
2. Проверьте текст под полем ввода:
   - ✓ **Зелёный текст** = ключ загружен из `.env`
   - ⚠ **Жёлтый текст** = ключ из QSettings, нужна миграция
   - ✗ **Красный текст** = ключ не найден

### Способ 2: Через консоль FreeCAD

Откройте **View → Panels → Python console** и выполните:

```python
from AIEngineer.utils import get_api_key
key = get_api_key()
print(f"API Key: {key[:10]}..." if key else "No key found")
```

Вы должны увидеть:
```
[AIEngineer] API key loaded from .env
API Key: AIzaSyC...
```

---

## 🛠️ Ручная миграция (при необходимости)

Если автоматическая миграция не сработала:

### Шаг 1: Найдите старый ключ

**Windows (через реестр):**
```
HKEY_CURRENT_USER\Software\FreeCAD\AIEngineer
```
Ключ: `api_key`

**Linux/macOS:**
```bash
grep -r "api_key" ~/.config/FreeCAD/
```

### Шаг 2: Создайте .env файл

**Windows:**
```batch
cd %APPDATA%\FreeCAD\AIEngineer
echo GEMINI_API_KEY=YOUR_KEY_HERE > .env
```

**Linux/macOS:**
```bash
cd ~/.FreeCAD/AIEngineer
echo "GEMINI_API_KEY=YOUR_KEY_HERE" > .env
```

### Шаг 3: Проверьте

Откройте FreeCAD и выполните команду **Ask AI** с любым связанным контентом.

---

## 🔐 Безопасность

### Рекомендации:

1. **Не публикуйте файл .env в GitHub/GitLab**
   Добавьте в `.gitignore`:
   ```
   .env
   *.env
   ```

2. **Установите права доступа (Linux/macOS)**
   ```bash
   chmod 600 ~/.FreeCAD/AIEngineer/.env
   ```

3. **Регулярно ротируйте ключи**
   - Создайте новый ключ на [aistudio.google.com](https://aistudio.google.com/app/apikey)
   - Обновите `.env` файл
   - Удалите старый ключ из Google Console

4. **Резервное копирование**
   Включите `.env` в экспорт проекта (**Export Project**), но храните архив в безопасном месте.

---

## ❓ Часто задаваемые вопросы

### Q: Можно ли продолжать использовать QSettings?

**A:** Да, система обратно совместима. Если `.env` файл не найден, ключ будет загружен из QSettings. Однако рекомендуется мигрировать для улучшения безопасности.

### Q: Что произойдёт, если удалить .env файл?

**A:** AIEngineer автоматически переключится на QSettings (если ключ там сохранён). При следующем сохранении через **AI Settings** `.env` файл будет создан заново.

### Q: Можно ли хранить несколько ключей?

**A:** В текущей версии поддерживается только один ключ. Для использования разных ключей переключайте их вручную в `.env` файле.

### Q: Как экспортировать настройки на другой компьютер?

**A:** Используйте **Export Project** — файл `.env` будет включён в ZIP-архив. Распакуйте архив в стандартное расположение на новой машине.

---

## 🐛 Решение проблем

### Проблема: "API key not found" после обновления

**Решение:**
1. Откройте **AI Settings**
2. Введите ключ заново
3. Нажмите **OK**

### Проблема: Ключ не сохраняется в .env

**Проверьте:**
- Есть ли права на запись в директорию `%APPDATA%\FreeCAD\AIEngineer\`?
- Не заблокирован ли файл антивирусом?
- Проверьте консоль FreeCAD (View → Report view) на наличие ошибок

**Ручное решение:**
```python
# В консоли FreeCAD:
from AIEngineer.utils import save_to_env
save_to_env('GEMINI_API_KEY', 'YOUR_KEY_HERE')
```

### Проблема: После миграции Ask AI не работает

**Проверка:**
```python
# В консоли FreeCAD:
from AIEngineer.utils import load_env
env = load_env()
print(env)
```

Если словарь пустой `{}`, файл `.env` повреждён. Пересоздайте его:
```python
from AIEngineer.utils import save_to_env
save_to_env('GEMINI_API_KEY', 'YOUR_ACTUAL_KEY')
```

---

## 📚 Дополнительная информация

- **Документация Google Gemini API**: [ai.google.dev/docs](https://ai.google.dev/docs)
- **Получение API-ключа**: [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
- **GitHub Issues**: [github.com/hypo69/AIEngineer/issues](https://github.com/hypo69/AIEngineer/issues)

---

**Версия документа:** 1.0  
**Дата:** 2025-01-07  
**Применимо к:** AIEngineer v0.2.0+