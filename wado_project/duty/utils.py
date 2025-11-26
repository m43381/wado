# duty/utils.py
def normalize_weekday_setting(day_setting):
    """
    Нормализует входное значение дня недели к числу от 0 (понедельник) до 6 (воскресенье).
    Поддерживает:
      - числа (int или str с цифрой)
      - полные и сокращённые названия на русском и английском
    Возвращает int или None при ошибке.
    """
    if day_setting is None:
        return None

    # Если уже число
    if isinstance(day_setting, int):
        return day_setting if 0 <= day_setting <= 6 else None

    # Если строка
    if isinstance(day_setting, str):
        clean = day_setting.strip()
        if not clean:
            return None

        # Попробуем как число
        if clean.isdigit():
            num = int(clean)
            if 0 <= num <= 6:
                return num

        # Названия на русском
        ru_map = {
            'понедельник': 0, 'вторник': 1, 'среда': 2, 'четверг': 3,
            'пятница': 4, 'суббота': 5, 'воскресенье': 6,
            'пн': 0, 'вт': 1, 'ср': 2, 'чт': 3, 'пт': 4, 'сб': 5, 'вс': 6,
        }

        # Названия на английском
        en_map = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6,
            'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3, 'fri': 4, 'sat': 5, 'sun': 6,
        }

        key = clean.lower()
        return ru_map.get(key) or en_map.get(key)

    return None