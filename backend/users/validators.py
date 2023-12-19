from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

validate_username_symbols = RegexValidator(
    regex=r'^[\w.@+-]+$',
    message='Юзернейм не может содержать специальные символы',
)


def validate_username_not_me(value):
    if value.lower() == 'me':
        raise ValidationError(
            _("Имя пользователя не может быть 'me'")
        )
