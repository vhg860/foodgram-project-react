from django.contrib import admin

from users.admin import BaseAdmin

from .models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                     ShoppingCart, Tag)


class IngredientInRecipeInline(admin.TabularInline):
    """Класс для отображения ингредиентов в панели рецептов."""

    model = IngredientInRecipe
    extra = 0
    min_num = 1


@admin.register(Ingredient)
class IngredientAdmin(BaseAdmin):
    """Класс для настройки административной панели ингредиентов."""

    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('name',)
    inlines = (IngredientInRecipeInline,)


@admin.register(Tag)
class TagAdmin(BaseAdmin):
    """Класс для настройки административной панели тегов."""

    list_display = ('name', 'color', 'slug')
    search_fields = ('name', 'color')
    list_filter = ('name', 'color')


@admin.register(Recipe)
class RecipeAdmin(BaseAdmin):
    """Класс для настройки административной панели рецептов."""

    list_display = (
        'name',
        'author',
        'text',
        'cooking_time',
        'pub_date',
        'favorites_count',
        'display_ingredients'
    )
    search_fields = ('name', 'author__username', 'favorites_count')
    list_filter = ('author', 'name', 'tags')
    inlines = (IngredientInRecipeInline,)

    def favorites_count(self, obj):
        """Число добавлений в избранное."""
        return obj.favorites.count()

    def display_ingredients(self, recipe):
        """Отображение ингредиентов через запятую."""
        return ', '.join([
            ingredient.name for ingredient in recipe.ingredienttorecipe.all()])
    display_ingredients.short_description = 'Отображение ингредиентов'


@admin.register(ShoppingCart)
class ShoppingCartAdmin(BaseAdmin):
    """Класс для настройки административной панели корзины покупок."""

    list_display = ('user', 'recipe')
    list_filter = ('user', 'recipe')
    search_fields = ('user',)


@admin.register(Favorite)
class FavoriteAdmin(BaseAdmin):
    """Класс для настройки административной панели избранного."""

    list_display = ('user', 'recipe')
    list_filter = ('user', 'recipe')
    search_fields = ('user',)
