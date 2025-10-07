## \file /src/utils/string/html_simplification.py
# -*- coding: utf-8 -*-
#! .pyenv/bin/python3

"""
Модуль для очистки HTML-тегов из текста и упрощения HTML-кода.
===============================================================
Модуль минимизирует HTML-код, удаляет теги и атрибуты, а также обрабатывает
специальные случаи, такие как скрипты, стили и комментарии.
Основное внимание уделяется содержимому тега <body>.
Позволяет удалять "незначимые" теги-контейнеры, оставляя только теги,
содержащие текст или являющиеся разрешенными пустыми тегами (например, <br>).
Использует BeautifulSoup для надежного парсинга HTML и класс Config
для управления параметрами упрощения.

Зависимости:
    - beautifulsoup4 (pip install beautifulsoup4)
    - lxml (опционально, для более быстрого парсинга: pip install lxml)

 .. module:: src.utils.string.html_simplification
"""

import re
import html
from pathlib import Path
from typing import Optional, Set, Dict, List, Union
from dataclasses import dataclass, field
from bs4 import BeautifulSoup, Comment, NavigableString, Tag


# Оставляем импорты из вашего проекта, если они нужны
import header
from header import __root__
from src import gs
from src.logger import logger

@dataclass
class Config:
    """
    Конфигурация для функции simplify_html.

    Attributes:
        allowed_tags (Set[str]): Множество тегов в нижнем регистре, которые нужно оставить.
            Если `set()` (пустое множество), все теги (кроме удаленных другими опциями) остаются.
            Теги не в этом множестве будут развернуты (unwrap), если `keep_only_significant`=False,
            или потенциально удалены/развернуты если `keep_only_significant`=True.
            Пример: `{'p', 'a', 'br', 'strong', 'em'}`
        allowed_attributes (Dict[str, Set[str]]): Словарь, где ключи - имена тегов (в нижнем регистре),
            а значения - множества разрешенных атрибутов (в нижнем регистре) для этого тега.
            Если `{}` (пустой словарь), все атрибуты удаляются.
            Если атрибут разрешен для тега `'*'`, он разрешен для всех тегов.
            Пример: `{'a': {'href', 'title'}, 'img': {'src', 'alt'}, '*': {'style'}}`
        unwrap_tags (Set[str]): Множество тегов (в нижнем регистре), которые нужно "развернуть"
            (удалить тег, оставив содержимое) на финальном этапе, независимо от других правил.
            Пример: `{'span', 'div'}`
        VOID_TAGS (Set[str]): Множество тегов, считающихся "пустыми" (void elements),
            используется при `keep_only_significant=True`.
        remove_comments (bool): Удалять ли HTML-комментарии (`<!-- ... -->`).
        remove_scripts_styles (bool): Удалять ли теги `<script>` и `<style>` вместе с их содержимым.
        normalize_whitespace (bool): Заменять множественные пробелы на один и удалять пробелы в начале/конце.
        keep_only_significant (bool): Удалять ли теги, не содержащие значимый контент.
        parser (str): Парсер для BeautifulSoup ('html.parser', 'lxml', 'html5lib').
    """
    # Установка значения по умолчанию через default_factory для изменяемых типов
    allowed_tags: Set[str] = field(default_factory=lambda: {'p', 'b', 'a', 'br', 'img', 'h1', 'hr', 'div', 'span', 'table', 'tbody', 'tr', 'td', 'th', 'ul', 'ol', 'li', 'strong', 'em', 'i', 'u'}) # Расширенный набор по умолчанию
    # Изменено: Удалены 'class' и 'id' из стандартно разрешенных для '*'
    allowed_attributes: Dict[str, Set[str]] = field(default_factory=lambda: {'a': {'href', 'title'}, 'img': {'src', 'alt', 'title'}, '*': {'style'}})
    unwrap_tags: Set[str] = field(default_factory=set) # По умолчанию ничего не разворачиваем принудительно
    VOID_TAGS: Set[str] = field(default_factory=lambda: {
        'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
        'link', 'meta', 'param', 'source', 'track', 'wbr'
    })
    remove_comments: bool = True
    remove_scripts_styles: bool = True # Удаляем скрипты и стили по умолчанию
    normalize_whitespace: bool = True
    keep_only_significant: bool = False # По умолчанию не удаляем "незначимые" теги
    parser: str = 'html.parser' # Значение по умолчанию для парсера

# --- Основные функции ---

def strip_tags(html_content: str | None, parser: Optional[str] = None) -> str:
    """
    Полностью удаляет все HTML/XML теги из строки, оставляя только текст.
    Также преобразует HTML-сущности (типа &) в соответствующие символы.
    Фокусируется на содержимом тега <body>, если он присутствует.

    Args:
        html_content (str | None): Строка с HTML-кодом или None.
        parser (Optional[str]): Парсер для BeautifulSoup ('html.parser', 'lxml', 'html5lib').
                                Если None, используется 'html.parser'.

    Returns:
        str: Текст без HTML-тегов. Возвращает пустую строку при ошибке, None или пустом вводе.

    Raises:
        Exception: BeautifulSoup может генерировать исключения при серьезных проблемах парсинга,
                   которые логируются.

    Example:
        >>> html_input = '<html><head><title>T</title></head><body><p>Hello <b>World</b>!</p><!-- comment --></body></html>'
        >>> strip_tags(html_input)
        'Hello World !'
        >>> strip_tags('Текст с <сущностями> & символами')
        'Текст с <сущностями> & символами'
        >>> strip_tags(None)
        ''
    """
    # Проверка входных данных
    if not html_content or not isinstance(html_content, str):
        # Логгер может быть не настроен на уровне warning, Используется debug или info, если нужно видеть это часто
        logger.debug("strip_tags: Входные данные некорректны или пустые.")
        return '' # Возврат пустую строку для некорректного ввода

    # Используется парсер из аргумента или значение по умолчанию
    actual_parser = parser if parser is not None else 'html.parser'

    try:
        # Инициализация BeautifulSoup для всего документа
        original_soup = BeautifulSoup(html_content, actual_parser)

        # Ищем тег body
        body_tag = original_soup.body

        # Если body не найден, обрабатываем весь контент как тело
        target_node = body_tag if body_tag else original_soup

        # Удаление нетекстовых элементов (скрипты, стили) внутри целевого узла
        for element in target_node(['script', 'style']):
            element.decompose() # Функция удаляет тег и его содержимое из дерева

        # Извлечение текста из целевого узла
        text: str = target_node.get_text(separator=' ', strip=True)

        # Преобразование HTML-сущностей (&, <, etc.) в символы
        text = html.unescape(text)

        # Дополнительная очистка: замена множественных пробелов одним
        text = re.sub(r'\s+', ' ', text).strip()

        return text
    except Exception as ex:
        # Логгирование ошибки с использованием logger
        logger.error(f"Ошибка при обработке HTML в strip_tags: {html_content[:100]}...", ex, exc_info=True)
        # Возврат пустую строку как индикатор проблемы
        ... # Добавлено троеточие перед return в блоке except
        return ''

def simplify_html(
    html_content: str | None,
    config: Optional[Config] = None, # Позволяет передать специфичную конфигурацию
    parser: Optional[str] = None, # Позволяет переопределить парсер из конфига
) -> str:
    """
    Упрощает HTML-код, фокусируясь на содержимом тега <body> и используя параметры
    из объекта Config (переданного или созданного по умолчанию).

    Удаляет все вне <body>, затем применяет правила упрощения (удаление тегов, атрибутов,
    комментариев, скриптов, стилей и т.д.) к содержимому <body> согласно настройкам
    в объекте `config`. Может также удалять теги-контейнеры внутри <body>,
    не содержащие значимого контента, если `config.keep_only_significant=True`.

    Args:
        html_content (str | None): Строка с HTML-кодом или None.
        config (Optional[Config]): Объект конфигурации. Если None, используется Config()
                                   с настройками по умолчанию.
        parser (Optional[str]): Парсер для BeautifulSoup ('html.parser', 'lxml', 'html5lib').
                                Если указан, переопределяет `config.parser`.

    Returns:
        str: Упрощенный HTML-код содержимого <body>. Возвращает пустую строку при ошибке,
             None/пустом вводе или если тег <body> не найден.

    Raises:
        Exception: BeautifulSoup может генерировать исключения при серьезных проблемах парсинга,
                   которые логируются.

    Example:
        >>> # Пример с удалением class/id по умолчанию
        >>> default_cfg = Config(allowed_tags={'div','span'})
        >>> sample_cls_id = '<body><div class="main" id="cont"><span style="color:red">Text</span></div></body>'
        >>> simplify_html(sample_cls_id, config=default_cfg)
        '<div><span style="color:red">Text</span></div>'

        >>> # Пример с явным разрешением class/id
        >>> allow_cls_id_cfg = Config(allowed_tags={'div','span'}, allowed_attributes={'*':{'class','id','style'}})
        >>> simplify_html(sample_cls_id, config=allow_cls_id_cfg)
        '<div class="main" id="cont"><span style="color:red">Text</span></div>'
    """
    # Используется переданный config или создание новый по умолчанию
    effective_config = config if config is not None else Config()

    # Проверка входных данных
    if not html_content or not isinstance(html_content, str):
        logger.debug("simplify_html: Входные данные некорректны или пустые.")
        return ''

    # Выбор парсера: приоритет у аргумента функции, затем у конфига
    actual_parser: str = parser if parser is not None else effective_config.parser

    try:
        # --- Шаг 1: Изоляция содержимого <body> ---
        original_soup = BeautifulSoup(html_content, actual_parser)
        body_tag = original_soup.body

        if not body_tag:
            # Если нет body, но есть контент, попробуем обработать его как фрагмент
            if original_soup.contents:
                 logger.debug(f"Тег <body> не найден, но есть контент. Обработка как фрагмента: {html_content[:100]}...")
                 body_content_str = html_content # Используется весь контент
            else:
                 logger.warning(f"Тег <body> не найден и нет контента в HTML: {html_content[:100]}... Возвращается пустая строка.")
                 return ''
        else:
            # Получаем содержимое body как строку для повторного парсинга
            body_content_str = body_tag.decode_contents()


        # --- Шаг 2: Обработка изолированного содержимого <body> (или фрагмента) ---
        # создание новый суп только из содержимого body или всего фрагмента
        soup = BeautifulSoup(body_content_str, actual_parser)

        # 2.1 Начальная чистка в новом супе: Комментарии, скрипты, стили
        if effective_config.remove_comments:
            comments = soup.find_all(string=lambda text: isinstance(text, Comment))
            for comment in comments:
                comment.extract()
        if effective_config.remove_scripts_styles:
            # Удаляем script/style, которые могли быть внутри body или фрагмента
            for element in soup(['script', 'style']):
                element.decompose()

        # 2.2 Удаление незначимых контейнеров (если включено)
        if effective_config.keep_only_significant:
            significant_void_tags: Set[str]
            current_allowed_tags = effective_config.allowed_tags
            significant_void_tags = effective_config.VOID_TAGS.intersection(current_allowed_tags)

            significant_elements_ids: Set[int] = set()
            all_tags: List[Tag] = soup.find_all(True)

            for tag in reversed(all_tags):
                if not tag.parent and tag.name != '[document]':
                     ... # Обработка элементов верхнего уровня (не удаляем на основе предков)

                is_significant: bool = False
                tag_name_lower: str = tag.name.lower()

                if tag_name_lower in significant_void_tags:
                    is_significant = True
                else:
                    for child in tag.children:
                        if isinstance(child, NavigableString) and child.string.strip():
                            is_significant = True
                            break
                        elif isinstance(child, Tag) and id(child) in significant_elements_ids:
                             is_significant = True
                             break

                if is_significant:
                    significant_elements_ids.add(id(tag))
                elif tag.parent: # Не удаляем корневые элементы содержимого body этим способом
                    should_unwrap: bool = effective_config.unwrap_tags is not None and tag_name_lower in effective_config.unwrap_tags
                    will_be_unwrapped_by_allowed: bool = tag_name_lower not in current_allowed_tags

                    if not should_unwrap and not will_be_unwrapped_by_allowed:
                         tag.decompose()


        # 2.3 Финальная обработка тегов и атрибутов
        tags_to_process_final: List[Tag] = soup.find_all(True)

        for tag in tags_to_process_final:
            if tag.name == '[document]':
                 continue
            if not tag.find_parent() and tag.name != '[document]':
                 ... # Обработка тега верхнего уровня

            tag_name: str = tag.name.lower()

            # 3.1. Разворачивание тегов из config.unwrap_tags
            if effective_config.unwrap_tags and tag_name in effective_config.unwrap_tags:
                 if tag.parent:
                      tag.unwrap()
                      continue
                 else:
                      logger.debug(f"Попытка unwrap тега '{tag_name}' без родителя (пропущено).")
                      ...

            # 3.2. Фильтрация по разрешенным тегам (config.allowed_tags)
            if tag_name not in effective_config.allowed_tags:
                 if tag.parent:
                      tag.unwrap()
                      continue
                 else:
                      logger.debug(f"Тег '{tag_name}' без родителя не в allowed_tags (пропущено удаление).")
                      ...

            # 3.3. Фильтрация атрибутов (config.allowed_attributes)
            if isinstance(tag, Tag) and tag.attrs:
                current_attrs = dict(tag.attrs)
                specific_allowed_attrs: Set[str] = set()

                if effective_config.allowed_attributes is not None:
                    specific_allowed_attrs.update(effective_config.allowed_attributes.get(tag_name, set()))
                    specific_allowed_attrs.update(effective_config.allowed_attributes.get('*', set()))

                # Если словарь атрибутов пустой или для тега нет разрешенных - удаляем все
                if not effective_config.allowed_attributes or not specific_allowed_attrs:
                     tag.attrs = {}
                else:
                    # Итерируем по копии ключей, чтобы безопасно удалять из оригинала
                    for attr_name_case_sensitive in list(current_attrs.keys()):
                        attr_name_lower: str = attr_name_case_sensitive.lower()
                        if attr_name_lower not in specific_allowed_attrs:
                            # Удаляем атрибут, если его нет в разрешенных
                            del tag.attrs[attr_name_case_sensitive]


        # --- Шаг 3: Получение финального HTML и нормализация пробелов ---
        # Извлекаем содержимое обработанного супа
        final_html: str = soup.decode_contents()

        # Нормализация пробелов, если опция включена
        if effective_config.normalize_whitespace and final_html:
            final_html = re.sub(r'\s+', ' ', final_html).strip()

        return final_html

    except Exception as ex:
        logger.error(f"Ошибка при обработке HTML в simplify_html: {html_content[:100]}...", ex, exc_info=True)
        ... # Добавлено троеточие перед return в блоке except
        return '' # Возврат пустую строку при любой ошибке


# --- Примеры использования (для демонстрации и отладки) ---

if __name__ == "__main__":
    # Предполагается, что logger уже настроен где-то при старте приложения
    # Если нет, можно добавить базовую настройку для тестов:
    # import logging
    # logging.basicConfig(level=logging.DEBUG)
    # logger = logging.getLogger(__name__) # Используется стандартный логгер, если src.logger не настроен

    logger.info("--- Примеры работы модуля html_simplification ---")

    # Определение парсер единожды
    parser_choice = 'lxml'
    try:
        import lxml
        logger.debug(f"(Используется парсер: {parser_choice})")
    except ImportError:
        parser_choice = 'html.parser'
        logger.debug(f"(Парсер lxml не найден, используется: {parser_choice})")


    sample_html_full: str = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Тестовая страница</title>
        <style> body { font-family: sans-serif; } /* CSS комментарий */ </style>
        <script type="text/javascript"> alert("Hello!"); // JS комментарий </script>
    </head>
    <body>
        <div id="main" class="container">
            <h1 style="color:blue;">   Пример    HTML   </h1>
            <p style="margin: 10px;" class="main-text first">
                Это <b>первый</b> абзац с <a HREF="http://example.com" Target="_blank" title="Visit">ссылкой</a>.
                <!-- Это HTML комментарий внутри body -->
                Содержит <span class="highlight">   ненужный   </span> & важный текст.
            </p>
            <div class="empty-container">   </div>
            <div>
                Еще текст <br/> с переносом строки. <img src="/logo.png" alt="Логотип" title="Company Logo" width="100" />
            </div>
            <p class="main-text second">Второй абзац.</p>
        </div>
        <hr/>
        <footer> Пустая секция </footer>
    </body>
    </html>
    """
    # Закомментировано чтение файла, чтобы примеры работали автономно
    # try:
    #     from header import __root__ # Предполагаем, что __root__ определен
    #     sample_html_full = Path(__root__,'SANDBOX','davidka','raw_data_products','raw-1802-27026.html').read_text(encoding='utf-8')
    #     logger.info("Загружен HTML из файла.")
    # except (ImportError, FileNotFoundError) as e:
    #     logger.warning(f"Не удалось загрузить HTML из файла, используется встроенный пример: {e}")

    logger.info("\n1. Исходный HTML (фрагмент):\n" + sample_html_full[150:650])

    logger.info("\n2. Текст после strip_tags():")
    stripped_text: str = strip_tags(sample_html_full, parser=parser_choice)
    logger.info(stripped_text)

    logger.info("\n3. simplify_html() с Config по умолчанию (class/id удалены):")
    # Используется config по умолчанию, где class/id НЕ разрешены для '*'
    default_cfg = Config()
    simplified_default: str = simplify_html(sample_html_full, config=default_cfg, parser=parser_choice)
    logger.info(simplified_default)
    # Ожидаемый результат: структура сохранена, но атрибуты class и id удалены. style остается.
    # <div style=""> <h1 style="color:blue;"> Пример HTML </h1> <p style="margin: 10px;"> Это <b>первый</b> абзац с <a href="http://example.com" title="Visit">ссылкой</a>. Содержит <span> ненужный </span> & важный текст. </p> <div style=""> </div> <div style=""> Еще текст <br/> с переносом строки. <img src="/logo.png" alt="Логотип" title="Company Logo"/> </div> <p style="">Второй абзац.</p> </div> <hr/> Пустая секция

    logger.info("\n4. simplify_html() с Config, явно разрешающим class/id:")
    config_allow_cls_id = Config(
        allowed_tags=default_cfg.allowed_tags, # Берем теги из дефолта
        allowed_attributes={'a': {'href', 'title'}, 'img': {'src', 'alt', 'title'}, '*': {'class', 'id', 'style'}}, # Разрешаем class, id, style для всех
        unwrap_tags=default_cfg.unwrap_tags,
        keep_only_significant=False,
    )
    simplified_cls_id: str = simplify_html(sample_html_full, config=config_allow_cls_id, parser=parser_choice)
    logger.info(simplified_cls_id)
    # Ожидаемый результат: class и id остаются, т.к. явно разрешены.
    # <div id="main" class="container" style=""> <h1 style="color:blue;"> Пример HTML </h1> <p style="margin: 10px;" class="main-text first"> Это <b>первый</b> абзац с <a href="http://example.com" title="Visit">ссылкой</a>. Содержит <span class="highlight"> ненужный </span> & важный текст. </p> <div class="empty-container" style=""> </div> <div style=""> Еще текст <br/> с переносом строки. <img src="/logo.png" alt="Логотип" title="Company Logo"/> </div> <p class="main-text second" style="">Второй абзац.</p> </div> <hr/> Пустая секция


    logger.info("\n5. simplify_html() с keep_significant=True (class/id удалены по умолчанию):")
    config_significant = Config(
        allowed_tags={'p', 'b', 'a', 'br', 'img', 'h1', 'hr', 'div'}, # Конкретные теги
        allowed_attributes={'a': {'href'}, 'img': {'src', 'alt'}, '*': {'style'}}, # Разрешен только style
        unwrap_tags={'span', 'footer'},
        keep_only_significant=True,
    )
    simplified_significant: str = simplify_html(sample_html_full, config=config_significant, parser=parser_choice)
    logger.info(simplified_significant)
    # Ожидаемый результат: Как в тесте 3, но без class/id. Пустой div удален.
    # <div style=""> <h1 style="color:blue;"> Пример HTML </h1> <p style="margin: 10px;"> Это <b>первый</b> абзац с <a href="http://example.com">ссылкой</a>. Содержит ненужный & важный текст. </p> <div style=""> Еще текст <br/> с переносом строки. <img src="/logo.png" alt="Логотип"/> </div> <p style="">Второй абзац.</p> </div> <hr/> Пустая секция


    logger.info("\n--- Тестирование крайних случаев ---")
    default_config_test = Config() # Используется config по умолчанию для тестов
    config_keep_significant_default = Config(keep_only_significant=True)

    logger.info(f"strip_tags(None): -> '{strip_tags(None)}'")
    logger.info("\n------------------------------------")
    logger.info(f"strip_tags(''): -> '{strip_tags('')}'")
    logger.info("\n------------------------------------")
    logger.info(f"simplify_html(None, config=default_config_test): -> '{simplify_html(None, config=default_config_test)}'")
    logger.info("\n------------------------------------")
    logger.info(f"simplify_html('', config=default_config_test): -> '{simplify_html('', config=default_config_test)}'")
    logger.info("\n------------------------------------")
    # HTML без body (будет обработан как фрагмент)
    html_no_body = '<h1 class="title">Title</h1><p id="intro">Text</p>'
    logger.info(f"simplify_html (no body, default config): -> '{simplify_html(html_no_body, config=default_config_test, parser=parser_choice)}'") # class/id будут удалены
    logger.info("\n------------------------------------")
    # HTML с пустым body
    html_empty_body = "<html><head></head><body></body></html>"
    logger.info(f"simplify_html (empty body): -> '{simplify_html(html_empty_body, config=default_config_test, parser=parser_choice)}'")
    logger.info("\n------------------------------------")
    # keep_significant с пустым div в body
    html_empty_div = '<body><div class="empty"> </div></body>'
    # Ожидаем '', т.к. div пустой и keep_significant=True
    logger.info(f"simplify_html ('<div class=\"empty\"> </div>', config=config_keep_significant_default): -> '{simplify_html(html_empty_div, config=config_keep_significant_default, parser=parser_choice)}'")
    logger.info("\n------------------------------------")
    # keep_significant с текстом в p
    html_p_text = '<body><p class="para">Text</p></body>'
    config_p_only_sig = Config(allowed_tags={'p'}, keep_only_significant=True) # class удалится, т.к. не разрешен в этой config
    logger.info(f"simplify_html ('<p class=\"para\">Text</p>', config=config_p_only_sig): -> '{simplify_html(html_p_text, config=config_p_only_sig, parser=parser_choice)}'")
    logger.info("\n------------------------------------")
    # keep_significant с br
    html_br = "<body>Текст <br class='break'/> еще</body>"
    config_br_only_sig = Config(allowed_tags={'br'}, keep_only_significant=True) # br останется, class удалится
    logger.info(f"simplify_html ('Текст <br class=\'break\'/> еще', config=config_br_only_sig): -> '{simplify_html(html_br, config=config_br_only_sig, parser=parser_choice)}'")