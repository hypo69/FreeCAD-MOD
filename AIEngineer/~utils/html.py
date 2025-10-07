## \file /src/utils/html.py
# -*- coding: utf-8 -*-
#! .pyenv/bin/python3

"""
Модуль для нормализации и очистки HTML-строк.
==========================================================

Предоставляет функции для удаления нежелательных тегов (скрипты, стили),
комментариев и нормализации пробельных символов в HTML-коде.
 **Функция `clean_html_string`:**
    *   Принимает HTML-строку и опционально имя парсера (`html.parser`, `html5lib`, `lxml`).
    *   Добавлена проверка на пустой или нестроковый ввод.
    *   Включен блок `try...except` для обработки ошибок парсинга и логирования их с помощью `logger.error`.
    *   Список `tags_to_remove` расширен типичными контейнерами навигации, форм, футеров и т.д.
    *   Нормализация пробелов теперь использует флаг `re.UNICODE` для корректной работы с разными пробельными символами Unicode.
    *   Удаление тегов `<body>` сделано более надежным с использованием `re.sub` и флагов `re.IGNORECASE` (регистронезависимость) и `re.DOTALL` (чтобы `[^>]*` соответствовал и переносам строк внутри тега body). `count=1` гарантирует удаление только первого вхождения `<body>`.
    *   Функция возвращает пустую строку `""` в случае ошибки или невалидного ввода.
```rst
.. module:: src.utils.html
```

"""

import re
from bs4 import BeautifulSoup, Comment
import logging # Добавим логирование для ошибок

# Настройка базового логирования (можно настроить более детально в основном приложении)
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clean_html_string(html_content: str, parser: str = 'html.parser') -> str:
    """
    Очищает строку HTML: удаляет скрипты, стили, комментарии
    и нормализует пробельные символы.

    Args:
        html_content (str): Входная строка с HTML.
        parser (str): Парсер для BeautifulSoup ('html.parser', 'html5lib', 'lxml').
                      'html.parser' - встроенный, быстрый, менее надежный.
                      'html5lib' - надежный, медленнее, требует установки.
                      'lxml' - быстрый, надежный, требует установки C-библиотек.

    Returns:
        str: Очищенная строка HTML или пустая строка в случае ошибки.
    """
    if not html_content or not isinstance(html_content, str):
        logger.debug("Получено пустое или нестроковое содержимое для очистки.")
        return ""

    try:
        # 1. Парсинг с помощью BeautifulSoup
        soup = BeautifulSoup(html_content, parser)

        # 2. Удаление ненужных тегов
        tags_to_remove = ['script', 'style', 'head', 'meta', 'link', 'noscript', 'iframe', 'button', 'input', 'textarea', 'select', 'option', 'form', 'nav', 'footer', 'header', 'aside']
        for tag in soup.find_all(tags_to_remove):
            tag.decompose()

        # 3. Удаление комментариев
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()

        # 4. Получаем "основное" содержимое (обычно внутри body, но если его нет, берем все)
        target_node = soup.body if soup.body else soup
        if not target_node:
            logger.debug("Не удалось найти корневой узел (body или soup) после парсинга.")
            return ""

        # 5. Получаем строку из обработанного дерева
        intermediate_string = str(target_node)

        # 6. Нормализация пробелов с помощью регулярных выражений
        # Заменяем все последовательности пробельных символов (\n, \t, пробел и т.д.) на один пробел
        cleaned_string = re.sub(r'\s+', ' ', intermediate_string, flags=re.UNICODE).strip()

        # Удаляем пробелы между тегами (например, "> <" на "><") - опционально
        cleaned_string = re.sub(r'>\s+<', '><', cleaned_string, flags=re.UNICODE)

        # Удаляем теги <body> и </body> если они остались по краям
        # Используется регистронезависимый поиск и учитываем возможные атрибуты
        cleaned_string = re.sub(r'^<body[^>]*>', '', cleaned_string, count=1, flags=re.IGNORECASE | re.DOTALL).lstrip()
        cleaned_string = re.sub(r'</body\s*>$', '', cleaned_string, count=1, flags=re.IGNORECASE).rstrip()


        return cleaned_string

    except Exception as e:
        logger.error(f"Ошибка при очистке HTML: {e}", exc_info=True) # Логируем ошибку с traceback
        # В случае ошибки можно вернуть исходную строку или пустую
        return "" # Возврат пустую строку при ошибке


# --- Блок для демонстрации и тестирования ---
if __name__ == "__main__":
    # Пример HTML для тестирования
    html_string_example = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Page</title>
        <meta charset="utf-8">
        <script>alert('remove me');</script>
        <style>.hide { display: none; }</style>
        <link rel="stylesheet" href="style.css">
    </head>
    <Body class="page">
        <!-- Это комментарий -->
        <header><h1>Лого</h1><nav>Меню</nav></header>
        <div>
            <p>Это первый   параграф.
            Содержит \t табы и \n переносы.</p>
            <p>Второй параграф.</p>
            <noscript>Включите JavaScript!</noscript>
        </div>
        <form action="#"><button>Кнопка</button></form>
        <footer>Контакты</footer>
        <script src="extra.js"></script>
    </BODY>
    </html>
    """

    print("--- Исходный HTML ---")
    print(html_string_example)

    print("\n--- Очищенный HTML (html.parser) ---")
    cleaned_html_parser = clean_html_string(html_string_example, parser='html.parser')
    print(cleaned_html_parser)

    # Пример использования с html5lib (требует pip install html5lib)
    try:
        print("\n--- Очищенный HTML (html5lib) ---")
        # Попытка импорта, чтобы проверить доступность
        import html5lib
        cleaned_html_html5lib = clean_html_string(html_string_example, parser='html5lib')
        print(cleaned_html_html5lib)
    except ImportError:
        print("Библиотека html5lib не установлена. Пропустите этот тест.")
    except Exception as e:
         print(f"Ошибка при использовании html5lib: {e}")

    # Пример с пустым вводом
    print("\n--- Пустой ввод ---")
    print(f"Результат: '{clean_html_string('')}'")

    # Пример с невалидным HTML
    invalid_html = "<div><p>Не закрыт</div>"
    print("\n--- Невалидный HTML ---")
    print(f"Результат: '{clean_html_string(invalid_html)}'")
