from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator


class ColorValidator(RegexValidator):
    """Валидатор для проверки формата цвета HEX (#RRGGBB)."""

    def __init__(self, *args, **kwargs):
        """Инициализация валидатора цвета"""
        regex = r'^#[A-Fa-f0-9]{6}$'
        message = 'Цвет должен быть в формате HEX (#RRGGBB)'

        super().__init__(regex=regex, message=message, *args, **kwargs)

    def __call__(self, value):
        """Вызов валидатора для проверки значения"""
        try:
            super().__call__(value)
        except ValidationError as e:
            raise ValidationError('Такого цвета не существует') from e
