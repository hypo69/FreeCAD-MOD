def list2dict(list_of_dicts, policy='last_wins'):
    """
    Преобразует список словарей в один словарь.

    Args:
        list_of_dicts (list): Список словарей для объединения.
        policy (str): Политика разрешения конфликтов для дублирующихся ключей.
                      - 'last_wins' (по умолчанию): оставляет значение из последнего встреченного словаря.
                      - 'first_wins': оставляет значение из первого встреченного словаря.

    Returns:
        dict: Объединенный словарь.
    """
    merged_dict = {}

    if policy == 'last_wins':
        # Проходим по списку и обновляем словарь.
        # Последнее значение для дублирующегося ключа перезаписывает предыдущее.
        for d in list_of_dicts:
            merged_dict.update(d)
    
    elif policy == 'first_wins':
        # Проходим по списку в обратном порядке, чтобы
        # первое значение для дублирующегося ключа осталось в результате.
        for d in reversed(list_of_dicts):
            merged_dict.update(d)

    return merged_dict