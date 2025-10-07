## \file /src/utils/port.py
# -*- coding: utf-8 -*-
#! .pyenv/bin/python3

"""
Модуль для поиска свободного сетевого порта.
============================================

Позволяет найти свободный порт на указанном хосте либо в заданном диапазоне(ах),
либо начиная с определенного порта вверх.

```rst
    .. module:: src.utils.port
"""

import socket
from typing import Optional, Union, List, Tuple, TypeVar

import header
from header import __root__
from src.logger import logger

T = TypeVar("T")
PortRangeType = Optional[Union[str, List[Union[str, List[int]]]]]

def get_free_port(port_range: PortRangeType = None, host: str = '127.0.0.1') -> int:
    """!
    Находит и возвращает свободный порт в указанном диапазоне(ах),
    или первый доступный порт, если диапазон не задан.

    Args:
        port_range (PortRangeType, optional): Диапазон(ы) портов.
            Может быть строкой "min-max", списком строк "min-max",
            списком списков чисел [min, max] или None.
            Например: "3000-3999", ["3000-3999", "8000-8010"], [[4000, 4099], [9000, 9010]].
        host (str, optional): IP-адрес хоста. По умолчанию '127.0.0.1'.

    Returns:
        int: Первый свободный порт.

    Raises:
        ValueError: Если не удалось найти свободный порт или формат диапазона некорректен.

    Examples:
        >>> get_free_port()  # Найдёт первый свободный порт от 1024 до 65535
        51023

        >>> get_free_port("3000-3010")
        3002

        >>> get_free_port(["3000-3010", "5000-5010"])
        3001

        >>> get_free_port([[4000, 4010], [6000, 6010]])
        4000
    """

    ranges: List[range] = []

    def _is_port_in_use(port: int) -> bool:
        """Проверяет, занят ли порт на заданном хосте.

        Args:
            port (int): Порт для проверки.

        Returns:
            bool: True — порт занят, False — порт свободен.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind((host, port))
                return False
            except OSError:
                return True
            except Exception as ex:
                logger.error(f"Ошибка при проверке порта {port} на хосте {host}", ex, exc_info=True)
                return True

    def _parse_range(r: Union[str, List[int]]) -> Optional[range]:
        """Преобразует строку "min-max" или список [min, max] в range.

        Args:
            r (Union[str, List[int]]): Входной диапазон.

        Returns:
            Optional[range]: Объект range, если успешно; иначе None.
        """
        try:
            if isinstance(r, str):
                parts = r.strip().split("-")
                if len(parts) != 2:
                    return None
                start, end = int(parts[0]), int(parts[1])
            elif isinstance(r, list) and len(r) == 2 and all(isinstance(x, int) for x in r):
                start, end = r
            else:
                return None

            if start < 1 or end > 65535 or start >= end:
                return None

            return range(start, end + 1)
        except Exception as ex:
            logger.error(f"Ошибка парсинга диапазона: {r}", ex, exc_info=True)
            return None

    match port_range:
        case None:
            port_range:list = [1024,65535]

        case str():
            if not _is_port_in_use(port):
                return int(port_range)
            
            raise ValueError(f"Неверный формат диапазона: {port_range}")
            return -1

        case list():
            for port in port_range:
                if not _is_port_in_use(port):
                    return port
            logger.error(f"Свободный порт не найден в диапазоне(ах): {port_range}")
            return -1
        case _:
            raise ValueError(f"Неподдерживаемый тип port_range: {type(port_range)}")
            return -1

