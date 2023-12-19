from django.contrib.auth.models import AbstractUser
from django.db import models
from .validators import validate_username_symbols, validate_username_not_me
from api.constans import (
    TEXT_LIMIT,
    MAX_LENGHT_EMAIL,
    MAX_LENGHT_USERNAME,
    MAX_LENGHT_FIRST_NAME,
    MAX_LENGHT_LAST_NAME
)


class CustomUser(AbstractUser):
    """Кастомная модель пользователя"""

    email = models.EmailField(
        'Адрес электронной почты',
        unique=True,
        max_length=MAX_LENGHT_EMAIL,
    )
    username = models.CharField(
        'Уникальный юзернейм',
        max_length=MAX_LENGHT_USERNAME,
        unique=True,
        validators=[
            validate_username_symbols,
            validate_username_not_me
        ]
    )
    first_name = models.CharField(
        'Имя',
        max_length=MAX_LENGHT_FIRST_NAME,
        blank=False
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=MAX_LENGHT_LAST_NAME,
        blank=False
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username[:TEXT_LIMIT]


class Subscription(models.Model):
    """Модель для подписок на других пользователей"""

    user = models.ForeignKey(
        CustomUser,
        verbose_name='Подписчик',
        on_delete=models.CASCADE,
        related_name='followers',
    )
    author = models.ForeignKey(
        CustomUser,
        verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='following',
    )

    class Meta:
        ordering = ('user',)
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='unique_follow'
            )
        ]

    def __str__(self):
        return f'{self.user.username} подписан(а) на {self.author.username}'
