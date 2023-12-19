from django.contrib import admin
from .models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                     ShoppingCart, Tag)


class BaseAdmin(admin.ModelAdmin):
    """
    Базовый класс для настройки административной панели Django.
    Содержит настройки, применяемые к нескольким моделям.
    """

    empty_value_display = '-'
    list_per_page = 20


class IngredientInRecipeInline(admin.TabularInline):
    """
    Класс для отображения ингредиентов в административной панели рецептов
    """

    model = IngredientInRecipe
    extra = 0
    min_num = 1


@admin.register(Ingredient)
class IngredientAdmin(BaseAdmin):
    """Класс для настройки административной панели ингредиентов"""

    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('name',)
    inlines = (IngredientInRecipeInline,)


@admin.register(Tag)
class TagAdmin(BaseAdmin):
    """Класс для настройки административной панели тегов"""

    list_display = ('name', 'color', 'slug')
    search_fields = ('name', 'color')
    list_filter = ('name', 'color')


@admin.register(Recipe)
class RecipeAdmin(BaseAdmin):
    """Класс для настройки административной панели рецептов"""

    list_display = (
        'name',
        'author',
        'text',
        'cooking_time',
        'pub_date',
        'favorites_count',
    )
    search_fields = ('name', 'author__username', 'favorites_count')
    list_filter = ('author', 'name', 'tags')
    inlines = (IngredientInRecipeInline,)

    def favorites_count(self, obj):
        """Число добавлений в избранное"""

        return obj.favorites.count()


@admin.register(ShoppingCart)
class ShoppingCartAdmin(BaseAdmin):
    """Класс для настройки административной панели корзины покупок"""

    list_display = ('user', 'recipe')
    list_filter = ('user', 'recipe')
    search_fields = ('user',)


@admin.register(Favorite)
class FavoriteAdmin(BaseAdmin):
    """Класс для настройки административной панели избранного"""

    list_display = ('user', 'recipe')
    list_filter = ('user', 'recipe')
    search_fields = ('user',)
