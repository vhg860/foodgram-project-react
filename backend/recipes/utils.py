import random


def generate_color():
    """Рандомная генерация цвета для тега."""
    return '#%06x' % random.randint(0, 0xFFFFFF)
