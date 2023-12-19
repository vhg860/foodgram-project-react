from django.contrib import admin

from .models import CustomUser, Subscription


class BaseAdmin(admin.ModelAdmin):
    """
    Базовый класс для настройки административной панели Django.
    Содержит настройки, применяемые к нескольким моделям.
    """
    empty_value_display = '-'
    list_per_page = 20


@admin.register(CustomUser)
class CustomUserAdmin(BaseAdmin):
    """Класс для настройки административной панели пользователей"""

    list_display = (
        'username',
        'first_name',
        'last_name',
        'email',
    )
    search_fields = ('username', 'email',)
    list_filter = ('username', 'email',)
    ordering = ('username',)


@admin.register(Subscription)
class SubscriptionAdmin(BaseAdmin):
    """Класс для настройки административной панели подписок"""

    list_display = (
        'user',
        'author',
    )
    search_fields = ('user__username', 'author__username',)
    list_filter = ('user', 'author',)
    ordering = ('user',)
